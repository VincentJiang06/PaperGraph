"""TC-J (R9): hostile probes proving the anti-hallucination floor holds where
it can, and pinning the ONE architectural limit (a schema-valid out-of-band
forgery is indistinguishable — the single-writer guarantee is by discipline)."""

from __future__ import annotations

import json

from tests.conftest import write_json

ARTICLE = "The pool hit its 200-connection ceiling at 02:59 before the crash."


def _setup(session, tmp_path):
    session("add", "--statement", "崩溃由连接池耗尽引起")            # N-0001
    session("add", "--parent", "N-0001", "--statement", "池是否打满?")  # N-0002
    src = tmp_path / "a.txt"; src.write_text(ARTICLE, encoding="utf-8")
    session("docs", "ingest", "--file", write_json(tmp_path / "e.json", {
        "kind": "report", "title": "监控周报", "url": "https://ex.org/w",
        "text_file": str(src), "summary": "池打满记录",
        "bindings": [{"node_id": "N-0002", "relation": "supports"}]}))   # DOC-0001
    return session


# (a) a fabricated quote (doc_id set, text absent) is degraded, never lands
def test_probe_fabricated_quote_degraded(session, tmp_path):
    _setup(session, tmp_path)
    env = session("conclude", "--file", write_json(tmp_path / "s.json", {
        "node_id": "N-0002", "lean": "supports", "summary": "编造", "confidence": "high",
        "based_on": {"children": [], "evidence": [
            {"title": "监控周报", "doc_id": "DOC-0001",
             "quote": "the pool NEVER filled — fabricated"}]}}))
    assert any("degraded to paraphrase" in w for w in env["warnings"])
    assert env["data"]["synthesis"]["based_on"]["evidence"][0]["quote"] is None


# (b) citing an unarchived doc in prose is a hard reject
def test_probe_unarchived_cite_rejected(session, tmp_path):
    _setup(session, tmp_path)
    session("conclude", "--file", write_json(tmp_path / "s.json", {
        "node_id": "N-0001", "lean": "supports", "summary": "s", "confidence": "low",
        "based_on": {"children": ["N-0002"], "evidence": []}}))
    session("article", "outline", "--file", write_json(tmp_path / "ol.json", {
        "title": "T", "thesis": "th", "grounded_in": ["SYN-0001"],
        "sections": [{"section_id": "S-01", "title": "证据", "role": "evidence",
                       "node_ids": ["N-0002"], "intent": "x"}], "excluded": []}))
    bad = tmp_path / "bad.md"; bad.write_text("凭空 (cite: DOC-9999)。", encoding="utf-8")
    env = session("article", "section", "--id", "S-01", "--file", str(bad), expect=1)
    assert any("does not resolve" in e for e in env["errors"])


# (c) an empty-evidence high-confidence conclusion LANDS but is soft-flagged;
#     a url-only quote is flagged unverifiable (R9 hardening)
def test_probe_unsupported_conclusion_is_soft(session, tmp_path):
    _setup(session, tmp_path)
    session("conclude", "--file", write_json(tmp_path / "s.json", {
        "node_id": "N-0002", "lean": "supports", "summary": "无据高信", "confidence": "high",
        "based_on": {"children": [], "evidence": [
            {"title": "道听途说", "url": "https://x", "quote": "unverifiable claim"}]}}))
    soft = session("check")["data"]["soft"]
    assert any("quote is not verifiable" in w for w in soft)


# (d) out-of-band tampering: a schema-INVALID hand-append is caught hard; a
#     schema-VALID forgery is NOT (documented limit — single writer by discipline)
def test_probe_out_of_band_tampering(session, tmp_path):
    _setup(session, tmp_path)
    nodes_file = session.root / "sessions" / "t" / "tree" / "nodes.jsonl"
    with nodes_file.open("a", encoding="utf-8") as fh:
        fh.write('{"schema":"node.v1","node_id":"N-0009","not":"a real field"}\n')
    env = session("check", expect=1)
    assert any("N-0009" in e or "node.v1" in e for e in env["errors"])

    # remove the invalid line; a perfectly-valid forged node passes (the limit)
    good_lines = [l for l in nodes_file.read_text().splitlines() if "N-0009" not in l]
    nodes_file.write_text("\n".join(good_lines) + "\n", encoding="utf-8")
    forged = {"schema": "node.v1", "node_id": "N-0008", "parent_id": "N-0001",
              "kind": "viewpoint", "statement": "forged but schema-valid",
              "why_helps_parent": None, "orientation": None, "status": "open",
              "status_note": None, "promotion_note": None, "stuck_reason": None,
              "revises": None, "created_at": "2026-07-09T12:00:00Z", "created_by": "attacker"}
    with nodes_file.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(forged) + "\n")
    # KNOWN LIMIT: indistinguishable from a legitimate nd write -> check passes
    assert session("check")["data"]["hard"] == []


# (TC-E) a non-JSON corrupt line surfaces as a clean located error, not a crash
def test_probe_corrupt_jsonl_line_is_located_not_a_crash(session, tmp_path):
    _setup(session, tmp_path)
    nodes_file = session.root / "sessions" / "t" / "tree" / "nodes.jsonl"
    with nodes_file.open("a", encoding="utf-8") as fh:
        fh.write("{ this is not valid json\n")
    env = session("check", expect=1)
    assert any("corrupt JSONL line" in e and "tree/nodes.jsonl:" in e
               for e in env["errors"])


# (e) empty and binary ingests are refused
def test_probe_empty_and_binary_ingest_rejected(session, tmp_path):
    _setup(session, tmp_path)
    empty = tmp_path / "empty.txt"; empty.write_text("", encoding="utf-8")
    env = session("docs", "ingest", "--file", write_json(tmp_path / "e2.json", {
        "kind": "web", "title": "E", "url": None, "text_file": str(empty),
        "summary": "s", "bindings": [{"node_id": "N-0002", "relation": "context"}]}),
        expect=1)
    assert any("empty" in e for e in env["errors"])

    binf = tmp_path / "b.bin"; binf.write_bytes(b"PK\x03\x04\x00\x00rubbish")
    env = session("docs", "ingest", "--file", write_json(tmp_path / "e3.json", {
        "kind": "web", "title": "B", "url": None, "text_file": str(binf),
        "summary": "s", "bindings": [{"node_id": "N-0002", "relation": "context"}]}),
        expect=1)
    assert any("binary" in e for e in env["errors"])
