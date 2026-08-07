---
id: PLAT-MOB-IOS-AUTH
type: guide
layer: platform
platform: [mobile]
architecture: [pragmatic-clean]
requires: [PLAT-MOB-IOS-INTEROP, PLAT-MOB-SECURE-STORAGE, ARCH-PC-DATASOURCE]
related: [PLAT-MOB-FIREBASE, PLAT-MOB-HTTP]
tags: [ios, auth, oauth, callback, url-scheme, session]
status: active
---

# iOS Authentication Integration

## Contract and ownership

The platform adapter performs the Apple/browser/provider ceremony and returns portable
credentials or a typed outcome to an auth DataSource. The DataSource exchanges/validates
credentials with the selected backend and maps provider errors.

**Rule PLAT-MOB-IOS-AUTH-BOUNDARY-01 (hard):** OAuth/Firebase/UIKit credential and
controller types MUST NOT cross the platform adapter/DataSource boundary.

## Callback configuration

Register only the URL schemes, universal links and associated domains required by selected
providers. Validate callback scheme, host/path and correlation state before accepting it.
Resume the single pending auth request exactly once.

**Rule PLAT-MOB-IOS-AUTH-STATE-01 (hard):** OAuth requests MUST use an unguessable state
value and reject callbacks whose state or expected route does not match.

**Rule PLAT-MOB-IOS-AUTH-CALLBACK-01 (hard):** Callback handling MUST be idempotent and
must not complete two pending callers from one callback.

## Session storage and cancellation

Store reusable session tokens through `PLAT-MOB-SECURE-STORAGE`. Never persist temporary
authorization codes longer than required. Sign-out/account deletion clears local credentials
and invalidates/revokes remote state when supported.

User dismissal maps to cancelled and must not be reported as an unexpected application error.
Network/provider failures retain their distinct error mapping.

## Validation checklist

- [ ] Provider configuration contains no server/client secret inappropriate for a public app.
- [ ] Callback route and state are validated and completion is idempotent.
- [ ] Tokens use secure storage and are cleared on sign-out/account deletion.
- [ ] Success, user cancellation, provider denial, malformed callback and network failure are tested.
- [ ] App restart/session restoration behavior is tested.
- [ ] Deferred providers are hidden or explicitly unavailable.

