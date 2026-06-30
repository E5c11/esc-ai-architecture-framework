#!/usr/bin/env python3
"""
Framework document validator.

Checks:
  1. Every document has an `id` field in its front matter.
  2. No two documents share the same ID (duplicate check).
  3. All IDs referenced in `requires` and `related` exist (reference check).
  4. No circular `requires` chains (cycle check).
  5. Document ID prefix matches the document's layer directory.

Usage:
  python tools/validate.py [--root <path>]

Exit code: 0 = all checks passed, 1 = one or more failures.
"""

import re
import sys
import argparse
from pathlib import Path
from collections import defaultdict, deque

# Directories that contain framework documents (relative to repo root)
LAYER_DIRS = [
    "core",
    "patterns",
    "architectures",
    "platforms",
    "build",
    "quality-gates",
    "feature-orchestrators",
]

# Expected ID prefix for each layer directory
LAYER_PREFIXES = {
    "core":                 "CORE-",
    "patterns":             "PAT-",
    "architectures":        "ARCH-",
    "platforms":            "PLAT-",
    "build":                "BUILD-",
    "quality-gates":        "QG-",
    "feature-orchestrators": "ORCH-",
}

ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*(-[A-Z0-9]+)+$")


# ---------------------------------------------------------------------------
# Front matter parsing — no external dependencies
# ---------------------------------------------------------------------------

def _parse_scalar(raw: str) -> str:
    return raw.strip().strip('"').strip("'")


def _parse_inline_list(raw: str) -> list[str]:
    """Parse '[A, B, C]' or '[]' into a list of strings."""
    inner = raw.strip()
    if inner.startswith("[") and inner.endswith("]"):
        inner = inner[1:-1]
    if not inner.strip():
        return []
    return [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()]


def parse_front_matter(text: str) -> dict:
    """
    Extract fields from YAML front matter delimited by '---'.
    Returns {} if no front matter is found.
    Handles scalar values, inline lists [A, B], and block sequences:
      key:
        - A
        - B
    """
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}

    lines = match.group(1).splitlines()
    result: dict = {}
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if ":" not in stripped:
            i += 1
            continue

        key, _, rest = stripped.partition(":")
        key = key.strip()
        rest = rest.strip()

        if rest.startswith("["):
            result[key] = _parse_inline_list(rest)
            i += 1
        elif rest == "":
            # Possible block sequence — collect '  - item' lines
            items = []
            i += 1
            while i < len(lines):
                next_stripped = lines[i].strip()
                if next_stripped.startswith("- "):
                    items.append(next_stripped[2:].strip().strip('"').strip("'"))
                    i += 1
                elif next_stripped == "" or next_stripped.startswith("#"):
                    i += 1
                    break
                else:
                    break
            result[key] = items if items else ""
        else:
            result[key] = _parse_scalar(rest)
            i += 1

    return result


# ---------------------------------------------------------------------------
# Document collection
# ---------------------------------------------------------------------------

