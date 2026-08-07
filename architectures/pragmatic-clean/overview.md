---
id: ARCH-PC
type: architecture
layer: architecture
platform: [mobile]
architecture: [pragmatic-clean]
requires: [CORE-DI, CORE-COUPLING, CORE-SSOT, PAT-DATA-ACCESS, PAT-OUTCOME, PAT-OBSERVER]
related: [ARCH-PC-DATASOURCE, ARCH-PC-REPOSITORY, ARCH-PC-USECASE, ARCH-PC-VIEWMODEL, ARCH-PC-VIEW, ARCH-PC-DI, ARCH-PC-ERROR-FLOW]
tags: [pragmatic-clean, clean-architecture, kmp, layers, mvvm]
status: active
---

# Pragmatic Clean Architecture

## What it is

A layered architecture for Kotlin Multiplatform that applies Clean Architecture
principles without the full abstraction overhead of strict Clean. Each layer has
one clearly defined responsibility and a contract that governs what crosses its
boundary. The architecture is implemented in KMP — business logic and domain
models live in `commonMain` and are shared across all targets.

## Layer stack

```
View                 Renders state. Emits user events. No logic.
ViewModel            Formats data for display. Manages UI state and events.
UseCase              Business logic and single-operation coordination.
Orchestrator         Multi-step coordination of UseCases. No logic.
Repository           SSOT coordination of multiple DataSources. (Optional)
DataSource           Abstracts one provider. Maps types. Wraps exceptions.
Provider             Raw data access: DAO, API, SDK. (Not owned by this arch)
```

## Data flow

```
View
  ↓ user event
ViewModel
  ↓ invoke UseCase / Orchestrator
UseCase
  ↓ read/write via Repository or DataSource
Repository (optional)
  ↓ coordinates DataSources, enforces SSOT
DataSource
  ↓ calls Provider
Provider (Room DAO / Firebase API / REST API)
```

State flows upward as reactive streams (`PAT-OBSERVER`). Mutations flow downward
as imperative calls. Results are wrapped in a typed result type (`PAT-OUTCOME`).

## Layer boundaries — what may NOT cross

| Boundary | What is blocked |
|---|---|
| DataSource → above | Provider types (Entity, DTO, DocumentSnapshot) |
| DataSource → above | Provider exceptions (SQLException, FirebaseException) |
| Repository → above | DataSource types; loading/resource states |
| UseCase → above | Repository or DataSource types |
| ViewModel → above | Domain models (map to presentation objects first) |
| View | No business logic, no direct data access |

## Feature module structure

Each top-level feature is its own Gradle module (`feature/{feature}/`), with
platform-specific source sets (`commonMain`, `androidMain`, `iosMain`,
`wasmJsMain`) mirroring the same package layout below `com.esma.ampm.features.{feature}`:

```
feature/{feature}/src/commonMain/kotlin/com/esma/ampm/features/{feature}/
├── data/            Domain models shared across io/domain/ui (e.g. UserProfile.kt)
├── di/
│   └── {Feature}Module.kt
├── domain/          UseCases: {Action}{Entity}UseCase.kt (business logic, orchestration)
├── io/              DataSource + Repository interfaces, and their non-platform-specific
│   │                implementations (e.g. Default{X}Repository.kt coordinating
│   │                local + remote per CORE-SSOT)
│   ├── local/       Room-backed DataSource implementations (Local{X}DataSource.kt) --
│   │                platform-specific ones instead live in androidMain/iosMain io/local/
│   └── remote/      Firebase/Spring-backed sync classes ({X}RemoteSync.kt,
│                    Remote{X}DataSource.kt) -- see PLAT-MOB-FIREBASE for the
│                    per-table Firebase/Spring seam pattern
└── features/{subfeature}/    A screen or cohesive group of screens within the
    ├── data/                 feature module gets the same shape one level deeper --
    ├── domain/                data/ (subfeature-specific models/UI state), domain/
    ├── io/                    (subfeature-specific UseCases), io/ (if the subfeature
    └── ui/                    needs its own I/O), ui/ ({SubFeature}Screen.kt,
                                {SubFeature}ViewModel.kt, ui/components/ for
                                subfeature-local composables)
```

There is no separate `usecases/`, `dao/`, `dto/`, `entities/`, or `mappers/`
directory — DAOs live in `core/database`, DTOs/entities/mappers live alongside
the DataSource that owns them (in `io/`, `io/local/`, or `io/remote/`), and
UseCases live directly under `domain/` (feature-level) or
`features/{subfeature}/domain/` (subfeature-level), not a separate top-level
`usecases/` folder.

## Which layer owns which concern

| Concern | Layer |
|---|---|
| SQL / Firestore queries | Provider |
| DTO → Domain mapping | DataSource |
| Provider exception → domain exception | DataSource |
| SSOT enforcement, cache coordination | Repository |
| Business rules, validation, transformation | UseCase |
| Multi-step operation sequencing | Orchestrator |
| Formatting data for display | ViewModel |
| UI state management | ViewModel |
| Rendering | View |
