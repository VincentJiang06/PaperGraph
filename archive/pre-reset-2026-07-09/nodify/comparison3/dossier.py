"""Render an nd tree session into the uniform Investigation Dossier template
(docs/10 §4.1), deterministically, from the canonical JSONL records. This is the
judged artifact for the skill+tree arm; the skill-only arm writes its dossier to the
SAME template by hand, so the blind judge compares content, not format.

Usage: python3 dossier.py <path-to-arm-workspace>   # expects sessions/cmp/…
Writes <workspace>/dossier.md and prints it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def latest(records):
    """Append-only log → latest record per id-key."""
    out = {}
    for r in records:
        k = r.get("node_id") or r.get("synthesis_id") or r.get("doc_id")
        out[k] = r
    return out


def load(p):
    p = Path(p)
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.is_file() else []


def synth_for(node_id, synth_by_node):
    """Latest synthesis for a node (highest synthesis_id wins; revises chain)."""
    cands = synth_by_node.get(node_id, [])
    return sorted(cands, key=lambda s: s["synthesis_id"])[-1] if cands else None


def evidence_lines(syn, doc_map=None):
    doc_map = doc_map or {}
    out = []
    for e in (syn or {}).get("based_on", {}).get("evidence", []) or []:
        did = e.get("doc_id")
        doc = doc_map.get(did, {})
        # evidence entry may leave url/title null and rely on doc_id → docs index
        title = e.get("title") or doc.get("title") or did or e.get("ref_id") or "source"
        url = e.get("url") or doc.get("url") or ""
        q = (e.get("quote") or "").strip().replace("\n", " ")
        out.append(f'      - {title} — {url}' + (f' — "{q}"' if q else ""))
    return out


def render_node(nid, label, nodes, children, synth_by_node, depth, lines, doc_map):
    # label is neutral L-notation (L1, L1.1, …) so the dossier does not leak that
    # it came from a tree (node-ids / kind tags are tree tells).
    n = nodes[nid]
    syn = synth_for(nid, synth_by_node)
    orient = n.get("orientation") or "neutral"
    head = "  " * (depth - 1)
    lines.append(f'{head}### {label} [orientation: {orient}]')
    lines.append(f'{head}  - statement: {n.get("statement","").strip()}')
    if syn:
        lines.append(f'{head}  - conclusion: [{syn.get("lean","?")}/{syn.get("confidence","?")}] {syn.get("summary","").strip()}')
        ev = evidence_lines(syn, doc_map)
        if ev:
            lines.append(f'{head}  - evidence:')
            lines.extend(ev)
    elif n.get("status") in ("stuck", "retired"):
        lines.append(f'{head}  - {n.get("status")}: {n.get("status_note") or n.get("stuck_reason") or ""}')
    for i, c in enumerate(children.get(nid, []), 1):
        render_node(c, f"{label}.{i}", nodes, children, synth_by_node, depth + 1, lines, doc_map)


def main(ws: str):
    ws = Path(ws)
    tree = ws / "sessions" / "cmp" / "tree"
    nodes = latest(load(tree / "nodes.jsonl"))
    synth = load(tree / "syntheses.jsonl")
    synth_by_node = {}
    for s in synth:
        synth_by_node.setdefault(s["node_id"], []).append(s)
    # doc_id -> {url,title} so evidence entries that left url null still resolve
    doc_map = {d["doc_id"]: d for d in load(ws / "sessions" / "cmp" / "docs" / "index.jsonl")}

    children = {}
    root = None
    for nid, n in nodes.items():
        p = n.get("parent_id")
        if p is None:
            root = nid
        else:
            children.setdefault(p, []).append(nid)
    for k in children:
        children[k].sort()

    q = nodes[root].get("statement", "") if root else ""
    lines = [f"# Investigation: {q}", "", "## Lines of inquiry", ""]
    for i, l1 in enumerate(children.get(root, []), 1):
        render_node(l1, f"L{i}", nodes, children, synth_by_node, 1, lines, doc_map)
        lines.append("")

    # dead ends (no node-ids — those are tree tells)
    dead = [n for n in nodes.values() if n.get("status") in ("retired", "stuck")]
    if dead:
        lines += ["## Dead ends / retired", ""]
        for n in dead:
            lines.append(f'  - {n.get("statement","")[:80]} — {n.get("status")}: {n.get("status_note") or n.get("stuck_reason") or ""}')
        lines.append("")

    # root conclusion + open gaps
    rsyn = synth_for(root, synth_by_node) if root else None
    lines += ["## Root conclusion", ""]
    if rsyn:
        lines.append(f'[{rsyn.get("lean","?")}/{rsyn.get("confidence","?")}] {rsyn.get("summary","").strip()}')
        gaps = rsyn.get("open_questions") or []
        if gaps:
            lines += ["", "## Open gaps", ""] + [f"  - {g}" for g in gaps]
    else:
        lines.append("(no root synthesis — investigation did not converge)")

    out = "\n".join(lines).rstrip() + "\n"
    (ws / "dossier.md").write_text(out, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
