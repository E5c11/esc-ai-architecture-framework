---
id: PLAT-WEB-NEXT-APP-DEPLOY
type: guide
layer: platforms
platform: [web]
architecture: [web-app]
requires: [PLAT-WEB-NEXT-APP]
related: [PLAT-WEB-DEPLOY]
tags: [deploy, docker, cloud-run, standalone, domain-mapping, tls, build, connection-pool]
---

# Build and Deploy — Next.js `web-app` on Docker/Cloud Run

Extends: `PLAT-WEB-NEXT-APP`

`PLAT-WEB-DEPLOY` covers the Vite/Firebase Hosting pipeline for `web-spa` —
its `PLAT-WEB-DEPLOY-BUILD-01` principle ("never deploy a build with
TypeScript errors") holds unchanged here. This doc adds only what's
genuinely different for a Next.js app shipped as a container image to a
scale-to-zero host (Cloud Run or equivalent) rather than a static bundle to
Firebase Hosting.

## Build gate

```rule
id: PLAT-WEB-NEXT-APP-DEPLOY-BUILD-01
statement: `next build` MUST pass with zero TypeScript errors before the container image is built — mirrors PLAT-WEB-DEPLOY-BUILD-01's principle for the Vite pipeline, restated for `next build`'s own type-check step.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-APP-DEPLOY-BUILD-01 — never build a container image from a `next build` that produced TypeScript errors.
```

`next build` runs its own type-check as part of the build step (unlike
Vite, which needs `tsc -b` invoked separately) — the container build stage
must not proceed past a failing `next build`, and `next.config.js`'s
`typescript.ignoreBuildErrors` must never be set to `true` to work around a
failure.

## Connection pooling on a scale-to-zero host

```rule
id: PLAT-WEB-NEXT-APP-DEPLOY-POOL-01
statement: A Route Handler/Server Action holding a direct database connection pool on a scale-to-zero host (Cloud Run or equivalent) MUST set a minimum instance count ≥ 1 and size the pool for deployed concurrency.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-APP-DEPLOY-POOL-01 — an unconfigured pool on a scale-to-zero host causes connection churn/exhaustion on every cold start.
```

A container instance that scales to zero tears down its pool with it; the
next request pays for a fresh pool (and, if the database sits behind a
proxy, a fresh proxy connection) before it can serve anything. Worse, a
burst of concurrent cold starts each opening their own pool can exhaust the
database's connection limit outright. Setting a minimum instance count ≥ 1
keeps one pool warm at all times; the pool itself still needs to be sized
for the concurrency the deployment actually expects, not left at a
driver's default meant for a long-lived server process.

This generalizes the operational note a Cloud SQL Auth Proxy + Cloud Run
deployment already worked out for a real project: `min-instances` set to
avoid proxy/pool churn on cold start, with a modest pool size sufficient for
the deployed concurrency. That project-specific configuration lives in the
project's own deployment docs — this rule is the framework-level statement
of the same fact.

## Docker: multi-stage build with `standalone` output

Set `output: 'standalone'` in `next.config.js` so the production image
contains only the minimal server bundle and its resolved dependencies, not
the full `node_modules` tree or build cache:

```dockerfile
# Stage 1 — install deps and build
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2 — copy only the standalone output
FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

The builder stage produces the artifact; the runner stage ships only what
`standalone` output actually needs at runtime — this is what keeps the
deployed image small and the cold-start time reasonable.

## Domain mapping and TLS

A custom subdomain (e.g. an admin dashboard mapped to its own subdomain of
an owned domain) uses Cloud Run domain mapping with Google-managed TLS —
certificate provisioning and renewal are handled by the platform, not
configured manually. This is a deployment-target fact, not a behavioral
constraint, so it isn't a rule: point the container's Cloud Run service at
the subdomain via domain mapping, verify domain ownership once, and let the
managed certificate handle the rest. Don't hardcode a specific project's
literal domain into shared tooling or CI config — treat it as an
environment-specific value.
