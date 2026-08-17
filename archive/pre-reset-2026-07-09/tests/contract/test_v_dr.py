"""V-DR contract tests (docs/09, docs/11 §4/§6).

Two layers, mirroring test_v_pr:
  1. one pass_ + one fail_ fixture PER V-DR rule (fixtures/vrules/V-DR-*/); the
     named rule must be absent (pass) / present (fail) in the fired rule ids.
  2. the hostile catalog D01-D05, each caught by its NAMED rule (the mapping is
     asserted). Plus a direct quote_match check: a whitespace-normalized true
     quote is accepted, a fabricated one rejected.

Check order (docs/11 §6): V-PATH first (exercised in integration), then the
V-DR-03 raw scan BEFORE schema parse, then schema (V-DR-01), then the semantic
rules.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from paperproof.textutil import quote_match
from paperproof.validate.rules import v_dr

pytestmark = pytest.mark.contract

VRULES = Path(__file__).resolve().parent.parent / "fixtures" / "vrules"


def _run(obj) -> list[str]:
    res = obj["result"]
    failures = v_dr.raw_scan(res)
    failures += v_dr.check(
        res,
        archived_doc_ids=set(obj.get("archived_doc_ids", [])),
        archived_texts=obj.get("archived_texts", {}),
    )
    return [f.rule_id for f in failures]


def _vdr_cases():
    cases = []
    for rule_dir in sorted(VRULES.glob("V-DR-*")):
        rule = rule_dir.name
        for path in sorted(rule_dir.glob("*.json")):
            cases.append((rule, path.name, path.name.startswith("fail_")))
    return cases


@pytest.mark.parametrize("rule,filename,expect_fail", _vdr_cases())
def test_vdr_fixtures(rule, filename, expect_fail):
    obj = json.loads((VRULES / rule / filename).read_bytes())
    fired = _run(obj)
    if expect_fail:
        assert rule in fired, (rule, filename, fired)
    else:
        assert rule not in fired, (rule, filename, fired)


def test_every_vdr_rule_has_pass_and_fail():
    from paperproof.validate import registry

    for r in [r for r in registry.rule_ids() if r.startswith("V-DR-")]:
        d = VRULES / r
        names = [p.name for p in d.glob("*.json")]
        assert any(n.startswith("pass_") for n in names), r
        assert any(n.startswith("fail_") for n in names), r


# --- hostile catalog D01-D05 (docs/11 §6) ----------------------------------


def _result(**over):
    r = {
        "schema_version": "docs_result.v1",
        "request_id": "DR-001",
        "project_id": "p4-ldi",
        "documents": [
            {
                "title": "T",
                "source_type": "official_report",
                "origin": {"kind": "web", "path": None, "url": "https://example.org"},
                "citation_key": "K",
                "text": "collateral calls exceeding liquid buffers within days",
            }
        ],
        "evidence_units": [
            {
                "doc_ref": 0,
                "doc_id": None,
                "location": "p.1",
                "kind": "quote",
                "quote_or_paraphrase": "collateral calls exceeding liquid buffers",
                "summary": "s",
                "support_direction": "supports",
                "can_cite_for": ["x"],
                "cannot_cite_for": ["y"],
                "scope": {},
            }
        ],
        "not_found": False,
        "search_log": ["q"],
    }
    r.update(over)
    return r


def _eu(**over):
    e = copy.deepcopy(_result()["evidence_units"][0])
    e.update(over)
    return e


def test_hostiles_vdr():
    # D01: evidence unit without cannot_cite_for -> V-DR-02
    assert "V-DR-02" in _run({"result": _result(evidence_units=[_eu(cannot_cite_for=[])])})
    # D02: quote not present in archived text -> V-DR-05
    assert "V-DR-05" in _run({"result": _result(evidence_units=[_eu(quote_or_paraphrase="never appears here")])})
    # D03: evidence unit with a "strength" field -> V-DR-03
    d03_eu = _eu()
    d03_eu["strength"] = "strong"
    assert "V-DR-03" in _run({"result": _result(evidence_units=[d03_eu])})
    # D04: both doc_ref and doc_id set -> V-DR-01
    assert "V-DR-01" in _run({"result": _result(evidence_units=[_eu(doc_ref=0, doc_id="DOC-001")])})
    # D05: not_found=true with documents present -> V-DR-06
    assert "V-DR-06" in _run({"result": _result(not_found=True)})


def test_quote_match_accepts_true_rejects_fabricated():
    text = "The  quick   brown\nfox jumps over the lazy dog."
    # whitespace-normalized true quote accepted (multiple spaces / newline collapse)
    assert quote_match(text, "quick brown fox jumps") is True
    # a fabricated quote is rejected
    assert quote_match(text, "swift auburn fox vaults") is False
