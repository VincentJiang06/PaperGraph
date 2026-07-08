"""F2/D2 — the wave lifecycle has a PRODUCTION driver: the CLI owns it.

Regressions for the m10 v2.1 confirmed defects:

  * the FULL wave runs through the CLI ONLY (no Python-API wave calls):
    wave → claim → wave-member ×N (auto merge + critic dispatch on the last)
    → claim critic → wave-resolve → ONE DRES; verify exit 0.
  * `docs ingest-result` REFUSES a wave-member item, naming `docs wave-member`
    (per-member ingest was corrupting the request record — V-WAVE-05/V-SP-05).
  * F5/D7: a same-URL-different-text wave CLOSES cleanly with BOTH docs archived
    (the old URL-dedup re-pointed quote EUs across texts and V-DR-05 wedged the
    wave open forever).
  * F6/D8: a followup wave's round-2 plan is round/origin-discriminated,
    CONTAINS the critic's suggested_query hint, and member task_ids are unique
    (round 2 used to re-execute round 1 byte-identically).
"""

from __future__ import annotations

import json

import pytest

from paperproof.docsdb import planner, wave as wave_mod
from paperproof.queue import engine
from paperproof.store import jsonl

from tests.fakes import scenario
from tests.fakes.workers import FakeCriticWorker, FakeDocsWorker

pytestmark = pytest.mark.integration

DR = "docs/docs_requests.jsonl"

_COVERED = {
    "form": {"angle_covered": {a: "yes" for a in wave_mod.MANDATORY_ANGLES},
             "primary_source_present": "yes", "disconfirming_captured": "yes"},
    "expected_sources": [], "notes": "fully covered",
}


def _open_dr(paths, pp):
    scenario.seed_docs_facts(paths, [scenario.FACT_CLAIM])
    env = pp("docs", "request", "--target", "NODE-003",
             "--need", "Evidence on 2022 LDI collateral calls.", "--hint", "BoE FSR 2022")
    return env["data"]["request_id"]


def _dres_ids(paths, dr_id):
    return {r["fulfilled_by"] for r in jsonl.read_all(paths.resolve(DR))
            if r["request_id"] == dr_id and str(r.get("fulfilled_by") or "").startswith("DRES-")}


def _drive_wave_cli(paths, pp, dr_id, docs_worker, critic_worker, max_rounds=4):
    """The production drive: every state change via the CLI. Workers only write
    their declared output files (that is their real job, not an API call)."""
    started = pp("docs", "wave", "--request", dr_id, "--fan")["data"]
    wave_id = started["wave_id"]
    last = {}
    for _ in range(max_rounds):
        wave = wave_mod.wave_by_id(paths, wave_id)  # read-only lookup for the loop
        member_ids = {m["work_item_id"] for m in wave["members"]}
        auto = None
        for wi_id in sorted(member_ids):
            item = engine.get_item(paths, wi_id)
            if item["status"] not in ("queued",):
                continue
            claimed = pp("queue", "claim", "--queue", "docs_queue", "--agent", "docs-w",
                         "--id", wi_id)["data"]["work_item"]
            docs_worker.run(claimed, paths.project_dir)
            env = pp("docs", "wave-member", claimed["output_files"][0], "--work-item", wi_id)
            auto = env["data"]
        assert auto is not None and auto.get("wave_status") == "critic", \
            "the LAST wave-member must auto-run merge + critic dispatch"
        critic_wi = auto["critic_work_item_id"]
        claimed = pp("queue", "claim", "--queue", "critic_queue", "--agent", "critic-w",
                     "--id", critic_wi)["data"]["work_item"]
        critic_worker.run(claimed, paths.project_dir)
        last = pp("docs", "wave-resolve", claimed["output_files"][0], "--work-item", critic_wi)["data"]
        if last.get("status") == "closed":
            break
    return {"wave_id": wave_id, **last}


def test_full_wave_through_cli_only(project, pp):
    """F2: wave → claim → wave-member ×N → auto merge+critic → claim critic →
    wave-resolve → one DRES; verify exit 0. No Python-API wave calls."""
    paths = scenario.paths_for_pp(pp)
    dr_id = _open_dr(paths, pp)

    result = _drive_wave_cli(paths, pp, dr_id,
                             FakeDocsWorker({"*": scenario.boe_docs_result_spec()}),
                             FakeCriticWorker({"*": _COVERED}))
    assert result["status"] == "closed" and result["verdict"] == "sufficient"
    assert result["dres_id"].startswith("DRES-")
    assert len(_dres_ids(paths, dr_id)) == 1          # V-WAVE-05: one DRES per wave
    assert pp("verify")["ok"] is True


