---
id: ORCH-WEB-APP
type: orchestrator
layer: feature-orchestrators
platform: [web]
architecture: [web-app]
goal: "Implement a complete web-app feature layer by layer (domain, DataSource, UseCase, Hook, Component, route), for either runtime, with each layer tested against the layer below's fake"
requires:
  - CORE-COUPLING
  - CORE-NAMING
  - CORE-TESTING
  - ARCH-WEB-APP-LAYERS
  - PLAT-WEB-NEXT
  - PLAT-WEB-REACT
  - PLAT-WEB-REACT-PATTERNS
  - PLAT-WEB-STATE
  - PLAT-WEB-FORMS
  - PLAT-WEB-DS-THEME
  - PLAT-WEB-DS-COMPONENT
  - PLAT-WEB-DS-ICONS
  - PLAT-WEB-A11Y
  - QG-WEB-TESTING
related: [QG-REVIEW, ORCH-WEB-FEAT, PLAT-WEB-NEXT-APP, PLAT-WEB-NEXT-DATA, PLAT-WEB-NEXT-STATIC, PLAT-WEB-NEXT-FIREBASE, PLAT-WEB-HTTP]
tags: [web, feature, nextjs, layers, datasource, usecase, hook, orchestrator, static-export, server]
status: active
---

# Implement Web-App Feature

## Goal

Produce a complete, typed feature: pure domain → DataSource (with its fake) → UseCase (only if
needed) → composition → Hook → Component → route, following `ARCH-WEB-APP`'s layer stack from the
inside out, with every layer tested against the fake of the layer below. The same phase-per-layer
shape `ORCH-WEB-FEAT` uses for `web-spa`, restated for `ARCH-WEB-APP`'s layers.

## Before you start

1. Read all documents listed in `requires` (`ARCH-WEB-APP-LAYERS` brings in the overview and every
   layer document).
2. Find the project's runtime: `frameworks.runtime` in its project profile
   (`ARCH-WEB-APP-RUNTIME-01`). Then also read the platform guides for it:
   - `server`: `PLAT-WEB-NEXT-APP`, `PLAT-WEB-NEXT-APP-DEPLOY`, `PLAT-WEB-NEXT-DATA`, `PLAT-WEB-HTTP`.
   - `static-export`: `PLAT-WEB-NEXT-STATIC`, `PLAT-WEB-NEXT-FIREBASE`.
   A profile passed to `tools/lookup.py --profile` adds these automatically.
3. Decide what the feature is: **read-only** (skip the form steps in Phases 1, 7), or **mutating**
   (needs a `PLAT-WEB-FORMS` schema and a form), and whether it needs a **UseCase** or a
   **Repository** at all (`ARCH-WEB-APP-USECASE-01`, `ARCH-WEB-APP-REPO-01`): most features need
   neither on the first pass.
4. Check the framework versions the project records (`PLAT-WEB-NEXT-VERSION-01`). Do not change them in
   this task.

Phases run in order. After each, the Validation list must hold before the next starts; if the project
has declared an architecture contract, run `esc-exec architecture check` at the end of Phases 2, 3, 6
and 7.

---

## Phase 1 — Domain and schema

**Goal:** The feature's vocabulary, rules and transforms exist as pure code with tests; if the feature
mutates data, its form schema exists.

Read: `ARCH-WEB-APP-DOMAIN`, `PLAT-WEB-FORMS` (mutating features only)

### Steps

1. Add entities, value objects and vocabularies in `features/{feature}/domain/`
   (`ARCH-WEB-APP-DOM-VOCAB-01`). Plain serialisable data only (`ARCH-WEB-APP-DOM-SERIAL-01`).
2. Write the pure functions the feature needs: rules, calculations, aggregations. Time and
   randomness are arguments (`ARCH-WEB-APP-DOM-CLOCK-01`); dates are explicit
   (`ARCH-WEB-APP-DOM-TIME-01`); results do not depend on input order
   (`ARCH-WEB-APP-DOM-DETERMINISM-01`).
3. If the feature mutates data, define one zod schema per content variant
   (`PLAT-WEB-FORMS-SCHEMA-01`).
