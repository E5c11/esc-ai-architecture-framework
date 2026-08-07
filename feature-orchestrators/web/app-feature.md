---
id: ORCH-WEB-APP
type: orchestrator
layer: feature-orchestrators
platform: [web]
architecture: [web-app]
goal: "Implement a complete web-app feature with a held server-side provider call, typed error mapping, and (where the feature mutates data) a validated form"
requires:
  - CORE-COUPLING
  - CORE-NAMING
  - CORE-TESTING
  - ARCH-WEB-APP
  - ARCH-WEB-APP-ERR-CLASSES
  - PLAT-WEB-NEXT
  - PLAT-WEB-NEXT-APP
  - PLAT-WEB-HTTP
  - PLAT-WEB-FORMS
  - PLAT-WEB-DS-THEME
  - QG-WEB-TESTING
related: [QG-REVIEW, ORCH-WEB-FEAT]
tags: [web, feature, nextjs, server-actions, route-handlers, orchestrator]
status: active
---

# Implement Web-App Feature (Next.js Server Actions)

## Goal

Produce a complete, typed feature page: domain type/schema → provider call →
error mapping → hook → Client Component → Server Component shell → tests —
following `ARCH-WEB-APP`'s layer stack top-to-bottom, the same
phase-per-layer shape `ORCH-WEB-FEAT` uses for `web-spa`, restated for this
architecture's layers instead.

## Before you start

Read all documents listed in `requires`. Decide upfront whether this
feature mutates data (needs a `PLAT-WEB-FORMS` schema and a form) or is
read-only (skip form-specific steps in Phases 1, 3, and 5).

---

## Phase 1 — Types/schema

**Goal:** The domain type is defined; if the feature mutates data, its
`PLAT-WEB-FORMS-SCHEMA-01` zod schema exists before any Server Action is
written.

Read: `ARCH-WEB-APP`, `PLAT-WEB-FORMS` (mutation features only)

### Steps

1. Add the domain type in `features/{feature}/types.ts`.
2. If the feature mutates data, define its zod schema in
   `features/{feature}/schema.ts` — one schema per content variant if the
   data is a discriminated type (`PLAT-WEB-FORMS-SCHEMA-01`).

### Validation

- [ ] The domain type has no `any`.
- [ ] The schema (if present) covers every field the Server Action will
      validate, and nothing else.

---

## Phase 2 — Provider call

**Goal:** The Route Handler/Server Action's call into `PLAT-WEB-HTTP`'s
executor (or a direct Postgres query) exists and returns raw provider data —
no error mapping yet.

Read: `PLAT-WEB-HTTP`, `ARCH-WEB-APP`

### Steps

1. Create `features/{feature}/actions/{action}.ts` (`'use server'`) or
   `features/{feature}/api/route.ts` — see `PLAT-WEB-NEXT-APP`'s guidance
   for which one this feature needs.
2. Call the shared executor (`PLAT-WEB-HTTP-LIB-01`) — never an inline
   `fetch`.
3. For a direct Postgres query, respect the pooling constraint
   `PLAT-WEB-NEXT-APP-DEPLOY-POOL-01` states for the deployment target.

### Validation

- [ ] No `fetch` call is written inline outside the executor.
- [ ] No provider-level type (a raw `Response`, a driver row) is returned
      past this layer — Phase 3 maps it before anything above sees it.

---

## Phase 3 — Error mapping

**Goal:** The provider's failure is mapped into `AppError` exactly once;
the UseCase-or-not decision is made.

Read: `ARCH-WEB-APP-ERR-CLASSES`, `ARCH-WEB-APP`

### Steps

1. Map the provider's failure into `AppError` at this boundary
   (`ARCH-WEB-APP-ERR-MAP-01`), via `PLAT-WEB-HTTP-ERR-01` if this is a
   REST call.
2. Return an `Outcome` — never `throw` for a failure the caller is meant
   to handle (`PLAT-WEB-NEXT-APP-THROW-01`).
3. Decide whether this feature's business logic already coordinates more
   than the single external call in this Server Action
   (`ARCH-WEB-APP-USECASE-01`) — introduce
   `features/{feature}/useCases/{action}.ts` only if it does; do not add
   the layer speculatively.
4. If this feature mutates data, call `revalidatePath`/`revalidateTag` for
   every path whose render depends on it (`PLAT-WEB-NEXT-APP-REVALIDATE-01`).

### Validation

- [ ] Every expected failure path returns a typed `Outcome` — nothing is
      thrown for a caller-handled case.
- [ ] A UseCase module exists only if business logic already outgrew a
      single Server Action call.
- [ ] Every Server Component render that depends on this mutation is
      revalidated.

---

## Phase 4 — Hook

**Goal:** Client-side state formatting and `Outcome` exposure.

Read: `ARCH-WEB-APP`

### Steps

1. Create `features/{feature}/hooks/use{Feature}.ts`.
2. Format the Server Action/Route Handler's `Outcome` for display; expose
   `loading`/`error`/`data` state to the Client Component.
3. If this hook wraps a form submit, map a `validation` `AppError` into
   `react-hook-form`'s `setError` via `fieldErrors` here
   (`PLAT-WEB-FORMS-ERR-01`).

