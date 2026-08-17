"""T-S1-1: plan-compiler goldens (docs/14 §"The plan compiler", docs/11 §12).

A fixed DocsRequest need + target scope compiles to a BYTE-EXACT search_plan.v1
under the determinism harness (no timestamps ⇒ same request ⇒ same bytes),
INCLUDING a CJK need (tokens() is CJK-aware, docs/09 §0). The counter query is
present in EVERY plan, regardless of angle.
"""

from __future__ import annotations

import pytest

from paperproof.docsdb.planner import ANGLE_SUFFIX, COUNTER_TERMS, compile_plan
from paperproof.serialize import canonical_bytes

pytestmark = pytest.mark.unit

NEED = "Unemployment and nonfarm employment levels"
HINTS = ["BLS nonfarm payrolls record 2024"]
TARGET_SCOPE = {"period": "2021-2025", "region": "United States"}

# The byte-exact golden for angle=official_stats (formula block, docs/14).
GOLDEN_OFFICIAL = (
    b'{"schema_version":"search_plan.v1","plan_id":"SP-DR-006","request_id":"DR-006",'
    b'"project_id":"ai-jobs","angle":"official_stats","facets":{"core_terms":'
    b'["unemployment","nonfarm","employment","levels"],"scope_terms":["2021-2025",'
    b'"united states"],"counter_terms":["decline","criticism","contrary",'
    b'"evidence against","refute"]},"queries":[{"qid":"Q1","kind":"core","text":'
    b'"unemployment nonfarm employment levels 2021-2025 united states"},{"qid":"Q2",'
    b'"kind":"angle","text":"unemployment nonfarm employment levels 2021-2025 '
    b'united states official statistics"},{"qid":"Q3","kind":"hint","text":'
    b'"BLS nonfarm payrolls record 2024"},{"qid":"Q4","kind":"narrow","text":'
    b'"unemployment nonfarm employment bls"},{"qid":"Q5","kind":"counter","text":'
    b'"unemployment nonfarm employment levels 2021-2025 united states decline '
    b'criticism"}],"stop":{"max_queries":8,"min_docs":2,"min_eus":4}}'
)


def _compile(angle: str):
    return compile_plan("DR-006", "ai-jobs", angle, NEED, HINTS, TARGET_SCOPE, {})


def test_golden_official_stats_is_byte_exact():
    assert canonical_bytes(_compile("official_stats")) == GOLDEN_OFFICIAL + b"\n"


def test_same_request_is_byte_identical():
    assert canonical_bytes(_compile("official_stats")) == canonical_bytes(_compile("official_stats"))


@pytest.mark.parametrize("angle", sorted(ANGLE_SUFFIX))
def test_counter_query_present_in_every_plan(angle):
    plan = _compile(angle)
    kinds = [q.kind for q in plan.queries]
    assert "counter" in kinds, (angle, kinds)
    counter = next(q for q in plan.queries if q.kind == "counter")
    # docs/14: counter query = Q1 + counter_terms[0..1].
    assert counter.text.endswith(f"{COUNTER_TERMS[0]} {COUNTER_TERMS[1]}")


@pytest.mark.parametrize("angle", sorted(ANGLE_SUFFIX))
def test_angle_suffix_applied(angle):
    plan = _compile(angle)
    angle_q = next(q for q in plan.queries if q.kind == "angle")
    assert angle_q.text.endswith(ANGLE_SUFFIX[angle])


def test_facets_and_scope_fallback():
    plan = _compile("official_stats")
    assert plan.facets.core_terms == ["unemployment", "nonfarm", "employment", "levels"]
    assert plan.facets.scope_terms == ["2021-2025", "united states"]
    assert plan.facets.counter_terms == COUNTER_TERMS
    # target has no scope ⇒ fall back to the contract scope.
    fallback = compile_plan("DR-007", "ai-jobs", "academic", NEED, [], {},
                            {"period": "2010-2019", "region": "Japan"})
    assert fallback.facets.scope_terms == ["2010-2019", "japan"]


CJK_NEED = "人工智能 就业 影响 人工智能"  # "AI employment impact AI" — 人工智能 repeated


def test_cjk_need_tokenizes_per_char_and_ranks_by_frequency():
    plan = compile_plan("DR-CJK", "ai-jobs", "academic", CJK_NEED, [], {"region": "中国"}, {})
    # tokens(): each CJK char is its own token; casefolded. 人 工 智 能 each appear
    # twice (人工智能 repeated), so they rank ahead of the singletons 就 业 影 响.
    core = plan.facets.core_terms
    assert core[:4] == ["人", "工", "智", "能"], core
    # region casefolded into scope_terms; the counter query is still present.
    assert plan.facets.scope_terms == ["中国"]
    assert any(q.kind == "counter" for q in plan.queries)
    # byte-identical on recompile (determinism holds for CJK too).
    assert canonical_bytes(plan) == canonical_bytes(
        compile_plan("DR-CJK", "ai-jobs", "academic", CJK_NEED, [], {"region": "中国"}, {})
    )
