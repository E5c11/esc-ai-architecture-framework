---
id: CORE-SSOT
type: principle
layer: core
platform: [all]
architecture: [all]
requires: []
related: [PAT-DATA-ACCESS, PAT-OBSERVER]
tags: [ssot, single-source-of-truth, consistency, state, synchronisation]
---

# Single Source of Truth

## Statement

Any piece of mutable state has exactly one authoritative owner. All reads flow
through that owner. All writes target that owner.

## Rationale

When the same data exists in multiple locations without explicit synchronisation,
reads from different locations diverge over time. The longer the system runs, the
less consistent it becomes. Debugging divergence is difficult because both sources
can appear correct in isolation.

## In Practice

- Identify the authoritative owner for each piece of data before writing any code
  that reads or writes it
- Derived representations (caches, projections, UI state) are computed from the owner
  and invalidated when the owner changes — they are never updated directly
- Write operations target the owner; derived representations update in response
- When coordinating multiple data providers, designate one as the truth and treat
  all others as update sources that feed into it

## Violations

- Two in-memory caches of the same remote data updated independently
- UI state mutated directly without going through the designated state owner
- A local database and a remote API treated as equal sources of truth with no
  explicit merge or precedence strategy
- Reading from a cache after a write without invalidating or updating the cache
