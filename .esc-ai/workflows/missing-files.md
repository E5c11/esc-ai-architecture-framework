# Missing Framework Documents

Entries state whether a stub already exists or a file still needs to be created. Complete
and validate the document before moving it to a completed section.

---

## High priority

### `platforms/mobile/design-system/component.md` — checklist items never defined as rules
Surfaced by `check_rule_citations` after the rule-embedding migration
(`workflows/archive/rule-embedding-migration.md`). `component.md` documents
~17 requirements as inline checklist bullets (`- **DS-STRUCTURE-01:** ...`,
`DS-A11Y-01..03`, `DS-M3-01..02`, `DS-KMP-01`, `DS-STRUCTURE-01..08`) that
never matched the canonical `**Rule ID (type):** statement` format, so they
were never real rule definitions — citations to them from `icons.md`,
`images.md`, `quality-gates/review.md`, and `feature-orchestrators/mobile/mobile-feature.md`
have always been unresolved, just never checked before. Needs each item
converted to a proper ```rule block (deciding `type`/`scope` per item) — real
authorship, not a mechanical fix. `platforms/mobile/design-system/images.md`
has the same issue for `DS-IMAGE-03/04/05`.

### `PLAT-WEB-NEXT-CONTENT` + deploy doc, `ORCH-WEB-CONTENT` — `web-content` still has no consuming project
Registered while authoring `workflows/active/web-platform-docs.md`, which
closed the rest of the "Next.js platform docs, quality gate, and
orchestrators" gap (`PLAT-WEB-NEXT`, `PLAT-WEB-NEXT-APP` + deploy doc,
`PLAT-WEB-HTTP`, `PLAT-WEB-FORMS`, the `platforms/web/design-system/` set,
`QG-WEB-TESTING`, `ORCH-WEB-APP`, and the web `PROFILE_DOC_MAP` entries — see
"Completed" below). Explicitly re-registered, not authored, for the same
reason `content-dashboard.md` §8 deferred its own AMPM CRUD-lifecycle doc: no
project consumes `web-content` today (unlike `web-app`, which
`ampm-backend`'s content dashboard uses right now), so writing these now
risks documenting a guess instead of a real usage pattern. Still needed:

- `PLAT-WEB-NEXT-CONTENT` (`platforms/web/nextjs-content.md`) + its deploy
  doc `PLAT-WEB-NEXT-CONTENT-DEPLOY` (`platforms/web/nextjs-content-deploy.md`).
- `ORCH-WEB-CONTENT` (`feature-orchestrators/web/content-feature.md`).

### Layer-specific unit test guides
No actionable test guides exist for any architecture layer. The framework has
philosophy (`CORE-TESTING`, `QG-TESTING`) but nothing that tells an agent how
to wire fakes, test Flows and Outcome, use Turbine/MockK, or name test functions.

Files to create:
- `quality-gates/mobile-unit-tests.md` — covering DataSource, Repository, UseCase, ViewModel
- `quality-gates/compose-ui-tests.md` — Compose UI test patterns, test tags, semantics
- `quality-gates/integration-tests.md` — end-to-end test setup, test doubles, CI wiring

---

## Medium priority

### Navigation — `platforms/mobile/navigation.md` (PLAT-MOB-NAV)
**Status: stub.** Open question: confirm split with `ARCH-PC-VIEW` (which owns Scaffold rules).
Resolve before writing.

## Low priority

### App-level ViewModel — `architectures/pragmatic-clean/app-viewmodel.md` (ARCH-PC-APP-VM)
**Status: stub.** Covers AppState contract, top-bar token pattern, scaffold coordination.

### Skeleton loading — `platforms/mobile/skeleton-loading.md` (PLAT-MOB-SKELETON)
**Status: stub.**

## Completed (Next.js platform docs, quality gate, and ORCH-WEB-APP, 2026-07-17)

Closed the `web-app`-blocking part of the gap registered while authoring
`workflows/archive/nextjs-web-architectures.md` — driven by `ampm-backend`'s
`plan/content-dashboard.md` §3 naming `PLAT-WEB-HTTP`, `PLAT-WEB-FORMS`, and
`PLAT-WEB-NEXT-APP` specifically as blocking its data-fetching/mutation layer
and question-authoring forms. `PLAT-WEB-NEXT-CONTENT` + deploy doc and
`ORCH-WEB-CONTENT` were re-registered above rather than authored — no
project consumes `web-content` yet.

| Doc ID | File | Notes |
|--------|------|-------|
| `PLAT-WEB-NEXT` | `platforms/web/nextjs.md` | App Router routing/layouts, Server/Client boundary, env var convention, `middleware.ts` — shared by `web-app` and `web-content` |
| `PLAT-WEB-NEXT-APP` | `platforms/web/nextjs-app.md` | Return-not-throw Server Action pattern, `revalidatePath`/`revalidateTag`, Route Handler vs. Server Action guidance |
| `PLAT-WEB-NEXT-APP-DEPLOY` | `platforms/web/nextjs-app-deploy.md` | Docker `standalone` build, Cloud Run domain mapping/TLS, connection-pool sizing on a scale-to-zero host |
| `PLAT-WEB-HTTP` | `platforms/web/http-client.md` | `fetch`-based executor, header provider, retry policy, typed error mapping, DI registration, fake/MSW testing split |
| `PLAT-WEB-FORMS` | `platforms/web/forms.md` | One zod schema per discriminated content variant, client/server schema reuse, `fieldErrors` → `setError` mapping |
| `PLAT-WEB-DS-THEME` | `platforms/web/design-system/theme.md` | `tailwind.config.ts` tokens, dark mode via class strategy |
| `PLAT-WEB-DS-COMPONENT` | `platforms/web/design-system/component.md` | `components/ui/` promotion threshold, Server-vs-Client default for shared components |
| `PLAT-WEB-DS-ICONS` | `platforms/web/design-system/icons.md` | Centralized icon module, sizing/accessibility |
| `QG-WEB-TESTING` | `quality-gates/web-testing.md` | Vitest/RTL baseline, Server Action testing, MSW at the Provider boundary, middleware-gated auth E2E |
| `ORCH-WEB-APP` | `feature-orchestrators/web/app-feature.md` | Seven-phase orchestrator mirroring `ORCH-WEB-FEAT`'s shape for `ARCH-WEB-APP`'s layers |

`schemas/project-profile.yaml` bumped to `1.1` (`frameworks.forms` field);
`tools/lookup.py`'s `PROFILE_DOC_MAP` gained its first web entries
(`fetch`/`axios` → `PLAT-WEB-HTTP`, `next` → `PLAT-WEB-NEXT`,
`react-hook-form` → `PLAT-WEB-FORMS`). `PLAT-WEB-A11Y` was deliberately left
`web-spa`-only rather than broadened — see `ORCH-WEB-APP`'s closing note for
why its container-guard/`ErrorBoundary` rules don't transfer to `web-app`.

## Completed (migrated from AMPM agents/instructions)

These were created during the AMPM → esc-ai-framework (now esc-ai-architecture-framework)
migration. They are generic enough
to reuse across projects and now live in `platforms/mobile/`.

| Doc ID | File | Notes |
|--------|------|-------|
| `PLAT-MOB-NOTIF` | `platforms/mobile/notifications.md` | WorkManager, NotificationScheduler, ClockProvider, stable IDs, DI, testing |
| `PLAT-MOB-DATASTORE` | `platforms/mobile/datastore.md` | Key definitions, read/write patterns, FakeDataStore, required test scenarios |
| `PLAT-MOB-HUAWEI` | `platforms/mobile/huawei.md` | Flavor dimensions, source set hierarchy, DI override, REST layer, unit tests |
| `PLAT-MOB-KMP-WEB` | `platforms/mobile/kmp-web-target.md` | Source set rules, KeyValueStorage, UUID rule, NoOp pattern, wasmJs Koin module |
| `PLAT-MOB-DS-COMPONENT` | `platforms/mobile/design-system/component.md` | M3 wrapper rules, component signature template, accessibility, previews |
| `PLAT-MOB-DS-THEME` | `platforms/mobile/design-system/theme.md` | DS-THEME-01 through DS-THEME-10 rules, Spacing/Corners/Elevations, Alpha constants |
| `PLAT-MOB-DS-ICONS` | `platforms/mobile/design-system/icons.md` | AppIcons singleton, ImageVector, DS-ICON rules, touch targets |
| `PLAT-MOB-DS-IMAGES` | `platforms/mobile/design-system/images.md` | Coil abstraction, AppAsyncImage/AppCircularImage, placeholder types, KMP engine split |

---

## Completed (arrow-http library-platform gap analysis, 2026-07-10)

Triggered by evaluating `arrow-http` (a published KMP HTTP library) as the transport for a
future generated API-client codegen pipeline. Surfaced that the framework had no vocabulary
for "publishing a library" as distinct from "building mobile/backend/web apps" — added a new
`library` platform (see `schemas/document.yaml` v1.1 and `platforms/library/README.md`) —
and that `PLAT-MOB-HTTP` had sat as an empty stub despite a real, working reference
implementation existing to write it from.

| Doc ID | File | Notes |
|--------|------|-------|
| `CORE-API-STABILITY` | `core/api-stability.md` | Semver discipline, additive-only public API evolution, default-vs-abstract interface method rule |
| `PLAT-LIB-KMP` | `platforms/library/kmp-packaging.md` | `api`/`implementation` visibility, Maven Central publishing, worked example from `arrow-http`'s real build config |
| `PLAT-MOB-HTTP` | `platforms/mobile/http-client.md` | Previously a stub — written for real using `arrow-http` (`HeaderProvider`/`AuthRefresher`/`RetryPolicy`/`HttpException` hierarchy) as the reference implementation |
| `PLAT-LIB-JS-EXPORT` | `platforms/library/js-npm-export.md` | Written for real from `arrow-http` 1.2.0's Phase 2 spike: verified Gradle DSL, per-type `@JsExport` results (including the hard `suspend fun` export blocker), the critical finding that `@JsExport` breaks non-`js` targets if placed in `commonMain`, the `webMain`/default-hierarchy-template conflict, and two Kotlin Gradle plugin bugs (KT-69996 and a `rootPackageJson` collision) that only surface with `js`+`wasmJs` together |

---

## Completed (KMP iOS platform coverage, 2026-07-15)

| Doc ID | File | Notes |
|--------|------|-------|
| `ARCH-PC-ERR-CLASSES` | `architectures/pragmatic-clean/exception-classes.md` | Portable typed errors, provider-boundary mapping, cancellation and presentation metadata |
| `PLAT-MOB-KMP-IOS` | `platforms/mobile/kmp-ios.md` | Apple target graph, source sets, framework/Xcode bootstrap, NoOp policy and validation ladder |
| `PLAT-MOB-SECURE-STORAGE` | `platforms/mobile/secure-storage.md` | Keychain/keystore boundary, accessibility, deletion and tests |
| `PLAT-MOB-IOS-INTEROP` | `platforms/mobile/ios-interop.md` | UIKit lifecycle, permissions, system actions, photos, rating and orientation |
| `PLAT-MOB-IOS-AUTH` | `platforms/mobile/ios-auth.md` | OAuth callbacks/state, cancellation and secure sessions |
| `PLAT-MOB-IOS-BILLING` | `platforms/mobile/ios-billing.md` | StoreKit outcomes, transaction lifecycle and verified entitlements |
| `BUILD-APPLE-CI` | `build/apple-ci.md` | macOS compile/link/Xcode ladder and protected signing |
| `QG-MOB-NATIVE` | `quality-gates/mobile-native-tests.md` | Native/simulator integration layers, isolation and coverage limits |
| `ORCH-MOB-IOS` | `feature-orchestrators/mobile/ios-port.md` | Phase-by-phase published-dependency-to-archive port workflow |

Existing Koin, Room, Firebase, DataStore, notifications, images, build and profile/lookup
documents were expanded for Apple/Native behavior in the same change.

---

## AMPM-specific (belongs in `AMPM/ampm-ai-framework/`, not here)

These were identified during the gap analysis as project-specific. They live in
`AMPM/ampm-ai-framework/` using the `AMPM-` ID prefix.

| Doc ID | File | Notes |
|--------|------|-------|
| `AMPM-SUBJ-STRUCT` | `ampm-ai-framework/subject/subject-module-structure.md` | Subject-first architecture, `:feature:{subject}` naming, data-driven nav |
| `AMPM-TIER-CAP` | `ampm-ai-framework/tier/tier-capabilities.md` | SubscriptionTier, AppFeature, TierCapabilities, sealed state pattern |
| `AMPM-SYNC-OFFLINE-QUEUE` | `ampm-ai-framework/sync/offline-retry-queue.md` | **Resolved 2026-08-10** (was stub). Generic outbox design: one shared `OutboxEntryEntity` table + one worker drive retries for all four Pattern B tables (`user_answers`/`user_sessions`/`video_completions`/`video_sessions`), each contributing only a small per-`opType` retry adapter — not four bespoke per-table sweeps (an earlier pass proposed that, rejected on review as not befitting a `pragmatic-clean` framework doc). App-foreground trigger, fixed retry cap + retryable/permanent classification, no time-based backoff. `video_sessions` still needs a stable client-generated session ID as a correctness prerequisite, independent of this design. Spec unblocks `ampm-kmp` item 1b; implementation not yet started. |
