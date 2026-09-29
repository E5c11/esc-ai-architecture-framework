---
id: ARCH-PY
type: overview
layer: architectures
platform: [python]
architecture: python-app
requires: [CORE-DI, CORE-ERROR, CORE-NAMING, CORE-COUPLING, CORE-SSOT, CORE-TESTING, PAT-DATA-ACCESS, PAT-OUTCOME]
related: [ARCH-PY-ENTRYPOINT, ARCH-PY-USECASE, ARCH-PY-DOMAIN, ARCH-PY-DATASOURCE, ARCH-PY-GATEWAY, ARCH-PY-COMPOSITION, ARCH-PY-ERROR, ARCH-PY-POLICY, ARCH-PY-OBSERVABILITY, ARCH-PY-CONCURRENCY, ARCH-PY-MODULES, PLAT-PY, PLAT-PY-IMPORT-LINTER]
tags: [python, architecture, layers, practical-clean, cli, mcp, service, control-plane]
status: active
---
# Python-App Architecture

## What it is

Python-App is Practical Clean Architecture expressed for Python. It applies Clean
Architecture's one load-bearing idea — dependencies point inward toward the
business rules, never outward toward I/O and delivery mechanisms — without the full
abstraction overhead of strict Clean, and it uses Python's own tools for the parts
other languages need frameworks for (`typing.Protocol` for inversion, plain
constructor injection for wiring, `import-linter` for enforcement).

It targets any Python program that does real work behind one or more **delivery
surfaces**: a command-line tool, an MCP server, an HTTP API, a background worker, or
several of these over the same logic. The defining property is that *the logic is
written once and every surface is a thin front door onto it*.

## Why "practical"

- A layer exists because it has a distinct reason to change, not to satisfy a
  diagram. There is no Repository layer unless a component coordinates two or more
  data sources (`ARCH-PY-DATASOURCE`).
- An interface exists where a real second implementation exists or is needed for
  tests. A pure function needs no interface.
- There is no dependency-injection container. Python's constructor arguments and a
  single composition root are enough (`ARCH-PY-COMPOSITION`).
- Python is dynamically typed at runtime, so the boundaries that Clean Architecture
  draws in a compiler are drawn here in *types plus an import-graph check* — both are
  mandatory, because convention alone does not survive a growing codebase.

## Layer structure

```
Entrypoints        CLI / MCP tool / HTTP route / worker loop — parse input, call ONE
                   use case, render the result. No logic.
    ↓
Application        Use cases — one operation each. Coordinates domain + ports.
                   Owns the unit of work. Declares the ports (Protocols) it needs.
    ↓
Domain             Entities, value objects, policies, rule tables. Pure: no I/O,
                   no clock, no randomness, no framework imports.
    ↑
Infrastructure     DataSources and Gateways — implement the application's ports
                   against SQLite, git, subprocesses, providers, the network.
```

`Infrastructure` and `Entrypoints` are both *outer* layers and are independent of each
other. Both depend inward; nothing depends on either of them. A single **composition
root** (`ARCH-PY-COMPOSITION`) is the only place that knows concrete classes.

### Layer contracts

| Layer | Receives | Returns | Must NOT |
|---|---|---|---|
| Entrypoint | Raw input (argv, JSON-RPC params, HTTP request) | Rendered output / exit status | Contain logic; print from below itself; construct infrastructure |
| Application (use case) | Domain values and primitives | Domain values, outcome objects | Print, prompt, read `sys.argv`, know a delivery surface exists |
| Domain | Domain values | Domain values | Perform I/O, read the clock, import a framework |
| DataSource | Domain parameters | Domain values | Return rows, cursors, or ORM objects; own business rules |
| Gateway | Domain parameters | Domain values or outcome objects | Leak a provider's types; decide policy |

## Dependency direction

```rule
id: ARCH-PY-DEP-01
statement: Domain code MUST NOT import from application, infrastructure, or entrypoints, and MUST NOT import any I/O or framework library.
type: hard
scope: structure
enforced_by: [ci, reviewer]
violation_message: Violates ARCH-PY-DEP-01 — Domain code MUST NOT import from application, infrastructure, or entrypoints, and MUST NOT import any I/O or framework library.
```

I/O libraries include `sqlite3`, `subprocess`, `socket`, `http`, `urllib`, `requests`,
`httpx`, `pathlib` *read/write calls*, and `open()`. Pure use of `pathlib.PurePath`
and of `datetime` types for values is fine; reading the current time is not
(`ARCH-PY-DOMAIN`).

