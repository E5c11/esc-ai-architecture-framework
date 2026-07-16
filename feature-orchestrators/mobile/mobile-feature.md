---
id: ORCH-MOB-FEAT
type: orchestrator
layer: feature-orchestrators
platform: [mobile]
architecture: [pragmatic-clean]
goal: "Implement a complete mobile feature module with all Pragmatic Clean layers wired and tested"
requires:
  - CORE-DI
  - CORE-SSOT
  - CORE-ERROR
  - CORE-NAMING
  - CORE-TESTING
  - CORE-COUPLING
  - PAT-DATA-ACCESS
  - PAT-OUTCOME
  - PAT-OBSERVER
  - ARCH-PC
  - ARCH-PC-DATASOURCE
  - ARCH-PC-REPOSITORY
  - ARCH-PC-USECASE
  - ARCH-PC-VIEWMODEL
  - ARCH-PC-VIEW
  - ARCH-PC-DI
  - ARCH-PC-ERROR-FLOW
  - ARCH-PC-FEATURE
  - PLAT-MOB-KMP
  - PLAT-MOB-KOIN
  - PLAT-MOB-KOTLIN
  - PLAT-MOB-COMPOSE
related: [QG-REVIEW, QG-TESTING]
tags: [mobile, feature, pragmatic-clean, kmp, scaffold, end-to-end]
---

# Implement Mobile Feature (Pragmatic Clean)

## Goal

Produce a complete, tested, DI-wired feature module. Every layer is implemented
in dependency order: DataSource → Repository → UseCase → ViewModel → View.

## Loading strategy

Load docs progressively — fetch only what each phase needs, not all 22 upfront.

1. Read this orchestrator to understand all phases and their scope.
2. Before each phase, run:
   ```
   python tools/lookup.py --orchestrator ORCH-MOB-FEAT --phase N [--profile context/project-profile.yaml]
   ```
   This returns the 4-6 docs for that phase only, sorted by layer.
3. Implement the phase. Run its validation checklist. Commit.
4. Discard the phase docs before loading the next phase.

The `requires` list in this document's frontmatter is for validation tooling only — not a loading instruction.

---

## Phase 1 — Scaffold

**Required framework docs:** `ARCH-PC-FEATURE`, `PLAT-MOB-KMP`, `BUILD-CONVENTION-PLUGINS`, `BUILD-PROJECT-STRUCTURE`
**Code paths:** `settings.gradle.kts`, `:feature:{name}/build.gradle.kts`
**Assumes:** Nothing — this is the first phase.
**Produces:** Empty, compiling feature module registered in the build.

### Steps

1. Create the module directory at `:feature:{name}/`
2. Create `build.gradle.kts` applying `{project}.kmp.feature` convention plugin;
   add `alias(libs.plugins.kover)`; declare dependencies on required `:core:*` modules
3. Register the module in `settings.gradle.kts` in alphabetical order within the `feature:` group
4. Create the base package structure:
   ```
   src/commonMain/kotlin/{package}/{feature}/
   ├── data/
   │   ├── datasource/
   │   └── repository/
   ├── domain/
   │   ├── model/
   │   └── usecase/
   └── presentation/
       ├── viewmodel/
       └── view/
   ```
5. Create an empty DI module file: `{Feature}Module.kt` in `di/`

### Validation

- [ ] `./gradlew :{feature}:compileKotlinMetadata` passes
- [ ] Module appears in `settings.gradle.kts`
- [ ] No source files yet (scaffold only)

---

## Phase 2 — DataSource layer

**Required framework docs:** `ARCH-PC-DATASOURCE`, `PAT-DATA-ACCESS`, `PAT-OUTCOME`, `PLAT-MOB-KOTLIN`, `ARCH-PC-ERROR-FLOW`
**Provider docs (load one based on project profile):** `PLAT-MOB-ROOM` (local cache), `PLAT-MOB-HTTP` (REST), `PLAT-MOB-FIREBASE` (Firebase)
**Code paths:** `domain/model/`, `domain/datasource/`, `data/datasource/`
**Assumes:** Phase 1 complete — module compiles.
**Produces:** Domain models, DataSource interfaces and implementations, DataSource unit tests.

