---
id: PLAT-MOB-ROOM
type: platform
layer: platform
platform: [mobile]
architecture: [all]
requires: [PAT-DATA-ACCESS, PLAT-MOB-KOTLIN]
related: [PLAT-MOB-KOIN, PLAT-MOB-FIREBASE, PLAT-MOB-KMP-IOS]
tags: [room, sqlite, dao, entity, local-database, android, ios, kmp]
---

# Room — Local Database

## Overview

Room is the SQLite abstraction for Android/KMP. It generates DAO implementations
at compile time. A DAO is the data-access abstraction (`PAT-DATA-ACCESS`) at the
SQLite boundary — it maps SQL results to Kotlin types.

## Entities

An entity maps directly to a database table. It carries only persistence concerns —
no business logic, no computed properties that require other entities.

**Rule PLAT-MOB-ROOM-ENT-01 (hard):** Entity classes MUST be annotated with
`@Entity`. They are persistence types — they MUST NOT be used as domain models
or passed across architecture layer boundaries.

**Rule PLAT-MOB-ROOM-ENT-02 (hard):** Entity field names that differ from the
database column name MUST use `@ColumnInfo(name = "...")`. Never rely on implicit
name matching across schema migrations.

## DAOs

A DAO declares the operations the data layer exposes for one entity or one related
group of entities.

**Rule PLAT-MOB-ROOM-DAO-01 (hard):** DAO interfaces MUST be annotated with `@Dao`.

**Rule PLAT-MOB-ROOM-DAO-02 (hard):** Query methods that return live data MUST
return `Flow<T>` so callers observe updates. One-shot reads and writes MUST use
`suspend fun`.

**Rule PLAT-MOB-ROOM-DAO-03 (hard):** DAOs MUST return entity types or primitive
types — never domain models. Mapping from entity to domain is the DataSource's
responsibility.

**Rule PLAT-MOB-ROOM-DAO-04 (hard):** `@Transaction` MUST be applied to any
DAO method that performs multiple database operations that must succeed or fail
together.

## Database class

**Rule PLAT-MOB-ROOM-DB-01 (hard):** The `@Database` class MUST be declared as
a `single` in Koin (see `PLAT-MOB-KOIN`). Room databases are expensive to
construct and must not be re-created per injection.

**Rule PLAT-MOB-ROOM-DB-02 (hard):** Schema version MUST be incremented on every
migration. `fallbackToDestructiveMigration()` is only acceptable in development;
production builds MUST provide explicit `Migration` objects.

## KMP and iOS construction

Put portable entities, DAOs and the database declaration in a source set compiled by every
target that needs persistence. Configure Room's compiler/KSP task for each target rather than
only `kspAndroid`. Keep platform database-builder/path code in platform source sets.

**Rule PLAT-MOB-ROOM-KSP-01 (hard):** Every target compiling Room declarations MUST
run the compatible Room compiler/KSP configuration and generated sources must be available
to that target compilation.

**Rule PLAT-MOB-ROOM-IOS-01 (hard):** The iOS database path MUST live in an
application-owned persistent container and database construction MUST use the project's
supported Native SQLite driver.

**Rule PLAT-MOB-ROOM-SCHEMA-01 (hard):** All platforms share one schema version and
migration history. Platform-specific destructive fallback is not a migration strategy.

Do not move Android-only platform APIs into common code while moving Room declarations.
If only selected features are ported, their schema/DAO dependencies must still form a
complete database compilation unit.

## Native verification

Common DAO/DataSource tests verify contracts. Add simulator integration tests that open the
real database, migrate representative old schemas, observe Flow updates, close/reopen the
database and verify persistence. Use temporary paths and clean them after the test.

## DataSource responsibility

A DataSource wraps a DAO. It maps entity types to domain types and translates
Room-specific exceptions into domain exceptions.

**Rule PLAT-MOB-ROOM-DS-01 (hard):** DataSources MUST translate `SQLiteException`
and Room-specific errors into domain exceptions before propagating. Raw Room
exceptions MUST NOT cross the DataSource boundary.

## Violations

- An entity class used directly as a domain model in a ViewModel
- A DAO method returning a `Flow` for a write operation
- DAO constructing domain objects or calling domain logic
- Room database declared as `factory` scope in Koin
- Production code using `fallbackToDestructiveMigration()`
- Room declarations compiled for iOS without an iOS KSP/compiler configuration
- iOS database created in a cache/temporary directory for durable user data
