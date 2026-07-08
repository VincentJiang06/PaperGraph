"""ProofTask bundle builder (docs/08 B4).

For a queued or stale proof work item, build the three immutable bundle files
(ProofTask, ContextPack, DocsPack) at the next -rN revision and attach them to
the item. The bundle is self-contained: target verbatim + 1-hop neighborhood +
claim_digest of every non-rejected node + prior verdict records + contract scope.
Bundle files are never overwritten (immutability); rebuilds write new files.
"""

from __future__ import annotations

import re
from typing import Any

from ..clock import actor as clock_actor
from ..docsdb import pack as docs_pack_builder
from ..graph import model as graph_model
from ..ids import bundle_id, next_bundle_revision
from ..paths import Paths
from ..queue import engine
from ..store import jsonl, snapshot
from ..schemas.docs import DocsPack
from ..schemas.proof import ContextPack, ProofTask

PROOF_RESULTS = "proof/proof_results.jsonl"


def _existing_pt_ids(paths: Paths, target_id: str) -> list[str]:
    tasks_dir = paths.resolve("proof/tasks")
    if not tasks_dir.exists():
        return []
    prefix = f"PT-{target_id}"
    out: list[str] = []
    for p in tasks_dir.glob("PT-*.json"):
        stem = p.stem
        if stem == prefix or re.match(rf"^{re.escape(prefix)}-r\d+$", stem):
            out.append(stem)
    return out


def _contract(paths: Paths) -> dict[str, Any]:
    if paths.project_contract.exists():
        return jsonl.read_json(paths.project_contract)
    return {}


def _prior_results(paths: Paths, target_id: str) -> list[dict[str, Any]]:
    return [
        r
        for r in jsonl.read_all(paths.resolve(PROOF_RESULTS))
        if r.get("target_id") == target_id
    ]


def build_bundle(paths: Paths, work_item: dict[str, Any]) -> dict[str, Any]:
    """Build the next-revision bundle for a work item; write the three files.

    Returns {task_id, bundle, output_files, revision, based_on_snapshot}.
    """
    target_id = work_item["target_id"]
    target_type = work_item["target_type"]
    task_type = "EDGE_CHECK" if target_type == "edge" else "NODE_CHECK"

    gv = graph_model.load(paths)
    target_record = gv.record(target_id)
    if target_record is None:
        raise ValueError(f"target not found in graph: {target_id}")

    revision = next_bundle_revision("PT", target_id, _existing_pt_ids(paths, target_id))
    pt_id = bundle_id("PT", target_id, revision)
    ctx_id = bundle_id("CTX", target_id, revision)
    dp_id = bundle_id("DOCSPACK", target_id, revision)

    task_file = f"proof/tasks/{pt_id}.json"
    context_pack = f"proof/context/{ctx_id}.json"
    docs_pack = f"docs/docspacks/{dp_id}.json"
    output_file = f"agent_outputs/proof_results/{pt_id}.proof_result.json"

    if target_type == "edge":
        target_ref = {
            "edge_id": target_id,
            "source_node_id": target_record["source_node_id"],
            "target_node_id": target_record["target_node_id"],
        }
    else:
        target_ref = {"node_id": target_id}

    task = ProofTask(
        task_id=pt_id,
        project_id=paths.project_id,
        task_type=task_type,
        target=target_ref,
        context_pack=context_pack,
        docs_pack=docs_pack,
        output_file=output_file,
    )

    neighbor_nodes, neighbor_edges = gv.one_hop(target_id)
    contract = _contract(paths)
    based_on = snapshot.latest_snapshot_id(paths) or "GS-000001"

    # S4 (docs/17, V-COV-02): embed the target's coverage ledger line for a
    # fact/mechanism/bridge target so the worker sees whether search is exhausted.
    coverage_block = None
    if target_type == "node" and (
        target_record.get("node_type") in ("fact", "mechanism")
        or (target_record.get("origin") or {}).get("kind") == "bridge"
    ):
        from ..docsdb import coverage as coverage_mod

        spine_ids, _ = gv.spine()
        cov_ctx = coverage_mod.build_context(paths, spine_ids)
        coverage_block = coverage_mod.target_ledger(target_record, cov_ctx)

    ctx = ContextPack(
        pack_id=ctx_id,
        task_id=pt_id,
        project_id=paths.project_id,
        based_on_snapshot=based_on,
        target=target_record,
        neighbor_nodes=neighbor_nodes,
        neighbor_edges=neighbor_edges,
        claim_digest=gv.claim_digest(),
        contract_scope=contract.get("scope", {}) or {},
        forbidden_claims=list(contract.get("forbidden_claims", []) or []),
        prior_results=_prior_results(paths, target_id),
        coverage=coverage_block,
    )

    # DocsPack assembled by the matcher (docs/04): the EvidenceUnits selected for
    # this target claim + their documents' metadata. Empty when nothing archived
    # yet (M1 behaviour) — an empty DocsPack is valid.
    evidence_units, documents_meta = docs_pack_builder.assemble(paths, target_record)
    docspack = DocsPack(
        pack_id=dp_id,
        task_id=pt_id,
        project_id=paths.project_id,
        evidence_units=evidence_units,
        documents_meta=documents_meta,
    )

    jsonl.write_json(paths.resolve(task_file), task)
    jsonl.write_json(paths.resolve(context_pack), ctx)
    jsonl.write_json(paths.resolve(docs_pack), docspack)

    return {
        "task_id": pt_id,
        "bundle": {"task_file": task_file, "context_pack": context_pack, "docs_pack": docs_pack},
        "output_files": [output_file],
        "revision": revision,
        "based_on_snapshot": based_on,
    }


