---
id: BUILD-APPLE-CI
type: guide
layer: build
platform: [mobile, build]
architecture: [all]
requires: [BUILD-CONVENTION-PLUGINS, BUILD-PROJECT-STRUCTURE, PLAT-MOB-KMP-IOS]
related: [BUILD-STATIC-ANALYSIS, BUILD-COVERAGE, QG-MOB-NATIVE]
tags: [ci, macos, ios, xcodebuild, kotlin-native, signing]
---

# Apple Build and CI

## Host responsibilities

Keep common Android/Wasm verification on Linux. Add a macOS job for Apple compilation,
linking and Xcode integration; do not append Apple tasks to an Ubuntu job.

**Rule BUILD-APPLE-HOST-01 (hard):** Any claim that iOS builds MUST be backed by a macOS
CI job. Metadata/configuration success on Linux is not an iOS build.

## Required macOS ladder

A baseline pull-request job should run:

```bash
./gradlew :composeApp:compileKotlinIosSimulatorArm64
./gradlew :composeApp:linkDebugFrameworkIosSimulatorArm64
xcodebuild \
  -project iosApp/iosApp.xcodeproj \
  -scheme iosApp \
  -configuration Debug \
  -sdk iphonesimulator \
  CODE_SIGNING_ALLOWED=NO \
  build
```

Adjust module/scheme names to the project, but retain all three proof levels. Add selected
`iosSimulatorArm64Test` tasks after native tests are stable.

**Rule BUILD-APPLE-LADDER-01 (hard):** CI MUST distinguish Kotlin compilation,
framework linking and Xcode application build. Passing an earlier level does not substitute
for a later one.

## Signing and secrets

Pull-request simulator jobs remain unsigned. Device/archive jobs run only in a protected
release context with certificates/profiles stored in the CI secret facility.

**Rule BUILD-APPLE-SIGN-01 (hard):** Fork/untrusted pull-request jobs MUST NOT receive
Apple signing identities, provisioning profiles or App Store credentials.

## Caching and diagnostics

Cache Gradle and Kotlin/Native downloads using keys that include wrapper, catalog and
relevant build scripts. Do not cache keychains, signed outputs or provisioning profiles.
Upload useful build logs/test results on failure while redacting credentials and tokens.

## Validation checklist

- [ ] macOS job compiles and links the Apple Silicon simulator framework.
- [ ] Xcode simulator build runs with signing disabled.
- [ ] Linux jobs contain no Apple link/Xcode task.
- [ ] Native tests are added selectively and their reports retained.
- [ ] Signing secrets are restricted to protected release jobs.
- [ ] Cache keys invalidate on toolchain/build configuration changes.

