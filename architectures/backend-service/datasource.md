---
id: ARCH-BE-DATASOURCE
type: rules
layer: architectures
platform: [backend]
architecture: backend-service
requires: [ARCH-BE, PAT-DATA-ACCESS, CORE-DI]
related: [ARCH-BE-SERVICE, ARCH-BE-ENTITY, PLAT-BE-JPA]
tags: [datasource, repository, jpa, data-access, store]
---

# DataSource Layer

## What it is

The DataSource layer is the persistence boundary between the service layer and
the database. It translates service-level operations into database operations
and returns JPA entities or primitives to the service.

In the Backend-Service architecture, there is exactly one data source (the
relational database). Therefore, no coordination layer (Repository) is needed.
Only a DataSource is needed — see `PAT-DATA-ACCESS` for the full distinction.

## Two implementation forms

**Form A — JpaRepository directly (default)**

A Spring Data `JpaRepository` extension is a DataSource in framework terms.
It is the correct choice whenever the service needs one or a few derived queries
or simple `@Query` annotations.

```
interface {Domain}Repository : JpaRepository<{Domain}Entity, UUID>
```

Derived queries and `@Query` annotations are added directly to this interface.

**Form B — Custom Store wrapper (justified exception)**

A hand-written wrapper class (`{Domain}Store`) is warranted only when:
- A single logical result requires 3 or more separate JPA repository calls
- The operation must combine data from multiple repositories
- A native or complex JPQL query is complex enough to benefit from isolation

The wrapper is still a DataSource — it translates; it does not coordinate multiple
data sources.

## Rules

**Rule REP-WHEN-01 (hard):** A `{Domain}Store` wrapper MUST only be created when
one of the three justifying conditions above is met. Creating a wrapper to rename
`findById` or wrap a single derived query adds indirection with no benefit.

**Rule REP-INTERFACE-01 (hard):** If a custom Store wrapper is created, it MUST
define an interface. The interface is required so service unit tests can mock the
dependency with Mockk.

> Violation: `@Repository class UserStore` with no interface, injected by concrete type.
> Fix: define `interface UserStore` and implement it in `UserStoreImpl`.

**Rule REP-TX-01 (hard):** `@Transactional` MUST NOT be placed on DataSource or
repository methods. Transaction scope is defined at the service layer.

**Rule REP-RETURN-01 (hard):** DataSource methods MUST return JPA entities or
primitives — never DTOs or HTTP-specific types. The DataSource is a persistence
boundary; it must not know about HTTP contracts.

> Violation: `fun getUser(): UserResponse`
> Fix: `fun getUser(): UserEntity` — the service maps it to a DTO.

**Rule REP-NAMING-01 (soft):** Spring Data interfaces: `{Domain}Repository`.
Custom wrappers: `{Domain}Store` (interface) / `{Domain}StoreImpl` (implementation).
Avoid names like `UserDao`, `UserManager`, `UserJpaRepository`.

## Decision tree

```
New data access needed
    │
    ├─ Only derived queries (findBy*, existsBy*, etc.)?
    │  └─ Add to JpaRepository extension. No wrapper.
    │
    ├─ Single @Query annotation (JPQL or native)?
    │  └─ Add to JpaRepository extension. No wrapper.
    │
    ├─ Operation needs 3+ separate JPA calls for one logical result?
    │  └─ YES → Justify a Store wrapper.
    │
    ├─ Operation must combine multiple repositories?
    │  └─ YES → Justify a Store wrapper.
    │
    └─ Complex native query benefiting from isolation?
       └─ YES → Justify a Store wrapper.
```

## Testing

DataSource integration tests verify custom `@Query` and native query correctness
against a real database. Use `@DataJpaTest` (Spring slice test) with an in-memory
or Testcontainers PostgreSQL database. Derived queries (`findBy*`) are provided
by Spring Data and do not require tests.
