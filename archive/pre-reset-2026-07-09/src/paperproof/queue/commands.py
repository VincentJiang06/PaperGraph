"""queue CLI command bodies (docs/10 §4). The unblock + expire sweeps run at the
start of every queue command (docs/05)."""

from __future__ import annotations

from typing import Any

from ..clock import actor as clock_actor
from ..errors import DomainError
from ..paths import Paths
from . import engine


def _sweep(paths: Paths, actor: str | None = None) -> None:
    engine.run_sweeps(paths, actor or clock_actor())


def list_items(paths: Paths, queue: str | None = None, status: str | None = None) -> dict[str, Any]:
    _sweep(paths)
    items = engine.load_items(paths)
    if queue == "commit_queue":
        # derived view: validated items awaiting commit, FIFO by validation time
        # (updated_at = validation-transition time; work_item_id is the tiebreak).
        items = sorted(
            [i for i in items if i["status"] == "validated"],
            key=lambda i: (i["updated_at"], i["work_item_id"]),
        )
    else:
        if queue:
            items = [i for i in items if i["queue_name"] == queue]
        if status:
            items = [i for i in items if i["status"] == status]
    return {"items": items, "count": len(items), "waves": _wave_groups(paths)}


def _wave_groups(paths: Paths) -> list[dict[str, Any]]:
    """S2 (docs/15): `queue list` shows wave grouping — each wave's members
    (docs_queue work items) plus its round/status, so an operator sees fanned
    searches grouped, not as loose docs items."""
    from ..docsdb import wave as wave_mod

    groups: list[dict[str, Any]] = []
    for w in wave_mod.load_waves(paths):
        groups.append({
            "wave_id": w["wave_id"], "request_id": w["request_id"], "round": w["round"],
            "status": w["status"],
            "members": [{"angle": m["angle"], "work_item_id": m["work_item_id"], "round": m.get("round", 1)}
                        for m in w.get("members", [])],
        })
    return groups


def claim(paths: Paths, queue: str, agent: str, wi_id: str | None = None) -> dict[str, Any]:
    item = engine.claim(paths, queue_name=queue, agent=agent, wi_id=wi_id)
    return {"work_item": item}


def heartbeat(paths: Paths, wi_id: str, agent: str) -> dict[str, Any]:
    _sweep(paths, agent)
    return {"work_item": engine.heartbeat(paths, wi_id, agent)}


def release(paths: Paths, wi_id: str) -> dict[str, Any]:
    _sweep(paths)
    return {"work_item": engine.release(paths, wi_id)}


def complete(paths: Paths, wi_id: str) -> dict[str, Any]:
    _sweep(paths)
    return {"work_item": engine.complete(paths, wi_id)}


def fail(paths: Paths, wi_id: str, reason: str) -> dict[str, Any]:
    _sweep(paths)
    return {"work_item": engine.fail(paths, wi_id, reason)}


def expire(paths: Paths) -> dict[str, Any]:
    actor = clock_actor()
    expired = engine.expire_sweep(paths, actor)
    unblocked = engine.unblock_sweep(paths, actor)
    dead = [i["work_item_id"] for i in engine.load_items(paths) if i["work_item_id"] in expired and i["status"] == "dead"]
    requeued = [wi for wi in expired if wi not in dead]
    return {"expired": expired, "requeued": requeued, "dead": dead, "unblocked": unblocked}


def requeue(paths: Paths, wi_id: str) -> dict[str, Any]:
    _sweep(paths)
    return {"work_item": engine.requeue(paths, wi_id)}


def events(paths: Paths, after: str | None = None) -> dict[str, Any]:
    _sweep(paths)
    evs = engine.load_events(paths)
    if after:
        evs = [e for e in evs if e["event_id"] > after]
    return {"events": evs, "count": len(evs)}
