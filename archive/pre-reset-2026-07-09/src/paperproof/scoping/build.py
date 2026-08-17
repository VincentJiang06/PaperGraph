"""spec build / accept / show (docs/01, docs/10 §4).

`spec build` parses a topic file deterministically and emits both the PaperSpec
and the ProjectContract drafts. The --patch application order is fixed (docs/01):
  (1) parse topic file -> PaperSpec
  (2) apply paper_spec patch
  (3) derive the contract FROM THE PATCHED spec
  (4) apply project_contract patch
  (5) write both
Nobody hand-edits specs/ files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ..clock import now as clock_now
from ..errors import DomainError, UsageError
from ..paths import Paths
from ..schemas.spec import PaperSpec, ProjectContract
from ..store import jsonl
from ..textutil import normalize
from ..validate import registry
from ..validate.envelope import Failure, to_envelope
from .parser import parse_list, parse_scope, parse_topic

# v1 knows exactly one bfs_plan template (docs/01).
BFS_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "single_event_mechanism": [
        {"bfs_id": "BFS-MAIN", "purpose": "core mechanism chain", "depends_on": []},
        {"bfs_id": "BFS-ALT", "purpose": "alternative explanations", "depends_on": ["BFS-MAIN"]},
    ]
}


def merge_patch(target: Any, patch: Any) -> Any:
    """RFC 7386 JSON Merge Patch."""
    if not isinstance(patch, dict):
        return patch
    base = dict(target) if isinstance(target, dict) else {}
    for key, value in patch.items():
        if value is None:
            base.pop(key, None)
        elif isinstance(value, dict):
            base[key] = merge_patch(base.get(key), value)
        else:
            base[key] = value
    return base


def _build_spec_dict(project_id: str, parsed: Any) -> tuple[dict[str, Any], list[str], list[str]]:
    """Return (spec_dict, scope_items_verbatim, warnings)."""
    warnings: list[str] = list(parsed.warnings)

    scope_items, w = parse_list(parsed.sections.get("scope", ""))
    warnings += w
    structured_scope = parse_scope(scope_items)

    excl, w = parse_list(parsed.sections.get("exclusions", ""))
    warnings += w
    seeds, w = parse_list(parsed.sections.get("seed_claims", ""))
    warnings += w
    known, w = parse_list(parsed.sections.get("known_sources", ""))
    warnings += w
    success, w = parse_list(parsed.sections.get("success_criteria", ""))
    warnings += w

    paper_type = normalize(parsed.sections.get("paper_type", ""))

    spec_dict: dict[str, Any] = {
        "schema_version": "paper_spec.v1",
        "project_id": project_id,
        "paper_type": paper_type,
        "core_question": parsed.sections.get("core_question", "").strip(),
        "intended_thesis": parsed.sections.get("intended_thesis", "").strip(),
        "scope": structured_scope,
        "hard_exclusions": excl,
        "seed_claims": seeds,
        "known_sources": known,
        "success_criteria": success,
        "bfs_plan": BFS_TEMPLATES.get(paper_type, []),
        "source_files": [],
    }
    return spec_dict, scope_items, warnings


def _derive_contract_dict(spec_dict: dict[str, Any], scope_items: list[str]) -> dict[str, Any]:
    return {
        "schema_version": "project_contract.v1",
        "project_id": spec_dict["project_id"],
        "contract_version": 1,
        "fixed_question": spec_dict.get("core_question", ""),
        "outcome_direction": spec_dict.get("intended_thesis", ""),
        "scope": spec_dict.get("scope", {}),
        "in_scope": list(scope_items),
        "out_of_scope": [],
        "forbidden_claims": list(spec_dict.get("hard_exclusions", []) or []),
        "success_criteria": list(spec_dict.get("success_criteria", []) or []),
        "accepted_by_user": False,
        "accepted_at": None,
    }


def _load_patch(patch_path: str | Path) -> dict[str, Any]:
    path = Path(patch_path)
    if not path.exists():
        raise UsageError([f"patch file not found: {patch_path}"])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise UsageError([f"patch file is not valid JSON: {exc.msg}"]) from exc
    if not isinstance(data, dict):
        raise UsageError(["patch file must be a JSON object"])
    extra = set(data.keys()) - {"paper_spec", "project_contract"}
    if extra:
        raise UsageError([f"patch has unknown top-level keys: {sorted(extra)}"])
    return data


def build(paths: Paths, topic_file: str | Path, patch_file: str | Path | None = None) -> dict[str, Any]:
    """Run spec build. Returns data payload; raises DomainError on V-SPEC failure."""
    topic_path = Path(topic_file)
    if not topic_path.exists():
        raise UsageError([f"topic file not found: {topic_file}"])

    # Refuse to overwrite an accepted contract (docs/01).
    if paths.project_contract.exists():
        existing = jsonl.read_json(paths.project_contract)
        if existing.get("accepted_by_user"):
            raise DomainError(
                ["V-GATE-01: contract already accepted; refusing to overwrite"],
                data={"contract_version": existing.get("contract_version")},
            )

    text = topic_path.read_text(encoding="utf-8")
    parsed = parse_topic(text)

    patch = _load_patch(patch_file) if patch_file else {}

    spec_dict, scope_items, warnings = _build_spec_dict(paths.project_id, parsed)
    spec_dict = merge_patch(spec_dict, patch.get("paper_spec", {}))
    contract_dict = _derive_contract_dict(spec_dict, scope_items)
    contract_dict = merge_patch(contract_dict, patch.get("project_contract", {}))

    failures: list[Failure] = registry.v_spec.check(parsed, spec_dict, contract_dict)
    if failures:
        env = to_envelope(failures)
        raise DomainError(
            env["failed_rules"],
            data={"failed_rules": env["failed_rules"], "detail": env["detail"]},
            warnings=warnings,
        )

    try:
        spec = PaperSpec.model_validate(spec_dict)
        contract = ProjectContract.model_validate(contract_dict)
    except ValidationError as exc:
        raise DomainError(
            ["V-SPEC-01: derived artifact failed schema validation"],
            data={"detail": {"schema": str(exc)}},
            warnings=warnings,
        ) from exc

    jsonl.write_json(paths.paper_spec, spec)
    jsonl.write_json(paths.project_contract, contract)

    return {
        "paper_spec": spec.model_dump(mode="json"),
        "project_contract": contract.model_dump(mode="json"),
        "warnings": warnings,
    }


def accept(paths: Paths) -> dict[str, Any]:
    """Set accepted_by_user=true (+ accepted_at). Human confirmation is the act
    of running this command (docs/01)."""
    if not paths.project_contract.exists():
        raise DomainError(["no contract to accept; run spec build first"])
    data = jsonl.read_json(paths.project_contract)
    data["accepted_by_user"] = True
    data["accepted_at"] = clock_now()
    contract = ProjectContract.model_validate(data)
    jsonl.write_json(paths.project_contract, contract)
    return {"project_contract": contract.model_dump(mode="json")}


def show(paths: Paths) -> dict[str, Any]:
    if not paths.paper_spec.exists() or not paths.project_contract.exists():
        raise DomainError(["spec/contract not found; run spec build first"])
    return {
        "paper_spec": jsonl.read_json(paths.paper_spec),
        "project_contract": jsonl.read_json(paths.project_contract),
    }
