"""nd check: hard = broken structure (exit 1); soft = visible laziness (exit 0).
Hard states are constructed by hand-appending records — the CLI itself refuses
to create them (that refusal is tested in test_tree)."""

from __future__ import annotations

import json

from tests.conftest import write_json


def _append(root, rel, record):
    path = root / "sessions" / "t" / rel
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


NODE = {
    "schema": "node.v1", "node_id": "N-0099", "parent_id": "N-4242",
    "kind": "viewpoint", "statement": "孤儿", "why_helps_parent": None,
    "orientation": None, "status": "open", "status_note": None,
    "promotion_note": None, "stuck_reason": None, "revises": None,
    "created_at": "2026-07-09T12:00:00Z", "created_by": "test",
}


def test_dangling_parent_is_hard(session):
    session("add", "--statement", "根")
    _append(session.root, "tree/nodes.jsonl", NODE)
    env = session("check", expect=1)
    assert any("dangling parent_id" in e for e in env["errors"])


def test_soft_warnings_visible_laziness(session, tmp_path):
    session("add", "--statement", "根")
    session("add", "--parent", "N-0001", "--statement", "只有中立方向")
    f = write_json(tmp_path / "s.json", {
        "node_id": "N-0002", "lean": "open", "summary": "无依据的结论",
        "confidence": "low", "based_on": {"children": [], "evidence": []},
    })
    session("conclude", "--file", f)
    env = session("check")
    soft = env["data"]["soft"]
    assert any("without an adversarial direction" in w for w in soft)
    assert any("based_on is empty" in w for w in soft)
    assert env["data"]["hard"] == []


def test_evidence_without_pointer_is_soft(session, tmp_path):
    session("add", "--statement", "根")
    f = write_json(tmp_path / "s.json", {
        "node_id": "N-0001", "lean": "supports", "summary": "s",
        "confidence": "low",
        "based_on": {"children": [], "evidence": [{"title": "口口相传"}]},
    })
    session("conclude", "--file", f)
    soft = session("check")["data"]["soft"]
    assert any("neither url nor locator" in w for w in soft)
