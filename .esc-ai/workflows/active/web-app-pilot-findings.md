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

---

# Slice 2: Notifications (writes, a use case, two projects)

Commits `1e99a8e`, `22819f5` in the pilot branch. Tested with 108 tests, 8 of them against the Firestore emulator (`firebase emulators:exec`), so no write touched dev or prod. Page is 643 lines in the original and 8 files (largest 236 lines) now.

## What it exercised
- `UC-WRITE-02`: the original `promoteNotificationToProd` did `addDoc` into prod (new id every call), then marked dev. A failed second write plus a retry duplicated the notification in prod, which real users receive. The new use case upserts under the dev id first and marks second; retry-after-failure is a test in both the fake and the emulator and leaves one prod document. **A real bug fixed, not a style gain.** Behaviour change: the prod document id is now the dev id (it was an auto id).
- A UseCase that earns its place (two stores, ordering, partial-failure message) while create is a plain DataSource call (no forwarding UseCase, `UC-LOGIC-01`).
- `EFLOW-RETURN-01` (value at boundaries): plumbing was `if (!x.ok) return x` four times in the use case. Cheap at this size.
- Contract test shared by the fake and the emulator (`DS-TEST-01`, now in the testing gate): **found a wrong error check in my own earlier work** (below).

## Findings that change the framework
1. **`instanceof FirestoreError` never matches.** Firestore throws `FirebaseError` with a `code`. It compiles, passes against a fake, and mis-reports every real failure as "unexpected", including permission-denied. It was in my Learning store and in the framework's own example. Found only by the emulator test. Docs fixed (`b974877`). Supports keeping "test the translation against the provider's emulator" as a rule, not advice.
2. **`COMPOSE-ENV-01` says a switch must discard the graph.** The pilot decision (one cache per environment) kept one graph per environment instead, which is fine only because neither holds a subscription. The rule's wording ("releasing every subscription") should allow retaining a graph with no live subscriptions.
3. **Promotion needs both environments at once.** A graph built "for the active environment" cannot express "always copy dev to prod". The graph carries both stores and exposes the active one. The rule set has no word for this; the multi-environment rules assume one active environment.
4. **The layout needs a home for shared DataSource utilities.** `toAppError` is now written twice (Learning and Notifications). `shared/` is forbidden from importing the SDK by the template rules (correctly), so a shared Firestore helper has nowhere to live. Proposed: a `data/` folder at the same level as `features/`, allowed to import the SDK, imported only by DataSources.
5. **The check caught two layout mistakes of mine again** (a use case filed under `domain/`, a component importing the form type from the domain). Both are the kind of drift the architecture exists to stop; the import check is earning its keep.
6. **Cost:** original `useNotifications` module-level cache is gone (no per-environment cache for notifications; the graph holds none). The page now re-reads on mount. Cheap here (2 dev, 15 prod documents).
7. `DS-PAGE-01`: the list reads the whole collection. A known violation, harmless at 15 documents; the rule has a trigger ("a collection that grows") that a project must judge, which is the local-rule point.

## Not exercised
`server` runtime rules, observability, security-rules tests (the emulator ran without rules), real login race, the other pages.

## Applied after slice 2
- `COMPOSE-ENV-01` reworded: switching gives consumers the new environment's graph and releases live subscriptions; a graph holding none may be kept.
- New `COMPOSE-ENV-03`: an operation spanning environments receives each store explicitly and does not depend on the active one.
- New `FEAT-DATA-01` and a top-level `data/` folder for code shared by DataSources; the `web-app` template gained `web.shared-data-only-for-datasources`. In the pilot one `toAppError` replaced two copies, and the check passes with 0 violations in new code.

---

# Generated lint configuration

`esc-exec architecture lint-config generate` (execution framework) writes a TypeScript `eslint.config.ts` from the lintable rules and the project's `.esc-ai/lint-limits.yaml`. It fails if a required limit is undeclared: the framework holds the mapping, the project holds the numbers. `esc-exec architecture lint-config coverage` lists what is covered and how far.

