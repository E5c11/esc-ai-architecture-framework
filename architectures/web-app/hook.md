---
id: ARCH-WEB-APP-HOOK
type: guide
layer: architectures
platform: [web]
architecture: [web-app]
requires: [ARCH-WEB-APP, ARCH-WEB-APP-USECASE, ARCH-WEB-APP-ERR-CLASSES, PAT-OUTCOME, PAT-OBSERVER, PLAT-WEB-REACT]
related: [ARCH-WEB-APP-DATASOURCE, ARCH-PC-VIEWMODEL, PLAT-WEB-STATE, PAT-ANALYTICS-EVENTS, QG-WEB-TESTING]
tags: [hook, viewmodel, presentation, view-state, formatting, race, subscription, client-component]
status: active
---

# Hook Layer

## Responsibility

Manage a screen's UI state. Format domain data into display-ready values. Call a
UseCase (or, below the UseCase threshold, a DataSource interface) in response to user
events. Surface the result to a Component as state it can render.

That is all. No business rules (a UseCase), no provider access (a DataSource), no
markup (a Component).

This is the ViewModel of `ARCH-PC-VIEWMODEL`, written as a React hook. It is
client-side only.

## Hook vs UseCase: the bright line

| Hook | UseCase |
|---|---|
| Format a date or number for display | Decide which date or figure is correct |
| Validate an input's format for immediate feedback | Apply the business validation rule |
| Hold loading / ready / error state | Produce the success or failure result |
| Map a domain value to a presentation shape | Transform or filter domain data |
| Decide what a button press calls | Decide what the operation does |

```rule
id: ARCH-WEB-APP-HOOK-LOGIC-01
statement: A Hook MUST contain presentation logic only; business rules, calculations on domain data, and decisions about what the data means belong in a UseCase or the domain.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-HOOK-LOGIC-01 — A Hook MUST contain presentation logic only; business rules, calculations on domain data, and decisions about what the data means belong in a UseCase or the domain.
```

A hook that computes a rate, filters records by a business condition or picks "the
latest" has absorbed a UseCase, and its logic can only be tested by rendering.

## Dependencies

The import boundary is `ARCH-WEB-APP-DEP-04`: a Hook imports a UseCase or, below the
UseCase threshold, a DataSource or Repository interface, never an implementation or a
provider SDK. This section is about how it *gets* them.

```rule
id: ARCH-WEB-APP-HOOK-DEPS-01
statement: A Hook MUST receive its UseCases and DataSources, typed as interfaces, from the composition through a provider context (or props), and MUST NOT import a constructed instance as a module-level singleton.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-HOOK-DEPS-01 — A Hook MUST receive its UseCases and DataSources, typed as interfaces, from the composition through a provider context (or props), and MUST NOT import a constructed instance as a module-level singleton.
```

```typescript
// ❌ Wrong — the hook is welded to the real thing; a test must mock a module
import { loadRegionFigures } from '@/composition';

// ✅ Correct — the test wraps the hook in a provider that supplies fakes
const { loadRegionFigures } = useUseCases();
```

A single `useUseCases()` (or per-feature equivalent) reads the composition context.
The composition module owns what that context holds (`ARCH-WEB-APP-DEP-06`).

## State

```rule
id: ARCH-WEB-APP-HOOK-STATE-01
statement: A Hook MUST expose its state as a discriminated union (`loading`, `ready` with data, `error` with an `AppError`), and MUST NOT expose separate `data`, `loading` and `error` fields that can contradict each other.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-HOOK-STATE-01 — A Hook MUST expose its state as a discriminated union (`loading`, `ready` with data, `error` with an `AppError`), and MUST NOT expose separate `data`, `loading` and `error` fields that can contradict each other.
```

```typescript
export type ViewState<T> =
  | { status: 'loading' }
  | { status: 'ready'; data: T; stale?: boolean }
  | { status: 'error'; error: AppError };

export function useRegionFigures(region: RegionId): {
  state: ViewState<RegionFiguresView>;
  retry: () => void;
} { /* … */ }
```

