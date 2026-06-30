---
id: PLAT-BE-SPRING
type: guide
layer: platforms
platform: [backend]
architecture: backend-service
requires: [ARCH-BE, ARCH-BE-CONTROLLER, ARCH-BE-SERVICE, ARCH-BE-ERROR]
related: [PLAT-BE-JPA, PLAT-BE-SECURITY]
tags: [spring-boot, annotations, rest-controller, service, path-constants, constructor-injection, time-provider]
---

# Spring Boot Platform Guide

Extends: `ARCH-BE`

## Annotations reference

| Layer | Annotation | Notes |
|---|---|---|
| Controller | `@RestController` | Combines `@Controller` + `@ResponseBody` |
| Controller | `@RequestMapping("{Domain}Paths.BASE")` | Class-level path; uses path constant |
| Controller | `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping` | Method-level; use path constant arguments |
| Controller | `@ResponseStatus(HttpStatus.CREATED)` | For 201; omit for 200 (default) |
| Controller | `@Valid` | On `@RequestBody` to trigger Bean Validation |
| Service | `@Service` | Spring-managed service bean |
| Service | `@Transactional` | On write methods and any multi-step operation |
| DataSource | `@Repository` | On custom Store wrapper implementations only |

## API path constants

All path strings live in a `{Domain}Paths` object in `:core:api`. No literal path
strings appear in controller annotations or `SecurityConfig`.

```kotlin
// :core:api — ApiConstants.kt
const val API_V1 = "/v1"

object AuthPaths {
    const val BASE       = "$API_V1/auth"
    const val PERMIT_ALL = "$BASE/**"
    const val REGISTER   = "/register"
    const val LOGIN      = "/login"
}

object UserPaths {
    const val BASE    = "$API_V1/users"
    const val PROFILE = "/{id}"
}
```

Adding a new domain: add a `{Domain}Paths` object to `ApiConstants.kt` **before**
writing the controller. Include `BASE`, a `PERMIT_ALL` if the domain has public
endpoints, and one `const val` per method path.

Path constant names use function names, not HTTP verb names:
- `SESSIONS_SYNC` not `POST_SESSIONS`
- `REGISTER` not `POST_REGISTER`

## Controller template

```kotlin
@RestController
@RequestMapping(UserPaths.BASE)
class UserController(
    private val userService: UserService,
) {

    @GetMapping(UserPaths.PROFILE)
    fun getProfile(@PathVariable id: UUID): UserProfileResponse =
        userService.getProfile(id)

    @PutMapping(UserPaths.PROFILE)
    fun updateProfile(
        @PathVariable id: UUID,
        @Valid @RequestBody request: UpdateProfileRequest,
    ): UserProfileResponse = userService.updateProfile(id, request)

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    fun create(@Valid @RequestBody request: CreateUserRequest): UserProfileResponse =
        userService.create(request)

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    fun delete(@PathVariable id: UUID) {
        userService.delete(id)
    }
}
```

## Service template

```kotlin
@Service
class UserService(
    private val userRepository: UserRepository,
    private val timeProvider: TimeProvider,
) {

    fun getProfile(userId: UUID): UserProfileResponse {
        val user = userRepository.findById(userId).orElseThrow {
            ResponseStatusException(HttpStatus.NOT_FOUND, "User not found")
        }
        return user.toResponse()
    }

    @Transactional
    fun updateProfile(userId: UUID, request: UpdateProfileRequest): UserProfileResponse {
        val user = userRepository.findById(userId).orElseThrow {
            ResponseStatusException(HttpStatus.NOT_FOUND, "User not found")
        }
        user.updatedAt = timeProvider.now()
        return userRepository.save(user).toResponse()
    }
}

private fun UserEntity.toResponse() = UserProfileResponse(id = id, email = email)
```

## TimeProvider

`TimeProvider` is an interface with a single implementation (`SystemTimeProvider`)
declared as a Spring bean. Inject via constructor. Never call `Instant.now()` or
`System.currentTimeMillis()` in service code.

```kotlin
interface TimeProvider {
    fun now(): Instant
    fun currentTimeMillis(): Long
}

@Component
class SystemTimeProvider : TimeProvider {
    override fun now(): Instant = Instant.now()
    override fun currentTimeMillis(): Long = System.currentTimeMillis()
}
```

In tests: stub `timeProvider.now()` with a fixed `Instant` in `@BeforeEach`.

## GlobalExceptionHandler template

```kotlin
@RestControllerAdvice
class GlobalExceptionHandler {

    private val logger = LoggerFactory.getLogger(GlobalExceptionHandler::class.java)

    @ExceptionHandler(ResponseStatusException::class)
    fun handleResponseStatus(e: ResponseStatusException): ResponseEntity<ErrorResponse> =
        ResponseEntity.status(e.statusCode)
            .body(ErrorResponse(status = e.statusCode.value(), message = e.reason ?: e.message))

    @ExceptionHandler(MethodArgumentNotValidException::class)
    fun handleValidation(e: MethodArgumentNotValidException): ResponseEntity<ErrorResponse> {
        val message = e.bindingResult.fieldErrors
            .joinToString("; ") { "${it.field}: ${it.defaultMessage}" }
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
            .body(ErrorResponse(status = 400, message = message))
    }

    @ExceptionHandler(Exception::class)
    fun handleUnexpected(e: Exception): ResponseEntity<ErrorResponse> {
        logger.error("Unexpected error", e)
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(ErrorResponse(status = 500, message = "An unexpected error occurred"))
    }
}
```

`ErrorResponse` is a simple data class: `data class ErrorResponse(val status: Int, val message: String)`.
Declare it in a core infrastructure package.

## Configuration properties

Runtime config values (secrets, expiry durations, feature toggles) live in
`application.yaml` and are bound via `@ConfigurationProperties`. Never call
`System.getenv()` or `System.getProperty()` directly in service code.

- Secrets and environment-specific values: injected as environment variables; `application.yaml`
  declares a safe dev default via `${ENV_VAR:default-dev-value}`
- Magic numbers (expiry durations, limits): declared in `application.yaml` and
  bound to a typed `@ConfigurationProperties` class

## Controller tests — MockMvc slice

```kotlin
@WebMvcTest(UserController::class)
@Import(SecurityConfig::class, JwtService::class, ApplicationProperties::class)
class UserControllerTest {

    @Autowired
    private lateinit var mvc: MockMvc

    @MockkBean
    private lateinit var userService: UserService

    @Test
    fun `GET users profile returns 200`() {
        val userId = UUID.randomUUID()
        every { userService.getProfile(userId) } returns UserProfileResponse(...)

        mvc.get("${UserPaths.BASE}/${userId}") {
            with(jwt().jwt { it.subject(userId.toString()) })
        }.andExpect {
            status { isOk() }
        }
    }
}
```

Use `@WebMvcTest` (not `@SpringBootTest`). Mock services with `@MockkBean`.
Add `@Import` for any security beans the controller requires.

## Service tests — Mockk without Spring

```kotlin
@ExtendWith(MockKExtension::class)
class UserServiceTest {

    @MockK private lateinit var userRepository: UserRepository
    @MockK private lateinit var timeProvider: TimeProvider
    @InjectMockKs private lateinit var userService: UserService

    private val fixedNow = Instant.parse("2025-01-01T12:00:00Z")

    @BeforeEach
    fun setUp() {
        every { timeProvider.now() } returns fixedNow
    }
}
```

No `@SpringBootTest` or `@DataJpaTest` for service tests. Zero Spring context startup.
