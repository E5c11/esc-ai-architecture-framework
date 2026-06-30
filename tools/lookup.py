#!/usr/bin/env python3
"""
Framework document lookup — resolves the minimal ordered document set for a task.

Two access modes:
  Orchestrator mode  — full dependency graph for orientation or CI validation
  Phase mode         — minimal doc set for a single implementation phase

Pass --use-index to read the pre-built index.json instead of scanning files.
Pass --profile to include provider-specific docs derived from a project profile.

Usage:
  # Full orchestrator load list (orientation / CI)
  python tools/lookup.py --orchestrator ORCH-MOB-FEAT

  # Single-phase load list (progressive implementation — preferred)
  python tools/lookup.py --orchestrator ORCH-MOB-FEAT --phase 2

  # With project profile (adds provider-specific docs)
  python tools/lookup.py --orchestrator ORCH-MOB-FEAT --phase 2 --profile context/project-profile.yaml

  # Use pre-built index.json instead of scanning filesystem
  python tools/lookup.py --orchestrator ORCH-MOB-FEAT --phase 2 --use-index

  # List all orchestrators
  python tools/lookup.py --list --platform mobile

Output (default): human-readable load list with phase context.
Output (--json):  JSON object/array suitable for programmatic consumption.

Exit code: 0 = success, 1 = orchestrator not found or error.
"""

import re
import sys
import json
import argparse
from pathlib import Path

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

LAYER_ORDER = {
    "core":                  0,
    "patterns":              1,
    "architectures":         2,
    "platforms":             3,
    "build":                 4,
    "quality-gates":         5,
    "feature-orchestrators": 6,
}

# Maps project profile frameworks fields to additional doc IDs.
PROFILE_DOC_MAP: dict[str, dict[str, list[str]]] = {
    "database": {
        "room":     ["PLAT-MOB-ROOM"],
    },
    "network": {
        "ktor":     ["PLAT-MOB-HTTP"],
        "http":     ["PLAT-MOB-HTTP"],
        "retrofit": ["PLAT-MOB-HTTP"],
    },
    "cloud": {
        "firebase": ["PLAT-MOB-FIREBASE"],
    },
    "notifications": {
        "workmanager": ["PLAT-MOB-NOTIF"],
    },
    "storage": {
        "datastore": ["PLAT-MOB-DATASTORE"],
    },
}


# ---------------------------------------------------------------------------
# Front matter parser
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
# Project profile parser (no external dependencies)
# ---------------------------------------------------------------------------

def parse_profile(path: Path) -> dict:
    """Parse a 2-level project-profile.yaml without external dependencies."""
    result: dict = {}
    current_section: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if ":" not in stripped:
            continue
        key, _, val = stripped.partition(":")
        key, val = key.strip(), val.strip()
        if indent == 0:
            if not val:
                current_section = key
                result[key] = {}
            else:
                current_section = None
                result[key] = val
        elif current_section and isinstance(result.get(current_section), dict):
            result[current_section][key] = val
    return result


def profile_extra_docs(profile: dict) -> list[str]:
    """Return additional doc IDs implied by the project profile's frameworks section."""
    extras: list[str] = []
    frameworks = profile.get("frameworks", {})
    if not isinstance(frameworks, dict):
        return extras
    for field, value in frameworks.items():
        for doc_id in PROFILE_DOC_MAP.get(field, {}).get(value, []):
            if doc_id not in extras:
                extras.append(doc_id)
    return extras


# ---------------------------------------------------------------------------
# Phase parsing
# ---------------------------------------------------------------------------

def find_phase_section(text: str, phase_number: int) -> str | None:
    """Return the markdown text of the specified phase section, or None."""
    lines = text.splitlines()
    start = None
    pattern = re.compile(rf"^##\s+Phase\s+{phase_number}(?:\s|$)")
    for i, line in enumerate(lines):
        if pattern.match(line):
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break
    return "\n".join(lines[start:end])


def extract_required_docs(phase_text: str) -> list[str]:
    """Extract doc IDs from the **Required framework docs:** line."""
    match = re.search(r"\*\*Required framework docs:\*\*\s*(.+)", phase_text)
    if not match:
        return []
    return re.findall(r"`([A-Z][A-Z0-9-]+)`", match.group(1))


def extract_phase_context(phase_text: str) -> dict[str, str]:
    """Extract Code paths, Assumes, and Produces from the phase header block."""
    result: dict[str, str] = {}
    for field in ["Code paths", "Assumes", "Produces"]:
        match = re.search(rf"\*\*{field}:\*\*\s*(.+)", phase_text)
        if match:
            result[field.lower().replace(" ", "_")] = match.group(1).strip()
    return result


