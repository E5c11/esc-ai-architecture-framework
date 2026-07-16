---
id: PLAT-MOB-KOTLIN
type: platform
layer: platform
platform: [mobile]
architecture: [all]
requires: [PAT-OBSERVER, PAT-OUTCOME]
related: [PLAT-MOB-KOIN, PLAT-MOB-COMPOSE]
tags: [kotlin, coroutines, flow, stateflow, sharedflow, suspend, dispatchers]
---

# Kotlin Coroutines and Flow

## Overview

Kotlin Coroutines are the concurrency model for KMP. Flow is the reactive stream
implementation. Together they are the platform expression of `PAT-OBSERVER` and
the async layer beneath `PAT-OUTCOME`.

## suspend vs Flow — choosing the right return type

| Scenario | Return type |
|---|---|
| One-shot operation that fetches or writes once | `suspend fun` |
| Data that lives locally and can change over time | `Flow<T>` |
| Write command (save, delete, send) | `suspend fun` |
| UI state derived from persisted data | `StateFlow<T>` |
| One-time UI events (navigation, toasts) | `SharedFlow<T>` |

```rule
id: PLAT-MOB-KT-FLOW-01
statement: Data persisted locally and observable by the UI MUST be exposed as `Flow<T>`, not as a `suspend fun`.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KT-FLOW-01 — Data persisted locally and observable by the UI MUST be exposed as `Flow<T>`, not as a `suspend fun`.
```

A suspend function cannot emit updates after the initial fetch.

```rule
id: PLAT-MOB-KT-FLOW-02
statement: Write commands and one-shot network requests MUST use `suspend fun`, not `Flow`.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KT-FLOW-02 — Write commands and one-shot network requests MUST use `suspend fun`, not `Flow`.
```

A `Flow` with exactly one emission is not a stream.

## StateFlow and SharedFlow

**StateFlow** — for UI state. Always has a current value. New subscribers receive the
latest emission immediately.

```kotlin
private val _state = MutableStateFlow(ScreenState())
val state: StateFlow<ScreenState> = _state
```

**SharedFlow** — for one-time events (navigation, toasts, dialogs). No retained value.
Subscribers only receive future emissions.

```kotlin
private val _event = MutableSharedFlow<ScreenEvent>()
val event: SharedFlow<ScreenEvent> = _event
```

```rule
id: PLAT-MOB-KT-SF-01
statement: `MutableStateFlow` and `MutableSharedFlow` MUST be private.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KT-SF-01 — `MutableStateFlow` and `MutableSharedFlow` MUST be private.
```

Expose only the read-only `StateFlow` / `SharedFlow` type.

```rule
id: PLAT-MOB-KT-SF-02
statement: State MUST be mutated via `_state.update { }`, never by reassigning the `MutableStateFlow` reference.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KT-SF-02 — State MUST be mutated via `_state.update { }`, never by reassigning the `MutableStateFlow` reference.
```

## Coroutine scopes

| Scope | Use |
|---|---|
| `viewModelScope` | ViewModel-launched coroutines; cancelled when ViewModel is cleared |
| `coroutineScope` | Structured concurrency within a suspend function; rethrows on failure |
| `GlobalScope` | Never use |

```rule
id: PLAT-MOB-KT-SCOPE-01
statement: ViewModels MUST launch coroutines in `viewModelScope`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KT-SCOPE-01 — ViewModels MUST launch coroutines in `viewModelScope`.
```

Never use `GlobalScope`.

## Job management

When a user action cancels and restarts an operation (e.g., search-as-you-type,
refresh), track the active Job and cancel it before starting a new one.

```kotlin
private var fetchJob: Job? = null

fun refresh() {
    fetchJob?.cancel()
    fetchJob = viewModelScope.launch { ... }
}
```

```rule
id: PLAT-MOB-KT-JOB-01
statement: Each independently cancellable operation MUST have its own `Job` variable in the ViewModel.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KT-JOB-01 — Each independently cancellable operation MUST have its own `Job` variable in the ViewModel.
```

```rule
id: PLAT-MOB-KT-JOB-02
statement: Cancel the existing Job before launching a new one for the same operation.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KT-JOB-02 — Cancel the existing Job before launching a new one for the same operation.
```

## Dispatchers

```rule
id: PLAT-MOB-KT-DISP-01
statement: Do not hardcode `Dispatchers.IO` or `Dispatchers.Main` inside business logic.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KT-DISP-01 — Do not hardcode `Dispatchers.IO` or `Dispatchers.Main` inside business logic.
```

Inject a dispatcher provider so tests can substitute `UnconfinedTestDispatcher`.

```rule
id: PLAT-MOB-KT-DISP-02
statement: Data layer operations (database reads, network calls) SHOULD be moved to an appropriate dispatcher by the provider (Room, Ktor) rather than forced by the caller.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KT-DISP-02 — Data layer operations (database reads, network calls) SHOULD be moved to an appropriate dispatcher by the provider (Room, Ktor) rather than forced by the caller.
```

## Time in tests

```rule
id: PLAT-MOB-KT-TIME-01
statement: Time-dependent logic MUST use an injected `TimeProvider`, never `System.currentTimeMillis()` or `Clock.System.now()` directly.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-KT-TIME-01 — Time-dependent logic MUST use an injected `TimeProvider`, never `System.currentTimeMillis()` or `Clock.System.now()` directly.
```

Direct time calls make tests non-deterministic.

## Violations

- `Flow` returned from a write command
- `GlobalScope.launch` in a ViewModel
- `MutableStateFlow` exposed as a public property
- `_state.value = _state.value.copy(...)` instead of `_state.update { }`
- `Dispatchers.IO` hardcoded inside a UseCase
