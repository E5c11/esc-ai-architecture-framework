---
id: PLAT-BE-JPA
type: guide
layer: platforms
platform: [backend]
architecture: backend-service
requires: [ARCH-BE-ENTITY, ARCH-BE-DATASOURCE]
related: [PLAT-BE-SPRING, PLAT-BE-SECURITY]
tags: [jpa, hibernate, flyway, postgresql, entity, migrations, allopen, uuid, timestamps]
---

# JPA / Flyway Platform Guide

Extends: `ARCH-BE-ENTITY`, `ARCH-BE-DATASOURCE`

## Entity annotation template

```kotlin
@Entity
@Table(name = "subjects")
class SubjectEntity(

    @Column(nullable = false)
    var title: String,

    @Column(columnDefinition = "TEXT")
    var description: String? = null,

    @Column(nullable = false)
    var isActive: Boolean = true,

    @Column(updatable = false, nullable = false)
    val createdAt: Instant = Instant.now(),

    @Column(nullable = false)
    var updatedAt: Instant = Instant.now(),

    @Id
    @Column(updatable = false, nullable = false)
    val id: UUID = UUID.randomUUID(),
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is SubjectEntity) return false
        return id == other.id
    }

    override fun hashCode(): Int = id.hashCode()
}
```

Declare `id` last in the constructor so all required fields are first and the ID
can carry a default value while still being passable explicitly.

## allOpen plugin

Hibernate requires non-final classes to create proxies. The `kotlin-allopen`
Gradle plugin (applied via the `ampm.backend.module` convention plugin) opens
all classes annotated with `@Entity`, `@MappedSuperclass`, and `@Embeddable`
at compile time. No `open` modifier needed in the source; no `data class` allowed.

## UUID primary key

Default to a plain Kotlin constructor default with no generation-strategy
annotation: `@Id val id: UUID = UUID.randomUUID()`. The JVM assigns the ID when
the object is constructed, before Hibernate is involved at all — there is no
`@GeneratedValue` to configure and no round trip needed to learn the generated
value after insert. This is the pattern used in production by `UserEntity` and
`RefreshTokenEntity`.

The migration still declares `DEFAULT gen_random_uuid()` on the column:

```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
```

Under the constructor-default approach this SQL default is **not** the primary
generation mechanism — Hibernate always sends the already-populated JVM value on
insert, so the column default never actually fires for entity-based writes. Keep
it anyway as an optional safety net: it only matters for a raw SQL `INSERT` that
bypasses the entity layer entirely (a one-off migration backfill, a manual
`psql` insert), and costs nothing to leave in place.

`@GeneratedValue(strategy = GenerationType.UUID)` is an acceptable alternative if
you'd rather have Hibernate own generation (see `ENT-ID-01` for the full
three-option comparison), but it is not required — do not add it back to the
constructor-default pattern above, the two are redundant with each other.

Never use `GenerationType.IDENTITY` with `Long` or `Int` — sequential integer IDs
are enumerable in URLs and unsafe to expose in API responses.

## Timestamps

Every entity gets two timestamp columns:

```kotlin
@Column(updatable = false, nullable = false)
val createdAt: Instant = Instant.now()

@Column(nullable = false)
var updatedAt: Instant = Instant.now()
```

`createdAt` is immutable (`updatable = false`). `updatedAt` is mutable. The
service sets `updatedAt = timeProvider.now()` before every save.

The `Instant.now()` constructor default is acceptable on entities — it fires only
at object construction time, not during a running operation. The authoritative
value for rows inserted directly by the database is the SQL `DEFAULT now()`.

## Relationship associations

```kotlin
// Many-to-one — always LAZY
@ManyToOne(fetch = FetchType.LAZY)
@JoinColumn(name = "user_id", nullable = false)
val user: UserEntity,

// One-to-many — always LAZY
@OneToMany(mappedBy = "user", fetch = FetchType.LAZY, cascade = [CascadeType.ALL])
val tokens: MutableList<RefreshTokenEntity> = mutableListOf(),
```

Always `FetchType.LAZY`. Eager fetching generates N+1 queries and cannot be turned
off at the query level. Load associations explicitly in the service when needed.

## Flyway migrations

```
src/main/resources/db/migration/
    V1__create_users.sql
    V2__create_subjects.sql
    V3__add_is_active_to_users.sql
```

File naming: `V{next}__<description>.sql`. Version numbers are sequential integers
starting from 1. Never reuse or gap a version number.

### New table template

```sql
CREATE TABLE subjects (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title       VARCHAR(255) NOT NULL,
    description TEXT,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_subjects_title ON subjects (title);
```

Rules:
- `UUID PRIMARY KEY DEFAULT gen_random_uuid()` — always
- `TIMESTAMPTZ NOT NULL DEFAULT now()` — always for both timestamp columns
- Add an index for every column used in a `WHERE` or `JOIN` predicate

### Adding a column

```sql
ALTER TABLE users ADD COLUMN profile_pic_url TEXT;
```

Never `DROP COLUMN` in the same migration that adds a replacement. Destructive
changes go in a separate migration after the transition period.

### Foreign key with cascade

```sql
user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
```

Always declare `ON DELETE` behaviour explicitly. `CASCADE` for owned children;
`RESTRICT` or `SET NULL` where the relationship is a reference only.

## JPA configuration

```yaml
spring:
  jpa:
    hibernate:
      ddl-auto: validate
    show-sql: false
    open-in-view: false
```

`ddl-auto: validate` means JPA checks that the entity matches the schema on startup
but makes no schema changes. This is why migration-first is a hard requirement.

`open-in-view: false` prevents the "Open Session In View" anti-pattern, which
keeps Hibernate sessions open during view rendering and triggers lazy-loading
outside service transaction boundaries.

## JpaRepository patterns

```kotlin
interface UserRepository : JpaRepository<UserEntity, UUID> {
    // Derived queries
    fun findByEmail(email: String): UserEntity?
    fun existsByEmail(email: String): Boolean
    fun findAllBySubjectId(subjectId: UUID): List<SubjectEntity>

    // JPQL query
    @Query("SELECT u FROM UserEntity u WHERE u.isPremium = true AND u.premiumExpiry < :now")
    fun findExpiredPremiumUsers(now: Instant): List<UserEntity>

    // Native SQL
    @Query(value = "SELECT * FROM users WHERE ...", nativeQuery = true)
    fun findByComplexCriteria(...): List<UserEntity>
}
```

Return types from repositories: `T?`, `T`, `List<T>`, `Page<T>`. Never DTOs.
No `@Transactional` on repository methods.

## DataJpaTest for custom queries

```kotlin
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Testcontainers
class UserRepositoryTest {

    @Container
    val postgres = PostgreSQLContainer("postgres:16")

    @Autowired
    private lateinit var userRepository: UserRepository

    @Test
    fun `findByEmail returns user when email matches`() {
        val saved = userRepository.save(UserEntity(email = "a@b.com", ...))
        val found = userRepository.findByEmail("a@b.com")
        assertEquals(saved.id, found?.id)
    }
}
```

Use `@DataJpaTest` (not `@SpringBootTest`) for DataSource integration tests.
Run against a real PostgreSQL instance (Testcontainers) to verify SQL compatibility.
In-memory H2 does not faithfully replicate PostgreSQL behaviour.
