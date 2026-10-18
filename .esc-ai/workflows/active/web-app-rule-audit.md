# Web-App Rule Audit (draft for review)

Status: **draft, nothing in the rules has been changed.** Written 2026-10-18 for review by the person whose
Postgres and KMP rules are the reference. Every verdict below is a recommendation to accept, change or
reject; the decisions that need that expertise are collected in section 6.

Scope: all 143 rules in `architectures/web-app/` rule by rule (section 7); the platform rules in
`platforms/web/` and `quality-gates/web-testing.md` by flagged group (section 8). The reference points are
`ARCH-PC` (113 rules, KMP) and `ARCH-BE` (51 rules, Postgres and Spring).

## 1. Verdict

The layering is sound, and the parts that came from real failures (the dependency direction, nothing
runs at import, a malformed record is an error and not a default, one time zone) are worth keeping
exactly as they are. The rule *set* is too heavy for the way you want to work:

- It is **about twice the size of the reference rules** per rule and per document load, and **half of it is compound**: one rule
  that is several checks, so it cannot be marked pass or fail, mapped to one tool check, or cited cleanly.
- It states some constraints **two or three times** in different documents, each owning a copy.
- It carries **process, testing and operations** rules (fakes and contract tests for every data source,
  retry policy, structured logs, record shapes) that `ARCH-PC` and `ARCH-BE` leave to tooling or to a
  separate gate.
- It diverges from `ARCH-PC` on two decisions without saying so (the error model and the state shape).
- It misses several of the **scars your Postgres rules encode** (atomic multi-write, a maximum page size and
  stable order, schema change paired with migration).

Applying every verdict takes the architecture from **143 rules to 112**, and the always-on hard rules
from **124 to 61** (plus 12 that apply only when a trigger is met). Section 9 says what that does to
the documents an onboarded project has to load.

## 2. Measurements

Computed from the rule blocks and the generated index, not estimated.

| | `ARCH-PC` (KMP) | `ARCH-BE` (Postgres) | `ARCH-PY` | **`web-app`** |
|---|---|---|---|---|
| Documents | 10 | 8 | 12 | 14 |
| Rules | 113 | 51 | 109 | **143** |
| Hard rules | 92% | 86% | 88% | 87% |
| Words per rule statement | 15 | 12 | 29 | **30** |
| Rules with 4+ conjunctions or commas | 5% | not measured | not measured | **50%** (135 of 270, architecture and platform) |
| Statements of 45+ words | 3 of 113 | not measured | not measured | 15 of 270 (architecture and platform) |
| Words in the architecture documents | 11,300 | not measured | not measured | **21,700** |

| Documents an agent must load | Docs | Tokens (about) |
|---|---|---|
| Backend endpoint (`ORCH-BE-ENDPOINT`) | 17 | 15k |
| KMP feature: ViewModel, UseCase, Repository, DataSource, View | 18 | 17k |
| KMP, the whole architecture | 22 | 24k |
| **Web-app onboarding set (static export)** | **33** | **55k** |

Two readings of those numbers. The hard-rule share is the same everywhere, so strictness in *level* is not what
differs; the difference is rule *size* and *volume*. And the reference architectures are cheap to load because their
rules are one-liners about a mechanism (`@Transactional` goes on service methods; entities use a UUID key).

## 3. Principles the audit applied

1. **Atomic.** One rule is one check, so it can be marked pass or fail and mapped to one tool. (`ARCH-PC` style.)
2. **Earns its place.** A rule prevents a failure that has happened, or is nearly free to follow. Your Postgres
   rules are all of this kind (`FetchType.LAZY`, hashed refresh tokens, `ORDER BY id`).
3. **Proportional.** Structural rules apply to every project. Rules that cost effort (fakes, contract tests,
   structured logging, record shapes) apply when a trigger is met, and say what the trigger is.
4. **Tool first.** If the compiler, the build, a lint rule or the import contract enforces it, it is not a
   reviewer rule, and often not a rule at all.
5. **One owner.** A constraint is stated once; every other document cites it.
6. **Architecture stays framework-neutral.** React, Next.js and Firebase mechanics belong in platform documents.
7. **Parity of intent, not of mechanism.** The reference rules are written for Kotlin, Compose, Koin, Flow and Spring. What transfers is the
   *failure* a rule prevents (a half-applied write, an unbounded read, a stale cache, an unmigrated schema). How it is prevented is decided for
   TypeScript, React and Next.js on their own merits, and a divergence from `ARCH-PC` is fine when the reason is stated.

## 4. Findings

1. **Compound rules.** Half of the web rules bundle several checks (`HOOK-RACE-01` is release, ignore-late-result and
   inputs-changed in one sentence). The reference rules are one-liners. Consequence: a reviewer cannot mark one
   clause failed, and 23 of the rules below need splitting or trimming.
2. **Duplicated ownership.** Seven groups state one constraint in two or three places: server-only code
   (`DS-SERVER-01`, `COMPOSE-SPLIT-01`, `PLAT-WEB-NEXT-SERVERONLY-01`); error boundaries (`EFLOW-BOUNDARY-01`,
   `PLAT-WEB-NEXT-BOUNDARY-01`, `PLAT-WEB-RP-BOUNDARY-01`); interface and return rules repeated for Repository and
   UseCase; the clock (`DOM-CLOCK-01`, `UC-IO-01`, `PLAT-WEB-NEXT-DATA-NONDET-01`); public surface (`DEP-07`,
   `FEAT-PUBLIC-01`, `MOD-API-01`); two size rules with different numbers (`COMP-LEAN-01` 150, `MOD-SIZE-01` 300); and
   auth state (`PLAT-WEB-NEXT-FB-AUTH-01` against the older `PLAT-WEB-FB-AUTH-01` and `PLAT-WEB-STATE-CTX-02`).
