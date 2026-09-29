---
id: PLAT-PY-CLI
type: guide
layer: platforms
platform: [python]
architecture: python-app
requires: [ARCH-PY, ARCH-PY-ENTRYPOINT, PLAT-PY]
related: [ARCH-PY-ERROR, ARCH-PY-POLICY, PLAT-PY-PACKAGING, PLAT-PY-TESTING, CORE-API-STABILITY]
tags: [cli, argparse, click, typer, subcommands, stdout, stderr, exit-codes, help, intent-verbs]
---
# Command-Line Surface

Extends: `ARCH-PY-ENTRYPOINT`

## Parser choice

Default to **`argparse`** (standard library): no dependency, ample for subcommand
trees, and its behavior is stable across Python versions. Move to `click` or `typer`
only when the command tree is large enough that declarative decorators clearly pay for
the added dependency. Whichever is used, it lives *only* in the CLI entrypoint
package; use cases never see it.

```rule
id: PYCLI-PARSER-01
statement: Argument parsing MUST be confined to `entrypoints/cli`; the parsed result MUST be converted to plain typed request values before any use case is called.
type: hard
scope: structure
enforced_by: [ci, reviewer]
violation_message: Violates PYCLI-PARSER-01 — Argument parsing MUST be confined to `entrypoints/cli`; the parsed result MUST be converted to plain typed request values before any use case is called.
```

Passing an `argparse.Namespace` inward makes every use case depend on the parser and
untestable without it.

## Structure of the CLI package

```
entrypoints/cli/
    parser.py        builds the parser from the command table (no logic)
    commands.py      one function per command: parse → use case → render
    render.py        pure renderers (text, table, --json)
    main.py          run(app, argv) -> int   (translation + top-level handler)
```

## Rules

```rule
id: PYCLI-STREAMS-01
statement: Command results (the data a script would consume) MUST be written to stdout; diagnostics, progress, prompts, deprecation notices, and errors MUST be written to stderr.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYCLI-STREAMS-01 — Command results (the data a script would consume) MUST be written to stdout; diagnostics, progress, prompts, deprecation notices, and errors MUST be written to stderr.
```

```rule
id: PYCLI-JSON-01
statement: Every command producing structured data MUST offer `--json` output rendered from the same value as the human form, with a documented, versioned shape.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYCLI-JSON-01 — Every command producing structured data MUST offer `--json` output rendered from the same value as the human form, with a documented, versioned shape.
```

```rule
id: PYCLI-NOTTY-01
statement: A command MUST behave deterministically when stdin is not a terminal: it MUST NOT block on a prompt, and where it needs an answer it MUST accept it as an argument or fail with a message naming the missing argument.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYCLI-NOTTY-01 — A command MUST behave deterministically when stdin is not a terminal: it MUST NOT block on a prompt, and where it needs an answer it MUST accept it as an argument or fail with a message naming the missing argument.
```

Interactive convenience is an addition (`sys.stdin.isatty()`), never the only path;
a CI job or an AI operator must be able to run every command with no human present.

```rule
id: PYCLI-DESTRUCTIVE-01
statement: A command that writes, executes, or is hard to undo MUST preview by default and require an explicit flag (`--yes`) to act; the preview MUST show what would change.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYCLI-DESTRUCTIVE-01 — A command that writes, executes, or is hard to undo MUST preview by default and require an explicit flag (`--yes`) to act; the preview MUST show what would change.
```

```rule
id: PYCLI-HELP-01
statement: Every command MUST have help text stating what it does and, for a procedure-backed command, the stages it enforces, generated from the procedure definition rather than hand-copied.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYCLI-HELP-01 — Every command MUST have help text stating what it does and, for a procedure-backed command, the stages it enforces, generated from the procedure definition rather than hand-copied.
```

Hand-copied help drifts from behavior. `argparse`'s `epilog` with
`formatter_class=argparse.RawDescriptionHelpFormatter` keeps a rendered stage list
readable.

```rule
id: PYCLI-EXIT-01
statement: `main` MUST return an integer status from the project's exit-status table and the module's `__main__` guard MUST be `raise SystemExit(main())`; no other function MUST call `sys.exit`.
type: hard
scope: behavior
enforced_by: [ci, reviewer]
violation_message: Violates PYCLI-EXIT-01 — `main` MUST return an integer status from the project's exit-status table and the module's `__main__` guard MUST be `raise SystemExit(main())`; no other function MUST call `sys.exit`.
```

## Grouped commands and intent verbs

A CLI can have both **intent verbs** (`fix`, `plan`, `investigate` — the front door) and
**resource groups** (`repository`, `initiative`, `task` — the underlying machinery for
scripting). Rules of thumb:

- Verbs take the objective and the scope as arguments and *drive* the resource
  operations; they add no logic of their own (`PYEP-INTENT-01`).
- A verb name and a group name MUST NOT collide; if an early group name is wanted by a
  verb, rename the group and keep the old spelling as a deprecated alias
  (`PYEP-DEPREC-01`). A small `argv` rewrite before parsing is enough and keeps the
  parser simple.
- Register commands from a table (`{name: (summary, handler)}`) so help, dispatch, and
  tests iterate one source (`PYEP-DISPATCH-01`).
- A verb whose pipeline is not yet available is *registered*, exits with a distinct
  non-zero status, and prints what the procedure will be (`PYEP-HONEST-01`).

## Interactive flows

An interactive menu is a separate entrypoint over the same use cases. It asks through a
`Prompter` (`PYEP-INTERACT-01`), loops back after an action instead of exiting, and
never contains a decision the non-interactive command would not also make.
