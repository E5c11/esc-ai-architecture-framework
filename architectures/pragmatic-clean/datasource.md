---
id: ARCH-PC-DATASOURCE
type: guide
layer: architecture
platform: [mobile]
architecture: [pragmatic-clean]
requires: [ARCH-PC, PAT-DATA-ACCESS, PLAT-MOB-KOTLIN]
related: [ARCH-PC-REPOSITORY, ARCH-PC-ERROR-FLOW, ARCH-PC-DI]
tags: [datasource, provider, mapping, exceptions, abstraction]
---

# DataSource Layer

## Responsibility

Abstract exactly one data provider. Translate provider-specific types into domain
models. Translate provider-specific exceptions into domain exceptions.

That is all. No business logic. No coordination of multiple providers.

## Structure

Every DataSource is an interface + implementation pair.

```
data/sources/
├── {Feature}DataSource.kt           Interface (in commonMain)
├── Local{Feature}DataSource.kt      Wraps DAO / local storage
└── Remote{Feature}DataSource.kt     Wraps API / remote SDK
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
statement: DataSource methods MUST return domain types (`data/models/`).
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-DS-MAPPING-01 — DataSource methods MUST return domain types (`data/models/`).
```

Never return DTOs, entities, or any provider-specific type.

```rule
id: ARCH-PC-DS-MAPPING-02
statement: Mapping functions belong in `data/mappers/`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-DS-MAPPING-02 — Mapping functions belong in `data/mappers/`.
```

DataSource implementations call mappers; they do not contain inline mapping logic.

```rule
id: ARCH-PC-DS-EMPTY-01
statement: A null or empty result for data that is expected to exist MUST throw a domain exception.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-DS-EMPTY-01 — A null or empty result for data that is expected to exist MUST throw a domain exception.
```

Never return null to signal not-found.

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
- Null returned for a not-found case instead of a domain exception
