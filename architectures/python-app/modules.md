---
id: ARCH-PY-MODULES
type: rules
layer: architectures
platform: [python]
architecture: python-app
requires: [ARCH-PY, CORE-COUPLING, CORE-NAMING, CORE-API-STABILITY]
related: [ARCH-PY-ENTRYPOINT, ARCH-PY-USECASE, PLAT-PY-IMPORT-LINTER, PLAT-PY-PACKAGING, ORCH-PY-MODULARISE]
tags: [modules, cohesion, size, splitting, public-api, packages, growth, monolith]
status: active
---
# Modules, Cohesion, and Growth

## Why this document exists

A program does not become unmaintainable in one step. It becomes so because *adding
one more thing to the existing file is always the cheapest move* — until a single
module holds rendering, prompting, business logic, wiring and half a dozen features,
every change touches it, and nothing can be reused without dragging the rest along.
The layer rules in `ARCH-PY` prevent the worst mixing, but they do not by themselves
stop a well-layered module from simply growing without bound. This document sets the
rules that keep growth cheap.

## Size and cohesion

```rule
id: PYMOD-SIZE-01
statement: A module SHOULD stay under 400 lines and MUST NOT exceed 800; a module over 400 lines MUST be justified by a comment naming the single concept it holds, or split.
type: soft
scope: structure
enforced_by: [ci, reviewer]
violation_message: Violates PYMOD-SIZE-01 — A module SHOULD stay under 400 lines and MUST NOT exceed 800; a module over 400 lines MUST be justified by a comment naming the single concept it holds, or split.
```

Line count is a proxy, not the goal: a 600-line module of one cohesive table-driven
concept is healthier than three 200-line modules that constantly import each other.
It is a proxy worth *measuring in CI*, though, because "it just grew" is invisible
until it is expensive. A linter (`ruff` `PLR0915`/`C901` for functions, a small
line-count check for modules) makes the drift visible.

```rule
id: PYMOD-COHESION-01
statement: A module MUST be describable in one sentence without the word "and"; a module mixing rendering, business logic, and I/O MUST be split along those lines.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYMOD-COHESION-01 — A module MUST be describable in one sentence without the word "and"; a module mixing rendering, business logic, and I/O MUST be split along those lines.
```

```rule
id: PYMOD-FUNC-01
statement: A function SHOULD stay under 50 lines and 10 branches; a function that both computes and performs I/O MUST be split into a pure computation and a thin effectful caller.
type: soft
scope: structure
enforced_by: [ci, reviewer]
violation_message: Violates PYMOD-FUNC-01 — A function SHOULD stay under 50 lines and 10 branches; a function that both computes and performs I/O MUST be split into a pure computation and a thin effectful caller.
```

Splitting "compute" from "effect" is the single most effective refactor: the pure
half becomes trivially testable, and the effectful half becomes short enough to read.

## Public surface

```rule
id: PYMOD-API-01
statement: Each package MUST expose its public surface explicitly (`__all__` and/or re-exports in `__init__.py`); other packages MUST import only from that surface, never from a module's internals.
type: hard
scope: structure
enforced_by: [ci, reviewer]
violation_message: Violates PYMOD-API-01 — Each package MUST expose its public surface explicitly (`__all__` and/or re-exports in `__init__.py`); other packages MUST import only from that surface, never from a module's internals.
```

Names beginning with `_` are private by convention and MUST NOT be imported across
packages. An `import-linter` `forbidden` or `independence` contract can enforce this
(`PLAT-PY-IMPORT-LINTER`).

```rule
id: PYMOD-CYCLE-01
statement: Import cycles between modules or packages MUST NOT exist; resolve a cycle by extracting the shared concept into a lower module, not by importing inside a function.
type: hard
scope: structure
enforced_by: [ci, reviewer]
violation_message: Violates PYMOD-CYCLE-01 — Import cycles between modules or packages MUST NOT exist; resolve a cycle by extracting the shared concept into a lower module, not by importing inside a function.
```

A function-local import that exists only to dodge a cycle hides the design problem
(`PYCOMP-LAZY-01` covers the legitimate reason to import locally: optional or heavy
dependencies).

## Splitting a module that has grown

The safe order, in full detail in `ORCH-PY-MODULARISE`:

1. Pin current behavior with tests first (characterization tests if none exist)
2. Extract the pure parts — renderers, parsers, rule tables — into their own modules
3. Extract the operations into use cases with ports
4. Leave a thin entrypoint that only parses, calls, renders
5. Add the `import-linter` contract so the split cannot silently erode

Keep old import paths working for one minor version through re-exports if anything
outside the package imports them (`CORE-API-STABILITY`).

```rule
id: PYMOD-SPLIT-01
statement: Splitting a module MUST be done under an unchanged, passing test suite, in behavior-preserving steps, each committed separately; a split MUST NOT be combined with a behavior change.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYMOD-SPLIT-01 — Splitting a module MUST be done under an unchanged, passing test suite, in behavior-preserving steps, each committed separately; a split MUST NOT be combined with a behavior change.
```

## Keeping a public import path alive

When a module is split and other code imports its old path, keep the old module as a thin
**facade** that re-exports the moved names, so callers keep working.

```rule
id: PYMOD-FACADE-01
statement: A compatibility facade MUST contain no logic and MUST re-export only from modules at its own layer or below; a re-export that makes a lower module import a higher one MUST be replaced by updating the importers.
type: hard
scope: structure
enforced_by: [ci, reviewer]
violation_message: Violates PYMOD-FACADE-01 — A compatibility facade MUST contain no logic and MUST re-export only from modules at its own layer or below; a re-export that makes a lower module import a higher one MUST be replaced by updating the importers.
```

A facade that re-exports upward turns the split into a layering violation. List, in the facade, only
the names that callers actually use; a facade that re-exports "everything just in case" hides how
much of the old surface is really relied on.

## Splitting a repository

Splitting a package into its own distribution/repository is warranted by a *concrete*
trigger, not by size: an independent consumer needs it without the rest, its release
cadence must differ, or cross-repository version coupling is causing breakage. Before
any of those, split *inside* the repository by package boundary and enforce it with
`import-linter`; a package that already has a clean, enforced boundary can be extracted
later almost for free, and one that does not cannot be extracted at all.

```rule
id: PYMOD-REPO-01
statement: A package MUST NOT be extracted into a separate distribution until its boundary is enforced by an import contract and its public surface is explicit.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYMOD-REPO-01 — A package MUST NOT be extracted into a separate distribution until its boundary is enforced by an import contract and its public surface is explicit.
```

## Naming

Module and package names are nouns for concepts in the problem domain (`planning`,
`verification`), lowercase with underscores (`CORE-NAMING`). Avoid `utils`,
`helpers`, `common`, and `misc`: they attract unrelated code and grow without bound.

```rule
id: PYMOD-NAME-01
statement: Modules and packages MUST NOT be named `utils`, `helpers`, `common`, `misc`, or `base`; code belongs in a module named for the concept it implements.
type: hard
scope: naming
enforced_by: [reviewer]
violation_message: Violates PYMOD-NAME-01 — Modules and packages MUST NOT be named `utils`, `helpers`, `common`, `misc`, or `base`; code belongs in a module named for the concept it implements.
```
