---
id: ARCH-PY-DOMAIN
type: rules
layer: architectures
platform: [python]
architecture: python-app
requires: [ARCH-PY, CORE-SSOT, CORE-NAMING]
related: [ARCH-PY-USECASE, ARCH-PY-POLICY, ARCH-PY-ERROR, PLAT-PY-TYPING]
tags: [domain, entity, value-object, pure, dataclass, clock, rule-table]
---
# Domain Layer

## Responsibility

The domain holds the program's vocabulary and rules: the values it talks about
(a task, a plan, a work type, a verification verdict), the invariants those values
must satisfy, and the policies and rule tables that decide things from them. It is
the innermost layer and the most stable one. It is **pure**: given the same inputs it
returns the same outputs, touches no disk, network, process, clock, or global state.

That purity is the payoff of the whole architecture — the domain is the part you can
test exhaustively in milliseconds and reason about without running anything.

## Rules

```rule
id: PYDOM-PURE-01
statement: Domain functions and methods MUST be free of I/O and ambient state — no file, network, subprocess, environment, randomness, or current-time access.
type: hard
scope: behavior
enforced_by: [ci, reviewer]
violation_message: Violates PYDOM-PURE-01 — Domain functions and methods MUST be free of I/O and ambient state — no file, network, subprocess, environment, randomness, or current-time access.
```

```rule
id: PYDOM-CLOCK-01
statement: Anything that needs the current time or a random/unique value MUST receive it as an argument or through a `Clock`/`IdGenerator` port supplied by the application layer, never call `datetime.now()`, `time.time()`, `uuid.uuid4()`, or `random` directly.
type: hard
scope: di
enforced_by: [ci, reviewer]
violation_message: Violates PYDOM-CLOCK-01 — Anything that needs the current time or a random/unique value MUST receive it as an argument or through a `Clock`/`IdGenerator` port supplied by the application layer, never call `datetime.now()`, `time.time()`, `uuid.uuid4()`, or `random` directly.
```

```rule
id: PYDOM-VALUE-01
statement: Domain values MUST be immutable — `@dataclass(frozen=True, slots=True)`, `NamedTuple`, or `Enum` — and collections held by them MUST be tuples or frozen mappings, not lists or dicts.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYDOM-VALUE-01 — Domain values MUST be immutable — `@dataclass(frozen=True, slots=True)`, `NamedTuple`, or `Enum` — and collections held by them MUST be tuples or frozen mappings, not lists or dicts.
```

Mutable shared values are where "who changed this?" bugs are born. A change is a new
value (`dataclasses.replace`).

```rule
id: PYDOM-INVARIANT-01
statement: A value's invariants MUST be enforced in its constructor (`__post_init__`) so an invalid instance cannot exist; validation MUST NOT be deferred to the caller.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYDOM-INVARIANT-01 — A value's invariants MUST be enforced in its constructor (`__post_init__`) so an invalid instance cannot exist; validation MUST NOT be deferred to the caller.
```

```rule
id: PYDOM-VOCAB-01
statement: A closed set of choices (work types, stage kinds, statuses, severities) MUST be an `Enum` or a `Literal` type — never bare strings compared at scattered call sites.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYDOM-VOCAB-01 — A closed set of choices (work types, stage kinds, statuses, severities) MUST be an `Enum` or a `Literal` type — never bare strings compared at scattered call sites.
```

The value's textual form is a boundary concern: parse it once at the edge into the
enum, and convert back only when rendering.

```rule
id: PYDOM-TABLE-01
statement: Behavior that varies by a closed vocabulary (per work type, per stage, per severity) SHOULD be expressed as a lookup table of frozen values keyed by that vocabulary, not as an if/elif ladder.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYDOM-TABLE-01 — Behavior that varies by a closed vocabulary (per work type, per stage, per severity) SHOULD be expressed as a lookup table of frozen values keyed by that vocabulary, not as an if/elif ladder.
```

A table can be validated at import time, listed in help, exhaustively tested
(`for key in Vocabulary`), and extended by one entry. An `if` ladder can do none of
these. This is how procedure definitions (`ARCH-PY-USECASE`) are stored.

```rule
id: PYDOM-TABLE-02
statement: A rule table MUST be checked for completeness against its vocabulary by a test — every member has an entry and every entry's referenced names exist.
type: hard
scope: testing
enforced_by: [ci, reviewer]
violation_message: Violates PYDOM-TABLE-02 — A rule table MUST be checked for completeness against its vocabulary by a test — every member has an entry and every entry's referenced names exist.
```

```rule
id: PYDOM-NAMING-01
statement: Domain names MUST come from the problem domain, not the implementation — no `Manager`, `Helper`, `Util`, `Handler`, or technology names in a domain identifier.
type: soft
scope: naming
enforced_by: [reviewer]
violation_message: Violates PYDOM-NAMING-01 — Domain names MUST come from the problem domain, not the implementation — no `Manager`, `Helper`, `Util`, `Handler`, or technology names in a domain identifier.
```

## Entities vs value objects

- A **value object** is defined by its content and compared by equality
  (`Stage`, `Match`, `VerificationVerdict`). Default to this.
- An **entity** has an identity that persists as its content changes (`Task`,
  `Initiative`). It is still an immutable value in Python — identity is a field, and a
  change produces a new instance that the DataSource persists under the same
  identity.

Do not add behavior methods to entities for the sake of an "anemic model" worry. A pure
function `is_ready(task, completed)` next to the type is clearer in Python than a
method, and easier to test.

## What does NOT belong here

- Parsing or serializing (YAML, JSON, SQL rows) — infrastructure or entrypoint
- Calling a provider or running a process — a Gateway
- Deciding *how to ask a user* — an entrypoint / `ARCH-PY-POLICY`
- Configuration loading — the composition root
