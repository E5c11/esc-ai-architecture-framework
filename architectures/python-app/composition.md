---
id: ARCH-PY-COMPOSITION
type: rules
layer: architectures
platform: [python]
architecture: python-app
requires: [ARCH-PY, CORE-DI]
related: [ARCH-PY-USECASE, ARCH-PY-DATASOURCE, ARCH-PY-GATEWAY, ARCH-PY-ENTRYPOINT, PLAT-PY-DI]
tags: [composition-root, di, wiring, configuration, settings, entry-point]
status: active
---
# Composition Root

## Responsibility

The composition root is the one place that knows which concrete classes exist. It
reads configuration, constructs DataSources and Gateways, injects them into use cases,
and hands the assembled use cases to the entrypoint. Everything else in the program
receives its collaborators; nothing else goes looking for them.

Python needs no DI container for this. A function that builds objects and passes them
along is clearer, debuggable with a plain stack trace, and has no runtime magic
(`PLAT-PY-DI`).

## Shape

```python
# composition.py
def build_app(settings: Settings) -> App:
    store = SqliteStore(settings.db_path)
    provider = provider_for(settings.provider)        # a Gateway, chosen by config
    return App(
        draft_plan=DraftPlan(routing=FileRoutingIndex(), drafts=store),
        run_task=RunTask(store=store, runner=provider, verifier=SubprocessVerifier()),
    )
```

```python
# __main__.py
def main(argv: list[str] | None = None) -> int:
    settings = Settings.from_environment()      # the only place ambient state is read
    return cli.run(build_app(settings), argv)
```

## Rules

```rule
id: PYCOMP-ROOT-01
statement: Concrete DataSources, Gateways, and use cases MUST be constructed only in the composition root (and in tests); no other module MAY instantiate an infrastructure class.
type: hard
scope: di
enforced_by: [ci, reviewer]
violation_message: Violates PYCOMP-ROOT-01 — Concrete DataSources, Gateways, and use cases MUST be constructed only in the composition root (and in tests); no other module MAY instantiate an infrastructure class.
```

```rule
id: PYCOMP-ROOT-02
statement: Only `__main__` (and the composition module it calls) MAY import both entrypoints and infrastructure; entrypoint modules MUST receive use cases as parameters and MUST NOT import the composition module.
type: hard
scope: structure
enforced_by: [ci, reviewer]
violation_message: Violates PYCOMP-ROOT-02 — Only `__main__` (and the composition module it calls) MAY import both entrypoints and infrastructure; entrypoint modules MUST receive use cases as parameters and MUST NOT import the composition module.
```

This is what keeps an entrypoint testable: a test passes it an `App` built from fakes.

```rule
id: PYCOMP-CONFIG-01
statement: Configuration (environment variables, config files, CLI-level options) MUST be read once, in one `Settings` loader called from the composition root, and passed onward as a frozen value; no other module MAY read `os.environ` or a config file.
type: hard
scope: di
enforced_by: [ci, reviewer]
violation_message: Violates PYCOMP-CONFIG-01 — Configuration (environment variables, config files, CLI-level options) MUST be read once, in one `Settings` loader called from the composition root, and passed onward as a frozen value; no other module MAY read `os.environ` or a config file.
```

```rule
id: PYCOMP-GLOBAL-01
statement: The program MUST NOT rely on module-level mutable singletons, import-time side effects, or global registries populated by import order; importing a module MUST NOT open a connection, read a file, or start a thread.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYCOMP-GLOBAL-01 — The program MUST NOT rely on module-level mutable singletons, import-time side effects, or global registries populated by import order; importing a module MUST NOT open a connection, read a file, or start a thread.
```

Import-time side effects make tests order-dependent and make `--help` slow or
dangerous. Read-only module constants (rule tables, compiled regexes) are fine.

```rule
id: PYCOMP-CHOICE-01
statement: Choosing between interchangeable implementations (which provider, which store) MUST be done in the composition root from configuration, and MUST fail with a clear configuration error if the choice is unknown, unless a generic fallback implementation is declared and documented as the default.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates PYCOMP-CHOICE-01 — Choosing between interchangeable implementations (which provider, which store) MUST be done in the composition root from configuration, and MUST fail with a clear configuration error if the choice is unknown, unless a generic fallback implementation is declared and documented as the default.
```

```rule
id: PYCOMP-LAZY-01
statement: Expensive or optional dependencies (provider SDKs, heavy libraries) SHOULD be imported inside the factory that needs them, so commands that never use them start fast and do not fail when they are absent.
type: soft
scope: performance
enforced_by: [reviewer]
violation_message: Violates PYCOMP-LAZY-01 — Expensive or optional dependencies (provider SDKs, heavy libraries) SHOULD be imported inside the factory that needs them, so commands that never use them start fast and do not fail when they are absent.
```

## When the app can only be built after the arguments are parsed

A command-line program often needs its own options (`--db`, `--registry`) to decide how to build the app, so
`build_app(settings)` cannot run before parsing. Do not make the entrypoint import the composition root to
get around that. Give the entrypoint an **app factory** instead: `run(argv, app_factory)` parses, calls
`app_factory(options)`, dispatches. The console-script target (the program's `__main__`) is the only code that
knows both sides and passes the real factory:

```python
# entrypoints/cli/main.py -- imports no infrastructure and no composition
def run(argv, app_factory): ...

# escape_ai_cli.py (console-script target) -- allowed to import composition
def main(argv=None) -> int:
    return run(argv, build_app)
```

## Operations that must build infrastructure per call

Some operations create a fresh collaborator each time they run -- a scheduler for one task, a connection, a
disposable worktree -- so it cannot be built once at startup. The operation still must not construct it: give
the `App` a **factory** for it (a `Callable` typed by a port) and have the operation take that factory as a
parameter.

```rule
id: PYCOMP-FACTORY-01
statement: An operation that needs a fresh piece of infrastructure per call MUST receive a factory for it (declared as a port, supplied by the composition root); it MUST NOT import and construct the concrete class.
type: hard
scope: di
enforced_by: [ci, reviewer]
violation_message: Violates PYCOMP-FACTORY-01 — An operation that needs a fresh piece of infrastructure per call MUST receive a factory for it (declared as a port, supplied by the composition root); it MUST NOT import and construct the concrete class.
```

The `App` may also expose the operation as a bound method (`app.execute_task(...)`) that forwards the composed
factories, so entrypoints do not thread them through by hand. Keep `App` a frozen dataclass declared in the
application layer, so entrypoints can type against it without importing the composition root.

## Multiple surfaces, one root

A CLI, an MCP server, and an HTTP API all call `build_app(settings)` and receive the
same `App`. Only the entrypoint that follows differs. Adding a surface adds an
entrypoint package and a `main`; it never adds a second wiring of the use cases.
