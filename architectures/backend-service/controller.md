---
id: ARCH-BE-CONTROLLER
type: rules
layer: architectures
platform: [backend]
architecture: backend-service
requires: [ARCH-BE, CORE-COUPLING]
related: [ARCH-BE-SERVICE, ARCH-BE-ERROR, PLAT-BE-SPRING]
tags: [controller, http, rest, boundary, thin-controller]
---

# Controller Layer

## Responsibility

The controller is the HTTP boundary. It translates an HTTP request into a service
call and a service result into an HTTP response. That is its entire purpose.

A controller method may:
- Parse the HTTP request (path variables, request body, authenticated principal)
- Call exactly one service method
- Return the result

## Rules

**Rule CTRL-LOGIC-01 (hard):** Controllers MUST contain zero business logic.
No conditional branching, domain decisions, computations, or calls to multiple
services inside a controller method. Any branching or computation belongs in
the service.

> Violation: `if (request.type == "admin") adminService.grant() else userService.update()`
> Fix: Move the conditional to a service method; the controller calls that one method.

**Rule CTRL-RETURN-01 (hard):** Controllers MUST return response DTOs, never JPA entities.
Returning an entity exposes the database schema as the API contract. Schema changes
break the API.

> Violation: `fun getUser(): UserEntity`
> Fix: Service maps entity to `UserResponse`; controller returns `UserResponse`.

**Rule CTRL-VALIDATION-01 (hard):** Input validation MUST use `@Valid` on the request
body parameter. Field-level constraints (`@NotBlank`, `@NotNull`, etc.) are declared
on the DTO. Manual null checks in a controller for fields expressible as Bean Validation
constraints are a violation.

**Rule CTRL-STATUS-01 (hard):** HTTP status codes MUST be set via `@ResponseStatus`
annotation or `ResponseEntity` with an `HttpStatus` enum value. Raw integer status
codes are forbidden.

> Violation: `ResponseEntity(body, 201)`
> Fix: `ResponseEntity(body, HttpStatus.CREATED)` or `@ResponseStatus(HttpStatus.CREATED)`

**Rule CTRL-INJECT-01 (hard):** Controllers MUST use constructor injection. `@Autowired`
field injection is forbidden. Constructor injection makes dependencies explicit and
the controller testable without a Spring context.

**Rule CTRL-MAPPING-01 (hard):** One controller per domain. A controller MUST NOT
inject two domain services and combine their results. Cross-domain orchestration
belongs in a service.

**Rule CTRL-NAMING-01 (soft):** Controller class: `{Domain}Controller`. Endpoint
methods: verb-noun pattern (`register`, `login`, `updateProfile`) — not HTTP verb
names (`post`, `get`, `put`).

**Rule CTRL-PATH-01 (hard):** `@RequestMapping` and `@GetMapping`/`@PostMapping` etc.
MUST reference named path constants from the `:core:api` constants module. Literal
path strings (including literal `/v1`) are forbidden. A future API version change
must require editing exactly one constant.

See `PLAT-BE-SPRING` for the path constants pattern and controller annotation syntax.

## Decision tree

```
New endpoint needed
    │
    ├─ Does it write data?
    │  ├─ Creates resource    → POST + @ResponseStatus(CREATED) + return DTO
    │  ├─ Updates resource    → PUT/PATCH + return updated DTO (200)
    │  └─ Deletes resource    → DELETE + @ResponseStatus(NO_CONTENT) + Unit
    │
    ├─ Does the method need branching or computation?
    │  └─ YES → Move to service. Controller calls service, returns result.
    │
    ├─ Does the method call more than one service?
    │  └─ YES → Add an orchestrating service method.
    │
    └─ Does the response include a JPA entity?
       └─ YES → Map to a DTO in the service before returning.
```

## Testing

Controller tests use a MockMvc slice test (`@WebMvcTest`) — not `@SpringBootTest`.
The service dependency is mocked. Controller tests verify HTTP routing, status codes,
request parsing, and response shape. Business logic correctness is the service test's
responsibility.

See `PLAT-BE-SPRING` for testing patterns and `PLAT-BE-SECURITY` for authenticated endpoint tests.
