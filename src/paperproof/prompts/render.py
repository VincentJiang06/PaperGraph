"""Prompt rendering for dispatch (F11/D11): `docs render-prompt` + `proof
render-prompt`.

Emits the fully-filled canonical template for a work item as ENVELOPE DATA (the
Orchestrator pastes it into a bounded worker). The registry excerpt that fills
``{registry}`` is CHECKED against V-SRC-05 here — the render is the dispatch
boundary, so an incomplete excerpt is refused, never silently shipped. The S5
advisory leads (top-3 similar fulfilled requests) are PROMPT-ONLY intel
[V-SEM-04]: they ride along in the text and the envelope, and nothing else ever
consumes them.
"""

from __future__ import annotations

import json
from typing import Any

from . import load as load_template
from ..errors import DomainError
from ..paths import Paths

DOCS_REQUESTS = "docs/docs_requests.jsonl"


def _fill(template: str, mapping: dict[str, str]) -> str:
    out = template
    for key, val in mapping.items():
        out = out.replace("{" + key + "}", val)
    return out


def _request_for(paths: Paths, request_id: str) -> dict[str, Any]:
    from ..store import jsonl

    req = jsonl.latest_by_id(paths.resolve(DOCS_REQUESTS), "request_id").get(request_id)
    if req is None:
        raise DomainError([f"docs request not found: {request_id}"])
    return req


def _target_scope(paths: Paths, target_id: str) -> dict[str, Any]:
    from ..graph import model as graph_model

    rec = graph_model.load(paths).record(target_id)
    return (rec.get("scope") or {}) if (rec and "node_id" in rec) else {}


def _target_claim(paths: Paths, target_id: str) -> str:
    from ..graph import model as graph_model

    rec = graph_model.load(paths).record(target_id)
    if rec is None:
        return ""
    return rec.get("claim") or rec.get("edge_claim") or ""


def _checked_registry_excerpt(paths: Paths, need: str, hints: list[str], scope: dict[str, Any]) -> str:
    """The {registry} block, V-SRC-05-checked (D11): the excerpt must contain
    every T1 profile + every facet-matched profile, or the render refuses."""
    from ..docsdb import registry
    from ..validate.rules import v_src

    profiles = registry.matched_profiles(paths, need, hints, scope)
    facet_text = registry._facet_text(need, hints, scope)
    failures = v_src.check_registry_excerpt(
        registry.load_latest(paths), facet_text,
        {p.get("source_id") for p in profiles},
    )
    if failures:
        from ..validate.envelope import to_envelope

        env = to_envelope(failures)
        raise DomainError(env["failed_rules"], data={"failed_rules": env["failed_rules"], "detail": env["detail"]})
    return registry.render_excerpt(profiles)


def _advisory_block(paths: Paths, need: str, hints: list[str]) -> tuple[str, list[dict[str, Any]]]:
    """S5 advisory leads (docs/18, V-SEM-04): prompt-only similar-request intel;
    empty (and absent from the prompt) when the model is not present."""
    from ..db import semantic

    leads = semantic.advisory_leads(paths, need, hints)
    if not leads:
        return "", []
    lines = [
        f"- {l['request_id']} (similarity {l['similarity']}): {l['need']}"
        for l in leads
    ]
    block = (
        "\nADVISORY LEADS (similar fulfilled requests — intel only, never a\n"
        "sufficiency verdict; their evidence is already archived):\n"
        + "\n".join(lines) + "\n"
    )
    return block, leads


def _docs_member_prompt(paths: Paths, wi: dict[str, Any]) -> dict[str, Any]:
    """A docs single item or wave member: the docs_worker template with the
    request fields, the member's OWN embedded plan JSON, the checked registry
    excerpt, and the declared output path."""
    from ..docsdb import planner

    request_id = wi["target_id"]
    req = _request_for(paths, request_id)
    need = req.get("need", "") or ""
    hints = list(req.get("search_hints", []) or [])
    scope = _target_scope(paths, req.get("target_id"))

    task_id = str(wi.get("task_id") or "")
    plan = planner.load_plan_by_id(paths, task_id) if task_id.startswith("SP-") else None
    if plan is None:
        plan = planner.load_plan(paths, request_id)
    if plan is None:
        raise DomainError([f"no compiled plan for work item {wi['work_item_id']} (request {request_id})"])

    output_file = (wi.get("output_files") or [None])[0]
    if not output_file:
        raise DomainError([f"work item {wi['work_item_id']} declares no output file"])

    excerpt = _checked_registry_excerpt(paths, need, hints, scope)
    advisory, leads = _advisory_block(paths, need, hints)

    text = _fill(load_template("docs_worker"), {
        "request_id": request_id,
        "project_id": paths.project_id,
        "need": need,
        "search_hints": json.dumps(hints, ensure_ascii=False),
        "plan_id": plan.get("plan_id", ""),
        "registry": excerpt,
        "output_file": output_file,
    })
    text += (
        "\nSEARCHPLAN (immutable, embedded):\n"
        + json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
        + advisory
    )
    return {"template": "docs_worker", "work_item_id": wi["work_item_id"],
            "request_id": request_id, "plan_id": plan.get("plan_id"),
            "output_file": output_file, "advisory_leads": leads, "prompt": text}


