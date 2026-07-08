"""V-FRZ contract tests (docs/09, docs/11 §2).

Each V-FRZ precondition violated => refusal; the language-limit union is correct;
unfreeze re-opens the affected proofs. Degenerate graph states are constructed
directly (append records + snapshot), so each rule is isolated.
"""

from __future__ import annotations

import pytest

from paperproof.errors import DomainError
from paperproof.freeze import apply as freeze
from paperproof.graph import commands as graph_commands
from paperproof.graph import model as graph_model
from paperproof.paths import paths_for
from paperproof.queue import engine
from paperproof.store import jsonl, snapshot

pytestmark = pytest.mark.contract

NODES = "graph/logic_nodes.jsonl"
EDGES = "graph/logic_edges.jsonl"
EVIDENCE_UNITS = "docs/evidence_units.jsonl"
DOCUMENTS = "docs/documents.jsonl"
DOCS_REQUESTS = "docs/docs_requests.jsonl"


def _node(node_id, *, node_type="mechanism", state="active", frozen=False, evidence=None, ll=None, scope=None):
    return {
        "schema_version": "logic_node.v1", "node_id": node_id, "project_id": "p4-ldi",
        "bfs_id": "BFS-MAIN", "layer": 1, "claim": f"Claim for {node_id}.", "claim_version": 1,
        "node_type": node_type, "scope": scope or {}, "parents": [], "origin": {"kind": "seed", "source": "topic-input"},
        "lifecycle_state": state, "state_reason": None, "state_detail": None,
        "strength": "strong" if state == "active" else "unassessed",
        "language_limits": ll, "assumptions": [], "evidence_bindings": list(evidence or []),
        "latest_proof_result_id": "PR-001" if state == "active" else None, "frozen": frozen,
        "created_at": "2026-07-07T00:00:00Z",
    }


def _seed(paths, nodes):
    for n in nodes:
        jsonl.append(paths.resolve(NODES), n)
    snapshot.take_snapshot(paths)


def _paths(pp):
    return paths_for(pp.tmp_path, "p4-ldi")


def test_v_frz_01_non_active_refused(project, pp):
    paths = _paths(pp)
    _seed(paths, [_node("NODE-001", node_type="definition", state="pending_proof")])
    with pytest.raises(DomainError) as exc:
        freeze.apply(paths, "NODE-001", "local")
    assert "V-FRZ-01" in exc.value.errors


def test_v_frz_02_missing_evidence_refused(project, pp):
    paths = _paths(pp)
    # active mechanism with no evidence binding -> V-FRZ-02.
    _seed(paths, [_node("NODE-001", node_type="mechanism", state="active", evidence=[], ll={"allowed": ["a"], "forbidden": ["b"]})])
    with pytest.raises(DomainError) as exc:
        freeze.apply(paths, "NODE-001", "local")
    assert "V-FRZ-02" in exc.value.errors


# --- S4: the spine floor is the role profile (>=2 EU, >=2 docs, TRIANGULATED,
#     counter attempted) -- STRICTER than the superseded flat >=2 rule (docs/17).


def _edge(edge_id, src, tgt):
    return {
        "schema_version": "logic_edge.v1", "edge_id": edge_id, "project_id": "p4-ldi",
        "source_node_id": src, "target_node_id": tgt, "edge_type": "supports",
        "edge_claim": f"{src} supports {tgt}.", "claim_version": 1, "lifecycle_state": "active",
        "state_reason": None, "state_detail": None, "strength": "strong", "language_limits": {"allowed": ["a"], "forbidden": ["b"]},
        "assumptions": [], "frozen": False, "latest_proof_result_id": "PR-001", "created_at": "2026-07-07T00:00:00Z",
    }


def _eu(evidence_id, doc_id, direction="supports"):
    return {"schema_version": "evidence_unit.v1", "evidence_id": evidence_id, "project_id": "p4-ldi",
            "doc_id": doc_id, "support_direction": direction}


def _doc(doc_id, source_type, url, tier):
    return {"schema_version": "document.v2", "doc_id": doc_id, "project_id": "p4-ldi",
            "source_type": source_type, "origin": {"kind": "web", "path": None, "url": url},
            "provenance": {"retrieved_at": "2026-07-07T00:00:00Z", "fetch_method": "direct", "tier": tier, "quoted_via": None}}


