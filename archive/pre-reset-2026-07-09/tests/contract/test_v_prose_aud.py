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


# --- F8/D14: ingest-prose implicit-complete + absolute paths -----------------


def _enqueue_prose_item(paths, section_id, agent="cw"):
    from paperproof.queue import engine

    out = f"agent_outputs/prose/{section_id}.md"
    item = engine.enqueue(paths, queue_name="compile_queue", target_type="section",
                          target_id=section_id, task_id=f"PROSE-{section_id}",
                          output_files=[out], actor="test")
    return engine.claim(paths, queue_name="compile_queue", agent=agent, wi_id=item["work_item_id"])


def test_ingest_prose_from_claimed_with_absolute_path(project, pp):
    """F8/D14: `compiler ingest-prose` implicit-completes a CLAIMED item and
    accepts the ABSOLUTE spelling of the declared output path (V-PATH-01 is a
    path-identity check, not a string compare)."""
    from paperproof.queue import engine

    paths = _paths(pp)
    _setup(paths)
    item = _enqueue_prose_item(paths, "SEC-mechanism")
    out = paths.project_dir / item["output_files"][0]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("Mech wording (claim: NODE-003)(cite: EU-001).", encoding="utf-8")

    res = prose_mod.ingest_prose(paths, str(out), item["work_item_id"])  # absolute path, claimed item
    assert res["section_id"] == "SEC-mechanism"
    assert engine.get_item(paths, item["work_item_id"])["status"] == "committed"
    # two queue events on the validate leg: complete + validate_pass (docs/05).
    events = [e for e in jsonl.read_all(paths.resolve("queue/events.jsonl"))
              if e["work_item_id"] == item["work_item_id"]]
    assert [e["op"] for e in events[-3:]] == ["complete", "validate_pass", "commit"]


def test_ingest_prose_real_failure_surfaces_its_own_rule(project, pp):
    """F8/D14: a genuine V-PROSE violation on a CLAIMED item surfaces V-PROSE-*
    — the old path died on the illegal claimed→validated transition and masked
    everything as V-Q-01 while burning retries."""
    from paperproof.errors import DomainError
    from paperproof.queue import engine

    paths = _paths(pp)
    _setup(paths)
    item = _enqueue_prose_item(paths, "SEC-mechanism")
    out = paths.project_dir / item["output_files"][0]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("A transition with no annotations at all.", encoding="utf-8")

    with pytest.raises(DomainError) as exc:
        prose_mod.ingest_prose(paths, item["output_files"][0], item["work_item_id"])
    assert any(r.startswith("V-PROSE-") for r in exc.value.errors)
    assert "V-Q-01" not in exc.value.errors
    # the item took the honest validate_fail path (failed -> retry), not a crash.
    assert engine.get_item(paths, item["work_item_id"])["status"] == "queued"
    assert engine.get_item(paths, item["work_item_id"])["attempt"] == 2


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
