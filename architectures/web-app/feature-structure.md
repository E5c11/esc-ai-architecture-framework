---
id: ARCH-WEB-APP-FEATURE-STRUCTURE
type: guide
layer: architectures
platform: [web]
architecture: [web-app]
requires: [ARCH-WEB-APP, ARCH-WEB-APP-COMPONENT, ARCH-WEB-APP-HOOK, CORE-NAMING, CORE-COUPLING]
related: [ARCH-WEB-APP-MODULES, ARCH-WEB-APP-COMPOSITION, ARCH-PC-FEATURE, PLAT-WEB-DS-COMPONENT, PLAT-WEB-NEXT]
tags: [feature, structure, folders, routes, app-router, public-surface, shared, promotion]
status: active
---

# Feature Structure

## Responsibility

Say where each kind of file goes, so that a new feature has an obvious shape and an
existing one can be navigated without a map. The dependency rules between layers are
owned by `ARCH-WEB-APP` (`ARCH-WEB-APP-DEP-01` to `-08`); this document owns the
folder layout, the route boundary, the public surface of a feature, and what may live
in shared code.

This restates `ARCH-PC-FEATURE` for a Next.js project.

## Layout

```
app/                                  Next.js routes (the framework's convention)
├── layout.tsx                        Root layout: AppProvider, theme
├── (app)/region/[region]/page.tsx    Route: composes one feature page. Nothing else
└── (app)/region/[region]/error.tsx   Route boundary files live with the route

features/{feature}/
├── components/                       {Feature}Page.tsx (server shell), {Feature}View.tsx (root view), presentational components
├── hooks/                            use{Feature}.ts, the presentation mapping, ViewState types
├── useCases/                         {Action}{Entity}UseCase.ts, only once the threshold is met
├── domain/                           Entities, value objects, pure transforms for this feature
├── data/                             DataSource and Repository interfaces, implementations, mappers, fakes, contract tests
├── content/                          Static strings, tables, chart definitions
└── index.ts                          The feature's public surface

shared/
├── ui/                               Presentational components two or more features use
├── domain/                           Domain code two or more features use
└── lib/                              Framework-free helpers named for a concept (see the modules document)

composition/                          Builds and wires the graph (ARCH-WEB-APP-COMPOSITION)
```

```rule
id: ARCH-WEB-APP-FEAT-STRUCT-01
statement: Each feature MUST live under `features/{feature}/` with its layers in the folders above, and a layer folder MUST be created only when the feature has code for it.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-FEAT-STRUCT-01 — Each feature MUST live under `features/{feature}/` with its layers in the folders above, and a layer folder MUST be created only when the feature has code for it.
```

An empty `useCases/` folder is a promise the feature has not kept
(`ARCH-WEB-APP-USECASE-01`).

```rule
id: ARCH-WEB-APP-FEAT-PLACE-01
statement: Each kind of file MUST go in its own layer folder: presentation types and the presentation mapping in `hooks/`, entities and value objects in `domain/`, DataSource and Repository interfaces with their implementations and mappers in `data/`, and error types in the shared error module, not in the feature.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-FEAT-PLACE-01 — Each kind of file MUST go in its own layer folder: presentation types and the presentation mapping in `hooks/`, entities and value objects in `domain/`, DataSource and Repository interfaces with their implementations and mappers in `data/`, and error types in the shared error module, not in the feature.
```

Presentation types and domain types are different things; do not mix them in one
file. The error union is shared across features by design
(`ARCH-WEB-APP-ERR-CLASSES`), so a feature does not define its own.

## Routes are thin

```rule
id: ARCH-WEB-APP-FEAT-ROUTE-01
statement: A route file (`page.tsx`, `layout.tsx`) MUST only compose features and route-level boundary files; it MUST NOT contain logic, data fetching of its own, or markup beyond layout.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-FEAT-ROUTE-01 — A route file (`page.tsx`, `layout.tsx`) MUST only compose features and route-level boundary files; it MUST NOT contain logic, data fetching of its own, or markup beyond layout.
```

```rule
id: ARCH-WEB-APP-FEAT-ROUTE-02
statement: Composition of two or more features on one screen MUST happen in the route (or a layout), never inside either feature.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-FEAT-ROUTE-02 — Composition of two or more features on one screen MUST happen in the route (or a layout), never inside either feature.
```

