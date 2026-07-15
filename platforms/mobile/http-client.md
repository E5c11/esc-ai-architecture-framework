---
id: PLAT-MOB-HTTP
type: guide
layer: platform
platform: [mobile]
architecture: [pragmatic-clean]
requires: [ARCH-PC-DATASOURCE, ARCH-PC-ERR-CLASSES, CORE-DI, PLAT-MOB-KOTLIN]
related: [ARCH-PC-ERROR-FLOW, PAT-OUTCOME, PLAT-MOB-KMP-IOS]
tags: [http, ktor, api-client, rest, serialization, auth-header, retry, timeout]
---

# HTTP Client Layer (Mobile → Backend)

The HTTP client is infrastructure behind DataSource interfaces. Ktor or an owned wrapper
such as `arrow-http` may implement transport policy, but it never becomes a domain API.

## Client ownership and source sets

Keep request/response DTOs, serialization and provider-neutral client policy in common or
a deliberate shared REST source set. Engine dependencies remain platform-specific:

| Target | Engine responsibility |
|---|---|
| Android/JVM | Android/JVM-compatible engine selected by the project |
| iOS | Ktor Darwin engine in `iosMain` |
| wasmJs | Browser-compatible Ktor engine |

**Rule PLAT-MOB-HTTP-ENGINE-01 (hard):** Every configured target MUST provide exactly
one compatible engine. A transitive engine must still be proven by a target compile/link test.

**Rule PLAT-MOB-HTTP-SS-01 (hard):** Platform engine classes and platform credential
APIs MUST NOT appear in common client policy or DataSource interfaces.

## Configuration

Configure one long-lived client per environment with base URL, content negotiation,
serialization, timeouts and approved logging. Secrets and bearer tokens must never be logged.

**Rule PLAT-MOB-HTTP-DI-01 (hard):** The configured client MUST be a Koin `single` and
injected into DataSources. DataSources must not construct clients per request.

**Rule PLAT-MOB-HTTP-CONFIG-01 (hard):** Base URLs and timeout values MUST come from
environment/build configuration, not inline request code.

## Authentication and refresh

Attach credentials through an injected header/token provider. Refresh coordination belongs
to a client plugin or `AuthRefresher`, not individual DataSources. Only one refresh may run
for concurrent unauthorized responses; waiting requests reuse its result.

**Rule PLAT-MOB-HTTP-AUTH-01 (hard):** DataSources MUST NOT read secure storage or
implement token refresh directly.

**Rule PLAT-MOB-HTTP-AUTH-02 (hard):** A refreshed request may be replayed at most once.
Refresh failure maps to unauthorized/session-expired rather than an infinite retry loop.

## Error mapping and retry

The transport layer classifies connectivity, timeout, protocol and serialization failures.
The DataSource maps that classification to the domain errors defined by
`ARCH-PC-ERR-CLASSES`.

Recommended status semantics: 401 unauthorized, 403 forbidden, 404 not found, 409 conflict,
429 throttled and 5xx server failure. Preserve response/request correlation identifiers for
diagnostics without exposing sensitive bodies.

**Rule PLAT-MOB-HTTP-ERR-01 (hard):** HTTP and Ktor exceptions MUST NOT escape the
DataSource boundary.

**Rule PLAT-MOB-HTTP-RETRY-01 (hard):** Retry only idempotent operations, or writes with
an explicit idempotency mechanism. Never automatically retry authentication, validation,
permission or ordinary 4xx failures.

**Rule PLAT-MOB-HTTP-CANCEL-01 (hard):** Coroutine cancellation MUST be rethrown before
broad exception mapping.

## Testing

Use a fake transport or Ktor mock engine to verify request shape, headers, serialization,
status mapping, retry limits and refresh coalescing. Add platform smoke tests that create the
real engine; common-only tests cannot prove Darwin/browser engine availability.

## Validation checklist

- [ ] One compatible engine exists per target; iOS client construction/linking is tested.
- [ ] Client is a `single`; DataSources receive it through DI.
- [ ] Tokens and secrets are absent from logs.
- [ ] Concurrent 401s trigger one refresh and at most one replay per request.
- [ ] Cancellation, timeout, offline, every handled status and malformed JSON are tested.
- [ ] Non-idempotent writes are not retried without idempotency protection.
- [ ] No transport/provider type crosses the DataSource boundary.
