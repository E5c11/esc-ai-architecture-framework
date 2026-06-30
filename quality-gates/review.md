---
id: QG-REVIEW
type: guide
layer: quality-gates
platform: [all]
architecture: [all]
requires: [CORE-DI, CORE-COUPLING, CORE-ERROR, CORE-NAMING, CORE-SSOT]
related: [QG-TESTING, BUILD-COVERAGE, BUILD-STATIC-ANALYSIS]
tags: [review, checklist, pre-merge, code-review, enforcement]
---

# Code Review Checklist

## Enforcement model

Rules across this framework specify an `enforced_by` role. This checklist maps
those roles to the review process:

| Role | When |
|---|---|
| `planner` | Before designing the approach — check architecture and dependency direction |
| `executor` | While writing code — check rule compliance layer by layer |
| `reviewer` | Before merge — check this document |
| `ci` | Automated in the pipeline — check build output |

A reviewer who finds a `planner` or `executor` violation is catching it late.
The earlier a violation is caught, the cheaper it is to fix.

## Universal checks (all platforms, all architectures)

### Dependency direction (CORE-DI)
- [ ] Inner layers do not import from outer layers
- [ ] Abstractions are depended upon; concretions are injected, not constructed
- [ ] No `new ConcreteClass()` inside a layer that is supposed to receive it via DI

### Coupling (CORE-COUPLING)
- [ ] No module-level circular dependencies
- [ ] Classes depend on interfaces, not sibling implementations
- [ ] No feature module importing another feature module directly

### Error handling (CORE-ERROR)
- [ ] Errors at boundaries are typed, not swallowed
- [ ] No empty `catch` blocks
- [ ] Errors are mapped at the layer boundary, not re-thrown as generic exceptions

### Naming (CORE-NAMING)
- [ ] Names describe the role, not the implementation
- [ ] No abbreviations that require context to decode
- [ ] Consistent suffix usage per role (`Entity`, `Service`, `Controller`, `DataSource`, `Repository`, `ViewModel`, `UseCase`)

### SSOT (CORE-SSOT)
- [ ] Local source is authoritative; remote feeds it, not bypasses it
- [ ] No two sources of truth for the same domain data

### Testing
- [ ] New logic has tests
- [ ] Tests verify behaviour, not implementation
- [ ] No test that passes with a broken implementation (tests actually fail when they should)
- [ ] Build passes `koverVerify` / coverage gate
- [ ] Build passes `detekt` / static analysis

---

## Mobile — Pragmatic Clean (ARCH-PC)

### DataSource
- [ ] DataSource interface is in `domain/` or `data/`; implementation is in the platform module
- [ ] DataSource returns `Outcome<T>` or equivalent typed result — no raw exceptions
- [ ] Remote never observed directly (REP-SSOT-01, REP-SSOT-02)
- [ ] Exception wrapping happens at the DataSource boundary (DS-EXCEPTION-01)

### Repository
- [ ] Repository interface injected, not concrete class
- [ ] Local DataSource is the single observed source of truth
- [ ] Remote only writes to local; local is never bypassed

### UseCase
- [ ] One public `invoke()` or `execute()` method
- [ ] Returns typed outcome — no unhandled exceptions escaping the boundary
- [ ] Contains no Android/platform imports

### ViewModel
- [ ] Exposes `StateFlow` / `SharedFlow`; never mutable state to the View
- [ ] `Job` references stored and cancelled in `onCleared`
- [ ] No UI framework imports in the ViewModel

### View
- [ ] State consumed via `collectAsStateWithLifecycle`
- [ ] Single `Scaffold` per screen
- [ ] No business logic; no direct ViewModel construction

### DI (ARCH-PC-DI)
- [ ] Correct scope for each binding (`activityScopedViewModel`, `single`, `factory`)
- [ ] Platform-specific bindings in platform modules; shared interfaces in shared modules

---

## Backend — Backend-Service (ARCH-BE)

