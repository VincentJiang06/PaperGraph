"""V-SWEEP: evidence-seeding floor (docs/04 §Evidence Seeding step 4, docs/09).

V-SWEEP-01  the first expansion beyond layer 0 requires, for every fact/mechanism
            LAYER-0 node N: >=2 EvidenceUnits from >=2 distinct documents that are
            REQUESTED-for-N, OR a recorded not_found for >=2 sweep DocsRequests
            targeting N.

Doc-sync note (docs/04 step 4): the spec phrases the floor as "every fact/mechanism
seed CLAIM"; this rule operationalizes a seed claim as a LAYER-0 fact/mechanism
NODE — a raw seed string has no node_type to test mechanically, and seed claims
become the layer-0 nodes. Enforced by ``expand ingest`` on the first proposal
whose ``layer >= 1``; ``graph msa-check`` reports coverage informationally (never a
new pass/fail MSA item).
"""

from __future__ import annotations

from typing import Any

from ...graph import model as graph_model
from ...paths import Paths
from ...store import jsonl
from ..envelope import Failure

EVIDENCE_UNITS = "docs/evidence_units.jsonl"
DOCS_REQUESTS = "docs/docs_requests.jsonl"


def seed_fact_mechanism_nodes(gv: graph_model.GraphView) -> list[dict[str, Any]]:
    """Layer-0 fact/mechanism nodes (the operationalized seed claims)."""
    return [
        n
        for n in gv.nodes
        if n.get("layer") == 0
        and n.get("node_type") in ("fact", "mechanism")
        and n.get("lifecycle_state") != "rejected"
    ]


def node_meets_floor(
    paths: Paths,
    node: dict[str, Any],
    eus: list[dict[str, Any]] | None = None,
    requests: list[dict[str, Any]] | None = None,
) -> bool:
    """The sweep floor for one seed node N: (>=2 EU from >=2 distinct docs
    REQUESTED-for-N) OR (>=2 sweep DocsRequests targeting N recorded not_found)."""
    from ...docsdb import pack as docs_pack  # local: avoid import cycle at load

    if eus is None:
        eus = jsonl.latest_records(paths.resolve(EVIDENCE_UNITS), "evidence_id")
    requested = docs_pack._requested_eus(paths, node["node_id"], eus)
    distinct_docs = {eu["doc_id"] for eu in requested if eu.get("doc_id")}
    if len(requested) >= 2 and len(distinct_docs) >= 2:
        return True

    if requests is None:
        requests = jsonl.latest_records(paths.resolve(DOCS_REQUESTS), "request_id")
    not_found = [
        r for r in requests
        if r.get("target_id") == node["node_id"] and r.get("status") == "not_found"
    ]
    return len(not_found) >= 2


def coverage(paths: Paths, gv: graph_model.GraphView) -> dict[str, Any]:
    """Informational sweep coverage for ``graph msa-check`` (NOT a pass/fail item)."""
    eus = jsonl.latest_records(paths.resolve(EVIDENCE_UNITS), "evidence_id")
    requests = jsonl.latest_records(paths.resolve(DOCS_REQUESTS), "request_id")
    seeds = seed_fact_mechanism_nodes(gv)
    per = {n["node_id"]: node_meets_floor(paths, n, eus, requests) for n in seeds}
    covered = sorted(k for k, v in per.items() if v)
    uncovered = sorted(k for k, v in per.items() if not v)
    return {
        "seed_fact_mechanism_nodes": sorted(per),
        "covered": covered,
        "uncovered": uncovered,
        "all_covered": all(per.values()),
    }


def check_sweep_floor(paths: Paths, gv: graph_model.GraphView) -> list[Failure]:
    """V-SWEEP-01: one Failure per seed fact/mechanism node below the floor."""
    eus = jsonl.latest_records(paths.resolve(EVIDENCE_UNITS), "evidence_id")
    requests = jsonl.latest_records(paths.resolve(DOCS_REQUESTS), "request_id")
    failures: list[Failure] = []
    for n in seed_fact_mechanism_nodes(gv):
        if not node_meets_floor(paths, n, eus, requests):
            failures.append(
                Failure(
                    "V-SWEEP-01",
                    f"seed {n['node_id']} lacks the sweep floor "
                    f"(needs >=2 EU/>=2 docs requested-for-it, or >=2 not_found angles)",
                )
            )
    return failures
