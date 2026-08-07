---
id: PLAT-LIB-KMP
type: guide
layer: platform
platform: [library]
architecture: [all]
requires: [CORE-API-STABILITY, PLAT-MOB-KMP, BUILD-VERSION-CATALOG]
related: [PLAT-LIB-JS-EXPORT, PLAT-MOB-KMP-IOS]
tags: [kmp, kotlin-multiplatform, publishing, maven-central, api-visibility, gradle, versioning, variants, klib, apple]
status: active
---

# Publishing a Kotlin Multiplatform Library

## Overview

Building KMP code that ships *inside an app* and building KMP code that ships *as a
dependency other repos consume* use the same language features (`expect`/`actual`, source
sets — see `PLAT-MOB-KMP` for those, still authoritative) but have a different concern on
top: every public declaration is now a contract with an external consumer (`CORE-API-
STABILITY`), and the build itself needs to produce and publish artifacts, not just compile
for a single app's targets.

Reference implementation: `arrow-http` (`io.github.blackarrows-apps:http-core` /
`:http-ktor`), a real published multi-module KMP library. Examples below are drawn from its
actual build configuration, not hypothetical.

## `api` vs `implementation` — public surface visibility

Gradle's `api`/`implementation` distinction controls whether a dependency's types are
exposed to *your* consumers' compile classpath, or stay purely internal to your module.

```rule
id: PLAT-LIB-KMP-VIS-01
statement: If a type from dependency X appears in any public function signature, constructor parameter, or public property type of your module, X MUST be declared `api`, not `implementation`.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates PLAT-LIB-KMP-VIS-01 — If a type from dependency X appears in any public function signature, constructor parameter, or public property type of your module, X MUST be declared `api`, not `implementation`.
```

Otherwise consumers get an "unresolved reference" on a type they never explicitly depended on, with no clear reason why.

```rule
id: PLAT-LIB-KMP-VIS-02
statement: If a dependency is used only internally — never appearing in a public signature — declare it `implementation`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-LIB-KMP-VIS-02 — If a dependency is used only internally — never appearing in a public signature — declare it `implementation`.
```

This keeps it out of consumers' transitive compile classpath, so upgrading it doesn't force a rebuild of every downstream consumer and doesn't leak an implementation choice as an accidental public contract.

**Worked example (`arrow-http`):** `http-ktor`'s `build.gradle.kts` declares:

```kotlin
commonMain {
    dependencies {
        api(project(":http-core"))                        // ← api: KtorHttpRequestExecutor
                                                            //   implements http-core's
                                                            //   HttpRequestExecutor — that
                                                            //   type is part of every
                                                            //   consumer's public surface.
        implementation(libs.ktor.client.core)              // ← implementation: deliberate.
    }
}
```

This looks inconsistent at first glance — `KtorHttpRequestExecutor`'s constructor takes a
Ktor `HttpClient` as a parameter, which *is* a public signature, so shouldn't `ktor-client-
core` be `api` too? In practice, no: the intended consumption path is through DI (the
library's own Koin module constructs the `HttpClient` internally), so most consumers never
touch the `HttpClient` type directly. The few that use the documented "Manual Setup" path
(constructing `KtorHttpRequestExecutor` by hand) are expected to add their own explicit
`ktor-client-core` dependency — confirmed by real consumer code: `AMPM/core/backend/
build.gradle.kts` declares `implementation(libs.ktor.client.core)` itself, alongside `libs.
arrow.http.ktor`, specifically to get `HttpClient`/`HttpMethod` visible for its own direct
Ktor usage (see that file's comment on why it needs the PATCH-bypass workaround). This is a
legitimate, deliberate choice: keep the common path (DI, never touching `HttpClient`
directly) free of an implicit Ktor coupling, and let the uncommon path opt in explicitly.

```rule
id: PLAT-LIB-KMP-VIS-03
statement: When a visibility choice is intentionally non-obvious (like the example above), leave a comment explaining why — the next person reading the build file (including a future version of yourself) will otherwise "fix" it into a `NoSuchMethodError` for someone's existing manual-setup code.
type: soft
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-LIB-KMP-VIS-03 — When a visibility choice is intentionally non-obvious (like the example above), leave a comment explaining why — the next person reading the build file (including a future version of yourself) will otherwise "fix" it into a `NoSuchMethodError` for someone's existing manual-setup code.
```

## Maven Central publishing

Each publishable module needs its own `mavenPublishing { }` block (Vanniktech's
`com.vanniktech.maven.publish` plugin is the de facto standard for KMP → Maven Central):

```kotlin
group = "io.github.<your-namespace>"
version = "1.2.0"

