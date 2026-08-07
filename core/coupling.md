---
id: CORE-COUPLING
type: principle
layer: core
platform: [all]
architecture: [all]
requires: []
related: [CORE-DI, CORE-NAMING]
tags: [coupling, cohesion, separation-of-concerns, single-responsibility]
status: active
---

# Low Coupling / High Cohesion

## Statement

Components should know as little as possible about each other, and each should
do exactly one thing.

## Rationale

**Low coupling:** when components are tightly coupled, a change in one forces
changes in others. The blast radius of any change is proportional to the degree
of coupling. Loosely coupled components can be changed, replaced, and tested
independently.

**High cohesion:** a component that does many unrelated things is hard to reason
about, hard to test in isolation, and hard to change without side effects. A
single-purpose component has one reason to change.

## In Practice

- A component's public interface is as small as possible — expose only what callers
  need
- Each component has a single, clearly stated responsibility
- Dependencies point inward; infrastructure details never leak into business logic
- Pass only what a component needs — not a large object it partially uses
- A change in one layer should not require changes in a non-adjacent layer

## Violations

- A ViewModel that makes network calls or references database classes directly
- A function that accepts an entire object when it only uses one field
- A class with methods that span multiple unrelated concerns (networking, formatting,
  persistence)
- A change in a database schema requiring changes in a UI component
