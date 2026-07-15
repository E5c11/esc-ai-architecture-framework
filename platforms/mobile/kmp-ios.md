---
id: PLAT-MOB-KMP-IOS
type: guide
layer: platform
platform: [mobile]
architecture: [all]
requires: [PLAT-MOB-KMP, PLAT-MOB-KOIN, BUILD-CONVENTION-PLUGINS]
related: [BUILD-APPLE-CI, PLAT-MOB-IOS-INTEROP, QG-MOB-NATIVE]
tags: [kmp, ios, apple, kotlin-native, xcode, framework, source-sets]
---

# Kotlin Multiplatform — iOS Target and Application Integration

## Supported target model

For modern Apple Silicon development, configure `iosArm64()` for physical devices and
`iosSimulatorArm64()` for the simulator. Add `iosX64()` only when Intel simulator support
is an explicit requirement.

**Rule PLAT-MOB-IOS-TARGET-01 (hard):** Every shared module in the application dependency
graph MUST expose every Apple target consumed by the application framework.

**Rule PLAT-MOB-IOS-TARGET-02 (hard):** Apple targets MUST remain declared on Linux and
macOS. Host-specific task availability belongs in execution/CI selection, not source edits.

Linux can configure the target graph and build common metadata. Kotlin/Native Apple
compilation, framework linking, Xcode builds and signing are macOS responsibilities.

## Source-set hierarchy

Use the default hierarchy when it models the graph correctly:

```text
commonMain
└── nativeMain              portable Native clock/dispatcher/filesystem helpers
    └── iosMain             Apple APIs and platform DI
        ├── iosArm64Main
        └── iosSimulatorArm64Main
```

Custom shared source sets such as `restMain` must have deliberate `dependsOn` edges and
must not silently disconnect `iosMain` from its compilations.

**Rule PLAT-MOB-IOS-HIER-01 (hard):** A custom hierarchy MUST be verified by compiling
each Apple target and confirming its intended shared sources are included. Do not suppress
default-hierarchy warnings without documenting the replacement graph.

**Rule PLAT-MOB-IOS-ACTUAL-01 (hard):** An `actual` MUST live in the same Gradle module
as its `expect`. Application code cannot satisfy a feature module's `expect`.

Portable Native actuals belong in `nativeMain`; UIKit/Foundation/Security actuals belong
in `iosMain`.

## Framework binary

Configure the same framework base name for every Apple target. Swift imports that name,
so changing it is an integration change.

```kotlin
listOf(iosArm64(), iosSimulatorArm64()).forEach { target ->
    target.binaries.framework {
        baseName = "SharedApp"
        isStatic = true
    }
}
```

**Rule PLAT-MOB-IOS-FRAMEWORK-01 (hard):** Framework name, linkage and minimum iOS
version MUST be consistent between Gradle and Xcode configurations.

Use the Compose/KMP-generated embed-and-sign task from the Xcode build phase. Do not keep
stale framework search paths from renamed modules.

## Application bootstrap and Koin

The iOS controller must initialize shared infrastructure before composing the root UI.
Move the common module list into common code and append one `iosPlatformModule()` last.

**Rule PLAT-MOB-IOS-BOOT-01 (hard):** Koin MUST start exactly once before any Composable
resolves a dependency. Controller recreation must not start a second Koin application.

**Rule PLAT-MOB-IOS-DI-01 (hard):** Every interface consumed by common code MUST have an
iOS binding. A compile-only NoOp is allowed only when it reports the capability as unsupported
and the associated action is hidden or disabled.

Platform objects remain behind common interfaces. UIKit, Foundation, Security and StoreKit
types never enter UseCases, ViewModels or repository contracts.

## Xcode configuration

- Bundle identifiers contain the app identifier only; team IDs belong to signing settings.
- Keep personal signing/team overrides out of version control.
- Align deployment target, marketing version and build number with Gradle/release policy.
- Add entitlements and usage descriptions only for capabilities the binary uses.
- Remove obsolete device capabilities and stale framework paths.
- Simulator builds should support unsigned verification; archives use a secure signing context.

**Rule PLAT-MOB-IOS-XCODE-01 (hard):** Checked-in Xcode configuration MUST NOT contain
personal signing material, credentials or provisioning profiles.

## Compile-first capability policy

NoOps can establish a compilation baseline, but must never silently claim success. Keep a
support matrix for every deferred adapter. User-visible actions backed by a NoOp are hidden,
disabled or return an explicit unsupported result.

**Rule PLAT-MOB-IOS-NOOP-01 (hard):** A NoOp MUST NOT report successful completion for
an operation it did not perform.

## Validation ladder

Run in increasing cost order:

1. leaf-module `compileKotlinIosSimulatorArm64`;
2. application `compileKotlinIosSimulatorArm64`;
3. `linkDebugFrameworkIosSimulatorArm64`;
4. Xcode simulator build with signing disabled;
5. simulator launch and Koin resolution smoke test;
6. device build/archive in an authorized signing context.

## Validation checklist

- [ ] All shared modules expose the same Apple target set.
- [ ] Linux configuration does not require commenting Apple targets out.
- [ ] Every `expect` is satisfied in its own module.
- [ ] Custom source-set edges include `iosMain` as intended.
- [ ] Framework name/deployment target match Xcode.
- [ ] Koin starts once before composition and all common dependencies resolve.
- [ ] Deferred capabilities are explicit and not clickable false successes.
- [ ] Compile, link, Xcode build and launch checks pass on macOS.

