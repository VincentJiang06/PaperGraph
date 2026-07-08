from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from nodify.cli import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def _fixed_clock(monkeypatch):
    monkeypatch.setenv("NODIFY_NOW", "2026-07-09T12:00:00Z")
    monkeypatch.delenv("NODIFY_SESSION", raising=False)
    monkeypatch.delenv("NODIFY_ACTOR", raising=False)


@pytest.fixture
def ws(tmp_path):
    """A workspace bound to tmp_path: ws(*argv) -> envelope (asserting exit)."""
    def run(*argv: str, expect: int = 0):
        args = list(argv) + ["--root", str(tmp_path)]
        if argv[0] != "init":
            args += ["--session", "t"]
        result = runner.invoke(app, args)
        lines = [l for l in result.stdout.strip().splitlines() if l.strip()]
        assert len(lines) == 1, f"expected one envelope line, got: {result.stdout!r}"
        env = json.loads(lines[0])
        code = result.exit_code or 0
        assert code == expect, (argv, code, env["errors"])
        return env
    run.root = tmp_path
    return run


@pytest.fixture
def session(ws):
    ws("init", "t", "--question", "为什么服务在周二凌晨崩溃?")
    return ws


def write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return str(path)
