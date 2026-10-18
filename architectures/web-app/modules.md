---
id: ARCH-WEB-APP-MODULES
type: rules
layer: architectures
platform: [web]
architecture: [web-app]
requires: [ARCH-WEB-APP, ARCH-WEB-APP-FEATURE-STRUCTURE, ARCH-WEB-APP-DOMAIN, CORE-COUPLING, CORE-NAMING]
related: [ARCH-WEB-APP-COMPOSITION, ARCH-PY-MODULES]
tags: [modules, cohesion, size, public-surface, barrel, cycles, packages, monorepo, refactoring]
status: active
---

# Modules, Cohesion, and Growth

## Why this document exists

A layered architecture keeps layers apart. It does not stop a single file from growing
until it does everything. A 900-line module that fetches, calculates and renders is
the usual end of "just add one more function here", and every later change to it is
slower and riskier than the one before. This document is the discipline that keeps
modules small enough to understand, and the procedure for splitting one that has not
been.

This restates `ARCH-PY-MODULES` for TypeScript, and adds the package boundary a
project needs when logic is shared between the app and other code (a Cloud Function, a
script).

## Size and cohesion

```rule
id: ARCH-WEB-APP-MOD-SIZE-01
statement: A project SHOULD declare a maximum module size and enforce it with a lint rule; a module over it SHOULD be split or carry a comment naming the single concept it holds.
type: soft
scope: structure
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-MOD-SIZE-01 — A project SHOULD declare a maximum module size and enforce it with a lint rule; a module over it SHOULD be split or carry a comment naming the single concept it holds.
```

```rule
id: ARCH-WEB-APP-MOD-COHESION-01
statement: A module MUST be describable in one sentence without the word "and", and a module that mixes rendering, business logic and I/O MUST be split along those lines.
type: hard
scope: structure
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-MOD-COHESION-01 — A module MUST be describable in one sentence without the word "and", and a module that mixes rendering, business logic and I/O MUST be split along those lines.
```

```rule
id: ARCH-WEB-APP-MOD-FUNC-01
statement: A project SHOULD declare a maximum function length and branch count and enforce them with a lint rule, and a function that both computes and performs I/O SHOULD be split into a pure computation and a thin effectful caller.
type: soft
scope: structure
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-MOD-FUNC-01 — A project SHOULD declare a maximum function length and branch count and enforce them with a lint rule, and a function that both computes and performs I/O SHOULD be split into a pure computation and a thin effectful caller.
```

The pure half is domain code (`ARCH-WEB-APP-DOMAIN`) and is tested with plain inputs. The
effectful half is a few lines of glue, with nothing left in it worth a test.

## Public surface

```rule
id: ARCH-WEB-APP-MOD-API-01
statement: A package or feature MUST list its public exports explicitly in its `index.ts` (its page or root view and public types, never hooks, DataSources, Repositories, UseCases or mappers), MUST NOT use `export *` in a public surface, and other code MUST import only from that surface.
type: hard
scope: structure
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-MOD-API-01 — A package or feature MUST list its public exports explicitly in its `index.ts` (its page or root view and public types, never hooks, DataSources, Repositories, UseCases or mappers), MUST NOT use `export *` in a public surface, and other code MUST import only from that surface.
```

`export *` makes the public surface whatever the files happen to export today, so an
internal helper becomes depended on by accident, and the next rename is a breaking
change nobody chose. It also defeats tree-shaking in a way that grows every bundle.

```rule
id: ARCH-WEB-APP-MOD-CYCLE-01
statement: Import cycles between modules or packages MUST NOT exist; a cycle MUST be resolved by extracting the shared concept into a lower module, not by importing inside a function or by deferring with a dynamic import.
type: hard
scope: structure
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-MOD-CYCLE-01 — Import cycles between modules or packages MUST NOT exist; a cycle MUST be resolved by extracting the shared concept into a lower module, not by importing inside a function or by deferring with a dynamic import.
```

## Naming

```rule
id: ARCH-WEB-APP-MOD-NAME-01
statement: Modules, folders and packages MUST NOT be named `utils`, `helpers`, `common`, `misc`, `base` or `lib` alone; code belongs in a module named for the concept it implements.
type: hard
scope: naming
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-MOD-NAME-01 — Modules, folders and packages MUST NOT be named `utils`, `helpers`, `common`, `misc`, `base` or `lib` alone; code belongs in a module named for the concept it implements.
```

`shared/lib/dates.ts` and `shared/lib/rate.ts` say what they hold. `shared/utils.ts` is a
place where unrelated code goes to avoid a decision.

## Splitting a module that has grown

A module split MUST be done under an unchanged, passing test suite, in behaviour-preserving steps each committed separately, and MUST NOT be combined with a behaviour change. (A refactoring procedure, not an architecture rule.)

The procedure:

1. Name the concepts the module holds. If they will not separate cleanly, find the
   missing concept first.
2. Move one concept at a time to a new module, and update the importers. The tests do
   not change; if a test must change, the step was not behaviour-preserving.
3. Run the suite after each move and commit. A failure points at one small step.
4. Only then change behaviour, in its own commit.

A facade keeps an old import path alive while importers move. It is scaffolding, with a
removal date, and never a place where logic lives.

## Packages

When logic is shared between the app and other code (a Cloud Function that runs the
same aggregation the dashboard displays, a script that rebuilds a snapshot), it lives
in a package, not in a folder both copy.

```
apps/web/                  The Next.js app. Imports packages; is imported by nothing
packages/{domain}/         The domain package: pure, framework-free, no I/O
functions/                 Cloud Functions. Imports packages; adds I/O around them
```

```rule
id: ARCH-WEB-APP-MOD-PACKAGE-01
statement: A shared package MUST import nothing from the app or from any package above it, MUST declare its own dependencies, and apps and functions MUST import it only through its public surface; the dependency direction MUST never reverse; logic used by both the app and another runtime lives once, in such a package, and is never copied.
type: hard
scope: structure
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-MOD-PACKAGE-01 — A shared package MUST import nothing from the app or from any package above it, MUST declare its own dependencies, and apps and functions MUST import it only through its public surface; the dependency direction MUST never reverse; logic used by both the app and another runtime lives once, in such a package, and is never copied.
```

Two copies of an aggregation drift, and then the dashboard and the rebuilt snapshot
disagree about a number. One package, tested once, imported by both, cannot.

```rule
id: ARCH-WEB-APP-MOD-PACKAGE-03
statement: A package MUST NOT be extracted from the app until its boundary is enforced by a declared dependency contract and its public surface is explicit.
type: hard
scope: structure
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-MOD-PACKAGE-03 — A package MUST NOT be extracted from the app until its boundary is enforced by a declared dependency contract and its public surface is explicit.
```

Extracting a package whose boundary is a convention only moves the tangle into a second
repository's worth of files. The contract is `ARCH-WEB-APP-DEP-08`.

## Violations

- A 900-line module that fetches, calculates and renders
- A function that parses a response and also computes figures from it
- `export * from './internals'` in a public surface
- An import of `features/x/data/FirestoreXDataSource` from another feature
- An import cycle "fixed" by a dynamic `import()` inside a function
- `utils.ts`, `helpers/`, `common/`
- A module split combined with a behaviour change in one commit
- The same aggregation copied into the app and into a Cloud Function
- A shared package that imports from `apps/web`
