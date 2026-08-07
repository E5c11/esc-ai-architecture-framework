---
id: PLAT-WEB-DEPLOY
type: guide
layer: platforms
platform: [web]
architecture: web-spa
requires: [ARCH-WEB, PLAT-WEB-REACT]
related: [PLAT-WEB-FIREBASE]
tags: [deploy, build, vite, firebase-hosting, tsc, sitemap, robots]
status: active
---

# Build and Deploy

Extends: `ARCH-WEB`

## Build pipeline

All projects build with Vite and TypeScript before every deploy.

```bash
npm run build
# Internally: tsc -b && vite build
```

```rule
id: PLAT-WEB-DEPLOY-BUILD-01
statement: The build MUST pass `tsc -b` with zero errors before deploying.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DEPLOY-BUILD-01 — The build MUST pass `tsc -b` with zero errors before deploying.
```

Never deploy from a build that produced TypeScript errors. `// @ts-ignore` suppressions and skipping `tsc` are forbidden.

```rule
id: PLAT-WEB-DEPLOY-BUILD-02
statement: Always build immediately before deploying.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DEPLOY-BUILD-02 — Always build immediately before deploying.
```

Never deploy from a stale build artefact or from the dev server output.

## package.json scripts

```json
{
  "scripts": {
    "dev":     "vite",
    "build":   "tsc -b && vite build",
    "preview": "vite preview",
    "deploy":  "npm run build && firebase deploy --only hosting"
  }
}
```

The `deploy` script chains `build` and deploy atomically. Never run
`firebase deploy` without first running `npm run build`.

## Firebase Hosting configuration

```json
{
  "hosting": {
    "public": "dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [{ "source": "**", "destination": "/index.html" }]
  }
}
```

```rule
id: PLAT-WEB-DEPLOY-REWRITE-01
statement: `firebase.json` MUST include the SPA rewrite (`"source": "**"` → `"/index.html"`).
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DEPLOY-REWRITE-01 — `firebase.json` MUST include the SPA rewrite (`"source": "**"` → `"/index.html"`).
```

Without it, direct navigation to any route other than `/` returns a 404 from Firebase Hosting.

```rule
id: PLAT-WEB-DEPLOY-HOSTING-01
statement: Deploy with `--only hosting` unless explicitly intending to deploy Firestore rules, Functions, or other Firebase services.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DEPLOY-HOSTING-01 — Deploy with `--only hosting` unless explicitly intending to deploy Firestore rules, Functions, or other Firebase services.
```

`firebase deploy` without a scope deploys everything, which can push unintended rule changes.

```bash
firebase deploy --only hosting      # ✅ always safe
firebase deploy                     # ✗ deploys everything — confirm intent first
```

## Commit before deploy

```rule
id: PLAT-WEB-DEPLOY-COMMIT-01
statement: Commit all changes before deploying.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DEPLOY-COMMIT-01 — Commit all changes before deploying.
```

The deployed build should always correspond to a commit. Build and commit getting out of sync makes rollback and incident diagnosis significantly harder.

## Preview before deploy

```rule
id: PLAT-WEB-DEPLOY-PREVIEW-01
statement: Run `npm run preview` and walk the golden path in a browser before deploying if there is any doubt about the build.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DEPLOY-PREVIEW-01 — Run `npm run preview` and walk the golden path in a browser before deploying if there is any doubt about the build.
```

`vite preview` serves the production build locally with the same optimisation settings as a live deploy.

## Public assets

```rule
id: PLAT-WEB-DEPLOY-ASSETS-01
statement: Static assets that must be served at a stable, unhashed URL (images used in OG tags, `robots.txt`, `sitemap.xml`, `favicon.ico`) MUST live in `public/`.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DEPLOY-ASSETS-01 — Static assets that must be served at a stable, unhashed URL (images used in OG tags, `robots.txt`, `sitemap.xml`, `favicon.ico`) MUST live in `public/`.
```

Assets in `src/assets/` are processed and hashed by Vite — their filenames change on every build.

## Sitemap and robots.txt

```rule
id: PLAT-WEB-DEPLOY-SITEMAP-01
statement: `sitemap.xml` MUST be updated when new public routes are added.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DEPLOY-SITEMAP-01 — `sitemap.xml` MUST be updated when new public routes are added.
```

Include the full `https://` URL for each route.

```rule
id: PLAT-WEB-DEPLOY-ROBOTS-01
statement: `robots.txt` on the production site MUST allow crawling (`User-agent: * / Allow: /`).
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-DEPLOY-ROBOTS-01 — `robots.txt` on the production site MUST allow crawling (`User-agent: * / Allow: /`).
```

Dev and staging environments should disallow; production must allow. Never deploy a disallow-all `robots.txt` to production.
