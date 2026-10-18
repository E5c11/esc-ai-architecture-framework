---
id: PLAT-WEB-NEXT-FIREBASE
type: guide
layer: platforms
platform: [web]
architecture: [web-app]
requires: [PLAT-WEB-NEXT, ARCH-WEB-APP-DATASOURCE, ARCH-WEB-APP-COMPOSITION, ARCH-WEB-APP-ERR-CLASSES]
related: [PLAT-WEB-FIREBASE, PLAT-WEB-NEXT-STATIC, PLAT-WEB-NEXT-APP-DEPLOY, PLAT-WEB-DEPLOY, ARCH-WEB-APP-OBS]
tags: [firebase, firestore, auth, security-rules, callable-functions, emulator, hosting, static-export, nextjs, pii]
status: active
---

# Firebase with Next.js

Extends: `ARCH-WEB-APP-DATASOURCE`, `ARCH-WEB-APP-COMPOSITION`

The Firebase platform guide for a `web-app`. `PLAT-WEB-FIREBASE` is its counterpart for
a `web-spa` on Vite and is not followed here: its configuration comes from
`import.meta.env.VITE_*`, and its hooks call Firestore directly, where a `web-app` has a
DataSource layer. Three rules carry over unchanged and are cited, not repeated:
`PLAT-WEB-FB-CONFIG-02` (no committed `.env`), `PLAT-WEB-FB-CLEANUP-01` (every
subscription unsubscribes) and `PLAT-WEB-FB-AUTH-01` (one owner of auth state).

This guide is written for the **`static-export`** runtime, where the browser talks to
Firestore, Storage and callable functions directly and the provider's access rules are
the security boundary (`ARCH-WEB-APP-RUNTIME-02`). Sections marked *server runtime*
cover the differences when Firebase is used from a Server Action or Route Handler.

## Configuration and secrets

```rule
id: PLAT-WEB-NEXT-FB-CONFIG-01
statement: The Firebase web configuration MUST be supplied as `NEXT_PUBLIC_FIREBASE_*` values read only by the composition's `loadConfig`, and MUST be treated as public identification, never as a secret and never as access control.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-FB-CONFIG-01 — The Firebase web configuration MUST be supplied as `NEXT_PUBLIC_FIREBASE_*` values read only by the composition's `loadConfig`, and MUST be treated as public identification, never as a secret and never as access control.
```

The web API key identifies the project; it does not authorise anything. Anyone can read
it from the bundle, so what protects the data is the security rules and the functions'
auth checks, not the key's obscurity. `NEXT_PUBLIC_*` values are inlined at build time, so
a different environment is a different build, not a different runtime setting.

```rule
id: PLAT-WEB-NEXT-FB-SECRET-01
statement: A service-account key, an Admin SDK credential or any private key MUST NOT exist in the app's source, its build, or its bundle, and MUST NOT carry a `NEXT_PUBLIC_` prefix; privileged access belongs to Cloud Functions and operator scripts, outside the client app.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-FB-SECRET-01 — A service-account key, an Admin SDK credential or any private key MUST NOT exist in the app's source, its build, or its bundle, and MUST NOT carry a `NEXT_PUBLIC_` prefix; privileged access belongs to Cloud Functions and operator scripts, outside the client app.
```

An operator script that needs a key keeps it outside the repository (gitignored
directory, or short-lived credentials) and deletes it when the task is finished.
`PLAT-WEB-NEXT-ENV-01` states the general `NEXT_PUBLIC_` rule this one specialises.

## Initialisation

```rule
id: PLAT-WEB-NEXT-FB-INIT-01
statement: Firebase MUST be initialised only inside the composition factory through an idempotent get-or-create keyed by the app's name (look the name up in `getApps()` before `initializeApp(config, name)`), and the factory MUST be called on the client after mount, never at module scope and never during prerendering.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-FB-INIT-01 — Firebase MUST be initialised only inside the composition factory through an idempotent get-or-create keyed by the app's name (look the name up in `getApps()` before `initializeApp(config, name)`), and the factory MUST be called on the client after mount, never at module scope and never during prerendering.
```

`next build` prerenders every page, **including Client Components**, in Node. A module
that calls `initializeApp` at its top level runs there, and a component that builds the
graph while rendering builds it there too. The prerendered HTML is therefore a shell:
the provider renders its loading state, and the graph is created in an effect on the
client. This is the rule `ARCH-WEB-APP-COMPOSE-GLOBAL-01` and
`ARCH-WEB-APP-COMPOSE-SDK-01` apply to this SDK specifically, and it is why a Strict
Mode double mount (`PLAT-WEB-RP-STRICT-01`) must not create a second app.

