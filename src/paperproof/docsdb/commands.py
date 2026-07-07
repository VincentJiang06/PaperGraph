"""docs CLI command bodies (docs/10 §4): ingest, search, build-pack, request,
ingest-result — plus `validate docs-result` (V-PATH + V-DR, no state change)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..clock import actor as clock_actor
from ..clock import now as clock_now
from ..errors import DomainError, UsageError
from ..graph import model as graph_model
from ..ids import next_id
from ..paths import Paths
from ..queue import engine
from ..schemas.docs import DocsPack
from ..store import jsonl
from . import cache, ingest, matcher, pack

DOCS_REQUESTS = "docs/docs_requests.jsonl"


def ingest_file(paths: Paths, file_path: str, source_type: str | None, title: str | None, citation_key: str | None) -> dict[str, Any]:
    return ingest.ingest_file(paths, file_path, source_type, title, citation_key)


def search(paths: Paths, query: str, scope: str | None = None) -> dict[str, Any]:
    scope_obj: dict[str, Any] = {}
    if scope:
        try:
            scope_obj = json.loads(scope)
        except json.JSONDecodeError as exc:
            raise UsageError([f"--scope is not valid JSON: {exc.msg}"]) from exc
    results = pack.search(paths, query, scope_obj)
    return {"results": results, "count": len(results)}


def build_pack(paths: Paths, task_id: str) -> dict[str, Any]:
    task_path = paths.resolve(f"proof/tasks/{task_id}.json")
    if not task_path.exists():
        raise DomainError([f"proof task not found: {task_id}"])
    task = jsonl.read_json(task_path)
    target = task["target"]
    target_id = target.get("edge_id") or target.get("node_id")
    rec = graph_model.load(paths).record(target_id)
    if rec is None:
        raise DomainError([f"target not found in graph: {target_id}"])
    eus, docs_meta = pack.assemble(paths, rec)
    docs_pack_rel = task["docs_pack"]
    pack_id = Path(docs_pack_rel).stem
    docspack = DocsPack(
        pack_id=pack_id, task_id=task_id, project_id=paths.project_id,
        evidence_units=eus, documents_meta=docs_meta,
    )
    jsonl.write_json(paths.resolve(docs_pack_rel), docspack)
    return {"pack_path": docs_pack_rel, "evidence_count": len(eus)}


def request(paths: Paths, target_id: str, need: str, hints: list[str] | None, actor: str | None = None) -> dict[str, Any]:
    """`docs request`: an Orchestrator-initiated DocsRequest (cache-checked like
    any request). Cache hit => fulfilled/"cache", no work item; miss => open + a
    docs_queue item."""
    actor = actor or clock_actor()
    hints = list(hints or [])
    rec = graph_model.load(paths).record(target_id)
    if rec is None:
        raise DomainError([f"target not found in graph: {target_id}"])
    fp = matcher.fingerprint(need, hints)
    dr_id = next_id("DR", [r["request_id"] for r in jsonl.read_all(paths.resolve(DOCS_REQUESTS))])
    hit = cache.is_cache_hit(paths, fp, rec)
    base = {
        "schema_version": "docs_request.v1", "request_id": dr_id, "project_id": paths.project_id,
        "requested_by": "orchestrator", "target_id": target_id, "need": need,
        "search_hints": hints, "fingerprint": fp, "created_at": clock_now(),
    }
    if hit:
        jsonl.append(paths.resolve(DOCS_REQUESTS), {**base, "status": "fulfilled", "fulfilled_by": "cache"})
        return {"request_id": dr_id, "status": "fulfilled", "fulfilled_by": "cache", "work_item_id": None}
    jsonl.append(paths.resolve(DOCS_REQUESTS), {**base, "status": "open", "fulfilled_by": None})
    output = f"agent_outputs/docs_results/{dr_id}.docs_result.json"
    item = engine.enqueue(paths, queue_name="docs_queue", target_type="request", target_id=dr_id,
                          output_files=[output], actor=actor)
    return {"request_id": dr_id, "status": "open", "fulfilled_by": None, "work_item_id": item["work_item_id"]}


def ingest_result(paths: Paths, file_path: str, work_item: str) -> dict[str, Any]:
    return ingest.ingest_result(paths, file_path, work_item)


def validate_docs_result(paths: Paths, file_path: str, work_item: str) -> dict[str, Any]:
    """`validate docs-result`: V-PATH + V-DR only (no ingest, no state change)."""
    wi = engine.get_item(paths, work_item)
    relpath = ingest._to_relpath(paths, file_path)
    p = paths.project_dir / relpath
    raw = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    failures = ingest._validate(paths, wi, relpath, raw)
    if failures:
        from ..validate.envelope import to_envelope

        env = to_envelope(failures)
        raise DomainError(env["failed_rules"], data={"ok": False, "failed_rules": env["failed_rules"], "detail": env["detail"]})
    return {"ok": True, "failed_rules": []}
