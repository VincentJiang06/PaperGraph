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


def _seed_counter_query_log(paths, rid):
    """D6: counter is EARNED only from an EXECUTED counter qid in a v2 query_log.
    Write the request's plan (a counter query) + its docs_result.v2 executing it."""
    plan = {"schema_version": "search_plan.v1", "plan_id": f"SP-{rid}", "request_id": rid,
            "queries": [{"qid": "Q5", "kind": "counter", "text": "evidence against"}]}
    pp = paths.resolve(f"docs/plans/SP-{rid}.json")
    pp.parent.mkdir(parents=True, exist_ok=True)
    pp.write_text(json.dumps(plan), encoding="utf-8")
    result = {"schema_version": "docs_result.v2", "request_id": rid, "project_id": "p4-ldi",
              "documents": [], "evidence_units": [], "not_found": True,
              "query_log": [{"qid": "Q5", "executed": True, "outcome": "empty", "urls_seen": 0, "docs_taken": 0, "note": ""}]}
    rp = paths.resolve(f"agent_outputs/docs_results/{rid}.docs_result.json")
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps(result), encoding="utf-8")


def _seed_critic_report(paths, wave_id, round=1, **angles):
    """Persist a critic coverage report so a seeded (fake-WI) wave earns its
    per-angle outcomes under the D6 terminal-members-only fold."""
    ac = {"official_stats": "tried_empty", "academic": "tried_empty",
          "industry": "tried_empty", "counter": "tried_empty"}
    ac.update(angles)
    rep = {"schema_version": "coverage_report.v1", "wave_id": wave_id,
           "form": {"angle_covered": ac, "primary_source_present": "yes", "disconfirming_captured": "yes"},
           "expected_sources": [], "notes": ""}
    p = paths.resolve(f"agent_outputs/coverage_reports/{wave_id}.r{round}.coverage_report.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rep), encoding="utf-8")


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
    # D6: the wave's seeded members carry fake work-item ids (never terminal), so
    # its angles are earned from the critic's authoritative per-round report.
    _seed_critic_report(paths, "WV-900", round=2)

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
    assert born[-1]["detail"].get("floor_met") is False  # D1: floor_met distinguishes
    assert v_cov.check_born_dead_reason(born[-1]["detail"]["reason"]) == []


def test_saturation_floor_met_born_dead_and_human_review(project, pp):
    """F1/D1: a SATURATED target whose role floor IS met answering needs_docs is
    ALSO born dead (reason='saturated', floor_met=true) AND the CommitDecision
    records a legal human_review action — the previously-crashing path (an illegal
    CommitAction had corrupted every later verify). verify stays exit 0."""
    from paperproof import verify as verify_mod

    paths = scenario.paths_for_pp(pp)
    scenario.seed_docs_facts(paths, [scenario.FACT_CLAIM])
    fact = next(i["target_id"] for i in engine.load_items(paths)
                if i["queue_name"] == "proof_queue" and i["target_type"] == "node"
                and i["target_id"] not in ("NODE-001", "NODE-002"))

    # give the (non-spine) fact ONE binding so its role floor is MET, then a
    # SATURATING search history so needs_docs cannot open more search. This test
    # runs `verify`, so the seeded records are SCHEMA-COMPLETE (strict models).
    jsonl.append(paths.resolve(DOCUMENTS), {
        **_doc("DOC-001", "official_report", "https://boe.example/a", "T1_official", "DRES-900"),
        "title": "BoE", "content_hash": "sha256:0", "text_path": None,
        "citation_key": "BoE2022", "ingested_at": "2026-07-07T00:00:00Z"})
    jsonl.append(paths.resolve(EVIDENCE_UNITS), {
        **_eu("EU-001", "DOC-001", "supports", "DRES-900"),
        "location": "p.1", "kind": "paraphrase", "quote_or_paraphrase": "q", "summary": "s",
        "can_cite_for": [scenario.FACT_CLAIM], "cannot_cite_for": ["x"], "scope": {},
        "extracted_by": "t", "created_at": "2026-07-07T00:00:00Z"})
    node = graph_model.load(paths).node_by_id[fact]
    bound = dict(node)
    bound.update({"evidence_bindings": ["EU-001"], "created_at": "2026-07-07T00:00:01Z"})
    jsonl.append(paths.resolve(NODES), bound)
    jsonl.append(paths.resolve(DOCS_REQUESTS), _request("DR-900", fact, "fulfilled", "DRES-900"))
    jsonl.append(paths.resolve(DOCS_REQUESTS), _request("DR-901", fact, "not_found", "DRES-901"))
    jsonl.append(paths.resolve(WAVES), _wave("WV-900", "DR-900", round=2, status="closed"))
    _seed_critic_report(paths, "WV-900", round=2)

    ctx = coverage.build_context(paths, spine_ids=set())
    led = coverage.target_ledger(graph_model.load(paths).node_by_id[fact], ctx)
    assert led["saturated"] is True and led["floor"]["met"] is True

    worker = FakeProofWorker({fact: scenario.node_insufficient_form()})
    res = prove_one(paths, fact, worker)

    # the re-proof is born dead with the floor_met detail.
    dead = [i for i in engine.load_items(paths) if i["target_id"] == fact and i["status"] == "dead"]
    assert dead
    events = jsonl.read_all(paths.resolve("queue/events.jsonl"))
    born = [e for e in events if e["work_item_id"] == dead[0]["work_item_id"]
            and e["op"] == "dead_letter" and e["from_status"] is None]
    assert born and born[-1]["detail"] == {"reason": "saturated", "floor_met": True}

    # the CommitDecision records the now-legal human_review action.
    cds = jsonl.read_all(paths.resolve("commit/commit_decisions.jsonl"))
    actions = [a for cd in cds for a in cd["actions"] if a["action"] == "human_review"]
    assert actions and actions[-1]["target_id"] == fact

    # and verify stays clean (the illegal-CommitAction corruption is gone).
    assert verify_mod.run(paths)["ok"] is True


# --- F4/D6: reactive saturation is REACHABLE; earned signals only ------------


def _academic_docs_spec():
    """A docs result whose archive spans T1 (official) + T2 (peer-reviewed), so a
    single-path (never-waved) target can EARN official_stats AND academic from
    requested-doc tiers (D6 iii)."""
    spec = scenario.boe_docs_result_spec()
    spec["documents"].append({
        "title": "A peer-reviewed study of LDI collateral dynamics",
        "source_type": "peer_reviewed",
        "origin": {"kind": "web", "path": None, "url": "https://joe.example/ldi-study"},
        "citation_key": "Doe2023LDI",
        "text": "Peer-reviewed analysis of LDI collateral calls in the 2022 gilt crisis.",
    })
    return spec


def test_single_path_target_reaches_saturation(project, pp):
    """F4(a): a never-waved target reaches saturated=true after HONEST rounds —
    round 1 a real search (T1+T2 docs archived; counter qid executed in the v2
    query_log), round 2 the identical request cache-fulfilled (0 new docs).
    Before D6, academic could never leave no_attempt without a wave, so
    is_saturated was unreachable and needs_docs livelocked."""
    paths = scenario.paths_for_pp(pp)
    scenario.seed_docs_facts(paths, [scenario.FACT_CLAIM])
    fact = "NODE-003"

    proof_worker = FakeProofWorker({fact: scenario.node_insufficient_form()})
    from tests.fakes.workers import FakeDocsWorker, drain_docs

    prove_one(paths, fact, proof_worker)                       # round 1: real search
    drain_docs(paths, FakeDocsWorker({"*": _academic_docs_spec()}))
    prove_one(paths, fact, proof_worker)                       # round 2: cache-fulfilled

    led = coverage.ledger_for(paths, fact)["ledger"]
    assert led["angles"]["official_stats"] == coverage.PRODUCTIVE  # T1 doc requested for the target
    assert led["angles"]["academic"] == coverage.PRODUCTIVE       # T2 doc — D6(iii), the livelock fix
    assert led["angles"]["counter"] == coverage.TRIED_EMPTY       # executed counter qid — D6(ii)
    assert led["rounds"] >= 2
    assert led["new_docs_last_round"] == 0                        # cache round archived nothing
    assert led["saturated"] is True


def test_repeat_needs_docs_on_saturated_target_born_dead(project, pp):
    """F4(b): once saturated (floor unmet — the worker never bound evidence), the
    NEXT fingerprint-identical needs_docs is born dead reason=saturated instead of
    cache-fulfilling into an infinite loop. verify exit 0."""
    from paperproof import verify as verify_mod
    from tests.fakes.workers import FakeDocsWorker, drain_docs

    paths = scenario.paths_for_pp(pp)
    scenario.seed_docs_facts(paths, [scenario.FACT_CLAIM])
    fact = "NODE-003"
    proof_worker = FakeProofWorker({fact: scenario.node_insufficient_form()})

    prove_one(paths, fact, proof_worker)                       # round 1: real search
    drain_docs(paths, FakeDocsWorker({"*": _academic_docs_spec()}))
    prove_one(paths, fact, proof_worker)                       # round 2: cache → saturated
    assert coverage.ledger_for(paths, fact)["ledger"]["saturated"] is True

    reqs_before = len(jsonl.read_all(paths.resolve(DOCS_REQUESTS)))
    prove_one(paths, fact, proof_worker)                       # round 3: the stop

    dead = [i for i in engine.load_items(paths) if i["target_id"] == fact and i["status"] == "dead"]
    assert dead, "saturated + floor-unmet: the re-proof must be born dead (no livelock)"
    events = jsonl.read_all(paths.resolve("queue/events.jsonl"))
    born = [e for e in events if e["work_item_id"] == dead[0]["work_item_id"]
            and e["op"] == "dead_letter" and e["from_status"] is None]
    assert born[-1]["detail"] == {"reason": "saturated", "floor_met": False}
    # the saturated branch opens NO new search (no new DocsRequest appended).
    assert len(jsonl.read_all(paths.resolve(DOCS_REQUESTS))) == reqs_before
    assert verify_mod.run(paths)["ok"] is True


def test_cache_and_v1_completions_never_flip_counter(project, pp):
    """F4(c): a cache-fulfilled request and a v1 (search_log) completion never
    flip the counter angle — only an executed-or-blocked counter qid in a v2
    query_log does (fixes the S4 counter over-report)."""
    paths = _paths(pp)
    # DR-1: fulfilled by a DRES but its result is v1 (search_log, no query_log).
    jsonl.append(paths.resolve(DOCS_REQUESTS), _request("DR-1", "NODE-010", "fulfilled", "DRES-001"))
    v1 = {"schema_version": "docs_result.v1", "request_id": "DR-1", "project_id": "p4-ldi",
          "documents": [], "evidence_units": [], "not_found": True, "search_log": ["searched"]}
    rp = paths.resolve("agent_outputs/docs_results/DR-1.docs_result.json")
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps(v1), encoding="utf-8")
    # DR-2: cache-fulfilled (no result file at all).
    jsonl.append(paths.resolve(DOCS_REQUESTS), _request("DR-2", "NODE-010", "fulfilled", "cache"))

    node = _node("NODE-010", node_type="fact", evidence=[])
    ctx = coverage.build_context(paths, spine_ids=set())
    led = coverage.target_ledger(node, ctx)
    assert led["angles"]["counter"] == coverage.NO_ATTEMPT
    # ...whereas an EXECUTED counter qid in a v2 log DOES earn it.
    _seed_counter_query_log(paths, "DR-1")
    ctx = coverage.build_context(paths, spine_ids=set())
    assert coverage.target_ledger(node, ctx)["angles"]["counter"] == coverage.TRIED_EMPTY


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
    _seed_counter_query_log(paths, "DR-1")  # D6: earn the counter angle honestly
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


