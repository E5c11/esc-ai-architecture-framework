---
id: BUILD-PROJECT-STRUCTURE
type: guide
layer: build
platform: [mobile, backend]
architecture: [all]
requires: [BUILD-CONVENTION-PLUGINS]
related: [BUILD-VERSION-CATALOG]
tags: [gradle, multi-module, settings, project-structure, modules, typesafe-accessors]
---

# Multi-Module Project Structure

## Layout

```
root/
├── build-logic/                 Included build for convention plugins
│   ├── settings.gradle.kts
│   └── convention/
│       ├── build.gradle.kts
│       └── src/main/kotlin/
├── core/                        Shared infrastructure modules
│   ├── common/
│   ├── network/
│   └── ...
├── feature/                     (mobile) Feature modules
│   ├── auth/
│   ├── profile/
│   └── ...
├── {domain}/                    (backend) Domain modules at root level
│   └── auth/
├── gradle/
│   └── libs.versions.toml       Version catalog
├── settings.gradle.kts          Module registration
└── build.gradle.kts             Root build file (minimal)
```

## settings.gradle.kts

The root `settings.gradle.kts` is the authoritative list of all modules. It:
- Declares the project name
- Registers the build-logic included build
- Configures repository resolution
- Includes all project modules

**Rule BUILD-PS-SETTINGS-01 (hard):** `build-logic` MUST be registered as an
included build in `pluginManagement { includeBuild("build-logic") }`. This
makes convention plugin IDs resolvable before the main build is evaluated.

**Rule BUILD-PS-SETTINGS-02 (hard):** Repository declarations belong in
`dependencyResolutionManagement { repositories { } }` in `settings.gradle.kts`,
not in individual module `build.gradle.kts` files.

## Module registration

**Rule BUILD-PS-REG-01 (hard):** Every module MUST be registered with `include()`
in `settings.gradle.kts`. A module directory that exists but is not included is
silently ignored by Gradle — it will not compile and will not appear in the build.

**Rule BUILD-PS-REG-02 (soft):** Module registrations SHOULD be kept in
alphabetical order within each group (`core:` before `feature:`). Alphabetical
order makes it easy to verify at a glance that a new module was registered.

**Rule BUILD-PS-REG-03 (hard):** Module path format uses colon-separated segments:
`:core:common`, `:feature:auth`. Never use directory path syntax.

## Typesafe project accessors

Enable `TYPESAFE_PROJECT_ACCESSORS` in `settings.gradle.kts` to reference modules
as type-safe Kotlin properties instead of string paths.

```kotlin
// Without typesafe accessors (error-prone)
implementation(project(":core:common"))

// With typesafe accessors (compile-time safe)
implementation(projects.core.common)
```

**Rule BUILD-PS-ACCESSOR-01 (soft):** Projects SHOULD enable typesafe project
accessors via `enableFeaturePreview("TYPESAFE_PROJECT_ACCESSORS")`. The accessor
name is derived from the module path — renaming a module produces a compile error
rather than a silent runtime failure.

## Root build.gradle.kts

The root `build.gradle.kts` is minimal. It applies only project-wide configuration
that cannot live in a convention plugin (e.g. `allprojects` tasks, root-level
plugin declarations needed for subproject resolution).

**Rule BUILD-PS-ROOT-01 (soft):** The root `build.gradle.kts` SHOULD contain as
little as possible. Module-specific configuration belongs in the module's own
`build.gradle.kts`. Shared tool configuration belongs in a convention plugin.

## Module build.gradle.kts

Each module's `build.gradle.kts`:
1. Applies the appropriate convention plugin(s)
2. Declares module-specific dependencies
3. Adds module-specific overrides only (e.g. coverage threshold, extra source sets)

**Rule BUILD-PS-MODULE-01 (hard):** Modules MUST apply a convention plugin rather
than re-declaring the full plugin list. One line per concern.

**Rule BUILD-PS-MODULE-02 (hard):** Module `build.gradle.kts` files MUST NOT
override JVM target, compiler options, or shared tool configuration. Those belong
in convention plugins.

## KMP target graph

An application target can consume only project dependencies that publish a compatible
variant. Adding iOS requires every transitive shared module to expose the same target,
normally through the convention plugin.

**Rule BUILD-PS-KMP-GRAPH-01 (hard):** Before enabling an application target, enumerate
its complete project dependency graph and ensure every shared module exposes a compatible
variant. Fix the graph bottom-up rather than adding ad-hoc module exceptions.

Custom source sets (`nativeMain`, `restMain`) must have a documented ownership/`dependsOn`
diagram when they replace the default hierarchy.

## Module naming

**Rule BUILD-PS-NAME-01 (hard):** Module directory names MUST be lowercase
and hyphen-separated. The Gradle path uses colons: `:feature:user-profile`.

**Rule BUILD-PS-NAME-02 (soft):** Core infrastructure modules SHOULD be grouped
under `:core:`. Feature modules under `:feature:` (mobile) or at root domain level
(backend). Avoid flat structures once the project exceeds three modules.

## Violations

- Module directory exists but is not registered in `settings.gradle.kts`
- Repository declarations in individual module `build.gradle.kts`
- `build-logic` not declared as an included build, requiring plugin IDs to be resolved externally
- Full plugin and compiler configuration duplicated in a module instead of using a convention plugin
- Application Apple target enabled while a transitive project module has no Apple variant
- Module names using camelCase or underscores
