---
id: CORE-ERROR
type: principle
layer: core
platform: [all]
architecture: [all]
requires: []
related: [PAT-OUTCOME, CORE-COUPLING]
tags: [error-handling, propagation, exceptions, boundaries, observability]
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
