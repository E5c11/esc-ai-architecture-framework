---
id: ARCH-BE-SERVICE
type: rules
layer: architectures
platform: [backend]
architecture: backend-service
requires: [ARCH-BE, CORE-DI, CORE-ERROR]
related: [ARCH-BE-CONTROLLER, ARCH-BE-DATASOURCE, ARCH-BE-ERROR, PLAT-BE-SPRING]
tags: [service, business-logic, transactions, time-provider, dto, token, refresh-token, rotation]
---

# Service Layer

## Responsibility

The service owns all business logic for a domain. It:
- Validates business preconditions
- Reads and writes through the DataSource layer
- Enforces business rules
- Maps entities to DTOs before returning

A service method owns the full operation from start to finish. It must not care
about HTTP.

## Rules

**Rule SVC-TIME-01 (hard):** Time-dependent logic MUST use an injected `TimeProvider`
abstraction. Direct calls to `Instant.now()`, `LocalDate.now()`, or
`System.currentTimeMillis()` inside a service method are forbidden. Direct time
calls make tests non-deterministic.

> Violation: `val now = Instant.now()`
> Fix: inject `TimeProvider` via constructor and call `timeProvider.now()`

Inject `TimeProvider` whenever the method:
- Records a timestamp (`createdAt`, `updatedAt`, `processedAt`)
- Computes an expiry (`timeProvider.now().plusSeconds(ttl)`)
- Compares a stored time to now (`stored.expiresAt.isBefore(timeProvider.now())`)

**Rule SVC-RETURN-01 (hard):** Service methods MUST return DTOs or primitives to
their callers. Returning a JPA entity couples the HTTP contract to the JPA schema
and can trigger unexpected lazy-loading outside a transaction.

> Violation: `fun getUser(): UserEntity`
> Fix: map the entity to a response DTO before returning

Map inside the service using a private extension function in the same file:
```
private fun {Domain}Entity.toResponse() = {Domain}Response(...)
```

**Rule SVC-TX-01 (hard):** `@Transactional` belongs on service methods — never on
DataSource/repository methods. Transaction scope must span the full operation,
which is defined at the service layer. A transaction on a repository method creates
an incomplete boundary that does not cover the surrounding service logic.

**Rule SVC-TX-02 (hard):** Any service method that writes to more than one table
MUST be annotated with `@Transactional`. Without a transaction, a failure after
the first write leaves the database in a partially-written state.

**Rule SVC-ERROR-01 (hard):** Known business errors MUST be thrown as
`ResponseStatusException` with the appropriate HTTP status from the service layer.
Returning null or a flag to signal an error, and letting the controller decide the
status, is a violation. See `ARCH-BE-ERROR` for the full two-tier error strategy.

**Rule SVC-INJECT-01 (hard):** Services MUST use constructor injection. `@Autowired`
field injection is forbidden. Constructor injection makes dependencies explicit and
allows mock injection in unit tests without a Spring context.

**Rule SVC-REPO-01 (soft):** Inject `JpaRepository` directly unless a wrapper is
clearly justified. A `{Domain}Store` wrapper is warranted only when:
(a) a single service operation requires 3+ separate JPA repository calls,
(b) the operation must combine data from multiple repositories, or
(c) a native/complex JPQL query benefits from isolation.
Creating a wrapper for a single `findBy*` call adds indirection with no benefit.

**Rule SVC-NAMING-01 (soft):** Service class: `{Domain}Service`. Methods: verb-noun
pattern (`login`, `register`, `updateProfile`, `createSubject`).

## Sensitive token handling

Any service that issues and persists its own long-lived tokens — refresh tokens,
password-reset links, email-verification codes, API keys — is running a credential
store, not just writing a business record. The same discipline applied to
passwords applies here, regardless of which HTTP framework or JWT library sits on
top.

**Rule SVC-TOKEN-01 (hard):** A long-lived token persisted by the service MUST be
stored as a one-way hash (SHA-256 or stronger), never in raw form. Look up an
incoming token by hashing it and querying on the hash column. A raw token sitting
in a database row is equivalent to a plaintext password — a database leak hands
the attacker a live, immediately usable credential with no cracking required.

> Violation: `RefreshTokenEntity(tokenHash = refreshToken, ...)`
> Fix: `RefreshTokenEntity(tokenHash = sha256(refreshToken), ...)` — return the raw
> token to the caller once at issuance; never store or log it again.

**Rule SVC-TOKEN-02 (hard):** An exchange/refresh operation MUST invalidate the
presented token as part of issuing its replacement (single-use rotation). Delete
or mark the stored token row consumed once it passes validation, before generating
the new pair. Without rotation, a stolen token stays valid for its entire
remaining lifetime even after the legitimate client has moved past it — rotation
caps a leaked token's usable window at one exchange, and a second exchange attempt
against an already-deleted token hash is a reliable replay signal.

> Violation: validate the token, issue a new pair, and leave the old row in place
> ("it'll expire on its own eventually").
> Fix: `refreshTokenRepository.delete(stored) // single-use rotation` before
> calling the token-issuance path.

**Rule SVC-TOKEN-03 (hard):** A token validity check MUST test both explicit
revocation and expiry — never one in isolation. A token can be individually
revoked (logout, admin action, detected compromise) long before its natural
expiry, and a token can simply outlive its TTL without ever being revoked.
Checking only `expiresAt` misses revoked-but-unexpired tokens; checking only
`revoked` misses tokens that expired on schedule.

> Violation: `if (stored.expiresAt.isBefore(timeProvider.now())) throw ...`
> (revocation never checked)
> Fix: `if (stored.revoked || stored.expiresAt.isBefore(timeProvider.now()))
> throw ResponseStatusException(HttpStatus.UNAUTHORIZED, "Token expired or revoked")`

## Business error HTTP status guide

| Condition | Status |
|---|---|
| Resource not found | 404 NOT_FOUND |
| Already exists / duplicate | 409 CONFLICT |
| Bad credentials | 401 UNAUTHORIZED |
| Action not allowed for this user | 403 FORBIDDEN |
| Invalid business input | 400 BAD_REQUEST |

## Testing

Service tests use Mockk without a Spring context (`@ExtendWith(MockKExtension::class)`).
All dependencies are `@MockK`. `TimeProvider` is always stubbed to a fixed `Instant`
before each test. Test every service method for: happy path, all documented error
conditions, and side effect verification (save called / not called).