mavenPublishing {
    coordinates("io.github.<your-namespace>", "<module-name>", "1.2.0")
    pom {
        name.set("...")
        description.set("...")
        url.set("https://github.com/<org>/<repo>")
        licenses { license { name.set("The Apache License, Version 2.0"); url.set("...") } }
        developers { developer { id.set("..."); name.set("..."); url.set("...") } }
        scm { connection.set("scm:git:..."); developerConnection.set("scm:git:ssh:...") ; url.set("...") }
    }
    publishToMavenCentral(com.vanniktech.maven.publish.SonatypeHost.CENTRAL_PORTAL)
    signAllPublications()
}
```

```rule
id: PLAT-LIB-KMP-VER-01
statement: `version` is declared per-module (each module's own `build.gradle.kts`), not centralized in one place — but every module in the same logical release MUST be bumped together, even ones with no code change, if they're expected to be consumed as a matched set.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-LIB-KMP-VER-01 — `version` is declared per-module (each module's own `build.gradle.kts`), not centralized in one place — but every module in the same logical release MUST be bumped together, even ones with no code change, if they're expected to be consumed as a matched set.
```

Publishing `http-ktor:1.2.0` against `http-core:1.1.1` (unbumped) works technically but signals to consumers that nothing in `http-core` changed, which is only true if that's actually the case — verify, don't assume, before skipping a module's bump.

```rule
id: PLAT-LIB-KMP-PUB-01
statement: `signAllPublications()` requires a GPG signing key and Sonatype credentials that are local to the publishing machine, never committed to the repo.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-LIB-KMP-PUB-01 — `signAllPublications()` requires a GPG signing key and Sonatype credentials that are local to the publishing machine, never committed to the repo.
```

The actual `publishAndReleaseToMavenCentral` (or equivalent) task execution is a manual, credentialed step — not something an agent or CI-without-secrets should run unprompted. See `CORE-API-STABILITY` for what should already be true (version bumped correctly, public surface reviewed) before this step is reached.

## Testing across every published target

```rule
id: PLAT-LIB-KMP-TEST-01
statement: `commonTest` runs across every declared target by default — adding a new target (e.g. a `js` target, see `PLAT-LIB-JS-EXPORT`) means the existing test suite needs to be confirmed green on that target too, not just compiled.
type: hard
scope: testing
enforced_by: [reviewer]
violation_message: Violates PLAT-LIB-KMP-TEST-01 — `commonTest` runs across every declared target by default — adding a new target (e.g. a `js` target, see `PLAT-LIB-JS-EXPORT`) means the existing test suite needs to be confirmed green on that target too, not just compiled.
```

A target that compiles but has never actually run its test suite is unverified, not supported.

## Target and publication set

The root multiplatform publication is metadata that points to target publications.
It is not a substitute for them.

```rule
id: PLAT-LIB-KMP-TARGET-01
statement: Every platform claimed as supported MUST have an explicit Kotlin target and a published target artifact.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-LIB-KMP-TARGET-01 — Every platform claimed as supported MUST have an explicit Kotlin target and a published target artifact.
```

```rule
id: PLAT-LIB-KMP-APPLE-01
statement: Apple Silicon device and simulator support requires both `iosArm64()` and `iosSimulatorArm64()`.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-LIB-KMP-APPLE-01 — Apple Silicon device and simulator support requires both `iosArm64()` and `iosSimulatorArm64()`.
```

Add `iosX64()` only when Intel simulator support is an explicit product requirement.

```rule
id: PLAT-LIB-KMP-COORD-01
statement: Root Gradle metadata MUST reference the exact artifact IDs produced by target publications.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-LIB-KMP-COORD-01 — Root Gradle metadata MUST reference the exact artifact IDs produced by target publications.
```

Renaming the root artifact without checking target coordinates is prohibited.

```rule
id: PLAT-LIB-KMP-ATOMIC-01
statement: Root metadata, POMs, target modules, KLIBs, sources and required checksums/signatures MUST be staged and released as one version.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-LIB-KMP-ATOMIC-01 — Root metadata, POMs, target modules, KLIBs, sources and required checksums/signatures MUST be staged and released as one version.
```

Never promote a root publication whose advertised target artifact is missing. Maven
Central releases are immutable. Correct a broken release with a new version; do not
attempt to replace an existing coordinate.

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

```rule
id: PLAT-LIB-KMP-FIXTURE-01
statement: Publication verification MUST run against the staged repository from a clean external build before release promotion.
type: hard
scope: testing
enforced_by: [reviewer]
violation_message: Violates PLAT-LIB-KMP-FIXTURE-01 — Publication verification MUST run against the staged repository from a clean external build before release promotion.
```

## Linux and macOS responsibilities

Keep the target model consistent on every host. Linux can configure Apple targets and
build common metadata, but Apple KLIB compilation/linking and Xcode integration are
validated on macOS. Do not require developers to comment targets in and out.

## Validation Checklist

Before publishing any version bump:
- [ ] Every dependency whose type appears in a public signature is `api`, not `implementation`
- [ ] Every module in the release is bumped to the same version (or the mismatch is deliberate and documented)
- [ ] `CORE-API-STABILITY`'s rules applied to every public surface change since the last release
- [ ] `commonTest` passes on every declared target, including any newly added this release
- [ ] Publishing (signing, Sonatype credentials) is a manual, confirmed step — never automated without explicit sign-off
- [ ] Supported targets and target artifacts match; Apple device and Apple Silicon
      simulator variants both exist when iOS is supported
- [ ] Root `.module` coordinates match uploaded target artifact IDs exactly, and no
      advertised artifact returns missing/unauthorized during clean resolution
- [ ] External consumer fixture compiles representative API for every supported target;
      Apple simulator link passes on macOS
- [ ] Release uses a new immutable version
