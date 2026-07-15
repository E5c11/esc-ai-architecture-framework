---
id: ORCH-MOB-IOS
type: orchestrator
layer: feature-orchestrators
platform: [mobile]
architecture: [pragmatic-clean]
goal: "Port an existing KMP mobile application to iOS from published dependencies through release validation"
requires:
  - CORE-API-STABILITY
  - ARCH-PC-ERR-CLASSES
  - PLAT-LIB-KMP
  - PLAT-MOB-KMP-IOS
  - PLAT-MOB-HTTP
  - PLAT-MOB-FIREBASE
  - PLAT-MOB-ROOM
  - PLAT-MOB-SECURE-STORAGE
  - PLAT-MOB-IOS-INTEROP
  - PLAT-MOB-IOS-AUTH
  - PLAT-MOB-IOS-BILLING
  - PLAT-MOB-NOTIF
  - BUILD-APPLE-CI
  - QG-MOB-NATIVE
related: [ORCH-MOB-FEAT, QG-REVIEW]
tags: [mobile, kmp, ios, apple, port, xcode, release]
---

# Port an Existing KMP Application to iOS

## Phase 1 — Published dependency readiness

**Required framework docs:** `CORE-API-STABILITY`, `PLAT-LIB-KMP`
**Code paths:** Owned KMP library target/publication configuration and external fixtures
**Assumes:** The application's dependency graph and supported Apple architectures are known
**Produces:** Consumable Apple variants for every published dependency

- Add device and Apple Silicon simulator variants.
- Publish root metadata and all referenced target artifacts atomically.
- Compile/link representative API from a clean staged-repository consumer.

## Phase 2 — Application target graph and Xcode shell

**Required framework docs:** `PLAT-MOB-KMP`, `PLAT-MOB-KMP-IOS`, `BUILD-CONVENTION-PLUGINS`, `BUILD-PROJECT-STRUCTURE`
**Code paths:** Convention plugins, module build files, app framework configuration, Xcode project
**Assumes:** Phase 1 complete
**Produces:** Consistent Apple targets through the module graph and a valid Xcode framework integration

- Add Apple targets centrally and keep them declared on Linux.
- Verify source-set hierarchy, framework name and deployment target.
- Correct bundle identity, search paths and unsigned simulator settings.

## Phase 3 — Actuals, platform DI and launch

**Required framework docs:** `PLAT-MOB-KMP-IOS`, `PLAT-MOB-KOIN`, `PLAT-MOB-KOTLIN`
**Code paths:** `nativeMain`, `iosMain`, common Koin bootstrap, iOS entry point
**Assumes:** Phase 2 compiles far enough to enumerate missing actuals
**Produces:** Linked framework and simulator app that launches without DI failure

- Implement portable Native primitives and thin Apple adapters in their owning modules.
- Provide explicit compile-first adapters for deferred capabilities.
- Start Koin exactly once before root composition and smoke-test the graph.

## Phase 4 — Functional network and persistence

**Required framework docs:** `PLAT-MOB-HTTP`, `PLAT-MOB-FIREBASE`, `PLAT-MOB-ROOM`, `PLAT-MOB-DATASTORE`, `PLAT-MOB-SECURE-STORAGE`, `ARCH-PC-DATASOURCE`, `CORE-SSOT`
**Code paths:** REST/native provider source sets, iOS storage/database builders and platform DI
**Assumes:** Phase 3 launches
**Produces:** Authenticated remote access and durable local state for the core flow

- Choose and document native-SDK versus REST provider strategy.
- Configure Darwin transport, Keychain tokens and Native database/preferences paths.
- Prove repository SSOT and restart/offline behavior.

## Phase 5 — Native user integrations

**Required framework docs:** `PLAT-MOB-IOS-INTEROP`, `PLAT-MOB-IOS-AUTH`, `PLAT-MOB-IOS-BILLING`, `PLAT-MOB-NOTIF`, `ARCH-PC-DATASOURCE`, `ARCH-PC-USECASE`
**Code paths:** Apple platform adapters, entitlements/plist, platform DI and affected common layers
**Assumes:** Phase 4 core flow works
**Produces:** Selected release integrations with explicit permission/cancel/error behavior

- Implement only approved release capabilities; hide deliberately deferred actions.
- Keep Apple SDK objects behind platform/DataSource boundaries.
- Test success, cancellation, denial, recovery and lifecycle behavior.

## Phase 6 — Native tests, CI and archive

**Required framework docs:** `QG-MOB-NATIVE`, `BUILD-APPLE-CI`, `QG-REVIEW`, `BUILD-STATIC-ANALYSIS`, `BUILD-COVERAGE`
**Code paths:** Native tests, macOS CI, Xcode/release configuration and documentation
**Assumes:** Phases 1–5 complete
**Produces:** Automated simulator proof and an authorized archive process

- Run Native unit/integration tests and the compile/link/Xcode ladder.
- Keep signing secrets in protected release context.
- Review every NoOp/deferred capability before declaring release readiness.

