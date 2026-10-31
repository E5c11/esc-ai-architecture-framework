---
id: PLAT-WEB-HTTP-BROWSER
type: guide
layer: platforms
platform: [web]
architecture: [web-app]
runtime: [static-export]
requires: [ARCH-WEB-APP, ARCH-WEB-APP-DATASOURCE, ARCH-WEB-APP-COMPOSITION, ARCH-WEB-APP-ERR-CLASSES, PLAT-WEB-NEXT-STATIC]
related: [PLAT-WEB-HTTP, PLAT-MOB-HTTP, PLAT-WEB-NEXT-FIREBASE, ARCH-WEB-APP-OBS, QG-WEB-TESTING]
tags: [http, fetch, rest, browser, static-export, bearer-token, refresh-token, session, cors, executor, header-provider]
status: active
---

# HTTP from the Browser to the Project's Own Backend (`static-export`)

## Scope

A `static-export` `web-app` (`PLAT-WEB-NEXT-STATIC`) has no server of its own, so its
DataSources run in the browser. When the provider is Firebase, the SDK holds the session
and the security rules are the boundary (`PLAT-WEB-NEXT-FIREBASE`). This guide covers the
other case: the browser calls the **project's own REST backend**, which signs a user in
and returns **bearer tokens** (a short-lived access token and a refresh token).

It is `PLAT-WEB-HTTP`'s shape (an executor, a header provider, error mapping, retry) and
`PLAT-MOB-HTTP`'s token handling (a header provider and a refresher behind the executor),
restated for a browser. What a browser changes:

- **The browser holds the tokens.** `PLAT-WEB-HTTP` reads a server-side session on every
  request; here the page itself keeps the tokens between requests, so storage, refresh and
  sign-out are this guide's concern.
- **Everything in the bundle is public** (`ARCH-WEB-APP-RUNTIME-02`). The backend enforces
  every access decision with the token; the client only reflects it.
- **The page and the backend are different origins**, so the backend's CORS configuration
  is part of the feature.

The layers are `ARCH-WEB-APP`'s, unchanged. The executor, header provider, session store
and refresher live in the top-level `data/` folder (`ARCH-WEB-APP-FEAT-DATA-01`), are
built by the composition (`ARCH-WEB-APP-COMPOSE-FACTORY-01`) and are reached by
DataSources only. A Hook or Component never sees a token.

```
Component → Hook → UseCase → {Entity}DataSource ──► HttpRequestExecutor ──► fetch
                                                     │  ├─ HeaderProvider (reads SessionStore)
                                                     │  └─ TokenRefresher (writes SessionStore)
Composition builds all of it; Hooks read the signed-in state through the composition.
```

## Executor and configuration

```rule
id: PLAT-WEB-HTTP-BROWSER-LIB-01
statement: Browser DataSources MUST call the backend only through one shared request executor built by the composition, and MUST NOT call `fetch` themselves.
type: hard
scope: structure
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-LIB-01 — Browser DataSources MUST call the backend only through one shared request executor built by the composition, and MUST NOT call `fetch` themselves.
```

The executor interface and `HttpResult` are `PLAT-WEB-HTTP`'s (`PLAT-WEB-HTTP-LIB-01`);
only its construction and its policies differ. Headers, the base URL, the access token, the
single refresh and the retry live in one place, so a DataSource is query construction,
parsing, mapping and error translation (`ARCH-WEB-APP-DS-RESPONSIBILITY-01`).

```typescript
// data/http/createBrowserExecutor.ts
export function createBrowserExecutor(deps: {
  baseUrl: string;
  headers: HeaderProvider;
  refresher: TokenRefresher;
  fetchFn?: typeof fetch;            // injected so the executor is tested with a fake
}): HttpRequestExecutor {
  const fetchFn = deps.fetchFn ?? ((input, init) => fetch(input, init));
  async function send<T>(path: string, init: RequestInit, auth: boolean, retried = false): Promise<HttpResult<T>> {
    let res: Response;
    try {
      res = await fetchFn(`${deps.baseUrl}${path}`, { ...init, headers: deps.headers.getHeaders(auth) });
    } catch {
      return { ok: false, status: 0, body: null };          // network failure -> `offline` in the mapping
    }
    if (res.status === 401 && auth && !retried && (await deps.refresher.refresh())) {
      return send<T>(path, init, auth, true);                // once, after the shared refresh
    }
    if (!res.ok) return { ok: false, status: res.status, body: await safeJson(res) };
    return { ok: true, status: res.status, data: (res.status === 204 ? undefined : await res.json()) as T };
  }
  // getJson / postJson / patchJson / deleteJson call send(path, init, auth)
}
```

