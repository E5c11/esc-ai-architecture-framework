---
id: ORCH-PY-USECASE
type: orchestrator
layer: feature-orchestrators
platform: [python]
architecture: [python-app]
goal: "Implement one complete operation across all python-app layers, wired and tested inward to outward"
requires: [CORE-DI, CORE-ERROR, CORE-TESTING, PAT-DATA-ACCESS, ARCH-PY, ARCH-PY-DOMAIN, ARCH-PY-USECASE, ARCH-PY-DATASOURCE, ARCH-PY-GATEWAY, ARCH-PY-COMPOSITION, ARCH-PY-ERROR, PLAT-PY, PLAT-PY-TYPING, PLAT-PY-DI, PLAT-PY-TESTING, QG-TESTING]
related: [ORCH-PY-ENTRYPOINT, ORCH-PY-ADAPTER, PLAT-PY-PERSISTENCE, PLAT-PY-IMPORT-LINTER, QG-REVIEW]
tags: [python, use-case, end-to-end, layers, scaffold]
---
# Implement a Python Operation (Python-App)

## Goal

Produce one complete, tested operation: domain values and rules → ports → use case →
DataSource/Gateway → composition wiring. Each layer is implemented inward to outward
(`ARCH-PY`, "Execution order"). The operation is *not* reachable from any surface yet —
adding a CLI command, MCP tool, or route is `ORCH-PY-ENTRYPOINT`.

## Before you start

Read every document in `requires`. Confirm the project already has an enforced layer
contract (`PLAT-PY-IMPORT-LINTER`); if it does not, add it first — a new operation
built without the contract is the start of the drift this architecture prevents.

---

## Phase 1 — Domain

**Goal:** The values and rules the operation needs exist, are immutable, and are tested.

**Required framework docs:** `ARCH-PY-DOMAIN`, `PLAT-PY-TYPING`

**Assumes:** Nothing.
**Produces:** Frozen value types, enums for closed vocabularies, pure rule functions or a
rule table, each with unit tests.
**Docs to update:** the project's domain glossary, or `None` if no new term appears.

### Steps

1. Name the operation as a verb phrase in domain language (`ApplyPlan`, not `PlanHelper`)
2. Define the input and output values as `@dataclass(frozen=True, slots=True)`;
   put invariants in `__post_init__`
3. Represent any closed set of choices as an `Enum`/`Literal`
4. Write the decision logic as pure functions taking values (and a time/id as arguments,
   never reading them)
5. If behavior varies per vocabulary member, use a table plus a completeness test
   (`PYDOM-TABLE-01/02`)

### Validation

- [ ] No import of I/O, framework, or outer-layer modules in `domain/` (contract passes)
- [ ] No `datetime.now()`, `uuid4()`, `random`, `os.environ` in domain code
- [ ] Every value is frozen; collections are tuples/frozen mappings
- [ ] Domain tests need no fixtures beyond plain values and run in milliseconds

---

## Phase 2 — Ports

**Goal:** Everything the use case needs from the outside is declared as a narrow Protocol.

**Required framework docs:** `ARCH-PY-USECASE`, `PLAT-PY-DI`

**Assumes:** Phase 1 values exist.
**Produces:** `Protocol` classes in `application/ports.py` and a matching in-memory fake
for each, beside the tests.

### Steps

1. List the outside capabilities the operation needs (load a draft, save a result,
   run a process, read the clock)
2. Declare one narrow Protocol per capability, named for intent, returning domain values
3. Add `Clock`/`IdGenerator` ports if the operation needs time or identifiers
4. Write the in-memory fake for each new port (deterministic, no I/O)

### Validation

- [ ] Ports mention no storage or provider technology
- [ ] Each port is minimal for its consumer (`PYDI-NARROW-01`)
- [ ] Every new port has a fake shared by tests (`PYTEST-FAKE-01`)

---

## Phase 3 — Use case

**Goal:** The operation is implemented against the ports and fully tested with fakes.

**Required framework docs:** `ARCH-PY-USECASE`, `ARCH-PY-ERROR`

**Assumes:** Phases 1–2.
**Produces:** One class (or function) with one public entry point and unit tests.

### Steps

1. Create the use case in `application/`, with ports as constructor fields
2. Implement the operation by calling domain functions and ports in order
3. Return domain values or a frozen outcome value for an expected failure branch
4. Raise a typed `AppError` subclass for a known error; let unexpected errors propagate
5. If it performs several writes, do them in one unit of work (`PYUC-UOW-01`)
6. If it is a staged procedure, add it to the procedure table and use the generic
   runner rather than a bespoke sequence (`PYUC-STAGE-01`)

### Validation

- [ ] No `print`, `input`, `sys.argv`, `os.environ`, or clock reads in the use case
- [ ] No import from `infrastructure/` or `entrypoints/` (contract passes)
- [ ] Tests cover the happy path, each `AppError`, and each outcome branch, using fakes
- [ ] Every gate stage decides from observable results (`PYUC-STAGE-02`)

---

## Phase 4 — DataSource / Gateway

**Goal:** The real implementations of the new ports exist and are tested against real
infrastructure.

**Required framework docs:** `ARCH-PY-DATASOURCE`, `ARCH-PY-GATEWAY`, `PLAT-PY-PERSISTENCE`, `PLAT-PY-SUBPROCESS`

**Assumes:** Phase 2 ports exist.
**Produces:** DataSource/Gateway classes in `infrastructure/` and integration tests.

### Steps

1. Implement each port in `infrastructure/datasources/` or `infrastructure/gateways/`
2. For persistence: add a numbered migration; map rows with one `_to_domain` function
3. Translate storage/provider exceptions into `AppError` subclasses using `raise ... from`
4. For a process/provider: go through the single runner; set timeout, `cwd`, and env
   allow-list; return exit status as data
5. Test against a `tmp_path` database/file or a temporary git repository

### Validation

- [ ] Methods return domain values only (`PYDS-RETURN-01`)
- [ ] No SQL outside the DataSource; all SQL parameterized
- [ ] A migration exists and an old-schema and a newer-schema test pass
- [ ] Every external call has a timeout; no `shell=True`

---

## Phase 5 — Composition

**Goal:** The operation is constructible from the composition root and nowhere else.

**Required framework docs:** `ARCH-PY-COMPOSITION`, `PLAT-PY-DI`

**Assumes:** Phases 3–4.
**Produces:** One added entry in `build_app`.

### Steps

1. Construct the DataSource/Gateway and the use case in `composition.build_app`
2. Expose the use case on the `App` value the entrypoints receive
3. If configuration is needed, add a field to `Settings` (read once); do not read the
   environment anywhere else

### Validation

- [ ] Only `composition.py` and tests instantiate the new infrastructure classes
- [ ] The use case is reachable through `App`; nothing imports the composition module
  except `__main__`

---

## Phase 6 — Architecture and quality gate

**Goal:** The change conforms mechanically, not by inspection.

**Required framework docs:** `PLAT-PY-IMPORT-LINTER`, `QG-TESTING`

### Steps

1. Run `lint-imports`; every contract passes with no new `ignore_imports`
2. Run `ruff check` and the strict type check
3. Run the full test suite; confirm the new layers' tests exist under
   `tests/{layer}/`

### Validation

- [ ] `lint-imports`, `ruff`, type check, and tests all pass
- [ ] No contract was weakened (`PYIL-NOBYPASS-01`)
- [ ] The operation is reachable by tests through the use case, and by no surface yet
