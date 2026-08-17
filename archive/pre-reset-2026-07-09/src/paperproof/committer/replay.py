"""CommitDecision replay helper (V-COMMIT-04, docs/08 §2b).

Replaying a CommitDecision's actions against the pre-snapshot must reproduce the
post-snapshot exactly. Because graph JSONL is append-only, the pre/post states are
the latest-by-id over the first ``rows`` lines recorded in each snapshot.

The reconstruction uses the actions' ``record`` payloads ONLY — it never reads the
appended lines. Each graph-mutating action (append_node/update_node/append_edge/
update_edge/tombstone/set_frozen) carries ``record`` = the exact graph record it
appended; the replay applies those records onto the pre-state and compares the
result to the ACTUAL post-state. So a CommitDecision whose actions do not
faithfully manifest the commit (a corrupted id, a mutated field, a dropped or
extra action) fails the check — the audit trail is genuinely replayable, not
tautologically true. Built as a test utility from day one (docs/10 §7).
"""

from __future__ import annotations

from typing import Any

from ..paths import Paths
from ..store import jsonl

_GRAPH_FILES = {
    "graph/logic_nodes.jsonl": "node_id",
    "graph/logic_edges.jsonl": "edge_id",
    "graph/tombstones.jsonl": "tombstone_id",
}
_GRAPH_ACTIONS = {"append_node", "update_node", "append_edge", "update_edge", "tombstone", "set_frozen"}


def _snapshot_rows(paths: Paths, snapshot_id: str) -> dict[str, int]:
    for r in jsonl.read_all(paths.snapshots):
        if r["snapshot_id"] == snapshot_id:
            return {rel: meta["rows"] for rel, meta in r["files"].items()}
    raise AssertionError(f"snapshot not found: {snapshot_id}")


def _latest_by_id(records: list[dict[str, Any]], id_field: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for rec in records:
        out[rec[id_field]] = rec
    return out


def _file_for(record: dict[str, Any]) -> str | None:
    if "node_id" in record:
        return "graph/logic_nodes.jsonl"
    if "edge_id" in record:
        return "graph/logic_edges.jsonl"
    if "tombstone_id" in record:
        return "graph/tombstones.jsonl"
    return None


def replay_reproduces(paths: Paths, commit_id: str) -> bool:
    """True iff replaying the commit's graph-action ``record`` payloads onto the
    pre-snapshot reproduces the actual post-snapshot state, AND every graph append
    is accounted for by exactly one action (no dropped/extra actions)."""
    cd = None
    for r in jsonl.read_all(paths.resolve("commit/commit_decisions.jsonl")):
        if r["commit_id"] == commit_id:
            cd = r
    if cd is None:
        raise AssertionError(f"commit not found: {commit_id}")

    pre_rows = _snapshot_rows(paths, cd["based_on_snapshot"])
    post_rows = _snapshot_rows(paths, cd["post_snapshot"])

    # Group each graph action's record by the file it belongs to (derived from the
    # record itself, not from the appended lines). A missing/null record on a
    # graph action => not replayable.
    by_file: dict[str, list[dict[str, Any]]] = {rel: [] for rel in _GRAPH_FILES}
    for a in cd["actions"]:
        if a["action"] not in _GRAPH_ACTIONS:
            continue
        rec = a.get("record")
        if not isinstance(rec, dict):
            return False
        rel = _file_for(rec)
        if rel is None:
            return False
        by_file[rel].append(rec)

    for rel, id_field in _GRAPH_FILES.items():
        lines = jsonl.read_all(paths.resolve(rel))
        pre_n = pre_rows.get(rel, 0)
        post_n = post_rows.get(rel, 0)
        pre_state = _latest_by_id(lines[:pre_n], id_field)
        actual_post = _latest_by_id(lines[:post_n], id_field)

        # the number of graph actions for this file must equal the appended-line
        # count (a dropped or extra action fails here)
        if len(by_file[rel]) != (post_n - pre_n):
            return False

        # reconstruct post from pre + the action records ALONE
        reconstructed = dict(pre_state)
        for rec in by_file[rel]:
            if id_field not in rec:
                return False
            reconstructed[rec[id_field]] = rec
        if reconstructed != actual_post:
            return False

    return True
