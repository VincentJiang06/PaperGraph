"""V-* rule registry: rule_id -> descriptor (docs/09).

In M0 only the V-SPEC and V-PATH families are implemented. The registry lets the
rule-coverage meta-test (M1+) enumerate every rule id the system knows about, and
gives the CLI a stable place to describe failed rules.
"""

from __future__ import annotations

from dataclasses import dataclass

from .envelope import Failure, to_envelope
from .rules import v_path, v_spec

__all__ = ["Failure", "to_envelope", "RULES", "rule_ids", "v_spec", "v_path"]


@dataclass(frozen=True)
class Rule:
    rule_id: str
    prefix: str
    description: str


def _rule(rule_id: str, description: str) -> Rule:
    return Rule(rule_id=rule_id, prefix=rule_id.rsplit("-", 1)[0], description=description)


# The rule families implemented in M0.
RULES: dict[str, Rule] = {
    r.rule_id: r
    for r in [
        _rule("V-SPEC-01", "all 9 topic sections present, unique, non-empty"),
        _rule("V-SPEC-02", "paper_type in enum; v1 requires single_event_mechanism"),
        _rule("V-SPEC-03", "bfs_plan is a DAG"),
        _rule("V-SPEC-04", "hard_exclusions and forbidden_claims non-empty"),
        _rule("V-SPEC-05", "3-10 seed claims; each <= 2 sentences"),
        _rule("V-PATH-01", "output path exactly matches declared output_files"),
        _rule("V-PATH-02", "project-relative, no traversal, no symlink escape"),
        _rule("V-PATH-03", "valid UTF-8 JSON (or .md), single document"),
        _rule("V-PATH-04", "no writes outside allowed paths (prefix rule)"),
    ]
}


def rule_ids() -> list[str]:
    return list(RULES.keys())