def collect_documents(root: Path) -> list[dict]:
    """
    Walk every layer directory and return a list of document records:
    { path, id, layer, requires, related }
    """
    documents = []
    for layer_dir in LAYER_DIRS:
        layer_path = root / layer_dir
        if not layer_path.exists():
            continue
        for md_file in sorted(layer_path.rglob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            meta = parse_front_matter(text)
            if not meta:
                continue
            documents.append({
                "path":     md_file.relative_to(root),
                "layer":    layer_dir,
                "id":       meta.get("id", ""),
                "requires": meta.get("requires", []) if isinstance(meta.get("requires"), list) else [],
                "related":  meta.get("related",  []) if isinstance(meta.get("related"),  list) else [],
            })
    return documents


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_missing_ids(documents: list[dict]) -> list[str]:
    errors = []
    for doc in documents:
        if not doc["id"]:
            errors.append(f"  MISSING ID  {doc['path']}")
    return errors


def check_duplicate_ids(documents: list[dict]) -> list[str]:
    seen: dict[str, list] = defaultdict(list)
    for doc in documents:
        if doc["id"]:
            seen[doc["id"]].append(doc["path"])
    errors = []
    for doc_id, paths in seen.items():
        if len(paths) > 1:
            listed = "\n".join(f"    {p}" for p in paths)
            errors.append(f"  DUPLICATE ID  {doc_id}\n{listed}")
    return errors


def check_id_pattern(documents: list[dict]) -> list[str]:
    errors = []
    for doc in documents:
        doc_id = doc["id"]
        if not doc_id:
            continue
        if not ID_PATTERN.match(doc_id):
            errors.append(f"  INVALID ID FORMAT  {doc_id!r}  in {doc['path']}")
    return errors


def check_layer_prefix(documents: list[dict]) -> list[str]:
    errors = []
    for doc in documents:
        doc_id = doc["id"]
        layer  = doc["layer"]
        if not doc_id:
            continue
        expected_prefix = LAYER_PREFIXES.get(layer)
        if expected_prefix and not doc_id.startswith(expected_prefix):
            errors.append(
                f"  PREFIX MISMATCH  {doc_id!r} in layer '{layer}' "
                f"should start with '{expected_prefix}'  ({doc['path']})"
            )
    return errors


def check_broken_references(documents: list[dict]) -> list[str]:
    known_ids = {doc["id"] for doc in documents if doc["id"]}
    errors = []
    for doc in documents:
        for ref in doc["requires"] + doc["related"]:
            if ref and ref not in known_ids:
                errors.append(
                    f"  BROKEN REF  {doc['id']} → '{ref}'  ({doc['path']})"
                )
    return errors


def check_circular_requires(documents: list[dict]) -> list[str]:
    """Detect cycles in the `requires` graph using DFS."""
    graph: dict[str, list[str]] = {doc["id"]: doc["requires"] for doc in documents if doc["id"]}
    errors = []
    visited: set[str] = set()
    in_stack: set[str] = set()

    def dfs(node: str, path: list[str]) -> None:
        if node in in_stack:
            cycle_start = path.index(node)
            cycle = " → ".join(path[cycle_start:] + [node])
            errors.append(f"  CIRCULAR REQUIRES  {cycle}")
            return
        if node in visited:
            return
        visited.add(node)
        in_stack.add(node)
        for neighbour in graph.get(node, []):
            if neighbour in graph:
                dfs(neighbour, path + [node])
        in_stack.discard(node)

    for node in graph:
        if node not in visited:
            dfs(node, [])

    return errors


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ESC AI Framework documents.")
    parser.add_argument(
        "--root",
        default=".",
        help="Path to the framework repo root (default: current directory)",
    )
    args = parser.parse_args()
    root = Path(args.root).resolve()

    print(f"Validating framework at: {root}\n")

    documents = collect_documents(root)
    print(f"Found {len(documents)} documents across {len(LAYER_DIRS)} layer directories.\n")

    all_errors: list[tuple[str, list[str]]] = [
        ("Missing IDs",           check_missing_ids(documents)),
        ("Duplicate IDs",         check_duplicate_ids(documents)),
        ("Invalid ID format",     check_id_pattern(documents)),
        ("Layer prefix mismatch", check_layer_prefix(documents)),
        ("Broken references",     check_broken_references(documents)),
        ("Circular requires",     check_circular_requires(documents)),
    ]

    any_failure = False
    for check_name, errors in all_errors:
        if errors:
            any_failure = True
            print(f"FAIL  {check_name} ({len(errors)} issue{'s' if len(errors) != 1 else ''}):")
            for err in errors:
                print(err)
            print()
        else:
            print(f"OK    {check_name}")

    print()
    if any_failure:
        print("Validation FAILED. Fix the issues above before merging.")
        return 1
    else:
        print("All checks passed.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
