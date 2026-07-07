"""S2 docs loop (docs/09 §3, docs/11 §8).

NODE_CHECK evidence insufficient -> needs_docs -> DocsRequest -> DocsResult
ingested -> re-proof pass(strong); an IDENTICAL second request resolves
fulfilled_by="cache" with NO docs work item created; the docs round-trip cap of
2 makes a 3rd needs_docs on a target BORN DEAD. Ends with verify exit 0.
"""

from __future__ import annotations

import pytest

from paperproof.graph import model as graph_model
from paperproof.queue import engine
from paperproof.store import jsonl

from tests.fakes import scenario
from tests.fakes.workers import FakeDocsWorker, FakeProofWorker, drain_docs, prove_one

pytestmark = pytest.mark.integration

NODE_A = "NODE-003"  # FACT_CLAIM (matcher-matched by the archived EU)
NODE_B = "NODE-004"  # a distinct fact, driven to the docs round-trip cap

DR = "docs/docs_requests.jsonl"
EU = "docs/evidence_units.jsonl"
DOCS_QUEUE = "docs_queue"


def _docs_items(paths):
    return [i for i in engine.load_items(paths) if i["queue_name"] == DOCS_QUEUE]


def _reqs(paths):
    return jsonl.latest_records(paths.resolve(DR), "request_id")


def test_s2_docs_loop(project, pp):
    paths = scenario.paths_for_pp(pp)
    scenario.seed_docs_facts(paths, [scenario.FACT_CLAIM, "UK gilt yields rose sharply during the 2022 autumn crisis."])

    proof_worker = FakeProofWorker({
        NODE_A: [scenario.node_insufficient_form(), scenario.node_sufficient_form(["EU-001"])],
        NODE_B: scenario.node_insufficient_form(),
    })
    docs_worker = FakeDocsWorker({"*": scenario.boe_docs_result_spec()})

    # Phase 1: NODE_A insufficient -> needs_docs -> a REAL docs work item (miss).
    prove_one(paths, NODE_A, proof_worker)
    assert len(_docs_items(paths)) == 1, "real miss should create one docs work item"
    dr1 = [r for r in _reqs(paths) if r["target_id"] == NODE_A][0]
    assert dr1["status"] == "open"

    # Phase 2: DocsWorker archives the source -> DR fulfilled, EU-001 archived.
    drain_docs(paths, docs_worker)
    dr1 = [r for r in _reqs(paths) if r["request_id"] == dr1["request_id"]][0]
    assert dr1["status"] == "fulfilled" and dr1["fulfilled_by"].startswith("DRES-")
    eus = jsonl.latest_records(paths.resolve(EU), "evidence_id")
    assert any(e["evidence_id"] == "EU-001" for e in eus)
    assert eus[0]["ingested_from"].startswith("DRES-")

    # Phase 3: an IDENTICAL second request => cache hit, NO docs work item created.
    before = len(_docs_items(paths))
    env = pp("docs", "request", "--target", NODE_A, "--need", scenario.DOCS_NEED,
             "--hint", scenario.DOCS_HINTS[0], "--hint", scenario.DOCS_HINTS[1])
    assert env["data"]["status"] == "fulfilled"
    assert env["data"]["fulfilled_by"] == "cache"
    assert env["data"]["work_item_id"] is None
    assert len(_docs_items(paths)) == before, "cache hit must NOT create a docs work item"

    # Phase 4: NODE_A re-proof now sees EU-001 in its rebuilt DocsPack -> pass(strong).
    prove_one(paths, NODE_A, proof_worker)
    gv = graph_model.load(paths)
    node_a = gv.node_by_id[NODE_A]
    assert node_a["lifecycle_state"] == "active"
    assert node_a["strength"] == "strong"
    assert node_a["evidence_bindings"] == ["EU-001"]

    # Phase 5: docs round-trip cap = 2. Drive NODE_B through needs_docs cycles;
    # the identical need resolves via cache each time (NO docs work items), and
    # the 3rd needs_docs is BORN DEAD.
    cap_docs_before = len(_docs_items(paths))
    prove_one(paths, NODE_B, proof_worker)  # cycle 1 (cache)
    prove_one(paths, NODE_B, proof_worker)  # cycle 2 (cache)
    assert len(_docs_items(paths)) == cap_docs_before, "cache-resolved cycles create no docs work items"
    completed = [r for r in _reqs(paths) if r["target_id"] == NODE_B and r["status"] == "fulfilled"]
    assert len(completed) == 2 and all(r["fulfilled_by"] == "cache" for r in completed)

    prove_one(paths, NODE_B, proof_worker)  # cycle 3 -> cap -> born dead
    dead = [i for i in engine.load_items(paths) if i["target_id"] == NODE_B and i["status"] == "dead"]
    assert dead, "3rd needs_docs on NODE_B must be born dead (cap 2)"
    events = jsonl.read_all(paths.resolve("queue/events.jsonl"))
    born = [
        e for e in events
        if e["work_item_id"] == dead[0]["work_item_id"]
        and e["op"] == "dead_letter" and e["from_status"] is None and e["to_status"] == "dead"
    ]
    assert born, "born-dead item must have a (created)->dead dead_letter event"
    # no third DocsRequest was appended for NODE_B beyond the two completed cycles.
    assert len([r for r in _reqs(paths) if r["target_id"] == NODE_B]) == 2

    # verify exit 0
    assert pp("verify")["ok"] is True
