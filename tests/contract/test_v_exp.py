"""V-EXP contract tests (docs/09) — expansion proposals, incl. layer-0 and
closing proposals. One passing + >=1 failing proposal per V-EXP rule.
"""

from __future__ import annotations

import json

import pytest

from paperproof.expander import ingest as expander
from paperproof.store import snapshot

from tests.fakes import scenario

pytestmark = pytest.mark.contract


def _validate(paths, proposal) -> list[str]:
    pf = paths.resolve("agent_outputs/expansions/tmp.json")
    pf.parent.mkdir(parents=True, exist_ok=True)
    pf.write_text(json.dumps(proposal), encoding="utf-8")
    return expander.validate(paths, str(pf)).get("failed_rules", [])


def _layer0(paths, **over):
    snap = snapshot.latest_snapshot_id(paths)
    p = {
        "schema_version": "expansion_proposal.v1", "proposal_id": "EXP-BFS-MAIN-L0",
        "project_id": "p4-ldi", "bfs_id": "BFS-MAIN", "layer": 0, "based_on_snapshot": snap,
        "nodes": [
            {"claim": "The core research question?", "node_type": "question", "scope": {}, "parents": []},
            {"claim": "The intended thesis answer.", "node_type": "thesis", "scope": {}, "parents": []},
            {"claim": "A seed definition claim.", "node_type": "definition", "scope": {}, "parents": []},
        ],
        "edges": [{"source_ref": "#1", "target_ref": "#0", "edge_type": "supports", "edge_claim": "The thesis resolves the question."}],
    }
    p.update(over)
    return p


def test_valid_layer0_passes(project, pp):
    paths = scenario.paths_for_pp(pp)
    assert _validate(paths, _layer0(paths)) == []


def test_v_exp_02_stale_snapshot(project, pp):
    paths = scenario.paths_for_pp(pp)
    p = _layer0(paths, based_on_snapshot="GS-999999")
    assert "V-EXP-02" in _validate(paths, p)


def test_v_exp_03_too_many_nodes(project, pp):
    paths = scenario.paths_for_pp(pp)
    nodes = _layer0(paths)["nodes"]
    nodes += [{"claim": f"Extra definition {i}.", "node_type": "definition", "scope": {}, "parents": []} for i in range(12)]
    assert "V-EXP-03" in _validate(paths, _layer0(paths, nodes=nodes))


def test_v_exp_03_wrong_layer(project, pp):
    paths = scenario.paths_for_pp(pp)
    assert "V-EXP-03" in _validate(paths, _layer0(paths, layer=2))


def test_v_exp_04_bad_edge_ref(project, pp):
    paths = scenario.paths_for_pp(pp)
    p = _layer0(paths)
    p["edges"].append({"source_ref": "#9", "target_ref": "#0", "edge_type": "supports", "edge_claim": "Dangling ref."})
    assert "V-EXP-04" in _validate(paths, p)


def test_v_exp_05_compound_node(project, pp):
    paths = scenario.paths_for_pp(pp)
    p = _layer0(paths)
    p["nodes"][2]["claim"] = "First claim; and therefore a second which means a third."
    assert "V-EXP-05" in _validate(paths, p)


def test_v_exp_06_missing_thesis_question_edge(project, pp):
    paths = scenario.paths_for_pp(pp)
    p = _layer0(paths, edges=[])
    assert "V-EXP-06" in _validate(paths, p)


def test_v_exp_06_question_outside_layer0(project, pp):
    """After committing layer-0, a layer-1 proposal that includes a question node
    trips V-EXP-06 (also V-EXP-03 layer, but the named rule fires)."""
    paths = scenario.paths_for_pp(pp)
    scenario.seed_layer0(paths)
    snap = snapshot.latest_snapshot_id(paths)
    p = {
        "schema_version": "expansion_proposal.v1", "proposal_id": "EXP-BFS-MAIN-L1",
        "project_id": "p4-ldi", "bfs_id": "BFS-MAIN", "layer": 1, "based_on_snapshot": snap,
        "nodes": [{"claim": "An illegal second question?", "node_type": "question", "scope": {}, "parents": []}],
        "edges": [],
    }
    assert "V-EXP-06" in _validate(paths, p)


def test_v_exp_01_previous_layer_open(project, pp):
    """Layer-1 proposal while layer-0 proof items are still open -> V-EXP-01."""
    paths = scenario.paths_for_pp(pp)
    scenario.seed_layer0(paths)  # layer-0 committed but its checks are open
    snap = snapshot.latest_snapshot_id(paths)
    p = {
        "schema_version": "expansion_proposal.v1", "proposal_id": "EXP-BFS-MAIN-L1",
        "project_id": "p4-ldi", "bfs_id": "BFS-MAIN", "layer": 1, "based_on_snapshot": snap,
        "nodes": [{"claim": "A layer-1 mechanism claim.", "node_type": "definition", "scope": {}, "parents": ["NODE-003"]}],
        "edges": [],
    }
    assert "V-EXP-01" in _validate(paths, p)


def test_v_exp_07_dependent_lane_before_complete(project, pp):
    """BFS-ALT's first proposal before BFS-MAIN is complete -> V-EXP-07."""
    paths = scenario.paths_for_pp(pp)
    scenario.seed_layer0(paths)
    snap = snapshot.latest_snapshot_id(paths)
    p = {
        "schema_version": "expansion_proposal.v1", "proposal_id": "EXP-BFS-ALT-L1",
        "project_id": "p4-ldi", "bfs_id": "BFS-ALT", "layer": 1, "based_on_snapshot": snap,
        "nodes": [{"claim": "An alternative explanation.", "node_type": "alternative", "scope": {}, "parents": []}],
        "edges": [],
    }
    assert "V-EXP-07" in _validate(paths, p)


def test_closing_proposal_is_valid(project, pp):
    """An empty proposal closes a lane and validates."""
    paths = scenario.paths_for_pp(pp)
    scenario.seed_layer0(paths)
    snap = snapshot.latest_snapshot_id(paths)
    # layer-0 has nodes so the closing proposal's layer is frontier+1 = 1
    p = {
        "schema_version": "expansion_proposal.v1", "proposal_id": "EXP-BFS-MAIN-L1",
        "project_id": "p4-ldi", "bfs_id": "BFS-MAIN", "layer": 1, "based_on_snapshot": snap,
        "nodes": [], "edges": [],
    }
    # V-EXP-01 still applies (layer-0 checks open) — closing is only legal once the
    # lane's work is committed; here we only assert the empty shape is accepted by
    # the schema + layer math (no V-EXP-03 layer error).
    assert "V-EXP-03" not in _validate(paths, p)
