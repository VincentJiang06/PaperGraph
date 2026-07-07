"""S1 seed loop (docs/09 §3, docs/11 §8).

Layer-0 seed (Q, T, A, B; edges T->Q, A->B, B->T) -> EDGE-A-B inference gap ->
needs_repair(bridge) -> Committer wires bridges C,D + edges C->B, D->B ->
prove C,D and their edges active -> re-prove EDGE-A-B -> pass(conditional).
Asserts the bridge wiring, the re-proof blocked_by, C/D in the spine, and ends
with verify exit 0. STOP at pass — local freeze is M3.
"""

from __future__ import annotations

import pytest

from paperproof.graph import model as graph_model
from paperproof.queue import engine
from paperproof.store import jsonl

from tests.fakes import scenario
from tests.fakes.workers import FakeProofWorker, drain

pytestmark = pytest.mark.integration


def test_s1_seed_loop(project, pp):
    paths = scenario.paths_for_pp(pp)
    scenario.seed_layer0(paths)

    worker = FakeProofWorker(scenario.s1_script())
    drain(paths, worker)

    gv = graph_model.load(paths)

    # bridges C, D created with origin.kind=bridge, source node's lane+layer.
    bridges = [n for n in gv.nodes if n["origin"]["kind"] == "bridge"]
    assert len(bridges) == 2, bridges
    a_node = gv.node_by_id[scenario.A]
    for br in bridges:
        assert br["bfs_id"] == a_node["bfs_id"] and br["layer"] == a_node["layer"]
        assert br["parents"] == [scenario.B]
        assert br["lifecycle_state"] == "active"

    # wired edges C->B, D->B exist (depends_on, since bridges are definitions).
    bridge_edges = [e for e in gv.edges if e["source_node_id"] in {b["node_id"] for b in bridges}]
    assert len(bridge_edges) == 2
    for e in bridge_edges:
        assert e["target_node_id"] == scenario.B
        assert e["edge_type"] == "depends_on"
        assert e["lifecycle_state"] == "active"

    # the re-proof EDGE-A-B item was blocked_by all four bridge items (2 node + 2 edge).
    reproof_items = [
        i for i in jsonl.read_all(paths.resolve("queue/work_items.jsonl"))
        if i["target_id"] == scenario.EDGE_AB and i["target_type"] == "edge" and len(i["blocked_by"]) == 4
    ]
    assert reproof_items, "expected an EDGE-A-B re-proof item blocked_by 4 bridge items"

    # final EDGE-A-B is active + conditional with the scripted assumptions.
    edge_ab = gv.edge_by_id[scenario.EDGE_AB]
    assert edge_ab["lifecycle_state"] == "active"
    assert edge_ab["strength"] == "conditional"
    assert edge_ab["assumptions"] == ["Rapid repricing outpaces collateral buffers."]

    # C, D are in the spine (active ancestors of T through B).
    spine_ids, _ = gv.spine()
    for br in bridges:
        assert br["node_id"] in spine_ids
    for e in bridge_edges:
        assert e["edge_id"] in spine_ids

    # every proof item ended committed/cancelled; nothing dead.
    statuses = {i["status"] for i in engine.load_items(paths)}
    assert "dead" not in statuses

    # verify exit 0
    env = pp("verify")
    assert env["ok"] is True