3. **Process in the architecture.** Rules about how to test (every DataSource ships a fake and a contract
   test; every UseCase decision branch has a test), how to split a module in steps, retry policy, and log record shape
   do not describe the structure. `ARCH-PC` has one testing rule in 113. They belong in the testing gate, a workflow,
   or tooling.
4. **Unexplained divergence from `ARCH-PC`.** Divergence is not the defect; leaving it unexplained is. (a) The error model: `ARCH-PC` throws a typed domain error from the
   DataSource and converts to an `Outcome` at the UseCase; the web rules return `Outcome` from the DataSource upward. (b)
   State shape: `ARCH-PC-VM-STATE-03` is one state class with its fields; the web rules require a discriminated union.
   Both are defensible. Neither was a decision anyone made; see Q1 and Q2.
5. **Missing scars.** Your Postgres rules encode failures this set does not: a multi-table write is transactional
   (`SVC-TX-02`), a maximum page size and a stable order are mandatory (`PAG-SIZE-01`, `PAG-ORDER-01`), an entity change ships
   with its migration (`ENT-MIGRATION-01`), time is injected (`TIME-01`). The Ampm run found the web equivalent of the
   migration rule: half the documents in both projects are in an older shape, and nothing in the set would have prevented it.
6. **Thresholds with no evidence.** Module 300/600 lines, component 150, function 50 lines and 10 branches, ten files per
   layer folder, eight chart series. `ARCH-PY` uses 400/800. They are judgment calls written as numbers; one of
   them (`MOD-SIZE-01`) is soft in its type and uses MUST in its text.
7. **Enforcement does not match the wording.** Only 8 rules are checked mechanically. About ten more are lintable with
   rules that already exist (no `console.*`, no `any`/`as`/`!` over unchecked data, no empty `catch`, no import cycles, a
   maximum module size, no `export *` in a public surface, an exhaustive `switch`) and none of them is generated into a
   lint configuration yet.

## 5. Parity with the reference architectures

What corresponds to what, and what each side has that the other does not. Read the rows as *intent*: the Kotlin mechanisms
(Flow, Koin scopes, `@Transactional`, annotations) are not meant to be copied, only the failure each one prevents.

| Concern | `ARCH-PC` (KMP) | `ARCH-BE` (Postgres) | `web-app` |
|---|---|---|---|
| Layer stack | View, ViewModel, UseCase, Repository, DataSource | Controller, Service, DataSource, Entity | Component, Hook, UseCase, Repository, DataSource, Domain |
| Optional layers | Repository when one source | Store wrapper when justified (`REP-WHEN-01`) | Repository and UseCase by threshold |
| DataSource role | Translate types and exceptions | Return entities or primitives | Parse, map, translate errors |
| Error model | DataSource **throws** domain errors; UseCase returns `Outcome` | Services throw `ResponseStatusException`; global handler | DataSource **returns** `Outcome` (diverges) |
| State | One state class with loading/error fields | n/a | Discriminated union (stricter) |
| Time | Not covered | `TimeProvider` injected (`TIME-01`) | Clock injected (`DOM-CLOCK-01`) |
| Atomic multi-write | n/a | `@Transactional` on multi-table writes (`SVC-TX-02`) | 'State what happens on failure' (`UC-WRITE-01`, weaker) |
| Bounded reads | n/a | Max page size, stable order (`PAG-*`) | `DS-BOUND-01`, soft |
| Schema change | n/a | Migration in the same commit (`ENT-MIGRATION-01`) | None |
| Cross-feature composition | Composition root (`COMP-ROOT-*`) | n/a | Route composes (`FEAT-ROUTE-02`), parity |
| Shared code | Promote on a second consumer (soft), no feature code in core (hard) | Domain modules depend on `:core:*` | `FEAT-SHARED-01/02`, parity (01 is wrongly hard) |
| Naming | No `Impl`, provider first | `{Domain}Service` etc. | `FEAT-NAME-01`, parity |
| Testing | 1 rule | 3 rules | **8 rules** in the architecture |
| Observability | analytics in the ViewModel | log in the global handler | **9 rules** |
| DI | Scopes, module order, qualifiers | Constructor injection | Composition root, no container |

Rules in the reference sets that have no web counterpart and probably should: schema/document-shape change paired
with a migration or an explicit tolerant read; atomic multi-document writes; a maximum read size and a stable
order. Q3 to Q5 below propose them.

## 6. Decisions needed

Each has my recommendation. They are the places where your Postgres and KMP experience should override mine.

**Q1. Error model.** Return `Outcome` from the DataSource upward (current), or follow `ARCH-PC`: the DataSource and Repository throw a
typed `AppError`, and the UseCase catches at its boundary and returns `Outcome` to the Hook.

*Correction to my first draft:* I leaned on 'it is the model you have verified', which is a parity argument and not a web one.
Judged on web merits, the case is closer than that, and it favours the current model at the DataSource boundary:

- In TypeScript a `catch` variable is `unknown`; there are no checked exceptions, so a typed error needs an `instanceof` check
  that nothing forces. Kotlin's compiler and coroutines give the JVM model structure TypeScript does not have.
- A rejected promise nobody awaits is silent, and an error thrown in an event handler or an effect never reaches a React error
  boundary (the React and Next.js documentation both say so).
- Next.js strips a thrown Server Action error to an opaque digest in production, so on the `server` runtime returning a value is not
  a preference but the documented way to carry an expected failure.

