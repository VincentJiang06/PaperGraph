"""S2 Search Orchestra contract tests (docs/15; docs/11 §12 T-S2-1..3).

Pure, deterministic checks over the merger, the CODE-computed verdict, and the
V-WAVE rules — no LLM anywhere:

  T-S2-1  merger goldens: dup content_hash, tracking-param URL variant, dup EU
          collapse to a byte-identical merged result; every merged doc/EU traces
          to a member (V-WAVE-02).
  T-S2-2  wave-verdict computation table over every angle_covered combination +
          R_MAX + the follow-up members a followup round opens.
  T-S2-3  hostile critic smuggling documents/evidence_units ⇒ V-WAVE-03; a
          closed-enum-incomplete form ⇒ V-WAVE-03; distinct member paths
          (V-WAVE-01); round cap + follow-up origin (V-WAVE-04); one DRES
          (V-WAVE-05).
"""

from __future__ import annotations

import itertools
import json

import pytest

from paperproof.docsdb import wave as wave_mod
from paperproof.textutil import normalize
from paperproof.validate.rules import v_wave

pytestmark = pytest.mark.contract

MANDATORY = wave_mod.MANDATORY_ANGLES

T1 = "Official statistics show unemployment fell to 3.5% in 2024."
T2 = "An academic study finds automation displaced 2% of roles by 2024."
T3 = "A different summary of the same official page, industry-flavoured."


def _doc(text, url, source_type="official_report", title="t", ck="k"):
    return {"title": title, "source_type": source_type,
            "origin": {"kind": "web", "path": None, "url": url}, "citation_key": ck, "text": text}


def _eu(doc_ref, quote, location, can=("claim",), cannot=("overclaim",)):
    return {"doc_ref": doc_ref, "doc_id": None, "location": location, "kind": "quote",
            "quote_or_paraphrase": quote, "summary": quote, "support_direction": "supports",
            "can_cite_for": list(can), "cannot_cite_for": list(cannot), "scope": {}}


def _member_a():
    return {
        "schema_version": "docs_result.v2", "request_id": "DR-001", "project_id": "p",
        "documents": [
            _doc(T1, "https://www.bls.gov/cps//data/?utm_medium=x&ref=y#top", ck="BLS"),
            _doc(T2, "https://acme.example/report", source_type="peer_reviewed", ck="ACME"),
        ],
        "evidence_units": [
            _eu(0, "Unemployment fell to 3.5 percent.", "p.1"),
            _eu(1, "Automation displaced two percent of roles.", "box 2"),
        ],
        "not_found": False,
        "query_log": [{"qid": "Q1", "executed": True, "outcome": "productive", "urls_seen": 2, "docs_taken": 2, "note": ""}],
    }


def _member_b():
    return {
        "schema_version": "docs_result.v2", "request_id": "DR-001", "project_id": "p",
        "documents": [
            # same text T1 as A's doc 0 -> content_hash dup (different URL)
            _doc(T1, "https://mirror.example/copy", ck="MIRROR"),
            # different text T3 but SAME canonical URL as A's doc 0 -> URL dup
            _doc(T3, "https://www.bls.gov/cps/data/?gclid=abc", ck="BLS2"),
        ],
        "evidence_units": [
            # same normalized quote + same doc as A's first EU -> dup EU (dropped)
            _eu(0, "Unemployment fell to  3.5 percent.", "p.1"),
            _eu(1, "Industry data corroborate the decline.", "table 4"),
        ],
        "not_found": False,
        "query_log": [{"qid": "Q1", "executed": True, "outcome": "empty", "urls_seen": 1, "docs_taken": 0, "note": ""}],
    }


# --- T-S2-1: merger goldens -------------------------------------------------


def test_canonical_url_strips_tracking_port_fragment_and_slashes():
    # MIGRATED for F5/D7: canonical_url now ALSO strips "www." (consistent with
    # registry.domain_from_url) — the old expectations kept www. and were part
    # of the buggy identity that re-pointed quote EUs across differing texts.
    cu = wave_mod.canonical_url
    assert cu("https://www.BLS.gov:443/cps//data/?utm_source=n&gclid=z&ref=a#frag") == "https://bls.gov/cps/data"
    assert cu("http://h.example:80/a/") == "http://h.example/a"
    # a real query param survives; only the frozen tracking list is stripped
    assert cu("https://h.example/p?q=1&utm_medium=x&fbclid=y") == "https://h.example/p?q=1"
    assert cu(None) is None


def test_canonical_url_total_on_malformed_port_and_schemeless():
    """F5/D7: canonical_url is TOTAL — a malformed port (the live ValueError
    crash) falls back to the raw netloc; a scheme-less URL gets a default
    scheme like the registry's domain parser."""
    cu = wave_mod.canonical_url
    assert cu("https://example.com:8o8/path") == "https://example.com:8o8/path"  # no crash
    assert cu("https://www.example.com:8o8/path") == "https://example.com:8o8/path"
    assert cu("example.com/path") == "https://example.com/path"


