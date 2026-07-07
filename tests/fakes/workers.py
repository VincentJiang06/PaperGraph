"""FakeWorkers + the drain dispatcher (docs/11 §5).

FakeProofWorker reads a real bundle and writes a scripted, schema-valid
proof_result.v1 at the declared output path — so the whole pipeline path
(claim -> write -> complete -> validate -> commit) runs unchanged. Modes:
  'script'  : render the scripted form for the target id
  'crash'   : return without writing (exercises the lease-expiry path)
  'hostile' : perform the scripted misbehavior (extra writes, bad payload)

``drain`` claims/runs/completes/validates until the proof queue is quiet, then
commits validated items serially. ``parallel=N`` uses threads to exercise the
queue/commit locks (S4).
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from paperproof.committer import apply as committer
from paperproof.paths import Paths
from paperproof.prooftask import builder
from paperproof.queue import engine
from paperproof.store import jsonl
from paperproof.validate import proof as validate_proof


class FakeProofWorker:
    def __init__(self, script: dict[str, Any] | str | Path, mode: str = "script") -> None:
        if isinstance(script, (str, Path)):
            script = json.loads(Path(script).read_text(encoding="utf-8"))
        self.script = script
        self.mode = mode
        self._counts: dict[str, int] = {}

    def run(self, work_item: dict[str, Any], project_root: Path) -> None:
        if self.mode == "crash":
            return  # write nothing; the lease will expire
        task = json.loads((project_root / work_item["bundle"]["task_file"]).read_text(encoding="utf-8"))
        target_id = work_item["target_id"]
        entry = self.script[target_id]
        if isinstance(entry, list):
            # A target may be proved multiple times (re-proof); consume in order.
            idx = min(self._counts.get(target_id, 0), len(entry) - 1)
            self._counts[target_id] = self._counts.get(target_id, 0) + 1
            spec = dict(entry[idx])
        else:
            spec = dict(entry)
        output_rel = work_item["output_files"][0]
        out_path = project_root / output_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if self.mode == "hostile":
            self._hostile(spec, work_item, project_root, out_path, task)
            return

        result = self._render(spec, task, target_id)
        out_path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")

    def _render(self, spec: dict[str, Any], task: dict[str, Any], target_id: str) -> dict[str, Any]:
        target_type = "edge" if "edge_id" in task["target"] else "node"
        return {
            "schema_version": "proof_result.v1",
            "task_id": task["task_id"],
            "project_id": task["project_id"],
            "target_type": target_type,
            "target_id": target_id,
            "form": spec["form"],
            "assumptions": spec.get("assumptions", []),
            "evidence_used": spec.get("evidence_used", []),
            "language_limits": spec.get("language_limits"),
            "repair_proposals": spec.get("repair_proposals", []),
            "docs_requests": spec.get("docs_requests", []),
            "notes": spec.get("notes", "ok"),
        }

    def _hostile(self, spec, work_item, project_root, out_path, task) -> None:
        behavior = spec.get("hostile")
        # write a base valid form first (unless the behavior replaces it)
        result = self._render(spec, task, work_item["target_id"])
        if behavior == "extra_file":  # H01: a second file outside allowed paths
            out_path.write_text(json.dumps(result), encoding="utf-8")
            (project_root / "docs" / "sneaky_extra.txt").write_text("x", encoding="utf-8")
        elif behavior == "append_graph":  # H10: append to a committer-owned file
            out_path.write_text(json.dumps(result), encoding="utf-8")
            with (project_root / "graph" / "logic_nodes.jsonl").open("a", encoding="utf-8") as fh:
                fh.write('{"node_id":"NODE-999"}\n')
        else:
            out_path.write_text(json.dumps(result), encoding="utf-8")


def _verdict_for_item(paths: Paths, wi_id: str) -> str | None:
    latest = None
    for r in jsonl.read_all(paths.resolve("proof/proof_results.jsonl")):
        if r["work_item_id"] == wi_id:
            latest = r["proof_result_id"]
    return latest


def drain(paths: Paths, worker: FakeProofWorker, parallel: int = 1, max_rounds: int = 100, actor: str = "test") -> None:
    """Process the proof queue to quiescence; commit validated items serially."""
    for _ in range(max_rounds):
        builder.build_frontier(paths, actor)
        engine.run_sweeps(paths, actor)
        claimable = [
            i
            for i in engine.load_items(paths)
            if i["queue_name"] == "proof_queue" and engine.is_claimable(paths, i)
        ]
        did = 0
        if claimable:
            _run_batch(paths, worker, len(claimable), parallel)
            did += len(claimable)
        # commit validated serially (FIFO)
        validated = sorted(
            [i for i in engine.load_items(paths) if i["status"] == "validated"],
            key=lambda i: i["work_item_id"],
        )
        for v in validated:
            pr = _verdict_for_item(paths, v["work_item_id"])
            if pr:
                committer.apply_proof_verdict(paths, pr, actor)
                did += 1
        if did == 0:
            break


def prove_one(paths: Paths, target_id: str, worker: FakeProofWorker, commit: bool = True, actor: str = "test") -> dict[str, Any]:
    """Claim the open item for a target, run the worker, complete + validate, and
    (optionally) commit. Returns {work_item_id, proof_result_id, commit}."""
    builder.build_frontier(paths, actor)
    engine.run_sweeps(paths, actor)
    item = next(
        i for i in engine.load_items(paths)
        if i["target_id"] == target_id and engine.is_claimable(paths, i)
    )
    claimed = engine.claim(paths, queue_name="proof_queue", agent="w", wi_id=item["work_item_id"])
    worker.run(claimed, paths.project_dir)
    engine.complete(paths, claimed["work_item_id"])
    vr = validate_proof.validate_result(paths, claimed["output_files"][0], claimed["work_item_id"], actor)
    out: dict[str, Any] = {"work_item_id": claimed["work_item_id"], "proof_result_id": vr["proof_result_id"]}
    if commit:
        out["commit"] = committer.apply_proof_verdict(paths, vr["proof_result_id"], actor)
    return out


def _one_cycle(paths: Paths, worker: FakeProofWorker) -> None:
    item = engine.claim(paths, queue_name="proof_queue", agent="fake-worker")
    worker.run(item, paths.project_dir)
    engine.complete(paths, item["work_item_id"])
    validate_proof.validate_result(paths, item["output_files"][0], item["work_item_id"])


def _run_batch(paths: Paths, worker: FakeProofWorker, count: int, parallel: int) -> None:
    if parallel <= 1:
        for _ in range(count):
            _one_cycle(paths, worker)
        return
    with ThreadPoolExecutor(max_workers=parallel) as pool:
        futures = [pool.submit(_one_cycle, paths, worker) for _ in range(count)]
        for f in futures:
            f.result()
