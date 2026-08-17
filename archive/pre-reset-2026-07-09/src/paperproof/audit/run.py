"""Mechanical audit (docs/06, docs/08 B10).

`audit run --draft <DRAFTMAP-id>` runs four mechanical check families over the
promoted prose (compiler/prose/) against the DraftMap + graph + evidence +
contract + covering FreezeItems:

  binding   every (cite: EU-x) resolves, sits in a claim sentence, and is bound
            in the DraftMap to a node annotated in that same sentence;
  strength  no forbidden_language string (DraftMap section + covering FreezeItems)
            appears in the prose;
  scope     no contract forbidden_claims string appears verbatim; every
            (claim: NODE-x) resolves to a frozen spine node;
  coverage  every DraftMap claim of each section is annotated >=1x; no annotation
            id is absent from the DraftMap.

Every finding carries kind + location + target_id so it can be routed as a
compile_queue item mechanically [V-AUD-01]. Audit writes only audit/ [V-AUD-02].
"""

from __future__ import annotations

import re
from typing import Any

from ..clock import actor as clock_actor
from ..clock import now as clock_now
from ..errors import DomainError
from ..graph import model as graph_model
from ..ids import next_id
from ..paths import Paths
from ..store import jsonl
from ..textutil import contains, sentence_split
from ..compiler import draft_map as draft_map_mod

AUDIT_REPORTS = "audit/audit_reports.jsonl"
EVIDENCE_UNITS = "docs/evidence_units.jsonl"
FROZEN_ITEMS = "freeze/frozen_items.jsonl"

_CLAIM = re.compile(r"\(claim:\s*(NODE-\d+)\s*\)")
_CITE = re.compile(r"\(cite:\s*(EU-\d+)\s*\)")


def _frozen_forbidden(paths: Paths) -> list[str]:
    items = jsonl.read_all(paths.resolve(FROZEN_ITEMS))
    revoked = {it["revokes"] for it in items if it["action"] == "unfreeze" and it.get("revokes")}
    forbidden: set[str] = set()
    for it in items:
        if it["action"] == "freeze" and it["freeze_id"] not in revoked:
            forbidden |= set(it.get("forbidden_language", []) or [])
    return sorted(forbidden)


def _read_prose(paths: Paths, section_id: str) -> str:
    p = paths.resolve(f"compiler/prose/{section_id}.md")
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def _locate(prose: str, needle: str) -> str | None:
    for idx, sentence in enumerate(sentence_split(prose), start=1):
        if contains(sentence, needle):
            return f"sentence {idx}"
    return None


def run(paths: Paths, draft_map_id: str, actor: str | None = None) -> dict[str, Any]:
    actor = actor or clock_actor()
    dm = draft_map_mod.load_draft_map(paths, draft_map_id)
    if dm is None:
        raise DomainError([f"draft map not found: {draft_map_id}"])

    gv = graph_model.load(paths)
    spine_ids, _ = gv.spine()
    frozen_spine = {i for i in spine_ids if (gv.record(i) or {}).get("frozen")}
    eus = {e["evidence_id"] for e in jsonl.latest_records(paths.resolve(EVIDENCE_UNITS), "evidence_id")}
    contract = jsonl.read_json(paths.project_contract) if paths.project_contract.exists() else {}
    contract_forbidden = list(contract.get("forbidden_claims", []) or [])
    freeze_forbidden = _frozen_forbidden(paths)

    findings: list[dict[str, Any]] = []

    def add(kind: str, location: str, target_id: str, detail: str) -> None:
        findings.append({"kind": kind, "location": location, "target_id": target_id, "detail": detail})

    for section in dm["sections"]:
        section_id = section["section_id"]
        prose = _read_prose(paths, section_id)
        node_ids: set[str] = set()
        bindings: dict[str, set[str]] = {}
        section_forbidden: list[tuple[str, str]] = []  # (phrase, target_node)
        section_eu_ids: set[str] = set()
        for claim in section.get("claims", []):
            nid = claim["node_id"]
            node_ids.add(nid)
            bindings[nid] = set(claim.get("evidence_ids", []) or [])
            section_eu_ids |= bindings[nid]
            for phrase in claim.get("forbidden_language", []) or []:
                section_forbidden.append((phrase, nid))

        fallback_target = next(iter(sorted(node_ids)), section_id)
        for phrase in freeze_forbidden:
            section_forbidden.append((phrase, fallback_target))

        annotated_nodes: set[str] = set()
        annotated_eus: set[str] = set()

        # per-sentence binding + scope(claim) checks
        for idx, sentence in enumerate(sentence_split(prose), start=1):
            loc = f"{section_id}:sentence {idx}"
            claims = _CLAIM.findall(sentence)
            cites = _CITE.findall(sentence)
            annotated_nodes |= set(claims)
            annotated_eus |= set(cites)

            allowed_eus: set[str] = set()
            for nid in claims:
                allowed_eus |= bindings.get(nid, set())

            for eu in cites:
                if eu not in eus:
                    add("binding", loc, eu, "cite does not resolve to an EvidenceUnit")
                elif not claims:
                    add("binding", loc, eu, "cite outside a claim sentence")
                elif eu not in allowed_eus:
                    add("binding", loc, eu, "cite not bound to an annotated node in this sentence")

            for nid in claims:
                if nid not in frozen_spine:
                    add("scope", loc, nid, "claim does not resolve to a frozen spine node")

        # strength: forbidden strings present anywhere in the section prose
        for phrase, target in section_forbidden:
            if phrase and contains(prose, phrase):
                where = _locate(prose, phrase) or "para 1"
                add("strength", f"{section_id}:{where}", target, f"forbidden string present: {phrase!r}")

        # scope: contract forbidden_claims present verbatim
        for phrase in contract_forbidden:
            if phrase and contains(prose, phrase):
                where = _locate(prose, phrase) or "para 1"
                add("scope", f"{section_id}:{where}", fallback_target, f"forbidden claim present: {phrase!r}")

        # coverage: every DraftMap claim annotated, no annotation absent from DraftMap
        for nid in sorted(node_ids):
            if nid not in annotated_nodes:
                add("coverage", f"{section_id}:para 1", nid, "DraftMap claim not annotated")
        for nid in sorted(annotated_nodes):
            if nid not in node_ids:
                add("coverage", f"{section_id}:para 1", nid, "annotated node absent from DraftMap")
        for eu in sorted(annotated_eus):
            if eu not in section_eu_ids:
                add("coverage", f"{section_id}:para 1", eu, "annotated cite absent from DraftMap")

    audit_id = next_id("AUD", [r["audit_id"] for r in jsonl.read_all(paths.resolve(AUDIT_REPORTS))])
    report = {
        "schema_version": "audit_report.v1",
        "audit_id": audit_id,
        "project_id": paths.project_id,
        "draft_ref": draft_map_id,
        "findings": findings,
        "passed": not findings,
        "created_at": clock_now(),
    }
    jsonl.append(paths.resolve(AUDIT_REPORTS), report)
    return report
