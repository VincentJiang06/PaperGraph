"""nd check — hard errors (broken structure) vs soft warnings (visible
laziness). The generalized framework cannot forbid lazy thinking; it makes it
visible instead. Hard list and soft list are pinned by the design doc §7."""

from __future__ import annotations

from typing import Any

from . import docsdb, store, tree
from .paths import NODES, SYNTHESES, Paths
from .schemas import validate


def run(paths: Paths, session: dict[str, Any]) -> tuple[list[str], list[str]]:
    hard: list[str] = []
    soft: list[str] = []

    node_records = store.read_all(paths.resolve(NODES))
    syn_records = store.read_all(paths.resolve(SYNTHESES))
    doc_records = store.read_all(paths.resolve(docsdb.INDEX))
    for rec in node_records + syn_records + doc_records:
        hard += validate(rec)
    # bail before structural checks if any record is schema-invalid: the
    # accessors below assume well-formed records, so proceeding would CRASH on
    # a malformed (e.g. out-of-band-forged) record instead of reporting it.
    if hard:
        return sorted(hard), []

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

    # --- docs store (V2): archives must stay whole and referenced ---
    entries = store.latest_by_id(paths.resolve(docsdb.INDEX), "doc_id")
    for e in entries.values():
        if not paths.resolve(e["text_file"]).is_file():
            hard.append(f"{e['doc_id']}: archived text missing: {e['text_file']}")
        for b in e["bindings"]:
            if b["node_id"] not in nodes:
                hard.append(f"{e['doc_id']}: binding to unknown node {b['node_id']}")
    for s in syn_records:
        for ref in s["based_on"]["evidence"]:
            doc_id = ref.get("doc_id")
            if doc_id is None:
                continue
            if doc_id not in entries:
                hard.append(f"{s['synthesis_id']}/{ref['ref_id']}: dangling doc_id {doc_id}")
            elif ref.get("quote") and paths.resolve(entries[doc_id]["text_file"]).is_file() \
                    and not docsdb.quote_ok(paths, entries[doc_id], ref["quote"]):
                hard.append(f"{s['synthesis_id']}/{ref['ref_id']}: stored quote no longer "
                            f"matches the archived text of {doc_id} (tampering?)")

    # --- article layer (V3) ---
    from . import article
    syn_ids = {s["synthesis_id"] for s in syn_records}
    a_hard, a_soft = article.check(paths, nodes, syn_ids, entries)
    hard += a_hard
    soft += a_soft

    # --- soft: laziness made visible ---
    ACTIVE = {"open", "expanding", "pending", "investigating"}
    DEAD_ANCESTOR = {"retired", "closed"}
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
        # retire hygiene (R5): an active node stranded under a retired/closed
        # ancestor — one warning per orphan, naming the nearest dead ancestor.
        if n["status"] in ACTIVE:
            cur = n
            while cur["parent_id"] in nodes:
                cur = nodes[cur["parent_id"]]
                if cur["status"] in DEAD_ANCESTOR:
                    soft.append(f"{n['node_id']} ({n['status']}) is active under "
                                f"{cur['status']} ancestor {cur['node_id']} — "
                                "retire or re-parent it")
                    break
    for s in syn_records:
        b = s["based_on"]
        if not b["children"] and not b["evidence"]:
            soft.append(f"{s['synthesis_id']}: based_on is empty (conclusion from nothing?)")
        for ref in b["evidence"]:
            if ref["url"] is None and ref["locator"] is None and ref.get("doc_id") is None:
                soft.append(f"{s['synthesis_id']}/{ref['ref_id']}: evidence has "
                            "neither doc_id nor url nor locator")
            # R9: a verbatim quote is only trustworthy if verifiable against an
            # archived doc — a quote with no doc_id is "trust me". Make it visible.
            if ref.get("quote") and ref.get("doc_id") is None:
                soft.append(f"{s['synthesis_id']}/{ref['ref_id']}: quote is not "
                            "verifiable (no doc_id — archive the source to verify it)")
    return sorted(hard), sorted(soft)
