# Framework Build — Context and Remaining Phases

This document captures decisions made and work remaining so the build can
continue in a future session without losing context.

---

## Status

| Phase | Status |
|-------|--------|
| 1 — Skeleton, schemas, conventions | Done (commit ff74c49) |
| 2 — Core principles | Next |
| 3 — Mobile platform extraction | Planned |
| 4 — Pragmatic Clean Architecture | Planned |
| 5 — Build system patterns | Planned |
| 6 — Backend platform extraction | Planned |
| 7 — Web platform extraction | Planned |
| 8 — Quality gates and CI validation | Planned |
| 9 — Retrieval index and RAG | Planned |

---

## Key Decisions Made

### Source material
The framework is extracted from three existing projects:
- `/home/emmanuel/StudioProjects/AMPM/agents/` — mobile (KMP/Compose), most mature
- `/home/emmanuel/IdeaProjects/ampm-backend/agents/` — Spring Boot backend
- `/home/emmanuel/WebstormProjects/ampm-website/agents/` — TypeScript/React web

None of these projects' specific knowledge (feature modules, Firebase config,
database schemas) enters the framework. Only reusable patterns, principles,
and platform conventions are extracted.

### Framework owns all rule IDs
Rule ID namespaces (REP-*, DI-*, CTRL-*, etc.) are owned by the framework.
Projects reference them; projects do not define their own rule IDs.

### Project knowledge directory is called `context/`
Projects consuming the framework store their project-specific knowledge in
a `context/` directory (not `agents/`, not `.ai/`).

### DataSource vs Repository — critical distinction
These are both expressions of the data-access abstraction pattern (PAT-DATA-ACCESS),
applied at different layers:

- **DataSource** — abstracts ONE provider (Firebase, Room, REST, JPA).
  Responsibility: translate provider language into domain language.
  Knows nothing about other DataSources.

- **Repository** (Pragmatic Clean only) — coordinates MULTIPLE DataSources.
  Responsibility: enforce SSOT by observing local DataSource as truth,
  updating it from remote. Optional — skip if only one DataSource exists.

The word "Repository" is overloaded across ecosystems:
- Spring/DDD calls the data-access abstraction a "Repository" (= DataSource in this framework)
- Pragmatic Clean calls the coordination layer a "Repository"
The framework pattern document (PAT-DATA-ACCESS) must note this alias explicitly.

### SSOT is a principle, not a pattern
SSOT (Single Source of Truth) belongs in `core/` as a principle.
The Repository layer in Pragmatic Clean Architecture is its implementation.
The two are documented separately and composed in `architectures/pragmatic-clean/`.

### Backend uses DataSource, not Repository
In the backend-service architecture, there is one data source (the database via JPA).
There is nothing to coordinate, so no Repository layer exists.
A custom JPA wrapper (UserStore / UserQueryRepository) is a DataSource in framework terms,
even though Spring convention calls it a Repository.

### Convention plugins belong in `build/`
Gradle convention plugins are a build-system concern shared by both mobile and
backend JVM projects. They do not belong under `platforms/mobile/` or `platforms/backend/`.

---

## Remaining Phases — Detail

### Phase 2 — Core

Extract platform and architecture agnostic engineering principles.
These are true regardless of language, framework, or architecture.

Candidates to extract from source projects:
- Dependency inversion
- Low coupling / high cohesion
- Separation of concerns
- SSOT (principle — see decision above)
- Error propagation philosophy (throw early, map at boundary, never swallow)
- Naming philosophy
- Testing philosophy

Each document:
- Must have metadata conforming to `schemas/document.yaml`
- `platform: [all]`, `architecture: [all]`
- ID prefix: `CORE-`

### Phase 3 — Mobile Platform

Extract Kotlin/KMP/Compose-specific implementation guides from AMPM's `agents/`.

