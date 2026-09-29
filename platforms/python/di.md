---
id: PLAT-PY-DI
type: guide
layer: platforms
platform: [python]
architecture: python-app
requires: [ARCH-PY, ARCH-PY-COMPOSITION, CORE-DI, PLAT-PY-TYPING]
related: [ARCH-PY-USECASE, PLAT-PY-TESTING]
tags: [dependency-injection, protocol, constructor-injection, composition-root, fakes, no-container]
---
# Dependency Injection in Python

Extends: `ARCH-PY-COMPOSITION`

## The idiom

Constructor injection by hand. A collaborator is a constructor (or function) parameter
typed as a Protocol; the composition root passes the concrete object.

```python
class RunTask(Protocol): ...

@dataclass(frozen=True)
class ApplyPlan:
    drafts: DraftStore          # Protocol
    manifests: ManifestWriter   # Protocol
    clock: Clock                # Protocol

    def __call__(self, initiative_id: InitiativeId, answers: Answers) -> PlanResult: ...
```

## Rules

```rule
id: PYDI-CONSTRUCTOR-01
statement: Collaborators MUST be passed in through the constructor or as explicit function parameters; a class MUST NOT instantiate an infrastructure collaborator, look one up in a global registry, or import a module-level singleton.
type: hard
scope: di
enforced_by: [ci, reviewer]
violation_message: Violates PYDI-CONSTRUCTOR-01 — Collaborators MUST be passed in through the constructor or as explicit function parameters; a class MUST NOT instantiate an infrastructure collaborator, look one up in a global registry, or import a module-level singleton.
```

```rule
id: PYDI-NOCONTAINER-01
statement: A dependency-injection container or service-locator library MUST NOT be introduced unless a written justification shows manual wiring at the composition root has become unmanageable.
type: soft
scope: di
enforced_by: [reviewer]
violation_message: Violates PYDI-NOCONTAINER-01 — A dependency-injection container or service-locator library MUST NOT be introduced unless a written justification shows manual wiring at the composition root has become unmanageable.
```

A container replaces a readable stack trace with reflection, and Python's first-class
functions and keyword arguments make the plain approach short.

```rule
id: PYDI-DEFAULT-01
statement: A default argument MUST NOT construct a collaborator (`def __init__(self, store=SqliteStore())`); defaults are for plain values, and collaborators are always supplied by the caller.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates PYDI-DEFAULT-01 — A default argument MUST NOT construct a collaborator (`def __init__(self, store=SqliteStore())`); defaults are for plain values, and collaborators are always supplied by the caller.
```

A default-constructed collaborator is evaluated at import time (once, shared) and
silently reintroduces the hidden dependency the pattern removes.

```rule
id: PYDI-NARROW-01
statement: A collaborator's Protocol MUST expose only the operations its consumer uses; a consumer needing two capabilities of one implementation SHOULD depend on two narrow Protocols rather than one wide one.
type: soft
scope: di
enforced_by: [reviewer]
violation_message: Violates PYDI-NARROW-01 — A collaborator's Protocol MUST expose only the operations its consumer uses; a consumer needing two capabilities of one implementation SHOULD depend on two narrow Protocols rather than one wide one.
```

One `SqliteStore` class may implement `DraftStore`, `TaskStore`, and `EventLog`; each
use case sees only the port it needs.

## Functions as collaborators

When a collaborator is a single operation, pass a callable typed with `Callable[...]`
or a one-method Protocol; `functools.partial` binds configuration. Do not write a class
just to hold one method.

## Test doubles

Provide, for each port you own, a small **fake** implementation living beside the
tests (in-memory, deterministic). A fake is used by many tests and is itself trivially
correct; a `Mock` re-declares behavior in every test and asserts on incidental calls
(`CORE-TESTING`, `PLAT-PY-TESTING`). Use `unittest.mock` only for boundaries you do not
own and cannot fake cheaply.
