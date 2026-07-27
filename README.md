# ESC AI Architecture Framework

Provider-agnostic AI engineering framework for deterministic software delivery.

The AI model is an interchangeable execution engine. This framework is the knowledge.

---

## Structure

```
esc-ai-architecture-framework/
│
├── core/                    # Platform-agnostic engineering principles
├── patterns/                # Reusable design patterns (technology-neutral)
├── architectures/           # Architectural styles and layer contracts
│   ├── pragmatic-clean/
│   ├── backend-service/
│   ├── web-app/
│   ├── web-content/
│   └── web-spa/
├── platforms/               # Technology-specific implementation guides
│   ├── mobile/              # Kotlin / KMP / Compose / Koin
│   ├── backend/             # Kotlin / Spring Boot / JPA
│   ├── web/                 # TypeScript / React / Next.js
│   └── library/             # Published KMP packaging and export
├── build/                   # Gradle build system patterns (cross-platform)
├── quality-gates/           # Testing philosophy and coverage standards
├── feature-orchestrators/   # Step-by-step implementation plans
├── schemas/                 # Document and rule schemas
└── tools/                   # Validation scripts
```

## For AI agents

See [`INSTRUCTIONS.md`](./INSTRUCTIONS.md) — the canonical, provider-agnostic guide to
using this framework. Provider-specific entry files (`CLAUDE.md`, etc.) just point here.

## For projects consuming this framework

Define `context/project-profile.yaml` in your project.
The profile determines which framework layers are loaded for each task.
See `INSTRUCTIONS.md`'s Gap Protocol for what to do when this framework and your
project's own internal framework extension both lack coverage for a scenario.

## Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | In progress | Framework skeleton, schemas, conventions |
| 2 | In progress | Core principles |
| 3 | In progress | Mobile platform extraction |
| 4 | In progress | Pragmatic Clean Architecture |
| 5 | In progress | Build system patterns |
| 6 | In progress | Backend platform extraction |
| 7 | In progress | Web platform extraction |
| 8 | In progress | Quality gates and CI validation |
| 9 | Planned | Retrieval index and RAG |
