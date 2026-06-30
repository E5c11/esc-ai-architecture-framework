---
id: ARCH-PC-ERR-CLASSES
type: guide
layer: architecture
platform: [mobile]
architecture: [pragmatic-clean]
requires: [ARCH-PC-ERROR-FLOW, CORE-ERROR]
related: [PAT-OUTCOME, PLAT-MOB-KOTLIN]
tags: [error-handling, exceptions, domain-exceptions, error-severity, error-presentation, actionable-errors]
status: stub
---

# Exception Class Definitions

> **TODO:** This document is a stub. See `todo/missing-files.md` for context.
>
> **Open question:** Determine whether the base exception type and
> `ErrorSeverity`/`ErrorPresentation`/`ErrorAction` sealed classes are defined:
> (a) directly in this project (KMP common),
> (b) via Arrow's error types (arrow-core Raise/Either), or
> (c) via a custom shared library (arrow-errors or similar).
> The implementation guide depends on this answer. Resolve before writing this doc.

## What this document must cover

- The base domain exception class — fields required (message, severity, presentation, primary action)
- `ErrorSeverity` sealed class or enum values and when to use each
- `ErrorPresentation` variants (snackbar, inline, dialog, full-screen) and when to use each
- `ErrorAction` — Retry, Dismiss, Navigate — and how to wire each to a ViewModel function
- Feature exception naming convention (e.g. `FetchVideosException`, `SubmitAnswerException`)
- Where to declare shared base types vs feature-specific types
- Step-by-step: defining a new feature exception from scratch
- What NOT to do — common mistakes (extending base language Exception directly, omitting severity)
