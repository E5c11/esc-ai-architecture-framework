---
id: ARCH-PC
type: architecture
layer: architecture
platform: [mobile]
architecture: [pragmatic-clean]
requires: [CORE-DI, CORE-COUPLING, CORE-SSOT, PAT-DATA-ACCESS, PAT-OUTCOME, PAT-OBSERVER]
related: [ARCH-PC-DATASOURCE, ARCH-PC-REPOSITORY, ARCH-PC-USECASE, ARCH-PC-VIEWMODEL, ARCH-PC-VIEW, ARCH-PC-DI, ARCH-PC-ERROR-FLOW]
tags: [pragmatic-clean, clean-architecture, kmp, layers, mvvm]
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

```
features/{feature}/
├── data/
│   ├── api/         Provider layer: remote API interface + implementation
│   ├── dao/         Provider layer: Room DAO
│   ├── dto/         Data Transfer Objects (provider format)
│   ├── entities/    Room entities
│   ├── errors/      Feature-specific domain exceptions
│   ├── mappers/     DTO ↔ Domain, Entity ↔ Domain mapping functions
│   ├── models/      Domain models
│   ├── repository/  Repository interface + implementation (if multi-source)
│   └── sources/     DataSource interface + implementations
├── di/
│   └── {Feature}Module.kt
├── ui/
│   ├── components/  Feature-specific composables
│   ├── data/        UI state and event types
│   ├── {Feature}Screen.kt
│   └── {Feature}ViewModel.kt
└── usecases/
    └── {Action}{Entity}UseCase.kt
```

See `ARCH-PC-FEATURE` for full naming and placement rules.

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
