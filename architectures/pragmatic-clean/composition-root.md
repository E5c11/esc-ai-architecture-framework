---
id: ARCH-PC-COMPOSITION
type: guide
layer: architecture
platform: [mobile]
architecture: [pragmatic-clean]
requires: [ARCH-PC, ARCH-PC-FEATURE]
related: [ARCH-PC-VIEW, ARCH-PC-APP-VM, ARCH-PC-DI, PLAT-MOB-NAV]
tags: [composition-root, cross-feature, module-boundary, coupling, common-module-trap, design-system, app-module, premature-abstraction]
status: active
---

# Cross-Feature Composition: Where It Lives

## What this document covers

`ARCH-PC-FEAT-DEP-01` (`ARCH-PC-FEATURE`) says features must not import other features.
That rule is easy to state and easy to violate by accident the moment one screen needs to
show another feature's UI or data — a home screen embedding a profile widget, a dialog that
conceptually spans two features, a "recently viewed" section owned by one feature but
displayed by another. The rule says what's forbidden; this document says where the code
actually goes instead, and closes off the two most common ways teams route around the rule
without actually fixing it.

## The rule

```rule
id: ARCH-PC-COMP-ROOT-01
statement: Composition of two or more features' UI or state on a single screen MUST happen at the app composition root module, never inside either feature module.
type: hard
scope: structure
enforced_by: [planner, reviewer]
violation_message: Violates ARCH-PC-COMP-ROOT-01 — a feature module is importing another feature's UI/state directly instead of the app composition root composing both.
```

The **composition root** is the top-level app module — the one module every feature
depends on and that depends on every feature in return (it owns the NavHost, DI bootstrap,
and top-level Scaffold; see `ARCH-PC-APP-VM`, `PLAT-MOB-NAV`). It is the only module in the
dependency graph where seeing two features simultaneously is not a violation, because
nothing depends on it — there is no cycle to create and no lower layer to contaminate.

```rule
id: ARCH-PC-COMP-ROOT-02
statement: The composition root MUST NOT contain business logic or data-fetching when wiring cross-feature composition — only instantiation of each feature's own DI-registered ViewModel and the passing of already-built composables/callbacks into the consuming feature's slot parameters.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-COMP-ROOT-02 — business logic or data-fetching found in the composition root's cross-feature wiring; this belongs in the owning feature's own ViewModel.
```

Concretely: if Feature A's screen needs to show Feature B's widget, Feature A's `Screen`
composable takes that widget as a slot parameter (`@Composable () -> Unit`, or a typed
callback). The composition root's `{Feature}Route` — not Feature A itself — resolves
Feature B's own DI-registered ViewModel, renders Feature B's own composable, and passes the
result into Feature A's slot. Feature A never imports anything from Feature B. Each
feature's data-fetching and business logic stay exactly where they already are, in that
feature's own ViewModel — the composition root is wiring, not a place to move logic to.

## Two traps: routing around the rule instead of following it

Both of the following are attempts to satisfy `ARCH-PC-FEAT-DEP-01` by relocating code
rather than by composing at the root. Neither actually removes the coupling; each just
moves it somewhere it's harder to see.

### Trap 1 — "put it in a shared/common module"

```rule
id: ARCH-PC-COMP-CORE-01
statement: A shared/core module MUST NOT host a composable, type, or piece of logic that is specific to a single feature's domain, even to route around ARCH-PC-FEAT-DEP-01.
type: hard
scope: structure
enforced_by: [planner, reviewer]
violation_message: Violates ARCH-PC-COMP-CORE-01 — feature-specific code was moved into a shared/core module to avoid a cross-feature import instead of composing at the root.
```

Shared/core modules sit at the *bottom* of the dependency graph: every feature depends on
core, and `ARCH-PC-FEAT-DEP-04` forbids the reverse. The composition root sits at the *top*.
These are not interchangeable "somewhere shared to put it" options — they are opposite ends
of the graph, and only one of them can see two features at once without breaking the graph's
direction.

Moving a feature-specific composable into core to dodge a cross-feature import forces a
choice, and both options are worse than the original violation:

1. The core module keeps importing the owning feature's domain type to render the
   composable — that's `core → feature`, a direction `ARCH-PC-FEAT-DEP-04` already forbids,
   and in practice a compile-time cycle, since the owning feature already depends on core.
