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


def test_spine_excludes_edge_with_reverted_source(project, pp):
    """P4 (docs/02 active ancestor closure): an active edge whose SOURCE node has
    been reverted to pending_proof drops OUT of the spine. Reopening a node
    without its incident edge must not leave a dangling edge over-included in the
    spine (and msa-check's reported spine must exclude it)."""
    from paperproof.graph import commands as graph_commands

    paths = scenario.paths_for_pp(pp)
    scenario.seed_layer0(paths)
    drain(paths, FakeProofWorker(scenario.s1_script()))

    gv = graph_model.load(paths)
    spine_before, _ = gv.spine()
    assert scenario.EDGE_BT in spine_before and scenario.B in spine_before

    # reopen node B (source of B->T) to pending_proof; leave B->T active.
    b = dict(gv.node_by_id[scenario.B])
    b.update({
        "lifecycle_state": "pending_proof", "state_reason": None, "state_detail": None,
        "strength": "unassessed", "created_at": "2026-07-07T01:00:00Z",
    })
    jsonl.append(paths.resolve("graph/logic_nodes.jsonl"), b)

    gv2 = graph_model.load(paths)
    assert gv2.edge_by_id[scenario.EDGE_BT]["lifecycle_state"] == "active"
    spine_after, _ = gv2.spine()
    assert scenario.EDGE_BT not in spine_after, "active edge off a pending source must leave the spine"
    assert scenario.B not in spine_after
    assert scenario.EDGE_BT not in graph_commands.msa_check(paths)["spine"]


def test_s1_local_freeze_coda(project, pp):
    """S1 freeze coda (docs/11 §8): after S1's pass(conditional), local_freeze the
    edge closure. The one target edge is frozen; its endpoints are not; the
    FreezeItem carries the union of the edge's language limits."""
    paths = scenario.paths_for_pp(pp)
    scenario.seed_layer0(paths)
    drain(paths, FakeProofWorker(scenario.s1_script()))

    env = pp("freeze", "apply", "--target", scenario.EDGE_AB, "--level", "local")
    assert env["ok"] is True

    gv = graph_model.load(paths)
    assert gv.edge_by_id[scenario.EDGE_AB]["frozen"] is True
    # local closure = the one target only; endpoints stay unfrozen.
    assert gv.node_by_id[scenario.A]["frozen"] is False
    assert gv.node_by_id[scenario.B]["frozen"] is False

    items = jsonl.read_all(paths.resolve("freeze/frozen_items.jsonl"))
    fi = items[-1]
    assert fi["freeze_type"] == "local_freeze"
    assert fi["target_ids"] == [scenario.EDGE_AB]
    assert fi["allowed_language"] and fi["forbidden_language"]

    assert pp("verify")["ok"] is True
