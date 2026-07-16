---
id: ARCH-BE-ERROR
type: rules
layer: architectures
platform: [backend]
architecture: backend-service
requires: [ARCH-BE, CORE-ERROR]
related: [ARCH-BE-SERVICE, ARCH-BE-CONTROLLER, PLAT-BE-SPRING]
tags: [error-handling, exceptions, http-status, global-exception-handler, two-tier]
---

# Error Flow

## Two-tier strategy

```
Tier 1: Known business errors
    Service throws ResponseStatusException(HttpStatus.X, "message")
    → Spring resolves HTTP status automatically
    → No custom handler needed

Tier 2: Unexpected errors
    Any unhandled exception
    → GlobalExceptionHandler catches it
    → Logs with full stack trace
    → Returns consistent ErrorResponse body with HTTP 500
```

Tier 1 requires no infrastructure. Tier 2 requires a single `GlobalExceptionHandler`
declared once per project.

## Rules

```rule
id: ERR-KNOWN-01
statement: Known business errors MUST be thrown as `ResponseStatusException` from the **service layer**, not the controller.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ERR-KNOWN-01 — Known business errors MUST be thrown as `ResponseStatusException` from the **service layer**, not the controller.
```

Throwing from the service keeps the controller clean and ensures the HTTP semantics are set as close as possible to the source of the error.

> Violation: Returning null from the service and letting the controller map it to a 404.
> Fix: Throw `ResponseStatusException(HttpStatus.NOT_FOUND, "...")` from the service.

```rule
id: ERR-UNKNOWN-01
statement: A `GlobalExceptionHandler` with a catch-all `@ExceptionHandler(Exception::class)` MUST exist.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ERR-UNKNOWN-01 — A `GlobalExceptionHandler` with a catch-all `@ExceptionHandler(Exception::class)` MUST exist.
```

Without it, unexpected exceptions return a 500 with no logging and an inconsistent body shape.

```rule
id: ERR-RESPONSE-01
statement: ALL error responses — both Tier 1 and Tier 2 — MUST use the same `ErrorResponse` body shape (`status: Int`, `message: String`).
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ERR-RESPONSE-01 — ALL error responses — both Tier 1 and Tier 2 — MUST use the same `ErrorResponse` body shape (`status: Int`, `message: String`).
```

Mixed shapes (plain strings, varying field names) prevent the client from handling errors uniformly.

```rule
id: ERR-SERVICE-01
statement: Services MUST NOT catch `ResponseStatusException` in a general `catch (e: Exception)` block without re-throwing it.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ERR-SERVICE-01 — Services MUST NOT catch `ResponseStatusException` in a general `catch (e: Exception)` block without re-throwing it.
```

Swallowing a `ResponseStatusException` loses the HTTP status the service intentionally set. If a service has a general exception handler, add `catch (e: ResponseStatusException) { throw e }` before the general handler.

```rule
id: ERR-LOG-01
statement: The `GlobalExceptionHandler` catch-all MUST log the exception with the full stack trace before building the error response.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ERR-LOG-01 — The `GlobalExceptionHandler` catch-all MUST log the exception with the full stack trace before building the error response.
```

Without a log entry, production errors are invisible.

## Known error → HTTP status mapping

| Business condition | HTTP status |
|---|---|
| Resource not found | 404 NOT_FOUND |
| Already exists / duplicate | 409 CONFLICT |
| Bad credentials / invalid token | 401 UNAUTHORIZED |
| Action not allowed for this user | 403 FORBIDDEN |
| Invalid business input | 400 BAD_REQUEST |
| Precondition failed | 412 PRECONDITION_FAILED |

## Error boundary

The controller never needs to catch exceptions for known errors. Spring and the
`GlobalExceptionHandler` handle all error-to-response mapping. A controller
that wraps a service call in a try-catch to produce a status code is a sign
that the service is not throwing `ResponseStatusException` correctly.

## GlobalExceptionHandler responsibilities

The `GlobalExceptionHandler` handles three cases:

1. **`ResponseStatusException`** — forward status and message from Tier 1 throws
2. **`MethodArgumentNotValidException`** — collect all `@Valid` field errors into one message
3. **`Exception` (catch-all)** — log + 500 + generic message

The handler MUST be declared in a core/infrastructure package, not in a domain module.
It handles errors from all controllers.

See `PLAT-BE-SPRING` for the implementation template.
