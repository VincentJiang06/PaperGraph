"""Commit family: commit_decision.v1 (docs/08 B6)."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel

from ._common import STRICT

CommitKind = Literal[
    "proof_verdict", "expansion", "park", "unpark", "freeze_batch",
    "unfreeze_batch", "contract_reopen",
]
CommitAction = Literal[
    "append_node", "update_node", "append_edge", "update_edge", "tombstone",
    "enqueue", "cancel_item", "mark_stale", "docs_request", "set_frozen",
    # A saturated needs_docs whose role floor IS met: no more search can be
    # opened, so the re-proof is surfaced for human review (docs/17, D1). The
    # committer also born-deads the re-proof item alongside this action.
    "human_review",
]


class CommitActionEntry(BaseModel):
    model_config = STRICT

    action: CommitAction
    target_id: str
    detail: dict[str, Any]
    # For every GRAPH-mutating action (append_node|update_node|append_edge|
    # update_edge|tombstone|set_frozen), `record` is the EXACT graph record
    # appended to graph/*.jsonl; for non-graph actions it is null. This makes the
    # audit trail genuinely replayable (V-COMMIT-04, docs/08 §2b): the replay
    # reconstructs the post-graph state from these records alone.
    record: Optional[dict[str, Any]] = None


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
