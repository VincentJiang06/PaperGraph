"""Decision table: 26 golden rows + precedence + totality fuzz (docs/03, docs/11 §6).

The decision table is a pure function ``(form, task_type, assumptions) -> verdict``
that walks the 8-row table top-down, first match wins. It is total over
ladder-valid forms. ``ladder_check`` partitions every form into ladder-valid
(exactly one verdict) or ladder-violating (V-PR-14/15/05) — there is no third
outcome. This test proves both, and that the ladder-valid set is non-vacuous
(all eight verdict classes are reachable).
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import pytest

from paperproof.committer.decision_table import (
    EVIDENCE_VALUES,
    INFERENCE_VALUES,
    SCOPE_VALUES,
    WELLFORMED_VALUES,
    compute_verdict,
    ladder_check,
)

pytestmark = pytest.mark.unit

FORMS = Path(__file__).resolve().parent.parent / "fixtures" / "forms"

# The reachable-row set is 26: N01..N11 (NODE) + E01..E15 (EDGE). N11/E15 add the
# scope=out_of_scope ∧ duplicate=true precedence rows (Row 1 wins) for both kinds.
GOLDEN_IDS = [f"N{i:02d}" for i in range(1, 12)] + [f"E{i:02d}" for i in range(1, 16)]


def _load(fixture_id: str) -> dict:
    return json.loads((FORMS / f"{fixture_id}.json").read_bytes())


def test_all_26_golden_fixtures_exist():
    on_disk = {p.stem for p in FORMS.glob("*.json")}
    assert on_disk == set(GOLDEN_IDS), {
        "missing": sorted(set(GOLDEN_IDS) - on_disk),
        "unexpected": sorted(on_disk - set(GOLDEN_IDS)),
    }


@pytest.mark.parametrize("fixture_id", GOLDEN_IDS)
def test_golden_row_computes_expected_verdict(fixture_id: str):
    fx = _load(fixture_id)
    verdict = compute_verdict(fx["form"], fx["task_type"], fx["assumptions"])
    assert verdict == fx["expected"], (fixture_id, verdict, fx["expected"])


@pytest.mark.parametrize("fixture_id", GOLDEN_IDS)
def test_golden_rows_are_ladder_valid(fixture_id: str):
    """Every golden row is a legal form: ladder_check returns []."""
    fx = _load(fixture_id)
    violations = ladder_check(fx["form"], fx["task_type"], fx["assumptions"], fx["node_type"])
    assert violations == [], (fixture_id, violations)


def test_golden_rows_cover_every_verdict_class():
    """Non-vacuity: the 26 rows exercise all eight distinct verdict classes."""
    classes = set()
    for fixture_id in GOLDEN_IDS:
        v = _load(fixture_id)["expected"]
        classes.add((v["verdict"], v["repair_kind"], v["strength"], v["reason"]))
    assert classes == {
        ("pass", None, "strong", None),
        ("pass", None, "conditional", None),
        ("needs_repair", "bridge", None, None),
        ("needs_repair", "narrow", None, None),
        ("needs_docs", None, None, None),
        ("rejected", None, None, "contradicted"),
        ("rejected", None, None, "out_of_scope"),
        ("rejected", None, None, "duplicate"),
    }


# --- precedence (first-match-wins) -----------------------------------------


def test_precedence_scope_outranks_everything():
    # An out_of_scope form whose later fields (illegally) look like a pass still
    # rejects out_of_scope — Row 1 wins. (compute_verdict does not require a
    # ladder-valid form; precedence is structural.)
    form = {
        "scope_check": "out_of_scope",
        "duplicate_check": {"duplicate": True, "duplicate_of": "NODE-002"},
        "wellformed_check": "single_proposition",
        "evidence_check": "sufficient",
        "inference_check": "holds",
    }
    assert compute_verdict(form, "EDGE_CHECK")["reason"] == "out_of_scope"


def test_precedence_duplicate_outranks_wellformed():
    form = {
        "scope_check": "in_scope",
        "duplicate_check": {"duplicate": True, "duplicate_of": "NODE-002"},
        "wellformed_check": "too_broad",
        "evidence_check": "not_evaluated",
    }
    assert compute_verdict(form, "NODE_CHECK")["reason"] == "duplicate"


def test_precedence_wellformed_outranks_evidence():
    form = {
        "scope_check": "in_scope",
        "duplicate_check": {"duplicate": False, "duplicate_of": None},
        "wellformed_check": "compound",
        "evidence_check": "contradicting",
    }
    v = compute_verdict(form, "NODE_CHECK")
    assert v["verdict"] == "needs_repair" and v["repair_kind"] == "narrow"


def test_precedence_contradicting_outranks_insufficient_by_position():
    # Row 4 (contradicting) precedes Row 5 (insufficient); a form can only carry
    # one evidence value, so this pins the ordering via each in isolation.
    base = {
        "scope_check": "in_scope",
        "duplicate_check": {"duplicate": False, "duplicate_of": None},
        "wellformed_check": "single_proposition",
    }
    assert compute_verdict({**base, "evidence_check": "contradicting"}, "NODE_CHECK")["reason"] == "contradicted"
    assert compute_verdict({**base, "evidence_check": "insufficient"}, "NODE_CHECK")["verdict"] == "needs_docs"


def test_strength_conditional_iff_assumptions():
    form = {
        "scope_check": "in_scope",
        "duplicate_check": {"duplicate": False, "duplicate_of": None},
        "wellformed_check": "single_proposition",
        "evidence_check": "sufficient",
    }
    assert compute_verdict(form, "NODE_CHECK", [])["strength"] == "strong"
    assert compute_verdict(form, "NODE_CHECK", ["x"])["strength"] == "conditional"


# --- totality fuzz ----------------------------------------------------------

_DUP = ({"duplicate": False, "duplicate_of": None}, {"duplicate": True, "duplicate_of": "NODE-999"})
_ASSUMPTIONS = ([], ["some assumption"])

_VALID_VERDICTS = {
    ("pass", None, "strong", None),
    ("pass", None, "conditional", None),
    ("needs_repair", "bridge", None, None),
    ("needs_repair", "narrow", None, None),
    ("needs_docs", None, None, None),
    ("rejected", None, None, "contradicted"),
    ("rejected", None, None, "out_of_scope"),
    ("rejected", None, None, "duplicate"),
}


def _verdict_tuple(v: dict) -> tuple:
    return (v["verdict"], v["repair_kind"], v["strength"], v["reason"])


@pytest.mark.slow
def test_totality_fuzz_node():
    """Every NODE form combination is ladder-valid (=> exactly one verdict) or
    violates V-PR-14/15/05 — no third outcome. Runs both a fact node (evidence
    required, exercises V-PR-05) and a definition node (not_required legal)."""
    reached_verdicts = set()
    ladder_valid_count = 0
    for node_type in ("fact", "definition"):
        for scope, d, wf, ev, assumptions in itertools.product(
            SCOPE_VALUES, _DUP, WELLFORMED_VALUES, EVIDENCE_VALUES, _ASSUMPTIONS
        ):
            form = {
                "scope_check": scope,
                "duplicate_check": d,
                "wellformed_check": wf,
                "evidence_check": ev,
            }
            violations = ladder_check(form, "NODE_CHECK", assumptions, node_type)
            if not violations:
                ladder_valid_count += 1
                v = compute_verdict(form, "NODE_CHECK", assumptions)
                vt = _verdict_tuple(v)
                assert vt in _VALID_VERDICTS, (form, assumptions, v)
                # idempotent / single-valued
                assert _verdict_tuple(compute_verdict(form, "NODE_CHECK", assumptions)) == vt
                reached_verdicts.add(vt)
            else:
                assert set(violations) <= {"V-PR-05", "V-PR-14", "V-PR-15"}
                assert violations  # non-empty by construction
    assert ladder_valid_count > 0
    # V-PR-05 must actually fire somewhere (fact node, not_required, Stage C).
    fact_form = {
        "scope_check": "in_scope",
        "duplicate_check": {"duplicate": False, "duplicate_of": None},
        "wellformed_check": "single_proposition",
        "evidence_check": "not_required",
    }
    assert "V-PR-05" in ladder_check(fact_form, "NODE_CHECK", [], "fact")
    assert "V-PR-05" not in ladder_check(fact_form, "NODE_CHECK", [], "definition")


@pytest.mark.slow
def test_totality_fuzz_edge():
    reached_verdicts = set()
    ladder_valid_count = 0
    for scope, d, wf, ev, inf, assumptions in itertools.product(
        SCOPE_VALUES, _DUP, WELLFORMED_VALUES, EVIDENCE_VALUES, INFERENCE_VALUES, _ASSUMPTIONS
    ):
        form = {
            "scope_check": scope,
            "duplicate_check": d,
            "wellformed_check": wf,
            "evidence_check": ev,
            "inference_check": inf,
        }
        violations = ladder_check(form, "EDGE_CHECK", assumptions, None)
        if not violations:
            ladder_valid_count += 1
            v = compute_verdict(form, "EDGE_CHECK", assumptions)
            vt = _verdict_tuple(v)
            assert vt in _VALID_VERDICTS, (form, assumptions, v)
            reached_verdicts.add(vt)
        else:
            assert set(violations) <= {"V-PR-05", "V-PR-14", "V-PR-15"}
            assert violations
    assert ladder_valid_count > 0
    # Non-vacuity: edges reach every verdict class except the node-only ones.
    assert reached_verdicts == _VALID_VERDICTS


@pytest.mark.slow
def test_totality_fuzz_all_verdict_classes_reachable():
    """Across node + edge ladder-valid forms, all 8 verdict classes appear."""
    seen = set()
    for tt, node_types in (("NODE_CHECK", ("fact", "definition")), ("EDGE_CHECK", (None,))):
        for node_type in node_types:
            evs = EVIDENCE_VALUES
            infs = INFERENCE_VALUES if tt == "EDGE_CHECK" else (None,)
            for scope, d, wf, ev, inf, assumptions in itertools.product(
                SCOPE_VALUES, _DUP, WELLFORMED_VALUES, evs, infs, _ASSUMPTIONS
            ):
                form = {
                    "scope_check": scope,
                    "duplicate_check": d,
                    "wellformed_check": wf,
                    "evidence_check": ev,
                }
                if inf is not None:
                    form["inference_check"] = inf
                if ladder_check(form, tt, assumptions, node_type):
                    continue
                seen.add(_verdict_tuple(compute_verdict(form, tt, assumptions)))
    assert seen == _VALID_VERDICTS
