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
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-LIB-01 — Browser DataSources MUST call the backend only through one shared request executor built by the composition, and MUST NOT call `fetch` themselves.
```

The executor's shape is `PLAT-WEB-HTTP`'s (`PLAT-WEB-HTTP-LIB-01`) with two differences a browser
needs: a success carries `data: unknown`, never a generic `T` behind a cast, because the DataSource parses
it (`ARCH-WEB-APP-DS-PARSE-01`, `ARCH-WEB-APP-EFLOW-ASSERT-01`); and a failure says whether it was an abort,
so a cancelled request does not look like a lost connection. A call passes `{ auth, signal }`. Headers, the base URL, the access token, the
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
  async function send(path: string, init: RequestInit, options: RequestOptions, retried = false): Promise<HttpResult> {
    const headers = deps.headers.getHeaders(options.auth);
    let res: Response;
    try {
      res = await fetchFn(`${deps.baseUrl}${path}`, { ...init, headers, signal: options.signal });
    } catch (cause) {
      // No response: an abort stays an abort (ARCH-WEB-APP-ERR-CANCEL-01); anything else is `offline`.
      return { ok: false, status: 0, body: null, aborted: isAbort(cause) };
    }
    if (res.status === 401 && options.auth && !retried) {
      const refresh = await deps.refresher.refresh(headers.Authorization?.replace(/^Bearer /, '')); // the token it carried
      if (refresh === 'refreshed') return send(path, init, options, true);   // once, after the shared refresh
      if (refresh === 'unavailable') return { ok: false, status: 0, body: null }; // session kept, call fails as offline
      // 'rejected': the refresher cleared the session; the 401 reaches the DataSource
    }
    const body = await safeJson(res);                        // `unknown`: the DataSource parses it
    return res.ok ? { ok: true, status: res.status, data: body } : { ok: false, status: res.status, body };
  }
  // getJson / postJson / patchJson / deleteJson call send(path, init, options)
}
```

```rule
id: PLAT-WEB-HTTP-BROWSER-CONFIG-01
statement: The backend base URL and any client identifier header the backend requires MUST come from build-time public configuration read by the composition's `loadConfig`, MUST be treated as public identification and never as a secret or as access control, and a build MUST target exactly one backend environment.
type: hard
scope: behavior
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-CONFIG-01 — The backend base URL and any client identifier header MUST come from build-time public configuration read by `loadConfig`, MUST be treated as public identification, never as a secret or access control, and a build MUST target exactly one backend environment.
```

This is `ARCH-WEB-APP-COMPOSE-CONFIG-01` and `PLAT-WEB-NEXT-STATIC-ENV-01` applied to a
REST backend: `NEXT_PUBLIC_*` values are inlined into the bundle, so anyone can read them,
and an artifact built for the development backend and deployed to production talks to
development without an error. A required value that is missing fails `loadConfig` with a
message naming it. A default backend URL is allowed only when the project has exactly one deployed
environment and the default is that environment, recorded beside the default; then a build for any other
environment must set the URL, and its deploy step checks it did. With two deploy targets there is no default.

## The session

```rule
id: PLAT-WEB-HTTP-BROWSER-SESSION-01
statement: The tokens MUST be owned by one session store created by the composition; only the header provider, the token refresher and the auth DataSource MAY read or write it, and Hooks MUST learn the signed-in state through a subscription the composition exposes, never by reading a token.
type: hard
scope: structure
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-SESSION-01 — The tokens MUST be owned by one session store created by the composition; only the header provider, the token refresher and the auth DataSource MAY read or write it, and Hooks MUST learn the signed-in state through a composition subscription, never by reading a token.
```

One owner of auth state, the rule `PLAT-WEB-FB-AUTH-01` sets for Firebase, here without an
SDK to be that owner. The store exposes `get()`, `set(tokens)`, `clear()` and
`subscribe(listener)` returning an unsubscribe function (`ARCH-WEB-APP-DS-RETURN-02`), plus `restore()`,
which reads the storage mirror once. The store starts signed out (it is built during the prerender, too),
so `restore()` runs in the browser, from the first subscription to the signed-in state, which a Hook
makes in an effect. The signed-in state a Hook sees is derived from the store (signed in, signed out,
and identity fields such as the user id), never a token; the auth DataSource exposes it as a subscription.

