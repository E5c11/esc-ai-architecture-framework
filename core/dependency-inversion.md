---
id: CORE-DI
type: principle
layer: core
platform: [all]
architecture: [all]
requires: []
related: [CORE-COUPLING, PAT-DATA-ACCESS]
tags: [dependency-inversion, abstraction, interfaces, testability, composition]
---

# Dependency Inversion

## Statement

High-level modules must not depend on low-level modules. Both must depend on abstractions.

## Rationale

When a component depends on a concrete implementation, it is coupled to that
implementation's existence, behaviour, and change history. Replacing or testing
the component requires either running the real implementation or rewriting the code.
Abstractions break this coupling — the component declares what it needs, and the
wiring layer decides what provides it.

## In Practice

- Every component declares its dependencies as interfaces or abstract types, never
  as concrete classes
- Concrete implementations are wired at composition time (DI container or manual
  constructor wiring), never instantiated inside the component that uses them
- The component that owns an interface does not know which implementation it will receive
- Dependencies point inward toward abstract core types; they never point outward
  toward concrete infrastructure

## Violations

- `val service = ConcreteService()` inside a class that uses the service
- A business logic component importing and constructing a database class directly
- A ViewModel that creates its own UseCase with `new` / constructor call
- A function that accepts a concrete class when it only uses a subset of its interface
