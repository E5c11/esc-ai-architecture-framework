# tools/

Validation scripts and CLI utilities for framework maintenance.

Tools in this directory enforce framework health — they are not consumed by
AI agents during feature implementation.

## Planned tools (Phase 6)

- `validate-references` — detect broken document ID references
- `validate-schema` — check document metadata against schemas/
- `check-duplicate-ids` — catch duplicate document or rule IDs
- `check-circular-refs` — detect circular requires chains
- `generate-index` — build retrieval index from document metadata

## Language / runtime

Scripts should be shell or a language available without project-specific
toolchain setup. Prefer minimal dependencies.
