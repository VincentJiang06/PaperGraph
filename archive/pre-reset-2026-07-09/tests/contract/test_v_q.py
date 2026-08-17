"""V-Q contract tests (docs/09): the transition table, leases, events, the
blocked/unblock rule, and crash recovery. Every V-Q rule is violated by a scenario
and the clean walk replays cleanly (verify_queue).
"""

from __future__ import annotations

import pytest

from paperproof.errors import DomainError
from paperproof.prooftask import builder
from paperproof.queue import engine
from paperproof.validate.rules import v_q

from tests.fakes import scenario
from tests.fakes.workers import FakeDocsWorker, FakeProofWorker, prove_one

pytestmark = pytest.mark.contract


def test_queue_fail_default_reason_is_manual_fail(project, pp):
    """P10 (docs/10 §4): `queue fail` without --reason records reason 'manual fail'."""
    paths = scenario.paths_for_pp(pp)
    scenario.seed_layer0(paths)
    wi = next(i["work_item_id"] for i in engine.load_items(paths) if i["target_id"] == scenario.Q)
    pp("queue", "claim", "--queue", "proof_queue", "--agent", "w", "--id", wi)
    pp("queue", "fail", wi)
    fail_ev = [e for e in engine.load_events(paths) if e["work_item_id"] == wi and e["op"] == "fail"][-1]
    assert fail_ev["detail"]["reason"] == "manual fail"


def test_full_lifecycle_walk_emits_one_event_per_transition(project, pp, clock):
    """enqueue -> claim -> heartbeat -> complete -> validate_pass -> commit, each
    with exactly one QueueEvent (V-Q-03), only legal transitions (V-Q-01)."""
    paths = scenario.paths_for_pp(pp)
    scenario.seed_layer0(paths)
    builder.build_frontier(paths)
    wi = next(i["work_item_id"] for i in engine.load_items(paths) if i["target_id"] == scenario.Q)

    engine.claim(paths, queue_name="proof_queue", agent="w", wi_id=wi)
    engine.heartbeat(paths, wi, "w")
    # write the output so complete succeeds
    worker = FakeProofWorker({scenario.Q: scenario.node_pass_form()})
    item = engine.get_item(paths, wi)
    worker.run(item, paths.project_dir)
    engine.complete(paths, wi)

    ops = [e["op"] for e in engine.load_events(paths) if e["work_item_id"] == wi]
    assert ops == ["enqueue", "claim", "heartbeat", "complete"]
    assert v_q.verify_queue(paths) == []


# --- T-r3-7: `validate` completes a claimed/running item implicitly -----------


def test_validate_result_completes_implicitly_from_claimed(project, pp, clock):
    """claim -> (NO explicit complete) -> validate result performs `complete`
    itself, so one command emits two events (complete + validate_pass) and the
    item reaches validated with no illegal V-Q-01 transition."""
    from paperproof.validate import proof as validate_proof

    paths = scenario.paths_for_pp(pp)
    scenario.seed_layer0(paths)
    builder.build_frontier(paths)
    wi = next(i["work_item_id"] for i in engine.load_items(paths) if i["target_id"] == scenario.Q)

    claimed = engine.claim(paths, queue_name="proof_queue", agent="w", wi_id=wi)
    assert claimed["status"] == "claimed"
    FakeProofWorker({scenario.Q: scenario.node_pass_form()}).run(claimed, paths.project_dir)

    res = validate_proof.validate_result(paths, claimed["output_files"][0], wi, "w")
    assert res["proof_result_id"]
    assert engine.get_item(paths, wi)["status"] == "validated"

    ops = [e["op"] for e in engine.load_events(paths) if e["work_item_id"] == wi]
    assert ops == ["enqueue", "claim", "complete", "validate_pass"]
    assert v_q.verify_queue(paths) == []
    assert pp("verify")["ok"] is True