def test_narrow_over_half_resets_rounds_in_fold(project, pp):
    """F10/D13 [V-COV-05]: the FOLD ITSELF consults the canonical narrow-reset fn
    — a committed >half-core-terms narrow resets rounds to 0 (requests/waves from
    before the narrow commit don't count), so the narrowed claim is NOT
    inherited-saturated. A small narrow still inherits."""
    paths = _paths(pp)
    # pre-narrow search history: two completed rounds, latest archived nothing.
    jsonl.append(paths.resolve(DOCS_REQUESTS), _request("DR-1", "NODE-020", "fulfilled", "DRES-001"))
    jsonl.append(paths.resolve(DOCS_REQUESTS), _request("DR-2", "NODE-020", "not_found", "DRES-002"))
    v1 = _node("NODE-020", node_type="fact",
               claim="Solvency liquidity gilt collateral pension stress dynamics.")
    jsonl.append(paths.resolve(NODES), v1)

    ctx = coverage.build_context(paths, spine_ids=set())
    assert coverage.target_ledger(v1, ctx)["rounds"] == 2

    # the committed narrow changes core_terms by MORE than half (later created_at).
    v2 = dict(v1)
    v2.update({"claim_version": 2, "created_at": "2026-07-07T00:00:05Z",
               "claim": "Wholly different market employment payroll telescope topic."})
    jsonl.append(paths.resolve(NODES), v2)

    ctx = coverage.build_context(paths, spine_ids=set())
    led = coverage.target_ledger(v2, ctx)
    assert led["rounds"] == 0, "a >half narrow must reset rounds (not inherit saturation)"
    assert led["saturated"] is False


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


