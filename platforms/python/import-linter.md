---
id: PLAT-PY-IMPORT-LINTER
type: guide
layer: platforms
platform: [python]
architecture: python-app
requires: [ARCH-PY, PLAT-PY]
related: [ARCH-PY-MODULES, ARCH-PY-COMPOSITION, PLAT-PY-TESTING]
tags: [import-linter, ruff, layers, enforcement, ci, contracts, fitness-function]
status: active
---
# Enforcing the Architecture: import-linter and ruff

Extends: `ARCH-PY-DEP-04`

A layer rule that exists only in prose is a suggestion. In Python the dependency
direction is checkable from the import graph, so the architecture is enforced
mechanically: `import-linter` for the layer graph and third-party/stdlib bans,
`ruff` for the same bans at the finer file-pattern level and for the style-level
rules. These checks are the project's **architecture fitness functions** — they measure
conformance directly, independent of whether tests happen to pass.

## Rules

```rule
id: PYIL-CONTRACT-01
statement: A project MUST declare at minimum a `layers` contract over `entrypoints | infrastructure`, `application`, `domain`, and a `forbidden` contract keeping I/O and framework modules out of `domain`, and MUST run `lint-imports` in CI as a failing check.
type: hard
scope: structure
enforced_by: [ci, planner]
violation_message: Violates PYIL-CONTRACT-01 — A project MUST declare at minimum a `layers` contract over `entrypoints | infrastructure`, `application`, `domain`, and a `forbidden` contract keeping I/O and framework modules out of `domain`, and MUST run `lint-imports` in CI as a failing check.
```

```rule
id: PYIL-NOBYPASS-01
statement: A contract MUST NOT be weakened (an `ignore_imports` entry, a removed contract) to make a failing change pass without a written justification in the same change; an ignore MUST name the exact import and the reason.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYIL-NOBYPASS-01 — A contract MUST NOT be weakened (an `ignore_imports` entry, a removed contract) to make a failing change pass without a written justification in the same change; an ignore MUST name the exact import and the reason.
```

A failing contract is the architecture doing its job. The fix is to move the code or
introduce a port, not to add an ignore.

```rule
id: PYIL-SURFACE-01
statement: Each delivery surface package MUST be covered by an `independence` contract so surfaces cannot import each other.
type: hard
scope: structure
enforced_by: [ci, reviewer]
violation_message: Violates PYIL-SURFACE-01 — Each delivery surface package MUST be covered by an `independence` contract so surfaces cannot import each other.
```

## Reference configuration

`.importlinter` (or `[tool.importlinter]` in `pyproject.toml`). This shape was run
against `import-linter` 2.x: `|` separates independent sibling layers on one line, and
`include_external_packages = True` is required to forbid third-party and standard-library
modules in a `forbidden` contract.

```ini
[importlinter]
root_package = mypackage
include_external_packages = True

[importlinter:contract:layers]
name = Clean layers
type = layers
layers =
    mypackage.entrypoints | mypackage.infrastructure
    mypackage.application
    mypackage.domain

[importlinter:contract:surfaces]
name = Delivery surfaces are independent
type = independence
modules =
    mypackage.entrypoints.cli
    mypackage.entrypoints.mcp
    mypackage.entrypoints.http

[importlinter:contract:pure-domain]
name = Domain performs no I/O and uses no framework
type = forbidden
source_modules = mypackage.domain
forbidden_modules =
    sqlite3
    subprocess
    socket
    http
    urllib
    requests
    httpx
    pydantic
```

`mypackage.composition` and `mypackage.__main__` sit outside the layered contract by
design: they are the one place allowed to import everything (`PYCOMP-ROOT-02`). Add a
`forbidden` contract if you want to guarantee that *nothing else* imports
`mypackage.composition`:

```ini
[importlinter:contract:only-the-composition-root-builds-infrastructure]
name = Only the composition root touches infrastructure
type = forbidden
source_modules =
    mypackage.domain
    mypackage.application
    mypackage.entrypoints
forbidden_modules =
    mypackage.infrastructure
    mypackage.composition
```

Because contracts are transitive by default, this also fails when an entrypoint reaches infrastructure *through*
a helper, which is the case that actually happens (a use case imports a class only for a type annotation; a
module you thought was pure imports the store). It is the contract that forces the App/factory pattern
(`ARCH-PY-COMPOSITION`).

## ruff: finer-grained bans and style rules

