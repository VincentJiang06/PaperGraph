"""r3 core-bug regressions from the ai-jobs live run (docs/00 r3 changelog).

Each test pins one of the run's basic failures:
  1. cache chaining — a false "cache" fulfillment must never satisfy a future
     identical search (docs/04: fingerprint sources are DRES-fulfilled only);
  2. pack composition — REQUESTED evidence lands unconditionally, matched half
     capped at K=12 (docs/04 r3; the run's packs carried all 24 EUs by luck);
  3. docs cap — verdict-based, never request-based; fresh target-relevant
     evidence since the 2nd verdict defuses the dead-letter (QE-000114);
  4. evidence-arrival staleness — newly ingested evidence marks pending proof
     items stale so re-proofs never run on pre-evidence packs (V-TASK-04).
"""

from __future__ import annotations

import json

import pytest

from paperproof.committer import apply as committer_apply
from paperproof.docsdb import cache, pack
from paperproof.paths import paths_for
from paperproof.queue import engine
from paperproof.store import jsonl

from tests.fakes import scenario

pytestmark = pytest.mark.contract

DOCS_REQUESTS = "docs/docs_requests.jsonl"
EVIDENCE_UNITS = "docs/evidence_units.jsonl"
PROOF_RESULTS = "proof/proof_results.jsonl"


def _paths(pp):
    return paths_for(pp.tmp_path, "p4-ldi")


def _request(rid: str, fp: str, fulfilled_by, target_id: str = "NODE-001") -> dict:
    return {
        "schema_version": "docs_request.v1", "request_id": rid, "project_id": "p4-ldi",
        "requested_by": "orchestrator", "target_id": target_id, "need": f"need {rid}",
        "search_hints": [], "fingerprint": fp, "status": "fulfilled",
        "fulfilled_by": fulfilled_by, "created_at": "2026-07-08T00:00:00Z",
    }


def _eu(eid: str, summary: str, ingested_from=None, created_at: str = "2026-07-08T00:00:00Z") -> dict:
    return {
        "schema_version": "evidence_unit.v1", "evidence_id": eid, "project_id": "p4-ldi",
        "doc_id": "DOC-001", "location": "p.1", "kind": "paraphrase",
        "quote_or_paraphrase": summary, "summary": summary, "support_direction": "supports",
        "can_cite_for": [summary], "cannot_cite_for": ["overclaim"], "scope": {},
        "extracted_by": "t", "ingested_from": ingested_from, "created_at": created_at,
    }


# --- 1. cache sources are DRES-fulfilled only --------------------------------


def test_cache_hit_requires_dres_fulfillment(project, pp):
    paths = _paths(pp)
    jsonl.append(paths.resolve(DOCS_REQUESTS), _request("DR-901", "fp-false", "cache"))
    jsonl.append(paths.resolve(DOCS_REQUESTS), _request("DR-902", "fp-real", "DRES-001"))
    # a false cache fulfillment must not chain; a real one may.
    assert cache.fingerprint_hit(paths, "fp-false") is False
    assert cache.fingerprint_hit(paths, "fp-real") is True
    assert cache.is_cache_hit(paths, "fp-false", {"node_id": "NODE-001", "claim": "x", "scope": {}}) is False


# --- 2. pack = REQUESTED (unconditional) ∪ top-12 MATCHED ---------------------


def test_pack_requested_unconditional_and_matched_capped(project, pp):
    paths = _paths(pp)
    target = {"node_id": "NODE-P", "claim": "gilt collateral pressure statistics", "scope": {}}
    # requested-for-target EU with ZERO token overlap with the claim:
    jsonl.append(paths.resolve(DOCS_REQUESTS), _request("DR-910", "fp-910", "DRES-009", target_id="NODE-P"))
    jsonl.append(paths.resolve(EVIDENCE_UNITS), _eu("EU-100", "unrelated aggregate employment figures", ingested_from="DRES-009"))
    # 14 matcher-matching EUs (>=2 shared tokens with the claim):
    for i in range(101, 115):
        jsonl.append(paths.resolve(EVIDENCE_UNITS), _eu(f"EU-{i}", "gilt collateral pressure evidence"))

    eus, _meta = pack.assemble(paths, target)
    ids = [e["evidence_id"] for e in eus]
    assert ids[0] == "EU-100"                # requested lands first, despite score 0
    assert len(ids) == 1 + pack.MATCHED_K    # matched half capped at K=12
    assert len(set(ids)) == len(ids)


# --- 3. docs cap: verdicts only; fresh evidence defuses it -------------------