A project that talks to two Firebase projects from one build (a development and a production
project, chosen at run time) has two **named** apps. `getApp()` with no name returns the default app
and `initializeApp(config)` with no name creates it, so two environments need
`initializeApp(config, 'dev')` and `initializeApp(config, 'prod')`, each created once, on demand, and
chosen only in the composition (`ARCH-WEB-APP-COMPOSE-ENV-01`). Each project has its own security
rules, so each environment's access boundary is tested separately (`ARCH-WEB-APP-DS-RULES-01`).

```typescript
// composition/firebase.ts
export function getOrCreateFirebase(config: FirebaseConfig, name: string): FirebaseHandles {
  const app = getApps().find(existing => existing.name === name) ?? initializeApp(config, name);
  return { app, firestore: getFirestore(app), functions: getFunctions(app, config.functionsRegion) };
}
```

```typescript
// composition/AppProvider.tsx
'use client';
export function AppProvider({ config, children }: AppProviderProps) {
  const [graph, setGraph] = useState<AppGraph | null>(null);
  useEffect(() => { setGraph(createApp(config)); }, [config]);       // client only; get-or-create inside
  if (graph === null) return <AppSkeleton />;                         // what prerendering emits
  return <AppGraphContext.Provider value={graph}>{children}</AppGraphContext.Provider>;
}
```

## Auth

```rule
id: PLAT-WEB-NEXT-FB-AUTH-01
statement: Auth state MUST be owned by one provider that exposes a discriminated state (`loading`, `signedOut`, `signedIn` with the user's role) to Hooks, and a client-side guard MUST be a convenience for the interface and MUST NOT be the access boundary.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-FB-AUTH-01 — Auth state MUST be owned by one provider that exposes a discriminated state (`loading`, `signedOut`, `signedIn` with the user's role) to Hooks, and a client-side guard MUST be a convenience for the interface and MUST NOT be the access boundary.
```

Hiding a page from a signed-out user stops a user, not a request. Anyone can call the
SDK from a console, so every read and write must be refused by the rules or the function,
whatever the interface shows (`ARCH-WEB-APP-RUNTIME-02`).

```rule
id: PLAT-WEB-NEXT-FB-ROLES-01
statement: A user's role MUST come from a source the client cannot write (a custom claim, or a document the rules forbid clients to write), and the security rules and callable functions MUST check that source on every request.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-FB-ROLES-01 — A user's role MUST come from a source the client cannot write (a custom claim, or a document the rules forbid clients to write), and the security rules and callable functions MUST check that source on every request.
```

```rule
id: PLAT-WEB-NEXT-FB-SIGNUP-01
statement: A project with a fixed set of authorised users MUST disable self-service sign-up at the project level, and a person MUST be added by an operator action that creates both the sign-in account and the access record.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-FB-SIGNUP-01 — A project with a fixed set of authorised users MUST disable self-service sign-up at the project level, and a person MUST be added by an operator action that creates both the sign-in account and the access record.
```

With sign-up open, anyone can create an account in the project. If the rules are right
the data stays protected, but the project fills with accounts nobody invited. The
consequence of disabling it is that a first sign-in by someone who was not added is
refused, so adding people is a documented operator step, not a user action.

## Security rules

```rule
id: PLAT-WEB-NEXT-FB-RULES-01
statement: Security rules MUST deny by default, every collection and storage path the app uses MUST have an explicit rule naming who may read and write it, and `allow read, write: if true` MUST NOT exist outside a path that is deliberately public.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-FB-RULES-01 — Security rules MUST deny by default, every collection and storage path the app uses MUST have an explicit rule naming who may read and write it, and `allow read, write: if true` MUST NOT exist outside a path that is deliberately public.
```

Rules live in the repository (`firestore.rules`, `storage.rules`) and are deployed on
purpose, separately from the UI. Every read and write the app performs is covered by an
automated test of the rules, as `ARCH-WEB-APP-DS-RULES-01` requires, with a case for each
role and for a signed-out caller. A rule that fails closed on a legitimate request is
found by that test; a rule that fails open is found by it too, which is the one that
matters.

```rule
id: PLAT-WEB-NEXT-FB-EMU-01
statement: Rules tests and DataSource contract tests MUST run against the Firebase emulators in CI, and the composition MUST select the emulator from configuration, never from a code edit.
type: hard
scope: testing
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-FB-EMU-01 — Rules tests and DataSource contract tests MUST run against the Firebase emulators in CI, and the composition MUST select the emulator from configuration, never from a code edit.
```

