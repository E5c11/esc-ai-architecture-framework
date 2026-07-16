#!/usr/bin/env python3
"""
One-time migration: inline bold-text rules -> fenced ```rule YAML blocks.

Converts:
  **Rule ARCH-PC-REP-INTERFACE-01 (hard):** Repository MUST define an interface.
into:
  ```rule
  id: ARCH-PC-REP-INTERFACE-01
  type: hard
  scope: structure
  enforced_by: [reviewer]
  violation_message: Violates ARCH-PC-REP-INTERFACE-01 — Repository MUST define an interface.
  ```

Only the bold line's *first sentence* becomes the block's violation_message
source; any remaining sentences in the same paragraph are left as plain
trailing prose immediately after the block. Everything else in the file
(blockquotes, bullets, following paragraphs) is untouched.

`scope` is guessed by keyword heuristic and `enforced_by` always defaults to
[reviewer] — see workflows/active/rule-embedding-migration.md for why. This
is a known lower-quality starting point, not a final answer.

Usage:
  python tools/migrate_rules.py <file.md> [file2.md ...]

Prints a per-file summary (rule count, scope distribution) and rewrites each
file in place.

Not deleted after the main migration (workflows/archive/rule-embedding-migration.md,
now complete) because platforms/mobile/kmp.md and platforms/mobile/http-client.md
were deliberately deferred — see workflows/missing-files.md. Delete this file
once those two are migrated and nothing else needs it.
"""

import re
import sys
from collections import Counter
from pathlib import Path

RULE_LINE = re.compile(
    r"^\*\*Rule ([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+) \((hard|soft)\):\*\* (.*)$"
)

# checked in order — first match wins
SCOPE_KEYWORDS = [
    ("di",             ["inject", "constructor", "koin module", "di module"]),
    ("return-type",    ["must return", "return type", "flow<", "suspend fun", "returns a", "returning"]),
    ("error-handling", ["exception", "throw", "catch", "error"]),
    ("testing",        ["test", "mock", "fake", "turbine"]),
    ("performance",    ["cache", "n+1", "performance", "index"]),
    ("naming",         ["naming", "named", "name is", "must be named"]),
    ("structure",      ["interface", "class must", "file", "module structure", "directory"]),
]

SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-Z`])")


def guess_scope(text: str) -> str:
    lowered = text.lower()
    for scope, keywords in SCOPE_KEYWORDS:
        if any(kw in lowered for kw in keywords):
            return scope
    return "behavior"


def split_first_sentence(paragraph: str) -> tuple[str, str]:
    """Return (first_sentence, remainder) — remainder is '' if there's only one sentence."""
    parts = SENTENCE_BOUNDARY.split(paragraph, maxsplit=1)
    if len(parts) == 1:
        return parts[0].strip(), ""
    return parts[0].strip(), parts[1].strip()


def find_rule_paragraphs(lines: list[str]) -> list[tuple[int, int, str, str, str]]:
    """
    Find every rule paragraph. Returns list of
    (start_line_idx, end_line_idx_exclusive, rule_id, rule_type, full_paragraph_text).
    A paragraph runs from the **Rule ...** line to the next blank line or EOF.
    """
    results = []
    i = 0
    while i < len(lines):
        match = RULE_LINE.match(lines[i])
        if not match:
            i += 1
            continue
        rule_id, rule_type, first_text = match.groups()
        paragraph_lines = [first_text]
        j = i + 1
        while j < len(lines) and lines[j].strip():
            paragraph_lines.append(lines[j])
            j += 1
        full_text = " ".join(l.strip() for l in paragraph_lines)
        results.append((i, j, rule_id, rule_type, full_text))
        i = j
    return results


def migrate_file(path: Path) -> Counter:
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    rule_paragraphs = find_rule_paragraphs(lines)

    scope_counts: Counter = Counter()
    # Replace in reverse so earlier-line indices stay valid as we edit.
    for start, end, rule_id, rule_type, full_text in reversed(rule_paragraphs):
        first_sentence, remainder = split_first_sentence(full_text)
        scope = guess_scope(full_text)
        scope_counts[scope] += 1

        block_lines = [
            "```rule",
            f"id: {rule_id}",
            f"statement: {first_sentence}",
            f"type: {rule_type}",
            f"scope: {scope}",
            "enforced_by: [reviewer]",
            f"violation_message: Violates {rule_id} — {first_sentence}",
            "```",
        ]
        if remainder:
            block_lines.append("")
            block_lines.append(remainder)

        lines[start:end] = block_lines

    if rule_paragraphs:
        path.write_text("\n".join(lines), encoding="utf-8")

    return scope_counts


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    total = Counter()
    for arg in sys.argv[1:]:
        path = Path(arg)
        if not path.exists():
            print(f"SKIP (not found): {path}")
            continue
        counts = migrate_file(path)
        rule_count = sum(counts.values())
        if rule_count == 0:
            print(f"{path}: no rules found")
            continue
        dist = ", ".join(f"{scope}={n}" for scope, n in counts.most_common())
        fallback = counts.get("behavior", 0)
        print(f"{path}: {rule_count} rules migrated ({dist})"
              + (f"  [{fallback} fell back to 'behavior' — review]" if fallback else ""))
        total.update(counts)

    print(f"\nTotal: {sum(total.values())} rules migrated across {len(sys.argv) - 1} files.")
    if total:
        print("Scope distribution: " + ", ".join(f"{s}={n}" for s, n in total.most_common()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
