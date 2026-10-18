---
id: ARCH-WEB-APP-DOMAIN
type: rules
layer: architectures
platform: [web]
architecture: [web-app]
requires: [ARCH-WEB-APP, CORE-SSOT, CORE-NAMING]
related: [ARCH-WEB-APP-DATASOURCE, ARCH-WEB-APP-REPOSITORY, ARCH-PY-DOMAIN]
tags: [domain, entity, value-object, pure, immutable, rule-table, aggregation, pipeline, determinism]
status: active
---

# Domain Layer

## Responsibility

The domain holds the app's vocabulary and rules: the values it talks about (a
record, a snapshot, a region, a figure), the invariants those values must satisfy,
and the pure functions and rule tables that decide things from them. It is the
innermost layer and the most stable. It is **pure**: given the same inputs it returns
the same outputs, touches no network, storage, clock or global state, and imports no
framework.

That purity is the payoff of the layering. The domain is the part you can test
exhaustively in milliseconds, reuse in a Cloud Function or a script, and change with
confidence, because nothing else is in the room. An aggregation pipeline (raw
records in, figures out) is domain code.

This restates `ARCH-PY-DOMAIN` for TypeScript.

## Structure

```
features/{feature}/domain/        Types, factories and pure functions for one feature
shared/domain/                    Domain code two or more features use
packages/{name}/                  A domain package, when the logic is reused outside the app
                                  (see the modules document)
```

A domain module exports types and functions, never classes holding mutable state, and
imports only other domain modules and the language's standard library
(`ARCH-WEB-APP-DEP-01`, which owns the dependency rule).

## Rules

```rule
id: ARCH-WEB-APP-DOM-PURE-01
statement: Domain functions MUST be free of I/O and ambient state: no network, storage, DOM, environment, randomness, or current-time access, and no mutation of their arguments.
type: hard
scope: behavior
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DOM-PURE-01 — Domain functions MUST be free of I/O and ambient state: no network, storage, DOM, environment, randomness, or current-time access, and no mutation of their arguments.
```

```rule
id: ARCH-WEB-APP-DOM-CLOCK-01
statement: Anything that needs the current time or a random or unique value MUST receive it as an argument or through a small port supplied from outside, and MUST NOT call `Date.now()`, `new Date()`, `Math.random()` or `crypto.randomUUID()` itself.
type: hard
scope: di
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DOM-CLOCK-01 — Anything that needs the current time or a random or unique value MUST receive it as an argument or through a small port supplied from outside, and MUST NOT call `Date.now()`, `new Date()`, `Math.random()` or `crypto.randomUUID()` itself.
```

```typescript
// ❌ Wrong — the result depends on when it runs
export const isOverdue = (due: IsoDate) => new Date(due) < new Date();

// ✅ Correct — "now" is an input, so the test is one line
export const isOverdue = (due: IsoDate, now: IsoInstant) => due < toDate(now);
```

```rule
id: ARCH-WEB-APP-DOM-VALUE-01
statement: Domain values MUST be immutable: `readonly` properties, `ReadonlyArray`, `ReadonlyMap` and `as const` data, and a change MUST produce a new value.
type: hard
scope: structure
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DOM-VALUE-01 — Domain values MUST be immutable: `readonly` properties, `ReadonlyArray`, `ReadonlyMap` and `as const` data, and a change MUST produce a new value.
```

```rule
id: ARCH-WEB-APP-DOM-SERIAL-01
statement: A domain value that can cross the Server/Client Component boundary or be stored MUST be plain serialisable data (strings, numbers, booleans, `null`, arrays and plain objects), and MUST NOT be a class instance, a `Date`, a `Map`, a `Set` or a function.
type: hard
scope: structure
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DOM-SERIAL-01 — A domain value that can cross the Server/Client Component boundary or be stored MUST be plain serialisable data (strings, numbers, booleans, `null`, arrays and plain objects), and MUST NOT be a class instance, a `Date`, a `Map`, a `Set` or a function.
```

Next.js serialises props from a Server Component to a Client Component, and a
stored snapshot is serialised too. A `Date` or a `Map` either fails or changes shape
on the way through, and the bug appears far from its cause. Keep the domain plain,
and keep `Date` arithmetic inside a function.