```rule
id: PLAT-WEB-HTTP-BROWSER-CONFIG-01
statement: The backend base URL and any client identifier header the backend requires MUST come from build-time public configuration read by the composition's `loadConfig`, MUST be treated as public identification and never as a secret or as access control, and a build MUST target exactly one backend environment.
type: hard
scope: behavior
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-CONFIG-01 — The backend base URL and any client identifier header MUST come from build-time public configuration read by `loadConfig`, MUST be treated as public identification, never as a secret or access control, and a build MUST target exactly one backend environment.
```

This is `ARCH-WEB-APP-COMPOSE-CONFIG-01` and `PLAT-WEB-NEXT-STATIC-ENV-01` applied to a
REST backend: `NEXT_PUBLIC_*` values are inlined into the bundle, so anyone can read them,
and an artifact built for the development backend and deployed to production talks to
development without an error. A required value that is missing fails `loadConfig` with a
message naming it; it is never replaced by a default that points at another environment.

## The session

```rule
id: PLAT-WEB-HTTP-BROWSER-SESSION-01
statement: The tokens MUST be owned by one session store created by the composition; only the header provider, the token refresher and the auth DataSource MAY read or write it, and Hooks MUST learn the signed-in state through a subscription the composition exposes, never by reading a token.
type: hard
scope: structure
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-SESSION-01 — The tokens MUST be owned by one session store created by the composition; only the header provider, the token refresher and the auth DataSource MAY read or write it, and Hooks MUST learn the signed-in state through a composition subscription, never by reading a token.
```

One owner of auth state, the rule `PLAT-WEB-FB-AUTH-01` sets for Firebase, here without an
SDK to be that owner. The store exposes `get()`, `set(tokens)`, `clear()` and
`subscribe(listener)` returning an unsubscribe function (`ARCH-WEB-APP-DS-RETURN-02`); the
signed-in state a Hook sees is derived from it (signed in, signed out), never the token.

```rule
id: PLAT-WEB-HTTP-BROWSER-STORE-01
statement: Tokens MUST be kept in memory and MAY be mirrored to `sessionStorage` so a reload in the same tab keeps the session; they MUST NOT be written to `localStorage`, IndexedDB, a cookie set by script, a URL, a log or an analytics event.
type: hard
scope: behavior
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-STORE-01 — Tokens MUST be kept in memory and MAY be mirrored to `sessionStorage`; they MUST NOT be written to `localStorage`, IndexedDB, a cookie set by script, a URL, a log or an analytics event.
```

Any script on the page can read every one of these places, so none is safe from a
cross-site scripting bug; the choice limits **how long** a stolen token stays usable.
`sessionStorage` is cleared when the tab closes and is not shared between tabs, so a
signed-in tab does not leave a session behind on a shared school computer. A project that
needs a session to outlive the tab records the reason and the extra exposure in its own
policy; a cookie the backend sets as `HttpOnly` is a backend design, outside this guide.
Reading `sessionStorage` happens only in the browser, after hydration
(`PLAT-WEB-NEXT-STATIC-BROWSER-01`); the store starts signed out during the build. Logs
and error reports redact tokens with everything else (`ARCH-WEB-APP-OBS-REDACT-01`).

## Attaching and refreshing tokens

```rule
id: PLAT-WEB-HTTP-BROWSER-AUTH-01
statement: The executor MUST attach the access token through an injected header provider that reads the session store, a call MUST say whether it needs authentication, and a DataSource MUST NOT read, pass or store a token itself.
type: hard
scope: behavior
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-AUTH-01 — The executor MUST attach the access token through an injected header provider that reads the session store, a call MUST say whether it needs authentication, and a DataSource MUST NOT read, pass or store a token itself.
```

