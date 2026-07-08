"""Docs family: document.v1, evidence_unit.v1, docs_request.v1, docs_result.v1,
docs_pack.v1 (docs/04, docs/08 B7)."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

from ._common import STRICT, Scope

# A field literally named ``model`` collides with pydantic's protected ``model_``
# namespace guard; disable it for the retrieval block only (docs/18 pins the JSON
# key ``model`` for the embedding-model pin).
STRICT_MODEL_OK = ConfigDict(extra="forbid", protected_namespaces=())

SourceType = Literal[
    "peer_reviewed", "official_report", "working_paper", "news", "dataset", "user_notes"
]
SupportDirection = Literal["supports", "refutes", "context"]
EvidenceKind = Literal["quote", "paraphrase"]

# S3 Stage A-lite (docs/16). Source tier enum (closed) and the fetch-recipe /
# provenance vocabulary. WorkaroundKind is the lawful public-access recipe set;
# FetchMethod is that set plus "direct" (how a document's text actually arrived).
Tier = Literal[
    "T1_official", "T2_peer_reviewed", "T3_working_paper",
    "T4_industry_data", "T5_press", "T6_other",
]
WorkaroundKind = Literal["mirror", "archive_org", "secondary_quote", "pdf_local_extract", "api"]
FetchMethod = Literal["direct", "mirror", "archive_org", "secondary_quote", "pdf_local_extract", "api"]


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


class Provenance(BaseModel):
    """document.v2 provenance block (docs/16): how a figure entered the project.

    tier is denormalized at ingest (registry lookup, worker-proposed on first
    sight); fetch_method is how THIS document's text arrived; quoted_via links a
    secondary_quote document to the carrier that was actually fetched.
    """

    model_config = STRICT

    retrieved_at: str
    fetch_method: FetchMethod
    tier: Tier
    quoted_via: Optional[str] = None


class DocumentV2(BaseModel):
    """document.v2 = document.v1 + a provenance block (docs/16).

    document.v1 stays registered and READABLE; the ingestor writes v2 going
    forward. Field order appends provenance to the v1 shape.
    """

    model_config = STRICT

    schema_version: Literal["document.v2"] = "document.v2"
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
    provenance: Provenance


class SourceWorkaround(BaseModel):
    """One lawful public-access fetch recipe for a domain (docs/16)."""

    model_config = STRICT

    kind: WorkaroundKind
    note: str


class SourceFetch(BaseModel):
    model_config = STRICT

    blocked_direct: bool = False
    workarounds: list[SourceWorkaround] = []


class SourceProfile(BaseModel):
    """source_profile.v1 (`docs/sources.jsonl`, docs/16): the project's durable
    memory of where evidence lives, how to fetch it, and how much it counts.

    Append-only, latest-per-domain. The ingestor LEARNS a new version on every
    ingested Document; `docs source set` appends human curation. ``tier_note``
    carries the reason for any tier change (V-SRC-03: no silent tier-lowering).
    """

    model_config = STRICT

    schema_version: Literal["source_profile.v1"] = "source_profile.v1"
    source_id: str
    project_id: str
    domain: str
    publisher: str = ""
    tier: Tier
    fetch: SourceFetch = SourceFetch()
    seen_count: int = 0
    last_ok_fetch_method: Optional[FetchMethod] = None
    tier_note: Optional[str] = None
    created_at: str


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
    # S2 (docs/15): fan the request into a per-angle wave. r3 sweep requests
    # default fan=true; reactive needs_docs / `docs request` default single.
    fan: bool = False


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


# --- S5 semantic retrieval (docs/18): docs_pack.v2 -------------------------


class RetrievalModel(BaseModel):
    """The project-pinned embedding model, recorded in every hybrid pack
    (V-SEM-01): name + revision + weights sha256 make the vector reproducible."""

    model_config = STRICT

    name: str
    revision: str
    weights_sha256: str


class RetrievalScore(BaseModel):
    """Per-EU hybrid scores. Serialized as fixed-6-decimal STRINGS so the pack is
    byte-identical across platforms (docs/18) — no float drift in canonical bytes.
    ``kscore`` is the min-max-normalized keyword score used in the weighted sum."""

    model_config = STRICT

    evidence_id: str
    sscore: str
    kscore: str


class RetrievalBlock(BaseModel):
    """docs_pack.v2 audit block (docs/18): how the pack was retrieved. ``matcher``
    is ``hybrid.v1`` (embeddings present) or ``keyword.v1`` (degrade path,
    V-SEM-03). ``model`` is present iff hybrid. ``alpha``/``tau`` pin the contract
    constants as strings (byte-determinism)."""

    model_config = STRICT_MODEL_OK

    matcher: Literal["hybrid.v1", "keyword.v1"]
    model: Optional[RetrievalModel] = None
    alpha: str = "0.6"
    tau: str = "0.35"
    scores: list[RetrievalScore] = []


class DocsPackV2(BaseModel):
    """docs_pack.v2 = docs_pack.v1 + a ``retrieval`` audit block (docs/18). v1
    stays registered and READABLE; the builder writes v2 going forward. The pack
    remains explainable: every hybrid pack names its model and carries per-EU
    sscore/kscore. documents_meta may carry a ``near_dups`` annotation
    (representative EU + within-document also-EUs, V-SEM-05)."""

    model_config = STRICT

    schema_version: Literal["docs_pack.v2"] = "docs_pack.v2"
    pack_id: str
    task_id: str
    project_id: str
    evidence_units: list[dict]
    documents_meta: list[dict]
    retrieval: RetrievalBlock
