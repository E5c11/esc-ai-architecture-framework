---
id: ARCH-WEB-APP-DATASOURCE
type: guide
layer: architectures
platform: [web]
architecture: [web-app]
requires: [ARCH-WEB-APP, ARCH-WEB-APP-ERR-CLASSES, PAT-DATA-ACCESS, PAT-OUTCOME, PAT-OBSERVER, CORE-NAMING]
related: [ARCH-WEB-APP-REPOSITORY, ARCH-WEB-APP-DOMAIN, ARCH-PC-DATASOURCE, PLAT-WEB-HTTP, PLAT-WEB-FORMS]
tags: [datasource, provider, mapping, parsing, outcome, subscription, firestore, rest, postgres, fake]
status: active
---

# DataSource Layer

## Responsibility

Abstract exactly one data provider. Translate provider-specific documents and
payloads into domain values. Translate provider-specific failures into the typed
error union.

That is all. No business logic. No coordination of several providers.

This restates `ARCH-PC-DATASOURCE` for a web app. It is the one layer whose code
differs between the two runtimes (`ARCH-WEB-APP`), so the rules below say where
they differ and otherwise hold for both.

## Structure

Every DataSource is an interface plus an implementation. The interface is what
every other layer imports (`ARCH-WEB-APP-DEP-02`, `ARCH-WEB-APP-DEP-04`); the
implementation is imported only by the composition module
(`ARCH-WEB-APP-DEP-06`).

```
features/{feature}/data/
├── {Entity}DataSource.ts              Interface, written in domain types imported from `domain/`
├── Firestore{Entity}DataSource.ts     Implementation over the Firestore SDK
├── Http{Entity}DataSource.ts          Implementation over the HTTP executor
├── Callable{Action}DataSource.ts      Implementation over a callable function
├── {entity}.mapper.ts                 Provider payload → domain value (parsing included)
├── Fake{Entity}DataSource.ts          In-memory implementation, for tests and previews
└── {Entity}DataSource.contract.ts     Shared contract tests run against real and fake
```

```rule
id: ARCH-WEB-APP-DS-INTERFACE-01
statement: Every DataSource MUST define an interface, and every consumer MUST depend on the interface, never on an implementation; the same applies to a Repository.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DS-INTERFACE-01 — Every DataSource MUST define an interface, and every consumer MUST depend on the interface, never on an implementation; the same applies to a Repository.
```

```rule
id: ARCH-WEB-APP-DS-ONE-01
statement: A DataSource MUST wrap exactly one provider; two providers MUST be two DataSources, coordinated above them.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DS-ONE-01 — A DataSource MUST wrap exactly one provider; two providers MUST be two DataSources, coordinated above them.
```

```rule
id: ARCH-WEB-APP-DS-RESPONSIBILITY-01
statement: A DataSource MUST contain only query construction, payload parsing, type mapping and error translation.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DS-RESPONSIBILITY-01 — A DataSource MUST contain only query construction, payload parsing, type mapping and error translation.
```

Business decisions (which records count, how a figure is derived) belong in a
UseCase or in the domain.

## Return types

An asynchronous result is an `Outcome` (`PAT-OUTCOME`); data that changes while a
consumer is looking at it is a subscription (`PAT-OBSERVER`).

```typescript
type Unsubscribe = () => void;

interface SnapshotDataSource {
  // One-shot: a Promise of an Outcome. Never rejects for an expected failure.
  getSnapshot(id: string): Promise<Outcome<Snapshot | null>>;

  // Live: delivers an Outcome per emission; returns the way to stop.
  subscribeSnapshots(
    region: RegionId,
    onChange: (outcome: Outcome<readonly Snapshot[]>) => void,
  ): Unsubscribe;
}
```

