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
from paperproof.compiler import draft_map as draft_map_mod
from paperproof.compiler import prose as prose_mod
from paperproof.docsdb import ingest as docs_ingest
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


class FakeDocsWorker:
    """Scripted DocsResult stand-in (docs/11 §5).

    Reads a docs work item (whose target_id is the DocsRequest id) and writes a
    schema-valid docs_result.v1 at the declared output path. The script is keyed
    by request_id, with a "*" default entry; a scripted ``not_found`` result is a
    legitimate terminal output.
    """

    def __init__(self, script: dict[str, Any], mode: str = "script") -> None:
        self.script = script
        self.mode = mode

    def run(self, work_item: dict[str, Any], project_root: Path) -> None:
        if self.mode == "crash":
            return
        request_id = work_item["target_id"]
        spec = self.script.get(request_id) or self.script.get("*") or {}
        documents = spec.get("documents", [])
        evidence_units = spec.get("evidence_units", [])
        not_found = spec.get("not_found", False)
        base = {
            "request_id": request_id,
            "project_id": work_item["project_id"],
            "documents": documents,
            "evidence_units": evidence_units,
            "not_found": not_found,
        }
        # The real DocsWorker now EMITS docs_result.v2 with a query_log accounting
        # for every planned qid (docs/14). When the immutable plan is attached at
        # dispatch, the fake mirrors that; with no plan it falls back to v1 (still
        # ingestible — the schema registry keeps v1 readable). A wave member's item
        # names its ANGLE plan via task_id (SP-<DR>-<angle>) — prefer it (docs/15).
        task_plan = work_item.get("task_id")
        if task_plan and str(task_plan).startswith("SP-"):
            plan_file = project_root / "docs" / "plans" / f"{task_plan}.json"
        else:
            plan_file = project_root / "docs" / "plans" / f"SP-{request_id}.json"
        if plan_file.exists() and spec.get("force_v1") is not True:
            plan = json.loads(plan_file.read_text(encoding="utf-8"))
            result = {"schema_version": "docs_result.v2", **base,
                      "query_log": self._query_log(spec, plan, documents, not_found)}
        else:
            result = {"schema_version": "docs_result.v1", **base,
                      "search_log": spec.get("search_log", ["scripted search"])}
        out_path = project_root / work_item["output_files"][0]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def _query_log(spec: dict[str, Any], plan: dict[str, Any], documents: list,
                   not_found: bool) -> list[dict[str, Any]]:
        if "query_log" in spec:  # a scripted (e.g. hostile) query_log wins verbatim
            return spec["query_log"]
        n = len(documents)
        log: list[dict[str, Any]] = []
        for i, q in enumerate(plan.get("queries", [])):
            productive = (i == 0 and n > 0 and not not_found)
            log.append({
                "qid": q["qid"],
                "executed": True,
                "outcome": "productive" if productive else "empty",
                "urls_seen": n if productive else 0,
                "docs_taken": n if productive else 0,
                "note": "",
            })
        return log


class FakeCompileWorker:
    """Scripted CompileWorker stand-in (docs/11 §5).

    Reads a PROSE compile_queue item, loads its DraftMap section, and writes a
    deterministic, annotation-grammar-conformant Markdown file: one claim sentence
    per DraftMap claim, using the claim's first allowed_language phrase, carrying
    "(claim: NODE-x)" plus a "(cite: EU-y)" for every bound EvidenceUnit.

    Modes:
      'script' : clean, V-PROSE-conformant prose.
      'taint'  : additionally emit one sentence containing the section's first
                 forbidden_language string (audit strength should flag it).
    """

    def __init__(self, mode: str = "script", taint_section: str | None = None) -> None:
        self.mode = mode
        self.taint_section = taint_section

    def _section(self, work_item: dict[str, Any], project_root: Path) -> dict[str, Any] | None:
        task_id = work_item.get("task_id") or ""
        section_id = task_id[len("PROSE-"):] if task_id.startswith("PROSE-") else work_item["target_id"]
        paths = _paths_from_root(project_root, work_item["project_id"])
        dm = draft_map_mod.latest_draft_map(paths)
        if dm is None:
            return None
        return next((s for s in dm["sections"] if s["section_id"] == section_id), None)

    def run(self, work_item: dict[str, Any], project_root: Path) -> None:
        if self.mode == "crash":
            return
        section = self._section(work_item, project_root)
        section_id = (work_item.get("task_id") or "")[len("PROSE-"):]
        sentences: list[str] = []
        first_node = None
        forbidden_phrase = None
        for claim in (section or {}).get("claims", []):
            if first_node is None:
                first_node = claim["node_id"]
            allowed = claim.get("allowed_language") or []
            lead = (allowed[0].rstrip(". ") if allowed else "This section presents the claim")
            cites = "".join(f"(cite: {eid})" for eid in claim.get("evidence_ids", []) or [])
            sentences.append(f"{lead} (claim: {claim['node_id']}){cites}.")
            if forbidden_phrase is None and (claim.get("forbidden_language") or []):
                forbidden_phrase = claim["forbidden_language"][0]
        text = "\n\n".join(sentences) if sentences else "Section overview."
        if self.mode == "taint" and forbidden_phrase and (self.taint_section is None or self.taint_section == section_id):
            text += f"\n\n{forbidden_phrase} (claim: {first_node})."
        out = project_root / work_item["output_files"][0]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")


