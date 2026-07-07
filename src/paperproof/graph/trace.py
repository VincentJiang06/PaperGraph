"""Traceability chain (docs/09 §3).

`trace --node <id>` walks and prints, as JSON:
  node -> claim -> freeze_id -> commit ids -> PR ids (with bundle paths)
       -> evidence ids -> doc + raw path + location -> prose occurrences
          (section:sentence).

The whole chain is mechanical: every link is a stored id resolved against the
canonical JSONL, so S7 can assert it resolves for every spine node.
"""

from __future__ import annotations

import re
from typing import Any

from ..errors import DomainError
from ..paths import Paths
from ..store import jsonl
from ..textutil import sentence_split
from . import model as graph_model

COMMITS = "commit/commit_decisions.jsonl"
PROOF_RESULTS = "proof/proof_results.jsonl"
DOCUMENTS = "docs/documents.jsonl"
EVIDENCE_UNITS = "docs/evidence_units.jsonl"
FROZEN_ITEMS = "freeze/frozen_items.jsonl"
PROSE_DIR = "compiler/prose"


def _covering_freezes(paths: Paths, node_id: str) -> list[str]:
    items = jsonl.read_all(paths.resolve(FROZEN_ITEMS))
    revoked = {it["revokes"] for it in items if it["action"] == "unfreeze" and it.get("revokes")}
    covering: list[str] = []
    for it in items:
        if it["action"] != "freeze" or it["freeze_id"] in revoked:
            continue
        if node_id in it.get("target_ids", []):
            covering.append(it["freeze_id"])
    return covering


def _prose_occurrences(paths: Paths, node_id: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    prose_dir = paths.resolve(PROSE_DIR)
    if not prose_dir.exists():
        return out
    # Same annotation tolerance as the writers (compiler/prose.py, audit/run.py):
    # (claim:\s*<id>\s*) — optional whitespace around the node id.
    claim_re = re.compile(rf"\(claim:\s*{re.escape(node_id)}\s*\)")
    for path in sorted(prose_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for idx, sentence in enumerate(sentence_split(text), start=1):
            if claim_re.search(sentence):
                out.append({"section": path.stem, "sentence": idx})
    return out


def trace_node(paths: Paths, node_id: str) -> dict[str, Any]:
    gv = graph_model.load(paths)
    node = gv.node_by_id.get(node_id)
    if node is None:
        raise DomainError([f"node not found: {node_id}"])

    freeze_ids = _covering_freezes(paths, node_id)

    commit_ids: list[str] = []
    for cd in jsonl.read_all(paths.resolve(COMMITS)):
        if any(a.get("target_id") == node_id for a in cd.get("actions", [])):
            commit_ids.append(cd["commit_id"])

    proofs: list[dict[str, Any]] = []
    for r in jsonl.read_all(paths.resolve(PROOF_RESULTS)):
        if r.get("target_id") == node_id:
            proofs.append({"proof_result_id": r["proof_result_id"], "bundle": r.get("bundle"), "computed_verdict": r.get("computed_verdict")})

    docs_by_id = {d["doc_id"]: d for d in jsonl.latest_records(paths.resolve(DOCUMENTS), "doc_id")}
    eus_by_id = {e["evidence_id"]: e for e in jsonl.latest_records(paths.resolve(EVIDENCE_UNITS), "evidence_id")}

    evidence: list[dict[str, Any]] = []
    for eid in node.get("evidence_bindings", []) or []:
        eu = eus_by_id.get(eid)
        entry: dict[str, Any] = {"evidence_id": eid, "resolved": eu is not None}
        if eu is not None:
            doc = docs_by_id.get(eu["doc_id"])
            origin = (doc or {}).get("origin", {}) or {}
            raw_path = origin.get("path") or (f"docs/raw/{eu['doc_id']}.txt" if doc is not None else None)
            entry.update(
                {
                    "doc_id": eu["doc_id"],
                    "location": eu.get("location"),
                    "citation_key": (doc or {}).get("citation_key"),
                    "raw_path": raw_path,
                    "text_path": (doc or {}).get("text_path"),
                }
            )
        evidence.append(entry)

    return {
        "node_id": node_id,
        "claim": node["claim"],
        "node_type": node["node_type"],
        "frozen": node.get("frozen", False),
        "freeze_ids": freeze_ids,
        "commit_ids": commit_ids,
        "proof_results": proofs,
        "evidence": evidence,
        "prose_occurrences": _prose_occurrences(paths, node_id),
    }