```rule
id: ARCH-WEB-APP-DS-RETURN-01
statement: A one-shot DataSource operation MUST return `Promise<Outcome<T>>` and MUST NOT reject for an expected failure; an abort is not a failure and is rethrown unchanged.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DS-RETURN-01 — A one-shot DataSource operation MUST return `Promise<Outcome<T>>` and MUST NOT reject for an expected failure; an abort is not a failure and is rethrown unchanged.
```

```rule
id: ARCH-WEB-APP-DS-RETURN-02
statement: Data the provider pushes changes for MUST be exposed as a subscription that delivers an `Outcome` on every emission, including errors, and returns an unsubscribe function.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DS-RETURN-02 — Data the provider pushes changes for MUST be exposed as a subscription that delivers an `Outcome` on every emission, including errors, and returns an unsubscribe function.
```

```rule
id: ARCH-WEB-APP-DS-RETURN-03
statement: A DataSource MUST NOT turn a one-shot provider call into a subscription (for example by polling) or hide a subscription behind a one-shot call.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DS-RETURN-03 — A DataSource MUST NOT turn a one-shot provider call into a subscription (for example by polling) or hide a subscription behind a one-shot call.
```

Respect the provider's own contract. If the provider pushes (Firestore
`onSnapshot`), the DataSource subscribes; if it answers once (`getDoc`, `fetch`),
the DataSource is one-shot. Never collapse or inflate it. If the app needs
polling, that is a decision made above the DataSource.

```rule
id: ARCH-WEB-APP-DS-SUBSCRIBE-01
statement: A subscription MUST start only when `subscribe…` is called, MUST be one provider listener per call, and MUST be fully released by the returned unsubscribe function.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DS-SUBSCRIBE-01 — A subscription MUST start only when `subscribe…` is called, MUST be one provider listener per call, and MUST be fully released by the returned unsubscribe function.
```

A DataSource that opens a listener when it is constructed, or shares one listener
between callers without reference counting, leaks listeners the moment two
components mount. The hook that calls `subscribe…` returns the unsubscribe from
its effect (`PLAT-WEB-TS-CLEANUP-01`).

```rule
id: ARCH-WEB-APP-DS-PAGE-01
statement: A list read over a collection that grows MUST be paginated with a limit, a unique order (the document id as the tie-break) and a cursor (`startAfter`), and MUST NOT use `offset`.
type: hard
scope: performance
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DS-PAGE-01 — A list read over a collection that grows MUST be paginated with a limit, a unique order (the document id as the tie-break) and a cursor (`startAfter`), and MUST NOT use `offset`.
```

Standard practice for any list a person browses. A collection that is a fixed set may be read whole.

```rule
id: ARCH-WEB-APP-DS-AGG-01
statement: Totals and breakdowns over a growing collection MUST NOT be computed by reading every document in the client; they MUST come from a server-side aggregate or a precomputed document.
type: hard
scope: performance
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DS-AGG-01 — Totals and breakdowns over a growing collection MUST NOT be computed by reading every document in the client; they MUST come from a server-side aggregate or a precomputed document.
```

Pagination answers "the next page"; it does not answer "the rate across everything", which would need every page. How large a collection may get before this applies is a decision for the project, recorded as a project-local rule (for example a read budget), not a number in this framework.


## Parsing and mapping

Everything a provider returns is untrusted shape. A Firestore `data()` is
`DocumentData`, a `fetch` body is `unknown`, a callable's result is whatever the
function sent.

```rule
id: ARCH-WEB-APP-DS-PARSE-01
statement: A DataSource MUST parse every provider payload with a schema parser into a domain value, MUST treat the payload as `unknown` until it has, and MUST NOT use a type assertion (`as Foo`) to give it a type.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DS-PARSE-01 — A DataSource MUST parse every provider payload with a schema parser into a domain value, MUST treat the payload as `unknown` until it has, and MUST NOT use a type assertion (`as Foo`) to give it a type.
```

