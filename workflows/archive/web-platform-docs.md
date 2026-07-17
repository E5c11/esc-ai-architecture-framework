# Web Platform Docs — `ARCH-WEB-APP` Follow-Ups

`workflows/archive/nextjs-web-architectures.md` added `architectures/web-app/`
and `architectures/web-content/` — the layering and error-class docs only.
Its own Phase 6 deliberately left platform docs, the testing gate, and the
orchestrator out of scope and registered them in `missing-files.md` under
"Next.js platform docs, quality gate, and orchestrators." This workflow
closes that list for `web-app`.

**Driver, not hypothetical:** `ampm-backend`'s `plan/content-dashboard.md` §3
names `PLAT-WEB-HTTP`, `PLAT-WEB-FORMS`, and `PLAT-WEB-NEXT-APP` specifically
as blocking its data-fetching/mutation layer and question-authoring forms —
those three come first (Phases 1–4). The rest (design-system doc set,
`QG-WEB-TESTING`, `ORCH-WEB-APP`, `PROFILE_DOC_MAP` entries) follow in
priority order, not urgency order — nothing downstream is waiting on them
yet.

**Explicitly out of scope, re-registered not authored (Phase 9):**
`PLAT-WEB-NEXT-CONTENT` + its deploy doc, and `ORCH-WEB-CONTENT`. No project
consumes `web-content` today (unlike `web-app`, which the content dashboard
is about to) — writing them now risks documenting a guess, the same reasoning
`content-dashboard.md` §8 already used to defer its own AMPM CRUD-lifecycle
doc. `PLAT-WEB-NEXT` (Phase 1) is shared by both architectures and is in
scope — it doesn't presuppose either architecture-specific doc.

**Workflow:** Do NOT enter plan mode — this document plus
`architectures/web-app/overview.md`, `architectures/web-app/error-classes.md`,
`platforms/mobile/http-client.md` (structural reference for Phase 3), and
`platforms/mobile/design-system/` (structural reference for Phase 5) provide
all the planning needed.

**Commit after each phase.**

---

## Phase 1 — `PLAT-WEB-NEXT`

