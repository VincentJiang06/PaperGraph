"""Graph-record static checks (docs/09 V-NODE / V-EDGE / V-GRAPH).

Registered top-level rules (F14): the Expander reports V-NODE-02/03 under
V-EXP-05, and the Committer / verify report structural violations under
V-COMMIT-05. Keeping them here means one implementation of "single
proposition", "reachability", and "no cycles".
"""

from __future__ import annotations

from typing import Any

from ...textutil import casefold, contains, sentence_count
from ..envelope import Failure

# V-NODE-02 static compound phrases (docs/09).
COMPOUND_PHRASES = ("; and", "and therefore", "which means")


def node02_ok(claim: str) -> tuple[bool, str]:
    """V-NODE-02: 1-2 sentences, single proposition (static heuristic)."""
    n = sentence_count(claim)
    if not (1 <= n <= 2):
        return False, f"claim has {n} sentences (want 1-2)"
    for phrase in COMPOUND_PHRASES:
        if contains(claim, phrase):
            return False, f"claim contains compound phrase {phrase!r}"
    return True, ""


def node03_ok(node_scope: dict[str, Any], contract_scope: dict[str, Any]) -> tuple[bool, str]:
    """V-NODE-03: node scope compatible with the contract scope."""
    from ...textutil import scope_compatible

    if scope_compatible(node_scope or {}, contract_scope or {}):
        return True, ""
    return False, "node scope incompatible with contract scope"


def edge02_ok(edge_claim: str, source_claim: str, target_claim: str) -> tuple[bool, str]:
    """V-EDGE-02: edge_claim is not a verbatim restatement of either endpoint."""
    ec = casefold(edge_claim)
    if ec == casefold(source_claim) or ec == casefold(target_claim):
        return False, "edge_claim restates an endpoint claim verbatim"
    return True, ""


def no_supports_cycle(edges: list[dict[str, Any]]) -> tuple[bool, str]:
    """V-GRAPH-01: no supports/depends_on cycle among non-rejected edges."""
    adj: dict[str, list[str]] = {}
    for e in edges:
        if e["lifecycle_state"] == "rejected":
            continue
        if e["edge_type"] not in ("supports", "depends_on"):
            continue
        adj.setdefault(e["source_node_id"], []).append(e["target_node_id"])
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {}

    def visit(node: str) -> bool:
        color[node] = GRAY
        for nxt in adj.get(node, []):
            c = color.get(nxt, WHITE)
            if c == GRAY:
                return False
            if c == WHITE and not visit(nxt):
                return False
        color[node] = BLACK
        return True

    for node in list(adj.keys()):
        if color.get(node, WHITE) == WHITE and not visit(node):
            return False, f"supports/depends_on cycle at {node}"
    return True, ""


