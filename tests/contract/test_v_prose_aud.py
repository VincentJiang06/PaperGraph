"""V-PROSE + audit contract tests (docs/09, docs/11 §2).

Annotation grammar (V-PROSE-01..04): a clean prose file passes; a mangled one is
rejected, per family. Audit finding kinds: a clean draft passes; a seeded
violation of EACH kind (binding/strength/scope/coverage) is caught.
"""

from __future__ import annotations

import pytest

from paperproof.audit import run as audit
from paperproof.compiler import prose as prose_mod
from paperproof.paths import paths_for
from paperproof.store import jsonl, snapshot

pytestmark = pytest.mark.contract


def _paths(pp):
    return paths_for(pp.tmp_path, "p4-ldi")


# --- V-PROSE annotation grammar (check_prose directly) ----------------------

SECTION = {
    "section_id": "SEC-mechanism",
    "role": "mechanism",
    "claims": [
        {"node_id": "NODE-003", "claim": "Mechanism claim.", "evidence_ids": ["EU-001"],
         "allowed_language": ["Mech wording"], "forbidden_language": ["overclaim"]},
    ],
    "edge_order": [],
}


def test_v_prose_clean_passes():
    assert prose_mod.check_prose("Mech wording (claim: NODE-003)(cite: EU-001).", SECTION) == []


@pytest.mark.parametrize(
    "text,rule",
    [
        # V-PROSE-01: malformed claim id (not NODE-\\d+).
        ("Mech wording (claim: NODE-BAD)(cite: EU-001).", "V-PROSE-01"),
        # V-PROSE-01: well-formed but unresolved node.
        ("Mech wording (claim: NODE-777)(cite: EU-001).", "V-PROSE-01"),
        # V-PROSE-02: cite not bound to an annotated node.
        ("Mech wording (claim: NODE-003)(cite: EU-999).", "V-PROSE-02"),
        # V-PROSE-03: forbidden_language string present.
        ("Mech wording overclaim (claim: NODE-003)(cite: EU-001).", "V-PROSE-03"),
        # V-PROSE-04: DraftMap claim never annotated.
        ("Just a transition sentence with no annotations.", "V-PROSE-04"),
    ],
)
def test_v_prose_mangled_rejected(text, rule):
    fired = {f.rule_id for f in prose_mod.check_prose(text, SECTION)}
    assert rule in fired, (rule, fired)


# --- audit finding kinds ----------------------------------------------------

NODES = "graph/logic_nodes.jsonl"
EDGES = "graph/logic_edges.jsonl"
EUS = "docs/evidence_units.jsonl"
DRAFT_MAPS = "compiler/draft_maps.jsonl"


def _node(node_id, node_type, evidence=None):
    return {
        "schema_version": "logic_node.v1", "node_id": node_id, "project_id": "p4-ldi",
        "bfs_id": "BFS-MAIN", "layer": 0, "claim": f"Claim {node_id}.", "claim_version": 1,
        "node_type": node_type, "scope": {}, "parents": [], "origin": {"kind": "seed", "source": "topic-input"},
        "lifecycle_state": "active", "state_reason": None, "state_detail": None, "strength": "strong",
        "language_limits": None, "assumptions": [], "evidence_bindings": list(evidence or []),
        "latest_proof_result_id": "PR-001", "frozen": True, "created_at": "2026-07-07T00:00:00Z",
    }


def _edge(edge_id, src, tgt):
    return {
        "schema_version": "logic_edge.v1", "edge_id": edge_id, "project_id": "p4-ldi",
        "source_node_id": src, "target_node_id": tgt, "edge_type": "supports",
        "edge_claim": f"{src} supports {tgt}.", "claim_version": 1, "lifecycle_state": "active",
        "state_reason": None, "state_detail": None, "strength": "strong", "language_limits": None,
        "assumptions": [], "frozen": True, "latest_proof_result_id": "PR-001", "created_at": "2026-07-07T00:00:00Z",
    }


