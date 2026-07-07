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


def _target_claim_scope(target_record: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """A node target uses (claim, scope); an edge target uses (edge_claim, {})."""
    if "edge_id" in target_record:
        return target_record.get("edge_claim", "") or "", {}
    return target_record.get("claim", "") or "", target_record.get("scope", {}) or {}


def assemble(paths: Paths, target_record: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (evidence_units, documents_meta) for a target via the matcher.

    Deterministic: matcher order is (score desc, evidence_id asc); documents_meta
    follows first-citation order of the selected EvidenceUnits.
    """
    claim, scope = _target_claim_scope(target_record)
    eus = jsonl.latest_records(paths.resolve(EVIDENCE_UNITS), "evidence_id")
    selected = [eu for _s, eu in matcher.match(claim, scope, eus)]

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
