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

**Rule ARCH-PC-UC-LOGIC-01 (hard):** A UseCase MUST contain business logic that
justifies its existence. A UseCase that only delegates to a Repository with no
added validation, transformation, or decision is pure boilerplate — eliminate it
and have the ViewModel call the Repository directly.

**Rule ARCH-PC-UC-ORCH-01 (hard):** An Orchestrator MUST contain no logic.
If an `if`, `when`, or calculation appears inside an Orchestrator, extract it
to a dedicated UseCase and inject that UseCase.

**Rule ARCH-PC-UC-ORCH-02 (hard):** Orchestrators MUST call UseCases, not
Repositories or DataSources directly.

**Rule ARCH-PC-UC-ORCH-03 (soft):** Orchestrators MAY construct request objects
and pass data between steps. Object creation is coordination, not logic.

## Flow-based vs one-shot

| Use | Return type |
|---|---|
| Observing data that changes over time | `Flow<Outcome<T>>` |
| Single request-response (fetch, write, command) | `suspend` returning `Outcome<T>` |
| Emitting intermediate progress | `Flow<Outcome<T>>` |

**Rule ARCH-PC-UC-RETURN-01 (hard):** A UseCase that observes a stream from the
Repository MUST preserve it as a `Flow`. Never collapse a `Flow` to a single
suspend call — it breaks the reactive chain and stops updates from propagating.

**Rule ARCH-PC-UC-LOADING-01 (hard):** UseCases MUST NOT emit loading states.
The ViewModel sets loading state before invoking the UseCase and clears it on result.

## Error handling

The UseCase layer is the last opportunity to intercept and handle unexpected
technical exceptions before they reach the ViewModel.

**Rule ARCH-PC-UC-ERROR-01 (hard):** The UseCase MUST catch at its boundary and
either translate unexpected exceptions to domain exceptions, or pass through
domain exceptions that were already translated by the DataSource.

**Rule ARCH-PC-UC-ERROR-02 (hard):** The fallback exception in the catch handler
MUST be a domain-specific exception named after the operation (e.g. `FetchVideosException`),
not a generic unknown exception. Generic exceptions lose diagnostic context.

**Rule ARCH-PC-UC-CANCEL-01 (hard):** Coroutine cancellation MUST be rethrown
before any general catch block. Swallowing cancellation causes the coroutine to
continue executing after it has been cancelled, and corrupts crash reporting.

**Rule ARCH-PC-UC-CANCEL-02 (hard):** Every inner catch block that logs the
exception must also guard against cancellation separately. An outer guard cannot
protect against cancellation swallowed by an inner catch.

**Rule ARCH-PC-UC-NETWORK-01 (hard):** Every Flow-based UseCase that performs
I/O MUST inject both `CrashReporter` and `NetworkStatusMonitor` via constructor.

**Rule ARCH-PC-UC-NETWORK-02 (hard):** A Flow-based UseCase MUST catch using
`catchWithNetworkStatus(crashReporter, networkMonitor) { e -> ... }`, never a
raw `.catch { }`. A raw `.catch { emit(Outcome.Success(...)) }` compiles, passes
tests, and passes lint — but silently swallows real crashes instead of
reporting them, and can't distinguish "the device is offline" from "the
provider actually failed."

## Side-effects that must not block the result

When a UseCase must return a result immediately while non-critical persistence
(logging, analytics, profile updates) happens in parallel:

**Rule ARCH-PC-UC-BG-01 (hard):** Fire-and-forget side-effects MUST run in a
scope that is independent of the caller's scope. The Outcome MUST be returned
before side-effects complete.

**Rule ARCH-PC-UC-BG-02 (hard):** The background scope MUST use a supervisor
strategy so that one failed side-effect does not cancel sibling operations.

## Dependency injection

**Rule ARCH-PC-UC-INJECT-01 (hard):** Constructor injection. ViewModels inject
UseCases and Orchestrators — never Repositories or DataSources directly.

**Rule ARCH-PC-UC-INJECT-02 (hard):** A UseCase MUST NOT inject another UseCase.
If UseCase A calls UseCase B, A is an Orchestrator — restructure accordingly.

**Rule ARCH-PC-UC-DISP-01 (hard):** Dispatch to an I/O-appropriate context via
an injected dispatcher provider. Never hardcode a platform dispatcher.

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
