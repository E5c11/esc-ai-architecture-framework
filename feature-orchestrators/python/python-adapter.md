---
id: ORCH-PY-ADAPTER
type: orchestrator
layer: feature-orchestrators
platform: [python]
architecture: [python-app]
goal: "Add a new interchangeable provider/adapter (Gateway) behind an existing provider-neutral port"
requires: [CORE-DI, CORE-ERROR, CORE-TESTING, ARCH-PY, ARCH-PY-GATEWAY, ARCH-PY-USECASE, ARCH-PY-ERROR, ARCH-PY-COMPOSITION, ARCH-PY-OBSERVABILITY, PLAT-PY, PLAT-PY-SUBPROCESS, PLAT-PY-TESTING, QG-TESTING]
related: [ORCH-PY-USECASE, PLAT-PY-DI, PLAT-PY-IMPORT-LINTER, QG-REVIEW]
tags: [python, adapter, gateway, provider, subprocess, capabilities]
---
# Add a Provider Adapter (Python-App)

## Goal

Add one more implementation of an existing provider-neutral port — a new AI provider, a
new build-system detector, a new hosting API — as a Gateway selected at the composition
root, with **no change to any use case**. If a use case must change to accommodate the
adapter, the port was provider-specific and must be fixed first (`PYGW-PORT-01`).

## Before you start

Read every document in `requires`. Read the existing port and one existing adapter: the
new adapter is measured against the same contract and should look like a sibling.

---

## Phase 1 — Capability and contract check

**Goal:** Confirm the new provider fits the existing port; record what it can and cannot do.

**Required framework docs:** `ARCH-PY-GATEWAY`

**Assumes:** An existing port and at least one implementation.
**Produces:** A short note: which port methods the provider supports, its declared
capabilities, its failure modes.
**Docs to update:** the provider support matrix, or `None` if none exists.

### Steps

1. Map each port method to the provider's mechanism (CLI flags, API calls)
2. Decide the declared capabilities honestly; a missing capability is *declared absent*,
   not faked (`PYGW-CAPS-01`)
3. List failure modes: unavailable, unauthenticated, timed out, rejected

### Validation

- [ ] No port change is needed; if one is, stop and revise the port first
- [ ] Capabilities are declared, not inferred by callers

---

## Phase 2 — Fake first

**Goal:** A scripted fake of the *provider* lets the adapter be tested without the real one.

**Required framework docs:** `PLAT-PY-TESTING`

**Assumes:** Phase 1.
**Produces:** A tiny scripted stand-in (a script run via `sys.executable`, or a recorded
response set) that mimics the provider's observable behavior.

### Steps

1. Write the stand-in emitting representative success, failure, timeout, and malformed
   output
2. Keep it beside the tests; it is reused by the adapter's tests

### Validation

- [ ] The stand-in covers every failure mode from Phase 1

---

## Phase 3 — The adapter

**Goal:** The Gateway implements the port, safely.

**Required framework docs:** `ARCH-PY-GATEWAY`, `PLAT-PY-SUBPROCESS`, `ARCH-PY-ERROR`

**Assumes:** Phases 1–2.
**Produces:** One module in `infrastructure/gateways/` implementing the port.

### Steps

1. Implement the port's methods, translating domain requests into the provider's form
2. Run processes only through the single runner: argument list, explicit `cwd`,
   env allow-list, timeout; capture bounded output
3. Return the observed exit status and output as data; never accept the provider's own
   claim of success in place of an observable result (`PYGW-EXIT-01`)
4. Translate provider errors into gateway error types (`PYGW-ERROR-01`); chain with
   `raise ... from`
5. Redact secrets in anything logged or returned (`PYOBS-REDACT-01`)
6. Import the provider SDK lazily inside the factory (`PYCOMP-LAZY-01`)

### Validation

- [ ] No provider name, flag shape, or SDK type leaks into the port or a use case
- [ ] No `shell=True`; every call has a timeout
- [ ] Errors are translated; secrets are not logged

---

## Phase 4 — Selection and wiring

**Goal:** The adapter is chosen from configuration at the composition root.

**Required framework docs:** `ARCH-PY-COMPOSITION`

**Assumes:** Phase 3.
**Produces:** One entry in the provider factory table and a `Settings` value.

### Steps

1. Register the adapter by name in the composition root's factory table
2. An unknown or unconfigured provider fails with a clear configuration error
   (`PYCOMP-CHOICE-01`)
3. Add any required optional dependency as an extra (`PYPKG-DEPS-01`)

### Validation

- [ ] Selecting the adapter requires no use-case change
- [ ] Nothing outside `composition.py` names the concrete adapter

---

## Phase 5 — Tests

**Goal:** The adapter is proven against the stand-in and, where cheap, the real provider.

**Required framework docs:** `PLAT-PY-TESTING`, `QG-TESTING`

### Steps

1. Run the port's shared **contract tests** (the same parametrized suite every adapter
   passes) against the new adapter and the stand-in
2. Test each failure mode: unavailable, timeout, rejected, malformed output
3. Optionally add an opt-in (marked, skipped by default) test against the real provider

### Validation

- [ ] The new adapter passes the same contract tests as its siblings
- [ ] No test needs the network, credentials, or the real provider by default
- [ ] `lint-imports` and `ruff` pass; the use cases were not modified
