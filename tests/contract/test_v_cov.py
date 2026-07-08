"""V-COV + V-SRC-04 contract tests (S4 coverage & saturation, docs/17, docs/16;
docs/11 §12b).

Covers the coverage-ledger fold goldens [V-COV-01], the saturation truth table +
the two run regressions [V-COV-03], the role-profile floors + narrow-inheritance
[V-COV-04/05], the ContextPack coverage block [V-COV-02], and triangulation
[V-SRC-04]. The r3/m5 flat floor + docs cap are SUPERSEDED; these tests pin the
STRICTER role-profile expectation.
"""

from __future__ import annotations

import json

import pytest

from paperproof.committer import apply as committer
from paperproof.docsdb import coverage
from paperproof.errors import DomainError
from paperproof.freeze import apply as freeze
from paperproof.graph import commands as graph_commands
from paperproof.graph import model as graph_model
from paperproof.paths import paths_for
from paperproof.prooftask import builder
from paperproof.queue import engine
from paperproof.store import jsonl, snapshot
from paperproof.validate.rules import v_cov, v_src

from tests.fakes import scenario
from tests.fakes.workers import FakeProofWorker, prove_one

pytestmark = pytest.mark.contract

NODES = "graph/logic_nodes.jsonl"
EDGES = "graph/logic_edges.jsonl"
EVIDENCE_UNITS = "docs/evidence_units.jsonl"
DOCUMENTS = "docs/documents.jsonl"
DOCS_REQUESTS = "docs/docs_requests.jsonl"
WAVES = "docs/waves.jsonl"


def _paths(pp):
    return paths_for(pp.tmp_path, "p4-ldi")


def _node(node_id, *, node_type, state="active", evidence=None, claim=None, scope=None, origin=None):
    return {
        "schema_version": "logic_node.v1", "node_id": node_id, "project_id": "p4-ldi",
        "bfs_id": "BFS-MAIN", "layer": 1, "claim": claim or f"Claim for {node_id}.",
        "claim_version": 1, "node_type": node_type, "scope": scope or {}, "parents": [],
        "origin": origin or {"kind": "seed", "source": "topic-input"},
        "lifecycle_state": state, "state_reason": None, "state_detail": None,
        "strength": "strong" if state == "active" else "unassessed",
        "language_limits": {"allowed": ["a"], "forbidden": ["b"]}, "assumptions": [],
        "evidence_bindings": list(evidence or []),
        "latest_proof_result_id": "PR-001" if state == "active" else None,
        "frozen": False, "created_at": "2026-07-07T00:00:00Z",
    }


def _edge(edge_id, src, tgt, etype="supports"):
    return {
        "schema_version": "logic_edge.v1", "edge_id": edge_id, "project_id": "p4-ldi",
        "source_node_id": src, "target_node_id": tgt, "edge_type": etype,
        "edge_claim": f"{src} supports {tgt}.", "claim_version": 1, "lifecycle_state": "active",
        "state_reason": None, "state_detail": None, "strength": "strong",
        "language_limits": {"allowed": ["a"], "forbidden": ["b"]}, "assumptions": [],
        "frozen": False, "latest_proof_result_id": "PR-001", "created_at": "2026-07-07T00:00:00Z",
    }


def _eu(eid, doc_id, direction="supports", ingested_from=None):
    return {"schema_version": "evidence_unit.v1", "evidence_id": eid, "project_id": "p4-ldi",
            "doc_id": doc_id, "support_direction": direction, "ingested_from": ingested_from}


def _doc(doc_id, source_type, url, tier, ingested_from=None):
    return {"schema_version": "document.v2", "doc_id": doc_id, "project_id": "p4-ldi",
            "source_type": source_type, "origin": {"kind": "web", "path": None, "url": url},
            "ingested_from": ingested_from,
            "provenance": {"retrieved_at": "2026-07-07T00:00:00Z", "fetch_method": "direct",
                           "tier": tier, "quoted_via": None}}


def _request(rid, target_id, status="fulfilled", fulfilled_by="DRES-001"):
    return {"schema_version": "docs_request.v1", "request_id": rid, "project_id": "p4-ldi",
            "requested_by": "orchestrator", "target_id": target_id, "need": "n", "search_hints": [],
            "fingerprint": rid, "status": status, "fulfilled_by": fulfilled_by,
            "created_at": "2026-07-07T00:00:00Z"}


