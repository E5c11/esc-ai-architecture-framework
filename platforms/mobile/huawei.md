---
id: PLAT-MOB-HUAWEI
type: guide
layer: platform
platform: [mobile]
architecture: [pragmatic-clean]
requires: [PLAT-MOB-KOIN, PLAT-MOB-KMP]
related: [PLAT-MOB-KMP-WEB, ARCH-PC-DI]
tags: [huawei, appgallery, hms, gms, flavor, build-variant, di-override, rest, koin]
---

# Huawei AppGallery Build Flavor

## Overview

The Huawei flavor distributes the app through AppGallery. Because AppGallery devices
lack Google Mobile Services (GMS), the Firebase SDK is unavailable. Instead, Firebase
APIs are implemented over the Firebase REST API.

---

## Flavor Dimensions

`composeApp` uses two flavor dimensions:

| Dimension | Values | Purpose |
|-----------|--------|---------|
| `environment` | `dev`, `prod` | Points to different backend projects |
| `distribution` | `google`, `huawei` | GMS (Firebase SDK) vs HMS (REST-only Firebase) |

`core/firebase` uses one flavor dimension:

| Dimension | Values | Purpose |
|-----------|--------|---------|
| `client` | `sdk`, `rest` | Firebase SDK vs Firebase REST implementation |

The `huawei` distribution flavor sets `missingDimensionStrategy("client", "rest")`,
so it automatically pulls the `rest` variant of `core/firebase` when building.

---

## Source Set Hierarchy

When building `devHuaweiDebug`, Kotlin sources resolve in this order (later overrides earlier):

```
commonMain
  └── androidMain
        └── androidHuawei       ← Huawei-only main code
              └── androidDevHuawei
                    └── androidDevHuaweiDebug
```

For unit tests:

```
commonTest
  └── androidUnitTest
        └── androidUnitTestHuawei
              └── androidUnitTestDevHuawei
```

---

## Where to Put New Code

| What | Where |
|------|-------|
| REST implementation of a Firebase interface | `composeApp/src/androidHuawei/kotlin/` |
| DI override (replaces SDK binding) | `composeApp/src/androidHuawei/kotlin/.../di/HuaweiAndroidModule.kt` |
| REST client / low-level REST utilities | `core/firebase/src/androidRest/kotlin/` |
| Huawei unit tests | `composeApp/src/androidUnitTestHuawei/kotlin/` |

---

## DI Override Mechanism

The `HuaweiAndroidModule` is loaded last by `initKoin`. Because Koin runs with
`allowOverride(true)`, any `single<Interface> { … }` here silently replaces the earlier
SDK binding registered in the standard android module.

```kotlin
fun huaweiAndroidModule() = module {
    includes(androidModule())
    // Override SDK bindings with REST implementations
    single<AuthApi> { RestAuthApi(storage = get(), http = get(), ...) }
    single<RemoteDataApi> { RestRemoteDataApi(get()) }
    // ... all Firebase API interfaces that need REST overrides
}
```

```rule
id: PLAT-MOB-HUAWEI-DI-01
statement: Always bind to the interface — never to the concrete class.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-HUAWEI-DI-01 — Always bind to the interface — never to the concrete class.
```

`single<ConcreteClass>` does not override the earlier `single<Interface>` binding and will cause a duplicate registration or silent miss.

---

## REST Implementation Layer (`core/firebase:androidRest`)

The REST layer lives in `core/firebase`'s `androidRest` source set. Typical classes:

| Role | Responsibility |
|------|---------------|
| `FirebaseAuthRestApi` | Email/password login, token caching, refresh, sign-out |
| `FirestoreRestClient` | CRUD + query + batch writes over Firestore REST API |

`FirestoreRestClient` is a concrete class. Tests instantiate it directly with a fake
HTTP executor — no mocking needed.

---

## Credentials

Credentials (project ID, API key) are resolved from `local.properties` at build time
and injected via Koin from a credentials holder class. Tests use hardcoded constants
(`PROJECT_ID = "test-project"`, `API_KEY = "test-api-key"`).

---

## Writing Huawei Unit Tests

- Place test files in `androidUnitTestHuawei` source set
- KSP/Mokkery does **not** process `androidUnitTestHuawei` — use manual fakes instead of `mock<T>()`
- Use an in-memory `FakeSharedPreferences` to pre-seed auth tokens for `FirebaseAuthRestApi`
- Stub HTTP with `FakeHttpRequestExecutor.stub(url, FakeApiResponse.success(json))`

```kotlin
private fun buildRestApi(http: FakeHttpRequestExecutor): MyRestApi {
    val prefs = FakeSharedPreferences()
    prefs.edit()
        .putString("firebase_id_token", "test_token")
        .putLong("firebase_token_expiry", Long.MAX_VALUE)
        .apply()
    val authApi = FirebaseAuthRestApi(http = http, projectId = PROJECT_ID, apiKey = API_KEY, prefs = prefs)
    val client = FirestoreRestClient(authApi = authApi, http = http, projectId = PROJECT_ID)
    return MyRestApi(client = client)
}
```

Standard Firestore REST URL patterns:
- GET doc: `https://firestore.googleapis.com/v1/projects/{project}/databases/(default)/documents/{path}`
- Query: `https://firestore.googleapis.com/v1/projects/{project}/databases/(default)/documents:runQuery`
- Batch write: `https://firestore.googleapis.com/v1/projects/{project}/databases/(default)/documents:batchWrite`

---

## Validation Checklist

When adding a new REST implementation:
- [ ] Interface defined in `commonMain`
- [ ] REST implementation placed in `androidHuawei` or `androidRest` (not `androidMain`)
- [ ] DI override binds to interface, not concrete class
- [ ] `HuaweiAndroidModule` includes `androidModule()` first
- [ ] No GMS / Firebase SDK imports in `androidRest` source set
- [ ] Unit test placed in `androidUnitTestHuawei`; uses manual fakes (no Mokkery)
- [ ] Google flavor unaffected — existing SDK binding still used
