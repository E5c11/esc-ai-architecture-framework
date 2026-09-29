---
id: ORCH-PY-MODULARISE
type: orchestrator
layer: feature-orchestrators
platform: [python]
architecture: [python-app]
goal: "Split an oversized or tangled Python module into layered, cohesive modules without changing behavior"
requires: [CORE-COUPLING, CORE-TESTING, ARCH-PY, ARCH-PY-MODULES, ARCH-PY-ENTRYPOINT, ARCH-PY-USECASE, ARCH-PY-DOMAIN, ARCH-PY-COMPOSITION, PLAT-PY, PLAT-PY-IMPORT-LINTER, PLAT-PY-TESTING, QG-TESTING]
related: [ORCH-PY-USECASE, ORCH-PY-ENTRYPOINT, CORE-API-STABILITY, QG-REVIEW]
tags: [python, refactor, modularise, split, monolith, characterization]
status: active
---
# Modularise a Python Module (Python-App)

## Goal

Take a module that has grown to hold several concerns (rendering, prompting, operations,
wiring, more) and split it into the layered structure of `ARCH-PY`, **preserving
behavior exactly**. This is a refactor: no feature, fix, or renaming of public commands
rides along (`PYMOD-SPLIT-01`).

## Before you start

Read every document in `requires`. Measure first: line count of the module, number of
top-level functions, and which concerns it mixes. Write down the target layout before
moving anything. Work in small commits, each leaving the suite green.

---

## Phase 1 — Baseline

**Goal:** Current behavior is pinned so any change in behavior fails a test.

**Required framework docs:** `PLAT-PY-TESTING`, `ARCH-PY-MODULES`

**Assumes:** Nothing.
**Produces:** A passing baseline test run and characterization tests for uncovered
behavior; a recorded coverage figure for the module.
**Docs to update:** `None`.

### Steps

1. Run the full suite and record the result — this is the baseline that must stay green
2. Measure coverage of the module; identify public behavior with no test
3. Write **characterization tests** for that behavior: call it, record what it returns,
   prints, or writes, and assert exactly that (even if the behavior looks odd — fixing it
   is a separate change)
4. Record the module's public surface (what other modules and entrypoints import from it)
5. **Find out how the tests replace collaborators.** Search the tests for assignments and
   `patch(...)` calls on the module (`module.name = fake`, `patch("pkg.module.name")`). A name that
   is patched on a module is looked up in *that module's namespace*, so once the code that uses it
   moves, the patch silently stops working. List every patched name and which function looks it up
   — that list is the exact set of test edits Phase 4 will need (usually a few provider-status and
   AI-call seams, not the whole suite). Also list which existing functions are *not* as pure as
   their names suggest (a `render_*` that reads files; a `format_*` that runs git) — Phase 3 fixes those

### Validation

- [ ] The suite is green before any code moves
- [ ] Every behavior about to be moved is covered by a test
- [ ] The list of external importers of the module is written down
- [ ] The list of patched names (and the function that looks each one up) is written down

---

## Phase 2 — Target layout and contracts

**Goal:** The destination is decided and the architecture check can fail if it is violated.

**Required framework docs:** `PLAT-PY-IMPORT-LINTER`, `ARCH-PY`

**Assumes:** Phase 1.
**Produces:** A layout plan and `import-linter` contracts (initially expected to fail or
carry temporary, justified ignores).

### Steps

1. Classify each function/class in the module by layer: renderer (entrypoint, pure),
   rule/vocabulary (domain), operation (use case), storage/process (DataSource/Gateway),
   wiring (composition), glue (entrypoint handler)
2. Draft the target package layout (`domain/`, `application/`, `infrastructure/`,
   `entrypoints/`, `composition.py`)
3. Add the layer, independence, and purity contracts; any existing violation gets a
   *temporary* `ignore_imports` entry with a reason and a tracking note — to be removed
   by the end of this refactor

### Validation

- [ ] Every top-level definition has a destination layer
- [ ] Contracts exist and run; temporary ignores are enumerated

---

## Phase 3 — Extract the pure parts

**Goal:** Renderers, parsers, and rule tables live in their own modules.

**Required framework docs:** `ARCH-PY-ENTRYPOINT`, `ARCH-PY-DOMAIN`

**Assumes:** Phase 2.
**Produces:** Pure modules with the same behavior, imported by the original module.

### Steps

1. Move renderers (`render_*`) into `entrypoints/{surface}/render.py`; they take values
   and return strings
2. Move vocabularies and rule tables into `domain/`; keep completeness tests
3. Where a function both computes and prints, split it: a pure function returning the
   result, and a one-line caller that prints (`PYMOD-FUNC-01`)
4. After each move, leave a re-export in the old module so external imports keep working
   (`CORE-API-STABILITY`)