Topics to extract (platform specifics only — not architecture rules):
- Koin DI patterns (scopes, modules, qualifiers)
- Compose UI patterns (slot API, theming, skeleton loading)
- Kotlin Flow / coroutines conventions
- Room conventions
- Ktor networking conventions
- Firebase KMP SDK conventions
- KMP source set structure (commonMain / androidMain / iosMain / wasmJsMain)
- Design system conventions

Each document references the architecture document it extends (e.g. ARCH-PC-VIEW).

### Phase 4 — Pragmatic Clean Architecture

Define the architectural style used by AMPM.
This is independent of mobile — it is the architecture, not the platform.

Layers to document:
- `ARCH-PC-DATASOURCE` — provider abstraction, type mapping, exception wrapping
- `ARCH-PC-REPOSITORY` — SSOT coordination, optional layer, when to skip
- `ARCH-PC-USECASE` — business logic, Outcome pattern, error mapping
- `ARCH-PC-VIEWMODEL` — state management, event handling
- `ARCH-PC-VIEW` — stateless composables, state consumption
- `ARCH-PC-DI` — module structure, scope rules
- `ARCH-PC-ERROR-FLOW` — end-to-end error propagation across layers

Rule migration: existing REP-*, DI-*, ARCH-* rules from AMPM's agents/rules/
are migrated here with proper metadata. Rules that were mobile-specific move
to Phase 3 instead.

### Phase 5 — Build System

Extract Gradle patterns shared by mobile and backend.

Topics:
- Convention plugin structure and naming
- Feature module template (build.gradle.kts shape)
- Kover coverage setup and thresholds
- Detekt configuration
- Version catalog conventions
- Multi-module registration patterns (settings.gradle.kts)

### Phase 6 — Backend Platform

Extract Spring Boot / JPA / Kotlin patterns from ampm-backend's `agents/`.

Topics:
- Controller rules (CTRL-*)
- Service layer rules (SVC-*)
- DataSource layer (custom JPA wrappers — note naming convention vs Spring's "Repository")
- Spring DI conventions
- Transaction management rules
- Request/response DTO patterns
- Error handling (Spring exception handlers)
- Testing (MockMvc, Mockk, test fixtures)

Note: The backend architecture (`architectures/backend-service/`) is defined
in Phase 6 alongside the platform, since both are simpler and tightly coupled.

### Phase 7 — Web Platform

Extract TypeScript/React patterns from ampm-website's `agents/`.

Topics:
- Component architecture (container / presentation split)
- Hook patterns
- Firebase Web SDK conventions
- TypeScript conventions
- Styling rules
- Accessibility rules
- Deployment patterns

### Phase 8 — Quality Gates and CI

Make the framework self-validating.

Tools to build (`tools/`):
- Reference validator — detect broken document ID references
- Schema validator — check document metadata against `schemas/`
- Duplicate ID checker — catch duplicate document or rule IDs
- Circular reference checker — detect circular `requires` chains
- Index generator — build flat index of all document IDs and metadata

GitHub Actions workflow:
- Runs on every commit to main
- Validates all of the above
- Fails the build on any violation

### Phase 9 — Retrieval Index and RAG

Generate a machine-readable index from document metadata for smart context loading.

Goals:
- Small context
- High relevance
- Low token usage

Output: a retrieval index that, given a project profile and task type, returns
the minimal set of document IDs needed.

---

## What to Start With in Phase 2

Suggested order for core/ documents:

1. `CORE-DI` — Dependency Inversion (most referenced principle across all layers)
2. `CORE-SSOT` — Single Source of Truth (directly informs PAT-DATA-ACCESS and ARCH-PC-REPOSITORY)
3. `CORE-COUPLING` — Low Coupling / High Cohesion
4. `CORE-ERROR` — Error propagation philosophy
5. `CORE-NAMING` — Naming philosophy
6. `CORE-TESTING` — Testing philosophy

Then move to `patterns/`:
7. `PAT-DATA-ACCESS` — Data-access abstraction (note Spring alias, references CORE-DI)
8. `PAT-OUTCOME` — Result/Outcome wrapper pattern (Outcome<T>)
9. `PAT-OBSERVER` — Observable data streams (Flow)
