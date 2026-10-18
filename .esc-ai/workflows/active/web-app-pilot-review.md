# Web-App Rules: Review After Two Pilot Slices

Evidence: Learning (reads) and Notifications (writes, two projects), 109 tests, 8 against the Firestore emulator.
113 architecture rules now. "Held" means the rule was applied in the new code and nothing about it hurt. It does **not** mean it was shown to prevent a failure; that is listed separately.

## Tally
| | Rules |
|---|---|
| Held (applied, no problem) | 54 |
| Shaped or changed by the evidence | 5 |
| **Not exercised by either slice** | **55** (44 of them hard) |

## Rules that demonstrably earned their place
| Rule | What it did |
|---|---|
| `DEP-03`, `DEP-05` | The mechanical check caught real slips in new code (a component importing domain constants; later a use case filed under `domain/`). Whole-app baseline: 12 of 12 hooks and 3 pages break `DEP-03`. |
| `UC-WRITE-02` | Fixed a real bug: the promotion duplicated a notification in prod on retry, and real users receive those. |
| `DS-PARSE-01`, `DS-MALFORMED-01`, `DS-SCHEMA-01` | 10,199 real documents parsed with 0 malformed; the legacy shape (half the answers) is now explicit and visible. |
| `DOM-CLOCK-01` | Domain tests need no fake timers. |
| `ERR-MAP-01` (with the emulator test) | Showed that `instanceof FirestoreError` never matches; every real failure would have been "unexpected". |
| `FEAT-DATA-01` | Removed a duplicated error translator. |

## Shaped by the evidence
`DEP-05` (constants must come through the hook), `COMPOSE-ENV-01` (a graph with no subscriptions may be kept), `HOOK-STATE-01` (soft), `DS-BOUND-01` (split into pagination and aggregation), `FEAT-PLACE-01` (the five-in-one rule did not stop two misplacements; the import check did).

## Trims applied from the evidence (14)
`DEP-02`, `DEP-04`, `DEP-07`, `MOD-API-01`, `RUNTIME-01`, `COMP-PROPS-01`, `DS-RETURN-01`, `DS-PARSE-01`, `DS-MALFORMED-01`, `DS-NAMING-01`, `EFLOW-VALIDATE-01`, `FEAT-PLACE-01`, `HOOK-FORMAT-01`, `HOOK-RACE-01`, `UC-SINGLE-01`: each now states one check. Cuts were limited to clauses that another rule or the build already enforces, or that no slice used.

## Trims not applied: no evidence yet
`COMPOSE-CONFIG-01` (split environment-read from validation), `DS-SUBSCRIBE-01`, `EFLOW-BOUNDARY-01`, `DOM-TIME-01` (its two clauses are related and the Ampm local-time bug supports keeping both). Applying wording changes to rules nothing exercised would be guessing.

## The 55 unexercised rules, by what would test them
| Needs | Rules |
|---|---|
| A Next.js server runtime | `COMP-SERVER-01`, `COMP-STATIC-01`, `COMPOSE-SPLIT-01`, `RUNTIME-02`, `BFF-01` |
| A live subscription (`onSnapshot`) | `DS-RETURN-02/-03`, `DS-SUBSCRIBE-01`, `HOOK-ERROR-02`, `ERR-CANCEL-01` |
| A Repository, orchestrator or background work | `REP-*` (3), `UC-ORCH-01`, `UC-SIDE-01`, `OBS-RECORD-01` |
| A multi-page app with routes and shared code | `FEAT-ROUTE-01/-02`, `FEAT-SHARED-01/-02`, `FEAT-SUB-01`, `COMP-NAMING-01` |
| A lint configuration (cheap to add) | `MOD-API-01`, `MOD-CYCLE-01`, `MOD-NAME-01`, `MOD-SIZE-01`, `MOD-FUNC-01`, `HOOK-NAMING-01`, `UC-NAMING-01`, `DOM-NAMING-01` |
| Error handling at page level | `EFLOW-BOUNDARY-01`, `-SWALLOW-01`, `-LOG-01`, `-NETWORK-01`, `-PRESENT-01`, `COMP-STATE-01` |
| Logging, analytics and reporting | `OBS-LOG-01/-02`, `OBS-REDACT-01`, `OBS-REPORT-01`, `HOOK-ANALYTICS-01` |
| Domain depth (a bigger domain slice) | `DOM-DETERMINISM-01`, `-INVARIANT-01`, `-SERIAL-01`, `-VALUE-01`, `-VOCAB-01` |

Of these, `MOD-*` and the naming rules are checkable by existing lint rules and could be wired into a generated lint configuration with no refactor. The `OBS`, `REP` and server-runtime groups cannot be tested on this app as it is: it has no Repository, no listeners, and no server.

## What this says about the rule set
- The rules that earned their place are the **structural and data-boundary** ones, the failures that cost something real (duplicate writes, silent defaults, wrong error mapping, layering drift). Those are also the ones with mechanical checks or real-provider tests.
- The largest untested block is behavioural (errors, observability, domain style). They are plausible, and written from the same reasoning as the ones that held, but they have no evidence. Treat them as **soft until exercised**: 44 of the 55 are currently hard.
- Recommendation: do not delete them, but mark the unexercised hard rules `status: unproven` in the index so a project can see which rules have been through a real slice, and promote them as evidence arrives.

## Next slices that would test the most unexercised rules
1. A page with a live listener and a Repository (the app's `Portal` uses `onSnapshot` and batches): subscriptions, `REP-*`, `UC-WRITE-01`.
2. A lint configuration generated from the declared limits: tests the `MOD-*` group without refactoring.
3. A server-runtime project (`ampm-backend`'s content dashboard is the intended consumer) for the Next.js server rules.
