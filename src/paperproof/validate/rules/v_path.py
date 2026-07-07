"""V-PATH rules: file/path safety, applied to every worker output (docs/09, docs/05).

V-PATH-01  output path exactly matches the work item's declared output_files
V-PATH-02  path is project-relative, no upward traversal, no symlink escape
V-PATH-03  file is valid UTF-8 JSON (or .md for prose), single document
V-PATH-04  no writes outside allowed_write_paths - the PREFIX rule: every JSONL
           file in lease.manifest still hash-matches on its first recorded
           `size` bytes (concurrent engines only append; a broken prefix =
           rewrite/truncation), every recorded non-JSONL file is byte-identical,
           and no file appears outside allowed_write_paths
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ...store.jsonl import PathSafetyError, safe_resolve
from ..envelope import Failure


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check_output_path(actual_relpath: str, declared_output_files: list[str]) -> list[Failure]:
    """V-PATH-01: the actual output path must exactly match a declared output."""
    if actual_relpath not in declared_output_files:
        return [
            Failure(
                "V-PATH-01",
                f"output path {actual_relpath!r} not in declared {declared_output_files!r}",
            )
        ]
    return []


def check_path_safety(project_dir: str | Path, relpath: str) -> list[Failure]:
    """V-PATH-02: project-relative, no traversal, no symlink escape."""
    try:
        safe_resolve(project_dir, relpath)
    except PathSafetyError as exc:
        return [Failure("V-PATH-02", "; ".join(exc.errors))]
    return []


def check_utf8_json(project_dir: str | Path, relpath: str, kind: str = "json") -> list[Failure]:
    """V-PATH-03: valid UTF-8 and (for json) a single JSON document."""
    try:
        path = safe_resolve(project_dir, relpath)
    except PathSafetyError as exc:
        return [Failure("V-PATH-02", "; ".join(exc.errors))]
    if not path.exists():
        return [Failure("V-PATH-03", f"output file missing: {relpath}")]
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [Failure("V-PATH-03", f"not valid UTF-8: {relpath}: {exc}")]
    if kind == "json":
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            return [Failure("V-PATH-03", f"not a single JSON document: {relpath}: {exc.msg}")]
    return []


def build_manifest(project_dir: str | Path, relpaths: list[str]) -> dict[str, dict[str, Any]]:
    """Claim-time manifest: (size, sha256, jsonl) per canonical file (docs/05)."""
    project_dir = Path(project_dir)
    manifest: dict[str, dict[str, Any]] = {}
    for rel in relpaths:
        p = project_dir / rel
        data = p.read_bytes() if p.exists() else b""
        manifest[rel] = {"size": len(data), "sha256": _sha(data), "jsonl": rel.endswith(".jsonl")}
    return manifest


def check_prefix_rule(project_dir: str | Path, manifest: dict[str, dict[str, Any]]) -> list[Failure]:
    """V-PATH-04 (prefix): each JSONL's first `size` bytes still hash-match;
    each non-JSONL is byte-identical. Legitimate appends pass; a broken prefix
    means someone rewrote, truncated, or edited history."""
    project_dir = Path(project_dir)
    failures: list[Failure] = []
    for rel, rec in manifest.items():
        p = project_dir / rel
        data = p.read_bytes() if p.exists() else b""
        if rec["jsonl"]:
            prefix = data[: rec["size"]]
            if len(prefix) < rec["size"] or _sha(prefix) != rec["sha256"]:
                failures.append(Failure("V-PATH-04", f"JSONL prefix broken (rewrite/truncate): {rel}"))
        else:
            if _sha(data) != rec["sha256"]:
                failures.append(Failure("V-PATH-04", f"non-JSONL file modified: {rel}"))
    return failures


# Files only the Committer/Freeze/Docs-ingestor write. A proof worker's lease
# window [claim, validate] never legitimately coincides with a change to these
# (commits run after validate in the layer loop), so any change to them during a
# lease is worker tampering (catches H10). Legit engine appends to queue/proof
# JSONL still pass via the prefix rule. (docs/05 §Parallelism; see OPEN DOC ISSUES.)
COMMITTER_OWNED: frozenset[str] = frozenset(
    {
        "graph/logic_nodes.jsonl",
        "graph/logic_edges.jsonl",
        "graph/tombstones.jsonl",
        "graph/snapshots.jsonl",
        "commit/commit_decisions.jsonl",
        "freeze/frozen_items.jsonl",
        "docs/documents.jsonl",
        "docs/evidence_units.jsonl",
        "docs/docs_requests.jsonl",
    }
)


def check_lease_scan(project_dir: str | Path, lease_manifest: dict[str, Any]) -> list[Failure]:
    """Full post-run V-PATH-04 scan from a claim-time lease manifest blob
    (keys: files, baseline, allowed). Prefix rule on all JSONL, byte-identity on
    non-JSONL and on committer-owned files, plus the stray-write rule."""
    project_dir = Path(project_dir)
    files = lease_manifest.get("files", {})
    failures = check_prefix_rule(project_dir, files)
    for rel, rec in files.items():
        if rel in COMMITTER_OWNED:
            p = project_dir / rel
            data = p.read_bytes() if p.exists() else b""
            if _sha(data) != rec["sha256"]:
                failures.append(Failure("V-PATH-04", f"committer-owned file changed under a worker lease: {rel}"))
    # Stray-write rule: a worker may only create files under agent_outputs/** or
    # agent_notes/**. Using the broad agent area (not the item's single declared
    # output) avoids false positives from CONCURRENT workers' own output files;
    # V-PATH-01 separately pins this worker to its exact declared output. A new
    # file anywhere in a canonical directory is the violation. (OPEN DOC ISSUE.)
    baseline = set(lease_manifest.get("baseline", []))
    failures += check_no_stray_writes(project_dir, baseline, ["agent_outputs/**", "agent_notes/**"])
    return failures


def build_lease_manifest(project_dir: str | Path, allowed_write_paths: list[str]) -> dict[str, Any]:
    """Claim-time manifest over every canonical (non-agent) file: prefix hashes,
    a baseline file set for the stray-write rule, and the allowed write paths."""
    project_dir = Path(project_dir)
    baseline = sorted(_walk_relpaths(project_dir))
    canonical = [
        rel
        for rel in baseline
        if not rel.startswith("agent_outputs/")
        and not rel.startswith("agent_notes/")
        and not rel.endswith(".lock")
    ]
    return {
        "files": build_manifest(project_dir, canonical),
        "baseline": baseline,
        "allowed": list(allowed_write_paths),
    }


def _is_allowed(rel: str, allowed_write_paths: list[str]) -> bool:
    for allowed in allowed_write_paths:
        if allowed.endswith("/**"):
            prefix = allowed[:-2]  # keep trailing slash
            if rel.startswith(prefix):
                return True
        elif rel == allowed:
            return True
    return False


def _walk_relpaths(project_dir: Path) -> set[str]:
    out: set[str] = set()
    for p in project_dir.rglob("*"):
        if p.is_file():
            out.add(str(p.relative_to(project_dir)))
    return out


def check_no_stray_writes(
    project_dir: str | Path,
    baseline_files: set[str],
    allowed_write_paths: list[str],
) -> list[Failure]:
    """V-PATH-04 (scope): any file present now that was absent at claim time and
    is not under allowed_write_paths is a stray write."""
    project_dir = Path(project_dir)
    failures: list[Failure] = []
    for rel in sorted(_walk_relpaths(project_dir) - baseline_files):
        if not _is_allowed(rel, allowed_write_paths):
            failures.append(Failure("V-PATH-04", f"write outside allowed paths: {rel}"))
    return failures