```rule
id: ARCH-PY-DEP-02
statement: Application code MUST NOT import from infrastructure or entrypoints.
type: hard
scope: structure
enforced_by: [ci, reviewer]
violation_message: Violates ARCH-PY-DEP-02 — Application code MUST NOT import from infrastructure or entrypoints.
```

```rule
id: ARCH-PY-DEP-03
statement: Infrastructure and entrypoints MUST NOT import from each other; both MAY import application and domain.
type: hard
scope: structure
enforced_by: [ci, reviewer]
violation_message: Violates ARCH-PY-DEP-03 — Infrastructure and entrypoints MUST NOT import from each other; both MAY import application and domain.
```

```rule
id: ARCH-PY-DEP-04
statement: The layer contract MUST be declared as an `import-linter` contract in the project's configuration and MUST run in CI.
type: hard
scope: structure
enforced_by: [ci, planner]
violation_message: Violates ARCH-PY-DEP-04 — The layer contract MUST be declared as an `import-linter` contract in the project's configuration and MUST run in CI.
```

A dependency rule that only lives in a document is a suggestion. See
`PLAT-PY-IMPORT-LINTER` for the contract to copy.

## Package structure

```
src/{package}/
    domain/            entities, value objects, policies, rule tables
    application/       use cases; ports.py (or ports/) declares the Protocols
    infrastructure/    datasources/ and gateways/ — one module per provider
    entrypoints/       cli/, mcp/, http/, worker/ — one subpackage per surface
    composition.py     the composition root
    __main__.py        wires composition → entrypoint; the only module allowed to
                       import both
tests/
    domain/  application/  infrastructure/  entrypoints/
```

```rule
id: ARCH-PY-STRUCT-01
statement: Source MUST be laid out as `domain/`, `application/`, `infrastructure/`, and `entrypoints/` packages under one top-level package, with tests mirroring that layout.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-PY-STRUCT-01 — Source MUST be laid out as `domain/`, `application/`, `infrastructure/`, and `entrypoints/` packages under one top-level package, with tests mirroring that layout.
```

```rule
id: ARCH-PY-STRUCT-02
statement: Each delivery surface MUST be its own subpackage of `entrypoints/`; surfaces MUST NOT import each other.
type: hard
scope: structure
enforced_by: [ci, reviewer]
violation_message: Violates ARCH-PY-STRUCT-02 — Each delivery surface MUST be its own subpackage of `entrypoints/`; surfaces MUST NOT import each other.
```

If the CLI and the MCP server both need the same behavior, the behavior is a use case,
not a helper the MCP server imports from the CLI (`ARCH-PY-ENTRYPOINT`).

## One logic, many surfaces

The reason this architecture exists as a distinct document, rather than reusing
`pragmatic-clean` or `backend-service`, is the delivery-surface problem. A Python
program routinely starts as a CLI and later needs an MCP server or an HTTP API. If
logic lives in the CLI module — printing, prompting and doing the work in the same
functions — every new surface must either import the CLI (dragging terminal I/O into
a server) or copy it. Both are how a single file grows to thousands of lines.

The rule is structural: **a use case never knows how it was invoked.** It takes values
and returns values. Rendering, prompting, exit codes, JSON-RPC envelopes and HTTP
status codes belong to entrypoints alone.

## Execution order for a new capability

Implement inward-to-outward, so nothing is written against a layer that does not
exist yet:

1. Domain — the values and rules (pure, unit-testable immediately)
2. Ports — the Protocols the use case will need
3. Use case — against fakes of those ports
4. DataSource / Gateway — the real implementations, integration-tested
5. Composition — wire it
6. Entrypoint(s) — one per surface, thin
7. Tests at each layer as it is written (`ORCH-PY-USECASE`)

## Cross-cutting concerns

| Concern | Document |
|---|---|
| Errors and failure outcomes | `ARCH-PY-ERROR` |
| Behavior that varies by user preference or role | `ARCH-PY-POLICY` |
| Logging, telemetry, audit trail | `ARCH-PY-OBSERVABILITY` |
| Threads, async, subprocess lifetime | `ARCH-PY-CONCURRENCY` |
| Module size, cohesion, splitting | `ARCH-PY-MODULES` |

## What this architecture does NOT include

- A web-UI architecture — a Python-served front end follows `web-app`/`web-spa` for
  its client side; only the server side follows this document.
- Event sourcing or CQRS.
- Plugin systems with dynamic discovery — extension points are ports wired at the
  composition root.
- Data-science or notebook code — exploratory scripts are outside this architecture's
  scope (see the Gap Protocol if a production pipeline needs its own).
