"""Spec family: paper_spec.v1, project_contract.v1 (docs/01)."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel

from ._common import STRICT, Scope

PaperType = Literal[
    "single_event_mechanism",
    "parallel_case_bfs_then_merge",
    "core_experiment_empirical",
    "literature_debate_mapping",
    "policy_design_memo",
    "freeform_research_design",
]


class BfsPlanEntry(BaseModel):
    model_config = STRICT

    bfs_id: str
    purpose: str
    depends_on: list[str] = []


class PaperSpec(BaseModel):
    model_config = STRICT

    schema_version: Literal["paper_spec.v1"] = "paper_spec.v1"
    project_id: str
    paper_type: PaperType
    core_question: str
    intended_thesis: str
    scope: Scope
    hard_exclusions: list[str]
    seed_claims: list[str]
    known_sources: list[str]
    success_criteria: list[str]
    bfs_plan: list[BfsPlanEntry]
    source_files: list[str] = []


class ProjectContract(BaseModel):
    model_config = STRICT

    schema_version: Literal["project_contract.v1"] = "project_contract.v1"
    project_id: str
    contract_version: int
    fixed_question: str
    outcome_direction: str
    scope: Scope
    in_scope: list[str]
    out_of_scope: list[str]
    forbidden_claims: list[str]
    success_criteria: list[str]
    accepted_by_user: bool
    accepted_at: Optional[str]
