---
id: PLAT-MOB-NOTIF
type: guide
layer: platform
platform: [mobile]
architecture: [pragmatic-clean]
requires: [ARCH-PC-USECASE, ARCH-PC-DI, PLAT-MOB-KOIN, PLAT-MOB-DATASTORE]
related: [PLAT-MOB-KMP, PLAT-MOB-KMP-WEB, PLAT-MOB-KMP-IOS, PLAT-MOB-IOS-INTEROP]
tags: [notifications, workmanager, scheduler, clockprovider, channels, kmp, background, ios]
---

# Notifications (WorkManager / Background Scheduling)

## Architecture Overview

```
commonMain (shared, testable)
  core/notifications/
    NotificationScheduler.kt          interface — schedule() / cancel()
    ScheduledNotification.kt          sealed class — one subclass per notification type
    ClockProvider.kt                  interface — abstraction for System.currentTimeMillis()
    NotificationPreferences.kt        interface — ephemeral deduplication state
    DefaultNotificationPreferences.kt DataStore implementation of NotificationPreferences
    domain/
      GetPendingNotificationsUseCase.kt  brain — what notifications are due right now
    di/
      NotificationsModule.kt          Koin module — common bindings

androidMain (Android-specific)
  core/notifications/
    WorkManagerNotificationScheduler.kt  implements NotificationScheduler via WorkManager
    NotificationWorker.kt                CoroutineWorker — calls UseCase, posts OS notifications
    NotificationChannelSetup.kt          registers Android notification channels
```

**Separation of concerns:**
- *What* to show → `GetPendingNotificationsUseCase` (commonMain, fully unit-testable)
- *When/how* to schedule the daily trigger → platform scheduler (androidMain)
- *How* to post the OS notification → platform worker (androidMain)
- *Which categories are enabled* → user preference synced to persistent store
- *Ephemeral deduplication state* → `NotificationPreferences` (DataStore, device-local)

iOS keeps the same common decision logic but uses separate Apple mechanisms for notification
delivery and optional background refresh. Local notification requests are scheduled with
`UNUserNotificationCenter`; remote push uses APNs capability/registration. Background app
refresh is best-effort and must not be treated as an exact periodic scheduler.

---

## `NotificationScheduler` Interface

```kotlin
interface NotificationScheduler {
    fun schedule()   // idempotent — safe to call multiple times
    fun cancel()     // call on sign-out or when all categories are disabled
}
```

**Android implementation:** `WorkManagerNotificationScheduler`
- Schedules a `PeriodicWorkRequest` targeting a fixed daily time
- Uses `ExistingPeriodicWorkPolicy.KEEP` — does not reset if already scheduled
- Add `NetworkType.CONNECTED` constraint if the use case requires a network call
- `schedule()` is called after sign-in; `cancel()` is called on sign-out

**Web (wasmJs) — Not supported:**
Browsers do not expose persistent background scheduling APIs. Register a
`NoOpNotificationScheduler` in the web Koin module so Koin can resolve
`NotificationScheduler` on the web target. See `PLAT-MOB-KMP-WEB`.

**iOS:**

- Request/inspect notification authorization through `UNUserNotificationCenter`.
- Map not-determined, provisional, authorized, denied and other supported states explicitly.
- Use stable identifiers for local requests so rescheduling replaces rather than duplicates.
- Add push entitlements and APNs registration only when remote push is in product scope.
- Use background refresh only for best-effort content refresh; delivery must not depend on an
  exact background execution time.

**Rule PLAT-MOB-NOTIF-IOS-01 (hard):** iOS local notification scheduling MUST use the
notification-center request API; background refresh MUST NOT be presented as exact delivery.

**Rule PLAT-MOB-NOTIF-IOS-02 (hard):** Notification permission, push registration and
background refresh are separate capabilities and MUST have separate configuration/state.

---

## `ScheduledNotification` Sealed Class

Each notification type is a subclass of `ScheduledNotification`:

```kotlin
sealed class ScheduledNotification(
    val id: Int,         // stable, non-random — ensures replace-not-stack on re-delivery
    val title: String,
    val body: String,
    val channelId: String
)

class MyNotification(param: String) : ScheduledNotification(
    id = 1001,              // stable ID — see ID range rules below
    title = "...",
    body = "... $param ...",
    channelId = CHANNEL_DEFAULT
)
```

**Stable ID rules:**
- Assign stable integer IDs by range per category. Example: category A = 1001–1999, category B = 2000–2999.
- Document the ranges in the sealed class file.
- Stable IDs ensure `NotificationManager.notify(id, …)` replaces the existing notification rather than stacking a duplicate.
- Do NOT use `Random.nextInt()` for notification IDs.

---

## `GetPendingNotificationsUseCase`

The "brain" of the notification system. Lives in `commonMain`. Returns a list of
`ScheduledNotification` instances that are due right now.