The cost is real: `if (!result.ok) return result` repeated in the Repository and UseCase layers. It can be contained with one or two
helpers, and it is the cost of an explicit contract.
*Revised recommendation: keep the DataSource boundary returning a value, state the reason, and shorten the rules* (the verdicts for
`DS-RETURN-01`, `EFLOW-RETURN-01` and `UC-RETURN-01` assume this). If the pilot shows the plumbing costs more than it saves in the
Repository and UseCase layers, relax those two layers to exceptions and keep the value at the DataSource and Hook boundaries.

**Q2. State shape.** Discriminated union (current) or one state object with loading and error fields.
*Recommendation: soft.* The union is idiomatic TypeScript and cheap, so this is not about `ARCH-PC`'s Compose state class. It is that
the rule prevents a bug class (contradictory flags) that has not appeared in the pilot, so it should not be a gate until it does.

**Q3. Atomic multi-write.** Mirror `SVC-TX-02`: a UseCase that writes more than one document MUST do it in one atomic
operation (a batch, a transaction, or one callable), and the exception needs a recorded reason.
*Recommendation: adopt, hard,* replacing `UC-WRITE-01`'s 'state what happens'. It is the same scar.

**Q4. Bounded reads.** Mirror `PAG-SIZE-01` and `PAG-ORDER-01`: a list read has a maximum, and a limited read has an explicit
order. *Recommendation: adopt both as one rule* (hard for a collection that grows, with your `PAG-SCOPE-01` bounded/unbounded test
as the trigger). Ampm's `getDocs(collectionGroup('answers'))` is exactly the case.

**Q5. Document-shape change.** Mirror `ENT-MIGRATION-01`: a change to a stored document's shape ships with a migration, or
with an explicit tolerant read that is named in the code and counted. *Recommendation: adopt.* Without it, the Ampm
situation recurs (half the answers are in an older shape and every figure quietly mixes two schemas).

**Q6. Testing in the architecture.** Keep the eight testing rules, or move them to `QG-WEB-TESTING` and leave the
architecture with `PC`'s one. *Recommendation: move; keep 'a layer is tested with the fake of the layer below' as a single soft rule.*

**Q7. Observability.** Keep nine rules in the architecture, or split to an optional document loaded when the app handles
personal data or runs background jobs. *Recommendation: keep `OBS-REDACT-01` in the core, make the rest an optional document.*

**Q8. Where does 'soft' end?** Several rules are soft but worded MUST (`HOOK-SCOPE-01`, `MOD-SIZE-01`). *Recommendation:* a
soft rule says SHOULD and a reviewer may accept a recorded exception; a hard rule is something the project's own check
fails on. Reword every soft rule to match.

**Q9. Should an error carry its presentation?** `ARCH-PC` and the Arrow Errors library put severity, presentation mode (snackbar, dialog,
full screen, silent), actions and a catalog code on the error itself, so the View needs no logic. The web rules say the Component chooses
the wording from the `AppError` variant (`HOOK-ERROR-01`, `EFLOW-PRESENT-01`). *Recommendation: only if web and mobile must show the
same message for the same failure,* in which case share a catalog as data (a code, severity, presentation and messages per locale as
JSON) and let `AppError` carry the code. For an admin dashboard that is not needed.

### 6a. Q3 to Q5 worked through

Each starts from your Postgres rule, translates the *failure* (not the mechanism) to Firestore, and uses what the Ampm code shows.
The draft rule text is atomic and is a proposal for you to correct.

**Q3. Atomic multi-write** (your `SVC-TX-02`: a method that writes more than one table is transactional).

- *Evidence.* The Ampm code already uses `writeBatch` in three places (papers, subjects, portal content), so the practice exists informally.
  The sites that are not atomic are the dev-to-prod *promotions*: `promoteNotificationToProd` does `addDoc` into prod and then
  `updateDoc` on dev to mark it promoted. They are two projects, so no batch can cover both. If the second write fails, the item is in
  prod and not marked in dev, and a retry creates a **duplicate** in prod because `addDoc` makes a new id. `promoteItem` does the same shape
  with `setDoc` and the same id, so a retry is harmless. Same design, two outcomes.
- *So the rule has two forms,* because Postgres has only the first:
  1. `UC-WRITE-01` (hard): a UseCase that writes more than one document **in one store** does it in one atomic operation the DataSource
     provides (a batch, a transaction, or one callable). An exception needs a recorded reason.
  2. `UC-WRITE-02` (hard, only when a write spans two stores or projects): it MUST be idempotent and ordered: a deterministic id and an
     upsert for the target first, then the marker, so repeating it after a partial failure does not duplicate.
- *Check on the limit.* A batch has a maximum number of operations; the repo's own `copy-to-prod.mjs` chunks at 500, which matches what I
  recall of the documented limit, but I could not confirm the number from the documentation page, so verify before it goes in a rule.
- *Your call:* is a recorded exception to the atomic rule acceptable, or should the atomic rule have none (as `SVC-TX-02` has none)?

**Q4. Bounded reads** (your `PAG-SCOPE-01` bounded or unbounded, `PAG-SIZE-01` server-enforced maximum, `PAG-ORDER-01` explicit stable order).

- *Evidence.* The dashboard has 25 `getDocs` or `onSnapshot` calls and **no `limit()` at all**. Three of them read an entire collection group
  (answers: 7,375 documents in prod; sessions; video sessions) and compute every figure in the browser. That is not pagination missing; it is
  a design in which the client aggregates everything. Paginating it would not fix it.
