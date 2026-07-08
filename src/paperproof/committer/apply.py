"""The Committer (docs/08 B6 / B6b): serial, single-writer graph mutation.

Every mutation goes through here under ``commit/.lock``. A commit:
  1. checks preconditions (V-COMMIT-01 input-scoped currency, V-COMMIT-03 frozen,
     V-COMMIT-06 provable target),
  2. plans the graph appends deterministically from the verdict->action table,
  3. simulates the post-graph and checks V-GRAPH-01..03 (V-COMMIT-05),
  4. appends graph records, takes the post snapshot, performs queue side effects
     (enqueue re-proof / bridge / docs items; cancel cascade items; mark siblings
     stale), and appends ONE CommitDecision listing every graph append,
  5. moves the input work item validated -> committed.

Same input + same snapshot => byte-identical CommitDecision (no LLM here).
"""

from __future__ import annotations

from typing import Any, Optional

from ..clock import actor as clock_actor
from ..clock import now as clock_now
from ..docsdb import cache as docs_cache
from ..docsdb.matcher import fingerprint as docs_fingerprint
from ..errors import DomainError
from ..graph import model as graph_model
from ..graph.model import structural_signature
from ..ids import edge_id as make_edge_id
from ..ids import next_id
from ..paths import Paths
from ..queue import engine
from ..store import file_lock, jsonl, snapshot
from ..validate.rules import v_cov, v_node_edge

NODES = "graph/logic_nodes.jsonl"
EDGES = "graph/logic_edges.jsonl"
TOMBSTONES = "graph/tombstones.jsonl"
COMMITS = "commit/commit_decisions.jsonl"
DOCS_REQUESTS = "docs/docs_requests.jsonl"
EVIDENCE_UNITS = "docs/evidence_units.jsonl"
PROOF_RESULTS = "proof/proof_results.jsonl"
COMMIT_LOCK = "commit/.lock"

_FILE_KEY = {"node": NODES, "edge": EDGES, "tombstone": TOMBSTONES, "docs_request": DOCS_REQUESTS}


class _CommitPlan:
    """Accumulates graph appends (in planned order) + CommitDecision actions +
    queue side effects for one commit."""

    def __init__(self, paths: Paths, gv: graph_model.GraphView) -> None:
        self.paths = paths
        self.gv = gv
        self.graph_appends: list[tuple[str, dict[str, Any]]] = []  # (file, record)
        self.actions: list[dict[str, Any]] = []
        self.node_ids = set(gv.node_by_id)
        self.edge_ids = set(gv.edge_by_id)
        # in-memory latest-by-id for simulation
        self.sim_nodes: dict[str, dict[str, Any]] = {k: dict(v) for k, v in gv.node_by_id.items()}
        self.sim_edges: dict[str, dict[str, Any]] = {k: dict(v) for k, v in gv.edge_by_id.items()}
        self.mutated_claim_or_reject: set[str] = set()
        self.new_edge_endpoints: set[str] = set()

    def _action(self, action: str, target_id: str, detail: dict[str, Any], record: dict[str, Any] | None = None) -> None:
        # `record` is the exact appended graph record for graph-mutating actions
        # (consumed by the V-COMMIT-04 replay), null for queue/docs actions.
        self.actions.append({"action": action, "target_id": target_id, "detail": detail, "record": record})

    def append_node(self, record: dict[str, Any], action: str, detail: dict[str, Any]) -> None:
        self.graph_appends.append((NODES, record))
        self.sim_nodes[record["node_id"]] = record
        self._action(action, record["node_id"], detail, record)

    def append_edge(self, record: dict[str, Any], action: str, detail: dict[str, Any]) -> None:
        self.graph_appends.append((EDGES, record))
        self.sim_edges[record["edge_id"]] = record
        self._action(action, record["edge_id"], detail, record)

    def append_tombstone(self, record: dict[str, Any]) -> None:
        self.graph_appends.append((TOMBSTONES, record))
        self._action("tombstone", record["target_id"], {"reason": record["reason"]}, record)

    def alloc_node_id(self) -> str:
        nid = next_id("NODE", self.node_ids)
        self.node_ids.add(nid)
        return nid

    def alloc_edge_id(self, source: str, target: str, edge_type: str) -> str:
        eid = make_edge_id(source, target, edge_type, self.edge_ids)
        self.edge_ids.add(eid)
        return eid


# --- record builders --------------------------------------------------------


