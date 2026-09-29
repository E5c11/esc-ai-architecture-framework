---
id: PLAT-PY
type: platform
layer: platforms
platform: [python]
architecture: python-app
requires: [ARCH-PY, CORE-NAMING]
related: [PLAT-PY-TYPING, PLAT-PY-DI, PLAT-PY-IMPORT-LINTER, PLAT-PY-TESTING, PLAT-PY-CLI, PLAT-PY-MCP, PLAT-PY-HTTP, PLAT-PY-PERSISTENCE, PLAT-PY-SUBPROCESS, PLAT-PY-PACKAGING, ARCH-PY-OBSERVABILITY]
tags: [python, pyproject, uv, ruff, venv, tooling, baseline]
status: active
---
# Python Platform Guide

Extends: `ARCH-PY`

Python 3.12+ implementation guides for the `python-app` architecture. Each document in
this platform extends an architecture rule with the concrete tools and idioms that
express it in Python; none redefines an architecture rule.

## Baseline

| Concern | Choice | Document |
|---|---|---|
| Language level | Python ≥ 3.12 | this document |
| Project metadata, build, entry points | `pyproject.toml` (PEP 621), `src/` layout | `PLAT-PY-PACKAGING` |
| Environments and dependencies | A virtual environment per project; a lockfile-capable tool (`uv` or `pip-tools`) | this document |
| Typing | Full annotations; `mypy --strict` or `pyright` strict | `PLAT-PY-TYPING` |
| Lint and format | `ruff` (lint + format) | this document |
| Layer enforcement | `import-linter` | `PLAT-PY-IMPORT-LINTER` |
| Tests | `pytest`, `coverage` | `PLAT-PY-TESTING` |
| CLI | `argparse` (stdlib) by default | `PLAT-PY-CLI` |
| MCP server | The official MCP Python SDK | `PLAT-PY-MCP` |
| HTTP API | FastAPI (when an HTTP surface is needed) | `PLAT-PY-HTTP` |
| Persistence | `sqlite3` (stdlib) by default | `PLAT-PY-PERSISTENCE` |
| Processes | `subprocess`, argument lists only | `PLAT-PY-SUBPROCESS` |

## Rules

```rule
id: PYENV-VERSION-01
statement: A project MUST declare its supported Python range in `requires-python` and MUST run CI on the lowest and highest supported versions.
type: hard
scope: structure
enforced_by: [ci, reviewer]
violation_message: Violates PYENV-VERSION-01 — A project MUST declare its supported Python range in `requires-python` and MUST run CI on the lowest and highest supported versions.
```

```rule
id: PYENV-LOCK-01
statement: Application projects MUST commit a lockfile or fully pinned requirements for reproducible installs; library projects MUST declare compatible version ranges and MUST NOT pin exact versions of their dependencies.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYENV-LOCK-01 — Application projects MUST commit a lockfile or fully pinned requirements for reproducible installs; library projects MUST declare compatible version ranges and MUST NOT pin exact versions of their dependencies.
```

```rule
id: PYENV-DEPS-01
statement: Runtime dependencies MUST be declared in `pyproject.toml` (`[project.dependencies]`); development-only tools MUST be declared in a separate group (`[project.optional-dependencies]` or a dependency group) and MUST NOT be imported by package code.
type: hard
scope: structure
enforced_by: [ci, reviewer]
violation_message: Violates PYENV-DEPS-01 — Runtime dependencies MUST be declared in `pyproject.toml` (`[project.dependencies]`); development-only tools MUST be declared in a separate group (`[project.optional-dependencies]` or a dependency group) and MUST NOT be imported by package code.
```

```rule
id: PYENV-LINT-01
statement: A project MUST configure `ruff` in `pyproject.toml` with the rule families the architecture relies on (see below) and MUST run it in CI as a failing check.
type: hard
scope: structure
enforced_by: [ci, reviewer]
violation_message: Violates PYENV-LINT-01 — A project MUST configure `ruff` in `pyproject.toml` with the rule families the architecture relies on (see below) and MUST run it in CI as a failing check.
```

### Ruff rule families the architecture relies on

Adopt them incrementally: run the whole set once, enable the families the code already satisfies,
and list each family that does not yet pass with its count and the refactor that unblocks it
(complexity rules, import sorting on a large legacy tree). A config that fails on day one is
switched off; one that passes today and ratchets is kept.

| Rules | Enforces |
|---|---|
| `T20` (`T201`) | No `print` outside entrypoints (`PYEP-IO-01`, `PYOBS-LOG-02`) |
| `E722`, `BLE`, `S110`, `SIM105` | No bare/blind/swallowed exceptions (`PYERR-SWALLOW-01`) |
| `S101` | No `assert` for validation or gates (`PYERR-ASSERT-01`) |
| `S602`, `S604`, `S605` | No shell invocation (`PYGW-PROC-01`) |
| `S603`, `S607` | Review every subprocess call: argument list from trusted input, full executable path |
| `S608` | No string-built SQL (`PYDS-SQL-01`) |
| `DTZ` | No naive or ambient datetimes (`PYDOM-CLOCK-01`) |
| `TID251` | Banned imports per layer — e.g. `sqlite3`/`subprocess` banned globally, allowed by `per-file-ignores` only in `infrastructure/` (`ARCH-PY-DEP-01`) |
| `C901`, `PLR0912`, `PLR0915` | Function size and complexity (`PYMOD-FUNC-01`) |
| `UP`, `B`, `SIM`, `I` | Modern syntax, bugbear defaults, simplifications, import order |

A minimal enforcing configuration is in `PLAT-PY-IMPORT-LINTER`.

## Code style essentials

- Formatting is `ruff format`'s; do not hand-format or debate it.
- Names: `snake_case` functions/modules, `PascalCase` classes, `UPPER_SNAKE` constants;
  a leading underscore means private (`CORE-NAMING`).
- Prefer `pathlib.Path` over `os.path` for path handling; prefer `enum`/`Literal` over
  magic strings (`PYDOM-VOCAB-01`).
- Prefer comprehension and generator expressions for simple transformations; prefer a
  named function once the expression needs a comment.
- Docstrings state *why and contract* (what the caller may rely on, what is raised),
  not a restatement of the signature.
- Mutable default arguments are never used (`def f(x: list = [])` is a bug).
- `from x import *` is never used.
