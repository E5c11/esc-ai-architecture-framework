---
id: ARCH-PC-DI
type: guide
layer: architecture
platform: [mobile]
architecture: [pragmatic-clean]
requires: [ARCH-PC, PLAT-MOB-KOIN, CORE-DI]
related: [ARCH-PC-DATASOURCE, ARCH-PC-USECASE, ARCH-PC-VIEWMODEL]
tags: [di, dependency-injection, koin, scope, factory, single, viewmodel, modules]
---

# Dependency Injection — Scope Rules

## Overview

Scope assignment is an architectural decision, not a Koin configuration detail.
The correct scope for each component follows from its lifecycle requirements.
Koin syntax for declaring scopes is in `PLAT-MOB-KOIN`.

## Scope per layer

| Layer | Scope | Rationale |
|---|---|---|
| ViewModel | ViewModel (composition-scoped) | Tied to screen lifecycle; cleared when screen leaves composition |
| UseCase | Factory (new per injection) | Stateless; no shared state needed |
| Orchestrator | Factory | Stateless; coordinates UseCases |
| Repository | Factory | Stateless; coordinates DataSources |
| DataSource | Factory | Stateless; wraps a provider |
| DAO | Singleton | Room best practice; single instance for database access |
| Database | Singleton | Expensive to construct; must be shared |
| SDK instances (Firebase, etc.) | Singleton | Expensive to construct; designed to be shared |
| DataStore / KeyValueStorage | Singleton | Requires single instance for correct state management |

**Rule ARCH-PC-DI-SCOPE-01 (hard):** ViewModels MUST use the composition-scoped
binding (`viewModel` scope in Koin). Not `factory`, not `single`.

**Rule ARCH-PC-DI-SCOPE-02 (hard):** UseCases, Orchestrators, Repositories, and
DataSources MUST use factory scope. They are stateless and must not be shared
across injection sites.

**Rule ARCH-PC-DI-SCOPE-03 (hard):** DAOs, Database instances, SDK instances,
and DataStore instances MUST use singleton scope. They are expensive to construct
or require a single shared instance for correctness.

**Rule ARCH-PC-DI-SCOPE-04 (hard):** Never use a higher scope than the component
requires. Injecting a singleton where a factory is correct creates hidden shared
mutable state.

## Module structure

Each feature owns exactly one DI module. Core infrastructure has its own modules.

**Rule ARCH-PC-DI-MODULE-01 (hard):** Every feature MUST have a dedicated module
function in a `di/` package within the feature directory.

**Rule ARCH-PC-DI-MODULE-02 (hard):** Module registration order in `initKoin()`
MUST be: core modules first → feature modules → platform module last.
Dependencies must be registered before they are resolved.

**Rule ARCH-PC-DI-MODULE-03 (hard):** Features MUST NOT depend on other feature
modules. Cross-feature dependencies signal a missing shared abstraction in core.

**Rule ARCH-PC-DI-MODULE-04 (hard):** Circular module dependencies MUST NOT exist.

## Named qualifiers for multiple implementations

When a Repository takes both a local and a remote DataSource of the same interface,
named qualifiers distinguish them at injection.

**Rule ARCH-PC-DI-QUAL-01 (hard):** Any two registrations of the same raw type
MUST use named qualifiers. This includes generic types where type parameters are
erased at runtime — two `UseCase<A>` and `UseCase<B>` are the same raw type and
will collide without qualifiers.

**Rule ARCH-PC-DI-QUAL-02 (hard):** Qualifier values MUST be defined as named
constants, never as inline string literals. See `PLAT-MOB-KOIN` for the constant
naming convention.

## Registering UseCases

**Rule ARCH-PC-DI-UC-01 (hard):** UseCases MUST be registered under their
interface type, not their concrete type. The ViewModel injects by interface;
if the factory is registered under the concrete type, Koin cannot resolve it.

## Violations

- UseCase declared as `single` (it is stateless; `factory` is correct)
- Firebase instance declared as `factory` (reconstructed on every injection)
- Feature module registered before the core modules it depends on
- Multiple `UseCase<T>` registrations without named qualifiers causing a collision
- Named qualifier using a string literal instead of a constant
- UseCase registered under its concrete class instead of its interface