```typescript
// ❌ Wrong — the cast promises a shape nobody checked
const items = snap.docs.map(d => ({ id: d.id, ...d.data() } as FeedDoc));

// ✅ Correct — the payload is unknown until the schema accepts it
const parsed = feedSchema.safeParse({ id: d.id, ...d.data() });
if (!parsed.success) return malformed('feeds', d.id, parsed.error); // logged; names the record
```

This differs deliberately from the `web-spa` Firebase guide, whose casting
example is an SPA convention. A schema parser (`zod`, the framework's choice for
forms in `PLAT-WEB-FORMS`) turns provider drift into a typed error instead of a
wrong number on a chart.

```rule
id: ARCH-WEB-APP-DS-MALFORMED-01
statement: A payload that fails parsing MUST become an explicit `unexpected` error outcome whose message names the record and whose cause is logged, and MUST NOT be silently dropped, defaulted or counted as zero.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DS-MALFORMED-01 — A payload that fails parsing MUST become an explicit `unexpected` error outcome whose message names the record and whose cause is logged, and MUST NOT be silently dropped, defaulted or counted as zero.
```

A collection read where one record is malformed returns the error; it does not
return the other records as though the read had succeeded. If a feature can
tolerate partial data, the DataSource returns the valid records together with the
rejected ones in its result type, so the caller decides and the loss is visible.

```rule
id: ARCH-WEB-APP-DS-MAPPING-01
statement: DataSource methods MUST return domain values and MUST NOT return documents, snapshots, DTOs, driver rows, `Response` objects or any other provider type.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DS-MAPPING-01 — DataSource methods MUST return domain values and MUST NOT return documents, snapshots, DTOs, driver rows, `Response` objects or any other provider type.
```

```rule
id: ARCH-WEB-APP-DS-MAPPING-02
statement: Mapping and parsing functions MUST live beside the DataSource that owns them, as private functions in its file or a mapper file in the same folder, and MUST NOT be inlined in a business method.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DS-MAPPING-02 — Mapping and parsing functions MUST live beside the DataSource that owns them, as private functions in its file or a mapper file in the same folder, and MUST NOT be inlined in a business method.
```

```rule
id: ARCH-WEB-APP-DS-EMPTY-01
statement: "Not found" for a single-record lookup and "no rows" for a list MUST be successful outcomes (`null` and an empty array), and `notFound` MUST be reserved for an operation on a specific identity that must exist.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DS-EMPTY-01 — "Not found" for a single-record lookup and "no rows" for a list MUST be successful outcomes (`null` and an empty array), and `notFound` MUST be reserved for an operation on a specific identity that must exist.
```

Whether an absent record is a failure is the caller's decision: a fresh account
before its first sync is not an error. Reading a snapshot that should exist and
does not is. An update or delete of a missing record is `notFound`.

## Schema change

```rule
id: ARCH-WEB-APP-DS-SCHEMA-01
statement: A change to a stored document's shape MUST ship with one of: an idempotent backfill with a dry run, a versioned reader that maps the old shape explicitly and whose exclusions are counted and shown, or a recorded decision to discard; a reader that silently defaults a missing field is none of these.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DS-SCHEMA-01 — A change to a stored document's shape MUST ship with one of: an idempotent backfill with a dry run, a versioned reader that maps the old shape explicitly and whose exclusions are counted and shown, or a recorded decision to discard; a reader that silently defaults a missing field is none of these.
```

This is the Firestore stand-in for a migration file, since a schemaless store has no tool to force one. Documents SHOULD carry a `schemaVersion`. When old documents cannot be reconstructed, use the versioned reader and show how many were excluded.

## Error handling

Provider failures (a rejected `fetch`, a Firestore `FirestoreError`, a callable's
`FunctionsError`, a driver error) are an implementation detail of the provider. They
do not cross the DataSource boundary. The translation rule, the error union and
the unknown-failure rule are owned by `ARCH-WEB-APP-ERR-CLASSES`
(`ARCH-WEB-APP-ERR-TYPE-01`, `ARCH-WEB-APP-ERR-MAP-01`, `ARCH-WEB-APP-ERR-UNKNOWN-01`,
`ARCH-WEB-APP-ERR-CANCEL-01`); this layer is where they are applied. It adds:

