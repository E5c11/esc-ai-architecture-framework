---
id: PLAT-WEB-NEXT
type: guide
layer: platforms
platform: [web]
architecture: [web-app, web-content]
requires: [CORE-COUPLING]
related: [ARCH-WEB-APP, ARCH-WEB-CONTENT]
tags: [nextjs, app-router, routing, layouts, server-components, client-components, middleware, env-vars]
status: active
---

# Next.js App Router Fundamentals

Shared by `ARCH-WEB-APP` and `ARCH-WEB-CONTENT` — file-based routing and the
Server/Client Component boundary are mechanically identical for both
architectures; what differs is what each architecture *does* with them
(`ARCH-WEB-APP`'s held external-call boundary vs. `ARCH-WEB-CONTENT`'s
SSG/ISR content model). This doc covers only the shared mechanics; it does
not repeat either architecture's layering decisions.

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
statement: An environment variable MUST NOT be prefixed `NEXT_PUBLIC_` unless its value is safe to ship in the client JS bundle — server-only credentials (DB connection strings, backend service credentials) MUST be read only in server-side code (Server Components, Route Handlers, Server Actions, middleware).
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-ENV-01 — a `NEXT_PUBLIC_`-prefixed variable ships in the client bundle; server-only credentials MUST NOT use that prefix.
```

Next.js inlines any `NEXT_PUBLIC_*` variable into the client bundle at build
time — it is not a runtime secret from that point on, regardless of where it
is read. An unprefixed variable is readable only in code that never crosses
the Client Component boundary.

## `middleware.ts`

`middleware.ts` at the project root (or inside `src/`) is the one file
Next.js itself recognizes for request-time interception — it runs before
routing resolves, ahead of every Server Component render for a matched path.

```rule
id: PLAT-WEB-NEXT-MW-01
statement: An auth/session check that gates an entire app or route group MUST live in `middleware.ts`, evaluated before any Server Component in that group renders — never duplicated as a per-page guard.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-MW-01 — gate the route group in `middleware.ts`, not with a per-page guard component.
```

This is the mechanical fact `ARCH-WEB-APP`'s "Auth enforcement:
`middleware.ts`, not a per-page guard component" decision rests on — see that
doc's overview for *why* a single upfront check is the right shape for this
architecture; this doc only establishes *which file* Next.js runs and *when*.

```typescript
// middleware.ts
export { auth as middleware } from './auth';   // or a hand-rolled session check

export const config = {
  matcher: ['/dashboard/:path*'],   // only intercepts matched paths
};
```

A `matcher` scopes middleware to the routes that actually need the check —
running it on every request (including static assets) is unnecessary
overhead.
