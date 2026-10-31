# Web-app on its own REST backend from a static export: rules and pilot

Branch `web-browser-rest-runtime`. Started 2026-10-31.

## Why

`ampm-website` (Next.js static export on Firebase Hosting) needed a sign-up page that calls the
project's own Spring backend with bearer tokens. The framework had no coverage for it:

- `PLAT-WEB-HTTP` covered only server-side calls and deliberately had no token refresh.
- `runtime: static-export` always brought `PLAT-WEB-NEXT-FIREBASE`, as if a static export meant Firebase.
- Profile values were not platform-aware: `cloud: firebase` brought only the mobile guide, so a web
  project could not select its own Firebase guide by that key at all.
- A site that is mostly content pages plus one interactive feature had to choose between
  `web-content` (no auth, no client data) and `web-app` (every route composes a feature).

## What changed

- Tooling: optional document field `runtime` (`schemas/document.yaml` 1.4); `tools/lookup.py`
  drops profile-selected documents whose `platform` or `runtime` does not match the profile
  (`applicable_extra_docs`); `profile-doc-map.json` gains an `applicability` section so esc-exec
  filters the same way; `validate.py` checks the field.
- Maps: `network: fetch|axios` names `PLAT-WEB-HTTP` and `PLAT-WEB-HTTP-BROWSER`; `cloud: firebase`
  names `PLAT-MOB-FIREBASE` and `PLAT-WEB-NEXT-FIREBASE`; `runtime: static-export` names only
  `PLAT-WEB-NEXT-STATIC` (`schemas/project-profile.yaml` 1.5).
- `runtime` declared on `PLAT-WEB-HTTP`, `PLAT-WEB-NEXT-APP`, `-APP-DEPLOY`, `-DATA` (server) and
  `PLAT-WEB-NEXT-STATIC`, `PLAT-WEB-HTTP-BROWSER` (static-export).
- New `platforms/web/http-browser.md` (`PLAT-WEB-HTTP-BROWSER`), 12 rules, all `unproven`.
- New `ARCH-WEB-APP-FEAT-CONTENT-01` (content-only routes in a web-app follow `ARCH-WEB-CONTENT`).
- Prose: `ARCH-WEB-APP-RUNTIME-02` names a REST backend's token check as the boundary; the
  `PLAT-WEB-HTTP` scope points to the browser guide; `ORCH-WEB-APP` Phase 0 and the DataSource phase
  name the browser guide.

Migration note: a `static-export` project on Firebase must now declare `cloud: firebase` to keep
`PLAT-WEB-NEXT-FIREBASE` in its profile set. No local project declared `frameworks.runtime` when
this changed.

## Pilot

`ampm-website` `/sign-up` (BLA-92 follow-up): register or sign in, accept the competition rules,
see the referral code, link, count and rank. Record here, rule by rule, whether it was applied as
written, changed, or not exercised, then set `evidence: exercised` on the rules that held.

| Rule | Result in the slice | Changed in the guide after the slice |
|---|---|---|
| `PLAT-WEB-HTTP-BROWSER-LIB-01` | Applied; sketch deviated | Sketch: `data: unknown` (no `as T`), a failure flags `aborted`, `{ auth, signal }` options |
| `PLAT-WEB-HTTP-BROWSER-CONFIG-01` | Applied | Prose: a default URL only for a single deployed environment, recorded |
| `PLAT-WEB-HTTP-BROWSER-SESSION-01` | Applied; restore step unclear | Prose: `restore()` runs from the first subscription, in an effect; identity fields may be exposed |
| `PLAT-WEB-HTTP-BROWSER-STORE-01` | Applied | Prose: the mirror may hold the displayed identity (user id, email), nothing more |
| `PLAT-WEB-HTTP-BROWSER-AUTH-01` | Applied; conflicted with SESSION-01 | Statement: the auth DataSource may store sign-in tokens and send the refresh token to logout |
| `PLAT-WEB-HTTP-BROWSER-REFRESH-01` | Applied with three outcomes; statement and prose disagreed | Statement: rejected clears and returns 401, unreachable keeps the session and fails as offline, refresh and logout never refresh. Prose: discard a refresh that settles after sign-out; retry with the current token instead of a second refresh |
| `PLAT-WEB-HTTP-BROWSER-REFRESH-02` | Applied | none |
| `PLAT-WEB-HTTP-BROWSER-SIGNOUT-01` | Applied | Prose: logout is unauthenticated and never refreshes |
| `PLAT-WEB-HTTP-BROWSER-ERR-01` | Applied; union lacked 429 | `AppError` gains `rateLimited` and `cancelled` (ARCH-WEB-APP-ERR-CLASSES); per-call codes before the table; form-level keys; Hook maps keys to a presentation union |
| `PLAT-WEB-HTTP-BROWSER-GUARD-01` | Applied (prerendered HTML has only the signed-out shell) | none |
| `PLAT-WEB-HTTP-BROWSER-CORS-01` | Applied in the plan only; host default domains missed | Statement: every origin the host serves, including default domains, or record them unsupported |
| `PLAT-WEB-HTTP-BROWSER-TEST-01` | Applied | Prose: refresher alone may use a fake refresh call; sign-out tested at the auth DataSource |
| `ARCH-WEB-APP-FEAT-CONTENT-01` | Not exercised (no content-only route changed) | none |

