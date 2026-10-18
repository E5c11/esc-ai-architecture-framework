---
id: ARCH-WEB-APP-COMPOSITION
type: rules
layer: architectures
platform: [web]
architecture: [web-app]
requires: [ARCH-WEB-APP, ARCH-WEB-APP-DATASOURCE, ARCH-WEB-APP-USECASE, CORE-DI, CORE-TESTING]
related: [ARCH-WEB-APP-REPOSITORY, ARCH-WEB-APP-HOOK, ARCH-PY-COMPOSITION, ARCH-PC-COMPOSITION, PLAT-WEB-HTTP]
tags: [composition, di, context, config, singleton, sdk-initialisation, test-graph, server, static-export]
status: active
---

# Composition

## Responsibility

The composition module is the one place that knows which concrete DataSources,
Repositories and UseCases exist. It reads configuration, builds the provider clients,
wires the layers together, and hands the finished graph to whoever asks. Everything
else receives its collaborators; nothing else goes looking for them.

(This is the dependency-injection root, as in `ARCH-PY-COMPOSITION`. It is not the
mobile `ARCH-PC-COMPOSITION`, which concerns composing two features on one screen;
that concern is the route's, see `ARCH-WEB-APP-FEATURE-STRUCTURE`.)

TypeScript needs no container for this. A function that builds objects and passes
them along is easier to read, has a plain stack trace, and has no runtime magic
(`PLAT-WEB-HTTP-DI-01` is the existing precedent in this framework). The import
boundary is `ARCH-WEB-APP-DEP-06`: concrete objects are constructed only here and in
tests. This document owns the rest: how the module is shaped and when it runs.

## Shape

```
composition/
├── createApp.ts          createApp(config, overrides?) → AppGraph. Pure construction; no side effects at import
├── config.ts             loadConfig(source) → Config. The only reader of environment values
├── graph.ts              AppGraph: the interfaces the graph exposes (UseCases, DataSources) and `dispose()`
├── AppProvider.tsx       Client context provider; useAppGraph(), useUseCases()
├── client.ts             The graph for the browser
└── server.ts             The graph for the server (server runtime only); server-only
```

```typescript
// composition/createApp.ts
export function createApp(config: Config, overrides: Partial<AppGraph> = {}): AppGraph {
  const firebase = getOrCreateFirebase(config.firebase);          // one named app per environment, idempotent
  const snapshots = new FirestoreSnapshotDataSource(firebase.firestore);
  const feeds = new CallableFeedDataSource(firebase.functions);
  return {
    snapshots, feeds,
    loadRegionFigures: createLoadRegionFigures({ snapshots }),
    saveFeed: createSaveFeed({ feeds }),
    ...overrides,                                                  // tests and previews swap parts
  };
}
```

## Rules

```rule
id: ARCH-WEB-APP-COMPOSE-FACTORY-01
statement: The composition module MUST expose a factory (`createApp(config, overrides?)`) that returns the whole graph typed by interfaces, and MUST do no work when imported.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-COMPOSE-FACTORY-01 — The composition module MUST expose a factory (`createApp(config, overrides?)`) that returns the whole graph typed by interfaces, and MUST do no work when imported.
```

```rule
id: ARCH-WEB-APP-COMPOSE-GLOBAL-01
statement: Importing a module MUST NOT initialise an SDK, open a connection or listener, read the environment, or populate a global registry; such work happens only when the factory is called.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-COMPOSE-GLOBAL-01 — Importing a module MUST NOT initialise an SDK, open a connection or listener, read the environment, or populate a global registry; such work happens only when the factory is called.
```

A module that calls `initializeApp(...)` or `getFirestore()` at its top level runs
during `next build`, during tests, and on the server when it is only meant for the
browser. It makes a test depend on import order and makes a fake impossible to
substitute. Every one of those problems disappears when construction is a function
call.

```rule
id: ARCH-WEB-APP-COMPOSE-CONFIG-01
statement: Configuration MUST be read once, by one `loadConfig` called from the composition module, validated with a schema parser, and passed on as a frozen value; no other module MAY read `process.env` or `NEXT_PUBLIC_*` values.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-COMPOSE-CONFIG-01 — Configuration MUST be read once, by one `loadConfig` called from the composition module, validated with a schema parser, and passed on as a frozen value; no other module MAY read `process.env` or `NEXT_PUBLIC_*` values.
```

A missing or malformed value fails at startup with a message naming the value, not
three screens later as `undefined`. Which values are safe to expose to the browser is
`PLAT-WEB-NEXT-ENV-01`; this rule makes sure there is one place that decides.

```rule
id: ARCH-WEB-APP-COMPOSE-SDK-01
statement: A provider SDK app MUST be initialised at most once per configured app (one name per project or environment), through an idempotent get-or-create keyed by that name, so hot reload, repeated calls and tests cannot create a second instance of the same app.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-COMPOSE-SDK-01 — A provider SDK app MUST be initialised at most once per configured app (one name per project or environment), through an idempotent get-or-create keyed by that name, so hot reload, repeated calls and tests cannot create a second instance of the same app.
```

The unit is the *app*, not the process: a program that legitimately talks to two projects (a
development and a production one) has two apps, each created once, each under its own name. What
the rule forbids is a second instance of the same app, which is what a hot reload, a repeated call or
a test that builds its own graph produces.

```rule
id: ARCH-WEB-APP-COMPOSE-ENV-01
statement: Where one build can talk to more than one environment (for example a development and a production project), each environment MUST be a named app created by the composition module on demand, the active environment MUST be chosen in that one place, and switching it MUST discard the current graph, releasing every subscription, and build a new one.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-COMPOSE-ENV-01 — Where one build can talk to more than one environment (for example a development and a production project), each environment MUST be a named app created by the composition module on demand, the active environment MUST be chosen in that one place, and switching it MUST discard the current graph, releasing every subscription, and build a new one.
```

```typescript
// composition/environment.ts: the only place the active environment is chosen
export type EnvironmentName = 'dev' | 'prod';

export function createAppFor(env: EnvironmentName, config: Config): AppGraph {
  return createApp({ ...config, firebase: config.environments[env], appName: env });   // named app
}

// AppProvider: a change of environment is a new graph, never a mutated one
useEffect(() => {
  const graph = createAppFor(environment, config);
  setGraph(graph);
  return () => graph.dispose();            // releases listeners; the named app itself is reused
}, [environment, config]);
```

Both apps must not exist as module-level constants created at import
(`ARCH-WEB-APP-COMPOSE-GLOBAL-01`), and neither a DataSource nor a Hook may choose, hold or reach for
an environment: they receive the graph for the active one. Mutating a live graph's providers in place
leaves a Hook still subscribed to the environment the user just left, showing its data under the new
environment's name. A new graph, built after the old one is released, cannot.

```rule
id: ARCH-WEB-APP-COMPOSE-ENV-02
statement: The active environment SHOULD be visible wherever a write can happen, and switching to an environment that holds real data SHOULD be an explicit, confirmed action.
type: soft
scope: behavior
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-COMPOSE-ENV-02 — The active environment SHOULD be visible wherever a write can happen, and switching to an environment that holds real data SHOULD be an explicit, confirmed action.
```

An administration tool that can write to production from the same screen that edits a test project is
one unnoticed toggle from a real incident. The indicator belongs to the component layer; the rule
that the choice lives in the composition is `ARCH-WEB-APP-COMPOSE-ENV-01`.

```rule
id: ARCH-WEB-APP-COMPOSE-CHOICE-01
statement: Choosing between interchangeable implementations (the live provider, the emulator, a fake) MUST be done in the composition module from configuration, and an unknown choice MUST fail with a clear configuration error rather than fall back silently.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-COMPOSE-CHOICE-01 — Choosing between interchangeable implementations (the live provider, the emulator, a fake) MUST be done in the composition module from configuration, and an unknown choice MUST fail with a clear configuration error rather than fall back silently.
```

A build that quietly falls back to a fake looks healthy and shows invented data. A
build wired to the production provider from a development machine does worse. The
choice is explicit and its failure is loud.

```rule
id: ARCH-WEB-APP-COMPOSE-CONTEXT-01
statement: The graph MUST reach Client Components through one provider context at the root of the client tree, exposed through typed accessors that return interfaces, and an accessor used without a provider MUST throw a clear error.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-COMPOSE-CONTEXT-01 — The graph MUST reach Client Components through one provider context at the root of the client tree, exposed through typed accessors that return interfaces, and an accessor used without a provider MUST throw a clear error.
```

This is the mechanism `ARCH-WEB-APP-HOOK-DEPS-01` relies on. A test wraps a hook in
`AppProvider` with a graph built from fakes.

## The two runtimes

```rule
id: ARCH-WEB-APP-COMPOSE-SPLIT-01
statement: In the `server` runtime the server graph and the client graph MUST be separate modules, the server module MUST be unimportable from client code, and a server-only DataSource MUST NOT appear in the client graph.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-COMPOSE-SPLIT-01 — In the `server` runtime the server graph and the client graph MUST be separate modules, the server module MUST be unimportable from client code, and a server-only DataSource MUST NOT appear in the client graph.
```

In `static-export` there is one graph, the client graph, and no secret in it
(`ARCH-WEB-APP-RUNTIME-02`).

```rule
id: ARCH-WEB-APP-COMPOSE-LAZY-01
statement: A heavy or optional dependency SHOULD be imported inside the factory that needs it, so a route that never uses it does not pay for it in the bundle.
type: soft
scope: performance
enforced_by: [reviewer]
violation_message: Violates ARCH-WEB-APP-COMPOSE-LAZY-01 — A heavy or optional dependency SHOULD be imported inside the factory that needs it, so a route that never uses it does not pay for it in the bundle.
```

## Testing

(`ARCH-WEB-APP-COMPOSE-TEST-01` now lives in `QG-WEB-TESTING`.)

The same override mechanism builds previews and demos: the app can run with an
in-memory graph and no backend, which is also how a screen is developed before its
provider exists.

## Violations

- `initializeApp(...)` or `getFirestore()` at a module's top level
- `process.env` or a `NEXT_PUBLIC_*` value read outside `loadConfig`
- A second SDK instance created by a hot reload or a test
- Two environments held as module-level constants, or switched by mutating a live graph
- A Hook or DataSource that picks the environment itself
- A hook or component importing a graph built in another module
- A silent fallback to a fake when configuration is missing
- A server-only DataSource reachable from client code
- A test that depends on a module-level graph or another test's leftovers
