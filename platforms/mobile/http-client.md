---
id: PLAT-MOB-HTTP
type: guide
layer: platform
platform: [mobile]
architecture: [pragmatic-clean]
requires: [ARCH-PC-DATASOURCE, ARCH-PC-ERR-CLASSES, CORE-DI, PLAT-MOB-KOTLIN]
related: [ARCH-PC-ERROR-FLOW, PAT-OUTCOME, PLAT-LIB-KMP, PLAT-MOB-KMP-IOS]
tags: [http, ktor, api-client, rest, serialization, auth-header, retry, timeout, interceptor, header-provider]
status: active
---

# HTTP Client Layer (Mobile → Backend)

## Overview

The mobile platform calls a backend (Spring Boot or otherwise) over HTTP from every KMP
target — Android, iOS, and web (`wasmJs`, see `PLAT-MOB-KMP`). This document covers the
mobile-side HTTP client only — not the backend server (that's `platforms/backend/`).

The HTTP client is infrastructure behind DataSource interfaces — Ktor or an owned wrapper
such as `arrow-http` may implement transport policy, but it never becomes a domain API.

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

Keep request/response DTOs, serialization and provider-neutral client policy in common or
a deliberate shared REST source set. Engine dependencies remain platform-specific:

| Target | Engine responsibility |
|---|---|
| Android/JVM | Android/JVM-compatible engine selected by the project |
| iOS | Ktor Darwin engine in `iosMain` |
| wasmJs | Browser-compatible Ktor engine |

```rule
id: PLAT-MOB-HTTP-ENGINE-01
statement: Every configured target MUST provide exactly one compatible engine.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-HTTP-ENGINE-01 — Every configured target MUST provide exactly one compatible engine.
```

A transitive engine must still be proven by a target compile/link test — a target that
resolves an engine dependency but never actually constructs a client on that target is
unverified, not supported (see `PLAT-MOB-HTTP-TEST-03` below).

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

Attach credentials through an injected header/token provider. Refresh coordination belongs
to a client plugin or `AuthRefresher`, not individual DataSources.

```rule
id: PLAT-MOB-HTTP-AUTH-01
statement: Auth token attachment is a provider the executor calls, not logic duplicated in every DataSource.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-HTTP-AUTH-01 — Auth token attachment is a provider the executor calls, not logic duplicated in every DataSource; DataSources MUST NOT read secure storage or implement token refresh directly.
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
statement: Token refresh-on-expiry is a policy/interceptor the executor runs transparently — not something the calling DataSource retries manually.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-HTTP-AUTH-02 — Token refresh-on-expiry is a policy/interceptor the executor runs transparently; only one refresh may run for concurrent unauthorized responses, and a refreshed request may be replayed at most once.
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
(mapped per the error rules below) exactly once. Concurrent requests that all hit a 401
at once must coalesce onto a single in-flight refresh — each does not trigger its own
refresh — and refresh failure maps to unauthorized/session-expired rather than an infinite
retry loop.

## Retry strategy

```rule
id: PLAT-MOB-HTTP-RETRY-01
statement: Retry policy operates on the *category* of failure, not the call site.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-HTTP-RETRY-01 — Retry policy operates on the *category* of failure, not the call site; retry only idempotent operations, or writes with an explicit idempotency mechanism.
```

Transient/network failures are retryable; 4xx client errors generally are not (retrying a 400 or 404 wastes a round-trip on a request that will never succeed unmodified). Never
automatically retry authentication, validation, permission, or ordinary 4xx failures.

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
violation_message: Violates PLAT-MOB-HTTP-ERR-01 — HTTP and Ktor exceptions MUST NOT escape the DataSource boundary; raw platform exceptions must already be mapped by the time execution reaches it.
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

```rule
id: PLAT-MOB-HTTP-CANCEL-01
statement: Coroutine cancellation MUST be rethrown before broad exception mapping.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-HTTP-CANCEL-01 — Coroutine cancellation MUST be rethrown before broad exception mapping.
```

A broad `catch (e: Exception)` around HTTP-layer error mapping swallows
`CancellationException` unless it's checked and rethrown first — silently breaking
structured concurrency (a cancelled parent scope no longer actually cancels its children).

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

```rule
id: PLAT-MOB-HTTP-SS-03
statement: Platform engine classes and platform credential APIs MUST NOT appear in common client policy or DataSource interfaces.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-HTTP-SS-03 — Platform engine classes and platform credential APIs MUST NOT appear in common client policy or DataSource interfaces.
```

The inverse of `PLAT-MOB-HTTP-SS-01`: not only must the executor interface and business
logic live in `commonMain`, nothing platform-specific may leak back into it either.

## DI registration

```rule
id: PLAT-MOB-HTTP-DI-01
statement: The configured executor is registered as a Koin `single`, constructed once at app start with its `HeaderProvider`, `AuthRefresher`, and policy list — not constructed ad hoc inside a DataSource.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-HTTP-DI-01 — the executor MUST be a Koin `single` injected into DataSources; DataSources must not construct clients per request.
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

```rule
id: PLAT-MOB-HTTP-TEST-03
statement: Platform smoke tests MUST construct the real engine on each target — common-only tests cannot prove Darwin/browser engine availability.
type: hard
scope: testing
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-HTTP-TEST-03 — Platform smoke tests MUST construct the real engine on each target; common-only tests cannot prove Darwin/browser engine availability.
```

The fake is for consumers of the executor; `MockEngine` is for testing the executor's own
request-building logic; a platform smoke test is for proving the real engine actually links
and connects on that target.

## Validation Checklist

Before committing any change to the HTTP client layer:
- [ ] No Ktor (or other concrete client) type appears in a `commonMain` DataSource's own
      public API — only the executor interface
- [ ] Every configured target provides exactly one compatible engine, proven by a
      compile/link test (iOS especially — client construction/linking is tested, not
      just assumed)
- [ ] Auth token attachment goes through `HeaderProvider`, never a DataSource reading a
      token store or secure storage directly
- [ ] Token refresh is a policy on the executor, not manual retry logic in a DataSource;
      concurrent 401s trigger one refresh and at most one replay per request
- [ ] Every HTTP failure surfaces as a typed `HttpException` subtype, not a raw platform
      exception, by the time it reaches the DataSource
- [ ] `CancellationException` is rethrown before broad exception mapping catches it
- [ ] The DataSource — not the HTTP client — is what translates `HttpException` into the
      app's own domain error vocabulary (`PAT-OUTCOME` / `ARCH-PC-ERR-CLASSES`)
- [ ] Non-idempotent writes are not retried without an explicit idempotency mechanism
- [ ] Tokens and secrets are absent from logs
- [ ] DataSource tests use a fake executor; the executor implementation's own tests use a
      client-level mock (`MockEngine`); platform smoke tests cover the real engine per target
- [ ] Any browser-specific client workaround is commented with *why*, not left unexplained