def build_frontier(paths: Paths, actor: str | None = None) -> dict[str, Any]:
    """Build/rebuild bundles for every claimable-or-stale proof item (docs/10 §4).

    Queued items with no bundle get their first bundle (no status change); stale
    items are rebuilt at the next revision (stale -> queued|blocked)."""
    actor = actor or clock_actor()
    engine.run_sweeps(paths, actor)
    built: list[dict[str, Any]] = []
    gv = graph_model.load(paths)
    by_id = engine.items_by_id(paths)
    for item in list(by_id.values()):
        if item["queue_name"] != "proof_queue":
            continue
        if item["status"] == "queued" and item.get("bundle") is None:
            info = build_bundle(paths, item)
            engine.attach_bundle(paths, item["work_item_id"], info["task_id"], info["bundle"], info["output_files"])
            built.append({"work_item_id": item["work_item_id"], "task_id": info["task_id"], "revision": info["revision"]})
        elif item["status"] == "stale":
            info = build_bundle(paths, item)
            to_blocked = _should_block(paths, item, gv, by_id)
            engine.rebuild(
                paths,
                item["work_item_id"],
                actor,
                to_blocked=to_blocked,
                changes={"task_id": info["task_id"], "bundle": info["bundle"], "output_files": info["output_files"]},
            )
            built.append({"work_item_id": item["work_item_id"], "task_id": info["task_id"], "revision": info["revision"]})
    return {"bundles_built": built, "count": len(built)}


def build_one(paths: Paths, target_id: str, actor: str | None = None) -> dict[str, Any]:
    """`proof build-task <target-id>`: one bundle for the open item of a target."""
    actor = actor or clock_actor()
    by_id = engine.items_by_id(paths)
    candidates = [
        i
        for i in by_id.values()
        if i["target_id"] == target_id
        and i["queue_name"] == "proof_queue"
        and i["status"] in ("queued", "blocked", "stale")
    ]
    if not candidates:
        raise ValueError(f"no open proof work item for target {target_id}")
    item = min(candidates, key=lambda i: i["work_item_id"])
    info = build_bundle(paths, item)
    if item["status"] == "stale":
        gv = graph_model.load(paths)
        engine.rebuild(
            paths, item["work_item_id"], actor,
            to_blocked=_should_block(paths, item, gv, by_id),
            changes={"task_id": info["task_id"], "bundle": info["bundle"], "output_files": info["output_files"]},
        )
    else:
        engine.attach_bundle(paths, item["work_item_id"], info["task_id"], info["bundle"], info["output_files"])
    return {"work_item_id": item["work_item_id"], "task_id": info["task_id"], "bundle": info["bundle"], "revision": info["revision"]}


def _should_block(paths: Paths, item: dict[str, Any], gv: graph_model.GraphView, by_id: dict[str, dict[str, Any]]) -> bool:
    """A rebuilt item returns to blocked if its blockers aren't all terminal or
    (EDGE_CHECK) its endpoints aren't both active; else queued."""
    for bid in item.get("blocked_by", []):
        blocker = by_id.get(bid)
        if blocker is None or blocker["status"] not in ("committed", "cancelled"):
            return True
    if item["target_type"] == "edge":
        edge = gv.edge_by_id.get(item["target_id"])
        if edge is None or not (gv.is_active(edge["source_node_id"]) and gv.is_active(edge["target_node_id"])):
            return True
    return False
