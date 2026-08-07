---
id: ARCH-WEB-APP
type: overview
layer: architectures
platform: [web]
architecture: [web-app]
requires: [CORE-COUPLING, CORE-NAMING, PAT-DATA-ACCESS, PAT-OUTCOME, PAT-OBSERVER]
related: [ARCH-PC]
tags: [web, nextjs, server-actions, route-handlers, server-components, client-components, layers]
status: active
---

# Web App Architecture

## What it is

Web App is a layered architecture for Next.js applications that are
server-capable for a specific reason: some part of the app needs a held
external-call boundary a browser cannot open directly — a REST client with
server-only credentials, or a database connection (e.g. a Cloud SQL Auth
Proxy) that must live in a long-running server process, not a client bundle.
Next.js is adopted here for that boundary, not for SEO — that concern belongs
to `ARCH-WEB-CONTENT`.

The layering is `ARCH-PC`'s View → ViewModel → UseCase → Repository/DataSource
→ Provider stack restated for the Next.js Server/Client Component boundary
instead of KMP. This doc cites `ARCH-PC` for the layering discipline; it does
not generalize or edit it — `ARCH-PC` remains mobile-specific and unaware of
this doc.

This is a real fork of `architectures/web-spa/`: nothing in `web-spa`'s
client-only hooks/Context model transfers to a Server/Client Component
boundary. `web-spa` is not touched or deprecated by this doc.

## Layer stack

```
Server Component      Initial data-fetch shell. Renders. No mutation logic.
Client Component      Renders interactive state. Emits user events.
Hook                  Formats data for display. Manages UI state/events.
Route Handler /        The one place all external calls happen: REST client
Server Action          to a backend, or a held DB connection. Repository/
                       DataSource-equivalent boundary.
Provider               External REST API / Postgres.
```

## Data flow

```
Server Component
  ↓ initial render (props, server-fetched data)
Client Component
  ↓ user event
Hook
  ↓ invoke Server Action / call Route Handler
Route Handler / Server Action
  ↓ calls Provider directly
Provider (REST API / Postgres)
```

State flows upward as reactive/typed results — a hook exposes `Outcome`-typed
state (`PAT-OUTCOME`) and, where the data can change while the consumer is
active, an observable subscription (`PAT-OBSERVER`) rather than a one-shot
fetch. Mutations flow downward as calls into the Route Handler/Server Action
layer — never as a direct client call to a REST API or database.

## Layer boundaries — what may NOT cross

| Boundary | What is blocked |
|---|---|
| Route Handler/Server Action → above | Provider types (`Response`, a driver row/cursor type) |
| Route Handler/Server Action → above | Provider exceptions (raw thrown `Error`, `fetch` rejection, Postgres driver error) |
| Hook → above | Unmapped Route Handler/Server Action-specific shapes |
| Client Component | No direct external calls — invokes hooks/Server Actions only, never `fetch`s a backend or opens a DB connection itself |
| Server Component | No mutation logic — initial render only |

## Feature folder structure

```
features/{feature}/
├── actions/
│   └── {action}.ts             Server Action — the one place external calls happen
├── api/
│   └── route.ts                 Route Handler (alternative to a Server Action)
├── useCases/                     Only once business logic outgrows a single Server Action call
│   └── {Action}{Entity}UseCase.ts
├── hooks/
│   └── use{Feature}.ts          Client-side state; calls the Server Action/Route Handler
└── components/
    ├── {Feature}Page.tsx         Server Component shell — initial fetch, renders
    └── {Feature}View.tsx         Client Component — interactive state, user events
```

## Which layer owns which concern

| Concern | Layer |
|---|---|
| REST call / Postgres query | Route Handler / Server Action |
| Provider error → typed `AppError` mapping | Route Handler / Server Action |
| Business rules, multi-step operation coordination | UseCase (once introduced — see `ARCH-WEB-APP-USECASE-01`) |
| Formatting data for display, UI state/events | Hook |
| Initial data-fetch, server render | Server Component |
| Interactive rendering, emitting user events | Client Component |

## Layer-inclusion decisions

```rule
id: ARCH-WEB-APP-USECASE-01
statement: A UseCase-equivalent module MUST be introduced once a feature's business logic requires coordinating more than the single external call already in its Server Action — it MUST NOT be added speculatively.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-USECASE-01 — Introduce a UseCase-equivalent module only once business logic outgrows a single Server Action call; do not add the layer speculatively.
```

This is expected to trigger soon in practice, not a hypothetical — both
analytics dashboard views and the content-authoring/validation surface are
exactly the kind of multi-step business logic this threshold is meant to
catch. When it does, the module lives at `features/{feature}/useCases/{action}.ts`,
called from the Server Action — same naming shape as pragmatic-clean's
`{Action}{Entity}UseCase`.

**No Repository layer for now** — decided, not deferred as a gap. Two sources
total exist on this boundary (REST to a backend, direct Postgres), nothing
merges both within one feature today, and persistence/multi-source
coordination is rare on this side of the stack generally. Revisit only if a
feature actually needs both sources merged under one SSOT — until then, a
Server Action/Route Handler talking to a single Provider is the
DataSource-equivalent boundary and no Repository-equivalent layer is
introduced.

**Auth enforcement: `middleware.ts`**, not a per-page guard component. Auth is
checked once, before any Server Component renders, rather than repeated per
protected route the way `web-spa`'s `AuthGuard` does — the Next.js middleware
boundary makes a single upfront check sufficient where a client-side SPA
needed a guard component per route.

## Deliberately out of scope

Shared components are not decided in this doc. Component rules are already
fully covered by `ARCH-WEB-COMPONENTS`; this doc cites that instead of
duplicating it, and does not add a sibling `components.md` because
`web-app`-specific component rules do not genuinely diverge from it.
