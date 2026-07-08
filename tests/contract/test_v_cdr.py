"""V-CDR contract tests (docs/09, docs/11 §2).

Gap detection is exercised PER kind on degenerate fixture states constructed
directly (a clean freeze yields zero gaps by construction — docs/06 reachability
note). Plus V-CDR-01 idempotency + auto-cancel and V-CDR-03 (the section plan
covers every spine node exactly once).
"""

from __future__ import annotations

import pytest

from paperproof.compiler import dry_run as dry
from paperproof.compiler import section_plan as sp
from paperproof.graph import model as graph_model
from paperproof.paths import paths_for
from paperproof.queue import engine
from paperproof.store import jsonl, snapshot

pytestmark = pytest.mark.contract

NODES = "graph/logic_nodes.jsonl"


def _node(node_id, *, node_type="definition", state="active", layer=1, evidence=None, scope=None, ll=None):
    return {
        "schema_version": "logic_node.v1", "node_id": node_id, "project_id": "p4-ldi",
        "bfs_id": "BFS-MAIN", "layer": layer, "claim": f"Claim for {node_id}.", "claim_version": 1,
        "node_type": node_type, "scope": scope or {}, "parents": [], "origin": {"kind": "seed", "source": "topic-input"},
        "lifecycle_state": state, "state_reason": None, "state_detail": None,
        "strength": "strong" if state == "active" else "unassessed",
        "language_limits": ll, "assumptions": [], "evidence_bindings": list(evidence or []),
        "latest_proof_result_id": None, "frozen": False, "created_at": "2026-07-07T00:00:00Z",
    }


def _edge(edge_id, src, tgt, *, strength="strong", ll=None):
    return {
        "schema_version": "logic_edge.v1", "edge_id": edge_id, "project_id": "p4-ldi",
        "source_node_id": src, "target_node_id": tgt, "edge_type": "supports",
        "edge_claim": f"{src} supports {tgt}.", "claim_version": 1, "lifecycle_state": "active",
        "state_reason": None, "state_detail": None, "strength": strength, "language_limits": ll,
        "assumptions": [], "frozen": False, "latest_proof_result_id": None, "created_at": "2026-07-07T00:00:00Z",
    }


def _gv(nodes, edges):
    return graph_model.GraphView(nodes, edges)


def _paths(pp):
    return paths_for(pp.tmp_path, "p4-ldi")


INTRO_PLAN = [{"section_id": "SEC-introduction", "role": "introduction", "nodes": ["NODE-Q"]}]


# --- gap detection per kind -------------------------------------------------


def test_gap_missing_evidence(project, pp):
    paths = _paths(pp)
    gv = _gv([_node("NODE-001", node_type="mechanism", evidence=[])], [])
    gaps = dry.detect_gaps(paths, gv, {"NODE-001"}, INTRO_PLAN)
    # S4 (docs/17): the spine mechanism has zero bindings, so it is below the
    # role-profile floor -> a missing_evidence gap (note reflects the new floor).
    assert {"kind": "missing_evidence", "target_id": "NODE-001", "note": "spine claim below the role-profile floor"} in gaps


def test_gap_unhandled_alternative(project, pp):
    paths = _paths(pp)
    gv = _gv([_node("NODE-009", node_type="alternative", state="active")], [])
    gaps = dry.detect_gaps(paths, gv, set(), INTRO_PLAN)
    assert any(g["kind"] == "unhandled_alternative" and g["target_id"] == "NODE-009" for g in gaps)


def test_gap_weak_spine_edge(project, pp):
    paths = _paths(pp)
    gv = _gv([], [_edge("EDGE-001-002", "NODE-001", "NODE-002", strength="conditional", ll=None)])
    gaps = dry.detect_gaps(paths, gv, {"EDGE-001-002"}, INTRO_PLAN)
    assert any(g["kind"] == "weak_spine_edge" and g["target_id"] == "EDGE-001-002" for g in gaps)


