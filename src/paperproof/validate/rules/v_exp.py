"""V-EXP: expansion proposal validation (docs/09, docs/08 B3).

V-EXP-01  lane's previous layer fully committed (no open proof item on the frontier)
V-EXP-02  based_on_snapshot current (whole graph)
V-EXP-03  <=12 nodes; layer = lane frontier + 1 (first layer 0 for BFS-MAIN, else 1);
          an empty proposal is the legal lane-closing form
V-EXP-04  edge refs resolve (existing id or #index within the proposal)
V-EXP-05  every proposed node passes V-NODE-02/03 statically
V-EXP-06  first BFS-MAIN proposal is layer 0: exactly one question, one thesis, a
          thesis->question supports edge; no other proposal has question/thesis nodes
V-EXP-07  a lane's first proposal requires all its depends_on lanes complete
"""

from __future__ import annotations

from typing import Any

from ...graph import model as graph_model
from ...paths import Paths
from ...store import jsonl, snapshot
from ..envelope import Failure
from . import v_node_edge

MAIN = "BFS-MAIN"
_OPEN = lambda s: s not in ("committed", "cancelled")  # noqa: E731
COMMITS = "commit/commit_decisions.jsonl"


def _lane_nodes(gv: graph_model.GraphView, bfs_id: str) -> list[dict[str, Any]]:
    return [n for n in gv.nodes if n["bfs_id"] == bfs_id and n["lifecycle_state"] != "rejected"]


def _lane_max_layer(gv: graph_model.GraphView, bfs_id: str) -> int | None:
    layers = [n["layer"] for n in _lane_nodes(gv, bfs_id)]
    return max(layers) if layers else None


def _first_layer(bfs_id: str) -> int:
    return 0 if bfs_id == MAIN else 1


def _lane_record_ids(gv: graph_model.GraphView, bfs_id: str) -> set[str]:
    ids = {n["node_id"] for n in gv.nodes if n["bfs_id"] == bfs_id}
    lane_nodes = {n["node_id"] for n in gv.nodes if n["bfs_id"] == bfs_id}
    ids |= {e["edge_id"] for e in gv.edges if e["source_node_id"] in lane_nodes}
    return ids


def _open_items_for(paths: Paths, ids: set[str]) -> bool:
    from ...queue import engine

    for item in engine.load_items(paths):
        if item["target_id"] in ids and _OPEN(item["status"]):
            return True
    return False


def lane_complete(paths: Paths, gv: graph_model.GraphView, bfs_id: str) -> bool:
    """A lane is complete when a closing (empty) proposal has committed AND no
    open work item targets any of its records (docs/02)."""
    closing = False
    for cd in jsonl.read_all(paths.resolve(COMMITS)):
        if cd.get("kind") != "expansion":
            continue
        ref = cd.get("input_ref", "")
        if ref.startswith(f"EXP-{bfs_id}-") and not any(
            a["action"] in ("append_node", "append_edge") for a in cd.get("actions", [])
        ):
            closing = True
    if not closing:
        return False
    return not _open_items_for(paths, _lane_record_ids(gv, bfs_id))


