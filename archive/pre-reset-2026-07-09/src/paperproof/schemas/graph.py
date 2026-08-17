"""Graph family: logic_node.v1, logic_edge.v1, tombstone.v1, snapshot.v1,
expansion_proposal.v1 (docs/02, docs/07, docs/08 B3)."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel

from ._common import STRICT, Scope

NodeType = Literal["question", "thesis", "fact", "mechanism", "definition", "alternative"]
EdgeType = Literal["supports", "refutes", "depends_on"]
LifecycleState = Literal[
    "candidate", "pending_proof", "active", "needs_repair", "needs_docs", "rejected", "parked"
]
Strength = Literal["unassessed", "strong", "conditional"]


class Origin(BaseModel):
    model_config = STRICT

    kind: Literal["seed", "expansion", "bridge"]
    source: str


class LanguageLimits(BaseModel):
    model_config = STRICT

    allowed: list[str]
    forbidden: list[str]


class LogicNode(BaseModel):
    model_config = STRICT

    schema_version: Literal["logic_node.v1"] = "logic_node.v1"
    node_id: str
    project_id: str
    bfs_id: str
    layer: int
    claim: str
    claim_version: int
    node_type: NodeType
    scope: Scope
    parents: list[str]
    origin: Origin
    lifecycle_state: LifecycleState
    state_reason: Optional[str]
    state_detail: Optional[dict[str, Any]]
    strength: Strength
    language_limits: Optional[LanguageLimits]
    assumptions: list[str]
    evidence_bindings: list[str]
    latest_proof_result_id: Optional[str]
    frozen: bool
    created_at: str


class LogicEdge(BaseModel):
    model_config = STRICT

    schema_version: Literal["logic_edge.v1"] = "logic_edge.v1"
    edge_id: str
    project_id: str
    source_node_id: str
    target_node_id: str
    edge_type: EdgeType
    edge_claim: str
    claim_version: int
    lifecycle_state: LifecycleState
    state_reason: Optional[str]
    state_detail: Optional[dict[str, Any]]
    strength: Strength
    language_limits: Optional[LanguageLimits]
    assumptions: list[str]
    frozen: bool
    latest_proof_result_id: Optional[str]
    created_at: str


class Tombstone(BaseModel):
    model_config = STRICT

    schema_version: Literal["tombstone.v1"] = "tombstone.v1"
    tombstone_id: str
    project_id: str
    target_type: Literal["node", "edge"]
    target_id: str
    reason: Literal["contradicted", "out_of_scope", "duplicate", "endpoint_rejected"]
    duplicate_of: Optional[str]
    commit_id: str
    created_at: str


class SnapshotFile(BaseModel):
    model_config = STRICT

    sha256: str
    rows: int


class Snapshot(BaseModel):
    """snapshot.v1 - the one canonical JSONL record that omits project_id
    (implied by location, docs/07)."""

    model_config = STRICT

    schema_version: Literal["snapshot.v1"] = "snapshot.v1"
    snapshot_id: str
    files: dict[str, SnapshotFile]
    created_at: str


class ProposalNode(BaseModel):
    model_config = STRICT

    claim: str
    node_type: NodeType
    scope: Scope
    parents: list[str] = []


class ProposalEdge(BaseModel):
    model_config = STRICT

    source_ref: str
    target_ref: str
    edge_type: EdgeType
    edge_claim: str


class ExpansionProposal(BaseModel):
    model_config = STRICT

    schema_version: Literal["expansion_proposal.v1"] = "expansion_proposal.v1"
    proposal_id: str
    project_id: str
    bfs_id: str
    layer: int
    based_on_snapshot: str
    nodes: list[ProposalNode]
    edges: list[ProposalEdge]
