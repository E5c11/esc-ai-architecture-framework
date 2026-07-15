---
id: PLAT-LIB-KMP
type: guide
layer: platform
platform: [library]
architecture: [all]
requires: [CORE-API-STABILITY, BUILD-VERSION-CATALOG]
related: [PLAT-LIB-JS-EXPORT, PLAT-MOB-KMP-IOS]
tags: [kmp, library, maven-central, publication, variants, klib, apple]
---

# Kotlin Multiplatform Library Packaging

## Public dependency visibility

Use `api` only when a dependency's public types appear in exported signatures or the
consumer must receive its API transitively. Everything else is `implementation`.

**Rule PLAT-LIB-KMP-DEPS-01 (hard):** A dependency exposed by a public signature
MUST be declared as `api`; an implementation detail MUST be `implementation`.

## Target and publication set

The root multiplatform publication is metadata that points to target publications.
It is not a substitute for them.

**Rule PLAT-LIB-KMP-TARGET-01 (hard):** Every platform claimed as supported MUST
have an explicit Kotlin target and a published target artifact.

**Rule PLAT-LIB-KMP-APPLE-01 (hard):** Apple Silicon device and simulator support
requires both `iosArm64()` and `iosSimulatorArm64()`. Add `iosX64()` only when Intel
simulator support is an explicit product requirement.

**Rule PLAT-LIB-KMP-COORD-01 (hard):** Root Gradle metadata MUST reference the exact
artifact IDs produced by target publications. Renaming the root artifact without
checking target coordinates is prohibited.

**Rule PLAT-LIB-KMP-ATOMIC-01 (hard):** Root metadata, POMs, target modules, KLIBs,
sources and required checksums/signatures MUST be staged and released as one version.
Never promote a root publication whose advertised target artifact is missing.

Maven Central releases are immutable. Correct a broken release with a new version;
do not attempt to replace an existing coordinate.

## External consumer fixture

Maintain a separate fixture build that depends only on the staged/published coordinates.
For each supported target it must:

1. resolve the root module and target variant;
2. compile code that exercises representative public API;
3. link where the host supports linking;
4. fail if repositories fall back to JitPack, local publications or project substitution.

For Apple libraries, compile both Apple targets on macOS and link at least the simulator
target. When the library wraps Ktor, instantiate the client so engine wiring is tested,
not merely metadata resolution.

**Rule PLAT-LIB-KMP-FIXTURE-01 (hard):** Publication verification MUST run against
the staged repository from a clean external build before release promotion.

## Linux and macOS responsibilities

Keep the target model consistent on every host. Linux can configure Apple targets and
build common metadata, but Apple KLIB compilation/linking and Xcode integration are
validated on macOS. Do not require developers to comment targets in and out.

## Validation checklist

- [ ] Supported targets and target artifacts match.
- [ ] Apple device and Apple Silicon simulator variants both exist when iOS is supported.
- [ ] Root `.module` coordinates match uploaded target artifact IDs exactly.
- [ ] No advertised artifact returns missing/unauthorized during clean resolution.
- [ ] External consumer compiles representative API for every supported target.
- [ ] Apple simulator link passes on macOS.
- [ ] Release uses a new immutable version.

