# Escape AI — Phase 1: Framework Composition Protocol
**Status:** In progress
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
- [ ] Rename `workflows/` -> `.esc-ai/workflows/` in this repo. Update
      `workflows/README.md` and `tools/validate.py`'s reference to
      `workflows/active/rule-embedding-migration.md`.
      `INSTRUCTIONS.md`'s mentions of `workflows/README.md` (lines ~107, ~149, ~168)
      describe a *consuming* project's own workflow policy file, not this repo's —
      leave those as generic guidance for now; revisit once `.esc-ai/workflows/` is
      the established convention for consuming repositories too (Phase 5).
- [ ] Define a versioned framework descriptor (`esc-framework.yaml` at this repo's
      root) for the execution framework's compatible-major-version check.
- [ ] No other structural change expected here — `index.json`/`tools/lookup.py`
      already provide what `esc-ai-execution-framework`'s new architecture-document
      lookup needs; it's consumed as a stable data contract, not a code dependency.
