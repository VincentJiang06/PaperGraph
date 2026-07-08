"""V-SP contract tests (docs/14 §Rules; docs/11 §12 T-S1-2 / T-S1-3).

Mirrors test_v_dr, one layer per S1 test-plan item:

  T-S1-2  one pass_ + one fail_ fixture PER V-SP rule
          (fixtures/vrules/V-SP-*/), each run through the REAL validator
          ``v_sp.check(result, plan)``: the named rule must be absent (pass) /
          present (fail). Plus schema back-compat — docs_result.v2 round-trips
          (query_log replaces search_log) and a docs_result.v1 result still
          validates against the v1 model (v1 stays READABLE after adoption).

  T-S1-3  hostile: a worker that fabricates outcome counts (docs_taken >
          urls_seen) is rejected with V-SP-03; ``docs plan --request <DR>``
          emits the compiled plan and re-emits it byte-identically on a second
          call (plans are immutable bundle artifacts, docs/14).

V-SP applies ONLY to a docs_result.v2 (structured query_log); a v1 result
carries a free-string search_log and is out of V-SP's scope (v_sp.check no-ops).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from paperproof.schemas.docs import DocsResult, DocsResultV2
from paperproof.validate.rules import v_sp

from tests.fakes import scenario

pytestmark = pytest.mark.contract

VRULES = Path(__file__).resolve().parent.parent / "fixtures" / "vrules"
SCHEMAS = Path(__file__).resolve().parent.parent / "fixtures" / "schemas"


# --- T-S1-2: one pass_ + one fail_ fixture per V-SP rule --------------------


def _run(obj) -> list[str]:
    return [f.rule_id for f in v_sp.check(obj["result"], obj.get("plan"))]


def _vsp_cases():
    cases = []
    for rule_dir in sorted(VRULES.glob("V-SP-*")):
        rule = rule_dir.name
        for path in sorted(rule_dir.glob("*.json")):
            cases.append((rule, path.name, path.name.startswith("fail_")))
    return cases


@pytest.mark.parametrize("rule,filename,expect_fail", _vsp_cases())
def test_vsp_fixtures(rule, filename, expect_fail):
    obj = json.loads((VRULES / rule / filename).read_bytes())
    fired = _run(obj)
    if expect_fail:
        assert rule in fired, (rule, filename, fired)
    else:
        assert rule not in fired, (rule, filename, fired)


def test_every_vsp_rule_has_pass_and_fail():
    from paperproof.validate import registry

    for r in [r for r in registry.rule_ids() if r.startswith("V-SP-")]:
        names = [p.name for p in (VRULES / r).glob("*.json")]
        assert any(n.startswith("pass_") for n in names), r
        assert any(n.startswith("fail_") for n in names), r


def test_v_sp_noops_on_a_v1_result():
    """A v1 result (free-string search_log) is entirely outside V-SP's scope."""
    v1 = json.loads((SCHEMAS / "docs_result.v1.json").read_bytes())
    assert v_sp.check(v1, None) == []


# --- T-S1-2: schema back-compat (v2 round-trips; v1 still readable) ---------


def test_docs_result_v2_round_trips():
    raw = (SCHEMAS / "docs_result.v2.json").read_bytes()
    inst = DocsResultV2.model_validate_json(raw)
    assert inst.schema_version == "docs_result.v2"
    assert inst.query_log, "v2 carries a structured query_log (replaces search_log)"
    assert not hasattr(inst, "search_log")
    # dump -> parse is a fixed point.
    again = DocsResultV2.model_validate_json(inst.model_dump_json())
    assert again.model_dump(mode="json") == inst.model_dump(mode="json")


def test_docs_result_v1_still_validates_under_v1():
    raw = (SCHEMAS / "docs_result.v1.json").read_bytes()
    inst = DocsResult.model_validate_json(raw)
    assert inst.schema_version == "docs_result.v1"
    assert inst.search_log, "v1 keeps its free-string search_log (stays readable)"


def test_v2_query_log_and_v1_search_log_do_not_cross():
    """A v2 body may not carry search_log, and a v1 body may not carry query_log
    (extra=forbid on both models)."""
    v2 = json.loads((SCHEMAS / "docs_result.v2.json").read_bytes())
    v2_bad = {**v2, "search_log": ["x"]}
    with pytest.raises(Exception):
        DocsResultV2.model_validate(v2_bad)
    v1 = json.loads((SCHEMAS / "docs_result.v1.json").read_bytes())
    v1_bad = {**v1, "query_log": []}
    with pytest.raises(Exception):
        DocsResult.model_validate(v1_bad)


