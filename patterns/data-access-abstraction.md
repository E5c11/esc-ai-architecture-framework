---
id: PAT-DATA-ACCESS
type: pattern
layer: pattern
platform: [all]
architecture: [all]
requires: [CORE-DI]
related: [CORE-SSOT, PAT-OUTCOME, PAT-OBSERVER]
tags: [data-access, abstraction, repository, datasource, interface, storage]
---

# Data-Access Abstraction

## Statement

Data access is hidden behind an interface that expresses domain operations.
Consumers never reference storage technologies directly.

## Rationale

When a component references a concrete storage technology — a SQL table, a
Firestore collection, an HTTP endpoint — it is coupled to that technology's
API, error types, and existence. Replacing or testing the storage requires
changing every consumer. An interface that speaks the domain language decouples
the consumer from the storage entirely.

## Naming across ecosystems

This pattern appears under different names in different ecosystems. The concept
is the same; the name varies:

| Ecosystem | Name used | Maps to |
|-----------|-----------|---------|
| This framework | **DataSource** | This pattern |
| Spring / JPA | **Repository** (`JpaRepository`, `CrudRepository`) | This pattern |
| Android Architecture Components | **DataSource** or **Repository** | This pattern |
| DDD | **Repository** | This pattern |

When reading platform-specific code, map the ecosystem's name back to this
pattern. Architecture documents clarify the exact term used in each context.

## Structure

- An **interface** declares domain operations using domain language
- An **implementation** wraps exactly one storage provider and translates
  between provider types and domain types
- **One implementation per provider** — an abstraction over a database and an
  abstraction over a REST API are two separate interfaces, not one

## In Practice

- Interface methods express domain intent: `findUserById(id)`, `saveOrder(order)`,
  `streamActiveBookings()` — never SQL, collection paths, or HTTP verbs
- Return types are domain types: never entities, DTOs, `DocumentSnapshot`,
  `Cursor`, or any other storage-specific type
- Errors thrown by the interface are domain errors, not storage errors
  (`UserNotFoundException` not `SQLException`)
- The interface lives in the domain layer; the implementation lives in the
  infrastructure layer

## Violations

- A business logic component that imports a storage class directly
- An interface method that returns a `DocumentSnapshot`, `ResultSet`, or ORM entity
- One abstraction that combines a database and a remote API (two providers = two abstractions)
- An interface method named after its SQL query: `selectUserWhereEmailEquals(email)`