Write `platforms/web/nextjs.md`. Frontmatter: `platform: [web]`,
`architecture: [web-app, web-content]` (genuinely shared — file-based
routing and the Server/Client boundary don't differ between the two),
`requires: [CORE-COUPLING]`, `related: [ARCH-WEB-APP, ARCH-WEB-CONTENT]`.

Covers: App Router file-based routing/route groups/layouts; the Server
Component default and where `'use client'` may be added; environment
variable convention; `middleware.ts` as the file Next.js itself recognizes
for request-time interception (the mechanical fact `ARCH-WEB-APP`'s "Auth
enforcement: `middleware.ts`" decision rests on).

```rule
id: PLAT-WEB-NEXT-CLIENT-01
statement: A component MUST NOT be marked `'use client'` unless it itself uses browser-only APIs, local state, or event handlers — the boundary is pushed to the smallest leaf that actually needs it, never applied to a whole page or layout by default.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-CLIENT-01 — push `'use client'` to the smallest leaf component that needs it; do not mark a whole page or layout client-side by default.
```

```rule
id: PLAT-WEB-NEXT-ENV-01
statement: An environment variable MUST NOT be prefixed `NEXT_PUBLIC_` unless its value is safe to ship in the client JS bundle — server-only credentials (DB connection strings, backend service credentials) MUST be read only in server-side code (Server Components, Route Handlers, Server Actions, middleware).
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-ENV-01 — a `NEXT_PUBLIC_`-prefixed variable ships in the client bundle; server-only credentials MUST NOT use that prefix.
```

```rule
id: PLAT-WEB-NEXT-MW-01
statement: An auth/session check that gates an entire app or route group MUST live in `middleware.ts`, evaluated before any Server Component in that group renders — never duplicated as a per-page guard.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-MW-01 — gate the route group in `middleware.ts`, not with a per-page guard component.
```

This restates `ARCH-WEB-APP`'s architecture-level decision as the concrete
platform mechanic; cite `ARCH-WEB-APP`'s prose rather than re-deriving why
`middleware.ts` was chosen over a guard component.

---

## Phase 2 — `PLAT-WEB-NEXT-APP` + its deploy doc

Write `platforms/web/nextjs-app.md`. Frontmatter: `architecture: [web-app]`,
`requires: [PLAT-WEB-NEXT, ARCH-WEB-APP, ARCH-WEB-APP-ERR-CLASSES]`.

**Restate, don't re-derive**, the fact `ARCH-WEB-APP-ERR-CLASSES` flagged and
explicitly deferred here: Next.js strips a thrown Server Action error to an
opaque digest in production. Show the concrete pattern (return, don't throw)
with a short before/after example.

```rule
id: PLAT-WEB-NEXT-APP-THROW-01
statement: A Server Action MUST return an `Outcome`-shaped result for every expected failure — it MUST NOT `throw` for a failure the caller is meant to handle.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-APP-THROW-01 — Next.js strips a thrown Server Action error to an opaque digest in production; return an explicit Outcome instead (see ARCH-WEB-APP-ERR-UNKNOWN-01).
```

```rule
id: PLAT-WEB-NEXT-APP-REVALIDATE-01
statement: A Server Action that mutates data MUST call `revalidatePath`/`revalidateTag` for every path whose Server Component render depends on that data.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-APP-REVALIDATE-01 — a mutating Server Action that doesn't revalidate leaves the affected Server Component stale until a hard refresh.
```

Cover the Route Handler vs. Server Action choice as guidance, not a rule: a
form mutation invoked from a Client Component is a Server Action; an
endpoint another service calls, or one needing standard HTTP semantics
(caching headers, a non-Next.js caller), is a Route Handler.

Write `platforms/web/nextjs-app-deploy.md` (`PLAT-WEB-NEXT-APP-DEPLOY`).
Frontmatter: `architecture: [web-app]`, `requires: [PLAT-WEB-NEXT-APP]`,
`related: [PLAT-WEB-DEPLOY]` — cite `PLAT-WEB-DEPLOY-BUILD-01`'s "never
deploy a build with TypeScript errors" principle rather than restating it;
this doc only adds what's genuinely different for a Next.js/Docker/Cloud Run
pipeline over Vite/Firebase Hosting.

```rule
id: PLAT-WEB-NEXT-APP-DEPLOY-POOL-01
statement: A Route Handler/Server Action holding a direct database connection pool on a scale-to-zero host (Cloud Run or equivalent) MUST set a minimum instance count ≥ 1 and size the pool for deployed concurrency.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-APP-DEPLOY-POOL-01 — an unconfigured pool on a scale-to-zero host causes connection churn/exhaustion on every cold start.
```

That rule generalizes the operational note `content-dashboard.md` §5 already
worked out for this project specifically (Cloud SQL Auth Proxy + Cloud Run
`min-instances`) — cite it as the worked example in this doc's prose, don't
invent a different one.

```rule
id: PLAT-WEB-NEXT-APP-DEPLOY-BUILD-01
statement: `next build` MUST pass with zero TypeScript errors before the container image is built — mirrors PLAT-WEB-DEPLOY-BUILD-01's principle for the Vite pipeline, restated for `next build`'s own type-check step.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-APP-DEPLOY-BUILD-01 — never build a container image from a `next build` that produced TypeScript errors.
```

Cover, as prose not a new rule (these are deployment-target facts, not
behavioral constraints): Docker multi-stage build using Next.js `standalone`
output, Cloud Run domain mapping + Google-managed TLS for a custom subdomain
(the `admin.askmoreprepmore.app` pattern from `content-dashboard.md` §5 is a
fine worked example to cite, generalized — don't hardcode that literal
domain into the framework doc).

---

## Phase 3 — `PLAT-WEB-HTTP`

Write `platforms/web/http-client.md`. Frontmatter: `architecture: [web-app]`,
`requires: [ARCH-WEB-APP, ARCH-WEB-APP-ERR-CLASSES, CORE-DI]`,
`related: [PLAT-MOB-HTTP, PLAT-WEB-NEXT-APP]`.

Scope this doc to the Route Handler/Server Action boundary only —
`ARCH-WEB-APP`'s own rule ("Client Component ... never fetches a backend or
opens a DB connection itself") already establishes there is no client-side
REST layer to document here. `PLAT-MOB-HTTP` is a reasonable *structural*
template (executor abstraction, header/auth provider, retry policy, typed
error mapping, DI registration, fake-based testing) but is Ktor/KMP-specific
— this needs a genuine `fetch`-based TypeScript rewrite, not a find-replace.
No token-refresh section is needed here unlike `PLAT-MOB-HTTP`'s — a staff
session on the server side doesn't face the same refresh-coordination
problem a mobile client juggling a long-lived token does; note *why* it's
absent rather than silently omitting it.

```rule
id: PLAT-WEB-HTTP-LIB-01
statement: REST calls to a backend MUST go through a shared request-executor abstraction — never an ad hoc `fetch` call written inline in a Server Action or Route Handler.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-LIB-01 — REST calls MUST go through a shared executor, not inline `fetch` scattered across Server Actions/Route Handlers.
```

```rule
id: PLAT-WEB-HTTP-AUTH-01
statement: The executor MUST attach the staff auth token via an injected header provider that reads the server-side session — a Server Action/Route Handler MUST NOT read or forward a token itself.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-AUTH-01 — token attachment is the executor's job via an injected provider, not something each call site does itself.
```

```rule
id: PLAT-WEB-HTTP-ERR-01
statement: A non-2xx response MUST be mapped into the `AppError` union at the executor or the calling Server Action/Route Handler — never left as an unmapped `Response`/thrown error past that boundary.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-ERR-01 — cites ARCH-WEB-APP-ERR-MAP-01; map the provider error exactly once, at this boundary.
```

```rule
id: PLAT-WEB-HTTP-RETRY-01
statement: Only idempotent requests (GET, or a write with an explicit idempotency key) MAY be retried automatically.
type: soft
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-RETRY-01 — a POST/PATCH/PUT/DELETE without an idempotency key MUST NOT be retried automatically.
```

Testing section: cite `QG-WEB-TESTING` (Phase 6) for the full pattern once it
exists — MSW mocks the Provider (the actual HTTP boundary), a fake
implementation of the executor interface is what a Server Action's own test
depends on, same fake-not-mock split `PLAT-MOB-HTTP-TEST-01` already
establishes for mobile.

---

## Phase 4 — `PLAT-WEB-FORMS`

Write `platforms/web/forms.md`. Frontmatter: `architecture: [web-app]`,
`requires: [ARCH-WEB-APP-ERR-CLASSES]`, `related: [PLAT-WEB-HTTP]`.

The content-authoring use case (`content-dashboard.md` §6 — one zod schema
per question `presentation` type) is the concrete motivating case for this
doc, cite it as the worked example, but write the rule generally — this
applies to any discriminated content type, not just questions.

```rule
id: PLAT-WEB-FORMS-SCHEMA-01
statement: A form backed by a discriminated content type (a `presentation`/`type`/`kind` field selecting the shape) MUST define one zod schema per variant — never one generic schema covering the superset of every variant's fields.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-FORMS-SCHEMA-01 — define one zod schema per content variant; a generic superset schema validates nothing type-specific.
```

```rule
id: PLAT-WEB-FORMS-SSOT-01
statement: The zod schema used for client-side react-hook-form validation MUST be reused, not re-derived, for server-side validation inside the Server Action that receives the submission.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-FORMS-SSOT-01 — never validate only on the client; reuse the same schema server-side (CORE-SSOT applied to validation).
```

```rule
id: PLAT-WEB-FORMS-ERR-01
statement: A `validation` `AppError` returned from a Server Action MUST be mapped into react-hook-form's `setError` via its `fieldErrors`, not surfaced as a single generic error message.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-FORMS-ERR-01 — cites ARCH-WEB-APP-ERR-CLASSES's `fieldErrors` shape, which exists specifically so this mapping needs no adapter.
```

Cover `zodResolver` wiring and per-field-array form patterns (e.g. a
blank-token-list editor for a `fitb`-shaped schema) as worked examples, not
new rules — the shape varies too much per content type to standardize
further than "one schema per variant."

---

## Phase 5 — `platforms/web/design-system/` doc set

Write `theme.md` (`PLAT-WEB-DS-THEME`), `component.md`
(`PLAT-WEB-DS-COMPONENT`), `icons.md` (`PLAT-WEB-DS-ICONS`) — mirrors
`platforms/mobile/design-system/`'s three-doc split structurally, restated
for Tailwind/React. Frontmatter: `architecture: [web-app, web-content]`
(shared by both, per `missing-files.md`), `requires: [CORE-COUPLING]`.

**Naming note, avoid a collision `PLAT-MOB-DS-THEME` already has**: mobile's
design-system rules use a bare `DS-THEME-01`-style ID (no platform prefix) —
an existing inconsistency, not this workflow's to fix, but it means these
new IDs must use the full `PLAT-WEB-DS-*` prefix so they don't collide with
mobile's `DS-*` namespace when `tools/validate.py` checks for duplicates
repo-wide.

`theme.md` — token definitions in `tailwind.config.ts` (colors, spacing,
radius, type scale), dark mode via Tailwind's class strategy:

```rule
id: PLAT-WEB-DS-THEME-01
statement: Components MUST use Tailwind utility classes backed by tokens defined in `tailwind.config.ts` — no arbitrary-value classes (`bg-[#hex]`, `p-[Npx]`, `text-[Npx]`) for any value a token already covers.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DS-THEME-01 — use a `tailwind.config.ts` token, not an arbitrary-value class.
```

```rule
id: PLAT-WEB-DS-THEME-02
statement: A value used in 3+ places, or specified by a design spec, MUST be added to `tailwind.config.ts` as a token — not repeated as an arbitrary-value class each time.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DS-THEME-02 — promote a repeated value to a token instead of repeating an arbitrary-value class.
```

This is the rule `missing-files.md` named as this doc set's whole reason for
existing — it's what finally makes §5 of `content-dashboard.md`'s Tailwind
decision a real, enforced framework convention instead of a per-project
exception layered on top of `PLAT-WEB-STYLING`'s stated default (which
stays unchanged, still governing `web-spa`).

`component.md` — shared component location, Server-vs-Client default per
component (cite `PLAT-WEB-NEXT-CLIENT-01`, don't re-derive):

```rule
id: PLAT-WEB-DS-COMPONENT-01
statement: A component used by two or more features MUST move to the shared `components/ui/` directory — never be duplicated across feature-local component files.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DS-COMPONENT-01 — promote a component used by 2+ features to `components/ui/` instead of duplicating it.
```

Mirrors `ARCH-WEB-CONTENT-SHARED-01`'s co-locate-until-reused threshold,
restated for components instead of content — cite that rule's reasoning in
prose rather than re-deriving the threshold.

`icons.md` — a single centralized icon module, same shape as mobile's
`AppIcons` singleton (`DS-ICON-01`), restated for React:

```rule
id: PLAT-WEB-DS-ICON-01
statement: Icons MUST be imported through a single centralized module — never imported ad hoc per-component directly from the icon library.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DS-ICON-01 — import icons through the centralized module, not ad hoc per-component.
```

Icon library choice (e.g. `lucide-react`) is a project decision, not
dictated by this doc — name it as a common default in prose, not a rule.

---

## Phase 6 — `QG-WEB-TESTING`

Write `quality-gates/web-testing.md`. Frontmatter: `platform: [web]`,
`architecture: [all]`, `requires: [QG-TESTING, CORE-TESTING]`,
`related: [PLAT-WEB-HTTP, PLAT-WEB-FORMS]`. Scoped broadly (`architecture:
[all]`) — this replaces `QG-TESTING`'s one-line web mention for every web
architecture, not just `web-app`; `QG-TESTING` itself stays as the
cross-platform philosophy doc and gets a citation added pointing here.

Covers: Vitest + React Testing Library baseline (restate what `QG-TESTING`
already has one line for, now with real detail); MSW's role specifically at
the Provider boundary for `web-app` (mocking the REST/Postgres call a Route
Handler or Server Action makes — not component-level).

```rule
id: QG-WEB-TESTING-SA-01
statement: A Server Action is tested by calling it directly as an async function and asserting on its `Outcome`-shaped return — not by mounting a form and simulating a DOM submit.
type: hard
scope: testing
enforced_by: [reviewer]
violation_message: Violates QG-WEB-TESTING-SA-01 — call the Server Action directly; a DOM-level submit test is slower and tests React's form handling, not the action's own logic.
```

```rule
id: QG-WEB-TESTING-MSW-01
statement: A Provider-boundary test (a Route Handler/Server Action calling the PLAT-WEB-HTTP executor) mocks at the network layer with MSW — not by mocking the executor's own methods.
type: hard
scope: testing
enforced_by: [reviewer]
violation_message: Violates QG-WEB-TESTING-MSW-01 — mirrors QG-TEST-MOCK-01 ("mock at architectural boundaries, not within a layer"); mock the network, not the executor.
```

```rule
id: QG-WEB-TESTING-MW-01
statement: An auth flow gated by `middleware.ts` MUST be covered by an integration/E2E test — a component or unit test cannot exercise the middleware boundary.
type: soft
scope: testing
enforced_by: [reviewer]
violation_message: Violates QG-WEB-TESTING-MW-01 — middleware-gated auth needs an E2E layer (e.g. Playwright); no lower test level reaches it.
```

---

## Phase 7 — `ORCH-WEB-APP` orchestrator

Write `feature-orchestrators/web/app-feature.md`. Frontmatter modeled on
`ORCH-WEB-FEAT`'s shape: `id: ORCH-WEB-APP`, `type: orchestrator`,
`layer: feature-orchestrators`, `platform: [web]`,
`architecture: [web-app]`,
`goal: "Implement a complete web-app feature with a held server-side
provider call, typed error mapping, and (where the feature mutates data) a
validated form"`,
`requires: [CORE-COUPLING, CORE-NAMING, CORE-TESTING, ARCH-WEB-APP,
ARCH-WEB-APP-ERR-CLASSES, PLAT-WEB-NEXT, PLAT-WEB-NEXT-APP, PLAT-WEB-HTTP,
PLAT-WEB-FORMS, PLAT-WEB-DS-THEME, QG-WEB-TESTING]`,
`related: [QG-REVIEW, ORCH-WEB-FEAT]`.

Phase structure, following `ARCH-WEB-APP`'s own layer stack top-to-bottom
(mirrors `ORCH-WEB-FEAT`'s phase-per-layer shape, restated for this
architecture's layers instead of `web-spa`'s):

1. **Types/schema** — the domain type plus (if the feature mutates data) its
   `PLAT-WEB-FORMS-SCHEMA-01` zod schema.
2. **Provider call** — the Route Handler/Server Action's call into
   `PLAT-WEB-HTTP`'s executor or a direct Postgres query.
3. **Error mapping** — map the provider's failure into `AppError`
   (`ARCH-WEB-APP-ERR-MAP-01`), decide UseCase-or-not against
   `ARCH-WEB-APP-USECASE-01`'s threshold.
4. **Hook** — client-side state formatting/`Outcome` exposure.
5. **Client Component** — interactive rendering; wire `PLAT-WEB-FORMS` if
   this phase's feature is a mutation.
6. **Server Component shell** — initial fetch/render;
   `PLAT-WEB-NEXT-APP-REVALIDATE-01` if a sibling mutation needs to
   invalidate this render.
7. **Test gate** — `QG-WEB-TESTING`'s Server Action/MSW patterns plus
   `next build` (`PLAT-WEB-NEXT-APP-DEPLOY-BUILD-01`).

**Open judgment call for the executing session, not decided here:** whether
`PLAT-WEB-A11Y` (currently `architecture: web-spa` only) should be broadened
to include `web-app`, or whether `web-app` needs its own accessibility
citation doc. Its content — semantic HTML, alt text, focus, ARIA — reads as
architecture-agnostic in substance, but the prior workflow's Phase 5
cross-check didn't examine this doc specifically (it named
`PLAT-WEB-FIREBASE` and `PLAT-WEB-STATE` as checked candidates, not
`PLAT-WEB-A11Y`/`PLAT-WEB-REACT`). Apply the same "does it still correctly
describe what it claims to describe" test before deciding; don't assume
either answer.

---

## Phase 8 — `PROFILE_DOC_MAP` + a `forms` project-profile field

`schemas/project-profile.yaml` has no `frameworks.forms` key today — add
one (`description: "Form state/validation library. Examples:
react-hook-form, formik, none"`), bump `schema.version` to `1.1` with a
changelog entry in the same style as `1.1`'s existing entries elsewhere in
the repo (check the current version isn't already past `1.1` before
writing the bump).

Add to `tools/lookup.py`'s `PROFILE_DOC_MAP`:

```python
"network": {
    ...,                        # existing mobile entries untouched
    "fetch": ["PLAT-WEB-HTTP"],
    "axios": ["PLAT-WEB-HTTP"],
},
"ui": {
    "next": ["PLAT-WEB-NEXT"],
},
"forms": {
    "react-hook-form": ["PLAT-WEB-FORMS"],
},
```

Architecture-scoped docs (`PLAT-WEB-NEXT-APP`, `ARCH-WEB-APP`, the
design-system set) don't need `PROFILE_DOC_MAP` entries — they already load
via their `architecture: [web-app]` frontmatter once a project profile
declares `architecture: web-app`, the same way `ARCH-WEB-APP` itself does
without a map entry. `PROFILE_DOC_MAP` is only for framework-choice-driven
extras a bare `platform`/`architecture` match wouldn't otherwise select —
confirm this reading against `tools/lookup.py`'s existing resolution logic
before adding entries speculatively.

---

## Phase 9 — Cross-check, re-register deferred gaps, index regen

Run `python tools/validate.py` full-repo — zero duplicate rule IDs (the
`PLAT-WEB-DS-*` naming from Phase 5 is the specific collision risk to
re-check), zero broken citations introduced by Phases 1–8.

In `workflows/missing-files.md`: remove the "Next.js platform docs, quality
gate, and orchestrators" entry this workflow closes, and add a narrower
replacement registering only what's still deliberately deferred:
`PLAT-WEB-NEXT-CONTENT` + `PLAT-WEB-NEXT-CONTENT-DEPLOY`, and
`ORCH-WEB-CONTENT` — with the same "no consuming project uses `web-content`
yet" rationale stated in this doc's header, so the next session doesn't
have to re-derive why they're still open.

Regenerate `index.json`/`index.md` with `python tools/index.py` and commit.

## Outcome

All nine phases completed and committed; `python tools/validate.py` passes
clean (only the pre-existing 23 WARN-only mobile design-system citations
remain, unchanged from baseline). Notes for the record:

- Frontmatter `related` fields that would have pointed forward to a
  doc created in a later phase were trimmed at commit time and backfilled
  once that doc existed (e.g. `PLAT-WEB-NEXT-APP`'s `related` picked up
  `PLAT-WEB-HTTP` in Phase 3 and `QG-WEB-TESTING` in Phase 6) — `requires`/
  `related` are validated as hard broken-reference failures, unlike a body
  citation, which only WARNs until the target exists. This wasn't spelled
  out in the phase text but follows from `tools/validate.py`'s own check
  behavior.
- `PLAT-WEB-HTTP` gained a `PLAT-WEB-HTTP-DI-01` rule not explicitly named
  in Phase 3's text — added for parity with `PLAT-MOB-HTTP-DI-01`'s DI
  registration rule, since the phase's own `requires: [..., CORE-DI]` and
  "DI registration" content pointer implied one was expected; it documents
  the module-level-singleton pattern this doc's construction example already
  needed anyway (no DI framework equivalent to Koin exists for Next.js
  server code).
- The `PLAT-WEB-A11Y` judgment call (Phase 7's open question) was resolved
  as: don't broaden the doc's `architecture` field. Five of its seven rules
  (semantic HTML, alt, aria-label, headings, focus) are architecture-agnostic
  and are cited directly from `ORCH-WEB-APP` Phase 5; its remaining two
  (`PLAT-WEB-A11Y-GUARD-01`, `PLAT-WEB-A11Y-EB-01`) are tied to `web-spa`'s
  manual container/`ErrorBoundary` model, which `web-app` doesn't use —
  Next.js's own `loading.tsx`/`error.tsx` conventions serve that role
  instead. Broadening the doc wholesale would have made those two rules
  read as applying when they don't; no new `web-app`-specific a11y doc was
  needed to make this citation work.
- `ORCH-WEB-APP` followed `ORCH-WEB-FEAT`'s Goal/Read/Steps/Validation phase
  format (the sibling convention inside `feature-orchestrators/web/`) rather
  than the newer Required-framework-docs/Code-paths/Assumes/Produces header
  block `schemas/feature-orchestrator.yaml` recommends for new orchestrators
  and `ORCH-MOB-IOS` already uses — a judgment call for consistency within
  the `web/` orchestrator family over cross-platform format uniformity,
  the same kind of call the prior `nextjs-web-architectures` workflow made
  for `type: overview` vs. `type: architecture`.
