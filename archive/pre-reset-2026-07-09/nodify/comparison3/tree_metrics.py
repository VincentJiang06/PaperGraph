"""Mechanical metrics for the aggressive-research eval, per arm. Where the tree arm
has exact records, use them; for the skill-only arm, parse the dossier/log. Metrics are
descriptive and intentionally asymmetric (the tree exposes more structure) — the blind
judge is the primary instrument; these quantify coverage, grounding, and sprawl.

Usage: python3 tree_metrics.py <base>   # base has runs/<topic>/{tree,notree}/
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def load(p):
    p = Path(p)
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.is_file() else []


def latest(recs, key):
    out = {}
    for r in recs:
        out[r[key]] = r
    return out


def tree_metrics(ws: Path) -> dict:
    t = ws / "sessions" / "cmp" / "tree"
    nodes = latest(load(t / "nodes.jsonl"), "node_id")
    synth = load(t / "syntheses.jsonl")
    docs = load(ws / "sessions" / "cmp" / "docs" / "index.jsonl")
    viewpoints = [n for n in nodes.values() if n.get("kind") == "viewpoint"]
    claims = [n for n in nodes.values() if n.get("kind") == "claim"]
    adversarial = [n for n in nodes.values() if n.get("orientation") == "adversarial"]
    dead = [n for n in nodes.values() if n.get("status") in ("stuck", "retired")]
    # grounding: syntheses whose based_on.evidence is non-empty
    syn_by_node = {}
    for s in synth:
        syn_by_node.setdefault(s["node_id"], []).append(s)
    latest_syn = [sorted(v, key=lambda s: s["synthesis_id"])[-1] for v in syn_by_node.values()]
    grounded = [s for s in latest_syn if (s.get("based_on", {}).get("evidence"))]
    # depth via parent chain
    def depth(nid, seen=()):
        p = nodes[nid].get("parent_id")
        return 0 if p is None or p not in nodes or nid in seen else 1 + depth(p, seen + (nid,))
    max_depth = max((depth(nid) for nid in nodes), default=0)
    # sprawl: notes bytes
    notes = ws / "sessions" / "cmp" / "notes"
    notes_bytes = sum(f.stat().st_size for f in notes.rglob("*") if f.is_file()) if notes.is_dir() else 0
    return {
        "arm": "tree",
        "lines_of_inquiry": len(viewpoints),
        "claims": len(claims),
        "adversarial_branches": len(adversarial),
        "max_depth": max_depth,
        "dead_ends": len(dead),
        "docs_archived": len({d["doc_id"] for d in docs}),
        "syntheses": len(latest_syn),
        "grounded_syntheses": len(grounded),
        "grounding_rate": round(len(grounded) / len(latest_syn), 3) if latest_syn else None,
        "notes_bytes": notes_bytes,
    }


def notree_metrics(ws: Path) -> dict:
    dossier = (ws / "dossier.md")
    text = dossier.read_text(encoding="utf-8") if dossier.is_file() else ""
    lines_inq = len(re.findall(r'(?m)^\s*###\s+L\d', text))
    adversarial = len(re.findall(r'orientation:\s*adversarial', text))
    ev_items = len(re.findall(r'—\s*https?://', text))
    grounded_lines = len(re.findall(r'(?mi)^\s*-\s*evidence:', text))
    dead = 1 if re.search(r'##\s*Dead ends', text) else 0
    conv = 1 if re.search(r'##\s*Root conclusion', text) and "did not converge" not in text else 0
    srcdir = ws / "sources"
    sources = len(list(srcdir.glob("*"))) if srcdir.is_dir() else 0
    log = ws / "log.md"
    log_bytes = log.stat().st_size if log.is_file() else 0
    return {
        "arm": "notree",
        "lines_of_inquiry": lines_inq,
        "adversarial_branches": adversarial,
        "evidence_items": ev_items,
        "grounded_lines": grounded_lines,
        "distinct_sources": sources,
        "converged": bool(conv),
        "has_dead_ends": bool(dead),
        "log_bytes": log_bytes,
    }


def main(base: str):
    base = Path(base)
    out = {}
    for topic_dir in sorted((base / "runs").glob("*")):
        if not topic_dir.is_dir():
            continue
        t = topic_dir.name
        out[t] = {}
        if (topic_dir / "tree" / "sessions" / "cmp").is_dir():
            out[t]["tree"] = tree_metrics(topic_dir / "tree")
        if (topic_dir / "notree" / "dossier.md").is_file():
            out[t]["notree"] = notree_metrics(topic_dir / "notree")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
