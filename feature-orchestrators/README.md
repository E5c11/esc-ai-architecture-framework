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
