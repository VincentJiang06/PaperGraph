"""Freeze gate (docs/06, docs/08 B8).

`freeze apply --target --level`:
  1. compute the closure for the level (local / subtree / spine),
  2. check V-FRZ-01..04 preconditions deterministically,
  3. union the closure's language limits (dedup + sorted) into a FreezeItem,
  4. append the FreezeItem to freeze/frozen_items.jsonl (Freeze writes only freeze/),
  5. set frozen=true on every closure record via a Committer batch commit
     (kind=freeze_batch) — Freeze never writes graph files.

`freeze unfreeze --target` is the human-only inverse: it appends a
FreezeItem(action=unfreeze, revokes=FRZ-id) and drives an unfreeze_batch commit
that clears frozen and re-opens the affected proofs. A record is frozen iff its
newest covering FreezeItem has action="freeze".
"""

from __future__ import annotations

from typing import Any, Optional

from ..clock import actor as clock_actor
from ..clock import now as clock_now
from ..committer import apply as committer
from ..errors import CorruptStateError, DomainError
from ..graph import model as graph_model
from ..ids import next_id
from ..paths import Paths
from ..queue import engine
from ..store import jsonl
from ..verify import run as verify_run

FROZEN_ITEMS = "freeze/frozen_items.jsonl"

_LEVEL_TO_TYPE = {
    "local": "local_freeze",
    "subtree": "subtree_freeze",
    "spine": "spine_freeze",
}


# --- closures (docs/06) -----------------------------------------------------


def _active_ancestor_closure(gv: graph_model.GraphView, root_id: str) -> set[str]:
    """Every node/edge from which ``root_id`` is reachable along ACTIVE
    supports/depends_on edges (the same backward walk the spine uses, rooted at
    ``root_id``). Includes the root node itself."""
    active = gv.active_ids()
    ids: set[str] = set()
    if root_id in gv.node_by_id:
        ids.add(root_id)

    by_target: dict[str, list[dict[str, Any]]] = {}
    for e in gv.edges:
        if e["lifecycle_state"] != "active":
            continue
        if e["edge_type"] not in ("supports", "depends_on"):
            continue
        by_target.setdefault(e["target_node_id"], []).append(e)

    stack = [root_id]
    seen = {root_id}
    while stack:
        cur = stack.pop()
        for e in by_target.get(cur, []):
            ids.add(e["edge_id"])
            src = e["source_node_id"]
            if src in active:
                ids.add(src)
                if src not in seen:
                    seen.add(src)
                    stack.append(src)
    return ids


def compute_closure(gv: graph_model.GraphView, freeze_type: str, target: str) -> set[str]:
    if freeze_type == "spine_freeze":
        ids, _ = gv.spine()
        return ids
    if freeze_type == "local_freeze":
        return {target}
    # subtree_freeze
    if target in gv.node_by_id:
        return _active_ancestor_closure(gv, target)
    edge = gv.edge_by_id.get(target)
    if edge is not None:
        return {target} | _active_ancestor_closure(gv, edge["source_node_id"])
    return {target}


# --- "touches" adjacency (docs/02) ------------------------------------------


def touches(gv: graph_model.GraphView, closure: set[str], target_id: str) -> bool:
    """A record touches a set C if it is in C, or is an edge with an endpoint in
    C, or is a node with a parent in C, or is an endpoint node of an edge in C."""
    if target_id in closure:
        return True
    edge = gv.edge_by_id.get(target_id)
    if edge is not None:
        if edge["source_node_id"] in closure or edge["target_node_id"] in closure:
            return True
    node = gv.node_by_id.get(target_id)
    if node is not None:
        if any(p in closure for p in node.get("parents", [])):
            return True
        for e in gv.edges:
            if e["edge_id"] in closure and target_id in (e["source_node_id"], e["target_node_id"]):
                return True
    return False


# --- preconditions (V-FRZ-01..04) -------------------------------------------