```rule
id: ARCH-WEB-APP-DOM-INVARIANT-01
statement: A value's invariants MUST be enforced where the value is created, by a factory or parser that returns an `Outcome`, so an invalid value cannot be constructed; validation MUST NOT be deferred to the caller.
type: hard
scope: behavior
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DOM-INVARIANT-01 — A value's invariants MUST be enforced where the value is created, by a factory or parser that returns an `Outcome`, so an invalid value cannot be constructed; validation MUST NOT be deferred to the caller.
```

Prefer branded types for values that look alike and must not be mixed (a region id
versus an agent id). The factory is the only place a brand is applied.

```rule
id: ARCH-WEB-APP-DOM-VOCAB-01
statement: A closed set of choices (statuses, regions, outcome kinds, severities) MUST be a string-literal union or an `as const` object, and bare strings compared at scattered call sites MUST NOT be used.
type: hard
scope: structure
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DOM-VOCAB-01 — A closed set of choices (statuses, regions, outcome kinds, severities) MUST be a string-literal union or an `as const` object, and bare strings compared at scattered call sites MUST NOT be used.
```

(`ARCH-WEB-APP-DOM-TABLE-02` now lives in `QG-WEB-TESTING`.)

A free-text classifier is domain code and is the part most likely to be quietly
wrong. The rules a record falls through (for example "no outcome recorded") are
reported, never hidden, so a gap in the list is visible.

```rule
id: ARCH-WEB-APP-DOM-TIME-01
statement: An instant MUST be represented with an explicit timezone (an ISO 8601 instant), a calendar date MUST be a date-only value, and domain code MUST NOT rely on the runtime's local timezone.
type: hard
scope: behavior
evidence: exercised
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DOM-TIME-01 — An instant MUST be represented with an explicit timezone (an ISO 8601 instant), a calendar date MUST be a date-only value, and domain code MUST NOT rely on the runtime's local timezone.
```

A date that means "the day the customer was visited" is not an instant. Parsing it
through the local timezone moves it a day on a server in another zone, which is a
wrong number that no test on the developer's machine catches.

```rule
id: ARCH-WEB-APP-DOM-DETERMINISM-01
statement: A transform over a collection SHOULD give the same result for the same records in any order, with an explicit sort and tie-break wherever order is part of the result.
type: soft
scope: behavior
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DOM-DETERMINISM-01 — A transform over a collection SHOULD give the same result for the same records in any order, with an explicit sort and tie-break wherever order is part of the result.
```

A provider returns records in no promised order, and an aggregation that depends on
arrival order changes when the provider does.

```rule
id: ARCH-WEB-APP-DOM-NAMING-01
statement: Domain names SHOULD come from the problem domain, not the implementation: no `Manager`, `Helper`, `Util`, `Handler`, `Dto`, `Doc` or technology names in a domain identifier.
type: soft
scope: naming
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DOM-NAMING-01 — Domain names SHOULD come from the problem domain, not the implementation: no `Manager`, `Helper`, `Util`, `Handler`, `Dto`, `Doc` or technology names in a domain identifier.
```

## Entities vs value objects

- A **value object** is defined by its content and compared by equality
  (`Region`, `FigureSet`, `Outcome`). Default to this.
- An **entity** has an identity that persists as its content changes (`Feed`,
  `Snapshot`). It is still an immutable plain object: identity is a field, and a
  change produces a new object that a DataSource persists under the same identity.

Prefer a pure function `isReady(task, completed)` next to the type over a method.
It is easier to test and it serialises (`ARCH-WEB-APP-DOM-SERIAL-01`).

## What does NOT belong here

- Parsing a provider payload — the DataSource (`ARCH-WEB-APP-DS-PARSE-01`)
- Reading a workbook, a response or a document — the DataSource or a gateway
- Formatting a number or date for display — the hook
- Deciding when to fetch or how to cache — a UseCase or Repository
- Reading configuration or the environment — the composition module

## Testing

Domain code is tested with plain inputs and no doubles: no fake, no mock, no
emulator, no framework. A domain test that needs a mock has found code that does
not belong in the domain.

## Violations

- `new Date()`, `Date.now()` or `Math.random()` inside a domain function
- A domain module importing React, Next, a provider SDK or `fetch`
- A function that mutates the array it was given
- A `Date`, `Map` or class instance in a value that crosses to a Client Component
- A branch on a bare string that should be a vocabulary member
- A timezone-dependent date parse
- An aggregation whose result changes with the input order
