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
from ..graph import model as graph_model
from ..paths import Paths
from ..schemas.graph import ExpansionProposal
from ..store import jsonl
from ..validate.envelope import to_envelope
from ..validate.rules import v_exp, v_sweep


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


def _require_accepted_contract(paths: Paths) -> None:
    """V-GATE-01 (docs/09): the graph may not be expanded until the user has
    accepted the latest ProjectContract. Human acceptance gates every mutation."""
    contract = jsonl.read_json(paths.project_contract) if paths.project_contract.exists() else {}
    if not contract.get("accepted_by_user"):
        raise DomainError(
            ["V-GATE-01: contract not accepted"],
            data={"failed_rules": ["V-GATE-01"]},
        )


def ingest(paths: Paths, proposal_file: str | Path, actor: str | None = None) -> dict[str, Any]:
    """`expand ingest`: validate (V-EXP) then commit (kind=expansion)."""
    _require_accepted_contract(paths)
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

    # V-SWEEP-01: the FIRST expansion beyond layer 0 is gated on the sweep floor
    # (docs/04 step 4, docs/05 pipeline) — proofs never again start against an
    # empty evidence base. Fires once, when a layer>=1 proposal arrives while no
    # layer>=1 node exists yet.
    sweep_failures = _check_sweep_gate(paths, raw)
    if sweep_failures:
        env = to_envelope(sweep_failures)
        raise DomainError(env["failed_rules"], data={"failed_rules": env["failed_rules"], "detail": env["detail"]})

    result = committer.apply_expansion(paths, raw, actor)
    return {
        "commit_id": result["commit_id"],
        "assigned_ids": result["assigned_ids"],
        "work_item_ids": result["work_item_ids"],
        "closing": result["closing"],
    }


def _check_sweep_gate(paths: Paths, proposal: dict[str, Any]) -> list:
    """V-SWEEP-01 fires only on the first expansion beyond layer 0 (the first
    layer>=1 proposal while the graph has no layer>=1 node yet)."""
    if proposal.get("layer", 0) < 1:
        return []
    gv = graph_model.load(paths)
    if any(n.get("layer", 0) >= 1 for n in gv.nodes):
        return []
    return v_sweep.check_sweep_floor(paths, gv)
