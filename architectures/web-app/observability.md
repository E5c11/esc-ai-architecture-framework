---
id: ARCH-WEB-APP-OBS
type: rules
layer: architectures
platform: [web]
architecture: [web-app]
requires: [ARCH-WEB-APP, ARCH-WEB-APP-COMPOSITION, ARCH-WEB-APP-ERR-FLOW, CORE-DI]
related: [ARCH-WEB-APP-DATASOURCE, ARCH-PY-OBSERVABILITY, PAT-ANALYTICS-EVENTS]
tags: [observability, logging, redaction, error-reporting, audit, correlation, analytics, privacy]
status: active
---

# Observability

Three different things are called "logging" and have different audiences and privacy
rules. Keep them apart.

| Kind | Audience | Lives in |
|---|---|---|
| **Diagnostic logging** | The developer debugging, in the browser console or the server log | An injected logger |
| **Operation record** | The user asking "what did the system just do, and did it work?" | Data a DataSource stores and the UI shows |
| **Error reporting and analytics** | The maintainers, in aggregate | An injected reporter or tracker |

This restates `ARCH-PY-OBSERVABILITY` for a web app.

## Diagnostic logging

```rule
id: ARCH-WEB-APP-OBS-LOG-01
statement: Code MUST log through a logger received from the composition and MUST NOT call `console.*` directly; only the composition module chooses the logger, its level and its destination.
type: hard
scope: behavior
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-OBS-LOG-01 — Code MUST log through a logger received from the composition and MUST NOT call `console.*` directly; only the composition module chooses the logger, its level and its destination.
```

A direct `console.log` in a UseCase is a decision about output made in the wrong layer.
Behind an injected logger a test can assert on what was logged, the server can write
structured entries, and the browser can drop debug output in production.

```rule
id: ARCH-WEB-APP-OBS-LOG-02
statement: A log entry MUST be a structured record (an event name plus named fields) and MUST NOT be an interpolated sentence, and server code MUST emit severity in the form its log service reads.
type: hard
scope: behavior
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-OBS-LOG-02 — A log entry MUST be a structured record (an event name plus named fields) and MUST NOT be an interpolated sentence, and server code MUST emit severity in the form its log service reads.
```

```typescript
// ❌ Wrong — a sentence nobody can query
log.info(`Snapshot built for ${region} with ${rows} rows`);

// ✅ Correct — fields can be filtered and counted
log.info('snapshot.built', { region, rows, durationMs });
```

The once-only rule for logging an error is `ARCH-WEB-APP-EFLOW-LOG-01`.

## Redaction

(`ARCH-WEB-APP-OBS-REDACT-01` now lives in `ARCH-WEB-APP`, because it applies to every project.)

An app that stores customer records will see those records in every error that
mentions one. A parse failure on a row must name the row's identity (a record id), not
print its contents. One redaction function, applied where a value enters a log, a
report or an event, is the only way this stays true after the tenth contributor.

## Operation records

```rule
id: ARCH-WEB-APP-OBS-RECORD-01
statement: An operation that runs outside the page (a build, an import, a scheduled fetch, a function) MUST record its outcome as data (what ran, when, against which inputs and versions, and whether it succeeded), and the UI MUST be able to show that record, including a failure with its reason.
type: hard
scope: behavior
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-OBS-RECORD-01 — An operation that runs outside the page (a build, an import, a scheduled fetch, a function) MUST record its outcome as data (what ran, when, against which inputs and versions, and whether it succeeded), and the UI MUST be able to show that record, including a failure with its reason.
```

A failure that exists only in a server log is invisible to the person who needs to know
it happened. "The last build ran at 14:02 and failed: column X is missing" on the
screen is both the audit trail and the support tool.

## Error reporting and correlation

```rule
id: ARCH-WEB-APP-OBS-REPORT-01
statement: Defects MUST be reported through an injected reporter that tags the release, deduplicates, and is a no-op in tests and previews, and the reporter MUST receive only redacted data.
type: hard
scope: behavior
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-OBS-REPORT-01 — Defects MUST be reported through an injected reporter that tags the release, deduplicates, and is a no-op in tests and previews, and the reporter MUST receive only redacted data.
```

## Analytics

The philosophy (which events, how many) is `PAT-ANALYTICS-EVENTS`.

Checking consent in the adapter, once, means no call site can forget it. Hooks receive
the tracker through the composition (`ARCH-WEB-APP-HOOK-ANALYTICS-01`).

## Violations

- `console.log` in a UseCase, a Hook or a DataSource
- A log line built by interpolating a record's fields into a sentence
- A customer name or phone number in an error message or a log entry
- A build or import that fails only in a server log
- An operation record edited after the fact
- An error reported with the raw payload attached
- An analytics event carrying free text
