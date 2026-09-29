---
id: PLAT-PY-PACKAGING
type: guide
layer: platforms
platform: [python]
architecture: python-app
requires: [ARCH-PY, PLAT-PY, CORE-API-STABILITY]
related: [ARCH-PY-MODULES, PLAT-PY-CLI, PLAT-PY-TESTING]
tags: [packaging, pyproject, pep-621, entry-points, console-scripts, semver, pypi, src-layout, library]
---
# Packaging and Publishing

Extends: `ARCH-PY`

This document covers both an **application** (an installable command) and a **library**
(a package other repositories depend on). The difference matters: an application owns its
environment and pins for reproducibility; a library serves consumers you do not control
and must keep a stable public surface (`CORE-API-STABILITY`).

## Rules

```rule
id: PYPKG-PYPROJECT-01
statement: A project MUST be described by `pyproject.toml` (PEP 621 `[project]` metadata and a `[build-system]`); `setup.py`/`setup.cfg` as the source of truth MUST NOT be introduced in new projects.
type: hard
scope: structure
enforced_by: [ci, reviewer]
violation_message: Violates PYPKG-PYPROJECT-01 — A project MUST be described by `pyproject.toml` (PEP 621 `[project]` metadata and a `[build-system]`); `setup.py`/`setup.cfg` as the source of truth MUST NOT be introduced in new projects.
```

```rule
id: PYPKG-SRC-01
statement: Package code MUST live under `src/{package}/` so tests import the installed package, not the working directory by accident.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYPKG-SRC-01 — Package code MUST live under `src/{package}/` so tests import the installed package, not the working directory by accident.
```

```rule
id: PYPKG-ENTRY-01
statement: A command-line application MUST expose its command through `[project.scripts]` pointing at the `main` function, and `python -m {package}` MUST work through `__main__.py`; both MUST call the same `main`.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYPKG-ENTRY-01 — A command-line application MUST expose its command through `[project.scripts]` pointing at the `main` function, and `python -m {package}` MUST work through `__main__.py`; both MUST call the same `main`.
```

```toml
[project]
name = "mypackage"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["pyyaml>=6"]

[project.scripts]
mycommand = "mypackage.__main__:main"
```

```rule
id: PYPKG-SEMVER-01
statement: A published version MUST follow semantic versioning: incompatible changes to the documented public surface (CLI commands and exit codes, MCP tool names and schemas, HTTP shapes, importable API) MUST bump the major version and MUST be preceded by a deprecation period.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYPKG-SEMVER-01 — A published version MUST follow semantic versioning: incompatible changes to the documented public surface (CLI commands and exit codes, MCP tool names and schemas, HTTP shapes, importable API) MUST bump the major version and MUST be preceded by a deprecation period.
```

For an application whose users are humans and scripts, the *public surface* includes the
command grammar, `--json` shapes, and exit-status table (`ARCH-PY-ERROR`), not only the
importable API.

```rule
id: PYPKG-SINGLE-VERSION-01
statement: The version MUST be defined in exactly one place (`pyproject.toml`, or derived from a tag) and read at runtime through `importlib.metadata`, not duplicated in a module constant.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYPKG-SINGLE-VERSION-01 — The version MUST be defined in exactly one place (`pyproject.toml`, or derived from a tag) and read at runtime through `importlib.metadata`, not duplicated in a module constant.
```

```rule
id: PYPKG-DEPS-01
statement: Optional heavy dependencies (a provider SDK, a server framework) MUST be declared as extras (`pip install mypackage[mcp]`) and imported lazily (`PYCOMP-LAZY-01`) so the base install stays small and each surface's dependencies are opt-in.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYPKG-DEPS-01 — Optional heavy dependencies (a provider SDK, a server framework) MUST be declared as extras (`pip install mypackage[mcp]`) and imported lazily (`PYCOMP-LAZY-01`) so the base install stays small and each surface's dependencies are opt-in.
```

Extras are also how one distribution can serve several delivery surfaces without forcing
the MCP SDK on a CLI-only user.

## Multi-package products

A product built from several packages that must be installed together (an engine, a
control plane, a knowledge base) is a *packaging* concern separate from its
architecture. A newcomer should install one thing and get a working product; how many
distributions exist behind that is a maintainer decision (`ARCH-PY-MODULES`,
"Splitting a repository"). Provide a single top-level distribution or installer that
depends on the rest, and do not require users to know the split.

- Depend on sibling packages through published version ranges, not through an editable
  path, for anything that ships. An editable install of a sibling is a *development*
  convenience, and it silently couples the running tool to whatever is checked out.
- When developing a package that a tool you are *running* depends on, run that tool from a
  pinned, separately installed release, not the checkout being edited.

## Publishing checklist

1. `ruff`, type check, `lint-imports`, and tests pass on the supported Python range
2. Version bumped per semver; changelog entry written
3. `python -m build` produces sdist and wheel; install the wheel in a clean environment
   and run the smoke command (`mycommand --help`)
4. Tag the release; publish from CI with a trusted-publishing or scoped token, never a
   personal credential in the repository
