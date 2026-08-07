---
id: PLAT-MOB-COMPOSE
type: platform
layer: platform
platform: [mobile]
architecture: [all]
requires: [PLAT-MOB-KOTLIN]
related: [PLAT-MOB-KMP]
tags: [compose, jetpack-compose, ui, state-hoisting, slot-api, theming, skeleton]
status: active
---

# Jetpack Compose / Compose Multiplatform

## Overview

Compose is the declarative UI framework for KMP. UI is a function of state.
Components are pure — they receive state and emit events, they do not own state
or trigger side effects.

## State hoisting

State is owned at the lowest common ancestor that needs it. Components receive
state as parameters and emit changes via lambdas — they do not hold state internally
unless the state is purely local to that component (e.g. expanded/collapsed toggle).

```rule
id: PLAT-MOB-CP-STATE-01
statement: Composables that display data MUST receive that data as parameters.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-CP-STATE-01 — Composables that display data MUST receive that data as parameters.
```

They MUST NOT call `viewModel()` or `koinViewModel()` internally (except for root Screen composables).

```rule
id: PLAT-MOB-CP-STATE-02
statement: User actions are surfaced as lambda parameters (`onClick: () -> Unit`, `onValueChange: (String) -> Unit`).
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-CP-STATE-02 — User actions are surfaced as lambda parameters (`onClick: () -> Unit`, `onValueChange: (String) -> Unit`).
```

Composables MUST NOT call ViewModel functions directly.

## Screen / View split

A **Screen** composable is the root of a navigation destination. It owns the
ViewModel connection and collects state.

A **View** composable is stateless. It receives all data it needs as parameters.

```
{Feature}Screen    — collects state from ViewModel, passes to View
{Feature}View      — receives state + event lambdas, renders UI
```

```rule
id: PLAT-MOB-CP-SPLIT-01
statement: Logic that connects to a ViewModel (state collection, event handling, side effects) MUST live in the Screen composable.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-CP-SPLIT-01 — Logic that connects to a ViewModel (state collection, event handling, side effects) MUST live in the Screen composable.
```

The View composable MUST be stateless and previewable without a ViewModel.

## Slot API

When a component needs to accept composable content from the caller, use a
composable lambda parameter (slot) rather than passing data the component
then renders internally.

```kotlin
@Composable
fun AppCard(
    modifier: Modifier = Modifier,
    header: @Composable () -> Unit,
    content: @Composable () -> Unit,
)
```

```rule
id: PLAT-MOB-CP-SLOT-01
statement: Shared components that need to render caller-provided UI SHOULD use composable slot parameters rather than accepting sealed state or type parameters.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-CP-SLOT-01 — Shared components that need to render caller-provided UI SHOULD use composable slot parameters rather than accepting sealed state or type parameters.
```

## Theming

```rule
id: PLAT-MOB-CP-THEME-01
statement: Composables MUST reference colours via `MaterialTheme.colorScheme` (or the project's custom theme extension).
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-CP-THEME-01 — Composables MUST reference colours via `MaterialTheme.colorScheme` (or the project's custom theme extension).
```

No hardcoded `Color(0xFF...)` values in composables.

```rule
id: PLAT-MOB-CP-THEME-02
statement: Composables MUST reference typography via `MaterialTheme.typography`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-CP-THEME-02 — Composables MUST reference typography via `MaterialTheme.typography`.
```

No hardcoded `fontSize` or `fontWeight` in composables.

```rule
id: PLAT-MOB-CP-THEME-03
statement: Spacing values SHOULD be referenced via a shared spacing scale rather than scattered `8.dp`, `16.dp` literals.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-CP-THEME-03 — Spacing values SHOULD be referenced via a shared spacing scale rather than scattered `8.dp`, `16.dp` literals.
```

## Skeleton loading

Placeholder loading state uses a shimmer animation over placeholder shapes that
approximate the layout of the real content. The placeholder layout mirrors the
structure of the loaded layout so there is no visual jump on load.

```rule
id: PLAT-MOB-CP-SKEL-01
statement: Loading states for list items and cards SHOULD use shimmer skeleton placeholders rather than a spinner.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-CP-SKEL-01 — Loading states for list items and cards SHOULD use shimmer skeleton placeholders rather than a spinner.
```

## Previews

```rule
id: PLAT-MOB-CP-PREV-01
statement: Every View composable SHOULD have at least one `@Preview` covering the default (loaded) state.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-CP-PREV-01 — Every View composable SHOULD have at least one `@Preview` covering the default (loaded) state.
```

Previews MUST NOT require a real ViewModel — all data is supplied as parameters.

## Violations

- A stateless View composable calling `koinViewModel()` directly
- User action implemented inside a composable instead of passed as a lambda
- `Color(0xFF1A73E8)` hardcoded in a composable body
- A Screen composable that is not previewable because it constructs real dependencies
