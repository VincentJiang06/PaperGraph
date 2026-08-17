"""Compiler draft map (docs/06, docs/08 B10).

Only when the latest dry run is writing_ready. Fully derived from the frozen
graph + the dry run: same inputs => byte-identical DraftMap. Enqueues one
compile_queue prose item per section (task_id PROSE-<section_id>, output
agent_outputs/prose/<section_id>.md).
"""

from __future__ import annotations

from typing import Any

from ..clock import actor as clock_actor
from ..clock import now as clock_now
from ..errors import DomainError
from ..graph import model as graph_model
from ..ids import next_id
from ..paths import Paths
from ..queue import engine
from ..store import jsonl

DRAFT_MAPS = "compiler/draft_maps.jsonl"
DRY_RUNS = "compiler/dry_runs.jsonl"
COMPILE_QUEUE = "compile_queue"


def _latest_dry_run(paths: Paths) -> dict[str, Any] | None:
    runs = jsonl.read_all(paths.resolve(DRY_RUNS))
    return runs[-1] if runs else None


def _node_language(node: dict[str, Any]) -> tuple[list[str], list[str]]:
    ll = node.get("language_limits") or {}
    return list(ll.get("allowed", []) or []), list(ll.get("forbidden", []) or [])


def _edge_order(gv: graph_model.GraphView, spine_ids: set[str], node_ids: set[str]) -> list[str]:
    """Spine edges whose both endpoints sit in this section, ordered by
    (source_node_id, target_node_id)."""
    edges = []
    for eid in spine_ids:
        e = gv.edge_by_id.get(eid)
        if e is None:
            continue
        if e["source_node_id"] in node_ids and e["target_node_id"] in node_ids:
            edges.append(e)
    edges.sort(key=lambda e: (e["source_node_id"], e["target_node_id"]))
    return [e["edge_id"] for e in edges]


def draft_map(paths: Paths, actor: str | None = None) -> dict[str, Any]:
    actor = actor or clock_actor()
    latest = _latest_dry_run(paths)
    if latest is None or not latest.get("writing_ready"):
        raise DomainError(["draft-map requires a writing_ready dry run"], data={"failed_rules": ["V-CDR"]})

    gv = graph_model.load(paths)
    spine_ids, _ = gv.spine()
    plan = latest["section_plan"]

    sections: list[dict[str, Any]] = []
    for entry in plan:
        section_id = entry["section_id"]
        node_ids = list(entry["nodes"])
        claims = []
        for nid in node_ids:
            node = gv.node_by_id.get(nid)
            if node is None:
                continue
            allowed, forbidden = _node_language(node)
            claims.append(
                {
                    "node_id": nid,
                    "claim": node["claim"],
                    "evidence_ids": list(node.get("evidence_bindings", []) or []),
                    "allowed_language": allowed,
                    "forbidden_language": forbidden,
                }
            )
        sections.append(
            {
                "section_id": section_id,
                "role": entry["role"],
                "claims": claims,
                "edge_order": _edge_order(gv, spine_ids, set(node_ids)),
            }
        )

    draft_map_id = next_id("DRAFTMAP", [r["draft_map_id"] for r in jsonl.read_all(paths.resolve(DRAFT_MAPS))])
    record = {
        "schema_version": "draft_map.v1",
        "draft_map_id": draft_map_id,
        "project_id": paths.project_id,
        "based_on_dry_run": latest["run_id"],
        "sections": sections,
        "created_at": clock_now(),
    }
    jsonl.append(paths.resolve(DRAFT_MAPS), record)

    enqueued: list[str] = []
    for entry in plan:
        section_id = entry["section_id"]
        output = f"agent_outputs/prose/{section_id}.md"
        item = engine.enqueue(
            paths,
            queue_name=COMPILE_QUEUE,
            target_type="section",
            target_id=section_id,
            task_id=f"PROSE-{section_id}",
            output_files=[output],
            actor=actor,
        )
        enqueued.append(item["work_item_id"])

    out = dict(record)
    out["prose_items"] = enqueued
    return out


def load_draft_map(paths: Paths, draft_map_id: str) -> dict[str, Any] | None:
    for r in jsonl.read_all(paths.resolve(DRAFT_MAPS)):
        if r["draft_map_id"] == draft_map_id:
            return r
    return None


def latest_draft_map(paths: Paths) -> dict[str, Any] | None:
    runs = jsonl.read_all(paths.resolve(DRAFT_MAPS))
    return runs[-1] if runs else None
