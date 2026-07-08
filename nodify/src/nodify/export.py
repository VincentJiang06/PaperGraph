"""nd export — the full tree + syntheses for downstream renderers (a paper
compiler, a decision memo, a postmortem). JSON is the machine form; md is a
human-readable outline. Raw process text was never state, so it isn't here."""

from __future__ import annotations

from typing import Any

from . import tree
from .paths import Paths


def as_json(paths: Paths, session: dict[str, Any]) -> dict[str, Any]:
    nodes = tree.nodes_by_id(paths)
    return {
        "session": session,
        "nodes": [nodes[k] for k in sorted(nodes)],
        "syntheses": tree.syntheses(paths),
    }


def _node_md(paths: Paths, nodes: dict, node_id: str, depth: int, lines: list[str]) -> None:
    n = nodes[node_id]
    syn = tree.latest_synthesis(paths, node_id)
    indent = "  " * depth
    mark = {"viewpoint": "○", "claim": "●"}[n["kind"]]
    lines.append(f"{indent}- {mark} **{n['node_id']}** ({n['status']}) {n['statement']}")
    if syn:
        lines.append(f"{indent}  - ⇒ [{syn['lean']}/{syn['confidence']}] {syn['summary']}")
        for ref in syn["based_on"]["evidence"]:
            where = ref["url"] or ref["locator"] or "(no source pointer)"
            lines.append(f"{indent}    - {ref['ref_id']}: {ref['title']} — {where}")
    for child in tree.children_of(nodes, node_id):
        _node_md(paths, nodes, child["node_id"], depth + 1, lines)


def as_markdown(paths: Paths, session: dict[str, Any]) -> str:
    nodes = tree.nodes_by_id(paths)
    lines = [f"# {session['question']}", ""]
    roots = sorted((n for n in nodes.values() if n["parent_id"] is None),
                   key=lambda n: n["node_id"])
    for root in roots:
        _node_md(paths, nodes, root["node_id"], 0, lines)
    return "\n".join(lines) + "\n"
