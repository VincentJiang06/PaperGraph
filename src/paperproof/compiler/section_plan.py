"""The `single_event_mechanism` section-plan template (docs/06).

Deterministic assignment: every spine node to exactly one section by node_type,
ordered within a section by (layer asc, node_id asc). Empty sections are dropped
from the plan (SEC-introduction emptiness surfaces as a missing_section_claim gap
in the dry run, not as a dropped section).
"""

from __future__ import annotations

from typing import Any

from ..graph import model as graph_model

# Template order + roles (docs/06). SEC-alternatives / SEC-conclusion carry no
# spine nodes, so they never appear in a node-covering section plan.
TEMPLATE_ORDER = [
    "SEC-introduction",
    "SEC-concepts",
    "SEC-mechanism",
    "SEC-evidence",
    "SEC-alternatives",
    "SEC-conclusion",
]

ROLE_BY_SECTION = {
    "SEC-introduction": "introduction",
    "SEC-concepts": "concepts",
    "SEC-mechanism": "mechanism",
    "SEC-evidence": "evidence",
    "SEC-alternatives": "alternatives",
    "SEC-conclusion": "conclusion",
}

# node_type -> the single section it belongs to.
NODE_TYPE_SECTION = {
    "question": "SEC-introduction",
    "thesis": "SEC-introduction",
    "definition": "SEC-concepts",
    "mechanism": "SEC-mechanism",
    "fact": "SEC-evidence",
}

# Sections the template always expects to carry content (docs/06).
EXPECTED_SECTIONS = ("SEC-introduction",)


def _sorted_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(nodes, key=lambda n: (n["layer"], n["node_id"]))


def assign(gv: graph_model.GraphView, spine_ids: set[str]) -> dict[str, list[dict[str, Any]]]:
    """Bucket spine nodes into template sections (raw records, sorted)."""
    buckets: dict[str, list[dict[str, Any]]] = {sid: [] for sid in TEMPLATE_ORDER}
    for nid in spine_ids:
        node = gv.node_by_id.get(nid)
        if node is None:
            continue
        section = NODE_TYPE_SECTION.get(node["node_type"])
        if section is not None:
            buckets[section].append(node)
    return {sid: _sorted_nodes(ns) for sid, ns in buckets.items()}


def build(gv: graph_model.GraphView, spine_ids: set[str]) -> list[dict[str, Any]]:
    """Section plan: node-bearing template sections, in template order."""
    buckets = assign(gv, spine_ids)
    plan: list[dict[str, Any]] = []
    for sid in TEMPLATE_ORDER:
        nodes = buckets[sid]
        if not nodes:
            continue
        plan.append(
            {
                "section_id": sid,
                "role": ROLE_BY_SECTION[sid],
                "nodes": [n["node_id"] for n in nodes],
            }
        )
    return plan