Translate in one function per provider, not at every call site:

```typescript
function toAppError(e: unknown): AppError {
  // An abort never reaches here: the caller rethrows it first (ARCH-WEB-APP-ERR-CANCEL-01).
  if (isAppError(e)) return e;                              // pass through unchanged
  if (e instanceof FirestoreError) {
    if (e.code === 'permission-denied') return { type: 'forbidden' };
    if (e.code === 'unauthenticated')   return { type: 'unauthorized' };
    if (e.code === 'unavailable')       return { type: 'offline' };
  }
  logUnexpected(e);                                         // full cause, once
  return { type: 'unexpected', message: 'Something went wrong.' };
}
```

Catch order, most specific first: an abort (rethrown unchanged, before any general
`catch`), an already-mapped `AppError`, a known provider error, then everything else.

## Runtime variants

### `server` runtime

The DataSource runs in a Server Action or Route Handler (or a module they call),
on a held server.

The environment-variable rule itself is `PLAT-WEB-NEXT-ENV-01`; this rule is the
architectural statement that the whole module, not only its variables, stays on
the server. Connection pooling on a scale-to-zero host is
`PLAT-WEB-NEXT-APP-DEPLOY-POOL-01`.

### `static-export` runtime

The DataSource runs in the browser. It has no secrets (`ARCH-WEB-APP-RUNTIME-02`);
the provider's access rules decide what it may read and write.

(`ARCH-WEB-APP-DS-RULES-01` now lives in `QG-WEB-TESTING`.)

When the browser is the caller, the rules are the only access control. A
DataSource whose reads and writes have no rules test has no verified security
boundary, and a rules change can silently open or close it. Include a case for
each role the app has and for a signed-out caller.

## Testing

(`ARCH-WEB-APP-DS-TEST-01` now lives in `QG-WEB-TESTING`.)

Layers above a DataSource are tested against its fake (`ARCH-WEB-APP-DEP-02`
means they cannot import anything else). The shared contract tests are what keep
the fake honest; without them the fake drifts and every test above it proves
nothing. The real implementation runs the contract against the provider's emulator
or, for HTTP, against a network-level mock (`QG-WEB-TESTING-MSW-01`), never a
mocked SDK.

## Naming

```rule
id: ARCH-WEB-APP-DS-NAMING-01
statement: The interface is named `{Entity}DataSource`, and an implementation is named with the provider first: `Firestore{Entity}DataSource`, `Http{Entity}DataSource`, `Callable{Action}DataSource`, `Fake{Entity}DataSource`.
type: hard
scope: naming
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-DS-NAMING-01 — The interface is named `{Entity}DataSource`, and an implementation is named with the provider first: `Firestore{Entity}DataSource`, `Http{Entity}DataSource`, `Callable{Action}DataSource`, `Fake{Entity}DataSource`.
```

## Construction scope

A provider client (the Firestore instance, the HTTP executor) is created once, in
the composition module, and handed to each DataSource. A DataSource is cheap and
holds no state beyond that client and any open subscriptions, so it is built once
per composition, not once per component render.

## Violations

- Business logic (which records count, a derived figure) inside a DataSource
- A document, snapshot, DTO or `Response` returned from a DataSource method
- A type assertion on a provider payload instead of parsing it
- A malformed record silently skipped, defaulted, or counted as zero
- A rejected promise or thrown error for an expected failure
- An `AppError` re-wrapped as another `AppError`
- A listener opened in a constructor, or left running after unsubscribe
- A one-shot call wrapped in a polling loop to look like a subscription
- An unbounded subscription on a collection that grows
- A `server` DataSource importable from a Client Component
- A `static-export` DataSource with no access-rules test
- A DataSource with no fake, or a fake that does not pass the contract tests