```rule
id: PLAT-WEB-HTTP-BROWSER-STORE-01
statement: Tokens MUST be kept in memory and MAY be mirrored to `sessionStorage`; the refresh token MAY be persisted to `localStorage` only when the user chose to stay signed in on that device, the backend rotates refresh tokens and refuses a reused one, and the page is served with a Content Security Policy that limits script and connect origins; the access token MUST NOT be persisted beyond the tab, and no token MUST be written to IndexedDB, a cookie set by script, a URL, a log or an analytics event.
type: hard
scope: behavior
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-STORE-01 — Tokens live in memory, optionally mirrored to `sessionStorage`; only the refresh token, only with the user's "stay signed in" choice, rotation with reuse detection and a CSP, may go to `localStorage`; never the access token there, and no token in IndexedDB, a script cookie, a URL, a log or analytics.
```

Any script on the page can read every one of these places, so none is safe from a
cross-site scripting bug; the choice limits **how long** a stolen token stays usable.
`sessionStorage` is cleared when the tab closes and is not shared between tabs, so a
signed-in tab does not leave a session behind on a shared school computer. The mirror may also hold the
identity the page shows after a reload (user id, the email signed in with), and nothing more.

**Staying signed in.** A session that ends with the tab makes a home-screen shortcut useless, so a
project may offer "Keep me signed in on this device". Then the refresh token (and the displayed identity)
goes to `localStorage`; the access token stays in memory and is fetched again with the refresh token after
a reload. Three conditions make that acceptable, and the statement requires all three: the user chose it
(default ticked is fine; a shared computer unticks it), the backend rotates the refresh token and refuses
a rotated-away one (`REFRESH-02`), so a stolen token stops working at the owner's next refresh, and a CSP
whose `script-src` and `connect-src` list only the origins the site needs, which makes it much harder to
inject a script and to send a token anywhere. A static export usually needs `'unsafe-inline'` in
`script-src` for the framework's inline bootstrap; `connect-src` is then the part that limits
exfiltration. An analytics or collection origin in `connect-src` (Google Analytics accepts hits for any
measurement ID) is still a channel out, so list only what the site needs and record the residual risk.
Check the policy under the real header, in the host's emulator, on every route, with zero violations:
`next dev` does not apply it, and some libraries probe `eval` at load (zod builds parsers with `new Function`
unless configured jitless) and are reported only under the header. Unticked, the session is exactly the `sessionStorage` one above. Persisted tokens are shared
by every tab, which needs `PLAT-WEB-HTTP-BROWSER-REFRESH-03`. A refresh cookie the backend sets as
`HttpOnly` is safer still, but it needs the API on the site's own registrable domain (browsers block
cross-site cookies) and CSRF protection: a backend design, outside this guide.
Reading `sessionStorage` happens only in the browser, after hydration
(`PLAT-WEB-NEXT-STATIC-BROWSER-01`); the store starts signed out during the build. Logs
and error reports redact tokens with everything else (`ARCH-WEB-APP-OBS-REDACT-01`).

## Attaching and refreshing tokens

```rule
id: PLAT-WEB-HTTP-BROWSER-AUTH-01
statement: The executor MUST attach the access token through an injected header provider that reads the session store, a call MUST say whether it needs authentication, and a DataSource MUST NOT read, pass or store a token, except the auth DataSource, which MAY store the tokens a sign-in returns and send the refresh token to logout.
type: hard
scope: behavior
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-AUTH-01 — The executor MUST attach the access token through an injected header provider that reads the session store, a call MUST say whether it needs authentication, and only the auth DataSource MAY handle a token, to store a sign-in's tokens and to send the refresh token to logout.
```

`PLAT-MOB-HTTP-AUTH-01` for the browser. Sign-in, registration and password-reset calls are
unauthenticated; sending a stale token to them invites a confusing 401.