def _fulfilled_request(target_id, dres="DRES-001"):
    """A completed docs search targeting the node: every S1 plan runs a counter
    query (V-SP-02), so a fulfilled search makes the counter angle attempted."""
    return {"schema_version": "docs_request.v1", "request_id": "DR-001", "project_id": "p4-ldi",
            "requested_by": "orchestrator", "target_id": target_id, "need": "n", "search_hints": [],
            "fingerprint": "fp", "status": "fulfilled", "fulfilled_by": dres, "created_at": "2026-07-07T00:00:00Z"}


def _seed_spine_with_mechanism(paths, *, evidence, eu_docs, documents=None, searched=True):
    """A minimal active spine {Q, T, M(mechanism), T->Q, M->T} plus the given
    EvidenceUnit->doc rows (and optional Document tier rows + a completed search),
    so MSA-4 / V-FRZ-02 see a spine mechanism node whose only defect is the floor."""
    ll = {"allowed": ["a"], "forbidden": ["b"]}
    for d in documents or []:
        jsonl.append(paths.resolve(DOCUMENTS), d)
    for eid, did in eu_docs:
        jsonl.append(paths.resolve(EVIDENCE_UNITS), _eu(eid, did))
    if searched:
        jsonl.append(paths.resolve(DOCS_REQUESTS), _fulfilled_request("NODE-003"))
    jsonl.append(paths.resolve(NODES), _node("NODE-001", node_type="question", state="active", ll=ll))
    jsonl.append(paths.resolve(NODES), _node("NODE-002", node_type="thesis", state="active", ll=ll))
    jsonl.append(paths.resolve(NODES), _node("NODE-003", node_type="mechanism", state="active", evidence=evidence, ll=ll))
    jsonl.append(paths.resolve(EDGES), _edge("EDGE-002-001", "NODE-002", "NODE-001"))
    jsonl.append(paths.resolve(EDGES), _edge("EDGE-003-002", "NODE-003", "NODE-002"))
    snapshot.take_snapshot(paths)


# T1 + distinct T4 documents => triangulation rule (a) holds.
_TRI_DOCS = [
    _doc("DOC-001", "official_report", "https://boe.example/a", "T1_official"),
    _doc("DOC-002", "dataset", "https://adp.example/b", "T4_industry_data"),
]
# Two T3 working papers from the SAME publisher (domain) => not independent.
_SAME_PUB_T3 = [
    _doc("DOC-001", "working_paper", "https://ssrn.example/a", "T3_working_paper"),
    _doc("DOC-002", "working_paper", "https://ssrn.example/b", "T3_working_paper"),
]


@pytest.mark.parametrize(
    "evidence, eu_docs, documents, label",
    [
        (["EU-001"], [("EU-001", "DOC-001")], _TRI_DOCS, "one_binding"),
        (["EU-001", "EU-002"], [("EU-001", "DOC-001"), ("EU-002", "DOC-001")], _TRI_DOCS, "two_eu_same_doc"),
        (["EU-001", "EU-002"], [("EU-001", "DOC-001"), ("EU-002", "DOC-002")], _SAME_PUB_T3, "two_docs_not_triangulated"),
    ],
)
def test_v_frz_02_floor_below_role_profile_fails_msa_and_spine_freeze(project, pp, evidence, eu_docs, documents, label):
    """A 1-binding spine mechanism, a 2-EU-but-same-document one, AND a
    2-doc-but-NOT-triangulated one (same-publisher T3 pair) each FAIL msa-check
    (MSA-4) and freeze apply --level spine (V-FRZ-02) — triangulation is stricter."""
    paths = _paths(pp)
    _seed_spine_with_mechanism(paths, evidence=evidence, eu_docs=eu_docs, documents=documents)

    # the mechanism IS in the spine (backward walk from T over M->T).
    spine_ids, _ = graph_model.load(paths).spine()
    assert "NODE-003" in spine_ids, label

    # MSA-4 fails (below the role-profile floor).
    msa = graph_commands.msa_check(paths)["msa"]
    assert msa["MSA-4"]["pass"] is False, label

    # spine freeze is refused with V-FRZ-02 in failed_rules.
    with pytest.raises(DomainError) as exc:
        freeze.apply(paths, "NODE-002", "spine")
    assert "V-FRZ-02" in exc.value.errors, label
    # a non-triangulated 2-doc profile additionally reports V-SRC-04.
    if label == "two_docs_not_triangulated":
        assert "V-SRC-04" in exc.value.errors, label


