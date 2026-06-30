# feature-orchestrators/

Step-by-step implementation plans for common engineering tasks.

An orchestrator is the entry point an AI agent uses when assigned a task.
It references framework documents by ID — the agent loads those documents
before executing.

## Structure

Orchestrators are organised by platform:

```
feature-orchestrators/
├── mobile/
├── backend/
└── shared/      # Orchestrators that span platforms
```

## What makes a good orchestrator

- A single, well-scoped goal
- Explicit phases with validation gates between them
- References to framework documents by ID (not by copying their content)
- A validation checklist at the end of each phase

## What does NOT go here

- Implementation instructions (→ `architectures/` or `platforms/`)
- Rule definitions (→ rule-set documents in the relevant layer)
- Project-specific steps (→ the project's own `context/` directory)

## Document ID prefix: `ORCH-`

---

## Gap protocol — mandatory hard stop

When executing an orchestrator, if you discover that a required pattern, rule, or
architectural decision is **not documented in the framework**, you MUST:

1. **Stop immediately.** Do not improvise or infer the missing pattern from existing code.
2. **Create a stub document** in the appropriate framework layer (`architectures/`,
   `platforms/`, `patterns/`, etc.) with a `status: stub` frontmatter field, a clear
   outline of what the document must cover, and a TODO note.
3. **Add an entry to `todo/missing-files.md`** describing the gap and any open questions.
4. **Notify the user.** Report the gap, the stub location, and what decision or research
   is needed before the document can be written.
5. **Do not continue** until the framework document is written and the gap is resolved.

**Why this matters:** Improvising undocumented patterns creates inconsistency across
features and defeats the purpose of the framework. A short pause to document the gap
correctly is always worth more than a fast but inconsistent implementation.

The framework grows through gaps found during real implementation work. Each hard stop
is a contribution to the framework.
