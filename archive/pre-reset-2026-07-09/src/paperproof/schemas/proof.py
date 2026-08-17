"""Proof family: proof_task.v1, context_pack.v1, proof_result.v1,
verdict_record.v1 (docs/03, docs/08 B4)."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, model_serializer

from ._common import STRICT, Scope
from .graph import LanguageLimits

TaskType = Literal["NODE_CHECK", "EDGE_CHECK"]

ScopeCheck = Literal["in_scope", "out_of_scope"]
WellformedCheck = Literal["single_proposition", "too_broad", "compound", "not_evaluated"]
EvidenceCheck = Literal[
    "not_required", "sufficient", "insufficient", "contradicting", "not_evaluated"
]
InferenceCheck = Literal[
    "holds", "holds_only_with_assumptions", "gap", "fails", "not_evaluated"
]


class Bundle(BaseModel):
    model_config = STRICT

    task_file: str
    context_pack: str
    docs_pack: str


class ProofTask(BaseModel):
    model_config = STRICT

    schema_version: Literal["proof_task.v1"] = "proof_task.v1"
    task_id: str
    project_id: str
    task_type: TaskType
    target: dict[str, Any]
    context_pack: str
    docs_pack: str
    output_file: str


class ClaimDigestEntry(BaseModel):
    model_config = STRICT

    node_id: str
    claim: str


class ContextPack(BaseModel):
    model_config = STRICT

    schema_version: Literal["context_pack.v1"] = "context_pack.v1"
    pack_id: str
    task_id: str
    project_id: str
    based_on_snapshot: str
    target: dict[str, Any]
    neighbor_nodes: list[dict[str, Any]]
    neighbor_edges: list[dict[str, Any]]
    claim_digest: list[ClaimDigestEntry]
    contract_scope: Scope
    forbidden_claims: list[str]
    prior_results: list[dict[str, Any]]
    # S4 (docs/17, V-COV-02): the target's current DERIVED coverage ledger line for
    # a fact/mechanism/bridge target, so the worker KNOWS whether search is
    # exhausted and answers the honest endgame (narrow / pass-conditional) instead
    # of asking for docs the world does not have. null for targets with no floor.
    coverage: Optional[dict[str, Any]] = None


class DuplicateCheck(BaseModel):
    model_config = STRICT

    duplicate: bool
    duplicate_of: Optional[str] = None


class CheckForm(BaseModel):
    """The worker check form (docs/03). inference_check is present iff
    EDGE_CHECK; it is omitted on serialization when absent."""

    model_config = STRICT

    scope_check: ScopeCheck
    duplicate_check: DuplicateCheck
    wellformed_check: WellformedCheck
    evidence_check: EvidenceCheck
    inference_check: Optional[InferenceCheck] = None

    @model_serializer
    def _serialize(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "scope_check": self.scope_check,
            "duplicate_check": self.duplicate_check.model_dump(mode="json"),
            "wellformed_check": self.wellformed_check,
            "evidence_check": self.evidence_check,
        }
        if self.inference_check is not None:
            out["inference_check"] = self.inference_check
        return out


class RepairProposal(BaseModel):
    """A bridge or narrow repair (docs/03). Kept permissive at the schema layer;
    exact shape per kind is enforced by V-PR-09."""

    model_config = STRICT

    kind: Literal["bridge", "narrow"]
    claim: Optional[str] = None
    node_type: Optional[str] = None
    narrowed_claim: Optional[str] = None

    @model_serializer
    def _serialize(self) -> dict[str, Any]:
        if self.kind == "bridge":
            return {"kind": "bridge", "claim": self.claim, "node_type": self.node_type}
        return {"kind": "narrow", "narrowed_claim": self.narrowed_claim}


class DocsRequestStub(BaseModel):
    model_config = STRICT

    need: str
    search_hints: list[str]


class ProofResult(BaseModel):
    """The worker output check form (docs/03). No verdict, no worker-invented id."""

    model_config = STRICT

    schema_version: Literal["proof_result.v1"] = "proof_result.v1"
    task_id: str
    project_id: str
    target_type: Literal["node", "edge"]
    target_id: str
    form: CheckForm
    assumptions: list[str]
    evidence_used: list[str]
    language_limits: Optional[LanguageLimits]
    repair_proposals: list[RepairProposal]
    docs_requests: list[DocsRequestStub]
    notes: str


class ComputedVerdict(BaseModel):
    model_config = STRICT

    verdict: Literal["pass", "needs_repair", "needs_docs", "rejected"]
    repair_kind: Optional[Literal["bridge", "narrow"]] = None
    strength: Optional[Literal["strong", "conditional"]] = None
    reason: Optional[Literal["contradicted", "out_of_scope", "duplicate"]] = None


class VerdictRecord(BaseModel):
    model_config = STRICT

    schema_version: Literal["verdict_record.v1"] = "verdict_record.v1"
    proof_result_id: str
    project_id: str
    work_item_id: str
    task_id: str
    target_type: Literal["node", "edge"]
    target_id: str
    form: CheckForm
    assumptions: list[str]
    evidence_used: list[str]
    language_limits: Optional[LanguageLimits]
    repair_proposals: list[RepairProposal]
    docs_requests: list[DocsRequestStub]
    notes: str
    computed_verdict: ComputedVerdict
    bundle: Bundle
    validated_at: str
