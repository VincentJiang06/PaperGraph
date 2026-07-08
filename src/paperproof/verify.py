"""`paperproof verify` — whole-project invariant sweep (docs/09 §3).

Re-validates every stored record against its schema, resolves cross-references,
runs V-GRAPH-* on the full graph, recomputes every verdict (V-PR-12), replays the
queue event log (V-Q) and every CommitDecision (V-COMMIT-04), and checks the
snapshot chain. Exit 0 = clean; any violation raises CorruptStateError (exit 3).

M1 is tolerant of absent freeze/compiler/docs state (those files exist empty from
`project init` and arrive in M2/M3).
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from .errors import CorruptStateError
from .committer.decision_table import compute_verdict
from .graph import model as graph_model
from .paths import Paths
from .schemas import REGISTRY
from .store import jsonl
from .validate.envelope import Failure, to_envelope
from .validate.rules import v_commit, v_node_edge, v_q, v_src

# Canonical JSONL files whose records carry a schema_version.
_JSONL_FILES = (
    "graph/logic_nodes.jsonl", "graph/logic_edges.jsonl", "graph/tombstones.jsonl",
    "graph/snapshots.jsonl", "proof/proof_results.jsonl", "docs/documents.jsonl",
    "docs/evidence_units.jsonl", "docs/docs_requests.jsonl", "docs/sources.jsonl",
    "docs/waves.jsonl",
    "queue/work_items.jsonl",
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

    # evidence ids: every non-rejected node's evidence_bindings resolve to an
    # archived EvidenceUnit (docs/09 §3 cross-reference resolution).
    gv = graph_model.load(paths)
    evidence_ids = {e["evidence_id"] for e in jsonl.latest_records(paths.resolve("docs/evidence_units.jsonl"), "evidence_id")}
    node_ids = set(gv.node_by_id)
    for node in gv.non_rejected_nodes():
        for eid in node.get("evidence_bindings", []) or []:
            if eid not in evidence_ids:
                failures.append(Failure("V-XREF", f"node {node['node_id']} -> dangling evidence_binding {eid}"))

    # duplicate_of: every rejected(duplicate) node's state_detail.duplicate_of and
    # every tombstone duplicate_of resolves to a real node/edge id.
    for node in gv.nodes:
        if node.get("state_reason") == "duplicate":
            dup = (node.get("state_detail") or {}).get("duplicate_of")
            if dup is not None and dup not in node_ids:
                failures.append(Failure("V-XREF", f"node {node['node_id']} -> dangling duplicate_of {dup}"))
    all_ids = node_ids | set(gv.edge_by_id)
    for ts in graph_model.load_tombstones(paths):
        dup = ts.get("duplicate_of")
        if dup is not None and dup not in all_ids:
            failures.append(Failure("V-XREF", f"tombstone {ts['tombstone_id']} -> dangling duplicate_of {dup}"))
    return failures


def _graph_check(paths: Paths) -> list[Failure]:
    gv = graph_model.load(paths)
    return v_node_edge.graph_record_checks(gv.nodes, gv.edges)


def _wave_check(paths: Paths) -> list[Failure]:
    """V-WAVE at rest across the wave lifecycle (docs/09 §V-WAVE, docs/15). These
    are corruption guards, not judgement:

    V-WAVE-01  a wave's member output paths are pairwise distinct — a collision
               means a follow-up round would silently overwrite (lose) a
               committed round-1 member's ingested evidence.
    V-WAVE-02  a CLOSED wave's stored merged result is the deterministic merge of
               its terminal members, and every merged doc/EU traces to a member.
    """
    from .docsdb import wave as wave_mod
    from .queue import engine
    from .validate.rules import v_wave

    failures: list[Failure] = []
    by_id = engine.items_by_id(paths)
    for w in wave_mod.load_waves(paths):
        wid = w.get("wave_id")
        member_paths: list[str] = []
        for mem in w.get("members", []) or []:
            item = by_id.get(mem.get("work_item_id"))
            files = (item or {}).get("output_files") or []
            if files:
                member_paths.append(files[0])
        for f in v_wave.check_member_paths(member_paths):
            failures.append(Failure(f.rule_id, f"wave {wid}: {f.detail}"))

        # V-WAVE-02 traceability: only a closed wave has a final merged file that
        # reflects its whole terminal member set (mid-lifecycle a follow-up round
        # may have added members the merged file does not yet include).
        if w.get("status") == "closed":
            merged_p = paths.project_dir / wave_mod.merged_relpath(w.get("request_id"))
            if merged_p.exists():
                merged = json.loads(merged_p.read_text(encoding="utf-8"))
                members = wave_mod._collect_member_results(paths, w)
                for f in v_wave.check_merge(members, merged, w.get("request_id"), paths.project_id):
                    failures.append(Failure(f.rule_id, f"wave {wid}: {f.detail}"))
    return failures


def run(paths: Paths) -> dict[str, Any]:
    if not paths.project_dir.exists():
        raise CorruptStateError([f"project not found: {paths.project_id}"])
    failures: list[Failure] = []
    failures += _schema_check(paths)
    failures += _graph_check(paths)
    failures += _verdict_recompute(paths)
    failures += v_q.verify_queue(paths)
    failures += v_commit.verify_commits(paths)
    failures += v_src.verify_sources(paths)
    failures += _wave_check(paths)
    failures += _crossref(paths)

    if failures:
        env = to_envelope(failures)
        raise CorruptStateError(
            env["failed_rules"],
            data={"failed_rules": env["failed_rules"], "detail": env["detail"]},
        )

    # DB manifest freshness (docs/09 §3): warning only — a stale derived index is
    # never a corruption, since db/ is rebuildable from the canonical JSONL.
    warnings: list[str] = []
    from .db import indexer as _indexer

    if paths.resolve(_indexer.MANIFEST_FILE).exists():
        if _indexer.check(paths)["stale_index"]:
            warnings.append("db index is stale (run `paperproof db rebuild`)")

    return {"ok": True, "checked": True, "warnings": warnings}
