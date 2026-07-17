# Next.js Web Architectures

Add two new architectures under `architectures/`: `web-content` (SSG/ISR-first
marketing/content sites — the SEO problem `ampm-website` and
`anthropologies-of-extortion` have as plain Vite/React SPAs) and `web-app`
(server-capable interactive apps with a held external-call boundary — the new
content dashboard, which needs Next.js for an unrelated reason: only a server
runtime can hold a Cloud SQL Auth Proxy connection a browser can't open
directly). Both are real forks from `architectures/web-spa/` — nothing there
transfers to Next.js's Server/Client Component boundary — and `web-spa` is not
touched or deprecated; it stays exactly as-is for every project still on a
plain Vite/React SPA (`black-arrows-website`, `pinboard-dashboard`,
`preemie-partner`, etc.).

`web-app` is modeled on mobile's `ARCH-PC` (`architectures/pragmatic-clean/`)
layering — View → ViewModel → UseCase → Repository/DataSource → Provider —
restated for the Next.js boundary instead of KMP. It cites `ARCH-PC`, it does
not generalize or edit it.

Scope of this workflow: the two architecture docs only. Platform docs
(`PLAT-WEB-NEXT*`, `PLAT-WEB-HTTP`, `PLAT-WEB-FORMS`, styling, deploy),
orchestrators, and `QG-WEB-TESTING` are deliberately out of scope — registered
as follow-up gaps in Phase 5, not authored here.

**Workflow:** Do NOT enter plan mode — this document plus
`schemas/document.yaml`, `architectures/pragmatic-clean/overview.md`, and
`architectures/web-spa/overview.md` provide all the planning needed.

**Commit after each phase.**

## Phase 1 — Schema

Add `web-content` and `web-app` to the `architecture` enum in
`schemas/document.yaml` (bump to `1.2`, changelog entry same style as `1.1`'s
`library` entry). Add the same two values to `schemas/project-profile.yaml`'s
`architecture` enum — and fix a pre-existing gap noticed while there: add
`web-spa` too, which is missing from that file's enum today despite being a
fully-built architecture (`vertical-slice`/`hexagonal` are listed there despite
having no architecture doc at all — leave those as-is, out of scope).

Verify: `python tools/validate.py` still passes clean before any doc changes.

## Phase 2 — `ARCH-WEB-CONTENT`

Write `architectures/web-content/overview.md`. Frontmatter: `platform: [web]`,
`architecture: [web-content]`, `requires: [CORE-COUPLING, CORE-NAMING,
PAT-DATA-ACCESS]`. Content, modeled on `web-spa/overview.md`'s "Static website"
section but restated for Server Components/SSG instead of CSR: what it is
(Server Components by default, pages are SSG/ISR, content is data — no client
data layer, no auth), folder structure (content co-located per route by
default — `app/[slug]/content.ts`), layer/responsibility table, dependency
direction, `generateMetadata`/JSON-LD owned per-route as a hard requirement,
not centralized. Rules as fenced ` ```rule ` blocks (this repo is fully
migrated off the old bold-text rule format — see
`workflows/archive/rule-embedding-migration.md` — any new rule must be a real
block from the start, not prose).

Two rules, decided this session — the Android/KMP-parity discussion (`strings.xml`
has no hardcoding-escape-hatch; the web equivalent has to be an enforced rule
instead of a tooling guarantee):

```rule
id: ARCH-WEB-CONTENT-NOLITERAL-01
statement: User-visible text MUST NOT appear as a string literal inside JSX — it MUST be sourced from an imported content object.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-CONTENT-NOLITERAL-01 — User-visible text MUST NOT appear as a string literal inside JSX — it MUST be sourced from an imported content object.
```

```rule
id: ARCH-WEB-CONTENT-SHARED-01
statement: A content object used by two or more routes MUST move to `content/shared/{domain}.ts` — never be duplicated across route-local content files.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-CONTENT-SHARED-01 — A content object used by two or more routes MUST move to `content/shared/{domain}.ts` — never be duplicated across route-local content files.
```

`ARCH-WEB-CONTENT-SHARED-01` is `ARCH-WEB-ORG-02`'s existing co-locate-until-
reused model (already governs component promotion in `ARCH-WEB`), restated for
content instead of components — cite `ARCH-WEB-ORG-02` in the doc's prose
rather than re-deriving the threshold.

Theming and shared components are deliberately NOT decided in this doc —
Tailwind-specific token rules name a specific technology, so per the placement
test they belong in a platform doc, not here. See Phase 5: this became a
`platforms/web/design-system/` doc set instead of a single styling doc.

Judgment call, apply the placement/ownership test from this file's own
`workflows/README.md`: if a component rule here would be pasted verbatim from
`ARCH-WEB-COMPONENTS`, cite it instead of duplicating it; only write a sibling
`components.md` if content-site component rules genuinely diverge.

## Phase 3 — `ARCH-WEB-APP`

Write `architectures/web-app/overview.md`. Frontmatter: `platform: [web]`,
`architecture: [web-app]`, `requires: [CORE-COUPLING, CORE-NAMING,
PAT-DATA-ACCESS, PAT-OUTCOME, PAT-OBSERVER]`, `related: [ARCH-PC]`. Content,
modeled on `architectures/pragmatic-clean/overview.md`'s shape (layer stack,
data-flow diagram, boundary table, feature-folder structure, which-layer-owns-
which-concern table), restated for the Next.js boundary:

```
Server Component      Initial data-fetch shell. Renders. No mutation logic.
Client Component      Renders interactive state. Emits user events.
Hook                  Formats data for display. Manages UI state/events.
Route Handler /        The one place all external calls happen: REST client
Server Action          to a backend, or a held DB connection. Repository/
                       DataSource-equivalent boundary.
