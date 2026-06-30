---
id: PLAT-MOB-NAV
type: guide
layer: platform
platform: [mobile]
architecture: [pragmatic-clean]
requires: [ARCH-PC-VIEW, PLAT-MOB-COMPOSE, PLAT-MOB-KOIN]
related: [ARCH-PC-FEATURE]
tags: [navigation, compose-navigation, navgraph, navhost, deeplink, back-stack]
status: stub
---

# Compose Navigation

> **TODO:** This document is a stub. See `todo/missing-files.md` for context.
>
> **Open question:** Verify whether the navigation layer is owned by this platform doc
> or partially by `ARCH-PC-VIEW`. The existing `ARCH-PC-VIEW` covers the single-Scaffold
> rule and `AppState`; this doc should cover implementation mechanics without duplicating
> those rules.

## What this document must cover

- NavHost and NavGraph setup at the app level
- How each feature registers its destinations (feature nav extension functions)
- Route constant naming and grouping convention
- Passing arguments — type-safe vs string-based; when each is appropriate
- Top-level destinations vs nested graphs
- Back-stack manipulation rules (popUpTo, launchSingleTop)
- Deep link registration
- How `AppState` integrates with the NavController
- Dependency injection for navigation (passing the NavController to ViewModels vs composables)
- KMP / wasmJs considerations if navigation lib differs per platform
