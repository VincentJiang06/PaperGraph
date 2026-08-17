"""Determinism (docs/11 §3).

Run S1 end-to-end in two fresh roots under an identical PAPERPROOF_NOW sequence =>
every canonical file under graph/ proof/ queue/ commit/ is byte-identical between
the two runs. This enforces the canonical-serialization convention across the
whole pipeline in one test.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from paperproof import project as project_mod
from paperproof.paths import paths_for
from paperproof.scoping import build as scoping_build

from tests.conftest import EXAMPLE_TOPIC
from tests.fakes import scenario
from tests.fakes.workers import FakeProofWorker, drain

pytestmark = pytest.mark.integration

_CANONICAL_DIRS = ("graph", "proof", "queue", "commit")


def _run_s1(root: Path):
    paths = paths_for(root, "p4-ldi")
    project_mod.init(paths)
    scoping_build.build(paths, str(EXAMPLE_TOPIC), None)
    scoping_build.accept(paths)
    scenario.seed_layer0(paths)
    drain(paths, FakeProofWorker(scenario.s1_script()))
    return paths


def _canonical_files(paths) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for d in _CANONICAL_DIRS:
        base = paths.resolve(d)
        for p in sorted(base.rglob("*")):
            if p.is_file() and not p.name.endswith(".lock"):
                out[str(p.relative_to(paths.project_dir))] = p.read_bytes()
    return out


def test_two_runs_are_byte_identical(tmp_path_factory, monkeypatch):
    monkeypatch.setenv("PAPERPROOF_NOW", "2026-07-07T00:00:00Z")
    monkeypatch.setenv("PAPERPROOF_ACTOR", "test")

    a = _run_s1(tmp_path_factory.mktemp("run_a"))
    b = _run_s1(tmp_path_factory.mktemp("run_b"))

    files_a = _canonical_files(a)
    files_b = _canonical_files(b)

    assert set(files_a) == set(files_b), {
        "only_a": sorted(set(files_a) - set(files_b)),
        "only_b": sorted(set(files_b) - set(files_a)),
    }
    mismatches = [rel for rel in files_a if files_a[rel] != files_b[rel]]
    assert not mismatches, f"byte mismatch in: {mismatches}"
