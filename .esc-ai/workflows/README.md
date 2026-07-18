# Workflows — Framework Maintenance

This directory tracks the ESC AI Architecture Framework's own build and extension work —
not a consuming project's implementation phases. If you're looking for how to
*use* this framework in a downstream project, see [`INSTRUCTIONS.md`](../../INSTRUCTIONS.md)
at the repo root; it's the canonical, comprehensive usage guide and nothing
here duplicates it.

## Structure

- **`active/`** — in-progress framework build/extension phases.
- **`archive/`** — completed phases, kept for history.
- **`missing-files.md`** — the framework's gap log: stub or missing doc IDs,
  what they need to cover, and any open questions blocking them.

## Gap Protocol

Governed by [`INSTRUCTIONS.md`](../../INSTRUCTIONS.md)'s Gap Protocol section —
not restated here, to avoid the drift risk of two copies. When a task
surfaces a genuine framework gap, register it in `missing-files.md`.

## How to Add New Docs

`INSTRUCTIONS.md`'s "Document IDs" section already covers ID prefixes and
required frontmatter — don't restate those here. This section covers the
placement and structure decisions that come *before* you pick an ID.

**Placement test — architecture vs platform:**
If a rule names a specific technology (Koin, Flow, Compose, Spring), it
belongs in `platforms/`. If removing the technology name still leaves the
rule meaningful, it belongs in `architectures/`.

**Rule format:**
A rule is a fenced ```rule block conforming to `schemas/rule.yaml`, sitting
where its prose statement used to be:

````
```rule
id: ARCH-PC-REP-INTERFACE-01
statement: Repository MUST define an interface.
type: hard
scope: structure
enforced_by: [reviewer]
violation_message: Violates ARCH-PC-REP-INTERFACE-01 — Repository MUST define an interface.
```
````

`statement` is one sentence. If the rule needs more explanation — rationale,
a `> Violation:`/`> Fix:` example, edge cases — write that as plain prose
immediately after the block, same as any other paragraph; don't cram it into
the block. `enforced_by` should name every role that actually checks the
rule (`planner`/`executor`/`reviewer`/`ci`) — don't claim `ci` unless a real
check exists somewhere. `python tools/validate.py` checks every block against
the schema and catches duplicate rule IDs across the whole repo.

A citation — referencing a rule defined elsewhere, without redefining it —
is just the ID mentioned in prose, conventionally backticked or parenthesized
(` `ARCH-PC-REP-INTERFACE-01` ` or `(ARCH-PC-REP-INTERFACE-01)`); `validate.py`
flags any such citation that doesn't resolve to a real rule or document ID.

**Rule ownership and citation:**
Every rule ID is defined in exactly one owning doc — the doc that governs the
behavior the rule constrains. Any other doc that needs that rule cites it by
ID in prose; it does not redefine it. Two cases where a rule looks "shared"
but isn't duplication:

- **General principle with per-layer instantiations** — e.g. `CORE-SSOT` (the
  principle, owned by `core/`) and `ARCH-PC-REP-SSOT-01` (the Repository
  layer's specific obligation under that principle, owned by
  `architectures/pragmatic-clean/repository.md`). These are related, distinct
  rules, not copies of each other.
- **Boundary/contract rule between two components** — e.g. "UseCase MUST NOT
  call DataSource directly." This isn't a property of either component alone,
  so it doesn't belong in either leaf doc. It belongs in whichever doc
  already describes the relationship between them (an architecture overview
  doc), and both leaf docs cite it.

If you're about to paste the *same* rule block into two docs verbatim, that's
the signal to extract a shared doc for both to cite — not to duplicate it.

**When to split a doc into two or three:**
Split on scope incoherence — you can't state the doc's Responsibility section
without an "and." Rule count or rule reuse alone is not a reason to split; a
shared rule is handled by citation (above), not by carving up the doc that
owns it.

**After adding or moving a doc**, run `python tools/validate.py` (same
invocation `.github/workflows/validate.yml` runs in CI) to catch broken
references, duplicate IDs, and schema violations before committing.
