"""V3 article layer: grounded outlines, cite resolution (hard), mechanical
references, check integration. The editorial content is the model's; the
traceability is ours."""

from __future__ import annotations

from tests.conftest import write_json

ARTICLE = ("The pool reached its 200-connection ceiling at 02:59, sixty seconds "
           "before the crash.")


def _prepared(session, tmp_path):
    session("add", "--statement", "崩溃由连接池耗尽引起")            # N-0001
    session("add", "--parent", "N-0001", "--statement", "池是否在崩溃前打满?")  # N-0002
    src = tmp_path / "a.txt"; src.write_text(ARTICLE, encoding="utf-8")
    session("docs", "ingest", "--file", write_json(tmp_path / "e.json", {
        "kind": "report", "title": "监控周报", "url": "https://example.org/w",
        "text_file": str(src), "summary": "池打满记录",
        "bindings": [{"node_id": "N-0002", "relation": "supports"}]}))
    session("conclude", "--file", write_json(tmp_path / "s.json", {
        "node_id": "N-0001", "lean": "supports", "summary": "池耗尽在先",
        "confidence": "medium",
        "based_on": {"children": ["N-0002"], "evidence": []}}))
    return session


def _outline(tmp_path, grounded=("SYN-0001",), node_ids=("N-0001",)):
    return write_json(tmp_path / "ol.json", {
        "title": "连接池耗尽与周二凌晨崩溃", "thesis": "崩溃由池耗尽引起",
        "grounded_in": list(grounded),
        "sections": [
            {"section_id": "S-01", "title": "引言", "role": "introduction",
             "node_ids": list(node_ids), "intent": "问题与论题"},
            {"section_id": "S-02", "title": "证据", "role": "evidence",
             "node_ids": ["N-0002"], "intent": "监控证据"}],
        "excluded": []})


def test_outline_requires_grounding(session, tmp_path):
    _prepared(session, tmp_path)
    env = session("article", "outline", "--file",
                  _outline(tmp_path, grounded=("SYN-0042",)), expect=1)
    assert any("unknown synthesis" in e for e in env["errors"])
    env = session("article", "outline", "--file", _outline(tmp_path))
    assert env["data"]["outline"]["outline_id"] == "OL-01"


def test_section_cite_resolution_and_assemble(session, tmp_path):
    _prepared(session, tmp_path)
    session("article", "outline", "--file", _outline(tmp_path))

    bad = tmp_path / "bad.md"
    bad.write_text("据监控 (cite: DOC-0042) 池已打满。", encoding="utf-8")
    env = session("article", "section", "--id", "S-02", "--file", str(bad), expect=1)
    assert any("does not resolve" in e for e in env["errors"])

    good = tmp_path / "good.md"
    good.write_text("据监控周报 (cite: DOC-0001),池在崩溃前打满。", encoding="utf-8")
    env = session("article", "section", "--id", "S-02", "--file", str(good))
    assert env["data"]["section"]["cites"] == ["DOC-0001"]

    intro = tmp_path / "intro.md"
    intro.write_text("本文论证崩溃根因。", encoding="utf-8")
    env = session("article", "section", "--id", "S-01", "--file", str(intro))
    # F7: role-aware — an introduction citing nothing is fine, no warning
    assert not any("cites nothing" in w for w in env["warnings"])

    # but an evidence-role section citing nothing DOES warn
    empty_ev = tmp_path / "ev2.md"
    empty_ev.write_text("空口无凭的证据节。", encoding="utf-8")
    env = session("article", "section", "--id", "S-02", "--file", str(empty_ev))
    assert any("cites nothing" in w for w in env["warnings"])
    # restore the cited version for assemble below
    env = session("article", "section", "--id", "S-02", "--file", str(good))

    env = session("article", "assemble")
    assert env["data"]["references"] == ["DOC-0001"]
    final = (session.root / "sessions" / "t" / "article" / "final.md").read_text()
    assert "## References" in final and "[DOC-0001] 监控周报" in final
    assert final.index("引言") < final.index("证据")


def test_check_folds_article_layer(session, tmp_path):
    _prepared(session, tmp_path)
    session("article", "outline", "--file", _outline(tmp_path))
    soft = session("check")["data"]["soft"]
    assert any("no registered prose" in w for w in soft)
    # prose file deleted after registration = hard
    good = tmp_path / "g.md"
    good.write_text("x (cite: DOC-0001)", encoding="utf-8")
    session("article", "section", "--id", "S-02", "--file", str(good))
    (session.root / "sessions" / "t" / "article" / "S-02.md").unlink()
    env = session("check", expect=1)
    assert any("prose file missing" in e for e in env["errors"])


def test_v2_session_gated_from_article(session, tmp_path):
    import json
    from nodify import schemas
    _prepared(session, tmp_path)
    sess_file = session.root / "sessions" / "t" / "session.json"
    rec = json.loads(sess_file.read_text())
    rec["schema_set_hash"] = schemas.schema_set_hash("v2")
    sess_file.write_text(json.dumps(rec, ensure_ascii=False))
    env = session("article", "outline", "--file", _outline(tmp_path), expect=1)
    assert any("nd upgrade" in e for e in env["errors"])


def test_live_test_1_fixes(session, tmp_path):
    """Audit #1 regressions: F1 session_dir in envelopes, F2 nd schema,
    F4 heading warning, F6 CJK word count."""
    env = session("brief")
    assert env["data"]["session_dir"].endswith("sessions/t")     # F1

    env = session("schema", "conclude")                          # F2
    assert env["data"]["name"] == "synthesis.v2"
    assert env["data"]["payload_example"]["based_on"]["evidence"][0]["doc_id"]
    env = session("schema", "nope", expect=2)
    assert any("unknown schema" in e for e in env["errors"])

    _prepared(session, tmp_path)
    session("article", "outline", "--file", _outline(tmp_path))
    d = tmp_path / "h.md"
    d.write_text("## 我自带标题\n\n中文正文四十个字左右 (cite: DOC-0001)。",
                 encoding="utf-8")
    env = session("article", "section", "--id", "S-02", "--file", str(d))
    assert any("markdown heading" in w for w in env["warnings"])  # F4
    assert env["data"]["section"]["word_count"] > 7               # F6 (CJK chars count)


def test_live_test_1_quote_unicode_fold(session, tmp_path):
    """F5: a curly-apostrophe source matches an ASCII-apostrophe quote."""
    session("add", "--statement", "根")
    src = tmp_path / "u.txt"
    src.write_text("The lab’s data — released in 2025 — shows it.",
                   encoding="utf-8")
    from tests.conftest import write_json
    session("docs", "ingest", "--file", write_json(tmp_path / "e.json", {
        "kind": "web", "title": "T", "url": "https://x", "text_file": str(src),
        "summary": "s", "bindings": [{"node_id": "N-0001", "relation": "supports"}]}))
    env = session("conclude", "--file", write_json(tmp_path / "s.json", {
        "node_id": "N-0001", "lean": "supports", "summary": "s", "confidence": "low",
        "based_on": {"children": [], "evidence": [
            {"title": "T", "doc_id": "DOC-0001",
             "quote": "The lab's data - released in 2025 - shows it."}]}}))
    assert env["warnings"] == []
    assert env["data"]["synthesis"]["based_on"]["evidence"][0]["quote"] is not None
