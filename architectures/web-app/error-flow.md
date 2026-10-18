---
id: ARCH-WEB-APP-ERR-FLOW
type: guide
layer: architectures
platform: [web]
architecture: [web-app]
requires: [ARCH-WEB-APP, ARCH-WEB-APP-ERR-CLASSES, ARCH-WEB-APP-DATASOURCE, ARCH-WEB-APP-USECASE, ARCH-WEB-APP-HOOK, PAT-OUTCOME, CORE-ERROR]
related: [ARCH-WEB-APP-COMPONENT, ARCH-WEB-APP-OBS, ARCH-PC-ERROR-FLOW, ARCH-PY-ERROR, PLAT-WEB-NEXT-APP]
tags: [error-handling, error-flow, outcome, boundary, retry, presentation, swallow, validation]
status: active
---

# End-to-End Error Flow

## Overview

`ARCH-WEB-APP-ERR-CLASSES` defines the typed error union and the rule that a provider
error is translated once. This document follows an error the whole way up: where it is
born, what each layer does with it, how it reaches the user, and what happens to the
failures nobody planned for. It restates `ARCH-PC-ERROR-FLOW` for a web app, with
`Outcome` values in place of exceptions for expected failures.

## Layer responsibilities

```
Provider
  fails in its own terms (a rejected fetch, a `FirebaseError` with a `code`, a driver error)
        ↓
DataSource                                           (ARCH-WEB-APP-ERR-MAP-01)
  catches the provider failure, translates it once to AppError, logs unknowns once
  returns { ok: false, error }.  An abort is rethrown unchanged.
        ↓
Repository (if present)
  passes the error outcome up unchanged; may fall back to a cache, visibly
        ↓
UseCase                                              (ARCH-WEB-APP-EFLOW-SWALLOW-01)
  passes the error up unchanged unless it adds domain meaning
  never turns an error into an empty success
        ↓
Hook                                                 (ARCH-WEB-APP-HOOK-ERROR-01)
  stores the full AppError in a ViewState { status: 'error' }; offers retry
        ↓
Component                                            (ARCH-WEB-APP-COMP-STATE-01)
  chooses the presentation from the AppError variant; does not parse messages
```

A defect (a programming error) is different: it is **thrown**, not returned, and
nothing above the point where it occurs catches it except a route-level boundary.

## Rules

```rule
id: ARCH-WEB-APP-EFLOW-RETURN-01
statement: An expected failure (a provider error, a validation failure, a denied permission, a missing record that must exist) MUST cross the DataSource and Hook boundaries as a returned error outcome, and a thrown error MUST mean a defect; layers between those two boundaries MAY propagate the outcome or throw internally, provided the UseCase boundary converts back to an outcome.
type: hard
scope: error-handling
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-EFLOW-RETURN-01 — An expected failure (a provider error, a validation failure, a denied permission, a missing record that must exist) MUST cross the DataSource and Hook boundaries as a returned error outcome, and a thrown error MUST mean a defect; layers between those two boundaries MAY propagate the outcome or throw internally, provided the UseCase boundary converts back to an outcome.
```

This differs from `ARCH-PC`, where the DataSource throws a typed domain error and the UseCase converts it. The reasons are specific to TypeScript and React, not a preference: a `catch` variable is `unknown` and nothing forces an `instanceof` check, an unawaited rejection is silent, an error thrown in an event handler or effect never reaches a React error boundary, and Next.js strips a thrown Server Action error to an opaque digest in production. The cost is `if (!result.ok) return result` plumbing in the layers between; if the pilot shows that costs more than it saves, relax those layers only.

If an expected failure is thrown, every caller needs a `try`/`catch` it will forget; if
a defect is returned, the screen shows a polite error for a bug nobody is told about.
The Server Action form of this rule is `PLAT-WEB-NEXT-APP-THROW-01`.

```rule
id: ARCH-WEB-APP-EFLOW-SWALLOW-01
statement: Code MUST NOT catch an error and discard it: every `catch` and `.catch` MUST translate the error into a returned outcome, rethrow it, or (only for a contained side effect) log it, and an empty handler MUST NOT exist.
type: hard
scope: error-handling
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-EFLOW-SWALLOW-01 — Code MUST NOT catch an error and discard it: every `catch` and `.catch` MUST translate the error into a returned outcome, rethrow it, or (only for a contained side effect) log it, and an empty handler MUST NOT exist.
```

```typescript
// ❌ Wrong — the failure disappears; the screen shows stale or empty data
try { await save(feed); } catch {}
save(feed).catch(() => {});

// ✅ Correct — the failure is part of the result
const result = await save(feed);                  // an Outcome; never rejects for an expected failure
if (!result.ok) return setState({ status: 'error', error: result.error });
```

