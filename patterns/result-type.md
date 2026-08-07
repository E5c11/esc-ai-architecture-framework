---
id: PAT-OUTCOME
type: pattern
layer: pattern
platform: [all]
architecture: [all]
requires: [CORE-ERROR]
related: [PAT-DATA-ACCESS, CORE-ERROR]
tags: [result-type, outcome, either, error-handling, typed-errors, railway]
status: active
---

# Result Type

## Statement

Operations that can fail return a typed result wrapper rather than throwing
exceptions across layer boundaries.

## Rationale

Exceptions are invisible in function signatures. A function that can fail but
returns `User` looks identical to one that always succeeds. Callers have no
compile-time signal that they must handle failure. A result type makes failure
explicit in the return type, forces the caller to handle both paths, and enables
composable error handling without try-catch noise at every call site.

## Also known as

`Result<T>`, `Either<E, T>`, `Outcome<T>`, Railway-Oriented Programming.
The concept is the same regardless of the name used by a platform or library.

## Structure

A result type has exactly two states:

- **Success** — carries the value of type `T`
- **Failure** — carries the error, typed to the domain's error vocabulary

## In Practice

- Use the result type at layer boundaries where failure is a normal, expected
  condition — not a programming error
- Compose result types with map / flatMap rather than nested if-checks or
  try-catch chains
- The success path and failure path are both explicit and type-safe; the compiler
  enforces that the caller handles both
- Use the result type for domain failures; let unexpected technical failures
  (programming errors, unrecoverable infrastructure failures) throw as exceptions

## When NOT to use

- For programming errors (null dereference, illegal state, contract violation) — these
  should throw and crash fast, not be wrapped in a result type
- For operations that cannot fail — adding a result type to an infallible function
  creates unnecessary noise

## Violations

- Returning `null` to signal failure from an otherwise typed function
- Throwing a domain exception across a layer boundary when a result type is
  the established pattern for that boundary
- Catching a result-type failure and swallowing it without propagating or handling
- Using a result type to wrap unexpected internal errors that should be treated
  as programming errors
