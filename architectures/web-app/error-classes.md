---
id: ARCH-WEB-APP-ERR-CLASSES
type: guide
layer: architectures
platform: [web]
architecture: [web-app]
requires: [ARCH-WEB-APP, PAT-OUTCOME, CORE-ERROR]
related: [ARCH-PC-ERR-CLASSES, ARCH-WEB-APP-ERR-FLOW]
tags: [error-handling, outcome, typed-errors, datasource, server-actions, route-handlers, static-export, zod, react-hook-form]
status: active
---

# Typed Error Classes

Sibling doc to `ARCH-WEB-APP`'s `overview.md` — same split mobile chose:
`ARCH-PC-ERR-CLASSES` sits next to `pragmatic-clean/overview.md` rather than
inside it. This doc mirrors `ARCH-PC-ERR-CLASSES` one-for-one, restated for the
DataSource boundary of a web app. That boundary is a Server Action or Route
Handler (or a DataSource module it calls) in the `server` runtime, and a
browser-side DataSource module in the `static-export` runtime (see
`ARCH-WEB-APP`). The rules are the same in both; only where they execute differs.

## Shape

The TS instantiation of `PAT-OUTCOME` for this boundary:

```typescript
type Outcome<T, E extends AppError = AppError> =
  | { ok: true; data: T }
  | { ok: false; error: E };

type AppError =
  | { type: 'offline' }
  | { type: 'unauthorized' }
  | { type: 'forbidden' }
  | { type: 'notFound' }
  | { type: 'validation'; fieldErrors: Record<string, string[]> }
  | { type: 'unexpected'; message: string };
```

`validation` is shaped like zod's `.flatten().fieldErrors` deliberately — it
composes directly with react-hook-form's `setError` instead of introducing a
second error channel next to the already-decided forms stack.

## Rules

```rule
id: ARCH-WEB-APP-ERR-TYPE-01
statement: Error types crossing the DataSource boundary (a Server Action or Route Handler in the `server` runtime, a browser-side DataSource in `static-export`) MUST be a typed discriminated union — never a raw thrown Error, fetch Response, Firestore error, or Postgres driver error.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-ERR-TYPE-01 — Error types crossing the DataSource boundary MUST be a typed discriminated union — never a raw thrown Error, fetch Response, Firestore error, or Postgres driver error.
```

```rule
id: ARCH-WEB-APP-ERR-MAP-01
statement: A provider error (REST error response, Postgres error, Firestore or callable-function error) MUST be translated exactly once, at the DataSource that calls the provider (in the `server` runtime, the Server Action or Route Handler or the DataSource module it calls).
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-ERR-MAP-01 — A provider error MUST be translated exactly once, at the DataSource that calls the provider.
```

```rule
id: ARCH-WEB-APP-ERR-UNKNOWN-01
statement: Unknown failures MUST be logged with full cause (server-side in the `server` runtime; through the client error reporter in `static-export`) and mapped to an explicit `unexpected` outcome — never returned as empty data or false success.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-ERR-UNKNOWN-01 — Unknown failures MUST be logged with full cause and mapped to an explicit `unexpected` outcome.
```

Rationale specific to this rule: Next.js strips a thrown Server Action error to
an opaque digest in production — the caller sees neither the message nor the
stack. Returning an explicit `unexpected` outcome instead of throwing is what
keeps the failure detail from being silently lost, which is exactly the
false-success failure mode `PAT-OUTCOME` already warns against. This is itself
a platform detail rather than an architecture rule, so it is not duplicated as
a second rule here — it is restated in `platforms/web/nextjs-app.md` when that
doc is authored.

In `static-export` nothing is stripped, but the same rule holds for a different
reason: a swallowed provider error shows the user an empty screen that looks like
"no data". Firestore's `permission-denied` maps to `forbidden` (or `unauthorized`
when there is no signed-in user), a callable function's typed failure maps to the
matching variant, and an unrecognised code maps to `unexpected` with the original
error logged.

```rule
id: ARCH-WEB-APP-ERR-CANCEL-01
statement: An aborted client-side request (AbortController) SHOULD remain distinguishable from operational failure.
type: soft
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-ERR-CANCEL-01 — An aborted client-side request SHOULD remain distinguishable from operational failure.
```
