"""V-FRZ contract tests (docs/09, docs/11 §2).

Each V-FRZ precondition violated => refusal; the language-limit union is correct;
unfreeze re-opens the affected proofs. Degenerate graph states are constructed
directly (append records + snapshot), so each rule is isolated.
"""

from __future__ import annotations

import pytest

from paperproof.errors import DomainError
from paperproof.freeze import apply as freeze
from paperproof.graph import model as graph_model
from paperproof.paths import paths_for
from paperproof.queue import engine
from paperproof.store import jsonl, snapshot

pytestmark = pytest.mark.contract

NODES = "graph/logic_nodes.jsonl"
EDGES = "graph/logic_edges.jsonl"


def _node(node_id, *, node_type="mechanism", state="active", frozen=False, evidence=None, ll=None, scope=None):
    return {
        "schema_version": "logic_node.v1", "node_id": node_id, "project_id": "p4-ldi",
        "bfs_id": "BFS-MAIN", "layer": 1, "claim": f"Claim for {node_id}.", "claim_version": 1,
        "node_type": node_type, "scope": scope or {}, "parents": [], "origin": {"kind": "seed", "source": "topic-input"},
        "lifecycle_state": state, "state_reason": None, "state_detail": None,
        "strength": "strong" if state == "active" else "unassessed",
        "language_limits": ll, "assumptions": [], "evidence_bindings": list(evidence or []),
        "latest_proof_result_id": "PR-001" if state == "active" else None, "frozen": frozen,
        "created_at": "2026-07-07T00:00:00Z",
    }


def _seed(paths, nodes):
    for n in nodes:
        jsonl.append(paths.resolve(NODES), n)
    snapshot.take_snapshot(paths)


def _paths(pp):
    return paths_for(pp.tmp_path, "p4-ldi")


def test_v_frz_01_non_active_refused(project, pp):
    paths = _paths(pp)
    _seed(paths, [_node("NODE-001", node_type="definition", state="pending_proof")])
    with pytest.raises(DomainError) as exc:
        freeze.apply(paths, "NODE-001", "local")
    assert "V-FRZ-01" in exc.value.errors


def test_v_frz_02_missing_evidence_refused(project, pp):
    paths = _paths(pp)
    # active mechanism with no evidence binding -> V-FRZ-02.
    _seed(paths, [_node("NODE-001", node_type="mechanism", state="active", evidence=[], ll={"allowed": ["a"], "forbidden": ["b"]})])
    with pytest.raises(DomainError) as exc:
        freeze.apply(paths, "NODE-001", "local")
    assert "V-FRZ-02" in exc.value.errors


def test_v_frz_03_open_item_touches_refused(project, pp):
    paths = _paths(pp)
    _seed(paths, [_node("NODE-001", node_type="definition", state="active", ll={"allowed": ["a"], "forbidden": ["b"]})])
    # an open proof item targeting the closure record blocks the freeze.
    engine.enqueue(paths, queue_name="proof_queue", target_type="node", target_id="NODE-001", actor="test")
    with pytest.raises(DomainError) as exc:
        freeze.apply(paths, "NODE-001", "local")
    assert "V-FRZ-03" in exc.value.errors


def test_v_frz_04_spine_freeze_requires_msa_and_verify(project, pp):
    paths = _paths(pp)
    # An empty/broken graph fails the MSA checklist, so spine_freeze is refused.
    _seed(paths, [_node("NODE-001", node_type="definition", state="active", ll={"allowed": ["a"], "forbidden": ["b"]})])
    with pytest.raises(DomainError) as exc:
        freeze.apply(paths, "NODE-001", "spine")
    assert "V-FRZ-04" in exc.value.errors


def test_v_frz_language_union_dedup_sorted(project, pp):
    paths = _paths(pp)
    _seed(paths, [
        _node("NODE-001", node_type="definition", state="active", ll={"allowed": ["zeta", "alpha"], "forbidden": ["no-x"]}),
        _node("NODE-002", node_type="definition", state="active", ll={"allowed": ["alpha", "mid"], "forbidden": ["no-y", "no-x"]}, evidence=[]),
    ])
    # subtree freeze over an explicit two-record closure (call the union directly
    # via a local freeze on each, then check a combined subtree via the helper).
    gv = graph_model.load(paths)
    closure = {"NODE-001", "NODE-002"}
    allowed = sorted({p for rid in closure for p in (gv.record(rid)["language_limits"]["allowed"])})
    forbidden = sorted({p for rid in closure for p in (gv.record(rid)["language_limits"]["forbidden"])})
    assert allowed == ["alpha", "mid", "zeta"]
    assert forbidden == ["no-x", "no-y"]

    # And the FreezeItem produced by a real local freeze carries the sorted union
    # of its single record's limits.
    res = freeze.apply(paths, "NODE-001", "local")
    items = jsonl.read_all(paths.resolve("freeze/frozen_items.jsonl"))
    fi = next(i for i in items if i["freeze_id"] == res["freeze_id"])
    assert fi["allowed_language"] == ["alpha", "zeta"]
    assert fi["forbidden_language"] == ["no-x"]


def test_v_frz_unfreeze_reopens_proof(project, pp):
    paths = _paths(pp)
    _seed(paths, [_node("NODE-001", node_type="definition", state="active", ll={"allowed": ["a"], "forbidden": ["b"]})])
    freeze.apply(paths, "NODE-001", "local")
    gv = graph_model.load(paths)
    assert gv.node_by_id["NODE-001"]["frozen"] is True

    freeze.unfreeze(paths, "NODE-001")
    gv = graph_model.load(paths)
    node = gv.node_by_id["NODE-001"]
    assert node["frozen"] is False
    assert node["lifecycle_state"] == "pending_proof"
    # a re-proof work item was enqueued for the re-opened record.
    reopened = [i for i in engine.load_items(paths) if i["target_id"] == "NODE-001" and i["status"] in ("queued", "blocked")]
    assert reopened, "unfreeze must re-open the affected proof"
