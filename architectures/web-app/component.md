---
id: ARCH-WEB-APP-COMPONENT
type: guide
layer: architectures
platform: [web]
architecture: [web-app]
requires: [ARCH-WEB-APP, ARCH-WEB-APP-HOOK, ARCH-WEB-COMPONENTS, ARCH-WEB-APP-DOMAIN, PLAT-WEB-NEXT]
related: [ARCH-PC-VIEW, PLAT-WEB-A11Y, PLAT-WEB-DS-COMPONENT, QG-WEB-TESTING]
tags: [component, view, server-component, client-component, view-state, props, serialisation, static-export]
status: active
---

# Component Layer

## Responsibility

Render state and surface user events. A Component takes presentation-shaped props and
callbacks and returns markup. It contains no business logic, fetches nothing and
imports nothing below the Hook (`ARCH-WEB-APP-DEP-05`).

This restates `ARCH-PC-VIEW` for React and the Next.js Server/Client boundary. The
generic component rules (props discipline, composition over flags, naming, exports)
are owned by `ARCH-WEB-COMPONENTS`, which `web-app` shares with `web-spa` and
`web-content`; this document holds only what the layered architecture and the
Server/Client boundary add.

## The two component roles

| Role | What it is | Calls a Hook? | Where |
|---|---|---|---|
| **Root view** | The feature's one entry component. Calls the feature's Hook, switches on the state, passes props down | Yes, and it is the only one that does | `features/{feature}/components/{Feature}View.tsx` (Client Component) |
| **Presentational component** | Everything below it. Receives props and callbacks, renders | Never | `components/` in the feature, or `shared/` if two features use it |

A route file (`app/**/page.tsx`) composes a feature's page and contains nothing else
(`ARCH-WEB-APP-FEATURE-STRUCTURE`). In the `server` runtime a **Server Component
shell** (`{Feature}Page.tsx`) may sit between the route and the root view to render
initial data.

```rule
id: ARCH-WEB-APP-COMP-SPLIT-01
statement: Only a feature's root view MAY call the feature's Hook; every component below it MUST receive what it renders as props and what it can do as callback props.
type: hard
scope: structure
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-COMP-SPLIT-01 — Only a feature's root view MAY call the feature's Hook; every component below it MUST receive what it renders as props and what it can do as callback props.
```

This is what makes a presentational component testable with plain props, reusable in
a second screen, and previewable with sample data, with no provider and no fake in
sight.

## State and props

```rule
id: ARCH-WEB-APP-COMP-STATE-01
statement: A root view MUST handle every status of its Hook's `ViewState` with an exhaustive switch, MUST NOT render with in-flight or undefined data, and MUST choose the error presentation from the `AppError` variant.
type: hard
scope: error-handling
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-COMP-STATE-01 — A root view MUST handle every status of its Hook's `ViewState` with an exhaustive switch, MUST NOT render with in-flight or undefined data, and MUST choose the error presentation from the `AppError` variant.
```

```tsx
const state = useRegionFigures(region).state;
switch (state.status) {
  case 'loading': return <FiguresSkeleton />;
  case 'error':   return <ErrorPanel error={state.error} onRetry={retry} />;
  case 'ready':   return <FiguresPanel figures={state.data} stale={state.stale} />;
  default:        return assertNever(state);                  // a new status is a compile error
}
```

This is the `web-app` form of `ARCH-WEB-CP-01` ("guard all three states"): the union
makes the guard checkable by the compiler instead of by a reviewer.

```rule
id: ARCH-WEB-APP-COMP-PROPS-01
statement: A component MUST receive all data it renders as props and surface user actions as callback props, and MUST NOT reach for data through a context, a module import, or a global.
type: hard
scope: behavior
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-COMP-PROPS-01 — A component MUST receive all data it renders as props and surface user actions as callback props, and MUST NOT reach for data through a context, a module import, or a global.
```

Theme and locale providers are not data in this sense. The composition context is
(`ARCH-WEB-APP-COMP-DI-01`).

