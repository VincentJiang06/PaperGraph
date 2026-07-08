"""WebUI read model (docs/07 §WebUI HTTP surface, docs/12 §5 views).

Every function here reads canonical records exclusively from the derived DuckDB
index (via ``IndexReader``) — never live JSONL — so a stale index is visible as
stale data plus the ``stale_index`` flag, not silently-fresh reads. Graph-derived
answers (spine, MSA, trace) are computed in Python over the *indexed* records.

Non-canonical inputs that are not part of the index (the contract/spec JSON files
and the prose ``.md`` files) are read from disk directly; they are not JSONL
tables and not part of the stale-index surface.
"""

from __future__ import annotations

from typing import Any, Optional

from ..db.indexer import TABLE_MAP, check as db_check
from ..graph.model import GraphView, meets_evidence_floor
from ..paths import Paths
from ..store import jsonl
from ..textutil import contains, sentence_split

# Work-item status buckets for the six Overview questions.
OPEN_STATUSES = ("queued", "claimed", "running", "validating", "blocked", "stale")
WORKING_STATUSES = ("claimed", "running")


def _graph_view(reader) -> GraphView:
    return GraphView(reader.current("nodes"), reader.current("edges"))


# ---------------------------------------------------------------------------
# /api/overview — the six questions (docs/12 §1, §5.1)
# ---------------------------------------------------------------------------


def overview(reader, paths: Paths) -> dict[str, Any]:
    items = reader.current("work_items")
    nodes = reader.current("nodes")
    edges = reader.current("edges")

    from ..project import _QUEUE_STATUSES  # closed status list

    # Queue matrix: queue_name -> status -> count.
    queues = ("proof_queue", "docs_queue", "compile_queue")
    matrix: dict[str, dict[str, int]] = {q: {s: 0 for s in _QUEUE_STATUSES} for q in queues}
    per_status: dict[str, int] = {s: 0 for s in _QUEUE_STATUSES}
    for it in items:
        st = it.get("status")
        qn = it.get("queue_name")
        if st in per_status:
            per_status[st] += 1
        if qn in matrix and st in matrix[qn]:
            matrix[qn][st] += 1

    # Q1 What is open?
    open_ids = [it["work_item_id"] for it in items if it.get("status") in OPEN_STATUSES]

    # Q2 Who is working on what?  (claimed/running -> agent -> [work items])
    by_agent: dict[str, list[dict[str, str]]] = {}
    for it in items:
        if it.get("status") in WORKING_STATUSES:
            agent = (it.get("lease") or {}).get("claimed_by") or "unknown"
            by_agent.setdefault(agent, []).append(
                {"work_item_id": it["work_item_id"], "target_id": it.get("target_id")}
            )

    # Q3 What is blocked?
    blocked = [
        {"work_item_id": it["work_item_id"], "target_id": it.get("target_id"),
         "blocked_by": it.get("blocked_by", [])}
        for it in items
        if it.get("status") == "blocked"
    ]

    # Q4 What can be committed?  (validated items awaiting `commit apply`)
    committable = [it["work_item_id"] for it in items if it.get("status") == "validated"]

    # Q5 What is frozen?
    frozen_records = [r["node_id"] for r in nodes if r.get("frozen")] + [
        r["edge_id"] for r in edges if r.get("frozen")
    ]

    # Q6 Is the index stale?
    chk = db_check(paths)

    dead_letters = [
        {"work_item_id": it["work_item_id"], "target_id": it.get("target_id"),
         "attempt": it.get("attempt")}
        for it in items
        if it.get("status") == "dead"
    ]

    return {
        "project_id": paths.project_id,
        "contract": _contract(paths),
        "open": {"count": len(open_ids), "work_item_ids": open_ids},
        "working": {"count": len(by_agent), "by_agent": by_agent},
        "blocked": {"count": len(blocked), "items": blocked},
        "committable": {"count": len(committable), "work_item_ids": committable},
        "frozen": {"count": len(frozen_records), "record_ids": frozen_records},
        "dead_letters": {"count": len(dead_letters), "items": dead_letters},
        "queue_matrix": matrix,
        "per_status": per_status,
        "msa": _msa(reader, paths),
        "stale_index": chk["stale_index"],
        "index_built_at": chk["built_at"],
    }


