---
id: PLAT-MOB-DATASTORE
type: guide
layer: platform
platform: [mobile]
architecture: [pragmatic-clean]
requires: [PLAT-MOB-KMP, PLAT-MOB-KOIN]
related: [PLAT-MOB-ROOM, ARCH-PC-DATASOURCE, PLAT-MOB-SECURE-STORAGE]
tags: [datastore, preferences, kmp, testing, fakeDataStore, coroutines, flow]
status: active
---

# DataStore<Preferences>

## Overview

`DataStore<Preferences>` is used for lightweight, device-local key-value persistence
that does not need a relational structure. Typical uses: onboarding flags, deduplication
timestamps, user preferences that are not synced remotely.

**Not a replacement for Room.** Use DataStore for flat key-value state; use Room for
structured, queryable, or relational data.

---

## Key Definitions

Define all keys in a companion object or top-level `object` in the preferences implementation:

```kotlin
private companion object {
    val KEY_LAST_SYNC = longPreferencesKey("last_sync_timestamp")
    val KEY_ONBOARDING_DONE = booleanPreferencesKey("onboarding_complete")
    val KEY_DISMISSED_IDS = stringSetPreferencesKey("dismissed_ids")
}
```

```rule
id: PLAT-MOB-DS-KEY-01
statement: All DataStore keys MUST be declared as typed `preferencesKey<T>()` constants.
type: hard
scope: behavior
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-DS-KEY-01 — All DataStore keys MUST be declared as typed `preferencesKey<T>()` constants.
```

Never use raw strings at the call site.

---

## Read Patterns

### One-shot read (suspend)

```kotlin
suspend fun getLastSyncAt(): Long {
    return dataStore.data.first()[KEY_LAST_SYNC] ?: 0L
}
```

### Flow-based read (reactive)

```kotlin
fun observeOnboardingComplete(): Flow<Boolean> {
    return dataStore.data.map { prefs -> prefs[KEY_ONBOARDING_DONE] ?: false }
}
```

---

## Write Patterns

### Simple write

```kotlin
suspend fun setOnboardingComplete(complete: Boolean) {
    dataStore.edit { prefs ->
        prefs[KEY_ONBOARDING_DONE] = complete
    }
}
```

### Conditional / null write (skip if null)

```kotlin
suspend fun updatePartial(newTimestamp: Long?, newFlag: Boolean?) {
    dataStore.edit { prefs ->
        newTimestamp?.let { prefs[KEY_LAST_SYNC] = it }
        newFlag?.let { prefs[KEY_ONBOARDING_DONE] = it }
    }
}
```

### Explicit removal

```kotlin
suspend fun clearDismissedId(id: String) {
    dataStore.edit { prefs ->
        val existing = prefs[KEY_DISMISSED_IDS] ?: emptySet()
        prefs[KEY_DISMISSED_IDS] = existing - id
    }
}
```

---

## DI Registration

`DataStore<Preferences>` instances MUST be declared as `single` (`PLAT-MOB-KOIN-SINGLE-02`, defined in `platforms/mobile/koin.md`).

```kotlin
// In platform or core DI module
single<DataStore<Preferences>> {
    PreferenceDataStoreFactory.create(
        corruptionHandler = ReplaceFileCorruptionHandler { emptyPreferences() },
        produceFile = { androidContext().dataStoreFile("app_preferences.preferences_pb") }
    )
}
```

### Native/iOS construction

On Native, construct the DataStore with a path inside the application support/files
container. Path selection is a platform adapter responsibility; preference read/write logic
remains common.

**Rule PLAT-MOB-DS-NATIVE-01 (hard):** Native DataStore files MUST live in an
application-owned persistent container and use one stable path per logical store.

**Rule PLAT-MOB-DS-SECRET-01 (hard):** Access tokens, refresh tokens and cryptographic
keys MUST NOT be stored in DataStore. Use `PLAT-MOB-SECURE-STORAGE`.

Add an iOS integration test for construction, write/read and recreation using a temporary
application-owned test path; common `FakeDataStore` tests do not validate filesystem wiring.

---

## Testing with `FakeDataStore`

`DataStore<T>` is an interface, but its `edit {}` extension function and `Preferences`
manipulation depend on internal types that cannot be replicated cleanly via generated
mocks. **Use a `FakeDataStore` backed by `MutableStateFlow` instead.**

```kotlin
class FakeDataStore(
    initial: Preferences = emptyPreferences()
) : DataStore<Preferences> {
    private val _data = MutableStateFlow(initial)
    override val data: Flow<Preferences> = _data
    override suspend fun updateData(
        transform: suspend (t: Preferences) -> Preferences
    ): Preferences {
        val updated = transform(_data.value)
        _data.value = updated
        return updated
    }
}
```

