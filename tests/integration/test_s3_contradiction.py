"""S3 contradiction cascade (docs/09 §3, docs/11 §8).

A fact node whose NODE_CHECK answers evidence_check=contradicting (evidence_used
from a real, non-empty DocsPack) -> rejected(contradicted) -> tombstone ->
CASCADE: every non-rejected incident edge -> rejected(endpoint_rejected) +
tombstone, and their open items cancelled. Runs at M2 because the contradicted
verdict needs evidence archived through the docs pipeline. Ends with verify 0.
"""

from __future__ import annotations

import pytest

from paperproof.graph import model as graph_model
from paperproof.queue import engine
from paperproof.store import jsonl

from tests.fakes import scenario
from tests.fakes.workers import FakeDocsWorker, FakeProofWorker, drain_docs, prove_one

pytestmark = pytest.mark.integration

NODE_X = "NODE-003"        # the fact node, claim = FACT_CLAIM
EDGE_XT = "EDGE-003-002"   # X -> T (incident to X)


def test_s3_contradiction(project, pp):
    paths = scenario.paths_for_pp(pp)
    scenario.seed_docs_facts(paths, [scenario.FACT_CLAIM])

    proof_worker = FakeProofWorker({
        NODE_X: [scenario.node_insufficient_form(), scenario.node_contradicting_form(["EU-001"])],
    })
    docs_worker = FakeDocsWorker({"*": scenario.boe_docs_result_spec()})

    # Archive evidence via the docs pipeline so the re-proof pack is non-empty.
    prove_one(paths, NODE_X, proof_worker)          # insufficient -> needs_docs -> docs item
    drain_docs(paths, docs_worker)                  # EU-001 archived, DR fulfilled, re-proof unblocked

    # The re-proof sees EU-001 in its DocsPack and answers contradicting.
    prove_one(paths, NODE_X, proof_worker)          # contradicting -> rejected(contradicted)

    gv = graph_model.load(paths)
    node_x = gv.node_by_id[NODE_X]
    assert node_x["lifecycle_state"] == "rejected"
    assert node_x["state_reason"] == "contradicted"

    # CASCADE: the incident edge X->T is rejected(endpoint_rejected).
    edge = gv.edge_by_id[EDGE_XT]
    assert edge["lifecycle_state"] == "rejected"
    assert edge["state_reason"] == "endpoint_rejected"

    # tombstones carry the right reasons.
    by_target = {t["target_id"]: t for t in graph_model.load_tombstones(paths)}
    assert by_target[NODE_X]["reason"] == "contradicted"
    assert by_target[EDGE_XT]["reason"] == "endpoint_rejected"

    # the edge's open EDGE_CHECK item was cancelled (op=cancel).
    edge_items = [i for i in engine.load_items(paths) if i["target_id"] == EDGE_XT]
    cancelled = [i for i in edge_items if i["status"] == "cancelled"]
    assert cancelled, "the incident edge's open item must be cancelled by the cascade"
    events = jsonl.read_all(paths.resolve("queue/events.jsonl"))
    cancel_ids = {i["work_item_id"] for i in cancelled}
    assert any(e["op"] == "cancel" and e["work_item_id"] in cancel_ids for e in events)

    # verify exit 0
    assert pp("verify")["ok"] is True