def _contract(paths: Paths) -> Optional[dict[str, Any]]:
    if not paths.project_contract.exists():
        return None
    c = jsonl.read_json(paths.project_contract)
    return {
        "accepted_by_user": c.get("accepted_by_user", False),
        "accepted_at": c.get("accepted_at"),
        "contract_version": c.get("contract_version"),
    }


# ---------------------------------------------------------------------------
# MSA checklist over indexed records (mirror of graph.commands.msa_check)
# ---------------------------------------------------------------------------


def _touches_spine(gv: GraphView, spine_ids: set[str], target_id: str) -> bool:
    if target_id in spine_ids:
        return True
    edge = gv.edge_by_id.get(target_id)
    if edge is not None and (edge["source_node_id"] in spine_ids or edge["target_node_id"] in spine_ids):
        return True
    node = gv.node_by_id.get(target_id)
    if node is not None:
        if any(p in spine_ids for p in node.get("parents", [])):
            return True
        for e in gv.edges:
            if e["edge_id"] in spine_ids and target_id in (e["source_node_id"], e["target_node_id"]):
                return True
    return False


def _lane_complete(reader, gv: GraphView, bfs_id: str) -> bool:
    closing = False
    for cd in reader.history("commit_decisions"):
        if cd.get("kind") != "expansion":
            continue
        ref = cd.get("input_ref", "")
        if ref.startswith(f"EXP-{bfs_id}-") and not any(
            a["action"] in ("append_node", "append_edge") for a in cd.get("actions", [])
        ):
            closing = True
    if not closing:
        return False
    lane_ids = {n["node_id"] for n in gv.nodes if n["bfs_id"] == bfs_id}
    lane_ids |= {e["edge_id"] for e in gv.edges if e["source_node_id"] in lane_ids}
    for it in reader.current("work_items"):
        if it.get("status") in ("committed", "cancelled"):
            continue
        if it.get("target_id") in lane_ids:
            return False
    return True


def _msa(reader, paths: Paths) -> dict[str, Any]:
    gv = _graph_view(reader)
    spine_ids, _ = gv.spine()
    items: list[tuple[str, bool, str]] = []

    q = gv.unique_node_of_type("question")
    t = gv.unique_node_of_type("thesis")
    msa1 = q is not None and t is not None and q["lifecycle_state"] == "active" and t["lifecycle_state"] == "active"
    items.append(("MSA-1", bool(msa1), "exactly one active question and thesis"))

    msa2 = any(
        e["edge_id"] in spine_ids for e in gv.edges
        if q and t and e["source_node_id"] == t["node_id"] and e["target_node_id"] == q["node_id"] and e["edge_type"] == "supports"
    )
    items.append(("MSA-2", bool(msa2), "supports edge thesis->question active"))

    spine_records = [gv.record(i) for i in spine_ids]
    msa3 = bool(spine_ids) and all(r is not None and r["lifecycle_state"] == "active" for r in spine_records)
    items.append(("MSA-3", msa3, "every spine record active"))

    eu_doc = {e["evidence_id"]: e["doc_id"] for e in reader.current("evidence_units") if e.get("doc_id")}
    msa4 = all(
        (n["node_type"] not in ("fact", "mechanism")) or meets_evidence_floor(n, eu_doc)
        for n in gv.nodes if n["node_id"] in spine_ids
    )
    items.append(("MSA-4", msa4, "spine fact/mechanism nodes have >=2 evidence bindings from >=2 documents"))

    msa5 = all(
        n["lifecycle_state"] == "rejected"
        or (n["lifecycle_state"] == "parked" and n.get("state_reason") in ("absorbed", "not_needed"))
        for n in gv.nodes if n["node_type"] == "alternative"
    )
    items.append(("MSA-5", msa5, "every alternative rejected or parked"))

    open_touch = any(
        it.get("status") not in ("committed", "cancelled") and _touches_spine(gv, spine_ids, it.get("target_id"))
        for it in reader.current("work_items")
    )
    items.append(("MSA-6", not open_touch, "no open work item touches the spine"))

    spec = jsonl.read_json(paths.paper_spec) if paths.paper_spec.exists() else {}
    lanes = [e["bfs_id"] for e in spec.get("bfs_plan", [])]
    msa7 = bool(lanes) and all(_lane_complete(reader, gv, lane) for lane in lanes)
    items.append(("MSA-7", msa7, "every bfs_plan lane complete"))

    dry_runs = reader.history("dry_runs")
    msa8 = True if not dry_runs else not (dry_runs[-1].get("gaps") or [])
    items.append(("MSA-8", msa8, "latest dry run reports no blocking gaps"))

    msa9 = any(
        n["node_id"] in spine_ids and n["node_type"] in ("fact", "mechanism") and n["lifecycle_state"] == "active"
        for n in gv.nodes
    )
    items.append(("MSA-9", msa9, "spine contains >=1 active fact/mechanism node"))

    checklist = {rid: {"pass": bool(ok), "detail": detail} for rid, ok, detail in items}
    return {"checklist": checklist, "all_pass": all(v["pass"] for v in checklist.values()), "spine": sorted(spine_ids)}


