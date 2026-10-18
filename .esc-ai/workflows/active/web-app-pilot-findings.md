# Web-App Pilot Findings: AmpmDashboard, Learning page

Branch `esc-ai/web-app-pilot` in `/home/emmanuel/WebstormProjects/AmpmDashboard-pilot` (commits `7c3bd96` tests, `d49361e` refactor). The original repo is untouched.
Measured 2026-10-18 against the 110-rule architecture. Verdicts are evidence for the rule review, not a decision.

## What was done
- 60 characterisation tests first, mutation-checked (11/11 broken variants caught).
- Learning moved from one 396-line page plus a 102-line hook to `features/learning/` (domain, data, hook, components), `composition/AppGraph.tsx` and `shared/outcome.ts`.
- Behaviour preserved: headline figures and all seven chart series equal the original on every real document (2,824 dev, 7,375 prod) for 8 environment-and-range combinations, and in the browser on both environments.
- 75 tests, type-check clean, build passes. The architecture check reports 0 violations in `features/`.

## Cost
- 396 + 102 lines became 671 lines across 9 files (plus 15 test files' worth of tests), so the page is **more code, not less**. The gain is that every part is a single-purpose unit under 110 lines and the logic runs without a browser.
- A 7,375-document read is repeated on each environment switch, because the graph (and its cache) is rebuilt on switch (`COMPOSE-ENV-01`). The original kept one cache per environment.

## Rule by rule: what happened
| Rule | Result |
|---|---|
| `DEP-03/04/05/07` (dependency direction) | **Earned its place.** Mechanical check, and it caught a real slip of mine (`LearningView` importing constants from the domain). The rest of the app still has 5 violations (`BugReports`, `EditAiModal`, `Papers`). |
| `DS-PARSE-01`, `DS-MALFORMED-01` | Parser accepted all 10,199 real documents (0 malformed), so no behaviour change; the strictness is free here and would catch drift. |
| `DS-SCHEMA-01` | Applied as option (b): a versioned reader. Legacy answers (1,419 dev, 3,768 prod) are explicit and shown in a note. This is a small **UI behaviour addition**. Needed a judgment call: legacy answers stay in the headline figures and out of the charts, exactly as before. |
| `DS-BOUND-01` | **Could not comply.** The page aggregates a whole growing collection in the browser. Satisfying the rule means a server-side aggregate (a function), which is a backend change, not a refactor. Left as a marked known violation. The rule is hard with no exception, so this needs a decision (see below). |
| `EFLOW-RETURN-01` (value at boundaries) | Cheap here: only the DataSource and Hook boundaries exist. No UseCase or Repository was needed, so the plumbing worry is untested. |
| `USECASE-01`, `REPO-01` | Thresholds worked: the pure `computeLearning` function took the UseCase's role; the cache is a decorator, not a Repository. Neither layer was added. |
| `DOM-CLOCK-01` | **Earned its place.** `now` is a parameter, so the domain tests need no fake timers. |
| `DOM-TIME-01` | The range maths still uses local-time days (behaviour preserved), which differs from the SAST day used for charts. A latent bug now recorded in a test comment, not fixed. |
| `HOOK-STATE-01` (soft) | Union used trivially; no contradictory-flag bug appeared, which supports keeping it soft. |
| `COMPOSE-GLOBAL-01`, `COMPOSE-SDK-01` | Not satisfied app-wide: `firebaseConfig.ts` still creates both Firebase apps at import. Only the new code follows them. |
| `MOD-SIZE-01` | Easy. Every new file is under 110 lines. |
| Not exercised | `server` runtime rules, Repository, UseCase, observability, route and boundary files, `UC-WRITE-*` (no writes on this page). |

## Tool findings
- The `web-app` template assumes a Next `app/` folder; for a Vite SPA the layout rule had to be edited by hand.
- A rule that scans no files (`web.usecases-depend-on-interfaces`) reports `files_scanned: 0` and passes only because it is optional. That is correct but easy to misread.

## Decisions this raises
1. **`DS-BOUND-01` has no exception path.** For client-aggregated analytics it forces a backend change. Options: keep hard and require a tracked backlog item for each violation, make it soft for admin-only data, or accept it as a known violation recorded in the repo.
2. **Cache on environment switch.** Keep the cache per environment across switches (an app-level cache outside the graph), or accept the re-read.
3. **Legacy answers.** The note was added; confirm that is the behaviour wanted, or choose to exclude them from the headline figures too.

## Not done
The login race, the other eleven hooks that import the SDK, the Next.js static-export step, and a server-side aggregate.
