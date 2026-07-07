"""S5 crash recovery (docs/09 §3, docs/11 §8).

A worker claims and dies without completing; the lease expires (clock.tick(901)),
the item requeues with attempt+1, and after 3 expiries it is dead (attempt > 3)
and appears in `queue list --status dead`.
"""

from __future__ import annotations

import pytest

from paperproof.prooftask import builder
from paperproof.queue import engine

from tests.fakes import scenario

pytestmark = pytest.mark.integration


def test_s5_crash_to_dead(project, pp, clock):
    paths = scenario.paths_for_pp(pp)
    scenario.seed_layer0(paths)
    builder.build_frontier(paths)

    wi_id = next(i["work_item_id"] for i in engine.load_items(paths) if i["target_id"] == scenario.Q)

    for expected_attempt in (1, 2, 3):
        claimed = engine.claim(paths, queue_name="proof_queue", agent="crasher", wi_id=wi_id)
        assert claimed["attempt"] == expected_attempt
        # worker crashes: never completes. lease expires.
        clock.tick(901)
        engine.expire_sweep(paths)

    item = engine.get_item(paths, wi_id)
    assert item["status"] == "dead"
    assert item["attempt"] == 4

    # the second worker on an earlier attempt won cleanly (each expiry requeued);
    # attempt increments are recorded as expire events.
    expire_events = [e for e in engine.load_events(paths) if e["work_item_id"] == wi_id and e["op"] == "expire"]
    assert len(expire_events) == 3
    assert expire_events[-1]["to_status"] == "dead"

    dead = pp("queue", "list", "--status", "dead")
    assert wi_id in [i["work_item_id"] for i in dead["data"]["items"]]

    env = pp("verify")
    assert env["ok"] is True
