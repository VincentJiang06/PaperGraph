"""Commit family: commit_decision.v1 (docs/08 B6)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from ._common import STRICT

CommitKind = Literal[
    "proof_verdict", "expansion", "park", "unpark", "freeze_batch",
    "unfreeze_batch", "contract_reopen",
]
CommitAction = Literal[
    "append_node", "update_node", "append_edge", "update_edge", "tombstone",
    "enqueue", "cancel_item", "mark_stale", "docs_request", "set_frozen",
]


class CommitActionEntry(BaseModel):
    model_config = STRICT

    action: CommitAction
    target_id: str
    detail: dict[str, Any]


class CommitDecision(BaseModel):
    model_config = STRICT

    schema_version: Literal["commit_decision.v1"] = "commit_decision.v1"
    commit_id: str
    project_id: str
    kind: CommitKind
    actor: str
    input_ref: str
    based_on_snapshot: str
    post_snapshot: str
    actions: list[CommitActionEntry]
    created_at: str
