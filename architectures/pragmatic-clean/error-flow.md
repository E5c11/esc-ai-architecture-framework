---
id: ARCH-PC-ERROR-FLOW
type: guide
layer: architecture
platform: [mobile]
architecture: [pragmatic-clean]
requires: [ARCH-PC, CORE-ERROR, ARCH-PC-DATASOURCE, ARCH-PC-USECASE, ARCH-PC-VIEWMODEL, ARCH-PC-VIEW]
related: [PAT-OUTCOME]
tags: [error-handling, exceptions, propagation, actionable, ui-metadata, layers]
---

# End-to-End Error Flow

## Overview

Errors originate at the provider level as raw technical exceptions. They are
progressively translated as they move up the layer stack until they reach the
View as structured objects that carry everything needed to render the error to
the user.

## Layer responsibilities

```
Provider
  throws raw technical exception (IOException, FirebaseException, SQLException)
        ↓
DataSource
  catches provider exception
  translates to domain exception (carries UI metadata: message, severity, actions)
  rethrows domain exception upward
        ↓
Repository (if present)
  passes domain exceptions through unchanged
  does not re-translate or re-wrap
        ↓
UseCase
  applies boundary catch
  passes through existing domain exceptions unchanged
  translates unexpected exceptions into operation-specific domain exceptions
  wraps result in Outcome.Failure
        ↓
ViewModel
  receives Outcome.Failure containing domain exception
  stores full exception object in state (not extracted fields)
  exposes retry and clearError if retryable
        ↓
View
  receives full exception from state
  delegates rendering to error presentation component
  does not inspect or parse the exception
```

## Domain exception contract

A domain exception carries UI metadata so the View can render it without
any logic:
- **Message** — what to show the user (localised)
- **Severity** — informational / warning / critical
- **Presentation style** — snackbar / dialog / full-screen
- **Primary action** — Retry / Dismiss / Navigate (optional)

All user-facing exceptions MUST extend the domain exception base type and carry
this metadata. Raw technical exceptions (IOException, etc.) MUST NEVER reach
the ViewModel.

**Rule ARCH-PC-ERR-BASE-01 (hard):** All user-facing exceptions MUST extend the
project's domain exception base type. Never extend the language's base exception
type directly for a user-facing error.

**Rule ARCH-PC-ERR-BASE-02 (hard):** Domain exceptions MUST be defined in
`data/errors/` within the feature that owns them, never in `core/` unless they
genuinely apply across all features.

## Translation rules

**Rule ARCH-PC-ERR-TRANSLATE-01 (hard):** Translation of provider exceptions to
domain exceptions happens ONLY in the DataSource. It MUST NOT happen in UseCases,
Repositories, or ViewModels.

**Rule ARCH-PC-ERR-TRANSLATE-02 (hard):** Domain exceptions MUST be rethrown
unchanged at every layer above the DataSource. Re-wrapping a domain exception
loses its UI metadata.

**Rule ARCH-PC-ERR-FALLBACK-01 (hard):** The fallback exception in a UseCase's
catch handler MUST be named after the operation (e.g. `FetchVideosException`),
not a generic "unknown error" type. Generic fallbacks lose diagnostic context
in crash reporting.

## Coroutine cancellation

**Rule ARCH-PC-ERR-CANCEL-01 (hard):** Coroutine cancellation exceptions MUST
be rethrown at every catch site before any other handling. An inner catch block
that swallows cancellation causes the coroutine to continue executing code that
should have been cancelled.

## State in ViewModel

**Rule ARCH-PC-ERR-STATE-01 (hard):** The ViewModel MUST store the full domain
exception in state, not individual extracted fields. Extracting a message string
discards severity, presentation style, and available actions.

**Rule ARCH-PC-ERR-STATE-02 (soft):** ViewModels SHOULD expose a `clearError()`
function that sets the error state back to null, used after the user dismisses
an error.

## Network exceptions

**Rule ARCH-PC-ERR-NETWORK-01 (soft):** Network connectivity errors are
user-side noise, not application bugs. They SHOULD NOT be recorded in crash
reporting. The UseCase layer is responsible for distinguishing network errors
from real application faults before logging.

## Violations

- Provider exception (`FirebaseException`, `IOException`) reaching the ViewModel
- Domain exception re-wrapped at the Repository or UseCase level
- Only an error message string stored in ViewModel state
- Cancellation exception swallowed in an inner catch block
- Generic fallback exception (`UnknownException`) used in UseCase boundary catch
- View parsing or branching on exception fields instead of delegating to error component