## Result on the pilot
- New code (`features`, `composition`, `data`, `shared`): **0 problems** after fixing what the first run found. The old pages: **151** (47 over-long functions, 34 non-null assertions, 30 over-complex functions, 17 floating promises, 11 `any`, 6 over-long modules, 4 `console`, 2 assertions).
- The first run found 4 real problems in code written to follow the rules: two floating promises in the hooks, a 210-line form component, and a mapper with 16 `??` defaults. All fixed (the form is split into sections; the legacy defaults are one explicit object).
- `package.json` gained a `lint` script scoped to the new code, so the generated verification profile now includes the lint gate and no longer notes that nothing lints. That scoping is a ratchet: it can widen as pages move.

## Where a rule is only partly lintable (recorded in `COVERAGE`)
1. `EFLOW-ASSERT-01`: a linter can ban `@ts-ignore`, non-null assertions and `{...} as T`, but not tell a plain `x as T` over unchecked data from a legitimate narrowing (ESLint `assertionStyle: 'never'` flagged 128 sites, most of them fine, including the parsers). Kept partial; the rest stays with a reviewer.
2. `MOD-FUNC-01`: ESLint's `complexity` counts `??`, so a mapper with many defaults trips it. It was a fair signal here (it pushed the legacy defaults into one object) but is noisy for mapping code.
3. A JSX component is mostly markup, so one function-length limit flags every component. The generator accepts a separate `maxComponentFunctionLines`; without it the rule is unusable on React.
4. `MOD-NAME-01` is a folder-name rule, not a lint rule; it is now generated into the web-app template as `web.no-grab-bag-names` (`forbidden-path`). On the pilot it flags only the old `src/utils` and `src/common`; moving `aggregations` and `dateUtils` into `shared/domain` also surfaced `DOM-CLOCK-01` violations, fixed by `shared/clock/` and passing `now` into the aggregations.

Marked exercised: `MOD-NAME-01`, `MOD-SIZE-01`, `MOD-FUNC-01`, `MOD-CYCLE-01`, `MOD-API-01`, `EFLOW-SWALLOW-01`, `OBS-LOG-01`.

---

# Slice 3: Portal content

Legacy banners, sections and section items (`portal_items`, `portal_sections`) as `features/portal`: domain, two stores (`PortalItemStore`, `PortalSectionStore`) with a Firestore implementation, a fake and one contract suite each, two use cases, and a `usePortal` hook. The 1,863-line `Portal.tsx` page stays one file for now; it swapped its hook and types and lost its own order-calculation code. The promo items and destinations on the same page are not migrated.

## Result
- 44 slice tests, 159 in the whole suite, all passing against the real Firestore emulator. New code: `tsc` clean, lint 0 problems, architecture check 0 violations.
- Read verified in Chrome on dev and prod with a temporary admin sign-in (both accounts deleted afterwards): banners, sections and lazily opened section items match what is stored, including the dev item that predates `placements` and `promoted_at`. No write was clicked against a real project; writes are covered by the emulator suite.

## What the slice exercised
- `UC-WRITE-01` now **exercised**. The reorder is one batch inside one store, and the contract test (fake and emulator alike) proves that a reorder naming a missing id changes nothing.
- `UC-WRITE-02` a second time (portal promote), with the clock injected (`now`), which `DOM-CLOCK-01` required.
- `DS-PARSE-01` and `DS-MALFORMED-01` against real documents: the parser needed `placements` and `promoted_at` optional (found by reading both projects first), and an unknown stored field (`collectionPath`) is ignored. A malformed document names its id and field, never its contents (tested).
- A use case that reads from the store instead of the page's state: `setHomeBanner` computes the next banner position from `listBanners()`, so a stale page cannot hand out a duplicate position.

## What it did not exercise, and why
1. **No live listener, no Repository.** I expected Portal to cover both; it reads once with `getDocs` and each entity has one source. `REPO-01` correctly says there is nothing to build, so the Repository rules (`REP-SSOT-01/02`, `REP-FALLBACK-01`) stay unproven. A real consumer needs a live listener plus a cache; none exists in this app yet.
2. `DS-PAGE-01`: the four collections hold 3 to 4 documents in each project, so the unbounded reads are a documented gap, not a cost.

