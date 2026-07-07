"""V-Q: queue engine invariants (docs/09).

V-Q-01  status transitions only along the docs/05 table
V-Q-02  claim atomic: a work item never has two live leases
V-Q-03  every status change has exactly one QueueEvent (heartbeat may repeat)
V-Q-04  blocked_by ids exist; claimability = blockers resolved AND endpoints active
V-Q-05  expired lease => requeue attempt+1; attempt >3 => dead

``verify_queue`` replays the event log and checks it reconstructs the latest
work-item statuses, that every transition is legal, and lease/blocked_by
consistency.
"""

from __future__ import annotations

from typing import Any

from ...paths import Paths
from ...store import jsonl
from ..envelope import Failure
from ...queue.engine import LEGAL


def transition_legal(from_status: Any, op: str, to_status: str) -> bool:
    allowed = LEGAL.get((from_status, op))
    return allowed is not None and to_status in allowed


def verify_queue(paths: Paths) -> list[Failure]:
    failures: list[Failure] = []
    from ...queue import engine

    events = engine.load_events(paths)
    replayed: dict[str, str] = {}
    for ev in events:
        wi = ev["work_item_id"]
        op = ev["op"]
        frm = ev["from_status"]
        to = ev["to_status"]
        # V-Q-01
        if not transition_legal(frm, op, to):
            failures.append(Failure("V-Q-01", f"illegal transition {frm}--{op}-->{to} on {wi}"))
        # from_status consistency with replay
        prev = replayed.get(wi)
        if frm is not None and prev is not None and frm != prev:
            failures.append(Failure("V-Q-03", f"{wi}: event from_status {frm} != replayed {prev}"))
        replayed[wi] = to

    items = engine.items_by_id(paths)
    for wi_id, item in items.items():
        # V-Q-03: latest record status must equal event-derived status
        if replayed.get(wi_id) != item["status"]:
            failures.append(Failure("V-Q-03", f"{wi_id}: latest status {item['status']} != events {replayed.get(wi_id)}"))
        # V-Q-02: a live lease belongs only to claimed/running items. (A lease
        # left on a committed/validating item is historical, not live — a
        # "live" lease is one an expiry sweep could act on.)
        lease = item.get("lease") or {}
        if item["status"] in ("claimed", "running") and not lease.get("claimed_by"):
            failures.append(Failure("V-Q-02", f"{wi_id}: {item['status']} without a live lease"))
        if item["status"] in ("queued", "blocked") and lease.get("claimed_by"):
            failures.append(Failure("V-Q-02", f"{wi_id}: {item['status']} still holds a live lease"))
        # V-Q-04: blocked_by resolvable
        for bid in item.get("blocked_by", []):
            if bid not in items:
                failures.append(Failure("V-Q-04", f"{wi_id}: blocked_by {bid} does not exist"))
        # V-Q-05: attempt bound
        if item["attempt"] > 3 and item["status"] != "dead":
            failures.append(Failure("V-Q-05", f"{wi_id}: attempt {item['attempt']} > 3 but not dead"))
    return failures