### Controller
- [ ] Zero business logic (CTRL-LOGIC-01)
- [ ] Returns DTO — never a JPA entity (CTRL-RETURN-01)
- [ ] `@Valid` on all `@RequestBody` parameters (CTRL-VALIDATION-01)
- [ ] Status codes via `HttpStatus` enum, not raw integers (CTRL-STATUS-01)
- [ ] Constructor injection only — no `@Autowired` fields (CTRL-INJECT-01)
- [ ] Path via constants, no literal `/v1` strings (CTRL-PATH-01)

### Service
- [ ] No `Instant.now()` — uses `timeProvider.now()` (SVC-TIME-01)
- [ ] Returns DTOs — never JPA entities (SVC-RETURN-01)
- [ ] Write methods annotated `@Transactional` (SVC-TX-01, SVC-TX-02)
- [ ] Known errors throw `ResponseStatusException` (SVC-ERROR-01)
- [ ] Constructor injection only (SVC-INJECT-01)

### DataSource
- [ ] Custom wrapper only when warranted by REP-WHEN-01
- [ ] Wrapper has an interface (REP-INTERFACE-01)
- [ ] No `@Transactional` on DataSource methods (REP-TX-01)
- [ ] Returns entities — never DTOs (REP-RETURN-01)

### Entity
- [ ] Migration present in same commit (ENT-MIGRATION-01)
- [ ] UUID primary key (ENT-ID-01)
- [ ] Both timestamp fields present (ENT-TIMESTAMP-01)
- [ ] Not a `data class`; `equals`/`hashCode` on `id` only (ENT-EQUALS-01)
- [ ] No business logic on the entity (ENT-LOGIC-01)

### Error handling
- [ ] Known errors thrown as `ResponseStatusException` from service (ERR-KNOWN-01)
- [ ] `GlobalExceptionHandler` exists and logs unexpected errors (ERR-UNKNOWN-01, ERR-LOG-01)
- [ ] All error responses use `ErrorResponse(status, message)` (ERR-RESPONSE-01)

---

## Web — Web SPA (ARCH-WEB)

### Components
- [ ] Container guards loading, error, and data before rendering (ARCH-WEB-CP-01)
- [ ] No Firebase/API calls inside components (ARCH-WEB-DEP-01)
- [ ] Props contain only fields the component uses (ARCH-WEB-PROPS-01)
- [ ] Every page-level route wrapped in `ErrorBoundary` (ARCH-WEB-EB-01)

### TypeScript
- [ ] Build passes `tsc -b` with zero errors (PLAT-WEB-TS-STRICT-01)
- [ ] No `any` (PLAT-WEB-TS-ANY-01)
- [ ] All `useEffect` subscriptions return cleanup (PLAT-WEB-TS-CLEANUP-01)
- [ ] Firestore types declared in `src/types/firestore.ts` (PLAT-WEB-FB-TYPES-01)

### Styling
- [ ] No raw hex values in components — imports from `colors.*` (PLAT-WEB-STYLE-TOKEN-01)
- [ ] Style constants defined after the component, not inside the function (PLAT-WEB-STYLE-SCOPE-01)

### Accessibility
- [ ] Semantic HTML elements used (PLAT-WEB-A11Y-SEMANTIC-01)
- [ ] All `<img>` have `alt` (PLAT-WEB-A11Y-ALT-01)
- [ ] Icon-only interactive elements have `aria-label` (PLAT-WEB-A11Y-ARIA-01)
- [ ] One `<h1>` per page; no skipped heading levels (PLAT-WEB-A11Y-HEADING-01)
- [ ] Focus ring not removed without replacement (PLAT-WEB-A11Y-FOCUS-01)

---

## Build system

- [ ] No raw coordinate strings in module build files — uses version catalog (BUILD-VC-ADD-01)
- [ ] No `compileOnly` declared as `implementation` in convention plugins (BUILD-CP-DEPS-01)
- [ ] New module registered in `settings.gradle.kts` (BUILD-PS-REG-01)
- [ ] Coverage threshold not lowered (BUILD-COV-THRESH-03)
- [ ] Standard Kover exclusions applied to new module (BUILD-COV-EXCL-01)