## Findings
1. **Refetch after a write, not optimistic local state.** The old hook patched its own lists after each write (and had a branch to sync banners with section items). The new hook re-reads the affected lists, so the screen shows what is stored. It costs a few reads on a tiny collection; it removed the state-sync code (the old hook was 242 lines, `usePortal` is about 100). Worth a sentence in the Hook rules if a second slice agrees.
2. **A legacy page contract rejects on failure; the architecture returns values.** The existing modals and cards rely on thrown errors. `usePortal` returns `Outcome` and a labelled temporary adapter (`usePortalForPage`) turns a failure into a rejection with the readable message. The rule held; the adapter is the cost of not rewriting the page in this slice, and it is deleted when the page becomes a view.
3. **The page had to change shape in small ways:** the forms no longer send the promotion marker (the store owns it: `update` never writes `promoted_at`), `promoted_at` became `promotedAt`, and the home-banner toggle lost its caller-side `maxOrder` calculation. A reviewer reading the page diff sees these as behaviour-preserving; the contract tests are what prove it.
4. **A test graph builder (`src/test/graph.ts`)** was needed once the graph grew a third feature: two older hook tests each listed every graph member. One helper, tests name only what they care about.
5. **Duplication to watch, not yet to extract:** the cross-project promote use case now exists twice (notifications, portal items) with the same shape and different stores. Two copies, different types; a third would justify a shared helper (`FEAT-SHARED-01`).
6. **Environment gotcha, not a rule:** the dashboard signs out any account not in its `VITE_DASHBOARD_EMAILS` allow-list without a message, which looked like a login failure. Vite's dependency re-optimisation also reloads the page mid sign-in the first time.

---

# Slice 4: Promotion items and destinations

The current content model on the Portal page (`promo_items`, `promo_destinations`) as `features/promotions`: domain (grouping by destination, destination validation), two stores with Firestore, fake and contract suites, a `saveDestination` use case, `usePromotions`, and a temporary page adapter. Also extracted `shared/useCases/promoteAcrossProjects`, now used by portal and promotions, and `orThrow` in `shared/outcome`. The page lost its grouping loop and both old hooks; the six record interfaces in `types/firestore.ts` that nothing uses any more were deleted.

## Result
- 206 tests across the whole suite pass against the real emulator (47 more than the 159 before this slice, covering the slice and the extraction); `tsc` clean, lint 0 problems, architecture check 0 violations in new code.
- Read verified in Chrome on dev and prod with a temporary admin account (deleted afterwards): destinations, items grouped under each destination in order, and the edit form's prefilled destinations and section. Prod output matches what the old page rendered. No write clicked against a real project.

## Findings
1. **The extraction rule worked as written.** `FEAT-SHARED-01` says move code to `shared/` when a second consumer needs it. Portal was the second copy and I noted it; promotions was the third, so I extracted, and a behaviour test now lives once. Notifications keeps its own version on purpose: it skips an already-promoted notification and tracks the prod id, which the other two do not.
2. **A data-loss bug the old code had, found by reading real data.** Promoting an item rewrote its prod copy from a mapped object that dropped the `sourcePortalItemId` field the migration script had put there. The domain now carries that field and a contract test proves an update and a promote keep it. Whether prod ever relied on the loss is unknown; the field is not read by the dashboard.
3. **Correction: the framework's `AppError` does have a `validation` variant** (`{ type: 'validation'; fieldErrors }`, `ARCH-WEB-APP-ERR-CLASSES`), and `PLAT-WEB-FORMS-SSOT-01` already requires the server to reuse the form's schema. The pilot's own copy of the union (`shared/outcome.ts`) had dropped it, so destination validation came back as `unexpected` with a message. That was the pilot diverging from the framework, not a framework gap; an earlier draft of this finding said otherwise and was wrong. Fix when the pilot's pages next change: add `validation` to the pilot union and return it from `saveDestination` and the notification form. Lesson: copy the framework's union verbatim.
4. **A boundary mapper earns its keep.** Stored destination fields are snake_case (`is_active`, `section_id`) and shared with the mobile apps, so the domain uses camelCase and `promotionMapper.ts` is the only file that knows both. A round-trip test (stored in, stored out) and an emulator test that reads the raw document guard the names the apps depend on.
5. **Two hooks became one read.** Items and destinations load together and fail together, so the page's separate loading and error states collapsed to one. If the destinations lookup ever needs its own error handling, split it then.
6. **`saveDestination` uses a merge write.** The old code chose between `updateDoc` and `setDoc` from the page's loaded list, so two editors could race on the choice. One merge write is create-or-update; an emulator test shows it keeps fields it does not know.

