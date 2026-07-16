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

```rule
id: PLAT-MOB-KOIN-MOD-01
statement: Each feature MUST have a dedicated module function in a `di/` package inside its feature directory.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KOIN-MOD-01 — Each feature MUST have a dedicated module function in a `di/` package inside its feature directory.
```

```rule
id: PLAT-MOB-KOIN-MOD-02
statement: Module functions MUST use lowercase with a `Module` suffix: `fun profileModule()`, `fun bookingModule()`.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KOIN-MOD-02 — Module functions MUST use lowercase with a `Module` suffix: `fun profileModule()`, `fun bookingModule()`.
```

```rule
id: PLAT-MOB-KOIN-MOD-03
statement: All modules MUST be registered in `initKoin()` in this order: core modules → feature modules → platform module last.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KOIN-MOD-03 — All modules MUST be registered in `initKoin()` in this order: core modules → feature modules → platform module last.
```

## Preferred shorthand syntax

Use the `Of` shorthands when a class has only injectable constructor parameters.

| Verbose | Preferred |
|---|---|
| `factory { MyClass(get(), get()) }` | `factoryOf(::MyClass)` |
| `viewModel { MyViewModel(get()) }` | `viewModelOf(::MyViewModel)` |

```rule
id: PLAT-MOB-KOIN-SYN-01
statement: Use `factoryOf()` and `viewModelOf()` for classes whose entire constructor is injectable.
type: soft
scope: di
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KOIN-SYN-01 — Use `factoryOf()` and `viewModelOf()` for classes whose entire constructor is injectable.
```

Fall back to the block form only when custom logic is required inside the block.

## Singleton resources

Heavy or stateful resources are declared `single{}` so they are created once and shared.

```rule
id: PLAT-MOB-KOIN-SINGLE-01
statement: Room DAOs MUST be declared as `single`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KOIN-SINGLE-01 — Room DAOs MUST be declared as `single`.
```

```rule
id: PLAT-MOB-KOIN-SINGLE-02
statement: `DataStore<Preferences>` instances MUST be declared as `single`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KOIN-SINGLE-02 — `DataStore<Preferences>` instances MUST be declared as `single`.
```

```rule
id: PLAT-MOB-KOIN-SINGLE-03
statement: Firebase SDK instances MUST be declared as `single`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KOIN-SINGLE-03 — Firebase SDK instances MUST be declared as `single`.
```

Firebase objects are expensive to construct and are designed to be shared.

## Named qualifiers

When multiple implementations of the same interface are registered, named qualifiers
distinguish them.

```rule
id: PLAT-MOB-KOIN-QUAL-01
statement: Named qualifiers MUST use constants from a shared `DIQualifiers` object.
type: hard
scope: naming
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KOIN-QUAL-01 — Named qualifiers MUST use constants from a shared `DIQualifiers` object.
```

Never use string literals as qualifier values.

```rule
id: PLAT-MOB-KOIN-QUAL-02
statement: All qualifier constants MUST be defined in the `DIQualifiers` object and MUST use `UPPER_SNAKE_CASE`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KOIN-QUAL-02 — All qualifier constants MUST be defined in the `DIQualifiers` object and MUST use `UPPER_SNAKE_CASE`.
```

```rule
id: PLAT-MOB-KOIN-QUAL-03
statement: Any two registrations of the same raw type MUST use named qualifiers — including generic types where type parameters are erased at the JVM level (e.g.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KOIN-QUAL-03 — Any two registrations of the same raw type MUST use named qualifiers — including generic types where type parameters are erased at the JVM level (e.g.
```

`UseCase<A>` and `UseCase<B>` are both `UseCase` at runtime). Without qualifiers, the last-registered wins and causes a `ClassCastException` at the injection site, not a compile error.

## Injection

```rule
id: PLAT-MOB-KOIN-INJ-01
statement: Use `get()` and `get(named(...))` to resolve dependencies inside module blocks.
type: hard
scope: naming
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KOIN-INJ-01 — Use `get()` and `get(named(...))` to resolve dependencies inside module blocks.
```

Never construct dependencies directly with `::` or `new`.

## Module organisation

```rule
id: PLAT-MOB-KOIN-ORG-01
statement: Module blocks SHOULD be organised by scope with section comments: ViewModels, UseCases, Repositories, DataSources, etc.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KOIN-ORG-01 — Module blocks SHOULD be organised by scope with section comments: ViewModels, UseCases, Repositories, DataSources, etc.
```

```rule
id: PLAT-MOB-KOIN-ORG-02
statement: Features SHOULD depend on core modules, not on other feature modules.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KOIN-ORG-02 — Features SHOULD depend on core modules, not on other feature modules.
```

Cross-feature dependencies signal a missing shared abstraction in core.

```rule
id: PLAT-MOB-KOIN-ORG-03
statement: Circular module dependencies MUST NOT exist.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KOIN-ORG-03 — Circular module dependencies MUST NOT exist.
```

## New feature module setup

> **TODO:** This section is a stub. See `workflows/missing-files.md` for context.
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
