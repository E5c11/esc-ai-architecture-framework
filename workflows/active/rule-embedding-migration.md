# Rule-Embedding Migration

Migrate framework rules from inline bold-text (`**Rule ID (type):** statement`)
to fenced YAML blocks conforming to `schemas/rule.yaml`, so `scope`,
`enforced_by`, and `violation_message` — described by the schema but present
in zero actual documents today — become real, and CI can catch duplicate
rule IDs and broken rule citations. Full design and survey data in the
session that authored this doc; summarized in each phase below.

**Workflow:** Do NOT enter plan mode — this document plus the framework's own
`tools/validate.py` and `schemas/rule.yaml` provide all the planning needed.

**Commit after each phase.**

## Format

Replace:
```
**Rule ARCH-PC-REP-INTERFACE-01 (hard):** Repository MUST define an interface.
```
with:
````
```rule
id: ARCH-PC-REP-INTERFACE-01
statement: Repository MUST define an interface.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-REP-INTERFACE-01 — Repository MUST define an interface.
```
````
`statement` is the first sentence only. Anything below the original bold
line (blockquotes, bullets, follow-on prose) stays exactly where it is.
No rule ID is ever renamed. `enforced_by` defaults to `[reviewer]`,
`violation_message` is auto-templated, `scope` is guessed by keyword
heuristic (fallback: `behavior`) — a known lower-quality starting point,
refined per-rule over time, not a blocker.

## Phase 1 — Tooling

Fix `schemas/rule.yaml`'s `id` pattern (currently 2-segment-only, doesn't
match real IDs like `ARCH-PC-REP-INTERFACE-01`) to reuse
`tools/validate.py`'s `ID_PATTERN`. Refactor `parse_front_matter` to expose a
reusable `_parse_flat_yaml` helper. Add `extract_rule_blocks`,
`check_rule_schema`, `check_duplicate_rule_ids`, `check_rule_citations`
(WARN-only) to `tools/validate.py`. Verify: `python tools/validate.py` still
reports 0 rules found, no false positives, before any doc changes.

## Phase 2 — Migration script + smoke test

Write `tools/migrate_rules.py` (temporary, deleted in Phase 4). Smoke-test
against `architectures/pragmatic-clean/repository.md`. Commit script +
migrated file together.

## Phase 3 — Parallel migration (4 agents, isolated worktrees)

| Agent | Scope | Files |
|---|---|---|
| A | `architectures/backend-service/` + `architectures/pragmatic-clean/` (remaining) + `architectures/web-spa/` | 17 |
| B | `platforms/mobile/` | 14 |
| C | `platforms/backend/` + `platforms/web/` + `platforms/library/` | 8 |
| D | `build/` + `quality-gates/` | 6 |

Each agent runs `tools/migrate_rules.py` against its files, runs
`python tools/validate.py`, fixes anything flagged, commits. No rule ID
renames. Agent B also fixes the `platforms/mobile/compose.md:71`
duplicate-prose bug (un-bolded sentence duplicating `PLAT-MOB-CP-THEME-01`).

## Phase 4 — Integration and cleanup

Merge all 4 worktree branches to `main`. Full-repo `python tools/validate.py`
run. Delete `tools/migrate_rules.py`. Re-run `check_rule_citations`; if
clean, promote it from WARN to a real failure. Update `workflows/README.md`'s
"How to Add New Docs" section to reference the shipped format concretely.
Final check: `grep -rn "\*\*Rule [A-Z]" .` returns nothing. Move this doc to
`workflows/archive/`.
