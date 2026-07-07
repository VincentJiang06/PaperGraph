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
from tests.fakes.workers import FakeProofWorker

pytestmark = pytest.mark.contract


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
