"""T-S3 (docs/11 §12): S3 Stage A-lite — source registry, tiers, provenance.

Covers the adopted Stage A-lite rules only. Stage B triangulation (V-SRC-04) is
NOT adopted in this build (docs/16, docs/00 adoption entry) and is not tested.

  T-S3-1  ingest learns blocked_direct from a blocked log entry (+ append-versioning)
  T-S3-2  tier-mapping golden; silent tier-lowering rejected (V-SRC-03)
  T-S3-4  provenance present (V-SRC-01); dangling quoted_via => V-SRC-02;
          dispatch registry excerpt completeness (V-SRC-05); document.v2
          round-trip (+ document.v1 still valid as v1)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from paperproof.docsdb import registry
from paperproof.schemas import REGISTRY
from paperproof.schemas.docs import Document, DocumentV2, Provenance, SourceProfile
from paperproof.serialize import canonical_bytes
from paperproof.store import jsonl
from paperproof.validate.rules import v_src
from tests.fakes import scenario
from tests.fakes.workers import FakeDocsWorker, FakeProofWorker, drain_docs, prove_one

pytestmark = pytest.mark.contract

SOURCES = "docs/sources.jsonl"
DOCUMENTS = "docs/documents.jsonl"
FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "schemas"


# --- T-S3-1: ingest learns blocked_direct + append-versioning ----------------


def test_ingest_learns_blocked_direct_from_log(project, pp):
    paths = scenario.paths_for_pp(pp)
    # a search_log entry evidencing a blocked direct fetch (the S1 query_log path
    # is read the same way — see registry._blocked_texts).
    result = {"search_log": ["fetched https://bls.gov/empsit -> HTTP 403 Forbidden",
                             "fell back to ERP secondary quote"]}
    registry.learn(paths, [("bls.gov", "official_report")], result)

    prof = next(p for p in registry.load_latest(paths) if p["domain"] == "bls.gov")
    assert prof["fetch"]["blocked_direct"] is True
    assert prof["tier"] == "T1_official"
    assert prof["seen_count"] == 1

    # append-versioning: a second ingest appends a NEW version (never mutates).
    registry.learn(paths, [("bls.gov", "official_report")], {"search_log": []})
    versions = [r for r in jsonl.read_all(paths.resolve(SOURCES)) if r["domain"] == "bls.gov"]
    assert len(versions) == 2, "each ingest appends a new SourceProfile version"
    latest = next(p for p in registry.load_latest(paths) if p["domain"] == "bls.gov")
    assert latest["seen_count"] == 2
    assert latest["source_id"] == prof["source_id"]  # stable id across versions
    assert latest["fetch"]["blocked_direct"] is True  # sticky once learned


def test_defensive_query_log_blocked_signal():
    # forward-compatible with S1's docs_result.v2 query_log (outcome='blocked').
    texts = registry._blocked_texts(
        {"query_log": [{"outcome": "blocked", "domain": "fred.stlouisfed.org", "query": "gdp"}]}
    )
    assert texts and registry._domain_blocked("fred.stlouisfed.org", texts)
    # and a clean log yields no blocked signal.
    assert registry._blocked_texts({"search_log": ["clean fetch ok"]}) == []


# --- T-S3-2: tier-mapping golden + silent tier-lowering rejected -------------


def test_tier_mapping_golden():
    assert registry.TIER_TABLE == {
        "official_report": "T1_official",
        "peer_reviewed": "T2_peer_reviewed",
        "working_paper": "T3_working_paper",
        "dataset": "T4_industry_data",
        "news": "T5_press",
        "user_notes": "T6_other",
    }
    for source_type, tier in registry.TIER_TABLE.items():
        assert registry.tier_for(source_type) == tier


def test_silent_tier_lowering_rejected_vsrc03():
    lowered = [
        {"domain": "x.gov", "tier": "T1_official", "tier_note": None},
        {"domain": "x.gov", "tier": "T5_press", "tier_note": None},
    ]
    fails = v_src.check_registry_history(lowered)
    assert any(f.rule_id == "V-SRC-03" for f in fails)

    # the SAME change carrying a note passes.
    noted = [
        {"domain": "x.gov", "tier": "T1_official", "tier_note": None},
        {"domain": "x.gov", "tier": "T5_press", "tier_note": "human recategorized"},
    ]
    assert v_src.check_registry_history(noted) == []


def test_auto_raise_carries_note_and_never_lowers(project, pp):
    paths = scenario.paths_for_pp(pp)
    # first a news doc (T5), then a peer-reviewed one from the same domain (T2):
    registry.learn(paths, [("nature.com", "news")], {})
    registry.learn(paths, [("nature.com", "peer_reviewed")], {})
    latest = next(p for p in registry.load_latest(paths) if p["domain"] == "nature.com")
    assert latest["tier"] == "T2_peer_reviewed"  # raised to the most authoritative
    assert latest["tier_note"]  # the change carries a note
    # a subsequent LESS authoritative doc does not lower the learned tier.
    registry.learn(paths, [("nature.com", "news")], {})
    latest2 = next(p for p in registry.load_latest(paths) if p["domain"] == "nature.com")
    assert latest2["tier"] == "T2_peer_reviewed"
    # and the whole history is V-SRC-03 clean (every change is noted).
    assert v_src.check_registry_history(registry.load_all(paths)) == []


def test_cli_source_set_refuses_silent_lowering(project, pp):
    paths = scenario.paths_for_pp(pp)
    registry.learn(paths, [("bls.gov", "official_report")], {})  # T1
    # lowering the tier with no note => V-SRC-03 (exit 1).
    env = pp("docs", "source", "set", "--domain", "bls.gov", "--tier", "T5_press", expect=1)
    assert "V-SRC-03" in env["errors"]
    # the same curation WITH a note is accepted (append).
    ok = pp("docs", "source", "set", "--domain", "bls.gov", "--tier", "T5_press",
            "--note", "operator downgrade after retraction")
    assert ok["data"]["tier"] == "T5_press"


def test_cli_source_list_and_set_workaround(project, pp):
    paths = scenario.paths_for_pp(pp)
    registry.learn(paths, [("bls.gov", "official_report")], {"search_log": ["bls.gov 403"]})
    listed = pp("docs", "source", "list")
    assert listed["data"]["count"] == 1
    pp("docs", "source", "set", "--domain", "bls.gov", "--workaround", "archive_org",
       "--note", "wayback snapshots fetch clean", "--publisher", "US BLS")
    latest = next(p for p in registry.load_latest(paths) if p["domain"] == "bls.gov")
    assert latest["publisher"] == "US BLS"
    assert any(w["kind"] == "archive_org" for w in latest["fetch"]["workarounds"])


# --- T-S3-4: provenance (V-SRC-01), quoted_via (V-SRC-02), excerpt (V-SRC-05) -


def _v2_doc(**prov) -> dict:
    p = {"retrieved_at": "2026-07-07T00:00:00Z", "fetch_method": "direct",
         "tier": "T1_official", "quoted_via": None}
    p.update(prov)
    return {
        "schema_version": "document.v2", "doc_id": "DOC-010", "project_id": "p4-ldi",
        "title": "T", "source_type": "official_report",
        "origin": {"kind": "web", "path": None, "url": "https://x.gov"},
        "content_hash": "sha256:x", "text_path": None, "citation_key": "K",
        "ingested_from": "DRES-001", "ingested_at": "2026-07-07T00:00:00Z", "provenance": p,
    }


def test_vsrc01_provenance_present_v2_only():
    assert v_src.check_document_provenance(_v2_doc()) == []
    # a v1 document is exempt (legacy, still readable).
    v1 = json.loads((FIXTURES / "document.v1.json").read_bytes())
    assert v_src.check_document_provenance(v1) == []
    # a v2 doc whose tier is out of enum fails V-SRC-01.
    bad = _v2_doc(tier="BOGUS_TIER")
    assert any(f.rule_id == "V-SRC-01" for f in v_src.check_document_provenance(bad))


def test_vsrc02_dangling_quoted_via():
    doc = _v2_doc(fetch_method="secondary_quote", quoted_via="DOC-999")
    # carrier not archived => V-SRC-02.
    fails = v_src.check_secondary_quote(doc, {"DOC-010"})
    assert any(f.rule_id == "V-SRC-02" for f in fails)
    # carrier present => clean.
    assert v_src.check_secondary_quote(doc, {"DOC-010", "DOC-999"}) == []
    # secondary_quote that names NO quoted_via => V-SRC-02.
    unnamed = _v2_doc(fetch_method="secondary_quote", quoted_via=None)
    assert any(f.rule_id == "V-SRC-02" for f in v_src.check_secondary_quote(unnamed, {"DOC-010"}))


def test_vsrc05_dispatch_excerpt_completeness(project, pp):
    paths = scenario.paths_for_pp(pp)
    registry.learn(paths, [("bls.gov", "official_report")], {})       # T1 (always ships)
    registry.learn(paths, [("brookings.edu", "working_paper")], {})  # T3, off-topic
    registry.learn(paths, [("adp.com", "dataset")], {})              # T4, facet match
    all_profiles = registry.load_latest(paths)

    need = "ADP payroll data on employment change"
    facet_text = registry._facet_text(need, [], {})
    excerpt = registry.matched_profiles(paths, need)
    domains = {p["domain"] for p in excerpt}
    assert "bls.gov" in domains          # every T1 profile ships
    assert "adp.com" in domains          # facet-matched by 'adp'
    assert "brookings.edu" not in domains  # off-topic, non-T1 excluded

    excerpt_ids = {p["source_id"] for p in excerpt}
    assert v_src.check_registry_excerpt(all_profiles, facet_text, excerpt_ids) == []
    # dropping the required T1 profile from the excerpt fails V-SRC-05.
    bls_id = next(p["source_id"] for p in excerpt if p["domain"] == "bls.gov")
    trimmed = excerpt_ids - {bls_id}
    fails = v_src.check_registry_excerpt(all_profiles, facet_text, trimmed)
    assert any(f.rule_id == "V-SRC-05" for f in fails)

    # the excerpt renders as a read-only, lawful-workaround REGISTRY block.
    block = registry.render_excerpt(excerpt)
    assert "bls.gov" in block and "[T1_official]" in block


def test_document_v2_roundtrip_and_v1_still_valid():
    # document.v2 round-trips to a fixed point.
    doc = DocumentV2(
        doc_id="DOC-020", project_id="p4-ldi", title="T", source_type="news",
        origin={"kind": "web", "path": None, "url": "https://x.press"},
        content_hash="sha256:z", text_path=None, citation_key="K2",
        ingested_from="DRES-003", ingested_at="2026-07-07T00:00:00Z",
        provenance=Provenance(retrieved_at="2026-07-07T00:00:00Z", fetch_method="archive_org",
                              tier="T5_press", quoted_via=None),
    )
    b = canonical_bytes(doc)
    assert canonical_bytes(DocumentV2.model_validate_json(b)) == b
    # document.v1 (no provenance) still parses + validates as document.v1.
    v1 = json.loads((FIXTURES / "document.v1.json").read_bytes())
    assert REGISTRY["document.v1"] is Document
    parsed = Document.model_validate(v1)
    assert parsed.schema_version == "document.v1"


# --- end-to-end: real ingest writes document.v2 + learns the registry --------


def test_ingest_result_writes_provenance_and_learns_registry(project, pp):
    paths = scenario.paths_for_pp(pp)
    scenario.seed_docs_facts(paths, [scenario.FACT_CLAIM])
    prove_one(paths, "NODE-003", FakeProofWorker({"NODE-003": scenario.node_insufficient_form()}))

    text = "BLS payroll tables show AI-exposed employment shifted in 2024 as reported."
    spec = {
        "documents": [{
            "title": "BLS Employment Situation",
            "source_type": "official_report",
            "origin": {"kind": "web", "path": None, "url": "https://www.bls.gov/news.release/empsit.htm"},
            "citation_key": "BLS2024",
            "text": text,
        }],
        "evidence_units": [{
            "doc_ref": 0, "doc_id": None, "location": "Table B-1", "kind": "quote",
            "quote_or_paraphrase": "AI-exposed employment shifted in 2024",
            "summary": "BLS payroll data on AI-exposed employment",
            "support_direction": "context",
            "can_cite_for": [scenario.FACT_CLAIM], "cannot_cite_for": ["unrelated claim"],
            "scope": {},
        }],
        "not_found": False,
        "search_log": ["bls.gov empsit -> HTTP 403 Forbidden; used archived copy"],
    }
    drain_docs(paths, FakeDocsWorker({"*": spec}))

    doc = next(d for d in jsonl.latest_records(paths.resolve(DOCUMENTS), "doc_id")
               if d["citation_key"] == "BLS2024")
    assert doc["schema_version"] == "document.v2"
    assert doc["provenance"]["tier"] == "T1_official"      # denormalized via registry
    assert doc["provenance"]["fetch_method"] == "direct"   # v1-path default
    assert doc["provenance"]["retrieved_at"]

    prof = next(p for p in registry.load_latest(paths) if p["domain"] == "bls.gov")
    assert prof["tier"] == "T1_official"
    assert prof["fetch"]["blocked_direct"] is True  # learned from the 403 log line

    # the whole project still verifies clean with v2 docs + a learned registry.
    assert pp("verify")["data"]["ok"] is True
