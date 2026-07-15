---
id: PLAT-MOB-KOIN
type: platform
layer: platform
platform: [mobile]
architecture: [all]
requires: [CORE-DI, PLAT-MOB-KMP]
related: [PLAT-MOB-KOTLIN, PLAT-MOB-KMP-IOS]
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

Declare bindings in dependency order and use architecture-appropriate lifetimes:

```kotlin
fun profileModule() = module {
    single<ProfileLocalDataSource> { DefaultProfileLocalDataSource(get()) }
    factory<ProfileRemoteDataSource> { DefaultProfileRemoteDataSource(get()) }
    factory<ProfileRepository> { DefaultProfileRepository(get(), get()) }
    factoryOf(::ObserveProfileUseCase)
    factoryOf(::UpdateProfileUseCase)
    viewModelOf(::ProfileViewModel)
}
```

Use `single` for expensive/stateful resources and platform SDK clients, `factory` for
stateless DataSources/repositories/UseCases unless architecture state requires otherwise,
and `viewModelOf` for ViewModels. Register the feature module once in the shared module list.

Conditional capabilities should bind one explicit implementation selected from build/runtime
configuration. If unsupported, bind an explicit unsupported result and hide/disable its UI.

**Rule PLAT-MOB-KOIN-FEAT-01 (hard):** Every constructor dependency in a feature graph
MUST resolve in a dedicated module-resolution test for every supported platform module.

**Rule PLAT-MOB-KOIN-COND-01 (hard):** Conditional DI MUST select exactly one binding
per interface and expose unsupported capability explicitly.

## iOS bootstrap

Keep the shared module list in common code and supply one platform module from the iOS entry
point. The platform module is registered last so intentional platform implementations can
replace portable defaults without duplicating feature modules.

**Rule PLAT-MOB-KOIN-IOS-01 (hard):** iOS MUST initialize Koin exactly once before the
root Compose controller renders content.

**Rule PLAT-MOB-KOIN-IOS-02 (hard):** The iOS platform module MUST bind every interface
used by common code whose implementation is platform-specific. Validate the graph at startup
or in a dedicated resolution test.

```kotlin
fun initKoin(platformModule: Module): KoinApplication = startKoin {
    modules(commonModules + platformModule)
}
```

Do not put UIKit/Foundation objects in common modules. Controller recreation should reuse
the initialized graph rather than catch and ignore duplicate-start exceptions.

## Violations

- Feature with no dedicated `di/` module
- Module function named `provideProfileDependencies` instead of `profileModule`
- Named qualifier using `named("local_datasource")` string literal
- `UseCase<TypeA>` and `UseCase<TypeB>` registered without named qualifiers
- Firebase instance declared as `factory` (reconstructed on every injection)
- Feature module registered before a core module it depends on
- iOS controller composing before Koin initialization
