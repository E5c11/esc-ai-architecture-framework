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

## Outcome

337 rules migrated across every file that used the bold-rule format (46 of
70 docs). All of `check_missing_ids` through `check_duplicate_rule_ids` pass
clean. Deviations from the plan above, and why:

- **Agent D's worktree wasn't actually isolated** — its commit
  (`8dadf48`) landed directly on `main`'s history instead of a separate
  branch. Content was verified clean (exactly the 6 target files, nothing
  else), so no harm done, but Agents A, B, C all had to fast-forward their
  stale worktree branches onto `main` to pick up tooling `8dadf48` had
  already added by the time they checked. Agent A separately caught itself
  editing the shared main checkout by mistake mid-run and reverted before
  redoing the work in its actual worktree — verified clean afterward.
- **Two real bugs surfaced post-merge**, both the same edge case (adjacent
  `**Rule` lines with no blank line between them — the script's
  paragraph-based splitter can't tell where one rule's paragraph ends and
  the next begins): `platforms/mobile/koin.md` had 3 rules merged into one
  corrupted block (Agent B didn't catch it, unlike Agent A which hit and
  fixed the same pattern independently in its own scope), and
  `platforms/mobile/datastore.md` had a stale, malformed duplicate
  definition of a koin.md rule that the script correctly never touched
  (missing its `(hard)` marker) — replaced with a citation instead of a
  second definition, per the ownership model. Both fixed by hand in Phase 4.
- **`tools/migrate_rules.py` was NOT deleted** — `platforms/mobile/kmp.md`
  and `platforms/mobile/http-client.md` were deliberately excluded from
  Phase 3 (unrelated uncommitted work in progress at the time) and still
  need it; tracked in `workflows/missing-files.md`.
- **`check_rule_citations` was NOT promoted to a real failure** — 26
  citations remain unresolved, all attributable to two tracked gaps in
  `workflows/missing-files.md` (design-system checklist items that were
  never real rule definitions in any format, plus the deferred kmp.md/
  http-client.md pair), not migration defects. Promote once both close.