- *So the web translation is two rules:*
  1. `DS-BOUND-01` (hard, triggered by your `PAG-SCOPE-01` test: the collection grows with users or content): a list read is bounded by a
     limit and an order that is unique (the document id as the tie-break), **or** is served from a server-side aggregate. A client MUST NOT
     read a whole growing collection to compute figures. (Ilitha already works this way: the function builds a snapshot and the page reads one document.)
  2. The 'server enforces the maximum' half of `PAG-SIZE-01` has a real Firestore equivalent: security rules can cap a list query, e.g.
     `allow list: if request.query.limit <= 100;` (confirmed in the Firestore rules documentation, which also says a query that could exceed the
     rule fails whole). *Soft* for admin-only collections, *hard* for anything a user can list.
- *Your call:* for analytics dashboards, should the architecture say 'precompute server-side' outright, or leave it to a trigger and a reviewer?

**Q5. Document-shape change** (your `ENT-MIGRATION-01`: an entity change ships with its migration in the same commit).

- *Evidence.* Half the answers have no skills, unit, topic, difficulty, presentation type, reveal flag or timestamp: **1,419 of 2,824 in dev and
  3,768 of 7,375 in prod**. `useAnswers` fills in `[]`, `''`, `0` and `false`, so these documents are in every headline figure and in no chart.
  Nobody decided that; the defaults did.
- *Draft rule* `DS-SCHEMA-01` (hard, when a stored shape changes): the change ships with **one of** (a) a backfill script that migrates the existing
  documents (idempotent, with a dry run, committed with the change), (b) a versioned reader that maps the old shape explicitly and whose exclusions are
  counted and shown, or (c) a recorded decision to discard. A reader that silently defaults a missing field is none of these. Documents SHOULD
  carry a `schemaVersion`. The rule is Firestore's stand-in for a migration file, because a schemaless store has no migration tool to force one.
- *Ampm in particular:* option (a) is impossible (the topic and skills are simply absent), so (b): treat these as `legacy`, leave them out of the
  breakdowns, and show 'N legacy answers excluded'.
- *Your call:* is 'one of three, explicitly' the right strength, or should (c) be disallowed?

## 7. Rule-by-rule verdicts

Codes: **keep** as written; **keep, reword** (make atomic or shorter); **soft** (a convention, not a gate);
**conditional** (applies only when the trigger is met); **merge** into the named rule; **move out** (platform document, lint
rule or workflow); **drop** (the framework enforces it, or it does not earn its overhead).

| Verdict | Count |
|---|---|
| keep | 43 |
| keep, reword (atomic) | 21 |
| soft | 36 |
| conditional | 12 |
| merge | 20 |
| move out | 4 |
| drop | 7 |
| **Total** | **143** |

### Overview: dependency direction, inclusion, runtime (`ARCH-WEB-APP`)

| Rule | Now | Verdict | Why |
|---|---|---|---|
| `DEP-01` | hard | keep | Domain imports nothing. CI-checked. |
| `DEP-02` | hard | keep, reword (atomic) | UseCase imports no framework/SDK/implementation. Drop 'Repository' (shares `data/` with implementations, so no folder rule can check it); CI-checked. |
| `DEP-03` | hard | keep | SDK only in DataSources. CI-checked. The single most valuable rule (Ampm: 12/12 hooks break it). |
| `DEP-04` | hard | keep, reword (atomic) | Hook imports no SDK/implementation. Absorbs HOOK-SERVER-01. CI-checked. |
| `DEP-05` | hard | keep | Component imports nothing below the Hook (PC VIEW-SPLIT/DEP-02). CI-checked. |
| `DEP-06` | hard | keep | Construct only in composition. CI-checked as 'no implementation imports'. |
| `DEP-07` | hard | keep, reword (atomic) | Absorbs FEAT-PUBLIC-01 and the feature half of MOD-API-01: one rule for the public surface of a feature (PC FEAT-DEP-01). |
| `DEP-08` | hard | keep | Contract declared and run in CI. Process rule, but it is what makes the others real. |
| `USECASE-01` | soft | keep | Threshold rule; matches ARCH-PC's 'justifies its existence'. |
| `REPO-01` | soft | keep | Threshold rule; matches ARCH-PC-REP-OPTIONAL-01. |
| `RUNTIME-01` | hard | keep, reword (atomic) | Keep 'declare the runtime'. Drop 'MUST NOT use an unsupported feature': `next build` already fails. |
| `RUNTIME-02` | hard | conditional: static-export | No secrets in the browser; provider rules are the boundary. Keep hard. |
| `BFF-01` | soft | soft | Guidance, not a gate. Keep as a short decision note. |

### DataSource (`ARCH-WEB-APP-DATASOURCE`)

