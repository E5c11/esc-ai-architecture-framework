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

## Capture gates: recording knowledge the program cannot check

Some gates cannot decide from an observable result because what they guard is *knowledge* someone supplies: a
root cause for a bug, a scope boundary, a rationale. `PYUC-STAGE-02` (decide from an observable result) cannot
apply, and pretending it does produces a gate that only looks strict. A **capture gate** is honest about what it
can do: it makes sure the knowledge was recorded, in a usable form, *before* the work it guides begins.

```rule
id: PYUC-STAGE-05
statement: A gate that records supplied knowledge (a capture gate) MUST check that it is present and well-formed, MUST reject the ways it is captured in name only (missing, empty, no supporting evidence, or a restatement of the request), MUST say in its help and documentation that it does not check the knowledge is true, and MUST leave truth to a later gate that decides from an observable result.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYUC-STAGE-05 — A gate that records supplied knowledge (a capture gate) MUST check that it is present and well-formed, MUST reject the ways it is captured in name only (missing, empty, no supporting evidence, or a restatement of the request), MUST say in its help and documentation that it does not check the knowledge is true, and MUST leave truth to a later gate that decides from an observable result.
```

Example: a `fix` procedure's `root_cause` stage requires a statement and evidence and rejects a statement that
only restates the problem report, but it cannot know the cause is right; the `verify` stage that runs the real
tests against the fix is what tests the cause.

```rule
id: PYUC-STAGE-06
statement: A stage that must hold at execution time MUST be enforced against the persisted artifact execution reads, not only where that artifact is created; the artifact MUST record which procedure it belongs to.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYUC-STAGE-06 — A stage that must hold at execution time MUST be enforced against the persisted artifact execution reads, not only where that artifact is created; the artifact MUST record which procedure it belongs to.
```

A gate that runs only when a plan is generated is bypassed by editing the plan file, and it cannot run at all if
the plan file does not say which procedure it belongs to. (In one real case the work type reached only a
human-readable README, so execution could not tell a `fix` from a `feature`.) Persist the procedure identity in
the artifact, make the artifact's own validator enforce the stage, and put the captured knowledge where the
agent will actually read it -- a fact stored but never shown to the agent is decoration.

## Gates that verify, and work that promises not to change anything

Three failure modes were found by building the `plan`, `investigate`, `refactor` and `document` procedures, each of
which looked fine in review and was wrong in a way only a real run showed.

```rule
id: PYUC-STAGE-07
statement: A gate that verifies a change MUST run against the tree the change was made in, decided from the run's own record of where it edited, not against a default location.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYUC-STAGE-07 — A gate that verifies a change MUST run against the tree the change was made in, decided from the run's own record of where it edited, not against a default location.
```

When an agent edits a disposable copy (a git worktree, a container, a temporary directory) its changes are *not* in the
live checkout. Running the gates there tests the code as it was before the agent started: a change that breaks the
build is reported as passing and one that fixes it as failing. This inversion existed in a real system and was
invisible because both outcomes look plausible. Make the location explicit (the run records where it edited; the
verifier reads that record), build the verification *plan* from the trusted checkout so the agent cannot rewrite its
own gates, and write logs to a location independent of where the commands run.

```rule
id: PYUC-STAGE-08
statement: A gate that can pass when nothing was checked MUST fail closed wherever the claim depends on its checks having run; "no check ran" MUST NOT be reported as "all checks passed".
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYUC-STAGE-08 — A gate that can pass when nothing was checked MUST fail closed wherever the claim depends on its checks having run; "no check ran" MUST NOT be reported as "all checks passed".
```

`all(check.passed for check in checks)` is true for an empty list. A verification plan whose gates are all skipped
reported `passed`, so a refactor with no tests "verified" having proved nothing. Where a procedure's whole point is a
claim the checks back (behaviour is unchanged), require at least one check that actually ran and passed, before
spending the expensive step, and refuse a baseline that is already failing.

```rule
id: PYUC-STAGE-09
statement: A work type that promises not to change state MUST be enforced by both reducing the capabilities it is granted and an independent before/after comparison of the state it must not change; omitting the stage that would change state is not enforcement.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYUC-STAGE-09 — A work type that promises not to change state MUST be enforced by both reducing the capabilities it is granted and an independent before/after comparison of the state it must not change; omitting the stage that would change state is not enforcement.
```

A read-only procedure that merely has no "implement" stage stops nothing: the agent had whatever permissions the global
default granted. Enforce it twice, at different layers, so a bug in one fails closed in the other: force the granted
capabilities down at the single place every run passes through (not only in the CLI, which other callers bypass), and
compare a snapshot of the state before and after the run regardless of adapter or policy. Include content hashes in
the snapshot, because a status listing cannot show that an already-modified file was modified again. Report what
changed and fail; never revert automatically, because a revert is itself a destructive edit. Also make the expected
outcome a success: "nothing changed" is the correct result of read-only work, not a warning.

## Pointing at things: reference checks

A check that documentation points at things that exist is cheap and useful, but only if it does not cry wolf. Treat a
token as a path claim only when it is unmistakable (an explicit link target, or a span whose last segment has a file
extension or whose first segment is a real top-level entry), and skip code blocks, URLs, hostnames, globs and
placeholders. State plainly, in the tool's own help and report, that it proves references *resolve*, not that the
prose is *true* (`PYUC-STAGE-05`).

## Testing

Use cases are tested against **fakes of their ports** (in-memory, deterministic), not
mocks asserting call counts (`CORE-TESTING`, `PLAT-PY-TESTING`). The suite for a use
case needs no database, subprocess, or network.
