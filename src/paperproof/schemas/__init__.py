"""Schema registry: schema_version string -> pydantic v2 model class.

THE only schema location (docs/10 §3). Every *.v1 model that appears anywhere in
the docs is registered here; the schema round-trip meta-test iterates this map.
"""

from __future__ import annotations

from pydantic import BaseModel

from .audit import AuditReport
from .commit import CommitDecision
from .compiler import CompilerDryRun, DraftMap
from .docs import (
    DocsPack,
    DocsPackV2,
    DocsRequest,
    DocsResult,
    DocsResultV2,
    Document,
    DocumentV2,
    EvidenceUnit,
    SourceProfile,
)
from .search import CoverageReport, SearchPlan, SearchWave
from .freeze import FreezeItem
from .graph import (
    ExpansionProposal,
    LogicEdge,
    LogicNode,
    Snapshot,
    Tombstone,
)
from .proof import ContextPack, ProofResult, ProofTask, VerdictRecord
from .queue import QueueEvent, WorkItem
from .spec import PaperSpec, ProjectContract

REGISTRY: dict[str, type[BaseModel]] = {
    "paper_spec.v1": PaperSpec,
    "project_contract.v1": ProjectContract,
    "logic_node.v1": LogicNode,
    "logic_edge.v1": LogicEdge,
    "tombstone.v1": Tombstone,
    "snapshot.v1": Snapshot,
    "expansion_proposal.v1": ExpansionProposal,
    "proof_task.v1": ProofTask,
    "context_pack.v1": ContextPack,
    "proof_result.v1": ProofResult,
    "verdict_record.v1": VerdictRecord,
    "document.v1": Document,
    "document.v2": DocumentV2,
    "source_profile.v1": SourceProfile,
    "evidence_unit.v1": EvidenceUnit,
    "docs_request.v1": DocsRequest,
    "docs_result.v1": DocsResult,
    "docs_result.v2": DocsResultV2,
    "search_plan.v1": SearchPlan,
    "search_wave.v1": SearchWave,
    "coverage_report.v1": CoverageReport,
    "docs_pack.v1": DocsPack,
    "docs_pack.v2": DocsPackV2,
    "work_item.v1": WorkItem,
    "queue_event.v1": QueueEvent,
    "commit_decision.v1": CommitDecision,
    "freeze_item.v1": FreezeItem,
    "compiler_dry_run.v1": CompilerDryRun,
    "draft_map.v1": DraftMap,
    "audit_report.v1": AuditReport,
}


def model_for(schema_version: str) -> type[BaseModel]:
    """Return the model class for a schema_version, or raise KeyError."""
    return REGISTRY[schema_version]


__all__ = ["REGISTRY", "model_for"]
