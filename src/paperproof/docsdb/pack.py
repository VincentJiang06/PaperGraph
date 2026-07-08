"""DocsPack assembly (docs/04, docs/08 B4; S5 hybrid retrieval docs/18).

The DocsPack builder is the producer of ``docs/docspacks/*.json``. It assembles
the EvidenceUnits selected for a target claim plus their documents' metadata. An
empty DocsPack is valid — it just means the worker cannot answer
``evidence_check=sufficient`` and routes to needs_docs on evidence-requiring
targets.

Two matchers, one composition rule. When the pinned embedding model + index are
present the MATCHED half is scored HYBRID (0.6·sscore + 0.4·kscore) and
near-duplicates within a document collapse to one representative; otherwise it
degrades to the keyword matcher LOUDLY (docs/18 V-SEM-03). Either way
``pack = REQUESTED ∪ top-12 MATCHED`` (the r3 rule is UNCHANGED — semantic scoring
feeds the matched half's SCORE only).
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


def _documents_meta(
    selected: list[dict[str, Any]],
    doc_by_id: dict[str, dict[str, Any]],
    also_map: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """documents_meta in first-citation order of the selected units. A document
    that owns a near-dup cluster representative carries a ``near_dups`` annotation
    listing the collapsed EUs (V-SEM-05: "also: EU-x")."""
    # rep_evidence_id -> doc_id, so we can attach cluster info to the right doc.
    rep_doc: dict[str, str] = {}
    for eu in selected:
        if eu["evidence_id"] in also_map:
            rep_doc[eu["evidence_id"]] = eu.get("doc_id")
    doc_clusters: dict[str, list[dict[str, Any]]] = {}
    for rep_id, others in also_map.items():
        did = rep_doc.get(rep_id)
        if did is not None:
            doc_clusters.setdefault(did, []).append({"representative": rep_id, "also": others})

    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for eu in selected:
        did = eu.get("doc_id")
        if did and did not in seen and did in doc_by_id:
            seen.add(did)
            meta = dict(doc_by_id[did])
            if did in doc_clusters:
                meta["near_dups"] = doc_clusters[did]
            out.append(meta)
    return out


def _fmt6(x: float) -> str:
    """Fixed-6-decimal string — byte-determinism for the retrieval block (docs/18)."""
    return f"{float(x):.6f}"


def assemble(paths: Paths, target_record: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Keyword-only assembly (docs/04 r3): pack = REQUESTED (unconditional,
    evidence_id asc) followed by the top-K keyword-MATCHED (score desc,
    evidence_id asc; minus requested). Retained for the degrade path and callers
    that only need the (evidence_units, documents_meta) pair."""
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
    return selected, _documents_meta(selected, doc_by_id, {})


