---
id: ARCH-WEB-APP-USECASE
type: guide
layer: architectures
platform: [web]
architecture: [web-app]
requires: [ARCH-WEB-APP, ARCH-WEB-APP-DATASOURCE, ARCH-WEB-APP-DOMAIN, PAT-OUTCOME, PAT-OBSERVER, CORE-DI, CORE-TESTING]
related: [ARCH-WEB-APP-REPOSITORY, ARCH-WEB-APP-ERR-CLASSES, ARCH-PC-USECASE, ARCH-PY-USECASE]
tags: [usecase, orchestrator, business-logic, outcome, side-effects, idempotence, testing]
status: active
---

# UseCase Layer

## Responsibility

Encapsulate one business operation (a UseCase) or sequence several of them (an
Orchestrator). A UseCase reads from and writes to DataSources and Repositories
through their interfaces and applies domain rules. It never reads from or writes to
the UI, and it owns no provider.

This restates `ARCH-PC-USECASE` for TypeScript. A UseCase is plain TypeScript: no
React, no Next.js, no provider SDK (`ARCH-WEB-APP-DEP-02`).

## When the layer exists

The threshold is `ARCH-WEB-APP-USECASE-01`, owned by the overview: the layer appears
once a feature's logic outgrows a single DataSource call, and not before. Below that,
a Hook calls the DataSource interface directly (`ARCH-WEB-APP-DEP-04`) and this layer
is absent.

The reverse also holds, and it is the first rule of this layer.

```rule
id: ARCH-WEB-APP-UC-LOGIC-01
statement: A UseCase MUST contain business logic that justifies its existence; a UseCase that only forwards a call to a DataSource or Repository MUST be removed.
type: hard
scope: behavior
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-UC-LOGIC-01 — A UseCase MUST contain business logic that justifies its existence; a UseCase that only forwards a call to a DataSource or Repository MUST be removed.
```

A forwarding UseCase is boilerplate that every future change must edit twice.

## UseCase vs Orchestrator

| | UseCase | Orchestrator |
|---|---|---|
| Contains logic | Yes: validation, transformation, calculation, decisions | No: sequencing only |
| Calls | DataSources, Repositories, domain functions | Other UseCases |
| Allowed to branch on data | Yes | No |

```rule
id: ARCH-WEB-APP-UC-SINGLE-01
statement: A UseCase MUST do one operation and expose one public entry point.
type: hard
scope: structure
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-UC-SINGLE-01 — A UseCase MUST do one operation and expose one public entry point.
```

A UseCase is a function built from its dependencies (or a class with one `execute`
method):

```typescript
export interface LoadRegionFigures {
  (region: RegionId, today: IsoDate): Promise<Outcome<RegionFigures>>;
}

export const createLoadRegionFigures = (deps: {
  snapshots: SnapshotDataSource;
}): LoadRegionFigures =>
  async (region, today) => {
    const latest = await deps.snapshots.getLatest(region);
    if (!latest.ok) return latest;
    if (latest.data === null) return ok(emptyFigures(region));
    return ok(withFreshness(latest.data, today));       // pure domain function
  };
```

```rule
id: ARCH-WEB-APP-UC-ORCH-01
statement: An Orchestrator MUST contain no logic: no branching on data and no calculation, only sequencing and passing results between steps.
type: hard
scope: behavior
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-UC-ORCH-01 — An Orchestrator MUST contain no logic: no branching on data and no calculation, only sequencing and passing results between steps.
```

If a condition or a calculation appears in an Orchestrator, extract it to a UseCase
and call that.

Coordination between UseCases is the Orchestrator's job and only its. A UseCase that
calls a UseCase has hidden an Orchestrator inside itself, and the dependency graph
between operations stops being visible.

## Purity of the surroundings

Time is passed in, as `ARCH-WEB-APP-DOM-CLOCK-01` requires of the domain, so a test
fixes "today" and a rule about "the last ten days" is checkable.

```rule
id: ARCH-WEB-APP-UC-STATELESS-01
statement: A UseCase MUST hold no state between calls: no module-level variable, cache, or counter that a call reads or writes.
type: hard
scope: behavior
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-UC-STATELESS-01 — A UseCase MUST hold no state between calls: no module-level variable, cache, or counter that a call reads or writes.
```

State between calls is a cache, and a cache has an owner and a rule for going stale:
a Repository (`ARCH-WEB-APP-REP-SSOT-01`). A module-level variable in a UseCase is a
shared cache with neither, and it makes a test depend on the one before it.

## Return types

```rule
id: ARCH-WEB-APP-UC-RETURN-01
statement: A UseCase MUST return `Outcome` of domain values, MUST NOT return provider, DataSource or Repository types, and MUST NOT emit loading states.
type: hard
scope: return-type
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-UC-RETURN-01 — A UseCase MUST return `Outcome` of domain values, MUST NOT return provider, DataSource or Repository types, and MUST NOT emit loading states.
```

