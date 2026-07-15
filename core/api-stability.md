---
id: CORE-API-STABILITY
type: principle
layer: core
platform: [all]
architecture: [all]
requires: [CORE-COUPLING]
related: [PLAT-LIB-KMP]
tags: [api, compatibility, semver, binary-compatibility, library]
---

# Public API Stability

## Principle

A published API is a contract with consumers that update independently. Source,
binary, behavioural and metadata compatibility all matter; a release that compiles
in its own repository but cannot be resolved or linked by an external consumer is broken.

## Compatibility rules

**Rule CORE-API-SEMVER-01 (hard):** A stable public API MUST follow semantic
versioning. Breaking source, binary or behavioural changes require a major release.

**Rule CORE-API-ADD-01 (hard):** New interface behaviour SHOULD be added with a
backward-compatible default implementation when a safe default exists. Adding an
abstract member to a published interface is a breaking change.

**Rule CORE-API-REMOVE-01 (hard):** Public declarations MUST be deprecated for at
least one release before removal, with a replacement and migration message where possible.

**Rule CORE-API-META-01 (hard):** Gradle module metadata, POMs and target artifacts
are part of the public contract. Every variant advertised by root metadata MUST exist
at the referenced immutable coordinates.

**Rule CORE-API-CONSUMER-01 (hard):** A published library MUST be verified from a
clean external consumer that has no project substitution, composite build or accidental
`mavenLocal()` fallback.

## Review checklist

- [ ] Public declarations changed in this release have been classified as additive,
      deprecated or breaking.
- [ ] Interface additions preserve existing implementers or intentionally bump major.
- [ ] Root metadata references only artifacts published in the same release operation.
- [ ] A clean consumer resolves and compiles every supported platform variant.
- [ ] Release notes describe migrations and behavioural changes.

