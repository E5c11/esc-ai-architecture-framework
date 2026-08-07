---
id: ARCH-WEB-APP-ERR-CLASSES
type: guide
layer: architectures
platform: [web]
architecture: [web-app]
requires: [ARCH-WEB-APP, PAT-OUTCOME, CORE-ERROR]
related: [ARCH-PC-ERR-CLASSES]
tags: [error-handling, outcome, typed-errors, server-actions, route-handlers, zod, react-hook-form]
status: active
---

# Typed Error Classes

Sibling doc to `ARCH-WEB-APP`'s `overview.md` — same split mobile chose:
`ARCH-PC-ERR-CLASSES` sits next to `pragmatic-clean/overview.md` rather than
inside it. This doc mirrors `ARCH-PC-ERR-CLASSES` one-for-one, restated for the
Server Action/Route Handler boundary instead of the DataSource boundary.

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
statement: Error types crossing the Server Action/Route Handler boundary MUST be a typed discriminated union — never a raw thrown Error, fetch Response, or Postgres driver error.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-ERR-TYPE-01 — Error types crossing the Server Action/Route Handler boundary MUST be a typed discriminated union — never a raw thrown Error, fetch Response, or Postgres driver error.
```

```rule
id: ARCH-WEB-APP-ERR-MAP-01
statement: A provider error (REST error response, Postgres error) MUST be translated exactly once, at the Server Action or Route Handler that calls the provider.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-ERR-MAP-01 — A provider error MUST be translated exactly once, at the Server Action or Route Handler that calls the provider.
```

```rule
id: ARCH-WEB-APP-ERR-UNKNOWN-01
statement: Unknown failures MUST be logged server-side with full cause and mapped to an explicit `unexpected` outcome — never returned as empty data or false success.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-ERR-UNKNOWN-01 — Unknown failures MUST be logged server-side with full cause and mapped to an explicit `unexpected` outcome.
```

Rationale specific to this rule: Next.js strips a thrown Server Action error to
an opaque digest in production — the caller sees neither the message nor the
stack. Returning an explicit `unexpected` outcome instead of throwing is what
keeps the failure detail from being silently lost, which is exactly the
false-success failure mode `PAT-OUTCOME` already warns against. This is itself
a platform detail rather than an architecture rule, so it is not duplicated as
a second rule here — it is restated in `platforms/web/nextjs-app.md` when that
doc is authored.

```rule
id: ARCH-WEB-APP-ERR-CANCEL-01
statement: An aborted client-side request (AbortController) MUST remain distinguishable from operational failure.
type: soft
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-ERR-CANCEL-01 — An aborted client-side request MUST remain distinguishable from operational failure.
```