2. To avoid that, the domain type (and whatever logic backs it) also moves into core — which
   doesn't remove the coupling, it just relabels the owning feature's business logic as
   "common" while a single feature still conceptually owns it. This is a worse outcome than
   the import violation it was meant to fix: the violation was at least visible and
   attributable to a specific feature; the relabeled version silently expands what "core"
   means and invites the next similar case to land there too.

A module only earns "shared/core" status by having no feature-specific domain knowledge.
The moment it needs one, it has stopped being core, regardless of which directory it lives
in.

### Trap 2 — "move the composable into the design system"

```rule
id: ARCH-PC-COMP-DS-01
statement: A composable relocated to a design-system/shared-UI module MUST be typed only against generic, feature-agnostic presentation models — never against another feature's domain model. Each consuming feature owns its own mapper from its domain type to that presentation model.
type: hard
scope: structure
enforced_by: [planner, reviewer]
violation_message: Violates ARCH-PC-COMP-DS-01 — a composable moved into the design system is still typed against a feature's domain model, which just relocates the cross-feature import rather than removing it.
```

Design-system modules are a subtype of "shared/core" (`ARCH-PC-COMP-CORE-01` applies to
them too), so the same trap applies: if the relocated composable's parameters still type on
a feature's domain model, the design-system module now illegally imports that feature —
same disease, one layer further down.

A version of this *can* work, but it's a real design commitment, not a file move: the
design-system component takes a fully generic presentation model owned by the design
system itself (primitives, no reference to any feature's domain type), and each consuming
feature writes its own mapper from its domain model to that shape. This only pays for
itself when the component has multiple real consumers across different features and no
feature-specific meaning left in it — see `ARCH-PC-COMP-PROMOTE-01` below before reaching
for it.

## Don't promote speculatively

```rule
id: ARCH-PC-COMP-PROMOTE-01
statement: Do not promote a single-consumer piece of code to a shared/core or design-system module speculatively. Promote only when a second real, concrete consumer exists.
type: soft
scope: structure
enforced_by: [planner, reviewer]
violation_message: Violates ARCH-PC-COMP-PROMOTE-01 — code with exactly one real consumer was promoted to a shared module "in case" something else needs it later.
```

This is the same failure mode as Trap 1, arrived at from the opposite direction: code that
was genuinely written as one feature's concern gets namespaced or located as if it were
shared infrastructure before anything else actually consumes it. The namespace/location then
asserts a shared-ownership story that isn't true yet, which is exactly as misleading as
Trap 1's relabeling — it's just been true from the start instead of arrived at defensively.
Keep single-consumer code inside the feature that owns it, named and packaged as that
feature's concern, until a second consumer is real. Promotion is easy later; a wrongly
"shared" module that turns out to have one real caller and a pile of assumptions built
around a promotion that never came is not.

## Decision table

| Situation | Where it goes |
|---|---|
| Feature A's screen needs to render Feature B's UI/data | Composition root composes both; Feature A exposes a slot, never imports Feature B |
| A dialog/component conceptually spans two features (e.g. wires one feature's ViewModel into another's screen) | Composition root owns it, or it moves fully into whichever feature conceptually owns the interaction, with the other feature exposing a narrow public contract — never both features' internals mixed inside a third feature |
| Code has zero feature-specific domain meaning and 2+ real consumers today | Shared/core module — but see `ARCH-PC-COMP-CORE-01`: it must not carry any feature's domain type in, even transitively |
| Code has feature-specific domain meaning but only one real consumer today | Stays in the owning feature, named and packaged as that feature's concern (`ARCH-PC-COMP-PROMOTE-01`) — not "common" |
| A UI component could theoretically be reused by other features but isn't yet | Stays in the owning feature until a second real consumer exists; when it does, extract via `ARCH-PC-COMP-DS-01`'s generic-presentation-model pattern, not a file move |

## Anti-patterns

```rule
id: ARCH-PC-COMP-ANTI-01
statement: No cross-feature composition logic embedded inside a feature module's own Screen/ViewModel "because the composition root felt like too many layers."
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-COMP-ANTI-01 — cross-feature composition logic found inside a feature module instead of the composition root.
```

```rule
id: ARCH-PC-COMP-ANTI-02
statement: No "common"/core module accreting feature-specific UI or domain logic over time because it was the path of least resistance for whoever needed to break a cross-feature import first.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-COMP-ANTI-02 — a shared/core module has accumulated feature-specific knowledge; audit its contents against ARCH-PC-COMP-CORE-01.
```

Split into a composition-root wiring block (`ARCH-PC-COMP-ROOT-01`/`02`) per screen instead.
