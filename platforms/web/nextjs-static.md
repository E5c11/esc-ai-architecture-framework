---
id: PLAT-WEB-NEXT-STATIC
type: guide
layer: platforms
platform: [web]
architecture: [web-app]
runtime: [static-export]
requires: [PLAT-WEB-NEXT, ARCH-WEB-APP]
related: [PLAT-WEB-NEXT-FIREBASE, PLAT-WEB-NEXT-DATA, PLAT-WEB-DEPLOY]
tags: [nextjs, static-export, output-export, prerender, generate-static-params, trailing-slash, client-components, hosting]
status: active
---

# Next.js Static Export

Extends: `PLAT-WEB-NEXT`, `ARCH-WEB-APP` (the `static-export` runtime)

What a `static-export` project may and may not do with Next.js, and what the build
actually produces. Checked against the Next.js 16 documentation on 2026-10-18; see
the pinned versions in `PLAT-WEB-NEXT`.

`next build` with `output: 'export'` writes one HTML file per route, plus the
JavaScript and static payloads, to an `out` folder (`distDir` changes it). Any web
server that serves static files can host it. There is no Next.js server at run time,
so everything that needs one is unavailable, and everything that runs happens either
**once, at build** (Server Components) or **in the browser** (Client Components, hooks,
the Firebase SDK).

## What runs when

| Code | Runs | Consequence |
|---|---|---|
| Server Component | Once, during `next build` | Whatever it reads is frozen into the HTML. It may read constants and build-time content, never data that changes after the build (`ARCH-WEB-APP-COMP-STATIC-01`) |
| Client Component | Prerendered to HTML during `next build` in Node, then hydrated in the browser | Browser APIs do not exist during the build; code that touches them must wait for the browser |
| Hook, DataSource, Firebase SDK | In the browser, after hydration | The prerendered HTML is a shell; real data arrives after |

## Rules

```rule
id: PLAT-WEB-NEXT-STATIC-CONFIG-01
statement: A `static-export` project MUST set `output: 'export'`, MUST NOT use the default image loader (it MUST set a custom `images.loader` or `images.unoptimized`), and MUST NOT use a feature the export does not support.
type: hard
scope: structure
enforced_by: [ci, reviewer]
violation_message: Violates PLAT-WEB-NEXT-STATIC-CONFIG-01 — A `static-export` project MUST set `output: 'export'`, MUST NOT use the default image loader (it MUST set a custom `images.loader` or `images.unoptimized`), and MUST NOT use a feature the export does not support.
```

The architecture check covers the mechanical part for a `static-export` project: `output: 'export'` is set in
`next.config.*` (`web.static-export-output`), nothing imports `next/headers` or `next/server`
(`web.static-export-no-request-apis`), and no file carries a `'use server'` directive
(`web.static-export-no-server-actions`). The image-loader clause and the rest of the unsupported list stay with a reviewer.

Unsupported with `output: 'export'`, as the Next.js documentation lists them: dynamic
routes with `dynamicParams: true` or without `generateStaticParams()`; Route Handlers
that rely on the request; cookies; rewrites, redirects and headers in the Next
configuration; proxy (formerly middleware); Incremental Static Regeneration; image
optimisation with the default loader; Draft Mode; **Server Actions**; intercepting routes.
Using one in `next dev` raises an error, which is the point: it fails where the developer
is looking. Headers, redirects and rewrites move to the host's configuration
(`PLAT-WEB-NEXT-FB-HOSTING-01` for Firebase Hosting).

```rule
id: PLAT-WEB-NEXT-STATIC-ROUTES-01
statement: A dynamic route segment MUST be used only for values known at build time, MUST list them in `generateStaticParams`, and MUST set `dynamicParams = false`; a value created at run time MUST travel in a search parameter or client-side state, not in the path.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-STATIC-ROUTES-01 — A dynamic route segment MUST be used only for values known at build time, MUST list them in `generateStaticParams`, and MUST set `dynamicParams = false`; a value created at run time MUST travel in a search parameter or client-side state, not in the path.
```

