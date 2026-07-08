"""Compiler dry run (docs/06, docs/08 B9).

Builds the section plan, detects the five gap kinds by their mechanical triggers,
reports writing_ready, and reconciles the compile_queue gap items (V-CDR-01):
every NEW gap spawns exactly one item; re-running deduplicates and auto-cancels
items for gaps that no longer hold. The dry run appends nothing to graph/ or docs/
[V-CDR-02]; the section plan covers every spine node exactly once [V-CDR-03].

Reachability note (docs/06): a first dry run after a clean spine freeze reports
zero gaps by construction — the gap machinery here is exercised by V-CDR fixtures
that construct degenerate states directly.
"""

from __future__ import annotations

from typing import Any

from ..clock import actor as clock_actor
from ..clock import now as clock_now
from ..graph import model as graph_model
from ..ids import next_id
from ..paths import Paths
from ..queue import engine
from ..store import jsonl, snapshot
from ..textutil import scope_compatible
from . import section_plan as sp

DRY_RUNS = "compiler/dry_runs.jsonl"
FROZEN_ITEMS = "freeze/frozen_items.jsonl"
COMPILE_QUEUE = "compile_queue"
GAP_PREFIX = "GAP:"


# --- gap detection ----------------------------------------------------------


def _contract(paths: Paths) -> dict[str, Any]:
    if paths.project_contract.exists():
        return jsonl.read_json(paths.project_contract)
    return {}


def detect_gaps(
    paths: Paths, gv: graph_model.GraphView, spine_ids: set[str], plan: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    spine_nodes = [gv.node_by_id[i] for i in spine_ids if i in gv.node_by_id]
    spine_edges = [gv.edge_by_id[i] for i in spine_ids if i in gv.edge_by_id]

    # missing_evidence: spine fact/mechanism node below the S4 role-profile floor
    # (docs/17 — delegates to the same coverage function as V-FRZ-02 / MSA-4).
    from ..docsdb import coverage as coverage_mod

    ctx = coverage_mod.build_context(paths, spine_ids)
    for n in spine_nodes:
        if n["node_type"] in ("fact", "mechanism") and not coverage_mod.meets_floor(coverage_mod.target_ledger(n, ctx)):
            gaps.append({"kind": "missing_evidence", "target_id": n["node_id"], "note": "spine claim below the role-profile floor"})

    # unhandled_alternative: any alternative node not rejected and not parked(absorbed|not_needed).
    for n in gv.nodes:
        if n["node_type"] != "alternative":
            continue
        handled = n["lifecycle_state"] == "rejected" or (
            n["lifecycle_state"] == "parked" and n.get("state_reason") in ("absorbed", "not_needed")
        )
        if not handled:
            gaps.append({"kind": "unhandled_alternative", "target_id": n["node_id"], "note": ""})

    # weak_spine_edge: conditional spine edge with empty language_limits (v1 proxy).
    for e in spine_edges:
        if e.get("strength") == "conditional" and not e.get("language_limits"):
            gaps.append({"kind": "weak_spine_edge", "target_id": e["edge_id"], "note": "conditional edge without language limits"})

    # missing_section_claim: an expected section with zero nodes assigned.
    present = {entry["section_id"] for entry in plan}
    for sid in sp.EXPECTED_SECTIONS:
        if sid not in present:
            gaps.append({"kind": "missing_section_claim", "target_id": sid, "note": "template expects content here"})

    # contract_violation: spine node whose scope fails the contract compatibility check.
    contract_scope = _contract(paths).get("scope", {}) or {}
    for n in spine_nodes:
        if not scope_compatible(n.get("scope", {}) or {}, contract_scope):
            gaps.append({"kind": "contract_violation", "target_id": n["node_id"], "note": "scope incompatible with contract"})

    gaps.sort(key=lambda g: (g["kind"], g["target_id"]))
    return gaps


# --- writing_ready ----------------------------------------------------------


def _active_spine_freeze(paths: Paths) -> bool:
    items = jsonl.read_all(paths.resolve(FROZEN_ITEMS))
    revoked = {it["revokes"] for it in items if it["action"] == "unfreeze" and it.get("revokes")}
    return any(
        it["action"] == "freeze" and it["freeze_type"] == "spine_freeze" and it["freeze_id"] not in revoked
        for it in items
    )


def spine_freeze_current(paths: Paths, gv: graph_model.GraphView, spine_ids: set[str]) -> bool:
    """A spine_freeze is current iff an un-revoked spine_freeze exists and every
    current spine record is frozen (docs/06 writing_ready binding)."""
    if not spine_ids:
        return False
    if not _active_spine_freeze(paths):
        return False
    for i in spine_ids:
        rec = gv.record(i)
        if rec is None or not rec.get("frozen"):
            return False
    return True


# --- compile_queue gap reconciliation (V-CDR-01) ----------------------------


def _open_gap_items(paths: Paths) -> dict[tuple[str, str], dict[str, Any]]:
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for item in engine.load_items(paths):
        if item["queue_name"] != COMPILE_QUEUE:
            continue
        if item["status"] in ("committed", "cancelled"):
            continue
        task_id = item.get("task_id") or ""
        if not task_id.startswith(GAP_PREFIX):
            continue
        _, kind, target = task_id.split(":", 2)
        out[(kind, target)] = item
    return out


def _reconcile_gap_items(paths: Paths, gaps: list[dict[str, Any]], actor: str) -> dict[str, list[str]]:
    want = {(g["kind"], g["target_id"]) for g in gaps}
    open_items = _open_gap_items(paths)
    enqueued: list[str] = []
    cancelled: list[str] = []
    for g in gaps:
        key = (g["kind"], g["target_id"])
        if key in open_items:
            continue
        item = engine.enqueue(
            paths,
            queue_name=COMPILE_QUEUE,
            target_type="gap",
            target_id=g["target_id"],
            task_id=f"{GAP_PREFIX}{g['kind']}:{g['target_id']}",
            actor=actor,
        )
        enqueued.append(item["work_item_id"])
    for key, item in open_items.items():
        if key not in want:
            engine.cancel(paths, item["work_item_id"], actor, detail={"reason": "gap_resolved"})
            cancelled.append(item["work_item_id"])
    return {"enqueued": enqueued, "cancelled": cancelled}


# --- entry point ------------------------------------------------------------


def dry_run(paths: Paths, actor: str | None = None) -> dict[str, Any]:
    actor = actor or clock_actor()
    gv = graph_model.load(paths)
    spine_ids, _ = gv.spine()
    plan = sp.build(gv, spine_ids)
    gaps = detect_gaps(paths, gv, spine_ids, plan)

    snapshot_id = snapshot.latest_snapshot_id(paths) or "GS-000001"
    writing_ready = (not gaps) and spine_freeze_current(paths, gv, spine_ids)

    run_id = next_id("CDR", [r["run_id"] for r in jsonl.read_all(paths.resolve(DRY_RUNS))])
    record = {
        "schema_version": "compiler_dry_run.v1",
        "run_id": run_id,
        "project_id": paths.project_id,
        "snapshot_id": snapshot_id,
        "writing_ready": writing_ready,
        "section_plan": plan,
        "gaps": gaps,
        "created_at": clock_now(),
    }
    jsonl.append(paths.resolve(DRY_RUNS), record)

    reconciled = _reconcile_gap_items(paths, gaps, actor)
    out = dict(record)
    out["gap_items_enqueued"] = reconciled["enqueued"]
    out["gap_items_cancelled"] = reconciled["cancelled"]
    return out
