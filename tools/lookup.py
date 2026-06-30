#!/usr/bin/env python3
"""
Framework document lookup — resolves the minimal ordered document set for a task.

Given an orchestrator ID (or platform + task hint), returns the ordered list of
document IDs an AI agent should load before executing the orchestrator.

The list is a topological sort of the `requires` graph rooted at the orchestrator.
Core principles come first; the orchestrator itself comes last.

Usage:
  # By orchestrator ID
  python tools/lookup.py --orchestrator ORCH-MOB-FEAT

  # List all orchestrators
  python tools/lookup.py --list

  # Filter by platform
  python tools/lookup.py --list --platform mobile

Output (default): one document ID per line, in load order.
Output (--json):  JSON array of { id, path, type } objects.

Exit code: 0 = success, 1 = orchestrator not found or error.
"""

import re
import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict, deque

FRAMEWORK_ROOT = Path(__file__).parent.parent

LAYER_DIRS = [
    "core",
    "patterns",
    "architectures",
    "platforms",
    "build",
    "quality-gates",
    "feature-orchestrators",
]

# Load order priority — lower number is loaded first
LAYER_ORDER = {
    "core":                  0,
    "patterns":              1,
    "architectures":         2,
    "platforms":             3,
    "build":                 4,
    "quality-gates":         5,
    "feature-orchestrators": 6,
}


# ---------------------------------------------------------------------------
# Front matter parser (duplicated from validate.py — no shared module needed)
# ---------------------------------------------------------------------------

def _parse_inline_list(raw: str) -> list[str]:
    inner = raw.strip()
    if inner.startswith("[") and inner.endswith("]"):
        inner = inner[1:-1]
    if not inner.strip():
        return []
    return [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()]


def _parse_scalar(raw: str) -> str:
    return raw.strip().strip('"').strip("'")


def parse_front_matter(text: str) -> dict:
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
# Index building
# ---------------------------------------------------------------------------

def build_index(root: Path) -> dict[str, dict]:
    """Return {doc_id: {id, path, layer, type, requires, related, platform}} for all docs."""
    index: dict[str, dict] = {}
    for layer_dir in LAYER_DIRS:
        layer_path = root / layer_dir
        if not layer_path.exists():
            continue
        for md_file in sorted(layer_path.rglob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            meta = parse_front_matter(text)
            doc_id = meta.get("id", "")
            if not doc_id:
                continue

            platform = meta.get("platform", [])
            if isinstance(platform, str):
                platform = [platform]

            index[doc_id] = {
                "id":       doc_id,
                "path":     str(md_file.relative_to(root)),
                "layer":    layer_dir,
                "type":     meta.get("type", ""),
                "requires": meta.get("requires", []) if isinstance(meta.get("requires"), list) else [],
                "related":  meta.get("related",  []) if isinstance(meta.get("related"),  list) else [],
                "platform": platform,
            }
    return index


# ---------------------------------------------------------------------------
# Topological resolution
# ---------------------------------------------------------------------------

def resolve(start_id: str, index: dict[str, dict]) -> list[dict]:
    """
    Topological sort of the `requires` graph rooted at `start_id`.
    Returns documents in dependency order: dependencies before dependents.
    The start document (the orchestrator) is last.
    Cycles are broken by layer order (core before patterns before architectures...).
    """
    if start_id not in index:
        return []

    visited: set[str] = set()
    result: list[str] = []

    def visit(doc_id: str) -> None:
        if doc_id in visited:
            return
        visited.add(doc_id)
        doc = index.get(doc_id)
        if not doc:
            return
        for dep in doc.get("requires", []):
            if dep in index:
                visit(dep)
        result.append(doc_id)

    visit(start_id)

    # Stable sort: within the DFS order, respect layer priority
    result.sort(key=lambda doc_id: LAYER_ORDER.get(index[doc_id]["layer"], 99))
    # Put the orchestrator last
    if start_id in result:
        result.remove(start_id)
        result.append(start_id)

    return [index[doc_id] for doc_id in result if doc_id in index]


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_lookup(orchestrator_id: str, index: dict[str, dict], as_json: bool) -> int:
    if orchestrator_id not in index:
        print(f"Error: orchestrator '{orchestrator_id}' not found.", file=sys.stderr)
        print("Run with --list to see available orchestrators.", file=sys.stderr)
        return 1

    doc = index[orchestrator_id]
    if doc["layer"] != "feature-orchestrators":
        print(
            f"Warning: '{orchestrator_id}' is not an orchestrator (layer: {doc['layer']}).\n"
            "Resolving its dependency chain anyway.",
            file=sys.stderr,
        )

    docs = resolve(orchestrator_id, index)

    if as_json:
        output = [{"id": d["id"], "path": d["path"], "type": d["type"]} for d in docs]
        print(json.dumps(output, indent=2))
    else:
        print(f"Load order for {orchestrator_id} ({len(docs)} documents):\n")
        for i, d in enumerate(docs, 1):
            marker = "← orchestrator" if d["id"] == orchestrator_id else ""
            print(f"  {i:2}. {d['id']:<40} {d['layer']}/{Path(d['path']).name}  {marker}")

    return 0


def cmd_list(index: dict[str, dict], platform_filter: str | None) -> int:
    orchestrators = [
        d for d in index.values()
        if d["layer"] == "feature-orchestrators"
    ]
    if platform_filter:
        orchestrators = [
            d for d in orchestrators
            if platform_filter in d.get("platform", []) or "all" in d.get("platform", [])
        ]

    if not orchestrators:
        print("No orchestrators found.")
        return 0

    print(f"Available orchestrators ({len(orchestrators)}):\n")
    for d in sorted(orchestrators, key=lambda x: x["id"]):
        platforms = ", ".join(d.get("platform", []))
        print(f"  {d['id']:<35} platforms: [{platforms}]")
        print(f"    {d['path']}")
        print()

    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Look up the ordered document set for a framework orchestrator."
    )
    parser.add_argument("--orchestrator", "-o", help="Orchestrator ID to resolve (e.g. ORCH-MOB-FEAT)")
    parser.add_argument("--list",     "-l", action="store_true", help="List all available orchestrators")
    parser.add_argument("--platform", "-p", help="Filter --list by platform (mobile/backend/web)")
    parser.add_argument("--json",          action="store_true", help="Output as JSON array")
    parser.add_argument("--root",          default=".", help="Framework repo root (default: .)")

    args = parser.parse_args()
    root = Path(args.root).resolve()

    index = build_index(root)

    if args.list:
        return cmd_list(index, args.platform)

    if args.orchestrator:
        return cmd_lookup(args.orchestrator, index, args.json)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
