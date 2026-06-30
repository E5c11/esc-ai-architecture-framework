---
id: PLAT-MOB-SKELETON
type: guide
layer: platform
platform: [mobile]
architecture: [pragmatic-clean]
requires: [ARCH-PC-VIEW, ARCH-PC-VIEWMODEL, PLAT-MOB-COMPOSE]
related: [PAT-OUTCOME]
tags: [skeleton, loading, shimmer, placeholder, compose, ui-state]
status: stub
---

# Skeleton Loading

> **TODO:** This document is a stub. See `todo/missing-files.md` for context.

## What this document must cover

- When to use skeleton loading vs a spinner vs nothing
- How loading state is represented in ViewModel UI state (sealed class, nullable model, boolean flag — pick one and justify)
- Skeleton composable structure — how to mirror the real layout with placeholder shapes
- Shimmer / animation approach (library vs manual `InfiniteTransition`)
- Rule: skeleton composable lives alongside its real counterpart in the same file/package
- How the View switches between skeleton and real content (state-driven, no logic in View)
- Content size stability — avoiding layout jumps when real content loads
- Accessibility — skeletons MUST be marked with `semantics { contentDescription = "Loading" }`
- What NOT to do — showing a full-screen loader for content that loads fast, no skeleton for slow data
