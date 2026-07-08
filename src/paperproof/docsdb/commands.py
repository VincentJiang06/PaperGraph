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
from ..schemas.docs import DocsPack, SourceProfile, Tier
from ..store import jsonl
from . import cache, ingest, matcher, pack, planner, registry, wave as wave_mod
from ..validate.rules import v_src

DOCS_REQUESTS = "docs/docs_requests.jsonl"
_TIERS = set(Tier.__args__)  # type: ignore[attr-defined]
_WORKAROUND_KINDS = {"mirror", "archive_org", "secondary_quote", "pdf_local_extract", "api"}


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
        # reactive / Orchestrator-initiated requests default single (docs/15);
        # a wave is opened explicitly with `docs wave`.
        "fan": False,
    }
    if hit:
        jsonl.append(paths.resolve(DOCS_REQUESTS), {**base, "status": "fulfilled", "fulfilled_by": "cache"})
        return {"request_id": dr_id, "status": "fulfilled", "fulfilled_by": "cache", "work_item_id": None}
    jsonl.append(paths.resolve(DOCS_REQUESTS), {**base, "status": "open", "fulfilled_by": None})
    output = f"agent_outputs/docs_results/{dr_id}.docs_result.json"
    item = engine.enqueue(paths, queue_name="docs_queue", target_type="request", target_id=dr_id,
                          output_files=[output], actor=actor)
    # Dispatch attaches the compiled plan as an immutable bundle artifact (docs/14).
    planner.plan_for_request(paths, dr_id)
    return {"request_id": dr_id, "status": "open", "fulfilled_by": None, "work_item_id": item["work_item_id"]}


def plan(paths: Paths, request_id: str) -> dict[str, Any]:
    """`docs plan --request <DR>`: compile (or reprint) the immutable SearchPlan
    for a DocsRequest and emit it. A second call is byte-identical (docs/14)."""
    req = jsonl.latest_by_id(paths.resolve(DOCS_REQUESTS), "request_id").get(request_id)
    if req is None:
        raise DomainError([f"docs request not found: {request_id}"])
    plan_obj = planner.plan_for_request(paths, request_id)
    return {"plan": plan_obj, "plan_path": planner.plan_relpath(request_id)}


def wave(paths: Paths, request_id: str, fan: bool = False, actor: str | None = None) -> dict[str, Any]:
    """`docs wave --request <DR> [--fan]` (docs/15): turn a DocsRequest into a
    wave — one member per angle, each a docs_queue item + angle plan + distinct
    output — and append the search_wave.v1 record."""
    rec = wave_mod.start_wave(paths, request_id, fan=fan, actor=actor)
    return {
        "wave_id": rec["wave_id"], "request_id": rec["request_id"], "round": rec["round"],
        "status": rec["status"],
        "members": [{"angle": m["angle"], "work_item_id": m["work_item_id"], "plan_id": m["plan_id"]}
                    for m in rec["members"]],
    }


def ingest_result(paths: Paths, file_path: str, work_item: str) -> dict[str, Any]:
    return ingest.ingest_result(paths, file_path, work_item)


def coverage(paths: Paths, node: str | None = None) -> dict[str, Any]:
    """`docs coverage [--node <id>]` (docs/17): the DERIVED coverage ledger — a
    deterministic fold, never a canonical write. Whole-project by default; one
    node's ledger line with ``--node``."""
    from . import coverage as coverage_mod

    if node:
        return coverage_mod.ledger_for(paths, node)
    return coverage_mod.build_ledger(paths)


def source_list(paths: Paths) -> dict[str, Any]:
    """`docs source list`: the live registry (latest SourceProfile per domain)."""
    profiles = registry.load_latest(paths)
    return {"sources": profiles, "count": len(profiles)}


def source_set(
    paths: Paths,
    domain: str,
    tier: str | None = None,
    publisher: str | None = None,
    workaround: str | None = None,
    note: str | None = None,
    blocked: bool | None = None,
) -> dict[str, Any]:
    """`docs source set`: append a curated SourceProfile version for a domain
    (docs/16). set = append — a new tier/workaround/publisher/note. A tier change
    must carry a note or V-SRC-03 rejects it (no silent tier-lowering)."""
    domain = registry.domain_from_url(domain) or domain.strip().lower()
    if not domain:
        raise UsageError(["--domain is required"])
    if tier is not None and tier not in _TIERS:
        raise UsageError([f"--tier must be one of {sorted(_TIERS)}"])
    if workaround is not None and workaround not in _WORKAROUND_KINDS:
        raise UsageError([f"--workaround must be one of {sorted(_WORKAROUND_KINDS)}"])

    prev = registry._latest_by_domain(paths).get(domain)
    existing_ids = [r["source_id"] for r in registry.load_all(paths)]
    source_id = prev["source_id"] if prev else next_id("SRC", existing_ids)
    fetch = dict((prev or {}).get("fetch", {}) or {})
    workarounds = list(fetch.get("workarounds", []) or [])
    if workaround is not None:
        workarounds.append({"kind": workaround, "note": note or ""})
    new_tier = tier or (prev or {}).get("tier") or "T6_other"
    tier_changed = bool(prev) and prev.get("tier") != new_tier
    tier_note = note if tier_changed else (prev or {}).get("tier_note")

    record = SourceProfile(
        source_id=source_id, project_id=paths.project_id, domain=domain,
        publisher=publisher if publisher is not None else (prev or {}).get("publisher", "") or "",
        tier=new_tier,
        fetch={
            "blocked_direct": blocked if blocked is not None else bool(fetch.get("blocked_direct")),
            "workarounds": workarounds,
        },
        seen_count=int((prev or {}).get("seen_count", 0)),
        last_ok_fetch_method=(prev or {}).get("last_ok_fetch_method"),
        tier_note=tier_note, created_at=clock_now(),
    )
    # V-SRC-03: a tier change with no note is a silent change — refuse before write.
    candidate_history = (registry.load_all(paths) + [record.model_dump(mode="json")])
    failures = v_src.check_registry_history(candidate_history)
    if failures:
        from ..validate.envelope import to_envelope

        env = to_envelope(failures)
        raise DomainError(env["failed_rules"], data={"failed_rules": env["failed_rules"], "detail": env["detail"]})
    jsonl.append(paths.resolve(registry.SOURCES), record)
    return {"source_id": source_id, "domain": domain, "tier": new_tier}


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
