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

**Rule PLAT-MOB-FB-SS-01 (hard):** Firebase SDK imports (`com.google.firebase.*`,
`dev.gitlive.firebase.*`) MUST NOT appear in `commonMain`. All Firebase code lives
in `androidMain` or, for the REST layer, in a dedicated source set (`restMain`
or `wasmJsMain`).

**Rule PLAT-MOB-FB-SS-02 (hard):** The `restMain` source set (web Firebase
implementation) MUST NOT import any `android.*` packages. It must be purely
Kotlin/HTTP.

## DataSource boundary

Firebase types (`DocumentSnapshot`, `QuerySnapshot`, task callbacks) MUST NOT
cross the DataSource boundary. The DataSource maps Firebase types to domain types
before returning.

**Rule PLAT-MOB-FB-DS-01 (hard):** DataSource methods MUST return domain types,
never Firebase SDK types.

**Rule PLAT-MOB-FB-DS-02 (hard):** Firebase exceptions (`FirebaseException`,
`FirebaseFirestoreException`) MUST be caught in the DataSource and translated
to domain exceptions. Raw Firebase exceptions MUST NOT propagate above the
DataSource layer.

**Rule PLAT-MOB-FB-DS-03 (hard):** Firestore collection paths and document
field names MUST be declared as constants, never as inline string literals in
query code.

## Auth

**Rule PLAT-MOB-FB-AUTH-01 (hard):** The currently authenticated user MUST be
retrieved via an injected auth abstraction, never via `FirebaseAuth.getInstance()`
called directly inside a UseCase or ViewModel.

**Rule PLAT-MOB-FB-AUTH-02 (hard):** Auth state changes (sign-in, sign-out,
token refresh) MUST be observed as a stream, not fetched on demand.

## DI registration

**Rule PLAT-MOB-FB-DI-01 (hard):** Firebase SDK instances MUST be declared as
`single` scope in Koin. (See `PLAT-MOB-KOIN-SINGLE-03`.)

**Rule PLAT-MOB-FB-DI-02 (hard):** The web target (`wasmJsMain`) MUST register
a `webFirebaseModule` that provides REST-based implementations for all Firebase
interfaces used by `commonMain` code.

## Violations

- `FirebaseFirestore.getInstance()` called inside a UseCase
- A Firestore `DocumentSnapshot` returned from a DataSource method
- `FirebaseException` propagated to a ViewModel
- Collection path `"users"` hardcoded inline in a query instead of a named constant
- Firebase SDK imported in `commonMain`
