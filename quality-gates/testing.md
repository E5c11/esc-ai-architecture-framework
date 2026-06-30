---
id: QG-TESTING
type: guide
layer: quality-gates
platform: [all]
architecture: [all]
requires: [CORE-TESTING, CORE-COUPLING]
related: [QG-REVIEW, BUILD-COVERAGE, BUILD-STATIC-ANALYSIS]
tags: [testing, unit-tests, integration, mocking, coverage, philosophy]
---

# Testing Philosophy

## What tests are for

Tests verify behaviour, not implementation. A test that breaks when you rename
a private method is not testing behaviour — it is testing structure. A test that
passes when the method produces the wrong output is not protecting anything.

Write tests to answer: "If I change this behaviour, will I know?" Not: "Can I
prove I touched this line?"

## Test types and when to use them

| Type | Tests | Scope | Speed |
|---|---|---|---|
| Unit | One class, all collaborators mocked | Logic only | Fast — no I/O |
| Integration | Multiple real classes, external system (DB, file) | Data access, wiring | Medium |
| Slice/component | Thin layer, framework wired but not full stack | HTTP boundary, UI route | Medium |
| End-to-end | Full stack, real environment | Critical user journeys | Slow |

**Rule QG-TEST-SCOPE-01 (hard):** Unit tests MUST mock all collaborators outside
the class under test. A unit test that starts a database, HTTP server, or file
system is a slow integration test with poor diagnostics — the failure does not
point at the unit that is broken.

**Rule QG-TEST-SCOPE-02 (hard):** Integration tests MUST run against real
infrastructure — a real database, a real file system — not mocks. Mocking a
database in an integration test eliminates the primary value of the test: proving
that the query or schema works.

## What to test in each layer

### Business logic (Service / UseCase)
Test every branch of business logic:
- Happy path returns expected data
- Every named error condition throws / returns the expected error
- Side effects (saves, notifications) happen or don't happen based on the condition
- Time-dependent logic uses a fixed time and asserts against it

### HTTP boundary (Controller / Presenter)
Test the HTTP contract:
- Correct status code for success
- Correct status code when the service throws a known error
- Authentication gate — unauthenticated request returns 401
- Input validation — invalid request body returns 400 and service is NOT called

### Data access (DataSource / Repository)
Test custom queries:
- Custom `@Query` or `onSnapshot` logic against a real data store
- Derived queries provided by frameworks (Spring Data, Firestore SDK) do NOT need tests

### UI components
Test observable behaviour from the user's perspective:
- Renders without error
- Correct element appears when loading / error / data state
- User interaction (click, input) produces the expected outcome

Do not test internal state or component implementation details.

## What not to test

- Derived or generated methods (Spring Data `findBy*`, Room-generated DAOs,
  Compose runtime behaviour, Kotlin data class `copy`)
- Framework infrastructure (Spring DI wiring, Firebase SDK internals, Hibernate lazy-loading)
- Pure data holders (DTO fields, state data classes with no logic)
- Pure mappings with no branching (a mapper that converts field A to field B in one line)

Testing these produces coverage numbers but no diagnostic value.

## Naming

**Rule QG-TEST-NAME-01 (soft):** Test names SHOULD be written as complete sentences
describing the expected behaviour, not the method being called.

```
// ✅ — describes what the system does
"register throws CONFLICT when email already exists"
"login returns 401 for invalid credentials"
"container shows LoadingSpinner while data is loading"

// ✗ — describes the code, not the behaviour
"testRegister"
"loginFailTest"
"testGetUser_null"
```

## Arrange / Act / Assert

Every test follows three sections: arrange the preconditions, act on the system
under test, assert the outcome. The sections are separated by a blank line.
Never mix assertion into the arrange phase.

## Mocking philosophy

**Rule QG-TEST-MOCK-01 (soft):** Mock at architectural boundaries, not within
a layer. If the Service → DataSource boundary is the boundary, mock the DataSource
interface. Do not mock private methods within the same class.

**Rule QG-TEST-MOCK-02 (hard):** Never mock the class under test. Mocking the
subject of the test means you are not testing the real implementation.

**Rule QG-TEST-MOCK-03 (soft):** Verify side effects (`save` was called,
notification was sent) with `verify()` calls. Do not rely on coverage to prove
a side effect occurred.

## Test fixtures

Shared test data factories belong in a dedicated package (`mocks/`, `fixtures/`,
`testUtils/`) — not constructed inline in test methods. Inline construction
duplicates setup, hides what varies between tests, and causes widespread test
failures when a DTO constructor changes.

```kotlin
// ✅ — shared factory, one place to update
val user = UserMocks.defaultUser(email = "test@example.com")

// ✗ — duplicated inline in every test
val user = UserEntity(email = "test@example.com", firstName = "Test", ...)
```

## Coverage as a floor, not a goal

Coverage gates exist to catch untested code at submission time — not to inflate
a percentage. 100% coverage with trivial assertions is worse than 75% with
thorough behavioural tests.

See `BUILD-COVERAGE` for threshold values and standard exclusions.

## Platform-specific testing details

- **Mobile (Kotlin/KMP):** Kover for coverage; Mokkery or Mockk for mocking; `@Test` with JUnit4/5
- **Backend (Spring Boot):** `@ExtendWith(MockKExtension::class)` for service tests; `@WebMvcTest` for controller slice tests; `@DataJpaTest` for DataSource tests
- **Web (React/TypeScript):** Vitest + React Testing Library for component tests; MSW for API mocking
