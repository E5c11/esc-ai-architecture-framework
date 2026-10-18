---
id: ARCH-WEB-APP
type: overview
layer: architectures
platform: [web]
architecture: [web-app]
requires: [CORE-COUPLING, CORE-NAMING, CORE-DI, CORE-SSOT, PAT-DATA-ACCESS, PAT-OUTCOME, PAT-OBSERVER]
related: [ARCH-PC, ARCH-WEB-APP-ERR-CLASSES, ARCH-WEB-APP-DATASOURCE, ARCH-WEB-APP-REPOSITORY, ARCH-WEB-APP-DOMAIN, ARCH-WEB-APP-USECASE, ARCH-WEB-APP-HOOK, ARCH-WEB-APP-COMPONENT, ARCH-WEB-APP-COMPOSITION, ARCH-WEB-APP-FEATURE-STRUCTURE, ARCH-WEB-APP-MODULES]
tags: [web, nextjs, layers, pragmatic-clean, datasource, usecase, hook, dependency-direction, server-actions, static-export, firebase]
status: active
---

# Web App Architecture

## What it is

Web App is **Pragmatic Clean (`ARCH-PC`) for a Next.js application**: the same
layers, the same responsibility split and the same dependency direction, written
in TypeScript and React instead of Kotlin and Compose. It is not a new style. A
reader who knows `ARCH-PC` already knows this one; this document records only
what the web changes.

It serves two **runtimes** with one set of layers. The runtime decides *where
the DataSource executes*, not how the code is organised:

| Runtime | The DataSource runs in | Typical provider | Use when |
|---|---|---|---|
| `server` | A Server Action or Route Handler, on a held server process | REST API with server-only credentials; Postgres through a connection that must live server-side | Some part of the app needs a boundary a browser cannot open itself |
| `static-export` | The browser (Next.js `output: 'export'`) | Firebase SDK (Firestore reads under security rules), callable functions | Everything the app needs is reachable from the browser under provider-side access rules; no server of its own is needed |

A project declares its runtime in its project profile as `frameworks.runtime`.
`ARCH-PC`'s layering is restated here for the Next.js Server/Client Component
boundary; this document cites `ARCH-PC`, it does not generalise or edit it.
Next.js is adopted for the `server` runtime for a held external-call boundary,
not for SEO (that concern belongs to `ARCH-WEB-CONTENT`).

This is a real fork of `architectures/web-spa/`: nothing in `web-spa`'s
client-only hooks/Context model transfers to a Server/Client Component boundary.
`web-spa` is not touched or deprecated by this document.

## How the layers map

| `ARCH-PC` layer | `web-app` layer | What it is |
|---|---|---|
| View | **Component** | Server or Client Component. Renders; emits user events. No logic, no data access |
| ViewModel | **Hook** | Client-side. Formats data for display; owns UI state and events; exposes `Outcome`-typed state |
| UseCase / Orchestrator | **UseCase** | Plain TypeScript. Business logic and multi-step coordination. No React, no framework |
| Repository (optional) | **Repository** | Plain TypeScript. Coordinates several DataSources behind one source of truth |
| DataSource | **DataSource** | Abstracts one provider. Maps types. Translates errors. Implements an interface |
| Provider | Provider | REST API, Postgres, Firestore SDK, callable function. Not owned by this architecture |
| — | **Domain** | Pure entities, value objects and transforms. No I/O, no framework |
| Composition root | **Composition** | The one module that builds and wires the concrete graph |

## Layer stack

```
Component        Renders state. Emits user events. No logic. No data access.
    ↓
Hook             Formats data for display. UI state and events. Outcome-typed.
    ↓
UseCase          Business logic; coordinates one or more DataSources/Repositories.
    ↓            (Only once the logic outgrows a single call; see below.)
Repository       Coordinates several DataSources; enforces SSOT.   (Optional)
    ↓
DataSource       Abstracts one provider. Maps provider types to domain types.
    ↓            Translates provider errors, once.
Provider         REST / Postgres / Firestore / callable.
                 (Not owned by this architecture.)

Domain           Entities, value objects, rule tables, pure transforms.
                 Imported by every layer above; imports nothing.
Composition      Builds providers, DataSources, Repositories, UseCases; hands them out.
```

