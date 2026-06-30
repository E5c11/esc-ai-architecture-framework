---
id: PLAT-MOB-KMP-WEB
type: guide
layer: platform
platform: [mobile]
architecture: [pragmatic-clean]
requires: [PLAT-MOB-KMP, PLAT-MOB-KOIN, PLAT-MOB-FIREBASE]
related: [PLAT-MOB-HUAWEI, PLAT-MOB-DS-IMAGES, PLAT-MOB-NOTIF]
tags: [kmp, wasmjs, web, compose-multiplatform, noop, source-sets, keyvaluestorage, uuid, rest]
---

# KMP Web Target (wasmJs / Compose Multiplatform)

## Stack

| Concern | Android | Web (wasmJs) |
|---------|---------|--------------|
| UI | Compose (Android) | Compose Multiplatform (Wasm/Canvas) |
| HTTP | Ktor + OkHttp | Ktor + JS Fetch (`ktor-client-js`) |
| Firebase | SDK (Google) or REST (HMS) | REST only — no Firebase SDK |
| Image loading | Coil 3 + `coil-network-okhttp` | Coil 3 + `coil-network-ktor` |
| Local storage | Room + DataStore + SharedPreferences | `localStorage` via `KeyValueStorage` |
| Offline / file system | Supported | Not supported — NoOp implementations |
| Auth (Google) | Platform credential flow | Not supported — NoOp |
| Entry point | `MainActivity` | `main.kt` → `ComposeViewport` |

---

## Source Set Rules

### Golden rule

**Rule PLAT-MOB-KMP-WEB-SS-01 (hard):** `commonMain` is the home for ALL business logic.
No use cases, repositories, or domain models live in `wasmJsMain`. `wasmJsMain` is a thin
wiring layer only.

### Source set hierarchy for Firebase REST

```
commonMain           ← interfaces (Firebase*Api)
    └── restMain     ← REST implementations (FirestoreRestClient, RestFirebase*Api)
         ├── androidRest   ← SharedPreferences KeyValueStorage wiring
         └── wasmJsMain    ← localStorage KeyValueStorage wiring
```

**Rule PLAT-MOB-KMP-WEB-SS-02 (hard):** NEVER add Android imports to `restMain`. The
`restMain` source set must compile for both Android and wasmJs. Anything importing
`android.*` or `SharedPreferences` directly does NOT belong in `restMain`.

### What lives where

| Code | Source set |
|------|-----------|
| Firebase API interfaces | `commonMain` |
| Firebase REST implementations | `restMain` |
| `KeyValueStorage` interface | `commonMain` (or `restMain`) |
| `SharedPreferencesKeyValueStorage` | `androidRest` |
| `LocalStorageKeyValueStorage` | `wasmJsMain` |
| Koin module for web Firebase | `wasmJsMain` |
| App entry point | `wasmJsMain/main.kt` |
| NoOp implementations (downloads, OS features) | `wasmJsMain` |
| Screens, ViewModels, UseCases | `commonMain` |

---

## `KeyValueStorage` — Mandatory Rule

`SharedPreferences` is Android-only and MUST NOT appear in `restMain`. All token and
credential persistence in the REST layer goes through `KeyValueStorage`:

```kotlin
// commonMain (or restMain)
interface KeyValueStorage {
    fun getString(key: String): String?
    fun getLong(key: String, default: Long = 0L): Long
    fun putString(key: String, value: String)
    fun putLong(key: String, value: Long)
    fun remove(key: String)
}

// androidRest — uses SharedPreferences
class SharedPreferencesKeyValueStorage(
    private val prefs: SharedPreferences
) : KeyValueStorage { ... }

// wasmJsMain — uses browser localStorage
class LocalStorageKeyValueStorage : KeyValueStorage { ... }
```

`KeyValueStorage` is constructed directly in platform Koin modules and passed into the
REST auth API — it is NOT registered as a Koin binding itself.

---

## UUID Rule

**Rule PLAT-MOB-KMP-WEB-UUID-01 (hard):** NEVER use `java.util.UUID`. It is JVM-only
and will not compile for wasmJs.

