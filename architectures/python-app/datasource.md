---
id: ARCH-PY-DATASOURCE
type: rules
layer: architectures
platform: [python]
architecture: python-app
requires: [ARCH-PY, PAT-DATA-ACCESS, CORE-SSOT]
related: [ARCH-PY-USECASE, ARCH-PY-GATEWAY, ARCH-PY-ERROR, PLAT-PY-PERSISTENCE]
tags: [datasource, persistence, sqlite, repository, store, ssot, migrations, files]
---
# DataSource Layer (Persistence)

## Responsibility

A DataSource implements a persistence port for exactly one storage technology — a
SQLite database, a directory of YAML files, a key-value store — and translates between
that technology's shapes (rows, documents, files) and domain values. It contains no
business rules.

This is the `PAT-DATA-ACCESS` pattern. In Python ecosystems the same idea is often
called a *Repository* or a *Store*; this architecture uses **DataSource** for the
single-technology implementation and reserves **Repository** for the optional
coordinator described below.

## Rules

```rule
id: PYDS-PORT-01
statement: A DataSource MUST implement a Protocol declared in the application package and MUST be constructed only at the composition root.
type: hard
scope: di
enforced_by: [ci, reviewer]
violation_message: Violates PYDS-PORT-01 — A DataSource MUST implement a Protocol declared in the application package and MUST be constructed only at the composition root.
```

```rule
id: PYDS-ONE-01
statement: A DataSource MUST wrap exactly one storage technology; two technologies MUST be two DataSources behind two ports.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYDS-ONE-01 — A DataSource MUST wrap exactly one storage technology; two technologies MUST be two DataSources behind two ports.
```

```rule
id: PYDS-RETURN-01
statement: DataSource methods MUST return domain values, never rows, cursors, `sqlite3.Row`, ORM instances, raw parsed dicts, or file handles.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates PYDS-RETURN-01 — DataSource methods MUST return domain values, never rows, cursors, `sqlite3.Row`, ORM instances, raw parsed dicts, or file handles.
```

Mapping between storage shape and domain value happens in one private function pair
per aggregate (`_to_domain`, `_to_row`) inside the DataSource, so a schema change has
exactly one place to update.

```rule
id: PYDS-ERROR-01
statement: A DataSource MUST translate storage-specific exceptions into the project's domain/persistence error types at its own boundary; storage exceptions MUST NOT propagate to callers.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PYDS-ERROR-01 — A DataSource MUST translate storage-specific exceptions into the project's domain/persistence error types at its own boundary; storage exceptions MUST NOT propagate to callers.
```

```rule
id: PYDS-SSOT-01
statement: Each piece of durable state MUST have exactly one authoritative DataSource; any other copy MUST be derived, rebuildable, and labeled as such.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYDS-SSOT-01 — Each piece of durable state MUST have exactly one authoritative DataSource; any other copy MUST be derived, rebuildable, and labeled as such.
```

This includes files that mirror database state (or the reverse): one is the source of
truth, the other is a cache or an export, and the code must say which (`CORE-SSOT`).

## Schema ownership and migration

```rule
id: PYDS-SCHEMA-01
statement: A SQL-backed DataSource MUST own its schema, carry an explicit schema version in the database, and apply forward-only, ordered migrations at open time; it MUST refuse to run against a newer schema than it understands.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYDS-SCHEMA-01 — A SQL-backed DataSource MUST own its schema, carry an explicit schema version in the database, and apply forward-only, ordered migrations at open time; it MUST refuse to run against a newer schema than it understands.
```

```rule
id: PYDS-SQL-01
statement: SQL MUST use bound parameters; string formatting or concatenation of values into SQL MUST NOT be used.
type: hard
scope: behavior
enforced_by: [ci, reviewer]
violation_message: Violates PYDS-SQL-01 — SQL MUST use bound parameters; string formatting or concatenation of values into SQL MUST NOT be used.
```

`ruff`'s `S608` flags the common cases.

```rule
id: PYDS-TX-01
statement: A DataSource MUST NOT open, commit, or roll back a transaction inside a single-row method the caller may compose; transaction scope is owned by the unit of work the use case opens.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYDS-TX-01 — A DataSource MUST NOT open, commit, or roll back a transaction inside a single-row method the caller may compose; transaction scope is owned by the unit of work the use case opens.
```

## File-backed state

Plain files (YAML manifests, JSON checkpoints) are a legitimate DataSource when humans
or other tools read them, but they carry the same obligations as a database:

```rule
id: PYDS-FILE-01
statement: A file-backed DataSource MUST write atomically (write to a temporary file in the same directory, then `os.replace`) and MUST validate what it reads against a declared schema, returning a domain error for malformed input.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYDS-FILE-01 — A file-backed DataSource MUST write atomically (write to a temporary file in the same directory, then `os.replace`) and MUST validate what it reads against a declared schema, returning a domain error for malformed input.
```

```rule
id: PYDS-FILE-02
statement: A file-backed DataSource MUST resolve every path against an explicit root it is given and MUST reject paths that escape it.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PYDS-FILE-02 — A file-backed DataSource MUST resolve every path against an explicit root it is given and MUST reject paths that escape it.
```

## When a Repository is justified

The default is: the use case depends on the DataSource's port directly. Introduce a
**Repository** — a class that coordinates two or more DataSources behind one port —
only when a single logical query truly needs several sources (a local cache plus a
remote API, say) and the coordination logic (which is authoritative, when to refresh)
is worth naming. It is a coordinator, not a wrapper: a Repository over one
DataSource is dead weight.

```rule
id: PYDS-REPO-01
statement: A Repository layer MUST exist only where it coordinates two or more DataSources; a Repository wrapping a single DataSource MUST NOT be introduced.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PYDS-REPO-01 — A Repository layer MUST exist only where it coordinates two or more DataSources; a Repository wrapping a single DataSource MUST NOT be introduced.
```

## Testing

Test a DataSource against **real** infrastructure — a temporary SQLite file, a
`tmp_path` directory — not a mock (`QG-TEST-SCOPE-02`). Use cases test against fakes
of the port, so the two suites together cover both the logic and the mapping.
