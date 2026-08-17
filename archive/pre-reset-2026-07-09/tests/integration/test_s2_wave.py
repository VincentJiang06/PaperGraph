"""S2 Search Orchestra integration (docs/15; docs/11 §12 T-S2-4 + T-S2-back).

Drives the real `docs wave` CLI + the wave engine end to end with FakeDocsWorker
and FakeCriticWorker:

  * `docs wave --fan` fans a DocsRequest into one member per angle, each a
    docs_queue item with a DISTINCT output [V-WAVE-01]; the pre-existing single
    docs item is superseded (cancelled).
  * a wave that never fully covers an angle CLOSES at R_MAX (=2) recording the
    uncovered angle — no infinite loop — and ingests exactly ONE merged result
    (one DRES per wave) [V-WAVE-05].
  * an all-covered wave is `sufficient` in round 1 (one DRES, closed).
  * back-compat: a non-fan `docs wave` runs as a single member; the pre-S2 docs
    loop is unaffected (its own test stays green). `verify` exits 0 throughout.
"""

from __future__ import annotations

import pytest

from paperproof.docsdb import wave as wave_mod
from paperproof.queue import engine
from paperproof.store import jsonl
from paperproof.validate.rules import v_wave

from tests.fakes import scenario
from tests.fakes.workers import FakeCriticWorker, FakeDocsWorker, drive_wave

pytestmark = pytest.mark.integration

DR = "docs/docs_requests.jsonl"
WAVES = "docs/waves.jsonl"
MANDATORY = set(wave_mod.MANDATORY_ANGLES)


def _open_dr(paths, pp, need="Evidence on 2022 LDI collateral calls.", hints=None):
    scenario.seed_docs_facts(paths, [scenario.FACT_CLAIM])
    hints = hints or ["BoE FSR 2022"]
    args = ["docs", "request", "--target", "NODE-003", "--need", need]
    for h in hints:
        args += ["--hint", h]
    env = pp(*args)
    return env["data"]["request_id"], env["data"]["work_item_id"]


def _reqs(paths):
    return jsonl.read_all(paths.resolve(DR))


# --- `docs wave --fan` (CLI) ------------------------------------------------


def test_docs_wave_fan_cli_fans_all_angles_and_supersedes_single(project, pp):
    paths = scenario.paths_for_pp(pp)
    dr_id, single_wi = _open_dr(paths, pp)

    env = pp("docs", "wave", "--request", dr_id, "--fan")
    data = env["data"]
    assert data["status"] == "open"
    angles = {m["angle"] for m in data["members"]}
    assert MANDATORY <= angles  # news joins only for recent periods (scope is empty here)
    assert len(data["members"]) == len(angles)
    # V-WAVE-01: member outputs pairwise distinct
    outs = [i["output_files"][0] for i in engine.load_items(paths)
            if i["work_item_id"] in {m["work_item_id"] for m in data["members"]}]
    assert v_wave.check_member_paths(outs) == []
    assert len(set(outs)) == len(outs)
    # the pre-existing single docs item is superseded (cancelled), not left dangling
    single = engine.get_item(paths, single_wi)
    assert single["status"] == "cancelled"
    # a search_wave.v1 record exists and `queue list` shows the grouping
    waves = jsonl.latest_records(paths.resolve(WAVES), "wave_id")
    assert len(waves) == 1 and waves[0]["status"] == "open"
    ql = pp("queue", "list", "--queue", "docs_queue")
    assert any(g["wave_id"] == waves[0]["wave_id"] for g in ql["data"]["waves"])
    assert pp("verify")["ok"] is True


# --- full drive: R_MAX close records the uncovered angle, one DRES -----------


def test_wave_closes_at_rmax_with_uncovered_angle_one_dres(project, pp):
    paths = scenario.paths_for_pp(pp)
    dr_id, _ = _open_dr(paths, pp)

    docs_worker = FakeDocsWorker({"*": scenario.boe_docs_result_spec()})
    # industry stays no_attempt every round -> followup at r1, closed at r2.
    uncovered = {
        "form": {
            "angle_covered": {"official_stats": "yes", "academic": "yes",
                              "industry": "no_attempt", "counter": "tried_empty"},
            "primary_source_present": "no", "disconfirming_captured": "yes",
        },
        "expected_sources": [], "notes": "industry angle never covered",
    }
    critic = FakeCriticWorker({"*": [uncovered, uncovered, uncovered]})

    result = drive_wave(paths, dr_id, fan=True, docs_worker=docs_worker, critic_worker=critic)
    assert result["status"] == "closed"
    assert result["verdict"] == "closed"          # R_MAX reached, angle uncovered
    assert result.get("dres_id", "").startswith("DRES-")

    wave = wave_mod.wave_by_id(paths, result["wave_id"])
    assert wave["round"] == 2                       # no infinite loop
    assert v_wave.check_wave_rounds(wave) == []
    # a follow-up member was opened in round 2 and cites its origin
    followups = [m for m in wave["members"] if m["round"] == 2]
    assert followups and all(m["origin"] for m in followups)
    assert any(m["origin"] == "angle:industry" for m in followups)

    # V-WAVE-05: exactly one DRES fulfils the request; only the merged result was
    # ingested (no per-member DRES).
    assert v_wave.check_single_dres(dr_id, _reqs(paths)) == []
    dres = {r["fulfilled_by"] for r in _reqs(paths)
            if r["request_id"] == dr_id and str(r.get("fulfilled_by") or "").startswith("DRES-")}
    assert len(dres) == 1
    assert pp("verify")["ok"] is True


