"""V-TASK: bundle content (docs/09).

V-TASK-01  claim refuses items marked stale until rebuilt with a -rN revision
           (behavior — covered by the S6 scenario)
V-TASK-02  ContextPack contains target + all 1-hop neighbors at its snapshot +
           claim_digest covering every non-rejected node
V-TASK-03  DocsPack evidence ids all resolve to archived Documents
"""

from __future__ import annotations

from typing import Any

from ...graph import model as graph_model
from ...paths import Paths
from ..envelope import Failure


def check_context_pack(paths: Paths, context_pack: dict[str, Any]) -> list[Failure]:
    """V-TASK-02: the pack's neighbor set matches the 1-hop of its target and the
    claim_digest covers every non-rejected node."""
    failures: list[Failure] = []
    gv = graph_model.load(paths)
    target = context_pack.get("target", {})
    tid = target.get("node_id") or target.get("edge_id")
    if tid is None:
        failures.append(Failure("V-TASK-02", "context pack target has no id"))
        return failures
    exp_nodes, exp_edges = gv.one_hop(tid)
    got_nodes = {n["node_id"] for n in context_pack.get("neighbor_nodes", [])}
    got_edges = {e["edge_id"] for e in context_pack.get("neighbor_edges", [])}
    if got_nodes != {n["node_id"] for n in exp_nodes}:
        failures.append(Failure("V-TASK-02", "neighbor_nodes != 1-hop nodes"))
    if got_edges != {e["edge_id"] for e in exp_edges}:
        failures.append(Failure("V-TASK-02", "neighbor_edges != 1-hop edges"))
    got_digest = {d["node_id"] for d in context_pack.get("claim_digest", [])}
    exp_digest = {n["node_id"] for n in gv.non_rejected_nodes()}
    if got_digest != exp_digest:
        failures.append(Failure("V-TASK-02", "claim_digest does not cover every non-rejected node"))
    return failures


def check_docs_pack(paths: Paths, docs_pack: dict[str, Any]) -> list[Failure]:
    """V-TASK-03: every DocsPack evidence id resolves to an archived Document."""
    from ...store import jsonl

    failures: list[Failure] = []
    doc_ids = {d["doc_id"] for d in jsonl.latest_records(paths.resolve("docs/documents.jsonl"), "doc_id")}
    for eu in docs_pack.get("evidence_units", []):
        did = eu.get("doc_id")
        if did is not None and did not in doc_ids:
            failures.append(Failure("V-TASK-03", f"evidence references unknown doc {did}"))
    return failures