def _wave(wave_id, request_id, round, status="closed", angles=("official_stats", "academic", "industry", "counter")):
    return {"schema_version": "search_wave.v1", "wave_id": wave_id, "request_id": request_id,
            "project_id": "p4-ldi", "round": round,
            "members": [{"angle": a, "work_item_id": f"WI-{wave_id}-{a}", "plan_id": f"SP-{a}",
                         "round": 1, "origin": None} for a in angles],
            "status": status, "created_at": "2026-07-07T00:00:00Z"}


def _spine(paths, mech_node):
    """A minimal active spine {Q, T, mech, T->Q, mech->T} around mech_node."""
    jsonl.append(paths.resolve(NODES), _node("NODE-001", node_type="question"))
    jsonl.append(paths.resolve(NODES), _node("NODE-002", node_type="thesis"))
    jsonl.append(paths.resolve(NODES), mech_node)
    jsonl.append(paths.resolve(EDGES), _edge("EDGE-002-001", "NODE-002", "NODE-001"))
    jsonl.append(paths.resolve(EDGES), _edge(f"EDGE-{mech_node['node_id'][-3:]}-002", mech_node["node_id"], "NODE-002"))
    snapshot.take_snapshot(paths)


# --- T-S4-1 / V-COV-01: coverage-ledger fold goldens ------------------------