def count_phases(orchestrator_text: str) -> int:
    """Return the number of numbered phases in the orchestrator."""
    return len(re.findall(r"^##\s+Phase\s+\d+", orchestrator_text, re.MULTILINE))


# ---------------------------------------------------------------------------
# Index building
# ---------------------------------------------------------------------------

def build_index(root: Path) -> dict[str, dict]:
    """Scan all framework docs and build an in-memory index."""
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
                "status":   meta.get("status", ""),
            }
    return index


def build_index_from_file(index_path: Path) -> dict[str, dict]:
    """Load the pre-built index.json instead of scanning the filesystem."""
    data = json.loads(index_path.read_text(encoding="utf-8"))
    return {doc["id"]: doc for doc in data["documents"]}


# ---------------------------------------------------------------------------
# Topological resolution (orchestrator mode)
# ---------------------------------------------------------------------------

def resolve(start_id: str, index: dict[str, dict]) -> list[dict]:
    if start_id not in index:
        return []
    visited: set[str] = set()
    result: list[str] = []

    def visit(doc_id: str) -> None:
        if doc_id in visited:
            return
        visited.add(doc_id)
        for dep in index.get(doc_id, {}).get("requires", []):
            if dep in index:
                visit(dep)
        result.append(doc_id)

    visit(start_id)
    result.sort(key=lambda doc_id: LAYER_ORDER.get(index[doc_id]["layer"], 99))
    if start_id in result:
        result.remove(start_id)
        result.append(start_id)
    return [index[doc_id] for doc_id in result if doc_id in index]


def merge_profile_docs(docs: list[dict], extra_ids: list[str], index: dict[str, dict]) -> list[dict]:
    resolved_ids = {d["id"] for d in docs}
    orchestrator = docs[-1] if docs else None
    base = docs[:-1] if orchestrator else docs[:]
    for extra_id in extra_ids:
        if extra_id not in resolved_ids and extra_id in index:
            base.append(index[extra_id])
            resolved_ids.add(extra_id)
    base.sort(key=lambda d: LAYER_ORDER.get(d["layer"], 99))
    return base + ([orchestrator] if orchestrator else [])


# ---------------------------------------------------------------------------
# Shared output helpers
# ---------------------------------------------------------------------------

def warn_stubs(docs: list[dict]) -> None:
    stubs = [d for d in docs if d.get("status") == "stub"]
    if stubs:
        print(f"Warning: {len(stubs)} stub doc(s) in set — gap protocol applies:", file=sys.stderr)
        for s in stubs:
            print(f"  {s['id']}  ({s['path']})", file=sys.stderr)
        print(file=sys.stderr)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_lookup(
    orchestrator_id: str,
    index: dict[str, dict],
    as_json: bool,
    extra_ids: list[str] | None = None,
) -> int:
    """Orchestrator mode — full dependency graph."""
    if orchestrator_id not in index:
        print(f"Error: orchestrator '{orchestrator_id}' not found.", file=sys.stderr)
        return 1

    docs = resolve(orchestrator_id, index)
    if extra_ids:
        docs = merge_profile_docs(docs, extra_ids, index)

    warn_stubs(docs)

    profile_ids = set(extra_ids or [])

    if as_json:
        print(json.dumps(
            [{"id": d["id"], "path": d["path"], "type": d["type"], "status": d.get("status", "")} for d in docs],
            indent=2,
        ))
    else:
        print(f"Load order for {orchestrator_id} ({len(docs)} documents):\n")
        for i, d in enumerate(docs, 1):
            profile_label = "(from profile) " if d["id"] in profile_ids else ""
            stub_label    = " ⚠ stub"          if d.get("status") == "stub" else ""
            orch_label    = " ← orchestrator"   if d["id"] == orchestrator_id else ""
            print(f"  {i:2}. {d['id']:<40} {profile_label}{d['layer']}/{Path(d['path']).name}{stub_label}{orch_label}")
    return 0


