"""The trace log (design §4): every command — mutating, read-only, or failed —
appends exactly one event. Retrofitting tracing is impossible; it ships in V1."""

from __future__ import annotations

import json


def _events(root):
    path = root / "sessions" / "t" / "tree" / "events.jsonl"
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def test_every_command_logs_exactly_one_event(session):
    session("add", "--statement", "根")                       # mutating
    session("tree")                                            # read-only
    session("show", "N-9999", expect=1)                        # failed
    evs = _events(session.root)
    # init, add, tree, show(FAILED) = 4 events
    assert [e["command"] for e in evs] == ["init", "add", "tree", "show"]
    assert [e["mutating"] for e in evs] == [True, True, False, False]
    assert evs[1]["touched"] == ["N-0001"]
    assert evs[3]["summary"].startswith("FAILED:")
    assert [e["event_id"] for e in evs] == [f"EV-{i:06d}" for i in range(1, 5)]


def test_log_command_returns_tail(session):
    session("add", "--statement", "根")
    env = session("log", "--tail", "2")
    cmds = [e["command"] for e in env["data"]["events"]]
    assert cmds == ["init", "add"]  # the log event itself is appended after