def _critic_prompt(paths: Paths, wi: dict[str, Any]) -> dict[str, Any]:
    """A critic item: the critic_worker template; {inputs} = the wave's claim,
    the member plan paths, the merged docs_result path, and the per-member
    query_log (output) paths."""
    from ..docsdb import planner, wave as wave_mod
    from ..queue import engine

    wave_id = wi["target_id"]
    wave = wave_mod.wave_by_id(paths, wave_id)
    if wave is None:
        raise DomainError([f"wave not found: {wave_id}"])
    req = _request_for(paths, wave["request_id"])
    claim = _target_claim(paths, req.get("target_id"))

    by_id = engine.items_by_id(paths)
    plan_paths = [planner.plan_id_relpath(m["plan_id"]) for m in wave.get("members", [])]
    member_outputs = []
    for m in wave.get("members", []):
        item = by_id.get(m["work_item_id"])
        files = (item or {}).get("output_files") or []
        if files:
            member_outputs.append(files[0])

    output_file = (wi.get("output_files") or [None])[0]
    if not output_file:
        raise DomainError([f"critic item {wi['work_item_id']} declares no output file"])

    inputs = "\n".join(
        [f"  claim under search: {claim}"]
        + [f"  SearchPlan: {p}" for p in plan_paths]
        + [f"  merged docs_result: {wave_mod.merged_relpath(wave['request_id'])}"]
        + [f"  member query_log (in its docs_result): {p}" for p in member_outputs]
    )
    text = _fill(load_template("critic_worker"), {
        "output_file": output_file,
        "inputs": inputs,
    })
    return {"template": "critic_worker", "work_item_id": wi["work_item_id"],
            "wave_id": wave_id, "output_file": output_file, "prompt": text}


def render_docs_prompt(paths: Paths, work_item_id: str) -> dict[str, Any]:
    """`docs render-prompt --work-item <WI>` (F11/D11): docs single items, wave
    members (docs_queue) and critic items (critic_queue)."""
    from ..queue import engine

    wi = engine.get_item(paths, work_item_id)
    queue = wi.get("queue_name")
    if queue == "critic_queue":
        return _critic_prompt(paths, wi)
    if queue == "docs_queue":
        return _docs_member_prompt(paths, wi)
    raise DomainError([f"work item {work_item_id} is not a docs/critic item ({queue}); "
                       f"use `proof render-prompt` for proof items"])


def render_proof_prompt(paths: Paths, work_item_id: str) -> dict[str, Any]:
    """`proof render-prompt --work-item <WI>` (F11/D11): the proof_worker
    template filled from the item's attached bundle."""
    from ..queue import engine

    wi = engine.get_item(paths, work_item_id)
    if wi.get("queue_name") != "proof_queue":
        raise DomainError([f"work item {work_item_id} is not a proof item ({wi.get('queue_name')})"])
    bundle = wi.get("bundle")
    if not bundle:
        raise DomainError([f"work item {work_item_id} has no bundle; run `proof build-tasks` first"])
    output_file = (wi.get("output_files") or [None])[0]
    if not output_file:
        raise DomainError([f"work item {work_item_id} declares no output file"])
    task_type = "EDGE_CHECK" if wi.get("target_type") == "edge" else "NODE_CHECK"
    claim = _target_claim(paths, wi["target_id"])
    summary = f"{wi['target_id']}: {claim}" if claim else wi["target_id"]
    text = _fill(load_template("proof_worker"), {
        "task_file": bundle.get("task_file", ""),
        "context_pack": bundle.get("context_pack", ""),
        "docs_pack": bundle.get("docs_pack", ""),
        "task_type": task_type,
        "target_summary": summary,
        "output_file": output_file,
    })
    return {"template": "proof_worker", "work_item_id": work_item_id,
            "task_id": wi.get("task_id"), "output_file": output_file, "prompt": text}
