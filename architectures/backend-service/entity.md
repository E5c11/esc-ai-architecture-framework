---
id: ARCH-BE-ENTITY
type: rules
layer: architectures
platform: [backend]
architecture: backend-service
requires: [ARCH-BE, CORE-NAMING]
related: [ARCH-BE-DATASOURCE, PLAT-BE-JPA]
tags: [entity, jpa, schema, migration, flyway, database]
---

# Entity Layer

## What it is

An entity is a JPA-mapped class that represents one table in the database. It is
a schema object — its fields mirror table columns. It contains no business logic.

## Rules

**Rule ENT-MIGRATION-01 (hard):** Every entity change MUST be paired with a database
migration in the same commit. JPA is configured to validate the schema on startup
(`ddl-auto: validate`). An entity that does not match the actual schema causes a
startup failure. Writing the migration first, then updating the entity, keeps the
repo deployable at every commit.

> Violation: Adding a field to an entity without a corresponding migration SQL file.
> Fix: Write the migration SQL first, then update the entity to match.

**Rule ENT-ID-01 (hard):** Entities MUST use a UUID primary key. The UUID MUST be
generated at the database level (`gen_random_uuid()` SQL default) or via JPA
`GenerationType.UUID`. Avoid sequential integer PKs — they are enumerable in
URLs and unsafe to expose.

**Rule ENT-TIMESTAMP-01 (hard):** Every entity MUST have `createdAt` and `updatedAt`
timestamp columns. `createdAt` MUST be immutable (`updatable = false`). Both columns
have `NOT NULL DEFAULT now()` in the migration. Audit timestamps are required
for debugging and analytics.

**Rule ENT-EQUALS-01 (hard):** Entity `equals` and `hashCode` MUST compare the
primary key only. Hibernate uses proxy objects; equality based on all fields breaks
`Set` semantics and dirty checking. Do NOT use a `data class` for entities —
Kotlin data classes generate all-field `equals`/`hashCode` and `componentN` /
`copy` methods, all of which break Hibernate's proxy mechanism.

**Rule ENT-LOGIC-01 (hard):** Entities MUST NOT contain business logic. Methods that
compute domain state (`isExpired()`, `applyDiscount()`, etc.) belong in the service.
An entity class declares fields and implements `equals`/`hashCode` — nothing more.

**Rule ENT-OPEN-01 (hard):** Entity classes MUST be open (non-final). Hibernate
requires non-final classes to create proxies. The `allOpen` Gradle plugin opens
classes annotated with `@Entity`, `@MappedSuperclass`, and `@Embeddable` at compile
time. Do not mark entity classes as `final` and do not use `data class`.

**Rule ENT-NAMING-01 (soft):** Entity class: `{Domain}Entity`. Table name:
plural snake_case (`users`, `refresh_tokens`, `subjects`).

> Violation: `@Entity class User`, `@Table(name = "User")`
> Fix: `@Entity @Table(name = "users") class UserEntity`

## Relationship fetching

**Rule ENT-FETCH-01 (hard):** `@ManyToOne` and `@OneToOne` associations MUST
declare `FetchType.LAZY`. Eager fetching silently generates N+1 queries and causes
unpredictable performance at scale. Load associations explicitly in the service
when they are needed.

## Migration-first workflow

1. Write the migration SQL (`db/migration/V{next}__<description>.sql`)
2. Write or update the entity class to match the migration exactly
3. Commit both files in the same commit

Never rely on `ddl-auto: create-drop` to generate the schema — production uses
`validate`, so any gap between the entity and the migration causes a startup failure.

## Timestamp column SQL pattern

```sql
created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
```

Always `TIMESTAMPTZ` (timezone-aware), always `NOT NULL`, always `DEFAULT now()`.
