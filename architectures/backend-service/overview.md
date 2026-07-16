---
id: ARCH-BE
type: overview
layer: architectures
platform: [backend]
architecture: backend-service
requires: [CORE-DI, CORE-ERROR, CORE-NAMING, CORE-COUPLING, PAT-DATA-ACCESS]
related: [ARCH-BE-CONTROLLER, ARCH-BE-SERVICE, ARCH-BE-DATASOURCE, ARCH-BE-ENTITY, ARCH-BE-ERROR, ARCH-BE-PAGINATION, ARCH-BE-PUBLISHING, PLAT-BE-SPRING, PLAT-BE-JPA]
tags: [backend, spring-boot, architecture, layers, rest-api]
---

# Backend-Service Architecture

## What it is

Backend-Service is a layered REST API architecture for server-side services
with a relational database. Each request travels inward through fixed layers;
responses travel back outward. No layer skips or bypasses another.

## Layer structure

```
HTTP Request
    ↓
Controller     — HTTP boundary only; translates request → service call
    ↓
Service        — all business logic; transaction owner; returns DTOs
    ↓
DataSource     — persistence boundary; JpaRepository or thin Store wrapper
    ↓
Entity         — JPA-mapped schema object; no business logic
    ↓
Database
```

### Layer contracts

| Layer | Receives | Returns | Must NOT |
|---|---|---|---|
| Controller | HTTP request | HTTP response (DTO) | Contain logic; return entities |
| Service | DTOs / primitives | DTOs / primitives | Return entities; know about HTTP |
| DataSource | Domain parameters | Entities / primitives | Return DTOs; own transactions |
| Entity | — | — | Contain business logic |

## Data-access naming

The data-access layer in this architecture is called **DataSource**, consistent with
`PAT-DATA-ACCESS`. Spring's `JpaRepository` interface is the primary DataSource.
A hand-written wrapper (`{Domain}Store`) is also a DataSource — it is NOT a Repository
in the Pragmatic Clean sense, because there is only one data source to coordinate.

See `PAT-DATA-ACCESS` for the full naming disambiguation across ecosystems.

## Dependency direction

Dependencies flow inward only: Controller → Service → DataSource → Entity.
Outer layers may depend on inner layers; inner layers must never depend on outer layers.

```rule
id: ARCH-BE-DEP-01
statement: A DataSource or Entity class MUST NOT import from the service or controller package.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-BE-DEP-01 — A DataSource or Entity class MUST NOT import from the service or controller package.
```

The entity does not know about DTOs, HTTP status codes, or service concerns.

```rule
id: ARCH-BE-DEP-02
statement: A Service MUST NOT import `org.springframework.web.*` or `org.springframework.http.*`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-BE-DEP-02 — A Service MUST NOT import `org.springframework.web.*` or `org.springframework.http.*`.
```

Services must not know they are called over HTTP.

## Module structure

Backend services are organised into domain modules. Each domain module is
self-contained and owns its slice of the layer stack: entity, DataSource, service, controller, DTOs.

```
:core:api        — API version prefix + domain path constants (no Spring deps)
:core:datetime   — TimeProvider abstraction for testable time
:{domain}        — entity, DataSource, service, controller, DTOs
```

```rule
id: ARCH-BE-MOD-01
statement: Domain modules MUST depend on `:core:*` modules only.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-BE-MOD-01 — Domain modules MUST depend on `:core:*` modules only.
```

Domain modules MUST NOT depend on other domain modules.

```rule
id: ARCH-BE-MOD-02
statement: API path constants (version prefix, domain paths) MUST live in `:core:api`, not inline in controller annotations.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-BE-MOD-02 — API path constants (version prefix, domain paths) MUST live in `:core:api`, not inline in controller annotations.
```

See `PLAT-BE-SPRING` for the path constants pattern.

## Execution order for a new feature

Always implement layers in persistence-to-boundary order:

1. Migration SQL
2. Entity
3. DataSource (JpaRepository + optional Store wrapper)
4. Request and response DTOs
5. Service
6. Controller
7. Tests

Never write a controller before the service exists, and never write a service
before the entity and DataSource exist. Dependencies flow inward; implementation
flows outward.

## Time abstraction

All time-dependent logic uses an injected `TimeProvider` abstraction rather than
calling `Instant.now()` or `System.currentTimeMillis()` directly. This makes
service logic deterministic in tests.

```rule
id: ARCH-BE-TIME-01
statement: Services MUST inject and use a `TimeProvider` for any operation that reads or produces a timestamp.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates ARCH-BE-TIME-01 — Services MUST inject and use a `TimeProvider` for any operation that reads or produces a timestamp.
```

Direct calls to `Instant.now()` or `System.currentTimeMillis()` inside a service method are a violation.

See `PLAT-BE-SPRING` for the `TimeProvider` bean declaration and injection pattern.

## What this architecture does NOT include

- WebSocket or streaming endpoints — this architecture targets synchronous REST
- Event-driven messaging — service-to-service calls are out of scope here
- CQRS — single read/write model via JPA