def test_wave_sufficient_in_round_one(project, pp):
    paths = scenario.paths_for_pp(pp)
    dr_id, _ = _open_dr(paths, pp)

    docs_worker = FakeDocsWorker({"*": scenario.boe_docs_result_spec()})
    covered = {
        "form": {
            "angle_covered": {"official_stats": "yes", "academic": "yes",
                              "industry": "yes", "counter": "yes"},
            "primary_source_present": "yes", "disconfirming_captured": "yes",
        },
        "expected_sources": [], "notes": "fully covered",
    }
    critic = FakeCriticWorker({"*": covered})
    result = drive_wave(paths, dr_id, fan=True, docs_worker=docs_worker, critic_worker=critic)
    assert result["verdict"] == "sufficient" and result["status"] == "closed"
    wave = wave_mod.wave_by_id(paths, result["wave_id"])
    assert wave["round"] == 1                       # no follow-up round needed
    assert len(dres_ids(paths, dr_id)) == 1
    assert pp("verify")["ok"] is True


def dres_ids(paths, dr_id):
    return {r["fulfilled_by"] for r in _reqs(paths)
            if r["request_id"] == dr_id and str(r.get("fulfilled_by") or "").startswith("DRES-")}


# --- back-compat: non-fan reactive request still a single member ------------


def test_non_fan_wave_runs_single_member(project, pp):
    paths = scenario.paths_for_pp(pp)
    dr_id, _ = _open_dr(paths, pp)
    env = pp("docs", "wave", "--request", dr_id)  # no --fan
    assert len(env["data"]["members"]) == 1
    assert env["data"]["members"][0]["angle"] == "official_stats"
    assert pp("verify")["ok"] is True


# --- data-loss regression: a follow-up must NOT overwrite a round-1 member ---


def _distinct_member_spec(work_item):
    """A content-DISTINCT docs_result per member, keyed by its (distinct)
    work_item_id — so if a round-2 follow-up reused a round-1 member's output
    path, the round-1 evidence would be silently overwritten and its unique
    quote would go missing from the ingested merged set (V-WAVE-01)."""
    wid = work_item["work_item_id"]
    quote = f"member {wid} verbatim liquidity finding for LDI 2022"
    text = f"{quote}. Background prose about the 2022 gilt crisis for member {wid}."
    return {
        "documents": [{
            "title": f"Doc for {wid}", "source_type": "official_report",
            "origin": {"kind": "web", "path": None, "url": f"https://ex.example/{wid}"},
            "citation_key": f"CK-{wid}", "text": text,
        }],
        "evidence_units": [{
            "doc_ref": 0, "doc_id": None, "location": "p.1", "kind": "quote",
            "quote_or_paraphrase": quote, "summary": quote,
            "support_direction": "supports",
            "can_cite_for": [scenario.FACT_CLAIM],
            "cannot_cite_for": ["all de-risking strategies create liquidity crises"],
            "scope": {},
        }],
        "not_found": False,
        "search_log": ["scripted distinct-per-member search"],
    }


def _ingested_quotes(paths):
    return {e["quote_or_paraphrase"] for e in
            jsonl.latest_records(paths.resolve("docs/evidence_units.jsonl"), "evidence_id")}