```rule
id: ARCH-WEB-APP-EFLOW-LOG-01
statement: An unexpected error MUST be logged exactly once, at the layer that first handles it (the DataSource for a provider failure, the boundary for a defect), and a layer above MUST NOT log the same error again.
type: hard
scope: error-handling
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-EFLOW-LOG-01 — An unexpected error MUST be logged exactly once, at the layer that first handles it (the DataSource for a provider failure, the boundary for a defect), and a layer above MUST NOT log the same error again.
```

The same failure logged at four layers is four entries to reconcile and no clearer cause.

An error message reaches a screen, a log and an error report. Whatever is in it is in
all three (`ARCH-WEB-APP-OBS-REDACT-01`).

## Validation at the boundary

```rule
id: ARCH-WEB-APP-EFLOW-VALIDATE-01
statement: Untrusted input (form values, URL parameters, provider payloads) MUST be parsed with a schema parser where it enters, and a failure MUST become an error outcome, not a thrown error or a default value.
type: hard
scope: error-handling
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-EFLOW-VALIDATE-01 — Untrusted input (form values, URL parameters, provider payloads) MUST be parsed with a schema parser where it enters, and a failure MUST become an error outcome, not a thrown error or a default value.
```

```rule
id: ARCH-WEB-APP-EFLOW-ASSERT-01
statement: A type assertion (`as Foo`), a non-null assertion (`!`) or `// @ts-ignore` MUST NOT be used to get past boundary validation or to silence the compiler about data that has not been checked.
type: hard
scope: error-handling
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-EFLOW-ASSERT-01 — A type assertion (`as Foo`), a non-null assertion (`!`) or `// @ts-ignore` MUST NOT be used to get past boundary validation or to silence the compiler about data that has not been checked.
```

An assertion tells the compiler the check happened. When it did not, the error moves
from the boundary, where it is one clear message, to wherever the value is first used,
where it is a `Cannot read properties of undefined`.

## Presenting errors

```rule
id: ARCH-WEB-APP-EFLOW-PRESENT-01
statement: The mapping from `AppError` variant to user-facing message and available action MUST live in one exhaustive presentation module shared by the app, and a feature MUST compose it rather than write its own wording for the same variant.
type: hard
scope: structure
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-EFLOW-PRESENT-01 — The mapping from `AppError` variant to user-facing message and available action MUST live in one exhaustive presentation module shared by the app, and a feature MUST compose it rather than write its own wording for the same variant.
```

An exhaustive switch over `AppError` means a new variant is a compile error in exactly
one place. A feature may add context ("the feed 'Mdantsane faults' could not be
saved") around the shared message; it does not re-decide what `forbidden` means.

```rule
id: ARCH-WEB-APP-EFLOW-NETWORK-01
statement: A connectivity failure (`offline`) MUST be presented as a recoverable state and MUST NOT be reported to the error reporter as a defect.
type: hard
scope: error-handling
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-EFLOW-NETWORK-01 — A connectivity failure (`offline`) MUST be presented as a recoverable state and MUST NOT be reported to the error reporter as a defect.
```

A user on a train is not a bug. Counting it as one buries the real defects.

## Retry

A retried "create" that succeeded the first time but timed out is a duplicate record.
Automatic retry lives at the DataSource (the transport), where the idempotence of the
call is known; the user's retry is the Hook's `retry`.

## Defects and boundaries

```rule
id: ARCH-WEB-APP-EFLOW-BOUNDARY-01
statement: A route-level error boundary (Next.js `error.tsx` or a React error boundary) MUST catch every thrown defect, report it once through the error reporter, and show a recoverable screen with a retry or a way back; an uncaught defect MUST NOT blank the page.
type: hard
scope: error-handling
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-EFLOW-BOUNDARY-01 — A route-level error boundary (Next.js `error.tsx` or a React error boundary) MUST catch every thrown defect, report it once through the error reporter, and show a recoverable screen with a retry or a way back; an uncaught defect MUST NOT blank the page.
```

The boundary files themselves, and where they sit in the route tree, are
`PLAT-WEB-NEXT`'s concern; this rule is what they are for.

## Violations

- A `catch {}` or `.catch(() => {})` that discards the failure
- An expected failure thrown, or a defect returned as an error outcome
- The same error logged in the DataSource, the UseCase and the Hook
- A message string that contains a token, a phone number or a raw response body
- `data as FeedDoc` or `value!` over unchecked input
- Two features wording `forbidden` differently
- An `offline` error sent to the error reporter as a bug
- A "create" retried automatically after a timeout
- A route with no error boundary, so one thrown defect blanks the page
