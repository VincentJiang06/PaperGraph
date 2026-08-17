"""V-SWEEP-01 contract test (docs/04 §Evidence Seeding, docs/09 §V-SWEEP).

The first expansion beyond layer 0 is REFUSED while a fact/mechanism layer-0
(seed) node lacks the sweep floor, and PASSES once the floor is met — either by
>=2 EvidenceUnits from >=2 distinct documents requested-for-it, or by >=2
recorded not_found sweep angles. `graph msa-check` reports coverage
informationally (never a pass/fail MSA item).

The graph is constructed directly (append records + snapshot) so V-SWEEP-01 is the
only thing under test — no open work items, so V-EXP-01 passes and the sweep gate
is reached.
"""

from __future__ import annotations

import pytest

from paperproof.errors import DomainError
from paperproof.expander import ingest as expander
from paperproof.graph import commands as graph_commands
from paperproof.paths import paths_for
from paperproof.store import jsonl, snapshot

from tests.fakes import scenario

pytestmark = pytest.mark.contract

NODES = "graph/logic_nodes.jsonl"
EVIDENCE_UNITS = "docs/evidence_units.jsonl"
DOCS_REQUESTS = "docs/docs_requests.jsonl"

SEED = "NODE-003"  # the layer-0 fact seed node under test


def _paths(pp):
    return paths_for(pp.tmp_path, "p4-ldi")


def _node(node_id, node_type):
    return {
        "schema_version": "logic_node.v1", "node_id": node_id, "project_id": "p4-ldi",
        "bfs_id": "BFS-MAIN", "layer": 0, "claim": f"Seed claim for {node_id}.", "claim_version": 1,
        "node_type": node_type, "scope": {}, "parents": [], "origin": {"kind": "seed", "source": "topic-input"},
        "lifecycle_state": "active", "state_reason": None, "state_detail": None, "strength": "strong",
        "language_limits": {"allowed": ["a"], "forbidden": ["b"]}, "assumptions": [], "evidence_bindings": [],
        "latest_proof_result_id": "PR-001", "frozen": False, "created_at": "2026-07-07T00:00:00Z",
    }


def _eu(evidence_id, doc_id, dres):
    return {"schema_version": "evidence_unit.v1", "evidence_id": evidence_id, "project_id": "p4-ldi",
            "doc_id": doc_id, "ingested_from": dres, "created_at": "2026-07-07T00:00:00Z"}


def _request(request_id, target_id, status, fulfilled_by):
    return {"schema_version": "docs_request.v1", "request_id": request_id, "project_id": "p4-ldi",
            "requested_by": "orchestrator", "target_id": target_id, "need": "seed sweep",
            "search_hints": [], "fingerprint": f"sha256:{request_id}", "status": status,
            "fulfilled_by": fulfilled_by, "created_at": "2026-07-07T00:00:00Z"}


def _seed_layer0_direct(paths, *, eus=(), requests=()):
    """Q, T and a layer-0 fact seed node (NODE-003), all active; plus the given
    EvidenceUnit + DocsRequest rows. No work items, so only the sweep gate can
    block the layer-1 expansion."""
    jsonl.append(paths.resolve(NODES), _node("NODE-001", "question"))
    jsonl.append(paths.resolve(NODES), _node("NODE-002", "thesis"))
    jsonl.append(paths.resolve(NODES), _node(SEED, "fact"))
    for eu in eus:
        jsonl.append(paths.resolve(EVIDENCE_UNITS), eu)
    for r in requests:
        jsonl.append(paths.resolve(DOCS_REQUESTS), r)
    snapshot.take_snapshot(paths)


def _layer1(paths):
    """`expand ingest` a minimal layer-1 proposal (one definition child of the
    seed). Raises DomainError on refusal."""
    return scenario.ingest_expansion(
        paths, "EXP-BFS-MAIN-L1", "BFS-MAIN", 1,
        nodes=[{"claim": "A layer-1 conceptual distinction.", "node_type": "definition", "scope": {}, "parents": [SEED]}],
        edges=[],
    )


def test_v_sweep_01_refuses_expansion_below_floor(project, pp):
    """One EU from one document requested-for the seed is below the floor ->
    the first layer-1 expansion is refused with V-SWEEP-01."""
    paths = _paths(pp)
    _seed_layer0_direct(
        paths,
        eus=[_eu("EU-001", "DOC-001", "DRES-001")],
        requests=[_request("DR-001", SEED, "fulfilled", "DRES-001")],
    )

    # msa-check reports the seed as uncovered (informational, not a pass/fail item).
    cov = graph_commands.msa_check(paths)["sweep_coverage"]
    assert cov["seed_fact_mechanism_nodes"] == [SEED]
    assert cov["uncovered"] == [SEED] and cov["all_covered"] is False

    with pytest.raises(DomainError) as exc:
        _layer1(paths)
    assert "V-SWEEP-01" in exc.value.errors


def test_v_sweep_01_passes_after_two_eu_from_two_docs(project, pp):
    """>=2 EU from >=2 distinct documents requested-for the seed meets the floor
    -> the layer-1 expansion commits."""
    paths = _paths(pp)
    _seed_layer0_direct(
        paths,
        eus=[_eu("EU-001", "DOC-001", "DRES-001"), _eu("EU-002", "DOC-002", "DRES-001")],
        requests=[_request("DR-001", SEED, "fulfilled", "DRES-001")],
    )
    cov = graph_commands.msa_check(paths)["sweep_coverage"]
    assert cov["covered"] == [SEED] and cov["all_covered"] is True

    res = _layer1(paths)
    assert res["commit_id"]  # committed, not refused


def test_v_sweep_01_two_eu_same_document_still_refused(project, pp):
    """Two EvidenceUnits from the SAME document do not meet the >=2-distinct-docs
    floor -> still refused."""
    paths = _paths(pp)
    _seed_layer0_direct(
        paths,
        eus=[_eu("EU-001", "DOC-001", "DRES-001"), _eu("EU-002", "DOC-001", "DRES-001")],
        requests=[_request("DR-001", SEED, "fulfilled", "DRES-001")],
    )
    with pytest.raises(DomainError) as exc:
        _layer1(paths)
    assert "V-SWEEP-01" in exc.value.errors


def test_v_sweep_01_passes_after_two_not_found_angles(project, pp):
    """>=2 sweep DocsRequests targeting the seed recorded not_found also meets the
    floor -> the layer-1 expansion commits."""
    paths = _paths(pp)
    _seed_layer0_direct(
        paths,
        requests=[
            _request("DR-001", SEED, "not_found", "DRES-001"),
            _request("DR-002", SEED, "not_found", "DRES-002"),
        ],
    )
    cov = graph_commands.msa_check(paths)["sweep_coverage"]
    assert cov["all_covered"] is True

    res = _layer1(paths)
    assert res["commit_id"]


def test_v_sweep_01_not_enforced_when_no_fact_mechanism_seed(project, pp):
    """A layer-0 with only definition seeds has no fact/mechanism seed claim, so
    the sweep floor is vacuously satisfied (definitions are not empirical)."""
    paths = _paths(pp)
    jsonl.append(paths.resolve(NODES), _node("NODE-001", "question"))
    jsonl.append(paths.resolve(NODES), _node("NODE-002", "thesis"))
    defn = _node(SEED, "definition")
    jsonl.append(paths.resolve(NODES), defn)
    snapshot.take_snapshot(paths)

    cov = graph_commands.msa_check(paths)["sweep_coverage"]
    assert cov["seed_fact_mechanism_nodes"] == []
    res = _layer1(paths)
    assert res["commit_id"]
