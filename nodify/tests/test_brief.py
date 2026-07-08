"""nd brief: the recovery hard-target (P14) — under a generous budget the brief
carries everything needed to resume; under a tight budget it truncates HONESTLY
(marker, never silence) and stays within max_chars; rendering is deterministic."""

from __future__ import annotations

from tests.conftest import write_json


def _build(session, tmp_path):
    session("add", "--statement", "崩溃由连接池耗尽引起")
    session("add", "--parent", "N-0001", "--statement", "崩溃时刻池是否满?")
    session("add", "--parent", "N-0001", "--statement", "有无绕过池的崩溃路径?",
            "--orientation", "adversarial")
    session("promote", "N-0002", "--note", "n")
    session("set-status", "N-0002", "investigating")
    session("set-status", "N-0002", "stuck", "--note", "日志缺失", "--reason", "evidence")
    f = write_json(tmp_path / "s.json", {
        "node_id": "N-0001", "lean": "open", "summary": "待N-0002解锁",
        "confidence": "low", "based_on": {"children": ["N-0002"], "evidence": []},
    })
    session("conclude", "--file", f)


def test_brief_carries_recovery_state(session, tmp_path):
    _build(session, tmp_path)
    text = session("brief")["data"]["brief"]
    assert "为什么服务在周二凌晨崩溃?" in text                    # question
    assert "有无绕过池的崩溃路径?" in text                        # frontier statement
    assert "[adversarial]" in text
    assert "stuck(evidence): 日志缺失" in text                    # stuck + reason
    assert "待N-0002解锁" in text                                  # conclusion
    assert "[truncated" not in text


def test_brief_is_bounded_and_truncates_honestly(session, tmp_path):
    _build(session, tmp_path)
    env = session("brief", "--max-chars", "260")
    text = env["data"]["brief"]
    assert len(text) <= 260 + 1
    assert "[truncated" in text


def test_brief_is_deterministic(session, tmp_path):
    _build(session, tmp_path)
    a = session("brief")["data"]["brief"]
    b = session("brief")["data"]["brief"]
    assert a == b
