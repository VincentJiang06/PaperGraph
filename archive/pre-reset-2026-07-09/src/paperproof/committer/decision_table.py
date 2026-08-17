"""The decision table (docs/03) as a pure function.

``compute_verdict(form, task_type, assumptions) -> verdict`` walks the 8-row
table top-down, first match wins. It is total over ladder-valid forms.

``ladder_check(form, task_type, assumptions, node_type) -> [rule_ids]`` partitions
every possible form into ladder-valid (empty result => exactly one verdict) or
ladder-violating (V-PR-14 shape, V-PR-15 assumptions, V-PR-05 evidence). This is
the mechanical enforcement behind the totality-fuzz test: a form is ladder-valid
IFF ``ladder_check`` returns [], and every ladder-valid form has exactly one
computed verdict; there is no third outcome.

This module imports nothing from ``validate`` or the store so it can be shared by
the Validator (which computes verdicts) and the Committer (which acts on them)
with no import cycle.
"""

from __future__ import annotations

from typing import Any

# Node types that require evidence: they may not answer evidence not_required
# (V-PR-05) once Stage C is reached.
NODE_EVIDENCE_REQUIRED = frozenset({"fact", "mechanism"})

_NE = "not_evaluated"

# Closed enum domains (used by the totality fuzz).
SCOPE_VALUES = ("in_scope", "out_of_scope")
WELLFORMED_VALUES = ("single_proposition", "too_broad", "compound", _NE)
EVIDENCE_VALUES = ("not_required", "sufficient", "insufficient", "contradicting", _NE)
INFERENCE_VALUES = ("holds", "holds_only_with_assumptions", "gap", "fails", _NE)


def _rejected(reason: str) -> dict[str, Any]:
    return {"verdict": "rejected", "repair_kind": None, "strength": None, "reason": reason}


def _needs_repair(kind: str) -> dict[str, Any]:
    return {"verdict": "needs_repair", "repair_kind": kind, "strength": None, "reason": None}


def compute_verdict(
    form: dict[str, Any], task_type: str, assumptions: list[str] | None = None
) -> dict[str, Any]:
    """Compute the verdict from a check form (docs/03 decision table).

    First-match-wins over the 8 rows. ``assumptions`` (a sibling field of the
    form) decides Row 8 strength: conditional iff non-empty.
    """
    assumptions = assumptions or []
    scope = form["scope_check"]
    dup = form["duplicate_check"]["duplicate"]
    wf = form["wellformed_check"]
    ev = form["evidence_check"]
    inf = form.get("inference_check")
    is_edge = task_type == "EDGE_CHECK"

    # Row 1
    if scope == "out_of_scope":
        return _rejected("out_of_scope")
    # Row 2
    if dup:
        return _rejected("duplicate")
    # Row 3
    if wf in ("too_broad", "compound"):
        return _needs_repair("narrow")
    # Row 4
    if ev == "contradicting":
        return _rejected("contradicted")
    # Row 5
    if ev == "insufficient":
        return {"verdict": "needs_docs", "repair_kind": None, "strength": None, "reason": None}
    # Row 6
    if is_edge and inf == "fails":
        return _rejected("contradicted")
    # Row 7
    if is_edge and inf == "gap":
        return _needs_repair("bridge")
    # Row 8 (otherwise): pass
    strength = "conditional" if assumptions else "strong"
    return {"verdict": "pass", "repair_kind": None, "strength": strength, "reason": None}


def ladder_check(
    form: dict[str, Any],
    task_type: str,
    assumptions: list[str] | None = None,
    node_type: str | None = None,
) -> list[str]:
    """Return the sorted list of ladder rules a form violates (subset of
    {V-PR-05, V-PR-14, V-PR-15}); [] iff the form is ladder-valid (docs/03).

    ``node_type`` is only consulted for NODE_CHECK V-PR-05 (fact/mechanism nodes
    may not answer evidence not_required in an evaluated Stage C).
    """
    assumptions = assumptions or []
    scope = form["scope_check"]
    dup = form["duplicate_check"]["duplicate"]
    wf = form["wellformed_check"]
    ev = form["evidence_check"]
    inf = form.get("inference_check")
    is_edge = task_type == "EDGE_CHECK"
    violated: set[str] = set()

    # Which stages the ladder reaches given Stage A/B/C outcomes.
    reach_B = (scope == "in_scope") and (not dup)
    reach_C = reach_B and (wf == "single_proposition")
    reach_D = reach_C and (ev in ("not_required", "sufficient"))

    # V-PR-14: each of wellformed/evidence/(inference) is not_evaluated IFF an
    # earlier stage stopped the ladder.
    if reach_B:
        if wf == _NE:
            violated.add("V-PR-14")
    else:
        if wf != _NE:
            violated.add("V-PR-14")

    if reach_C:
        if ev == _NE:
            violated.add("V-PR-14")
        elif (not is_edge) and node_type in NODE_EVIDENCE_REQUIRED and ev == "not_required":
            # V-PR-05 (only when Stage C was evaluated).
            violated.add("V-PR-05")
    else:
        if ev != _NE:
            violated.add("V-PR-14")

    if is_edge:
        if reach_D:
            if inf == _NE:
                violated.add("V-PR-14")
        else:
            if inf != _NE:
                violated.add("V-PR-14")

    # V-PR-15: assumptions constraint.
    if is_edge:
        if (inf == "holds_only_with_assumptions") != bool(assumptions):
            violated.add("V-PR-15")
    else:
        if assumptions and ev not in ("not_required", "sufficient"):
            violated.add("V-PR-15")

    return sorted(violated)
