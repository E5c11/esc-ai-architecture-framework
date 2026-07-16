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

```rule
id: ARCH-PC-REP-OPTIONAL-01
statement: The Repository layer MAY be skipped when a feature has exactly one DataSource.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-REP-OPTIONAL-01 — The Repository layer MAY be skipped when a feature has exactly one DataSource.
```

The UseCase may consume the DataSource directly.

Create a Repository only when:
- There is a local DataSource AND a remote DataSource that must be coordinated
- SSOT enforcement is required (local is truth; remote feeds it)

## Structure

```
data/repository/
├── {Feature}Repository.kt           Interface
└── Default{Feature}Repository.kt    Implementation
```

```rule
id: ARCH-PC-REP-INTERFACE-01
statement: Repository MUST define an interface.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-REP-INTERFACE-01 — Repository MUST define an interface.
```

```rule
id: ARCH-PC-REP-NAMING-01
statement: Interface is `{Feature}Repository`.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-REP-NAMING-01 — Interface is `{Feature}Repository`.
```

Implementation is `Default{Feature}Repository`.

## What a Repository talks to

```rule
id: ARCH-PC-REP-DATASOURCE-01
statement: Repository MUST only call DataSources.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-REP-DATASOURCE-01 — Repository MUST only call DataSources.
```

It MUST NOT call DAOs, APIs, or any provider directly.

```rule
id: ARCH-PC-REP-INJECT-01
statement: DataSources are injected via constructor.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-REP-INJECT-01 — DataSources are injected via constructor.
```

The Repository never instantiates them.

## Return types

```rule
id: ARCH-PC-REP-RETURN-01
statement: Repository methods returning sync-dependent data MUST return `Flow<T>`.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-REP-RETURN-01 — Repository methods returning sync-dependent data MUST return `Flow<T>`.
```

```rule
id: ARCH-PC-REP-RETURN-02
statement: One-shot operations MUST use suspend functions.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-REP-RETURN-02 — One-shot operations MUST use suspend functions.
```

```rule
id: ARCH-PC-REP-RETURN-03
statement: Repository MUST NOT return loading states or resource wrappers.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-REP-RETURN-03 — Repository MUST NOT return loading states or resource wrappers.
```

That is the ViewModel's responsibility.

```rule
id: ARCH-PC-REP-RETURN-04
statement: Return types are plain domain models only.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-REP-RETURN-04 — Return types are plain domain models only.
```

Never DTOs, entities, or provider types.

## SSOT enforcement

```rule
id: ARCH-PC-REP-SSOT-01
statement: When coordinating local and remote DataSources, the Repository MUST observe the local DataSource as the stream that consumers read.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-REP-SSOT-01 — When coordinating local and remote DataSources, the Repository MUST observe the local DataSource as the stream that consumers read.
```

Never observe the remote DataSource directly.

```rule
id: ARCH-PC-REP-SSOT-02
statement: After a successful remote fetch, the Repository MUST write the result to the local DataSource.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-REP-SSOT-02 — After a successful remote fetch, the Repository MUST write the result to the local DataSource.
```

The local DataSource then emits the update to all observers.

### Standard coordination pattern

```
Repository.observeData()
    1. Attempt remote fetch → write result to local DataSource
    2. Observe local DataSource (the SSOT)
    3. Emit from local to caller
```

Remote failure during step 1 does not prevent step 2 from emitting cached data.

## Error handling

```rule
id: ARCH-PC-REP-FALLBACK-01
statement: When implementing fallback strategies, the Repository MUST rethrow domain exceptions after fallback logic is exhausted.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-REP-FALLBACK-01 — When implementing fallback strategies, the Repository MUST rethrow domain exceptions after fallback logic is exhausted.
```

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