Provider               External REST API / Postgres.
```

State up as reactive/typed results (`PAT-OBSERVER`/`PAT-OUTCOME`), mutations
down as calls into the Route Handler/Server Action layer. Same
cite-vs-duplicate judgment call as Phase 2 for a possible `components.md`.

Three layer-inclusion decisions, resolved this session:

```rule
id: ARCH-WEB-APP-USECASE-01
statement: A UseCase-equivalent module MUST be introduced once a feature's business logic requires coordinating more than the single external call already in its Server Action — it MUST NOT be added speculatively.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-USECASE-01 — Introduce a UseCase-equivalent module only once business logic outgrows a single Server Action call; do not add the layer speculatively.
```

Expected to trigger soon in practice, not a hypothetical — both the analytics
dashboard views and the content-authoring/validation surface (per-`presentation`-type
rules, `content-dashboard.md` §6) are exactly the kind of multi-step business logic
this threshold is meant to catch. When it does, the module lives at
`features/{feature}/useCases/{action}.ts`, called from the Server Action, same
naming shape as pragmatic-clean's `{Action}{Entity}UseCase`.

**No Repository layer for now** — decided, not deferred-as-a-gap: two sources
total (REST to `ampm-backend`, direct Postgres), nothing merges both in one
feature today, and persistence/multi-source coordination is rare on this side
of the stack generally. Revisit only if a feature actually needs both sources
merged under one SSOT.

**Auth enforcement: `middleware.ts`**, not a per-page guard component — checked
once, before any Server Component renders, rather than repeated per protected
route the way `web-spa`'s `AuthGuard` does.

## Phase 4 — `ARCH-WEB-APP-ERR-CLASSES`

Write `architectures/web-app/error-classes.md` as a sibling doc to
`web-app/overview.md` — same split mobile chose (`ARCH-PC-ERR-CLASSES` sits
next to `pragmatic-clean/overview.md`, not inside it). Frontmatter:
`platform: [web]`, `architecture: [web-app]`, `requires: [ARCH-WEB-APP,
PAT-OUTCOME, CORE-ERROR]`, `related: [ARCH-PC-ERR-CLASSES]`.

Shape — the TS instantiation of `PAT-OUTCOME` for this boundary:

```typescript
type Outcome<T, E extends AppError = AppError> =
  | { ok: true; data: T }
  | { ok: false; error: E };

type AppError =
  | { type: 'offline' }
  | { type: 'unauthorized' }
  | { type: 'forbidden' }
  | { type: 'notFound' }
  | { type: 'validation'; fieldErrors: Record<string, string[]> }
  | { type: 'unexpected'; message: string };
