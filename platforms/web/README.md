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

## Project-set values

A web rule that needs a number says "declare a limit", never the number itself. A project records its values as
local rules in `.esc-ai/local-architecture/` (status `stub`, so they cannot pass for framework rules) and enforces
them with its own lint or architecture check. Values a project is expected to declare: maximum module size,
maximum function length and branch count, the point at which a feature splits into sub-features, the cap on
categorical chart series, and any read budget (see `ARCH-WEB-APP-DS-AGG-01`). A value that recurs across projects
is a candidate for a framework default through the normal contribution route.

The lintable limits are read from `.esc-ai/lint-limits.yaml` (`maxModuleLines`, `maxFunctionLines`, `maxComplexity`, optionally `maxComponentFunctionLines`) by `esc-exec architecture lint-config generate`, which writes a TypeScript `eslint.config.ts`. Generation fails when a limit is not declared; the framework sets no default sizes.