# --- F12/D12: publisher independence is EARNED, never fabricated -------------


def _local_doc(doc_id, tier="T3_working_paper"):
    return {"schema_version": "document.v2", "doc_id": doc_id, "project_id": "p4-ldi",
            "source_type": "working_paper",
            "origin": {"kind": "user_provided", "path": f"docs/raw/{doc_id}.pdf", "url": None},
            "provenance": {"retrieved_at": "2026-07-07T00:00:00Z", "fetch_method": "direct",
                           "tier": tier, "quoted_via": None}}


def test_two_uncurated_local_t3_docs_do_not_triangulate(project, pp):
    """F12/D12: two LOCAL T3 docs have publisher "" (unknown) — an empty-publisher
    pair is NOT mutually independent, so rule (b) fails. The old code fabricated a
    distinct 'local:<doc_id>' publisher per file, making any two local PDFs
    'independent'."""
    paths = _paths(pp)
    jsonl.append(paths.resolve(DOCUMENTS), _local_doc("DOC-001"))
    jsonl.append(paths.resolve(DOCUMENTS), _local_doc("DOC-002"))
    jsonl.append(paths.resolve(EVIDENCE_UNITS), _eu("EU-001", "DOC-001"))
    jsonl.append(paths.resolve(EVIDENCE_UNITS), _eu("EU-002", "DOC-002"))
    node = _node("NODE-030", node_type="fact", evidence=["EU-001", "EU-002"])
    ctx = coverage.build_context(paths, spine_ids={"NODE-030"})
    led = coverage.target_ledger(node, ctx)
    assert led["triangulated"] is False
    assert led["floor"] == {"required": "spine_fact", "met": False}


