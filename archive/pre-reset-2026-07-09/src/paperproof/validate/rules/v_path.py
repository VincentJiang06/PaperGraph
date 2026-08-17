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


# V-PATH-04, the three clauses of docs/05 §Parallelism (r3):
#   (a) JSONL prefix intact — rewrites/truncations fail; APPENDS ARE NEVER
#       INSPECTED HERE (concurrent engines legitimately append during any
#       lease; attribution of appended graph records is `verify`'s job via the
#       V-COMMIT-04 replay + snapshot-EOF check).
#   (b) recorded IMMUTABLE non-JSONL files byte-identical (bundles, specs,
#       prose, raw/text). db/** is NEVER in the manifest — it is derived and
#       legitimately rebuilt at any moment.
#   (c) NEW files fail only under the strict single-writer dirs below, where a
#       new file is never legitimate mid-run. Engine-additive dirs (bundle
#       dirs, docs/raw|text|docspacks, db/, compiler/) create files during
#       leases by design and are exempt.
# The r2 impl's committer-owned byte-identity + all-dirs new-file baseline
# were non-conformant with docs/05 and killed 5 of the live run's 8
# validations (QE-000048/51/64/101/104).
STRICT_NEW_FILE_DIRS: tuple[str, ...] = (
    "specs/", "graph/", "queue/", "commit/", "freeze/", "audit/",
)
_MANIFEST_EXCLUDE_PREFIXES: tuple[str, ...] = (
    "agent_outputs/", "agent_notes/", "db/",
)


def check_lease_scan(project_dir: str | Path, lease_manifest: dict[str, Any]) -> list[Failure]:
    """Full post-run V-PATH-04 scan from a claim-time lease manifest blob
    (keys: files, baseline, allowed) — exactly the three docs/05 clauses."""
    project_dir = Path(project_dir)
    files = lease_manifest.get("files", {})
    # (a) + (b): prefix rule on JSONL, byte-identity on recorded non-JSONL.
    failures = check_prefix_rule(project_dir, files)
    # (c): new files only under the strict single-writer dirs are violations.
    baseline = set(lease_manifest.get("baseline", []))
    for rel in sorted(_walk_relpaths(project_dir) - baseline):
        if rel.startswith(STRICT_NEW_FILE_DIRS) and not rel.endswith(".lock"):
            failures.append(Failure("V-PATH-04", f"new file in single-writer dir: {rel}"))
    return failures


def build_lease_manifest(project_dir: str | Path, allowed_write_paths: list[str]) -> dict[str, Any]:
    """Claim-time manifest: prefix hashes for every canonical file (db/** and
    agent areas excluded), a baseline set for the strict-dir new-file clause,
    and the allowed write paths."""
    project_dir = Path(project_dir)
    baseline = sorted(
        rel for rel in _walk_relpaths(project_dir)
        if not rel.startswith(_MANIFEST_EXCLUDE_PREFIXES)
    )
    canonical = [rel for rel in baseline if not rel.endswith(".lock")]
    return {
        "files": build_manifest(project_dir, canonical),
        "baseline": baseline,
        "allowed": list(allowed_write_paths),
    }


def _walk_relpaths(project_dir: Path) -> set[str]:
    out: set[str] = set()
    for p in project_dir.rglob("*"):
        if p.is_file():
            out.add(str(p.relative_to(project_dir)))
    return out
