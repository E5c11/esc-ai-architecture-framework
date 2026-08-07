---
id: ORCH-BE-ENDPOINT
type: orchestrator
layer: feature-orchestrators
platform: [backend]
architecture: [backend-service]
goal: "Implement a complete REST endpoint with all backend-service layers wired and tested"
requires:
  - CORE-DI
  - CORE-ERROR
  - CORE-NAMING
  - CORE-TESTING
  - PAT-DATA-ACCESS
  - ARCH-BE
  - ARCH-BE-CONTROLLER
  - ARCH-BE-SERVICE
  - ARCH-BE-DATASOURCE
  - ARCH-BE-ENTITY
  - ARCH-BE-ERROR
  - PLAT-BE-SPRING
  - PLAT-BE-JPA
  - PLAT-BE-SECURITY
  - QG-TESTING
related: [QG-REVIEW]
tags: [backend, endpoint, spring-boot, jpa, rest, end-to-end]
status: active
---

# Implement Backend REST Endpoint (Backend-Service)

## Goal

Produce a complete, tested endpoint: migration → entity → DataSource → DTOs →
service → controller. Every layer is implemented in persistence-to-boundary order.

## Before you start

Read all documents listed in `requires` above. Pay particular attention to the
dependency direction rule in `ARCH-BE`: outer layers know about inner layers;
inner layers know nothing about outer layers.

---

## Phase 1 — Migration and Entity

**Goal:** Database schema is in place; entity matches it exactly.

Read: `ARCH-BE-ENTITY`, `PLAT-BE-JPA`

### Steps

1. Determine the next Flyway version number: check `src/main/resources/db/migration/`
2. Write the migration SQL (`V{n}__<description>.sql`):
   - `UUID PRIMARY KEY DEFAULT gen_random_uuid()`
   - `TIMESTAMPTZ NOT NULL DEFAULT now()` for both timestamp columns
   - Add indexes for all `WHERE`/`JOIN` columns
3. Write the entity class `{Domain}Entity.kt`:
   - Regular `class`, not `data class`
   - `@GeneratedValue(strategy = GenerationType.UUID)` on `id`
   - `@Column(updatable = false)` on `createdAt`
   - `@ManyToOne(fetch = FetchType.LAZY)` for all associations
   - `equals`/`hashCode` comparing `id` only
4. Commit migration and entity in the same commit (ENT-MIGRATION-01)

### Validation

- [ ] Migration file present; version number is next in sequence
- [ ] `./gradlew flywayMigrate` applies cleanly (requires local DB running)
- [ ] Entity class is not a `data class`
- [ ] No business logic methods on the entity
- [ ] `createdAt` has `@Column(updatable = false)`
- [ ] All `@ManyToOne` and `@OneToOne` associations use `FetchType.LAZY`

---

## Phase 2 — DataSource

**Goal:** Data access interface is defined; correct form chosen (direct vs wrapper).

Read: `ARCH-BE-DATASOURCE`, `PLAT-BE-JPA`

### Steps

1. Create `{Domain}Repository : JpaRepository<{Domain}Entity, UUID>` in the domain package
2. Add derived queries (`findBy*`, `existsBy*`) and `@Query` methods as needed
3. Decision — custom Store wrapper justified? (see `ARCH-BE-DATASOURCE` decision tree):
   - Default: inject `{Domain}Repository` directly in the service (REP-WHEN-01)
   - Exception: if 3+ JPA calls are needed for one logical result, create
     `{Domain}Store` interface + `{Domain}StoreImpl`
4. If creating a Store: define the interface first; implementation is `@Repository`

### Validation

- [ ] No `@Transactional` on repository methods (REP-TX-01)
- [ ] Repository methods return entities — never DTOs (REP-RETURN-01)
- [ ] Custom Store created only when warranted by REP-WHEN-01
- [ ] If Store exists: interface defined; implementation is injectable

---

## Phase 3 — DTOs

**Goal:** Request and response shapes defined; no entity types cross the service boundary.

### Steps

1. Create request DTO(s) in `{domain}/dto/`:
   - Add Bean Validation annotations (`@NotBlank`, `@NotNull`, `@Size`, etc.)
2. Create response DTO(s) in `{domain}/dto/`
3. Decide on mapping location: private extension function in the service file
   (`private fun {Domain}Entity.toResponse(): {Domain}Response`)

### Validation

- [ ] No JPA entity types appear in any DTO
- [ ] Request DTO fields have appropriate Bean Validation constraints
- [ ] Response DTO is a plain data class — no Hibernate imports

---

## Phase 4 — Service

**Goal:** Business logic is complete, transactional, and returns only DTOs.

Read: `ARCH-BE-SERVICE`, `ARCH-BE-ERROR`, `PLAT-BE-SPRING`

### Steps

1. Create `{Domain}Service.kt` annotated with `@Service`
2. Inject dependencies via constructor (no `@Autowired` fields)
3. Inject `TimeProvider` for any timestamp-producing operations
4. For each operation:
   - Read methods: fetch entity, map to DTO, return DTO
   - Write methods: annotate with `@Transactional`; use `timeProvider.now()` for timestamps
   - Validation: throw `ResponseStatusException(HttpStatus.X, "message")` for known errors
