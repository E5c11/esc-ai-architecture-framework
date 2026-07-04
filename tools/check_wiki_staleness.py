#!/usr/bin/env python3
"""
Wiki staleness checker.

Scans markdown docs (e.g. a project's wiki/) for inline-code identifiers —
`ClassName`, `methodName()`, `Object.member`, `FileName.kt` — and flags ones
that no longer appear anywhere in a given source tree. This catches the
cheapest, most mechanical class of doc staleness: a renamed or deleted
class/function that a doc still references by its old name.

This is a heuristic, not a hard gate. It will not catch behavioral drift
(a doc describing logic that changed shape but kept the same names) and it
can false-positive on identifiers that are also common English words
(`Available`, `Error`) — those just won't get flagged, since the word will
almost always appear somewhere in the code for unrelated reasons. Treat
findings as candidates for human review, not proven bugs.

Usage:
  python3 tools/check_wiki_staleness.py --docs <dir> --code <dir> [<dir> ...] [--strict]

Exit code: 0 normally (informational). With --strict, exits 1 if any
identifier could not be found in the code tree.
"""

import re
import sys
import argparse
from pathlib import Path

DOC_GLOB = "*.md"

# Source file extensions searched for both "word appears in code" and
# "filename exists in tree" checks. Deliberately broad — this tool is meant
# to generalize across whatever project pulls in this framework.
CODE_EXTENSIONS = {
    ".kt", ".kts", ".java", ".swift", ".ts", ".tsx", ".js", ".jsx",
    ".py", ".go", ".rs", ".rb", ".cs", ".cpp", ".c", ".h",
}

# Directory names pruned while walking --code roots: build output, dependency
# caches, and VCS metadata. Not project-specific paths — safe defaults for
# any repo this tool runs against.
EXCLUDED_DIR_NAMES = {
    "build", "node_modules", ".git", ".gradle", ".idea", "dist",
    "__pycache__", ".venv", "venv", "target", ".next",
}

FENCED_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)(\(\))?`")
WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
FILE_REF_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+$")


def is_code_like(token: str) -> bool:
    """Filter out prose words picked up by the backtick regex."""
    if "." in token:
        return True
    # camelCase or PascalCase: a lowercase-to-uppercase transition, or a
    # capitalized multi-syllable word (heuristically: mixed case at all).
    has_lower = any(c.islower() for c in token)
    has_upper = any(c.isupper() for c in token)
    if has_lower and has_upper:
        return True
    # ALL_CAPS_CONSTANT style
    if "_" in token and token == token.upper():
        return True
    return False


def extract_identifiers(doc_text: str) -> list[tuple[int, str]]:
    """Return (line_number, identifier) for every inline-code span that
    looks like a code identifier, skipping fenced code blocks."""
    stripped = FENCED_BLOCK_RE.sub("", doc_text)
    results = []
    for lineno, line in enumerate(stripped.splitlines(), start=1):
        for match in INLINE_CODE_RE.finditer(line):
            token = match.group(1)
            if is_code_like(token):
                results.append((lineno, token))
    return results


def collect_documents(docs_root: Path) -> list[Path]:
    return sorted(docs_root.rglob(DOC_GLOB))


def build_code_index(code_roots: list[Path]) -> tuple[set[str], set[str]]:
    """Return (all_words_in_code, all_filenames_in_code)."""
    import os

    words: set[str] = set()
    filenames: set[str] = set()
    for root in code_roots:
        for dirpath, dirnames, files in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIR_NAMES]
            for name in files:
                filenames.add(name)
                suffix = Path(name).suffix
                if suffix not in CODE_EXTENSIONS:
                    continue
                path = Path(dirpath) / name
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                words.update(WORD_RE.findall(text))
    return words, filenames


def check_identifier(token: str, words: set[str], filenames: set[str]) -> bool:
    """Return True if the identifier is found somewhere in the code tree."""
    if FILE_REF_RE.match(token):
        return token in filenames or token.split(".")[0] in words
    if "." in token:
        # Dotted reference (Class.member, object.property) — check the
        # more distinctive trailing segment rather than the literal
        # "A.b" text, since code rarely spells it identically.
        segment = token.split(".")[-1]
        return segment in words
    return token in words


def main() -> int:
    parser = argparse.ArgumentParser(description="Flag wiki doc identifiers that no longer exist in code.")
    parser.add_argument("--docs", required=True, help="Directory of markdown docs to scan")
    parser.add_argument("--code", required=True, nargs="+", help="One or more source directories to search")
    parser.add_argument("--strict", action="store_true", help="Exit 1 if any finding is reported")
    args = parser.parse_args()

    docs_root = Path(args.docs).resolve()
    code_roots = [Path(c).resolve() for c in args.code]

    if not docs_root.is_dir():
        print(f"error: --docs path does not exist or is not a directory: {docs_root}")
        return 2
    for c in code_roots:
        if not c.is_dir():
            print(f"error: --code path does not exist or is not a directory: {c}")
            return 2

    documents = collect_documents(docs_root)
    print(f"Scanning {len(documents)} doc(s) under {docs_root}")
    words, filenames = build_code_index(code_roots)
    print(f"Indexed {len(words)} distinct code words and {len(filenames)} filenames "
          f"under {', '.join(str(c) for c in code_roots)}\n")

    total_checked = 0
    findings: list[str] = []
    for doc in documents:
        text = doc.read_text(encoding="utf-8", errors="ignore")
        rel = doc.relative_to(docs_root)
        seen_on_line: set[tuple[int, str]] = set()
        for lineno, token in extract_identifiers(text):
            if (lineno, token) in seen_on_line:
                continue
            seen_on_line.add((lineno, token))
            total_checked += 1
            if not check_identifier(token, words, filenames):
                findings.append(f"{rel}:{lineno}: `{token}` — not found in scanned code")

    print(f"Checked {total_checked} identifier reference(s).\n")

    if findings:
        print(f"POSSIBLY STALE ({len(findings)}):")
        for f in findings:
            print(f"  {f}")
        print(
            "\nThese are heuristic candidates, not confirmed bugs — verify each one "
            "manually (renamed/removed vs. a common word that just isn't in this code tree)."
        )
    else:
        print("No candidate stale identifiers found.")

    if args.strict and findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