### Steps

1. Define the domain model(s) in `domain/model/` — plain Kotlin data classes, no framework imports
2. Define the DataSource interface(s) in `domain/datasource/`:
   - Remote DataSource interface: `{Feature}RemoteDataSource`
   - Local DataSource interface: `{Feature}LocalDataSource` (if persistent)
3. Implement `{Feature}RemoteDataSourceImpl` in `data/datasource/`:
   - All methods return `Outcome<T>` or equivalent typed result
   - Map provider exceptions to domain types at this boundary (ARCH-PC-DS-EXCEPTION-01)
   - Map provider DTOs to domain models at this boundary (ARCH-PC-DS-MAPPING-01)
4. Implement `{Feature}LocalDataSourceImpl` in `data/datasource/` (if persistent)
5. Write unit tests for each DataSource implementation

### Validation

- [ ] DataSource interfaces declare only domain types — no provider SDK types
- [ ] All DataSource methods return `Outcome<T>` or `Flow<Outcome<T>>`
- [ ] Exceptions from the provider are caught and mapped inside the DataSource (ARCH-PC-DS-EXCEPTION-01)
- [ ] Unit tests cover: success path, all error conditions, empty collection
- [ ] Tests pass: `./gradlew :{feature}:testDebugUnitTest`

---

## Phase 3 — Repository layer

**Required framework docs:** `ARCH-PC-REPOSITORY`, `CORE-SSOT`, `PAT-OBSERVER`
**Code paths:** `domain/repository/`, `data/repository/`
**Assumes:** Phase 2 complete — DataSource interfaces and implementations exist.
**Produces:** Repository interface and implementation, Repository unit tests.

> **Skip this phase if** there is only one DataSource and no coordination is needed.
> Inject the DataSource directly into the UseCase instead.

### Steps

1. Define `{Feature}Repository` interface in `domain/repository/`
2. Implement `{Feature}RepositoryImpl` in `data/repository/`:
   - Expose a `Flow` of the local DataSource as the observable truth
   - On fetch: write to local DataSource; never return remote data directly
   - On write: update remote first, then sync to local on success
3. Write unit tests for the Repository (mock both DataSources)

### Validation

- [ ] Repository interface is in `domain/`; implementation is in `data/`
- [ ] `Flow` observed by callers comes from the local DataSource only (ARCH-PC-REP-SSOT-01)
- [ ] Remote DataSource is never directly observed (ARCH-PC-REP-SSOT-02)
- [ ] Tests verify that local is updated after a successful remote write
- [ ] Tests pass

---

## Phase 4 — UseCase layer

**Required framework docs:** `ARCH-PC-USECASE`, `PAT-OUTCOME`, `CORE-ERROR`, `ARCH-PC-ERROR-FLOW`
**Code paths:** `domain/usecase/`
**Assumes:** Phase 3 complete (or Phase 2 if Phase 3 was skipped) — Repository or DataSource interface exists.
**Produces:** One UseCase class per distinct business operation, with unit tests.

### Steps

1. Create one UseCase class per distinct business operation in `domain/usecase/`
2. Each UseCase has a single public method (`invoke()` or a named `execute*()`)
3. UseCase returns `Outcome<T>` or `Flow<T>` to its caller
4. UseCase maps Repository errors to domain-level errors
5. Write unit tests for each UseCase (mock the Repository)

### Validation

- [ ] No Android, Compose, or Koin imports in UseCase classes
- [ ] Each UseCase has exactly one public callable method
- [ ] UseCase handles all Repository error states — no unhandled `Outcome.Failure`
- [ ] Tests cover: success, each error condition, edge cases
- [ ] Tests pass

---

## Phase 5 — ViewModel layer

**Required framework docs:** `ARCH-PC-VIEWMODEL`, `PLAT-MOB-KOTLIN`, `PLAT-MOB-KOIN`
**Code paths:** `presentation/viewmodel/`
**Assumes:** Phase 4 complete — UseCase interfaces exist.
**Produces:** State class, Event sealed class, ViewModel with unit tests.

### Steps