# --- T-S1-3: hostile fabricated counts -> V-SP-03 ---------------------------


def _counter_plan(request_id: str = "DR-001") -> dict:
    """A minimal, otherwise-satisfiable plan whose single query is the mandatory
    counter, so an execution accounting for it leaves ONLY the fabricated-count
    clause of V-SP-03 to fire."""
    return {
        "schema_version": "search_plan.v1",
        "plan_id": f"SP-{request_id}",
        "request_id": request_id,
        "project_id": "p4-ldi",
        "angle": "official_stats",
        "facets": {"core_terms": [], "scope_terms": [], "counter_terms": []},
        "queries": [{"qid": "Q1", "kind": "counter", "text": "x decline criticism"}],
        "stop": {"max_queries": 8, "min_docs": 2, "min_eus": 4},
    }


def test_hostile_fabricated_counts_rejected_by_v_sp_03():
    result = {
        "schema_version": "docs_result.v2",
        "request_id": "DR-001",
        "project_id": "p4-ldi",
        "documents": [],
        "evidence_units": [],
        "not_found": False,
        # the worker claims it TOOK more documents than URLs it ever saw.
        "query_log": [
            {"qid": "Q1", "executed": True, "outcome": "productive",
             "urls_seen": 2, "docs_taken": 5, "note": ""}
        ],
    }
    fired = [f.rule_id for f in v_sp.check(result, _counter_plan())]
    assert fired == ["V-SP-03"], fired


def test_non_int_counts_are_clean_v_sp_03_not_a_crash():
    """Live-run regression (ai-jobs-2 wave WV-001): a DocsWorker emitted
    ``urls_seen`` as a LIST of URLs, but QueryLogEntry.urls_seen is an int. The
    ``dt > us`` compare used to raise an INTERNAL ``TypeError: '>' not supported
    between 'int' and 'list'`` at ingest; it must instead surface a clean V-SP-03
    validate_fail so the member takes the honest retry path."""
    result = {
        "schema_version": "docs_result.v2",
        "request_id": "DR-001",
        "project_id": "p4-ldi",
        "documents": [],
        "evidence_units": [],
        "not_found": False,
        "query_log": [
            {"qid": "Q1", "executed": True, "outcome": "productive",
             "urls_seen": ["https://a.example", "https://b.example"],
             "docs_taken": 1, "note": ""}
        ],
    }
    fired = [f.rule_id for f in v_sp.check(result, _counter_plan())]  # must NOT raise
    assert fired == ["V-SP-03"], fired


# --- T-S1-3: `docs plan` emits and re-emits the plan byte-identically -------


def test_docs_plan_cli_reprint_is_byte_identical(project, pp):
    paths = scenario.paths_for_pp(pp)
    scenario.seed_layer0(paths)  # creates NODE-001..004 (A == NODE-003)

    env = pp("docs", "request", "--target", scenario.A,
             "--need", "size and timing of collateral buffer depletion",
             "--hint", "buffer depletion timing")
    assert env["data"]["status"] == "open", env["data"]  # a fresh need is a miss
    dr = env["data"]["request_id"]

    plan_file = paths.resolve(f"docs/plans/SP-{dr}.json")
    first_bytes = plan_file.read_bytes()  # written at dispatch (immutable)

    p1 = pp("docs", "plan", "--request", dr)
    p2 = pp("docs", "plan", "--request", dr)
    second_bytes = plan_file.read_bytes()

    # the reprint is byte-stable at both levels: the stored artifact and the
    # emitted envelope data.
    assert first_bytes == second_bytes, "the plan file is immutable across reprints"
    assert json.dumps(p1["data"], sort_keys=True) == json.dumps(p2["data"], sort_keys=True)
    assert p1["data"]["plan_path"] == f"docs/plans/SP-{dr}.json"

    plan = p1["data"]["plan"]
    assert plan["request_id"] == dr
    assert plan["plan_id"] == f"SP-{dr}"
    # the counter query is MANDATORY in every plan (docs/14).
    assert "counter" in [q["kind"] for q in plan["queries"]]