4. Write the tests first or alongside: plain inputs, no doubles (`ARCH-WEB-APP-DOMAIN`'s Testing).

### Validation

- [ ] Domain files import no React, Next, provider SDK or other layer (`ARCH-WEB-APP-DEP-01`).
- [ ] No `any`; no `Date.now()`, `Math.random()` or ambient state in a domain function.
- [ ] Every rule table is complete for its vocabulary (`ARCH-WEB-APP-DOM-TABLE-02`).

---

## Phase 2 — DataSource interface, fake and contract

**Goal:** The feature's data boundary is an interface with an in-memory fake and a shared contract
test; nothing real is touched yet.

Read: `ARCH-WEB-APP-DATASOURCE`, `ARCH-WEB-APP-ERR-CLASSES`

### Steps

1. Write `{Entity}DataSource` in `features/{feature}/data/`, in domain types
   (`ARCH-WEB-APP-DS-INTERFACE-01`, `-MAPPING-01`). One-shot operations return
   `Promise<Outcome<T>>`; changing data is a subscription (`ARCH-WEB-APP-DS-RETURN-01`, `-02`).
2. Write `Fake{Entity}DataSource` and `{Entity}DataSource.contract.ts`, the tests both the fake and
   the real implementation must pass (`ARCH-WEB-APP-DS-TEST-01`).
3. Decide, for each lookup, what absence means (`null`, an empty list, or `notFound`:
   `ARCH-WEB-APP-DS-EMPTY-01`).

### Validation

- [ ] The interface mentions no provider type.
- [ ] The fake passes the contract tests.
- [ ] Bounded reads are declared (`ARCH-WEB-APP-DS-PAGE-01`).

---

## Phase 3 — DataSource implementation

**Goal:** The real implementation exists, passes the same contract, and is the only code that touches
the provider.

Read: `ARCH-WEB-APP-DATASOURCE`, then the runtime's guides: `PLAT-WEB-NEXT-FIREBASE` or `PLAT-WEB-HTTP`
and `PLAT-WEB-NEXT-APP`

### Steps

1. Implement it with the provider first in the name (`Firestore{Entity}DataSource`,
   `Http{Entity}DataSource`, `Callable{Action}DataSource`; `ARCH-WEB-APP-DS-NAMING-01`).
2. Parse every payload with a schema parser; never assert a type (`ARCH-WEB-APP-DS-PARSE-01`). A payload
   that fails parsing is an error naming the record (`ARCH-WEB-APP-DS-MALFORMED-01`).
3. Translate provider errors once, in one function, using the table in `PLAT-WEB-NEXT-FIREBASE` for
   Firestore and callables (`ARCH-WEB-APP-ERR-MAP-01`). Rethrow an abort.
4. **`server` runtime:** the DataSource is `server-only` (`ARCH-WEB-APP-COMPOSE-SPLIT-01`,
   `PLAT-WEB-NEXT-SERVERONLY-01`) and is called from a Server Action or Route Handler that returns an
   `Outcome` (`PLAT-WEB-NEXT-APP-THROW-01`); a mutating action invalidates what it changed
   (`PLAT-WEB-NEXT-APP-REVALIDATE-01`).
5. **`static-export` runtime:** no secrets (`ARCH-WEB-APP-RUNTIME-02`); write the security-rules tests
   for every read and write, with a case per role and a signed-out caller (`ARCH-WEB-APP-DS-RULES-01`,
   `PLAT-WEB-NEXT-FB-RULES-01`); a subscription starts only when called and is fully released
   (`ARCH-WEB-APP-DS-SUBSCRIBE-01`).

### Validation

- [ ] The implementation passes the contract tests against the provider's emulator or a network mock,
      never a mocked SDK.
- [ ] The provider SDK is imported here and in the composition module only (`ARCH-WEB-APP-DEP-03`).
- [ ] No expected failure rejects or throws (`ARCH-WEB-APP-DS-RETURN-01`).

---

## Phase 4 — Repository and UseCase (only if needed)

**Goal:** Logic that outgrew one DataSource call has a home; nothing is added that does not.

Read: `ARCH-WEB-APP-USECASE`, `ARCH-WEB-APP-REPOSITORY`

### Steps

1. Introduce a UseCase only when the feature's logic coordinates more than a single call
   (`ARCH-WEB-APP-USECASE-01`) and contains logic that justifies it (`ARCH-WEB-APP-UC-LOGIC-01`).
   One operation each, named in the domain's language (`ARCH-WEB-APP-UC-SINGLE-01`).
2. Introduce a Repository only when one entity is assembled from more than one DataSource
   (`ARCH-WEB-APP-REPO-01`).
3. Pass time and anything ambient in as arguments (`ARCH-WEB-APP-DOM-PURE-01`); hold no state between
   calls (`ARCH-WEB-APP-UC-STATELESS-01`).
4. State what a failed second write means (`ARCH-WEB-APP-UC-WRITE-01`); contain side effects
   (`ARCH-WEB-APP-UC-SIDE-01`).
5. Test against the DataSource fakes, covering every decision (`ARCH-WEB-APP-UC-TEST-01`).

### Validation

- [ ] Every UseCase contains logic; none only forwards a call.
- [ ] No UseCase calls another; an Orchestrator contains no branching (`ARCH-WEB-APP-UC-ORCH-01`, `-02`).
- [ ] A UseCase returns `Outcome` and no loading state (`ARCH-WEB-APP-UC-RETURN-01`).

---

## Phase 5 — Composition

**Goal:** The new objects are built in one place and reach Hooks through the context.

Read: `ARCH-WEB-APP-COMPOSITION`

### Steps

1. Register the DataSource (and Repository, UseCase) in `createApp` (`ARCH-WEB-APP-DEP-06`). Choose
   between implementations from configuration (`ARCH-WEB-APP-COMPOSE-CONFIG-01`).
2. Add any new configuration to `loadConfig`, validated, and nowhere else
   (`ARCH-WEB-APP-COMPOSE-CONFIG-01`).
3. Expose the new interface through the typed accessor (`ARCH-WEB-APP-COMPOSE-CONTEXT-01`).
   If the build can talk to more than one environment, the new object is built for the active one and
   rebuilt when it changes (`ARCH-WEB-APP-COMPOSE-ENV-01`).
4. **`server` runtime:** the server-only objects go in the server graph, never the client graph
   (`ARCH-WEB-APP-COMPOSE-SPLIT-01`).

### Validation

- [ ] Nothing runs on import; each SDK app is initialised once, on the client after mount
      (`ARCH-WEB-APP-COMPOSE-GLOBAL-01`, `PLAT-WEB-NEXT-FB-INIT-01`).
- [ ] A test can build its own graph with fakes (`ARCH-WEB-APP-COMPOSE-TEST-01`).

---

## Phase 6 — Hook

**Goal:** The screen's state, mapped and formatted for display, with the race handled.

Read: `ARCH-WEB-APP-HOOK`, `PLAT-WEB-REACT`, `PLAT-WEB-REACT-PATTERNS`

### Steps

1. Create `features/{feature}/hooks/use{Feature}.ts` (`ARCH-WEB-APP-HOOK-NAMING-01`) with an explicit
   return type exposing a `ViewState` union (`ARCH-WEB-APP-HOOK-STATE-01`).
2. Get the UseCase or DataSource interface from the composition context, never import an instance
   (`ARCH-WEB-APP-HOOK-DEPS-01`).
3. Map domain values to presentation shapes and format with an explicit locale and timezone
   (`ARCH-WEB-APP-HOOK-MAP-01`, `-FORMAT-01`).
4. Release the operation on unmount or input change and ignore a late result
   (`ARCH-WEB-APP-HOOK-RACE-01`); keep the full `AppError` and offer `retry`
   (`ARCH-WEB-APP-HOOK-ERROR-01`, `-02`).
5. If the hook wraps a form submit, map a `validation` error into `setError` (`PLAT-WEB-FORMS-ERR-01`).
6. **`server` runtime:** reach the server only through a Server Action or Route Handler
   (`ARCH-WEB-APP-DEP-04`).

### Validation

- [ ] The Hook imports no provider SDK and no implementation (`ARCH-WEB-APP-DEP-04`).
- [ ] No business rule is computed here (`ARCH-WEB-APP-HOOK-LOGIC-01`).
- [ ] Tested with `renderHook` inside a test provider with fakes (`ARCH-WEB-APP-HOOK-TEST-01`).

---

## Phase 7 — Components

**Goal:** The root view and its presentational components render every state.

Read: `ARCH-WEB-APP-COMPONENT`, `PLAT-WEB-DS-THEME`, `PLAT-WEB-DS-COMPONENT`, `PLAT-WEB-A11Y`

### Steps

1. Create `{Feature}View.tsx` as the only component that calls the Hook; `'use client'` goes on it and
   nowhere else (`ARCH-WEB-APP-COMP-SPLIT-01`, `PLAT-WEB-NEXT-CLIENT-01`).
2. Switch on every `ViewState` status exhaustively and choose the error presentation from the
   `AppError` variant (`ARCH-WEB-APP-COMP-STATE-01`, `ARCH-WEB-APP-EFLOW-PRESENT-01`).
3. Build presentational components from props and callbacks only (`ARCH-WEB-APP-COMP-PROPS-01`);
   no business state in `useState` (`ARCH-WEB-APP-COMP-LOCAL-01`).
4. Use semantic tokens and shared components and icons (`PLAT-WEB-DS-THEME-LAYER-01`,
   `PLAT-WEB-DS-COMPONENT-01`, `PLAT-WEB-DS-ICON-01`); chart colours come from the chart tokens
   (`PLAT-WEB-DS-THEME-VIZ-01`).
5. If the feature mutates data, wire `PLAT-WEB-FORMS`: `zodResolver` with the Phase 1 schema.
6. Apply `PLAT-WEB-A11Y`'s agnostic rules (semantic HTML, `alt`, `aria-label`, headings, focus). Its
   container guard and `ErrorBoundary` rules are `web-spa` only; route boundaries are Phase 8.
7. **`server` runtime:** the `{Feature}Page.tsx` shell obtains data through a UseCase or DataSource
   from the composition, maps it to serialisable props, and renders; no hooks, state or mutation logic
   (`ARCH-WEB-APP-COMP-SERVER-01`, `-BOUNDARY-01`).
8. **`static-export` runtime:** the shell fetches no runtime data; all of it arrives in the browser
   through the Hook (`ARCH-WEB-APP-COMP-STATIC-01`); browser APIs only in effects or handlers
   (`PLAT-WEB-NEXT-STATIC-BROWSER-01`).

### Validation

- [ ] No presentational component imports below the Hook or reads the composition context
      (`ARCH-WEB-APP-DEP-05`, `ARCH-WEB-APP-COMP-DI-01`).
- [ ] Each `ViewState` status is rendered and tested (`ARCH-WEB-APP-COMP-TEST-01`).
- [ ] Every icon-only control has `aria-label`; every `<img>` has `alt`; both themes meet contrast
      (`PLAT-WEB-DS-THEME-CONTRAST-01`).

---

## Phase 8 — Route and boundaries

**Goal:** The feature is reachable, thin at the route, and fails gracefully.

Read: `ARCH-WEB-APP-FEATURE-STRUCTURE`, `PLAT-WEB-NEXT`

### Steps

1. Add `app/.../page.tsx` that composes the feature and nothing else
   (`ARCH-WEB-APP-FEAT-ROUTE-01`); export only the page and public types from `index.ts`
   (`ARCH-WEB-APP-DEP-07`).
2. Add `loading.tsx`, `error.tsx` and `not-found.tsx` where the segment needs them
   (`PLAT-WEB-NEXT-BOUNDARY-01`); the error boundary reports once and offers retry
   (`ARCH-WEB-APP-EFLOW-BOUNDARY-01`).
3. State a person would share (region, filter, range) lives in the URL, read inside a `<Suspense>`
   boundary and validated (`PLAT-WEB-NEXT-URL-01`).
4. `await` `params` and `searchParams` (`PLAT-WEB-NEXT-ASYNC-01`).
5. **`server` runtime:** place uncached data behind `<Suspense>` as deep as possible and cache
   deliberately (`PLAT-WEB-NEXT-DATA-SUSPENSE-01`, `-USECACHE-01`, `-TAG-01`).
6. **`static-export` runtime:** a dynamic segment only for build-time values
   (`PLAT-WEB-NEXT-STATIC-ROUTES-01`).

### Validation

- [ ] The route renders the feature end to end in `next dev`.
- [ ] A hand-edited URL parameter produces a clear state, not a crash.
- [ ] Composition of two features on one screen happens here, not inside either
      (`ARCH-WEB-APP-FEAT-ROUTE-02`).

---

## Phase 9 — Test and enforcement gate

**Goal:** Every layer is tested at its own level, the contract holds, and the build is clean.

Read: `QG-WEB-TESTING`

### Steps

1. Check the testing-by-layer table in `QG-WEB-TESTING` against what exists: domain with plain inputs;
   UseCases and Repositories against fakes; DataSources against their contract; Hooks in a test
   provider; presentational components with props.
2. An `async` Server Component and any proxy-gated route are covered end to end
   (`QG-WEB-TESTING-RSC-01`, `QG-WEB-TESTING-MW-01`).
3. Run, in this order: type-check, lint (it is a separate step: `PLAT-WEB-NEXT-LINT-01`), the tests, the
   architecture check, then `next build` (`PLAT-WEB-NEXT-APP-DEPLOY-BUILD-01`).
4. **`static-export` runtime:** after deploy, load and refresh every new route on the host, and confirm
   an unknown path shows the app's 404 (`PLAT-WEB-NEXT-STATIC-DIRECT-01`); the security rules tests
   run against the emulator (`PLAT-WEB-NEXT-FB-EMU-01`).

### Validation

- [ ] No test mocks a provider SDK.
- [ ] `esc-exec architecture check` passes, and the `web.layout-present` rule is not the only one that
      scanned anything.
- [ ] `next build` passes with zero errors; lint passes.
