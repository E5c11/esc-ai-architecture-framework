# Escape AI — Phase 1: Framework Composition Protocol
**Status:** Complete
**Plan:** see `esc-ai-orchestrator/plan/cohesive-system-integration-and-onboarding.md`
(Phase 0 + Phase 1) for full rationale; this tracks only this repo's share.

## Objective

Let `esc-ai-execution-framework` resolve this framework's documents (via
`index.json`) into a task context, and give this repo's own workflow tracking an
obvious, repository-local home consistent with the other two repos.

## Deliverables

- [x] Internal title and reference migration to `esc-ai-architecture-framework`
      (`README.md`, `INSTRUCTIONS.md`, `CLAUDE.md`, `tools/index.py`,
      `tools/validate.py`, `workflows/README.md`, `workflows/missing-files.md`).
- [x] Rename `workflows/` -> `.esc-ai/workflows/` in this repo. Updated
      `.esc-ai/workflows/README.md`'s `INSTRUCTIONS.md` links (one directory
      deeper now) and `tools/validate.py`'s stale reference (which also had a
      pre-existing active/archive mismatch — the cited file is in `archive/`).
      `INSTRUCTIONS.md`'s mentions of `workflows/README.md` (lines ~107, ~149, ~168)
      describe a *consuming* project's own workflow policy file, not this repo's —
      left as generic guidance for now; revisit once `.esc-ai/workflows/` is the
      established convention for consuming repositories too (Phase 5).
- [x] Define a versioned framework descriptor (`esc-framework.yaml` at this repo's
      root) for the execution framework's compatible-major-version check.
      `major_version: 1`, conforming to `esc-ai-execution-framework`'s
      `schemas/framework-descriptor.schema.yaml`.
- [x] No other structural change needed here — confirmed: `esc_exec/architecture_lookup.py`
      reads this repo's `index.json` directly as plain JSON, with no code dependency
      between the two repos.
