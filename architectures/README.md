# architectures/

Specific architectural styles. Each architecture composes core principles and
patterns into a concrete layer structure with explicit contracts between layers.

Each subdirectory is one architecture. It defines:
- The layers that exist and what each one is responsible for
- The contracts between layers (what crosses the boundary, what does not)
- Which patterns each layer implements and how
- Rules specific to this architecture

## Structure

```
architectures/
├── pragmatic-clean/     # Clean Architecture layers without full abstraction overhead
└── backend-service/     # Controller → Service → DataSource
```

## Relationship to patterns/

Architecture documents reference patterns by ID. They express *how this architecture
uses the pattern*, not what the pattern is.

Example: `PAT-DATA-ACCESS` defines data-access abstraction.
`architectures/pragmatic-clean/datasource.md` defines how Pragmatic Clean
implements that pattern as a DataSource layer.

## Document ID prefix: `ARCH-`

Subdirectory convention: `ARCH-{ARCH_CODE}-{DOCUMENT}`
Examples: `ARCH-PC-DATASOURCE`, `ARCH-BE-SERVICE`
