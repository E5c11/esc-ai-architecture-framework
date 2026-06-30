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

**Rule ARCH-PC-VM-LOGIC-01 (hard):** ViewModels contain presentation logic only.
Business rules, data transformation, and domain decisions belong in UseCases.

**Rule ARCH-PC-VM-INJECT-01 (hard):** ViewModels MUST inject UseCases and
Orchestrators. They MUST NOT inject Repositories or DataSources.

## State

State is a data class with default values, exposed as a reactive stream.

```
private val _state = MutableStateFlow(ScreenState())
val state: StateFlow<ScreenState> = _state
```

**Rule ARCH-PC-VM-STATE-01 (hard):** The mutable state holder MUST be private.
Expose only the read-only type.

**Rule ARCH-PC-VM-STATE-02 (hard):** State MUST be mutated via an atomic update
function (`update {}`). Never reassign fields on the mutable reference directly.

**Rule ARCH-PC-VM-STATE-03 (hard):** State type is a data class named `{Screen}State`
with default values for every field so it can be constructed without parameters.

## Events

One-time events (navigation, toasts, dialogs) are emitted on a hot stream that
retains no value. Subscribers only receive future emissions.

```
private val _event = MutableSharedFlow<ScreenEvent>()
val event: SharedFlow<ScreenEvent> = _event
```

**Rule ARCH-PC-VM-EVENT-01 (hard):** The mutable event stream MUST be private.
**Rule ARCH-PC-VM-EVENT-02 (hard):** Event type is an enum named `{Screen}Event`.

## Formatting

All values displayed to the user must be formatted before they enter the state.
The ViewModel is the formatting boundary; the View renders pre-formatted strings.

**Rule ARCH-PC-VM-FORMAT-01 (hard):** All user-facing formatting (dates, numbers,
currency, localised strings) MUST go through an injected platform resource/formatting
service. Never format inline in the ViewModel or in the View.

**Rule ARCH-PC-VM-FORMAT-02 (hard):** Domain models MUST be mapped to presentation
objects before being placed in state. A presentation object contains only
display-ready fields (formatted strings, display booleans). It carries no domain
logic and no platform-specific types.

## Error state

**Rule ARCH-PC-VM-ERROR-01 (hard):** Error state MUST store the full domain
exception object, not extracted fields. Storing only a message string loses the
metadata (severity, presentation style, available actions) that the View needs
to render the error correctly.

**Rule ARCH-PC-VM-ERROR-02 (soft):** ViewModels SHOULD expose a `retry()` function
and a `clearError()` function when the underlying operation is retryable.

## Job management

**Rule ARCH-PC-VM-JOB-01 (hard):** Each independently cancellable operation MUST
have its own Job variable. Cancel the existing Job before starting a new one
for the same operation.

## Scope

**Rule ARCH-PC-VM-SCOPE-01 (hard):** All coroutines launched by a ViewModel MUST
use the ViewModel's lifecycle-aware scope. Never use a global or unmanaged scope.

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
