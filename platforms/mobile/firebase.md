---
id: PLAT-MOB-FIREBASE
type: platform
layer: platform
platform: [mobile]
architecture: [all]
requires: [PAT-DATA-ACCESS, PLAT-MOB-KMP, PLAT-MOB-KOTLIN]
related: [PLAT-MOB-KOIN, PLAT-MOB-ROOM]
tags: [firebase, firestore, auth, cloud, sdk, rest, android]
---

# Firebase KMP SDK

## Overview

Firebase provides cloud storage (Firestore), authentication, and other services.
In KMP, the Android target uses the native Firebase SDK; the wasmJs target uses
a REST-based implementation. Both expose the same interface — the DataSource layer
abstracts which implementation is active.

## Source set strategy

```rule
id: PLAT-MOB-FB-SS-01
statement: Firebase SDK imports (`com.google.firebase.*`, `dev.gitlive.firebase.*`) MUST NOT appear in `commonMain`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-FB-SS-01 — Firebase SDK imports (`com.google.firebase.*`, `dev.gitlive.firebase.*`) MUST NOT appear in `commonMain`.
```

All Firebase code lives in `androidMain` or, for the REST layer, in a dedicated source set (`restMain` or `wasmJsMain`).

```rule
id: PLAT-MOB-FB-SS-02
statement: The `restMain` source set (web Firebase implementation) MUST NOT import any `android.*` packages.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-FB-SS-02 — The `restMain` source set (web Firebase implementation) MUST NOT import any `android.*` packages.
```

It must be purely Kotlin/HTTP.

## DataSource boundary

Firebase types (`DocumentSnapshot`, `QuerySnapshot`, task callbacks) MUST NOT
cross the DataSource boundary. The DataSource maps Firebase types to domain types
before returning.

```rule
id: PLAT-MOB-FB-DS-01
statement: DataSource methods MUST return domain types, never Firebase SDK types.
type: hard
scope: return-type
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-FB-DS-01 — DataSource methods MUST return domain types, never Firebase SDK types.
```

```rule
id: PLAT-MOB-FB-DS-02
statement: Firebase exceptions (`FirebaseException`, `FirebaseFirestoreException`) MUST be caught in the DataSource and translated to domain exceptions.
type: hard
scope: error-handling
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-FB-DS-02 — Firebase exceptions (`FirebaseException`, `FirebaseFirestoreException`) MUST be caught in the DataSource and translated to domain exceptions.
```

Raw Firebase exceptions MUST NOT propagate above the DataSource layer.

```rule
id: PLAT-MOB-FB-DS-03
statement: Firestore collection paths and document field names MUST be declared as constants, never as inline string literals in query code.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-FB-DS-03 — Firestore collection paths and document field names MUST be declared as constants, never as inline string literals in query code.
```

## Auth

```rule
id: PLAT-MOB-FB-AUTH-01
statement: The currently authenticated user MUST be retrieved via an injected auth abstraction, never via `FirebaseAuth.getInstance()` called directly inside a UseCase or ViewModel.
type: hard
scope: di
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-FB-AUTH-01 — The currently authenticated user MUST be retrieved via an injected auth abstraction, never via `FirebaseAuth.getInstance()` called directly inside a UseCase or ViewModel.
```

```rule
id: PLAT-MOB-FB-AUTH-02
statement: Auth state changes (sign-in, sign-out, token refresh) MUST be observed as a stream, not fetched on demand.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-FB-AUTH-02 — Auth state changes (sign-in, sign-out, token refresh) MUST be observed as a stream, not fetched on demand.
```

## DI registration

```rule
id: PLAT-MOB-FB-DI-01
statement: Firebase SDK instances MUST be declared as `single` scope in Koin. (See `PLAT-MOB-KOIN-SINGLE-03`.)
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-FB-DI-01 — Firebase SDK instances MUST be declared as `single` scope in Koin. (See `PLAT-MOB-KOIN-SINGLE-03`.)
```

```rule
id: PLAT-MOB-FB-DI-02
statement: The web target (`wasmJsMain`) MUST register a `webFirebaseModule` that provides REST-based implementations for all Firebase interfaces used by `commonMain` code.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-FB-DI-02 — The web target (`wasmJsMain`) MUST register a `webFirebaseModule` that provides REST-based implementations for all Firebase interfaces used by `commonMain` code.
```

## Violations

- `FirebaseFirestore.getInstance()` called inside a UseCase
- A Firestore `DocumentSnapshot` returned from a DataSource method
- `FirebaseException` propagated to a ViewModel
- Collection path `"users"` hardcoded inline in a query instead of a named constant
- Firebase SDK imported in `commonMain`
