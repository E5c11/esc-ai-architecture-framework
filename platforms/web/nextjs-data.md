---
id: PLAT-WEB-NEXT-DATA
type: guide
layer: platforms
platform: [web]
architecture: [web-app]
runtime: [server]
requires: [PLAT-WEB-NEXT, PLAT-WEB-NEXT-APP, ARCH-WEB-APP-DATASOURCE]
related: [PLAT-WEB-NEXT-STATIC, PLAT-WEB-HTTP, ARCH-WEB-APP-DOMAIN]
tags: [nextjs, caching, cache-components, use-cache, cache-life, cache-tag, suspense, streaming, revalidation, server-runtime]
status: active
---

# Next.js Data Fetching and Caching

Extends: `PLAT-WEB-NEXT`, `PLAT-WEB-NEXT-APP`

For the **`server`** runtime. A `static-export` project has no run-time cache and no
request-time rendering; it uses none of this (`PLAT-WEB-NEXT-STATIC`).

Checked against the Next.js 16 documentation on 2026-10-18. Caching behaviour has
changed between major versions, so this guide names a model and states what it relies on.

## Two models

Next.js 16 has two caching models:

- **Cache Components** (`cacheComponents: true`): rendering is static by default;
  caching is explicit, with the `use cache` directive and `cacheLife`/`cacheTag`; anything
  uncached or request-dependent must sit behind `<Suspense>`. New apps created with
  `create-next-app` have it enabled, together with `partialPrefetching: true`.
- **The previous model**: route-level options and `fetch` caching options, documented
  in the Next.js guide "Caching and Revalidating (Previous Model)".

```rule
id: PLAT-WEB-NEXT-DATA-MODEL-01
statement: A `server`-runtime project MUST declare which caching model it uses in `next.config`, MUST set `partialPrefetching` explicitly when `cacheComponents` is on and the targeted Next.js version has that option (16.3 and later), and MUST NOT write code for one model while configured for the other.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-DATA-MODEL-01 — A `server`-runtime project MUST declare which caching model it uses in `next.config`, MUST set `partialPrefetching` explicitly when `cacheComponents` is on and the targeted Next.js version has that option (16.3 and later), and MUST NOT write code for one model while configured for the other.
```

`partialPrefetching` does not exist in Next.js 16.2 (a project on 16.2 sets `cacheComponents` alone); it is part of the version recorded under `PLAT-WEB-NEXT-VERSION-01`. New projects SHOULD use Cache Components. Enabling it on an existing app is not a rename:
it can surface build errors for uncached data outside `<Suspense>`, and it is an upgrade
step of its own (`PLAT-WEB-NEXT-VERSION-01`). The rules below are written for Cache
Components.

## Where data is read

```rule
id: PLAT-WEB-NEXT-DATA-FETCH-01
statement: A Server Component MUST read data through a server DataSource or UseCase obtained from the composition, and MUST NOT call `fetch`, a database client or an SDK inline.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-DATA-FETCH-01 — A Server Component MUST read data through a server DataSource or UseCase obtained from the composition, and MUST NOT call `fetch`, a database client or an SDK inline.
```

This is `ARCH-WEB-APP-DEP-05`'s exception for the Server Component shell
(`ARCH-WEB-APP-COMP-SERVER-01`), and the executor rule `PLAT-WEB-HTTP-LIB-01`, applied to
rendering.

## Request-time reads

```rule
id: PLAT-WEB-NEXT-DATA-DYNAMIC-01
statement: A Server Component that reads data which changes between requests, but which Next.js cannot see changing (an in-process store, any read that resolves without I/O), MUST make the read request-time with `await connection()` inside a `<Suspense>` boundary, or MUST cache it deliberately with `use cache`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-DATA-DYNAMIC-01 — A Server Component that reads data which changes between requests, but which Next.js cannot see changing (an in-process store, any read that resolves without I/O), MUST make the read request-time with `await connection()` inside a `<Suspense>` boundary, or MUST cache it deliberately with `use cache`.
```

Next.js decides what is dynamic from the request APIs, `fetch` and I/O it observes while prerendering.
A read of an in-memory store finishes without any of those, so the route is prerendered with whatever the
store held at build time and that value is frozen into the page: it builds as `Static`, no error is raised,
and after a write the page still shows the old data. Verified on Next.js 16.3 with an in-process store
(not verified for a real database client). `connection()` marks the read as request-time.

