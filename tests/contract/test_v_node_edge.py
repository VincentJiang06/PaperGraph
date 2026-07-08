"""V-EDGE-02 contract tests (docs/09): edge_claim must not verbatim-restate an
endpoint claim. Wired into the commit-time graph check (V-COMMIT-05 path) and
verify via graph_record_checks. The bridge-synthesized edge_claim must PASS.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from paperproof.validate.rules import v_node_edge

pytestmark = pytest.mark.contract

VRULES = Path(__file__).resolve().parent.parent / "fixtures" / "vrules" / "V-EDGE-02"


def _run(fixture: dict) -> list[str]:
    failures = v_node_edge.graph_record_checks(fixture["nodes"], fixture["edges"])
    return [f.rule_id for f in failures]


@pytest.mark.parametrize("path", sorted(VRULES.glob("*.json")))
def test_v_edge_02_fixtures(path):
    fixture = json.loads(path.read_bytes())
    fired = _run(fixture)
    if path.name.startswith("fail_"):
        assert "V-EDGE-02" in fired, (path.name, fired)
    else:
        assert "V-EDGE-02" not in fired, (path.name, fired)


def test_bridge_synthesized_edge_claim_passes_v_edge_02():
    """The Committer's synthesized bridge edge_claim satisfies V-EDGE-02."""
    x_claim = "Solvency and liquidity risk are distinct categories."
    b_claim = "Leveraged LDI links gilt yields to collateral demand."
    edge_claim = f"Bridge premise supporting the inference: {x_claim}"
    ok, _ = v_node_edge.edge02_ok(edge_claim, x_claim, b_claim)
    assert ok


def test_edge_claim_equal_to_endpoint_fails_v_edge_02():
    ok, _ = v_node_edge.edge02_ok("Alpha claim.", "alpha claim.", "Beta.")
    assert not ok


# --- F14: direct exercises for the registered V-NODE/V-EDGE/V-GRAPH rules ----


def _n(nid, node_type="fact", state="active", parents=None, origin_kind="seed", frozen=False):
    return {"node_id": nid, "claim": f"Claim {nid}.", "node_type": node_type,
            "lifecycle_state": state, "strength": "strong" if state == "active" else "unassessed",
            "parents": list(parents or []), "origin": {"kind": origin_kind, "source": "x"},
            "frozen": frozen}


def _e(eid, src, tgt, etype="supports", state="active"):
    return {"edge_id": eid, "source_node_id": src, "target_node_id": tgt, "edge_type": etype,
            "edge_claim": f"{src} relates to {tgt}.", "lifecycle_state": state,
            "strength": "strong" if state == "active" else "unassessed", "frozen": False}


def test_v_node_04_dangling_parent_fires():
    nodes = [_n("NODE-001", "question"), _n("NODE-002", parents=["NODE-999"])]
    fired = _run({"nodes": nodes, "edges": []})
    assert "V-NODE-04" in fired
    ok = _run({"nodes": [_n("NODE-001", "question"), _n("NODE-002", parents=["NODE-001"])], "edges": []})
    assert "V-NODE-04" not in ok


def test_v_edge_04_refutes_must_target_alternative():
    nodes = [_n("NODE-001", "question"), _n("NODE-002", "fact", parents=["NODE-001"]),
             _n("NODE-003", "alternative", parents=["NODE-001"])]
    bad = _run({"nodes": nodes, "edges": [_e("EDGE-002-003-ref", "NODE-002", "NODE-002", "refutes")]})
    assert "V-EDGE-04" in bad
    good = _run({"nodes": nodes, "edges": [_e("EDGE-002-003-ref", "NODE-002", "NODE-003", "refutes")]})
    assert "V-EDGE-04" not in good


def test_v_graph_01_supports_cycle_fires():
    nodes = [_n("NODE-001", "question"), _n("NODE-002", parents=["NODE-001"]), _n("NODE-003", parents=["NODE-001"])]
    edges = [_e("EDGE-002-003", "NODE-002", "NODE-003"), _e("EDGE-003-002", "NODE-003", "NODE-002")]
    assert "V-GRAPH-01" in _run({"nodes": nodes, "edges": edges})


def test_v_graph_02_unreachable_node_fires():
    nodes = [_n("NODE-001", "question"), _n("NODE-002", origin_kind="expansion", parents=[])]
    assert "V-GRAPH-02" in _run({"nodes": nodes, "edges": []})


def test_v_graph_03_strength_and_frozen_consistency():
    bad_strength = _n("NODE-001", "question")
    bad_strength["strength"] = "unassessed"  # active but unassessed
    assert "V-GRAPH-03" in _run({"nodes": [bad_strength], "edges": []})
    frozen_pending = _n("NODE-001", "question", state="pending_proof", frozen=True)
    assert "V-GRAPH-03" in _run({"nodes": [frozen_pending], "edges": []})
