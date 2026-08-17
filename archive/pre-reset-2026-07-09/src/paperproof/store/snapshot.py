"""Graph snapshots (docs/07 §Snapshots).

A snapshot records {snapshot_id, files: {relpath: {sha256, rows}}, created_at}
over exactly graph/logic_nodes.jsonl, graph/logic_edges.jsonl,
graph/tombstones.jsonl. A snapshot is *current* iff recomputing those three
hashes matches.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from ..clock import now as clock_now
from ..ids import next_id
from ..paths import GRAPH_SNAPSHOT_FILES, Paths
from ..schemas.graph import Snapshot, SnapshotFile
from . import jsonl


def _hash_file(path: Path) -> tuple[str, int]:
    """Return (sha256_hex, row_count) for a JSONL file (empty file -> 0 rows)."""
    if not path.exists():
        data = b""
        rows = 0
    else:
        data = path.read_bytes()
        rows = sum(1 for line in data.splitlines() if line.strip())
    return hashlib.sha256(data).hexdigest(), rows


def compute_files(paths: Paths) -> dict[str, SnapshotFile]:
    files: dict[str, SnapshotFile] = {}
    for rel in GRAPH_SNAPSHOT_FILES:
        sha, rows = _hash_file(paths.resolve(rel))
        files[rel] = SnapshotFile(sha256=sha, rows=rows)
    return files


def take_snapshot(paths: Paths, snapshot_id: str | None = None) -> Snapshot:
    """Compute + append a snapshot over the three graph files. Returns the record."""
    existing = [r["snapshot_id"] for r in jsonl.read_all(paths.snapshots)]
    sid = snapshot_id or next_id("GS", existing)
    record = Snapshot(snapshot_id=sid, files=compute_files(paths), created_at=clock_now())
    jsonl.append(paths.snapshots, record)
    return record


def _load_snapshot(paths: Paths, snapshot_id: str) -> dict[str, Any] | None:
    latest = jsonl.latest_by_id(paths.snapshots, "snapshot_id")
    return latest.get(snapshot_id)


def latest_snapshot_id(paths: Paths) -> str | None:
    records = jsonl.read_all(paths.snapshots)
    return records[-1]["snapshot_id"] if records else None


def verify_snapshot(paths: Paths, snapshot_id: str) -> bool:
    """True iff recomputing the three graph-file hashes matches the record."""
    record = _load_snapshot(paths, snapshot_id)
    if record is None:
        return False
    current = compute_files(paths)
    recorded = record.get("files", {})
    if set(recorded.keys()) != {f for f in GRAPH_SNAPSHOT_FILES}:
        return False
    for rel, cur in current.items():
        rec = recorded.get(rel)
        if rec is None:
            return False
        if rec.get("sha256") != cur.sha256 or rec.get("rows") != cur.rows:
            return False
    return True


def is_current(paths: Paths, snapshot_id: str) -> bool:
    """Alias: a snapshot is current iff its recomputed hashes still match."""
    return verify_snapshot(paths, snapshot_id)
