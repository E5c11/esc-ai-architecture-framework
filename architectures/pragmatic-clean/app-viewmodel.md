---
id: ARCH-PC-APP-VM
type: guide
layer: architecture
platform: [mobile]
architecture: [pragmatic-clean]
requires: [ARCH-PC-VIEWMODEL, ARCH-PC-VIEW, PLAT-MOB-KOIN]
related: [PLAT-MOB-NAV, PLAT-MOB-COMPOSE]
tags: [viewmodel, app-viewmodel, scaffold, app-state, top-bar, bottom-bar, snackbar, global-state]
status: stub
---

# App-Level ViewModel

> **TODO:** This document is a stub. See `todo/missing-files.md` for context.

## What this document must cover

- Purpose: what belongs in an app-level ViewModel vs a feature ViewModel
  - App-wide state (authentication state, user session, connectivity)
  - Scaffold control (top bar, bottom bar visibility and content)
  - Snackbar / global message queue
  - Nothing that belongs to a single feature
- The `AppState` contract — what it exposes to the NavHost and Scaffold
- Top bar token pattern — how features claim/release the top bar on navigation
  (e.g. `setTopBar { ... }` returns a token; `onDispose { clearTopBar(token) }`)
- Bottom bar visibility — `LaunchedEffect` vs `DisposableEffect` and which to use (and why)
- How the AppViewModel is injected into composables (avoid passing NavController into VMs)
- Scoping: why AppViewModel must be scoped to the activity/app, not to a navigation graph
- What NOT to do — feature state leaking into AppViewModel, clearing top bar with empty dispose
