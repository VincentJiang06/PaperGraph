"""project init / status (docs/07, docs/10 §4)."""

from __future__ import annotations

import re
from typing import Any

from .errors import DomainError, UsageError
from .paths import DIRS, EMPTY_JSONL, LOCK_FILES, PROJECT_ID_RE, Paths
from .store import jsonl, snapshot

_QUEUE_STATUSES = (
    "queued", "claimed", "running", "validating", "validated", "committed",
    "blocked", "stale", "failed", "dead", "cancelled",
)


def init(paths: Paths) -> dict[str, Any]:
    """Create the exact docs/07 storage tree + GS-000001 over the empty graph."""
    if not re.match(PROJECT_ID_RE, paths.project_id):
        raise UsageError([f"invalid project_id (must match {PROJECT_ID_RE}): {paths.project_id!r}"])
    if paths.project_dir.exists():
        raise DomainError([f"project already exists: {paths.project_id}"])

    project_dir = paths.project_dir
    project_dir.mkdir(parents=True, exist_ok=False)
    for rel in DIRS:
        (project_dir / rel).mkdir(parents=True, exist_ok=True)
    for rel in EMPTY_JSONL:
        (project_dir / rel).touch()
    for rel in LOCK_FILES:
        (project_dir / rel).touch()

    # GS-000001 over the (empty) graph files.
    snap = snapshot.take_snapshot(paths, snapshot_id="GS-000001")

    return {"project_id": paths.project_id, "root": str(paths.root), "snapshot_id": snap.snapshot_id}


def status(paths: Paths) -> dict[str, Any]:
    """Contract state, per-queue counts, MSA summary, dead letters, snapshot id."""
    if not paths.project_dir.exists():
        raise DomainError([f"project not found: {paths.project_id}"])

    contract: dict[str, Any] | None = None
    if paths.project_contract.exists():
        c = jsonl.read_json(paths.project_contract)
        contract = {
            "accepted_by_user": c.get("accepted_by_user", False),
            "accepted_at": c.get("accepted_at"),
            "contract_version": c.get("contract_version"),
        }

    work_items = jsonl.latest_records(paths.resolve("queue/work_items.jsonl"), "work_item_id")
    per_status = {s: 0 for s in _QUEUE_STATUSES}
    for wi in work_items:
        st = wi.get("status")
        if st in per_status:
            per_status[st] += 1
    dead_letters = per_status.get("dead", 0)

    return {
        "project_id": paths.project_id,
        "contract": contract,
        "current_snapshot": snapshot.latest_snapshot_id(paths),
        "queues": per_status,
        "dead_letters": dead_letters,
        "msa": None,
    }