## Still not exercised
Repository, live listeners, `server` runtime, observability, and security-rules tests, as before. Both Portal slices read once; neither needed a Repository.

---

# Slice 5: the first `server`-runtime consumer (garage-management-system)

A different repository, on purpose: `/home/emmanuel/WebstormProjects/garage-management-system` is a Next.js app with Server Actions, untrusted form input, no auth and no database (an in-memory store, by design). Worked in a worktree (`../garage-management-system-pilot`, branch `esc-ai/web-app-pilot`), in four commits: characterization tests, the layering refactor, the Next.js 16.2 to 16.3 upgrade (its own step, `PLAT-WEB-NEXT-VERSION-01`), and Cache Components. Declared `frameworks.runtime: server` in `context/project-profile.yaml`.

## Result
- 60 tests (domain, schemas, store contract, use cases, actions called directly, hooks, composition); `tsc`, lint, the generated architecture lint, `next build` clean; the architecture check passes all 13 rules.
- The same browser flow (empty submit, valid submit, dashboard, detail, triage save, back to dashboard) gives identical text on the original and the refactor, on dev and on the production build. One difference found and fixed: the original showed each viewer's local time, mine showed UTC, because `HOOK-FORMAT-01` requires an explicit timezone. The workshop must declare it; set to `Africa/Johannesburg` as an assumption for the owner to confirm.

## Defects the original had, found by the work
1. **Every export of a `'use server'` file is a callable endpoint.** The original's two `'use server'` files exported six functions between them (`createFault`, `updateFault`, `listFaults`, `getFault` and the two form handlers). Next registered all six. Verified against the running original: an unauthenticated POST with an action id (taken from the build manifest, so an attacker needs the id to leak) listed customer records and overwrote a customer's name. The refactor registers only the two real entry points.
2. **Mass assignment.** `updateFault` did `{...existing, ...patch}` on a patch that was typed but never checked, so `id`, `customer_name` and `created_at` were overwritable. Pinned by a characterization test on the old code, then fixed: a strict schema per entry point rejects unknown keys, and the action picks only the form's named fields (a form also carries framework-added hidden fields, so a strict schema on the raw form fails).
3. **Silently frozen data.** On Next 16.2 (previous model) `/manager` was prerendered static at build, so its data was whatever the build saw. Under Cache Components the same read of an in-process store is still frozen unless the component calls `await connection()`: verified, the page builds as `Static`, and after a successful submission the dashboard still says "No faults waiting for triage". The platform did flag the other route (`params` awaited outside `<Suspense>`) but nothing flagged this one. Verified only for a read that resolves without I/O (an in-memory store); I did not test a real database client.
4. Smaller: a blank scheduled date was stored as `undefined` against a type of `string | null`; `isTriaged` is inferred from `updated_at !== created_at` (fine in practice, noted in the code).

## Rules exercised (marked `exercised`)
`COMP-SERVER-01`, `COMPOSE-SPLIT-01` (the server half; the app needs no client graph), `DOM-SERIAL-01`, `UC-STATELESS-01`, `FEAT-ROUTE-01`, `EFLOW-PRESENT-01`, `COMPOSE-FACTORY-01`, `HOOK-NAMING-01`. Platform rules exercised (they carry no marker): `NEXT-APP-THROW-01`, `NEXT-DATA-FETCH-01`, `NEXT-DATA-SUSPENSE-01`, `NEXT-DATA-MODEL-01`, `NEXT-SERVERONLY-01`, `NEXT-BOUNDARY-01`, `NEXT-CLIENT-01`, `NEXT-ASYNC-01`, `NEXT-VERSION-01`, `NEXT-LINT-01`, `FORMS-SSOT-01`.

Left `unproven` on purpose: `UC-NAMING-01` (see 7), `COMP-NAMING-01` (see 8), `COMP-STATE-01` (assumes a client `loading/ready/error` state that the server runtime replaces with Suspense and `error.tsx`), `FEAT-ROUTE-02` (one feature, nothing to compose), `OBS-REDACT-01` (nothing is logged), and the Repository, listener and security-rules rules (no consumer yet).