def _check_preconditions(
    paths: Paths, gv: graph_model.GraphView, freeze_type: str, closure: set[str]
) -> tuple[list[str], dict[str, str]]:
    """Returns (failed_rules, per-rule detail). Every failed rule names the
    offending record / floor line (F15 — the r3 per-rule-detail principle:
    bare rule ids proved undiagnosable in the live run)."""
    failed: list[str] = []
    detail: dict[str, str] = {}

    # V-FRZ-01: every record in the closure is active.
    for rid in sorted(closure):
        rec = gv.record(rid)
        if rec is None or rec["lifecycle_state"] != "active":
            failed.append("V-FRZ-01")
            state = "missing" if rec is None else rec["lifecycle_state"]
            detail["V-FRZ-01"] = f"{rid}: not active ({state})"
            break

    # V-FRZ-02: every fact/mechanism node in the closure clears the S4 role-profile
    # floor (docs/17) — which for a spine node folds in V-SRC-04 triangulation and
    # a counter-angle attempt (supersedes the r3 flat >=2 floor). One function.
    from ..docsdb import coverage as coverage_mod
    from ..validate.rules import v_src as _v_src

    spine_ids, _ = gv.spine()
    ctx = coverage_mod.build_context(paths, spine_ids)
    for rid in sorted(closure):
        n = gv.node_by_id.get(rid)
        if n is not None and n["node_type"] in ("fact", "mechanism"):
            ledger = coverage_mod.target_ledger(n, ctx)
            if not coverage_mod.meets_floor(ledger):
                failed.append("V-FRZ-02")
                detail["V-FRZ-02"] = coverage_mod.floor_line(ledger)
                # F13: the triangulation verdict comes from the ONE canonical fn
                # (v_src.check_triangulation -> coverage.triangulated) over the
                # same binding docmeta the ledger folded — no duplicate logic.
                if ledger["floor"]["required"] in ("spine_fact", "spine_mechanism", "bridge"):
                    docmeta = coverage_mod.binding_docmeta(n, ctx)
                    tri = _v_src.check_triangulation(docmeta)
                    if tri:
                        failed.append("V-SRC-04")
                        detail["V-SRC-04"] = f"{rid}: {tri[0].detail}"
                break

    # V-FRZ-03: no work item with status not in {committed, cancelled} touches it.
    for item in engine.load_items(paths):
        if item["status"] in ("committed", "cancelled"):
            continue
        if touches(gv, closure, item["target_id"]):
            failed.append("V-FRZ-03")
            detail["V-FRZ-03"] = (
                f"open work item {item['work_item_id']} ({item['status']}) touches {item['target_id']}"
            )
            break

    # V-FRZ-04: spine_freeze requires MSA checklist pass AND verify exit 0.
    if freeze_type == "spine_freeze":
        from ..graph import commands as graph_commands

        msa = graph_commands.msa_check(paths)
        if not msa["all_pass"]:
            failed.append("V-FRZ-04")
            missing = sorted(k for k, v in msa["msa"].items() if not v.get("pass"))
            detail["V-FRZ-04"] = f"msa-check failed: {', '.join(missing)}"
        else:
            try:
                verify_run(paths)
            except CorruptStateError as exc:
                failed.append("V-FRZ-04")
                detail["V-FRZ-04"] = f"verify exit 3: {', '.join(exc.errors)}"
    return failed, detail


# --- freeze / unfreeze ------------------------------------------------------


def _next_freeze_id(paths: Paths) -> str:
    existing = [r["freeze_id"] for r in jsonl.read_all(paths.resolve(FROZEN_ITEMS))]
    return next_id("FRZ", existing)


def _append_freeze_item(paths: Paths, item: dict[str, Any]) -> None:
    jsonl.append(paths.resolve(FROZEN_ITEMS), item)


def apply(paths: Paths, target: str, level: str, actor: str | None = None) -> dict[str, Any]:
    actor = actor or clock_actor()
    if level not in _LEVEL_TO_TYPE:
        raise DomainError([f"unknown freeze level: {level}"])
    freeze_type = _LEVEL_TO_TYPE[level]

    gv = graph_model.load(paths)
    if freeze_type != "spine_freeze" and gv.record(target) is None:
        raise DomainError([f"record not found: {target}"])

    closure = compute_closure(gv, freeze_type, target)
    if not closure and freeze_type != "spine_freeze":
        raise DomainError(["freeze closure empty"], data={"failed_rules": ["V-FRZ-01"]})

    failed, detail = _check_preconditions(paths, gv, freeze_type, closure)
    if failed:
        raise DomainError(failed, data={"failed_rules": failed, "detail": detail})

    allowed: set[str] = set()
    forbidden: set[str] = set()
    evidence: set[str] = set()
    for rid in closure:
        rec = gv.record(rid)
        ll = rec.get("language_limits")
        if ll:
            allowed |= set(ll.get("allowed", []) or [])
            forbidden |= set(ll.get("forbidden", []) or [])
        node = gv.node_by_id.get(rid)
        if node is not None:
            evidence |= set(node.get("evidence_bindings", []) or [])

    freeze_id = _next_freeze_id(paths)
    target_ids = sorted(closure)
    item = {
        "schema_version": "freeze_item.v1",
        "freeze_id": freeze_id,
        "project_id": paths.project_id,
        "action": "freeze",
        "freeze_type": freeze_type,
        "target_ids": target_ids,
        "evidence_ids": sorted(evidence),
        "allowed_language": sorted(allowed),
        "forbidden_language": sorted(forbidden),
        "revokes": None,
        "created_at": clock_now(),
    }
    _append_freeze_item(paths, item)
    commit = committer.freeze_batch(paths, target_ids, freeze_id, actor)
    return {"freeze_id": freeze_id, "commit_id": commit["commit_id"], "target_ids": target_ids}


def _covering_freeze(paths: Paths, target: str) -> Optional[dict[str, Any]]:
    """The newest FreezeItem whose target_ids contains ``target`` (append order)."""
    covering = None
    for it in jsonl.read_all(paths.resolve(FROZEN_ITEMS)):
        if target in it.get("target_ids", []):
            covering = it
    return covering


def unfreeze(paths: Paths, target: str, actor: str | None = None) -> dict[str, Any]:
    actor = actor or clock_actor()
    covering = _covering_freeze(paths, target)
    if covering is None or covering["action"] != "freeze":
        raise DomainError([f"no active freeze covering {target}"])

    freeze_id = _next_freeze_id(paths)
    target_ids = list(covering["target_ids"])
    item = {
        "schema_version": "freeze_item.v1",
        "freeze_id": freeze_id,
        "project_id": paths.project_id,
        "action": "unfreeze",
        "freeze_type": covering["freeze_type"],
        "target_ids": target_ids,
        "evidence_ids": [],
        "allowed_language": [],
        "forbidden_language": [],
        "revokes": covering["freeze_id"],
        "created_at": clock_now(),
    }
    _append_freeze_item(paths, item)
    commit = committer.unfreeze_batch(paths, target_ids, freeze_id, actor)
    return {"freeze_id": freeze_id, "commit_id": commit["commit_id"], "target_ids": target_ids}