The choice of live provider or emulator is `ARCH-WEB-APP-COMPOSE-CONFIG-01`'s: explicit,
from configuration, and loud when wrong. A test run must never be able to reach the
production project.

## Reading and writing data

The DataSource rules apply unchanged: one interface per provider, schema parsing of every
document (`ARCH-WEB-APP-DS-PARSE-01`), bounded reads (`ARCH-WEB-APP-DS-PAGE-01`), one
listener per `subscribe…` call (`ARCH-WEB-APP-DS-SUBSCRIBE-01`). Choose the read by how the
data behaves: `onSnapshot` for data that changes while someone is looking at it,
`getDoc`/`getDocs` for one-shot reads.

```rule
id: PLAT-WEB-NEXT-FB-DOC-01
statement: A document MUST stay well under Firestore's 1 MiB limit, and a large derived payload (an aggregated snapshot, a generated report) MUST be split across documents or stored as a file with the document holding its reference.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-FB-DOC-01 — A document MUST stay well under Firestore's 1 MiB limit, and a large derived payload (an aggregated snapshot, a generated report) MUST be split across documents or stored as a file with the document holding its reference.
```

An aggregate that grows with the data eventually crosses the limit, and the first sign is
a failed write in production. Design for the size the data will reach, not the size it has.

```rule
id: PLAT-WEB-NEXT-FB-INDEX-01
statement: Composite indexes MUST be declared in the repository (`firestore.indexes.json`) and deployed with the app, and a query that needs one MUST NOT be left to fail in production.
type: soft
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-FB-INDEX-01 — Composite indexes MUST be declared in the repository (`firestore.indexes.json`) and deployed with the app, and a query that needs one MUST NOT be left to fail in production.
```

```rule
id: PLAT-WEB-NEXT-FB-PERSIST-01
statement: Local persistence (an offline cache) MUST NOT be enabled for data that includes personal information unless the project's data policy allows that data to be stored on the user's device.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-FB-PERSIST-01 — Local persistence (an offline cache) MUST NOT be enabled for data that includes personal information unless the project's data policy allows that data to be stored on the user's device.
```

Persistence leaves a copy of what was read on a device that may be shared and that the
operator does not control. For an app that handles customer records this is a policy
decision with a privacy law behind it, not a performance setting.

## Callable functions

Actions that change data, or that need privileges the client lacks, go through callable
functions. The client calls them only from a DataSource.

```rule
id: PLAT-WEB-NEXT-FB-CALLABLE-01
statement: A callable function MUST verify the caller's authentication and role itself, MUST validate its input with a schema parser, and MUST return a typed result or a typed error; the client's checks are never relied on.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-FB-CALLABLE-01 — A callable function MUST verify the caller's authentication and role itself, MUST validate its input with a schema parser, and MUST return a typed result or a typed error; the client's checks are never relied on.
```

```rule
id: PLAT-WEB-NEXT-FB-CALLABLE-02
statement: The functions region MUST be set once in configuration and used by both the client and the deployment, and a callable's error code MUST be translated to the error union once, in the DataSource that calls it, using the table below.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-FB-CALLABLE-02 — The functions region MUST be set once in configuration and used by both the client and the deployment, and a callable's error code MUST be translated to the error union once, in the DataSource that calls it, using the table below.
```

A client that calls the wrong region gets a not-found that looks like a missing function
and is really a configuration error.

| Provider code (Firestore or callable) | `AppError` | Notes |
|---|---|---|
| `permission-denied` | `forbidden` | The rules or the function refused a signed-in caller |
| `unauthenticated` | `unauthorized` | No signed-in caller |
| `invalid-argument` | `validation` | A callable's input failed its schema; carry the field errors |
| `not-found` | `notFound` | Only where the record had to exist (`ARCH-WEB-APP-DS-EMPTY-01`) |
| `unavailable`, `deadline-exceeded` | `offline` | Connectivity or timeout; retry is the user's or a bounded idempotent retry (`PLAT-WEB-HTTP-RETRY-01`) |
| `failed-precondition` | `unexpected` | Often a missing index: log with the full cause, never mask |
| `resource-exhausted` | `unexpected` | A quota; log and surface as unavailable, not as empty data |
| anything else | `unexpected` | Logged once with the cause (`ARCH-WEB-APP-ERR-UNKNOWN-01`) |

## Static export and Hosting

