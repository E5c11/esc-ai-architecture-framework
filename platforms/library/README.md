# platforms/library/

Guides for publishing a versioned package that other repositories depend on — a Maven
artifact, an npm package, or both from the same source.

A document belongs here if it's about the mechanics of *packaging and publishing* code for
external consumption. It does not belong here if it's about consuming a published package
(that's ordinary `platforms/mobile/`, `platforms/backend/`, or `platforms/web/` usage), and
it does not belong here if it's a platform-agnostic principle about API evolution — that's
`core/api-stability.md`. This directory is the technology-specific *how*; `core/` is the
platform-agnostic *why*.

## Why a separate platform, not folded into `mobile`

Kotlin Multiplatform is currently the only technology represented here, and it's also what
`platforms/mobile/kmp.md` covers — but that document is about KMP *inside an app*
(source-set structure for `commonMain`/`androidMain`/`iosMain`/`wasmJsMain` as consumed by a
single deployable app). Publishing a *library* is a different lifecycle: your consumers are
other repositories you don't control, on their own upgrade schedule, and the concerns are
semver discipline, binary compatibility, and public-surface visibility (`api` vs
`implementation`) — none of which apply to an app's own internal module graph. A backend-only
project with zero mobile code could equally want to publish a Kotlin library; labelling this
guidance `mobile` would make it unfindable from that context.

## What goes here

- KMP library module structure and Maven publishing mechanics
- `api` vs `implementation` dependency visibility discipline for a published public surface
- Kotlin/JS → npm export mechanics (`.d.ts` generation, ES modules, `@JsExport` constraints)
- Binary-compatibility validation tooling
- Anything else specific to *packaging code for external consumption*, regardless of which
  consuming platform (mobile, backend, web) ends up depending on the published artifact

## What does NOT go here

- How to structure KMP code inside an app you're shipping directly (→ `platforms/mobile/kmp.md`)
- Semver policy and breaking-change philosophy in the abstract (→ `core/api-stability.md`)
- How to *consume* a published library (→ the relevant platform's own docs)

## Document ID prefix: `PLAT-LIB-`