## Caching

```rule
id: PLAT-WEB-NEXT-DATA-USECACHE-01
statement: A function or component marked `use cache` MUST be deterministic in its arguments, MUST be paired with an explicit `cacheLife`, and MUST NOT read a runtime API (`cookies()`, `headers()`, `searchParams`) inside the cached scope; a runtime value MUST be read outside and passed in as an argument.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-DATA-USECACHE-01 — A function or component marked `use cache` MUST be deterministic in its arguments, MUST be paired with an explicit `cacheLife`, and MUST NOT read a runtime API (`cookies()`, `headers()`, `searchParams`) inside the cached scope; a runtime value MUST be read outside and passed in as an argument.
```

Arguments and captured values become the cache key, so a cached function that reads
the session from a cookie inside itself caches one user's result for everyone, or
refuses to cache. Pass the extracted value in (the session id becomes part of the key).
An unspecified `cacheLife` silently applies the default profile, which nobody chose.

```rule
id: PLAT-WEB-NEXT-DATA-TAG-01
statement: Cache tags MUST be named by entity and identity from one module that both the `cacheTag` calls and the invalidation calls import, and a tag MUST NOT be written as a string literal at a call site.
type: hard
scope: naming
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-DATA-TAG-01 — Cache tags MUST be named by entity and identity from one module that both the `cacheTag` calls and the invalidation calls import, and a tag MUST NOT be written as a string literal at a call site.
```

A misspelt tag does not fail; it simply never invalidates, and a user sees stale data
with no error. The invalidation API choice (`updateTag`, `revalidateTag(tag, profile)`,
`revalidatePath`, `refresh`) is `PLAT-WEB-NEXT-APP-REVALIDATE-01`.

## Streaming and the static shell

```rule
id: PLAT-WEB-NEXT-DATA-SUSPENSE-01
statement: Data that is uncached or depends on the request MUST be read inside a `<Suspense>` boundary placed as deep in the tree as possible, and a layout MUST NOT `await` `params`, `searchParams`, `cookies()` or `headers()` at its top level if that can be deferred below a boundary.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-DATA-SUSPENSE-01 — Data that is uncached or depends on the request MUST be read inside a `<Suspense>` boundary placed as deep in the tree as possible, and a layout MUST NOT `await` `params`, `searchParams`, `cookies()` or `headers()` at its top level if that can be deferred below a boundary.
```

Everything above the boundary is part of the static shell sent immediately; everything
below it streams. A layout that awaits a request value at its top makes the whole subtree
request-time, and the shell shrinks to nothing. Pass the promise down and await it inside
the boundary.

```rule
id: PLAT-WEB-NEXT-DATA-NONDET-01
statement: A Server Component MUST NOT call `Date.now()`, `new Date()`, `Math.random()` or `crypto.randomUUID()` during render unless the value is deferred to request time (`await connection()` inside a `<Suspense>` boundary) or deliberately cached.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-DATA-NONDET-01 — A Server Component MUST NOT call `Date.now()`, `new Date()`, `Math.random()` or `crypto.randomUUID()` during render unless the value is deferred to request time (`await connection()` inside a `<Suspense>` boundary) or deliberately cached.
```

Under Cache Components these calls fail the build until handled, because their result
differs on every execution. This is the framework enforcing what
`ARCH-WEB-APP-DOM-CLOCK-01` asks of domain code: the current time is an input, not
something a function reaches for.

```rule
id: PLAT-WEB-NEXT-DATA-ENV-01
statement: A non-public environment value that can change between deploys of one build MUST be read at request time, after `await connection()`, and MUST NOT be read during prerender, where it is frozen into the build.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-DATA-ENV-01 — A non-public environment value that can change between deploys of one build MUST be read at request time, after `await connection()`, and MUST NOT be read during prerender, where it is frozen into the build.
```

Server-only credentials stay server-side (`PLAT-WEB-NEXT-ENV-01`); this rule is about
*when* they are read.

## Violations

- Caching configured one way and code written for the other
- A `use cache` function with no `cacheLife`, or one that calls `cookies()`
- A tag spelt out as a string in two places
- A layout that awaits `params` at its top, so nothing is static
- `new Date()` in a Server Component with no deferral
- `fetch` called inline in a page
- A runtime setting read at build time and frozen into the output
