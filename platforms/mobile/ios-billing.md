---
id: PLAT-MOB-IOS-BILLING
type: guide
layer: platform
platform: [mobile]
architecture: [pragmatic-clean]
requires: [PLAT-MOB-IOS-INTEROP, ARCH-PC-DATASOURCE, ARCH-PC-REPOSITORY, ARCH-PC-USECASE]
related: [PLAT-MOB-SECURE-STORAGE]
tags: [ios, storekit, billing, subscriptions, entitlements, restore]
---

# StoreKit Billing and Entitlements

## Architecture

StoreKit is a platform provider behind a common billing interface. Product eligibility,
premium capabilities and user messaging remain common/domain concerns. StoreKit product and
transaction objects stay inside the iOS adapter/DataSource.

**Rule PLAT-MOB-IOS-BILL-BOUNDARY-01 (hard):** StoreKit types MUST NOT cross into common
repository, UseCase, ViewModel or domain contracts.

## Products and purchase outcomes

Product identifiers come from environment/release configuration. Model success, pending,
user-cancelled, failed and restored outcomes explicitly. Observe transaction updates for the
life of the application and finish only transactions the application has processed durably.

**Rule PLAT-MOB-IOS-BILL-OUTCOME-01 (hard):** Pending and user-cancelled purchases MUST
NOT be reported as success or unexpected failure.

**Rule PLAT-MOB-IOS-BILL-FINISH-01 (hard):** A verified transaction MUST be persisted/
acknowledged by the entitlement flow before it is finished, with idempotent repeat handling.

## Entitlement authority

The client may display provisional state, but durable premium authority should be verified by
the trusted backend and reconciled on launch/restore. Never trust a plain local premium flag.

**Rule PLAT-MOB-IOS-BILL-ENTITLEMENT-01 (hard):** Durable paid entitlement MUST derive
from verified transaction/backend state and be idempotent across duplicate callbacks.

## Restore and testing

Restore is user-invoked where product requirements call for it and reconciles the same
entitlement model as purchase. Test with StoreKit configuration plus sandbox/integration
accounts: unavailable products, success, pending, cancellation, verification failure,
duplicate transaction, restore, renewal, expiry and revocation.

## Validation checklist

- [ ] Product identifiers are configured, not scattered literals.
- [ ] StoreKit objects remain behind the platform boundary.
- [ ] Purchase outcomes and transaction updates are exhaustive.
- [ ] Entitlements are verified and duplicate callbacks are idempotent.
- [ ] Transactions are finished only after durable processing.
- [ ] Purchase and restore test matrix passes without affecting other billing platforms.

