---
id: ARCH-PC-REPOSITORY
type: guide
layer: architecture
platform: [mobile]
architecture: [pragmatic-clean]
requires: [ARCH-PC, ARCH-PC-DATASOURCE, CORE-SSOT, PAT-DATA-ACCESS]
related: [ARCH-PC-USECASE, ARCH-PC-ERROR-FLOW, ARCH-PC-DI]
tags: [repository, ssot, coordination, cache, multi-source]
---

# Repository Layer

## Responsibility

Coordinate multiple DataSources and enforce Single Source of Truth (`CORE-SSOT`).

The Repository knows which DataSource is authoritative (always local). It decides
when to fetch from remote and how to update local after a successful remote call.

## When to create a Repository

**Rule ARCH-PC-REP-OPTIONAL-01 (soft):** The Repository layer MAY be skipped when
a feature has exactly one DataSource. The UseCase may consume the DataSource directly.

Create a Repository only when:
- There is a local DataSource AND a remote DataSource that must be coordinated
- SSOT enforcement is required (local is truth; remote feeds it)

## Structure

```
data/repository/
├── {Feature}Repository.kt           Interface
└── Default{Feature}Repository.kt    Implementation
```

**Rule ARCH-PC-REP-INTERFACE-01 (hard):** Repository MUST define an interface.

**Rule ARCH-PC-REP-NAMING-01 (hard):** Interface is `{Feature}Repository`.
Implementation is `Default{Feature}Repository`.

## What a Repository talks to

**Rule ARCH-PC-REP-DATASOURCE-01 (hard):** Repository MUST only call DataSources.
It MUST NOT call DAOs, APIs, or any provider directly.

**Rule ARCH-PC-REP-INJECT-01 (hard):** DataSources are injected via constructor.
The Repository never instantiates them.

## Return types

**Rule ARCH-PC-REP-RETURN-01 (hard):** Repository methods returning sync-dependent
data MUST return `Flow<T>`.

**Rule ARCH-PC-REP-RETURN-02 (hard):** One-shot operations MUST use suspend functions.

**Rule ARCH-PC-REP-RETURN-03 (hard):** Repository MUST NOT return loading states
or resource wrappers. That is the ViewModel's responsibility.

**Rule ARCH-PC-REP-RETURN-04 (hard):** Return types are plain domain models only.
Never DTOs, entities, or provider types.

## SSOT enforcement

**Rule ARCH-PC-REP-SSOT-01 (hard):** When coordinating local and remote DataSources,
the Repository MUST observe the local DataSource as the stream that consumers read.
Never observe the remote DataSource directly.

**Rule ARCH-PC-REP-SSOT-02 (hard):** After a successful remote fetch, the Repository
MUST write the result to the local DataSource. The local DataSource then emits
the update to all observers.

### Standard coordination pattern

```
Repository.observeData()
    1. Attempt remote fetch → write result to local DataSource
    2. Observe local DataSource (the SSOT)
    3. Emit from local to caller
```

Remote failure during step 1 does not prevent step 2 from emitting cached data.

## Error handling

**Rule ARCH-PC-REP-FALLBACK-01 (hard):** When implementing fallback strategies,
the Repository MUST rethrow domain exceptions after fallback logic is exhausted.
Never swallow exceptions silently.

Domain exceptions pass through the Repository unchanged — they were already
translated by the DataSource. The Repository does not re-translate.

## DI scope and qualifiers

DataSources are injected with named qualifiers when a Repository takes both a
local and a remote implementation of the same interface.

See `ARCH-PC-DI` for scope and qualifier rules.

## Violations

- Repository calling a DAO or API directly, bypassing a DataSource
- Repository returning a loading/resource wrapper type
- Repository observing the remote DataSource as the primary stream
- Not writing remote results to local DataSource after a successful fetch
- Swallowing a domain exception instead of rethrowing after fallback
- Repository created for a single-DataSource feature (use the DataSource directly)
