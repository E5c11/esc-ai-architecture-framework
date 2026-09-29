---
id: ARCH-PY-USECASE
type: rules
layer: architectures
platform: [python]
architecture: python-app
requires: [ARCH-PY, CORE-DI, PAT-DATA-ACCESS]
related: [ARCH-PY-DOMAIN, ARCH-PY-DATASOURCE, ARCH-PY-GATEWAY, ARCH-PY-ERROR, ARCH-PY-ENTRYPOINT, ARCH-PY-COMPOSITION, PLAT-PY-DI]
tags: [use-case, application, ports, protocol, unit-of-work, orchestration, stages]
---
# Application Layer (Use Cases)

## Responsibility

The application layer is where one operation gets done. A **use case** coordinates
domain rules and the ports (Protocols) it needs to accomplish a single thing a caller
wants: *draft a plan*, *run a task*, *rate a note*, *validate a repository*. It owns
the unit of work and decides the order of steps; it does not own the rules of the
domain (those are pure functions in `ARCH-PY-DOMAIN`) and does not know how it was
invoked.

## Shape

A use case is a small class with injected ports and one public method, or — when it
has no state — a plain function with its ports as leading parameters.

```python
@dataclass(frozen=True)
class DraftPlan:
    routing: RoutingIndex          # port
    drafts: DraftStore             # port

    def __call__(self, request: DraftRequest) -> PlanDraft:
        matches = self.routing.match(request.repository, request.objective)
        draft = build_draft(request, matches)      # pure, domain
        self.drafts.save(draft)
        return draft
```

## Rules

```rule
id: PYUC-SINGLE-01
statement: A use case MUST do one operation, expose one public entry point, and be named for the operation in the domain's language (a verb phrase), not for a technology or a surface.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYUC-SINGLE-01 — A use case MUST do one operation, expose one public entry point, and be named for the operation in the domain's language (a verb phrase), not for a technology or a surface.
```

`RunTask`, `ApplyPlan`, `RateLocalNote` — not `CliHelpers`, `SqliteOps`, `McpHandlers`.

```rule
id: PYUC-PORTS-01
statement: A use case MUST depend on collaborators only through Protocols it (or the application package) declares, received by constructor or parameter — never by importing an infrastructure module or constructing one.
type: hard
scope: di
enforced_by: [ci, reviewer]
violation_message: Violates PYUC-PORTS-01 — A use case MUST depend on collaborators only through Protocols it (or the application package) declares, received by constructor or parameter — never by importing an infrastructure module or constructing one.
```

```rule
id: PYUC-PORTS-02
statement: Ports MUST be declared as `typing.Protocol` classes in the application package, expressing domain operations in domain language and returning domain types.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYUC-PORTS-02 — Ports MUST be declared as `typing.Protocol` classes in the application package, expressing domain operations in domain language and returning domain types.
```

A port method is named for intent (`save_draft`, `next_ready_task`), never for its
storage (`insert_row`, `run_sql`). See `PAT-DATA-ACCESS`.

```rule
id: PYUC-IO-01
statement: A use case MUST NOT perform presentation I/O — no print, prompt, log-as-output, or process exit — and MUST NOT read ambient state (`os.environ`, `sys.argv`, the current directory, the clock).
type: hard
scope: behavior
enforced_by: [ci, reviewer]
violation_message: Violates PYUC-IO-01 — A use case MUST NOT perform presentation I/O — no print, prompt, log-as-output, or process exit — and MUST NOT read ambient state (`os.environ`, `sys.argv`, the current directory, the clock).
```

Ambient state is a hidden parameter. Pass configuration in through the constructor and
time through a `Clock` port so a test can pin it (`ARCH-PY-DOMAIN`).

```rule
id: PYUC-RETURN-01
statement: A use case MUST return domain values or frozen outcome objects, never infrastructure types (rows, cursors, subprocess handles, provider SDK objects).
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates PYUC-RETURN-01 — A use case MUST return domain values or frozen outcome objects, never infrastructure types (rows, cursors, subprocess handles, provider SDK objects).
```

```rule
id: PYUC-UOW-01
statement: A use case that performs more than one write MUST perform them inside a single unit of work exposed by a port, so they commit or roll back together.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYUC-UOW-01 — A use case that performs more than one write MUST perform them inside a single unit of work exposed by a port, so they commit or roll back together.
```

Where the writes span systems that cannot share a transaction (a database and a git
worktree, say), the use case orders them so a failure between steps leaves a state
that is resumable and detectable — and records enough (a checkpoint) to resume.

## Staged use cases (procedures)

Some operations are a fixed, ordered sequence of stages that must always run the same
way — an intake question, a gate, an implementation step, a verification. Model the
procedure as **data**, not as a hand-written `if` ladder per operation:

- A `Stage` is a frozen value: name, kind (gate / question / action), interaction mode
  (fixed or variable), and what implements it.
- A procedure is an ordered tuple of stages, defined in the domain (`ARCH-PY-DOMAIN`).
- A single runner in the application layer walks the tuple, resolves each stage to a
  registered implementation, and records the outcome.

```rule
id: PYUC-STAGE-01
statement: A procedure's stage sequence MUST be declared as data in one place and executed by one generic runner; use cases MUST NOT re-implement the sequence per operation.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYUC-STAGE-01 — A procedure's stage sequence MUST be declared as data in one place and executed by one generic runner; use cases MUST NOT re-implement the sequence per operation.
```

```rule
id: PYUC-STAGE-02
statement: A gate stage MUST decide pass or fail from an observable result (an exit code, a checked artifact, a computed metric), never from a caller's or an agent's own claim of success.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYUC-STAGE-02 — A gate stage MUST decide pass or fail from an observable result (an exit code, a checked artifact, a computed metric), never from a caller's or an agent's own claim of success.
```

```rule
id: PYUC-STAGE-03
statement: A mandatory stage MUST run for every caller; who is running the procedure MAY change how a stage is presented (`ARCH-PY-POLICY`) but MUST NOT change whether it runs.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYUC-STAGE-03 — A mandatory stage MUST run for every caller; who is running the procedure MAY change how a stage is presented (`ARCH-PY-POLICY`) but MUST NOT change whether it runs.
```

```rule
id: PYUC-STAGE-04
statement: A stage with no implementation yet MUST be represented explicitly as pending and MUST fail loudly if a caller tries to treat it as passed.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYUC-STAGE-04 — A stage with no implementation yet MUST be represented explicitly as pending and MUST fail loudly if a caller tries to treat it as passed.
```

A pending stage silently counted as green is worse than a missing one: it looks like
assurance and provides none.

## Testing

Use cases are tested against **fakes of their ports** (in-memory, deterministic), not
mocks asserting call counts (`CORE-TESTING`, `PLAT-PY-TESTING`). The suite for a use
case needs no database, subprocess, or network.