`PLAT-MOB-HTTP-AUTH-01` for the browser. Sign-in, registration and password-reset calls are
unauthenticated; sending a stale token to them invites a confusing 401.

```rule
id: PLAT-WEB-HTTP-BROWSER-REFRESH-01
statement: On a 401 from an authenticated call the executor MUST run one shared refresh for every request waiting on it, MUST retry each original request once after a successful refresh, and MUST clear the session and return the 401 when the refresh fails; the refresh call itself MUST NOT trigger a refresh.
type: hard
scope: behavior
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-REFRESH-01 — On a 401 from an authenticated call the executor MUST run one shared refresh for every request waiting on it, MUST retry each original request once after a successful refresh, and MUST clear the session and return the 401 when the refresh fails; the refresh call itself MUST NOT trigger a refresh.
```

`PLAT-MOB-HTTP-AUTH-02` for the browser. A screen that loads three things at once gets
three 401s when the access token expires; three separate refreshes race, and with a
rotating refresh token (below) the second and third present a token the first already
spent, so the user is signed out for no reason. The refresher holds the in-flight promise
and hands it to every caller until it settles:

```typescript
export function createTokenRefresher(deps: { store: SessionStore; refreshCall: RefreshCall }): TokenRefresher {
  let inFlight: Promise<boolean> | null = null;
  return {
    refresh() {
      inFlight ??= run().finally(() => { inFlight = null; });
      return inFlight;
    },
  };
  async function run(): Promise<boolean> {
    const current = deps.store.get();
    if (!current) return false;
    const result = await deps.refreshCall(current.refreshToken);   // unauthenticated, never refreshes itself
    if (!result.ok) {
      if (result.status === 400 || result.status === 401) deps.store.clear();  // token rejected: signed out
      return false;                                                // offline or 5xx: keep the session, fail this call
    }
    deps.store.set(result.tokens);
    return true;
  }
}
```

Only a refresh token the backend **rejected** ends the session. A refresh that failed
because the network dropped or the backend returned a 5xx or a 429 leaves the session in
place and fails the current call, so a flaky connection does not sign the user out (the
same distinction `ARCH-WEB-APP-EFLOW-NETWORK-01` draws for presentation).

```rule
id: PLAT-WEB-HTTP-BROWSER-REFRESH-02
statement: When the backend returns a new refresh token with each refresh, the session store MUST replace the access and refresh tokens together in one write, and the old refresh token MUST NOT be used again.
type: hard
scope: behavior
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-REFRESH-02 — When the backend returns a new refresh token with each refresh, the session store MUST replace the access and refresh tokens together in one write, and the old refresh token MUST NOT be used again.
```

A store that writes the access token and the refresh token separately can be read between
the writes, or survive a reload with a pair the backend no longer recognises.

## Signing out

```rule
id: PLAT-WEB-HTTP-BROWSER-SIGNOUT-01
statement: Signing out MUST clear the session store and its storage mirror whether or not the backend's logout call succeeds, and SHOULD call that logout endpoint first so the backend can revoke the refresh token.
type: hard
scope: behavior
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-SIGNOUT-01 — Signing out MUST clear the session store and its storage mirror whether or not the backend's logout call succeeds, and SHOULD call the logout endpoint first so the backend can revoke the refresh token.
```

A failed logout call (offline, already expired) is not an error the user can act on; the
local session is what the user asked to end, so it always ends.

## Errors

```rule
id: PLAT-WEB-HTTP-BROWSER-ERR-01
statement: A backend error body MUST be parsed and mapped to an `AppError` in the DataSource, the backend's error codes MUST be named constants in one module beside the DataSources, and a Hook or Component MUST NOT compare a raw status or error code.
type: hard
scope: error-handling
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-ERR-01 — A backend error body MUST be parsed and mapped to an `AppError` in the DataSource, the backend's error codes MUST be named constants in one module beside the DataSources, and a Hook or Component MUST NOT compare a raw status or error code.
```

