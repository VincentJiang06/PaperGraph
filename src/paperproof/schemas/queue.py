"""Queue family: work_item.v1, queue_event.v1 (docs/05)."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel

from ._common import STRICT

# critic_queue (docs/15 — S2): the coverage critic is a distinct bounded worker
# (fresh context, adversarial, read-only), so it rides its own queue.
QueueName = Literal["proof_queue", "docs_queue", "compile_queue", "critic_queue"]
WorkStatus = Literal[
    "queued", "claimed", "running", "validating", "validated", "committed",
    "blocked", "stale", "failed", "dead", "cancelled",
]
QueueOp = Literal[
    "enqueue", "unblock", "claim", "heartbeat", "release", "expire", "complete",
    "fail", "validate_pass", "validate_fail", "retry", "dead_letter", "commit",
    "invalidate", "rebuild", "cancel", "requeue",
]


class Lease(BaseModel):
    model_config = STRICT

    claimed_by: Optional[str] = None
    claimed_at: Optional[str] = None
    expires_at: Optional[str] = None
    manifest: Optional[dict[str, Any]] = None


class WorkItem(BaseModel):
    model_config = STRICT

    schema_version: Literal["work_item.v1"] = "work_item.v1"
    work_item_id: str
    project_id: str
    queue_name: QueueName
    status: WorkStatus
    target_type: Literal["node", "edge", "request", "gap", "section", "wave"]
    target_id: str
    task_id: Optional[str]
    bundle: Optional[dict[str, Any]]
    output_files: list[str]
    blocked_by: list[str]
    lease: Lease
    attempt: int
    created_at: str
    updated_at: str


class QueueEvent(BaseModel):
    model_config = STRICT

    schema_version: Literal["queue_event.v1"] = "queue_event.v1"
    event_id: str
    project_id: str
    work_item_id: str
    op: QueueOp
    from_status: Optional[WorkStatus]
    to_status: WorkStatus
    actor: str
    detail: dict[str, Any]
    created_at: str