A `{ data, loading, error }` triple admits "loading and error", "ready and error" and
"neither", states that cannot happen and that a Component then has to guard against.
A union makes them unrepresentable, and a Component switches on `status` and is
checked for exhaustiveness. This is the `web-app` hook shape; the three-field shape
in `PLAT-WEB-STATE-HOOK-01` is `web-spa` only. `stale` carries the repository's
labelled-stale value (`ARCH-WEB-APP-REP-SSOT-01`) to the screen.

```rule
id: ARCH-WEB-APP-HOOK-SCOPE-01
statement: A Hook MUST own one cohesive screen concern, and a Hook that returns state for more than one unrelated concern MUST be split.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-HOOK-SCOPE-01 — A Hook MUST own one cohesive screen concern, and a Hook that returns state for more than one unrelated concern MUST be split.
```

State shared across screens is not a hook's to own: it lives in a Context
(`PLAT-WEB-STATE`'s tiers), or in the data layer when it is data.

## Presentation mapping and formatting

```rule
id: ARCH-WEB-APP-HOOK-MAP-01
statement: A Hook MUST map domain values to presentation shapes before placing them in state, and a Component MUST receive presentation shapes only.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-HOOK-MAP-01 — A Hook MUST map domain values to presentation shapes before placing them in state, and a Component MUST receive presentation shapes only.
```

The mapping is a pure function in the hook's folder, tested without rendering. It is
what lets the domain change shape without every Component changing with it.

```rule
id: ARCH-WEB-APP-HOOK-FORMAT-01
statement: User-facing formatting (dates, numbers, percentages, currency, plurals) MUST happen in the Hook's mapping with an explicit locale and timezone, and MUST NOT depend on the runtime's defaults or be done in the domain.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-HOOK-FORMAT-01 — User-facing formatting (dates, numbers, percentages, currency, plurals) MUST happen in the Hook's mapping with an explicit locale and timezone, and MUST NOT depend on the runtime's defaults or be done in the domain.
```

Formatting with `Intl` and no explicit locale or timezone renders differently on the
server and in the browser, which is a hydration mismatch in the `server` runtime and a
wrong day on a chart in either.

## Errors

```rule
id: ARCH-WEB-APP-HOOK-ERROR-01
statement: Error state MUST store the full `AppError`, not an extracted message string, and the Component MUST decide the user-facing wording from it.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-HOOK-ERROR-01 — Error state MUST store the full `AppError`, not an extracted message string, and the Component MUST decide the user-facing wording from it.
```

A `forbidden` and an `offline` deserve different screens and different actions.
Extracting a string at the Hook discards what the Component needs to choose.

```rule
id: ARCH-WEB-APP-HOOK-ERROR-02
statement: A Hook over a retryable operation SHOULD expose a `retry` function, and a Hook that holds a dismissible error SHOULD expose a way to clear it.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-HOOK-ERROR-02 — A Hook over a retryable operation SHOULD expose a `retry` function, and a Hook that holds a dismissible error SHOULD expose a way to clear it.
```

## Effects, subscriptions and races

```rule
id: ARCH-WEB-APP-HOOK-RACE-01
statement: A Hook that starts an asynchronous operation or a subscription MUST release it when the Hook unmounts or its inputs change, and MUST ignore any result that arrives after that.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-HOOK-RACE-01 — A Hook that starts an asynchronous operation or a subscription MUST release it when the Hook unmounts or its inputs change, and MUST ignore any result that arrives after that.
```

```typescript
useEffect(() => {
  const controller = new AbortController();
  setState({ status: 'loading' });
  loadRegionFigures(region, today, controller.signal).then(outcome => {
    if (controller.signal.aborted) return;              // a newer request owns the state
    setState(toViewState(outcome));
  });
  return () => controller.abort();                      // release on unmount or input change
}, [region, today, loadRegionFigures]);
```

Without this, switching region quickly shows the figures of the region you left. The
cleanup rule for subscriptions is `PLAT-WEB-TS-CLEANUP-01`; this rule adds the stale
result, which a plain unsubscribe does not cover for one-shot calls.

## Where a Hook runs

```rule
id: ARCH-WEB-APP-HOOK-CLIENT-01
statement: A Hook MUST be used only from Client Components and MUST NOT be imported by a Server Component.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-HOOK-CLIENT-01 — A Hook MUST be used only from Client Components and MUST NOT be imported by a Server Component.
```

The `'use client'` boundary goes on the leaf Component that uses the Hook
(`PLAT-WEB-NEXT-CLIENT-01`), not on a whole page.

```rule
id: ARCH-WEB-APP-HOOK-SERVER-01
statement: In the `server` runtime a Hook MUST reach the server only through a Server Action or Route Handler call that returns an `Outcome`, and MUST NOT import a server-only DataSource.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-HOOK-SERVER-01 — In the `server` runtime a Hook MUST reach the server only through a Server Action or Route Handler call that returns an `Outcome`, and MUST NOT import a server-only DataSource.
```

A mutating Server Action revalidates what it changed (`PLAT-WEB-NEXT-APP-REVALIDATE-01`);
the Hook does not manage server cache state itself.

## Analytics

```rule
id: ARCH-WEB-APP-HOOK-ANALYTICS-01
statement: A Hook that records analytics MUST receive its tracker through the composition, and MUST fire the event inline at the point the corresponding user action or state change is already being handled.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-HOOK-ANALYTICS-01 — A Hook that records analytics MUST receive its tracker through the composition, and MUST fire the event inline at the point the corresponding user action or state change is already being handled.
```

The philosophy (which events, how many) is `PAT-ANALYTICS-EVENTS`. A tracker call
that fails never affects the user's action (`ARCH-WEB-APP-UC-SIDE-01`).

## Naming

```rule
id: ARCH-WEB-APP-HOOK-NAMING-01
statement: A Hook is named `use{Feature}` or `use{Feature}{Concern}`, lives in `features/{feature}/hooks/`, and has an explicit return type.
type: hard
scope: naming
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-HOOK-NAMING-01 — A Hook is named `use{Feature}` or `use{Feature}{Concern}`, lives in `features/{feature}/hooks/`, and has an explicit return type.
```

The explicit return type is `PLAT-WEB-TS-HOOKS-01`; the location replaces the
`web-spa` convention in `PLAT-WEB-STATE-HOOK-02`.

## Testing

```rule
id: ARCH-WEB-APP-HOOK-TEST-01
statement: A Hook MUST be tested by rendering it inside a test provider that supplies fakes of its UseCases or DataSources, asserting on the state it exposes, and MUST NOT be tested against a mocked SDK or by asserting on rendered markup.
type: hard
scope: testing
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-HOOK-TEST-01 — A Hook MUST be tested by rendering it inside a test provider that supplies fakes of its UseCases or DataSources, asserting on the state it exposes, and MUST NOT be tested against a mocked SDK or by asserting on rendered markup.
```

A hook test covers each branch of the state union (loading, ready, ready with stale
data, each error variant), the change-of-input race, and unmount cleanup. The mapping
and formatting functions are pure and have their own tests (`QG-WEB-TESTING`).

## Violations

- A Hook that computes a business figure or filters by a business rule
- A Hook that imports `firebase/*`, `fetch`, a DataSource implementation, or a
  module-level singleton from the composition
- Separate `data`, `loading` and `error` fields on a `web-app` Hook
- A domain object placed in state and passed through to a Component
- A date or number formatted with the runtime's default locale or timezone
- An error reduced to a `message` string
- An effect with no cleanup, or a result applied after the inputs changed
- A Hook imported by a Server Component
- A Hook that calls a server-only DataSource instead of a Server Action
- A Hook test that mocks the SDK
