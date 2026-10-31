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

| Rule | Result | Note |
|---|---|---|
| `PLAT-WEB-HTTP-BROWSER-LIB-01` | | |
| `PLAT-WEB-HTTP-BROWSER-CONFIG-01` | | |
| `PLAT-WEB-HTTP-BROWSER-SESSION-01` | | |
| `PLAT-WEB-HTTP-BROWSER-STORE-01` | | |
| `PLAT-WEB-HTTP-BROWSER-AUTH-01` | | |
| `PLAT-WEB-HTTP-BROWSER-REFRESH-01` | | |
| `PLAT-WEB-HTTP-BROWSER-REFRESH-02` | | |
| `PLAT-WEB-HTTP-BROWSER-SIGNOUT-01` | | |
| `PLAT-WEB-HTTP-BROWSER-ERR-01` | | |
| `PLAT-WEB-HTTP-BROWSER-GUARD-01` | | |
| `PLAT-WEB-HTTP-BROWSER-CORS-01` | | |
| `PLAT-WEB-HTTP-BROWSER-TEST-01` | | |
| `ARCH-WEB-APP-FEAT-CONTENT-01` | | |
