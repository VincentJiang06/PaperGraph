"""Read-only graph model (docs/02, docs/08 B4).

Loads the latest record per id from the append-only graph JSONL files and derives
the structures every downstream module consumes: 1-hop neighborhoods (V-TASK-02),
the spine (docs/02), and the structural signatures the staleness/currency checks
compare. No mutation happens here — the Committer is the only graph writer.
"""

from __future__ import annotations

from typing import Any

from ..paths import Paths
from ..store import jsonl

NODES_FILE = "graph/logic_nodes.jsonl"
EDGES_FILE = "graph/logic_edges.jsonl"
TOMBSTONES_FILE = "graph/tombstones.jsonl"


class GraphView:
    """A latest-per-id snapshot of the graph at read time."""

    def __init__(self, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> None:
        self.nodes = nodes
        self.edges = edges
        self.node_by_id: dict[str, dict[str, Any]] = {n["node_id"]: n for n in nodes}
        self.edge_by_id: dict[str, dict[str, Any]] = {e["edge_id"]: e for e in edges}

    # -- record sets --------------------------------------------------------

    def record(self, target_id: str) -> dict[str, Any] | None:
        return self.node_by_id.get(target_id) or self.edge_by_id.get(target_id)

    def kind(self, target_id: str) -> str | None:
        if target_id in self.node_by_id:
            return "node"
        if target_id in self.edge_by_id:
            return "edge"
        return None

    def non_rejected_nodes(self) -> list[dict[str, Any]]:
        return [n for n in self.nodes if n["lifecycle_state"] != "rejected"]

    def non_rejected_edges(self) -> list[dict[str, Any]]:
        return [e for e in self.edges if e["lifecycle_state"] != "rejected"]

    def active_ids(self) -> set[str]:
        out = {n["node_id"] for n in self.nodes if n["lifecycle_state"] == "active"}
        out |= {e["edge_id"] for e in self.edges if e["lifecycle_state"] == "active"}
        return out

    def is_active(self, target_id: str) -> bool:
        rec = self.record(target_id)
        return bool(rec and rec["lifecycle_state"] == "active")

    # -- neighborhoods ------------------------------------------------------

    def incident_edges(self, node_id: str) -> list[dict[str, Any]]:
        """Non-rejected edges with this node as source or target."""
        return [
            e
            for e in self.non_rejected_edges()
            if e["source_node_id"] == node_id or e["target_node_id"] == node_id
        ]

    def one_hop(self, target_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Return (neighbor_nodes, neighbor_edges) for a target (V-TASK-02).

        NODE target: every non-rejected incident edge + those edges' other
        endpoints. EDGE target: both endpoint nodes, every non-rejected edge
        incident to either endpoint, and those edges' other endpoints. The
        target record itself is never listed among its own neighbors.
        """
        neighbor_node_ids: set[str] = set()
        neighbor_edge_ids: set[str] = set()

        if target_id in self.node_by_id:
            for e in self.incident_edges(target_id):
                neighbor_edge_ids.add(e["edge_id"])
                for endpoint in (e["source_node_id"], e["target_node_id"]):
                    if endpoint != target_id:
                        neighbor_node_ids.add(endpoint)
        elif target_id in self.edge_by_id:
            edge = self.edge_by_id[target_id]
            endpoints = {edge["source_node_id"], edge["target_node_id"]}
            neighbor_node_ids |= endpoints
            for ep in endpoints:
                for e in self.incident_edges(ep):
                    if e["edge_id"] == target_id:
                        continue
                    neighbor_edge_ids.add(e["edge_id"])
                    for endpoint in (e["source_node_id"], e["target_node_id"]):
                        if endpoint not in endpoints:
                            neighbor_node_ids.add(endpoint)

        nodes = [self.node_by_id[nid] for nid in sorted(neighbor_node_ids) if nid in self.node_by_id]
        edges = [self.edge_by_id[eid] for eid in sorted(neighbor_edge_ids) if eid in self.edge_by_id]
        return nodes, edges

    def one_hop_ids(self, target_id: str) -> set[str]:
        nodes, edges = self.one_hop(target_id)
        return {n["node_id"] for n in nodes} | {e["edge_id"] for e in edges}

    def claim_digest(self) -> list[dict[str, str]]:
        """{node_id, claim} for every non-rejected node (docs/08 B4), by id."""
        return [
            {"node_id": n["node_id"], "claim": n["claim"]}
            for n in sorted(self.non_rejected_nodes(), key=lambda n: n["node_id"])
        ]

    # -- spine (docs/02) ----------------------------------------------------

    def unique_node_of_type(self, node_type: str) -> dict[str, Any] | None:
        found = [n for n in self.nodes if n["node_type"] == node_type and n["lifecycle_state"] != "rejected"]
        return found[0] if len(found) == 1 else None

    def spine(self) -> tuple[set[str], dict[str, Any]]:
        """Compute the spine id set (docs/02). Returns (ids, detail)."""
        detail: dict[str, Any] = {}
        q = self.unique_node_of_type("question")
        t = self.unique_node_of_type("thesis")
        if q is None or t is None or q["lifecycle_state"] != "active" or t["lifecycle_state"] != "active":
            detail["reason"] = "question/thesis missing or not active"
            return set(), detail

        active = self.active_ids()
        ids: set[str] = {q["node_id"], t["node_id"]}

        # the supports edge T -> Q must be active to seed the spine
        tq_edge = None
        for e in self.edges:
            if (
                e["source_node_id"] == t["node_id"]
                and e["target_node_id"] == q["node_id"]
                and e["edge_type"] == "supports"
                and e["lifecycle_state"] == "active"
            ):
                tq_edge = e
                break
        if tq_edge is not None:
            ids.add(tq_edge["edge_id"])

        # active ancestor closure of T along active supports/depends_on edges
        # (edges point source -> target; we walk backwards from T to sources).
        by_target: dict[str, list[dict[str, Any]]] = {}
        for e in self.edges:
            if e["lifecycle_state"] != "active":
                continue
            if e["edge_type"] not in ("supports", "depends_on"):
                continue
            by_target.setdefault(e["target_node_id"], []).append(e)

        stack = [t["node_id"]]
        seen_nodes: set[str] = {t["node_id"]}
        while stack:
            cur = stack.pop()
            for e in by_target.get(cur, []):
                src = e["source_node_id"]
                # active ancestor closure (docs/02): an active edge joins the
                # spine only when its SOURCE node is also active — an active edge
                # dangling off a reverted (pending/rejected) source is NOT spine.
                if src not in active:
                    continue
                ids.add(e["edge_id"])
                ids.add(src)
                if src not in seen_nodes:
                    seen_nodes.add(src)
                    stack.append(src)
        return ids, detail


def load(paths: Paths) -> GraphView:
    nodes = jsonl.latest_records(paths.resolve(NODES_FILE), "node_id")
    edges = jsonl.latest_records(paths.resolve(EDGES_FILE), "edge_id")
    return GraphView(nodes, edges)


# --- evidence resolution (docs/04) ------------------------------------------
#
# The r3/m5 flat "at-least-two bindings from two documents" floor that lived here
# is SUPERSEDED by the S4 role-profile floors (docs/17): MSA-4, V-FRZ-02 and the
# compiler's missing_evidence gap now all delegate to
# ``docsdb.coverage.target_ledger`` + ``coverage.meets_floor`` (which read the
# evidence JSONL themselves).


def load_tombstones(paths: Paths) -> list[dict[str, Any]]:
    return jsonl.latest_records(paths.resolve(TOMBSTONES_FILE), "tombstone_id")


# --- structural signatures (staleness / currency) --------------------------


def structural_signature(record: dict[str, Any]) -> tuple[Any, ...]:
    """The fields whose change makes a bundle stale: id, claim_version,
    rejected-ness. A pure lifecycle pass (pending -> active) does NOT change the
    signature, so parallel proofs don't invalidate each other (docs/05)."""
    rid = record.get("node_id") or record.get("edge_id")
    return (rid, record.get("claim_version"), record.get("lifecycle_state") == "rejected")
