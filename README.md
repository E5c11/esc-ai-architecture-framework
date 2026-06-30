# ESC AI Engineering Framework

Provider-agnostic AI engineering framework for deterministic software delivery.

The AI model is an interchangeable execution engine. This framework is the knowledge.

---

## Structure

```
esc-ai-framework/
│
├── core/                    # Platform-agnostic engineering principles
├── patterns/                # Reusable design patterns (technology-neutral)
├── architectures/           # Architectural styles and layer contracts
│   ├── pragmatic-clean/
│   └── backend-service/
├── platforms/               # Technology-specific implementation guides
│   ├── mobile/              # Kotlin / KMP / Compose / Koin
│   ├── backend/             # Kotlin / Spring Boot / JPA
│   └── web/                 # TypeScript / React / Next.js
├── build/                   # Gradle build system patterns (cross-platform)
├── quality-gates/           # Testing philosophy and coverage standards
├── feature-orchestrators/   # Step-by-step implementation plans
├── schemas/                 # Document and rule schemas
└── tools/                   # Validation scripts
```

## For AI agents

Start with `CLAUDE.md`.

## For projects consuming this framework

Define `context/project-profile.yaml` in your project.
The profile determines which framework layers are loaded for each task.

## Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | In progress | Framework skeleton, schemas, conventions |
| 2 | Planned | Core principles |
| 3 | Planned | Mobile platform extraction |
| 4 | Planned | Pragmatic Clean Architecture |
| 5 | Planned | Build system patterns |
| 6 | Planned | Backend platform extraction |
| 7 | Planned | Web platform extraction |
| 8 | Planned | Quality gates and CI validation |
| 9 | Planned | Retrieval index and RAG |
