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

## `check_wiki_staleness.py`

Flags inline-code identifiers (`` `ClassName` ``, `` `methodName()` ``,
`` `File.kt` ``) in a project's own `wiki/`-style docs that no longer appear
anywhere in that project's source tree. Project-agnostic — takes doc and
code directories as CLI args, doesn't assume any particular repo layout.

```
python3 tools/check_wiki_staleness.py --docs wiki --code . [--strict]
```

Heuristic, not a hard gate: it will miss behavioral drift (same names, changed
logic) and can under-flag identifiers that are also plain English words. Point
`--code` at the whole repo root, not just one module — module-scoped runs
undercount badly since KMP/monorepo code is split across many `*/src` trees.
Findings are candidates for human review, not proven bugs.

## Language / runtime

Scripts should be shell or a language available without project-specific
toolchain setup. Prefer minimal dependencies.
