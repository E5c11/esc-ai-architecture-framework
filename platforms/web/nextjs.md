---
id: PLAT-WEB-NEXT
type: guide
layer: platforms
platform: [web]
architecture: [web-app, web-content]
requires: [CORE-COUPLING]
related: [ARCH-WEB-APP, ARCH-WEB-CONTENT, PLAT-WEB-NEXT-APP, PLAT-WEB-NEXT-DATA, PLAT-WEB-NEXT-STATIC]
tags: [nextjs, app-router, routing, layouts, server-components, client-components, proxy, env-vars, versions, error-boundaries, server-only, search-params, lint]
status: active
---

# Next.js App Router Fundamentals

Shared by `ARCH-WEB-APP` and `ARCH-WEB-CONTENT` — file-based routing and the
Server/Client Component boundary are mechanically identical for both
architectures; what differs is what each architecture *does* with them
(`ARCH-WEB-APP`'s held external-call boundary vs. `ARCH-WEB-CONTENT`'s
SSG/ISR content model). This doc covers only the shared mechanics; it does
not repeat either architecture's layering decisions.

## Pinned versions

Next.js changes its caching, request and file conventions between major versions, so
the guidance in `PLAT-WEB-NEXT` and its siblings is written against one version line.
Versions checked against the upstream registries and documentation on **2026-10-18**:

| Package | Version line | Notes |
|---|---|---|
| `next` | **16.x** (16.4.2 at the check) | Needs Node.js 20.9 or later and TypeScript 5.1 or later. Turbopack is the default bundler for `dev` and `build` |
| `react`, `react-dom` | **19.x** (19.3.1 at the check) | The App Router uses a React release that includes 19.2 features (`useEffectEvent`, `Activity`, `ViewTransition`) |
| `tailwindcss` | **4.x** (4.3.3 at the check) | CSS-first configuration; see `PLAT-WEB-DS-THEME` |
| `firebase` (JS SDK) | **13.x** (13.0.0 at the check) | The modular SDK |

```rule
id: PLAT-WEB-NEXT-VERSION-01
statement: A project MUST record the Next.js, React, Tailwind and Firebase SDK versions it targets in its repository, MUST change them only as a deliberate upgrade step committed on its own, and MUST NOT adopt a new major version's opt-in features (Cache Components, the React Compiler) as a side effect of upgrading.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-VERSION-01 — A project MUST record the Next.js, React, Tailwind and Firebase SDK versions it targets in its repository, MUST change them only as a deliberate upgrade step committed on its own, and MUST NOT adopt a new major version's opt-in features (Cache Components, the React Compiler) as a side effect of upgrading.
```