Also changed from the slice: `PLAT-WEB-NEXT-STATIC` names `useSyncExternalStore` with a server snapshot as
the allowed way to read a browser value for the first render.

Slice: `ampm-website` branch `esc-ai-task-sign-up-page-ampm-website`, commit `3280c18` (run
`run-8e02ac92f2b64ff3bc1c7e8db790f447`). Gates passed: `npm test` (105), lint, static build, architecture
check (13 rules, 0 violations). The run's own notes are in that repo's
`.esc-ai/workflows/active/sign-up-page-ampm-website/README.md`.

**Live test, 2026-10-31, dev backend: passed.** Chrome DevTools (a second Claude session) ran 18 browser
steps against `localhost:3000` with the dev backend, and the Android emulator (dev build 2.6.0-dev01) ran
the two app steps: an account registered on the web signs in to the app with the same code, and a fresh
app user entering that code after a first lesson credits the web account (score 1, rank 17). Step 12 failed
first: a 401 that arrived 3 to 30 ms after another call's refresh finished started a second refresh (an
extra rotation, risky with reuse detection). Fixed in `ampm-website` `c9080d2` (the executor passes the
token it sent; the refresher skips the refresh when the session already holds a newer one), with a unit
test reproducing the timing. `REFRESH-01` and `TEST-01` now require it. Re-run on a normal network and
Slow 3G: one refresh each. All 12 `PLAT-WEB-HTTP-BROWSER` rules are now `evidence: exercised`;
`ARCH-WEB-APP-FEAT-CONTENT-01` stays `unproven` (needs a slice that changes a content-only route).

Open, not decided here: `QG-WEB-TESTING` DataSource contract tests (fake and real run the same suite) were
not written for the new DataSources, and the project has no fake `AccountDataSource`.

## Second slice: staying signed in (2026-10-31)

`STORE-01` now allows the refresh token in `localStorage` when the user opts in to "Keep me signed in",
the backend rotates with reuse detection, and a CSP limits script and connect origins; it is back to
`unproven` because the changed clause is untested. New `REFRESH-03` (unproven): with tokens shared by
tabs, refresh is serialised across tabs (Web Locks), each tab adopts a newer stored pair before
refreshing, tabs sync through `storage` events, and a rejection for an already-replaced token does not
sign out. `SIGNOUT-01` clears the persisted mirror too. Found while planning: `ampm-backend` refuses a
rotated-away refresh token once its successor was used (`AMPM-BE-AUTH-REFRESH-REUSE-01`), so without
`REFRESH-03` a background tab signs every tab out. Pilot: `ampm-website` task
`keep-signed-in-ampm-website`.

**Result, 2026-10-31.** Both slices passed a browser test against the dev backend.

- `keep-signed-in-ampm-website`: steps 1 to 9 pass, including five two-tab refresh races (normal network,
  Slow 3G, and a forced overlap with the lock held by a third tab) with no refresh token presented twice,
  no refresh refused and nobody signed out; sign-out in one tab signs out the other. The run found that
  `REFRESH-03` as first written assumed the access token travels with the stored pair; the statement now
  says "refresh with the latest stored refresh token", which is what was built and tested. Also added from
  the run: the residual risk of an analytics origin in `connect-src`, checking the CSP in the host emulator
  (zod's `new Function` probe showed up only there), the two ways a session ends (sign-out and a refused
  refresh), and the Web Locks fallback's dependence on the backend's reuse policy. `STORE-01` and
  `REFRESH-03` are now `evidence: exercised`.
- `refer-and-win-entry-points-ampm-website`: the home page (a content route) composes the competition
  banner feature. Clarified from the run: shared UI state is not feature state, the provider wraps the
  narrowest element (one graph per page), and an optional island may render nothing on failure.
  `ARCH-WEB-APP-FEAT-CONTENT-01` is now `evidence: exercised`.

## Third slice: error reporting to Sentry (2026-10-31)

`ampm-website` task `sentry-error-reporting-ampm-website`: `@sentry/browser` behind the logger, started from
`instrumentation-client.ts`, scrubbed in the send hooks, ingest host in the CSP, source maps uploaded and
removed before deploy. Live smoke test on askmoreprepmore.com: the first envelope kept a query inside the
exception message (fixed in `f4320aa`), the second was clean; the stored event showed a server-derived
location (a Sentry project setting, not client data). `ARCH-WEB-APP-OBS-REDACT-01` now names emails, user
ids and share codes and requires the reporter's send hooks and a real-payload check;
`ARCH-WEB-APP-EFLOW-LOG-01` allows one record in several sinks and names the global handler;
`ARCH-WEB-APP-EFLOW-BOUNDARY-01` says how a boundary above the composition gets the reporter;
`ARCH-WEB-APP-ERR-UNKNOWN-01` defines "full cause". The first three move to `evidence: exercised`.
Not yet reflected: `ARCH-WEB-APP-COMPOSE-CONFIG-01` and `-COMPOSE-GLOBAL-01` should name
`instrumentation-client` as a second, browser-only entry with a lighter parser.