class FakeCriticWorker:
    """Scripted coverage-critic stand-in (docs/15, docs/11 §5).

    The critic is a FRESH, adversarial, READ-ONLY worker: same maker/checker
    separation as FakeDocsWorker/FakeProofWorker. It reads a critic_queue item
    (target_id = wave_id), and writes a schema-valid coverage_report.v1 at the
    declared output path. It NEVER writes documents or evidence_units — code
    computes the wave verdict from its closed form.

    The script maps ``wave_id`` (or "*") -> either a single form spec or, for
    multi-round waves, a LIST consumed one form per round. Each spec provides
    ``form`` (angle_covered/primary_source_present/disconfirming_captured),
    optional ``expected_sources`` (<=3) and ``notes``. A ``hostile`` key emits
    the smuggled documents/evidence_units V-WAVE-03 must reject.
    """

    def __init__(self, script: dict[str, Any], mode: str = "script") -> None:
        self.script = script
        self.mode = mode
        self._counts: dict[str, int] = {}

    def run(self, work_item: dict[str, Any], project_root: Path) -> None:
        if self.mode == "crash":
            return
        wave_id = work_item["target_id"]
        entry = self.script.get(wave_id) or self.script.get("*") or {}
        if isinstance(entry, list):
            idx = min(self._counts.get(wave_id, 0), len(entry) - 1)
            self._counts[wave_id] = self._counts.get(wave_id, 0) + 1
            spec = dict(entry[idx])
        else:
            spec = dict(entry)
        report: dict[str, Any] = {
            "schema_version": "coverage_report.v1",
            "wave_id": wave_id,
            "form": spec["form"],
            "expected_sources": spec.get("expected_sources", []),
            "notes": spec.get("notes", "scripted critic"),
        }
        if spec.get("hostile") == "smuggle_evidence":
            report["documents"] = [{"title": "sneaked"}]
            report["evidence_units"] = [{"quote_or_paraphrase": "sneaked evidence"}]
        out = project_root / work_item["output_files"][0]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")


def drive_wave(paths, request_id, fan, docs_worker: FakeDocsWorker, critic_worker: FakeCriticWorker,
               max_rounds: int = 8, actor: str = "test") -> dict[str, Any]:
    """Drive a whole wave to closure (docs/15): start it, then for each round
    drain the member docs items (validate-only; no per-member ingest), merge,
    dispatch + run the critic, and let CODE compute the verdict — ingesting the
    merged result once at closure or opening a bounded follow-up round.

    Returns {wave_id, rounds, verdict, status, dres_id?}.
    """
    from paperproof.docsdb import wave as wave_mod

    started = wave_mod.start_wave(paths, request_id, fan=fan, actor=actor)
    wave_id = started["wave_id"]
    last: dict[str, Any] = {"wave_id": wave_id}
    for _ in range(max_rounds):
        wave = wave_mod.wave_by_id(paths, wave_id)
        # drain this wave's member docs items (validate, commit; NOT ingest)
        member_ids = {m["work_item_id"] for m in wave["members"]}
        engine.run_sweeps(paths, actor)
        for item in engine.load_items(paths):
            if item["work_item_id"] in member_ids and engine.is_claimable(paths, item):
                claimed = engine.claim(paths, queue_name="docs_queue", agent="docs-w", wi_id=item["work_item_id"])
                docs_worker.run(claimed, paths.project_dir)
                wave_mod.complete_member(paths, wave_id, claimed["work_item_id"], actor)
        # merge + critic + verdict
        wave_mod.merge(paths, wave_id)
        critic_item = wave_mod.open_critic(paths, wave_id, actor)
        critic_claimed = engine.claim(paths, queue_name="critic_queue", agent="critic-w", wi_id=critic_item["work_item_id"])
        critic_worker.run(critic_claimed, paths.project_dir)
        last = wave_mod.resolve_critic(paths, wave_id, critic_claimed["work_item_id"], actor)
        if last.get("status") == "closed":
            break
    return {"wave_id": wave_id, **last}


def _paths_from_root(project_root: Path, project_id: str) -> Paths:
    # project_root is <root>/projects/<project_id>; recover the Paths object.
    return Paths(root=project_root.parent.parent, project_id=project_id)


def drain_compile(paths: Paths, worker: FakeCompileWorker, max_rounds: int = 50, actor: str = "test") -> list[str]:
    """Claim/run/complete/ingest every PROSE compile_queue item to quiescence."""
    processed: list[str] = []
    for _ in range(max_rounds):
        engine.run_sweeps(paths, actor)
        claimable = [
            i for i in engine.load_items(paths)
            if i["queue_name"] == "compile_queue" and i["target_type"] == "section" and engine.is_claimable(paths, i)
        ]
        if not claimable:
            break
        item = engine.claim(paths, queue_name="compile_queue", agent="compile-w", wi_id=claimable[0]["work_item_id"])
        worker.run(item, paths.project_dir)
        engine.complete(paths, item["work_item_id"])
        prose_mod.ingest_prose(paths, item["output_files"][0], item["work_item_id"], actor)
        processed.append(item["work_item_id"])
    return processed


def drain_docs(paths: Paths, worker: FakeDocsWorker, max_rounds: int = 50, actor: str = "test") -> list[str]:
    """Claim/run/complete/ingest every claimable docs_queue item to quiescence."""
    processed: list[str] = []
    for _ in range(max_rounds):
        engine.run_sweeps(paths, actor)
        claimable = [
            i for i in engine.load_items(paths)
            if i["queue_name"] == "docs_queue" and engine.is_claimable(paths, i)
        ]
        if not claimable:
            break
        item = engine.claim(paths, queue_name="docs_queue", agent="docs-w")
        worker.run(item, paths.project_dir)
        engine.complete(paths, item["work_item_id"])
        docs_ingest.ingest_result(paths, item["output_files"][0], item["work_item_id"], actor)
        processed.append(item["work_item_id"])
    return processed


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