def cmd_phase(
    orchestrator_id: str,
    phase_number: int,
    index: dict[str, dict],
    root: Path,
    as_json: bool,
    extra_ids: list[str] | None = None,
) -> int:
    """Phase mode — minimal doc set for a single implementation phase."""
    if orchestrator_id not in index:
        print(f"Error: orchestrator '{orchestrator_id}' not found.", file=sys.stderr)
        return 1

    orch_path = root / index[orchestrator_id]["path"]
    orch_text = orch_path.read_text(encoding="utf-8")
    total_phases = count_phases(orch_text)

    phase_text = find_phase_section(orch_text, phase_number)
    if phase_text is None:
        print(f"Error: Phase {phase_number} not found in {orchestrator_id} ({total_phases} phases available).", file=sys.stderr)
        return 1

    doc_ids = extract_required_docs(phase_text)
    if not doc_ids:
        print(f"Error: no 'Required framework docs:' header found in Phase {phase_number}.", file=sys.stderr)
        print("Ensure the phase uses the standard header format.", file=sys.stderr)
        return 1

    # Merge profile extras
    all_ids = list(doc_ids)
    for extra_id in (extra_ids or []):
        if extra_id not in all_ids:
            all_ids.append(extra_id)

    docs: list[dict] = []
    missing: list[str] = []
    for doc_id in all_ids:
        if doc_id in index:
            docs.append(index[doc_id])
        else:
            missing.append(doc_id)

    if missing:
        print(f"Warning: doc IDs listed in phase but not in index: {', '.join(missing)}", file=sys.stderr)

    docs.sort(key=lambda d: LAYER_ORDER.get(d["layer"], 99))
    warn_stubs(docs)

    context = extract_phase_context(phase_text)
    profile_ids = set(extra_ids or [])

    if as_json:
        print(json.dumps({
            "orchestrator":  orchestrator_id,
            "phase":         phase_number,
            "total_phases":  total_phases,
            "context":       context,
            "documents":     [{"id": d["id"], "path": d["path"], "type": d["type"], "status": d.get("status", "")} for d in docs],
        }, indent=2))
    else:
        print(f"Phase {phase_number}/{total_phases} of {orchestrator_id} ({len(docs)} documents):\n")
        if context.get("assumes"):
            print(f"  Assumes:    {context['assumes']}")
        if context.get("produces"):
            print(f"  Produces:   {context['produces']}")
        if context.get("code_paths"):
            print(f"  Code paths: {context['code_paths']}")
        print()
        for i, d in enumerate(docs, 1):
            profile_label = " (from profile)" if d["id"] in profile_ids else ""
            stub_label    = " ⚠ stub"          if d.get("status") == "stub" else ""
            print(f"  {i:2}. {d['id']:<40} {d['layer']}/{Path(d['path']).name}{profile_label}{stub_label}")
    return 0


def cmd_list(index: dict[str, dict], platform_filter: str | None) -> int:
    orchestrators = [d for d in index.values() if d["layer"] == "feature-orchestrators"]
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
    parser.add_argument("--orchestrator", "-o", help="Orchestrator ID (e.g. ORCH-MOB-FEAT)")
    parser.add_argument("--phase",        "-n", type=int, help="Phase number for progressive loading (e.g. 2)")
    parser.add_argument("--profile",      "-p", help="Path to project-profile.yaml for provider-specific docs")
    parser.add_argument("--use-index",          action="store_true", help="Read index.json instead of scanning files")
    parser.add_argument("--list",         "-l", action="store_true", help="List all available orchestrators")
    parser.add_argument("--platform",           help="Filter --list by platform (mobile/backend/web)")
    parser.add_argument("--json",               action="store_true", help="Output as JSON")
    parser.add_argument("--root",               default=".", help="Framework repo root (default: .)")

    args = parser.parse_args()
    root = Path(args.root).resolve()

    # Build index
    if args.use_index:
        index_path = root / "index.json"
        if not index_path.exists():
            print(f"Error: index.json not found at {index_path}. Run tools/index.py first.", file=sys.stderr)
            return 1
        print(f"Using pre-built index ({index_path.name})\n")
        index = build_index_from_file(index_path)
    else:
        index = build_index(root)

    if args.list:
        return cmd_list(index, args.platform)

    if not args.orchestrator:
        parser.print_help()
        return 0

    # Resolve profile extras
    extra_ids: list[str] = []
    if args.profile:
        profile_path = Path(args.profile)
        if not profile_path.exists():
            print(f"Error: profile not found: {profile_path}", file=sys.stderr)
            return 1
        profile = parse_profile(profile_path)
        extra_ids = profile_extra_docs(profile)
        if extra_ids:
            print(f"Profile adds: {', '.join(extra_ids)}\n")

    if args.phase is not None:
        return cmd_phase(args.orchestrator, args.phase, index, root, args.json, extra_ids or None)

    return cmd_lookup(args.orchestrator, index, args.json, extra_ids or None)


if __name__ == "__main__":
    sys.exit(main())
