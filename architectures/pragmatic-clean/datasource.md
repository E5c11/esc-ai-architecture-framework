---
id: ARCH-PC-DATASOURCE
type: guide
layer: architecture
platform: [mobile]
architecture: [pragmatic-clean]
requires: [ARCH-PC, PAT-DATA-ACCESS, PLAT-MOB-KOTLIN]
related: [ARCH-PC-REPOSITORY, ARCH-PC-ERROR-FLOW, ARCH-PC-DI]
tags: [datasource, provider, mapping, exceptions, abstraction]
status: active
---

# DataSource Layer

## Responsibility

Abstract exactly one data provider. Translate provider-specific types into domain
models. Translate provider-specific exceptions into domain exceptions.

That is all. No business logic. No coordination of multiple providers.

## Structure

Every DataSource is an interface + implementation pair. Per `ARCH-PC`'s feature
module structure, interfaces and non-platform-specific implementations live in
`io/`; platform-specific `Local{Feature}DataSource` implementations live in
`io/local/` (in the relevant platform source set, e.g. `androidMain`/`iosMain`
when they need Context or a platform SDK); remote sync/DataSource
implementations live in `io/remote/`.

```
io/
├── {Feature}DataSource.kt            Interface (in commonMain)
├── local/
│   └── Local{Feature}DataSource.kt   Wraps DAO / local storage
└── remote/
    └── Remote{Feature}DataSource.kt  Wraps API / remote SDK
```

```rule
id: ARCH-PC-DS-INTERFACE-01
statement: Every DataSource MUST define an interface.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-DS-INTERFACE-01 — Every DataSource MUST define an interface.
```

The interface lives in `commonMain`; implementations live in the appropriate source set.

```rule
id: ARCH-PC-DS-RESPONSIBILITY-01
statement: A DataSource MUST contain only type mapping and exception translation.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-DS-RESPONSIBILITY-01 — A DataSource MUST contain only type mapping and exception translation.
```

Business logic belongs in UseCases.

## Return types

```rule
id: ARCH-PC-DS-RETURN-01
statement: Data that is persisted locally and can be updated by background sync MUST be returned as a stream (`Flow<T>`).
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-DS-RETURN-01 — Data that is persisted locally and can be updated by background sync MUST be returned as a stream (`Flow<T>`).
```

```rule
id: ARCH-PC-DS-RETURN-02
statement: One-shot operations (fetch once, write, delete) MUST use suspend functions.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-DS-RETURN-02 — One-shot operations (fetch once, write, delete) MUST use suspend functions.
```

```rule
id: ARCH-PC-DS-RETURN-03
statement: Do NOT wrap a suspend call in a stream just to return a stream.
type: hard
scope: testing
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-DS-RETURN-03 — Do NOT wrap a suspend call in a stream just to return a stream.
```

A `flow { emit(suspendCall()) }` is a fake stream. If the provider is suspend, the DataSource is suspend.

```rule
id: ARCH-PC-DS-RETURN-04
statement: Respect the provider's own contract.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-DS-RETURN-04 — Respect the provider's own contract.
```

If the DAO returns a `Flow`, the DataSource returns a `Flow`. If the API returns suspend, the DataSource returns suspend. Never collapse or inflate the contract.

## Type mapping

```rule
id: ARCH-PC-DS-MAPPING-01
statement: DataSource methods MUST return domain types (`data/`, this feature's shared domain models — see `ARCH-PC`).
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-DS-MAPPING-01 — DataSource methods MUST return domain types (`data/`).
```

Never return DTOs, entities, or any provider-specific type.

```rule
id: ARCH-PC-DS-MAPPING-02
statement: Mapping functions live alongside the DataSource implementation that owns them (`io/`, `io/local/`, or `io/remote/`) — either as private functions/extension functions in the same file, or a dedicated mapper file in the same directory for a large mapping surface.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-DS-MAPPING-02 — Mapping functions live alongside the DataSource implementation that owns them.
```

DataSource implementations call mappers; they do not inline large ad-hoc
mapping logic directly in a business method.

```rule
id: ARCH-PC-DS-EMPTY-01
statement: "Not found" is a valid, expected outcome for a single-row lookup and MUST be represented as a nullable return (`T?`), not a thrown exception.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-DS-EMPTY-01 — "Not found" MUST be represented as a nullable return (`T?`), not a thrown exception.
```

This repository's established, consistently-applied convention across every
per-resource DataSource (`getIdentity(): UserIdentity?`, `getProfile():
UserProfile?`, `getEducation(): UserEducation?`, and so on) is nullable
return, not throw-on-empty — callers decide at the UseCase/Repository layer
whether an absent row is a real failure (throw a domain exception there) or
an expected state (self-heal, fall back, or compose from another source).
Throwing at the DataSource layer forecloses that decision for every caller,
including ones for whom "not found yet" is completely normal (a fresh
account before its first sync, an optional field). Reserve thrown domain
exceptions in a DataSource for genuine operation failures — the query itself
erroring, not simply returning zero rows.

## Exception handling

Provider exceptions (database errors, network errors, SDK errors) are an
implementation detail of the provider. They must not cross the DataSource boundary.

```rule
id: ARCH-PC-DS-EXCEPTION-01
statement: All provider exceptions MUST be caught in the DataSource and translated into domain exceptions before propagating.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-DS-EXCEPTION-01 — All provider exceptions MUST be caught in the DataSource and translated into domain exceptions before propagating.
```

```rule
id: ARCH-PC-DS-EXCEPTION-02
statement: Domain exceptions (exceptions that already carry UI metadata) MUST be rethrown unchanged.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-DS-EXCEPTION-02 — Domain exceptions (exceptions that already carry UI metadata) MUST be rethrown unchanged.
```

Do not re-wrap them.

```rule
id: ARCH-PC-DS-CANCEL-01
statement: Coroutine cancellation exceptions MUST be rethrown before any general `catch` block.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-DS-CANCEL-01 — Coroutine cancellation exceptions MUST be rethrown before any general `catch` block.
```

Never swallow cancellation.

### Exception catch order

```
catch (e: CancellationException) { throw e }     // Always first
catch (e: DomainException)       { throw e }     // Pass through unchanged
catch (e: ProviderException)     { throw translate(e) }  // Translate
catch (e: Exception)             { throw translateUnknown(e) }
```

## Naming

```rule
id: ARCH-PC-DS-NAMING-01
statement: DataSource interface is named `{Feature}DataSource`.
type: hard
scope: naming
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-DS-NAMING-01 — DataSource interface is named `{Feature}DataSource`.
```

```rule
id: ARCH-PC-DS-NAMING-02
statement: Implementations are named `Local{Feature}DataSource` or `Remote{Feature}DataSource`.
type: hard
scope: naming
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-DS-NAMING-02 — Implementations are named `Local{Feature}DataSource` or `Remote{Feature}DataSource`.
```

Source type prefix comes first.

## DI scope

DataSources are `factory` scoped — a new instance per injection point.
See `ARCH-PC-DI` for scope rules.

## Violations

- Business logic (if/when decisions about data) inside a DataSource
- Provider type (`Entity`, `DocumentSnapshot`) returned from a DataSource method
- Provider exception propagating above the DataSource
- `flow { emit(dao.getData()) }` wrapping a one-shot DAO call
- Domain exception re-wrapped instead of rethrown
- A thrown domain exception for a simple not-found row instead of a nullable return
