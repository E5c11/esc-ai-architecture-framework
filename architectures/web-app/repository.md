---
id: ARCH-WEB-APP-REPOSITORY
type: guide
layer: architectures
platform: [web]
architecture: [web-app]
requires: [ARCH-WEB-APP, ARCH-WEB-APP-DATASOURCE, CORE-SSOT, PAT-DATA-ACCESS, PAT-OUTCOME]
related: [ARCH-WEB-APP-DOMAIN, ARCH-PC-REPOSITORY]
tags: [repository, ssot, coordination, cache, multi-source]
status: active
---

# Repository Layer

## Responsibility

Coordinate several DataSources behind one source of truth (`CORE-SSOT`) for one
entity.

The Repository knows which source is authoritative and when to consult the others.
It decides when to fetch and how to update a cache after a successful fetch. That is
all. No business rules (a UseCase), no provider types (a DataSource).

This restates `ARCH-PC-REPOSITORY` for a web app.

## When to create a Repository

The threshold is `ARCH-WEB-APP-REPO-01`, owned by the overview: a Repository exists
only when one entity is assembled from more than one DataSource. A Repository
wrapping a single DataSource adds a layer that does nothing, and MUST NOT be
introduced.

Cases that qualify:

- A live source and a cache: a Firestore subscription and a locally stored copy the
  app shows while the live read is in flight or offline.
- Two providers that both hold part of an entity: a record read from one provider and
  its attachments from another.
- A current value and its history, read from different sources, presented as one.

Cases that do not: a feature with one provider; a UseCase that calls two unrelated
DataSources for two different entities (that is a UseCase coordinating, not a
Repository).

## Structure

```
features/{feature}/data/
├── {Entity}Repository.ts           Interface
└── Default{Entity}Repository.ts    Implementation; constructor takes DataSource interfaces
```

## What a Repository talks to

The composition module builds the DataSources and the Repository and passes the
first to the second (`ARCH-WEB-APP-DEP-06`).

## Return types

"Loading" is a UI state, owned by the hook. A Repository that exposes `{ data,
loading, error }` has pushed presentation down a layer.

## SSOT enforcement

```rule
id: ARCH-WEB-APP-REP-SSOT-01
statement: A Repository MUST designate one DataSource as authoritative for each entity; every other copy MUST be derived, rebuildable, and labelled as such, and consumers MUST read through the Repository, never from a secondary source directly.
type: hard
scope: behavior
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-REP-SSOT-01 — A Repository MUST designate one DataSource as authoritative for each entity; every other copy MUST be derived, rebuildable, and labelled as such, and consumers MUST read through the Repository, never from a secondary source directly.
```

```rule
id: ARCH-WEB-APP-REP-SSOT-02
statement: A Repository MUST update a secondary copy only from a successful read of the authoritative source, and MUST NOT let a failed or partial read overwrite it.
type: hard
scope: behavior
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-REP-SSOT-02 — A Repository MUST update a secondary copy only from a successful read of the authoritative source, and MUST NOT let a failed or partial read overwrite it.
```

Standard coordination for a live source with a cache:

```
read:   subscribe to the authoritative source → on each success, write the cache →
        deliver the value to the consumer.
        While the first emission is pending, deliver the cached value, marked stale.
write:  send to the authoritative source → on success, update the cache → return.
        A failed write leaves the cache unchanged and returns the error.
```

A value delivered from the cache while the authoritative read is pending is
labelled stale in the domain value (a field, not a separate type), so the hook can
show it as such and no consumer mistakes it for current data.

## Error handling

Error translation happened in the DataSource (`ARCH-WEB-APP-ERR-MAP-01`); a
Repository receives `AppError` values and does not translate again.

```rule
id: ARCH-WEB-APP-REP-FALLBACK-01
statement: When a fallback strategy is exhausted, a Repository MUST return the original error outcome, and MUST NOT swallow it or substitute an empty value.
type: hard
scope: error-handling
evidence: unproven
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-REP-FALLBACK-01 — When a fallback strategy is exhausted, a Repository MUST return the original error outcome, and MUST NOT swallow it or substitute an empty value.
```

A fallback to a cache is a decision, so it is visible: the value is marked stale,
and the error that triggered the fallback is still logged. An empty list returned
in place of an error looks like "no data" and is the false-success failure
`PAT-OUTCOME` exists to prevent.

## Testing

A Repository is tested against the fakes of its DataSources (`ARCH-WEB-APP-DS-TEST-01`),
which makes each coordination case a plain in-memory test: authoritative source
fails and the cache answers, the cache is updated only on success, a failed write
leaves the cache unchanged.

## Violations

- A Repository over a single DataSource
- A provider SDK imported in a Repository
- `{ data, loading, error }` or any resource wrapper returned from a Repository
- A consumer reading a cache directly instead of through the Repository
- A cache overwritten from a failed or partial read
- An error replaced by an empty value
- A DataSource constructed inside the Repository
