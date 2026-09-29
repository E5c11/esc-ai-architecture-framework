---
id: PLAT-PY-PERSISTENCE
type: guide
layer: platforms
platform: [python]
architecture: python-app
requires: [ARCH-PY, ARCH-PY-DATASOURCE, PLAT-PY]
related: [ARCH-PY-CONCURRENCY, ARCH-PY-ERROR, PLAT-PY-TESTING, PAT-DATA-ACCESS]
tags: [sqlite, sqlite3, persistence, migrations, transactions, sqlalchemy, wal, row-mapping]
---
# Persistence in Python

Extends: `ARCH-PY-DATASOURCE`

## Choosing the store

- **`sqlite3` (standard library)** is the default for local, single-machine state —
  a control plane's runs, drafts, events. No dependency, real transactions, one file.
- **SQLAlchemy** (Core or ORM) when the schema and query surface are large enough that
  hand-written SQL becomes the maintenance burden, or when a server database
  (PostgreSQL) is a real requirement. The ORM's classes are infrastructure types and
  follow `PYDS-RETURN-01`: they never leave the DataSource.
- **Plain files** (YAML/JSON) only for state that people or other tools read and edit;
  see `PYDS-FILE-01`.

## Rules

```rule
id: PYDB-OWN-01
statement: All SQL for a store MUST live in that store's DataSource module(s); no other layer MUST contain SQL or import `sqlite3`/SQLAlchemy.
type: hard
scope: structure
enforced_by: [ci, reviewer]
violation_message: Violates PYDB-OWN-01 — All SQL for a store MUST live in that store's DataSource module(s); no other layer MUST contain SQL or import `sqlite3`/SQLAlchemy.
```

```rule
id: PYDB-CONN-01
statement: A connection MUST be opened by the composition root (or the DataSource's constructor), closed deterministically (`contextlib.closing`, `with`, or an owning object's `close`), and MUST NOT be shared across threads without serialization.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYDB-CONN-01 — A connection MUST be opened by the composition root (or the DataSource's constructor), closed deterministically (`contextlib.closing`, `with`, or an owning object's `close`), and MUST NOT be shared across threads without serialization.
```

Note that `with sqlite3.connect(...)` manages a *transaction*, not the connection's
lifetime: it commits or rolls back but does not close. Close explicitly.

```rule
id: PYDB-TX-01
statement: Multi-statement writes MUST run in one explicit transaction that commits on success and rolls back on any exception; autocommit MUST NOT be relied on for multi-step invariants.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYDB-TX-01 — Multi-statement writes MUST run in one explicit transaction that commits on success and rolls back on any exception; autocommit MUST NOT be relied on for multi-step invariants.
```

```rule
id: PYDB-MIGRATE-01
statement: Schema changes MUST be ordered, numbered migrations applied inside a transaction at open time and recorded in a schema-version table (or `PRAGMA user_version`); a migration MUST NOT be edited after release, only superseded.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYDB-MIGRATE-01 — Schema changes MUST be ordered, numbered migrations applied inside a transaction at open time and recorded in a schema-version table (or `PRAGMA user_version`); a migration MUST NOT be edited after release, only superseded.
```

```rule
id: PYDB-MAP-01
statement: Row-to-domain mapping MUST be done by one `_to_domain` function per aggregate inside the DataSource, addressing columns by name (`sqlite3.Row` / named columns), never by position.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYDB-MAP-01 — Row-to-domain mapping MUST be done by one `_to_domain` function per aggregate inside the DataSource, addressing columns by name (`sqlite3.Row` / named columns), never by position.
```

```rule
id: PYDB-JSON-01
statement: Structured payloads stored in a text column MUST carry a schema version and be parsed into typed values by the DataSource; a raw `json.loads` result MUST NOT be returned to callers.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates PYDB-JSON-01 — Structured payloads stored in a text column MUST carry a schema version and be parsed into typed values by the DataSource; a raw `json.loads` result MUST NOT be returned to callers.
```

```rule
id: PYDB-FK-01
statement: SQLite foreign-key enforcement MUST be enabled on every connection (`PRAGMA foreign_keys = ON`); it is off by default.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYDB-FK-01 — SQLite foreign-key enforcement MUST be enabled on every connection (`PRAGMA foreign_keys = ON`); it is off by default.
```

## Concurrency notes for SQLite

Use WAL mode (`PRAGMA journal_mode = WAL`) when readers and a writer are concurrent, set
a `busy_timeout` so contention waits instead of failing immediately, and keep write
transactions short. Claims on shared work use a single atomic statement
(`UPDATE ... WHERE status = 'ready' ... RETURNING`) per `PYCONC-CLAIM-01`.

## Testing

Each DataSource has a test module that opens a real store on a `tmp_path` file, runs the
migrations, and exercises every port method including the error translation
(`PYTEST-REAL-01`). A test also opens a database at an *older* schema version and
asserts the migrations bring it forward, and one asserts refusal of a *newer* version
(`PYDS-SCHEMA-01`).
