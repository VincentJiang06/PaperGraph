"""Failure envelope for validator rules (docs/08 §Failure taxonomy).

Every rejected artifact records machine-readable failure reasons:
  {"failed_rules": ["V-PR-07"], "detail": {"V-PR-07": "..."}}
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Failure:
    rule_id: str
    detail: str = ""


def to_envelope(failures: list[Failure]) -> dict[str, Any]:
    """Collapse a list of Failures into the standard failed_rules envelope.

    ``failed_rules`` is de-duplicated preserving first-seen order; ``detail``
    joins multiple details per rule.
    """
    order: list[str] = []
    detail: dict[str, str] = {}
    for f in failures:
        if f.rule_id not in detail:
            order.append(f.rule_id)
            detail[f.rule_id] = f.detail
        elif f.detail:
            detail[f.rule_id] = (detail[f.rule_id] + "; " + f.detail).strip("; ")
    return {"failed_rules": order, "detail": detail}
