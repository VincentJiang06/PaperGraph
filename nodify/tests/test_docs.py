"""V2 docs store: schema-set gating + upgrade, ingest dedup, verbatim quote
floor (P7 hard), tree-distance recall ordering (P8: recall is a pure read)."""

from __future__ import annotations

import json

from nodify import schemas
from tests.conftest import write_json

ARTICLE = ("The pool reached its 200-connection ceiling at 02:59, sixty seconds "
           "before the crash. Every request after that queued indefinitely.")


def _tree(session):
    session("add", "--statement", "崩溃由连接池耗尽引起")            # N-0001
    session("add", "--parent", "N-0001", "--statement", "池是否在崩溃前打满?")  # N-0002
    session("add", "--parent", "N-0001", "--statement", "有无绕过池的路径?",
            "--orientation", "adversarial")                            # N-0003
    session("add", "--parent", "N-0002", "--statement", "池上限配置是多少?")   # N-0004 (under 2)


def _ingest(session, tmp_path, node="N-0002", title="监控周报", fname="a.txt",
            text=ARTICLE, expect=0):
    src = tmp_path / fname
    src.write_text(text, encoding="utf-8")
    f = write_json(tmp_path / f"{fname}.entry.json", {
        "kind": "report", "title": title, "url": "https://example.org/weekly",
        "text_file": str(src), "summary": "崩溃前60秒池打满的监控记录",
        "bindings": [{"node_id": node, "relation": "supports"}],
    })
    return session("docs", "ingest", "--file", f, expect=expect)


def test_v1_session_is_gated_and_upgrade_unlocks(session, tmp_path):
    # forge a v1 session (old hash) and confirm docs are refused with a hint
    sess_file = session.root / "sessions" / "t" / "session.json"
    rec = json.loads(sess_file.read_text())
    rec["schema_set_hash"] = schemas.schema_set_hash("v1")
    sess_file.write_text(json.dumps(rec, ensure_ascii=False))
    _tree(session)
    env = _ingest(session, tmp_path, expect=1)
    assert any("nd upgrade" in e for e in env["errors"])

    env = session("upgrade")
    assert env["data"]["from"] == "v1" and env["data"]["to"] == "v2"
    env = session("upgrade")            # idempotent
    assert env["data"]["from"] == "v2"
    _ingest(session, tmp_path)          # now allowed


def test_ingest_dedup_merges_bindings(session, tmp_path):
    _tree(session)
    env = _ingest(session, tmp_path)
    assert env["data"]["entry"]["doc_id"] == "DOC-0001"
    # same content bound to another node: no new doc, binding merged
    env = _ingest(session, tmp_path, node="N-0003", fname="b.txt")
    assert env["data"]["entry"]["doc_id"] == "DOC-0001"
    assert any("already archived" in w for w in env["warnings"])
    assert {b["node_id"] for b in env["data"]["entry"]["bindings"]} == {"N-0002", "N-0003"}
    # exact duplicate (same content, same binding): unchanged
    env = _ingest(session, tmp_path, fname="c.txt")
    assert any("unchanged" in w for w in env["warnings"])


def test_ingest_refuses_dangling_binding(session, tmp_path):
    _tree(session)
    env = _ingest(session, tmp_path, node="N-9999", expect=1)
    assert any("unknown node" in e for e in env["errors"])


def test_quote_floor_verbatim_passes_fake_degrades(session, tmp_path):
    _tree(session)
    _ingest(session, tmp_path)
    good = write_json(tmp_path / "g.json", {
        "node_id": "N-0002", "lean": "supports", "summary": "打满在先",
        "confidence": "high",
        "based_on": {"children": [], "evidence": [
            {"title": "监控周报", "doc_id": "DOC-0001",
             "quote": "The pool reached its   200-connection ceiling at 02:59"}]},
    })
    env = session("conclude", "--file", good)
    assert env["warnings"] == []        # whitespace-normalized verbatim: kept
    assert env["data"]["synthesis"]["schema"] == "synthesis.v2"
    assert env["data"]["synthesis"]["based_on"]["evidence"][0]["quote"] is not None

    fake = write_json(tmp_path / "f.json", {
        "node_id": "N-0002", "lean": "supports", "summary": "编造引文",
        "confidence": "low",
        "based_on": {"children": [], "evidence": [
            {"title": "监控周报", "doc_id": "DOC-0001",
             "quote": "the pool NEVER reached its ceiling"}]},
    })
    env = session("conclude", "--file", fake)
    assert any("degraded to paraphrase" in w for w in env["warnings"])
    assert env["data"]["synthesis"]["based_on"]["evidence"][0]["quote"] is None

    dangling = write_json(tmp_path / "d.json", {
        "node_id": "N-0002", "lean": "supports", "summary": "x", "confidence": "low",
        "based_on": {"children": [], "evidence": [
            {"title": "t", "doc_id": "DOC-0042"}]},
    })
    env = session("conclude", "--file", dangling, expect=1)
    assert any("unknown doc" in e for e in env["errors"])


def test_check_catches_archive_tampering(session, tmp_path):
    _tree(session)
    _ingest(session, tmp_path)
    good = write_json(tmp_path / "g.json", {
        "node_id": "N-0002", "lean": "supports", "summary": "s", "confidence": "low",
        "based_on": {"children": [], "evidence": [
            {"title": "监控周报", "doc_id": "DOC-0001",
             "quote": "sixty seconds before the crash"}]},
    })
    session("conclude", "--file", good)
    session("check")
    store_file = session.root / "sessions" / "t" / "docs" / "store" / "DOC-0001.txt"
    store_file.write_text("rewritten archive", encoding="utf-8")
    env = session("check", expect=1)
    assert any("no longer matches the archived text" in e for e in env["errors"])


def test_recall_orders_by_tree_distance_then_lexical(session, tmp_path):
    _tree(session)
    # bind three docs at different tree distances from the query node N-0002
    _ingest(session, tmp_path, node="N-0002", title="self doc pool ceiling",
            fname="s.txt", text="text self " + ARTICLE)
    _ingest(session, tmp_path, node="N-0004", title="descendant doc config",
            fname="d.txt", text="text descendant limits")
    _ingest(session, tmp_path, node="N-0003", title="sibling doc bypass",
            fname="x.txt", text="text sibling routes")
    env = session("recall", "--node", "N-0002", "--query", "pool ceiling 池")
    hits = env["data"]["recall"]["hits"]
    assert [h["distance"] for h in hits] == ["self", "descendant", "sibling"]
    assert hits[0]["doc_id"] == "DOC-0001"
    assert hits[0]["text_file"].startswith("docs/store/")
    # recall wrote NOTHING (pure read): only the event log grew
    idx = (session.root / "sessions" / "t" / "docs" / "index.jsonl").read_text()
    assert idx.count("\n") == 3


def test_for_node_includes_ancestors(session, tmp_path):
    _tree(session)
    _ingest(session, tmp_path, node="N-0001", title="root doc", fname="r.txt",
            text="root-level background")
    env = session("docs", "for-node", "N-0004")
    assert [e["doc_id"] for e in env["data"]["entries"]] == ["DOC-0001"]
