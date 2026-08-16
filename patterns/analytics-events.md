---
id: PAT-ANALYTICS-EVENTS
type: pattern
layer: pattern
platform: [mobile, web]
architecture: [all]
requires: []
related: [ARCH-PC-VIEWMODEL, ARCH-PC-VIEW]
tags: [analytics, telemetry, tracking, events, instrumentation, philosophy]
status: active
---

# Analytics Events

## Statement

An analytics/telemetry tracker is fired from the layer that already owns the
state or decision being tracked — never from a rendering/presentational
component. Which interactions are worth tracking at all is a separate,
per-project policy decision this document does not make on a project's
behalf; it names the choices and requires one be picked.

## Rationale

Analytics tracking is dual-use in a way that invites two different mistakes.
Structurally, it looks like a harmless, side-effect-free read (`tracker.logEvent(...)`
returns nothing, touches no visible state) — which makes it easy to reach for
from wherever is most convenient to type, including a deeply nested rendering
component that has no other reason to touch dependency injection at all. That
convenience is exactly the trap: once one component injects a tracker
directly, every component becomes a plausible place for the next one, and
"what does this screen actually track" stops having a single, inspectable
answer. The fix is the same one this framework already applies to formatting
(`ARCH-PC-VM-FORMAT-01`) and cross-feature composition data
(`ARCH-PC-COMP-ROOT-03`): a cross-cutting concern gets one legitimate entry
point, not "wherever it's needed this time."

Separately, and just as often gotten wrong: teams that never decide *how much*
to track end up with either instrumentation sprawl (an event on every pixel,
most never read by anyone) or accidental blind spots (the one conversion step
that mattered was never wired up, discovered only after the fact). Neither
failure is a structural problem — both are a missing decision. This document
treats them as two separate rules for that reason: one is a hard, universal
placement rule; the other is a required-but-project-chosen policy.

## Placement rule

```rule
id: PAT-ANALYTICS-01
statement: An analytics/telemetry tracker MUST be injected only at the layer that owns the state or decision being tracked (a ViewModel, an Orchestrator, or the platform-equivalent state/controller layer) — never inside a rendering/presentational component. A component surfaces the triggering action as a callback parameter and lets the layer that already holds the tracker fire the event.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates PAT-ANALYTICS-01 — an analytics tracker is injected directly into a rendering/presentational component instead of being fired from the state-owning layer.
```

This is the general form of what `ARCH-PC-VIEW-COMPONENT-01` already says for
one specific case (a Compose component calling `koinInject()` for a tracker);
that rule's example is this pattern's specific platform expression, not a
separate concern. See `ARCH-PC-VIEWMODEL`'s Analytics section
(`ARCH-PC-VM-ANALYTICS-01`) for the concrete Koin/Compose expression of this
rule; a platform-specific doc for other platforms can cite this pattern the
same way once one exists.

*Violation signal:* a rendering component (anything that only accepts data
and callbacks, per `ARCH-PC-VIEW-STATE-01`) directly resolves a tracker from
DI, imports one, or receives one as a non-callback constructor/parameter
dependency.

## Philosophy: a required, per-project choice

```rule
id: PAT-ANALYTICS-02
statement: A project MUST declare which analytics philosophy it follows before analytics instrumentation is added, using one of the named values below (or an explicitly documented equivalent). Absence of a declared philosophy is a Gap Protocol trigger — decide and record it, do not default silently to either "track everything" or "track nothing."
type: hard
scope: behavior
enforced_by: [planner, reviewer]
violation_message: Violates PAT-ANALYTICS-02 — new analytics instrumentation was added without the project having declared which tracking philosophy it follows.
```

| Value | What it means |
|---|---|
| `comprehensive` | Track every meaningful user-visible interaction — impressions, taps, dismissals, shows — for full engagement and funnel visibility. Accepts higher event volume and more instrumentation code as the cost of not having to predict in advance which interaction will matter later. |
| `deliberate` | An event is added only when it answers a specific, named question someone will actually look at (a metric, a dashboard, an experiment). No "just in case" tracking. Lower volume, but a genuinely new question may require a genuinely new event before it can be answered. |
| `funnel-critical-only` | Track only conversion/retention-critical steps (signup, purchase, core-loop completion). UI-engagement detail (card shown, button hover) is deliberately not tracked. |
| `none` | This project does not track user interactions at all (e.g. a component/library with no product-analytics surface of its own). |

This framework does not pick one of these on a project's behalf — the right
choice depends on product stage, privacy posture, and who actually reads the
resulting data, none of which this document can know. What it requires is
that *some* value is picked and recorded, so "should this click be tracked"
has a project-level answer instead of being re-litigated call-site by
call-site.

## Declaring the choice

A project records its choice as `frameworks.analytics: <value>` in its
`project-profile.yaml` (see `schemas/project-profile.yaml`) — the same
mechanism already used for e.g. `frameworks.notifications`. This is
retrieval-only: it resolves to this document (and any platform-specific
elaboration of it) the same way any other declared framework choice does. A
pragmatic-clean mobile project also receives this document automatically via
`ARCH-PC-VIEWMODEL`'s own `requires` chain, since the placement rule above is
inseparable from that document's own scope — the `frameworks.analytics`
declaration is what records *which philosophy*, not *whether the placement
rule applies*.

## Violations

- A tracker resolved via DI (constructor injection, `koinInject`,
  `useContext`, or equivalent) inside a component that only renders data and
  emits callbacks
- A new analytics event added to a project that has never declared a
  philosophy value
- An event added under `deliberate` or `funnel-critical-only` with no named
  consumer (metric, dashboard, experiment) for it