def _verdict(pr: str, target_id: str, validated_at: str) -> dict:
    return {
        "schema_version": "verdict_record.v1", "proof_result_id": pr, "project_id": "p4-ldi",
        "work_item_id": "WI-000001", "task_id": f"PT-{target_id}", "target_type": "node",
        "target_id": target_id, "form": {}, "assumptions": [], "evidence_used": [],
        "language_limits": None, "repair_proposals": [], "docs_requests": [], "notes": "",
        "computed_verdict": {"verdict": "needs_docs", "repair_kind": None, "strength": None, "reason": None},
        "bundle": {"task_file": "", "context_pack": "", "docs_pack": ""},
        "validated_at": validated_at,
    }


def test_cap_counts_verdicts_and_fresh_evidence_defuses(project, pp):
    paths = _paths(pp)
    target = {"node_id": "NODE-C", "claim": "gilt collateral pressure statistics", "scope": {}}
    jsonl.append(paths.resolve(PROOF_RESULTS), _verdict("PR-901", "NODE-C", "2026-07-08T01:00:00Z"))
    jsonl.append(paths.resolve(PROOF_RESULTS), _verdict("PR-902", "NODE-C", "2026-07-08T02:00:00Z"))
    # a pile of completed ORCHESTRATOR requests must not count (QE-000114 repro):
    for i in range(920, 925):
        jsonl.append(paths.resolve(DOCS_REQUESTS), _request(f"DR-{i}", f"fp-{i}", "DRES-002", target_id="NODE-C"))
    assert len(committer_apply._needs_docs_verdicts(paths, "NODE-C")) == 2

    # no target-relevant evidence since the 2nd verdict => a 3rd would dead-letter
    assert committer_apply._new_target_evidence_since(paths, target, "2026-07-08T02:00:00Z") is False
    # fresh MATCHING evidence after the 2nd verdict defuses the cap
    jsonl.append(paths.resolve(EVIDENCE_UNITS), _eu("EU-200", "gilt collateral pressure dataset", created_at="2026-07-08T03:00:00Z"))
    assert committer_apply._new_target_evidence_since(paths, target, "2026-07-08T02:00:00Z") is True
    # non-matching late evidence does not
    jsonl.append(paths.resolve(EVIDENCE_UNITS), _eu("EU-201", "unrelated employment survey", created_at="2026-07-08T03:30:00Z"))
    assert committer_apply._new_target_evidence_since(
        paths, {"node_id": "NODE-C", "claim": "zzz qqq", "scope": {}}, "2026-07-08T03:15:00Z"
    ) is False


# --- 4. evidence arrival marks pending proof items stale (V-TASK-04) ---------


def test_evidence_arrival_marks_pending_items_stale(project, pp, clock):
    paths = _paths(pp)
    scenario.seed_docs_facts(paths, [scenario.FACT_CLAIM])
    fact_item = next(
        i for i in engine.load_items(paths)
        if i["queue_name"] == "proof_queue" and i["target_type"] == "node"
        and i["target_id"] not in ("NODE-001", "NODE-002")
    )
    assert fact_item["status"] in ("queued", "blocked")

    # an orchestrator DocsRequest (fresh fingerprint => cache miss => real item)
    env = pp("--project", "p4-ldi", "docs", "request", "--target", fact_item["target_id"],
             "--need", "primary evidence on LDI margin calls and liquidity pressure",
             "--hint", "boe fsr 2022")
    dr_id = env["data"]["request_id"]
    assert env["data"]["status"] == "open"
    docs_item = next(i for i in engine.load_items(paths) if i.get("target_id") == dr_id)

    engine.claim(paths, queue_name="docs_queue", agent="dw-test", wi_id=docs_item["work_item_id"])
    out_rel = docs_item["output_files"][0]
    out = paths.resolve(out_rel)
    out.parent.mkdir(parents=True, exist_ok=True)
    spec = scenario.boe_docs_result_spec()
    spec.update({"schema_version": "docs_result.v1", "request_id": dr_id, "project_id": "p4-ldi"})
    out.write_text(json.dumps(spec), encoding="utf-8")
    engine.complete(paths, docs_item["work_item_id"], "dw-test")

    env = pp("--project", "p4-ldi", "docs", "ingest-result", out_rel, "--work-item", docs_item["work_item_id"])
    assert env["ok"] is True

    # the pending fact NODE_CHECK is now stale (its future -rN pack will carry the EU)
    refreshed = engine.get_item(paths, fact_item["work_item_id"])
    assert refreshed["status"] == "stale"
    events = jsonl.read_all(paths.resolve("queue/events.jsonl"))
    inv = [e for e in events if e["op"] == "invalidate" and e["work_item_id"] == fact_item["work_item_id"]]
    assert inv and inv[-1]["detail"].get("reason") == "evidence_arrival"
