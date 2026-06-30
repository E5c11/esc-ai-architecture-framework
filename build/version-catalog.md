---
id: BUILD-VERSION-CATALOG
type: guide
layer: build
platform: [mobile, backend]
architecture: [all]
requires: [BUILD-PROJECT-STRUCTURE]
related: [BUILD-CONVENTION-PLUGINS]
tags: [gradle, version-catalog, libs-versions-toml, dependencies, versions]
---

# Version Catalog

## What it is

A version catalog (`gradle/libs.versions.toml`) is the single source of truth
for all dependency versions and coordinates in a multi-module project. Every
module references dependencies by alias rather than by coordinate string.

```toml
# gradle/libs.versions.toml
[versions]
kotlin = "2.0.21"
koin   = "4.0.0"

[libraries]
koin-core    = { module = "io.insert-koin:koin-core",    version.ref = "koin" }
koin-compose = { module = "io.insert-koin:koin-compose", version.ref = "koin" }

[plugins]
kotlin-multiplatform = { id = "org.jetbrains.kotlin.multiplatform", version.ref = "kotlin" }
```

```kotlin
// In any module's build.gradle.kts
implementation(libs.koin.core)
```

## Why

- Upgrading a library requires changing one version string in one file
- The Gradle build fails to compile if an alias does not exist, catching typos at build time
- All modules are guaranteed to use the same version of the same library

## File location

**Rule BUILD-VC-LOC-01 (hard):** The version catalog MUST be at `gradle/libs.versions.toml`.
Gradle resolves this path automatically; no explicit registration is needed.

## Alias naming

**Rule BUILD-VC-ALIAS-01 (hard):** Library aliases MUST use kebab-case and follow
the pattern `{group}-{artifact}`. Hyphens in the TOML become dots in Kotlin:
`koin-core` → `libs.koin.core`.

**Rule BUILD-VC-ALIAS-02 (hard):** Version aliases MUST use kebab-case and be
named after the library or library group they govern: `kotlin`, `koin`, `spring-boot`.
Never use generic names (`version1`, `v2`).

**Rule BUILD-VC-ALIAS-03 (soft):** Plugin aliases SHOULD mirror the library alias
for the same project: `kotlinx-serialization` (library) and `kotlinx-serialization`
(plugin) both reference the same version.

## Version references

**Rule BUILD-VC-VER-01 (hard):** Library entries MUST reference a version alias
via `version.ref` rather than inlining the version string. Inline versions defeat
the purpose of a catalog — the version appears in two places and will drift.

```toml
# ✅ Correct
koin-core = { module = "io.insert-koin:koin-core", version.ref = "koin" }

# ❌ Wrong — version inlined, not shared
koin-core = { module = "io.insert-koin:koin-core", version = "4.0.0" }
```

Exception: BOMs and platform dependencies that declare their own version management
may omit `version.ref`.

## Plugin aliases

Plugins declared in the catalog are applied in `build.gradle.kts` with `alias()`:

```kotlin
plugins {
    alias(libs.plugins.kotlin.multiplatform)
}
```

**Rule BUILD-VC-PLUGIN-01 (hard):** Gradle plugin application MUST use `alias(libs.plugins.*)`.
Never hardcode plugin IDs with version strings in module build files.

Exception: Convention plugin IDs (defined in `build-logic/`) are applied with `id()`
because they are not declared in the version catalog.

## Convention plugin dependencies

Convention plugin `build.gradle.kts` accesses the catalog via the `libs` extension.
Gradle plugin APIs used only during the build process are declared `compileOnly`.

**Rule BUILD-VC-CP-01 (hard):** Convention plugins MUST declare Gradle plugin API
dependencies as `compileOnly(libs.*)`. They are provided by the Gradle runtime
and must not be bundled.

## Adding a new dependency

1. Add the version to `[versions]` if not already present
2. Add the library entry to `[libraries]` using `version.ref`
3. Add a plugin entry to `[plugins]` if it has a Gradle plugin
4. Reference the alias in the module `build.gradle.kts`

**Rule BUILD-VC-ADD-01 (hard):** Dependencies MUST NOT be added as raw coordinate
strings in module `build.gradle.kts`. Every dependency goes through the catalog.

## Violations

- `implementation("io.insert-koin:koin-core:4.0.0")` in a module build file
- Version inlined in a library entry instead of using `version.ref`
- Two aliases for the same library with different versions causing version conflicts
- Plugin applied with `id("org.jetbrains.kotlin.multiplatform") version "2.0.21"` instead of `alias()`
