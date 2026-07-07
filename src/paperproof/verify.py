"""`paperproof verify` — whole-project invariant sweep (docs/09 §3).

Re-validates every stored record against its schema, resolves cross-references,
runs V-GRAPH-* on the full graph, recomputes every verdict (V-PR-12), replays the
queue event log (V-Q) and every CommitDecision (V-COMMIT-04), and checks the
snapshot chain. Exit 0 = clean; any violation raises CorruptStateError (exit 3).

M1 is tolerant of absent freeze/compiler/docs state (those files exist empty from
`project init` and arrive in M2/M3).
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from .errors import CorruptStateError
from .committer.decision_table import compute_verdict
from .graph import model as graph_model
from .paths import Paths
from .schemas import REGISTRY
from .store import jsonl
from .validate.envelope import Failure, to_envelope
from .validate.rules import v_commit, v_node_edge, v_q

# Canonical JSONL files whose records carry a schema_version.
_JSONL_FILES = (
    "graph/logic_nodes.jsonl", "graph/logic_edges.jsonl", "graph/tombstones.jsonl",
    "graph/snapshots.jsonl", "proof/proof_results.jsonl", "docs/documents.jsonl",
    "docs/evidence_units.jsonl", "docs/docs_requests.jsonl", "queue/work_items.jsonl",
    "queue/events.jsonl", "commit/commit_decisions.jsonl", "freeze/frozen_items.jsonl",
    "compiler/dry_runs.jsonl", "compiler/draft_maps.jsonl", "audit/audit_reports.jsonl",
)


def _schema_check(paths: Paths) -> list[Failure]:
    failures: list[Failure] = []
    for rel in _JSONL_FILES:
        for i, rec in enumerate(jsonl.read_all(paths.resolve(rel)), start=1):
            sv = rec.get("schema_version")
            model = REGISTRY.get(sv)
            if model is None:
                failures.append(Failure("V-SCHEMA", f"{rel}:{i} unknown schema_version {sv!r}"))
                continue
            try:
                model.model_validate(rec)
            except ValidationError as exc:
                failures.append(Failure("V-SCHEMA", f"{rel}:{i} {sv}: {exc.errors()[:1]}"))
    return failures


def _verdict_recompute(paths: Paths) -> list[Failure]:
    failures: list[Failure] = []
    for r in jsonl.read_all(paths.resolve("proof/proof_results.jsonl")):
        task_type = "EDGE_CHECK" if r["target_type"] == "edge" else "NODE_CHECK"
        recomputed = compute_verdict(r["form"], task_type, r.get("assumptions", []))
        if recomputed != r["computed_verdict"]:
            failures.append(Failure("V-PR-12", f"{r['proof_result_id']}: verdict mismatch"))
    return failures


def _crossref(paths: Paths) -> list[Failure]:
    failures: list[Failure] = []
    from .queue import engine

    item_ids = set(engine.items_by_id(paths))
    pr_ids = {r["proof_result_id"] for r in jsonl.read_all(paths.resolve("proof/proof_results.jsonl"))}
    for r in jsonl.read_all(paths.resolve("proof/proof_results.jsonl")):
        if r["work_item_id"] not in item_ids:
            failures.append(Failure("V-XREF", f"verdict {r['proof_result_id']} -> missing work item"))
    snap_ids = {s["snapshot_id"] for s in jsonl.read_all(paths.snapshots)}
    for cd in jsonl.read_all(paths.resolve("commit/commit_decisions.jsonl")):
        for key in ("based_on_snapshot", "post_snapshot"):
            if cd[key] not in snap_ids:
                failures.append(Failure("V-XREF", f"commit {cd['commit_id']} -> missing snapshot {cd[key]}"))
    return failures


def _graph_check(paths: Paths) -> list[Failure]:
    gv = graph_model.load(paths)
    return v_node_edge.graph_record_checks(gv.nodes, gv.edges)


def run(paths: Paths) -> dict[str, Any]:
    if not paths.project_dir.exists():
        raise CorruptStateError([f"project not found: {paths.project_id}"])
    failures: list[Failure] = []
    failures += _schema_check(paths)
    failures += _graph_check(paths)
    failures += _verdict_recompute(paths)
    failures += v_q.verify_queue(paths)
    failures += v_commit.verify_commits(paths)
    failures += _crossref(paths)

    if failures:
        env = to_envelope(failures)
        raise CorruptStateError(
            env["failed_rules"],
            data={"failed_rules": env["failed_rules"], "detail": env["detail"]},
        )
    return {"ok": True, "checked": True}
