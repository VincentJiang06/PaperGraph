"""Docs ingestor + matcher + fingerprint contract tests (docs/04, docs/09 §2
matrix: dedup by content_hash, citation-key uniqueness, text extraction,
fingerprint stability, matcher threshold/order)."""

from __future__ import annotations

import pytest

from paperproof.docsdb import ingest, matcher, pack
from paperproof.paths import paths_for
from paperproof.store import jsonl

pytestmark = pytest.mark.contract

DOCUMENTS = "docs/documents.jsonl"


def _paths(pp):
    return paths_for(pp.tmp_path, "p4-ldi")


# --- `docs ingest`: content_hash dedup + text extraction --------------------


def test_ingest_dedup_by_content_hash(project, pp, tmp_path):
    paths = _paths(pp)
    src = tmp_path / "note.txt"
    src.write_text("Gilt yields rose sharply in autumn 2022.", encoding="utf-8")

    first = ingest.ingest_file(paths, str(src), None, None, None)
    assert first["deduped"] is False
    # a byte-identical second ingest returns the SAME doc_id and appends no record.
    second = ingest.ingest_file(paths, str(src), None, None, None)
    assert second["deduped"] is True
    assert second["doc_id"] == first["doc_id"]
    docs = jsonl.latest_records(paths.resolve(DOCUMENTS), "doc_id")
    assert len(docs) == 1
    # .txt copied verbatim to docs/text/.
    text_path = paths.resolve(docs[0]["text_path"])
    assert text_path.read_text(encoding="utf-8") == "Gilt yields rose sharply in autumn 2022."


def test_ingest_citation_key_collision_appends_suffix(project, pp, tmp_path):
    paths = _paths(pp)
    a = tmp_path / "a.txt"; a.write_text("content A", encoding="utf-8")
    b = tmp_path / "b.txt"; b.write_text("different content B", encoding="utf-8")
    r1 = ingest.ingest_file(paths, str(a), None, None, "SharedKey")
    r2 = ingest.ingest_file(paths, str(b), None, None, "SharedKey")
    assert r1["citation_key"] == "SharedKey"
    assert r2["citation_key"] == "SharedKey-b"


def test_ingest_pdf_extraction_failure_null_text(project, pp, tmp_path):
    paths = _paths(pp)
    bad = tmp_path / "broken.pdf"
    bad.write_bytes(b"%PDF-1.4 this is not a real pdf body")
    r = ingest.ingest_file(paths, str(bad), "official_report", "Broken", None)
    assert r["text_path"] is None
    assert any("text_path=null" in w or "extraction failed" in w for w in r["warnings"])
    doc = jsonl.latest_records(paths.resolve(DOCUMENTS), "doc_id")[0]
    assert doc["text_path"] is None  # still indexed by metadata


# --- fingerprint stability (docs/04) ----------------------------------------


def test_fingerprint_is_stable_and_hint_order_independent():
    a = matcher.fingerprint("Need X", ["h2", "h1"])
    b = matcher.fingerprint("Need X", ["h1", "h2"])
    assert a == b  # hints sorted before hashing
    assert a.startswith("sha256:")
    assert matcher.fingerprint("Need X", ["h1"]) != matcher.fingerprint("Need Y", ["h1"])
    # normalize: NFC + lowercase + whitespace collapse.
    assert matcher.fingerprint("Need   X", []) == matcher.fingerprint("need x", [])


# --- matcher threshold + ordering (docs/04) ---------------------------------


def test_matcher_threshold_and_order():
    claim = "LDI margin calls created acute liquidity pressure in 2022"
    eus = [
        {"evidence_id": "EU-002", "summary": "unrelated topic about weather patterns",
         "quote_or_paraphrase": "", "can_cite_for": [], "scope": {}},
        {"evidence_id": "EU-001", "summary": "LDI margin calls liquidity pressure",
         "quote_or_paraphrase": "acute liquidity pressure 2022", "can_cite_for": [claim], "scope": {}},
        {"evidence_id": "EU-003", "summary": "LDI margin only", "quote_or_paraphrase": "",
         "can_cite_for": [], "scope": {}},
    ]
    matched = matcher.match(claim, {}, eus)
    ids = [eu["evidence_id"] for _s, eu in matched]
    # EU-002 (score < 2) excluded; strongest first, then evidence_id asc.
    assert "EU-002" not in ids
    assert ids[0] == "EU-001"
    assert "EU-003" in ids  # "ldi" + "margin" = score 2


def test_matcher_scope_incompatible_excluded():
    claim = "LDI margin calls created acute liquidity pressure in 2022"
    eu = {"evidence_id": "EU-001", "summary": "LDI margin calls liquidity pressure",
          "quote_or_paraphrase": "", "can_cite_for": [claim], "scope": {"region": "US"}}
    # target scope region UK conflicts with EU region US -> excluded.
    assert matcher.match(claim, {"region": "UK"}, [eu]) == []
    # compatible region passes.
    assert matcher.match(claim, {"region": "UK"}, [{**eu, "scope": {"region": "UK"}}])