## Execution framework changes this forced (done, tested: 705 tests)
- The `web-app` template did not scan the `actions/` layer, so a Server Action importing an SDK or a DataSource implementation was invisible to the SDK and implementation rules. It now does, plus a new `web.actions-below-the-ui`.
- `InMemory*` was not recognised as a DataSource implementation.
- New rule type `required-import`, used by `web.server-graph-imports-server-only`; new `web.server-graph-not-in-client-code`. Both proven by tests that plant the violation.
- The lint generator hard-coded `src/**` and always wrote `eslint.config.ts`. It now detects a project without `src/` and takes `--output`, so it can sit beside a Next project's own config.

## Proposals for the architecture framework (1 to 6 applied on the user's go-ahead: new `PLAT-WEB-NEXT-DATA-DYNAMIC-01` and `PLAT-WEB-NEXT-APP-ACTION-01`, `DATA-MODEL-01` made version-conditional, prose notes on revalidation, soft 404 and native forms)
1. **New hard rule `PLAT-WEB-NEXT-DATA-DYNAMIC-01`**: a Server Component that reads data which changes between requests but that Next cannot see changing (an in-process store, any read that resolves without I/O) MUST make the read request-time with `await connection()` inside `<Suspense>`, or cache it deliberately; otherwise the build-time value is frozen into the page. Defect 3.
2. **New hard rule `PLAT-WEB-NEXT-APP-ACTION-01`**: every export of a `'use server'` file is a public endpoint, so it MUST be a deliberate entry point, take its input as `unknown`, validate it with a schema that rejects unknown keys, and check the caller's authority wherever the data is not public; the file MUST NOT export anything else. This is the Server Action counterpart of `PLAT-WEB-NEXT-FB-CALLABLE-01`, which exists only for Firebase callables. Defects 1 and 2. Generic, applies to every `server` project.
3. **`PLAT-WEB-NEXT-DATA-MODEL-01` is version-specific as written.** It says to set `partialPrefetching`, which exists only from Next.js 16.3 (the installed 16.2.10 does not know it; 16.3.4 does). Reword: "where the targeted Next.js has it".
4. **`PLAT-WEB-NEXT-APP-REVALIDATE-01` prose.** With Cache Components and uncached request-time reads, removing every `revalidatePath` left the flow correct (verified on a production build, including navigating back to the dashboard). The rule says to invalidate cached results, which is right, but a reader can take it as "always call `revalidatePath`". One clarifying sentence: nothing cached, nothing to invalidate.
5. **`PLAT-WEB-NEXT-BOUNDARY-01` prose.** A `notFound()` inside the streamed part returns HTTP 200 with the not-found page (a soft 404), because the status line leaves with the static shell. Verified. Harmless for an internal tool, wrong for a public page.
6. **`PLAT-WEB-FORMS` assumes `react-hook-form`.** This app uses native `<form action>` with `useActionState` and one server-side schema; the validation error shape (`fieldErrors`) carried over unchanged and the rules held. Add a short native-form variant.

## Observations that are not proposals yet
7. **`UC-NAMING-01` is followed by this consumer and was silently not followed by the Ampm pilot** (`promoteNotification.ts`, `portalUseCases.ts`). Nothing checks it. Either make it checkable (a filename pattern check) or relax it; the two pilots disagree.
8. **`COMP-NAMING-01` says a feature's shell is `{Feature}Page.tsx`.** A feature with three screens has three shells; I named them per screen (`SubmitFaultPage`, `ManagerDashboardPage`, `FaultDetailPage`). The rule needs a word on multi-screen features.
9. **The framework is silent on what a Server Action contains and imports.** I decided: a thin host (pick the form's named fields, call the use case, map the `Outcome`), imports no component or hook, never a DataSource implementation; and the server shell passes the action to the client root view as a prop, so client code imports no server module and a hook test needs no module mock. `HOOK-DEPS-01` mentions only a provider context. Worth a short section in `hook.md` or `overview.md`.
10. **Use cases only for the two writes.** Reads go from the Server Component shell straight to the store interface (`DATA-FETCH-01` allows it). The justification for the write use cases is not the `USECASE-01` threshold but that untrusted input must be validated whichever entry point arrives (a Route Handler tomorrow); putting the schema in the use case gives every entry point the same checks.
