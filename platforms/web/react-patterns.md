---
id: PLAT-WEB-REACT-PATTERNS
type: guide
layer: platforms
platform: [web]
architecture: [web-spa, web-app, web-content]
requires: [PLAT-WEB-REACT]
related: [PLAT-WEB-STATE, PLAT-WEB-FORMS, PLAT-WEB-NEXT, PLAT-WEB-NEXT-APP, ARCH-WEB-COMPONENTS]
tags: [react, react-19, effects, derived-state, keys, strict-mode, suspense, use, use-action-state, use-optimistic, error-boundary, memoisation]
status: active
---

# React Patterns

Extends: `PLAT-WEB-REACT`

`PLAT-WEB-REACT` fixes the TypeScript and structural conventions: strict mode, props
interfaces, explicit hook return types, effect cleanup. This guide covers how React is
used correctly: when an effect is the wrong tool, how lists and state behave, and the
React 19 APIs a data-driven app reaches for. It applies to every web architecture;
where an architecture's layer document already owns a rule, that rule is cited rather
than repeated.

Written for **React 19**. A project on an earlier version follows the rules that do not
name a 19-only API.

## Effects are for synchronising with the outside

```rule
id: PLAT-WEB-RP-EFFECT-01
statement: An effect MUST be used only to synchronise with something outside React (a subscription, a timer, the DOM, a network request), and MUST NOT be used to compute data derivable from props or state, to copy one piece of state into another, or to respond to a user event.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-RP-EFFECT-01 — An effect MUST be used only to synchronise with something outside React (a subscription, a timer, the DOM, a network request), and MUST NOT be used to compute data derivable from props or state, to copy one piece of state into another, or to respond to a user event.
```

```tsx
// ❌ Wrong — derived data stored in state and kept in sync by an effect
const [visible, setVisible] = useState<Row[]>([]);
useEffect(() => { setVisible(rows.filter(r => r.region === region)); }, [rows, region]);

// ✅ Correct — computed while rendering; there is nothing to keep in sync
const visible = rows.filter(r => r.region === region);
```

An effect that sets state runs after the render that needed it, causing an extra render
and a frame showing the stale value. A user event is answered in its handler, where the
cause is known, not in an effect that infers it from a change.

```rule
id: PLAT-WEB-RP-STRICT-01
statement: The app MUST run in React Strict Mode, and every effect MUST be safe to mount, unmount and mount again.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-RP-STRICT-01 — The app MUST run in React Strict Mode, and every effect MUST be safe to mount, unmount and mount again.
```

In development, Strict Mode runs each effect, cleans it up and runs it again, to expose
effects that leak. An effect that opens a second listener, sends a second request or
initialises an SDK twice fails here first, in front of a developer, instead of in
production in front of a user.

```rule
id: PLAT-WEB-RP-DEPS-01
statement: Dependency arrays of effects and memoised values MUST be complete, the `react-hooks/exhaustive-deps` lint rule MUST be enabled as an error, and it MUST NOT be silenced without a comment stating why.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-RP-DEPS-01 — Dependency arrays of effects and memoised values MUST be complete, the `react-hooks/exhaustive-deps` lint rule MUST be enabled as an error, and it MUST NOT be silenced without a comment stating why.
```

An incomplete array is a stale closure: the effect keeps using the first render's
values, and the bug appears only when an input changes.

## State and lists

```rule
id: PLAT-WEB-RP-IMMUTABLE-01
statement: State and props MUST NOT be mutated; an update MUST produce a new value.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-RP-IMMUTABLE-01 — State and props MUST NOT be mutated; an update MUST produce a new value.
```

React decides whether to re-render by comparing references. `rows.push(x); setRows(rows)`
changes the data and not the reference, so nothing renders.

```rule
id: PLAT-WEB-RP-KEY-01
statement: Elements in a rendered list MUST have a `key` that is stable and unique among siblings and comes from the data (an id), and an array index MUST NOT be the key of a list that can be filtered, sorted, inserted into or reordered.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-RP-KEY-01 — Elements in a rendered list MUST have a `key` that is stable and unique among siblings and comes from the data (an id), and an array index MUST NOT be the key of a list that can be filtered, sorted, inserted into or reordered.
```

An index key attaches an input's typed text, an open row or a focus state to a position,
not to the record, so sorting a table moves the data and leaves the state behind.

```rule
id: PLAT-WEB-RP-CONTEXT-01
statement: A context value MUST be referentially stable between renders in which its content has not changed, and contexts that change at different rates SHOULD be separate.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-RP-CONTEXT-01 — A context value MUST be referentially stable between renders in which its content has not changed, and contexts that change at different rates SHOULD be separate.
```

A provider that passes `value={{ user, setUser }}` creates a new object every render and
re-renders every consumer. The composition graph (`ARCH-WEB-APP-COMPOSE-CONTEXT-01`) is
built once and so is stable by construction.

