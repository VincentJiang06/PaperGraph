"""r3 core-bug regressions from the ai-jobs live run (docs/00 r3 changelog).

Each test pins one of the run's basic failures:
  1. cache chaining — a false "cache" fulfillment must never satisfy a future
     identical search (docs/04: fingerprint sources are DRES-fulfilled only);
  2. pack composition — REQUESTED evidence lands unconditionally, matched half
     capped at K=12 (docs/04 r3; the run's packs carried all 24 EUs by luck);
  3. saturation (S4, docs/17) SUPERSEDES the r3 docs cap — a pile of completed
     Orchestrator single requests must NOT dead-letter a healthy target
     (QE-000114): rounds accrue but a mandatory angle stays no_attempt, so the
     target is NOT saturated and search keeps opening;
  4. evidence-arrival staleness — newly ingested evidence marks pending proof
     items stale so re-proofs never run on pre-evidence packs (V-TASK-04).
"""

from __future__ import annotations

import json

import pytest

from paperproof.committer import apply as committer_apply
from paperproof.docsdb import cache, coverage, pack
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


# --- 3. saturation supersedes the docs cap (QE-000114) -----------------------


def test_orchestrator_requests_do_not_saturate_a_healthy_target(project, pp):
    """SUPERSEDES the r3 verdict-count cap (migrated to saturation). A pile of
    completed Orchestrator single requests accrues rounds but never attempts the
    academic angle, so the target is NOT saturated -- exactly the QE-000114
    regression: a healthy target must keep opening search, never dead-letter."""
    paths = _paths(pp)
    node = {"node_id": "NODE-C", "node_type": "fact", "claim": "gilt collateral pressure statistics",
            "scope": {}, "evidence_bindings": []}
    jsonl.append(paths.resolve(DOCS_REQUESTS), _request("DR-920", "fp-920", "DRES-002", target_id="NODE-C"))
    for i in range(921, 925):
        jsonl.append(paths.resolve(DOCS_REQUESTS), _request(f"DR-{i}", f"fp-{i}", "DRES-002", target_id="NODE-C"))

    ctx = coverage.build_context(paths, spine_ids=set())
    ledger = coverage.target_ledger(node, ctx)
    # rounds accrue (5 completed single requests) but a mandatory angle never
    # attempted => NOT saturated => the committer keeps opening search (no cap).
    assert ledger["rounds"] >= 2
    assert ledger["angles"]["academic"] == coverage.NO_ATTEMPT
    assert ledger["saturated"] is False


def test_saturation_is_a_pure_function_of_rounds_angles_new_docs(project, pp):
    """The saturation stop criterion (docs/17): rounds>=2 AND every mandatory
    angle not no_attempt AND new_docs_last_round=0."""
    prod = {a: coverage.PRODUCTIVE for a in coverage.BASE_MANDATORY}
    assert coverage.is_saturated(2, prod, 0, coverage.BASE_MANDATORY) is True
    assert coverage.is_saturated(1, prod, 0, coverage.BASE_MANDATORY) is False
    assert coverage.is_saturated(2, prod, 3, coverage.BASE_MANDATORY) is False
    missing = {**prod, "academic": coverage.NO_ATTEMPT}
    assert coverage.is_saturated(2, missing, 0, coverage.BASE_MANDATORY) is False


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