def test_merge_dedups_content_and_dup_eu_keeps_url_collision():
    """MIGRATED for F5/D7: the OLD behavior (URL-collision dedup with DIFFERING
    content_hash) WAS the bug — it re-pointed B's quote EU onto A's text and
    broke V-DR-05 at ingest_merged. Docs now dedup by content_hash ONLY: T3
    (same canonical URL as T1, different text) is KEPT as its own document."""
    merged = wave_mod.merge_results("DR-001", "p", [_member_a(), _member_b()])
    # content_hash dup (T1 twice) collapses; the same-URL-different-text T3 stays.
    texts = sorted(d["text"] for d in merged["documents"])
    assert texts == sorted([T1, T2, T3])
    # the dup EU (same doc, same normalized quote) is dropped -> 3 unique EUs.
    quotes = sorted(normalize(e["quote_or_paraphrase"]) for e in merged["evidence_units"])
    assert quotes == sorted([
        normalize("Unemployment fell to 3.5 percent."),
        normalize("Automation displaced two percent of roles."),
        normalize("Industry data corroborate the decline."),
    ])
    # every EU re-points to a real merged doc index — and B's "industry" EU
    # points at ITS OWN member's T3 text, never another member's.
    docs = merged["documents"]
    for e in merged["evidence_units"]:
        assert 0 <= e["doc_ref"] < len(docs)
    industry_eu = next(e for e in merged["evidence_units"]
                       if normalize(e["quote_or_paraphrase"]) == normalize("Industry data corroborate the decline."))
    assert docs[industry_eu["doc_ref"]]["text"] == T3
    assert merged["not_found"] is False
    assert merged["schema_version"] == "docs_result.v2"


def test_merge_is_byte_identical_for_same_member_set():
    # V-WAVE-02: the same member set (independently reconstructed) merges to the
    # byte-identical result — the merger's ordering is fixed by content, not by
    # dict identity or insertion accidents.
    b1 = json.dumps(wave_mod.merge_results("DR-001", "p", [_member_a(), _member_b()]), separators=(",", ":"))
    b2 = json.dumps(wave_mod.merge_results("DR-001", "p", [_member_a(), _member_b()]), separators=(",", ":"))
    assert b1 == b2


def test_v_wave_02_traceability_pass_and_fail():
    members = [_member_a(), _member_b()]
    merged = wave_mod.merge_results("DR-001", "p", members)
    assert v_wave.check_merge(members, merged, "DR-001", "p") == []
    # inject an untraceable doc -> V-WAVE-02 (determinism + traceability both fire)
    tampered = json.loads(json.dumps(merged))
    tampered["documents"].append(_doc("a fabricated document from nowhere", "https://evil.example/x"))
    fired = [f.rule_id for f in v_wave.check_merge(members, tampered, "DR-001", "p")]
    assert "V-WAVE-02" in fired


# --- T-S2-2: verdict computation table --------------------------------------


def _form(ac_values, primary, disc):
    return {"angle_covered": dict(zip(MANDATORY, ac_values)),
            "primary_source_present": primary, "disconfirming_captured": disc}


def test_verdict_sufficient_when_all_ok_and_primary_present():
    f = _form(["yes", "yes", "yes", "yes"], "yes", "yes")
    assert wave_mod.wave_verdict(f, round=1) == "sufficient"


def test_verdict_followup_when_primary_missing_before_rmax():
    f = _form(["yes", "yes", "yes", "yes"], "no", "yes")
    assert wave_mod.wave_verdict(f, round=1) == "followup"


def test_verdict_primary_waived_at_rmax():
    f = _form(["yes", "yes", "yes", "yes"], "no", "yes")
    assert wave_mod.wave_verdict(f, round=2) == "sufficient"


def test_verdict_no_attempt_followup_then_closed_at_rmax():
    f = _form(["yes", "yes", "no_attempt", "yes"], "yes", "yes")
    assert wave_mod.wave_verdict(f, round=1) == "followup"
    assert wave_mod.wave_verdict(f, round=2) == "closed"  # records the uncovered angle


def test_verdict_disconfirming_missing_blocks_sufficiency():
    f = _form(["yes", "yes", "yes", "yes"], "yes", "no")
    assert wave_mod.wave_verdict(f, round=1) == "followup"
    assert wave_mod.wave_verdict(f, round=2) == "closed"


def test_verdict_tried_states_and_na_disc_are_sufficient():
    f = _form(["tried_empty", "tried_blocked", "yes", "tried_empty"], "yes", "n/a")
    assert wave_mod.wave_verdict(f, round=1) == "sufficient"