```kotlin
// ❌ Wrong
val id = java.util.UUID.randomUUID().toString()

// ✅ Correct
@OptIn(ExperimentalUuidApi::class)
val id = Uuid.random().toString()
```

This applies everywhere — `commonMain`, `restMain`, `androidRest`, anywhere shared with web.

---

## Image Loading

`coil-network-okhttp` is JVM/Android only. The web target requires a Ktor engine:

```kotlin
// build.gradle.kts
androidMain {
    dependencies { implementation(libs.coil.network.okhttp) }
}
wasmJsMain {
    dependencies { implementation(libs.coil.network.ktor) }
}
```

No code changes needed in components — Coil 3 detects the engine automatically.

---

## NoOp Pattern for Unsupported Features

Features that depend on the file system, Room, or platform OS APIs are not available
on web. Provide NoOp implementations registered in the `wasmJsMain` Koin module:

```kotlin
// wasmJsMain — WebNoOpModule.kt
fun webNoOpModule() = module {
    // File system / offline features
    single<LocalFileResolver> { NoOpLocalFileResolver() }
    factory(named(DIQualifiers.CAN_DOWNLOAD)) {
        UseCase<Unit, Boolean> { false }
    }
    factory(named(DIQualifiers.DO_DOWNLOAD)) {
        UseCaseAsync<DownloadParams, Unit> { /* no-op */ }
    }
    // Notifications
    single<NotificationScheduler> { NoOpNotificationScheduler() }
    // Analytics / crash reporting (if not supported on web)
    single<CrashReporter> { NoOpCrashReporter() }
}
```

**Rule PLAT-MOB-KMP-WEB-NOOP-01 (hard):** Every `androidMain`-only Koin registration
MUST have a corresponding `wasmJsMain` NoOp so Koin can resolve all bindings on web.

---

## `expect`/`actual` for Platform UI

Pure Compose composables require no `expect`/`actual` — they compile for all targets.

Use `expect`/`actual` ONLY when the composable must interop with a native platform API:

| Component | Reason |
|-----------|--------|
| Platform video player | Android uses a WebView-based player; web needs a DOM element overlay |
| Google Sign-In launcher | Android uses `CredentialManager`; web is NoOp |

For a NoOp web `actual`:
```kotlin
@Composable
actual fun rememberGoogleSignInLauncher(): suspend () -> String? = {
    error("Google Sign-In is not supported on web")
}
```
Ensure the NoOp actual is never called by conditionally hiding the UI entry point on web.

---

## Koin Module for `wasmJsMain`

```kotlin
// wasmJsMain — WebFirebaseModule.kt
fun webFirebaseModule() = module {
    single {
        FirebaseAuthRestApi(
            http = get(),
            projectId = WebBuildConfig.FIREBASE_PROJECT_ID,
            apiKey = WebBuildConfig.FIREBASE_API_KEY,
            storage = LocalStorageKeyValueStorage(),
        )
    }
    single<FirebaseAuthApi> { get<FirebaseAuthRestApi>() }
    single { FirestoreRestClient(authApi = get(), http = get(), projectId = ...) }
    // ... all REST Firebase API registrations
}
```

Credentials live in a `wasmJsMain` build config object — Firebase project IDs and API
keys are safe to expose client-side (they are visible in the browser regardless).

---

## App Entry Point

```kotlin
// wasmJsMain/main.kt
fun main() {
    startKoin {
        modules(
            httpModule(),
            webFirebaseModule(),
            webNoOpModule(),
            commonModule(),
            // ... all feature modules
        )
    }

    ComposeViewport(document.body!!) {
        App()
    }
}
```

---

## Validation Checklist

Before committing any web-related change:
- [ ] No `java.util.UUID` in `commonMain`, `restMain`, or `wasmJsMain`
- [ ] No `android.*` imports in `restMain` source files
- [ ] No `SharedPreferences` in `restMain` — only `KeyValueStorage`
- [ ] `coil-network-okhttp` is NOT on the `wasmJs` compile classpath
- [ ] Every `androidMain`-only Koin binding has a `wasmJsMain` NoOp counterpart
- [ ] `./gradlew :composeApp:wasmJsBrowserDistribution` builds without errors
- [ ] New `expect` declarations have both `androidMain` and `wasmJsMain` actuals
