# platforms/web/

TypeScript / React / Next.js implementation guides.

Documents here cover web frontend patterns. They reference `patterns/` and
`core/` but are not tied to a single architecture — web projects declare their
own architectural style in their project profile.

## Tech stack covered

- TypeScript
- React
- Next.js
- Firebase Web SDK

## Document ID prefix: `PLAT-WEB-`

## Language of the examples

Code examples in the `web` documents are TypeScript and TSX. A block in another language appears only where
the tool requires it: CSS for Tailwind 4 configuration, JSON for `firebase.json`, YAML for an architecture
profile, a Dockerfile, shell commands. A project's configuration files are TypeScript where the tool allows
(`next.config.ts`, `proxy.ts`, `vitest.config.ts`); where it does not (for example a PostCSS config), the
document says so.