| Rule | Now | Verdict | Why |
|---|---|---|---|
| `DS-INTERFACE-01` | hard | keep | PC DS-INTERFACE-01. Absorbs REP-INTERFACE-01: one rule for DataSource and Repository. |
| `DS-ONE-01` | hard | keep | One provider per DataSource (PC responsibility). |
| `DS-RESPONSIBILITY-01` | hard | keep | PC DS-RESPONSIBILITY-01. |
| `DS-RETURN-01` | hard | keep, reword (atomic) (see error model) | Keep, shorter. On web merits the DataSource boundary should return a value (Q1): `catch` is `unknown`, a rejection is silent, and Next strips a thrown Server Action error. |
| `DS-RETURN-02` | hard | keep | Pushed data stays a subscription. Absorbs UC-RETURN-02. |
| `DS-RETURN-03` | hard | keep | PC DS-RETURN-03: do not fake a stream. |
| `DS-SUBSCRIBE-01` | hard | keep, reword (atomic) | Keep 'one listener per call, released by unsubscribe'. 'Starts only when called' is COMPOSE-GLOBAL-01. |
| `DS-BOUND-01` | soft | conditional: a collection grows with users or content | Decided (Q4): limit + unique order, or precomputed; hard. Applied. |
| `DS-PARSE-01` | hard | keep, reword (atomic) | Atomic: a provider payload is parsed by a schema into a domain value. The assertion ban is EFLOW-ASSERT-01. |
| `DS-MALFORMED-01` | hard | keep, reword (atomic) | Keep 'a malformed record is an explicit error naming the record; never defaulted or dropped'. Ampm: half the documents are legacy-shaped. |
| `DS-MAPPING-01` | hard | keep | PC DS-MAPPING-01. |
| `DS-MAPPING-02` | hard | soft | Placement of mappers; PC makes it hard, but nothing breaks if a mapper moves. |
| `DS-EMPTY-01` | hard | keep | PC DS-EMPTY-01. |
| `DS-ERROR-01` | hard | merge into `ERR-MAP-01` | Translate once; pass an already-mapped error through unchanged. Same rule as ERR-MAP-01 / PC ERR-TRANSLATE-02. |
| `DS-SERVER-01` | hard | merge into `COMPOSE-SPLIT-01` | Also PLAT-WEB-NEXT-SERVERONLY-01; three owners for one constraint. |
| `DS-RULES-01` | hard | move out to `PLAT-WEB-NEXT-FB-RULES-01 / -EMU-01` | Already a platform rule; the architecture does not need to know about Firestore rules tests. |
| `DS-TEST-01` | hard | soft | Fake and contract test for every DataSource is overhead for a small app. A fake when consumers are tested; a shared contract test once real and fake both exist. |
| `DS-NAMING-01` | hard | keep, reword (atomic) | Interface `{Entity}DataSource`, provider-first implementation (PC DS-NAMING). Drop the per-provider list. |

### Repository (`ARCH-WEB-APP-REPOSITORY`)

| Rule | Now | Verdict | Why |
|---|---|---|---|
| `REP-INTERFACE-01` | hard | merge into `DS-INTERFACE-01` | Duplicate (0.71 similarity). |
| `REP-NAMING-01` | hard | merge into `DS-NAMING-01` | One naming rule. |
| `REP-DATASOURCE-01` | hard | merge into `DEP-02` | Restates the import rule. |
| `REP-RETURN-01` | hard | merge into `UC-RETURN-01` | One 'returns Outcome of domain values' rule. |
| `REP-SSOT-01` | hard | keep | PC REP-SSOT-01 (CORE-SSOT). |
| `REP-SSOT-02` | hard | keep | A failed read must not overwrite the cache (PC REP-SSOT-02). |
| `REP-FALLBACK-01` | hard | keep | PC REP-FALLBACK-01. |

### Domain (`ARCH-WEB-APP-DOMAIN`)

| Rule | Now | Verdict | Why |
|---|---|---|---|
| `DOM-PURE-01` | hard | keep | No I/O or ambient state. Absorbs the ambient-state half of UC-IO-01. |
| `DOM-CLOCK-01` | hard | keep (see parity) | Mirrors your Postgres rules ARCH-BE-TIME-01 / SVC-TIME-01 (inject the clock). Absorbs the clock part of UC-IO-01 and PLAT-WEB-NEXT-DATA-NONDET-01's principle. |
| `DOM-VALUE-01` | hard | soft | `readonly` everywhere is ergonomic overhead in TypeScript. |
| `DOM-SERIAL-01` | hard | soft | Matters for Server-to-Client props and stored snapshots. Absorbs COMP-BOUNDARY-01. |
| `DOM-INVARIANT-01` | hard | soft | 'Parse, don't validate' as a style; not a failure-preventer at this size. |
| `DOM-VOCAB-01` | hard | soft | Closed sets as unions. Absorbs DOM-TABLE-01. |
| `DOM-TABLE-01` | soft | merge into `DOM-VOCAB-01` | A style of expressing VOCAB-01. |
| `DOM-TABLE-02` | hard | move out to `lint: switch-exhaustiveness-check` | Exhaustive switch is a compiler/lint rule; keyword-list completeness is test guidance. |
| `DOM-TIME-01` | hard | keep, reword (atomic) | Keep 'explicit timezone; dates are date-only'. Ampm: `startOfDay` is local time while `formatDate` is SAST. |
| `DOM-DETERMINISM-01` | soft | soft | Order-independent aggregation; a real lesson, but guidance. |
| `DOM-NAMING-01` | soft | soft | PC FEAT-ANTI-02 is the model; soft. |

### UseCase (`ARCH-WEB-APP-USECASE`)

| Rule | Now | Verdict | Why |
|---|---|---|---|
| `UC-LOGIC-01` | hard | keep | PC UC-LOGIC-01. |
| `UC-SINGLE-01` | hard | keep, reword (atomic) | One operation per UseCase; naming moves to UC-NAMING-01. |
| `UC-ORCH-01` | hard | conditional: orchestrators exist | Orchestrators are rare in a web app; keep as 'if you have one, it has no logic'. Absorbs UC-ORCH-02. |
| `UC-ORCH-02` | hard | merge into `UC-ORCH-01` | Same orchestrator rule. |
| `UC-IO-01` | hard | merge into `DOM-PURE-01 / DEP-02` | Framework imports are DEP-02; ambient state and the clock are DOM-PURE/DOM-CLOCK. |
| `UC-STATELESS-01` | hard | keep | No module-level state. A real cache-bug class and cheap. |
| `UC-RETURN-01` | hard | keep (see error model) | Returns Outcome of domain values. Absorbs REP-RETURN-01. |
| `UC-RETURN-02` | hard | merge into `DS-RETURN-02` | Observable data stays observable up the stack: one rule. |
| `UC-ERROR-01` | hard | merge into `EFLOW-SWALLOW-01 / EFLOW-RETURN-01` | Three clauses, each stated elsewhere. |
| `UC-CANCEL-01` | hard | merge into `ERR-CANCEL-01` | Plumbing an abort signal through every UseCase is overhead; the rule that matters is that an abort is not an error. |
| `UC-WRITE-01` | hard | keep | Decided (Q3): atomic in one store, no exception; UC-WRITE-02 added for cross-store writes. Applied. |
| `UC-SIDE-01` | hard | soft | Contained side effects; guidance. |
| `UC-NAMING-01` | hard | soft | Over-specified (type and factory names and path). |
| `UC-TEST-01` | hard | soft | 'Every decision branch has a test' is a coverage mandate; PC has one testing rule in total. |

