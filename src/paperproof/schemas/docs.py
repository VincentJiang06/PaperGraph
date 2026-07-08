"""Docs family: document.v1, evidence_unit.v1, docs_request.v1, docs_result.v1,
docs_pack.v1 (docs/04, docs/08 B7)."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel

from ._common import STRICT, Scope

SourceType = Literal[
    "peer_reviewed", "official_report", "working_paper", "news", "dataset", "user_notes"
]
SupportDirection = Literal["supports", "refutes", "context"]
EvidenceKind = Literal["quote", "paraphrase"]


class DocumentOrigin(BaseModel):
    model_config = STRICT

    kind: Literal["user_provided", "web"]
    path: Optional[str] = None
    url: Optional[str] = None


class Document(BaseModel):
    model_config = STRICT

    schema_version: Literal["document.v1"] = "document.v1"
    doc_id: str
    project_id: str
    title: str
    source_type: SourceType
    origin: DocumentOrigin
    content_hash: str
    text_path: Optional[str]
    citation_key: str
    ingested_from: Optional[str]
    ingested_at: str


class EvidenceUnit(BaseModel):
    model_config = STRICT

    schema_version: Literal["evidence_unit.v1"] = "evidence_unit.v1"
    evidence_id: str
    project_id: str
    doc_id: str
    location: str
    kind: EvidenceKind
    quote_or_paraphrase: str
    summary: str
    support_direction: SupportDirection
    can_cite_for: list[str]
    cannot_cite_for: list[str]
    scope: Scope
    extracted_by: str
    ingested_from: Optional[str]
    created_at: str


class DocsRequest(BaseModel):
    model_config = STRICT

    schema_version: Literal["docs_request.v1"] = "docs_request.v1"
    request_id: str
    project_id: str
    requested_by: str
    target_id: str
    need: str
    search_hints: list[str]
    fingerprint: str
    status: Literal["open", "fulfilled", "not_found"]
    fulfilled_by: Optional[str]
    created_at: str


class DocsResultDocument(BaseModel):
    model_config = STRICT

    title: str
    source_type: SourceType
    origin: DocumentOrigin
    citation_key: str
    text: Optional[str] = None


class DocsResultEvidence(BaseModel):
    model_config = STRICT

    doc_ref: Optional[int] = None
    doc_id: Optional[str] = None
    location: str
    kind: EvidenceKind
    quote_or_paraphrase: str
    summary: str
    support_direction: SupportDirection
    can_cite_for: list[str]
    cannot_cite_for: list[str]
    scope: Scope


class DocsResult(BaseModel):
    model_config = STRICT

    schema_version: Literal["docs_result.v1"] = "docs_result.v1"
    request_id: str
    project_id: str
    documents: list[DocsResultDocument]
    evidence_units: list[DocsResultEvidence]
    not_found: bool
    search_log: list[str]


QueryOutcome = Literal["productive", "empty", "blocked", "offtopic"]


class QueryLogEntry(BaseModel):
    """One accounted query line (docs/14). ``qid`` refers to a plan query (or an
    ``X<n>`` worker-initiated extra); the worker records what actually happened."""

    model_config = STRICT

    qid: str
    executed: bool
    outcome: QueryOutcome
    urls_seen: int
    docs_taken: int
    note: str


class DocsResultV2(BaseModel):
    """docs_result.v2 (docs/14 adoption): identical to v1 but the structured
    ``query_log`` replaces the free-string ``search_log``. The DocsWorker now
    EMITS v2; v1 stays readable (schema registry keeps both)."""

    model_config = STRICT

    schema_version: Literal["docs_result.v2"] = "docs_result.v2"
    request_id: str
    project_id: str
    documents: list[DocsResultDocument]
    evidence_units: list[DocsResultEvidence]
    not_found: bool
    query_log: list[QueryLogEntry]


class DocsPack(BaseModel):
    model_config = STRICT

    schema_version: Literal["docs_pack.v1"] = "docs_pack.v1"
    pack_id: str
    task_id: str
    project_id: str
    evidence_units: list[dict]
    documents_meta: list[dict]
