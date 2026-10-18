---
id: PLAT-MOB-IOS-INTEROP
type: guide
layer: platform
platform: [mobile]
architecture: [pragmatic-clean]
requires: [PLAT-MOB-KMP-IOS, ARCH-PC-DATASOURCE, ARCH-PC-VIEW]
related: [PLAT-MOB-IOS-AUTH, PLAT-MOB-IOS-BILLING, PLAT-MOB-NOTIF]
tags: [ios, uikit, foundation, interop, permissions, lifecycle, sharing]
status: active
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

## Popover-capable controllers on iPad

Some controllers can present as a popover on iPad and, on current iPadOS, UIKit may still
force one. `UIActivityViewController` (share sheets) and `UIAlertController` with the
`actionSheet` style are the common cases. Without an anchor, UIKit raises an
`NSGenericException` ("UIPopoverPresentationController should have a non-nil sourceView or
barButtonItem") and the app crashes.

**Rule PLAT-MOB-IOS-POPOVER-01 (hard):** Any UIKit controller that can present as a popover on
iPad (UIActivityViewController, UIAlertController actionSheet) MUST have its
popoverPresentationController anchored (sourceView + sourceRect, or barButtonItem) before
presentation — setting a non-popover modalPresentationStyle alone is not sufficient, since UIKit
may still force a popover. Enforced by: executor, reviewer. Violation: "Violates
PLAT-MOB-IOS-POPOVER-01 — popover-capable controller presented without an anchor crashes on iPad
(NSGenericException)."

```kotlin
controller.popoverPresentationController?.let { popover ->
    popover.sourceView = presenter.view
    popover.sourceRect = presenter.view.bounds
}
presenter.presentViewController(controller, animated = true, completion = null)
```

*Violation signal:* iPad handled only by forcing `modalPresentationStyle` (e.g. `FullScreen`)
with no popover anchor.

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
- [ ] Popover-capable controllers (share sheets, action sheets) are anchored before presentation,
      not just given a non-popover presentation style.