### Hook (`ARCH-WEB-APP-HOOK`)

| Rule | Now | Verdict | Why |
|---|---|---|---|
| `HOOK-LOGIC-01` | hard | keep | PC VM-LOGIC-01. |
| `HOOK-DEPS-01` | hard | soft | Dependencies from a context, not a singleton: a testability convention. |
| `HOOK-STATE-01` | hard | soft (see state shape) | A discriminated union is idiomatic TypeScript and cheap, but it prevents a bug class that has not yet appeared in the pilot. Soft until it does (Q2). |
| `HOOK-SCOPE-01` | soft | soft | Labelled soft but worded MUST; reword. |
| `HOOK-MAP-01` | hard | keep | PC VM-FORMAT-02. |
| `HOOK-FORMAT-01` | hard | keep, reword (atomic) | Formatting happens in the Hook, with an explicit locale (PC VM-FORMAT-01). Timezone is DOM-TIME-01. |
| `HOOK-ERROR-01` | hard | keep | Store the full error (PC ERR-STATE-01). |
| `HOOK-ERROR-02` | soft | soft | retry / clear error (PC ERR-STATE-02 is soft). |
| `HOOK-RACE-01` | hard | keep, reword (atomic) | Ignore results after unmount/input change (PC VM-JOB-01). Real bug class; make it one clause. |
| `HOOK-CLIENT-01` | hard | drop | React and Next already fail the build when a hook is used in a Server Component. |
| `HOOK-SERVER-01` | hard | merge into `DEP-04` | Same boundary, server variant. |
| `HOOK-ANALYTICS-01` | soft | soft | PC VM-ANALYTICS-01. Absorbs OBS-ANALYTICS-01. |
| `HOOK-NAMING-01` | hard | soft | Explicit return type duplicates PLAT-WEB-TS-HOOKS-01. |
| `HOOK-TEST-01` | hard | soft | Testing convention. |

### Component (`ARCH-WEB-APP-COMPONENT`)

| Rule | Now | Verdict | Why |
|---|---|---|---|
| `COMP-SPLIT-01` | hard | keep | Only the root view calls the Hook (PC VIEW-SPLIT-02). |
| `COMP-STATE-01` | hard | soft | Three checks in one. Keep 'handle every state' as soft; drop the error-wording clause (EFLOW-PRESENT-01). |
| `COMP-PROPS-01` | hard | keep, reword (atomic) | Keep 'data arrives as props' (PC VIEW-STATE-01). The `on{Event}` naming becomes a soft naming note. |
| `COMP-LOCAL-01` | hard | keep | PC VIEW-LOCAL-01. |
| `COMP-DI-01` | hard | keep | PC VIEW-COMPONENT-01. |
| `COMP-BOUNDARY-01` | hard | merge into `DOM-SERIAL-01` | Same constraint stated twice; Next fails the build for most violations anyway. |
| `COMP-SERVER-01` | hard | conditional: server | Server shell: no hooks/state. Soft. |
| `COMP-STATIC-01` | hard | conditional: static-export | Server Components fetch no runtime data. Keep hard: it fails silently with stale numbers. |
| `COMP-LEAN-01` | soft | merge into `MOD-SIZE-01` | A second size rule (150 lines) contradicts MOD-SIZE-01 (300). One rule, one number. |
| `COMP-NAMING-01` | hard | soft | Page/View suffixes are a convention. |
| `COMP-TEST-01` | hard | soft | How to test components belongs in QG-WEB-TESTING; soft here. |

### Composition (`ARCH-WEB-APP-COMPOSITION`)

| Rule | Now | Verdict | Why |
|---|---|---|---|
| `COMPOSE-FACTORY-01` | hard | soft | Prescribes an API name (`createApp`). The requirement is GLOBAL-01. |
| `COMPOSE-GLOBAL-01` | hard | keep | Nothing runs at import. Found in Ampm (SDK apps created at module scope). |
| `COMPOSE-CONFIG-01` | hard | keep, reword (atomic) | Split: 'environment read only in composition' (hard, lintable) and 'validated at start' (soft). Absorbs COMPOSE-CHOICE-01. |
| `COMPOSE-SDK-01` | hard | keep | Once per configured app (fixed after the Ampm run). |
| `COMPOSE-ENV-01` | hard | conditional: more than one environment per build | Split in two: named app per environment; a switch rebuilds the graph. Applies only to multi-environment builds. |
| `COMPOSE-ENV-02` | soft | conditional: more than one environment per build | Soft: show the active environment where a write can happen. |
| `COMPOSE-CHOICE-01` | hard | merge into `COMPOSE-CONFIG-01` | 'Fail loudly on bad config' is the validation half of CONFIG-01. |
| `COMPOSE-CONTEXT-01` | hard | soft | A React mechanism (context provider). Keep the idea soft; the how moves to PLAT-WEB-REACT-PATTERNS. |
| `COMPOSE-SPLIT-01` | hard | conditional: server | Server graph is server-only. Absorbs DS-SERVER-01. |
| `COMPOSE-LAZY-01` | soft | drop | Bundle-size nicety, soft already; measure before it earns a rule. |
| `COMPOSE-TEST-01` | hard | soft | A testing convention. |