def _update_record(current: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
    new = dict(current)
    new.update(changes)
    new["created_at"] = clock_now()  # append time of this version
    return new


def _tombstone_record(paths: Paths, existing_ts: list[str], target_type: str, target_id: str, reason: str, commit_id: str, duplicate_of: Optional[str]) -> dict[str, Any]:
    ts_id = next_id("TS", existing_ts)
    existing_ts.append(ts_id)
    return {
        "schema_version": "tombstone.v1",
        "tombstone_id": ts_id,
        "project_id": paths.project_id,
        "target_type": target_type,
        "target_id": target_id,
        "reason": reason,
        "duplicate_of": duplicate_of,
        "commit_id": commit_id,
        "created_at": clock_now(),
    }


# --- currency (V-COMMIT-01, input-scoped) -----------------------------------


def _bundle_current(paths: Paths, verdict_record: dict[str, Any], gv: graph_model.GraphView) -> bool:
    """Input-scoped currency: target + 1-hop unchanged (structurally) since the
    verdict's bundle. Pure lifecycle passes do not count as change (docs/05)."""
    ctx_path = verdict_record["bundle"]["context_pack"]
    ctx = jsonl.read_json(paths.resolve(ctx_path))
    tid = verdict_record["target_id"]
    cur_target = gv.record(tid)
    if cur_target is None:
        return False
    if structural_signature(cur_target) != structural_signature(ctx.get("target", {})):
        return False
    pack_nodes = {n["node_id"]: structural_signature(n) for n in ctx.get("neighbor_nodes", [])}
    pack_edges = {e["edge_id"]: structural_signature(e) for e in ctx.get("neighbor_edges", [])}
    cur_nodes, cur_edges = gv.one_hop(tid)
    cur_node_sig = {n["node_id"]: structural_signature(n) for n in cur_nodes}
    cur_edge_sig = {e["edge_id"]: structural_signature(e) for e in cur_edges}
    if set(pack_nodes) != set(cur_node_sig) or set(pack_edges) != set(cur_edge_sig):
        return False
    if any(pack_nodes[k] != cur_node_sig[k] for k in cur_node_sig):
        return False
    if any(pack_edges[k] != cur_edge_sig[k] for k in cur_edge_sig):
        return False
    return True


def _bridge_rounds(paths: Paths, edge_id: str) -> int:
    """Count committed bridge rounds already applied to this edge (docs/08 cap=2)."""
    verdicts = {r["proof_result_id"]: r for r in jsonl.read_all(paths.resolve(PROOF_RESULTS))}
    rounds = 0
    for cd in jsonl.read_all(paths.resolve(COMMITS)):
        if cd.get("kind") != "proof_verdict":
            continue
        vr = verdicts.get(cd.get("input_ref"))
        if vr and vr.get("target_id") == edge_id and vr.get("computed_verdict", {}).get("repair_kind") == "bridge":
            rounds += 1
    return rounds


# --- the main entry: apply a proof verdict ----------------------------------


def apply_proof_verdict(paths: Paths, pr_id: str, actor: str | None = None) -> dict[str, Any]:
    actor = actor or clock_actor()
    with file_lock(paths.resolve(COMMIT_LOCK)):
        engine.run_sweeps(paths, actor)
        vr = _find_verdict(paths, pr_id)  # V-COMMIT-02
        wi_id = vr["work_item_id"]
        wi = engine.get_item(paths, wi_id)
        if wi["status"] != "validated":
            raise DomainError([f"work item not in validated state: {wi_id} ({wi['status']})"])

        gv = graph_model.load(paths)
        target_id = vr["target_id"]
        target_type = vr["target_type"]
        target = gv.record(target_id)

        # V-COMMIT-06: target must be in a provable state.
        provable = {"pending_proof", "needs_repair", "needs_docs"}
        if target is None or target["lifecycle_state"] not in provable:
            engine.cancel(paths, wi_id, actor, detail={"reason": "V-COMMIT-06 target not provable"})
            return {"commit_id": None, "cancelled": True, "reason": "V-COMMIT-06"}

        # V-COMMIT-03: frozen refusal.
        if target.get("frozen"):
            raise DomainError([f"V-COMMIT-03: target frozen: {target_id}"])

        # V-COMMIT-01: input-scoped currency.
        if not _bundle_current(paths, vr, gv):
            engine.invalidate(paths, wi_id, actor, detail={"reason": "V-COMMIT-01 stale bundle"})
            return {"commit_id": None, "stale": True, "reason": "V-COMMIT-01"}

        verdict = vr["computed_verdict"]
        plan = _CommitPlan(paths, gv)
        existing_ts = [r["tombstone_id"] for r in jsonl.read_all(paths.resolve(TOMBSTONES))]
        commit_id = next_id("CD", [r["commit_id"] for r in jsonl.read_all(paths.resolve(COMMITS))])

        deferred_enqueues: list[dict[str, Any]] = []  # queue side effects executed post-snapshot
        _plan_verdict(paths, plan, vr, target, target_type, pr_id, commit_id, existing_ts, deferred_enqueues)

        # Simulate + V-COMMIT-05 (post-commit V-GRAPH-*).
        _validate_post_graph(plan)

        based_on = _current_snapshot(paths)
        _apply_graph_appends(paths, plan)
        post_snap = snapshot.take_snapshot(paths).snapshot_id

        # queue side effects (enqueues, cancels, staleness) — do not affect graph
        _run_deferred(paths, plan, deferred_enqueues, actor)
        _mark_siblings_stale(paths, plan, wi_id, actor)

        engine.commit_item(paths, wi_id, actor)

        _write_commit_decision(paths, commit_id, "proof_verdict", actor, pr_id, based_on, post_snap, plan.actions)
        return {"commit_id": commit_id, "actions": plan.actions, "post_snapshot": post_snap}


def _plan_verdict(paths, plan, vr, target, target_type, pr_id, commit_id, existing_ts, deferred_enqueues):
    verdict = vr["computed_verdict"]
    kind = verdict["verdict"]
    if kind == "pass":
        _plan_pass(plan, vr, target, target_type, pr_id)
    elif kind == "needs_repair" and verdict["repair_kind"] == "narrow":
        _plan_narrow(plan, vr, target, target_type, pr_id, deferred_enqueues)
    elif kind == "needs_repair" and verdict["repair_kind"] == "bridge":
        _plan_bridge(paths, plan, vr, target, pr_id, deferred_enqueues)
    elif kind == "needs_docs":
        _plan_needs_docs(paths, plan, vr, target, target_type, pr_id, commit_id, deferred_enqueues)
    elif kind == "rejected":
        _plan_rejected(paths, plan, vr, target, target_type, pr_id, commit_id, existing_ts, deferred_enqueues)
    else:  # pragma: no cover
        raise DomainError([f"unknown verdict: {verdict}"])


def _upd_action(target_type: str) -> str:
    return "update_edge" if target_type == "edge" else "update_node"


def _append_update(plan: _CommitPlan, target_type: str, record: dict[str, Any], detail: dict[str, Any]) -> None:
    if target_type == "edge":
        plan.append_edge(record, "update_edge", detail)
    else:
        plan.append_node(record, "update_node", detail)


def _plan_pass(plan, vr, target, target_type, pr_id):
    strength = vr["computed_verdict"]["strength"]
    changes = {
        "lifecycle_state": "active",
        "state_reason": None,
        "state_detail": None,
        "strength": strength,
        "language_limits": vr.get("language_limits"),
        "assumptions": list(vr.get("assumptions") or []),
        "latest_proof_result_id": pr_id,
    }
    if target_type == "node":
        changes["evidence_bindings"] = list(vr.get("evidence_used") or [])
    new = _update_record(target, changes)
    _append_update(plan, target_type, new, {"lifecycle_state": "active", "strength": strength})


def _plan_narrow(plan, vr, target, target_type, pr_id, deferred_enqueues):
    narrowed = None
    for r in vr.get("repair_proposals", []):
        if r.get("kind") == "narrow":
            narrowed = r.get("narrowed_claim")
    changes = {
        "lifecycle_state": "needs_repair",
        "state_reason": "narrow",
        "state_detail": None,
        "strength": "unassessed",
        "language_limits": None,
        "assumptions": [],
        "claim_version": target["claim_version"] + 1,
        "latest_proof_result_id": pr_id,
    }
    if target_type == "edge":
        changes["edge_claim"] = narrowed
    else:
        changes["claim"] = narrowed
    new = _update_record(target, changes)
    _append_update(plan, target_type, new, {"lifecycle_state": "needs_repair", "reason": "narrow"})
    # a claim_version bump is a structural mutation: stale any sibling whose
    # target/1-hop includes this record.
    plan.mutated_claim_or_reject.add(target["node_id"] if target_type == "node" else target["edge_id"])
    deferred_enqueues.append({
        "op": "enqueue", "queue_name": "proof_queue", "target_type": target_type,
        "target_id": target["node_id"] if target_type == "node" else target["edge_id"],
        "blocked_by": [],
    })


def _plan_bridge(paths, plan, vr, target, pr_id, deferred_enqueues):
    edge_id = target["edge_id"]
    changes = {
        "lifecycle_state": "needs_repair", "state_reason": "bridge", "state_detail": None,
        "strength": "unassessed", "language_limits": None, "latest_proof_result_id": pr_id,
    }
    new = _update_record(target, changes)
    plan.append_edge(new, "update_edge", {"lifecycle_state": "needs_repair", "reason": "bridge"})

    rounds = _bridge_rounds(paths, edge_id)
    if rounds >= 2:
        # bridge-round cap: no new bridges; re-proof item is born dead.
        deferred_enqueues.append({"op": "dead_letter", "queue_name": "proof_queue",
                                  "target_type": "edge", "target_id": edge_id, "reason": "bridge cap reached"})
        return

    source_node = plan.gv.node_by_id.get(target["source_node_id"])
    target_node = plan.gv.node_by_id.get(target["target_node_id"])
    proposals = [r for r in vr.get("repair_proposals", []) if r.get("kind") == "bridge"][:2]

    bridge_wi_refs: list[dict[str, Any]] = []  # marker dicts resolved to WI ids post-snapshot
    for i, prop in enumerate(proposals):
        node_type = prop.get("node_type")
        xid = plan.alloc_node_id()
        node_rec = {
            "schema_version": "logic_node.v1", "node_id": xid, "project_id": paths.project_id,
            "bfs_id": source_node["bfs_id"], "layer": source_node["layer"],
            "claim": prop.get("claim"), "claim_version": 1, "node_type": node_type,
            "scope": source_node.get("scope", {}), "parents": [target["target_node_id"]],
            "origin": {"kind": "bridge", "source": pr_id}, "lifecycle_state": "pending_proof",
            "state_reason": None, "state_detail": None, "strength": "unassessed",
            "language_limits": None, "assumptions": [], "evidence_bindings": [],
            "latest_proof_result_id": None, "frozen": False, "created_at": clock_now(),
        }
        plan.append_node(node_rec, "append_node", {"origin": "bridge"})
        edge_type = "depends_on" if node_type == "definition" else "supports"
        beid = plan.alloc_edge_id(xid, target["target_node_id"], edge_type)
        edge_rec = {
            "schema_version": "logic_edge.v1", "edge_id": beid, "project_id": paths.project_id,
            "source_node_id": xid, "target_node_id": target["target_node_id"], "edge_type": edge_type,
            "edge_claim": f"Bridge premise supporting the inference: {prop.get('claim')}",
            "claim_version": 1, "lifecycle_state": "pending_proof", "state_reason": None,
            "state_detail": None, "strength": "unassessed", "language_limits": None,
            "assumptions": [], "frozen": False, "latest_proof_result_id": None, "created_at": clock_now(),
        }
        plan.append_edge(edge_rec, "append_edge", {"origin": "bridge", "edge_type": edge_type})
        plan.new_edge_endpoints.add(target["target_node_id"])
        bridge_wi_refs.append({"node_id": xid, "edge_id": beid, "edge_type": edge_type})

    deferred_enqueues.append({"op": "bridge_wiring", "edge_id": edge_id, "bridges": bridge_wi_refs})


def _plan_needs_docs(paths, plan, vr, target, target_type, pr_id, commit_id, deferred_enqueues):
    changes = {
        "lifecycle_state": "needs_docs", "state_reason": None, "state_detail": None,
        "strength": "unassessed", "language_limits": None, "latest_proof_result_id": pr_id,
    }
    if target_type == "edge":
        changes["assumptions"] = []
    else:
        changes["assumptions"] = []
    new = _update_record(target, changes)
    _append_update(plan, target_type, new, {"lifecycle_state": "needs_docs"})

    tgt_id = target["edge_id"] if target_type == "edge" else target["node_id"]
    # S4 SATURATION replaces the r3 docs round-trip cap (docs/17, docs/00). A
    # needs_docs verdict ALWAYS opens more search while the target is NOT saturated
    # -- no count-based refusal remains. When the target IS saturated, no new search
    # is opened: the re-proof item is born dead reason="saturated" iff the role
    # floor is ALSO unmet [V-COV-03]; if the floor is met the worker's insufficient
    # answer conflicts with a met floor, so route to human review (no born-dead).
    from ..docsdb import coverage as coverage_mod

    spine_ids, _ = plan.gv.spine()
    ctx = coverage_mod.build_context(paths, spine_ids)
    ledger = coverage_mod.target_ledger(target, ctx)
    if ledger["saturated"]:
        # D1: BOTH saturated branches born-dead the re-proof (queue trace; a later
        # `queue requeue` resumes). reason is ALWAYS the v_cov constant "saturated";
        # floor_met distinguishes the stops [V-COV-03]. When the floor IS met the
        # committer additionally records a human_review action (the worker's
        # "insufficient" conflicts with a met floor — surface it, no more search).
        floor_met = coverage_mod.meets_floor(ledger)
        deferred_enqueues.append({"op": "dead_letter", "queue_name": "proof_queue",
                                  "target_type": target_type, "target_id": tgt_id,
                                  "reason": v_cov.SATURATED, "floor_met": floor_met})
        if floor_met:
            deferred_enqueues.append({"op": "human_review", "target_type": target_type,
                                      "target_id": tgt_id, "ledger": ledger["floor"]})
        return

    existing_dr = [r["request_id"] for r in jsonl.read_all(paths.resolve(DOCS_REQUESTS))]
    miss_dr_ids: list[str] = []
    for req in vr.get("docs_requests", []):
        need = req.get("need", "")
        hints = list(req.get("search_hints", []))
        dr_id = next_id("DR", existing_dr)
        existing_dr.append(dr_id)
        fp = docs_fingerprint(need, hints)
        # Request-level cache (docs/04 r3): fingerprint match with a
        # DRES-fulfilled identical request => cache hit. Nothing else.
        hit = docs_cache.is_cache_hit(paths, fp, target)
        record = {
            "schema_version": "docs_request.v1", "request_id": dr_id, "project_id": paths.project_id,
            "requested_by": pr_id, "target_id": tgt_id, "need": need, "search_hints": hints,
            "fingerprint": fp,
            "status": "fulfilled" if hit else "open",
            "fulfilled_by": "cache" if hit else None, "created_at": clock_now(),
            "fan": False,  # reactive needs_docs requests default single (docs/15)
        }
        plan.graph_appends.append((DOCS_REQUESTS, record))
        plan._action("docs_request", dr_id, {"target_id": tgt_id, "status": record["status"]})
        if not hit:
            miss_dr_ids.append(dr_id)
    # re-proof blocked_by only real-miss docs items; all-cache => unblocked now.
    deferred_enqueues.append({"op": "docs_wiring", "target_type": target_type, "target_id": tgt_id, "miss_dr_ids": miss_dr_ids})


def _plan_rejected(paths, plan, vr, target, target_type, pr_id, commit_id, existing_ts, deferred_enqueues):
    reason = vr["computed_verdict"]["reason"]
    dup_of = None
    state_detail = None
    if reason == "duplicate":
        dup_of = target and vr.get("form", {}).get("duplicate_check", {}).get("duplicate_of")
        state_detail = {"duplicate_of": dup_of}
    changes = {
        "lifecycle_state": "rejected", "state_reason": reason, "state_detail": state_detail,
        "strength": "unassessed", "language_limits": None, "latest_proof_result_id": pr_id,
    }
    tgt_id = target["node_id"] if target_type == "node" else target["edge_id"]
    new = _update_record(target, changes)
    _append_update(plan, target_type, new, {"lifecycle_state": "rejected", "reason": reason})
    plan.mutated_claim_or_reject.add(tgt_id)
    plan.append_tombstone(_tombstone_record(paths, existing_ts, target_type, tgt_id, reason, commit_id, dup_of))

    if target_type == "node":
        node_id = target["node_id"]
        for edge in plan.gv.incident_edges(node_id):
            if edge["lifecycle_state"] == "rejected":
                continue
            e_changes = {
                "lifecycle_state": "rejected", "state_reason": "endpoint_rejected", "state_detail": None,
                "strength": "unassessed", "language_limits": None, "latest_proof_result_id": edge.get("latest_proof_result_id"),
            }
            e_new = _update_record(edge, e_changes)
            plan.append_edge(e_new, "update_edge", {"lifecycle_state": "rejected", "reason": "endpoint_rejected"})
            plan.mutated_claim_or_reject.add(edge["edge_id"])
            plan.append_tombstone(_tombstone_record(paths, existing_ts, "edge", edge["edge_id"], "endpoint_rejected", commit_id, None))
            deferred_enqueues.append({"op": "cancel_incident", "target_id": edge["edge_id"]})
    deferred_enqueues.append({"op": "cancel_incident", "target_id": target["node_id"] if target_type == "node" else target["edge_id"]})


# --- apply / snapshot / decision -------------------------------------------


def _current_snapshot(paths: Paths) -> str:
    sid = snapshot.latest_snapshot_id(paths)
    if sid is None or not snapshot.is_current(paths, sid):
        sid = snapshot.take_snapshot(paths).snapshot_id
    return sid


def _apply_graph_appends(paths: Paths, plan: _CommitPlan) -> None:
    for file_rel, record in plan.graph_appends:
        jsonl.append(paths.resolve(file_rel), record)


def _validate_post_graph(plan: _CommitPlan) -> None:
    nodes = list(plan.sim_nodes.values())
    edges = list(plan.sim_edges.values())
    failures = v_node_edge.graph_record_checks(nodes, edges)
    if failures:
        raise DomainError(["V-COMMIT-05: post-commit graph invariants violated"] + [f.rule_id for f in failures])


def _run_deferred(paths: Paths, plan: _CommitPlan, deferred: list[dict[str, Any]], actor: str) -> None:
    for op in deferred:
        kind = op["op"]
        if kind == "enqueue":
            item = engine.enqueue(
                paths, queue_name=op["queue_name"], target_type=op["target_type"],
                target_id=op["target_id"], blocked_by=op.get("blocked_by", []), actor=actor,
            )
            plan._action("enqueue", item["work_item_id"], {"queue": op["queue_name"], "target": op["target_id"]})
        elif kind == "dead_letter":
            extra = {"floor_met": op["floor_met"]} if "floor_met" in op else None
            item = engine.dead_letter_born(
                paths, queue_name=op["queue_name"], target_type=op["target_type"],
                target_id=op["target_id"], reason=op["reason"], actor=actor, detail=extra,
            )
            plan._action("enqueue", item["work_item_id"], {"queue": op["queue_name"], "dead": True})
        elif kind == "bridge_wiring":
            _wire_bridges(paths, plan, op, actor)
        elif kind == "docs_wiring":
            _wire_docs(paths, plan, op, actor)
        elif kind == "human_review":
            # Saturated target whose floor IS met: no new search, no born-dead
            # (V-COV-03 reserves born-dead reason=saturated for the floor-unmet
            # case). Surface it for human review — the ContextPack coverage block
            # tells the worker search is exhausted so it answers the honest endgame.
            plan._action("human_review", op["target_id"],
                         {"reason": "saturated", "floor_met": True})
        elif kind == "cancel_incident":
            _cancel_open_items(paths, plan, op["target_id"], actor)


def _wire_bridges(paths: Paths, plan: _CommitPlan, op: dict[str, Any], actor: str) -> None:
    all_bridge_wis: list[str] = []
    for br in op["bridges"]:
        node_wi = engine.enqueue(paths, queue_name="proof_queue", target_type="node", target_id=br["node_id"], actor=actor)
        plan._action("enqueue", node_wi["work_item_id"], {"queue": "proof_queue", "target": br["node_id"]})
        edge_wi = engine.enqueue(paths, queue_name="proof_queue", target_type="edge", target_id=br["edge_id"], blocked_by=[node_wi["work_item_id"]], actor=actor)
        plan._action("enqueue", edge_wi["work_item_id"], {"queue": "proof_queue", "target": br["edge_id"]})
        all_bridge_wis += [node_wi["work_item_id"], edge_wi["work_item_id"]]
    reproof = engine.enqueue(paths, queue_name="proof_queue", target_type="edge", target_id=op["edge_id"], blocked_by=all_bridge_wis, actor=actor)
    plan._action("enqueue", reproof["work_item_id"], {"queue": "proof_queue", "target": op["edge_id"], "reproof": True})


def _wire_docs(paths: Paths, plan: _CommitPlan, op: dict[str, Any], actor: str) -> None:
    from ..docsdb import planner as docs_planner  # local: avoid import cycle

    docs_wis: list[str] = []
    for dr_id in op["miss_dr_ids"]:
        output = f"agent_outputs/docs_results/{dr_id}.docs_result.json"
        item = engine.enqueue(paths, queue_name="docs_queue", target_type="request", target_id=dr_id,
                              output_files=[output], actor=actor)
        plan._action("enqueue", item["work_item_id"], {"queue": "docs_queue", "target": dr_id})
        # Dispatch attaches the compiled plan as an immutable bundle artifact
        # (docs/14). It is NOT a graph mutation and not tracked in the
        # CommitDecision — same input+snapshot still yields identical decisions.
        docs_planner.plan_for_request(paths, dr_id)
        docs_wis.append(item["work_item_id"])
    reproof = engine.enqueue(paths, queue_name="proof_queue", target_type=op["target_type"], target_id=op["target_id"], blocked_by=docs_wis, actor=actor)
    plan._action("enqueue", reproof["work_item_id"], {"queue": "proof_queue", "target": op["target_id"], "reproof": True})


def _cancel_open_items(paths: Paths, plan: _CommitPlan, target_id: str, actor: str) -> None:
    for item in engine.load_items(paths):
        if item["target_id"] != target_id:
            continue
        if item["status"] in ("queued", "blocked", "stale", "failed"):
            engine.cancel(paths, item["work_item_id"], actor, detail={"reason": "endpoint_rejected cascade"})
            plan._action("cancel_item", item["work_item_id"], {"reason": "cascade"})


def _mark_siblings_stale(paths: Paths, plan: _CommitPlan, input_wi: str, actor: str) -> None:
    mutation_ids = set(plan.mutated_claim_or_reject) | set(plan.new_edge_endpoints)
    for eid in plan.edge_ids - set(plan.gv.edge_by_id):  # newly created edges
        mutation_ids.add(eid)
    if not mutation_ids:
        return
    gv = graph_model.load(paths)
    for item in engine.load_items(paths):
        if item["work_item_id"] == input_wi or item["queue_name"] != "proof_queue":
            continue
        if item["status"] not in ("queued", "blocked") or item.get("bundle") is None:
            continue
        one_hop = gv.one_hop_ids(item["target_id"]) | {item["target_id"]}
        if one_hop & mutation_ids:
            engine.invalidate(paths, item["work_item_id"], actor, detail={"reason": "target/1-hop mutated"})
            plan._action("mark_stale", item["work_item_id"], {"reason": "sibling staled"})


def _write_commit_decision(paths, commit_id, kind, actor, input_ref, based_on, post_snap, actions) -> None:
    record = {
        "schema_version": "commit_decision.v1", "commit_id": commit_id, "project_id": paths.project_id,
        "kind": kind, "actor": actor, "input_ref": input_ref, "based_on_snapshot": based_on,
        "post_snapshot": post_snap, "actions": actions, "created_at": clock_now(),
    }
    jsonl.append(paths.resolve(COMMITS), record)


def _find_verdict(paths: Paths, pr_id: str) -> dict[str, Any]:
    for r in jsonl.read_all(paths.resolve(PROOF_RESULTS)):
        if r.get("proof_result_id") == pr_id:
            return r
    raise DomainError([f"V-COMMIT-02: verdict record not found: {pr_id}"])


# --- expansion commit (B3) --------------------------------------------------


def apply_expansion(paths: Paths, proposal: dict[str, Any], actor: str | None = None) -> dict[str, Any]:
    """Commit a validated ExpansionProposal: assign ids, append nodes/edges
    (pending_proof), enqueue NODE_CHECK/EDGE_CHECK items (edges blocked_by their
    endpoint checks). One CommitDecision (kind=expansion)."""
    actor = actor or clock_actor()
    with file_lock(paths.resolve(COMMIT_LOCK)):
        engine.run_sweeps(paths, actor)
        gv = graph_model.load(paths)
        plan = _CommitPlan(paths, gv)
        proposal_id = proposal["proposal_id"]
        layer = proposal["layer"]
        bfs_id = proposal["bfs_id"]
        seed = layer == 0
        origin = {"kind": "seed" if seed else "expansion", "source": "topic-input" if seed else proposal_id}

        # nodes: index -> assigned id
        index_to_id: dict[int, str] = {}
        assigned_ids: list[str] = []
        for i, pnode in enumerate(proposal.get("nodes", [])):
            nid = plan.alloc_node_id()
            index_to_id[i] = nid
            assigned_ids.append(nid)
            record = {
                "schema_version": "logic_node.v1", "node_id": nid, "project_id": paths.project_id,
                "bfs_id": bfs_id, "layer": layer, "claim": pnode["claim"], "claim_version": 1,
                "node_type": pnode["node_type"], "scope": pnode.get("scope", {}) or {},
                "parents": list(pnode.get("parents", [])), "origin": origin,
                "lifecycle_state": "pending_proof", "state_reason": None, "state_detail": None,
                "strength": "unassessed", "language_limits": None, "assumptions": [],
                "evidence_bindings": [], "latest_proof_result_id": None, "frozen": False,
                "created_at": clock_now(),
            }
            plan.append_node(record, "append_node", {"origin": origin["kind"]})

        def _resolve(ref: str) -> str:
            if ref.startswith("#"):
                return index_to_id[int(ref[1:])]
            return ref

        edge_specs: list[tuple[str, dict[str, Any]]] = []  # (edge_id, record)
        for pedge in proposal.get("edges", []):
            src = _resolve(pedge["source_ref"])
            tgt = _resolve(pedge["target_ref"])
            etype = pedge["edge_type"]
            eid = plan.alloc_edge_id(src, tgt, etype)
            record = {
                "schema_version": "logic_edge.v1", "edge_id": eid, "project_id": paths.project_id,
                "source_node_id": src, "target_node_id": tgt, "edge_type": etype,
                "edge_claim": pedge["edge_claim"], "claim_version": 1, "lifecycle_state": "pending_proof",
                "state_reason": None, "state_detail": None, "strength": "unassessed",
                "language_limits": None, "assumptions": [], "frozen": False,
                "latest_proof_result_id": None, "created_at": clock_now(),
            }
            plan.append_edge(record, "append_edge", {"edge_type": etype})
            edge_specs.append((eid, record))
            assigned_ids.append(eid)

        _validate_post_graph(plan)

        based_on = _current_snapshot(paths)
        _apply_graph_appends(paths, plan)
        post_snap = snapshot.take_snapshot(paths).snapshot_id if plan.graph_appends else based_on

        # enqueue node checks first (map id -> wi), then edge checks blocked_by endpoints.
        node_check_wi: dict[str, str] = {}
        work_item_ids: list[str] = []
        for nid in [index_to_id[i] for i in sorted(index_to_id)]:
            item = engine.enqueue(paths, queue_name="proof_queue", target_type="node", target_id=nid, actor=actor)
            node_check_wi[nid] = item["work_item_id"]
            work_item_ids.append(item["work_item_id"])
            plan._action("enqueue", item["work_item_id"], {"queue": "proof_queue", "target": nid})

        post_gv = graph_model.load(paths)
        open_node_checks = _open_node_checks(paths)
        for eid, record in edge_specs:
            blocked_by: list[str] = []
            for ep in (record["source_node_id"], record["target_node_id"]):
                if ep in node_check_wi:
                    blocked_by.append(node_check_wi[ep])
                elif not post_gv.is_active(ep) and ep in open_node_checks:
                    blocked_by.append(open_node_checks[ep])
            item = engine.enqueue(
                paths, queue_name="proof_queue", target_type="edge", target_id=eid,
                blocked_by=blocked_by, actor=actor,
            )
            work_item_ids.append(item["work_item_id"])
            plan._action("enqueue", item["work_item_id"], {"queue": "proof_queue", "target": eid})

        commit_id = next_id("CD", [r["commit_id"] for r in jsonl.read_all(paths.resolve(COMMITS))])
        _write_commit_decision(paths, commit_id, "expansion", actor, proposal_id, based_on, post_snap, plan.actions)
        return {"commit_id": commit_id, "assigned_ids": assigned_ids, "work_item_ids": work_item_ids, "closing": not plan.graph_appends}


def _open_node_checks(paths: Paths) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in engine.load_items(paths):
        if item["target_type"] == "node" and item["status"] not in ("committed", "cancelled", "dead"):
            out.setdefault(item["target_id"], item["work_item_id"])
    return out


# --- administrative commits (B6b) -------------------------------------------


def _admin_commit(paths, kind, actor, input_ref, graph_appends, actions, deferred=None):
    """Shared administrative-commit machinery under the commit lock."""
    plan_actions = actions
    based_on = _current_snapshot(paths)
    for file_rel, record in graph_appends:
        jsonl.append(paths.resolve(file_rel), record)
    post_snap = snapshot.take_snapshot(paths).snapshot_id
    for fn in deferred or []:
        fn()
    commit_id = next_id("CD", [r["commit_id"] for r in jsonl.read_all(paths.resolve(COMMITS))])
    _write_commit_decision(paths, commit_id, kind, actor, input_ref, based_on, post_snap, plan_actions)
    return commit_id


def park(paths: Paths, target_id: str, reason: str, into: str | None = None, actor: str | None = None) -> dict[str, Any]:
    actor = actor or clock_actor()
    with file_lock(paths.resolve(COMMIT_LOCK)):
        gv = graph_model.load(paths)
        rec = gv.record(target_id)
        ttype = gv.kind(target_id)
        if rec is None:
            raise DomainError([f"record not found: {target_id}"])
        if rec["lifecycle_state"] not in ("active", "candidate"):
            raise DomainError([f"park requires active|candidate, got {rec['lifecycle_state']}"])
        if rec.get("frozen"):
            raise DomainError([f"V-COMMIT-03: cannot park frozen record: {target_id}"])
        if reason not in ("absorbed", "not_needed"):
            raise DomainError(["park reason must be absorbed|not_needed"])
        detail = None
        if reason == "absorbed":
            if not into:
                raise DomainError(["park --reason absorbed requires --into"])
            other = gv.record(into)
            if other is None or other["lifecycle_state"] != "active" or into == target_id:
                raise DomainError([f"--into must point at a different active record: {into}"])
            detail = {"absorbed_into": into}
        changes = {"lifecycle_state": "parked", "state_reason": reason, "state_detail": detail, "strength": "unassessed"}
        new = _update_record(rec, changes)
        file_rel = EDGES if ttype == "edge" else NODES
        action = "update_edge" if ttype == "edge" else "update_node"
        actions = [{"action": action, "target_id": target_id, "detail": {"lifecycle_state": "parked", "reason": reason}, "record": new}]
        commit_id = _admin_commit(paths, "park", actor, target_id, [(file_rel, new)], actions)
        return {"commit_id": commit_id}


def unpark(paths: Paths, target_id: str, actor: str | None = None) -> dict[str, Any]:
    actor = actor or clock_actor()
    with file_lock(paths.resolve(COMMIT_LOCK)):
        gv = graph_model.load(paths)
        rec = gv.record(target_id)
        ttype = gv.kind(target_id)
        if rec is None or rec["lifecycle_state"] != "parked":
            raise DomainError([f"unpark requires a parked record: {target_id}"])
        ever_proven = rec.get("latest_proof_result_id") is not None
        new_state = "pending_proof" if ever_proven else "candidate"
        changes = {"lifecycle_state": new_state, "state_reason": None, "state_detail": None, "strength": "unassessed"}
        new = _update_record(rec, changes)
        file_rel = EDGES if ttype == "edge" else NODES
        action = "update_edge" if ttype == "edge" else "update_node"
        actions = [{"action": action, "target_id": target_id, "detail": {"lifecycle_state": new_state}, "record": new}]
        deferred = []
        if new_state == "pending_proof":
            def _enq():
                item = engine.enqueue(paths, queue_name="proof_queue", target_type=ttype, target_id=target_id, actor=actor)
                actions.append({"action": "enqueue", "target_id": item["work_item_id"], "detail": {"queue": "proof_queue"}, "record": None})
            deferred.append(_enq)
        commit_id = _admin_commit(paths, "unpark", actor, target_id, [(file_rel, new)], actions, deferred)
        return {"commit_id": commit_id}


def freeze_batch(paths: Paths, target_ids: list[str], input_ref: str, actor: str | None = None) -> dict[str, Any]:
    """B6b freeze_batch: set frozen=true on targets (Freeze gate calls this)."""
    actor = actor or clock_actor()
    with file_lock(paths.resolve(COMMIT_LOCK)):
        gv = graph_model.load(paths)
        appends: list[tuple[str, dict[str, Any]]] = []
        actions: list[dict[str, Any]] = []
        for tid in target_ids:
            rec = gv.record(tid)
            ttype = gv.kind(tid)
            new = _update_record(rec, {"frozen": True})
            appends.append((EDGES if ttype == "edge" else NODES, new))
            actions.append({"action": "set_frozen", "target_id": tid, "detail": {"frozen": True}, "record": new})
        commit_id = _admin_commit(paths, "freeze_batch", actor, input_ref, appends, actions)
        return {"commit_id": commit_id}


def unfreeze_batch(paths: Paths, target_ids: list[str], input_ref: str, actor: str | None = None) -> dict[str, Any]:
    actor = actor or clock_actor()
    with file_lock(paths.resolve(COMMIT_LOCK)):
        gv = graph_model.load(paths)
        appends: list[tuple[str, dict[str, Any]]] = []
        actions: list[dict[str, Any]] = []
        deferred = []
        for tid in target_ids:
            rec = gv.record(tid)
            ttype = gv.kind(tid)
            new = _update_record(rec, {"frozen": False, "lifecycle_state": "pending_proof", "strength": "unassessed"})
            appends.append((EDGES if ttype == "edge" else NODES, new))
            actions.append({"action": "set_frozen", "target_id": tid, "detail": {"frozen": False}, "record": new})

            def _enq(tid=tid, ttype=ttype):
                item = engine.enqueue(paths, queue_name="proof_queue", target_type=ttype, target_id=tid, actor=actor)
                actions.append({"action": "enqueue", "target_id": item["work_item_id"], "detail": {"queue": "proof_queue"}, "record": None})
            deferred.append(_enq)
        commit_id = _admin_commit(paths, "unfreeze_batch", actor, input_ref, appends, actions, deferred)
        return {"commit_id": commit_id}


def contract_reopen(paths: Paths, target_ids: list[str], input_ref: str, actor: str | None = None) -> dict[str, Any]:
    """B6b contract_reopen: batch re-open after a contract version bump (v1: no
    CLI trigger; exercised via API in tests only)."""
    actor = actor or clock_actor()
    with file_lock(paths.resolve(COMMIT_LOCK)):
        gv = graph_model.load(paths)
        appends: list[tuple[str, dict[str, Any]]] = []
        actions: list[dict[str, Any]] = []
        deferred = []
        for tid in target_ids:
            rec = gv.record(tid)
            ttype = gv.kind(tid)
            new = _update_record(rec, {"lifecycle_state": "pending_proof", "strength": "unassessed", "state_reason": None})
            appends.append((EDGES if ttype == "edge" else NODES, new))
            actions.append({"action": "update_edge" if ttype == "edge" else "update_node", "target_id": tid, "detail": {"lifecycle_state": "pending_proof"}, "record": new})

            def _enq(tid=tid, ttype=ttype):
                item = engine.enqueue(paths, queue_name="proof_queue", target_type=ttype, target_id=tid, actor=actor)
                actions.append({"action": "enqueue", "target_id": item["work_item_id"], "detail": {"queue": "proof_queue"}, "record": None})
            deferred.append(_enq)
        commit_id = _admin_commit(paths, "contract_reopen", actor, input_ref, appends, actions, deferred)
        return {"commit_id": commit_id}
