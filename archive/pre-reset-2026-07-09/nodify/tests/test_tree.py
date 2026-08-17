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


def test_kind_is_free_claim_allowed_directly_under_viewpoint(session):
    # loosened v0.2: no forced promote ceremony — a claim may be added straight
    # under a viewpoint (diverge OR decompose, the model's call).
    _seed(session)
    env = session("add", "--parent", "N-0001", "--kind", "claim", "--statement", "x")
    assert env["ok"] is True
    node = session("show", env["data"]["nodes"][0]["node_id"])["data"]["node"]
    assert node["kind"] == "claim"
    assert node["promotion_note"] == "claim under N-0001"


def test_promote_still_available_and_requires_note(session):
    _seed(session)
    env = session("promote", "N-0002", "--note", "", expect=2)  # empty note -> usage
    assert any("note" in e for e in env["errors"])
    env = session("promote", "N-0002", "--note", "无新方向;工具可解")
    assert env["data"]["node"]["kind"] == "claim"


def test_budgets_are_soft_guardrails_not_gates(session):
    # loosened v0.2: over-budget WRITES SUCCEED; nd check surfaces them as soft.
    _seed(session)                                    # N-0001 already has 2 children
    for i in range(5):                                # default max_children=5 -> 7 total
        assert session("add", "--parent", "N-0001", "--statement", f"方向{i}")["ok"]
    env = session("check")                            # no hard error despite over-width
    assert env["ok"] is True and env["data"]["hard"] == []
    assert any("max_children" in w for w in env["data"]["soft"])


def test_budget_max_depth_is_soft(ws):
    ws("init", "t", "--question", "q?", "--budget", "max_depth=2")
    ws("add", "--statement", "根")
    ws("add", "--parent", "N-0001", "--statement", "一层")
    ws("add", "--parent", "N-0002", "--statement", "二层")
    assert ws("add", "--parent", "N-0003", "--statement", "三层")["ok"]   # succeeds now
    env = ws("check")
    assert env["ok"] is True
    assert any("max_depth" in w for w in env["data"]["soft"])


def test_reframe_updates_statement_in_place_including_root(session):
    _seed(session)
    env = session("reframe", "N-0001", "--statement", "崩溃的真正根因(重构框架)",
                  "--note", "证据把问题变宽了")
    assert env["data"]["node"]["node_id"] == "N-0001"                 # same id
    assert env["data"]["node"]["statement"] == "崩溃的真正根因(重构框架)"
    assert session("show", "N-0001")["data"]["children"] == ["N-0002", "N-0003"]  # kept
    # revise on the root still refuses and points to reframe
    env = session("revise", "N-0001", "--statement", "x", expect=1)
    assert any("reframe" in e for e in env["errors"])


def test_reparent_moves_subtree_children_and_guards_cycles(session):
    _seed(session)
    session("add", "--parent", "N-0002", "--statement", "子")          # N-0004 under N-0002
    env = session("reparent", "N-0004", "--to", "N-0003", "--note", "更契合对立线")
    assert env["data"]["node"]["parent_id"] == "N-0003"
    assert "N-0004" in session("show", "N-0003")["data"]["children"]
    assert "N-0004" not in session("show", "N-0002")["data"]["children"]
    # cycle guard: N-0003 cannot move under its new descendant N-0004
    env = session("reparent", "N-0003", "--to", "N-0004", expect=1)
    assert any("cycle" in e or "descendant" in e for e in env["errors"])
    # the root cannot be reparented
    env = session("reparent", "N-0001", "--to", "N-0002", expect=1)
    assert any("root" in e for e in env["errors"])


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