**Rule PLAT-MOB-NOTIF-CLOCK-01 (hard):** The use case MUST NOT call
`System.currentTimeMillis()` directly. All time access goes through `ClockProvider`
so tests can control the clock without mocking.

```kotlin
interface ClockProvider {
    fun getCurrentTimeMillis(): Long
}

// Production
class SystemClockProvider : ClockProvider {
    override fun getCurrentTimeMillis(): Long = System.currentTimeMillis()
}

// Tests
class FakeClockProvider(private val fixedTimeMillis: Long) : ClockProvider {
    override fun getCurrentTimeMillis(): Long = fixedTimeMillis
}
```

**Rule PLAT-MOB-NOTIF-DELIVERY-01 (hard):** `GetPendingNotificationsUseCase` MUST
return *what* to show. It MUST NOT call `NotificationManager` or interact with
WorkManager. Those responsibilities belong in the platform worker.

**Prioritization rule (example):** If high-priority notification types are due
simultaneously with low-priority ones, enforce priority inside the use case — not
in the delivery layer.

---

## `NotificationPreferences` (Ephemeral State)

Stores device-local state that does not belong in a remote store:
- Last-sent timestamps for deduplication
- Per-item milestone tracking (e.g. "which countdown milestone was last sent")
- One-time prompt flags

**Adding a new preference:**
1. Add the `get`/`set` pair to the `NotificationPreferences` interface
2. Implement in `DefaultNotificationPreferences` using DataStore (follow `PLAT-MOB-DATASTORE`)
3. Update any test fakes used for this interface

---

## DI Wiring

### Common bindings

```kotlin
fun notificationsModule() = module {
    factoryOf(::GetPendingNotificationsUseCase)
    single<ClockProvider> { SystemClockProvider() }
    single<NotificationPreferences> { DefaultNotificationPreferences(get()) }
}
```

### Android bindings

```kotlin
fun androidModule(): Module = module {
    workerOf(::NotificationWorker)
    single<NotificationScheduler> { WorkManagerNotificationScheduler(androidContext()) }
}
```

### Lifecycle

| Event | Action |
|-------|--------|
| Sign-in completes | `notificationScheduler.schedule()` |
| Sign-out | `notificationScheduler.cancel()` |
| All categories disabled | `notificationScheduler.cancel()` |

---

## WorkManager Setup (Android)

- [ ] Dependencies: `androidx.work:work-runtime-ktx` + `io.insert-koin:koin-androidx-workmanager`
- [ ] Disable WorkManager auto-init in `AndroidManifest.xml`:
  ```xml
  <provider
      android:name="androidx.startup.InitializationProvider"
      android:authorities="${applicationId}.androidx-startup"
      android:exported="false"
      tools:node="merge">
      <meta-data
          android:name="androidx.work.WorkManagerInitializer"
          android:value="androidx.startup"
          tools:node="remove" />
  </provider>
  ```
- [ ] Call `workManagerFactory()` **inside** the `initKoin` lambda — not after it
- [ ] Call `NotificationChannelSetup.createChannels(context)` from `Application.onCreate()` after `initKoin`
- [ ] Register worker with `workerOf(::NotificationWorker)` in the android module

---

## Unit Testing

Use `FakeClockProvider` to control time. No mocking needed — construct it directly.

**Required scenarios per notification type:**
- Fires when condition is met
- Does not fire when category is disabled
- Deduplication: does not fire when already sent for this milestone
- Prioritization: high-priority type suppresses low-priority when both are due

---

## Validation Checklist

After adding a new notification type:
- [ ] New subclass added to `ScheduledNotification` with stable, documented `id`
- [ ] Trigger logic added to `GetPendingNotificationsUseCase` behind correct category flag
- [ ] If deduplication needed: new `NotificationPreferences` methods added and implemented
- [ ] Unit tests written for all scenarios above
- [ ] No `System.currentTimeMillis()` calls in the use case

After adding a new platform:
- [ ] New `NotificationScheduler` implementation in platform source set
- [ ] Bound as `single<NotificationScheduler>` in platform DI module
- [ ] No commonMain code changed
- [ ] Permission states, entitlements and delivery mechanism match the platform capability
- [ ] iOS stable identifier replacement/cancellation and denied behavior are tested

---

## Common Mistakes

**Using random notification IDs** — stacks duplicate notifications instead of replacing.

**Calling `workManagerFactory()` after `initKoin`** — crashes with "WorkManager is not initialized".

**Putting delivery logic in the UseCase** — the use case returns *what* to show; the worker does the posting.

**Forgetting to disable WorkManager auto-init** — double-initialization causes `IllegalStateException` at startup.

**Mocking `ClockProvider`** — use `FakeClockProvider` directly; mocking is unnecessary complexity.