5. Add private mapping extension: `private fun {Domain}Entity.toResponse() = ...`
6. Ensure multi-step writes are in a single `@Transactional` method (SVC-TX-02)

### Validation

- [ ] No `Instant.now()` or `System.currentTimeMillis()` — uses `timeProvider.now()` (SVC-TIME-01)
- [ ] Service returns DTOs — never JPA entities (SVC-RETURN-01)
- [ ] All write methods annotated `@Transactional` (SVC-TX-01)
- [ ] Known errors throw `ResponseStatusException` with correct `HttpStatus` (SVC-ERROR-01)
- [ ] Constructor injection only (SVC-INJECT-01)
- [ ] Service MUST NOT import `org.springframework.web.*` or `org.springframework.http.HttpStatus`
  (only `ResponseStatusException` is acceptable from the web package)

---

## Phase 5 — Controller

**Goal:** HTTP boundary routes requests to the service and maps results to responses.

Read: `ARCH-BE-CONTROLLER`, `PLAT-BE-SPRING`, `PLAT-BE-SECURITY`

### Steps

1. Add `{Domain}Paths` object to `ApiConstants.kt` in `:core:api` before writing the controller:
   ```kotlin
   object {Domain}Paths {
       const val BASE = "$API_V1/{domain}"
       // one const per method path
   }
   ```
2. Create `{Domain}Controller.kt`:
   - `@RestController @RequestMapping({Domain}Paths.BASE)`
   - Constructor injection of `{Domain}Service` only
   - One method per endpoint; method named by action (not HTTP verb)
   - `@Valid` on every `@RequestBody` parameter
   - `@ResponseStatus(HttpStatus.CREATED)` on POST; `@ResponseStatus(HttpStatus.NO_CONTENT)` on DELETE
   - For protected endpoints: `@AuthenticationPrincipal userId: UUID` parameter

### Validation

- [ ] No logic beyond request parsing and service delegation (CTRL-LOGIC-01)
- [ ] Returns DTO — never a JPA entity (CTRL-RETURN-01)
- [ ] `@Valid` on all `@RequestBody` parameters (CTRL-VALIDATION-01)
- [ ] Status codes via `HttpStatus` enum (CTRL-STATUS-01)
- [ ] Constructor injection only (CTRL-INJECT-01)
- [ ] No literal `/v1` or path strings — uses `{Domain}Paths` constants (CTRL-PATH-01)

---

## Phase 6 — Error handling

**Goal:** `GlobalExceptionHandler` exists; all error responses use `ErrorResponse`.

Read: `ARCH-BE-ERROR`, `PLAT-BE-SPRING`

### Steps (first endpoint in the project only)

1. Create `ErrorResponse(status: Int, message: String)` in `core/error/`
2. Create `GlobalExceptionHandler` in `config/`:
   - Handle `ResponseStatusException` — forward status and message
   - Handle `MethodArgumentNotValidException` — collect field errors, return 400
   - Handle `Exception` (catch-all) — log with stack trace, return 500

### Steps (subsequent endpoints)

No changes needed — the handler is already in place. Verify the new service
methods throw `ResponseStatusException` as required.

### Validation

- [ ] `GlobalExceptionHandler` exists with catch-all `@ExceptionHandler(Exception::class)` (ERR-UNKNOWN-01)
- [ ] Catch-all logs with `logger.error("...", e)` before returning (ERR-LOG-01)
- [ ] All error responses use `ErrorResponse(status, message)` (ERR-RESPONSE-01)

---

## Phase 7 — Tests

**Goal:** Service unit tests and controller slice tests cover all documented behaviours.

Read: `QG-TESTING`, `PLAT-BE-SPRING`

### Service unit tests (`{Domain}ServiceTest.kt`)

- `@ExtendWith(MockKExtension::class)` — no Spring context
- All dependencies `@MockK`; service `@InjectMockKs`
- `timeProvider.now()` stubbed to a fixed `Instant` in `@BeforeEach`
- Test: happy path, every `ResponseStatusException` condition, `@Transactional` side effects

### Controller slice tests (`{Domain}ControllerTest.kt`)

- `@WebMvcTest({Domain}Controller::class)` — not `@SpringBootTest`
- Service dependency is `@MockkBean`
- Test: happy path status code, service error propagation, `@Valid` rejection (400),
  unauthenticated 401 for protected endpoints

### DataSource integration tests (only for custom `@Query` or Store)

- `@DataJpaTest` against a real PostgreSQL instance (Testcontainers)
- Test the custom query; do not test derived queries

### Validation

- [ ] Service tests pass with no Spring context
- [ ] Controller tests pass with MockMvc slice
- [ ] All documented `ResponseStatusException` conditions have a test
- [ ] Authentication gate tested (401 for unauthenticated requests to protected routes)
