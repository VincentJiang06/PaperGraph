"""V-PR: proof check-form validation (docs/03, docs/09) — the biggest rule block.

The worker submits a check form along the evaluation ladder; code computes the
verdict. V-PR validates the FORM; the verdict is computed by
``committer.decision_table``; V-PR-12 (recompute) is checked at rest by verify.

Check order (docs/11 §6): the caller runs V-PATH first, then this module's
``raw_scan`` (V-PR-03) BEFORE schema parsing, then ``check`` (schema V-PR-01, then
the semantic rules). ``raw_scan`` is what makes V-PR-03 reachable even though the
schema is strict.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import ValidationError

from ...committer.decision_table import compute_verdict, ladder_check
from ...schemas.proof import ProofResult
from ...textutil import word_count
from ..envelope import Failure
from . import v_node_edge

# Id keys the schema legitimately carries; any other *_id key => invented id.
_ALLOWED_ID_KEYS = {"task_id", "project_id", "target_id"}
_ID_TOKEN_RE = re.compile(r"\b(EU|DOC)-[0-9]+\b")
_BRIDGE_NODE_TYPES = {"fact", "mechanism", "definition", "alternative"}


# --- V-PR-03 raw scan (runs before schema parse) ---------------------------


def raw_scan(raw: Any) -> list[Failure]:
    """V-PR-03: no numeric value anywhere, no key named 'verdict', no invented
    id-valued field beyond the schema's own. Walks the raw JSON tree."""
    failures: list[Failure] = []

    def walk(node: Any, path: str) -> None:
        if isinstance(node, bool):
            return  # booleans are legal (duplicate)
        if isinstance(node, (int, float)):
            failures.append(Failure("V-PR-03", f"numeric value at {path}: {node!r}"))
            return
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "verdict":
                    failures.append(Failure("V-PR-03", "form carries a 'verdict' field"))
                if key.endswith("_id") and key not in _ALLOWED_ID_KEYS:
                    failures.append(Failure("V-PR-03", f"invented id field: {key}"))
                walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, f"{path}[{i}]")

    walk(raw, "$")
    return failures


# --- V-PR-01 + semantic rules ----------------------------------------------


def check(
    result_dict: dict[str, Any],
    *,
    task: dict[str, Any],
    context_pack: dict[str, Any],
    docs_pack: dict[str, Any],
    work_item: dict[str, Any],
) -> tuple[list[Failure], dict[str, Any] | None]:
    """Validate the form (V-PR-01..15). Returns (failures, computed_verdict).

    ``computed_verdict`` is present whenever the schema parsed (so the caller can
    record it on success); the caller records only when failures == []."""
    # V-PR-01: schema parse.
    try:
        result = ProofResult.model_validate(result_dict)
    except ValidationError as exc:
        return [Failure("V-PR-01", f"schema invalid: {exc.errors()[:2]}")], None

    failures: list[Failure] = []
    task_type = task["task_type"]
    form = result.form.model_dump(mode="json")
    node_type = None
    tgt = context_pack.get("target") or {}
    if result.target_type == "node":
        node_type = tgt.get("node_type")

    # V-PR-02: task_id + target match.
    task_target_id = task["target"].get("edge_id") or task["target"].get("node_id")
    if result.task_id != task.get("task_id") or result.task_id != work_item.get("task_id"):
        failures.append(Failure("V-PR-02", f"task_id {result.task_id!r} != claimed work item task"))
    if result.target_id != task_target_id:
        failures.append(Failure("V-PR-02", f"target_id {result.target_id!r} != task target {task_target_id!r}"))
    expected_ttype = "edge" if "edge_id" in task["target"] else "node"
    if result.target_type != expected_ttype:
        failures.append(Failure("V-PR-02", f"target_type {result.target_type!r} != {expected_ttype!r}"))

    # V-PR-04: inference_check present iff EDGE_CHECK.
    has_inf = result.form.inference_check is not None
    if task_type == "EDGE_CHECK" and not has_inf:
        failures.append(Failure("V-PR-04", "EDGE_CHECK form missing inference_check"))
    if task_type == "NODE_CHECK" and has_inf:
        failures.append(Failure("V-PR-04", "NODE_CHECK form carries inference_check"))

    # V-PR-14 (ladder shape) + V-PR-15 (assumptions) + V-PR-05 (fact/mech ev).
    for rule_id in ladder_check(form, task_type, result.assumptions, node_type):
        failures.append(Failure(rule_id, f"ladder/assumptions/evidence violation: {rule_id}"))

    # V-PR-06: evidence_used subset of DocsPack.
    docspack_eu = {e.get("evidence_id") for e in (docs_pack.get("evidence_units") or [])}
    for eu in result.evidence_used:
        if eu not in docspack_eu:
            failures.append(Failure("V-PR-06", f"evidence id {eu!r} not in DocsPack"))

    # V-PR-08: duplicate_of resolves to a ContextPack id, != target.
    if result.form.duplicate_check.duplicate:
        ctx_ids = {n.get("node_id") for n in (context_pack.get("neighbor_nodes") or [])}
        ctx_ids |= {e.get("edge_id") for e in (context_pack.get("neighbor_edges") or [])}
        ctx_ids |= {d.get("node_id") for d in (context_pack.get("claim_digest") or [])}
        dof = result.form.duplicate_check.duplicate_of
        if dof is None or dof not in ctx_ids or dof == result.target_id:
            failures.append(Failure("V-PR-08", f"duplicate_of {dof!r} not a valid ContextPack id"))

    # V-PR-07: conditional attachments present exactly when required.
    failures += _check_attachments(result, task_type)

    # V-PR-09 + V-PR-11: repair proposal shapes.
    failures += _check_repairs(result)

    # V-PR-10: notes word count + no stray EU/DOC id tokens.
    if word_count(result.notes) > 150:
        failures.append(Failure("V-PR-10", f"notes {word_count(result.notes)} words (>150)"))
    allowed_ids = set(result.evidence_used) | docspack_eu | {
        d.get("doc_id") for d in (docs_pack.get("documents_meta") or [])
    }
    blob = _result_text_blob(result_dict)
    for match in _ID_TOKEN_RE.finditer(blob):
        tok = match.group(0)
        if tok not in allowed_ids:
            failures.append(Failure("V-PR-10", f"stray evidence id token {tok!r}"))

    # verdict + V-PR-13.
    verdict = compute_verdict(form, task_type, result.assumptions)
    if verdict["verdict"] == "pass":
        ll = result.language_limits
        if ll is None or not ll.allowed or not ll.forbidden:
            failures.append(Failure("V-PR-13", "pass requires language_limits.allowed AND .forbidden"))
    else:
        if result.language_limits is not None:
            failures.append(Failure("V-PR-13", "non-pass verdict requires language_limits = null"))

    return failures, verdict


