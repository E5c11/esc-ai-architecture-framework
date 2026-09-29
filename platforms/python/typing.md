---
id: PLAT-PY-TYPING
type: guide
layer: platforms
platform: [python]
architecture: python-app
requires: [ARCH-PY, PLAT-PY]
related: [ARCH-PY-DOMAIN, ARCH-PY-USECASE, ARCH-PY-ERROR, PLAT-PY-DI]
tags: [typing, mypy, pyright, protocol, dataclass, typeddict, pydantic, literal, enum]
---
# Typing and Data Modeling

Extends: `ARCH-PY`

In Python, static types are the compiler the architecture would otherwise borrow from
its host language. The layer boundaries in `ARCH-PY` are only as strong as the types
that cross them.

## Rules

```rule
id: PYTYPE-STRICT-01
statement: All code in `src/` MUST be fully annotated and MUST pass a strict type check (`mypy --strict` or `pyright` in strict mode) in CI; a `# type: ignore` MUST name the error code and carry a reason.
type: hard
scope: structure
enforced_by: [ci, reviewer]
violation_message: Violates PYTYPE-STRICT-01 — All code in `src/` MUST be fully annotated and MUST pass a strict type check (`mypy --strict` or `pyright` in strict mode) in CI; a `# type: ignore` MUST name the error code and carry a reason.
```

```rule
id: PYTYPE-ANY-01
statement: `Any` MUST NOT appear in a public signature of the domain or application layers; where a dynamic value genuinely enters (parsed JSON/YAML), it MUST be narrowed to a typed value at the boundary that received it.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates PYTYPE-ANY-01 — `Any` MUST NOT appear in a public signature of the domain or application layers; where a dynamic value genuinely enters (parsed JSON/YAML), it MUST be narrowed to a typed value at the boundary that received it.
```

An untyped `dict[str, Any]` passed inward is a boundary that was never drawn: every
later reader must guess its shape.

## Choosing a representation

| Need | Use | Where |
|---|---|---|
| An immutable domain value | `@dataclass(frozen=True, slots=True)` | domain |
| A closed set of choices | `enum.Enum` (or `StrEnum` when the string form is the contract) / `typing.Literal` | domain |
| A fixed shape of untrusted external data | `TypedDict` for typing only, or a validating model (pydantic) for parsing | infrastructure / entrypoints — the boundary |
| A structural interface (a port) | `typing.Protocol` | application |
| A value with a few positional fields | `typing.NamedTuple` | domain |
| A function-shaped collaborator | `Callable[[A], B]` | anywhere, when a Protocol would be ceremony |

```rule
id: PYTYPE-BOUNDARY-01
statement: Untrusted external data (files, JSON-RPC params, HTTP bodies, provider responses) MUST be parsed and validated into typed domain or request values at the boundary that receives it, and only those typed values MUST cross inward.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYTYPE-BOUNDARY-01 — Untrusted external data (files, JSON-RPC params, HTTP bodies, provider responses) MUST be parsed and validated into typed domain or request values at the boundary that receives it, and only those typed values MUST cross inward.
```

```rule
id: PYTYPE-PYDANTIC-01
statement: A validation/serialization library (pydantic or equivalent) MAY be used in infrastructure and entrypoints and MUST NOT be imported by the domain layer; domain values stay plain frozen dataclasses.
type: hard
scope: structure
enforced_by: [ci, reviewer]
violation_message: Violates PYTYPE-PYDANTIC-01 — A validation/serialization library (pydantic or equivalent) MAY be used in infrastructure and entrypoints and MUST NOT be imported by the domain layer; domain values stay plain frozen dataclasses.
```

The domain then has no framework dependency to upgrade, and its values are cheap to
construct in tests. Convert at the boundary: `Request.model_validate(...)` →
`to_domain()`.

```rule
id: PYTYPE-PORT-01
statement: A port MUST be a `typing.Protocol`; an `abc.ABC` base class MUST NOT be used solely to declare an interface a collaborator implements.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates PYTYPE-PORT-01 — A port MUST be a `typing.Protocol`; an `abc.ABC` base class MUST NOT be used solely to declare an interface a collaborator implements.
```

`Protocol` is structural: an infrastructure class satisfies a port without importing the
application package to inherit from it, which is exactly the dependency direction the
architecture wants. Use `@runtime_checkable` only where an `isinstance` check is
genuinely needed.

```rule
id: PYTYPE-OPTIONAL-01
statement: A function that may not produce a value MUST declare `X | None` and callers MUST handle the `None`; `None` MUST NOT be used to signal failure where an outcome value or `AppError` applies.
type: hard
scope: return-type
enforced_by: [ci, reviewer]
violation_message: Violates PYTYPE-OPTIONAL-01 — A function that may not produce a value MUST declare `X | None` and callers MUST handle the `None`; `None` MUST NOT be used to signal failure where an outcome value or `AppError` applies.
```

## Idioms

- Use `X | None` and `list[int]` (built-in generics), not `Optional[X]` / `List[int]`.
- Use `typing.Self`, `typing.override`, and `type` aliases where they clarify.
- Use `typing.assert_never(x)` in the `else` branch of a match/if over an enum so
  adding a member is a type error at every unhandled site.
- Use `match` for dispatch over a closed vocabulary; it reads better than an if-chain
  and pairs with `assert_never`.
- Use `dataclasses.replace(value, field=...)` for "modified copies" of a frozen value.
- Use `functools.cache` only on pure functions of hashable arguments; it is a hidden
  global otherwise (`PYCOMP-GLOBAL-01`).
