"""DocsPack assembly (docs/04, docs/08 B4).

The DocsPack builder is the producer of ``docs/docspacks/*.json``. It assembles
the EvidenceUnits the matcher selects for a target claim plus their documents'
metadata. An empty DocsPack is valid — it just means the worker cannot answer
``evidence_check=sufficient`` and routes to needs_docs on evidence-requiring
targets.
"""

from __future__ import annotations

from typing import Any

from ..paths import Paths
from ..store import jsonl
from . import matcher

EVIDENCE_UNITS = "docs/evidence_units.jsonl"
DOCUMENTS = "docs/documents.jsonl"
DOCS_REQUESTS = "docs/docs_requests.jsonl"

# docs/04 r3: pack(target) = REQUESTED U top-K(MATCHED). K bounds the matched
# half only -- requested evidence is unconditional.
MATCHED_K = 12


def _target_claim_scope(target_record: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """A node target uses (claim, scope); an edge target uses (edge_claim, {})."""
    if "edge_id" in target_record:
        return target_record.get("edge_claim", "") or "", {}
    return target_record.get("claim", "") or "", target_record.get("scope", {}) or {}


def _requested_eus(paths: Paths, target_id: str, eus: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every EU ingested from a DocsRequest whose target_id is this record
    (request -> DRES -> ingested_from). Included UNCONDITIONALLY (docs/04 r3):
    in the live run, evidence fetched FOR a target only reached its pack via
    matcher luck on common tokens."""
    dres_ids = {
        r.get("fulfilled_by")
        for r in jsonl.latest_records(paths.resolve(DOCS_REQUESTS), "request_id")
        if r.get("target_id") == target_id
        and str(r.get("fulfilled_by") or "").startswith("DRES-")
    }
    return sorted(
        (eu for eu in eus if eu.get("ingested_from") in dres_ids),
        key=lambda e: e["evidence_id"],
    )


def assemble(paths: Paths, target_record: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (evidence_units, documents_meta) for a target (docs/04 r3):
    pack = REQUESTED (unconditional, evidence_id asc) followed by the top-K
    MATCHED (matcher order: score desc, evidence_id asc; minus requested).
    documents_meta follows first-citation order of the selected units.
    """
    claim, scope = _target_claim_scope(target_record)
    target_id = target_record.get("edge_id") or target_record.get("node_id") or ""
    eus = jsonl.latest_records(paths.resolve(EVIDENCE_UNITS), "evidence_id")
    requested = _requested_eus(paths, target_id, eus)
    requested_ids = {eu["evidence_id"] for eu in requested}
    matched = [
        eu for _s, eu in matcher.match(claim, scope, eus)
        if eu["evidence_id"] not in requested_ids
    ][:MATCHED_K]
    selected = requested + matched

    doc_by_id = {d["doc_id"]: d for d in jsonl.latest_records(paths.resolve(DOCUMENTS), "doc_id")}
    documents_meta: list[dict[str, Any]] = []
    seen: set[str] = set()
    for eu in selected:
        did = eu.get("doc_id")
        if did and did not in seen and did in doc_by_id:
            seen.add(did)
            documents_meta.append(doc_by_id[did])
    return selected, documents_meta


def search(paths: Paths, query: str, scope: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """`docs search`: the matcher as a scored EvidenceUnit list."""
    eus = jsonl.latest_records(paths.resolve(EVIDENCE_UNITS), "evidence_id")
    return [
        {"score": s, "evidence_id": eu["evidence_id"], "doc_id": eu.get("doc_id"), "evidence_unit": eu}
        for s, eu in matcher.match(query, scope or {}, eus)
    ]