def _result_text_blob(result_dict: dict[str, Any]) -> str:
    import json

    return json.dumps(result_dict, ensure_ascii=False)


def _check_attachments(result: ProofResult, task_type: str) -> list[Failure]:
    failures: list[Failure] = []
    form = result.form
    wf = form.wellformed_check
    ev = form.evidence_check
    inf = form.inference_check
    n_repairs = len(result.repair_proposals)
    n_docs = len(result.docs_requests)
    n_evidence = len(result.evidence_used)

    # repair_proposals expectation
    if wf in ("too_broad", "compound"):
        if n_repairs != 1 or result.repair_proposals[0].kind != "narrow":
            failures.append(Failure("V-PR-07", "too_broad/compound requires exactly 1 narrow repair"))
    elif task_type == "EDGE_CHECK" and inf == "gap":
        if not (1 <= n_repairs <= 2) or any(r.kind != "bridge" for r in result.repair_proposals):
            failures.append(Failure("V-PR-07", "gap requires 1-2 bridge repairs"))
    else:
        if n_repairs != 0:
            failures.append(Failure("V-PR-07", "repair_proposals must be empty for this form"))

    # evidence / docs expectation
    if ev in ("sufficient", "contradicting"):
        if n_evidence < 1:
            failures.append(Failure("V-PR-07", f"{ev} requires evidence_used >= 1"))
    elif ev == "insufficient":
        if n_docs < 1:
            failures.append(Failure("V-PR-07", "insufficient requires docs_requests >= 1"))
    else:  # not_required | not_evaluated
        if n_evidence != 0:
            failures.append(Failure("V-PR-07", f"evidence_used must be empty for evidence_check={ev}"))

    if ev != "insufficient" and n_docs != 0:
        failures.append(Failure("V-PR-07", "docs_requests only allowed on insufficient"))

    return failures


def _check_repairs(result: ProofResult) -> list[Failure]:
    failures: list[Failure] = []
    for r in result.repair_proposals:
        if r.kind == "bridge":
            if not r.claim or r.narrowed_claim is not None:
                failures.append(Failure("V-PR-09", "bridge repair must carry {kind, claim, node_type}"))
            if r.node_type not in _BRIDGE_NODE_TYPES:
                failures.append(Failure("V-PR-09", f"bridge node_type {r.node_type!r} not allowed"))
        elif r.kind == "narrow":
            if not r.narrowed_claim or r.claim is not None or r.node_type is not None:
                failures.append(Failure("V-PR-09", "narrow repair must carry {kind, narrowed_claim} only"))
            else:
                ok, detail = v_node_edge.node02_ok(r.narrowed_claim)
                if not ok:
                    failures.append(Failure("V-PR-11", f"narrowed_claim fails V-NODE-02: {detail}"))
    return failures
