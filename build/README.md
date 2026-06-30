# build/

Gradle build system patterns that span JVM/Kotlin projects.

These documents apply to both mobile and backend projects. They are loaded
when a project profile declares `build.system: gradle`.

## What goes here

- Convention plugin patterns and structure
- Multi-module project organisation
- Coverage setup (Kover)
- Static analysis (Detekt)
- Dependency management (version catalogs)
- Build variant / flavour patterns

## What does NOT go here

- Android-specific build config (→ `platforms/mobile/`)
- Spring Boot application config (→ `platforms/backend/`)

## Document ID prefix: `BUILD-`
