---
id: ARCH-PY-CONCURRENCY
type: rules
layer: architectures
platform: [python]
architecture: python-app
requires: [ARCH-PY, CORE-COUPLING]
related: [ARCH-PY-GATEWAY, ARCH-PY-USECASE, ARCH-PY-ENTRYPOINT, ARCH-PY-COMPOSITION, PLAT-PY-SUBPROCESS]
tags: [concurrency, async, asyncio, threads, processes, scheduler, cancellation, sync-by-default]
---
# Concurrency

## Position

**Synchronous by default.** Most of this architecture's work — planning, validating,
running one task and waiting for its verification — is naturally sequential, and
sequential code is the easiest to reason about, test, and debug. Concurrency is
introduced at a specific, named seam when a concrete need exists (several tasks in
flight, a server handling many clients), and it stays *out of the domain and out of
use-case logic*.

## Where concurrency may live

| Need | Mechanism | Seam |
|---|---|---|
| Wait for several independent external processes / tasks | Threads (`concurrent.futures.ThreadPoolExecutor`) or subprocess handles | A scheduler in the application layer, driving a Gateway |
| Serve many clients (MCP over network, HTTP) | `asyncio` at the entrypoint | The entrypoint only; it calls sync use cases via `asyncio.to_thread`, or use cases are `async` end to end if the whole stack is |
| CPU-bound work | `ProcessPoolExecutor` | A Gateway or worker; values must be picklable |

```rule
id: PYCONC-SYNC-01
statement: Domain code MUST be synchronous and MUST NOT create threads, tasks, or event loops.
type: hard
scope: behavior
enforced_by: [ci, reviewer]
violation_message: Violates PYCONC-SYNC-01 — Domain code MUST be synchronous and MUST NOT create threads, tasks, or event loops.
```

```rule
id: PYCONC-COLOR-01
statement: A project MUST choose one execution model per delivery surface — sync or async — and MUST NOT mix `async def` and blocking calls in the same layer; a blocking call from async code MUST go through `asyncio.to_thread` (or an executor).
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYCONC-COLOR-01 — A project MUST choose one execution model per delivery surface — sync or async — and MUST NOT mix `async def` and blocking calls in the same layer; a blocking call from async code MUST go through `asyncio.to_thread` (or an executor).
```

A blocking call inside a coroutine stalls every other task on the loop. If the
program is mostly sync with one async surface, bridge at that surface's boundary and
leave the rest alone; do not "async-ify" the use cases to please one entrypoint.

```rule
id: PYCONC-STATE-01
statement: Concurrent workers MUST NOT share mutable state; they MUST communicate through immutable values, queues, or a DataSource that serializes access.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYCONC-STATE-01 — Concurrent workers MUST NOT share mutable state; they MUST communicate through immutable values, queues, or a DataSource that serializes access.
```

Frozen domain values (`ARCH-PY-DOMAIN`) make this nearly free.

```rule
id: PYCONC-CLAIM-01
statement: Work that multiple workers could pick up MUST be claimed atomically through the DataSource (a compare-and-set or single-statement claim), never by read-then-write in application code.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYCONC-CLAIM-01 — Work that multiple workers could pick up MUST be claimed atomically through the DataSource (a compare-and-set or single-statement claim), never by read-then-write in application code.
```

```rule
id: PYCONC-CANCEL-01
statement: Long-running or externally-effecting work MUST be cancellable and MUST clean up what it started (terminate spawned processes, release worktrees, record the interruption) on cancellation, timeout, and `KeyboardInterrupt`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYCONC-CANCEL-01 — Long-running or externally-effecting work MUST be cancellable and MUST clean up what it started (terminate spawned processes, release worktrees, record the interruption) on cancellation, timeout, and `KeyboardInterrupt`.
```

An interrupted run leaves a **resumable checkpoint**, not orphaned processes and a
half-written state. Recording the interruption is part of the audit trail
(`ARCH-PY-OBSERVABILITY`).

```rule
id: PYCONC-LIFETIME-01
statement: Resources that outlive a call (threads, executors, connections, subprocesses) MUST be owned by an object with an explicit close/`__exit__`, opened and closed by the composition root or the use case that started them.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYCONC-LIFETIME-01 — Resources that outlive a call (threads, executors, connections, subprocesses) MUST be owned by an object with an explicit close/`__exit__`, opened and closed by the composition root or the use case that started them.
```

## Database connections

`sqlite3` connections are not safely shared across threads by default. Give each worker
its own connection (or serialize through one writer) and keep transactions short
(`PLAT-PY-PERSISTENCE`).

## Testing

Test the scheduler with a **deterministic fake executor** that runs work inline, so a
test asserts on ordering and claims without sleeping. Have one integration test with a
real thread pool to catch shared-state mistakes. Tests MUST NOT rely on `time.sleep`
for synchronization.
