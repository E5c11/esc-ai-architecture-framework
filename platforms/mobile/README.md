# platforms/mobile/

Kotlin Multiplatform (KMP) / Compose / Koin implementation guides.

Documents here extend `architectures/pragmatic-clean/` with mobile-specific
tooling. They assume the reader has already loaded the relevant architecture layer.

## Tech stack covered

- Kotlin Multiplatform (commonMain / androidMain / iosMain / wasmJsMain)
- Jetpack Compose / Compose Multiplatform
- Koin (dependency injection)
- Kotlin Coroutines / Flow
- Room (local database)
- Ktor (networking)
- Firebase Android/KMP SDK
- Apple targets, Xcode framework integration, UIKit interop, OAuth and StoreKit

## Target-specific entry points

- `PLAT-MOB-KMP-IOS` — Apple target graph, framework/Xcode bootstrap and validation
- `PLAT-MOB-KMP-WEB` — Wasm/browser target structure and NoOp policy
- `ORCH-MOB-IOS` — dependency-to-archive iOS port sequence

## Document ID prefix: `PLAT-MOB-`