def test_gap_missing_section_claim(project, pp):
    paths = _paths(pp)
    gv = _gv([], [])
    gaps = dry.detect_gaps(paths, gv, set(), [])  # no SEC-introduction in the plan
    assert any(g["kind"] == "missing_section_claim" and g["target_id"] == "SEC-introduction" for g in gaps)


def test_gap_contract_violation(project, pp):
    paths = _paths(pp)
    # a spine definition node whose region scope is incompatible with the contract.
    gv = _gv([_node("NODE-001", node_type="definition", scope={"region": "Mars"})], [])
    gaps = dry.detect_gaps(paths, gv, {"NODE-001"}, INTRO_PLAN)
    assert any(g["kind"] == "contract_violation" and g["target_id"] == "NODE-001" for g in gaps)


# --- V-CDR-01 idempotency + auto-cancel -------------------------------------


def _gap_items(paths):
    return [
        i for i in engine.load_items(paths)
        if i["queue_name"] == "compile_queue" and (i.get("task_id") or "").startswith("GAP:")
        and i["status"] not in ("committed", "cancelled")
    ]


def test_v_cdr_01_idempotent_and_auto_cancel(project, pp):
    paths = _paths(pp)
    jsonl.append(paths.resolve(NODES), _node("NODE-009", node_type="alternative", state="active"))
    snapshot.take_snapshot(paths)

    # V-CDR-02: the dry run appends nothing to graph/ or docs/.
    before = {rel: paths.resolve(rel).read_bytes() for rel in ("graph/logic_nodes.jsonl", "graph/logic_edges.jsonl", "docs/documents.jsonl", "docs/evidence_units.jsonl")}

    dry.dry_run(paths)
    dry.dry_run(paths)  # re-run creates NO duplicate item (V-CDR-01)

    for rel, data in before.items():
        assert paths.resolve(rel).read_bytes() == data, f"dry run mutated {rel} (V-CDR-02)"

    items = _gap_items(paths)
    task_ids = [i["task_id"] for i in items]
    # each gap identity (kind, target) maps to exactly one open item (no dups).
    assert len(task_ids) == len(set(task_ids))
    assert "GAP:unhandled_alternative:NODE-009" in task_ids

    # resolve the gap: the alternative becomes rejected -> its item auto-cancels.
    rejected = _node("NODE-009", node_type="alternative", state="rejected")
    rejected["state_reason"] = "out_of_scope"
    jsonl.append(paths.resolve(NODES), rejected)
    snapshot.take_snapshot(paths)

    out = dry.dry_run(paths)
    assert not any(g["kind"] == "unhandled_alternative" for g in out["gaps"])
    open_task_ids = [i["task_id"] for i in _gap_items(paths)]
    assert "GAP:unhandled_alternative:NODE-009" not in open_task_ids
    # the resolved item was cancelled.
    cancelled = [
        i for i in engine.load_items(paths)
        if i["status"] == "cancelled" and i.get("task_id") == "GAP:unhandled_alternative:NODE-009"
    ]
    assert cancelled


# --- V-CDR-03 section plan coverage -----------------------------------------


def test_v_cdr_03_section_plan_covers_every_spine_node_once(project, pp):
    nodes = [
        _node("NODE-001", node_type="question", layer=0),
        _node("NODE-002", node_type="thesis", layer=0),
        _node("NODE-003", node_type="mechanism", layer=0, evidence=["EU-001"]),
        _node("NODE-004", node_type="definition", layer=1),
    ]
    gv = _gv(nodes, [])
    spine = {"NODE-001", "NODE-002", "NODE-003", "NODE-004"}
    plan = sp.build(gv, spine)
    covered = [nid for entry in plan for nid in entry["nodes"]]
    assert sorted(covered) == sorted(spine)
    assert len(covered) == len(set(covered))  # exactly once
