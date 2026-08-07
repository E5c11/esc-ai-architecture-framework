---
id: ORCH-ALL-CROSS-REPO
type: orchestrator
layer: feature-orchestrators
platform: [all]
architecture: [all]
goal: "Implement a feature that spans a backend endpoint and its mobile (and optionally web) consumer, keeping the contract and each repo's docs in sync"
requires:
  - CORE-DI
  - CORE-SSOT
  - CORE-NAMING
related: [ORCH-BE-ENDPOINT, ORCH-MOB-FEAT, ORCH-WEB-FEAT, QG-REVIEW]
tags: [cross-platform, cross-repo, backend, mobile, web, contract, orchestration]
status: active
---

# Implement a Cross-Repo Feature (Backend + Mobile [+ Web])

## Goal

Coordinate a feature whose implementation spans more than one repository —
typically a backend endpoint consumed by a mobile app, optionally also surfaced
in a web dashboard — so the contract, build order, and documentation stay
consistent across repos instead of drifting apart independently.

## When to use this orchestrator

Use this instead of — not in addition to — `ORCH-BE-ENDPOINT` / `ORCH-MOB-FEAT` /
`ORCH-WEB-FEAT` directly, whenever a single feature requires coordinated changes
in 2+ repos. This orchestrator sequences those platform orchestrators and adds
the cross-repo contract and documentation steps none of them cover individually,
since each one only knows about its own repo.

## Before you start

Identify which repos this feature touches and which platform orchestrator
applies to each:

- Backend repo → `ORCH-BE-ENDPOINT`
- Mobile repo → `ORCH-MOB-FEAT` (often only the phases needed to consume an
  existing feature module, not a full new-module scaffold — skip phases that
  don't apply)
- Web/dashboard repo → `ORCH-WEB-FEAT` (only if this feature has an
  admin-facing or public web surface)

---

## Phase 1 — Contract design

**Goal:** the request/response shape is agreed and written down before either
side is implemented, so backend and mobile don't discover a mismatch after both
are already built.

**Docs to update:** the contract note itself (see Steps) — not a framework doc.

### Steps

1. Write the endpoint contract: HTTP method, path, request DTO shape, response
   DTO shape, status codes, auth requirement.
2. Record it somewhere both repos' implementers will see before writing code —
   e.g. a shared design note referenced from both repos' TODO documents. Do not
   let the contract live only in conversation.
3. Decide build order for this feature: backend-first (mobile builds against a
   real endpoint) is the default. Only build against a mocked contract if the
   mobile side is time-critical, and only once the backend implementer has
   confirmed they will follow the recorded contract exactly.

### Validation

- [ ] Request/response shapes are written down, not just discussed
- [ ] Both repos' TODO documents reference the same contract note

---

## Phase 2 — Backend implementation

**Follow `ORCH-BE-ENDPOINT`** in the backend repo, in full.

### Validation

- [ ] All of `ORCH-BE-ENDPOINT`'s phase validations pass
- [ ] The shipped endpoint matches the Phase 1 contract exactly. If it had to
  change during implementation, the Phase 1 contract note is updated to match
  before Phase 3 starts — never left stale.

---

## Phase 3 — Mobile consumption

**Follow `ORCH-MOB-FEAT`** in the mobile repo — typically only the
DataSource → Repository → UseCase → ViewModel → View phases relevant to
consuming the new endpoint, unless this genuinely introduces a new feature
module.

### Validation

- [ ] Mobile DataSource matches the Phase 1 contract exactly (field names,
  types, nullability)
- [ ] All `ORCH-MOB-FEAT` phase validations pass for the phases actually used

---

## Phase 4 — Web/dashboard surface (only if this feature has one)

**Follow `ORCH-WEB-FEAT`** in the dashboard or website repo.

### Validation

- [ ] All of `ORCH-WEB-FEAT`'s phase validations pass
- [ ] Web/dashboard data hook matches the Phase 1 contract exactly

---

## Phase 5 — Cross-repo documentation and closeout

**Goal:** every repo whose behavior changed has an updated doc. This is the
step no single platform orchestrator can cover, since none of them know the
other repos exist.

### Steps

1. In each repo touched, identify the doc that describes this feature's
   behavior (that repo's feature-doc equivalent — e.g. a `wiki/*.md` entry) and
   update it in the same change as the code. Do not defer this to a follow-up.
2. If a touched repo has no doc for this feature area yet, create one rather
   than leaving it undocumented — follow that repo's own doc-creation
   convention.
3. Cross-reference: each updated doc should note which other repo(s) this
   feature also touches, so a future reader in one repo knows to check the
   other side of the contract before changing it.

### Validation

- [ ] Every repo touched by this feature has its feature doc updated or
  created in the same change
- [ ] Each updated doc cross-references the other repo(s) involved
- [ ] The Phase 1 contract note reflects the final, shipped shape — not just
  the initial design

---

## Gap protocol

If any platform-specific orchestrator referenced here (`ORCH-BE-ENDPOINT`,
`ORCH-MOB-FEAT`, `ORCH-WEB-FEAT`) is missing a pattern this feature needs,
follow that orchestrator's own gap protocol directly — do not improvise a
cross-repo workaround here.
