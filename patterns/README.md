# patterns/

Reusable solutions to recurring design problems, defined independently of
any technology or architecture.

A pattern describes the *what* and *why* — not the *how*. The how is expressed
in `architectures/` and `platforms/`, which reference patterns by ID.

## Naming note

Pattern names are intentionally neutral. The same underlying concept may be
called different things across ecosystems (e.g. "Repository" in Spring means
what this framework calls "data-access abstraction"). The pattern document
defines the canonical name and notes known aliases.

## What goes here

- Data-access abstraction
- Observer / reactive streams
- Error propagation
- Command / event patterns
- Decorator / wrapper patterns

## What does NOT go here

- How to implement a pattern in Kotlin (→ `platforms/mobile/`)
- How a specific architecture uses a pattern (→ `architectures/`)

## Document ID prefix: `PAT-`
