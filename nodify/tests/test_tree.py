"""Tree discipline: root uniqueness, kind rules, budgets, transitions,
promotion, conclude flow. All through the CLI (the only supported writer)."""

from __future__ import annotations

from tests.conftest import write_json


def _seed(session):
    session("add", "--statement", "崩溃由连接池耗尽引起")            # N-0001 root
    session("add", "--parent", "N-0001", "--statement", "崩溃时刻池是否满?",
            "--why", "直接检验")                                       # N-0002
    session("add", "--parent", "N-0001", "--statement", "有无不经过池的崩溃?",
            "--orientation", "adversarial")                            # N-0003
    return session


def test_root_is_unique_and_viewpoint(session):
    _seed(session)
    env = session("add", "--statement", "第二个根", expect=1)
    assert any("root already exists" in e for e in env["errors"])


def test_first_child_auto_expands_parent(session):
    _seed(session)
    env = session("show", "N-0001")
    assert env["data"]["node"]["status"] == "expanding"
    assert env["data"]["children"] == ["N-0002", "N-0003"]


def test_viewpoint_children_must_be_viewpoints(session):
    _seed(session)
    env = session("add", "--parent", "N-0001", "--kind", "claim",
                  "--statement", "x", expect=1)
    assert any("promotion re-kinds" in e for e in env["errors"])


def test_claim_children_are_claims_with_auto_split_note(session):
    _seed(session)
    session("promote", "N-0002", "--note", "无新方向;工具可解")
    session("add", "--parent", "N-0002", "--statement", "池上限是多少?")
    env = session("show", "N-0004")
    node = env["data"]["node"]
    assert node["kind"] == "claim"
    assert node["promotion_note"] == "split from N-0002"


def test_budget_max_children(session):
    _seed(session)
    for i in range(3):  # already 2 children; default max 5
        session("add", "--parent", "N-0001", "--statement", f"方向{i}")
    env = session("add", "--parent", "N-0001", "--statement", "超了", expect=1)
    assert any("max_children" in e for e in env["errors"])


def test_budget_max_depth(ws):
    ws("init", "t", "--question", "q?", "--budget", "max_depth=2")
    ws("add", "--statement", "根")
    ws("add", "--parent", "N-0001", "--statement", "一层")
    ws("add", "--parent", "N-0002", "--statement", "二层")
    env = ws("add", "--parent", "N-0003", "--statement", "三层", expect=1)
    assert any("max_depth" in e for e in env["errors"])


def test_promote_requires_note_and_open_claim_budget(ws):
    ws("init", "t", "--question", "q?", "--budget", "max_open_claims=1")
    ws("add", "--statement", "根")
    ws("add", "--parent", "N-0001", "--statement", "a")
    ws("add", "--parent", "N-0001", "--statement", "b")
    ws("promote", "N-0002", "--note", "穷尽")
    env = ws("promote", "N-0003", "--note", "穷尽", expect=1)
    assert any("max_open_claims" in e for e in env["errors"])


def test_status_transitions_legal_and_note_required(session):
    _seed(session)
    session("promote", "N-0002", "--note", "n")
    env = session("set-status", "N-0002", "concluded", expect=1)       # not legal directly
    assert any("illegal transition" in e for e in env["errors"])
    env = session("set-status", "N-0003", "retired", expect=2)         # note required
    assert any("--note is required" in e for e in env["errors"])
    session("set-status", "N-0003", "retired", "--note", "与N-0002重复")
    env = session("set-status", "N-0002", "investigating")
    assert env["data"]["node"]["status"] == "investigating"
    env = session("set-status", "N-0002", "stuck", "--note", "证据不足", expect=2)
    assert any("--reason" in e for e in env["errors"])
    session("set-status", "N-0002", "stuck", "--note", "证据不足",
            "--reason", "evidence")


def test_conclude_flow_and_dangling_refs(session, tmp_path):
    _seed(session)
    session("promote", "N-0002", "--note", "n")
    good = write_json(tmp_path / "s.json", {
        "node_id": "N-0002", "lean": "supports", "summary": "池在崩溃前60s打满",
        "confidence": "high",
        "based_on": {"children": [], "evidence": [
            {"title": "app.log 崩溃窗口", "locator": "logs/app.log:1201-1260"}]},
    })
    env = session("conclude", "--file", good)
    syn = env["data"]["synthesis"]
    assert syn["synthesis_id"] == "SYN-0001"
    assert syn["based_on"]["evidence"][0]["ref_id"] == "E-01"
    assert session("show", "N-0002")["data"]["node"]["status"] == "concluded"

    bad = write_json(tmp_path / "b.json", {
        "node_id": "N-0002", "lean": "supports", "summary": "x",
        "confidence": "low",
        "based_on": {"children": ["N-9999"], "evidence": []},
    })
    env = session("conclude", "--file", bad, expect=1)
    assert any("unknown node: N-9999" in e for e in env["errors"])


def test_conclude_viewpoint_synthesizes_it(session, tmp_path):
    _seed(session)
    f = write_json(tmp_path / "v.json", {
        "node_id": "N-0001", "lean": "mixed", "summary": "部分成立",
        "confidence": "medium",
        "based_on": {"children": ["N-0002", "N-0003"], "evidence": []},
    })
    session("conclude", "--file", f)
    assert session("show", "N-0001")["data"]["node"]["status"] == "synthesized"
    # a new direction can reopen it
    session("set-status", "N-0001", "expanding")
