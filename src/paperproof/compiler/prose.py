"""Prose annotation grammar + V-PROSE checks + ingest-prose (docs/06, docs/08 B10).

The annotation grammar (mechanical, docs/06):
  - every claim-bearing sentence carries "(claim: NODE-xxx)" inside the sentence;
  - every "(cite: EU-xxx)" sits in the SAME sentence as a claim annotation and
    cites an EvidenceUnit bound to one of that sentence's annotated nodes;
  - transitions carry no annotations.

`ingest-prose` runs V-PROSE-01..04 as the work item's validate-pass, copies the
accepted agent_outputs/prose/<sec>.md to compiler/prose/<sec>.md, and commits the
item — one command, two queue events (validate_pass + commit; docs/05 ingest
exception). On failure it fails the item under the normal retry policy.
"""

from __future__ import annotations

import re
from typing import Any

from ..clock import actor as clock_actor
from ..errors import DomainError
from ..paths import Paths
from ..queue import engine
from ..store import jsonl
from ..textutil import contains, sentence_split
from ..validate.envelope import Failure
from . import draft_map as draft_map_mod

PROSE_DIR = "compiler/prose"

_CLAIM_STRICT = re.compile(r"\(claim:\s*(NODE-\d+)\s*\)")
_CITE_STRICT = re.compile(r"\(cite:\s*(EU-\d+)\s*\)")
_CLAIM_LOOSE = re.compile(r"\(claim:[^)]*\)")
_CITE_LOOSE = re.compile(r"\(cite:[^)]*\)")


def _section_index(section: dict[str, Any]) -> tuple[set[str], dict[str, set[str]], list[str]]:
    node_ids: set[str] = set()
    bindings: dict[str, set[str]] = {}
    forbidden: list[str] = []
    for claim in section.get("claims", []):
        node_ids.add(claim["node_id"])
        bindings[claim["node_id"]] = set(claim.get("evidence_ids", []) or [])
        forbidden.extend(claim.get("forbidden_language", []) or [])
    return node_ids, bindings, forbidden


def check_prose(text: str, section: dict[str, Any]) -> list[Failure]:
    """Run V-PROSE-01..04 for one section's prose against its DraftMap section."""
    node_ids, bindings, forbidden = _section_index(section)
    failures: list[Failure] = []
    annotated_nodes: set[str] = set()

    for idx, sentence in enumerate(sentence_split(text), start=1):
        strict_claims = _CLAIM_STRICT.findall(sentence)
        strict_cites = _CITE_STRICT.findall(sentence)
        loose_claims = _CLAIM_LOOSE.findall(sentence)
        loose_cites = _CITE_LOOSE.findall(sentence)

        # malformed annotation grammar => the offending family's rule fires.
        if len(loose_claims) != len(strict_claims):
            failures.append(Failure("V-PROSE-01", f"sentence {idx}: malformed claim annotation"))
        if len(loose_cites) != len(strict_cites):
            failures.append(Failure("V-PROSE-02", f"sentence {idx}: malformed cite annotation"))

        sentence_nodes = set(strict_claims)
        annotated_nodes |= sentence_nodes

        # V-PROSE-01: every claim annotation resolves to a DraftMap claim.
        for nid in strict_claims:
            if nid not in node_ids:
                failures.append(Failure("V-PROSE-01", f"sentence {idx}: {nid} not in DraftMap section"))

        # V-PROSE-02: every cite is bound to a node annotated in the SAME sentence.
        allowed_eus: set[str] = set()
        for nid in sentence_nodes:
            allowed_eus |= bindings.get(nid, set())
        for eu in strict_cites:
            if eu not in allowed_eus:
                failures.append(Failure("V-PROSE-02", f"sentence {idx}: {eu} not bound to an annotated node"))

    # V-PROSE-03: no forbidden_language string appears in the prose.
    for phrase in forbidden:
        if phrase and contains(text, phrase):
            failures.append(Failure("V-PROSE-03", f"forbidden string present: {phrase!r}"))

    # V-PROSE-04: every DraftMap claim of the section is annotated >=1 time.
    for nid in node_ids:
        if nid not in annotated_nodes:
            failures.append(Failure("V-PROSE-04", f"claim {nid} not annotated"))

    return failures


def _section_of(wi: dict[str, Any]) -> str:
    task_id = wi.get("task_id") or ""
    if task_id.startswith("PROSE-"):
        return task_id[len("PROSE-"):]
    return wi["target_id"]


def ingest_prose(paths: Paths, output_file: str, work_item_id: str, actor: str | None = None) -> dict[str, Any]:
    actor = actor or clock_actor()
    wi = engine.get_item(paths, work_item_id)
    section_id = _section_of(wi)

    failures: list[Failure] = []
    declared = list(wi.get("output_files") or [])
    if declared and output_file != declared[0]:
        failures.append(Failure("V-PATH-01", f"path {output_file} != declared {declared[0]}"))

    dm = draft_map_mod.latest_draft_map(paths)
    section = None
    if dm is not None:
        section = next((s for s in dm["sections"] if s["section_id"] == section_id), None)
    if section is None:
        failures.append(Failure("V-PROSE-01", f"no DraftMap section for {section_id}"))

    src = paths.project_dir / output_file
    if not src.exists():
        failures.append(Failure("V-PATH-03", f"prose file missing: {output_file}"))
        text = ""
    else:
        text = src.read_text(encoding="utf-8")

    if section is not None and src.exists():
        failures += check_prose(text, section)

    if failures:
        rule_ids = _dedup([f.rule_id for f in failures])
        engine.validate_fail(paths, work_item_id, rule_ids, actor)
        raise DomainError(rule_ids, data={"failed_rules": rule_ids, "section_id": section_id})

    dst = paths.resolve(f"{PROSE_DIR}/{section_id}.md")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")

    engine.validate_pass(paths, work_item_id, actor, detail={"section_id": section_id})
    engine.commit_item(paths, work_item_id, actor)
    return {"section_id": section_id, "prose_path": f"{PROSE_DIR}/{section_id}.md"}


def _dedup(items: list[str]) -> list[str]:
    seen: list[str] = []
    for i in items:
        if i not in seen:
            seen.append(i)
    return seen