"Loading" is a UI state and belongs to the Hook. A UseCase answers, or fails.

A UseCase must not collapse a live source into a single value, which would freeze a
screen at the first emission, and must not poll to fake one
(`ARCH-WEB-APP-DS-RETURN-03` applies here too).

## Error handling

Provider failures were translated once, in the DataSource
(`ARCH-WEB-APP-ERR-MAP-01`); a UseCase receives `AppError` values.

Adding domain meaning is a decision: a `notFound` on "load the latest snapshot" is
an empty state the UI shows, so the UseCase may turn it into an empty result; the
same `notFound` on "update this feed" is a failure and passes through. The UseCase
states the decision in code and a test.

This keeps a user's navigation away from turning into an error banner
(`ARCH-WEB-APP-ERR-CANCEL-01`).

## Writes

```rule
id: ARCH-WEB-APP-UC-WRITE-01
statement: A UseCase that writes more than one document in one store MUST do so in one atomic operation the DataSource provides (a batch, a transaction, or a single callable), with no exception.
type: hard
scope: behavior
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-UC-WRITE-01 — A UseCase that writes more than one document in one store MUST do so in one atomic operation the DataSource provides (a batch, a transaction, or a single callable), with no exception.
```

This is `SVC-TX-02`'s failure (a half-applied write) in Firestore terms. Two sequential writes to a provider are not atomic, and the second can fail while the first is already visible to other users.

```rule
id: ARCH-WEB-APP-UC-WRITE-02
statement: A write that spans two stores or projects (so no single batch can cover it) MUST be idempotent and ordered: the target is written first under a deterministic id by an upsert, and the marker or source update second, so repeating it after a partial failure cannot duplicate.
type: hard
scope: behavior
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-UC-WRITE-02 — A write that spans two stores or projects (so no single batch can cover it) MUST be idempotent and ordered: the target is written first under a deterministic id by an upsert, and the marker or source update second, so repeating it after a partial failure cannot duplicate.
```

A promotion that does `addDoc` into the target (a new id each call) and then marks the source leaves a duplicate in the target when the marker write fails and the operation is retried. The same operation with `setDoc` under the source's id is safe to repeat.

When a cross-store write does fail part-way, return an outcome that says which writes happened, so the UI can show a truthful state and a retry is safe.

## Side effects that must not block the result

An analytics event, a cache warm-up or an audit entry is a side effect the caller does
not wait for and whose failure must not fail the operation.

```rule
id: ARCH-WEB-APP-UC-SIDE-01
statement: A side effect that must not block the result MUST be started without being awaited, MUST have its own failure handled and logged, and MUST NOT leave an unhandled promise rejection.
type: hard
scope: error-handling
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-UC-SIDE-01 — A side effect that must not block the result MUST be started without being awaited, MUST have its own failure handled and logged, and MUST NOT leave an unhandled promise rejection.
```

```typescript
// ❌ Wrong — an analytics failure fails the save, or rejects unobserved
await deps.analytics.track('feed_saved');
deps.analytics.track('feed_saved');

// ✅ Correct — fire and contain
void deps.analytics.track('feed_saved').catch(deps.log.warn);
```

## Naming

```rule
id: ARCH-WEB-APP-UC-NAMING-01
statement: A UseCase is named `{Action}{Entity}UseCase` as a type and `create{Action}{Entity}` as its factory, and lives in `features/{feature}/useCases/{Action}{Entity}UseCase.ts`.
type: hard
scope: naming
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-UC-NAMING-01 — A UseCase is named `{Action}{Entity}UseCase` as a type and `create{Action}{Entity}` as its factory, and lives in `features/{feature}/useCases/{Action}{Entity}UseCase.ts`.
```

Use a verb phrase from the domain: `LoadRegionFigures`, `SaveFeed`, `RebuildSnapshot`. Not
`DashboardData`, `FirestoreFetcher` or `HandleClick`.

## Testing

(`ARCH-WEB-APP-UC-TEST-01` now lives in `QG-WEB-TESTING`.)

The fakes pass the DataSource contract tests (`ARCH-WEB-APP-DS-TEST-01`), so a UseCase
test that passes against a fake is evidence about the real DataSource, not about a
guess at it. A UseCase test that needs a mocked SDK has found a dependency that was
never an interface.

## Violations

- A UseCase that only forwards one call
- A UseCase calling another UseCase, or an Orchestrator with an `if` in it
- `Date.now()`, `window`, `localStorage` or `console.log` inside a UseCase
- A module-level cache or counter read by a UseCase
- A DataSource type, a snapshot or a loading flag in a UseCase's return type
- An error outcome swallowed and replaced by an empty list
- A `try`/`catch` that hides a programming error
- Two writes in sequence with no account of the second failing
- An awaited analytics call that fails the operation
- A UseCase named for a screen or a provider
