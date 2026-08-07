---
id: ARCH-BE-PUBLISHING
type: rules
layer: architectures
platform: [backend]
architecture: backend-service
requires: [ARCH-BE, ARCH-BE-ENTITY, ARCH-BE-SERVICE]
related: [ARCH-BE-CONTROLLER, ARCH-BE-PAGINATION, PLAT-BE-JPA]
tags: [publishing, content-lifecycle, draft, admin-content, visibility]
status: active
---

# Content Publishing (Draft/Published Visibility)

## When this applies

A table needs publish visibility control when it holds **admin-authored content** — rows
created and curated by an editor/admin process, not by app users, and not purely derived
from another row. Three categories are explicitly out of scope:

- **User-generated data** (a user's own rating, answer, session, preference) — this is a
  content-authoring concern, not a general visibility concern. Don't gate it.
- **Junction/child tables** (many-to-many join tables, detail tables meaningless without
  their parent row) — these inherit visibility from their parent via the FK relationship;
  giving them their own `is_published` creates a second state to keep in sync for no
  benefit. See `PUB-CHILD-01`.
- **Static, rarely-changing configuration** (a small fixed lookup table unlikely to ever
  need a draft/review cycle) — apply judgment here per project; not every reference table
  needs this, only ones that go through an actual editorial process.

## Rules

```rule
id: PUB-SHAPE-01
statement: Every table in scope MUST carry:
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PUB-SHAPE-01 — Every table in scope MUST carry:
```

```sql
is_published  BOOLEAN     NOT NULL DEFAULT false
published_at  TIMESTAMPTZ                          -- set only when is_published is true
```

`published_at` is **repeatable, not one-shot** — it is overwritten every time the row is
(re-)published, not set once and left immutable. A single-shot "already published, cannot
republish" flag doesn't support the normal edit → review → republish cycle real editorial
content goes through; model this as a status that can flip back and forth, not a
write-once marker.

> Violation: `promoted_at: timestamp?  // set once on dev→prod promotion; presence
> disables re-promote` — blocks republishing an already-published row after further edits.
> Fix: `published_at` updates on every publish action; nothing about a prior publish
> prevents a later one.

```rule
id: PUB-READ-01
statement: Every app-facing read query (list and by-ID) against a table in scope MUST filter `WHERE is_published = true`, unconditionally — no endpoint parameter to opt out, no "show everything" default.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PUB-READ-01 — Every app-facing read query (list and by-ID) against a table in scope MUST filter `WHERE is_published = true`, unconditionally — no endpoint parameter to opt out, no "show everything" default.
```

An admin/internal-only read path that needs to see unpublished rows too is a distinct, separately-authenticated concern, not a query flag on the public endpoint.

```kotlin
fun findByIsPublishedTrue(pageable: Pageable): Page<T>          // paginated case
fun findByIsPublishedTrueAndUpdatedAtAfter(since: Instant, pageable: Pageable): Page<T>  // + ARCH-BE-PAGINATION's since composition
```

> Violation: `videoRepository.findAll(pageable)` on an app-facing endpoint — returns
> unpublished drafts to real users.
> Fix: `videoRepository.findByIsPublishedTrue(pageable)`, or the `since`-composed
> equivalent per `ARCH-BE-PAGINATION`'s `PAG-FILTER-01`.

```rule
id: PUB-CHILD-01
statement: A junction table or a detail/child table with no independent meaning apart from its parent row MUST NOT carry its own `is_published`/`published_at`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PUB-CHILD-01 — A junction table or a detail/child table with no independent meaning apart from its parent row MUST NOT carry its own `is_published`/`published_at`.
```

If it is ever queried independently of its parent (uncommon), the query MUST join back to the parent and filter on the parent's `is_published`, not maintain a parallel flag.

```rule
id: PUB-SCOPE-01
statement: Do not add these columns to user-generated or purely-derived tables.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PUB-SCOPE-01 — Do not add these columns to user-generated or purely-derived tables.
```

If a table's rows are written by app users (not an admin/editorial process) or computed from other tables, `ARCH-BE-PUBLISHING` does not apply to it.

## The write/authoring path is intentionally out of scope here

This doc defines the **schema and the read-side contract** — every unpublished row is
invisible to app-facing reads, full stop. It deliberately does **not** mandate how
`is_published` gets set to `true` in the first place. That's a separate concern layered on
top (an admin dashboard, a CLI publish command, a one-off content-import script defaulting
newly-imported rows to `true`), and its shape varies per project — a project may have no
promote-across-environments mechanism at all yet and still correctly adopt this doc by
having its one data-loading path set the columns directly. Don't block adopting
`PUB-SHAPE-01`/`PUB-READ-01` on designing the full authoring workflow first; the read-side
guarantee is valuable on its own, and the write side can arrive later without requiring a
schema change (the columns already support it).

## Migration template

```sql
-- New table
CREATE TABLE {table} (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- ... domain columns ...
    is_published  BOOLEAN     NOT NULL DEFAULT false,
    published_at  TIMESTAMPTZ
);

-- Existing table
ALTER TABLE {table}
    ADD COLUMN is_published BOOLEAN     NOT NULL DEFAULT false,
    ADD COLUMN published_at TIMESTAMPTZ;
```

Adding these to an already-live table with existing rows needs a deliberate backfill
decision (default new rows to `false`, but what about rows that already exist and are
already being served?) — if a project can add this migration **before** any real data
exists (e.g. ahead of a first content import), that ordering avoids the backfill question
entirely: every row is written by the importer with the correct `is_published` value from
the start.

## Testing

Test that an unpublished row is excluded from every app-facing read (list and by-ID) and
that a published row is included. For paginated endpoints, assert `totalElements`/
`totalPages` reflect only published rows, not the full table. If `PAG-FILTER-01` composition
with a `since` filter also applies, test both filters together — a row that matches `since`
but not `is_published` must still be excluded.