What a static export may use, how its routes are generated, and how to verify it on the
host are `PLAT-WEB-NEXT-STATIC`'s (`PLAT-WEB-NEXT-STATIC-CONFIG-01`,
`PLAT-WEB-NEXT-STATIC-ROUTES-01`, `PLAT-WEB-NEXT-STATIC-DIRECT-01`). This section is what
is specific to Firebase Hosting. Headers, redirects and rewrites, which a static export
cannot put in the Next.js configuration, belong in `firebase.json`.

```rule
id: PLAT-WEB-NEXT-FB-HOSTING-01
statement: `firebase.json` MUST serve the export directory, MUST give hashed assets (`_next/static/**`) a long immutable cache lifetime, and MUST NOT cache HTML or any non-hashed file so that a deploy takes effect immediately.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-FB-HOSTING-01 — `firebase.json` MUST serve the export directory, MUST give hashed assets (`_next/static/**`) a long immutable cache lifetime, and MUST NOT cache HTML or any non-hashed file so that a deploy takes effect immediately.
```

```json
{
  "hosting": {
    "public": "out",
    "cleanUrls": true,
    "headers": [
      { "source": "/_next/static/**", "headers": [{ "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }] },
      { "source": "**/*.html",         "headers": [{ "key": "Cache-Control", "value": "no-cache" }] }
    ]
  }
}
```

An uploaded page that is cached for a day shows the previous version's numbers for a day
after a deploy, with nothing to say it is stale.

```rule
id: PLAT-WEB-NEXT-FB-DEPLOY-01
statement: UI changes MUST be deployed with `firebase deploy --only hosting` after `next build` has passed, and rules, indexes and functions MUST each be deployed deliberately and separately, never as a side effect of a UI deploy.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-WEB-NEXT-FB-DEPLOY-01 — UI changes MUST be deployed with `firebase deploy --only hosting` after `next build` has passed, and rules, indexes and functions MUST each be deployed deliberately and separately, never as a side effect of a UI deploy.
```

This is `PLAT-WEB-DEPLOY-HOSTING-01` and `PLAT-WEB-NEXT-APP-DEPLOY-BUILD-01` applied to a
Firebase-hosted export. A changed security rule is a change to who can read the data, and
it is reviewed as one.

## Server runtime

When Firebase is used from a Server Action or Route Handler, the Admin SDK runs there with
the project's service identity. It bypasses security rules, so the function's own checks
are the only access control: verify the caller from the session or ID token on every call
(`PLAT-WEB-NEXT-FB-CALLABLE-01` applies in the same spirit), keep the DataSource
server-only (`ARCH-WEB-APP-COMPOSE-SPLIT-01`), and never import the Admin SDK from a module a
Client Component can reach.

## Known platform traps

Facts that have cost real time and are not in the general documentation. Confirm each
against the current Firebase and Google Cloud documentation before relying on it.

- **Uploads from the page can fail with "you do not have permission"** until a role is
  granted to the Storage service agent that evaluates the rules (the Firestore service
  agent role on the Storage service account). The grant is once per project and can take
  a few minutes to apply.
- **Product availability differs by region.** Cloud Scheduler is not available in every
  Google Cloud region, so a scheduled function may need a different region from the rest
  of the project. State the region of each function in configuration
  (`PLAT-WEB-NEXT-FB-CALLABLE-02`) rather than assuming one.
- **Large files can exhaust a function's memory** if loaded whole; stream them, and keep
  files small enough to load whole where streaming is unreliable.
- **A pay-as-you-go project has no spending cap by default.** Set a budget alert on the
  billing account when the project is created.

```rule
id: PLAT-WEB-NEXT-FB-COST-01
statement: A project on a pay-as-you-go plan SHOULD have a budget alert on its billing account, set when the project is created.
type: soft
scope: behavior
enforced_by: [planner, reviewer]
violation_message: Violates PLAT-WEB-NEXT-FB-COST-01 — A project on a pay-as-you-go plan SHOULD have a budget alert on its billing account, set when the project is created.
```

## Violations

- `initializeApp(...)` at the top of a module, or the graph built while rendering
- A service-account key in the repository, the build or the bundle
- A Firebase web key treated as a secret, or as the access control
- A client-side route guard as the only protection of a page
- A role read from a document the client can write
- Rules with `allow read, write: if true` on a private collection
- A test run that can reach the production project
- An aggregated snapshot that grows toward the 1 MiB document limit
- Offline persistence enabled over customer records with no data-policy decision
- A callable that trusts the client's role
- HTML cached for a day, or hashed assets not cached at all
- Rules or functions deployed as a side effect of a UI deploy