def graph_record_checks(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> list[Failure]:
    """V-EDGE-01/02/03/04 + V-NODE-04 + V-GRAPH-01..03 over the whole graph (used
    by verify + the commit-time V-COMMIT-05 post-graph check)."""
    failures: list[Failure] = []
    node_claim = {n["node_id"]: n.get("claim", "") for n in nodes}
    ok, detail = no_supports_cycle(edges)
    if not ok:
        failures.append(Failure("V-GRAPH-01", detail))

    # V-EDGE-02: an active/pending edge_claim must not verbatim-restate either
    # endpoint's claim (static, casefold). Rejected edges are exempt.
    for e in edges:
        if e["lifecycle_state"] == "rejected":
            continue
        ok2, detail2 = edge02_ok(
            e["edge_claim"],
            node_claim.get(e["source_node_id"], ""),
            node_claim.get(e["target_node_id"], ""),
        )
        if not ok2:
            failures.append(Failure("V-EDGE-02", f"{e['edge_id']}: {detail2}"))

    # V-EDGE-01: a non-rejected edge's endpoints must resolve to existing nodes
    # and may not coincide (no self-loop). A rejected edge is exempt (its
    # endpoints may since have been tombstoned/removed).
    node_ids = set(node_claim)
    for e in edges:
        if e["lifecycle_state"] == "rejected":
            continue
        if e["source_node_id"] == e["target_node_id"]:
            failures.append(Failure("V-EDGE-01", f"{e['edge_id']}: self-loop at {e['source_node_id']}"))
        for ep_key in ("source_node_id", "target_node_id"):
            if e[ep_key] not in node_ids:
                failures.append(Failure("V-EDGE-01", f"{e['edge_id']}: endpoint {e[ep_key]} does not resolve to a node"))

    # V-EDGE-03: at most one non-rejected edge per (source, target, edge_type).
    # Recreation after a rejection (a fresh edge id) is legal because the prior
    # is rejected; a SECOND live edge over the same triple is a duplicate.
    seen_triples: dict[tuple[str, str, str], str] = {}
    for e in edges:
        if e["lifecycle_state"] == "rejected":
            continue
        key = (e["source_node_id"], e["target_node_id"], e["edge_type"])
        prior = seen_triples.get(key)
        if prior is not None:
            failures.append(Failure(
                "V-EDGE-03",
                f"{e['edge_id']}: duplicate live edge of {prior} ({key[2]} {key[0]}->{key[1]})",
            ))
        else:
            seen_triples[key] = e["edge_id"]

    # V-NODE-04: a non-rejected node's every parent must resolve to a known node
    # id (existence half) AND that parent must not itself be rejected — a
    # non-rejected node may not hang off a rejected parent. (The existence half
    # also guards an at-rest graph against a parent removed after the append.)
    rejected_node_ids = {n["node_id"] for n in nodes if n["lifecycle_state"] == "rejected"}
    for n in nodes:
        if n["lifecycle_state"] == "rejected":
            continue
        for pid in n.get("parents") or []:
            if pid not in node_claim:
                failures.append(Failure("V-NODE-04", f"{n['node_id']}: parent {pid} does not exist"))
            elif pid in rejected_node_ids:
                failures.append(Failure("V-NODE-04", f"{n['node_id']}: parent {pid} is rejected"))

    # V-EDGE-04 (v1 restriction, docs/02): a non-rejected refutes edge may only
    # target an alternative node.
    node_type = {n["node_id"]: n.get("node_type") for n in nodes}
    for e in edges:
        if e["lifecycle_state"] == "rejected" or e["edge_type"] != "refutes":
            continue
        tgt_type = node_type.get(e["target_node_id"])
        if tgt_type != "alternative":
            failures.append(Failure(
                "V-EDGE-04", f"{e['edge_id']}: refutes targets {tgt_type!r} (must be alternative)"
            ))

    # V-GRAPH-03: strength iff active; frozen only on active.
    for rec in list(nodes) + list(edges):
        rid = rec.get("node_id") or rec.get("edge_id")
        active = rec["lifecycle_state"] == "active"
        strong = rec["strength"] in ("strong", "conditional")
        if active != strong:
            failures.append(Failure("V-GRAPH-03", f"{rid}: strength/active mismatch"))
        if rec.get("frozen") and not active:
            failures.append(Failure("V-GRAPH-03", f"{rid}: frozen but not active"))

    # V-GRAPH-02: every non-seed, non-rejected node reachable from a layer-0
    # node via parents or edges.
    node_by_id = {n["node_id"]: n for n in nodes}
    reachable: set[str] = set()
    # layer-0 seeds: origin.kind == seed, or the question/thesis nodes.
    frontier: list[str] = []
    for n in nodes:
        if n["lifecycle_state"] == "rejected":
            continue
        if n["origin"]["kind"] == "seed" or n["node_type"] in ("question", "thesis"):
            reachable.add(n["node_id"])
            frontier.append(n["node_id"])
    # propagate along parents (child reachable if a parent is) and edges
    changed = True
    child_edges: dict[str, list[str]] = {}
    for e in edges:
        if e["lifecycle_state"] == "rejected":
            continue
        child_edges.setdefault(e["target_node_id"], []).append(e["source_node_id"])
        child_edges.setdefault(e["source_node_id"], []).append(e["target_node_id"])
    while changed:
        changed = False
        for n in nodes:
            nid = n["node_id"]
            if nid in reachable or n["lifecycle_state"] == "rejected":
                continue
            parents = n.get("parents") or []
            if any(p in reachable for p in parents) or any(
                nb in reachable for nb in child_edges.get(nid, [])
            ):
                reachable.add(nid)
                changed = True
    for n in nodes:
        if n["lifecycle_state"] == "rejected":
            continue
        if n["node_id"] not in reachable:
            failures.append(Failure("V-GRAPH-02", f"{n['node_id']} unreachable from layer-0"))
    return failures
