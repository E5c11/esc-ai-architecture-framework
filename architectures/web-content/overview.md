---
id: ARCH-WEB-CONTENT
type: overview
layer: architectures
platform: [web]
architecture: [web-content]
requires: [CORE-COUPLING, CORE-NAMING, PAT-DATA-ACCESS]
related: [ARCH-WEB, ARCH-WEB-COMPONENTS]
tags: [web, nextjs, content, ssg, isr, server-components, seo, json-ld]
status: active
---

# Web Content Architecture

## What it is

Web Content is a Server-Components-first architecture for Next.js marketing and
content sites — the SEO-focused fork of `ARCH-WEB`'s "Static website" variant,
restated for the App Router's Server/Client Component boundary instead of a
client-side SPA.

- **Server Components by default.** A route renders on the server; nothing
  ships a client bundle unless it genuinely needs interactivity (`'use client'`
  is the exception, not the default).
- **Pages are SSG/ISR.** Content is known at build time or revalidated on an
  interval — there is no per-request client fetch for page content.
- **Content is data.** User-visible text and structured content are treated as
  a data-access concern (`PAT-DATA-ACCESS`), not literals scattered through
  JSX — the same "hide the source behind an interface" discipline the pattern
  applies to a database or REST call applies here to an imported content
  object.
- **No client data layer, no auth.** There are no hooks fetching from a
  browser, no `AuthContext`, no `AuthGuard`. If a project needs either, it has
  outgrown this architecture — see `ARCH-WEB-APP`.

This is a real fork of `architectures/web-spa/`, not an extension of it: the
CSR/hooks/Context model `ARCH-WEB` builds on has no equivalent here. `web-spa`
is not touched or deprecated by this doc — it remains the correct architecture
for every project still shipping a plain Vite/React SPA.

## Folder structure

Content is co-located with the route that owns it by default. Promote to a
shared location only once a second route needs the same content (see
`ARCH-WEB-CONTENT-SHARED-01` below).

```
app/
├── layout.tsx             Root layout — shared chrome only, no page content
├── page.tsx                Home route
├── [slug]/
│   ├── page.tsx             Server Component — renders content, generates metadata
│   └── content.ts           Route-local content object (text, structured data)
└── about/
    ├── page.tsx
    └── content.ts
content/
└── shared/
    └── {domain}.ts          Content object used by two or more routes
components/                 Shared presentational primitives (see ARCH-WEB-COMPONENTS)
```

## Layer responsibilities

| Layer | Directory | Responsibility |
|---|---|---|
| Route render | `app/[route]/page.tsx` | Server Component. Renders content. SSG/ISR. No client data fetching, no mutation logic. |
| Metadata / SEO | `app/[route]/page.tsx` (`generateMetadata`) | Per-route `<title>`/`<meta>` and JSON-LD structured data. |
| Route-local content | `app/[route]/content.ts` | The content object for one route — text, structured data, imagery references. |
| Shared content | `content/shared/{domain}.ts` | A content object consumed by two or more routes. |
| Shared UI | `components/` | Pure presentational primitives used across routes. |

## Dependency direction

```
app/[route]/page.tsx
  ├── content.ts (route-local)          → promoted to content/shared/{domain}.ts once reused
  └── components/                        shared presentational primitives
```

Routes depend on content and shared components; content and shared components
never depend on a route.

## Rules

```rule
id: ARCH-WEB-CONTENT-NOLITERAL-01
statement: User-visible text MUST NOT appear as a string literal inside JSX — it MUST be sourced from an imported content object.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-CONTENT-NOLITERAL-01 — User-visible text MUST NOT appear as a string literal inside JSX — it MUST be sourced from an imported content object.
```

This is the web equivalent of the Android/KMP `strings.xml` guarantee — but
unlike a resource file, nothing about a `.ts` module stops a literal from being
typed directly into JSX, so the constraint has to be an enforced rule rather
than a tooling guarantee.

```rule
id: ARCH-WEB-CONTENT-SHARED-01
statement: A content object used by two or more routes MUST move to `content/shared/{domain}.ts` — never be duplicated across route-local content files.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-CONTENT-SHARED-01 — A content object used by two or more routes MUST move to `content/shared/{domain}.ts` — never be duplicated across route-local content files.
```

This is `ARCH-WEB-ORG-02`'s co-locate-until-reused model — already governing
component promotion in `ARCH-WEB` — restated for content instead of
components. The reuse threshold is the same; see `ARCH-WEB-ORG-02` for the
rationale rather than re-deriving it here.

```rule
id: ARCH-WEB-CONTENT-SEO-01
statement: Each route MUST own its `generateMetadata` export and any JSON-LD structured data for that route — neither may be centralized in a shared layout, utility, or root config.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-CONTENT-SEO-01 — Each route MUST own its `generateMetadata` export and JSON-LD structured data — neither may be centralized in a shared layout, utility, or root config.
```

A centralized metadata utility inevitably drifts from what a specific route
actually renders — title, description, and structured data are only accurate
when authored next to the content they describe.

## Deliberately out of scope

Theming and shared components are not decided in this doc. A Tailwind token
rule names a specific technology, so per the placement test in
`workflows/README.md` it belongs in a platform doc, not here — see
`platforms/web/design-system/` in the follow-up gap log. Component rules are
already fully covered by `ARCH-WEB-COMPONENTS`; this doc cites that instead of
duplicating it, and does not add a sibling `components.md` because content-site
component rules do not genuinely diverge from it.
