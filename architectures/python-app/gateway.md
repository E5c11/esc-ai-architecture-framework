---
id: ARCH-PY-GATEWAY
type: rules
layer: architectures
platform: [python]
architecture: python-app
requires: [ARCH-PY, CORE-COUPLING, CORE-ERROR]
related: [ARCH-PY-USECASE, ARCH-PY-DATASOURCE, ARCH-PY-ERROR, ARCH-PY-CONCURRENCY, ARCH-PY-OBSERVABILITY, PLAT-PY-SUBPROCESS]
tags: [gateway, adapter, provider, subprocess, git, http-client, external-system, timeout]
---
# Gateway Layer (External Systems)

## Responsibility

A Gateway implements a port for a system the program *acts on or asks* rather than
*stores into*: a git repository, a spawned process, an AI provider, a package registry,
an HTTP API. Where a DataSource is about durable state, a Gateway is about effects and
external answers. Like a DataSource it wraps exactly one technology and translates to
and from domain values; unlike a DataSource its calls can be slow, flaky, expensive, or
unsafe, so it carries extra obligations.

## Provider-agnostic adapters

When several interchangeable providers do the same job (different AI CLIs, different
hosting APIs), each is one Gateway implementing the *same* port. The port describes
the capability the application needs — `run_task(request) -> RunResult` — never a
provider's vocabulary. Provider-specific behavior stays inside the adapter, chosen at
the composition root.

```rule
id: PYGW-PORT-01
statement: A provider-specific Gateway MUST implement a provider-neutral Protocol in the application package; provider names, SDK types, and command-line shapes MUST NOT appear in the port or in any use case.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYGW-PORT-01 — A provider-specific Gateway MUST implement a provider-neutral Protocol in the application package; provider names, SDK types, and command-line shapes MUST NOT appear in the port or in any use case.
```

```rule
id: PYGW-CAPS-01
statement: Differences in what providers can do MUST be expressed as declared capabilities on the port (a `capabilities()` value the use case can inspect), not as `isinstance` checks or provider-name branches in a use case.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYGW-CAPS-01 — Differences in what providers can do MUST be expressed as declared capabilities on the port (a `capabilities()` value the use case can inspect), not as `isinstance` checks or provider-name branches in a use case.
```

## Safety and bounds

```rule
id: PYGW-TIMEOUT-01
statement: Every call to an external system MUST have an explicit timeout; a call with no upper bound MUST NOT be made.
type: hard
scope: behavior
enforced_by: [ci, reviewer]
violation_message: Violates PYGW-TIMEOUT-01 — Every call to an external system MUST have an explicit timeout; a call with no upper bound MUST NOT be made.
```

```rule
id: PYGW-PROC-01
statement: Spawned processes MUST be started with an argument list (`shell=False`), an explicit `cwd`, an explicit environment allow-list where secrets are present, and a timeout; output MUST be captured and bounded.
type: hard
scope: behavior
enforced_by: [ci, reviewer]
violation_message: Violates PYGW-PROC-01 — Spawned processes MUST be started with an argument list (`shell=False`), an explicit `cwd`, an explicit environment allow-list where secrets are present, and a timeout; output MUST be captured and bounded.
```

`ruff`'s `S602`, `S604` and `S605` flag shell use, and `S603`/`S607` prompt review of every subprocess call. See `PLAT-PY-SUBPROCESS`.

```rule
id: PYGW-EXIT-01
statement: A Gateway MUST return the observed exit status and captured output of an external process as data; deciding whether that counts as success MUST be a use-case or domain decision, and an external agent's own report of success MUST NOT be accepted in place of an observable result.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYGW-EXIT-01 — A Gateway MUST return the observed exit status and captured output of an external process as data; deciding whether that counts as success MUST be a use-case or domain decision, and an external agent's own report of success MUST NOT be accepted in place of an observable result.
```

This is what lets a verification gate trust an exit code instead of a model saying
"tests pass".

```rule
id: PYGW-ISOLATE-01
statement: Effects on a working copy (edits, checkouts, generated files) SHOULD be performed in an isolated, disposable copy (a git worktree or temporary directory) and merged back only by an explicit, separate step.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYGW-ISOLATE-01 — Effects on a working copy (edits, checkouts, generated files) SHOULD be performed in an isolated, disposable copy (a git worktree or temporary directory) and merged back only by an explicit, separate step.
```

```rule
id: PYGW-SECRET-01
statement: Credentials MUST be received through configuration at the composition root, MUST NOT be logged or embedded in error messages, and MUST NOT be passed to a subprocess that does not need them.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYGW-SECRET-01 — Credentials MUST be received through configuration at the composition root, MUST NOT be logged or embedded in error messages, and MUST NOT be passed to a subprocess that does not need them.
```

```rule
id: PYGW-ERROR-01
statement: A Gateway MUST translate its transport and provider errors into the project's gateway error types (distinguishing at least unavailable, timed out, and rejected) at its own boundary.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PYGW-ERROR-01 — A Gateway MUST translate its transport and provider errors into the project's gateway error types (distinguishing at least unavailable, timed out, and rejected) at its own boundary.
```

## Retry

Retrying is policy, not plumbing. A Gateway does not silently retry non-idempotent
calls. Where retry is appropriate (idempotent reads, rate-limit backoff), it is
explicit, bounded, logged, and configured at the composition root.

```rule
id: PYGW-RETRY-01
statement: A Gateway MUST NOT retry a call unless the call is idempotent or the retry policy is explicitly configured; retries MUST be bounded and logged.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYGW-RETRY-01 — A Gateway MUST NOT retry a call unless the call is idempotent or the retry policy is explicitly configured; retries MUST be bounded and logged.
```

## Testing

Test a Gateway against the real thing where that is cheap and safe (a temporary git
repository, a trivial spawned script), and against a **recorded or scripted fake** of
the external system where it is not (a paid provider). Use cases never see the real
Gateway in unit tests; they get a fake of the port.
