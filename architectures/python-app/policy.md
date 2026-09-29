---
id: ARCH-PY-POLICY
type: rules
layer: architectures
platform: [python]
architecture: python-app
requires: [ARCH-PY, CORE-DI, CORE-COUPLING]
related: [ARCH-PY-USECASE, ARCH-PY-ENTRYPOINT, ARCH-PY-DOMAIN, ARCH-PY-OBSERVABILITY, ARCH-PY-COMPOSITION]
tags: [policy, strategy, preferences, roles, autonomy, interaction, trust, evidence, seams]
---
# Policy and Interaction Seams

## The problem this solves

Real programs behave differently for different users: a newcomer wants to be asked and
told why; an experienced user wants sensible defaults applied silently; an automated
caller wants neither. The tempting implementation is `if role == "junior": ...`
scattered wherever the difference shows up. That produces persona logic in the engine,
untestable combinatorics, and — worst — code paths where a safety check runs for one
kind of user and not another.

This document defines the alternative: **variation is confined to a small number of
named seams, expressed as injected policy objects over independent preference
settings, and it may change *how* something is done or shown, never *whether a
mandatory step runs*.**

## Rules

```rule
id: PYPOL-SEAM-01
statement: Behavior that varies by user preference MUST be implemented as an injected policy object behind a Protocol at a named seam; code MUST NOT branch on a persona, role, or preset name outside the code that translates a preset into settings.
type: hard
scope: di
enforced_by: [ci, reviewer]
violation_message: Violates PYPOL-SEAM-01 — Behavior that varies by user preference MUST be implemented as an injected policy object behind a Protocol at a named seam; code MUST NOT branch on a persona, role, or preset name outside the code that translates a preset into settings.
```

```rule
id: PYPOL-KNOBS-01
statement: User preference MUST be modelled as a small set of independent, typed settings (each an Enum or Literal), not as one flat list of personas; named presets MAY exist only as a mapping onto those settings, resolved once at configuration time.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYPOL-KNOBS-01 — User preference MUST be modelled as a small set of independent, typed settings (each an Enum or Literal), not as one flat list of personas; named presets MAY exist only as a mapping onto those settings, resolved once at configuration time.
```

Two independent knobs express far more than four hard-coded roles and compose without
new code. A typical pair: *how much the system asks vs. decides* (autonomy) and *how
much it explains* (explanation depth). A "junior developer" preset is just
`(ask-mostly, teaching)`; nothing in the engine knows the word "junior".

```rule
id: PYPOL-MANDATORY-01
statement: A stage marked mandatory MUST run for every combination of settings; a policy MAY choose to ask, auto-resolve, or explain it, but MUST NOT skip it or report it as passed without it having run.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYPOL-MANDATORY-01 — A stage marked mandatory MUST run for every combination of settings; a policy MAY choose to ask, auto-resolve, or explain it, but MUST NOT skip it or report it as passed without it having run.
```

```rule
id: PYPOL-VARIABLE-01
statement: Each stage MUST be declared either `fixed` (identical for every caller) or `variable` (a policy chooses ask vs. auto-resolve); only `variable` stages MAY consult a policy, and the declaration MUST live in the stage definition, not at the call site.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYPOL-VARIABLE-01 — Each stage MUST be declared either `fixed` (identical for every caller) or `variable` (a policy chooses ask vs. auto-resolve); only `variable` stages MAY consult a policy, and the declaration MUST live in the stage definition, not at the call site.
```

```rule
id: PYPOL-RENDER-01
statement: Explanation depth MUST be a rendering concern only — it selects how much already-computed context is shown; it MUST NOT cause additional computation or change any decision.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYPOL-RENDER-01 — Explanation depth MUST be a rendering concern only — it selects how much already-computed context is shown; it MUST NOT cause additional computation or change any decision.
```

If a "teaching" mode needs a fact, the use case computed it regardless; the renderer
chooses whether to show it. This keeps every mode's behavior identical and testable.

## Auto-resolution is bounded by evidence, not by a list

When a policy is allowed to resolve a decision on the user's behalf, the safe boundary
is **how much verified evidence backs the decision**, not a hand-maintained list of
"sensitive topics":

- Applying a decision already covered by a vetted, resolved source (an established
  framework profile) is execution, not judgment, and MAY be auto-resolved.
- A decision with no vetted source — an unreviewed, locally-invented one — always
  surfaces to a human *unless* it has accumulated a real record of good outcomes.
- The record is built from **repeated applications judged by an objective measure**
  (a conformance check, a passing verification), never one run in either direction: a
  single failure does not condemn a sound decision (the failure may lie elsewhere),
  and a single success does not fast-track a poor one.

```rule
id: PYPOL-FLOOR-01
statement: A severity floor MUST apply independent of the autonomy setting: a decision lacking a vetted source and lacking accumulated evidence MUST be surfaced to a human regardless of how auto-leaning the user's settings are.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYPOL-FLOOR-01 — A severity floor MUST apply independent of the autonomy setting: a decision lacking a vetted source and lacking accumulated evidence MUST be surfaced to a human regardless of how auto-leaning the user's settings are.
```

```rule
id: PYPOL-EVIDENCE-01
statement: A trust rating MUST be computed from an objective measure across multiple applications, MUST separate the decision's quality from unrelated failures where the measure allows, and MUST NOT be raised or lowered by a single observation.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYPOL-EVIDENCE-01 — A trust rating MUST be computed from an objective measure across multiple applications, MUST separate the decision's quality from unrelated failures where the measure allows, and MUST NOT be raised or lowered by a single observation.
```

The rating computation is domain logic (pure, table-tested); the evidence store is a
DataSource; the *thresholds* are named constants in the domain, not literals in a use
case.

```rule
id: PYPOL-PERSIST-01
statement: Persisted auto-resolved decisions MUST be stored per decision kind in the store that fits that kind's trust and reuse properties; different kinds MUST NOT share one generic "remembered decisions" mechanism.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYPOL-PERSIST-01 — Persisted auto-resolved decisions MUST be stored per decision kind in the store that fits that kind's trust and reuse properties; different kinds MUST NOT share one generic "remembered decisions" mechanism.
```

Product-shape decisions (scope, completion conditions) belong with the project's
durable roadmap; pattern-application decisions belong with the evidence-rated
architecture notes. They are both "remembered decisions" and they are not the same
thing.

## Contribution and sharing are separate from telemetry

Sharing evidence outward (a rated note offered back to a shared framework) is an
explicit, attributed, human-reviewed contribution, distinct from operational
telemetry. Neither is on by default. See `ARCH-PY-OBSERVABILITY`.

## Testing

Test each policy in isolation as a pure decision over `(stage, evidence, settings)`.
Test the seams once: a parametrized test runs every procedure under every settings
combination and asserts the *set of stages that ran* is identical
(`PYPOL-MANDATORY-01`). Nothing else in the suite needs a settings matrix.