def check(paths: Paths, proposal: dict[str, Any]) -> list[Failure]:
    failures: list[Failure] = []
    gv = graph_model.load(paths)
    bfs_id = proposal["bfs_id"]
    layer = proposal["layer"]
    nodes = proposal.get("nodes", [])
    edges = proposal.get("edges", [])
    is_empty = not nodes and not edges
    lane_has_nodes = bool(_lane_nodes(gv, bfs_id))
    is_first = not lane_has_nodes

    # V-EXP-03: node cap + layer correctness.
    if len(nodes) > 12:
        failures.append(Failure("V-EXP-03", f"{len(nodes)} nodes > 12"))
    max_layer = _lane_max_layer(gv, bfs_id)
    expected_layer = _first_layer(bfs_id) if max_layer is None else max_layer + 1
    if layer != expected_layer:
        failures.append(Failure("V-EXP-03", f"layer {layer} != expected {expected_layer}"))

    # V-EXP-01: previous layer fully committed (skip for the lane's first layer).
    if not is_first:
        frontier_ids = {
            n["node_id"] for n in gv.nodes if n["bfs_id"] == bfs_id and n["layer"] == layer - 1
        }
        lane_nodes = {n["node_id"] for n in gv.nodes if n["bfs_id"] == bfs_id and n["layer"] == layer - 1}
        frontier_ids |= {e["edge_id"] for e in gv.edges if e["source_node_id"] in lane_nodes}
        if _open_items_for(paths, frontier_ids):
            failures.append(Failure("V-EXP-01", f"open proof items on {bfs_id} layer {layer - 1}"))

    # V-EXP-02: snapshot current (whole graph).
    based_on = proposal.get("based_on_snapshot")
    if not based_on or not snapshot.is_current(paths, based_on):
        failures.append(Failure("V-EXP-02", f"based_on_snapshot not current: {based_on}"))

    # V-EXP-04: edge refs resolve.
    n_nodes = len(nodes)
    for e in edges:
        for ref_key in ("source_ref", "target_ref"):
            ref = e[ref_key]
            if ref.startswith("#"):
                try:
                    idx = int(ref[1:])
                except ValueError:
                    failures.append(Failure("V-EXP-04", f"bad ref {ref}"))
                    continue
                if not (0 <= idx < n_nodes):
                    failures.append(Failure("V-EXP-04", f"ref {ref} out of range"))
            elif gv.record(ref) is None:
                failures.append(Failure("V-EXP-04", f"ref {ref} does not resolve"))

    # V-EXP-05: proposed nodes pass V-NODE-02/03.
    contract = jsonl.read_json(paths.project_contract) if paths.project_contract.exists() else {}
    contract_scope = contract.get("scope", {}) or {}
    for i, node in enumerate(nodes):
        ok, detail = v_node_edge.node02_ok(node["claim"])
        if not ok:
            failures.append(Failure("V-EXP-05", f"node[{i}] V-NODE-02: {detail}"))
        ok, detail = v_node_edge.node03_ok(node.get("scope", {}) or {}, contract_scope)
        if not ok:
            failures.append(Failure("V-EXP-05", f"node[{i}] V-NODE-03: {detail}"))

    # V-EXP-06: layer-0 question/thesis rule; and no q/t outside layer 0.
    node_types = [n["node_type"] for n in nodes]
    is_layer0_main = bfs_id == MAIN and layer == 0
    if is_layer0_main:
        if node_types.count("question") != 1 or node_types.count("thesis") != 1:
            failures.append(Failure("V-EXP-06", "layer-0 needs exactly one question and one thesis"))
        else:
            q_idx = node_types.index("question")
            t_idx = node_types.index("thesis")
            has_tq = any(
                e["edge_type"] == "supports"
                and e["source_ref"] == f"#{t_idx}"
                and e["target_ref"] == f"#{q_idx}"
                for e in edges
            )
            if not has_tq:
                failures.append(Failure("V-EXP-06", "layer-0 missing thesis->question supports edge"))
    else:
        if "question" in node_types or "thesis" in node_types:
            failures.append(Failure("V-EXP-06", "question/thesis nodes only allowed in layer-0 BFS-MAIN"))

    # V-EXP-07: first proposal requires depends_on lanes complete.
    if is_first and not is_empty:
        spec = jsonl.read_json(paths.paper_spec) if paths.paper_spec.exists() else {}
        deps = []
        for entry in spec.get("bfs_plan", []):
            if entry.get("bfs_id") == bfs_id:
                deps = entry.get("depends_on", []) or []
        for dep in deps:
            if not lane_complete(paths, gv, dep):
                failures.append(Failure("V-EXP-07", f"depends_on lane not complete: {dep}"))

    return failures