def test_followup_reopening_official_stats_preserves_round1_evidence(project, pp):
    """CONFIRMED-bug regression: a round-2 follow-up that REOPENS official_stats
    (served from an expected_source) must land on its OWN output path, never
    overwriting the round-1 official_stats member. Every member's DISTINCT
    evidence must survive into the single ingested merged set (no loss)."""
    paths = scenario.paths_for_pp(pp)
    dr_id, _ = _open_dr(paths, pp)

    docs_worker = FakeDocsWorker({}, per_member=_distinct_member_spec)
    # round 1: all angles covered but primary missing -> followup (round<R_MAX),
    # and an expected_source opens a round-2 official_stats member.
    r1 = {
        "form": {"angle_covered": {a: "yes" for a in wave_mod.MANDATORY_ANGLES},
                 "primary_source_present": "no", "disconfirming_captured": "yes"},
        "expected_sources": [{"name": "BLS primary series",
                              "why": "the primary series is unqueried",
                              "suggested_query": "bls primary 2024"}],
        "notes": "primary source missing",
    }
    # round 2: primary now present -> sufficient -> ingest the merged result once.
    r2 = {
        "form": {"angle_covered": {a: "yes" for a in wave_mod.MANDATORY_ANGLES},
                 "primary_source_present": "yes", "disconfirming_captured": "yes"},
        "expected_sources": [], "notes": "now covered",
    }
    critic = FakeCriticWorker({"*": [r1, r2]})

    result = drive_wave(paths, dr_id, fan=True, docs_worker=docs_worker, critic_worker=critic)
    assert result["verdict"] == "sufficient" and result["status"] == "closed"

    wave = wave_mod.wave_by_id(paths, result["wave_id"])
    # a round-2 official_stats follow-up was opened for the expected_source
    followups = [m for m in wave["members"] if m["round"] == 2]
    assert any(m["angle"] == "official_stats" and str(m["origin"]).startswith("expected_source:")
               for m in followups)
    # the round-1 and round-2 official_stats members declare DISTINCT output paths
    by_id = engine.items_by_id(paths)
    outs = [by_id[m["work_item_id"]]["output_files"][0] for m in wave["members"]]
    assert v_wave.check_member_paths(outs) == [] and len(set(outs)) == len(outs)

    # every member's DISTINCT evidence survived into the ingested merged set —
    # in particular the round-1 official_stats member's quote is NOT overwritten.
    ingested = _ingested_quotes(paths)
    for m in wave["members"]:
        expected = f"member {m['work_item_id']} verbatim liquidity finding for LDI 2022"
        assert expected in ingested, f"evidence for member {m['work_item_id']} was lost"
    assert len(dres_ids(paths, dr_id)) == 1
    assert pp("verify")["ok"] is True


def test_verify_flags_path_colliding_wave_v_wave_01(project, pp):
    """`paperproof verify` sweeps V-WAVE-01 across the wave lifecycle: a wave with
    two members declaring the SAME output path is corruption (silent overwrite)
    and must fail verify (exit 3). A clean wave verifies (exit 0)."""
    paths = scenario.paths_for_pp(pp)
    dr_id, _ = _open_dr(paths, pp)
    started = pp("docs", "wave", "--request", dr_id, "--fan")["data"]
    assert pp("verify")["ok"] is True  # the real wave is clean

    members = started["members"]
    collide_path = engine.get_item(paths, members[0]["work_item_id"])["output_files"][0]
    dup = engine.enqueue(paths, queue_name="docs_queue", target_type="request",
                         target_id=dr_id, task_id=members[0]["plan_id"],
                         output_files=[collide_path], actor="test")
    corrupt = dict(wave_mod.wave_by_id(paths, started["wave_id"]))
    corrupt["members"] = list(members) + [{
        "angle": members[0]["angle"], "work_item_id": dup["work_item_id"],
        "plan_id": members[0]["plan_id"], "round": 1, "origin": None,
    }]
    jsonl.append(paths.resolve(WAVES), wave_mod.SearchWave.model_validate(corrupt))

    env = pp("verify", expect=3)
    assert "V-WAVE-01" in env["errors"]


def test_verify_sweeps_v_wave_04_round_cap(project, pp):
    """F13: `verify` sweeps V-WAVE-04 at rest — a stored wave whose round exceeds
    R_MAX (or a follow-up member with no origin) is corruption (exit 3)."""
    paths = scenario.paths_for_pp(pp)
    dr_id, _ = _open_dr(paths, pp)
    started = pp("docs", "wave", "--request", dr_id, "--fan")["data"]
    assert pp("verify")["ok"] is True

    corrupt = dict(wave_mod.wave_by_id(paths, started["wave_id"]))
    corrupt["round"] = 3  # past R_MAX=2
    jsonl.append(paths.resolve(WAVES), wave_mod.SearchWave.model_validate(corrupt))
    env = pp("verify", expect=3)
    assert "V-WAVE-04" in env["errors"]


def test_verify_sweeps_v_wave_05_double_dres(project, pp):
    """F13: `verify` sweeps V-WAVE-05 at rest — a wave request fulfilled by TWO
    DRES ids (the per-member-ingest corruption) is exit 3."""
    paths = scenario.paths_for_pp(pp)
    dr_id, _ = _open_dr(paths, pp)

    docs_worker = FakeDocsWorker({"*": scenario.boe_docs_result_spec()})
    covered = {
        "form": {"angle_covered": {a: "yes" for a in wave_mod.MANDATORY_ANGLES},
                 "primary_source_present": "yes", "disconfirming_captured": "yes"},
        "expected_sources": [], "notes": "covered",
    }
    result = drive_wave(paths, dr_id, fan=True, docs_worker=docs_worker,
                        critic_worker=FakeCriticWorker({"*": covered}))
    assert result["status"] == "closed"
    assert pp("verify")["ok"] is True

    latest = [r for r in _reqs(paths) if r["request_id"] == dr_id][-1]
    jsonl.append(paths.resolve(DR), {**latest, "fulfilled_by": "DRES-000099"})
    env = pp("verify", expect=3)
    assert "V-WAVE-05" in env["errors"]