1. Create `{Feature}State` data class in `presentation/viewmodel/`
2. Create `{Feature}Event` sealed class for one-shot events (navigation, toasts)
3. Create `{Feature}ViewModel` extending the base ViewModel class:
   - Expose state as `StateFlow<{Feature}State>` (immutable to callers)
   - Expose events as `SharedFlow<{Feature}Event>` (hot, replay = 0)
   - Inject UseCases via constructor
   - Store launched `Job` references; cancel in `onCleared()`
4. Write unit tests for the ViewModel (mock UseCases; use `TestCoroutineDispatcher`)

### Validation

- [ ] ViewModel exposes only `StateFlow` and `SharedFlow` — no `MutableStateFlow`
- [ ] All coroutine Jobs are tracked and cancelled in `onCleared()`
- [ ] No View or Compose imports in the ViewModel
- [ ] Tests verify: state transitions on success, state on error, events emitted
- [ ] Tests pass

---

## Phase 6 — View layer

**Required framework docs:** `ARCH-PC-VIEW`, `PLAT-MOB-COMPOSE`, `PLAT-MOB-NAV`
**Code paths:** `presentation/view/`, app-level NavGraph
**Assumes:** Phase 5 complete — ViewModel, State, and Event types exist.
**Produces:** Screen composable, stateless View composable, navigation registration.

### Steps

1. Create `{Feature}Screen.kt` — the Composable entry point that collects state
   and wires the scaffold
2. Create `{Feature}View.kt` — stateless, receives data via parameters, emits
   actions via callbacks
3. Collect ViewModel state via `collectAsStateWithLifecycle()`
4. Collect events via `LaunchedEffect` and handle navigation/toasts
5. Register the destination in the app NavGraph (see `PLAT-MOB-NAV`)

### Validation

- [ ] Single `Scaffold` per screen (ARCH-PC-VIEW-SCAFFOLD-01)
- [ ] Top bar claimed with token and released in `onDispose` (ARCH-PC-VIEW-SCAFFOLD-03)
- [ ] No ViewModel construction in Composables — ViewModel injected via Koin
- [ ] No business logic in Composables
- [ ] `{Feature}View` is stateless — no ViewModel or UseCase references
- [ ] Preview Composables exist for the main View component

---

## Phase 7 — DI registration

**Required framework docs:** `ARCH-PC-DI`, `PLAT-MOB-KOIN`
**Code paths:** `di/{Feature}Module.kt`, app-level `initKoin()`
**Assumes:** Phases 2–6 complete — all concrete types exist.
**Produces:** Fully wired Koin module; app starts without `NoBeanDefinitionException`.

### Steps

1. In `{Feature}Module.kt`:
   - Bind DataSource interfaces to implementations (`single { }`)
   - Bind Repository interface to implementation (`single { }`)
   - Bind UseCases (`factory { }` or `factoryOf(::UseCaseName)`)
   - Declare ViewModel with `viewModelOf(::FeatureViewModel)`
2. Register `{feature}Module()` in the app's Koin module list in `initKoin()`

### Validation

- [ ] All DI bindings use interfaces, not concrete types (CORE-DI)
- [ ] ViewModel declared with the correct Koin scope (ARCH-PC-DI)
- [ ] Module follows naming convention: `fun {feature}Module()` (PLAT-MOB-KOIN-MOD-02)
- [ ] App starts without `NoBeanDefinitionException`

---

## Phase 8 — Coverage and static analysis

**Required framework docs:** `BUILD-COVERAGE`, `BUILD-STATIC-ANALYSIS`, `QG-TESTING`
**Code paths:** `:{feature}/build.gradle.kts`, `detekt-baseline.xml` (if needed)
**Assumes:** All prior phases complete and passing.
**Produces:** Module meeting coverage and lint quality gates; ready for merge.

### Steps

1. Apply Kover exclusions in `build.gradle.kts` — standard exclusion list from `BUILD-COVERAGE`
2. Set minimum coverage threshold (`minValue = 80`)
3. Run `./gradlew :{feature}:koverVerify`
4. Run `./gradlew :{feature}:detekt`
5. Fix any violations

### Validation

- [ ] `koverVerify` passes at ≥ 80% threshold
- [ ] `detekt` passes with zero new violations
- [ ] `detekt-baseline.xml` committed if pre-existing violations were baselined