## React 19 APIs

```rule
id: PLAT-WEB-RP-USE-01
statement: `use(promise)` MUST be given a promise that is stable across renders (created outside the component, in a parent, or from a cache) and MUST be inside a Suspense boundary; a promise MUST NOT be created during render and passed to `use`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-RP-USE-01 — `use(promise)` MUST be given a promise that is stable across renders (created outside the component, in a parent, or from a cache) and MUST be inside a Suspense boundary; a promise MUST NOT be created during render and passed to `use`.
```

A new promise on every render suspends forever, because each render starts the wait
again. In an app with a Hook layer, data arrives through `ViewState`
(`ARCH-WEB-APP-HOOK-STATE-01`), and `use` is for the cases that layer does not cover,
such as reading a context conditionally or a promise a Server Component hands down.

```rule
id: PLAT-WEB-RP-ACTION-01
statement: Where a form's submission is not owned by a form library, its pending state and result MUST come from `useActionState` and `useFormStatus` rather than hand-rolled flags, and the action MUST return an `Outcome` instead of throwing for an expected failure.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-RP-ACTION-01 — Where a form's submission is not owned by a form library, its pending state and result MUST come from `useActionState` and `useFormStatus` rather than hand-rolled flags, and the action MUST return an `Outcome` instead of throwing for an expected failure.
```

Forms backed by `react-hook-form` follow `PLAT-WEB-FORMS`, which owns their submission
state; this rule is for the simple forms that do not need that library. For the
Server Action form of the return-not-throw rule see `PLAT-WEB-NEXT-APP-THROW-01`.

```rule
id: PLAT-WEB-RP-OPTIMISTIC-01
statement: `useOptimistic` MUST be used only for an update whose outcome the UI can reconcile, and a failed update MUST roll the displayed value back and show the error outcome.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-RP-OPTIMISTIC-01 — `useOptimistic` MUST be used only for an update whose outcome the UI can reconcile, and a failed update MUST roll the displayed value back and show the error outcome.
```

An optimistic toggle that fails and stays toggled is a screen that lies. Do not use it for
a write whose failure the user must act on before continuing, or for a destructive
action.

```rule
id: PLAT-WEB-RP-REF-01
statement: New function components in React 19 SHOULD accept `ref` as an ordinary prop and SHOULD NOT use `forwardRef`.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-RP-REF-01 — New function components in React 19 SHOULD accept `ref` as an ordinary prop and SHOULD NOT use `forwardRef`.
```

## Error boundaries

```rule
id: PLAT-WEB-RP-BOUNDARY-01
statement: Error boundaries MUST be placed around regions that can fail independently (a route, a panel, a chart), not around every component, and a boundary MUST be assumed to catch render errors only, never errors thrown in event handlers or asynchronous code.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-RP-BOUNDARY-01 — Error boundaries MUST be placed around regions that can fail independently (a route, a panel, a chart), not around every component, and a boundary MUST be assumed to catch render errors only, never errors thrown in event handlers or asynchronous code.
```

A failing chart should not blank the rest of the dashboard, so a chart panel is its own
boundary. A rejected promise in a click handler never reaches a boundary at all, which is
why expected failures are returned as outcomes (`ARCH-WEB-APP-EFLOW-RETURN-01`) and a
boundary exists only for defects. In Next.js the route-level boundary is `error.tsx`;
the architecture's rule for what it must do is `ARCH-WEB-APP-EFLOW-BOUNDARY-01`.

## Memoisation

```rule
id: PLAT-WEB-RP-MEMO-01
statement: `useMemo`, `useCallback` and `React.memo` MUST NOT be added without a measured reason; where the React Compiler is enabled, manual memoisation MUST NOT be added at all.
type: soft
scope: performance
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-RP-MEMO-01 — `useMemo`, `useCallback` and `React.memo` MUST NOT be added without a measured reason; where the React Compiler is enabled, manual memoisation MUST NOT be added at all.
```

Memoisation has a cost and a correctness risk (a wrong dependency array,
`PLAT-WEB-RP-DEPS-01`). Measure first. The common real cost in a data-heavy dashboard is
a large list or a heavy aggregation recomputed on every render; the fix for the second
is to compute it once in the Hook's mapping or the domain
(`ARCH-WEB-APP-HOOK-MAP-01`), not to wrap it in `useMemo` at the call site.

## Violations

- An effect that sets state from props or other state
- An effect that runs a request in response to a click
- An effect with a missing dependency, and a lint disable with no reason
- `array.push` followed by `setState(array)`
- `key={index}` on a sortable table
- A provider whose `value` is a fresh object each render
- A promise created inside a component and passed to `use`
- An optimistic update that is never rolled back
- One error boundary around the whole app and none around a chart
- `useMemo` wrapped around everything "for performance"