### Feature structure (`ARCH-WEB-APP-FEATURE-STRUCTURE`)

| Rule | Now | Verdict | Why |
|---|---|---|---|
| `FEAT-STRUCT-01` | hard | keep, reword (atomic) | Folder layout; PC FEAT-PLACE rules are separate atomic rules. |
| `FEAT-PLACE-01` | hard | keep, reword (atomic) | Five placements in one rule. Make it a table in the doc, not a rule (PC uses four atomic ones). |
| `FEAT-ROUTE-01` | hard | conditional: Next.js App Router | Routes only compose features. |
| `FEAT-ROUTE-02` | hard | keep | Cross-feature composition in the route (PC COMP-ROOT-01). |
| `FEAT-PUBLIC-01` | hard | merge into `DEP-07` | Export side of the same public-surface rule. |
| `FEAT-SHARED-01` | hard | soft | PC COMP-PROMOTE-01 is soft. |
| `FEAT-SHARED-02` | hard | keep | PC COMP-CORE-01. |
| `FEAT-SUB-01` | soft | soft | Already soft. |
| `FEAT-NAME-01` | hard | keep | PC FEAT-NAME-01/02 (no `Impl`, provider first). |
| `FEAT-TEST-01` | soft | drop | Test file placement is a tool convention. |

### Modules and packages (`ARCH-WEB-APP-MODULES`)

| Rule | Now | Verdict | Why |
|---|---|---|---|
| `MOD-SIZE-01` | soft | soft | One size rule, with its numbers justified (PY uses 400/800; this says 300/600). Lintable `max-lines`. |
| `MOD-COHESION-01` | hard | soft | 'Describable without the word and' is subjective; hard but unverifiable is the worst combination. |
| `MOD-FUNC-01` | soft | keep, reword (atomic) | Size is lint; 'compute vs I/O split' is the useful half. Two soft rules. |
| `MOD-API-01` | hard | keep, reword (atomic) | Keep 'explicit exports, no `export *` in a public surface' (lintable). The import half is DEP-07. |
| `MOD-CYCLE-01` | hard | keep | No cycles (PC DI-MODULE-04). Lintable. |
| `MOD-NAME-01` | hard | keep | No utils/helpers/common (PC FEAT-ANTI-01). |
| `MOD-SPLIT-01` | hard | move out to `workflow / ORCH` | A refactoring procedure, not an architecture rule. |
| `MOD-FACADE-01` | hard | drop | Niche migration guidance. |
| `MOD-PACKAGE-01` | hard | conditional: a shared package exists | Direction never reverses. Absorbs MOD-PACKAGE-02. |
| `MOD-PACKAGE-02` | hard | merge into `MOD-PACKAGE-01` | Logic used by app and function lives once, in the package. |
| `MOD-PACKAGE-03` | hard | conditional: a shared package exists | Soft: do not extract before the boundary is enforced. |

### Errors (`ARCH-WEB-APP-ERR-CLASSES / -ERR-FLOW`)

| Rule | Now | Verdict | Why |
|---|---|---|---|
| `ERR-TYPE-01` | hard | keep | PC ERR-TYPE-01. |
| `ERR-MAP-01` | hard | keep | Translate exactly once, at the DataSource (PC ERR-MAP-01). Absorbs DS-ERROR-01. |
| `ERR-UNKNOWN-01` | hard | keep | PC ERR-UNKNOWN-01. |
| `ERR-CANCEL-01` | soft | soft | Abort stays distinguishable. Absorbs UC-CANCEL-01. |
| `EFLOW-RETURN-01` | hard | keep | Decided (Q1): value at DataSource and Hook boundaries; middle layers may throw. Applied. |
| `EFLOW-SWALLOW-01` | hard | keep | No swallowed errors. Largely lintable (`no-empty`, floating-promise rules). |
| `EFLOW-LOG-01` | hard | soft | Log once; guidance. |
| `EFLOW-CONTEXT-01` | hard | merge into `OBS-REDACT-01` | The no-secrets/PII half is REDACT-01; the 'carry the next action' half is guidance. |
| `EFLOW-VALIDATE-01` | hard | keep, reword (atomic) | One rule for untrusted input (forms, URL, payloads). Absorbs the 'untrusted' part of DS-PARSE-01. |
| `EFLOW-ASSERT-01` | hard | keep | No `as`/`!`/`@ts-ignore` over unchecked data. Lintable. Absorbs the assertion clause of DS-PARSE-01. |
| `EFLOW-PRESENT-01` | hard | soft | One shared error-presentation module is right at scale, not for a small app. |
| `EFLOW-NETWORK-01` | hard | soft | PC ERR-NETWORK-01 is soft. |
| `EFLOW-RETRY-01` | hard | move out to `PLAT-WEB-HTTP-RETRY-01` | Retry policy lives at the transport; the platform doc already has it. |
| `EFLOW-BOUNDARY-01` | hard | keep, reword (atomic) | Keep one owner: a route boundary reports once and offers retry. PLAT-WEB-NEXT-BOUNDARY-01 and PLAT-WEB-RP-BOUNDARY-01 currently restate it. |

### Observability (`ARCH-WEB-APP-OBS`)