def test_verdict_totality_never_loops_at_rmax():
    """Every angle_covered combination yields exactly one verdict; at R_MAX it is
    never `followup` (no infinite loop)."""
    vals = ("yes", "tried_empty", "tried_blocked", "no_attempt")
    for combo in itertools.product(vals, repeat=len(MANDATORY)):
        for primary in ("yes", "no", "n/a"):
            for disc in ("yes", "no", "n/a"):
                f = _form(list(combo), primary, disc)
                assert wave_mod.wave_verdict(f, round=1) in {"sufficient", "followup"}
                assert wave_mod.wave_verdict(f, round=2) in {"sufficient", "closed"}


def test_followup_specs_one_per_no_attempt_and_expected_source():
    f = _form(["yes", "yes", "no_attempt", "yes"], "no", "yes")
    es = [{"name": "BLS CPS", "why": "primary series unqueried", "suggested_query": "bls cps 2024"}]
    specs = wave_mod.followup_specs(f, es)
    origins = [s["origin"] for s in specs]
    assert "angle:industry" in origins
    assert "expected_source:BLS CPS" in origins
    assert len(specs) == 2
    hint = next(s for s in specs if s["origin"].startswith("expected_source"))["hint"]
    assert hint == "bls cps 2024"


# --- T-S2-3 + rule fixtures -------------------------------------------------


def _good_form():
    return {"angle_covered": {"official_stats": "yes", "academic": "yes", "industry": "yes", "counter": "tried_empty"},
            "primary_source_present": "yes", "disconfirming_captured": "yes"}


def test_critic_closed_enum_complete_passes():
    raw = {"schema_version": "coverage_report.v1", "wave_id": "WV-001", "form": _good_form(),
           "expected_sources": [], "notes": "ok"}
    assert v_wave.check_critic(raw, MANDATORY) == []


def test_critic_hostile_smuggles_evidence_rejected_v_wave_03():
    raw = {"schema_version": "coverage_report.v1", "wave_id": "WV-001", "form": _good_form(),
           "expected_sources": [], "notes": "ok",
           "documents": [{"title": "x"}], "evidence_units": [{"quote_or_paraphrase": "y"}]}
    fired = [f.rule_id for f in v_wave.check_critic(raw, MANDATORY)]
    assert fired == ["V-WAVE-03"] or "V-WAVE-03" in fired
    assert "V-WAVE-03" in fired


def test_critic_incomplete_mandatory_angle_rejected_v_wave_03():
    form = _good_form()
    del form["angle_covered"]["industry"]  # a mandatory angle unanswered
    raw = {"schema_version": "coverage_report.v1", "wave_id": "WV-001", "form": form,
           "expected_sources": [], "notes": "ok"}
    assert "V-WAVE-03" in [f.rule_id for f in v_wave.check_critic(raw, MANDATORY)]


def test_critic_too_many_expected_sources_rejected_v_wave_03():
    raw = {"schema_version": "coverage_report.v1", "wave_id": "WV-001", "form": _good_form(),
           "expected_sources": [{"name": str(i), "why": "w", "suggested_query": "q"} for i in range(4)],
           "notes": "ok"}
    assert "V-WAVE-03" in [f.rule_id for f in v_wave.check_critic(raw, MANDATORY)]


def test_v_wave_01_member_paths_distinct():
    assert v_wave.check_member_paths(["a.json", "b.json", "c.json"]) == []
    fired = [f.rule_id for f in v_wave.check_member_paths(["a.json", "a.json"])]
    assert fired == ["V-WAVE-01"]


def test_v_wave_04_round_cap_and_followup_origin():
    ok = {"round": 2, "members": [
        {"work_item_id": "WI-1", "round": 1, "origin": None},
        {"work_item_id": "WI-2", "round": 2, "origin": "angle:industry"},
    ]}
    assert v_wave.check_wave_rounds(ok) == []
    over = {"round": 3, "members": [{"work_item_id": "WI-3", "round": 3, "origin": "x"}]}
    assert "V-WAVE-04" in [f.rule_id for f in v_wave.check_wave_rounds(over)]
    no_origin = {"round": 2, "members": [{"work_item_id": "WI-4", "round": 2, "origin": None}]}
    assert "V-WAVE-04" in [f.rule_id for f in v_wave.check_wave_rounds(no_origin)]


def test_v_wave_05_single_dres():
    ok = [{"request_id": "DR-1", "status": "open", "fulfilled_by": None},
          {"request_id": "DR-1", "status": "fulfilled", "fulfilled_by": "DRES-001"}]
    assert v_wave.check_single_dres("DR-1", ok) == []
    double = ok + [{"request_id": "DR-1", "status": "fulfilled", "fulfilled_by": "DRES-002"}]
    assert "V-WAVE-05" in [f.rule_id for f in v_wave.check_single_dres("DR-1", double)]
