"""CLI conformance meta-test (docs/11 §7) + true-subprocess smoke tests.

The closed command list (docs/10 §4) is mirrored here; the test asserts the typer
app exposes exactly that set (no drift either direction), and every command emits
exactly one JSON envelope with keys {ok, command, data, errors, warnings} -
including on failure (exit 1) and usage error (exit 2).
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest
import typer
from typer.testing import CliRunner

from paperproof.cli.app import app

pytestmark = pytest.mark.contract

# The authoritative, closed v1 command surface (docs/10 §4).
CLOSED_COMMANDS = {
    "project init", "project status",
    "spec build", "spec accept", "spec show",
    "graph list-nodes", "graph list-edges", "graph show", "graph msa-check",
    "graph park", "graph unpark",
    "expand ingest",
    "proof build-tasks", "proof build-task",
    "docs ingest", "docs search", "docs build-pack", "docs request", "docs ingest-result", "docs plan",
    "docs source list", "docs source set",
    "queue list", "queue claim", "queue heartbeat", "queue release", "queue complete",
    "queue fail", "queue expire", "queue requeue", "queue events",
    "validate result", "validate proposal", "validate docs-result",
    "commit apply",
    "freeze apply", "freeze unfreeze",
    "compiler dry-run", "compiler draft-map", "compiler ingest-prose",
    "audit run",
    "db rebuild", "db check",
    "ui serve",
    "verify", "trace",
}

ENVELOPE_KEYS = {"ok", "command", "data", "errors", "warnings"}


def _walk(command, prefix):
    out = set()
    subs = getattr(command, "commands", None)
    if subs:
        for name, sub in subs.items():
            out |= _walk(sub, prefix + [name])
    else:
        out.add(" ".join(prefix))
    return out


def _command_tree():
    root = typer.main.get_command(app)
    return _walk(root, [])


def test_command_set_matches_closed_list_both_directions():
    exposed = _command_tree()
    assert exposed == CLOSED_COMMANDS, {
        "unexpected": sorted(exposed - CLOSED_COMMANDS),
        "missing": sorted(CLOSED_COMMANDS - exposed),
    }


def _assert_valid_envelope(result):
    env = json.loads(result.stdout.strip())
    assert set(env.keys()) == ENVELOPE_KEYS
    assert isinstance(env["ok"], bool)
    assert isinstance(env["command"], str)
    assert isinstance(env["data"], dict)
    assert isinstance(env["errors"], list)
    assert isinstance(env["warnings"], list)
    return env


@pytest.mark.parametrize("command", sorted(CLOSED_COMMANDS))
def test_every_command_emits_one_envelope(tmp_path, command, monkeypatch):
    monkeypatch.setenv("PAPERPROOF_NOW", "2026-07-07T00:00:00Z")
    monkeypatch.delenv("PAPERPROOF_PROJECT", raising=False)
    runner = CliRunner()
    argv = ["--root", str(tmp_path), *command.split()]
    result = runner.invoke(app, argv)
    assert result.exit_code in (0, 1, 2, 3), (command, result.exit_code, result.stdout)
    env = _assert_valid_envelope(result)
    # exactly one envelope on stdout (single JSON line)
    assert result.stdout.strip().count("\n") == 0


def test_no_stub_commands_remain(tmp_path, monkeypatch):
    """M4 is the last milestone: db/ui are now REAL, so no command returns the
    NOT-IMPLEMENTED stub sentinel anymore (the closed surface is unchanged)."""
    monkeypatch.setenv("PAPERPROOF_NOW", "2026-07-07T00:00:00Z")
    monkeypatch.delenv("PAPERPROOF_PROJECT", raising=False)
    runner = CliRunner()
    for command in sorted(CLOSED_COMMANDS):
        result = runner.invoke(app, ["--root", str(tmp_path), *command.split()])
        env = _assert_valid_envelope(result)
        assert env["errors"] != ["NOT-IMPLEMENTED"], command


def test_usage_error_emits_envelope_exit_2(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERPROOF_NOW", "2026-07-07T00:00:00Z")
    monkeypatch.setenv("PAPERPROOF_PROJECT", "p4-ldi")
    runner = CliRunner()
    runner.invoke(app, ["--root", str(tmp_path), "project", "init", "p4-ldi"])
    result = runner.invoke(app, ["--root", str(tmp_path), "--project", "p4-ldi", "spec", "build"])
    assert result.exit_code == 2
    env = _assert_valid_envelope(result)
    assert env["ok"] is False
    assert env["command"] == "spec build"


def test_success_and_domain_failure_exit_codes(pp, monkeypatch):
    monkeypatch.setenv("PAPERPROOF_PROJECT", "p4-ldi")
    env_ok = pp("project", "init", "p4-ldi")  # expect 0
    assert env_ok["ok"] is True
    # domain failure: status on a non-existent project
    env_fail = pp("--project", "nope-xyz", "project", "status", expect=1)
    assert env_fail["ok"] is False


# --- true-subprocess smoke tests (envelope + exit-code contract) ---


def test_subprocess_success(tmp_path):
    env = {"PAPERPROOF_NOW": "2026-07-07T00:00:00Z", "PATH": _path_env()}
    proc = subprocess.run(
        [sys.executable, "-m", "paperproof", "--root", str(tmp_path), "project", "init", "sub-proj"],
        capture_output=True, text=True, env=env,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout.strip())
    assert payload["ok"] is True
    assert payload["command"] == "project init"
    assert set(payload.keys()) == ENVELOPE_KEYS


def test_subprocess_usage_error(tmp_path):
    env = {"PAPERPROOF_NOW": "2026-07-07T00:00:00Z", "PATH": _path_env()}
    proc = subprocess.run(
        [sys.executable, "-m", "paperproof", "--root", str(tmp_path), "project", "init"],
        capture_output=True, text=True, env=env,
    )
    assert proc.returncode == 2, (proc.returncode, proc.stdout, proc.stderr)
    payload = json.loads(proc.stdout.strip())
    assert payload["ok"] is False
    assert set(payload.keys()) == ENVELOPE_KEYS


def _path_env() -> str:
    import os

    return os.environ.get("PATH", "")