```rule
id: ARCH-WEB-APP-COMP-LOCAL-01
statement: A component MUST NOT keep business state or derived display data in `useState`; local state is limited to transient interface state such as open or closed, focus, hover, or an unsaved input draft.
type: hard
scope: behavior
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-COMP-LOCAL-01 — A component MUST NOT keep business state or derived display data in `useState`; local state is limited to transient interface state such as open or closed, focus, hover, or an unsaved input draft.
```

Derived data is computed during render or in the Hook's mapping
(`ARCH-WEB-APP-HOOK-MAP-01`), never copied into state and kept in sync by an effect.

```rule
id: ARCH-WEB-APP-COMP-DI-01
statement: A component MUST NOT read the composition context, call a composition accessor, or construct a dependency, including for cross-cutting concerns such as an analytics tracker.
type: hard
scope: di
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-COMP-DI-01 — A component MUST NOT read the composition context, call a composition accessor, or construct a dependency, including for cross-cutting concerns such as an analytics tracker.
```

Everything a component needs from the app arrives through its props. If a deeply
nested component needs a tracker, the Hook exposes a callback and the root view passes
it down.

## The Server/Client boundary

The domain is already plain serialisable data (`ARCH-WEB-APP-DOM-SERIAL-01`); this rule
keeps the boundary honest when a mapping is skipped.

```rule
id: ARCH-WEB-APP-COMP-SERVER-01
statement: In the `server` runtime, a Server Component shell MUST contain no hooks, no state, no event handlers and no mutation logic; it obtains initial data through a UseCase or DataSource from the composition root, maps it to presentation props, and renders.
type: hard
scope: behavior
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-COMP-SERVER-01 — In the `server` runtime, a Server Component shell MUST contain no hooks, no state, no event handlers and no mutation logic; it obtains initial data through a UseCase or DataSource from the composition root, maps it to presentation props, and renders.
```

`'use client'` goes on the root view, the smallest leaf that needs it, never on the
shell or on a layout (`PLAT-WEB-NEXT-CLIENT-01`).

```rule
id: ARCH-WEB-APP-COMP-STATIC-01
statement: In the `static-export` runtime, a Server Component MUST NOT fetch runtime data, because it runs once at build; all runtime data MUST be loaded in the browser by the root view's Hook.
type: hard
scope: behavior
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-COMP-STATIC-01 — In the `static-export` runtime, a Server Component MUST NOT fetch runtime data, because it runs once at build; all runtime data MUST be loaded in the browser by the root view's Hook.
```

A Server Component that reads a snapshot under `output: 'export'` bakes that
snapshot into the HTML at build time, and the deployed page shows stale numbers until
the next build with no error to explain it. Pages are shells; the data arrives in the
browser.

## Size and extraction

## Naming

```rule
id: ARCH-WEB-APP-COMP-NAMING-01
statement: A feature's route shell is `{Feature}Page.tsx` and its root view `{Feature}View.tsx`; every other component is named for what it shows (`ARCH-WEB-NAME-02`).
type: hard
scope: naming
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-COMP-NAMING-01 — A feature's route shell is `{Feature}Page.tsx` and its root view `{Feature}View.tsx`; every other component is named for what it shows (`ARCH-WEB-NAME-02`).
```

## Accessibility and styling

Semantic HTML, alt text, labels, headings and focus follow `PLAT-WEB-A11Y`'s
architecture-agnostic rules; styling and tokens follow `PLAT-WEB-DS-THEME`; shared
components and icons follow `PLAT-WEB-DS-COMPONENT-01` and `PLAT-WEB-DS-ICON-01`. This
document adds nothing to them.

## Testing

(`ARCH-WEB-APP-COMP-TEST-01` now lives in `QG-WEB-TESTING`.)

A presentational component that cannot be rendered with props alone has a hidden
dependency (`ARCH-WEB-APP-COMP-SPLIT-01`). The patterns are in `QG-WEB-TESTING`.

## Violations

- A presentational component calling a Hook, or the composition accessor
- A root view with an `if (loading)` chain instead of an exhaustive switch
- A domain object, a `Date` or a function passed from a Server Component to a Client Component
- `'use client'` on a page or a layout
- A derived figure stored in `useState` and synced by an effect
- A Server Component reading runtime data under `output: 'export'`
- Business logic, formatting or a provider call in a component
- A 400-line component with its content strings inline
