---
id: PLAT-MOB-FIREBASE
type: platform
layer: platform
platform: [mobile]
architecture: [all]
requires: [PAT-DATA-ACCESS, PLAT-MOB-KMP, PLAT-MOB-KOTLIN]
related: [PLAT-MOB-KOIN, PLAT-MOB-ROOM, PLAT-MOB-HTTP, PLAT-MOB-SECURE-STORAGE]
tags: [firebase, firestore, auth, cloud, sdk, rest, android, ios]
status: active
---

# Firebase KMP SDK

## Overview

Firebase provides cloud storage (Firestore), authentication, and other services.
KMP applications can use native Firebase SDK bindings or a provider-neutral REST layer.
The DataSource layer abstracts the selected implementation so common callers do not change.

## iOS strategy decision

Choose one iOS strategy before implementation:

1. Reuse a pure Kotlin REST implementation with Darwin HTTP and secure token storage; or
2. integrate supported Firebase Apple SDK bindings and Apple configuration.

Record the choice, supported Firebase products, source-set graph, authentication behavior
and test environment. Do not mix native and REST implementations for the same interface
without explicit qualifiers and ownership.

**Rule PLAT-MOB-FB-IOS-01 (hard):** A project MUST document whether each Firebase
capability uses REST or the native Apple SDK before wiring iOS DI.

## Source set strategy

```rule
id: PLAT-MOB-FB-SS-01
statement: Firebase SDK imports (`com.google.firebase.*`, `dev.gitlive.firebase.*`) MUST NOT appear in `commonMain`.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-FB-SS-01 — Firebase SDK imports (`com.google.firebase.*`, `dev.gitlive.firebase.*`) MUST NOT appear in `commonMain`.
```

All Firebase code lives in its platform source set (`androidMain`/`iosMain`) or, for the
REST layer, in a dedicated provider-neutral source set such as `restMain`.

```rule
id: PLAT-MOB-FB-SS-02
statement: A `restMain` source set shared by web, Huawei or iOS MUST be pure Kotlin/HTTP and MUST NOT import Android, browser or Apple platform APIs.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-FB-SS-02 — A `restMain` source set shared by web, Huawei or iOS MUST be pure Kotlin/HTTP and MUST NOT import Android, browser or Apple platform APIs.
```

```rule
id: PLAT-MOB-FB-SS-03
statement: Custom REST source-set edges MUST be explicit and verified for every consuming target.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-FB-SS-03 — Custom REST source-set edges MUST be explicit and verified for every consuming target. Do not silence hierarchy warnings without proving the intended sources compile into each target.
```

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

**Rule PLAT-MOB-FB-DI-03 (hard):** iOS MUST register exactly one implementation for
every Firebase-facing common interface. REST bindings should be assembled from shared REST
modules; native bindings remain in `iosMain`.

## Apple configuration and credentials

Native SDK integration requires environment-specific Apple configuration, URL schemes and
callback handling. REST integration requires environment endpoints/keys plus Keychain-backed
session tokens. Public client configuration may be packaged with the app; server secrets and
administrative credentials must never be embedded.

## Validation checklist

- [ ] REST/native choice and supported products are recorded.
- [ ] No provider SDK type crosses the DataSource boundary.
- [ ] REST source set compiles for every intended target, including iOS when selected.
- [ ] iOS DI resolves exactly one implementation for every common interface.
- [ ] Auth change/refresh/sign-out behavior is tested without exposing credentials.
- [ ] Environment configuration contains no server secret.

## Violations

- `FirebaseFirestore.getInstance()` called inside a UseCase
- A Firestore `DocumentSnapshot` returned from a DataSource method
- `FirebaseException` propagated to a ViewModel
- Collection path `"users"` hardcoded inline in a query instead of a named constant
- Firebase SDK imported in `commonMain`
- REST code labelled web-only while also being wired to a Native target