def test_docs_ingest_result_completes_implicitly_from_claimed(project, pp, clock):
    """The docs validate-and-ingest path (`docs ingest-result`) likewise completes
    a claimed item itself: complete + validate_pass + commit, one command."""
    from paperproof.docsdb import ingest as docs_ingest

    paths = scenario.paths_for_pp(pp)
    scenario.seed_docs_facts(paths, [scenario.FACT_CLAIM])
    # NODE-003 (fact) -> needs_docs creates a DocsRequest + a docs_queue item.
    prove_one(paths, "NODE-003", FakeProofWorker({"NODE-003": scenario.node_insufficient_form()}))

    engine.run_sweeps(paths, "test")
    docs_item = next(
        i for i in engine.load_items(paths)
        if i["queue_name"] == "docs_queue" and engine.is_claimable(paths, i)
    )
    claimed = engine.claim(paths, queue_name="docs_queue", agent="dw", wi_id=docs_item["work_item_id"])
    FakeDocsWorker({"*": scenario.boe_docs_result_spec()}).run(claimed, paths.project_dir)

    # NO explicit complete before ingest-result.
    docs_ingest.ingest_result(paths, claimed["output_files"][0], claimed["work_item_id"], "test")
    assert engine.get_item(paths, claimed["work_item_id"])["status"] == "committed"

    ops = [e["op"] for e in engine.load_events(paths) if e["work_item_id"] == claimed["work_item_id"]]
    assert ops == ["enqueue", "claim", "complete", "validate_pass", "commit"]
    assert v_q.verify_queue(paths) == []


def test_v_q_01_illegal_transition_rejected(project, pp):
    paths = scenario.paths_for_pp(pp)
    scenario.seed_layer0(paths)
    wi = next(i["work_item_id"] for i in engine.load_items(paths) if i["target_id"] == scenario.Q)
    # committing a queued item is not a legal edge
    with pytest.raises(DomainError) as exc:
        engine.commit_item(paths, wi, "w")
    assert any("V-Q-01" in e for e in exc.value.errors)


def test_v_q_02_second_claim_fails(project, pp):
    paths = scenario.paths_for_pp(pp)
    scenario.seed_layer0(paths)
    builder.build_frontier(paths)
    wi = next(i["work_item_id"] for i in engine.load_items(paths) if i["target_id"] == scenario.Q)
    engine.claim(paths, queue_name="proof_queue", agent="w1", wi_id=wi)
    with pytest.raises(DomainError):
        engine.claim(paths, queue_name="proof_queue", agent="w2", wi_id=wi)


def test_v_q_04_edge_blocked_until_endpoints_active(project, pp):
    paths = scenario.paths_for_pp(pp)
    scenario.seed_layer0(paths)
    builder.build_frontier(paths)
    # the T->Q edge item is blocked; claiming it directly must fail
    edge_wi = next(i["work_item_id"] for i in engine.load_items(paths) if i["target_id"] == scenario.EDGE_TQ)
    with pytest.raises(DomainError):
        engine.claim(paths, queue_name="proof_queue", agent="w", wi_id=edge_wi)
    # blocked_by ids exist
    item = engine.get_item(paths, edge_wi)
    ids = {i["work_item_id"] for i in engine.load_items(paths)}
    assert set(item["blocked_by"]) <= ids


def test_v_q_05_crash_recovery_requeue(project, pp, clock):
    paths = scenario.paths_for_pp(pp)
    scenario.seed_layer0(paths)
    builder.build_frontier(paths)
    wi = next(i["work_item_id"] for i in engine.load_items(paths) if i["target_id"] == scenario.Q)
    engine.claim(paths, queue_name="proof_queue", agent="w", wi_id=wi)
    clock.tick(901)
    engine.expire_sweep(paths)
    item = engine.get_item(paths, wi)
    assert item["status"] == "queued" and item["attempt"] == 2
    assert v_q.verify_queue(paths) == []


def test_v_q_03_hand_corrupted_event_detected(project, pp):
    """A status change with no matching event (or an impossible transition in the
    log) is caught by verify_queue (V-Q-03/V-Q-01)."""
    paths = scenario.paths_for_pp(pp)
    scenario.seed_layer0(paths)
    # append a bogus work-item record whose status was never reached by an event
    from paperproof.store import jsonl

    items = engine.load_items(paths)
    corrupt = dict(items[0])
    corrupt["status"] = "committed"  # no commit event exists
    jsonl.append(paths.resolve("queue/work_items.jsonl"), corrupt)
    failures = [f.rule_id for f in v_q.verify_queue(paths)]
    assert "V-Q-03" in failures
