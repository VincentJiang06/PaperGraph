"""Expander ingest (docs/08 B3, docs/10 §4).

`validate proposal` runs the static/stateful V-EXP checks; `expand ingest`
validates then commits via the Committer (kind=expansion), returning the assigned
ids and enqueued work items.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ..committer import apply as committer
from ..errors import DomainError, UsageError
from ..paths import Paths
from ..schemas.graph import ExpansionProposal
from ..validate.envelope import to_envelope
from ..validate.rules import v_exp


def _load(proposal_file: str | Path) -> dict[str, Any]:
    path = Path(proposal_file)
    if not path.exists():
        raise UsageError([f"proposal file not found: {proposal_file}"])
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise UsageError([f"proposal file is not valid JSON: {exc.msg}"]) from exc


def validate(paths: Paths, proposal_file: str | Path) -> dict[str, Any]:
    """`validate proposal`: schema + V-EXP static/stateful checks."""
    raw = _load(proposal_file)
    try:
        ExpansionProposal.model_validate(raw)
    except ValidationError as exc:
        return {"ok": False, "failed_rules": ["V-EXP-03"], "detail": {"schema": str(exc.errors()[:2])}}
    failures = v_exp.check(paths, raw)
    if failures:
        env = to_envelope(failures)
        return {"ok": False, "failed_rules": env["failed_rules"], "detail": env["detail"]}
    return {"ok": True, "failed_rules": []}


def ingest(paths: Paths, proposal_file: str | Path, actor: str | None = None) -> dict[str, Any]:
    """`expand ingest`: validate (V-EXP) then commit (kind=expansion)."""
    raw = _load(proposal_file)
    try:
        ExpansionProposal.model_validate(raw)
    except ValidationError as exc:
        raise DomainError(
            ["V-EXP-03: proposal failed schema validation"],
            data={"failed_rules": ["V-EXP-03"], "detail": {"schema": str(exc.errors()[:2])}},
        ) from exc
    failures = v_exp.check(paths, raw)
    if failures:
        env = to_envelope(failures)
        raise DomainError(env["failed_rules"], data={"failed_rules": env["failed_rules"], "detail": env["detail"]})

    result = committer.apply_expansion(paths, raw, actor)
    return {
        "commit_id": result["commit_id"],
        "assigned_ids": result["assigned_ids"],
        "work_item_ids": result["work_item_ids"],
        "closing": result["closing"],
    }
