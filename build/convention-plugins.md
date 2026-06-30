---
id: BUILD-CONVENTION-PLUGINS
type: guide
layer: build
platform: [mobile, backend]
architecture: [all]
requires: []
related: [BUILD-PROJECT-STRUCTURE, BUILD-VERSION-CATALOG, BUILD-STATIC-ANALYSIS]
tags: [gradle, convention-plugins, build-logic, plugins, composability]
---

# Convention Plugins

## What they are

Convention plugins are Gradle plugins defined inside the project that encode
shared build configuration. Instead of copying the same `plugins {}`, `java {}`,
and `kotlin {}` blocks into every module's `build.gradle.kts`, you write the
configuration once as a plugin and apply it by ID.

```
// Without convention plugins — repeated in every module
plugins {
    id("org.jetbrains.kotlin.multiplatform")
    id("com.android.library")
    id("io.gitlab.arturbosch.detekt")
}
kotlin { /* same config every time */ }
java { sourceCompatibility = JavaVersion.VERSION_17 }

// With convention plugins — one line per module
plugins {
    id("myproject.kmp.feature")
}
```

## Why

- A JVM version change requires one edit in one plugin, not N edits across N modules
- Every module that applies the plugin automatically inherits future changes
- New modules start correctly configured with zero copy-paste

## Structure

```
build-logic/
├── settings.gradle.kts          Declares build-logic as an included build
└── convention/
    ├── build.gradle.kts         Plugin metadata: declares plugin IDs → implementation classes
    └── src/main/kotlin/
        ├── MyProjectKmpLibraryConventionPlugin.kt
        ├── MyProjectKmpFeatureConventionPlugin.kt
        └── ...
```

**Rule BUILD-CP-STRUCT-01 (hard):** Convention plugins MUST live in `build-logic/convention/`
and be declared as an included build via `includeBuild("build-logic")` in the root
`settings.gradle.kts`. Never place convention plugins inside the main build.

**Rule BUILD-CP-STRUCT-02 (hard):** Each convention plugin MUST be a Kotlin class
implementing `Plugin<Project>`. All build configuration logic lives inside `apply()`.

## Plugin registration

Each plugin must be registered in `build-logic/convention/build.gradle.kts` with a
stable ID and its implementation class:

```kotlin
gradlePlugin {
    plugins {
        register("myprojectKmpFeature") {
            id = "myproject.kmp.feature"
            implementationClass = "MyProjectKmpFeatureConventionPlugin"
        }
    }
}
```

**Rule BUILD-CP-REG-01 (hard):** Plugin IDs MUST use reverse-domain dot notation:
`{project}.{platform}.{purpose}`. Examples: `ampm.kmp.feature`, `ampm.backend.module`.

**Rule BUILD-CP-REG-02 (hard):** Each plugin ID MUST map to exactly one implementation
class. The class name mirrors the ID in PascalCase.

## Plugin hierarchy

Convention plugins compose via `pluginManager.apply()`. Build a hierarchy
from general to specific — never duplicate configuration.

```
myproject.kmp.library           KMP + Android library baseline
  └── myproject.kmp.compose.library    + Compose compiler
        └── myproject.kmp.feature      + feature-specific deps (DI, lifecycle)
              └── myproject.kmp.room   + Room + KSP (added alongside feature)
```

**Rule BUILD-CP-HIER-01 (soft):** Convention plugins SHOULD compose via
`pluginManager.apply("parent.plugin.id")` rather than duplicating parent configuration.

**Rule BUILD-CP-HIER-02 (hard):** Shared tool configuration (static analysis,
JVM target, compiler options) MUST live in a base plugin and be inherited.
Never configure the same tool in multiple sibling plugins.

## Version catalog in convention plugins

Access the version catalog inside a convention plugin via a `libs` extension
function on `Project`. Reference library and version aliases rather than
hardcoding version strings.

**Rule BUILD-CP-DEPS-01 (hard):** Convention plugin dependencies declared in
`build-logic/convention/build.gradle.kts` MUST use `compileOnly()` for Gradle
plugin APIs. They are provided by the Gradle runtime; declaring them as
`implementation` causes classpath conflicts.

## JVM target

**Rule BUILD-CP-JVM-01 (hard):** JVM target version MUST be declared once in
the `build-logic/convention/build.gradle.kts` `kotlin {}` block and replicated
consistently in every convention plugin that configures JVM compilation.
Never declare different JVM targets in different modules.

## Violations

- Build configuration copy-pasted across module `build.gradle.kts` files
- Convention plugin placed inside a feature module rather than `build-logic/`
- Plugin ID using underscores or camelCase instead of dot notation
- Same Detekt or JVM config duplicated in multiple convention plugins
- Gradle plugin API declared as `implementation` instead of `compileOnly`