An upgrade is a behaviour-preserving change (`ARCH-WEB-APP-workflow`'s discipline):
run the framework's upgrade codemod, get the suite green, commit; adopt a new feature
afterwards, in its own change. Where a rule in this framework names a version-specific
file or flag (`proxy.ts`, `cacheComponents`), it says which versions it applies to; on
an older version, use the older name.

## File-based routing

A route is a folder under `app/` containing a `page.tsx`. The folder path
maps directly to the URL path — there is no separate route-config file to
keep in sync.

```
app/
├── layout.tsx           Root layout — wraps every route
├── page.tsx              /
├── dashboard/
│   ├── layout.tsx         Layout shared by every route under /dashboard
│   ├── page.tsx           /dashboard
│   └── settings/
│       └── page.tsx       /dashboard/settings
└── (marketing)/           Route group — organizes without affecting the URL
    ├── about/page.tsx      /about, not /marketing/about
    └── pricing/page.tsx    /pricing
```

A route group (`(name)`) exists to apply a different `layout.tsx` to a
subset of routes, or to organize routes by concern, without adding a URL
segment. It is a filesystem-only construct — nothing about it is visible to
a request.

Layouts nest: a route renders inside every `layout.tsx` from the root down
to its own folder. A layout persists across navigations between its child
routes — it does not re-render or lose state when only the child route
changes.

## Server Component default, Client Component exception

Every component under `app/` is a Server Component unless its file (or a
file it's defined in) starts with the `'use client'` directive. A Server
Component renders on the server and ships no JavaScript for itself to the
client; a Client Component renders on the server for the initial paint and
then hydrates, shipping its code to the browser.

```rule
id: PLAT-WEB-NEXT-CLIENT-01
statement: A component MUST NOT be marked `'use client'` unless it itself uses browser-only APIs, local state, or event handlers — the boundary is pushed to the smallest leaf that actually needs it, never applied to a whole page or layout by default.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-CLIENT-01 — push `'use client'` to the smallest leaf component that needs it; do not mark a whole page or layout client-side by default.
```

```tsx
// ❌ Wrong — the whole page opts into the client bundle for one button
'use client';
export default function DashboardPage() {
  return (
    <div>
      <StaticSummary />          {/* doesn't need to be client-side */}
      <RefreshButton />          {/* the only part that does */}
    </div>
  );
}

// ✅ Correct — only the interactive leaf ships JS
export default function DashboardPage() {
  return (
    <div>
      <StaticSummary />
      <RefreshButton />          {/* 'use client' lives inside this file */}
    </div>
  );
}
```

A `'use client'` directive marks a module boundary, not just one component —
everything that module imports is pulled into the client bundle too. Placing
the directive on a whole page drags every child component across the
boundary with it, even ones that never touch browser-only state.

## Environment variables

```rule
id: PLAT-WEB-NEXT-ENV-01
statement: An environment variable MUST NOT be prefixed `NEXT_PUBLIC_` unless its value is safe to ship in the client JS bundle — server-only credentials (DB connection strings, backend service credentials) MUST be read only in server-side code (Server Components, Route Handlers, Server Actions, the proxy file).
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-ENV-01 — a `NEXT_PUBLIC_`-prefixed variable ships in the client bundle; server-only credentials MUST NOT use that prefix.
```

Next.js inlines any `NEXT_PUBLIC_*` variable into the client bundle at build
time — it is not a runtime secret from that point on, regardless of where it
is read. An unprefixed variable is readable only in code that never crosses
the Client Component boundary.

## `proxy.ts` (`middleware.ts` before Next.js 16)

`proxy.ts` at the project root (or inside `src/`) is the one file Next.js itself
recognizes for request-time interception — it runs before routing resolves, ahead of
every Server Component render for a matched path. In Next.js 16 the `middleware`
filename and its `middleware` export are deprecated and renamed `proxy`; on Next.js 15
and earlier the file is `middleware.ts` and the export is `middleware`. The `proxy` file
runs on the Node.js runtime and the runtime cannot be configured; a project that needs the
edge runtime keeps `middleware`. A static export has neither (`PLAT-WEB-NEXT-STATIC`).

```rule
id: PLAT-WEB-NEXT-MW-01
statement: In the `server` runtime, an auth/session check that gates an entire app or route group MUST live in `proxy.ts` (`middleware.ts` before Next.js 16), evaluated before any Server Component in that group renders — never duplicated as a per-page guard.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-MW-01 — gate the route group in `proxy.ts` (`middleware.ts` before Next.js 16), not with a per-page guard component.
```

This is the mechanical fact `ARCH-WEB-APP`'s "Auth enforcement:
`proxy.ts`, not a per-page guard component" decision rests on — see that
doc's overview for *why* a single upfront check is the right shape for this
architecture; this doc only establishes *which file* Next.js runs and *when*.

```typescript
// proxy.ts
export function proxy(request: Request) {
  // verify the session; redirect or respond when it is missing
}

export const config = {
  matcher: ['/dashboard/:path*'],   // only intercepts matched paths
};
```

A `matcher` scopes the proxy to the routes that actually need the check — running it
on every request (including static assets) is unnecessary overhead. Confirm the exact
`proxy` export and `config` shape against the file-convention reference for the pinned
version.

## Request APIs are asynchronous

```rule
id: PLAT-WEB-NEXT-ASYNC-01
statement: `params`, `searchParams`, `cookies()`, `headers()` and `draftMode()` MUST be accessed asynchronously (`await`, or `use` in a Client Component); synchronous access, supported for compatibility in Next.js 15, is removed in 16.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-ASYNC-01 — `params`, `searchParams`, `cookies()`, `headers()` and `draftMode()` MUST be accessed asynchronously (`await`, or `use` in a Client Component); synchronous access, supported for compatibility in Next.js 15, is removed in 16.
```

Use the generated `PageProps`, `LayoutProps` and `RouteContext` type helpers
(`next typegen`) so a route's `params` type cannot drift from its folder name.

## Server-only code

```rule
id: PLAT-WEB-NEXT-SERVERONLY-01
statement: A module that reads a secret, holds a server credential or must never run in the browser MUST import `server-only` as its first import, and a module that touches browser APIs MAY import `client-only`.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-SERVERONLY-01 — A module that reads a secret, holds a server credential or must never run in the browser MUST import `server-only` as its first import, and a module that touches browser APIs MAY import `client-only`.
```

JavaScript modules are shared between the server and client graphs, so it is easy to
import server code into the client by accident. Without the marker, an unprefixed
environment variable becomes an empty string in the browser and the code fails in a
confusing way; with it, the build fails with a clear message. This is the mechanism
`ARCH-WEB-APP-COMPOSE-SPLIT-01` requires of a server DataSource and
`ARCH-WEB-APP-COMPOSE-SPLIT-01` of the server graph.

## Route boundary files

```rule
id: PLAT-WEB-NEXT-BOUNDARY-01
statement: Each route group MUST have an `error.tsx` (a Client Component receiving `error` and `retry`), a segment that suspends MUST have a `loading.tsx` or an explicit `<Suspense>` fallback, a segment that calls `notFound()` MUST have a `not-found.tsx`, and the root MUST have a `global-error.tsx` that defines its own `<html>` and `<body>`.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-BOUNDARY-01 — Each route group MUST have an `error.tsx` (a Client Component receiving `error` and `retry`), a segment that suspends MUST have a `loading.tsx` or an explicit `<Suspense>` fallback, a segment that calls `notFound()` MUST have a `not-found.tsx`, and the root MUST have a `global-error.tsx` that defines its own `<html>` and `<body>`.
```

`error.tsx` catches uncaught exceptions below it, so it is the implementation of
`ARCH-WEB-APP-EFLOW-BOUNDARY-01`: report the error once through the injected reporter,
show a recoverable screen, and call `retry` to re-render the segment (older Next.js
versions named this prop `reset`). It does not catch errors in event handlers or
asynchronous code, which is why expected failures are returned as outcomes
(`PLAT-WEB-RP-BOUNDARY-01`). `catchError` from `next/error` makes a boundary for a
component-level region, such as a chart panel.

## URL as state

```rule
id: PLAT-WEB-NEXT-URL-01
statement: State that a person would want to share or bookmark (the selected region, filters, sort order, date range) MUST live in the URL, MUST be read in Client Components with `useSearchParams` inside a `<Suspense>` boundary, and MUST be validated with a schema parser before use.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-URL-01 — State that a person would want to share or bookmark (the selected region, filters, sort order, date range) MUST live in the URL, MUST be read in Client Components with `useSearchParams` inside a `<Suspense>` boundary, and MUST be validated with a schema parser before use.
```

During a production build, a statically rendered page whose Client Component calls
`useSearchParams` without a `Suspense` boundary fails the build; in development it does
not, so the problem appears only at deploy. A layout does not receive `searchParams`
(it is not re-rendered on navigation), so read them in the page or in a Client Component.
A search parameter is untrusted input (`ARCH-WEB-APP-EFLOW-VALIDATE-01`): a hand-edited
`?region=nowhere` must produce a clear state, not a crash.

## Linting and the build

```rule
id: PLAT-WEB-NEXT-LINT-01
statement: Linting MUST run as its own step in CI with the project's ESLint (flat configuration) or Biome setup, and MUST NOT be assumed to run as part of `next build`.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-LINT-01 — Linting MUST run as its own step in CI with the project's ESLint (flat configuration) or Biome setup, and MUST NOT be assumed to run as part of `next build`.
```

Next.js 16 removed `next lint`, and `next build` no longer lints. A pipeline that relied
on the build to lint now lints nothing, and passes. The type-check still runs in
`next build` (`PLAT-WEB-NEXT-APP-DEPLOY-BUILD-01`).