def test_v_frz_02_floor_met_role_profile_passes_msa4(project, pp):
    """The positive side: >=2 bindings from >=2 distinct TRIANGULATED documents
    (T1 + a distinct T4) with the counter angle attempted meets MSA-4."""
    paths = _paths(pp)
    _seed_spine_with_mechanism(
        paths, evidence=["EU-001", "EU-002"],
        eu_docs=[("EU-001", "DOC-001"), ("EU-002", "DOC-002")], documents=_TRI_DOCS,
    )
    msa = graph_commands.msa_check(paths)["msa"]
    assert msa["MSA-4"]["pass"] is True


def test_v_frz_02_role_profile_needs_counter_angle(project, pp):
    """Even a triangulated 2-doc profile FAILS the spine floor if the counter
    angle was never attempted (no completed search) — the floor's counter
    condition (docs/17) is genuinely part of the gate."""
    paths = _paths(pp)
    _seed_spine_with_mechanism(
        paths, evidence=["EU-001", "EU-002"],
        eu_docs=[("EU-001", "DOC-001"), ("EU-002", "DOC-002")], documents=_TRI_DOCS,
        searched=False,
    )
    msa = graph_commands.msa_check(paths)["msa"]
    assert msa["MSA-4"]["pass"] is False


def test_v_frz_03_open_item_touches_refused(project, pp):
    paths = _paths(pp)
    _seed(paths, [_node("NODE-001", node_type="definition", state="active", ll={"allowed": ["a"], "forbidden": ["b"]})])
    # an open proof item targeting the closure record blocks the freeze.
    engine.enqueue(paths, queue_name="proof_queue", target_type="node", target_id="NODE-001", actor="test")
    with pytest.raises(DomainError) as exc:
        freeze.apply(paths, "NODE-001", "local")
    assert "V-FRZ-03" in exc.value.errors


def test_v_frz_04_spine_freeze_requires_msa_and_verify(project, pp):
    paths = _paths(pp)
    # An empty/broken graph fails the MSA checklist, so spine_freeze is refused.
    _seed(paths, [_node("NODE-001", node_type="definition", state="active", ll={"allowed": ["a"], "forbidden": ["b"]})])
    with pytest.raises(DomainError) as exc:
        freeze.apply(paths, "NODE-001", "spine")
    assert "V-FRZ-04" in exc.value.errors


def test_v_frz_language_union_dedup_sorted(project, pp):
    paths = _paths(pp)
    _seed(paths, [
        _node("NODE-001", node_type="definition", state="active", ll={"allowed": ["zeta", "alpha"], "forbidden": ["no-x"]}),
        _node("NODE-002", node_type="definition", state="active", ll={"allowed": ["alpha", "mid"], "forbidden": ["no-y", "no-x"]}, evidence=[]),
    ])
    # subtree freeze over an explicit two-record closure (call the union directly
    # via a local freeze on each, then check a combined subtree via the helper).
    gv = graph_model.load(paths)
    closure = {"NODE-001", "NODE-002"}
    allowed = sorted({p for rid in closure for p in (gv.record(rid)["language_limits"]["allowed"])})
    forbidden = sorted({p for rid in closure for p in (gv.record(rid)["language_limits"]["forbidden"])})
    assert allowed == ["alpha", "mid", "zeta"]
    assert forbidden == ["no-x", "no-y"]

    # And the FreezeItem produced by a real local freeze carries the sorted union
    # of its single record's limits.
    res = freeze.apply(paths, "NODE-001", "local")
    items = jsonl.read_all(paths.resolve("freeze/frozen_items.jsonl"))
    fi = next(i for i in items if i["freeze_id"] == res["freeze_id"])
    assert fi["allowed_language"] == ["alpha", "zeta"]
    assert fi["forbidden_language"] == ["no-x"]


def test_v_frz_unfreeze_reopens_proof(project, pp):
    paths = _paths(pp)
    _seed(paths, [_node("NODE-001", node_type="definition", state="active", ll={"allowed": ["a"], "forbidden": ["b"]})])
    freeze.apply(paths, "NODE-001", "local")
    gv = graph_model.load(paths)
    assert gv.node_by_id["NODE-001"]["frozen"] is True

    freeze.unfreeze(paths, "NODE-001")
    gv = graph_model.load(paths)
    node = gv.node_by_id["NODE-001"]
    assert node["frozen"] is False
    assert node["lifecycle_state"] == "pending_proof"
    # a re-proof work item was enqueued for the re-opened record.
    reopened = [i for i in engine.load_items(paths) if i["target_id"] == "NODE-001" and i["status"] in ("queued", "blocked")]
    assert reopened, "unfreeze must re-open the affected proof"
