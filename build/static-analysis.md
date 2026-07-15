---
id: BUILD-STATIC-ANALYSIS
type: guide
layer: build
platform: [mobile, backend]
architecture: [all]
requires: [BUILD-CONVENTION-PLUGINS]
related: [BUILD-COVERAGE, QG-TESTING]
tags: [detekt, static-analysis, linting, code-quality, baseline]
---

# Static Analysis — Detekt

## What it is

Detekt is a static analysis tool for Kotlin that enforces code style, complexity
limits, and common error patterns at build time. It runs on every module and
fails the build on violations.

## Configuration structure

```
root/
├── config/
│   └── detekt/
│       └── detekt.yml       Single shared ruleset for all modules
├── feature/auth/
│   └── detekt-baseline.xml  Per-module baseline (pre-existing violations)
└── feature/profile/
    └── detekt-baseline.xml
```

**Rule BUILD-SA-CONFIG-01 (hard):** There MUST be exactly one shared `detekt.yml`
at the root of the project. All modules use the same ruleset. Per-module configs
that override rules undermine consistency.

**Rule BUILD-SA-CONFIG-02 (hard):** The path to the shared config MUST be set in
the Detekt convention plugin, not in individual modules. Modules must not re-declare
or override the config path.

```kotlin
// In the Detekt convention plugin
extensions.configure(DetektExtension::class.java) {
    config.setFrom(rootProject.file("config/detekt/detekt.yml"))
    baseline = file("$projectDir/detekt-baseline.xml")
}
```

## Baselines

A baseline file records pre-existing violations that existed when Detekt was first
introduced to a module. Baseline violations are suppressed so they do not block
the build, but any new violation added after the baseline was created is still
caught.

**Rule BUILD-SA-BASELINE-01 (hard):** Baselines are per-module files
(`detekt-baseline.xml`). Never use a single shared baseline — it hides new
violations in modules that were already clean.

**Rule BUILD-SA-BASELINE-02 (soft):** Baseline files SHOULD be committed to
version control. They represent a snapshot of accepted technical debt at a point
in time and allow new developers to run Detekt without encountering pre-existing failures.

**Rule BUILD-SA-BASELINE-03 (soft):** Baseline entries SHOULD be reduced over
time. When fixing a violation, remove it from the baseline rather than leaving
a stale suppression.

## Convention plugin wiring

Detekt is applied via a convention plugin that every module inherits, not declared
individually per module.

**Rule BUILD-SA-PLUGIN-01 (hard):** Detekt MUST be applied via a convention plugin
that sets the shared config path. Never apply the Detekt Gradle plugin directly
in a module build file without wiring it to the shared config.

## Running Detekt

```bash
./gradlew detekt              # Run across all modules
./gradlew :feature:auth:detekt  # Run on a single module
```

The build MUST pass `detekt` with zero new violations before merging. Baseline
violations do not count as failures.

For KMP, configure analysis inputs to include portable and platform source sets, including
`nativeMain`/`iosMain` where supported by the selected task strategy. A root task that
silently analyzes Android/JVM sources only is not whole-project evidence.

**Rule BUILD-SA-KMP-01 (hard):** Static-analysis configuration MUST enumerate or otherwise
prove coverage of every maintained source set; new Native source sets cannot be omitted.

## What Detekt checks (examples)

- Complexity: function length, class length, cyclomatic complexity
- Style: formatting, naming conventions, unused imports
- Potential bugs: `!!` (non-null assertion), `equals()` without `hashCode()`, shadowed variables
- Performance: inefficient collection operators

The specific rules enabled are defined in `config/detekt/detekt.yml`.

## Violations

- Running `detekt` and suppressing failures with `--continue` instead of fixing them
- Adding a `@Suppress("Detekt.RuleName")` annotation without also creating a baseline entry
- Modifying `detekt.yml` in a single module to disable rules for that module only
- Not committing `detekt-baseline.xml` files, causing Detekt to fail for new contributors
- Adding `iosMain` while the configured analysis inputs still cover Android/JVM only
