"""Iteration 1 (Opus): R1 final.md staleness, R3 docs bind, R5 retire hygiene,
R6 nd revise, R7 brief activity line. Sessions from the fixture are on the
current schema set (v3), so docs/article commands work directly."""

from __future__ import annotations

from tests.conftest import write_json

ARTICLE = "The pool hit its 200-connection ceiling at 02:59, before the crash."


def _doc(session, tmp_path, node="N-0002", fname="a.txt", text=ARTICLE,
         relation="supports", expect=0):
    src = tmp_path / fname
    src.write_text(text, encoding="utf-8")
    return session("docs", "ingest", "--file", write_json(tmp_path / f"{fname}.json", {
        "kind": "report", "title": "监控周报", "url": "https://ex.org/w",
        "text_file": str(src), "summary": "池打满记录",
        "bindings": [{"node_id": node, "relation": relation}]}), expect=expect)


def _article_base(session, tmp_path):
    session("add", "--statement", "崩溃由连接池耗尽引起")            # N-0001
    session("add", "--parent", "N-0001", "--statement", "池是否打满?")  # N-0002
    _doc(session, tmp_path)                                         # DOC-0001 -> N-0002
    session("conclude", "--file", write_json(tmp_path / "s.json", {
        "node_id": "N-0001", "lean": "supports", "summary": "池耗尽在先",
        "confidence": "medium",
        "based_on": {"children": ["N-0002"], "evidence": []}}))     # SYN-0001
    session("article", "outline", "--file", write_json(tmp_path / "ol.json", {
        "title": "崩溃根因", "thesis": "池耗尽引起", "grounded_in": ["SYN-0001"],
        "sections": [{"section_id": "S-01", "title": "证据", "role": "evidence",
                       "node_ids": ["N-0002"], "intent": "证据"}],
        "excluded": []}))
    return session


# --- R1: final.md staleness ------------------------------------------------

def test_r1_stale_final_md_is_hard_until_reassembled(session, tmp_path):
    _article_base(session, tmp_path)
    a = tmp_path / "a.md"
    a.write_text("据周报 (cite: DOC-0001) 池已打满。", encoding="utf-8")
    session("article", "section", "--id", "S-01", "--file", str(a))
    session("article", "assemble")
    session("check")                       # clean right after assemble

    # change the section content without re-assembling -> final.md is stale
    b = tmp_path / "b.md"
    b.write_text("完全不同的正文 (cite: DOC-0001)。", encoding="utf-8")
    session("article", "section", "--id", "S-01", "--file", str(b))
    env = session("check", expect=1)
    assert any("final.md is stale" in e for e in env["errors"])

    session("article", "assemble")         # re-assemble clears it
    env = session("check")
    assert env["data"]["hard"] == []


def test_r1_no_false_positive_when_content_unchanged(session, tmp_path):
    _article_base(session, tmp_path)
    a = tmp_path / "a.md"
    a.write_text("据周报 (cite: DOC-0001) 池已打满。", encoding="utf-8")
    session("article", "section", "--id", "S-01", "--file", str(a))
    session("article", "assemble")
    # re-register identical content -> output identical -> NOT stale
    session("article", "section", "--id", "S-01", "--file", str(a))
    assert session("check")["data"]["hard"] == []


# --- R3: docs bind ---------------------------------------------------------

