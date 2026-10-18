---
id: PAT-OBSERVER
type: pattern
layer: pattern
platform: [all]
architecture: [all]
requires: [CORE-SSOT]
related: [PAT-DATA-ACCESS, PAT-OUTCOME]
tags: [observer, reactive, streams, push, subscription, real-time]
status: active
---

# Observable Data

## Statement

Data that changes over time is modelled as a stream that consumers subscribe to,
rather than a value that consumers fetch once.

## Rationale

Polling (fetch-on-demand) misses changes that happen between fetches and creates
unnecessary load. A push model where producers emit changes and consumers react
eliminates the polling gap and keeps derived state — including UI — consistent
without manual refresh logic. It also composes naturally with SSOT: the
authoritative owner emits; all derived representations subscribe and update.

## Also known as

Observer pattern, reactive streams, Pub/Sub, event-driven data.

## Platform expressions

| Platform | Common implementation |
|----------|-----------------------|
| Kotlin | `Flow<T>`, `StateFlow<T>`, `SharedFlow<T>` |
| Java | `Flux<T>` (Project Reactor), `Observable` (RxJava) |
| TypeScript | `Observable<T>` (RxJS), React state + hooks |
| General | Event emitters, message queues |

## In Practice

- Data that can change while a consumer is active is exposed as a stream, not
  a one-shot fetch
- One-shot operations (commands, write requests) use request/response semantics,
  not streams — a stream with exactly one emission is not a stream, it is a fetch
- The producer emits when state changes; the consumer subscribes and reacts —
  consumers do not poll the producer
- Streams are lazy by default; they start producing only when subscribed and stop
  when unsubscribed
- Sharing (broadcasting one stream to multiple subscribers) is explicit and
  intentional, not the default

## Choosing between stream and one-shot

| Scenario | Use |
|----------|-----|
| Read data that persists locally and can change | Stream |
| One-time network request or write command | One-shot (suspend / Promise / async) |
| UI state derived from changing data | Stream |
| Fetching a value once to populate a form | One-shot |

## Narrowing side-effect triggers

```rule
id: PAT-OBS-TRIGGER-01
statement: A subscription whose emissions trigger a side effect (network request, sync, write) MUST be narrowed to the specific inputs that side effect depends on, and fire only when those inputs change — never keyed on a whole aggregate whose unrelated fields change often.
type: hard
scope: behavior
enforced_by: [executor, reviewer]
violation_message: Violates PAT-OBS-TRIGGER-01 — side effect re-runs on unrelated changes to the observed aggregate.
```

An aggregate (a profile, settings, a session) emits whenever *any* of its fields
changes. If a side effect is keyed on the whole aggregate, every write to an
unrelated, frequently-updated field re-runs the side effect. Project the
aggregate down to the inputs the side effect actually uses and suppress repeats
of that projection.

| Platform | Narrowing |
|----------|-----------|
| Kotlin | `.map { it.subjectKey to it.syllabusKey }.distinctUntilChanged()` before `flatMapLatest` / `collectLatest` |
| React | Narrow the `useEffect` dependency array to the fields the effect uses (e.g. `user.subjectId`, not `user`) |

*Violation signal:* a network, sync or write call inside a collector (or effect)
of a whole aggregate that also carries frequently-written fields.

## Violations

- Polling a function on a timer to detect changes instead of subscribing
- A stream exposed for a write command that completes exactly once
- Multiple independent fetches of the same data instead of one shared subscription
- Subscribing to a stream and calling `.first()` every time instead of modelling
  the data as a one-shot fetch
- Network/sync call inside a collector of a whole aggregate (profile, settings) that also
  carries frequently-written fields (violates `PAT-OBS-TRIGGER-01`)
