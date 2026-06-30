---
id: ARCH-PC-FEATURE
type: guide
layer: architecture
platform: [mobile]
architecture: [pragmatic-clean]
requires: [ARCH-PC]
related: [ARCH-PC-DI, ARCH-PC-DATASOURCE]
tags: [feature, module, structure, naming, file-placement, directories]
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

**Rule ARCH-PC-FEAT-NAME-01 (hard):** Never use `Impl` suffix for implementations.
Use `Default` prefix.

**Rule ARCH-PC-FEAT-NAME-02 (hard):** DataSource names put source type first:
`LocalProfileDataSource`, not `ProfileLocalDataSource`.

## Placement rules

**Rule ARCH-PC-FEAT-PLACE-01 (hard):** Screen and ViewModel files go directly in
`ui/`, not in subdirectories.

**Rule ARCH-PC-FEAT-PLACE-02 (hard):** UI state types (State, Event) go in `ui/data/`.
Domain models go in `data/models/`. They are different things; do not mix them.

**Rule ARCH-PC-FEAT-PLACE-03 (hard):** UseCases go directly in `usecases/`. Group
in subdirectories only when there are 10+ UseCases and a clear sub-domain grouping exists.

**Rule ARCH-PC-FEAT-PLACE-04 (hard):** Feature-specific exceptions go in `data/errors/`.
Never in `core/`.

## Layer dependency rules

Dependencies flow inward (toward data) and downward. Higher layers MUST NOT
be imported by lower layers.

```
ui/ → usecases/ → data/ → core/
```

**Rule ARCH-PC-FEAT-DEP-01 (hard):** Features MUST NOT import from other features.
Shared types belong in `core/`.

**Rule ARCH-PC-FEAT-DEP-02 (hard):** `ui/` MUST NOT import from `data/` directly.
All data access goes through ViewModels and UseCases.

**Rule ARCH-PC-FEAT-DEP-03 (hard):** `usecases/` MUST NOT import from `ui/`.

**Rule ARCH-PC-FEAT-DEP-04 (hard):** `core/` MUST NOT import from any feature.

## Anti-patterns

**Rule ARCH-PC-FEAT-ANTI-01 (hard):** No `utils/` or `helpers/` packages inside a
feature. Either place code in the correct layer directory or move it to `core/`.

**Rule ARCH-PC-FEAT-ANTI-02 (hard):** No Manager, Helper, or Service god-objects that
hold multiple unrelated responsibilities. Split into focused UseCases.
