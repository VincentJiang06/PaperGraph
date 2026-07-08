"""The queue engine (docs/05): the exact 11-state transition table, leases,
QueueEvents, and the unblock/expire sweeps.

Every legal transition is in ``LEGAL`` (V-Q-01); every transition appends exactly
one WorkItem record and exactly one QueueEvent (V-Q-03). Claims are atomic under
``queue/.lock`` (V-Q-02). Leases are 900s, driven by PAPERPROOF_NOW; the expiry
sweep requeues (attempt+1) and dead-letters past 3 attempts (V-Q-05).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from ..clock import actor as clock_actor
from ..clock import now as clock_now
from ..errors import DomainError
from ..graph import model as graph_model
from ..ids import next_id
from ..paths import Paths
from ..store import file_lock, jsonl
from ..validate.rules import v_path

LEASE_SECONDS = 900
MAX_ATTEMPTS = 3

WORK_ITEMS = "queue/work_items.jsonl"
EVENTS = "queue/events.jsonl"
LOCK = "queue/.lock"

_TERMINAL = {"committed", "cancelled"}

# The complete transition table (docs/05). Each entry: (from_status, op) -> set
# of legal to_status. ``None`` from_status is the (created) pseudo-state.
LEGAL: dict[tuple[Optional[str], str], set[str]] = {
    (None, "enqueue"): {"queued", "blocked"},
    (None, "dead_letter"): {"dead"},
    ("blocked", "unblock"): {"queued"},
    ("queued", "claim"): {"claimed"},
    ("claimed", "heartbeat"): {"running"},
    ("running", "heartbeat"): {"running"},
    ("claimed", "release"): {"queued"},
    ("running", "release"): {"queued"},
    ("claimed", "expire"): {"queued", "dead"},
    ("running", "expire"): {"queued", "dead"},
    ("claimed", "complete"): {"validating"},
    ("running", "complete"): {"validating"},
    ("validating", "validate_pass"): {"validated"},
    ("validating", "validate_fail"): {"failed"},
    ("claimed", "fail"): {"failed"},
    ("running", "fail"): {"failed"},
    ("validating", "fail"): {"failed"},
    ("failed", "retry"): {"queued"},
    ("failed", "dead_letter"): {"dead"},
    ("validated", "commit"): {"committed"},
    ("queued", "invalidate"): {"stale"},
    ("blocked", "invalidate"): {"stale"},
    ("validated", "invalidate"): {"stale"},
    ("stale", "rebuild"): {"queued", "blocked"},
    ("queued", "cancel"): {"cancelled"},
    ("blocked", "cancel"): {"cancelled"},
    ("stale", "cancel"): {"cancelled"},
    ("failed", "cancel"): {"cancelled"},
    ("validated", "cancel"): {"cancelled"},
    ("dead", "requeue"): {"queued"},
}


# --- time helpers ----------------------------------------------------------

_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _parse(ts: str) -> datetime:
    return datetime.strptime(ts, _FMT).replace(tzinfo=timezone.utc)


def _plus(ts: str, seconds: int) -> str:
    return (_parse(ts) + timedelta(seconds=seconds)).strftime(_FMT)


def _empty_lease() -> dict[str, Any]:
    return {"claimed_by": None, "claimed_at": None, "expires_at": None, "manifest": None}


# --- load/append -----------------------------------------------------------


def load_items(paths: Paths) -> list[dict[str, Any]]:
    return jsonl.latest_records(paths.resolve(WORK_ITEMS), "work_item_id")


def items_by_id(paths: Paths) -> dict[str, dict[str, Any]]:
    return {i["work_item_id"]: i for i in load_items(paths)}


def load_events(paths: Paths) -> list[dict[str, Any]]:
    return jsonl.read_all(paths.resolve(EVENTS))


def get_item(paths: Paths, wi_id: str) -> dict[str, Any]:
    item = items_by_id(paths).get(wi_id)
    if item is None:
        raise DomainError([f"work item not found: {wi_id}"])
    return item


def _next_wi_id(paths: Paths) -> str:
    existing = [r["work_item_id"] for r in jsonl.read_all(paths.resolve(WORK_ITEMS))]
    return next_id("WI", existing)


def _next_qe_id(paths: Paths) -> str:
    existing = [r["event_id"] for r in jsonl.read_all(paths.resolve(EVENTS))]
    return next_id("QE", existing)


def _append_event(
    paths: Paths,
    *,
    work_item_id: str,
    op: str,
    from_status: Optional[str],
    to_status: str,
    actor: str,
    detail: dict[str, Any] | None = None,
) -> None:
    ev = {
        "schema_version": "queue_event.v1",
        "event_id": _next_qe_id(paths),
        "project_id": paths.project_id,
        "work_item_id": work_item_id,
        "op": op,
        "from_status": from_status,
        "to_status": to_status,
        "actor": actor,
        "detail": detail or {},
        "created_at": clock_now(),
    }
    jsonl.append(paths.resolve(EVENTS), ev)


def _transition(
    paths: Paths,
    item: dict[str, Any],
    *,
    op: str,
    to_status: str,
    actor: str,
    changes: dict[str, Any] | None = None,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from_status = item["status"]
    allowed = LEGAL.get((from_status, op))
    if allowed is None or to_status not in allowed:
        raise DomainError([f"V-Q-01: illegal transition {from_status} --{op}--> {to_status}"])
    new = dict(item)
    new["status"] = to_status
    new["updated_at"] = clock_now()
    if changes:
        new.update(changes)
    jsonl.append(paths.resolve(WORK_ITEMS), new)
    _append_event(
        paths,
        work_item_id=item["work_item_id"],
        op=op,
        from_status=from_status,
        to_status=to_status,
        actor=actor,
        detail=detail,
    )
    return new


# --- enqueue / born-dead (Committer/Compiler side effects) -----------------


def enqueue(
    paths: Paths,
    *,
    queue_name: str,
    target_type: str,
    target_id: str,
    task_id: Optional[str] = None,
    bundle: Optional[dict[str, Any]] = None,
    output_files: list[str] | None = None,
    blocked_by: list[str] | None = None,
    actor: str,
) -> dict[str, Any]:
    """(created) -> queued|blocked. Used by the Committer and Compiler only."""
    blocked_by = list(blocked_by or [])
    status = "blocked" if blocked_by else "queued"
    now = clock_now()
    item = {
        "schema_version": "work_item.v1",
        "work_item_id": _next_wi_id(paths),
        "project_id": paths.project_id,
        "queue_name": queue_name,
        "status": status,
        "target_type": target_type,
        "target_id": target_id,
        "task_id": task_id,
        "bundle": bundle,
        "output_files": list(output_files or []),
        "blocked_by": blocked_by,
        "lease": _empty_lease(),
        "attempt": 1,
        "created_at": now,
        "updated_at": now,
    }
    jsonl.append(paths.resolve(WORK_ITEMS), item)
    _append_event(
        paths,
        work_item_id=item["work_item_id"],
        op="enqueue",
        from_status=None,
        to_status=status,
        actor=actor,
        detail={"blocked_by": blocked_by} if blocked_by else {},
    )
    return item


def dead_letter_born(
    paths: Paths,
    *,
    queue_name: str,
    target_type: str,
    target_id: str,
    blocked_by: list[str] | None = None,
    reason: str,
    actor: str,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """(created) -> dead (op=dead_letter): a re-proof item born dead for human
    review when the docs or bridge round cap is hit (docs/08). ``detail`` merges
    extra keys into the QueueEvent detail (e.g. saturation carries floor_met so a
    later `queue requeue` can resume — D1)."""
    now = clock_now()
    item = {
        "schema_version": "work_item.v1",
        "work_item_id": _next_wi_id(paths),
        "project_id": paths.project_id,
        "queue_name": queue_name,
        "status": "dead",
        "target_type": target_type,
        "target_id": target_id,
        "task_id": None,
        "bundle": None,
        "output_files": [],
        "blocked_by": list(blocked_by or []),
        "lease": _empty_lease(),
        "attempt": 1,
        "created_at": now,
        "updated_at": now,
    }
    jsonl.append(paths.resolve(WORK_ITEMS), item)
    event_detail: dict[str, Any] = {"reason": reason}
    if detail:
        event_detail.update(detail)
    _append_event(
        paths,
        work_item_id=item["work_item_id"],
        op="dead_letter",
        from_status=None,
        to_status="dead",
        actor=actor,
        detail=event_detail,
    )
    return item


# --- sweeps ----------------------------------------------------------------


def expire_sweep(paths: Paths, actor: str | None = None) -> list[str]:
    """Expire leases past their expiry: attempt+1 -> queued, or dead if >3."""
    actor = actor or clock_actor()
    now = clock_now()
    affected: list[str] = []
    for item in load_items(paths):
        if item["status"] not in ("claimed", "running"):
            continue
        exp = item["lease"].get("expires_at")
        if not exp or _parse(exp) > _parse(now):
            continue
        new_attempt = item["attempt"] + 1
        to_status = "dead" if new_attempt > MAX_ATTEMPTS else "queued"
        _transition(
            paths,
            item,
            op="expire",
            to_status=to_status,
            actor=actor,
            changes={"attempt": new_attempt, "lease": _empty_lease()},
            detail={"attempt": new_attempt},
        )
        affected.append(item["work_item_id"])
    return affected


def _blockers_resolved(item: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> bool:
    for bid in item.get("blocked_by", []):
        blocker = by_id.get(bid)
        if blocker is None or blocker["status"] not in _TERMINAL:
            return False
    return True


def _edge_endpoints_active(paths: Paths, item: dict[str, Any], gv: graph_model.GraphView) -> bool:
    edge = gv.edge_by_id.get(item["target_id"])
    if edge is None:
        return False
    return gv.is_active(edge["source_node_id"]) and gv.is_active(edge["target_node_id"])


def is_claimable(paths: Paths, item: dict[str, Any], gv: graph_model.GraphView | None = None) -> bool:
    """V-Q-04: claimable iff queued, blockers resolved, and (EDGE_CHECK) both
    endpoints active. Queued items have already passed the unblock sweep."""
    if item["status"] != "queued":
        return False
    if item["queue_name"] == "proof_queue" and item["target_type"] == "edge":
        gv = gv or graph_model.load(paths)
        return _edge_endpoints_active(paths, item, gv)
    return True


def unblock_sweep(paths: Paths, actor: str | None = None) -> list[str]:
    """blocked -> queued when all blockers are terminal AND (EDGE_CHECK) both
    endpoints are active."""
    actor = actor or clock_actor()
    by_id = items_by_id(paths)
    gv = graph_model.load(paths)
    affected: list[str] = []
    for item in list(by_id.values()):
        if item["status"] != "blocked":
            continue
        if not _blockers_resolved(item, by_id):
            continue
        if item["queue_name"] == "proof_queue" and item["target_type"] == "edge":
            if not _edge_endpoints_active(paths, item, gv):
                continue
        _transition(paths, item, op="unblock", to_status="queued", actor=actor)
        affected.append(item["work_item_id"])
    return affected


def run_sweeps(paths: Paths, actor: str | None = None) -> dict[str, list[str]]:
    return {"expired": expire_sweep(paths, actor), "unblocked": unblock_sweep(paths, actor)}


# --- claim / lease-cycle ops -----------------------------------------------


def claim(paths: Paths, *, queue_name: str, agent: str, wi_id: str | None = None) -> dict[str, Any]:
    with file_lock(paths.resolve(LOCK)):
        run_sweeps(paths, agent)
        gv = graph_model.load(paths)
        by_id = items_by_id(paths)
        if wi_id is not None:
            item = by_id.get(wi_id)
            if item is None:
                raise DomainError([f"work item not found: {wi_id}"])
            if item["queue_name"] != queue_name or not is_claimable(paths, item, gv):
                raise DomainError([f"work item not claimable: {wi_id} (status {item['status']})"])
        else:
            claimable = [
                i
                for i in by_id.values()
                if i["queue_name"] == queue_name and is_claimable(paths, i, gv)
            ]
            if not claimable:
                raise DomainError([f"no claimable item in {queue_name}"])
            item = min(claimable, key=lambda i: i["work_item_id"])

        now = clock_now()
        allowed_paths = list(item.get("output_files") or []) + ["agent_notes/**"]
        manifest = v_path.build_lease_manifest(paths.project_dir, allowed_paths)
        lease = {
            "claimed_by": agent,
            "claimed_at": now,
            "expires_at": _plus(now, LEASE_SECONDS),
            "manifest": manifest,
        }
        return _transition(
            paths,
            item,
            op="claim",
            to_status="claimed",
            actor=agent,
            changes={"lease": lease},
            detail={"claimed_by": agent, "expires_at": lease["expires_at"]},
        )


def heartbeat(paths: Paths, wi_id: str, agent: str) -> dict[str, Any]:
    with file_lock(paths.resolve(LOCK)):
        item = get_item(paths, wi_id)
        lease = dict(item["lease"])
        lease["expires_at"] = _plus(clock_now(), LEASE_SECONDS)
        return _transition(
            paths, item, op="heartbeat", to_status="running", actor=agent,
            changes={"lease": lease}, detail={"expires_at": lease["expires_at"]},
        )


def release(paths: Paths, wi_id: str, actor: str | None = None) -> dict[str, Any]:
    actor = actor or clock_actor()
    with file_lock(paths.resolve(LOCK)):
        item = get_item(paths, wi_id)
        return _transition(
            paths, item, op="release", to_status="queued", actor=actor,
            changes={"lease": _empty_lease()},
        )


def complete(paths: Paths, wi_id: str, actor: str | None = None) -> dict[str, Any]:
    actor = actor or clock_actor()
    with file_lock(paths.resolve(LOCK)):
        item = get_item(paths, wi_id)
        for out in item.get("output_files", []):
            if not (paths.project_dir / out).exists():
                raise DomainError([f"output file missing, cannot complete: {out}"])
        return _transition(paths, item, op="complete", to_status="validating", actor=actor)


def _after_fail(paths: Paths, item_now: dict[str, Any], actor: str, detail: dict[str, Any]) -> dict[str, Any]:
    """From ``failed``: retry (attempt+1 -> queued) or dead-letter (attempt>=3)."""
    if item_now["attempt"] < MAX_ATTEMPTS:
        return _transition(
            paths, item_now, op="retry", to_status="queued", actor=actor,
            changes={"attempt": item_now["attempt"] + 1, "lease": _empty_lease()},
        )
    return _transition(
        paths, item_now, op="dead_letter", to_status="dead", actor=actor,
        changes={"lease": _empty_lease()}, detail=detail,
    )


def fail(paths: Paths, wi_id: str, reason: str, actor: str | None = None) -> dict[str, Any]:
    actor = actor or clock_actor()
    with file_lock(paths.resolve(LOCK)):
        item = get_item(paths, wi_id)
        failed = _transition(
            paths, item, op="fail", to_status="failed", actor=actor, detail={"reason": reason}
        )
        return _after_fail(paths, failed, actor, {"reason": reason})


def validate_pass(paths: Paths, wi_id: str, actor: str | None = None, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    actor = actor or clock_actor()
    with file_lock(paths.resolve(LOCK)):
        item = get_item(paths, wi_id)
        return _transition(paths, item, op="validate_pass", to_status="validated", actor=actor, detail=detail)


def validate_fail(
    paths: Paths,
    wi_id: str,
    failed_rules: list[str],
    actor: str | None = None,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """`detail` maps rule id -> offending path/field message (docs/08 failure
    taxonomy; T-r3-8 — the live run's V-PATH-04 events carried bare rule ids,
    leaving the offending file undiagnosable from the event log)."""
    actor = actor or clock_actor()
    event_detail: dict[str, Any] = {"failed_rules": failed_rules}
    if detail:
        event_detail["detail"] = detail
    with file_lock(paths.resolve(LOCK)):
        item = get_item(paths, wi_id)
        failed = _transition(
            paths, item, op="validate_fail", to_status="failed", actor=actor,
            detail=event_detail,
        )
        return _after_fail(paths, failed, actor, event_detail)


def requeue(paths: Paths, wi_id: str, actor: str | None = None) -> dict[str, Any]:
    actor = actor or clock_actor()
    with file_lock(paths.resolve(LOCK)):
        item = get_item(paths, wi_id)
        return _transition(
            paths, item, op="requeue", to_status="queued", actor=actor,
            changes={"attempt": 1, "lease": _empty_lease()},
        )


# --- Committer-side transitions (called while holding commit lock) ----------


def attach_bundle(paths: Paths, wi_id: str, task_id: str, bundle: dict[str, Any], output_files: list[str]) -> dict[str, Any]:
    """Fill a queued item's bundle/task_id/output_files without a status change
    (no QueueEvent — appending a bundle is not a transition)."""
    with file_lock(paths.resolve(LOCK)):
        item = get_item(paths, wi_id)
        new = dict(item)
        new["task_id"] = task_id
        new["bundle"] = bundle
        new["output_files"] = list(output_files)
        new["updated_at"] = clock_now()
        jsonl.append(paths.resolve(WORK_ITEMS), new)
        return new


def commit_item(paths: Paths, wi_id: str, actor: str) -> dict[str, Any]:
    item = get_item(paths, wi_id)
    return _transition(paths, item, op="commit", to_status="committed", actor=actor)


def invalidate(paths: Paths, wi_id: str, actor: str, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    item = get_item(paths, wi_id)
    return _transition(paths, item, op="invalidate", to_status="stale", actor=actor, detail=detail)


def cancel(paths: Paths, wi_id: str, actor: str, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    item = get_item(paths, wi_id)
    return _transition(paths, item, op="cancel", to_status="cancelled", actor=actor, detail=detail)


def rebuild(paths: Paths, wi_id: str, actor: str, to_blocked: bool = False, changes: dict[str, Any] | None = None) -> dict[str, Any]:
    item = get_item(paths, wi_id)
    merged = {"lease": _empty_lease()}
    if changes:
        merged.update(changes)
    return _transition(
        paths, item, op="rebuild", to_status="blocked" if to_blocked else "queued",
        actor=actor, changes=merged,
    )
