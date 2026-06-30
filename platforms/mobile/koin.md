---
id: PLAT-MOB-KOIN
type: platform
layer: platform
platform: [mobile]
architecture: [all]
requires: [CORE-DI, PLAT-MOB-KMP]
related: [PLAT-MOB-KOTLIN]
tags: [koin, dependency-injection, modules, qualifiers, scopes, factory, single]
---

# Koin — Dependency Injection Tooling

## Overview

Koin is the DI framework for KMP. It uses a Kotlin DSL to declare modules.
This document covers Koin-specific tooling conventions. Scope assignment rules
(which architecture layer uses which scope) are defined in the architecture document
for each architectural style.

## Module structure and naming

Each feature owns a dedicated module function in a `di/` package within the feature.

**Rule PLAT-MOB-KOIN-MOD-01 (hard):** Each feature MUST have a dedicated module
function in a `di/` package inside its feature directory.

**Rule PLAT-MOB-KOIN-MOD-02 (hard):** Module functions MUST use lowercase with
a `Module` suffix: `fun profileModule()`, `fun bookingModule()`.

**Rule PLAT-MOB-KOIN-MOD-03 (hard):** All modules MUST be registered in `initKoin()`
in this order: core modules → feature modules → platform module last.

## Preferred shorthand syntax

Use the `Of` shorthands when a class has only injectable constructor parameters.

| Verbose | Preferred |
|---|---|
| `factory { MyClass(get(), get()) }` | `factoryOf(::MyClass)` |
| `viewModel { MyViewModel(get()) }` | `viewModelOf(::MyViewModel)` |

**Rule PLAT-MOB-KOIN-SYN-01 (soft):** Use `factoryOf()` and `viewModelOf()` for
classes whose entire constructor is injectable. Fall back to the block form only
when custom logic is required inside the block.

## Singleton resources

Heavy or stateful resources are declared `single{}` so they are created once and shared.

**Rule PLAT-MOB-KOIN-SINGLE-01 (hard):** Room DAOs MUST be declared as `single`.
**Rule PLAT-MOB-KOIN-SINGLE-02 (hard):** `DataStore<Preferences>` instances MUST
be declared as `single`.
**Rule PLAT-MOB-KOIN-SINGLE-03 (hard):** Firebase SDK instances MUST be declared
as `single`. Firebase objects are expensive to construct and are designed to be shared.

## Named qualifiers

When multiple implementations of the same interface are registered, named qualifiers
distinguish them.

**Rule PLAT-MOB-KOIN-QUAL-01 (hard):** Named qualifiers MUST use constants from a
shared `DIQualifiers` object. Never use string literals as qualifier values.

**Rule PLAT-MOB-KOIN-QUAL-02 (hard):** All qualifier constants MUST be defined in
the `DIQualifiers` object and MUST use `UPPER_SNAKE_CASE`.

**Rule PLAT-MOB-KOIN-QUAL-03 (hard):** Any two registrations of the same raw type
MUST use named qualifiers — including generic types where type parameters are erased
at the JVM level (e.g. `UseCase<A>` and `UseCase<B>` are both `UseCase` at runtime).
Without qualifiers, the last-registered wins and causes a `ClassCastException` at
the injection site, not a compile error.

## Injection

**Rule PLAT-MOB-KOIN-INJ-01 (hard):** Use `get()` and `get(named(...))` to resolve
dependencies inside module blocks. Never construct dependencies directly with `::` or `new`.

## Module organisation

**Rule PLAT-MOB-KOIN-ORG-01 (soft):** Module blocks SHOULD be organised by scope
with section comments: ViewModels, UseCases, Repositories, DataSources, etc.

**Rule PLAT-MOB-KOIN-ORG-02 (hard):** Features SHOULD depend on core modules,
not on other feature modules. Cross-feature dependencies signal a missing shared
abstraction in core.

**Rule PLAT-MOB-KOIN-ORG-03 (hard):** Circular module dependencies MUST NOT exist.

## New feature module setup

> **TODO:** This section is a stub. See `todo/missing-files.md` for context.
>
> Needs a step-by-step walkthrough covering:
> - Which scopes to use for each layer (ViewModel → factory/viewModel, UseCase → factory, Repository → factory, DataSource → factory, DAOs → single)
> - The order in which to declare bindings inside the module block
> - How to register the module in `initKoin()`
> - How to handle optional / conditional registrations (e.g. feature-flagged DataSources)
> - A complete worked example of a feature module with all layers wired

## Violations

- Feature with no dedicated `di/` module
- Module function named `provideProfileDependencies` instead of `profileModule`
- Named qualifier using `named("local_datasource")` string literal
- `UseCase<TypeA>` and `UseCase<TypeB>` registered without named qualifiers
- Firebase instance declared as `factory` (reconstructed on every injection)
- Feature module registered before a core module it depends on
