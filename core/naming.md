---
id: CORE-NAMING
type: principle
layer: core
platform: [all]
architecture: [all]
requires: []
related: [CORE-COUPLING]
tags: [naming, readability, domain-language, conventions, intent]
status: active
---

# Naming Philosophy

## Statement

Names communicate intent and role. They do not describe implementation, recapitulate
the type system, or add noise words that carry no meaning.

## Rationale

Code is read far more often than it is written. A well-named identifier requires no
comment to explain what it is or why it exists. A poorly-named identifier creates
cognitive overhead every time it is encountered. Consistent naming also serves as
an implicit architecture guide — a reader can infer layer and responsibility from
the name alone.

## In Practice

**Use domain language, not technical language**
- `UserRepository` not `UserJpaRepository`
- `OrderService` not `OrderBusinessLogicHandler`
- `PaymentFailedException` not `HttpClientErrorException`

**Suffixes communicate architectural role**
Architecture documents define the suffix conventions for each layer. Follow them
consistently. A reader who sees `UserDataSource`, `UserRepository`, `UserUseCase`,
`UserViewModel` understands the layer without reading the class body.

**Functions are verb-noun**
- `fetchUser()`, `createOrder()`, `cancelBooking()`
- Not `user()`, `order()`, `booking()`

**Booleans read as assertions**
- `isActive`, `hasPermission`, `isEmpty`
- Not `active`, `permission`, `empty`

**Consistency over cleverness**
Use the same name for the same concept everywhere. If the domain calls it an
"appointment", every layer calls it an "appointment" — not "booking", "slot",
or "session" depending on who wrote the file.

## Violations

- Noise-word class names: `UserManager`, `DataHelper`, `ServiceUtil`, `RequestHandler`
- Verbs that describe the mechanism, not the intent: `doFetchData()`, `handleIt()`,
  `processRequest()`
- Generic variable names: `data`, `result`, `obj`, `temp` where a specific name fits
- Names that lie: a function called `getUser` that also modifies state
