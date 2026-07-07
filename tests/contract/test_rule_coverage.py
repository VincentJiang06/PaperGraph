"""Rule-coverage meta-test (docs/11 §7).

For every rule id currently in the registry: either fixtures/vrules/<id>/ has
>=1 pass_ and >=1 fail_ file, or the id appears in SCENARIO_COVERED (a closed map
from rule id -> the test that exercises it). A rule in NEITHER place fails the
build; so does a vrules directory for a rule id that no longer exists, or a stale
SCENARIO_COVERED key. Covers only the rules registered so far (M0+M1):
V-SPEC / V-PATH / V-PR / V-EXP / V-TASK / V-Q / V-COMMIT.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from paperproof.validate import registry

pytestmark = pytest.mark.contract

VRULES = Path(__file__).resolve().parent.parent / "fixtures" / "vrules"

# Rules exercised by an integration/contract scenario rather than vrules fixtures.
SCENARIO_COVERED = {
    "V-SPEC-01": "test_v_spec.py (topic fixtures)",
    "V-SPEC-02": "test_v_spec.py",
    "V-SPEC-03": "test_v_spec.py",
    "V-SPEC-04": "test_v_spec.py",
    "V-SPEC-05": "test_v_spec.py",
    "V-PR-12": "test_s1_seed_loop.py verify recompute (_verdict_recompute)",
    "V-EXP-01": "test_v_exp.py::test_v_exp_01_previous_layer_open",
    "V-EXP-02": "test_v_exp.py::test_v_exp_02_stale_snapshot",
    "V-EXP-03": "test_v_exp.py::test_v_exp_03_*",
    "V-EXP-04": "test_v_exp.py::test_v_exp_04_bad_edge_ref",
    "V-EXP-05": "test_v_exp.py::test_v_exp_05_compound_node",
    "V-EXP-06": "test_v_exp.py::test_v_exp_06_*",
    "V-EXP-07": "test_v_exp.py::test_v_exp_07_dependent_lane_before_complete",
    "V-TASK-01": "test_s6_stale.py (stale claim refusal + -r2 rebuild)",
    "V-TASK-02": "test_v_task.py::test_v_task_02_*",
    "V-TASK-03": "test_v_task.py::test_v_task_03_docs_pack_resolution",
    "V-Q-01": "test_v_q.py::test_v_q_01_illegal_transition_rejected",
    "V-Q-02": "test_v_q.py::test_v_q_02_second_claim_fails",
    "V-Q-03": "test_v_q.py::test_v_q_03_hand_corrupted_event_detected",
    "V-Q-04": "test_v_q.py::test_v_q_04_edge_blocked_until_endpoints_active",
    "V-Q-05": "test_v_q.py::test_v_q_05_crash_recovery_requeue",
    "V-COMMIT-01": "test_v_commit.py::test_v_commit_01_stale_refusal",
    "V-COMMIT-02": "test_v_commit.py (verdict lookup; missing PR raises V-COMMIT-02)",
    "V-COMMIT-03": "test_v_commit.py::test_b6b_freeze_unfreeze_and_frozen_refusal",
    "V-COMMIT-04": "test_v_commit.py (replay.replay_reproduces per row)",
    "V-COMMIT-05": "test_v_commit.py (post-graph V-GRAPH checks) + verify",
    "V-COMMIT-06": "test_v_commit.py::test_v_commit_06_noop_cancel",
}


def _has_pass_and_fail(rule: str) -> bool:
    d = VRULES / rule
    if not d.is_dir():
        return False
    names = [p.name for p in d.glob("*.json")]
    return any(n.startswith("pass_") for n in names) and any(n.startswith("fail_") for n in names)


def test_every_registered_rule_is_covered():
    gaps = []
    for rule in registry.rule_ids():
        if _has_pass_and_fail(rule) or rule in SCENARIO_COVERED:
            continue
        gaps.append(rule)
    assert not gaps, f"rules with no pass_/fail_ fixture and no SCENARIO_COVERED entry: {gaps}"


def test_no_orphan_vrules_directory():
    registered = set(registry.RULES)
    orphans = [d.name for d in VRULES.iterdir() if d.is_dir() and d.name not in registered]
    assert not orphans, f"vrules dirs for unregistered rule ids: {orphans}"


def test_scenario_covered_keys_are_registered():
    registered = set(registry.RULES)
    stale = [r for r in SCENARIO_COVERED if r not in registered]
    assert not stale, f"stale SCENARIO_COVERED keys (rule no longer registered): {stale}"


def test_no_double_counting_is_allowed_but_complete():
    """Sanity: the union of fixtured + scenario-covered rules is exactly the
    registry (nothing registered is silently uncovered)."""
    covered = {r for r in registry.rule_ids() if _has_pass_and_fail(r)} | set(SCENARIO_COVERED)
    assert covered >= set(registry.rule_ids())