def test_r3_bind_existing_doc_without_reingest(session, tmp_path):
    session("add", "--statement", "根")                            # N-0001
    session("add", "--parent", "N-0001", "--statement", "子A")      # N-0002
    session("add", "--parent", "N-0001", "--statement", "子B",
            "--orientation", "adversarial")                        # N-0003
    _doc(session, tmp_path)                                         # DOC-0001 -> N-0002
    env = session("docs", "bind", "DOC-0001", "--node", "N-0003", "--relation", "refutes")
    assert env["data"]["entry"]["doc_id"] == "DOC-0001"
    assert {(b["node_id"], b["relation"]) for b in env["data"]["entry"]["bindings"]} \
        == {("N-0002", "supports"), ("N-0003", "refutes")}
    # duplicate bind = no-op warning
    env = session("docs", "bind", "DOC-0001", "--node", "N-0003", "--relation", "refutes")
    assert any("unchanged" in w for w in env["warnings"])
    # errors
    assert any("unknown doc" in e for e in
               session("docs", "bind", "DOC-9999", "--node", "N-0002",
                       "--relation", "supports", expect=1)["errors"])
    assert any("unknown node" in e for e in
               session("docs", "bind", "DOC-0001", "--node", "N-9999",
                       "--relation", "supports", expect=1)["errors"])
    assert any("relation must be" in e for e in
               session("docs", "bind", "DOC-0001", "--node", "N-0002",
                       "--relation", "cites", expect=2)["errors"])


# --- R5: retire hygiene ----------------------------------------------------

def test_r5_active_node_under_retired_ancestor_is_soft(session):
    session("add", "--statement", "根")                            # N-0001
    session("add", "--parent", "N-0001", "--statement", "支线")     # N-0002 (open->expanding)
    session("add", "--parent", "N-0002", "--statement", "支线下的活")  # N-0003 (open)
    session("set-status", "N-0002", "retired", "--note", "此路不通")
    soft = session("check")["data"]["soft"]
    assert any("N-0003" in w and "retired ancestor N-0002" in w for w in soft)
    # retiring the orphan too clears the hygiene warning
    session("set-status", "N-0003", "retired", "--note", "随父退")
    soft = session("check")["data"]["soft"]
    assert not any("active under" in w for w in soft)


# --- R6: nd revise ---------------------------------------------------------

def test_r6_revise_mints_new_retires_old_warns_unmigrated(session, tmp_path):
    session("add", "--statement", "根")                            # N-0001
    session("add", "--parent", "N-0001", "--statement", "宽泛论点?")   # N-0002
    session("promote", "N-0002", "--note", "穷尽")                  # N-0002 -> claim
    session("add", "--parent", "N-0002", "--statement", "子论点")   # N-0003 (claim split)
    _doc(session, tmp_path)                                         # DOC-0001 -> N-0002

    env = session("revise", "N-0002", "--statement", "收窄后的论点", "--note", "被证据收窄")
    new_id = env["data"]["new"]["node_id"]
    assert env["data"]["new"]["revises"] == "N-0002"
    assert env["data"]["new"]["kind"] == "claim" and env["data"]["new"]["status"] == "pending"
    assert env["data"]["new"]["statement"] == "收窄后的论点"
    assert env["data"]["retired"]["status"] == "retired"
    assert f"revised → {new_id}" in env["data"]["retired"]["status_note"]
    assert any("N-0003" in w and "NOT migrated" in w for w in env["warnings"])
    assert any("DOC-0001" in w for w in env["warnings"])

    # revises is not dangling (old node still exists); check has no hard error
    assert session("check")["data"]["hard"] == []
    # revising a retired node is refused
    assert any("already retired" in e for e in
               session("revise", "N-0002", "--statement", "x", expect=1)["errors"])


def test_r6_cannot_revise_the_root(session):
    session("add", "--statement", "根论题")
    env = session("revise", "N-0001", "--statement", "重述根", expect=1)
    assert any("cannot revise the root" in e for e in env["errors"])
    # the tree stays single-rooted and clean
    assert session("check")["data"]["hard"] == []


# --- R7: brief activity line -----------------------------------------------

def test_r7_brief_shows_activity(session, tmp_path):
    session("add", "--statement", "根")
    session("add", "--parent", "N-0001", "--statement", "子")
    _doc(session, tmp_path)
    session("conclude", "--file", write_json(tmp_path / "s.json", {
        "node_id": "N-0001", "lean": "open", "summary": "s", "confidence": "low",
        "based_on": {"children": ["N-0002"], "evidence": []}}))
    text = session("brief")["data"]["brief"]
    assert "ACTIVITY:" in text
    assert "adds" in text and "1 concludes" in text and "1 ingests" in text
