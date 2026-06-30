---
id: PLAT-WEB-DEPLOY
type: guide
layer: platforms
platform: [web]
architecture: web-spa
requires: [ARCH-WEB, PLAT-WEB-REACT]
related: [PLAT-WEB-FIREBASE]
tags: [deploy, build, vite, firebase-hosting, tsc, sitemap, robots]
---

# Build and Deploy

Extends: `ARCH-WEB`

## Build pipeline

All projects build with Vite and TypeScript before every deploy.

```bash
npm run build
# Internally: tsc -b && vite build
```

**Rule PLAT-WEB-DEPLOY-BUILD-01 (hard):** The build MUST pass `tsc -b` with zero
errors before deploying. Never deploy from a build that produced TypeScript errors.
`// @ts-ignore` suppressions and skipping `tsc` are forbidden.

**Rule PLAT-WEB-DEPLOY-BUILD-02 (hard):** Always build immediately before deploying.
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

**Rule PLAT-WEB-DEPLOY-REWRITE-01 (hard):** `firebase.json` MUST include the SPA
rewrite (`"source": "**"` → `"/index.html"`). Without it, direct navigation to
any route other than `/` returns a 404 from Firebase Hosting.

**Rule PLAT-WEB-DEPLOY-HOSTING-01 (hard):** Deploy with `--only hosting` unless
explicitly intending to deploy Firestore rules, Functions, or other Firebase
services. `firebase deploy` without a scope deploys everything, which can push
unintended rule changes.

```bash
firebase deploy --only hosting      # ✅ always safe
firebase deploy                     # ✗ deploys everything — confirm intent first
```

## Commit before deploy

**Rule PLAT-WEB-DEPLOY-COMMIT-01 (soft):** Commit all changes before deploying.
The deployed build should always correspond to a commit. Build and commit getting
out of sync makes rollback and incident diagnosis significantly harder.

## Preview before deploy

**Rule PLAT-WEB-DEPLOY-PREVIEW-01 (soft):** Run `npm run preview` and walk the
golden path in a browser before deploying if there is any doubt about the build.
`vite preview` serves the production build locally with the same optimisation
settings as a live deploy.

## Public assets

**Rule PLAT-WEB-DEPLOY-ASSETS-01 (hard):** Static assets that must be served at
a stable, unhashed URL (images used in OG tags, `robots.txt`, `sitemap.xml`,
`favicon.ico`) MUST live in `public/`. Assets in `src/assets/` are processed and
hashed by Vite — their filenames change on every build.

## Sitemap and robots.txt

**Rule PLAT-WEB-DEPLOY-SITEMAP-01 (soft):** `sitemap.xml` MUST be updated when
new public routes are added. Include the full `https://` URL for each route.

**Rule PLAT-WEB-DEPLOY-ROBOTS-01 (hard):** `robots.txt` on the production site
MUST allow crawling (`User-agent: * / Allow: /`). Dev and staging environments
should disallow; production must allow. Never deploy a disallow-all `robots.txt`
to production.