```rule
id: PLAT-WEB-HTTP-BROWSER-REFRESH-01
statement: On a 401 from an authenticated call the executor MUST run one shared refresh for every request waiting on it and MUST retry each original request once after it succeeds; when the backend rejects the refresh token the session MUST be cleared and the 401 returned, when the refresh cannot reach the backend the session MUST be kept and the call fail as offline, a 401 for a request sent with an access token the session has since replaced MUST be retried with the current token without a refresh, and the refresh and logout calls MUST NOT trigger a refresh.
type: hard
scope: behavior
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-REFRESH-01 — On a 401 from an authenticated call the executor MUST run one shared refresh for every waiting request and retry each once after it succeeds; a rejected refresh token clears the session and returns the 401, an unreachable backend keeps the session and fails the call as offline, a 401 sent with a since-replaced token retries without a refresh, and refresh and logout calls MUST NOT trigger a refresh.
```

`PLAT-MOB-HTTP-AUTH-02` for the browser. A screen that loads three things at once gets
three 401s when the access token expires; three separate refreshes race, and with a
rotating refresh token (below) the second and third present a token the first already
spent, so the user is signed out for no reason. The refresher holds the in-flight promise
and hands it to every caller until it settles:

```typescript
export type RefreshOutcome = 'refreshed' | 'rejected' | 'unavailable';

export function createTokenRefresher(deps: { store: SessionStore; refreshCall: RefreshCall }): TokenRefresher {
  let inFlight: Promise<RefreshOutcome> | null = null;
  return {
    refresh(sentAccessToken) {
      const current = deps.store.get();
      // Another call's refresh already replaced the token this request carried: retry, do not refresh again.
      if (!inFlight && current && sentAccessToken !== undefined && current.accessToken !== sentAccessToken) {
        return Promise.resolve('refreshed');
      }
      inFlight ??= run().finally(() => { inFlight = null; });
      return inFlight;
    },
  };
  async function run(): Promise<RefreshOutcome> {
    const current = deps.store.get();
    if (!current) return 'rejected';
    const result = await deps.refreshCall(current.refreshToken);   // unauthenticated, never refreshes itself
    if (deps.store.get() !== current) return 'rejected';           // signed out or in again meanwhile: discard
    if (!result.ok) {
      if (result.rejected) deps.store.clear();                     // token refused: signed out
      return result.rejected ? 'rejected' : 'unavailable';         // offline, 5xx, 429: keep the session
    }
    deps.store.set({ ...current, ...result.tokens });               // the pair, in one write (REFRESH-02)
    return 'refreshed';
  }
}
```

Only a refresh token the backend **rejected** ends the session. A refresh that failed
because the network dropped or the backend returned a 5xx or a 429 leaves the session in
place and fails the current call, so a flaky connection does not sign the user out (the
same distinction `ARCH-WEB-APP-EFLOW-NETWORK-01` draws for presentation). "Rejected" is decided from the
backend's answer to the refresh call (a 400 or 401, or its refresh-token error codes), never from the
original call's 401. A refresh that settles after the user signed out, or signed in again, belongs to
nobody and is discarded.

A request that was sent with an access token the session has since replaced (another call's refresh
finished while it was in flight) retries with the current token instead of starting a second refresh. The
single-flight promise alone does not cover it: it only joins 401s that arrive while a refresh is running,
and a slow response arrives after. The executor passes the token the request carried to the refresher,
which answers "refreshed" at once when the session already holds a newer one. Without this, every
refresh during a burst of slow requests rotates the refresh token again, and with reuse detection on the
backend that can end the session (found by the `ampm-website` pilot on a real backend).

```rule
id: PLAT-WEB-HTTP-BROWSER-REFRESH-02
statement: When the backend returns a new refresh token with each refresh, the session store MUST replace the access and refresh tokens together in one write, and the old refresh token MUST NOT be used again.
type: hard
scope: behavior
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-REFRESH-02 — When the backend returns a new refresh token with each refresh, the session store MUST replace the access and refresh tokens together in one write, and the old refresh token MUST NOT be used again.
```

A store that writes the access token and the refresh token separately can be read between
the writes, or survive a reload with a pair the backend no longer recognises.