A static export has one HTML file per route. A path the build did not generate is a 404
however valid the record is. If adding a region is a configuration change and a
redeploy anyway, a build-time segment is fine; if it is data created at run time, it must
not be a path segment.

```rule
id: PLAT-WEB-NEXT-STATIC-BROWSER-01
statement: Browser-only APIs (`window`, `document`, `localStorage`, `navigator`) MUST be used only inside effects or event handlers, never at module scope or during render, because Client Components are prerendered during the build.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-STATIC-BROWSER-01 — Browser-only APIs (`window`, `document`, `localStorage`, `navigator`) MUST be used only inside effects or event handlers, never at module scope or during render, because Client Components are prerendered during the build.
```

This is the mechanism behind `PLAT-WEB-NEXT-FB-INIT-01` and
`ARCH-WEB-APP-COMPOSE-GLOBAL-01`: a module that touches `window` or initialises an SDK
at its top level fails the build, or worse, works in development and fails in production.

```rule
id: PLAT-WEB-NEXT-STATIC-ROUTEHANDLER-01
statement: A Route Handler in a static export MUST be a `GET` handler marked `dynamic = 'force-static'`, MUST be used only to emit a file at build time, and MUST NOT serve data that changes after the build.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-STATIC-ROUTEHANDLER-01 — A Route Handler in a static export MUST be a `GET` handler marked `dynamic = 'force-static'`, MUST be used only to emit a file at build time, and MUST NOT serve data that changes after the build.
```

```rule
id: PLAT-WEB-NEXT-STATIC-TRAILING-01
statement: `trailingSlash` and `skipTrailingSlashRedirect` MUST be set deliberately to match how the host maps a URL to a file, and the choice MUST be recorded in the project's Next.js configuration.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-STATIC-TRAILING-01 — `trailingSlash` and `skipTrailingSlashRedirect` MUST be set deliberately to match how the host maps a URL to a file, and the choice MUST be recorded in the project's Next.js configuration.
```

With `trailingSlash` off, a route is emitted as `route.html`; with it on, as
`route/index.html`. The host must serve whichever one the app links to.

```rule
id: PLAT-WEB-NEXT-STATIC-DIRECT-01
statement: After every deploy of a static export, each route MUST be loaded directly and refreshed on the real host, in addition to being navigated to from within the app, and an unknown path MUST show the app's `404` page.
type: hard
scope: testing
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-STATIC-DIRECT-01 — After every deploy of a static export, each route MUST be loaded directly and refreshed on the real host, in addition to being navigated to from within the app, and an unknown path MUST show the app's `404` page.
```

Client-side navigation does not request the HTML file; a direct load does. An export whose
links work but whose pages 404 on refresh passes every in-app check.

```rule
id: PLAT-WEB-NEXT-STATIC-ENV-01
statement: Each environment MUST be its own build, because `NEXT_PUBLIC_*` values are inlined at build time, and an artifact built for one environment MUST NOT be deployed to another.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-STATIC-ENV-01 — Each environment MUST be its own build, because `NEXT_PUBLIC_*` values are inlined at build time, and an artifact built for one environment MUST NOT be deployed to another.
```

A build made for a test project and deployed to production talks to the test project,
and shows no error to say so. Build from the same commit with the target environment's
configuration, and keep the artifacts apart.

## Authentication

There is no proxy, no cookies and no Server Action in a static export, so there is no
request-time place to enforce access. Access is enforced by the provider's own rules, and
the client reflects the signed-in state: `ARCH-WEB-APP-RUNTIME-02`, and for Firebase
`PLAT-WEB-NEXT-FB-AUTH-01` and `PLAT-WEB-NEXT-FB-RULES-01`.

## Violations

- A Server Component reading a snapshot, so the deployed page shows the build's numbers
- `output: 'export'` with a Server Action, a `proxy.ts`, or `headers()` in the config
- A dynamic segment for a record created after the build
- `window` or `localStorage` read at module scope
- A route that works by navigation and 404s on refresh
- A build made for one environment deployed to another
- An export deployed after checking only the home page
