---
id: ARCH-PC-VIEW
type: guide
layer: architecture
platform: [mobile]
architecture: [pragmatic-clean]
requires: [ARCH-PC, ARCH-PC-VIEWMODEL, PLAT-MOB-COMPOSE]
related: [ARCH-PC-ERROR-FLOW]
tags: [view, screen, compose, stateless, scaffold, state-hoisting]
---

# View Layer

## Responsibility

Render state. Emit user events as callbacks. Nothing else.

The View layer has no business logic, no data access, and no state ownership
beyond transient local UI state (an expanded/collapsed toggle, scroll position).

## Screen / View split

```
{Feature}Screen     Connects to ViewModel. Owns the ViewModel relationship.
{Feature}View       Pure rendering. Stateless. Fully previewable.
```

**Rule ARCH-PC-VIEW-SPLIT-01 (hard):** Logic that connects to a ViewModel — state
collection, event observation, side effects — MUST live in the Screen composable.
The View composable MUST be stateless and previewable without a live ViewModel.

**Rule ARCH-PC-VIEW-SPLIT-02 (hard):** Only root Screen composables may inject a
ViewModel. Nested View composables receive data as parameters.

## Screen responsibilities

- Inject ViewModel using the platform DI mechanism
- Collect state with lifecycle awareness (`collectAsStateWithLifecycle`)
- Observe events and handle side effects (navigation, snackbars)
- Configure the app scaffold (top bar, FAB, bottom bar visibility) via the app state
- Delegate rendering to the View composable

**Rule ARCH-PC-VIEW-SCAFFOLD-01 (hard):** The application has exactly ONE Scaffold.
Screens MUST participate in it via the app state object — they MUST NOT embed their
own Scaffold, TopBar, or BottomBar composables directly in the layout tree.

**Rule ARCH-PC-VIEW-SCAFFOLD-02 (hard):** Top bar configuration MUST be registered
via the app state in a `DisposableEffect` and cleared on dispose. This prevents
a previous screen's top bar from persisting when navigating forward.

## View responsibilities

- Accept state as parameters
- Accept user action callbacks as lambda parameters
- Render UI based on the received state
- Call callbacks when the user acts — do not call ViewModel functions directly

**Rule ARCH-PC-VIEW-STATE-01 (hard):** All data a View composable renders MUST
arrive as parameters. A View composable MUST NOT access external state, call
ViewModels, or read from any DI container.

**Rule ARCH-PC-VIEW-CALLBACK-01 (hard):** User actions are surfaced as lambda
parameters (`onClick: () -> Unit`, `onValueChange: (String) -> Unit`). The View
calls the lambda; the Screen or ViewModel decides what to do.

## Local UI state

`remember` is allowed only for state that is purely local to the composable and
has no meaning outside it: expanded/collapsed, focus state, scroll position.

**Rule ARCH-PC-VIEW-LOCAL-01 (hard):** Business state and derived display data
MUST NOT be stored in `remember`. If a value matters to the ViewModel or affects
what is displayed across recompositions, it belongs in ViewModel state.

## Error display

The View receives the full domain exception object in state and renders it
using the established error presentation component. It does not parse or
extract fields from the exception.

## Naming

`{Feature}Screen`, `{Feature}View`, `{Feature}Components.kt` (for feature-specific
composables in `ui/components/`).

## Violations

- A View composable calling `koinViewModel()` or accessing a DI container
- A Screen composable embedding a second `Scaffold` or directly adding a `TopBar`
- Business state stored in `remember` instead of ViewModel state
- A View composable containing `if` logic that mirrors a business rule
- Top bar or FAB not cleared in `onDispose`, leaving remnants on the next screen