```

`validation` is shaped like zod's `.flatten().fieldErrors` deliberately — it
composes with react-hook-form's `setError` instead of a second error channel
next to the already-decided forms stack.

Four rules, mirroring `ARCH-PC-ERR-CLASSES` one-for-one for this boundary:

```rule
id: ARCH-WEB-APP-ERR-TYPE-01
statement: Error types crossing the Server Action/Route Handler boundary MUST be a typed discriminated union — never a raw thrown Error, fetch Response, or Postgres driver error.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-ERR-TYPE-01 — Error types crossing the Server Action/Route Handler boundary MUST be a typed discriminated union — never a raw thrown Error, fetch Response, or Postgres driver error.
```
```rule
id: ARCH-WEB-APP-ERR-MAP-01
statement: A provider error (REST error response, Postgres error) MUST be translated exactly once, at the Server Action or Route Handler that calls the provider.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-ERR-MAP-01 — A provider error MUST be translated exactly once, at the Server Action or Route Handler that calls the provider.
```
```rule
id: ARCH-WEB-APP-ERR-UNKNOWN-01
statement: Unknown failures MUST be logged server-side with full cause and mapped to an explicit `unexpected` outcome — never returned as empty data or false success.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-ERR-UNKNOWN-01 — Unknown failures MUST be logged server-side with full cause and mapped to an explicit `unexpected` outcome.
```
```rule
id: ARCH-WEB-APP-ERR-CANCEL-01
statement: An aborted client-side request (AbortController) MUST remain distinguishable from operational failure.
type: soft
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-ERR-CANCEL-01 — An aborted client-side request MUST remain distinguishable from operational failure.
```

Rationale to include for `ARCH-WEB-APP-ERR-UNKNOWN-01` specifically: Next.js
strips a thrown Server Action error to an opaque digest in production — return,
don't throw, or the failure detail is silently lost, exactly the false-success
failure mode `PAT-OUTCOME` already warns against. That fact itself is a
platform detail, not an architecture rule — restate it in `platforms/web/
nextjs-app.md` when that doc is authored (registered in Phase 6); don't
duplicate it as a second rule here.

## Phase 5 — Cross-check existing citations

Run `python tools/validate.py` full-repo — zero duplicate rule IDs, zero
broken citations introduced by Phases 2–4.

Grep every doc that cites `ARCH-WEB`/`web-spa` and currently describes the
*dashboard* variant specifically (candidates: `PLAT-WEB-FIREBASE`,
`PLAT-WEB-STATE`'s "Dashboard routing — protected routes" section, `ARCH-WEB`
overview's "Firebase dashboard" folder-structure section). For each, confirm
it still correctly describes a plain SPA+Firebase dashboard project — if so,
leave it untouched (per this session's decision: `web-spa` is not deprecated,
don't edit it defensively). None of these should be repointed at `ARCH-WEB-APP`
in this workflow.

## Phase 6 — Register follow-up gaps

Add entries to `workflows/missing-files.md` for what these two architectures
need next, explicitly out of scope here: `PLAT-WEB-NEXT`, a
`platforms/web/design-system/` doc set (`theme.md`, `component.md`, `icons.md`)
mirroring `platforms/mobile/design-system/`'s structure — shared by both
`web-content` and `web-app` since both use Tailwind. Supersedes the single-doc
`PLAT-WEB-NEXT-STYLE` sketched earlier; owns the Tailwind-specific token rule
(no arbitrary `bg-[#hex]`/`p-[px]` values — tokens from `tailwind.config.ts`
only) that doesn't belong in either architecture doc since it names a specific
technology. Also register: `PLAT-WEB-NEXT-CONTENT` + its deploy doc,
`PLAT-WEB-NEXT-APP` + its deploy doc (the latter should restate, not repeat as
a new rule, the thrown-Server-Action-error-stripped-in-production fact flagged
in Phase 4), `PLAT-WEB-HTTP`, `PLAT-WEB-FORMS`, `QG-WEB-TESTING`, orchestrators
`ORCH-WEB-CONTENT`/`ORCH-WEB-APP`, and `PROFILE_DOC_MAP` web entries in
`tools/lookup.py` (currently zero web entries at all). Regenerate
`index.json`/`index.md` with `python tools/index.py` and commit.