### Validation

- [ ] The hook exposes `Outcome`-typed state, not a raw `Response` or
      thrown error.
- [ ] No direct `fetch`/DB call happens inside the hook — it only calls
      the Server Action/Route Handler from Phase 2–3.

---

## Phase 5 — Client Component

**Goal:** Interactive rendering; user events wired; the form (if this
feature mutates data) is functional.

Read: `PLAT-WEB-NEXT`, `PLAT-WEB-DS-COMPONENT`, `PLAT-WEB-FORMS` (mutation
features only)

### Steps

1. Create `features/{feature}/components/{Feature}View.tsx`. `'use client'`
   goes on this leaf only (`PLAT-WEB-NEXT-CLIENT-01`) — not on the Server
   Component shell in Phase 6.
2. If this feature mutates data, wire `PLAT-WEB-FORMS`: `zodResolver` with
   the Phase 1 schema, `setError` from the Phase 4 hook's mapped
   `fieldErrors`.
3. Use shared components from `components/ui/` (`PLAT-WEB-DS-COMPONENT-01`)
   and icons from the centralized module (`PLAT-WEB-DS-ICON-01`) — no ad
   hoc icon-library import, no duplicated one-off component this feature
   should be sharing.
4. Apply `PLAT-WEB-A11Y`'s semantic-HTML/alt-text/`aria-label`/heading/focus
   rules. Its container-guard (`PLAT-WEB-A11Y-GUARD-01`) and
   `ErrorBoundary` (`PLAT-WEB-A11Y-EB-01`) rules are specific to
   `web-spa`'s manual container-component model and do not transfer
   mechanically here — Next.js's own `loading.tsx`/`error.tsx`
   file conventions (Phase 6) serve the equivalent role for this
   architecture instead of a hand-rolled guard/boundary.

### Validation

- [ ] `'use client'` is present only on this component, not the Server
      Component shell.
- [ ] Shared components come from `components/ui/`; icons come from the
      centralized module.
- [ ] Every icon-only interactive element has `aria-label`; every `<img>`
      has `alt`.

---

## Phase 6 — Server Component shell

**Goal:** Initial fetch/render exists; revalidation wiring is confirmed
end to end.

Read: `PLAT-WEB-NEXT`, `ARCH-WEB-APP`

### Steps

1. Create `features/{feature}/components/{Feature}Page.tsx` — a Server
   Component: no `'use client'`, no mutation logic.
2. Fetch initial data via the Phase 2 provider call and pass it to the
   Client Component from Phase 5 as props.
3. Add `loading.tsx`/`error.tsx` alongside this route's `page.tsx` if it
   needs loading/error UI — the Next.js-native equivalent to `web-spa`'s
   manual loading/error guard and `ErrorBoundary` wrap, which this
   architecture does not use (see Phase 5's a11y note).
4. Register the route under `app/{feature}/page.tsx` if this is a new
   route, and confirm the Phase 3 revalidation actually invalidates this
   shell's cached render after a mutation.

### Validation

- [ ] The Server Component shell has no `'use client'` and no mutation
      logic.
- [ ] The route renders the feature end-to-end in `next dev`.
- [ ] A test mutation followed by a re-render shows fresh data, not a
      stale cached render.

---

## Phase 7 — Test gate

**Goal:** Server Action and Provider-boundary tests pass; `next build` is
clean.

Read: `QG-WEB-TESTING`, `PLAT-WEB-NEXT-APP-DEPLOY`

### Steps

1. Test the Server Action directly per `QG-WEB-TESTING-SA-01` — call it,
   assert on its `Outcome`, don't mount the form.
2. Test the Provider-boundary call with MSW per `QG-WEB-TESTING-MSW-01`.
3. If this feature added or changed a `middleware.ts`-gated route, add or
   update the E2E coverage `QG-WEB-TESTING-MW-01` requires.
4. Run `next build` — zero TypeScript errors
   (`PLAT-WEB-NEXT-APP-DEPLOY-BUILD-01`).

### Validation

- [ ] The Server Action test asserts on `Outcome`, not a mounted form
      submit.
- [ ] The Provider-boundary test mocks at MSW, not the executor's own
      methods.
- [ ] `next build` passes with zero errors.

---

## Note — `PLAT-WEB-A11Y` scope, resolved this session

`PLAT-WEB-A11Y` stays `architecture: web-spa` only; it is not broadened to
`web-app`, and no sibling `web-app`-specific accessibility doc is created.
Five of its seven rules (semantic HTML, `alt`, `aria-label`, heading
hierarchy, focus) are architecture-agnostic in substance and are cited
directly from Phase 5 above. Its remaining two rules —
`PLAT-WEB-A11Y-GUARD-01` (a container component guarding `loading`/`error`
before rendering data) and `PLAT-WEB-A11Y-EB-01` (every route wrapped in a
React `ErrorBoundary`) — are specific to `web-spa`'s manual
container/`ErrorBoundary` model and do not correctly describe `web-app`,
which uses Next.js's own `loading.tsx`/`error.tsx` file conventions for the
same purpose instead. Broadening the doc's `architecture` field wholesale
would have made those two rules appear to apply as written when they don't;
citing the five that do transfer, in place, was the accurate fix.