| Rule | Now | Verdict | Why |
|---|---|---|---|
| `OBS-LOG-01` | hard | soft | 'No `console.*` in committed code' is lintable; an injected logger is a scale-up. |
| `OBS-LOG-02` | hard | soft | Structured logs; guidance. |
| `OBS-LOG-03` | hard | drop | Obvious. |
| `OBS-REDACT-01` | hard | keep | No secrets or personal data in logs, errors, reports or analytics. Atomic; POPIA makes it a production rule. |
| `OBS-RECORD-01` | hard | conditional: background jobs exist | Operation outcomes are visible in the UI (the Ilitha build line). Soft. |
| `OBS-RECORD-02` | hard | drop | Append-only record shape is detail. |
| `OBS-REPORT-01` | hard | soft | Five requirements in one; split or soften. |
| `OBS-CORRELATE-01` | soft | drop | Niche. |
| `OBS-ANALYTICS-01` | hard | merge into `HOOK-ANALYTICS-01` | Same concern as PC VM-ANALYTICS-01. |

## 8. Platform rules (flagged, not itemised)

`platforms/web/` has 123 rules. The web-spa documents (`PLAT-WEB-STYLING`, `-STATE`, `-FIREBASE`, `-A11Y`, `-REACT`, `-DEPLOY`)
predate this work and are not audited here. The new Next.js, React, Firebase and theme rules have these issues.

**Duplicated or multiply-owned.** `PLAT-WEB-NEXT-BOUNDARY-01` and `PLAT-WEB-RP-BOUNDARY-01` restate `ARCH-WEB-APP-EFLOW-BOUNDARY-01`;
`PLAT-WEB-NEXT-SERVERONLY-01` against `DS-SERVER-01`; `PLAT-WEB-NEXT-FB-AUTH-01` against `PLAT-WEB-FB-AUTH-01` and `PLAT-WEB-STATE-CTX-02`
(0.80 token similarity); `PLAT-WEB-A11Y-FOCUS-01` against `PLAT-WEB-STYLE-FOCUS-01` (identical, pre-existing).

**Enforced by the build, so not rules:** `PLAT-WEB-NEXT-ASYNC-01` (Next 16 removed synchronous access),
`PLAT-WEB-NEXT-STATIC-CONFIG-01` and `-ROUTEHANDLER-01` (the build rejects unsupported features), `PLAT-WEB-NEXT-DATA-MODEL-01`.

**Process or ops, not architecture:** `PLAT-WEB-NEXT-VERSION-01`, `PLAT-WEB-NEXT-FB-DEPLOY-01`, `PLAT-WEB-NEXT-FB-COST-01`,
`PLAT-WEB-NEXT-STATIC-ENV-01`. Keep as a deployment runbook section, not as MUST rules.

**Over-specified.** The theme document has 12 rules for a colour system. Keep `-THEME-01`, `-LAYER-01`, `-DARK-01` (merging
`-DARK-02`) and `-CONTRAST-01`; make `-VIZ-01..03` one soft rule; drop `-SWITCH-01`, `-SETUP-01` and `-TYPE-01` (setup and tooling).
`PLAT-WEB-RP-REF-01` and `PLAT-WEB-RP-OPTIMISTIC-01` are niche; `PLAT-WEB-RP-KEY-01`, `-DEPS-01` and `-STRICT-01` are lint or configuration.

**Keep, they came from real failures or real law:** `PLAT-WEB-NEXT-FB-SECRET-01`, `-ROLES-01`, `-RULES-01`, `-SIGNUP-01`, `-PERSIST-01`
(personal data on a shared device), `-INIT-01`, `PLAT-WEB-NEXT-STATIC-BROWSER-01`, `-ROUTES-01`, `-DIRECT-01`.

**Untested and server-runtime only:** the seven `PLAT-WEB-NEXT-DATA-*` rules. Nothing has exercised them. Hold them as soft until a
server-runtime project uses them.

## 9. Effect and proposed shape

| | Now | After the verdicts |
|---|---|---|
| Architecture rules | 143 | 112 |
| Always-on hard | 124 | 61 |
| Soft | 19 | 38 |
| Conditional (trigger stated) | 0 | 12 |
| Removed (merged, moved, dropped) | 0 | 31 |

Two further steps beyond the rule count, both about load:

- **Split the documents into core and optional.** Core, always loaded: the overview, Domain, DataSource, UseCase, Hook, Component,
  Feature structure, error classes. Optional, loaded on a trigger: Repository (more than one source), Composition (the
  multi-environment and server-split parts), Modules and packages (a shared package exists), Observability beyond redaction.
  The core documents are 14,700 of the 21,700 architecture words today, before any trimming.
- **Cut the repetition.** Each document ends with a list of violations that restates its rules (about 1,000 words in all), and
  each rule block carries a `violation_message` that repeats the statement. Together with the rule rewrites a target of
  roughly 14,000 architecture words is realistic; the onboarding load then falls well below today's 55k tokens. That target is
  a plan to test, not a measured result.

## 10. How to test the rules (the worktree)

The Ampm dashboard is the test bed, in a worktree on its own branch so the deprecated `main` is untouched.

1. **Baseline now.** Already measured against the current rules: 52 import violations across four rules; five modules over 600 lines;
   half the data in an older shape; one login race; no tests. Aggregation tests (60) and the generated gates pass.
2. **After review, change the rules** (nothing is changed yet) and regenerate the import contract.
3. **Refactor one feature** (Learning) to the layered shape and re-measure: violations, module sizes, and the characterisation
   tests that must stay green.
4. **Judge each rule by what it did on the pilot:** did it catch something real, did following it cost more than it saved, did
   two rules say the same thing. Those answers, not this document, decide what stays.

## 11. What changes once you have reviewed

Apply the accepted verdicts as edits to the architecture documents (atomic rewrites, merges, moves, a conditional trigger
field on each conditional rule), add the rules Q3 to Q5 call for, generate the lint configuration for the lintable rules,
regenerate the index, and keep a changelog of every rule ID that was merged or removed so citations can be updated.
