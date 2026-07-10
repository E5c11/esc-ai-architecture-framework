# Missing Framework Documents

Stubs exist for all entries marked as pending. Each stub contains an outline of what the
document must cover. Write the full content before removing the entry from this list.

---

## High priority

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

### Exception class definitions — `architectures/pragmatic-clean/exception-classes.md` (ARCH-PC-ERR-CLASSES)
**Status: stub.** Blocker: determine whether the base exception type comes from:
(a) project-defined KMP common code, (b) Arrow error types, or (c) a custom
`arrow-errors` library owned by the project author. The implementation guide depends
on this answer.

---

## Low priority

### App-level ViewModel — `architectures/pragmatic-clean/app-viewmodel.md` (ARCH-PC-APP-VM)
**Status: stub.** Covers AppState contract, top-bar token pattern, scaffold coordination.

### Skeleton loading — `platforms/mobile/skeleton-loading.md` (PLAT-MOB-SKELETON)
**Status: stub.**

### Koin feature module setup — `platforms/mobile/koin.md` (PLAT-MOB-KOIN)
**Status: partial.** TODO section added to the existing document. The feature module
setup phase (factory registrations, viewModel block, module includes) needs to be
expanded into a full guide.

---

## Completed (migrated from AMPM agents/instructions)

These were created during the AMPM → esc-ai-framework migration. They are generic enough
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

## AMPM-specific (belongs in `AMPM/ampm-ai-framework/`, not here)

These were identified during the gap analysis as project-specific. They live in
`AMPM/ampm-ai-framework/` using the `AMPM-` ID prefix.

| Doc ID | File | Notes |
|--------|------|-------|
| `AMPM-SUBJ-STRUCT` | `ampm-ai-framework/subject/subject-module-structure.md` | Subject-first architecture, `:feature:{subject}` naming, data-driven nav |
| `AMPM-TIER-CAP` | `ampm-ai-framework/tier/tier-capabilities.md` | SubscriptionTier, AppFeature, TierCapabilities, sealed state pattern |
