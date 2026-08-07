---
id: QG-MOB-NATIVE
type: guide
layer: quality
platform: [mobile]
architecture: [all]
requires: [QG-TESTING, PLAT-MOB-KMP-IOS]
related: [BUILD-APPLE-CI, BUILD-COVERAGE]
tags: [testing, kotlin-native, ios, simulator, xcode, integration]
status: active
---

# Mobile Native and iOS Testing

## Test layers

Common tests prove portable logic. Native target tests prove Kotlin/Native compilation and
platform-neutral actuals. Simulator integration tests prove Apple frameworks, filesystem,
database, Keychain and platform DI. An Xcode launch smoke test proves final app integration.

**Rule QG-MOB-NATIVE-LAYER-01 (hard):** Common tests MUST NOT be used as evidence that an
Apple engine, database driver, Keychain adapter, framework link or Xcode app works.

## Required baseline

- Compile common/native test sources for both configured Apple targets.
- Run selected `iosSimulatorArm64Test` suites on macOS.
- Construct and resolve the complete iOS Koin graph.
- Exercise real platform adapters that can safely run in the simulator.
- Build and launch the Xcode simulator application.

Device-only capabilities are tested on protected physical-device/release infrastructure or
recorded as a manual release gate; simulator absence is not converted into a passing NoOp.

## Isolation and secrets

Use temporary application-owned paths and dedicated test service/account identifiers. Clean
database/files/Keychain state after each test. Tests must never log credentials or use live
production billing/auth accounts.

**Rule QG-MOB-NATIVE-ISOLATION-01 (hard):** Native integration tests MUST isolate and
clean persistent state so order/retry does not change results.

## Coverage

Kover/JVM coverage may not include executed Kotlin/Native code. Report that limitation
explicitly and retain behavioral Native test results; never claim uncovered Native adapters
are covered because common interfaces were exercised on JVM.

## Validation checklist

- [ ] Apple test compilations and selected simulator tests pass on macOS.
- [ ] iOS Koin graph resolution test covers every common platform dependency.
- [ ] Darwin client, database recreation/migration and Keychain lifecycle tests pass.
- [ ] Xcode simulator app builds and launches.
- [ ] Persistent test state is isolated and cleaned.
- [ ] Device-only manual gates are documented and not represented as automated passes.

