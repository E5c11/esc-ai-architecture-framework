---
id: PLAT-PY-TESTING
type: guide
layer: platforms
platform: [python]
architecture: python-app
requires: [ARCH-PY, PLAT-PY, CORE-TESTING, QG-TESTING]
related: [PLAT-PY-DI, ARCH-PY-USECASE, ARCH-PY-DATASOURCE, ARCH-PY-GATEWAY, PLAT-PY-IMPORT-LINTER, QG-REVIEW]
tags: [pytest, testing, fakes, tmp_path, coverage, fixtures, characterization, parametrize]
status: active
---
# Testing in Python

Extends: `QG-TESTING`, `CORE-TESTING`

## Test layout mirrors the architecture

```
tests/
    domain/           pure unit tests — no fixtures beyond values
    application/      use cases against fakes of their ports
    infrastructure/   DataSources/Gateways against REAL storage/processes (tmp_path)
    entrypoints/      each surface given an App built from fakes; assert output/exit
    architecture/     import-linter and completeness checks (one test invokes lint-imports)
    fakes.py          in-memory implementations of the application's ports
```

Each layer's tests need only the layer below, which is what makes them fast and their
failures precise.

## Rules

```rule
id: PYTEST-RUNNER-01
statement: Tests MUST use `pytest`; test modules MUST be named `test_*.py` under `tests/` mirroring the source layout.
type: hard
scope: testing
enforced_by: [ci, reviewer]
violation_message: Violates PYTEST-RUNNER-01 — Tests MUST use `pytest`; test modules MUST be named `test_*.py` under `tests/` mirroring the source layout.
```

```rule
id: PYTEST-FAKE-01
statement: Each application port MUST have one in-memory fake maintained beside the tests and shared across them; use-case tests MUST use these fakes rather than per-test `Mock` objects asserting call counts.
type: hard
scope: testing
enforced_by: [reviewer]
violation_message: Violates PYTEST-FAKE-01 — Each application port MUST have one in-memory fake maintained beside the tests and shared across them; use-case tests MUST use these fakes rather than per-test `Mock` objects asserting call counts.
```

```rule
id: PYTEST-REAL-01
statement: DataSource and Gateway tests MUST run against real infrastructure — a temporary SQLite file, a `tmp_path` directory, a temporary git repository, a spawned trivial process — not against mocks of the library they wrap.
type: hard
scope: testing
enforced_by: [reviewer]
violation_message: Violates PYTEST-REAL-01 — DataSource and Gateway tests MUST run against real infrastructure — a temporary SQLite file, a `tmp_path` directory, a temporary git repository, a spawned trivial process — not against mocks of the library they wrap.
```

A mocked `sqlite3` connection proves the mock, not the SQL.

```rule
id: PYTEST-ISOLATE-01
statement: Tests MUST NOT touch the developer's real home directory, environment, network, or working copy; they MUST use `tmp_path`, `monkeypatch`, and explicit settings objects, and MUST be runnable in any order and in parallel.
type: hard
scope: testing
enforced_by: [ci, reviewer]
violation_message: Violates PYTEST-ISOLATE-01 — Tests MUST NOT touch the developer's real home directory, environment, network, or working copy; they MUST use `tmp_path`, `monkeypatch`, and explicit settings objects, and MUST be runnable in any order and in parallel.
```

```rule
id: PYTEST-CLOCK-01
statement: Tests MUST pin time and identifiers by passing a fixed `Clock`/`IdGenerator` fake; tests MUST NOT use `time.sleep` to wait for a result or assert on wall-clock durations.
type: hard
scope: testing
enforced_by: [reviewer]
violation_message: Violates PYTEST-CLOCK-01 — Tests MUST pin time and identifiers by passing a fixed `Clock`/`IdGenerator` fake; tests MUST NOT use `time.sleep` to wait for a result or assert on wall-clock durations.
```

```rule
id: PYTEST-TABLE-01
statement: Every rule table in the domain MUST have a completeness test parametrized over its vocabulary; behavior varying by settings MUST have one matrix test asserting the mandatory stage set is identical across all settings.
type: hard
scope: testing
enforced_by: [ci, reviewer]
violation_message: Violates PYTEST-TABLE-01 — Every rule table in the domain MUST have a completeness test parametrized over its vocabulary; behavior varying by settings MUST have one matrix test asserting the mandatory stage set is identical across all settings.
```

```rule
id: PYTEST-ARCH-01
statement: The suite MUST include a test (or CI step) that runs the import-linter contracts, so an architecture violation fails the same gate as a behavior regression.
type: hard
scope: testing
enforced_by: [ci, reviewer]
violation_message: Violates PYTEST-ARCH-01 — The suite MUST include a test (or CI step) that runs the import-linter contracts, so an architecture violation fails the same gate as a behavior regression.
```

## Idioms

- **Arrange the fixture, not the file system.** `tmp_path` gives a fresh directory;
  build the smallest repository/manifest the test needs with a small helper, not a
  copied fixture tree.
- **Parametrize over the vocabulary.** `@pytest.mark.parametrize("stage", ...)` beats a
  loop inside one test: each case reports separately.
- **Assert outcomes.** Assert on the returned value, the fake's recorded state, or the
  rendered output — not on internal calls.
- **Test the CLI as a function.** Call the entrypoint's `run(app, argv)` with a fake
  `App`, capture output with `capsys`, assert the exit status. Avoid spawning the
  installed command unless the test is about packaging.
- **Subtests for tables.** When a case list is data, generate cases from the data so a
  new entry is automatically covered.
- **Patching a module attribute couples a test to file layout.** `module.name = fake` (or
  `patch("pkg.module.name")`) replaces the name in *that module's namespace*; it only affects code that
  looks the name up there. It works until the code that uses `name` moves. Prefer injecting the
  collaborator (`PLAT-PY-DI`) so the test passes a fake to the constructor; where legacy tests
  already patch, retarget the patch to the module that now looks the name up when moving code.
- **Characterization tests before a refactor.** If a module lacks tests, first record
  its current observable behavior (`ORCH-PY-MODULARISE`), then change the structure.

## Coverage

Measure with `coverage.py` (`--branch`), enforce a threshold on the layers where it
matters (domain and application near-complete; infrastructure meaningful; entrypoints
covered by behavior tests). Coverage is a floor that catches untested code, not a
target to optimize: a covered line with no assertion protects nothing
(`QG-TESTING`).
