# Web App Readiness — A Pragmatic-Clean `web-app` That Scales

`workflows/archive/web-platform-docs.md` closed the `web-app` follow-ups that
`ampm-backend`'s content dashboard needed. An audit on 2026-10-17, driven by the
planned refactor of `ilitha-ops-firebase` into a Next.js app, found two problems:

1. **The `web-app` architecture is a sketch, not an architecture.** Two docs and
   5 rules, against `ARCH-PC` (12 docs, 113 rules) and `ARCH-PY` (12 docs, 109
   rules, 32 enforced in CI). The layers that make those scale — one doc per
   layer, a composition root, module/growth rules, a layer contract run in CI —
   do not exist for web.
2. **The surrounding platform docs have gaps** (React/TS/state scoped to the SPA
   only, Firebase written for Vite, a two-rule theme doc, about ten Next.js
   rules) and **nothing is mechanically enforced** (all 70 web rules are
   `enforced_by: [reviewer]`; the one automatic check scans `.kt`/`.java`).

This workflow builds `web-app` as a faithful restatement of **pragmatic clean**
(`ARCH-PC`), at the same depth, then fills the platform gaps and the
enforcement gap.

**Driver:** `ilitha-ops-firebase`, the first consumer. An internal, login-only
dashboard on Firebase: the browser reads Firestore under security rules and
writes through callable Cloud Functions; a pure aggregation pipeline turns
uploaded workbooks into snapshots. No server of its own is needed, so it
targets Next.js as a **static export** with no BFF. The docs must cover that
and the server-capable case (`ampm-backend`'s dashboard) with one set of layers.

**Out of scope (still deferred, see `missing-files.md`):** `PLAT-WEB-NEXT-CONTENT`,
its deploy doc and `ORCH-WEB-CONTENT` (no project consumes `web-content`); the 23
pre-existing mobile design-system citation WARNs.

**Workflow:** Do NOT enter plan mode. This document, `architectures/pragmatic-clean/`
(structural reference for every layer doc), `architectures/python-app/`
(structural reference for composition, domain, modules, and the CI layer
contract), `architectures/web-app/` and `schemas/rule.yaml` provide the
planning needed. Phases 1–10 are in this repository; Phase 9 is in
`esc-ai-execution-framework` and is committed there.

**Commit after each phase.**

## How the layers map

| `ARCH-PC` layer | `web-app` equivalent | Notes |
|---|---|---|
| View | **Component** (Server or Client) | Renders; no logic, no data access. Owned today by `ARCH-WEB-COMPONENTS` (web-spa) |
| ViewModel | **Hook** (Client) | Formats for display, UI state and events; `Outcome`-typed state |
| UseCase / Orchestrator | **UseCase module** (plain TS) | Business logic and multi-step coordination; no React or framework imports |
| Repository (optional) | **Repository module** (optional) | Only for SSOT across several DataSources; same threshold logic as `ARCH-PC` |
| DataSource | **DataSource module** | Abstracts one provider, maps types, wraps errors. Runs in a Server Action/Route Handler (`server` runtime) or in the browser (`static-export` runtime) |
| Provider | Provider | REST API, Postgres, Firestore SDK, callable function. Not owned by this architecture |
| Domain / pipeline | **Domain package** (pure) | Entities, rules and transforms with no I/O and no framework; testable alone, shareable with Cloud Functions |
| Composition root | **Composition module** | The one place providers and data sources are built and wired |

The variant (`server` vs `static-export`) changes **where the DataSource runs**
and what Next.js features are available. It does not change the layers or the
direction of dependency. That is why one architecture carries both, rather than
two architectures with duplicated rules.

## Audit findings this workflow answers

| # | Finding | Phase |
|---|---|---|
| 1 | `web-app` has 2 docs / 5 rules; no per-layer docs, no composition root, no domain or module rules | 2–5 |
| 2 | Layer contract not declared as a checkable contract | 6, 9 |
| 3 | `ARCH-WEB-APP` forbids Client Components external calls and puts error mapping in the Server Action; neither fits `static-export` | 2 |
| 4 | `PLAT-WEB-REACT`, `-STATE`, `-FIREBASE`, `-STYLING` are `web-spa` only and not required by `ORCH-WEB-APP` (`PLAT-WEB-A11Y` is a deliberate exception: see the archived workflow's Outcome) | 1 |
| 5 | React 19 patterns, effects/derived state, error boundaries not covered | 7 |
| 6 | `PLAT-WEB-FIREBASE` is a Vite doc; nothing for Firebase on Next, callables, rules, emulator | 7 |
| 7 | `PLAT-WEB-DS-THEME`: two rules, Tailwind-config only, no chart tokens, dark mode is prose | 8 |
| 8 | Next.js rules thin: data fetching/caching, route boundary files, server-only guards, Server Action security, URL state, testing | 8 |
| 9 | All web rules `enforced_by: [reviewer]`; the only mechanical check scans `.kt`/`.java` | 9 |
| 10 | Wiring: `PROFILE_DOC_MAP`, orchestrator `requires`, dangling IDs `PLAT-WEB-HOOKS`, `PLAT-WEB-NEXT-STYLE` | 10 |

## Target size

Match the reference architectures so the docs scale the same way:

| | Docs | Rules | In CI |
|---|---|---|---|
| `ARCH-PC` | 12 | 113 | 0 |
| `ARCH-PY` | 12 | 109 | 32 |
| **`web-app` target** | 11–12 | 90–110 | 25+ |

Rule count is a check on coverage, not a goal. Do not pad; if a layer genuinely
has fewer rules, say why in the doc.

## Decisions (settled here; reverse only with a reason, in the Outcome)

1. **One architecture, two runtimes.** Keep `web-app`; add a project-profile
   field `frameworks.runtime: server | static-export` that selects the variant
   sections and the variant platform docs. No `web-app-static` architecture
   value. *(Revised from the earlier draft: with per-layer docs the runtimes
   differ only in the DataSource and in Next.js feature availability, so
   duplicating the layer docs would break the "one rule, one owner" principle in
   `.esc-ai/workflows/README.md`.)*
2. **Hooks do not call providers.** A hook calls a UseCase or a DataSource
   module through the composition root. The earlier idea of "hook is the one
   place a Provider is called" is rejected: it merges ViewModel and DataSource,
   which `ARCH-PC` separates for good reason.
3. **Rule IDs are stable.** Existing IDs (`ARCH-WEB-APP-*`, `PLAT-WEB-*`) keep
   their names; ownership may move to a new doc, wording may widen. New IDs
   follow `ARCH-WEB-APP-<LAYER>-<TOPIC>-NN`, as `ARCH-PC-DS-RETURN-01` does.
4. **Tailwind and Next.js versions are pinned** in the docs that depend on them
   (Phase 8). Confirm against the upstream docs at write time; Tailwind v4 is
   believed to define tokens in CSS (`@theme`), not `tailwind.config.ts`.

## Layer doc template

Every layer doc in Phases 3–5 follows the `ARCH-PC` layer-doc shape so they read
as one family:

- **Responsibility** — one paragraph, no "and"; what the layer owns and what it
  does not.
- **Structure** — folder layout and file naming for this layer.
- **Rules** — fenced ```rule blocks, `type`/`scope` decided per rule,
  `enforced_by` naming only roles that really check it (`ci` only with a real
  check from Phase 9), each with a ✅/❌ TypeScript example where the rule is
  not self-evident.
- **Boundary** — what may and may not cross the layer, as a table.
- **Error handling** — how this layer produces, maps or passes errors
  (cite `ARCH-WEB-APP-ERR-*`; do not restate).
- **Testing** — what is tested at this layer, with what double (a fake of the
  layer below, never a mock of the SDK; cite `QG-WEB-TESTING`).
- **Naming** — file and symbol names as rules.
- **Violations** — a short list of the common ways the layer is broken, each
  pointing at the rule.

Cite rules owned elsewhere by ID in prose. Never paste the same rule block into
two docs.

---

## Phase 1 — Make the generic web docs apply to `web-app`

Edit `platforms/web/react-typescript.md`, `state.md`, `firebase.md`,
`styling.md`. For each rule decide: architecture-agnostic (keep; widen the doc's
`architecture` to `[web-spa, web-app]`) or SPA-specific (keep; add one sentence
saying it applies to `web-spa` only). Decide explicitly: `PLAT-WEB-TS-STRICT-01`,
`-ANY-01`, `-PROPS-01`, `-CLEANUP-01` (agnostic); `PLAT-WEB-STATE-HOOK-02`
(`src/hooks/` is a path convention that must be reconciled with
`features/{feature}/hooks/`); `PLAT-WEB-ROUTE-GUARD-01` (SPA only;
`PLAT-WEB-NEXT-MW-01` is the Next equivalent).

`PLAT-WEB-STYLING` stays SPA-only; add a sentence pointing `web-app` and
`web-content` at `PLAT-WEB-DS-THEME` so the two approaches do not read as
competing.

Add `PLAT-WEB-REACT` and `PLAT-WEB-STATE` to `ORCH-WEB-APP`'s `requires`.

Verify: `python tools/validate.py` clean; `git diff` shows no `id:` line edits.

## Phase 2 — `ARCH-WEB-APP` overview rewrite and the project-profile field

Rewrite `architectures/web-app/overview.md` to the full `ARCH-PC` overview
shape, keeping `ARCH-WEB-APP` and its two existing rules' IDs:

- Layer stack and data flow for the mapping table above, with the two runtimes
  shown side by side.
- **Layer boundaries — what may NOT cross** (table): DataSource → above (provider
  types, provider errors); Repository → above; UseCase → above; Hook → above
  (domain models are mapped to presentation shapes first); Component (no logic,
  no data access, no provider SDK import).
- **Dependency direction** rules (`ARCH-WEB-APP-DEP-01..0N`, modelled on
  `ARCH-PY-DEP-01..04`): component → hook → usecase/repository → datasource →
  provider; domain imports nothing; nothing imports upward; a feature does not
  import another feature's internals. The final rule: the contract MUST be a
  declared, checkable contract that runs in CI (`enforced_by: [ci, planner]`;
  the check is built in Phase 9; until then it is `[reviewer]` and the rule says
  so).
- **Which layer owns which concern** table; **layer-inclusion decisions**
  (UseCase threshold `ARCH-WEB-APP-USECASE-01` stays here or moves to Phase 4's
  doc with its ID unchanged; Repository threshold; why no BFF is the default for
  `static-export` and when one is justified: server-held secrets, shaping data
  across sources, SSR/SEO, hiding the data store).
- **Runtime variants** section: what is available and forbidden in each. In
  `static-export` the DataSource runs in the browser, so "no external calls in a
  Client Component" is satisfied by the layer (the component calls a hook, the
  hook a DataSource), not by a network boundary.

Amend `architectures/web-app/error-classes.md` wording where it names the Server
Action/Route Handler as the only mapping point, to say "the DataSource (a Server
Action/Route Handler in `server`, a browser module in `static-export`)", keeping
all five IDs.

Schemas: add `frameworks.runtime` (`server`, `static-export`) to
`schemas/project-profile.yaml` with a version bump and changelog entry in the
existing style.

## Phase 3 — Data side: DataSource, Repository, Domain

Write, each to the layer-doc template:

- `architectures/web-app/datasource.md` (`ARCH-WEB-APP-DATASOURCE`, target ~12
  rules): one interface per provider; returns `Outcome`-typed results; DTO →
  domain mapping happens here and nowhere else; provider errors translated
  exactly once to the typed union; empty vs error distinguished; abort
  distinguished from failure (cite `ARCH-WEB-APP-ERR-CANCEL-01`); naming
  (`{Entity}DataSource`, `Firestore{Entity}DataSource`). Two variant sections:
  `server` (Server Action/Route Handler, held credentials) and `static-export`
  (browser module using the Firebase SDK or a callable; no secrets; access is
  governed by security rules, so a rules test is part of the layer's definition
  of done).
- `architectures/web-app/repository.md` (`ARCH-WEB-APP-REPOSITORY`, ~8 rules):
  optional; introduced only when one entity merges more than one DataSource
  (for example a cache and a live source); SSOT; never exposes DataSource types.
  Include the "decided, not deferred" note from the current overview.
- `architectures/web-app/domain.md` (`ARCH-WEB-APP-DOMAIN`, ~8 rules, modelled on
  `ARCH-PY-DOMAIN`): pure entities, value objects and transforms; no I/O, no
  React, no Next, no Firebase; deterministic; one place for business rules and
  rule tables. This is where an aggregation pipeline lives.

## Phase 4 — UseCase and Hook

- `architectures/web-app/usecase.md` (`ARCH-WEB-APP-USECASE-DOC`, ~12 rules,
  modelled on `ARCH-PC-USECASE`): plain TypeScript, constructed with its
  DataSources/Repositories (constructor or factory injection from the
  composition root); one operation per UseCase; orchestration of several is a
  separate coordinating module with no logic of its own; returns `Outcome`;
  side effects that must not block the result; naming
  `{Action}{Entity}UseCase`; threshold for introducing the layer (cite
  `ARCH-WEB-APP-USECASE-01`).
- `architectures/web-app/hook.md` (`ARCH-WEB-APP-HOOK`, ~12 rules, modelled on
  `ARCH-PC-VIEWMODEL`): the ViewModel equivalent. Exposes `{ data, loading,
  error }`-compatible `Outcome` state (cite `PLAT-WEB-STATE-HOOK-01`); formats
  for display; owns UI state and events; subscribes and cleans up (cite
  `PLAT-WEB-TS-CLEANUP-01`); never imports a provider SDK or a DataSource
  implementation, only a UseCase or an interface obtained from the composition
  root; no domain models leak to the component (map first); one hook per
  screen concern.

## Phase 5 — Component, composition, feature structure, modules

- `architectures/web-app/component.md` (`ARCH-WEB-APP-COMPONENT`, ~10 rules,
  modelled on `ARCH-PC-VIEW`): the Server/Client Component rules the
  Next-specific layer needs. Cite and extend `ARCH-WEB-COMPONENTS` (SPA) rather
  than copy it; decide in this phase whether `ARCH-WEB-COMPONENTS` widens to
  `web-app` (preferred, as in Phase 1) and this doc holds only what is new
  (Server Component shells, no mutation logic, `'use client'` leaves, no
  provider access, accessibility hand-off to `PLAT-WEB-A11Y`).
- `architectures/web-app/composition.md` (`ARCH-WEB-APP-COMPOSITION`, ~8 rules,
  modelled on `ARCH-PY-COMPOSITION` and `ARCH-PC-COMPOSITION`): one composition
  module builds providers, DataSources, Repositories and UseCases; Firebase (or
  any SDK) is initialised exactly once there; consumers receive what they need,
  they do not import construction; tests build their own graph with fakes; how
  the composition is made available to hooks (a context provider at the root);
  nothing outside the composition module (and tests) imports a concrete
  DataSource. `PLAT-WEB-HTTP-DI-01` is the existing precedent; cite it.
- `architectures/web-app/feature-structure.md` (`ARCH-WEB-APP-FEATURE-STRUCTURE`,
  ~10 rules, modelled on `ARCH-PC-FEATURE-STRUCTURE`): `features/{feature}/` layout
  (`components/`, `hooks/`, `domain/`, `data/`), where `app/` routes end and
  features begin (routes are thin: compose a feature, nothing else), the public
  surface of a feature (one `index.ts`), no cross-feature internals, shared code
  moves to `shared/` by the two-feature rule (cite `PLAT-WEB-DS-COMPONENT-01`).
- `architectures/web-app/modules.md` (`ARCH-WEB-APP-MODULES`, ~9 rules, modelled
  on `ARCH-PY-MODULES`): size and cohesion, splitting a module that has grown,
  public surface, keeping an import path alive during a split; and the
  **package boundary** for repos with a pipeline: `apps/web`, `packages/<domain>`
  (framework-free), and any functions package; the domain package imports
  nothing from the app; the app and the functions both import the domain
  package, never each other.

## Phase 6 — Errors, observability, and the declared layer contract

- Extend `architectures/web-app/error-classes.md` (or add `error-flow.md`,
  `ARCH-WEB-APP-ERR-FLOW`, ~8 rules, modelled on `ARCH-PC-ERROR-FLOW`): how an
  error travels DataSource → UseCase → Hook → Component; which layer maps and
  which only passes; how the Hook turns an error into a UI state; where
  `error.tsx`/error boundaries catch the unexpected; what is logged where.
- `architectures/web-app/observability.md` (`ARCH-WEB-APP-OBS`, ~6 rules,
  modelled on `ARCH-PY-OBS` but sized for web): structured logging in server
  code, client error reporting without PII, no `console.log` in committed code,
  correlation of a failed callable to its function log.
- Add the layer-contract rule block (see Phase 2) and a worked example of the
  contract in the form Phase 9 will check.

## Phase 7 — React and Firebase platform docs

- `platforms/web/react-patterns.md` (`PLAT-WEB-REACT-PATTERNS`;
  `architecture: [web-spa, web-app, web-content]`; `requires: [PLAT-WEB-REACT]`):
  effects as a last resort; no derived state in `useState`; stable keys; React 19
  (`use`, `useActionState`, `useOptimistic`, ref as a prop) and when each applies
  against a hook that wraps a UseCase; error boundaries vs Next's `error.tsx`;
  memoisation only with a measured reason. Cite, do not restate, TypeScript
  strictness and cleanup.
- `platforms/web/firebase-next.md` (`PLAT-WEB-NEXT-FIREBASE`;
  `architecture: [web-app]`, applies to both runtimes where stated):
  `NEXT_PUBLIC_*` Firebase config (public by design; safe only with rules);
  client-only initialisation vs the Server Component boundary; `onSnapshot` vs
  one-shot reads and which DataSource shape each implies; callable functions as
  the write boundary and their input validation; Firestore and Storage rules as
  the access model, with a rules test for every read the UI relies on; emulator
  testing; hosting a static export (`output: 'export'`, `firebase.json`
  rewrites, headers); a short "known platform traps" section (Storage service
  agent role; Cloud Scheduler not in every region). Cite the config and cleanup
  rules from `PLAT-WEB-FIREBASE`.

## Phase 8 — Theme and Next.js depth

Pin the Tailwind and Next.js versions first (decision 4).

**`PLAT-WEB-DS-THEME` rewrite.** Keep `-01` and `-02` and their IDs. Add: a
two-layer token rule (raw palette private, semantic names public, components use
semantic only); dark mode as rules (strategy, no flash of the wrong theme on
first paint, tokens resolve per theme so `dark:` is the exception, a contrast
requirement tied to `PLAT-WEB-A11Y`); **data-viz tokens** (categorical palette,
sequential/diverging scales, status colours with light and dark variants,
consumed by chart code, no hex in chart components); typography via `next/font`
and a type scale as tokens; where the theme preference is stored and read.

**Next.js depth** in `platforms/web/nextjs.md` (shared) or new sibling docs where
the topic is one runtime only, each rule with a violation message and an example:
data fetching and caching (static vs dynamic; defaults in the pinned version;
revalidation; Suspense streaming); route boundary files (`loading.tsx`,
`error.tsx`, `not-found.tsx`); server-only guards (`server-only` marker; no
secret reachable from a Client Component); Server Action security (`server`
only: an action is a public endpoint; authenticate and authorise inside it;
validate input with the form schema; never trust client identity); URL as state;
**`static-export` constraints** (what `output: 'export'` rules out: no Server
Actions, no Route Handlers, no middleware, no request-time rendering; how auth
is enforced instead, by Firebase Auth plus rules, with a client guard that is a
convenience only, never the boundary); App Router layout vs feature folders (cite
`ARCH-WEB-APP-FEATURE-STRUCTURE`).

Add to `quality-gates/web-testing.md`: testing async Server Components; testing a
hook against a fake UseCase/DataSource; testing a DataSource against the
emulator or a fake provider; testing Firestore rules; testing a domain package
with no framework present.

## Phase 9 — Mechanical enforcement (`esc-ai-execution-framework`)

Separate repository; committed there (`c9d20df`).

### Investigation (2026-10-18)

1. **npm gates.** `esc_exec/npm.py` detected frameworks and source roots and nothing else.
   Onboarding generated a verification profile only for `build.system: gradle`
   (`generate_gradle_verification_profile`, which raised "supports Gradle only" for
   anything else), so an npm component had no verification profile at all and
   `verification plan` failed with "has no paths.verification_profile". A Next.js
   repository therefore had **no verification gates**. The existing onboarding test
   asserted exactly that ("skips verification profile").
2. **The import check.** `forbidden-import` accepted only `.kt` and `.java` files
   (`path.suffix not in {".kt", ".java"}`), took a single `source_root`, matched with
   `fnmatchcase` over the imported name, and **passed when it scanned zero files**. The
   profile schema was strict (`additionalProperties: false`), and `architecture profile
   generate` wrote an empty profile that `check` then rejected.
3. **Next.js 16 changed the lint story.** `next lint` is removed and `next build` no longer
   lints, so a gate set built around `next build` lints nothing and passes.

### Decisions

- **Scanner, not dependency-cruiser.** The check stays dependency-free and keeps the bounded
  JSON report and the rule format the other rule types use. It reads imports by regular
  expression after blanking comments and resolves `tsconfig.json` aliases itself. The cost is
  the limits listed in `esc_exec/ts_imports.py` (no computed dynamic imports); the fail-closed
  rule is what stops those limits turning into a pass. dependency-cruiser would resolve more
  and add a Node toolchain to a Python engine; revisit if the scanner's limits bite.
- **Fail closed in two places.** A rule that scans no files is a violation; an npm component
  with no `test` script gets no profile (reported by onboarding) instead of an empty test
  gate. Missing lint, typecheck and build are recorded in the profile's notes.
- **A template, with a layout check.** `--template web-app` carries the mechanical
  `ARCH-WEB-APP-DEP` rules and a `required-path` rule, so a layout the template did not
  assume fails visibly instead of leaving the other rules checking nothing.

### Built

- `esc_exec/ts_imports.py`: comment stripping, specifier extraction (static, type,
  side-effect, re-export, dynamic, `require`), `tsconfig` alias resolution (`paths`,
  `baseUrl`, relative `extends`), glob matching (`**`, `*`, `?`).
- `forbidden-import` over TypeScript and JavaScript, with `source_roots`, `exclude`,
  `include_tests`, `except_own_feature`, `optional` and profile `pattern_sets`;
  `files_scanned` in each result; the schema extended to match.
- `esc_exec/architecture_templates.py` and `architecture profile generate --template web-app`.
- npm verification profiles from `package.json` scripts (package manager from the lockfile,
  workspace members run in their own directory, bare `vitest` run once, repository test in
  the final gate for a workspace member); `verification profile generate` dispatches by build
  system; onboarding reports `skipped_verification_profiles`.
- 43 new tests; the engine's own `import-linter` contracts and `ruff` rules pass with the two
  new modules classified as core.
- Here: `enforced_by` flipped to `[ci, reviewer]` for `ARCH-WEB-APP-DEP-01` to `-07` and
  `[ci, planner]` for `-08`, with the partial coverage of `-02` and `-06` stated in the
  overview.

### Left open

- **No JUnit report for npm checks.** The generated checks have no `report`, so a failing npm
  gate yields the exit code and logs but not the summarised failing-test list a Gradle gate
  gives. Vitest can write JUnit XML; wiring it needs a per-runner reporter flag.
- **The architecture check is not added to the generated verification profile.** At onboarding
  the architecture profile has no rules yet, so a gate that ran it would fail. Add
  `esc-exec architecture check …` to the component gate once the profile is authored (the
  guide says so).
- **Coverage of the architecture rules is the import-shaped subset.** Rules about calls and
  construction (`ARCH-WEB-APP-COMPOSE-*`), `export *` (`ARCH-WEB-APP-MOD-API-01`) and
  similar are not import-shaped and remain reviewer-enforced.
- **Not run against a real Next.js project.** The template is tested against synthetic
  layouts shaped like the documented folder structure. Phase 10's dry run is the first real
  one.

## Phase 10 — Wiring, cross-check and dry run

- `ORCH-WEB-APP`: updated `requires` and phases for the new layers (domain →
  DataSource → UseCase → hook → component → composition → tests), with variant
  notes for `static-export`. If the two runtimes diverge enough in steps, add
  `ORCH-WEB-APP-STATIC` in the `ORCH-WEB-FEAT` Goal/Read/Steps/Validation format
  rather than overloading one file.
- `PROFILE_DOC_MAP` (`tools/lookup.py`, `profile-doc-map.json`): `frameworks.runtime`
  selects the variant docs; `ui: next` with `cloud: firebase` selects
  `PLAT-WEB-NEXT-FIREBASE`. The existing `cloud: firebase` entry selects the
  mobile doc, so confirm how resolution combines platform and architecture
  before adding entries (as the earlier workflow's Phase 8 did).
- Resolve the dangling IDs `PLAT-WEB-HOOKS` (reword the `platforms/README.md`
  example to a real ID) and `PLAT-WEB-NEXT-STYLE`.
- `python tools/validate.py` full repo: zero duplicate IDs, zero new broken
  citations (the 23 existing mobile WARNs stay). `requires`/`related` are hard
  failures; trim forward references at commit time and backfill, as the earlier
  workflow did.
- `python tools/index.py` to regenerate `index.json` and `index.md`.
- Update `workflows/missing-files.md`: anything deliberately not written, with
  the reason.
- **Dry run:** run `escape-ai repository analyze` on a scratch copy of
  `ilitha-ops-firebase` laid out as the target (`apps/web` Next.js static
  export, `packages/pipeline` framework-free, functions importing the pipeline).
  Record which docs resolve, which do not, what onboarding asks, and whether the
  generated architecture profile passes on the scratch copy and fails when a
  deliberate violation is added. Fix resolution gaps before declaring done.
- Move this file to `archive/` with an Outcome section: what changed, judgement
  calls, anything left open.

## Outcome

_Not started._
