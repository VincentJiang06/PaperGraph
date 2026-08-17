"""S4 parallel (docs/09 §3, docs/11 §8).

8 independent proof items, drained with parallel=4 concurrent FakeWorkers ->
all committed, zero double leases (V-Q-02 in the event log), events replay to the
final state (verify exit 0).
"""

from __future__ import annotations

import json

import pytest

from paperproof.expander import ingest as expander
from paperproof.graph import model as graph_model
from paperproof.queue import engine
from paperproof.store import jsonl, snapshot

from tests.fakes import scenario
from tests.fakes.workers import FakeProofWorker, drain

pytestmark = pytest.mark.integration


def _seed_8_independent(paths):
    """Layer-0 with Q, T and 6 independent definition nodes (8 node checks that
    share no 1-hop mutation, so none stales another)."""
    snap = snapshot.latest_snapshot_id(paths)
    nodes = [
        {"claim": "Why can pension de-risking transform solvency risk into liquidity risk?", "node_type": "question", "scope": {}, "parents": []},
        {"claim": "De-risking via leveraged LDI converts solvency hedging into liquidity stress.", "node_type": "thesis", "scope": {}, "parents": []},
    ]
    for i in range(6):
        nodes.append({"claim": f"Independent conceptual distinction number {i}.", "node_type": "definition", "scope": {}, "parents": []})
    proposal = {
        "schema_version": "expansion_proposal.v1", "proposal_id": "EXP-BFS-MAIN-L0",
        "project_id": "p4-ldi", "bfs_id": "BFS-MAIN", "layer": 0, "based_on_snapshot": snap,
        "nodes": nodes,
        "edges": [{"source_ref": "#1", "target_ref": "#0", "edge_type": "supports", "edge_claim": "The thesis resolves the question."}],
    }
    pf = paths.resolve("agent_outputs/expansions/EXP-BFS-MAIN-L0.json")
    pf.parent.mkdir(parents=True, exist_ok=True)
    pf.write_text(json.dumps(proposal), encoding="utf-8")
    return expander.ingest(paths, str(pf))


def test_s4_parallel(project, pp):
    paths = scenario.paths_for_pp(pp)
    _seed_8_independent(paths)

    node_ids = [f"NODE-{i:03d}" for i in range(1, 9)]
    script = {nid: scenario.node_pass_form() for nid in node_ids}
    # the one seed edge T->Q too
    script["EDGE-002-001"] = scenario.edge_pass_form("holds")

    drain(paths, FakeProofWorker(script), parallel=4)

    gv = graph_model.load(paths)
    # all 8 nodes committed (active)
    for nid in node_ids:
        assert gv.node_by_id[nid]["lifecycle_state"] == "active", nid

    items = engine.load_items(paths)
    assert all(i["status"] == "committed" for i in items), [(i["work_item_id"], i["status"]) for i in items]
    assert len(items) == 9  # 8 node checks + 1 edge check

    # V-Q-02: no work item was ever claimed twice without an intervening
    # release/expire (no double leases). In the happy path each item is claimed once.
    claims: dict[str, int] = {}
    for ev in engine.load_events(paths):
        if ev["op"] == "claim":
            claims[ev["work_item_id"]] = claims.get(ev["work_item_id"], 0) + 1
    assert all(c == 1 for c in claims.values()), claims

    env = pp("verify")
    assert env["ok"] is True
