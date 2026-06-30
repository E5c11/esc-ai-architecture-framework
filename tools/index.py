#!/usr/bin/env python3
"""
Framework index generator.

Reads all framework documents and writes two outputs:
  - index.json  — machine-readable; used by agents for document lookup
  - index.md    — human-readable summary of all document IDs

Usage:
  python tools/index.py [--root <path>] [--out <path>]

The `index.json` schema:
  {
    "generated": "<ISO timestamp>",
    "count": <int>,
    "documents": [
      {
        "id":           "<DOC-ID>",
        "type":         "<type>",
        "layer":        "<layer>",
        "path":         "<repo-relative path>",
        "platform":     ["<platform>", ...],
        "architecture": "<architecture>",
        "requires":     ["<DOC-ID>", ...],
        "related":      ["<DOC-ID>", ...],
        "tags":         ["<tag>", ...]
      },
      ...
    ]
  }
"""

import json
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
from collections import defaultdict

LAYER_DIRS = [
    "core",
    "patterns",
    "architectures",
    "platforms",
    "build",
    "quality-gates",
    "feature-orchestrators",
]


def _parse_scalar(raw: str) -> str:
    return raw.strip().strip('"').strip("'")


def _parse_list(raw: str) -> list[str]:
    inner = raw.strip()
    if inner.startswith("[") and inner.endswith("]"):
        inner = inner[1:-1]
    if not inner.strip():
        return []
    return [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()]


def parse_front_matter(text: str) -> dict:
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    front = match.group(1)
    result: dict = {}
    for line in front.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, rest = line.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest.startswith("["):
            result[key] = _parse_list(rest)
        else:
            result[key] = _parse_scalar(rest)
    return result


def collect_documents(root: Path) -> list[dict]:
    documents = []
    for layer_dir in LAYER_DIRS:
        layer_path = root / layer_dir
        if not layer_path.exists():
            continue
        for md_file in sorted(layer_path.rglob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            meta = parse_front_matter(text)
            if not meta.get("id"):
                continue

            platform = meta.get("platform", [])
            if isinstance(platform, str):
                platform = [platform]

            architecture = meta.get("architecture", "")
            if isinstance(architecture, list):
                architecture = architecture[0] if architecture else ""

            documents.append({
                "id":           meta.get("id", ""),
                "type":         meta.get("type", ""),
                "layer":        layer_dir,
                "path":         str(md_file.relative_to(root)),
                "platform":     platform,
                "architecture": architecture,
                "requires":     meta.get("requires", []) if isinstance(meta.get("requires"), list) else [],
                "related":      meta.get("related",  []) if isinstance(meta.get("related"),  list) else [],
                "tags":         meta.get("tags",     []) if isinstance(meta.get("tags"),     list) else [],
            })
    return documents


def write_json_index(documents: list[dict], out_path: Path) -> None:
    index = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "count":     len(documents),
        "documents": sorted(documents, key=lambda d: d["id"]),
    }
    out_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(f"Written: {out_path}  ({len(documents)} documents)")


def write_markdown_index(documents: list[dict], out_path: Path) -> None:
    by_layer: dict[str, list[dict]] = defaultdict(list)
    for doc in documents:
        by_layer[doc["layer"]].append(doc)

    lines = [
        "# Framework Document Index",
        "",
        f"*Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d')} — {len(documents)} documents*",
        "",
    ]

    for layer in LAYER_DIRS:
        docs = by_layer.get(layer)
        if not docs:
            continue
        lines.append(f"## {layer}/")
        lines.append("")
        lines.append("| ID | Type | Path |")
        lines.append("|---|---|---|")
        for doc in sorted(docs, key=lambda d: d["id"]):
            lines.append(f"| `{doc['id']}` | {doc['type']} | `{doc['path']}` |")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Written: {out_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate ESC AI Framework document index.")
    parser.add_argument("--root", default=".", help="Framework repo root (default: .)")
    parser.add_argument("--out",  default=".", help="Output directory for index files (default: .)")
    args = parser.parse_args()

    root    = Path(args.root).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    documents = collect_documents(root)
    print(f"Collected {len(documents)} documents.\n")

    write_json_index(documents,    out_dir / "index.json")
    write_markdown_index(documents, out_dir / "index.md")

    return 0


if __name__ == "__main__":
    sys.exit(main())
