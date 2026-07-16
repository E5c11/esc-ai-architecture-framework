---
id: PLAT-MOB-HTTP
type: guide
layer: platform
platform: [mobile]
architecture: [pragmatic-clean]
requires: [ARCH-PC-DATASOURCE, CORE-DI, PLAT-MOB-KOTLIN]
related: [ARCH-PC-ERROR-FLOW, ARCH-PC-ERR-CLASSES, PAT-OUTCOME, PLAT-LIB-KMP]
tags: [http, ktor, api-client, rest, serialization, auth-header, retry, timeout, interceptor, header-provider]
---

# HTTP Client Layer (Mobile → Backend)

## Overview

The mobile platform calls a backend (Spring Boot or otherwise) over HTTP from every KMP
target — Android, iOS, and web (`wasmJs`, see `PLAT-MOB-KMP`). This document covers the
mobile-side HTTP client only — not the backend server (that's `platforms/backend/`).

This guide describes the shape of an HTTP client layer for `commonMain`, not a specific
library mandate. The reference example throughout is `arrow-http`
(`io.github.blackarrows-apps:http-core` / `:http-ktor`) — a published, client-agnostic
Kotlin Multiplatform HTTP abstraction (see `PLAT-LIB-KMP` if you're building or evaluating a
library like it, as opposed to consuming one). Using `arrow-http` specifically is not a hard
requirement of this document; the rules below are about the *shape* an HTTP layer needs,
regardless of which concrete library backs it.

## Client library choice and rationale

```rule
id: PLAT-MOB-HTTP-LIB-01
statement: The HTTP client used in `commonMain` MUST be abstracted behind an interface `commonMain` code depends on — never a concrete client type (a Ktor `HttpClient`, an OkHttp client, etc.) referenced directly from a DataSource.
type: hard
scope: testing
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-HTTP-LIB-01 — The HTTP client used in `commonMain` MUST be abstracted behind an interface `commonMain` code depends on — never a concrete client type (a Ktor `HttpClient`, an OkHttp client, etc.) referenced directly from a DataSource.
```

This is `CORE-DI` applied specifically to networking: swapping the underlying client (or testing against a fake) must not require touching every call site.

Ktor is the practical default for KMP (it has engines for every target this framework
supports: OkHttp on Android/JVM, Darwin on iOS, `Js`/Fetch on `wasmJs`/`js`) — but the
abstraction interface itself should not leak Ktor types into its public signatures.

```kotlin
// commonMain — the abstraction DataSources depend on
interface HttpRequestExecutor {
    suspend fun getJson(url: String, queryParams: Map<String, String> = emptyMap(), ...): ApiResponse
    suspend fun postJson(url: String, body: Any, ...): ApiResponse
    // ... put, patch, delete
}
```

## Client configuration

Base URL, timeouts, and serialization are configured once, at composition time — not
per-call, and not hardcoded inside a DataSource:

```rule
id: PLAT-MOB-HTTP-CFG-01
statement: Base URL is injected via DI (build-config or a platform-specific config object — see `PLAT-MOB-KMP-WEB-02` for the web-target equivalent), never string-literal-concatenated inside a DataSource method.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-HTTP-CFG-01 — Base URL is injected via DI (build-config or a platform-specific config object — see `PLAT-MOB-KMP-WEB-02` for the web-target equivalent), never string-literal-concatenated inside a DataSource method.
```

```rule
id: PLAT-MOB-HTTP-CFG-02
statement: JSON serialization uses `kotlinx.serialization` exclusively in `commonMain` — no platform-specific JSON library (Gson, Moshi) may appear in shared code, since it won't compile for iOS/web.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-HTTP-CFG-02 — JSON serialization uses `kotlinx.serialization` exclusively in `commonMain` — no platform-specific JSON library (Gson, Moshi) may appear in shared code, since it won't compile for iOS/web.
```

Per-request overrides (a longer timeout for one specific call, an extra header) go through
an explicit config parameter on the call, not a mutable global:

```kotlin
data class HttpRequestConfig(
    val headers: HttpHeaders = HttpHeaders.Empty,
    val timeout: Long? = null,
    val followRedirects: Boolean = true,
)
```

## Authentication and token refresh

```rule
id: PLAT-MOB-HTTP-AUTH-01
statement: Auth token attachment is a provider the executor calls, not logic duplicated in every DataSource:
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-HTTP-AUTH-01 — Auth token attachment is a provider the executor calls, not logic duplicated in every DataSource:
```

```kotlin
interface HeaderProvider {
    suspend fun getHeaders(vararg additional: Pair<String, String>): Map<String, String>
    fun invalidate()
}
```

A DataSource asks for a request with `authRequired = true`; the executor is responsible for
resolving the current token via the injected `HeaderProvider`. The DataSource never touches
a token store, a JWT, or a refresh endpoint directly — that would violate `CORE-DI` (the
DataSource would depend on a concrete auth mechanism instead of an abstraction) and duplicate
refresh logic across every call site that needs auth.

```rule
id: PLAT-MOB-HTTP-AUTH-02
statement: Token refresh-on-expiry is a policy/interceptor the executor runs transparently — not something the calling DataSource retries manually:
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-HTTP-AUTH-02 — Token refresh-on-expiry is a policy/interceptor the executor runs transparently — not something the calling DataSource retries manually:
```

```kotlin
interface AuthRefresher {
    suspend fun refresh(): ReauthResult   // Success | Failed
}

class AuthPolicy(
    private val authRefresher: AuthRefresher,
    private val maxRetries: Int = 1,
) : HttpPolicy {
    override suspend fun intercept(next: suspend () -> ApiResponse): ApiResponse
    // on a 401: invalidate cached headers, call authRefresher.refresh(), retry up to maxRetries
}
```

A DataSource that receives a response from the executor should never see a stale-token 401 —
by the time the executor returns, either the refresh succeeded and the retried call's result
is returned, or the refresh failed and the DataSource sees the resulting `AuthException`
(mapped per the error rules below) exactly once.

## Retry strategy

```rule
id: PLAT-MOB-HTTP-RETRY-01
statement: Retry policy operates on the *category* of failure, not the call site.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-HTTP-RETRY-01 — Retry policy operates on the *category* of failure, not the call site.
```

Transient/network failures are retryable; 4xx client errors generally are not (retrying a 400 or 404 wastes a round-trip on a request that will never succeed unmodified).

```kotlin
class RetryPolicy(
    private val maxRetries: Int = 3,
    private val initialDelayMs: Long = 1000,
    private val factor: Double = 2.0,     // exponential backoff
) : HttpPolicy
```

The retryability signal lives on the exception, not on a per-call flag the DataSource has to
remember to pass:

```kotlin
class NetworkException(
    message: String,
    val isRetryable: Boolean = true,
    ...
) : HttpException(message, cause)
```

## Error mapping

```rule
id: PLAT-MOB-HTTP-ERR-01
statement: HTTP-layer failures map to a typed exception hierarchy at the client layer itself — not left as raw platform exceptions (a Ktor `ConnectTimeoutException`, an OkHttp `IOException`) for the DataSource to catch and interpret.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-HTTP-ERR-01 — HTTP-layer failures map to a typed exception hierarchy at the client layer itself — not left as raw platform exceptions (a Ktor `ConnectTimeoutException`, an OkHttp `IOException`) for the DataSource to catch and interpret.
```

This is `CORE-ERROR`'s "map low-level technical errors... at the layer boundary closest to where they originate" applied to the HTTP boundary specifically:

```kotlin
sealed class HttpException(message: String, cause: Throwable?) : Exception(message, cause)
class NetworkException(...) : HttpException(...)       // retryable connectivity failures
class AuthException(...) : HttpException(...)           // 401/403, token issues
class HttpStatusException(...) : HttpException(...)     // other 4xx/5xx
class TimeoutException(...) : HttpException(...)
class SerializationException(...) : HttpException(...)  // JSON parse failures
```

```rule
id: PLAT-MOB-HTTP-ERR-02
statement: The HTTP client layer's exceptions are a **provider- level** vocabulary, not the app's domain error vocabulary — `PAT-OUTCOME` and `ARCH-PC-ERR- CLASSES` still govern what a DataSource surfaces to the layer above it.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-HTTP-ERR-02 — The HTTP client layer's exceptions are a **provider- level** vocabulary, not the app's domain error vocabulary — `PAT-OUTCOME` and `ARCH-PC-ERR- CLASSES` still govern what a DataSource surfaces to the layer above it.
```

The DataSource is where `HttpStatusException(404)` becomes `DataNotFoundException` or similar; the HTTP client itself should not know about domain concepts. This is consistent with `CORE-ERROR`'s category table — the HTTP client throwing a typed technical exception is correct; letting that same exception type propagate past the DataSource boundary unmapped is not.

## KMP source-set placement

```rule
id: PLAT-MOB-HTTP-SS-01
statement: The executor interface and all business logic that calls it live in `commonMain` (per `PLAT-MOB-KMP-SS-01`).
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-HTTP-SS-01 — The executor interface and all business logic that calls it live in `commonMain` (per `PLAT-MOB-KMP-SS-01`).
```

Only the concrete client construction — the actual `HttpClient(engine) { ... }` — is platform-specific:

```
commonMain:  interface HttpRequestExecutor; class KtorHttpRequestExecutor (implements it,
             calls an `expect fun createHttpClient(): HttpClient`)
androidMain: actual fun createHttpClient() = HttpClient(OkHttp) { ... }
iosMain:     actual fun createHttpClient() = HttpClient(Darwin) { ... }
wasmJsMain:  actual fun createHttpClient() = HttpClient(Js) { ... }   // + browser Fetch quirks,
                                                                        // see below
```

```rule
id: PLAT-MOB-HTTP-SS-02
statement: Browser-specific Fetch API quirks (e.g. gzip responses keeping a pre-decompression `Content-Length` header, which trips a strict length check on some HTTP clients) belong in the `wasmJsMain`/`jsMain` client factory as a documented workaround with an explanation of *why*, not silently patched — a future reader needs to know it's a browser behaviour, not a bug in the abstraction.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-HTTP-SS-02 — Browser-specific Fetch API quirks (e.g. gzip responses keeping a pre-decompression `Content-Length` header, which trips a strict length check on some HTTP clients) belong in the `wasmJsMain`/`jsMain` client factory as a documented workaround with an explanation of *why*, not silently patched — a future reader needs to know it's a browser behaviour, not a bug in the abstraction.
```

## DI registration

```rule
id: PLAT-MOB-HTTP-DI-01
statement: The configured executor is registered as a Koin `single`, constructed once at app start with its `HeaderProvider`, `AuthRefresher`, and policy list — not constructed ad hoc inside a DataSource:
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-HTTP-DI-01 — The configured executor is registered as a Koin `single`, constructed once at app start with its `HeaderProvider`, `AuthRefresher`, and policy list — not constructed ad hoc inside a DataSource:
```

```kotlin
val httpModule = module {
    single { createHttpClient() }
    single<HttpRequestExecutor> {
        KtorHttpRequestExecutor(
            client = get(),
            authHeaderProvider = get(),
            policies = listOf(get<AuthPolicy>(), get<RetryPolicy>()),
        )
    }
}
```

Platform-specific `HeaderProvider`/`AuthRefresher` implementations (if they touch platform
credential storage) follow `PLAT-MOB-KMP-DI-01` — registered in the relevant platform module.

## Testing

```rule
id: PLAT-MOB-HTTP-TEST-01
statement: Per `CORE-TESTING`/`QG-TESTING` — DataSource unit tests use a **fake** implementation of the executor interface, not a mock.
type: hard
scope: testing
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-HTTP-TEST-01 — Per `CORE-TESTING`/`QG-TESTING` — DataSource unit tests use a **fake** implementation of the executor interface, not a mock.
```

A fake HTTP executor is a component you own (it's part of your own testing infrastructure), so it should behave like one: stub responses per URL, record calls for assertion, no call-count verification theater.

```kotlin
val fake = FakeHttpRequestExecutor()
fake.stub("https://api.example.com/users/1", FakeApiResponse.success("""{"id":1}"""))

val result = myDataSource.fetchUser("1")   // internally calls fake

assertEquals(1, fake.calls.size)
assertEquals(FakeHttpMethod.GET, fake.calls.first().method)
```

```rule
id: PLAT-MOB-HTTP-TEST-02
statement: If the executor implementation itself needs testing (e.g. confirming `KtorHttpRequestExecutor.patchJson` issues an actual `HttpMethod.Patch`), that's a different, narrower test — use Ktor's `MockEngine` at that layer, not the fake.
type: soft
scope: testing
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-HTTP-TEST-02 — If the executor implementation itself needs testing (e.g. confirming `KtorHttpRequestExecutor.patchJson` issues an actual `HttpMethod.Patch`), that's a different, narrower test — use Ktor's `MockEngine` at that layer, not the fake.
```

The fake is for consumers of the executor; `MockEngine` is for testing the executor itself.

## Validation Checklist

Before committing any change to the HTTP client layer:
- [ ] No Ktor (or other concrete client) type appears in a `commonMain` DataSource's own
      public API — only the executor interface
- [ ] Auth token attachment goes through `HeaderProvider`, never a DataSource reading a
      token store directly
- [ ] Token refresh is a policy on the executor, not manual retry logic in a DataSource
- [ ] Every HTTP failure surfaces as a typed `HttpException` subtype, not a raw platform
      exception, by the time it reaches the DataSource
- [ ] The DataSource — not the HTTP client — is what translates `HttpException` into the
      app's own domain error vocabulary (`PAT-OUTCOME` / `ARCH-PC-ERR-CLASSES`)
- [ ] DataSource tests use a fake executor; only the executor implementation's own tests use
      a client-level mock (`MockEngine` or equivalent)
- [ ] Any browser-specific client workaround is commented with *why*, not left unexplained
