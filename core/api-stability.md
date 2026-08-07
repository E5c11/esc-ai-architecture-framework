---
id: CORE-API-STABILITY
type: principle
layer: core
platform: [all]
architecture: [all]
requires: [CORE-COUPLING]
related: [CORE-ERROR, CORE-NAMING, PLAT-LIB-KMP]
tags: [api, semver, versioning, breaking-change, compatibility, binary-compatibility, deprecation, public-surface, library]
status: active
---

# Public API Stability

## Statement

Once a piece of code is consumed outside the module or repository that defines it, changing
its public surface is a decision with a cost paid by every consumer — not a free refactor.
Evolve public APIs additively by default; treat removal or signature changes as a deliberate,
explicitly-flagged decision, never a side effect of adding something new.

## Rationale

Internal code can be freely restructured because every caller is visible and updates in the
same commit. A public API breaks that assumption — the callers are in repositories you don't
control, may not update on your schedule, and often can't be enumerated at all (an OSS
library, a published SDK, a versioned internal package consumed by other teams). A change
that looks trivial from the defining side ("just add a parameter", "just make this method
abstract") can be a compile break or silent behaviour change on the consuming side. Additive
evolution — new capability appears without disturbing what already compiles — lets consumers
upgrade on their own timeline instead of being forced into lockstep.

This is not "never break anything." It's "breaking is a decision, not a default." Some
changes are worth a major version bump. The point is that the bump is chosen, not discovered
by a consumer's build failing.

## In Practice

**Adding a new capability to a public interface is additive only if existing implementers
still compile.** In a language with default interface methods (Kotlin, Java 8+), a new
interface method should default to either delegating to existing behaviour or throwing a
clear `UnsupportedOperationException` — not be abstract — unless you specifically intend to
force every implementer to handle the new case. An abstract addition to a public interface is
a source-breaking change no matter how small the addition feels.

**Version the change to match its actual impact, not its effort.** A one-line addition that
adds a new public method is still a minor-version change if it's additive; a one-line change
to an existing method's parameter type is a major-version change no matter how small the diff.
Semantic versioning bumps track *consumer impact*, not lines changed:
- **Patch** — bug fixes only, no public surface change
- **Minor** — new public surface added, nothing existing removed or changed shape
- **Major** — any existing public signature removed, renamed, or changed shape; any behaviour
  change a reasonable consumer would have depended on

**Deprecate before removing.** Mark the old path `@Deprecated` with a `ReplaceWith` or
equivalent pointer to the new path, ship at least one release where both exist, then remove
in the next major version. Don't delete a public symbol in the same release that introduces
its replacement.

**The boundary is "public," not "written."** A class marked `internal` (Kotlin) or
package-private can be restructured freely — this principle applies at the actual consumption
boundary (what's exported from the module/package/artifact), not to every line of code.

## Violations

- Adding an abstract method to a public interface when a default implementation would have
  preserved compatibility
- Changing an existing public method's parameter types, return type, or nullability without
  a major version bump
- Removing a public symbol in the same release that adds its replacement, with no
  deprecation window
- Treating "it's a small change" as a substitute for assessing consumer impact
- Silently changing runtime behaviour of an existing public method (e.g. a method that used
  to be safe to call unauthenticated now throwing) without documenting it as a breaking change
