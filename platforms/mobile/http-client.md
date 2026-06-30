---
id: PLAT-MOB-HTTP
type: guide
layer: platform
platform: [mobile]
architecture: [pragmatic-clean]
requires: [ARCH-PC-DATASOURCE, CORE-DI, PLAT-MOB-KOTLIN]
related: [ARCH-PC-ERROR-FLOW, ARCH-PC-ERR-CLASSES, PAT-OUTCOME]
tags: [http, ktor, api-client, rest, serialization, auth-header, retry, timeout]
status: stub
---

# HTTP Client Layer (Mobile → Backend)

> **TODO:** This document is a stub. See `todo/missing-files.md` for context.
>
> **Context:** Firebase SDK is being replaced by a Spring Boot backend.
> The mobile platform will call the backend over HTTP. This document covers
> the mobile-side HTTP client — not the backend server. Backend patterns live
> in `platforms/backend/` and `architectures/backend-service/`.

## What this document must cover

- HTTP client library choice and rationale (Ktor for KMP — confirm)
- Client configuration: base URL, timeouts, logging, serialization (kotlinx.serialization)
- Authentication: how auth tokens are attached to requests (interceptor / plugin pattern)
- Token refresh: how expired tokens are handled without leaking auth logic into DataSources
- DataSource boundary: HTTP client is a provider detail; DataSource translates HTTP responses to domain types
- Error mapping: HTTP error codes → domain exceptions (401, 403, 404, 5xx)
- Retry strategy: which errors are retried, which fail immediately
- KMP source set placement: where the client is declared for Android vs iOS vs wasmJs
- DI registration: how the configured client is injected (single, qualifiers)
- Testing: how to fake/mock the HTTP client in DataSource unit tests