```rule
id: PLAT-WEB-HTTP-BROWSER-REFRESH-03
statement: When the refresh token is persisted where several tabs share it, a refresh MUST be serialised across tabs, each tab MUST re-read the stored refresh token before and after its refresh call and refresh only with the latest one, a tab MUST pick up a refresh token or a sign-out written by another tab, and a refresh rejected for a token the store has since replaced MUST NOT clear the session.
type: hard
scope: behavior
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-REFRESH-03 — With a refresh token shared between tabs, refresh MUST be serialised across tabs and always use the latest stored token (re-read before and after the call), tabs pick up each other's token and sign-out, and a rejection for an already-replaced token MUST NOT clear the session.
```

The single-flight promise of `REFRESH-01` lives in one tab. Two tabs that each refresh with the same
stored refresh token race: the second presents a token the first already rotated away, the backend refuses
it, and if that tab then clears the store it signs the user out of every tab. The Web Locks API
(`navigator.locks.request('<app>-refresh', …)`) serialises the refresh across tabs of one origin; inside
the lock the tab reads the stored refresh token again and adopts it when it differs from the one it holds
("newer" is simply "different": every write a tab sees comes after the one it holds). Only the refresh token
is shared (`STORE-01` keeps the access token out of storage), so a tab that adopted a newer refresh token
still needs an access token: it refreshes once more with the adopted token, which is safe because no token
is presented twice. Two tabs whose access tokens expire together therefore make two serialised refreshes,
not one; the test is "no refresh token presented twice, nobody signed out". Re-read after the call as well:
a sign-out, or a new sign-in, may have arrived meanwhile, and then the result belongs to nobody. A `storage`
event delivers another tab's write (a new refresh token, a new kept sign-in, or the removal that means signed
out) to the session store, which notifies its subscribers; a tab with a session-only sign-in keeps its own
token and ignores them.

The store needs two ways to end a session: sign-out (`SIGNOUT-01`, every mirror, every tab) and a refused
refresh, which ends the session only while the store still holds the refused token, and clears the shared
record only when that record holds it, so a session-only tab's dead token cannot sign out a kept session.
When `localStorage` cannot be read, that says nothing about other tabs (do not treat it as signed out); when
it cannot be written, the sign-in falls back to session-only.

Where Web Locks is missing, re-reading before and after the call is the fallback. It still lets two tabs
present the same token now and then, which is safe only if the backend refuses just the reused token; a
backend that revokes the whole token family on reuse signs both tabs out, so check the backend's policy
before relying on the fallback.

## Signing out

```rule
id: PLAT-WEB-HTTP-BROWSER-SIGNOUT-01
statement: Signing out MUST clear the session store and every storage mirror (the persisted one too, which signs out every tab) whether or not the backend's logout call succeeds, and SHOULD call that logout endpoint first so the backend can revoke the refresh token.
type: hard
scope: behavior
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-SIGNOUT-01 — Signing out MUST clear the session store and its storage mirror whether or not the backend's logout call succeeds, and SHOULD call the logout endpoint first so the backend can revoke the refresh token.
```

A failed logout call (offline, already expired) is not an error the user can act on; the
local session is what the user asked to end, so it always ends. Logout carries the refresh token in its
body and is sent unauthenticated, so a 401 from it never starts a refresh (`PLAT-WEB-HTTP-BROWSER-REFRESH-01`).

## Errors

```rule
id: PLAT-WEB-HTTP-BROWSER-ERR-01
statement: A backend error body MUST be parsed and mapped to an `AppError` in the DataSource, the backend's error codes MUST be named constants in one module beside the DataSources, and a Hook or Component MUST NOT compare a raw status or error code.
type: hard
scope: error-handling
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-ERR-01 — A backend error body MUST be parsed and mapped to an `AppError` in the DataSource, the backend's error codes MUST be named constants in one module beside the DataSources, and a Hook or Component MUST NOT compare a raw status or error code.
```

`PLAT-WEB-HTTP-ERR-01` and `ARCH-WEB-APP-ERR-MAP-01` with the backend's own vocabulary.
A REST backend usually answers with a body such as `{ code, message }`; the DataSource
parses it (`ARCH-WEB-APP-DS-PARSE-01`), then maps:

| Backend answer | `AppError` |
|---|---|
| Aborted by the caller | `cancelled` |
| Network failure (status 0) | `offline` |
| 401 after the refresh | `unauthorized` |
| 403 | `forbidden` |
| 404 on an identity that must exist | `notFound` |
| 429, or the backend's rate-limit code | `rateLimited` |
| A code that names a field (e.g. "email already registered", "password too short") | `validation` with that field |
| Anything else, including an unparseable body | `unexpected`, logged once (`ARCH-WEB-APP-ERR-UNKNOWN-01`) |

