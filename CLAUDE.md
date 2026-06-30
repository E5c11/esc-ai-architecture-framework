# ESC AI Engineering Framework

## What This Is

A provider-agnostic engineering framework. It encodes engineering principles,
architecture patterns, and platform conventions so that any AI agent can
implement features correctly and consistently.

The AI model is an interchangeable execution engine. This framework is the knowledge.

---

## How to Use This Framework

### Step 1 — Read the project profile

Every project that consumes this framework defines a `context/project-profile.yaml`.
It declares the platform, architecture, and technology choices.

### Step 2 — Load the relevant framework layers

Use the profile to determine which layers to load. Load in this order:

| # | Layer | Load when |
|---|-------|-----------|
| 1 | `core/` | Always |
| 2 | `patterns/` | Always |
| 3 | `architectures/{name}/` | Matches `profile.architecture` |
| 4 | `platforms/{name}/` | Matches `profile.platform` |
| 5 | `build/` | Touching build config |
| 6 | `quality-gates/` | Writing or reviewing tests |

### Step 3 — Follow the Feature Orchestrator

Locate the relevant orchestrator in `feature-orchestrators/` for the task at hand.
The orchestrator defines phases, steps, validation gates, and which framework
documents are required.

### Step 4 — Apply rules

Rules are referenced by ID throughout documents. Every rule specifies its
`enforced_by` role:

| Role | When to apply |
|------|--------------|
| `planner` | Before designing the approach |
| `executor` | While writing code |
| `reviewer` | After implementation |
| `ci` | Automated — checked by pipeline |

---

## Framework Layers

### `core/`
Engineering principles that are platform and architecture agnostic.
True here regardless of language, framework, or pattern choice.

Examples: dependency inversion, low coupling, high cohesion, naming philosophy.

### `patterns/`
Reusable solutions to recurring design problems. Patterns are named and
defined independently of any technology.

Examples: data-access abstraction, error propagation, observer.

### `architectures/`
Specific architectural styles. Each architecture composes patterns and principles
into a concrete layer structure with explicit contracts between layers.

Examples: `pragmatic-clean/`, `backend-service/`.

### `platforms/`
Technology-specific implementation guides that extend architecture rules.
A platform document always references the architecture it extends.

Examples: `mobile/` (Kotlin/KMP/Compose), `backend/` (Spring Boot/JPA), `web/` (TypeScript/React).

### `build/`
Build system patterns that span platforms. Any JVM/Kotlin project may apply these
regardless of whether it is mobile or backend.

Examples: Gradle convention plugins, coverage setup, static analysis config.

### `quality-gates/`
Testing philosophy, coverage standards, and review checklists.
Applied across all platforms and architectures.

### `feature-orchestrators/`
Step-by-step implementation plans for common engineering tasks.
Each orchestrator declares which framework documents it requires.

### `schemas/`
Formal schemas for all framework document types. Used for validation and tooling.

### `tools/`
Validation scripts and CLI utilities for framework maintenance.

---

## Document IDs

Every framework document has a unique ID declared in its metadata block.
The prefix indicates the layer:

| Prefix | Layer |
|--------|-------|
| `CORE-` | `core/` |
| `PAT-` | `patterns/` |
| `ARCH-` | `architectures/` |
| `PLAT-` | `platforms/` |
| `BUILD-` | `build/` |
| `QG-` | `quality-gates/` |
| `ORCH-` | `feature-orchestrators/` |

Rule IDs within documents follow the pattern:
`{CATEGORY}-{SUBCATEGORY}-{NUMBER}` — e.g. `REP-SSOT-01`, `DI-SCOPE-03`

Rule ID namespaces are owned by this framework. Projects reference them; they do not define their own.

---

## What This Framework Does NOT Contain

- Project-specific knowledge (feature modules, database schemas, service config)
- Business logic or domain models
- Any executable code

Project-specific knowledge lives in the project's own `context/` directory and
references this framework by document ID.