def test_curation_via_source_set_publisher_restores_independence(project, pp):
    """F12/D12: two T3 web docs whose domain profiles carry EMPTY publishers do
    not triangulate; `docs source set --publisher` on each domain restores the
    mechanical independence."""
    paths = _paths(pp)
    jsonl.append(paths.resolve(DOCUMENTS), _doc("DOC-001", "working_paper", "https://alab.example/a", "T3_working_paper"))
    jsonl.append(paths.resolve(DOCUMENTS), _doc("DOC-002", "working_paper", "https://blab.example/b", "T3_working_paper"))
    jsonl.append(paths.resolve(EVIDENCE_UNITS), _eu("EU-001", "DOC-001"))
    jsonl.append(paths.resolve(EVIDENCE_UNITS), _eu("EU-002", "DOC-002"))
    # uncurated profiles with EMPTY publishers (e.g. curated pre-fix or tier-only).
    pp("docs", "source", "set", "--domain", "alab.example", "--tier", "T3_working_paper")
    pp("docs", "source", "set", "--domain", "blab.example", "--tier", "T3_working_paper")

    node = _node("NODE-031", node_type="fact", evidence=["EU-001", "EU-002"])
    ctx = coverage.build_context(paths, spine_ids={"NODE-031"})
    assert coverage.target_ledger(node, ctx)["triangulated"] is False

    pp("docs", "source", "set", "--domain", "alab.example", "--publisher", "A Lab")
    pp("docs", "source", "set", "--domain", "blab.example", "--publisher", "B Lab")
    ctx = coverage.build_context(paths, spine_ids={"NODE-031"})
    assert coverage.target_ledger(node, ctx)["triangulated"] is True