5. Run the suite after each move; commit each move separately
6. When a moved function's callers or tests replace a collaborator on the old module, retarget
   that patch to the module that now *looks the name up* (mechanical; assertions untouched) and say
   so in the commit message. Do this in the same commit as the move so every commit is green
7. A "renderer" that reads files, resolves registry routes, or runs a process is not pure: split it
   into an effectful gatherer in the application layer that returns a value and a pure formatter
   that takes it. This changes the function's signature — do it as its own step, updating callers and
   tests, and enforce it with a `forbidden` contract on the renderer module (`PYEP-RENDER-01`)

### Validation

- [ ] The suite is green after every commit (including any mechanical test retargeting)
- [ ] Moved functions are pure and covered by direct unit tests
- [ ] The old module re-exports what it used to define

---

## Phase 4 — Extract operations into use cases

**Goal:** Each operation is a use case behind ports; I/O is behind DataSources/Gateways.

**Required framework docs:** `ARCH-PY-USECASE`, `ARCH-PY-DATASOURCE`, `ARCH-PY-GATEWAY`

**Assumes:** Phase 3.
**Produces:** Use cases in `application/`, ports, infrastructure implementations, and
fakes for tests.

### Steps

1. For each operation, identify what it touches (store, process, filesystem, clock) and
   declare a Protocol per capability
2. Move the operation into a use case that receives those ports; strip any `print` /
   prompt / `sys.argv` (`PYUC-IO-01`)
3. Move the concrete storage/process code into `infrastructure/` implementing the ports.
   A port for a wide concrete class (a SQLite store) can be generated from the signatures of the
   methods the application layer actually calls, and a test can assert the concrete class still
   satisfies it (parameter names match) — annotation-only, so behavior cannot change
4. Where the old code asked a question mid-operation, introduce a `Prompter` port and a
   scripted fake; the interactive entrypoint supplies the terminal implementation
5. If an operation *constructs* its own infrastructure (a use case that does `Scheduler(store, ...)`
   or builds a provider runtime), that is composition-root work, not a type dependency. A
   behavior-preserving split cannot fix it without changing signatures (the handlers must receive an
   app/composition object). Record it as an explicit, justified `ignore_imports` entry naming the exact
   import, keep the contract blocking any *new* violation, and open a follow-up ticket
6. Keep the original function as a thin caller of the use case until every caller is
   migrated; add fakes and use-case tests as each operation moves

### Validation

- [ ] Each moved operation has use-case tests using fakes plus DataSource/Gateway tests
  against real infrastructure
- [ ] No moved code performs presentation I/O or reads ambient state
- [ ] The baseline and characterization tests still pass unchanged

---

## Phase 5 — Composition and thin entrypoints

**Goal:** One composition root wires everything; entrypoints only parse, call, and render.

**Required framework docs:** `ARCH-PY-COMPOSITION`, `ARCH-PY-ENTRYPOINT`

**Assumes:** Phase 4.
**Produces:** `composition.py`, `__main__.py`, and per-surface entrypoint packages.

### Steps

1. Create `build_app(settings)` constructing every DataSource/Gateway/use case; read
   configuration only in the `Settings` loader
2. Rewrite each command handler to receive the `App`, call one use case, and render
3. Turn the command dispatch into a registration table
4. Keep the original `main` importable (and the packaging entry point unchanged)

### Validation

- [ ] Only composition/tests construct infrastructure; entrypoints do not import it
- [ ] Every handler is under ~30 lines and contains no domain branching
- [ ] `main`'s behavior and exit codes are unchanged (characterization tests pass)

---

## Phase 6 — Close the loop

*Applying this to a flat library (a package of many top-level modules that other repositories import
as `pkg.module`) does not mean moving every module into layer packages, which would be churn across
a public API for no coupling benefit. Classify modules into groups, write contracts for the properties
that hold today, and add a test that fails when a new module is not classified*
(`PLAT-PY-IMPORT-LINTER`).

**Goal:** The split cannot silently erode.

**Required framework docs:** `PLAT-PY-IMPORT-LINTER`, `ARCH-PY-MODULES`

### Steps

1. Remove every temporary `ignore_imports` that can be removed; each one left MUST name its exact
   import and reason, and be tracked by a follow-up (`PYIL-NOBYPASS-01`)
2. Add the size check (`PYMOD-SIZE-01`) to CI, with the original module now small or
   deleted
3. Remove re-exports only if no external importer remains; otherwise keep them for one
   minor version and record the deprecation
4. Compare final coverage against the Phase 1 figure; it must not have dropped

### Validation

- [ ] `lint-imports`, `ruff`, type check, and the full suite pass with **no new** ignores (any remaining
  ignore is justified and tracked)
- [ ] No module exceeds the size limit without a justification
- [ ] Behavior is unchanged: baseline and characterization tests pass unmodified
- [ ] Coverage is at least the Phase 1 figure
