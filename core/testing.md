---
id: CORE-TESTING
type: principle
layer: core
platform: [all]
architecture: [all]
requires: []
related: [CORE-DI, CORE-COUPLING]
tags: [testing, behaviour, unit-tests, mocking, fakes, coverage]
---

# Testing Philosophy

## Statement

Tests verify behaviour observable from the outside. They do not test implementation
details, verify code that cannot fail, or test what the framework already guarantees.

## Rationale

Tests that verify implementation details break every time the code is refactored,
even when behaviour is unchanged. They create refactor friction without catching
real regressions. Tests that verify observable behaviour survive refactors and
catch the failures that matter.

## In Practice

**Test observable behaviour, not internal mechanics**
- Assert on what the component produces given inputs
- Do not assert on the number of times an internal method was called
- Do not test private methods directly; test through the public interface

**Fakes for things you own; mocks for things you don't**
- Components you own (DataSources, repositories, services): use a fake implementation
  (in-memory, deterministic) rather than a mock that asserts on call counts
- External systems and third-party libraries you do not control: mock at the boundary

**Do not test the framework**
- Do not write tests to verify that Spring injects dependencies correctly
- Do not write tests to verify that Room writes to SQLite
- Test your logic, not your dependencies

**One reason to fail per test**
- Each test arranges one scenario, acts once, and asserts one outcome
- A test with multiple unrelated assertions is testing multiple things; split it

**What not to test**
- Pure data classes (no logic)
- DI wiring modules
- Generated code
- UI layout (structure); test UI behaviour instead

## Violations

- A test that breaks after an internal refactor with no change in external behaviour
- Mocking the class under test
- Asserting that `repository.save()` was called N times instead of asserting on
  the final state
- A test that passes with an empty implementation because it only verifies structure
