---
id: ARCH-BE-PAGINATION
type: rules
layer: architectures
platform: [backend]
architecture: backend-service
requires: [ARCH-BE, ARCH-BE-SERVICE, ARCH-BE-CONTROLLER]
related: [ARCH-BE-ENTITY, ARCH-BE-ERROR, PLAT-BE-SPRING, PLAT-BE-JPA]
tags: [pagination, list-endpoints, offset, page, dto-boundary, ordering]
status: active
---

# Pagination

## When to paginate

Not every list endpoint needs pagination — only endpoints whose result set scales with
data volume the caller doesn't control (content grows over time, more users create more
rows). A small, fixed enumeration (status types, category lookups, a handful of
configuration rows) does not benefit from pagination; the ceremony adds nothing when
there are, and will only ever be, a few dozen rows at most.

```rule
id: PAG-SCOPE-01
statement: Before adding pagination to a list endpoint, check whether the underlying table is bounded (a fixed taxonomy/enumeration) or unbounded (grows with content/user volume).
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PAG-SCOPE-01 — Before adding pagination to a list endpoint, check whether the underlying table is bounded (a fixed taxonomy/enumeration) or unbounded (grows with content/user volume).
```

Paginate only the unbounded ones. Paginating a bounded reference table is unnecessary complexity; leaving an unbounded one unpaginated is an unbounded-response and scrape/cost-amplification risk.

## Offset vs. cursor

This architecture defaults to offset-based pagination (`page`/`size`), not cursor-based.
Offset is simpler to implement and reason about, and is the right choice for read-mostly
or infrequently-mutated data. Cursor-based pagination matters when the underlying set is
high-churn (continuously appended, e.g. an activity feed) — offset pagination on such data
can skip or repeat rows as new items are inserted ahead of the current page. If a
project's data is high-churn, that's a deliberate exception to document, not the default.

## Shape

```rule
id: PAG-SHAPE-01
statement: A paginated endpoint's request and response types MUST be plain, framework-free data classes — never Spring Data's `Pageable`/`Page<T>` directly on the controller signature or in a DTO.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PAG-SHAPE-01 — A paginated endpoint's request and response types MUST be plain, framework-free data classes — never Spring Data's `Pageable`/`Page<T>` directly on the controller signature or in a DTO.
```

Spring Data types are a persistence-layer concern; leaking them into the API contract couples the wire format to the JPA/Spring Data version, and if the project has a shared multiplatform contracts layer, Spring Data types cannot cross into it at all (JVM-only).

```kotlin
data class PageRequest(val page: Int, val size: Int)
data class PageResponse<T>(
    val items: List<T>,
    val page: Int,
    val size: Int,
    val totalElements: Long,
    val totalPages: Int,
)
```

Map Spring Data's `Page<T>` to this shape at the service/controller boundary — see
`ARCH-BE-SERVICE`'s `SVC-RETURN-01` (services return DTOs, never entities); the same
boundary-mapping discipline applies to the paginated wrapper, not just the item type.

```kotlin
fun <T> org.springframework.data.domain.Page<T>.toPageResponse(): PageResponse<T> = PageResponse(
    items = content,
    page = number,
    size = size,
    totalElements = totalElements,
    totalPages = totalPages,
)
```

**Naming collision:** Spring Data's own `org.springframework.data.domain.PageRequest`
shares a name with the contract-facing `PageRequest` above. Alias-import one of them at
every call site that uses both: `import org.springframework.data.domain.PageRequest as
SpringPageRequest`.

## Size limits

```rule
id: PAG-SIZE-01
statement: The server MUST enforce a maximum page size regardless of what the caller requests.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PAG-SIZE-01 — The server MUST enforce a maximum page size regardless of what the caller requests.
```

An unbounded caller-supplied `size` defeats the entire purpose of pagination — it becomes an optional courtesy, not a hardening control.

```kotlin
val size = requestedSize.coerceIn(1, MAX_PAGE_SIZE)
```

Pick `MAX_PAGE_SIZE` and a default page size deliberately per project (a reasonable
starting point: default 20, max 100) — there is no universal correct number, only a
universal requirement that one exists and is enforced server-side.

## Deterministic ordering

```rule
id: PAG-ORDER-01
statement: Every paginated query MUST specify an explicit, stable sort order (`ORDER BY id` or another column guaranteed unique and immutable).
type: hard
scope: testing
enforced_by: [reviewer]
violation_message: Violates PAG-ORDER-01 — Every paginated query MUST specify an explicit, stable sort order (`ORDER BY id` or another column guaranteed unique and immutable).
```

Offset pagination without a deterministic order silently repeats or skips rows across pages when the underlying result order isn't guaranteed by the database — this is invisible in manual testing (small datasets often happen to come back in insertion order) and only surfaces as missing/duplicate data once the table is large enough for the database to choose a different physical scan order.

```kotlin
val pageable = PageRequest.of(page, size, Sort.by("id"))
```

> Violation: `PageRequest.of(page, size)` with no `Sort` — relies on implicit/undefined
> ordering.
> Fix: always pass an explicit `Sort` referencing a unique, immutable column.

## Interaction with filtered/incremental queries

A paginated endpoint often also accepts a filter parameter (an incremental-sync cursor, a
search term, a status filter). Pagination MUST compose with the filter, not be bypassed by
it — apply the filter first, then paginate the filtered result set unconditionally. An
endpoint where "filter present → return everything unpaginated, filter absent →
paginate" reopens exactly the unbounded-response risk `PAG-SIZE-01` exists to close, since
a caller can simply supply a filter value guaranteed to match everything (or omit a value
the filter would otherwise narrow on) to get an unpaginated dump.

```rule
id: PAG-FILTER-01
statement: A list endpoint accepting both pagination parameters and a filter parameter MUST apply pagination to every response, regardless of which filter values are present.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PAG-FILTER-01 — A list endpoint accepting both pagination parameters and a filter parameter MUST apply pagination to every response, regardless of which filter values are present.
```

Never expose an alternate, unpaginated response shape gated on a filter parameter's presence.

If a project has a domain-specific incremental sync architecture with requirements beyond
this general composition rule, its own framework layer is the right place to document
that — see, for example, `ampm-backend-framework`'s pagination extension for the
`since`-cursor-specific case.

## Testing

Paginated endpoint tests must cover: page size defaults, the server-enforced max-size cap
(request a larger size than the max, assert it's clamped, not rejected or honored
as-requested), stable ordering across two consecutive calls with no intervening writes,
and — where a filter parameter coexists — that filtered results are still paginated
(assert `totalPages` reflects the filtered count, not the full table).
