"""Determinism harness fixtures (docs/11 §3).

Three injection points, all environment-driven so the CLI needs no test-only
flags: PAPERPROOF_NOW (clock), PAPERPROOF_ACTOR (actor), and deterministic id
allocation (no injection needed).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from typer.testing import CliRunner

from paperproof.cli.app import app

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_TOPIC = REPO_ROOT / "examples" / "topic-input-p4.md"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

_FMT = "%Y-%m-%dT%H:%M:%SZ"


class Clock:
    """Pins PAPERPROOF_NOW; tick(seconds) monotonically bumps it."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, start: str = "2026-07-07T00:00:00Z") -> None:
        self._monkeypatch = monkeypatch
        self._dt = datetime.strptime(start, _FMT).replace(tzinfo=timezone.utc)
        self._apply()

    def _apply(self) -> None:
        self._monkeypatch.setenv("PAPERPROOF_NOW", self._dt.strftime(_FMT))

    @property
    def now(self) -> str:
        return self._dt.strftime(_FMT)

    def tick(self, seconds: int = 1) -> str:
        self._dt += timedelta(seconds=seconds)
        self._apply()
        return self.now


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> Clock:
    return Clock(monkeypatch)


@pytest.fixture
def pp(tmp_path: Path, clock: Clock, monkeypatch: pytest.MonkeyPatch):
    """CliRunner wrapper: pp("queue", "claim", ...) -> parsed envelope; asserts
    the declared exit code (expect=, default 0)."""
    monkeypatch.setenv("PAPERPROOF_ACTOR", "test")
    runner = CliRunner()

    def _pp(*args: object, expect: int = 0) -> dict:
        argv = ["--root", str(tmp_path), *[str(a) for a in args]]
        result = runner.invoke(app, argv)
        out = result.stdout
        try:
            env = json.loads(out.strip())
        except json.JSONDecodeError as exc:  # pragma: no cover - failure aid
            raise AssertionError(
                f"non-JSON envelope (exit {result.exit_code}) for {argv}: {out!r}"
            ) from exc
        assert result.exit_code == expect, (
            f"expected exit {expect}, got {result.exit_code} for {argv}; env={env}"
        )
        assert set(env.keys()) == {"ok", "command", "data", "errors", "warnings"}
        return env

    _pp.tmp_path = tmp_path  # type: ignore[attr-defined]
    return _pp


@pytest.fixture
def project(pp, monkeypatch: pytest.MonkeyPatch) -> Path:
    """init p4-ldi + spec build the example + spec accept; returns project root."""
    monkeypatch.setenv("PAPERPROOF_PROJECT", "p4-ldi")
    pp("project", "init", "p4-ldi")
    pp("spec", "build", str(EXAMPLE_TOPIC))
    pp("spec", "accept")
    return Path(pp.tmp_path) / "projects" / "p4-ldi"


@pytest.fixture
def canonical():
    """Helper: read a file for byte comparison."""

    def _read(path) -> bytes:
        return Path(path).read_bytes()

    return _read
