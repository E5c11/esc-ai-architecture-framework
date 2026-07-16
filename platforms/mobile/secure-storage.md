---
id: PLAT-MOB-SECURE-STORAGE
type: guide
layer: platform
platform: [mobile]
architecture: [all]
requires: [PLAT-MOB-KMP, ARCH-PC-DATASOURCE]
related: [PLAT-MOB-DATASTORE, PLAT-MOB-IOS-AUTH, PLAT-MOB-HTTP]
tags: [security, keychain, credentials, tokens, storage, ios]
---

# Secure Credential Storage

## Scope

Secure storage is for credentials and similarly sensitive small values: access/refresh
tokens, private session material and cryptographic keys. Preferences/DataStore and ordinary
files are not secure-storage substitutes.

Expose a narrow common interface such as read, write and delete by typed key. Platform
implementations own Android keystore/encrypted storage or Apple Keychain APIs.

**Rule PLAT-MOB-SECSTORE-BOUNDARY-01 (hard):** Security/Keychain/keystore types MUST
remain behind a common storage interface and platform DI binding.

**Rule PLAT-MOB-SECSTORE-SECRET-01 (hard):** Credentials MUST NOT be stored in plain
preferences, logs, analytics, crash metadata or checked-in configuration.

## Apple Keychain

Use a stable service identifier and account/key name. Choose an accessibility class that
matches product requirements; authentication tokens normally must be unavailable before the
device is first unlocked and should not migrate to another device unless explicitly intended.

Treat duplicate-item as update, item-not-found as absence for reads/deletes, and map every
other status to a typed storage error. Delete session material on sign-out/account deletion.

**Rule PLAT-MOB-SECSTORE-IOS-01 (hard):** Keychain queries MUST constrain service and
account sufficiently to avoid reading/deleting another application's item.

**Rule PLAT-MOB-SECSTORE-IOS-02 (hard):** Accessibility and device-migration behavior
MUST be selected and documented rather than relying on an implicit default.

## Testing

Common tests use an in-memory fake to verify session behavior. Apple integration tests cover
write/read/update/delete, absence, persistence across adapter recreation and access failure.
Never print stored values in test diagnostics.

## Validation checklist

- [ ] Only sensitive small values use secure storage; ordinary preferences use DataStore.
- [ ] Platform SDK types do not cross the interface.
- [ ] Service/account and accessibility/migration policy are explicit.
- [ ] Sign-out and account deletion remove all relevant values.
- [ ] Duplicate, missing and unexpected OS statuses map correctly.
- [ ] No secret appears in logs, analytics, crash reports or fixtures.