def test_ingest_result_refuses_wave_member(project, pp):
    """F2/D2: `docs ingest-result` on a wave-member item is refused with a
    DomainError naming `docs wave-member` — per-member ingest is illegal."""
    paths = scenario.paths_for_pp(pp)
    dr_id = _open_dr(paths, pp)
    started = pp("docs", "wave", "--request", dr_id, "--fan")["data"]
    wi_id = sorted(m["work_item_id"] for m in started["members"])[0]

    claimed = pp("queue", "claim", "--queue", "docs_queue", "--agent", "docs-w",
                 "--id", wi_id)["data"]["work_item"]
    FakeDocsWorker({"*": scenario.boe_docs_result_spec()}).run(claimed, paths.project_dir)

    env = pp("docs", "ingest-result", claimed["output_files"][0], "--work-item", wi_id, expect=1)
    assert any("docs wave-member" in e for e in env["errors"])
    # the refusal changed nothing: the item is still claimed, the request open.
    assert engine.get_item(paths, wi_id)["status"] == "claimed"
    assert _dres_ids(paths, dr_id) == set()


# --- F5/D7: same-URL-different-text closes cleanly with BOTH docs ------------


def _same_url_different_text_spec(work_item):
    """Two members return the SAME canonical URL with DIFFERENT text; each quote
    EU is verbatim in ITS OWN text. Under the old URL-dedup the second member's
    quote was re-pointed onto the first member's text → V-DR-05 at ingest_merged
    → the wave could never close."""
    wid = work_item["work_item_id"]
    quote = f"distinct verbatim finding of member {wid}"
    text = f"{quote}. Same page, refreshed content for {wid}."
    return {
        "documents": [{
            "title": f"Same page seen by {wid}", "source_type": "official_report",
            "origin": {"kind": "web", "path": None, "url": "https://stats.example/page?utm_source=x"},
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
        "search_log": ["scripted same-url search"],
    }


def test_same_url_different_text_wave_closes_with_both_docs(project, pp):
    """F5/D7 executed repro: the wave closes cleanly and BOTH same-URL docs are
    archived; every quote EU still matches its own document's text (V-DR-05)."""
    paths = scenario.paths_for_pp(pp)
    dr_id = _open_dr(paths, pp)

    result = _drive_wave_cli(paths, pp, dr_id,
                             FakeDocsWorker({}, per_member=_same_url_different_text_spec),
                             FakeCriticWorker({"*": _COVERED}))
    assert result["status"] == "closed"

    wave = wave_mod.wave_by_id(paths, result["wave_id"])
    n_members = len(wave["members"])
    merged = json.loads((paths.project_dir / wave_mod.merged_relpath(dr_id)).read_text())
    assert len(merged["documents"]) == n_members, "both same-URL-different-text docs kept"
    urls = {d["origin"]["url"] for d in merged["documents"]}
    assert len({wave_mod.canonical_url(u) for u in urls}) == 1  # genuinely colliding URLs
    # each archived quote EU matches its own archived text (V-DR-05 held at ingest).
    assert len(_dres_ids(paths, dr_id)) == 1
    assert pp("verify")["ok"] is True


# --- F6/D8: follow-up plans carry the critic's hints, task_ids unique --------


def test_followup_round2_plan_contains_hint_and_task_ids_unique(project, pp):
    """F6/D8: the round-2 expected_source member gets a round/origin-discriminated
    plan id, compiled WITH the suggested_query hint — round 2 no longer re-executes
    round 1 byte-identically, and no two members share a task_id."""
    paths = scenario.paths_for_pp(pp)
    dr_id = _open_dr(paths, pp)

    r1 = {
        "form": {"angle_covered": {a: "yes" for a in wave_mod.MANDATORY_ANGLES},
                 "primary_source_present": "no", "disconfirming_captured": "yes"},
        "expected_sources": [{"name": "ONS vacancy series",
                              "why": "the primary series is unqueried",
                              "suggested_query": "ons vacancy telescope 2024"}],
        "notes": "primary missing",
    }
    result = _drive_wave_cli(paths, pp, dr_id,
                             FakeDocsWorker({"*": scenario.boe_docs_result_spec()}),
                             FakeCriticWorker({"*": [r1, _COVERED]}))
    assert result["status"] == "closed"

    wave = wave_mod.wave_by_id(paths, result["wave_id"])
    followup = next(m for m in wave["members"]
                    if m["round"] == 2 and str(m["origin"]).startswith("expected_source:"))
    round1_os = next(m for m in wave["members"] if m["round"] == 1 and m["angle"] == "official_stats")

    # the plan id is round/origin-discriminated — never the round-1 id.
    assert followup["plan_id"] != round1_os["plan_id"]
    assert ".r2." in followup["plan_id"]
    # the round-2 plan DIFFERS from round 1 and carries the hint's token.
    p1 = planner.load_plan_by_id(paths, round1_os["plan_id"])
    p2 = planner.load_plan_by_id(paths, followup["plan_id"])
    assert p2 is not None and p2 != p1
    assert any("telescope" in q["text"] for q in p2["queries"]), \
        "the critic's suggested_query hint must reach the round-2 plan"
    # task_ids (member plan ids on the queue items) are pairwise unique.
    task_ids = [engine.get_item(paths, m["work_item_id"])["task_id"] for m in wave["members"]]
    assert len(set(task_ids)) == len(task_ids)
    assert pp("verify")["ok"] is True