A call's own codes are checked before the table: "invalid credentials" on a sign-in is a 401 that
means "wrong password", not "session ended", so the sign-in DataSource maps it first.

The `message` the backend sends is for its developers; the wording the user sees comes
from the presentation module (`ARCH-WEB-APP-EFLOW-PRESENT-01`). When a screen needs to act
on a code that has no `AppError` variant (for example "this email is already registered:
offer sign-in instead"), the DataSource maps it to `validation` with a stable key, on the field
it concerns or, for a code about the whole form such as invalid credentials, on a named form-level
key. The Hook turns those feature keys into a small presentation union of its own (for example
`{ kind: 'alreadyRegistered' }`), because a Component may not import the domain's keys
(`ARCH-WEB-APP-DEP-05`); every other error reaches the Component as the full `AppError`
(`ARCH-WEB-APP-HOOK-ERROR-01`).

## Access and origins

```rule
id: PLAT-WEB-HTTP-BROWSER-GUARD-01
statement: A client-side check of the signed-in state MUST only decide what the screen shows, every protected read and write MUST be an authenticated backend call the backend authorises, and the static build MUST NOT contain protected data.
type: hard
scope: behavior
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-GUARD-01 — A client-side check of the signed-in state MUST only decide what the screen shows, every protected read and write MUST be an authenticated backend call the backend authorises, and the static build MUST NOT contain protected data.
```

`ARCH-WEB-APP-RUNTIME-02` with a REST backend as the provider: the backend's own
authorisation of the token is the access boundary. A signed-out visitor who opens the
page sees the sign-in form because the Hook says so, and gets nothing else because there
is nothing else in the HTML.

```rule
id: PLAT-WEB-HTTP-BROWSER-CORS-01
statement: Every origin the host serves a build from, including the host's default domains, MUST be in the allowed origins of the backend environment that build targets before the deploy, or the plan MUST record which of those origins are left unsupported, and a plan that adds an origin or calls a backend path with a new method or header MUST include the backend change.
type: hard
scope: structure
evidence: exercised
enforced_by: [planner, reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-CORS-01 — Every origin the host serves a build from, including its default domains, MUST be allowed by the targeted backend before the deploy or recorded as unsupported, and a plan that adds an origin or a new method or header MUST include the backend change.
```

A CORS rejection shows in the browser as a network failure (`offline`) with no response to
inspect, and only in a deployed build: local development usually runs on an origin the
backend already allows. Hosts serve the same files from more than one origin (Firebase Hosting also
serves `<project>.web.app` and `<project>.firebaseapp.com`); a visitor on one the backend does not allow
sees a page that cannot sign in. With bearer tokens in a header and no cookies, the backend does
not need to allow credentials, and should not.

## Testing

```rule
id: PLAT-WEB-HTTP-BROWSER-TEST-01
statement: The executor, the refresher and the session store MUST be tested with an injected fake `fetch` and an in-memory storage, covering at least: the header on authenticated calls only, two concurrent 401s sharing one refresh, a 401 that arrives after another call's refresh finished retrying without a second refresh, a rejected refresh clearing the session, a network failure during refresh keeping it, the rotated pair replacing the old one, and sign-out clearing the session when the logout call fails.
type: hard
scope: testing
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-HTTP-BROWSER-TEST-01 — The executor, the refresher and the session store MUST be tested with an injected fake `fetch` and an in-memory storage, covering the header on authenticated calls only, two concurrent 401s sharing one refresh, a late 401 retrying without a second refresh, a rejected refresh clearing the session, a network failure during refresh keeping it, the rotated pair replacing the old one, and sign-out clearing the session when logout fails.
```

These are the failures no manual test reliably finds: a token expiring during a burst of
requests, or a refresh racing a reload. The refresher alone may be tested against a fake refresh call, as
long as the executor's tests cover the refresh over a fake `fetch`; the sign-out case is tested at the auth
DataSource, which owns sign-out. They are plain TypeScript with no React, so they
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
