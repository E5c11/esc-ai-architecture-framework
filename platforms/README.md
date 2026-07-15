# platforms/

Technology-specific implementation guides. Platform documents extend architecture
rules with the concrete tools, libraries, and idioms of a specific tech stack.

A platform document always declares which architecture it extends. It never
redefines architecture rules — it only adds platform-specific expression of them.

## Structure

```
platforms/
├── mobile/      # Kotlin / KMP / Compose / Koin / Coroutines
├── backend/     # Kotlin / Spring Boot / JPA / Spring Security
├── web/         # TypeScript / React / Next.js
└── library/     # Independently published KMP libraries and exports
```

## Document ID prefix: `PLAT-`

Subdirectory convention: `PLAT-{PLATFORM_CODE}-{DOCUMENT}`
Examples: `PLAT-MOB-KOIN`, `PLAT-BE-JPA`, `PLAT-WEB-HOOKS`