# ---------------------------------------------------------------------------
# /api/graph, /api/record, /api/queue, /api/events, /api/evidence, /api/compiler
# ---------------------------------------------------------------------------


def graph(reader, lane: str | None = None, layer: int | None = None, state: str | None = None) -> dict[str, Any]:
    gv = _graph_view(reader)
    nodes = []
    for n in gv.nodes:
        if state and n["lifecycle_state"] != state:
            continue
        if lane and n["bfs_id"] != lane:
            continue
        if layer is not None and n["layer"] != layer:
            continue
        nodes.append(n)
    node_ids = {n["node_id"] for n in nodes}
    edges = []
    for e in gv.edges:
        if state and e["lifecycle_state"] != state:
            continue
        src = gv.node_by_id.get(e["source_node_id"])
        if lane and (src is None or src["bfs_id"] != lane):
            continue
        if layer is not None and (src is None or src["layer"] != layer):
            continue
        edges.append(e)
    return {"nodes": nodes, "edges": edges, "counts": {"nodes": len(nodes), "edges": len(edges)}}


def record(reader, rid: str) -> dict[str, Any]:
    for _relpath, table, _idf in TABLE_MAP:
        hist = reader.history_for_id(table, rid)
        if hist:
            verdicts = [v for v in reader.history("verdict_records") if v.get("target_id") == rid]
            return {
                "found": True,
                "id": rid,
                "table": table,
                "record": hist[-1],
                "history": hist,
                "verdict_records": verdicts,
            }
    return {"found": False, "id": rid}


def queue(reader, queue_name: str | None = None, status: str | None = None) -> dict[str, Any]:
    items = reader.current("work_items")
    if queue_name == "commit_queue":
        # derived view: validated items awaiting commit, FIFO by validation time
        # (updated_at = validation-transition time; work_item_id is the tiebreak).
        items = sorted(
            [i for i in items if i["status"] == "validated"],
            key=lambda i: (i["updated_at"], i["work_item_id"]),
        )
    else:
        if queue_name:
            items = [i for i in items if i.get("queue_name") == queue_name]
        if status:
            items = [i for i in items if i.get("status") == status]
    return {"items": items, "count": len(items)}


def events(reader, after: str | None = None, limit: int | None = None) -> dict[str, Any]:
    evs = reader.history("queue_events")
    # newest first
    evs = list(reversed(evs))
    if after:
        # return events strictly older than the `after` cursor (page forward)
        idx = next((i for i, e in enumerate(evs) if e.get("event_id") == after), None)
        if idx is not None:
            evs = evs[idx + 1:]
    if limit is not None:
        evs = evs[:limit]
    return {"events": evs, "count": len(evs)}


def evidence(reader, q: str | None = None) -> dict[str, Any]:
    docs = reader.current("documents")
    eus = reader.current("evidence_units")
    nodes = reader.current("nodes")
    # backlinks: node evidence_bindings -> which nodes reference each EU.
    bound_to: dict[str, list[str]] = {}
    for n in nodes:
        for eid in n.get("evidence_bindings", []) or []:
            bound_to.setdefault(eid, []).append(n["node_id"])
    by_doc: dict[str, list[dict[str, Any]]] = {}
    for eu in eus:
        eu = dict(eu)
        eu["bound_to"] = bound_to.get(eu["evidence_id"], [])
        by_doc.setdefault(eu["doc_id"], []).append(eu)
    documents = []
    for d in docs:
        units = by_doc.get(d["doc_id"], [])
        if q:
            needle = q.lower()
            hit_doc = needle in (d.get("title", "") + d.get("citation_key", "")).lower()
            hit_units = [u for u in units if needle in u.get("quote_or_paraphrase", "").lower() or needle in u.get("summary", "").lower()]
            if not hit_doc and not hit_units:
                continue
        documents.append({"document": d, "evidence_units": units, "eu_count": len(units)})
    return {"documents": documents, "count": len(documents)}


