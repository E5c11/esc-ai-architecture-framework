---
id: ARCH-PY-ENTRYPOINT
type: rules
layer: architectures
platform: [python]
architecture: python-app
requires: [ARCH-PY, CORE-COUPLING]
related: [ARCH-PY-USECASE, ARCH-PY-ERROR, ARCH-PY-POLICY, CORE-API-STABILITY, PLAT-PY-CLI, PLAT-PY-MCP, PLAT-PY-HTTP]
tags: [entrypoint, cli, mcp, http, boundary, thin, rendering, delivery-surface]
status: active
---
# Entrypoint Layer

## Responsibility

An entrypoint is a delivery surface: the place where the outside world (a terminal,
an MCP client, an HTTP caller, a scheduler) meets the program. It translates raw
input into a use-case call and a use-case result into that surface's output. That is
its entire purpose.

An entrypoint function may:

- Parse and validate the *shape* of raw input (argv, JSON params, request body)
- Call exactly one use case
- Render the result, or translate a domain error into the surface's error form
- Ask the human a question *when the surface is interactive*, and pass the answer to
  the use case as a value

## Rules

```rule
id: PYEP-LOGIC-01
statement: Entrypoint functions MUST contain no business logic — no domain decisions, branching on domain state, or calls to more than one use case per operation.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYEP-LOGIC-01 — Entrypoint functions MUST contain no business logic — no domain decisions, branching on domain state, or calls to more than one use case per operation.
```

> Violation: a CLI handler that loads a task, decides whether it is ready, and then
> chooses which of two functions to call.
> Fix: move the decision into one use case; the handler calls that use case.

```rule
id: PYEP-USECASE-01
statement: Every operation reachable from more than one delivery surface MUST be implemented as a use case that each surface calls; one surface MUST NOT call into another.
type: hard
scope: structure
enforced_by: [ci, reviewer]
violation_message: Violates PYEP-USECASE-01 — Every operation reachable from more than one delivery surface MUST be implemented as a use case that each surface calls; one surface MUST NOT call into another.
```

```rule
id: PYEP-RENDER-01
statement: Rendering (formatting values into text, tables, JSON, or a protocol envelope) MUST live in pure functions in the entrypoint package that take values and return values; only the outermost handler may write to a stream.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYEP-RENDER-01 — Rendering (formatting values into text, tables, JSON, or a protocol envelope) MUST live in pure functions in the entrypoint package that take values and return values; only the outermost handler may write to a stream.
```

Pure renderers are trivially unit-tested and reusable between the human and `--json`
forms of the same command. A function that both computes and `print()`s can be
tested only by capturing stdout.

```rule
id: PYEP-IO-01
statement: Code below the entrypoint layer MUST NOT call `print()`, `input()`, read `sys.argv`, or exit the process; only entrypoints may.
type: hard
scope: behavior
enforced_by: [ci, reviewer]
violation_message: Violates PYEP-IO-01 — Code below the entrypoint layer MUST NOT call `print()`, `input()`, read `sys.argv`, or exit the process; only entrypoints may.
```

`ruff`'s `T201` (print) and `SLF`/`PLR` selections can enforce this per package.

```rule
id: PYEP-INTERACT-01
statement: A question to the human MUST be asked by an entrypoint (or an injected prompter port), and the answer MUST reach the use case as an ordinary argument.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYEP-INTERACT-01 — A question to the human MUST be asked by an entrypoint (or an injected prompter port), and the answer MUST reach the use case as an ordinary argument.
```

A use case that calls `input()` cannot be driven by an MCP client or a test. Where an
interactive flow needs to ask mid-operation, the use case depends on a `Prompter`
Protocol and the composition root supplies a terminal implementation, an MCP
elicitation implementation, or a scripted fake (`ARCH-PY-POLICY`).

```rule
id: PYEP-EXIT-01
statement: Entrypoints MUST map every outcome to exactly one exit status or protocol error code through a single translation function per surface.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PYEP-EXIT-01 — Entrypoints MUST map every outcome to exactly one exit status or protocol error code through a single translation function per surface.
```

See `ARCH-PY-ERROR` for the mapping tiers. Scattered `return 1` / `sys.exit(2)`
literals in handlers make the contract with scripts and clients undiscoverable.

```rule
id: PYEP-DISPATCH-01
statement: Command and tool registration MUST be data-driven (a table or decorator registry) so adding an operation adds one entry, not a branch in a growing if-chain.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYEP-DISPATCH-01 — Command and tool registration MUST be data-driven (a table or decorator registry) so adding an operation adds one entry, not a branch in a growing if-chain.
```

## Intent-shaped surfaces

A surface may present *intent verbs* (`fix`, `plan`, `investigate`) rather than
implementation nouns (`repository`, `task`). The verb selects a use case (or a fixed
sequence of stages the application layer defines); it never decides what the
procedure does. The mapping from verb to procedure is data in the application or
domain layer, and the surface reads it — including to render help that lists what
the verb will enforce.

```rule
id: PYEP-INTENT-01
statement: The set of stages an intent verb runs MUST be defined in the application or domain layer and read by the entrypoint; the entrypoint MUST NOT hard-code a per-verb pipeline.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYEP-INTENT-01 — The set of stages an intent verb runs MUST be defined in the application or domain layer and read by the entrypoint; the entrypoint MUST NOT hard-code a per-verb pipeline.
```

```rule
id: PYEP-HONEST-01
statement: Help, docs, and output MUST NOT imply that a stage or guarantee is enforced when no implementation backs it; unimplemented stages MUST be labeled as such.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYEP-HONEST-01 — Help, docs, and output MUST NOT imply that a stage or guarantee is enforced when no implementation backs it; unimplemented stages MUST be labeled as such.
```

A verb that routes to a procedure with no real gates behind it is cosmetic. Showing
the gate list in help is worthwhile only if every listed gate is real or clearly
marked pending.

## Surface-specific guidance

- CLI: `PLAT-PY-CLI` — parser choice, subcommand groups, stdout/stderr split,
  deprecated aliases
- MCP server: `PLAT-PY-MCP` — one tool per use case, schemas from types, structured
  errors
- HTTP: `PLAT-PY-HTTP` — routers, request/response models, error envelope

## Deprecating an entrypoint

Renaming a command or tool is a public contract change (`CORE-API-STABILITY`). Keep the
old spelling as an alias that delegates to the new one, emit a deprecation notice on
the *diagnostic* stream (stderr / protocol log), never on the data stream, and remove
it only on a documented major version.

```rule
id: PYEP-DEPREC-01
statement: A renamed or removed command, tool, or route MUST keep a delegating alias for at least one minor version, with the deprecation notice written to stderr or the protocol log, never to the data stream.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYEP-DEPREC-01 — A renamed or removed command, tool, or route MUST keep a delegating alias for at least one minor version, with the deprecation notice written to stderr or the protocol log, never to the data stream.
```
