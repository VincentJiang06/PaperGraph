"""V-SPEC contract tests: golden spec build + one failing topic per rule (docs/11)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.contract

TOPICS = Path(__file__).resolve().parent.parent / "fixtures" / "topics"
SCHEMAS = Path(__file__).resolve().parent.parent / "fixtures" / "schemas"


def test_golden_spec_build_is_byte_exact(pp, monkeypatch, canonical):
    """spec build on the P4 example under a fixed clock yields byte-exact
    PaperSpec + Contract."""
    monkeypatch.setenv("PAPERPROOF_PROJECT", "p4-ldi")
    pp("project", "init", "p4-ldi")
    env = pp("spec", "build", str(TOPICS / "ok_p4.md"))
    assert env["ok"] is True

    project_dir = Path(pp.tmp_path) / "projects" / "p4-ldi"
    got_spec = canonical(project_dir / "specs" / "paper_spec.json")
    got_contract = canonical(project_dir / "specs" / "project_contract.json")

    assert got_spec == canonical(SCHEMAS / "paper_spec.v1.json")
    assert got_contract == canonical(SCHEMAS / "project_contract.v1.json")


def test_spec_build_is_deterministic(pp, monkeypatch, canonical):
    monkeypatch.setenv("PAPERPROOF_PROJECT", "p4-ldi")
    pp("project", "init", "p4-ldi")
    pp("spec", "build", str(TOPICS / "ok_p4.md"))
    project_dir = Path(pp.tmp_path) / "projects" / "p4-ldi"
    first = canonical(project_dir / "specs" / "paper_spec.json")
    # rebuild (contract not yet accepted) must produce identical bytes
    pp("spec", "build", str(TOPICS / "ok_p4.md"))
    assert canonical(project_dir / "specs" / "paper_spec.json") == first


def test_spec_accept_then_build_refuses(pp, monkeypatch):
    monkeypatch.setenv("PAPERPROOF_PROJECT", "p4-ldi")
    pp("project", "init", "p4-ldi")
    pp("spec", "build", str(TOPICS / "ok_p4.md"))
    pp("spec", "accept")
    env = pp("spec", "build", str(TOPICS / "ok_p4.md"), expect=1)
    assert env["ok"] is False


@pytest.mark.parametrize(
    "topic,patch,rule",
    [
        ("fail_V-SPEC-01_missing_success.md", None, "V-SPEC-01"),
        ("fail_V-SPEC-02_wrong_pattern.md", None, "V-SPEC-02"),
        ("fail_V-SPEC-03_cyclic_bfs.md", "fail_V-SPEC-03_cyclic_bfs.patch.json", "V-SPEC-03"),
        ("fail_V-SPEC-04_missing_exclusions.md", None, "V-SPEC-04"),
        ("fail_V-SPEC-05_too_few_seeds.md", None, "V-SPEC-05"),
    ],
)
def test_each_v_spec_rule_has_failing_fixture(pp, monkeypatch, topic, patch, rule):
    monkeypatch.setenv("PAPERPROOF_PROJECT", "p4-ldi")
    pp("project", "init", "p4-ldi")
    args = ["spec", "build", str(TOPICS / topic)]
    if patch:
        args += ["--patch", str(TOPICS / patch)]
    env = pp(*args, expect=1)
    assert rule in env["data"]["failed_rules"], env["data"]
