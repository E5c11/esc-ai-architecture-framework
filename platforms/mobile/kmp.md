---
id: PLAT-MOB-KMP
type: platform
layer: platform
platform: [mobile]
architecture: [all]
requires: [CORE-DI]
related: [PLAT-MOB-KOIN, PLAT-MOB-KOTLIN]
tags: [kmp, kotlin-multiplatform, source-sets, expect-actual, wasm, ios, android]
---

# Kotlin Multiplatform — Source Set Structure

## Overview

KMP projects share business logic across platforms via `commonMain`. Platform-specific
code lives in source sets that are only compiled for their target. The source set
hierarchy determines what each target can see and use.

## Source Set Responsibilities

| Source set | Purpose |
|---|---|
| `commonMain` | All business logic, architecture layers, domain models. No platform APIs. |
| `androidMain` | Android-specific implementations: Context-dependent code, Android SDKs |
| `iosMain` | iOS-specific implementations: UIKit bridges, iOS SDKs |
| `wasmJsMain` | Web-specific implementations: browser APIs, JS interop |
| `commonTest` | All unit tests that do not require a platform runtime |

**Rule PLAT-MOB-KMP-SS-01 (hard):** Business logic, UseCases, Repositories, DataSources,
and ViewModels MUST live in `commonMain`. No exceptions.

**Rule PLAT-MOB-KMP-SS-02 (hard):** `commonMain` code MUST NOT import any platform SDK.
No `android.*`, no `UIKit`, no browser globals.

## expect / actual

Use `expect`/`actual` to declare a common contract that each platform fulfils.

```
commonMain:    expect fun platformName(): String
androidMain:   actual fun platformName(): String = "Android"
iosMain:       actual fun platformName(): String = "iOS"
wasmJsMain:    actual fun platformName(): String = "Web"
```

**Rule PLAT-MOB-KMP-EA-01 (hard):** `expect` declarations MUST be placed in `commonMain`.
**Rule PLAT-MOB-KMP-EA-02 (hard):** Every `expect` MUST have an `actual` in every
compiled target. Missing actuals are a compile error — do not suppress.

## Platform DI modules

Platform-specific Koin bindings live in platform modules registered at startup.

**Rule PLAT-MOB-KMP-DI-01 (hard):** Platform-specific dependencies (Context, platform
SDKs) MUST be declared in their respective platform DI module, not in `commonMain` modules.

**Rule PLAT-MOB-KMP-DI-02 (soft):** Platform modules SHOULD use `includes()` to
compose feature-level platform sub-modules.

## wasmJs (web target)

The web target runs in the browser via WebAssembly. Android-specific Koin registrations
are not available. Every interface injected by `commonMain` code must have a
registration on the web target — either a real implementation or a NoOp.

**Rule PLAT-MOB-KMP-WEB-01 (hard):** Every `androidMain`-only Koin registration for
an interface consumed by `commonMain` MUST have a corresponding `wasmJsMain` registration.
If no real implementation exists, provide a NoOp that satisfies the interface contract.

**Rule PLAT-MOB-KMP-WEB-02 (hard):** Firebase credentials for the web target MUST
be stored in a `wasmJsMain`-only `WebBuildConfig` object. Never in `commonMain`
or resource files.

**Rule PLAT-MOB-KMP-WEB-03 (hard):** The `wasmJsMain` entry point MUST include
all required platform modules in `startKoin` before rendering the composition.
Missing modules cause runtime "No definition found" crashes in the browser.

## Violations

- `commonMain` class importing `android.content.Context`
- An `expect` declaration with no `actual` in a compiled target
- Firebase or device API calls placed directly in `commonMain`
- Android-only Koin registration with no web counterpart for an interface used in `commonMain`