def test_registry_learn_defaults_publisher_to_domain(project, pp):
    """F12/D12: `registry.learn` stamps publisher := domain for a web doc's
    profile when no curation exists — so two docs from distinct domains stay
    mechanically independent without a human step."""
    from paperproof.docsdb import registry

    paths = _paths(pp)
    registry.learn(paths, [("nber.example", "working_paper")], {}, now="2026-07-07T00:00:00Z")
    prof = registry._latest_by_domain(paths)["nber.example"]
    assert prof["publisher"] == "nber.example"
    # curation survives a later learn (never overwritten).
    pp("docs", "source", "set", "--domain", "nber.example", "--publisher", "NBER")
    registry.learn(paths, [("nber.example", "working_paper")], {}, now="2026-07-07T00:00:01Z")
    assert registry._latest_by_domain(paths)["nber.example"]["publisher"] == "NBER"


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


# --- F15: smaller confirmed items --------------------------------------------


def test_proof_build_task_no_open_item_is_domain_error(project, pp):
    """F15: `proof build-task` on a target with no open item is a clean DomainError
    envelope (exit 1), never a raw ValueError INTERNAL."""
    env = pp("proof", "build-task", "NODE-999", expect=1)
    assert env["errors"] == ["no open proof work item for target NODE-999"]


def test_build_tasks_surfaces_degrade_warnings(project, pp):
    """F15: assemble_v2 degrade warnings (V-SEM-03 keyword fallback) surface in
    the `proof build-tasks` envelope instead of being dropped."""
    paths = scenario.paths_for_pp(pp)
    scenario.seed_docs_facts(paths, [scenario.FACT_CLAIM])
    env = pp("proof", "build-tasks")
    assert env["data"]["count"] >= 1
    assert any("V-SEM-03" in w for w in env["warnings"]), env["warnings"]


def test_docs_request_fan_flag_recorded(project, pp):
    """F15/D5: `docs request --fan` records fan=true, so a later `docs wave`
    fans one member per angle without repeating --fan."""
    from paperproof.docsdb import wave as wave_mod

    paths = scenario.paths_for_pp(pp)
    scenario.seed_docs_facts(paths, [scenario.FACT_CLAIM])
    env = pp("docs", "request", "--target", "NODE-003",
             "--need", "Evidence on 2022 LDI collateral calls.", "--fan")
    dr_id = env["data"]["request_id"]
    req = jsonl.latest_by_id(paths.resolve(DOCS_REQUESTS), "request_id")[dr_id]
    assert req["fan"] is True
    started = pp("docs", "wave", "--request", dr_id)["data"]  # no --fan repeated
    assert {m["angle"] for m in started["members"]} >= set(wave_mod.MANDATORY_ANGLES)