def _seed_rich_node(paths):
    """A spine fact NODE-003 with a full search history: a 2-round closed wave +
    a not_found follow-up round, a critic report marking academic tried_blocked,
    and a T1(supports)+T4(refutes) binding profile."""
    jsonl.append(paths.resolve(DOCUMENTS), _doc("DOC-001", "official_report", "https://boe.example/a", "T1_official", "DRES-001"))
    jsonl.append(paths.resolve(DOCUMENTS), _doc("DOC-002", "dataset", "https://adp.example/b", "T4_industry_data", "DRES-001"))
    jsonl.append(paths.resolve(EVIDENCE_UNITS), _eu("EU-001", "DOC-001", "supports", "DRES-001"))
    jsonl.append(paths.resolve(EVIDENCE_UNITS), _eu("EU-002", "DOC-002", "refutes", "DRES-001"))
    # the productive wave (round 2, closed) + a not_found follow-up (latest DRES, 0 docs)
    jsonl.append(paths.resolve(DOCS_REQUESTS), _request("DR-001", "NODE-003", "fulfilled", "DRES-001"))
    jsonl.append(paths.resolve(DOCS_REQUESTS), _request("DR-002", "NODE-003", "not_found", "DRES-002"))
    jsonl.append(paths.resolve(WAVES), _wave("WV-001", "DR-001", round=2, status="closed"))
    # the critic's coverage report (persistent, per-round) => academic tried_blocked
    rep = {"schema_version": "coverage_report.v1", "wave_id": "WV-001",
           "form": {"angle_covered": {"official_stats": "yes", "academic": "tried_blocked",
                                      "industry": "yes", "counter": "yes"},
                    "primary_source_present": "yes", "disconfirming_captured": "yes"},
           "expected_sources": [], "notes": ""}
    p = paths.resolve("agent_outputs/coverage_reports/WV-001.r2.coverage_report.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rep), encoding="utf-8")
    _spine(paths, _node("NODE-003", node_type="fact", evidence=["EU-001", "EU-002"],
                        claim="A neutral empirical observation."))


def test_ledger_fold_determinism(project, pp):
    """[V-COV-01] same canonical state => identical ledger; the fold folds angles
    from wave rounds + the critic report, eu_counts by direction, distinct
    docs/publishers, tiers, rounds, new_docs_last_round, saturated, floor.met."""
    paths = _paths(pp)
    _seed_rich_node(paths)

    first = coverage.build_ledger(paths)
    second = coverage.build_ledger(paths)
    assert first == second, "identical canonical state must yield a byte-identical ledger"

    led = next(l for l in first["ledger"] if l["node_id"] == "NODE-003")
    assert led["eu_counts"] == {"supports": 1, "refutes": 1, "context": 0}
    assert led["distinct_docs"] == 2
    assert led["distinct_publishers"] == 2
    assert led["tiers_present"] == ["T1_official", "T4_industry_data"]
    # angles folded: official/industry/counter productive; academic tried_blocked
    # (critic report overrides the member-inferred tried_empty).
    assert led["angles"]["official_stats"] == coverage.PRODUCTIVE
    assert led["angles"]["counter"] == coverage.PRODUCTIVE
    assert led["angles"]["academic"] == coverage.TRIED_BLOCKED
    assert led["rounds"] == 3  # 2 (closed wave rounds) + 1 (not_found follow-up)
    assert led["new_docs_last_round"] == 0  # DRES-002 archived nothing
    assert led["triangulated"] is True
    assert led["saturated"] is True
    assert led["floor"] == {"required": "spine_fact", "met": True}


# --- T-S4-2 / V-COV-03: saturation truth table ------------------------------


@pytest.mark.parametrize(
    "rounds, academic, new_docs, expected",
    [
        (2, coverage.PRODUCTIVE, 0, True),
        (1, coverage.PRODUCTIVE, 0, False),          # < 2 rounds
        (2, coverage.PRODUCTIVE, 2, False),          # last round produced docs
        (2, coverage.NO_ATTEMPT, 0, False),          # a mandatory angle untried
        (3, coverage.TRIED_BLOCKED, 0, True),        # tried_blocked counts as attempted
    ],
)
def test_saturation_truth_table(rounds, academic, new_docs, expected):
    angles = {a: coverage.PRODUCTIVE for a in coverage.BASE_MANDATORY}
    angles["academic"] = academic
    assert coverage.is_saturated(rounds, angles, new_docs, coverage.BASE_MANDATORY) is expected


# --- T-S4-3 / V-COV-03: saturation replaces the docs cap --------------------


def test_saturation_fresh_target_not_dead_lettered(project, pp):
    """(a) a fresh (pre-saturation) fact target answering needs_docs opens more
    search -- a real docs work item -- and is NEVER born dead (the r3 cap
    regression)."""
    paths = scenario.paths_for_pp(pp)
    scenario.seed_docs_facts(paths, [scenario.FACT_CLAIM])
    fact = next(i["target_id"] for i in engine.load_items(paths)
                if i["queue_name"] == "proof_queue" and i["target_type"] == "node"
                and i["target_id"] not in ("NODE-001", "NODE-002"))
    worker = FakeProofWorker({fact: scenario.node_insufficient_form()})
    prove_one(paths, fact, worker)

    dead = [i for i in engine.load_items(paths) if i["target_id"] == fact and i["status"] == "dead"]
    assert not dead, "a non-saturated target must not be born dead"
    docs_items = [i for i in engine.load_items(paths) if i["queue_name"] == "docs_queue"]
    assert docs_items, "a non-saturated needs_docs must open a real docs work item"


def test_saturation_floor_unmet_born_dead(project, pp):
    """(b) a SATURATED target whose role floor is unmet answering needs_docs is
    born dead with reason='saturated' [V-COV-03] -- the ONLY born-dead reason."""
    paths = scenario.paths_for_pp(pp)
    scenario.seed_docs_facts(paths, [scenario.FACT_CLAIM])
    fact = next(i["target_id"] for i in engine.load_items(paths)
                if i["queue_name"] == "proof_queue" and i["target_type"] == "node"
                and i["target_id"] not in ("NODE-001", "NODE-002"))

    # pre-seed a SATURATING search history for the fact: a closed 2-round wave
    # (all angles attempted) + a not_found follow-up (rounds>=2, new_docs=0). The
    # fact has no bindings, so the (non-spine) role floor stays unmet.
    jsonl.append(paths.resolve(DOCS_REQUESTS), _request("DR-900", fact, "fulfilled", "DRES-900"))
    jsonl.append(paths.resolve(DOCS_REQUESTS), _request("DR-901", fact, "not_found", "DRES-901"))
    jsonl.append(paths.resolve(WAVES), _wave("WV-900", "DR-900", round=2, status="closed"))

    ctx = coverage.build_context(paths, spine_ids=set())
    rec = graph_model.load(paths).node_by_id[fact]
    assert coverage.target_ledger(rec, ctx)["saturated"] is True

    worker = FakeProofWorker({fact: scenario.node_insufficient_form()})
    prove_one(paths, fact, worker)

    dead = [i for i in engine.load_items(paths) if i["target_id"] == fact and i["status"] == "dead"]
    assert dead, "a saturated + floor-unmet target must be born dead"
    events = jsonl.read_all(paths.resolve("queue/events.jsonl"))
    born = [e for e in events if e["work_item_id"] == dead[0]["work_item_id"]
            and e["op"] == "dead_letter" and e["from_status"] is None]
    assert born and born[-1]["detail"].get("reason") == "saturated"
    assert v_cov.check_born_dead_reason(born[-1]["detail"]["reason"]) == []


# --- T-S4-4 / V-COV-04: role-profile floors ---------------------------------


def test_role_profile_nonspine_needs_one_eu(project, pp):
    """A non-spine fact node clears the floor with >=1 binding (no triangulation)."""
    paths = _paths(pp)
    jsonl.append(paths.resolve(DOCUMENTS), _doc("DOC-001", "official_report", "https://boe.example/a", "T1_official"))
    jsonl.append(paths.resolve(EVIDENCE_UNITS), _eu("EU-001", "DOC-001"))
    node = _node("NODE-050", node_type="fact", evidence=["EU-001"])
    ctx = coverage.build_context(paths, spine_ids=set())
    led = coverage.target_ledger(node, ctx)
    assert led["floor"] == {"required": "nonspine", "met": True}
    node0 = _node("NODE-051", node_type="fact", evidence=[])
    assert coverage.target_ledger(node0, ctx)["floor"]["met"] is False


def test_role_profile_bridge_needs_three_docs(project, pp):
    """A bridge (origin.kind=bridge) fact repairing a spine edge needs the spine
    floor PLUS >=3 distinct docs (bridges are the most contested premises)."""
    paths = _paths(pp)
    docs = [
        _doc("DOC-001", "official_report", "https://boe.example/a", "T1_official"),
        _doc("DOC-002", "dataset", "https://adp.example/b", "T4_industry_data"),
        _doc("DOC-003", "dataset", "https://lightcast.example/c", "T4_industry_data"),
    ]
    for d in docs:
        jsonl.append(paths.resolve(DOCUMENTS), d)
    jsonl.append(paths.resolve(EVIDENCE_UNITS), _eu("EU-001", "DOC-001"))
    jsonl.append(paths.resolve(EVIDENCE_UNITS), _eu("EU-002", "DOC-002", "refutes"))
    jsonl.append(paths.resolve(EVIDENCE_UNITS), _eu("EU-003", "DOC-003"))
    jsonl.append(paths.resolve(DOCS_REQUESTS), _request("DR-1", "NODE-BR"))
    bridge_origin = {"kind": "bridge", "source": "PR-1"}

    # two docs only => bridge floor UNMET (needs >=3).
    two = _node("NODE-BR", node_type="fact", evidence=["EU-001", "EU-002"], origin=bridge_origin)
    ctx = coverage.build_context(paths, spine_ids=set())
    led2 = coverage.target_ledger(two, ctx)
    assert led2["floor"]["required"] == "bridge"
    assert led2["floor"]["met"] is False
    # three distinct docs => met.
    three = _node("NODE-BR", node_type="fact", evidence=["EU-001", "EU-002", "EU-003"], origin=bridge_origin)
    assert coverage.target_ledger(three, ctx)["floor"]["met"] is True


def test_msa4_reports_per_node_ledger_line(project, pp):
    """[V-COV-04] msa-check reports the per-node ledger line for every miss."""
    paths = _paths(pp)
    jsonl.append(paths.resolve(DOCUMENTS), _doc("DOC-001", "official_report", "https://boe.example/a", "T1_official"))
    jsonl.append(paths.resolve(EVIDENCE_UNITS), _eu("EU-001", "DOC-001"))
    _spine(paths, _node("NODE-003", node_type="mechanism", evidence=["EU-001"]))  # 1 binding => miss
    msa = graph_commands.msa_check(paths)["msa"]
    assert msa["MSA-4"]["pass"] is False
    assert "NODE-003" in msa["MSA-4"]["detail"] and "role=spine_mechanism" in msa["MSA-4"]["detail"]


# --- T-S4-4 / V-COV-05: narrow-inheritance ----------------------------------


def test_narrow_inherits_ledger(project, pp):
    """[V-COV-05] a narrowed claim (same node_id, bumped claim_version) inherits
    the parent's ledger -- its bindings/requests are keyed by node_id, so rounds
    and evidence carry across the narrow."""
    paths = _paths(pp)
    jsonl.append(paths.resolve(DOCUMENTS), _doc("DOC-001", "official_report", "https://boe.example/a", "T1_official"))
    jsonl.append(paths.resolve(EVIDENCE_UNITS), _eu("EU-001", "DOC-001"))
    jsonl.append(paths.resolve(DOCS_REQUESTS), _request("DR-1", "NODE-003", "fulfilled", "DRES-001"))
    jsonl.append(paths.resolve(DOCS_REQUESTS), _request("DR-2", "NODE-003", "not_found", "DRES-002"))
    parent = _node("NODE-003", node_type="fact", evidence=["EU-001"], claim="Original broad claim about X.")
    ctx = coverage.build_context(paths, spine_ids=set())
    parent_rounds = coverage.target_ledger(parent, ctx)["rounds"]
    assert parent_rounds == 2

    # a narrow bumps claim_version but keeps node_id => same ledger key => inherited.
    narrowed = dict(parent)
    narrowed.update({"claim_version": 2, "claim": "Original narrow claim about X, region UK."})
    assert coverage.target_ledger(narrowed, ctx)["rounds"] == parent_rounds

    # the core-terms guard: a small change inherits rounds; a >half change resets.
    assert v_cov.rounds_reset_on_narrow("Original broad claim about X", "Original broad claim about X in the UK") is False
    assert v_cov.rounds_reset_on_narrow("Solvency liquidity gilt collateral pension", "Wholly different market employment payroll topic") is True


# --- V-COV-02: ContextPack coverage block -----------------------------------


def test_context_pack_embeds_coverage(project, pp):
    """[V-COV-02] a bundle for a fact/mechanism/bridge target embeds the target's
    ledger line; a definition target carries coverage=null."""
    paths = scenario.paths_for_pp(pp)
    scenario.seed_s7_layer0(paths)
    builder.build_frontier(paths, "test")

    mech_ctx = json.loads(paths.resolve(f"proof/context/CTX-{scenario.S7_M}.json").read_text())
    assert isinstance(mech_ctx.get("coverage"), dict)
    assert mech_ctx["coverage"]["node_id"] == scenario.S7_M
    assert v_cov.check_context_pack_coverage(mech_ctx) == []

    def_ctx = json.loads(paths.resolve(f"proof/context/CTX-{scenario.S7_D}.json").read_text())
    assert def_ctx.get("coverage") is None
    assert v_cov.check_context_pack_coverage(def_ctx) == []


# --- T-S4-tri / V-SRC-04: triangulation -------------------------------------


def test_triangulation_t1_plus_distinct_passes():
    """(a) >=1 T1/T2 EU + >=1 more from a distinct doc triangulates."""
    profile = [("T1_official", "boe.example", "DOC-001"), ("T4_industry_data", "adp.example", "DOC-002")]
    assert coverage.triangulated(profile) is True
    assert v_src.check_triangulation(profile) == []


def test_triangulation_same_publisher_t3_pair_fails():
    """(b) two T3 working papers from the SAME publisher do NOT triangulate
    (the run's Stanford-paper-plus-its-own-press-release pattern)."""
    profile = [("T3_working_paper", "ssrn.example", "DOC-001"), ("T3_working_paper", "ssrn.example", "DOC-002")]
    assert coverage.triangulated(profile) is False
    assert any(f.rule_id == "V-SRC-04" for f in v_src.check_triangulation(profile))
    # two T3/T4 from DIFFERENT publishers DO triangulate under (b).
    indep = [("T3_working_paper", "nber.example", "DOC-001"), ("T4_industry_data", "adp.example", "DOC-002")]
    assert coverage.triangulated(indep) is True


def test_triangulation_t5_press_alone_fails():
    """T5 press never carries a spine binding alone."""
    profile = [("T5_press", "ft.example", "DOC-001"), ("T5_press", "guardian.example", "DOC-002")]
    assert coverage.triangulated(profile) is False


def test_triangulation_enforced_at_freeze(project, pp):
    """V-SRC-04 is enforced at freeze (extends V-FRZ-02): a spine mechanism with a
    same-publisher T3 pair is refused with both V-FRZ-02 and V-SRC-04."""
    paths = _paths(pp)
    jsonl.append(paths.resolve(DOCUMENTS), _doc("DOC-001", "working_paper", "https://ssrn.example/a", "T3_working_paper"))
    jsonl.append(paths.resolve(DOCUMENTS), _doc("DOC-002", "working_paper", "https://ssrn.example/b", "T3_working_paper"))
    jsonl.append(paths.resolve(EVIDENCE_UNITS), _eu("EU-001", "DOC-001"))
    jsonl.append(paths.resolve(EVIDENCE_UNITS), _eu("EU-002", "DOC-002"))
    jsonl.append(paths.resolve(DOCS_REQUESTS), _request("DR-1", "NODE-003"))
    _spine(paths, _node("NODE-003", node_type="mechanism", evidence=["EU-001", "EU-002"]))
    with pytest.raises(DomainError) as exc:
        freeze.apply(paths, "NODE-002", "spine")
    assert "V-FRZ-02" in exc.value.errors
    assert "V-SRC-04" in exc.value.errors