The route is the one place allowed to know several features. When feature A needs to
show something feature B owns, the route renders B and passes it to A as `children`
or a slot prop. A imports nothing of B (`ARCH-WEB-APP-DEP-07`), and the cross-feature
decision does not hide in a hook "because the route felt like too many layers".

## Public surface

```rule
id: ARCH-WEB-APP-FEAT-PUBLIC-01
statement: A feature's `index.ts` MUST export only what other code needs (its page or root view and its public types), and MUST NOT export hooks, DataSources, Repositories, UseCases or mappers.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-FEAT-PUBLIC-01 — A feature's `index.ts` MUST export only what other code needs (its page or root view and its public types), and MUST NOT export hooks, DataSources, Repositories, UseCases or mappers.
```

The import side is `ARCH-WEB-APP-DEP-07`: other code imports a feature only through
this file. The export side is this rule: a small surface is what lets a feature's
insides change freely.

## Shared code

```rule
id: ARCH-WEB-APP-FEAT-SHARED-01
statement: Code MUST move to `shared/` only when a second feature actually needs it, and MUST NOT be moved there in advance of a second consumer.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-FEAT-SHARED-01 — Code MUST move to `shared/` only when a second feature actually needs it, and MUST NOT be moved there in advance of a second consumer.
```

Promotion on a guess produces shared code with one consumer and a vague owner. The
UI-specific form of this rule is `PLAT-WEB-DS-COMPONENT-01`.

```rule
id: ARCH-WEB-APP-FEAT-SHARED-02
statement: `shared/` MUST NOT host a component, type or function specific to one feature's domain, even to avoid a cross-feature import, and shared UI MUST be typed only against generic presentation shapes, never against a feature's domain model.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-FEAT-SHARED-02 — `shared/` MUST NOT host a component, type or function specific to one feature's domain, even to avoid a cross-feature import, and shared UI MUST be typed only against generic presentation shapes, never against a feature's domain model.
```

A `shared/` folder that collects whatever was inconvenient to import across features
becomes a second, unowned application. The fix for a cross-feature need is the route
composing the features (`ARCH-WEB-APP-FEAT-ROUTE-02`), not relocating one feature's
code into shared.

## Growth

```rule
id: ARCH-WEB-APP-FEAT-SUB-01
statement: A feature whose layer folders hold more than about ten files each, or whose screens have separate state, SHOULD be split into sub-features, each with the same shape one level deeper.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-FEAT-SUB-01 — A feature whose layer folders hold more than about ten files each, or whose screens have separate state, SHOULD be split into sub-features, each with the same shape one level deeper.
```

```
features/dashboard/
├── index.ts
└── features/
    ├── fault-resolution/          components/ hooks/ domain/ data/
    └── data-quality/              components/ hooks/ domain/ data/
```

A sub-feature is imported only through its parent's public surface.

## Naming and tests

```rule
id: ARCH-WEB-APP-FEAT-NAME-01
statement: Implementations MUST NOT use an `Impl` suffix, and a DataSource implementation MUST put the provider first, as in `FirestoreSnapshotDataSource`, not `SnapshotFirestoreDataSource`.
type: hard
scope: naming
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-FEAT-NAME-01 — Implementations MUST NOT use an `Impl` suffix, and a DataSource implementation MUST put the provider first, as in `FirestoreSnapshotDataSource`, not `SnapshotFirestoreDataSource`.
```


The doubles per layer: none for the domain, DataSource fakes for UseCases and
Repositories, a test provider with fakes for Hooks, plain props for presentational
components.

## Anti-patterns

The ban on `utils`, `helpers`, `common`, `misc` and `base` names is
`ARCH-WEB-APP-MOD-NAME-01`. The same applies to a feature folder: nothing named for a
technical grab-bag, and no `Manager`, `Helper` or `Service` object holding several
unrelated responsibilities.

## Violations

- A route file with a `fetch`, a calculation or a conditional on data
- Two features composed inside a hook or a component of one of them
- A feature `index.ts` that exports its hooks and DataSource
- `shared/` holding a type from one feature's domain
- A file moved to `shared/` with a single importer
- A feature importing another feature's `data/` folder
- Presentation types and domain types in one file
- `SnapshotFirestoreDataSource`, `FeedRepositoryImpl`
