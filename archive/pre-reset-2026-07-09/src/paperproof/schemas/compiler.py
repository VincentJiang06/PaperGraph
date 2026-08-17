"""Compiler family: compiler_dry_run.v1, draft_map.v1 (docs/06)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from ._common import STRICT

GapKind = Literal[
    "missing_evidence", "unhandled_alternative", "weak_spine_edge",
    "missing_section_claim", "contract_violation",
]


class SectionPlanEntry(BaseModel):
    model_config = STRICT

    section_id: str
    role: str
    nodes: list[str]


class Gap(BaseModel):
    model_config = STRICT

    kind: GapKind
    target_id: str
    note: str


class CompilerDryRun(BaseModel):
    model_config = STRICT

    schema_version: Literal["compiler_dry_run.v1"] = "compiler_dry_run.v1"
    run_id: str
    project_id: str
    snapshot_id: str
    writing_ready: bool
    section_plan: list[SectionPlanEntry]
    gaps: list[Gap]
    created_at: str


class DraftMapClaim(BaseModel):
    model_config = STRICT

    node_id: str
    claim: str
    evidence_ids: list[str]
    allowed_language: list[str]
    forbidden_language: list[str]


class DraftMapSection(BaseModel):
    model_config = STRICT

    section_id: str
    role: str
    claims: list[DraftMapClaim]
    edge_order: list[str]


class DraftMap(BaseModel):
    model_config = STRICT

    schema_version: Literal["draft_map.v1"] = "draft_map.v1"
    draft_map_id: str
    project_id: str
    based_on_dry_run: str
    sections: list[DraftMapSection]
    created_at: str
