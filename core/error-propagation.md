---
id: CORE-ERROR
type: principle
layer: core
platform: [all]
architecture: [all]
requires: []
related: [PAT-OUTCOME, CORE-COUPLING]
tags: [error-handling, propagation, exceptions, boundaries, observability]
status: active
---

# Error Propagation

## Statement

Errors must propagate to the architectural boundary where they can be meaningfully
handled. They must never be silently swallowed.

## Rationale

Swallowing an error removes information from the system. The caller receives a
success signal when the operation failed, producing silent data corruption,
unexpected state, or behaviour that is nearly impossible to diagnose. Every
swallowed error is a future mystery bug.

## In Practice

- Catch errors only at boundaries where you can either recover with a meaningful
  fallback or translate the error into the domain's error vocabulary
- Map low-level technical errors (I/O, network, database) into domain error types
  at the layer boundary closest to where they originate — not deep inside business
  logic and not at the top of the call stack
- User-facing errors carry enough context for the user to take action
- Internal errors carry enough context for a developer to diagnose the failure
- Every catch block either: resolves the error with a meaningful fallback, translates
  and rethrows as a domain error, or logs and rethrows — never catches and discards

## Deliberate degraded-mode fallback is not swallowing

A catch block that falls back to a cached value, an empty collection, or a
previous state is **not** a violation of this principle when that fallback is
the documented, intended behaviour for a supplementary or best-effort data
source — e.g. a mobile client on unreliable connectivity choosing to render a
content hierarchy without live analytics overlay rather than block the whole
screen on one non-critical fetch, or one of several independently-synced
per-resource updates failing without blocking the others. This is still
propagation: the fallback is a conscious design decision, encoded and
comment-documented at the point it happens, not an accidental swallow that
hides a bug. What makes it a violation is the *absence* of that reasoning —
the same code, undocumented and covering for infrastructure that should have
been fixed instead, is exactly the "future mystery bug" this principle warns
against. When in doubt: can a future reader tell from the code and its
comments whether the empty/cached result was intentional? If yes, it's a
degraded-mode fallback. If a reader has to guess, it's a violation.

## Error categories

| Category | Meaning | Handling |
|----------|---------|----------|
| Domain error | Expected failure within the business rules (not found, conflict, unauthorised) | Translate at the layer boundary; surface to caller as a typed result |
| Technical error | Unexpected infrastructure failure (network timeout, disk full) | Translate to a generic domain error at the boundary; log the original |
| Programming error | Bug — null dereference, illegal state, contract violation | Do not catch; let it propagate and crash fast |

## Violations

- `catch (e: Exception) { return null }`
- `catch (e: Exception) { /* ignore */ }`
- Returning an empty list or a zero value to signal a failed operation
- Catching a typed exception and re-throwing a less specific one, losing the cause
- Handling a programming error with a try-catch instead of fixing the bug
