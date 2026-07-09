"""Closed CLI surface (design §5) mirrored bidirectionally + envelope contract."""

from __future__ import annotations

import typer

from nodify.cli import app

CLOSED_COMMANDS = {
    "init", "add", "promote", "set-status", "revise", "conclude",
    "brief", "show", "tree", "log", "check", "export",
    "upgrade", "recall", "docs ingest", "docs bind", "docs for-node",
    "article outline", "article section", "article assemble", "article show",
    "schema",
}

ENVELOPE_KEYS = {"ok", "command", "data", "errors", "warnings"}


def _walk(cmd, prefix):
    subs = getattr(cmd, "commands", None)
    if not subs:
        return {" ".join(prefix)}
    out = set()
    for name, sub in subs.items():
        out |= _walk(sub, prefix + [name])
    return out


def test_command_set_matches_closed_list_both_directions():
    exposed = _walk(typer.main.get_command(app), [])
    assert exposed == CLOSED_COMMANDS, {
        "unexpected": sorted(exposed - CLOSED_COMMANDS),
        "missing": sorted(CLOSED_COMMANDS - exposed)}


def test_every_command_emits_one_envelope(session):
    env = session("tree")
    assert set(env.keys()) == ENVELOPE_KEYS
    env = session("show", "N-9999", expect=1)   # domain failure still enveloped
    assert set(env.keys()) == ENVELOPE_KEYS and env["ok"] is False


def test_missing_session_is_usage_error(ws):
    env = ws("tree", expect=1)
    assert env["ok"] is False
    assert any("no session" in e for e in env["errors"])


def test_double_init_refused(session):
    env = session("init", "t", "--question", "again?", expect=1)
    assert any("already exists" in e for e in env["errors"])
