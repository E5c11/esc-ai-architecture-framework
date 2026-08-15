---
id: ARCH-PC-FEATURE
type: guide
layer: architecture
platform: [mobile]
architecture: [pragmatic-clean]
requires: [ARCH-PC]
related: [ARCH-PC-DI, ARCH-PC-DATASOURCE, ARCH-PC-COMPOSITION]
tags: [feature, module, structure, naming, file-placement, directories]
status: active
---

# Feature Module Structure

## Directory structure

```
features/{feature}/
├── data/
│   ├── api/             Firebase{Feature}Api.kt + DefaultFirebase{Feature}Api.kt
│   ├── dao/             {Feature}Dao.kt
│   ├── dto/             {Feature}Dto.kt
│   ├── entities/        {Feature}Entity.kt
│   ├── errors/          {Feature}Exceptions.kt
│   ├── mappers/         {Feature}Mappers.kt
│   ├── models/          {DomainEntity}.kt
│   ├── repository/      {Feature}Repository.kt + Default{Feature}Repository.kt
│   └── sources/         Local{Feature}DataSource.kt, Remote{Feature}DataSource.kt
├── di/
│   └── {Feature}Module.kt
├── ui/
│   ├── components/      Feature-specific composables
│   ├── data/            {Feature}State.kt, {Feature}Event.kt
│   ├── {Feature}Screen.kt
│   └── {Feature}ViewModel.kt
└── usecases/
    └── {Action}{Entity}UseCase.kt
```

Omit directories that do not apply (no `dao/` for remote-only features,
no `repository/` for single-DataSource features).

## Naming conventions

### Files

| File | Convention | Example |
|---|---|---|
| Screen | `{Feature}Screen.kt` | `ProfileScreen.kt` |
| ViewModel | `{Feature}ViewModel.kt` | `ProfileViewModel.kt` |
| State | `{Feature}State.kt` in `ui/data/` | `ProfileState.kt` |
| Event | `{Feature}Event.kt` in `ui/data/` | `ProfileEvent.kt` |
| UseCase | `{Action}{Entity}UseCase.kt` | `FetchProfileUseCase.kt` |
| Orchestrator | `{Feature}Orchestrator.kt` | `LoginOrchestrator.kt` |
| Repository interface | `{Feature}Repository.kt` | `ProfileRepository.kt` |
| Repository impl | `Default{Feature}Repository.kt` | `DefaultProfileRepository.kt` |
| DataSource | `{Local\|Remote}{Feature}DataSource.kt` | `LocalProfileDataSource.kt` |
| API interface | `{Protocol}{Feature}Api.kt` | `FirebaseProfileApi.kt` |
| API impl | `Default{Protocol}{Feature}Api.kt` | `DefaultFirebaseProfileApi.kt` |
| DAO | `{Feature}Dao.kt` | `ProfileDao.kt` |
| DI module | `{Feature}Module.kt` | `ProfileModule.kt` |
| Exceptions | `{Feature}Exceptions.kt` | `ProfileExceptions.kt` |
| Mappers | `{Feature}Mappers.kt` | `ProfileMappers.kt` |

```rule
id: ARCH-PC-FEAT-NAME-01
statement: Never use `Impl` suffix for implementations.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-FEAT-NAME-01 — Never use `Impl` suffix for implementations.
```

Use `Default` prefix.

```rule
id: ARCH-PC-FEAT-NAME-02
statement: DataSource names put source type first: `LocalProfileDataSource`, not `ProfileLocalDataSource`.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-FEAT-NAME-02 — DataSource names put source type first: `LocalProfileDataSource`, not `ProfileLocalDataSource`.
```

## Placement rules

```rule
id: ARCH-PC-FEAT-PLACE-01
statement: Screen and ViewModel files go directly in `ui/`, not in subdirectories.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-FEAT-PLACE-01 — Screen and ViewModel files go directly in `ui/`, not in subdirectories.
```

```rule
id: ARCH-PC-FEAT-PLACE-02
statement: UI state types (State, Event) go in `ui/data/`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-FEAT-PLACE-02 — UI state types (State, Event) go in `ui/data/`.
```

Domain models go in `data/models/`. They are different things; do not mix them.

```rule
id: ARCH-PC-FEAT-PLACE-03
statement: UseCases go directly in `usecases/`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-FEAT-PLACE-03 — UseCases go directly in `usecases/`.
```

Group in subdirectories only when there are 10+ UseCases and a clear sub-domain grouping exists.

```rule
id: ARCH-PC-FEAT-PLACE-04
statement: Feature-specific exceptions go in `data/errors/`.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-FEAT-PLACE-04 — Feature-specific exceptions go in `data/errors/`.
```

Never in `core/`.

## Layer dependency rules

Dependencies flow inward (toward data) and downward. Higher layers MUST NOT
be imported by lower layers.

```
ui/ → usecases/ → data/ → core/
```

```rule
id: ARCH-PC-FEAT-DEP-01
statement: Features MUST NOT import from other features.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-FEAT-DEP-01 — Features MUST NOT import from other features.
```

Shared types belong in `core/`. When a screen needs to *compose* another feature's UI or
state rather than share a generic type, see `ARCH-PC-COMPOSITION` — `core/` is not a
default answer for that case, and routing around this rule via `core/` or a design-system
module without following that doc's rules is itself a violation.

```rule
id: ARCH-PC-FEAT-DEP-02
statement: `ui/` MUST NOT import from `data/` directly.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-FEAT-DEP-02 — `ui/` MUST NOT import from `data/` directly.
```

All data access goes through ViewModels and UseCases.

```rule
id: ARCH-PC-FEAT-DEP-03
statement: `usecases/` MUST NOT import from `ui/`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-FEAT-DEP-03 — `usecases/` MUST NOT import from `ui/`.
```

```rule
id: ARCH-PC-FEAT-DEP-04
statement: `core/` MUST NOT import from any feature.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-FEAT-DEP-04 — `core/` MUST NOT import from any feature.
```

## Anti-patterns

```rule
id: ARCH-PC-FEAT-ANTI-01
statement: No `utils/` or `helpers/` packages inside a feature.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-FEAT-ANTI-01 — No `utils/` or `helpers/` packages inside a feature.
```

Either place code in the correct layer directory or move it to `core/`.

```rule
id: ARCH-PC-FEAT-ANTI-02
statement: No Manager, Helper, or Service god-objects that hold multiple unrelated responsibilities.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-FEAT-ANTI-02 — No Manager, Helper, or Service god-objects that hold multiple unrelated responsibilities.
```

Split into focused UseCases.
