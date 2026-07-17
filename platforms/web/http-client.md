---
id: PLAT-WEB-HTTP
type: guide
layer: platforms
platform: [web]
architecture: [web-app]
requires: [ARCH-WEB-APP, ARCH-WEB-APP-ERR-CLASSES, CORE-DI]
related: [PLAT-WEB-NEXT-APP, QG-WEB-TESTING]
tags: [http, fetch, rest, executor, header-provider, retry, typed-errors, testing, msw]
---

# HTTP Client Layer (`web-app` → Backend)

## Scope

This doc covers REST calls made from the Route Handler/Server Action
boundary only. `ARCH-WEB-APP`'s own layer-boundary rule — "Client Component
... never fetches a backend or opens a DB connection itself" — already
establishes that there is no client-side REST layer to document: every call
this doc governs happens server-side, inside a Route Handler or Server
Action.

`PLAT-MOB-HTTP` is a reasonable *structural* template for this doc — the
same shape (executor abstraction, header/auth provider, retry policy, typed
error mapping, DI registration, fake-based testing) recurs here — but it is
Ktor/KMP-specific. This is a genuine `fetch`-based TypeScript rewrite of
that shape, not a find-replace of Kotlin syntax.

No token-refresh section exists here, unlike `PLAT-MOB-HTTP`'s
`AuthRefresher`/`AuthPolicy` pair. A mobile client holds a long-lived token
across app sessions and has to coordinate refresh across concurrent
in-flight requests from a single device; a `web-app` Route Handler/Server
Action reads a server-side session on every request instead of holding a
token in memory between requests, so there is no refresh-coordination
problem to solve at this layer — the session mechanism itself (whatever
issues and validates the staff session) owns expiry, not the HTTP executor.

## Executor abstraction

```rule
id: PLAT-WEB-HTTP-LIB-01
statement: REST calls to a backend MUST go through a shared request-executor abstraction — never an ad hoc `fetch` call written inline in a Server Action or Route Handler.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-LIB-01 — REST calls MUST go through a shared executor, not inline `fetch` scattered across Server Actions/Route Handlers.
```

This is `CORE-DI` applied to networking: swapping the transport, adding a
policy (retry, logging), or testing against a fake must not require editing
every call site.

```typescript
// lib/http/executor.ts
export interface HttpRequestExecutor {
  getJson<T>(url: string, params?: Record<string, string>): Promise<HttpResult<T>>;
  postJson<T>(url: string, body: unknown): Promise<HttpResult<T>>;
  patchJson<T>(url: string, body: unknown): Promise<HttpResult<T>>;
  deleteJson<T>(url: string): Promise<HttpResult<T>>;
}

export type HttpResult<T> =
  | { ok: true; status: number; data: T }
  | { ok: false; status: number; body: unknown };
```

`HttpResult` is deliberately a provider-level vocabulary, not the app's
`AppError` union — it carries the raw status/body so the calling boundary
can decide how to map it (see Error mapping below). Base URL and default
headers are configured once at construction:

```typescript
// lib/http/createExecutor.ts
export function createFetchExecutor(config: {
  baseUrl: string;
  headerProvider: HeaderProvider;
}): HttpRequestExecutor {
  async function request<T>(path: string, init: RequestInit): Promise<HttpResult<T>> {
    const headers = await config.headerProvider.getHeaders(init.headers as Record<string, string>);
    const res = await fetch(`${config.baseUrl}${path}`, { ...init, headers });
    if (!res.ok) return { ok: false, status: res.status, body: await safeJson(res) };
    return { ok: true, status: res.status, data: (await res.json()) as T };
  }
  return {
    getJson:   (path, params) => request(withQuery(path, params), { method: 'GET' }),
    postJson:  (path, body)   => request(path, { method: 'POST',  body: JSON.stringify(body) }),
    patchJson: (path, body)   => request(path, { method: 'PATCH', body: JSON.stringify(body) }),
    deleteJson: path          => request(path, { method: 'DELETE' }),
  };
}
```

## Auth header attachment

```rule
id: PLAT-WEB-HTTP-AUTH-01
statement: The executor MUST attach the staff auth token via an injected header provider that reads the server-side session — a Server Action/Route Handler MUST NOT read or forward a token itself.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-AUTH-01 — token attachment is the executor's job via an injected provider, not something each call site does itself.
```