## Data flow

`server` runtime:

```
Server Component  ──initial render (presentation-mapped props)──▶  Client Component
                                                                       ↓ user event
                                                                      Hook
                                                                       ↓ invoke Server Action / Route Handler
Server Action / Route Handler  ──calls──▶  UseCase / DataSource  ──▶  Provider (REST / Postgres)
```

`static-export` runtime:

```
Client Component
  ↓ user event
Hook
  ↓ invoke UseCase / DataSource (obtained from the composition root)
UseCase (optional)
  ↓
Repository (optional)
  ↓
DataSource  (runs in the browser)
  ↓
Provider (Firestore SDK read under security rules / callable function)
```

State flows upward as typed results: a hook exposes `Outcome`-typed state
(`PAT-OUTCOME`) and, where the data can change while the consumer is active, an
observable subscription (`PAT-OBSERVER`) rather than a one-shot fetch.
Mutations flow downward as calls. In neither runtime does a Component call a
provider.

## Layer boundaries — what may NOT cross

| Boundary | What is blocked |
|---|---|
| DataSource → above | Provider types (`Response`, a driver row or cursor, `DocumentSnapshot`, a callable's raw payload) |
| DataSource → above | Provider exceptions (a thrown `Error`, a `fetch` rejection, a driver or Firestore error) |
| Repository → above | DataSource types; loading and resource states |
| UseCase → above | Repository or DataSource types |
| Hook → above | Domain models (map to presentation shapes first) |
| Component | Any provider SDK, DataSource, Repository or UseCase import. Business logic. Data fetching of its own |
| Server Component | Mutation logic. It renders initial data only |

## Layer contracts

| Layer | Receives | Returns | Must NOT |
|---|---|---|---|
| Component | Props, user events | Rendered UI | Contain logic; fetch; import below the hook |
| Hook | User events; UseCase/DataSource results | `Outcome`-typed presentation state | Import a provider SDK or an implementation; leak domain models |
| UseCase | Domain values, primitives | `Outcome` of domain values | Import React, Next or a provider SDK; know which runtime it runs in |
| Repository | Domain values | `Outcome` of domain values | Return DataSource types; decide business policy |
| DataSource | Domain parameters | `Outcome` of domain values | Return provider types; own business rules; throw an expected failure |
| Domain | Domain values | Domain values | Perform I/O; read the clock; import a framework or SDK |
| Composition | Configuration | A wired graph | Contain logic |

## Dependency direction

Allowed imports, by layer. Anything not listed is forbidden.

| Layer | May import |
|---|---|
| Component | Hooks; presentation types the hook exports; shared UI components |
| Hook | UseCases; (below the UseCase threshold) Repository/DataSource **interfaces**; presentation types; Domain types |
| UseCase | Repository/DataSource **interfaces**; Domain |
| Repository | DataSource **interfaces**; Domain |
| DataSource | Its own provider SDK or client; Domain types; the error union |
| Domain | Nothing but the language's own standard library |
| Composition | Every concrete implementation; the layers it wires |

```rule
id: ARCH-WEB-APP-DEP-01
statement: Domain code MUST NOT import from any other layer and MUST NOT import React, Next.js, a provider SDK, or any I/O library.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DEP-01 — Domain code MUST NOT import from any other layer and MUST NOT import React, Next.js, a provider SDK, or any I/O library.
```

```rule
id: ARCH-WEB-APP-DEP-02
statement: UseCase and Repository code MUST NOT import React, Next.js, a provider SDK, or a DataSource implementation; they depend on interfaces.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DEP-02 — UseCase and Repository code MUST NOT import React, Next.js, a provider SDK, or a DataSource implementation; they depend on interfaces.
```

```rule
id: ARCH-WEB-APP-DEP-03
statement: A provider SDK or client MUST be imported only by the DataSource that wraps it (and by the composition module that constructs that client).
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DEP-03 — A provider SDK or client MUST be imported only by the DataSource that wraps it (and by the composition module that constructs that client).
```

```rule
id: ARCH-WEB-APP-DEP-04
statement: A Hook MUST NOT import a provider SDK or a DataSource or Repository implementation; it depends on a UseCase or, below the UseCase threshold, on a DataSource or Repository interface.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DEP-04 — A Hook MUST NOT import a provider SDK or a DataSource or Repository implementation; it depends on a UseCase or, below the UseCase threshold, on a DataSource or Repository interface.
```

```rule
id: ARCH-WEB-APP-DEP-05
statement: A Component MUST NOT import a provider SDK, DataSource, Repository or UseCase, and MUST NOT fetch data itself; it receives data through a Hook or props.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DEP-05 — A Component MUST NOT import a provider SDK, DataSource, Repository or UseCase, and MUST NOT fetch data itself; it receives data through a Hook or props.
```

A `server`-runtime Server Component shell may obtain a UseCase or DataSource from
the composition root to render initial data. It is the only Component allowed to,
it passes presentation-mapped props down, and it contains no mutation logic.

```rule
id: ARCH-WEB-APP-DEP-06
statement: Concrete DataSources, Repositories and UseCases MUST be constructed only in the composition module (and in tests); every other module receives what it needs.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DEP-06 — Concrete DataSources, Repositories and UseCases MUST be constructed only in the composition module (and in tests); every other module receives what it needs.
```

```rule
id: ARCH-WEB-APP-DEP-07
statement: A feature MUST NOT import another feature's internals; it imports only that feature's public surface, and code two features share MUST move to shared code.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DEP-07 — A feature MUST NOT import another feature's internals; it imports only that feature's public surface, and code two features share MUST move to shared code.
```

```rule
id: ARCH-WEB-APP-DEP-08
statement: The layer contract MUST be declared as a checkable dependency contract in the project's configuration and MUST run in CI.
type: hard
scope: structure
enforced_by: [planner, reviewer]
violation_message: Violates ARCH-WEB-APP-DEP-08 — The layer contract MUST be declared as a checkable dependency contract in the project's configuration and MUST run in CI.
```

A dependency rule that only lives in a document is a suggestion. The Python
architecture meets the equivalent rule (`ARCH-PY-DEP-04`) with `import-linter`;
the web equivalent is a declared contract over `import` statements and path
aliases, run as an architecture check. Until a project declares one, the eight
rules above are reviewer-enforced.

## Feature folder structure

```
features/{feature}/
├── components/        Components. {Feature}Page.tsx (Server shell), {Feature}View.tsx (Client)
├── hooks/             use{Feature}.ts. Presentation state; calls a UseCase or DataSource interface
├── useCases/          {Action}{Entity}UseCase.ts — only once the threshold below is met
├── domain/            Entities, value objects, pure transforms for this feature
├── data/              DataSource (and Repository) interfaces and implementations, with their mappers
└── index.ts           The feature's public surface

composition/           The composition module: builds and wires the concrete graph
shared/                Code two or more features use (UI components, shared domain, utilities)
app/                   Next.js routes. Thin: compose a feature, nothing else
```

`server` runtime adds `features/{feature}/actions/{action}.ts` (Server Action) and
`features/{feature}/api/route.ts` (Route Handler) as the host for a server
DataSource or UseCase call. Routes and the host files contain no logic of their
own.

## Which layer owns which concern

| Concern | Layer |
|---|---|
| REST call / Postgres query / Firestore read / callable invocation | Provider |
| DTO or document → domain mapping | DataSource |
| Provider error → typed `AppError` | DataSource |
| SSOT enforcement; merging several DataSources | Repository |
| Business rules, validation, transformation, multi-step coordination | UseCase |
| Pure rules and transforms with no I/O | Domain |
| Formatting data for display; UI state and events | Hook |
| Initial data-fetch shell; server render | Server Component (`server` runtime) |
| Interactive rendering; emitting user events | Client Component |
| Building and wiring the concrete graph | Composition |

## Layer-inclusion decisions

```rule
id: ARCH-WEB-APP-USECASE-01
statement: A UseCase-equivalent module MUST be introduced once a feature's business logic requires coordinating more than the single external call already in its Server Action or Hook — it MUST NOT be added speculatively.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-USECASE-01 — Introduce a UseCase-equivalent module only once business logic outgrows a single Server Action or Hook call; do not add the layer speculatively.
```

In the `server` runtime the call in question is the one in the Server Action or
Route Handler; in `static-export` it is a single DataSource call from a Hook. The
layer appears when logic outgrows one call, not before.

```rule
id: ARCH-WEB-APP-REPO-01
statement: A Repository MUST be introduced only when one entity is assembled from more than one DataSource (for example a cache and a live source), and MUST NOT be added speculatively.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-REPO-01 — Introduce a Repository only when one entity is assembled from more than one DataSource; do not add the layer speculatively.
```

**No Repository layer by default** — decided, not deferred. Most features have
one source, so a DataSource behind its interface is the whole data boundary.

### Runtime and auth

```rule
id: ARCH-WEB-APP-RUNTIME-01
statement: A project MUST declare its runtime (`server` or `static-export`) as `frameworks.runtime` in its project profile, and MUST NOT use a feature the declared runtime does not support.
type: hard
scope: structure
enforced_by: [planner, reviewer]
violation_message: Violates ARCH-WEB-APP-RUNTIME-01 — A project MUST declare its runtime (`server` or `static-export`) as `frameworks.runtime` in its project profile, and MUST NOT use a feature the declared runtime does not support.
```

```rule
id: ARCH-WEB-APP-RUNTIME-02
statement: In the `static-export` runtime, a DataSource MUST NOT embed or read a secret, and every read and write MUST be authorised by the provider's own access rules, not by client code.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-RUNTIME-02 — In the `static-export` runtime, a DataSource MUST NOT embed or read a secret, and every read and write MUST be authorised by the provider's own access rules, not by client code.
```

Everything that ships in a browser bundle is public. Under `static-export` the
provider's access rules (Firestore security rules, callable-function auth checks)
are the access boundary; a client-side route guard is a convenience for the user
interface and is never the boundary.

```rule
id: ARCH-WEB-APP-BFF-01
statement: A separate backend-for-frontend service SHOULD NOT be introduced unless one of these is recorded as the reason: a server-held secret, shaping data across several sources, server rendering, or hiding the data store from the client.
type: soft
scope: structure
enforced_by: [planner, reviewer]
violation_message: Violates ARCH-WEB-APP-BFF-01 — A separate backend-for-frontend service SHOULD NOT be introduced unless a server-held secret, shaping data across sources, server rendering, or hiding the data store is recorded as the reason.
```

A `server`-runtime app already has a server boundary (Server Actions and Route
Handlers); that is not a BFF in this sense. A BFF is an additional service.

**Auth enforcement.** In the `server` runtime: `middleware.ts`, not a per-page
guard component. Auth is checked once, before any Server Component renders, rather
than repeated per protected route the way `web-spa`'s `AuthGuard` does. In the
`static-export` runtime there is no request-time middleware; the provider's access
rules enforce access (`ARCH-WEB-APP-RUNTIME-02`) and the client reflects the
signed-in state.

## Deliberately out of scope

Shared components are not decided in this document. Component rules are covered
by `ARCH-WEB-COMPONENTS`; this document cites that instead of duplicating it.

## Layer documents

The per-layer documents hold each layer's detailed rules, in the shape of the
`ARCH-PC` layer documents. They live beside this overview in
`architectures/web-app/`: `datasource.md`, `repository.md`, `domain.md`,
`usecase.md`, `hook.md`, `component.md`, `composition.md`,
`feature-structure.md`, `modules.md`, `error-flow.md` and `observability.md`.
Typed errors are in `error-classes.md` (`ARCH-WEB-APP-ERR-CLASSES`). Until a
layer's document exists, this overview's boundary, contract and dependency tables
are the authority for that layer.