def compiler(reader, paths: Paths) -> dict[str, Any]:
    dry_runs = reader.history("dry_runs")
    draft_maps = reader.history("draft_maps")
    audits = reader.history("audit_reports")
    latest_dry = dry_runs[-1] if dry_runs else None
    latest_map = draft_maps[-1] if draft_maps else None
    latest_audit = audits[-1] if audits else None
    prose_dir = paths.resolve("compiler/prose")
    prose_files = sorted(p.name for p in prose_dir.glob("*.md")) if prose_dir.exists() else []
    return {
        "dry_run": latest_dry,
        "draft_map": latest_map,
        "audit": latest_audit,
        "prose_files": prose_files,
        "writing_ready": bool(latest_dry and latest_dry.get("writing_ready")),
        "gaps": (latest_dry or {}).get("gaps", []) if latest_dry else [],
    }


# ---------------------------------------------------------------------------
# /api/trace/{node} — the docs/09 §3 chain over indexed records
# ---------------------------------------------------------------------------


def trace(reader, paths: Paths, node_id: str) -> dict[str, Any]:
    gv = _graph_view(reader)
    node = gv.node_by_id.get(node_id)
    if node is None:
        return {"found": False, "node_id": node_id}

    freeze_items = reader.history("freeze_items")
    revoked = {it["revokes"] for it in freeze_items if it.get("action") == "unfreeze" and it.get("revokes")}
    freeze_ids = [
        it["freeze_id"] for it in freeze_items
        if it.get("action") == "freeze" and it["freeze_id"] not in revoked and node_id in it.get("target_ids", [])
    ]

    commit_ids = [
        cd["commit_id"] for cd in reader.history("commit_decisions")
        if any(a.get("target_id") == node_id for a in cd.get("actions", []))
    ]

    proofs = [
        {"proof_result_id": r["proof_result_id"], "bundle": r.get("bundle"), "computed_verdict": r.get("computed_verdict")}
        for r in reader.history("verdict_records") if r.get("target_id") == node_id
    ]

    docs_by_id = {d["doc_id"]: d for d in reader.current("documents")}
    eus_by_id = {e["evidence_id"]: e for e in reader.current("evidence_units")}
    evidence_chain: list[dict[str, Any]] = []
    for eid in node.get("evidence_bindings", []) or []:
        eu = eus_by_id.get(eid)
        entry: dict[str, Any] = {"evidence_id": eid, "resolved": eu is not None}
        if eu is not None:
            doc = docs_by_id.get(eu["doc_id"])
            origin = (doc or {}).get("origin", {}) or {}
            raw_path = origin.get("path") or (f"docs/raw/{eu['doc_id']}.txt" if doc is not None else None)
            entry.update({
                "doc_id": eu["doc_id"],
                "location": eu.get("location"),
                "citation_key": (doc or {}).get("citation_key"),
                "raw_path": raw_path,
                "text_path": (doc or {}).get("text_path"),
            })
        evidence_chain.append(entry)

    # prose occurrences (compiler/prose/*.md is not a JSONL table)
    occ: list[dict[str, Any]] = []
    prose_dir = paths.resolve("compiler/prose")
    if prose_dir.exists():
        needle = f"(claim: {node_id})"
        for path in sorted(prose_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            for idx, sentence in enumerate(sentence_split(text), start=1):
                if contains(sentence, needle):
                    occ.append({"section": path.stem, "sentence": idx})

    return {
        "found": True,
        "node_id": node_id,
        "claim": node["claim"],
        "node_type": node["node_type"],
        "frozen": node.get("frozen", False),
        "freeze_ids": freeze_ids,
        "commit_ids": commit_ids,
        "proof_results": proofs,
        "evidence": evidence_chain,
        "prose_occurrences": occ,
    }
