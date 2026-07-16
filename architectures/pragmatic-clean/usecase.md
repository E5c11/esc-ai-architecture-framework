---
id: ARCH-PC-USECASE
type: guide
layer: architecture
platform: [mobile]
architecture: [pragmatic-clean]
requires: [ARCH-PC, PAT-OUTCOME, PAT-OBSERVER, PLAT-MOB-KOTLIN]
related: [ARCH-PC-REPOSITORY, ARCH-PC-VIEWMODEL, ARCH-PC-ERROR-FLOW, ARCH-PC-DI]
tags: [usecase, orchestrator, business-logic, outcome, flow, suspend]
---

# UseCase Layer

## Responsibility

Encapsulate business logic (UseCase) or sequence multiple operations (Orchestrator).
Neither reads from nor writes to the UI. Neither owns a provider directly.

## UseCase vs Orchestrator

| | UseCase | Orchestrator |
|---|---|---|
| Contains logic | Yes — validation, transformation, calculation | No — sequencing only |
| Calls | Repositories / DataSources | Other UseCases |
| Allowed to branch | Yes | No |

```rule
id: ARCH-PC-UC-LOGIC-01
statement: A UseCase MUST contain business logic that justifies its existence.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-UC-LOGIC-01 — A UseCase MUST contain business logic that justifies its existence.
```

A UseCase that only delegates to a Repository with no added validation, transformation, or decision is pure boilerplate — eliminate it and have the ViewModel call the Repository directly.

```rule
id: ARCH-PC-UC-ORCH-01
statement: An Orchestrator MUST contain no logic.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-UC-ORCH-01 — An Orchestrator MUST contain no logic.
```

If an `if`, `when`, or calculation appears inside an Orchestrator, extract it to a dedicated UseCase and inject that UseCase.

```rule
id: ARCH-PC-UC-ORCH-02
statement: Orchestrators MUST call UseCases, not Repositories or DataSources directly.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-UC-ORCH-02 — Orchestrators MUST call UseCases, not Repositories or DataSources directly.
```

```rule
id: ARCH-PC-UC-ORCH-03
statement: Orchestrators MAY construct request objects and pass data between steps.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-UC-ORCH-03 — Orchestrators MAY construct request objects and pass data between steps.
```

Object creation is coordination, not logic.

## Flow-based vs one-shot

| Use | Return type |
|---|---|
| Observing data that changes over time | `Flow<Outcome<T>>` |
| Single request-response (fetch, write, command) | `suspend` returning `Outcome<T>` |
| Emitting intermediate progress | `Flow<Outcome<T>>` |

```rule
id: ARCH-PC-UC-RETURN-01
statement: A UseCase that observes a stream from the Repository MUST preserve it as a `Flow`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-UC-RETURN-01 — A UseCase that observes a stream from the Repository MUST preserve it as a `Flow`.
```

Never collapse a `Flow` to a single suspend call — it breaks the reactive chain and stops updates from propagating.

```rule
id: ARCH-PC-UC-LOADING-01
statement: UseCases MUST NOT emit loading states.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-UC-LOADING-01 — UseCases MUST NOT emit loading states.
```

The ViewModel sets loading state before invoking the UseCase and clears it on result.

## Error handling

The UseCase layer is the last opportunity to intercept and handle unexpected
technical exceptions before they reach the ViewModel.

```rule
id: ARCH-PC-UC-ERROR-01
statement: The UseCase MUST catch at its boundary and either translate unexpected exceptions to domain exceptions, or pass through domain exceptions that were already translated by the DataSource.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-UC-ERROR-01 — The UseCase MUST catch at its boundary and either translate unexpected exceptions to domain exceptions, or pass through domain exceptions that were already translated by the DataSource.
```

```rule
id: ARCH-PC-UC-ERROR-02
statement: The fallback exception in the catch handler MUST be a domain-specific exception named after the operation (e.g.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-UC-ERROR-02 — The fallback exception in the catch handler MUST be a domain-specific exception named after the operation (e.g.
```

`FetchVideosException`), not a generic unknown exception. Generic exceptions lose diagnostic context.

