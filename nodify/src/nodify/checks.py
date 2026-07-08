"""nd check — hard errors (broken structure) vs soft warnings (visible
laziness). The generalized framework cannot forbid lazy thinking; it makes it
visible instead. Hard list and soft list are pinned by the design doc §7."""

from __future__ import annotations

from typing import Any

from . import store, tree
from .paths import NODES, SYNTHESES, Paths
from .schemas import validate


def run(paths: Paths, session: dict[str, Any]) -> tuple[list[str], list[str]]:
    hard: list[str] = []
    soft: list[str] = []

    node_records = store.read_all(paths.resolve(NODES))
    syn_records = store.read_all(paths.resolve(SYNTHESES))
    for rec in node_records + syn_records:
        hard += validate(rec)

    nodes = store.latest_by_id(paths.resolve(NODES), "node_id")

    roots = [n for n in nodes.values() if n["parent_id"] is None]
    if len(roots) > 1:
        hard.append(f"multiple roots: {sorted(n['node_id'] for n in roots)}")

    for n in nodes.values():
        if n["parent_id"] is not None and n["parent_id"] not in nodes:
            hard.append(f"{n['node_id']}: dangling parent_id {n['parent_id']}")
        if n["revises"] is not None and n["revises"] not in nodes:
            hard.append(f"{n['node_id']}: dangling revises {n['revises']}")

    syn_ids = {s["synthesis_id"] for s in syn_records}
    concluded_with_syn = {s["node_id"] for s in syn_records}
    for s in syn_records:
        if s["node_id"] not in nodes:
            hard.append(f"{s['synthesis_id']}: dangling node_id {s['node_id']}")
        for child in s["based_on"]["children"]:
            if child not in nodes:
                hard.append(f"{s['synthesis_id']}: dangling based_on child {child}")
        if s["revises"] is not None and s["revises"] not in syn_ids:
            hard.append(f"{s['synthesis_id']}: dangling revises {s['revises']}")

    budgets = session["budgets"]
    if not hard:  # depth walk needs intact parents
        for n in nodes.values():
            if tree.depth_of(nodes, n["node_id"]) > budgets["max_depth"]:
                hard.append(f"{n['node_id']}: exceeds max_depth={budgets['max_depth']}")
    for n in nodes.values():
        kids = tree.children_of(nodes, n["node_id"])
        if len(kids) > budgets["max_children"]:
            hard.append(f"{n['node_id']}: {len(kids)} children exceeds "
                        f"max_children={budgets['max_children']}")
    open_claims = tree._open_claims(nodes)
    if open_claims > budgets["max_open_claims"]:
        hard.append(f"{open_claims} open claims exceeds "
                    f"max_open_claims={budgets['max_open_claims']}")

    # --- soft: laziness made visible ---
    for n in nodes.values():
        kids = tree.children_of(nodes, n["node_id"])
        if (n["kind"] == "viewpoint" and kids
                and not any(k["orientation"] == "adversarial" for k in kids)):
            soft.append(f"{n['node_id']}: expanded without an adversarial direction")
        if n["status"] in ("retired", "stuck", "closed") and not n["status_note"]:
            soft.append(f"{n['node_id']}: {n['status']} without a status_note")
        if n["kind"] == "claim" and n["status"] == "concluded" \
                and n["node_id"] not in concluded_with_syn:
            soft.append(f"{n['node_id']}: concluded claim has no synthesis")
    for s in syn_records:
        b = s["based_on"]
        if not b["children"] and not b["evidence"]:
            soft.append(f"{s['synthesis_id']}: based_on is empty (conclusion from nothing?)")
        for ref in b["evidence"]:
            if ref["url"] is None and ref["locator"] is None:
                soft.append(f"{s['synthesis_id']}/{ref['ref_id']}: evidence has "
                            "neither url nor locator")
    return sorted(hard), sorted(soft)