`PLAT-WEB-HTTP-ERR-01` and `ARCH-WEB-APP-ERR-MAP-01` with the backend's own vocabulary.
A REST backend usually answers with a body such as `{ code, message }`; the DataSource
parses it (`ARCH-WEB-APP-DS-PARSE-01`), then maps:

| Backend answer | `AppError` |
|---|---|
| Network failure (status 0) | `offline` |
| 401 after the refresh | `unauthorized` |
| 403 | `forbidden` |
| 404 on an identity that must exist | `notFound` |
| A code that names a field (e.g. "email already registered", "password too short") | `validation` with that field |
| Anything else, including an unparseable body | `unexpected`, logged once (`ARCH-WEB-APP-ERR-UNKNOWN-01`) |

The `message` the backend sends is for its developers; the wording the user sees comes
from the presentation module (`ARCH-WEB-APP-EFLOW-PRESENT-01`). When a screen needs to act
on a code that has no `AppError` variant (for example "this email is already registered:
offer sign-in instead"), the DataSource maps it to `validation` on the field it concerns
with a stable key, and the Hook decides what to offer from that key.

## Access and origins

```rule
id: PLAT-WEB-HTTP-BROWSER-GUARD-01
statement: A client-side check of the signed-in state MUST only decide what the screen shows, every protected read and write MUST be an authenticated backend call the backend authorises, and the static build MUST NOT contain protected data.
type: hard
scope: behavior
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-GUARD-01 — A client-side check of the signed-in state MUST only decide what the screen shows, every protected read and write MUST be an authenticated backend call the backend authorises, and the static build MUST NOT contain protected data.
```

`ARCH-WEB-APP-RUNTIME-02` with a REST backend as the provider: the backend's own
authorisation of the token is the access boundary. A signed-out visitor who opens the
page sees the sign-in form because the Hook says so, and gets nothing else because there
is nothing else in the HTML.

```rule
id: PLAT-WEB-HTTP-BROWSER-CORS-01
statement: Every origin a build is deployed to MUST be in the allowed origins of the backend environment that build targets before the deploy, and a plan that adds a deployed origin or calls a backend path with a new method or header MUST include the backend change.
type: hard
scope: structure
evidence: unproven
enforced_by: [planner, reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-CORS-01 — Every origin a build is deployed to MUST be in the allowed origins of the backend environment that build targets before the deploy, and a plan that adds a deployed origin or a new method or header MUST include the backend change.
```

A CORS rejection shows in the browser as a network failure (`offline`) with no response to
inspect, and only in a deployed build: local development usually runs on an origin the
backend already allows. With bearer tokens in a header and no cookies, the backend does
not need to allow credentials, and should not.

## Testing

```rule
id: PLAT-WEB-HTTP-BROWSER-TEST-01
statement: The executor, the refresher and the session store MUST be tested with an injected fake `fetch` and an in-memory storage, covering at least: the header on authenticated calls only, two concurrent 401s sharing one refresh, a rejected refresh clearing the session, a network failure during refresh keeping it, the rotated pair replacing the old one, and sign-out clearing the session when the logout call fails.
type: hard
scope: testing
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-TEST-01 — The executor, the refresher and the session store MUST be tested with an injected fake `fetch` and an in-memory storage, covering the header on authenticated calls only, two concurrent 401s sharing one refresh, a rejected refresh clearing the session, a network failure during refresh keeping it, the rotated pair replacing the old one, and sign-out clearing the session when logout fails.
```

These are the failures no manual test reliably finds: a token expiring during a burst of
requests, or a refresh racing a reload. They are plain TypeScript with no React, so they
run under the project's ordinary unit-test runner. DataSources above the executor are
tested against a fake `HttpRequestExecutor` (`ARCH-WEB-APP-TEST-01`, `QG-WEB-TESTING`).

## Violations

- A Hook reading `sessionStorage` to decide whether the user is signed in
- A DataSource adding `Authorization` itself, or catching a 401 and refreshing on its own
- Three parallel requests producing three refresh calls
- A network blip during refresh signing the user out
- Tokens in `localStorage`, a query string or an error report
- A production deploy whose bundle points at the development backend
- A new deployed origin that the backend's CORS list was never told about