- `data` replays the current value on each collection (matches real DataStore behaviour)
- `edit {}` calls `updateData` internally — no extra stubbing needed
- Each test gets a clean `FakeDataStore` — JUnit4 creates a new class instance per test method

```rule
id: PLAT-MOB-DS-FAKE-01
statement: Each Gradle module that tests a DataStore-backed class MUST have its own copy of `FakeDataStore` in its `commonTest` source set.
type: hard
scope: testing
enforced_by: [reviewer]
violation_message: Violates PLAT-MOB-DS-FAKE-01 — Each Gradle module that tests a DataStore-backed class MUST have its own copy of `FakeDataStore` in its `commonTest` source set.
```

KMP test code cannot be shared across module boundaries.

---

## Required Test Scenarios

For every DataStore-backed preferences class, write tests covering:

### 1. Default when empty

```kotlin
@Test
fun `getLastSyncAt - RETURNS 0 WHEN not set`() = runTest {
    val result = preferences.getLastSyncAt()
    result shouldBeEqualTo 0L
}
```

### 2. Write → read round-trip

```kotlin
@Test
fun `getLastSyncAt - RETURNS timestamp WHEN previously written`() = runTest {
    preferences.setLastSyncAt(1234567890L)
    preferences.getLastSyncAt() shouldBeEqualTo 1234567890L
}
```

### 3. Flow emission

```kotlin
@Test
fun `observeOnboardingComplete - EMITS value WHEN updated`() = runTest {
    preferences.setOnboardingComplete(true)
    preferences.observeOnboardingComplete().test {
        awaitItem() shouldBeEqualTo true
        cancelAndIgnoreRemainingEvents()
    }
}
```

### 4. Null / removal

```kotlin
@Test
fun `clearDismissedId - REMOVES id WHEN present`() = runTest {
    preferences.addDismissedId("id_001")
    preferences.clearDismissedId("id_001")
    preferences.getDismissedIds().shouldBeEmpty()
}
```

### 5. Accumulation

```kotlin
@Test
fun `addDismissedId - APPENDS to set WHEN called multiple times`() = runTest {
    preferences.addDismissedId("id_001")
    preferences.addDismissedId("id_002")
    preferences.getDismissedIds() shouldBeEqualTo setOf("id_001", "id_002")
}
```

### 6. Null-field skipping (partial updates)

```kotlin
@Test
fun `updatePartial - DOES NOT overwrite existing WHEN new field is null`() = runTest {
    preferences.setLastSyncAt(1000L)
    preferences.updatePartial(newTimestamp = null, newFlag = true)
    preferences.getLastSyncAt() shouldBeEqualTo 1000L
}
```

---

## Verify Step

DataStore tests do **not** use `verifySuspend` — there is no mock to verify against.
The assertion on the read-back IS the verification. For Flow reads, Turbine's
`awaitItem()` serves as both assertion and verification.

**Rule:** Always call `cancelAndIgnoreRemainingEvents()` at the end of a Flow test —
`MutableStateFlow` never completes, so a test without this will hang.

---

## Known Limitations of `FakeDataStore`

| Scenario | Why untestable in commonTest |
|----------|------------------------------|
| File I/O errors / corruption | `FakeDataStore` never throws `IOException` |
| Concurrent write serialization | `MutableStateFlow` doesn't enforce sequential access |
| DataStore contract changes | Fake is decoupled from library internals |

Exception-handling paths require instrumented tests or a throwable variant of `FakeDataStore`.

---

## Validation Checklist

- [ ] All keys declared as typed `preferencesKey<T>()` constants (PLAT-MOB-DS-KEY-01)
- [ ] `DataStore<Preferences>` registered as `single` in Koin
- [ ] `FakeDataStore` copied into module's `commonTest` — not imported from another module
- [ ] `FakeDataStore` instantiated at class level (fresh per test method)
- [ ] Every read function has a "default when empty" test
- [ ] Every write function has a write → read round-trip test
- [ ] Every Flow function uses Turbine with `cancelAndIgnoreRemainingEvents()`
- [ ] No `mock()` for DataStore — use `FakeDataStore`
- [ ] Native file path is application-owned and stable; recreation test passes
- [ ] Sensitive credentials use secure storage rather than DataStore

---

## Common Mistakes

```kotlin
// WRONG — mocking DataStore
private val dataStore: DataStore<Preferences> = mock()

// CORRECT
private val fakeDataStore = FakeDataStore()

// WRONG — Flow test hangs without cancel
preferences.observeX().test { awaitItem() }

// CORRECT
preferences.observeX().test {
    awaitItem() shouldBeEqualTo expected
    cancelAndIgnoreRemainingEvents()
}

// WRONG — divergent FakeDataStore
class MyFakeStore : DataStore<Preferences> { /* custom logic */ }

// CORRECT — copy the canonical FakeDataStore verbatim into the module's commonTest
```
