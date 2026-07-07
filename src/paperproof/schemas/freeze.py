"""Freeze family: freeze_item.v1 (docs/06)."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel

from ._common import STRICT


class FreezeItem(BaseModel):
    model_config = STRICT

    schema_version: Literal["freeze_item.v1"] = "freeze_item.v1"
    freeze_id: str
    project_id: str
    action: Literal["freeze", "unfreeze"]
    freeze_type: Literal["local_freeze", "subtree_freeze", "spine_freeze"]
    target_ids: list[str]
    evidence_ids: list[str]
    allowed_language: list[str]
    forbidden_language: list[str]
    revokes: Optional[str]
    created_at: str