def assemble_v2(
    paths: Paths, target_record: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], list[str]]:
    """Hybrid-aware assembly (docs/18). Returns
    (evidence_units, documents_meta, retrieval, warnings).

    Hybrid when the pinned model + eu_vectors index are present: the matched half
    is scored 0.6·sscore + 0.4·kscore, included iff (sscore≥0.35 OR raw-keyword≥2),
    near-dups within a document collapse (V-SEM-05). Otherwise degrades to keyword
    LOUDLY (a warning, matcher=keyword.v1 — V-SEM-03). Composition is unchanged:
    REQUESTED ∪ top-12 MATCHED."""
    from ..db import semantic  # local import: never a base dependency

    claim, scope = _target_claim_scope(target_record)
    target_id = target_record.get("edge_id") or target_record.get("node_id") or ""
    eus = jsonl.latest_records(paths.resolve(EVIDENCE_UNITS), "evidence_id")
    requested = _requested_eus(paths, target_id, eus)
    requested_ids = {eu["evidence_id"] for eu in requested}
    doc_by_id = {d["doc_id"]: d for d in jsonl.latest_records(paths.resolve(DOCUMENTS), "doc_id")}

    warnings: list[str] = []
    scores_by_id: dict[str, dict[str, float]] = {}
    also_map: dict[str, list[str]] = {}

    if semantic.model_present(paths):
        eu_vectors = semantic.load_vectors(paths)
        claim_vec = semantic.embed_claim(paths, claim)
        included, scores_by_id = matcher.hybrid_score(claim, scope, eus, eu_vectors, claim_vec)
        matched_all = [eu for _s, eu in included if eu["evidence_id"] not in requested_ids]
        kept, also_map = matcher.cluster_near_dups(matched_all, eu_vectors)
        matched = kept[:MATCHED_K]
        matcher_name = "hybrid.v1"
        model = semantic.model_pin()
    else:
        matched = [
            eu for _s, eu in matcher.match(claim, scope, eus)
            if eu["evidence_id"] not in requested_ids
        ][:MATCHED_K]
        matcher_name = "keyword.v1"
        model = None
        if not semantic.deps_available():
            warnings.append(
                "V-SEM-03: semantic deps absent — retrieval DEGRADED to keyword.v1 "
                "(install `.[semantic]` then `db semantic rebuild`)"
            )
        else:
            warnings.append(
                "V-SEM-03: semantic model/index absent — retrieval DEGRADED to keyword.v1 "
                "(run `db semantic rebuild`)"
            )

    selected = requested + matched
    documents_meta = _documents_meta(selected, doc_by_id, also_map)

    scores = [
        {"evidence_id": eu["evidence_id"],
         "sscore": _fmt6(scores_by_id[eu["evidence_id"]]["sscore"]),
         "kscore": _fmt6(scores_by_id[eu["evidence_id"]]["kscore"])}
        for eu in selected
        if eu["evidence_id"] in scores_by_id
    ]
    retrieval = {
        "matcher": matcher_name,
        "model": model,
        "alpha": "0.6",
        "tau": "0.35",
        "scores": scores,
    }
    return selected, documents_meta, retrieval, warnings


def search(
    paths: Paths, query: str, scope: dict[str, Any] | None = None, semantic_flag: bool = False
) -> dict[str, Any]:
    """`docs search`: the matcher as a scored EvidenceUnit list. With
    ``--semantic`` (docs/18) and the pinned model present, results are ranked by
    the hybrid score and carry sscore/kscore; otherwise (or when semantic is
    unavailable) the keyword matcher ranks them and a degrade warning is set."""
    eus = jsonl.latest_records(paths.resolve(EVIDENCE_UNITS), "evidence_id")
    scope = scope or {}
    if not semantic_flag:
        return {
            "matcher": "keyword.v1",
            "results": [
                {"score": s, "evidence_id": eu["evidence_id"], "doc_id": eu.get("doc_id"), "evidence_unit": eu}
                for s, eu in matcher.match(query, scope, eus)
            ],
        }

    from ..db import semantic  # local import

    if not semantic.model_present(paths):
        warn = (
            "V-SEM-03: semantic deps absent — falling back to keyword search"
            if not semantic.deps_available()
            else "V-SEM-03: semantic model/index absent — falling back to keyword search (run `db semantic rebuild`)"
        )
        return {
            "matcher": "keyword.v1",
            "results": [
                {"score": s, "evidence_id": eu["evidence_id"], "doc_id": eu.get("doc_id"), "evidence_unit": eu}
                for s, eu in matcher.match(query, scope, eus)
            ],
            "warnings": [warn],
        }

    eu_vectors = semantic.load_vectors(paths)
    claim_vec = semantic.embed_claim(paths, query)
    included, scores_by_id = matcher.hybrid_score(query, scope, eus, eu_vectors, claim_vec)
    results = []
    for sc, eu in included:
        sid = scores_by_id[eu["evidence_id"]]
        results.append({
            "score": _fmt6(sc), "sscore": _fmt6(sid["sscore"]), "kscore": _fmt6(sid["kscore"]),
            "evidence_id": eu["evidence_id"], "doc_id": eu.get("doc_id"), "evidence_unit": eu,
        })
    return {"matcher": "hybrid.v1", "model": semantic.model_pin(), "results": results}
