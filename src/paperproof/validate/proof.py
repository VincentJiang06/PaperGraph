"""`validate result` orchestration (docs/08 B5, docs/10 §4).

Runs V-PATH (path safety + prefix scan) then V-PR-03 raw scan then the V-PR
semantic block; on success computes the verdict, appends the verdict record to
proof/proof_results.jsonl (assigning the PR- id), and moves the work item
validating -> validated. On failure the item goes validating -> failed (with
retry/dead per attempt) and the failed rule ids are returned.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..clock import actor as clock_actor
from ..clock import now as clock_now
from ..errors import DomainError, UsageError
from ..ids import next_id
from ..paths import Paths
from ..queue import engine
from ..schemas.proof import VerdictRecord
from ..store import file_lock, jsonl
from .envelope import Failure, to_envelope
from .rules import v_path, v_pr

PROOF_RESULTS = "proof/proof_results.jsonl"


def _to_relpath(paths: Paths, output_file: str) -> str:
    p = Path(output_file)
    if p.is_absolute():
        try:
            return str(p.resolve().relative_to(paths.project_dir.resolve()))
        except ValueError:
            return output_file
    return output_file


def validate_result(paths: Paths, output_file: str, work_item_id: str, actor: str | None = None) -> dict[str, Any]:
    actor = actor or clock_actor()
    wi = engine.get_item(paths, work_item_id)
    if wi["status"] != "validating":
        raise DomainError([f"work item not in validating state: {work_item_id} ({wi['status']})"])

    relpath = _to_relpath(paths, output_file)
    failures: list[Failure] = []

    # V-PATH
    failures += v_path.check_output_path(relpath, wi.get("output_files", []))
    failures += v_path.check_path_safety(paths.project_dir, relpath)
    vpath03 = v_path.check_utf8_json(paths.project_dir, relpath)
    failures += vpath03
    lease = wi.get("lease") or {}
    if lease.get("manifest"):
        failures += v_path.check_lease_scan(paths.project_dir, lease["manifest"])

    verdict: dict[str, Any] | None = None
    if not vpath03:  # file exists and is valid JSON -> we can parse it
        raw = json.loads((paths.project_dir / relpath).read_text(encoding="utf-8"))
        # V-PR-03 raw scan (before schema parse)
        failures += v_pr.raw_scan(raw)
        # bundle inputs
        task = jsonl.read_json(paths.resolve(wi["bundle"]["task_file"]))
        context_pack = jsonl.read_json(paths.resolve(wi["bundle"]["context_pack"]))
        docs_pack = jsonl.read_json(paths.resolve(wi["bundle"]["docs_pack"]))
        vpr_failures, verdict = v_pr.check(raw, task=task, context_pack=context_pack, docs_pack=docs_pack, work_item=wi)
        failures += vpr_failures

    if failures:
        env = to_envelope(failures)
        engine.validate_fail(paths, work_item_id, env["failed_rules"], actor)
        raise DomainError(
            env["failed_rules"],
            data={"failed_rules": env["failed_rules"], "detail": env["detail"]},
        )

    # success: append verdict record, then validate_pass. PR-id allocation +
    # append must be atomic under proof/.lock (docs/07) — parallel validators (S4)
    # otherwise race to the same PR id (read-then-append is not atomic).
    with file_lock(paths.resolve("proof/.lock")):
        pr_id = next_id("PR", [r["proof_result_id"] for r in jsonl.read_all(paths.resolve(PROOF_RESULTS))])
        record = _build_verdict_record(paths, pr_id, work_item_id, raw, verdict, wi)
        jsonl.append(paths.resolve(PROOF_RESULTS), record)
    engine.validate_pass(paths, work_item_id, actor, detail={"proof_result_id": pr_id})
    return {"proof_result_id": pr_id, "computed_verdict": verdict}


def _build_verdict_record(paths, pr_id, work_item_id, raw, verdict, wi):
    return VerdictRecord.model_validate(
        {
            "proof_result_id": pr_id,
            "project_id": paths.project_id,
            "work_item_id": work_item_id,
            "task_id": raw["task_id"],
            "target_type": raw["target_type"],
            "target_id": raw["target_id"],
            "form": raw["form"],
            "assumptions": raw.get("assumptions", []),
            "evidence_used": raw.get("evidence_used", []),
            "language_limits": raw.get("language_limits"),
            "repair_proposals": raw.get("repair_proposals", []),
            "docs_requests": raw.get("docs_requests", []),
            "notes": raw.get("notes", ""),
            "computed_verdict": verdict,
            "bundle": wi["bundle"],
            "validated_at": clock_now(),
        }
    )
