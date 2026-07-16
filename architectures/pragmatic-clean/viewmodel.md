---
id: ARCH-PC-VIEWMODEL
type: guide
layer: architecture
platform: [mobile]
architecture: [pragmatic-clean]
requires: [ARCH-PC, PLAT-MOB-KOTLIN, PLAT-MOB-KOIN]
related: [ARCH-PC-USECASE, ARCH-PC-VIEW, ARCH-PC-ERROR-FLOW, ARCH-PC-DI]
tags: [viewmodel, state, events, presentation, formatting, stateflow, sharedflow]
---

# ViewModel Layer

## Responsibility

Manage UI state. Format domain data into display-ready values. Coordinate
with UseCases. Surface one-time events. No business logic.

## ViewModel vs UseCase — the bright line

| ViewModel | UseCase |
|---|---|
| Format a date for display | Determine which date is correct |
| Validate input format (email regex) | Apply business validation rules |
| Manage loading / error / success state | Produce the success or failure result |
| Convert domain model → presentation object | Transform or filter domain data |

```rule
id: ARCH-PC-VM-LOGIC-01
statement: ViewModels contain presentation logic only.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VM-LOGIC-01 — ViewModels contain presentation logic only.
```

Business rules, data transformation, and domain decisions belong in UseCases.

```rule
id: ARCH-PC-VM-INJECT-01
statement: ViewModels MUST inject UseCases and Orchestrators.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VM-INJECT-01 — ViewModels MUST inject UseCases and Orchestrators.
```

They MUST NOT inject Repositories or DataSources.

## State

State is a data class with default values, exposed as a reactive stream.

```
private val _state = MutableStateFlow(ScreenState())
val state: StateFlow<ScreenState> = _state
```

```rule
id: ARCH-PC-VM-STATE-01
statement: The mutable state holder MUST be private.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VM-STATE-01 — The mutable state holder MUST be private.
```

Expose only the read-only type.

```rule
id: ARCH-PC-VM-STATE-02
statement: State MUST be mutated via an atomic update function (`update {}`).
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VM-STATE-02 — State MUST be mutated via an atomic update function (`update {}`).
```

Never reassign fields on the mutable reference directly.

```rule
id: ARCH-PC-VM-STATE-03
statement: State type is a data class named `{Screen}State` with default values for every field so it can be constructed without parameters.
type: hard
scope: naming
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VM-STATE-03 — State type is a data class named `{Screen}State` with default values for every field so it can be constructed without parameters.
```

## Events

One-time events (navigation, toasts, dialogs) are emitted on a hot stream that
retains no value. Subscribers only receive future emissions.

```
private val _event = MutableSharedFlow<ScreenEvent>()
val event: SharedFlow<ScreenEvent> = _event
```

```rule
id: ARCH-PC-VM-EVENT-01
statement: The mutable event stream MUST be private.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VM-EVENT-01 — The mutable event stream MUST be private.
```

```rule
id: ARCH-PC-VM-EVENT-02
statement: Event type is an enum named `{Screen}Event`.
type: hard
scope: naming
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VM-EVENT-02 — Event type is an enum named `{Screen}Event`.
```

## Formatting

All values displayed to the user must be formatted before they enter the state.
The ViewModel is the formatting boundary; the View renders pre-formatted strings.

```rule
id: ARCH-PC-VM-FORMAT-01
statement: All user-facing formatting (dates, numbers, currency, localised strings) MUST go through an injected platform resource/formatting service.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VM-FORMAT-01 — All user-facing formatting (dates, numbers, currency, localised strings) MUST go through an injected platform resource/formatting service.
```

Never format inline in the ViewModel or in the View.

```rule
id: ARCH-PC-VM-FORMAT-02
statement: Domain models MUST be mapped to presentation objects before being placed in state.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VM-FORMAT-02 — Domain models MUST be mapped to presentation objects before being placed in state.
```

A presentation object contains only display-ready fields (formatted strings, display booleans). It carries no domain logic and no platform-specific types.

## Error state

```rule
id: ARCH-PC-VM-ERROR-01
statement: Error state MUST store the full domain exception object, not extracted fields.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VM-ERROR-01 — Error state MUST store the full domain exception object, not extracted fields.
```

Storing only a message string loses the metadata (severity, presentation style, available actions) that the View needs to render the error correctly.

```rule
id: ARCH-PC-VM-ERROR-02
statement: ViewModels SHOULD expose a `retry()` function and a `clearError()` function when the underlying operation is retryable.
type: soft
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VM-ERROR-02 — ViewModels SHOULD expose a `retry()` function and a `clearError()` function when the underlying operation is retryable.
```

## Job management

```rule
id: ARCH-PC-VM-JOB-01
statement: Each independently cancellable operation MUST have its own Job variable.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VM-JOB-01 — Each independently cancellable operation MUST have its own Job variable.
```

Cancel the existing Job before starting a new one for the same operation.

## Scope

```rule
id: ARCH-PC-VM-SCOPE-01
statement: All coroutines launched by a ViewModel MUST use the ViewModel's lifecycle-aware scope.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VM-SCOPE-01 — All coroutines launched by a ViewModel MUST use the ViewModel's lifecycle-aware scope.
```

Never use a global or unmanaged scope.

## DI scope

ViewModels are scoped to the UI composition lifecycle.
See `ARCH-PC-DI` for scope declaration.

## Naming

`{Screen}ViewModel`, `{Screen}State`, `{Screen}Event`, `{Screen}Presentation`.

## Violations

- ViewModel injecting a Repository or DataSource
- Business validation or domain decision inside a ViewModel
- Inline date or number formatting in a ViewModel
- Domain model stored directly in UI state (not mapped to presentation object)
- Full error object extracted into individual string fields before storing in state
- MutableStateFlow exposed as a public property
- State mutated directly on the mutable reference outside an update block
