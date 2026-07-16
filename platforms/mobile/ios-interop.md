---
id: PLAT-MOB-IOS-INTEROP
type: guide
layer: platform
platform: [mobile]
architecture: [pragmatic-clean]
requires: [PLAT-MOB-KMP-IOS, ARCH-PC-DATASOURCE, ARCH-PC-VIEW]
related: [PLAT-MOB-IOS-AUTH, PLAT-MOB-IOS-BILLING, PLAT-MOB-NOTIF]
tags: [ios, uikit, foundation, interop, permissions, lifecycle, sharing]
---

# iOS Native Interop and Platform Adapters

## Boundary

Apple frameworks are delivery mechanisms behind common contracts. Put UIKit, Foundation,
Photos, AVFoundation and StoreKit usage in `iosMain`; expose portable state/results upward.

**Rule PLAT-MOB-IOS-INTEROP-BOUNDARY-01 (hard):** Apple SDK types MUST NOT appear in
UseCase, ViewModel, repository or common DataSource signatures.

Adapters should accept the minimum callbacks/state required. Business decisions—whether to
prompt, eligibility, throttling and follow-up navigation—remain in common UseCases/ViewModels.

## Presenting controllers and lifecycle

Resolve a currently active presentation context at action time rather than storing a stale
controller globally. UI presentation must run on the main thread and handle the absence of an
active scene/controller as an explicit failure or unavailable capability.

**Rule PLAT-MOB-IOS-INTEROP-UI-01 (hard):** UIKit presentation MUST occur on the main
thread from a currently active scene/controller; platform adapters must not retain obsolete
controllers across lifecycle transitions.

## Permissions

Model at least not-determined, denied/restricted and authorized states. Request permission
only in response to a justified user action. When denied, expose recovery state and an app
settings action where appropriate.

**Rule PLAT-MOB-IOS-PERM-01 (hard):** Every requested capability MUST have matching
usage-description/entitlement configuration and explicit denied/cancelled behavior.

## System actions

Settings, App Store links, browser/deep links and share sheets are thin adapters returning
success, cancelled, unavailable or failure. Validate URLs before opening. User cancellation
is not an unexpected crash/error.

## Photos and camera

Prefer system pickers that minimize broad library permission. Camera capture requires the
matching usage description and device capability checks. Convert selected content into a
portable value/owned file before crossing the adapter boundary; do not leak picker objects.

## Rating and orientation

The common layer decides when a rating request is eligible; iOS only invokes the native
request in an active scene. Orientation behavior must use supported scene/controller APIs and
must restore any temporary policy after the feature exits.

## Validation checklist

- [ ] Apple SDK types remain in iOS/platform implementation code.
- [ ] UI presentation uses active-scene/main-thread handling.
- [ ] Every permission has plist/entitlement, denial and recovery behavior.
- [ ] Success, cancellation, unavailable and failure are distinct outcomes.
- [ ] Deferred capability is disabled/hidden rather than a successful NoOp.
- [ ] Lifecycle recreation and background/foreground transitions are tested.

