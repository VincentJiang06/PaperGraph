"""graph CLI command bodies (docs/10 §4): list-nodes/list-edges, show,
msa-check, park/unpark. Park/unpark are administrative commits via the Committer.
"""

from __future__ import annotations

from typing import Any, Optional

from ..committer import apply as committer
from ..errors import DomainError
from ..paths import Paths
from ..store import jsonl
from . import model as graph_model


def _lane_layer_of_edge(gv: graph_model.GraphView, edge: dict[str, Any]) -> tuple[Optional[str], Optional[int]]:
    src = gv.node_by_id.get(edge["source_node_id"])
    if src is None:
        return None, None
    return src["bfs_id"], src["layer"]


def list_nodes(paths: Paths, state: str | None = None, lane: str | None = None, layer: int | None = None) -> dict[str, Any]:
    gv = graph_model.load(paths)
    out = []
    for n in gv.nodes:
        if state and n["lifecycle_state"] != state:
            continue
        if lane and n["bfs_id"] != lane:
            continue
        if layer is not None and n["layer"] != layer:
            continue
        out.append(n)
    return {"nodes": out, "count": len(out)}


def list_edges(paths: Paths, state: str | None = None, lane: str | None = None, layer: int | None = None) -> dict[str, Any]:
    gv = graph_model.load(paths)
    out = []
    for e in gv.edges:
        if state and e["lifecycle_state"] != state:
            continue
        e_lane, e_layer = _lane_layer_of_edge(gv, e)
        if lane and e_lane != lane:
            continue
        if layer is not None and e_layer != layer:
            continue
        out.append(e)
    return {"edges": out, "count": len(out)}


def show(paths: Paths, target_id: str) -> dict[str, Any]:
    gv = graph_model.load(paths)
    rec = gv.record(target_id)
    if rec is None:
        raise DomainError([f"record not found: {target_id}"])
    id_field = "node_id" if gv.kind(target_id) == "node" else "edge_id"
    src_file = "graph/logic_nodes.jsonl" if id_field == "node_id" else "graph/logic_edges.jsonl"
    history = [r for r in jsonl.read_all(paths.resolve(src_file)) if r.get(id_field) == target_id]
    verdicts = [
        r for r in jsonl.read_all(paths.resolve("proof/proof_results.jsonl")) if r.get("target_id") == target_id
    ]
    return {"record": rec, "history": history, "verdict_records": verdicts}


def park(paths: Paths, target_id: str, reason: str, into: str | None = None) -> dict[str, Any]:
    return committer.park(paths, target_id, reason, into)


def unpark(paths: Paths, target_id: str) -> dict[str, Any]:
    return committer.unpark(paths, target_id)


# --- MSA checklist (docs/02) ------------------------------------------------


def _touches_spine(gv: graph_model.GraphView, spine_ids: set[str], target_id: str) -> bool:
    if target_id in spine_ids:
        return True
    edge = gv.edge_by_id.get(target_id)
    if edge is not None:
        if edge["source_node_id"] in spine_ids or edge["target_node_id"] in spine_ids:
            return True
    node = gv.node_by_id.get(target_id)
    if node is not None:
        if any(p in spine_ids for p in node.get("parents", [])):
            return True
        for e in gv.edges:
            if e["edge_id"] in spine_ids and target_id in (e["source_node_id"], e["target_node_id"]):
                return True
    return False


def msa_check(paths: Paths) -> dict[str, Any]:
    from ..queue import engine
    from ..validate.rules import v_exp

    gv = graph_model.load(paths)
    spine_ids, _ = gv.spine()
    items = []

    q = gv.unique_node_of_type("question")
    t = gv.unique_node_of_type("thesis")
    msa1 = q is not None and t is not None and q["lifecycle_state"] == "active" and t["lifecycle_state"] == "active"
    items.append(("MSA-1", msa1, "exactly one active question and thesis"))

    msa2 = any(e["edge_id"] in spine_ids for e in gv.edges if q and t and e["source_node_id"] == t["node_id"] and e["target_node_id"] == q["node_id"] and e["edge_type"] == "supports")
    items.append(("MSA-2", bool(msa2), "supports edge thesis->question active"))

    spine_records = [gv.record(i) for i in spine_ids]
    msa3 = all(r is not None and r["lifecycle_state"] == "active" for r in spine_records) and bool(spine_ids)
    items.append(("MSA-3", msa3, "every spine record active"))

    msa4 = all(
        (n["node_type"] not in ("fact", "mechanism")) or len(n.get("evidence_bindings", [])) >= 1
        for n in gv.nodes
        if n["node_id"] in spine_ids
    )
    items.append(("MSA-4", msa4, "spine fact/mechanism nodes have >=1 evidence binding"))

    msa5 = all(
        n["lifecycle_state"] == "rejected"
        or (n["lifecycle_state"] == "parked" and n.get("state_reason") in ("absorbed", "not_needed"))
        for n in gv.nodes
        if n["node_type"] == "alternative"
    )
    items.append(("MSA-5", msa5, "every alternative rejected or parked"))

    open_touch = False
    for item in engine.load_items(paths):
        if item["status"] in ("committed", "cancelled"):
            continue
        if _touches_spine(gv, spine_ids, item["target_id"]):
            open_touch = True
            break
    items.append(("MSA-6", not open_touch, "no open work item touches the spine"))

    spec = jsonl.read_json(paths.paper_spec) if paths.paper_spec.exists() else {}
    lanes = [e["bfs_id"] for e in spec.get("bfs_plan", [])]
    msa7 = all(v_exp.lane_complete(paths, gv, lane) for lane in lanes) and bool(lanes)
    items.append(("MSA-7", msa7, "every bfs_plan lane complete"))

    dry_runs = jsonl.read_all(paths.resolve("compiler/dry_runs.jsonl"))
    if not dry_runs:
        msa8 = True  # informational before first dry run
    else:
        msa8 = not (dry_runs[-1].get("gaps") or [])
    items.append(("MSA-8", msa8, "latest dry run reports no blocking gaps"))

    msa9 = any(
        n["node_id"] in spine_ids and n["node_type"] in ("fact", "mechanism") and n["lifecycle_state"] == "active"
        for n in gv.nodes
    )
    items.append(("MSA-9", msa9, "spine contains >=1 active fact/mechanism node"))

    checklist = {rid: {"pass": bool(ok), "detail": detail} for rid, ok, detail in items}
    all_pass = all(v["pass"] for v in checklist.values())
    return {"msa": checklist, "all_pass": all_pass, "spine": sorted(spine_ids)}
