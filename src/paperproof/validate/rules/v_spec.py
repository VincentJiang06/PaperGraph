"""V-SPEC rules: topic input & scoping (docs/09).

V-SPEC-01  all 9 required topic sections present, unique, non-empty (P1-P7)
V-SPEC-02  paper_type in supported pattern enum (v1 additionally requires
           single_event_mechanism - others exit 1 "pattern not implemented")
V-SPEC-03  bfs_plan is a DAG (no cycles, all depends_on ids exist)
V-SPEC-04  hard_exclusions and forbidden_claims are non-empty lists
V-SPEC-05  3-10 seed claims; each <= 2 sentences (sentence_count, §0)
"""

from __future__ import annotations

from typing import Any

from ...textutil import sentence_count
from ..envelope import Failure

SUPPORTED_PATTERNS = {
    "single_event_mechanism",
    "parallel_case_bfs_then_merge",
    "core_experiment_empirical",
    "literature_debate_mapping",
    "policy_design_memo",
    "freeform_research_design",
}
V1_PATTERN = "single_event_mechanism"


def _bfs_plan_is_dag(bfs_plan: list[dict[str, Any]]) -> tuple[bool, str]:
    ids = [entry.get("bfs_id") for entry in bfs_plan]
    id_set = set(ids)
    # all depends_on must resolve
    for entry in bfs_plan:
        for dep in entry.get("depends_on", []) or []:
            if dep not in id_set:
                return False, f"depends_on id does not exist: {dep!r}"
    # cycle detection (DFS with colors)
    graph = {entry.get("bfs_id"): list(entry.get("depends_on", []) or []) for entry in bfs_plan}
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}

    def visit(node: str) -> bool:
        color[node] = GRAY
        for nxt in graph.get(node, []):
            if color.get(nxt) == GRAY:
                return False
            if color.get(nxt) == WHITE and not visit(nxt):
                return False
        color[node] = BLACK
        return True

    for node in graph:
        if color[node] == WHITE and not visit(node):
            return False, f"cycle detected involving {node!r}"
    return True, ""


def check(parsed: Any, spec_dict: dict[str, Any], contract_dict: dict[str, Any]) -> list[Failure]:
    """Run V-SPEC-01..05 over the parsed topic and derived artifacts."""
    failures: list[Failure] = []

    # V-SPEC-01
    problems: list[str] = []
    if parsed.missing:
        problems.append("missing sections: " + ", ".join(parsed.missing))
    if parsed.duplicates:
        problems.append("duplicate sections: " + ", ".join(parsed.duplicates))
    if parsed.empty:
        problems.append("empty sections: " + ", ".join(parsed.empty))
    if problems:
        failures.append(Failure("V-SPEC-01", "; ".join(problems)))

    # V-SPEC-02
    paper_type = spec_dict.get("paper_type", "")
    if paper_type not in SUPPORTED_PATTERNS:
        failures.append(Failure("V-SPEC-02", f"paper_type not in supported patterns: {paper_type!r}"))
    elif paper_type != V1_PATTERN:
        failures.append(
            Failure("V-SPEC-02", f"pattern not implemented in v1: {paper_type!r}")
        )

    # V-SPEC-03
    bfs_plan = spec_dict.get("bfs_plan", []) or []
    ok, detail = _bfs_plan_is_dag(bfs_plan)
    if not ok:
        failures.append(Failure("V-SPEC-03", detail))

    # V-SPEC-04
    if not (spec_dict.get("hard_exclusions") or []):
        failures.append(Failure("V-SPEC-04", "hard_exclusions is empty"))
    if not (contract_dict.get("forbidden_claims") or []):
        failures.append(Failure("V-SPEC-04", "forbidden_claims is empty"))

    # V-SPEC-05
    seeds = spec_dict.get("seed_claims", []) or []
    if not (3 <= len(seeds) <= 10):
        failures.append(Failure("V-SPEC-05", f"seed claims count {len(seeds)} not in 3..10"))
    for i, claim in enumerate(seeds):
        if sentence_count(claim) > 2:
            failures.append(
                Failure("V-SPEC-05", f"seed claim {i} has {sentence_count(claim)} sentences (>2)")
            )
            break

    return failures
