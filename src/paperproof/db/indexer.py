"""DuckDB indexer: `db rebuild` / `db check` (docs/07 §Derived DB).

One table per canonical JSONL file. Each table carries ``id``, ``seq`` (line
number, 1-based), ``json`` (the full canonical record text), plus the extracted
hot columns docs/07 names (``state``/``status``/``strength``/``queue_name``/
``kind`` — populated where applicable, NULL otherwise). ``*_current`` views expose
the latest record per id (highest seq); the base tables keep full history.

Canonical rule: JSONL is the source of truth; the index is derived. `db rebuild`
reads every source through the loader (``jsonl.read_all``), so a corrupt line
raises ``CorruptStateError`` (exit 3, naming file+line) — the index refuses to
build over corrupt state. `db check` recomputes source hashes and compares them
to ``index_manifest.json`` to report ``stale_index``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Optional

import duckdb

from .. import clock
from ..paths import Paths
from ..serialize import canonical_line
from ..store import jsonl

# (relpath, table_name, id_field) — the closed set of canonical JSONL sources
# (docs/07 §Derived DB), in a fixed order so rebuilds are deterministic.
TABLE_MAP: tuple[tuple[str, str, str], ...] = (
    ("graph/logic_nodes.jsonl", "nodes", "node_id"),
    ("graph/logic_edges.jsonl", "edges", "edge_id"),
    ("graph/tombstones.jsonl", "tombstones", "tombstone_id"),
    ("graph/snapshots.jsonl", "snapshots", "snapshot_id"),
    ("proof/proof_results.jsonl", "verdict_records", "proof_result_id"),
    ("docs/documents.jsonl", "documents", "doc_id"),
    ("docs/evidence_units.jsonl", "evidence_units", "evidence_id"),
    ("docs/docs_requests.jsonl", "docs_requests", "request_id"),
    ("queue/work_items.jsonl", "work_items", "work_item_id"),
    ("queue/events.jsonl", "queue_events", "event_id"),
    ("commit/commit_decisions.jsonl", "commit_decisions", "commit_id"),
    ("freeze/frozen_items.jsonl", "freeze_items", "freeze_id"),
    ("compiler/dry_runs.jsonl", "dry_runs", "run_id"),
    ("compiler/draft_maps.jsonl", "draft_maps", "draft_map_id"),
    ("audit/audit_reports.jsonl", "audit_reports", "audit_id"),
)

DB_FILE = "db/index.duckdb"
MANIFEST_FILE = "db/index_manifest.json"

_HOT_COLUMNS = ("state", "status", "strength", "queue_name", "kind")

# Which record field supplies the ``kind`` hot column, per table.
_KIND_FIELD: dict[str, str] = {
    "nodes": "node_type",
    "edges": "edge_type",
    "tombstones": "reason",
    "documents": "source_type",
    "evidence_units": "kind",
    "queue_events": "op",
    "commit_decisions": "kind",
    "freeze_items": "freeze_type",
    "work_items": "target_type",
    "verdict_records": "target_type",
}


def _hot_columns(table: str, rec: dict[str, Any]) -> dict[str, Optional[str]]:
    """Extract the five hot columns from one record (docs/07)."""
    state = rec.get("lifecycle_state")

    strength = rec.get("strength")
    if strength is None and table == "verdict_records":
        strength = (rec.get("computed_verdict") or {}).get("strength")

    queue_name = rec.get("queue_name")

    status: Optional[str] = rec.get("status")
    if status is None:
        if table == "queue_events":
            status = rec.get("to_status")
        elif table == "verdict_records":
            status = (rec.get("computed_verdict") or {}).get("verdict")
        elif table == "freeze_items":
            status = rec.get("action")
        elif table == "dry_runs":
            wr = rec.get("writing_ready")
            status = None if wr is None else ("ready" if wr else "not_ready")
        elif table == "audit_reports":
            passed = rec.get("passed")
            status = None if passed is None else ("passed" if passed else "failed")

    kind_field = _KIND_FIELD.get(table)
    kind = rec.get(kind_field) if kind_field else None

    def _s(v: Any) -> Optional[str]:
        return None if v is None else str(v)

    return {
        "state": _s(state),
        "status": _s(status),
        "strength": _s(strength),
        "queue_name": _s(queue_name),
        "kind": _s(kind),
    }


def _sha256(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_hashes(paths: Paths) -> dict[str, str]:
    out: dict[str, str] = {}
    for relpath, _table, _idf in TABLE_MAP:
        digest = _sha256(paths.resolve(relpath))
        # init creates every canonical file empty, so a live project always has
        # them; a missing file hashes to the empty-bytes digest so `check` still
        # produces a stable, comparable map.
        out[relpath] = digest if digest is not None else hashlib.sha256(b"").hexdigest()
    return out


# ---------------------------------------------------------------------------
# rebuild
# ---------------------------------------------------------------------------


def rebuild(paths: Paths) -> dict[str, Any]:
    """Drop + recreate every table from the canonical JSONL; write the manifest.

    Reads every source through the loader first (so a corrupt line aborts the
    whole rebuild with exit 3, before the index file is touched). Idempotent:
    two rebuilds over identical sources produce identical table contents and an
    identical ``sources`` hash map.
    """
    if not paths.project_dir.exists():
        from ..errors import DomainError

        raise DomainError([f"project not found: {paths.project_id}"])

    # 1. Read + parse everything up front (raises CorruptStateError -> exit 3).
    loaded: dict[str, list[dict[str, Any]]] = {}
    for relpath, table, _idf in TABLE_MAP:
        loaded[table] = jsonl.read_all(paths.resolve(relpath))

    # 2. Recreate the index file from scratch (drop = delete the file).
    db_path = paths.resolve(DB_FILE)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("", ".wal"):
        p = Path(str(db_path) + suffix)
        if p.exists():
            p.unlink()

    table_counts: dict[str, int] = {}
    con = duckdb.connect(str(db_path))
    try:
        for relpath, table, id_field in TABLE_MAP:
            records = loaded[table]
            con.execute(
                f"CREATE TABLE {table} ("
                "id VARCHAR, seq BIGINT, json VARCHAR, "
                "state VARCHAR, status VARCHAR, strength VARCHAR, "
                "queue_name VARCHAR, kind VARCHAR)"
            )
            rows = []
            for seq, rec in enumerate(records, start=1):
                hot = _hot_columns(table, rec)
                rows.append(
                    [
                        rec.get(id_field),
                        seq,
                        canonical_line(rec),
                        hot["state"],
                        hot["status"],
                        hot["strength"],
                        hot["queue_name"],
                        hot["kind"],
                    ]
                )
            if rows:
                con.executemany(
                    f"INSERT INTO {table} VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows
                )
            # *_current view: the latest record per id (highest seq wins).
            con.execute(
                f"CREATE VIEW {table}_current AS SELECT * FROM {table} t "
                f"WHERE seq = (SELECT MAX(seq) FROM {table} t2 WHERE t2.id = t.id)"
            )
            table_counts[table] = len(rows)
    finally:
        con.close()

    # 3. Manifest: built_at (injectable clock) + per-source hashes.
    sources = _source_hashes(paths)
    manifest = {"built_at": clock.now(), "sources": sources}
    jsonl.write_json(paths.resolve(MANIFEST_FILE), manifest)

    return {
        "built_at": manifest["built_at"],
        "sources": sources,
        "tables": table_counts,
        "db_path": DB_FILE,
    }


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------


def check(paths: Paths) -> dict[str, Any]:
    """Recompute source hashes and compare to the manifest -> {stale_index}.

    Stale if the manifest is missing, the db file is missing, any source changed,
    or a source is missing from the manifest.
    """
    manifest_path = paths.resolve(MANIFEST_FILE)
    db_path = paths.resolve(DB_FILE)
    current = _source_hashes(paths)

    if not manifest_path.exists() or not db_path.exists():
        return {
            "stale_index": True,
            "built_at": None,
            "manifest_present": manifest_path.exists() and db_path.exists(),
            "changed_sources": sorted(current.keys()),
        }

    manifest = jsonl.read_json(manifest_path)
    recorded = manifest.get("sources", {})
    changed: list[str] = []
    for relpath, digest in current.items():
        if recorded.get(relpath) != digest:
            changed.append(relpath)
    # A source recorded in the manifest but no longer known is also drift.
    for relpath in recorded:
        if relpath not in current:
            changed.append(relpath)

    return {
        "stale_index": bool(changed),
        "built_at": manifest.get("built_at"),
        "manifest_present": True,
        "changed_sources": sorted(set(changed)),
    }


# ---------------------------------------------------------------------------
# read side
# ---------------------------------------------------------------------------


class IndexReader:
    """Read-only accessor over the derived DuckDB index.

    Every WebUI read goes through this (never live JSONL) so the stale-index
    banner is meaningful: after a rebuild, a JSONL mutation leaves the reader
    serving the indexed value until the next rebuild.
    """

    def __init__(self, db_path: str | Path) -> None:
        self._con = duckdb.connect(str(db_path), read_only=True)

    def close(self) -> None:
        self._con.close()

    def __enter__(self) -> "IndexReader":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def current(self, table: str) -> list[dict[str, Any]]:
        rows = self._con.execute(
            f"SELECT json FROM {table}_current ORDER BY seq"
        ).fetchall()
        return [json.loads(r[0]) for r in rows]

    def history(self, table: str) -> list[dict[str, Any]]:
        rows = self._con.execute(f"SELECT json FROM {table} ORDER BY seq").fetchall()
        return [json.loads(r[0]) for r in rows]

    def history_for_id(self, table: str, rid: str) -> list[dict[str, Any]]:
        rows = self._con.execute(
            f"SELECT json FROM {table} WHERE id = ? ORDER BY seq", [rid]
        ).fetchall()
        return [json.loads(r[0]) for r in rows]