`ruff` complements `import-linter` where the rule is per file pattern or a call-level
check. Ban an API globally, then re-allow it only where the architecture permits:

```toml
[tool.ruff]
src = ["src"]          # first-party detection for a src/ layout (import sorting)
line-length = 120      # set it: the default (88) alone flags hundreds of existing lines

[tool.ruff.lint]
select = ["F", "I", "B", "SIM105", "S101", "S110", "S602", "S604", "S605", "S608",
          "BLE", "T20", "DTZ", "E722", "TID"]
# Enable C901, PLR0912 and PLR0915 (complexity) once existing offenders are refactored. Do NOT select all
# of "PLR": PLR2004 (magic values) is noise and will bury the findings that matter.

[tool.ruff.lint.flake8-tidy-imports.banned-api]
"sqlite3".msg = "Persistence I/O belongs in infrastructure (ARCH-PY-DEP-01)."
"subprocess".msg = "Process execution belongs in a Gateway (PYGW-PROC-01)."

[tool.ruff.lint.per-file-ignores]
"src/mypackage/infrastructure/**" = ["TID251"]
"src/mypackage/entrypoints/**" = ["T201"]     # entrypoints may print
"tests/**" = ["S101", "TID251"]               # tests may assert and touch real I/O
```

Verified behavior: with `sqlite3` in `banned-api` and an `infrastructure/**`
per-file-ignore, an `import sqlite3` in `domain/` is reported (`TID251`) and the same
import in `infrastructure/` is not.

## Behavior worth knowing (each verified by running `import-linter` 2.15)

- **A `forbidden` contract can only name *top-level* external packages.** `forbidden_modules =
  esc_exec.registry` fails with "subpackages of external packages are not valid". To forbid a
  submodule of a sibling library you own, add that library to `root_packages` so it is part of the
  analyzed graph. Standard-library modules (`sqlite3`, `subprocess`) can be forbidden by name with
  `include_external_packages = True`.
- **Contracts check transitive imports by default.** "A imports B" is broken if A → C → B.
  That is what you want for purity ("the renderer must not reach `subprocess`, even through a
  helper") and it surfaces real design smells (a pure value type living in an I/O module). Set
  `allow_indirect_imports = True` only when you mean direct imports only, and say why.
- **`ignore_imports` belongs to the contract it is written under.** Put it directly under the
  contract it relaxes, with a comment naming the exact import and the reason. Inserting another
  contract between the comment and the list silently attaches the ignores to the wrong contract.
- **A `layers` contract only constrains the modules it lists.** Modules not named are
  unconstrained, so for a flat library add a completeness test (below).
- **Compatibility re-exports must point downward.** A facade that re-exports a higher layer's
  names from a lower module makes the lower module import the higher one and breaks the contract;
  move the importers to the new module instead of keeping the upward re-export.
- **Ruff `# noqa: F401` on a multi-line import goes on the first line** (`from x import (  # noqa:
  F401`), not after the closing parenthesis, or `--fix` will delete the names.

### A flat library: classify every module

When the public layout must stay flat (`from pkg.module import name` is the API), keep the modules
where they are and classify them into groups in `.importlinter` (entrypoint, application, gateways,
core). Write `forbidden` contracts for what holds today (core imports no gateway; core does no
process/network/database I/O; only `__main__` imports the CLI). A `layers` contract does not
notice a module it does not list, so add a test that reads `.importlinter` and fails when a module
under the package appears in no contract:

```python
def test_every_module_is_classified_in_the_contracts(self):
    parser = configparser.ConfigParser(); parser.read(ROOT / ".importlinter")
    mentioned = {part.strip() for s in parser.sections()
                 for key in ("layers", "source_modules", "forbidden_modules")
                 for line in parser[s].get(key, "").splitlines() for part in line.split("|")}
    modules = {f"pkg.{p.stem}" for p in PACKAGE.glob("*.py") if p.stem != "__init__"}
    self.assertEqual(set(), modules - mentioned)
```

## Making the check part of a change, not an afterthought

- Run `lint-imports` and `ruff check` locally before pushing and in CI on every change.
- A new package gets its contract entry in the *same* change that creates it.
- A refactor that moves code across layers (`ORCH-PY-MODULARISE`) is done when the
  contracts pass without new ignores.
- The list of contracts and their pass/fail result is machine-readable input for
  architecture-conformance measurement: a tool orchestrating this framework can run
  `lint-imports` and treat its exit status as an objective fitness signal.
