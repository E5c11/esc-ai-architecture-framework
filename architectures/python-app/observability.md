---
id: ARCH-PY-OBSERVABILITY
type: rules
layer: architectures
platform: [python]
architecture: python-app
requires: [ARCH-PY, CORE-ERROR]
related: [ARCH-PY-POLICY, ARCH-PY-GATEWAY, ARCH-PY-ERROR, ARCH-PY-COMPOSITION, PLAT-PY]
tags: [logging, telemetry, audit, privacy, opt-in, observability, events, redaction]
---
# Observability, Audit, and Telemetry

Three different things are called "logging"; keep them separate, because they have
different audiences, retention, and privacy rules.

| Kind | Audience | Default | Lives in |
|---|---|---|---|
| **Diagnostic logging** | The developer running or debugging the program | On, to stderr / a local file, at `WARNING`+ | stdlib `logging` |
| **Audit / run record** | The user (and their team) asking "what did it do and why?" | On, **local**, part of the product | A DataSource (events, run artifacts) |
| **Telemetry** | The tool's maintainers, in aggregate | **Off** until explicitly enabled | A Gateway behind a port |

## Diagnostic logging

```rule
id: PYOBS-LOG-01
statement: Library and application code MUST log through a module-level `logging.getLogger(__name__)` and MUST NOT configure handlers, levels, or formats; only the composition root configures logging.
type: hard
scope: behavior
enforced_by: [ci, reviewer]
violation_message: Violates PYOBS-LOG-01 — Library and application code MUST log through a module-level `logging.getLogger(__name__)` and MUST NOT configure handlers, levels, or formats; only the composition root configures logging.
```

```rule
id: PYOBS-LOG-02
statement: Diagnostic messages MUST NOT be used as the program's output; user-facing output goes through the entrypoint's renderer, and `print()` MUST NOT be used for diagnostics.
type: hard
scope: behavior
enforced_by: [ci, reviewer]
violation_message: Violates PYOBS-LOG-02 — Diagnostic messages MUST NOT be used as the program's output; user-facing output goes through the entrypoint's renderer, and `print()` MUST NOT be used for diagnostics.
```

```rule
id: PYOBS-LOG-03
statement: Log calls MUST use lazy formatting (`logger.info("... %s", value)`) or structured extras, and an exception MUST be logged with its traceback (`logger.exception` or `exc_info=True`) exactly once, at the top-level handler or the boundary that swallows it.
type: hard
scope: behavior
enforced_by: [ci, reviewer]
violation_message: Violates PYOBS-LOG-03 — Log calls MUST use lazy formatting (`logger.info("... %s", value)`) or structured extras, and an exception MUST be logged with its traceback (`logger.exception` or `exc_info=True`) exactly once, at the top-level handler or the boundary that swallows it.
```

Logging and re-raising at every layer produces the same traceback five times and
buries the signal.

## Redaction

```rule
id: PYOBS-REDACT-01
statement: Secrets, tokens, credentials, and full provider payloads MUST NOT appear in logs, run records, error messages, or telemetry; values crossing into any of these MUST pass through one redaction function.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYOBS-REDACT-01 — Secrets, tokens, credentials, and full provider payloads MUST NOT appear in logs, run records, error messages, or telemetry; values crossing into any of these MUST pass through one redaction function.
```

## Audit and run records

A program whose value is trust in what it did keeps a **run record**: which procedure
ran, each stage's outcome, the observable evidence for each gate (exit codes,
artifact paths), and what the user was asked and answered. It is written by the
application layer through a port and stored by a DataSource. It is a product feature,
not a debugging aid.

```rule
id: PYOBS-AUDIT-01
statement: Every stage outcome MUST be recorded to the run record through a port, including gate verdicts and their observable evidence; a stage MUST NOT report a result that was not recorded.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYOBS-AUDIT-01 — Every stage outcome MUST be recorded to the run record through a port, including gate verdicts and their observable evidence; a stage MUST NOT report a result that was not recorded.
```

```rule
id: PYOBS-AUDIT-02
statement: Run records MUST be append-only events with a stable, versioned schema; a record MUST NOT be rewritten to change what happened.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYOBS-AUDIT-02 — Run records MUST be append-only events with a stable, versioned schema; a record MUST NOT be rewritten to change what happened.
```

## Telemetry

```rule
id: PYOBS-TELE-01
statement: Telemetry MUST be off by default, enabled only by an explicit user action, and revocable; nothing MUST be sent before consent, and the consent state MUST be checked at the Gateway, not at each call site.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYOBS-TELE-01 — Telemetry MUST be off by default, enabled only by an explicit user action, and revocable; nothing MUST be sent before consent, and the consent state MUST be checked at the Gateway, not at each call site.
```

```rule
id: PYOBS-TELE-02
statement: Telemetry payloads MUST be built from an allow-list of aggregate, non-identifying fields (counts, outcomes, durations, stage names); free text, file paths, repository names, code, and prompts MUST NOT be included.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYOBS-TELE-02 — Telemetry payloads MUST be built from an allow-list of aggregate, non-identifying fields (counts, outcomes, durations, stage names); free text, file paths, repository names, code, and prompts MUST NOT be included.
```

```rule
id: PYOBS-TELE-03
statement: The exact payload that would be sent MUST be inspectable by the user before and after enabling telemetry (a preview command or a local copy of what was sent).
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYOBS-TELE-03 — The exact payload that would be sent MUST be inspectable by the user before and after enabling telemetry (a preview command or a local copy of what was sent).
```

```rule
id: PYOBS-SHARE-01
statement: Sharing richer evidence (a run trace, a rated decision) MUST be a separate, explicit, per-item opt-in distinct from aggregate telemetry, and MUST be attributable and human-reviewed on the receiving side.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYOBS-SHARE-01 — Sharing richer evidence (a run trace, a rated decision) MUST be a separate, explicit, per-item opt-in distinct from aggregate telemetry, and MUST be attributable and human-reviewed on the receiving side.
```

A project that has not yet earned users' trust should not ask for it by default; see
`ARCH-PY-POLICY` for why contribution is a reviewed path, not a data feed.

## Testing

Assert on emitted run-record events and on the telemetry payload builder (a pure
function over an outcome), not on log text. A test that greps log output is testing a
formatting detail.
