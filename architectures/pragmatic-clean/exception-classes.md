---
id: ARCH-PC-ERR-CLASSES
type: guide
layer: architecture
platform: [mobile]
architecture: [pragmatic-clean]
requires: [ARCH-PC-ERROR-FLOW, CORE-ERROR]
related: [PAT-OUTCOME, PLAT-MOB-KOTLIN]
tags: [error-handling, exceptions, domain-exceptions, error-severity, error-presentation, actionable-errors]
---

# Typed Exception Classes

## Boundary model

Provider exceptions are unstable implementation details. DataSources catch them and
return the project's typed error/result model; repositories and use cases must not learn
Ktor, Firebase, SQL, StoreKit or UIKit exception classes.

Projects may use an owned KMP error library such as `arrow-errors`, provided its public
error types are available from `commonMain` and have published variants for every target.

**Rule ARCH-PC-ERR-TYPE-01 (hard):** Error types crossing an architecture boundary
MUST be declared in common/domain code and MUST NOT inherit a platform SDK exception.

**Rule ARCH-PC-ERR-MAP-01 (hard):** A platform/provider exception MUST be translated
exactly once, at the DataSource or platform-adapter boundary that understands it.

**Rule ARCH-PC-ERR-UNKNOWN-01 (hard):** Unknown failures MUST retain their cause for
diagnostics and map to an explicit unexpected/unknown error. They must not be silently
reported as offline, empty data or success.

**Rule ARCH-PC-ERR-CANCEL-01 (hard):** Coroutine cancellation and user cancellation
MUST remain distinguishable from operational failure. Coroutine cancellation is rethrown;
user cancellation maps to an explicit cancelled outcome when the caller needs it.

## Recommended hierarchy

Use a small stable common hierarchy rather than mirroring every provider exception:

```kotlin
sealed interface AppError {
    data object Offline : AppError
    data object Unauthorized : AppError
    data object Forbidden : AppError
    data object NotFound : AppError
    data object Timeout : AppError
    data object Cancelled : AppError
    data class InvalidData(val detail: String? = null) : AppError
    data class Unexpected(val cause: Throwable? = null) : AppError
}
```

Names may differ in a consuming project or owned error library. The semantic constraints
above are authoritative: portable types, one mapping boundary, preserved causes and no
false success.

## Presentation metadata

If a project attaches severity, presentation or recovery actions to errors, those types
must also be portable common types. Prefer stable semantic values such as informational,
recoverable and fatal severity; inline, snackbar, dialog and full-screen presentation;
and retry, dismiss or navigate actions. The ViewModel maps domain errors to presentation
state. DataSources never decide how an error is rendered.

Feature errors should describe the failed operation (`FetchVideosError`,
`SubmitAnswerError`) and live with that feature's domain contract. Shared transport and
authentication errors belong in a shared error module or owned KMP error library.

## Validation checklist

- [ ] Boundary error types compile in `commonMain` and every configured target.
- [ ] No Ktor/Firebase/SQL/UIKit/StoreKit type escapes a DataSource or platform adapter.
- [ ] Cancellation is handled before broad `Throwable` handling.
- [ ] Unknown errors preserve a diagnostic cause and are reported.
- [ ] Tests cover every named mapping plus cancellation and an unknown exception.