```typescript
export interface HeaderProvider {
  getHeaders(additional?: Record<string, string>): Promise<Record<string, string>>;
}

export class SessionHeaderProvider implements HeaderProvider {
  async getHeaders(additional: Record<string, string> = {}) {
    const session = await getServerSession();   // e.g. next-auth, or a hand-rolled session read
    return {
      'Content-Type': 'application/json',
      ...(session?.accessToken ? { Authorization: `Bearer ${session.accessToken}` } : {}),
      ...additional,
    };
  }
}
```

A Server Action/Route Handler calls `questionsExecutor.postJson(...)` and
never sees a token — the same discipline `PLAT-MOB-HTTP-AUTH-01` establishes
for a DataSource, restated for this boundary.

## Error mapping

```rule
id: PLAT-WEB-HTTP-ERR-01
statement: A non-2xx response MUST be mapped into the `AppError` union at the executor or the calling Server Action/Route Handler — never left as an unmapped `Response`/thrown error past that boundary.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-ERR-01 — cites ARCH-WEB-APP-ERR-MAP-01; map the provider error exactly once, at this boundary.
```

```typescript
function toAppError(result: Extract<HttpResult<unknown>, { ok: false }>): AppError {
  switch (result.status) {
    case 401: return { type: 'unauthorized' };
    case 403: return { type: 'forbidden' };
    case 404: return { type: 'notFound' };
    case 422: return { type: 'validation', fieldErrors: extractFieldErrors(result.body) };
    default:  return { type: 'unexpected', message: `Backend returned ${result.status}` };
  }
}
```

A network-level failure (the `fetch` call itself rejecting — DNS, connection
refused, timeout) maps to `{ type: 'offline' }` rather than `unexpected`;
distinguishing "the backend responded with an error" from "the backend was
unreachable" is worth preserving through the mapping, not collapsed into one
generic case.

## Retry policy

```rule
id: PLAT-WEB-HTTP-RETRY-01
statement: Only idempotent requests (GET, or a write with an explicit idempotency key) MAY be retried automatically.
type: soft
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-RETRY-01 — a POST/PATCH/PUT/DELETE without an idempotency key MUST NOT be retried automatically.
```

A retry wraps the executor's `getJson` (and any write call the caller has
explicitly marked idempotent) with a small bounded backoff on network-level
failures — a 4xx response is never retried, since retrying a request the
backend has already rejected wastes a round-trip without changing the
outcome.

## DI registration

`web-app` has no dependency-injection framework equivalent to Koin — the
executor is instead a module-level singleton, constructed once when the
module is first imported and exported for every Server Action/Route
Handler to import:

```rule
id: PLAT-WEB-HTTP-DI-01
statement: The configured executor MUST be constructed once as a module-level singleton and imported by Server Actions/Route Handlers — never constructed ad hoc inside a call site.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-DI-01 — the executor MUST be a module-level singleton; a Server Action/Route Handler MUST NOT construct its own executor instance.
```

```typescript
// lib/http/questionsExecutor.ts
export const questionsExecutor = createFetchExecutor({
  baseUrl: process.env.QUESTIONS_API_BASE_URL!,
  headerProvider: new SessionHeaderProvider(),
});
```

```typescript
// features/questions/actions/updateQuestion.ts
'use server';
import { questionsExecutor } from '@/lib/http/questionsExecutor';

export async function updateQuestion(input: UpdateQuestionInput): Promise<Outcome<Question>> {
  const result = await questionsExecutor.patchJson<QuestionDto>(`/questions/${input.id}`, input);
  if (!result.ok) return { ok: false, error: toAppError(result) };
  return { ok: true, data: fromDto(result.data) };
}
```

This satisfies `CORE-DI` the same way Koin's `single {}` does for mobile —
one construction point, swappable for a fake in tests — without requiring a
DI framework Next.js server code has no standard equivalent for.

## Testing

See `QG-WEB-TESTING` for the full pattern — MSW mocks the Provider (the
actual HTTP boundary a Route Handler/Server Action calls out to); a fake
implementation of `HttpRequestExecutor` is what a Server Action's own test
depends on. Same fake-not-mock split `PLAT-MOB-HTTP-TEST-01` establishes for
mobile: the fake is for consumers of the executor, MSW is for proving the
executor itself builds the right request against the network.
