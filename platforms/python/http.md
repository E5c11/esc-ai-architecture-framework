---
id: PLAT-PY-HTTP
type: guide
layer: platforms
platform: [python]
architecture: python-app
requires: [ARCH-PY, ARCH-PY-ENTRYPOINT, PLAT-PY, PLAT-PY-TYPING]
related: [ARCH-PY-ERROR, ARCH-PY-COMPOSITION, ARCH-PY-CONCURRENCY, PLAT-PY-TESTING, ARCH-BE-ERROR]
tags: [http, fastapi, rest, api, router, pydantic, error-envelope, openapi]
---
# HTTP API Surface

Extends: `ARCH-PY-ENTRYPOINT`

FastAPI is the default HTTP framework: type-hint-driven request/response models, an
OpenAPI document for free, and dependency injection that maps neatly onto the
composition root. An HTTP route is an entrypoint like any other — thin, no logic.

This is the Python counterpart of the controller layer in `backend-service`
(`ARCH-BE-CONTROLLER`); the same idea — the controller is the HTTP boundary, nothing
more — applies, with the layers named as in `ARCH-PY`.

## Rules

```rule
id: PYHTTP-THIN-01
statement: A route handler MUST parse the request into typed values, call exactly one use case, and translate the result or error to a response; it MUST contain no business logic.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYHTTP-THIN-01 — A route handler MUST parse the request into typed values, call exactly one use case, and translate the result or error to a response; it MUST contain no business logic.
```

```rule
id: PYHTTP-MODELS-01
statement: Request and response models MUST be separate from domain values and defined in the HTTP entrypoint package; a route MUST NOT return a domain entity or a DataSource row directly.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates PYHTTP-MODELS-01 — Request and response models MUST be separate from domain values and defined in the HTTP entrypoint package; a route MUST NOT return a domain entity or a DataSource row directly.
```

The wire shape is a public contract (`CORE-API-STABILITY`); the domain must be free to change
without breaking clients.

```rule
id: PYHTTP-WIRING-01
statement: Use cases MUST reach route handlers as parameters supplied at the composition root (an app factory `create_app(app: App)` and a FastAPI dependency returning the pre-built use case); handlers MUST NOT construct DataSources or read configuration.
type: hard
scope: di
enforced_by: [ci, reviewer]
violation_message: Violates PYHTTP-WIRING-01 — Use cases MUST reach route handlers as parameters supplied at the composition root (an app factory `create_app(app: App)` and a FastAPI dependency returning the pre-built use case); handlers MUST NOT construct DataSources or read configuration.
```

`app.dependency_overrides` lets a test swap in fakes without touching the routes.

```rule
id: PYHTTP-ERROR-01
statement: All error responses MUST share one envelope (a status and a message) produced by exception handlers registered once — one for `AppError` subclasses mapped by cause, one catch-all that logs the traceback and returns a generic 500.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PYHTTP-ERROR-01 — All error responses MUST share one envelope (a status and a message) produced by exception handlers registered once — one for `AppError` subclasses mapped by cause, one catch-all that logs the traceback and returns a generic 500.
```

This mirrors the two-tier flow in `ARCH-BE-ERROR` and `ARCH-PY-ERROR`.

```rule
id: PYHTTP-ASYNC-01
statement: A route that calls a synchronous, blocking use case MUST be declared `def` (run by the framework in a worker thread) or use `run_in_threadpool`; it MUST NOT be `async def` and block the event loop.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYHTTP-ASYNC-01 — A route that calls a synchronous, blocking use case MUST be declared `def` (run by the framework in a worker thread) or use `run_in_threadpool`; it MUST NOT be `async def` and block the event loop.
```

```rule
id: PYHTTP-AUTH-01
statement: Authentication and authorization MUST be enforced by a dependency applied at the router level, deny by default, with no unauthenticated route added without an explicit, reviewed allow-list entry.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYHTTP-AUTH-01 — Authentication and authorization MUST be enforced by a dependency applied at the router level, deny by default, with no unauthenticated route added without an explicit, reviewed allow-list entry.
```

```rule
id: PYHTTP-PATHS-01
statement: Route path constants and the API version prefix MUST be defined in one module and referenced by routers; literal path strings MUST NOT be repeated in handlers or tests.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYHTTP-PATHS-01 — Route path constants and the API version prefix MUST be defined in one module and referenced by routers; literal path strings MUST NOT be repeated in handlers or tests.
```

Same discipline as the path-constants rule in `ARCH-BE-MOD-02`.

## Testing

Test routes with FastAPI's `TestClient` and `dependency_overrides` supplying fakes:
happy path status, error mapping, request validation (422), and authentication (401/403).
Use case behavior is tested at the application layer, not through HTTP.
