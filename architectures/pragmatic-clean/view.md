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

```rule
id: ARCH-PC-VIEW-SPLIT-01
statement: Logic that connects to a ViewModel — state collection, event observation, side effects — MUST live in the Screen composable.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VIEW-SPLIT-01 — Logic that connects to a ViewModel — state collection, event observation, side effects — MUST live in the Screen composable.
```

The View composable MUST be stateless and previewable without a live ViewModel.

```rule
id: ARCH-PC-VIEW-SPLIT-02
statement: Only root Screen composables may inject a ViewModel.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VIEW-SPLIT-02 — Only root Screen composables may inject a ViewModel.
```

Nested View composables receive data as parameters.

## Screen responsibilities

- Inject ViewModel using the platform DI mechanism
- Collect state with lifecycle awareness (`collectAsStateWithLifecycle`)
- Observe events and handle side effects (navigation, snackbars)
- Configure the app scaffold (top bar, FAB, bottom bar visibility) via the app state
- Delegate rendering to the View composable

```rule
id: ARCH-PC-VIEW-SCAFFOLD-01
statement: The application has exactly ONE Scaffold.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VIEW-SCAFFOLD-01 — The application has exactly ONE Scaffold.
```

Screens MUST participate in it via the app state object — they MUST NOT embed their own Scaffold, TopBar, or BottomBar composables directly in the layout tree.

```rule
id: ARCH-PC-VIEW-SCAFFOLD-02
statement: Top bar configuration MUST be registered via the app state in a `DisposableEffect` and cleared on dispose.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VIEW-SCAFFOLD-02 — Top bar configuration MUST be registered via the app state in a `DisposableEffect` and cleared on dispose.
```

This prevents a previous screen's top bar from persisting when navigating forward.

```rule
id: ARCH-PC-VIEW-SCAFFOLD-03
statement: Bottom bar (and other non-disposable scaffold visibility flags) MUST be set via `LaunchedEffect(Unit)`, not `DisposableEffect`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VIEW-SCAFFOLD-03 — Bottom bar (and other non-disposable scaffold visibility flags) MUST be set via `LaunchedEffect(Unit)`, not `DisposableEffect`.
```

Visibility is a plain state-set, not a resource that needs dispose-time cleanup — `DisposableEffect` is the wrong tool and invites an empty or incorrect `onDispose { }` block.

## View responsibilities

- Accept state as parameters
- Accept user action callbacks as lambda parameters
- Render UI based on the received state
- Call callbacks when the user acts — do not call ViewModel functions directly

```rule
id: ARCH-PC-VIEW-STATE-01
statement: All data a View composable renders MUST arrive as parameters.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VIEW-STATE-01 — All data a View composable renders MUST arrive as parameters.
```

A View composable MUST NOT access external state, call ViewModels, or read from any DI container.

```rule
id: ARCH-PC-VIEW-CALLBACK-01
statement: User actions are surfaced as lambda parameters (`onClick: () -> Unit`, `onValueChange: (String) -> Unit`).
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VIEW-CALLBACK-01 — User actions are surfaced as lambda parameters (`onClick: () -> Unit`, `onValueChange: (String) -> Unit`).
```

The View calls the lambda; the Screen or ViewModel decides what to do.

## Local UI state

`remember` is allowed only for state that is purely local to the composable and
has no meaning outside it: expanded/collapsed, focus state, scroll position.

```rule
id: ARCH-PC-VIEW-LOCAL-01
statement: Business state and derived display data MUST NOT be stored in `remember`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VIEW-LOCAL-01 — Business state and derived display data MUST NOT be stored in `remember`.
```

If a value matters to the ViewModel or affects what is displayed across recompositions, it belongs in ViewModel state.

## Components

Shared or extracted composables in `ui/components/` (see Naming) are part of
the View layer, not a third category with looser rules. `ARCH-PC-VIEW-STATE-01`
and `ARCH-PC-VIEW-CALLBACK-01` apply to them exactly as they apply to the root
`{Feature}View` — a component two levels deep in the render tree still MUST NOT
reach into DI.

```rule
id: ARCH-PC-VIEW-COMPONENT-01
statement: A component MUST NOT call `koinInject()`, construct a ViewModel, or read from any DI container — including for cross-cutting concerns like an analytics tracker.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VIEW-COMPONENT-01 — A component MUST NOT call `koinInject()`, construct a ViewModel, or read from any DI container — including for cross-cutting concerns like an analytics tracker.
```

Surface the action as a callback parameter and let the caller (Screen, or the composable that already holds the dependency) perform the side effect. This is `ARCH-PC-VIEW-STATE-01` restated explicitly for nested components, because in practice it is the rule most often missed once a component lives a few call-sites away from the Screen.

```rule
id: ARCH-PC-VIEW-COMPONENT-02
statement: An inline UI block that has grown large enough to have its own clear responsibility (a card, a row, a nudge banner) SHOULD be extracted into its own file in `ui/components/` rather than left inlined inside a `Screen` or another component.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VIEW-COMPONENT-02 — An inline UI block that has grown large enough to have its own clear responsibility (a card, a row, a nudge banner) SHOULD be extracted into its own file in `ui/components/` rather than left inlined inside a `Screen` or another component.
```

There is no hard line count — extract when the block obscures the surrounding composable's own structure, not on a fixed threshold.

```rule
id: ARCH-PC-VIEW-PREVIEW-01
statement: Every component MUST have at least one `@Preview` function using realistic sample data, wrapped in the app's theme.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-VIEW-PREVIEW-01 — Every component MUST have at least one `@Preview` function using realistic sample data, wrapped in the app's theme.
```

Components with meaningfully different visual states (loading / error / empty, enabled / disabled) SHOULD have one preview per state.

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
- Bottom bar visibility set in `DisposableEffect` instead of `LaunchedEffect(Unit)`
- A nested component in `ui/components/` calling `koinInject()` directly instead
  of receiving a callback
- A component with no `@Preview`
