---
id: BUILD-COVERAGE
type: guide
layer: build
platform: [mobile, backend]
architecture: [all]
requires: [BUILD-CONVENTION-PLUGINS, BUILD-PROJECT-STRUCTURE]
related: [BUILD-STATIC-ANALYSIS, QG-TESTING]
tags: [coverage, kover, jacoco, thresholds, exclusions, quality-gate]
---

# Code Coverage

## Purpose

Coverage gates enforce that new code has tests. A per-module minimum threshold
fails the build when a module's measurable coverage drops below the floor.
The gate catches untested code at submission time, not during production incidents.

## Coverage tool

Platform-specific:
- **Kotlin/KMP (mobile, backend):** Kover — native Kotlin coverage, understands
  `inline` functions and multiplatform source sets correctly
- **Java:** JaCoCo

```rule
id: BUILD-COV-TOOL-01
statement: KMP/Kotlin projects SHOULD use Kover.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates BUILD-COV-TOOL-01 — KMP/Kotlin projects SHOULD use Kover.
```

JaCoCo does not handle Kotlin `inline` functions correctly and may over- or under-report coverage for multiplatform modules.

## Per-module threshold

Each module declares its own minimum coverage bound. New modules start at a lower
threshold and raise it once the initial test suite is stable.

```rule
id: BUILD-COV-THRESH-01
statement: Every module with testable code MUST declare a coverage verification rule with a minimum bound.
type: hard
scope: testing
enforced_by: [reviewer]
violation_message: Violates BUILD-COV-THRESH-01 — Every module with testable code MUST declare a coverage verification rule with a minimum bound.
```

```rule
id: BUILD-COV-THRESH-02
statement: New modules SHOULD start at 80% and raise to 85% once the initial test suite is complete and coverage is stable.
type: soft
scope: testing
enforced_by: [reviewer]
violation_message: Violates BUILD-COV-THRESH-02 — New modules SHOULD start at 80% and raise to 85% once the initial test suite is complete and coverage is stable.
```

```rule
id: BUILD-COV-THRESH-03
statement: Never lower a module's threshold once it is established.
type: hard
scope: testing
enforced_by: [reviewer]
violation_message: Violates BUILD-COV-THRESH-03 — Never lower a module's threshold once it is established.
```

If coverage drops, write the missing tests.

## Aggregate report

The root app module merges per-module coverage data into a single aggregate
report. The aggregate threshold is enforced alongside per-module thresholds.

```rule
id: BUILD-COV-AGG-01
statement: Every module with production code MUST be included in the aggregate coverage merge.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates BUILD-COV-AGG-01 — Every module with production code MUST be included in the aggregate coverage merge.
```

A module omitted from the merge contributes zero to the aggregate denominator, inflating the aggregate percentage.

## Standard exclusions

Generated code, pure data classes, and DI wiring carry no testable logic.
Excluding them prevents the threshold from rewarding developers for writing
non-testable code.

### Always exclude

| Pattern | Reason |
|---|---|
| Composable-annotated functions | UI layout is not unit-testable |
| `**.di.*` packages | DI module wiring — no logic |
| `**.*Mapper`, `**.*MapperKt` | Pure data transformation — no branching |
| `**.*State`, `**.*StateKt` | Data holders — no logic |
| `**.*Exception`, `**.*ExceptionKt` | Exception class declarations — no logic |
| `**.*_Impl`, `**.*_Impl$*` | Generated (Room, Compose compiler) |
| `**.navigation.*` | Navigation route declarations |
| Generated resource accessors | Compose Multiplatform generated code |

```rule
id: BUILD-COV-EXCL-01
statement: Standard exclusions MUST be applied consistently in every module.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates BUILD-COV-EXCL-01 — Standard exclusions MUST be applied consistently in every module.
```

Never include generated or logic-free code in the coverage denominator — it distorts the threshold and creates incentives to add boilerplate.

```rule
id: BUILD-COV-EXCL-02
statement: Module-specific exclusions (e.g. platform SDK wrappers that require a device to test) MUST be declared explicitly in that module's Kover configuration with a comment explaining why they are excluded.
type: hard
scope: testing
enforced_by: [reviewer]
violation_message: Violates BUILD-COV-EXCL-02 — Module-specific exclusions (e.g. platform SDK wrappers that require a device to test) MUST be declared explicitly in that module's Kover configuration with a comment explaining why they are excluded.
```

## Running coverage

```bash
./gradlew koverVerify              # Verify all module thresholds
./gradlew koverHtmlReport          # Generate HTML report
./gradlew :{module}:koverVerify    # Verify a single module
```

```rule
id: BUILD-COV-CI-01
statement: Coverage verification MUST run in CI on every merge request.
type: hard
scope: testing
enforced_by: [reviewer]
violation_message: Violates BUILD-COV-CI-01 — Coverage verification MUST run in CI on every merge request.
```

A build that passes unit tests but fails `koverVerify` MUST NOT be merged.

## What coverage does NOT measure

Coverage shows which lines were executed during tests. It does not measure:
- Whether tests are meaningful (a test with no assertions passes coverage)
- Whether edge cases are covered
- Integration behaviour

A 100% coverage number with trivial tests is worse than 75% coverage with
thorough behavioural tests. Coverage is a floor, not a goal.

Kover reports commonly measure JVM executions and may not represent Kotlin/Native simulator
tests. Keep the aggregate JVM gate, but report Native test execution separately and do not
describe platform adapters as covered unless the tool actually records them.

**Rule BUILD-COV-NATIVE-01 (hard):** Coverage reporting MUST disclose when Native code is
outside the measured engine and MUST pair that limitation with explicit Native behavioral tests.

## Violations

- Module with testable business logic missing a coverage verification rule
- Module excluded from the aggregate merge
- Lowering a module threshold to make the build pass
- Standard exclusions missing from a module, including generated code in the denominator
- Coverage gate not running in CI
- Claiming Native adapter coverage from a JVM-only coverage report
