---
id: ORCH-PY-ENTRYPOINT
type: orchestrator
layer: feature-orchestrators
platform: [python]
architecture: [python-app]
goal: "Expose an existing use case on a delivery surface (CLI command, MCP tool, or HTTP route) without adding logic"
requires: [CORE-API-STABILITY, CORE-TESTING, ARCH-PY, ARCH-PY-ENTRYPOINT, ARCH-PY-ERROR, ARCH-PY-POLICY, ARCH-PY-COMPOSITION, PLAT-PY, PLAT-PY-CLI, PLAT-PY-MCP, PLAT-PY-HTTP, PLAT-PY-TESTING, QG-TESTING]
related: [ORCH-PY-USECASE, PLAT-PY-IMPORT-LINTER, PLAT-PY-PACKAGING, QG-REVIEW]
tags: [python, entrypoint, cli, mcp, http, surface, front-door]
---
# Add a Python Entrypoint (Python-App)

## Goal

Make an existing use case reachable from one delivery surface — a CLI command or intent
verb, an MCP tool, an HTTP route — as a thin translation layer. If the use case does not
exist yet, run `ORCH-PY-USECASE` first: an entrypoint must never be the place logic is
first written.

## Before you start

Read every document in `requires`. Decide the surface(s); do them one at a time, each as
its own phase below. Confirm the operation you are exposing is the *same* use case other
surfaces call (`PYEP-USECASE-01`).

---

## Phase 1 — Public contract

**Goal:** The name, inputs, outputs, and errors of the new entry are decided before any code.

**Required framework docs:** `ARCH-PY-ENTRYPOINT`, `CORE-API-STABILITY`

**Assumes:** The use case exists and is composed into `App`.
**Produces:** A short written contract: name, arguments (types), result shape, error →
status mapping.
**Docs to update:** the command/tool/route reference and the exit-status table if it
changes.

### Steps

1. Choose the name from the existing vocabulary; an intent verb or tool name MUST map to
   an existing procedure/use case (`PYEP-INTENT-01`, `PYMCP-VOCAB-01`)
2. List arguments as typed values; use enums for closed choices
3. Decide the result shape (human form and `--json`/structured form from one value)
4. Map each `AppError` cause and outcome to the surface's status or error
5. Check for name collisions with existing verbs/groups/tools; if one exists, plan a
   rename with a deprecated alias (`PYEP-DEPREC-01`)

### Validation

- [ ] The name does not collide, or the rename and alias are planned
- [ ] Every outcome and error has an explicit status/response
- [ ] Nothing in the contract is a shortcut the other surfaces lack

---

## Phase 2 — Renderers

**Goal:** Output formatting exists as pure functions, tested without I/O.

**Required framework docs:** `ARCH-PY-ENTRYPOINT`, `PLAT-PY-CLI`

**Assumes:** Phase 1 contract.
**Produces:** Pure `render_*` functions (value → text/JSON/envelope) and their tests.

### Steps

1. Write the human renderer and the structured renderer from the same result value
2. For a procedure-backed entry, render the stage list from the procedure definition;
   mark any stage with no implementation as not yet enforced (`PYEP-HONEST-01`)
3. Unit test each renderer with plain values

### Validation

- [ ] Renderers take values and return strings/dicts; they never print
- [ ] The stage list is generated, not hand-copied

---

## Phase 3 — Surface wiring

**Goal:** The entry parses its input, calls exactly one use case, and translates the result.

**Required framework docs:** `PLAT-PY-CLI`, `PLAT-PY-MCP`, `PLAT-PY-HTTP`, `ARCH-PY-ERROR`

**Assumes:** Phases 1–2.
**Produces:** One registered command/tool/route.

### Steps

1. Add one entry to the surface's registration table (`PYEP-DISPATCH-01`)
2. Convert raw input to typed request values immediately (`PYCLI-PARSER-01`)
3. Call the one use case from the `App` it was given; do not import the composition root
4. Pass the result to the renderer; translate errors through the surface's single
   translation function (`PYERR-TRANSLATE-01`)
5. CLI: results to stdout, diagnostics to stderr; preview by default for effectful
   commands; deterministic without a TTY
6. MCP: raise `ToolError` for known errors; nothing writes to stdout on stdio; no
   parameter that skips a gate (`PYMCP-MANDATORY-01`)
7. HTTP: separate request/response models; deny-by-default auth dependency; `def` for
   blocking use cases

### Validation

- [ ] The handler contains no branching on domain state (`PYEP-LOGIC-01`)
- [ ] One use case is called; no other surface is imported
- [ ] Effectful entries preview by default / require confirmation
- [ ] No `print` outside the CLI renderer/handler; no `sys.exit` outside `__main__`

---

## Phase 4 — Tests

**Goal:** The surface is tested with a fake `App`, not the real infrastructure.

**Required framework docs:** `PLAT-PY-TESTING`, `QG-TESTING`

### Steps

1. Build an `App` from the shared fakes and call the surface's `run(app, argv)` /
   the tool function / the `TestClient` with `dependency_overrides`
2. Assert the exit status/response and the rendered output for: success, each known
   error, each outcome branch, and invalid input
3. For a renamed entry: assert the old spelling still works and warns on stderr
4. Add the entry to the coverage test that iterates the registration table against the
   use-case list (`PYMCP-VOCAB-01`)

### Validation

- [ ] All statuses in the contract have a test
- [ ] The suite runs with no network, home directory, or real provider
- [ ] `lint-imports` passes — surfaces do not import each other or infrastructure

---

## Phase 5 — Documentation

**Goal:** The public surface is documented where users look.

### Steps

1. Update the command/tool/route reference and any README quick-start
2. Update the exit-status table if a status was added
3. Add a changelog entry; bump the minor version (new entry) or plan a major bump
   (breaking change) per `PYPKG-SEMVER-01`

### Validation

- [ ] Reference docs match `--help` / tool schemas / OpenAPI
