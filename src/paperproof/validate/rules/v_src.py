"""V-SRC: source registry, provenance & tiers (docs/16 S3 Stage A-lite + Stage B).

    V-SRC-01  every ingested document carries provenance (retrieved_at,
              fetch_method, tier); tier in enum
    V-SRC-02  secondary_quote documents name quoted_via, and the carrier
              document exists in the archive
    V-SRC-03  registry updates are appends (latest-per-domain wins); the ingestor
              never lowers a tier silently — a tier change carries a note
    V-SRC-04  (Stage B — ADOPTED, docs/16/docs/17) a spine fact/mechanism binding
              profile satisfies the triangulation rule; enforced at freeze
              (extends V-FRZ-02) and reported by msa-check
    V-SRC-05  the dispatch prompt's registry excerpt contains every T1 profile +
              every profile matching a plan facet domain (bundle completeness)

Provenance/tier are STRUCTURAL on document.v2 (the schema requires them), so
V-SRC-01 is enforced by the ingestor writing v2; these functions give the rules a
testable home and a whole-project ``verify`` sweep. document.v1 records predate
the registry and are exempt (they stay readable).
"""

from __future__ import annotations

from typing import Any

from ...paths import Paths
from ...schemas.docs import Tier
from ...store import jsonl
from ..envelope import Failure

DOCUMENTS = "docs/documents.jsonl"

_TIERS = set(Tier.__args__)  # type: ignore[attr-defined]


# --- V-SRC-01 provenance present + tier in enum -----------------------------


def check_document_provenance(doc: dict[str, Any]) -> list[Failure]:
    """V-SRC-01 for one document record. v1 documents are exempt (legacy)."""
    if doc.get("schema_version") != "document.v2":
        return []
    prov = doc.get("provenance")
    if not isinstance(prov, dict):
        return [Failure("V-SRC-01", f"{doc.get('doc_id')}: document.v2 lacks provenance")]
    failures: list[Failure] = []
    for key in ("retrieved_at", "fetch_method", "tier"):
        if not prov.get(key):
            failures.append(Failure("V-SRC-01", f"{doc.get('doc_id')}: provenance missing {key}"))
    if prov.get("tier") not in _TIERS:
        failures.append(Failure("V-SRC-01", f"{doc.get('doc_id')}: tier {prov.get('tier')!r} not in enum"))
    return failures


# --- V-SRC-02 secondary_quote names quoted_via + carrier exists -------------


def check_secondary_quote(doc: dict[str, Any], archived_doc_ids: set[str]) -> list[Failure]:
    """V-SRC-02 for one document record: a secondary_quote document must name a
    quoted_via, and any quoted_via must resolve to an archived carrier."""
    prov = doc.get("provenance") or {}
    if not isinstance(prov, dict):
        return []
    quoted_via = prov.get("quoted_via")
    failures: list[Failure] = []
    if prov.get("fetch_method") == "secondary_quote" and not quoted_via:
        failures.append(Failure("V-SRC-02", f"{doc.get('doc_id')}: secondary_quote names no quoted_via"))
    if quoted_via and quoted_via not in archived_doc_ids:
        failures.append(Failure("V-SRC-02", f"{doc.get('doc_id')}: quoted_via {quoted_via!r} not archived"))
    return failures


# --- V-SRC-03 appends, latest-per-domain, no silent tier change --------------


def check_registry_history(profile_records: list[dict[str, Any]]) -> list[Failure]:
    """V-SRC-03 over the append-ordered SourceProfile history: for each domain,
    consecutive versions whose tier differs must carry a non-empty tier_note (in
    particular, no silent tier-lowering)."""
    failures: list[Failure] = []
    prev_by_domain: dict[str, dict[str, Any]] = {}
    for rec in profile_records:
        domain = rec.get("domain")
        if domain is None:
            continue
        prev = prev_by_domain.get(domain)
        if prev is not None and prev.get("tier") != rec.get("tier"):
            if not (rec.get("tier_note") or "").strip():
                failures.append(
                    Failure(
                        "V-SRC-03",
                        f"{domain}: tier {prev.get('tier')} -> {rec.get('tier')} "
                        f"without a note (silent tier change)",
                    )
                )
        prev_by_domain[domain] = rec
    return failures


# --- V-SRC-04 spine-binding triangulation (Stage B, docs/16) ----------------


def check_triangulation(binding_docmeta: list[tuple[str, str, str]]) -> list[Failure]:
    """V-SRC-04 for one spine fact/mechanism binding profile. ``binding_docmeta``
    is (tier, publisher, doc_id) per binding EU. Returns a Failure iff the profile
    does not triangulate (docs/16): (a) >=1 EU from a T1/T2 doc + >=1 more from a
    distinct doc, OR (b) >=2 EUs from distinct independent T3/T4 docs (different
    publishers). T5 press never carries a spine binding alone."""
    from ...docsdb import coverage as _coverage

    if _coverage.triangulated(binding_docmeta):
        return []
    return [Failure("V-SRC-04", "spine binding profile does not triangulate (docs/16)")]


# --- V-SRC-05 dispatch excerpt completeness ---------------------------------


def check_registry_excerpt(
    all_profiles: list[dict[str, Any]],
    facet_text: str,
    excerpt_source_ids: set[str],
) -> list[Failure]:
    """V-SRC-05: the excerpt must contain every T1 profile + every profile whose
    domain/publisher matches a request facet. ``all_profiles`` = latest-per-domain
    registry; ``facet_text`` = lower-cased need+hints+scope."""
    from ...docsdb import registry as _registry  # local: avoid import cycle

    failures: list[Failure] = []
    for p in all_profiles:
        if _registry.profile_matches_facets(p, facet_text) and p.get("source_id") not in excerpt_source_ids:
            failures.append(
                Failure("V-SRC-05", f"dispatch excerpt missing required profile {p.get('source_id')} ({p.get('domain')})")
            )
    return failures


# --- whole-project sweep (paperproof verify) --------------------------------


def verify_sources(paths: Paths) -> list[Failure]:
    """V-SRC-01/02/03 over stored documents + the registry (docs/09 §3 style)."""
    from ...docsdb import registry as _registry

    docs = jsonl.latest_records(paths.resolve(DOCUMENTS), "doc_id")
    archived = {d.get("doc_id") for d in docs}
    failures: list[Failure] = []
    for d in docs:
        failures += check_document_provenance(d)
        failures += check_secondary_quote(d, archived)
    failures += check_registry_history(_registry.load_all(paths))
    return failures