```rule
id: ARCH-PC-UC-CANCEL-01
statement: Coroutine cancellation MUST be rethrown before any general catch block.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-UC-CANCEL-01 — Coroutine cancellation MUST be rethrown before any general catch block.
```

Swallowing cancellation causes the coroutine to continue executing after it has been cancelled, and corrupts crash reporting.

```rule
id: ARCH-PC-UC-CANCEL-02
statement: Every inner catch block that logs the exception must also guard against cancellation separately.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-UC-CANCEL-02 — Every inner catch block that logs the exception must also guard against cancellation separately.
```

An outer guard cannot protect against cancellation swallowed by an inner catch.

```rule
id: ARCH-PC-UC-NETWORK-01
statement: Every Flow-based UseCase that performs I/O MUST inject both `CrashReporter` and `NetworkStatusMonitor` via constructor.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-UC-NETWORK-01 — Every Flow-based UseCase that performs I/O MUST inject both `CrashReporter` and `NetworkStatusMonitor` via constructor.
```

```rule
id: ARCH-PC-UC-NETWORK-02
statement: A Flow-based UseCase MUST catch using `catchWithNetworkStatus(crashReporter, networkMonitor) { e -> ... }`, never a raw `.catch { }`.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-UC-NETWORK-02 — A Flow-based UseCase MUST catch using `catchWithNetworkStatus(crashReporter, networkMonitor) { e -> ... }`, never a raw `.catch { }`.
```

A raw `.catch { emit(Outcome.Success(...)) }` compiles, passes tests, and passes lint — but silently swallows real crashes instead of reporting them, and can't distinguish "the device is offline" from "the provider actually failed."

## Side-effects that must not block the result

When a UseCase must return a result immediately while non-critical persistence
(logging, analytics, profile updates) happens in parallel:

```rule
id: ARCH-PC-UC-BG-01
statement: Fire-and-forget side-effects MUST run in a scope that is independent of the caller's scope.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-UC-BG-01 — Fire-and-forget side-effects MUST run in a scope that is independent of the caller's scope.
```

The Outcome MUST be returned before side-effects complete.

```rule
id: ARCH-PC-UC-BG-02
statement: The background scope MUST use a supervisor strategy so that one failed side-effect does not cancel sibling operations.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-UC-BG-02 — The background scope MUST use a supervisor strategy so that one failed side-effect does not cancel sibling operations.
```

## Dependency injection

```rule
id: ARCH-PC-UC-INJECT-01
statement: Constructor injection.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-UC-INJECT-01 — Constructor injection.
```

ViewModels inject UseCases and Orchestrators — never Repositories or DataSources directly.

```rule
id: ARCH-PC-UC-INJECT-02
statement: A UseCase MUST NOT inject another UseCase.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-UC-INJECT-02 — A UseCase MUST NOT inject another UseCase.
```

If UseCase A calls UseCase B, A is an Orchestrator — restructure accordingly.

```rule
id: ARCH-PC-UC-DISP-01
statement: Dispatch to an I/O-appropriate context via an injected dispatcher provider.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-UC-DISP-01 — Dispatch to an I/O-appropriate context via an injected dispatcher provider.
```

Never hardcode a platform dispatcher.

## Naming

| Component | Convention | Example |
|---|---|---|
| UseCase (observing) | `Observe{Noun}UseCase` | `ObserveProfileUseCase` |
| UseCase (one-shot) | `{Verb}{Noun}UseCase` | `FetchVideosUseCase`, `CreateBookingUseCase` |
| Orchestrator | `{Feature}Orchestrator` | `LoginOrchestrator` |

## DI scope

UseCases and Orchestrators are `factory` scoped. See `ARCH-PC-DI`.

## Violations

- A UseCase that only passes data through with no added logic
- An Orchestrator containing validation or calculation logic
- An Orchestrator calling a Repository directly instead of a UseCase
- A UseCase emitting a loading state
- A Flow-based UseCase collapsed to a single suspend call
- Hardcoded dispatcher instead of injected dispatcher provider
- Cancellation exception swallowed inside an inner catch block
- A raw `.catch { emit(Outcome.Success(...)) }` in place of `catchWithNetworkStatus` —
  compiles clean, passes tests, silently swallows crashes
