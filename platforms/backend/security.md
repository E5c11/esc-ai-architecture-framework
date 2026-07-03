---
id: PLAT-BE-SECURITY
type: guide
layer: platforms
platform: [backend]
architecture: backend-service
requires: [ARCH-BE, ARCH-BE-CONTROLLER, ARCH-BE-SERVICE]
related: [PLAT-BE-SPRING]
tags: [security, jwt, authentication, spring-security, authentication-principal, stateless, refresh-token, token-rotation]
---

# Spring Security / JWT Platform Guide

Extends: `ARCH-BE-CONTROLLER`

## Authentication model

The backend uses stateless JWT authentication. No server-side session state.

```
HTTP request with Authorization: Bearer <access-token>
    ↓
JwtAuthFilter — validates token, extracts userId (UUID), sets SecurityContext principal
    ↓
Controller — reads userId via @AuthenticationPrincipal
    ↓
Service — receives userId as a plain constructor parameter
```

The principal in the `SecurityContext` is a raw `UUID`, not a `UserDetails` object.
No database lookup happens on every request.

## Reading the current user

### In controllers — preferred

```kotlin
@GetMapping("/me")
fun getMyProfile(@AuthenticationPrincipal userId: UUID): UserProfileResponse =
    userService.getProfile(userId)

@PutMapping("/me")
fun updateProfile(
    @AuthenticationPrincipal userId: UUID,
    @Valid @RequestBody request: UpdateProfileRequest,
): UserProfileResponse = userService.updateProfile(userId, request)

@DeleteMapping("/me/sessions")
@ResponseStatus(HttpStatus.NO_CONTENT)
fun revokeAllSessions(@AuthenticationPrincipal userId: UUID) {
    authService.revokeAllSessions(userId)
}
```

`@AuthenticationPrincipal` is from `org.springframework.security.core.annotation.AuthenticationPrincipal`.
Spring resolves the principal from the `SecurityContext` automatically.

### In services — pass as parameter

Services receive the `userId` as a plain method parameter from the controller.
Services MUST NOT access `SecurityContextHolder` directly.

```kotlin
// Controller passes it:
userService.getProfile(userId)

// Service receives it as a parameter:
fun getProfile(userId: UUID): UserProfileResponse { ... }
```

**Rule PLAT-BE-SEC-SVC-01 (hard):** Services MUST NOT inject or call
`SecurityContextHolder.getContext()`. Accessing the security context in a service
couples business logic to HTTP request state and makes service methods impossible
to test in isolation.

### Fallback — background tasks only

If a context exists in a non-controller path (e.g. a scheduled task that still
has an authenticated security context), reading directly is acceptable as a
last resort:

```kotlin
val userId = SecurityContextHolder.getContext().authentication?.principal as? UUID
    ?: throw ResponseStatusException(HttpStatus.UNAUTHORIZED, "Not authenticated")
```

Use this only when `@AuthenticationPrincipal` is not available. Never use it in
service classes.

## SecurityConfig pattern

```kotlin
@Configuration
@EnableWebSecurity
class SecurityConfig(
    private val jwtAuthFilter: JwtAuthFilter,
    private val applicationProperties: ApplicationProperties,
) : WebSecurityConfigurerAdapter() {

    override fun configure(http: HttpSecurity) {
        http
            .sessionManagement { it.sessionCreationPolicy(SessionCreationPolicy.STATELESS) }
            .csrf { it.disable() }
            .authorizeHttpRequests {
                it.requestMatchers(AuthPaths.PERMIT_ALL).permitAll()
                it.anyRequest().authenticated()
            }
            .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter::class.java)
    }
}
```

Path patterns in `requestMatchers` MUST use the same path constants as the
controllers (`AuthPaths.PERMIT_ALL`, `UserPaths.PERMIT_ALL`, etc.). No literal
strings in `SecurityConfig`.

## Controller tests with JWT

Use Spring Security Test's `jwt()` post-processor to supply a valid principal
in slice tests:

```kotlin
import org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.jwt

@Test
fun `GET users me returns 200 for authenticated user`() {
    val userId = UUID.randomUUID()
    every { userService.getProfile(userId) } returns UserProfileResponse(...)

    mvc.get("/v1/users/me") {
        with(jwt().jwt { it.subject(userId.toString()) })
    }.andExpect {
        status { isOk() }
    }
}

@Test
fun `GET users me returns 401 for unauthenticated request`() {
    mvc.get("/v1/users/me").andExpect {
        status { isUnauthorized() }
    }
}
```

The `jwt()` post-processor sets the `authentication.principal` to the JWT's
`subject`. Because `JwtAuthFilter` extracts the principal as a `UUID`, supply
the `userId.toString()` as the subject value.

`@Import(SecurityConfig::class, JwtService::class, ApplicationProperties::class)` is
required on `@WebMvcTest` classes that test endpoints protected by the JWT filter.
Public endpoints (under `PERMIT_ALL` paths) do not need `@Import` for the security beans.

## Refresh token storage

Refresh tokens are the long-lived half of the JWT pair and MUST follow the
sensitive-token rules in `ARCH-BE-SERVICE` (`SVC-TOKEN-01`, `SVC-TOKEN-02`,
`SVC-TOKEN-03`): hashed at rest, single-use/rotated on exchange, and validated
against both `revoked` and `expiresAt`. Those rules are framework-agnostic; this
is what they look like wired into `AuthService`:

```kotlin
@Transactional
fun refresh(request: RefreshRequest): AuthResponse {
    if (!jwtService.isValid(request.refreshToken)) {
        throw ResponseStatusException(HttpStatus.UNAUTHORIZED, "Invalid refresh token")
    }
    val stored = refreshTokenRepository.findByTokenHash(sha256(request.refreshToken))
        ?: throw ResponseStatusException(HttpStatus.UNAUTHORIZED, "Refresh token not recognised")
    if (stored.revoked || stored.expiresAt.isBefore(timeProvider.now())) {
        throw ResponseStatusException(HttpStatus.UNAUTHORIZED, "Refresh token expired or revoked")
    }
    val user = stored.user
    refreshTokenRepository.delete(stored) // single-use rotation
    return issueTokens(user)
}

private fun issueTokens(user: UserEntity): AuthResponse {
    val accessToken = jwtService.generateAccessToken(user.id)
    val refreshToken = jwtService.generateRefreshToken(user.id)
    refreshTokenRepository.save(
        RefreshTokenEntity(
            user = user,
            tokenHash = sha256(refreshToken),
            expiresAt = timeProvider.now().plusMillis(jwtService.refreshTokenExpirationMs),
        )
    )
    return AuthResponse(accessToken, refreshToken, ...)
}
```

`RefreshTokenEntity.tokenHash` stores `sha256(refreshToken)` — the raw JWT refresh
token is generated, returned to the client once, and never persisted. `logout()`
performs the same hash lookup to delete a token on demand, so a stolen-but-unused
token can still be revoked before an attacker exchanges it.

## Violations

- `SecurityContextHolder.getContext()` called in a service class
- Path patterns hardcoded as strings in `SecurityConfig.requestMatchers`
- `@SpringBootTest` used for controller tests that only need MockMvc
- No test for the unauthenticated (401) case on a protected endpoint
- Refresh token persisted or logged in raw form instead of hashed (`SVC-TOKEN-01`)
- Refresh endpoint issues a new token pair without deleting/rotating the old row
  (`SVC-TOKEN-02`)
- Refresh validity check tests `expiresAt` or `revoked` alone instead of both
  (`SVC-TOKEN-03`)