def _setup(paths):
    for n in [_node("NODE-001", "question"), _node("NODE-002", "thesis"), _node("NODE-003", "mechanism", ["EU-001"])]:
        jsonl.append(paths.resolve(NODES), n)
    jsonl.append(paths.resolve(EDGES), _edge("EDGE-002-001", "NODE-002", "NODE-001"))
    jsonl.append(paths.resolve(EDGES), _edge("EDGE-003-002", "NODE-003", "NODE-002"))
    snapshot.take_snapshot(paths)
    jsonl.append(paths.resolve(EUS), {
        "schema_version": "evidence_unit.v1", "evidence_id": "EU-001", "project_id": "p4-ldi",
        "doc_id": "DOC-001", "location": "p.1", "kind": "quote", "quote_or_paraphrase": "q",
        "summary": "s", "support_direction": "supports", "can_cite_for": ["x"], "cannot_cite_for": ["y"],
        "scope": {}, "extracted_by": "docs", "ingested_from": "DRES-001", "created_at": "2026-07-07T00:00:00Z",
    })
    dm = {
        "schema_version": "draft_map.v1", "draft_map_id": "DRAFTMAP-001", "project_id": "p4-ldi",
        "based_on_dry_run": "CDR-001",
        "sections": [
            {"section_id": "SEC-introduction", "role": "introduction", "claims": [
                {"node_id": "NODE-001", "claim": "Claim NODE-001.", "evidence_ids": [], "allowed_language": ["Intro wording"], "forbidden_language": []},
                {"node_id": "NODE-002", "claim": "Claim NODE-002.", "evidence_ids": [], "allowed_language": ["Thesis wording"], "forbidden_language": []},
            ], "edge_order": ["EDGE-002-001"]},
            {"section_id": "SEC-mechanism", "role": "mechanism", "claims": [
                {"node_id": "NODE-003", "claim": "Claim NODE-003.", "evidence_ids": ["EU-001"], "allowed_language": ["Mech wording"], "forbidden_language": ["overclaim"]},
            ], "edge_order": []},
        ],
        "created_at": "2026-07-07T00:00:00Z",
    }
    jsonl.append(paths.resolve(DRAFT_MAPS), dm)


def _write_prose(paths, section_id, text):
    p = paths.resolve(f"compiler/prose/{section_id}.md")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _clean_prose(paths):
    _write_prose(paths, "SEC-introduction", "Intro wording (claim: NODE-001).\n\nThesis wording (claim: NODE-002).")
    _write_prose(paths, "SEC-mechanism", "Mech wording (claim: NODE-003)(cite: EU-001).")


def test_audit_clean_draft_passes(project, pp):
    paths = _paths(pp)
    _setup(paths)
    _clean_prose(paths)
    report = audit.run(paths, "DRAFTMAP-001")
    assert report["passed"] is True
    assert report["findings"] == []


def test_audit_catches_binding(project, pp):
    paths = _paths(pp)
    _setup(paths)
    _clean_prose(paths)
    _write_prose(paths, "SEC-mechanism", "Mech wording (claim: NODE-003)(cite: EU-999).")
    report = audit.run(paths, "DRAFTMAP-001")
    assert report["passed"] is False
    assert "binding" in {f["kind"] for f in report["findings"]}


def test_audit_catches_strength(project, pp):
    paths = _paths(pp)
    _setup(paths)
    _clean_prose(paths)
    _write_prose(paths, "SEC-mechanism", "Mech wording overclaim (claim: NODE-003)(cite: EU-001).")
    report = audit.run(paths, "DRAFTMAP-001")
    assert report["passed"] is False
    assert "strength" in {f["kind"] for f in report["findings"]}


def test_audit_catches_scope(project, pp):
    paths = _paths(pp)
    _setup(paths)
    _clean_prose(paths)
    # a contract forbidden_claims string present verbatim in prose => scope.
    contract = jsonl.read_json(paths.project_contract)
    forbidden_claim = contract["forbidden_claims"][0]
    _write_prose(paths, "SEC-introduction", f"{forbidden_claim} (claim: NODE-001).\n\nThesis wording (claim: NODE-002).")
    report = audit.run(paths, "DRAFTMAP-001")
    assert report["passed"] is False
    assert "scope" in {f["kind"] for f in report["findings"]}


def test_audit_catches_coverage(project, pp):
    paths = _paths(pp)
    _setup(paths)
    _clean_prose(paths)
    _write_prose(paths, "SEC-mechanism", "A transition with no claim annotation at all.")
    report = audit.run(paths, "DRAFTMAP-001")
    assert report["passed"] is False
    assert "coverage" in {f["kind"] for f in report["findings"]}
