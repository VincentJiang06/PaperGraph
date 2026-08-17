"""V-PATH contract tests: path safety + the post-run prefix scan (docs/09, docs/05).

Exercises the relevant hostile cases directly (the full worker flow arrives at
M1): H02 (wrong output path) -> V-PATH-01; traversal/symlink -> V-PATH-02;
H03 (invalid JSON bytes) -> V-PATH-03; H01/H10-style stray or prefix-breaking
writes -> V-PATH-04.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from paperproof.validate.rules import v_path

pytestmark = pytest.mark.contract

VRULES = Path(__file__).resolve().parent.parent / "fixtures" / "vrules"


def _rule_ids(failures):
    return [f.rule_id for f in failures]


def test_v_path_01_output_path_must_match():
    declared = ["agent_outputs/proof_results/PT-NODE-001.proof_result.json"]
    assert v_path.check_output_path(declared[0], declared) == []
    failures = v_path.check_output_path("agent_outputs/prose/wrong.json", declared)
    assert _rule_ids(failures) == ["V-PATH-01"]


def test_v_path_02_traversal_and_symlink(tmp_path):
    assert v_path.check_path_safety(tmp_path, "graph/logic_nodes.jsonl") == []
    assert "V-PATH-02" in _rule_ids(v_path.check_path_safety(tmp_path, "../escape.json"))
    assert "V-PATH-02" in _rule_ids(v_path.check_path_safety(tmp_path, "/etc/passwd"))

    outside = tmp_path.parent / "vpath_outside"
    outside.mkdir(exist_ok=True)
    (tmp_path / "link").symlink_to(outside, target_is_directory=True)
    assert "V-PATH-02" in _rule_ids(v_path.check_path_safety(tmp_path, "link/x.json"))


def test_v_path_03_valid_and_invalid_json(tmp_path):
    (tmp_path / "agent_outputs").mkdir()
    good = tmp_path / "agent_outputs" / "good.json"
    good.write_text('{"ok": true}', encoding="utf-8")
    assert v_path.check_utf8_json(tmp_path, "agent_outputs/good.json") == []

    bad = tmp_path / "agent_outputs" / "bad.json"
    bad.write_text("{not json,,,", encoding="utf-8")
    assert "V-PATH-03" in _rule_ids(v_path.check_utf8_json(tmp_path, "agent_outputs/bad.json"))

    # invalid UTF-8 bytes
    raw = tmp_path / "agent_outputs" / "raw.json"
    raw.write_bytes(b"\xff\xfe\x00")
    assert "V-PATH-03" in _rule_ids(v_path.check_utf8_json(tmp_path, "agent_outputs/raw.json"))

    # missing file
    assert "V-PATH-03" in _rule_ids(v_path.check_utf8_json(tmp_path, "agent_outputs/missing.json"))


def _make_graph_files(tmp_path):
    graph = tmp_path / "graph"
    graph.mkdir()
    nodes = graph / "logic_nodes.jsonl"
    nodes.write_text('{"node_id":"NODE-001"}\n', encoding="utf-8")
    contract = tmp_path / "specs"
    contract.mkdir()
    spec = contract / "paper_spec.json"
    spec.write_text('{"schema_version":"paper_spec.v1"}\n', encoding="utf-8")
    return nodes, spec


def test_v_path_04_legit_append_passes_prefix(tmp_path):
    nodes, _ = _make_graph_files(tmp_path)
    manifest = v_path.build_manifest(tmp_path, ["graph/logic_nodes.jsonl"])
    # engines only append; a broken prefix is what the rule catches
    with nodes.open("a", encoding="utf-8") as fh:
        fh.write('{"node_id":"NODE-002"}\n')
    assert v_path.check_prefix_rule(tmp_path, manifest) == []


def test_v_path_04_broken_jsonl_prefix(tmp_path):
    nodes, _ = _make_graph_files(tmp_path)
    manifest = v_path.build_manifest(tmp_path, ["graph/logic_nodes.jsonl"])
    nodes.write_text('{"node_id":"NODE-999"}\n', encoding="utf-8")  # rewrite/truncate
    failures = v_path.check_prefix_rule(tmp_path, manifest)
    assert "V-PATH-04" in _rule_ids(failures)


def test_v_path_04_non_jsonl_modification(tmp_path):
    _, spec = _make_graph_files(tmp_path)
    manifest = v_path.build_manifest(tmp_path, ["specs/paper_spec.json"])
    spec.write_text('{"schema_version":"paper_spec.v1","edited":true}\n', encoding="utf-8")
    failures = v_path.check_prefix_rule(tmp_path, manifest)
    assert "V-PATH-04" in _rule_ids(failures)


# --- fixture-driven coverage over tests/fixtures/vrules/V-PATH-* (docs/11 §4) ---


def _run_vpath_scenario(rule: str, scenario: dict, tmp_path: Path) -> list[str]:
    if rule == "V-PATH-01":
        return _rule_ids(v_path.check_output_path(scenario["actual"], scenario["declared"]))
    if rule == "V-PATH-02":
        return _rule_ids(v_path.check_path_safety(tmp_path, scenario["relpath"]))
    if rule == "V-PATH-03":
        target = tmp_path / "agent_outputs"
        target.mkdir(exist_ok=True)
        (target / "out.json").write_text(scenario["body"], encoding="utf-8")
        return _rule_ids(v_path.check_utf8_json(tmp_path, "agent_outputs/out.json"))
    if rule == "V-PATH-04":
        nodes, _ = _make_graph_files(tmp_path)
        manifest = v_path.build_manifest(tmp_path, ["graph/logic_nodes.jsonl"])
        if scenario["scenario"] == "append":
            with nodes.open("a", encoding="utf-8") as fh:
                fh.write('{"node_id":"NODE-002"}\n')
        elif scenario["scenario"] == "prefix_break":
            nodes.write_text('{"node_id":"NODE-999"}\n', encoding="utf-8")
        return _rule_ids(v_path.check_prefix_rule(tmp_path, manifest))
    raise AssertionError(f"unknown rule {rule}")


def _collect_vrules():
    cases = []
    for rule_dir in sorted(VRULES.glob("V-PATH-*")):
        rule = rule_dir.name
        for path in sorted(rule_dir.glob("*.json")):
            expect_fail = path.name.startswith("fail_")
            cases.append((rule, path.name, expect_fail))
    return cases


@pytest.mark.parametrize("rule,filename,expect_fail", _collect_vrules())
def test_vrules_v_path_fixtures(tmp_path, rule, filename, expect_fail):
    scenario = json.loads((VRULES / rule / filename).read_bytes())
    fired = _run_vpath_scenario(rule, scenario, tmp_path)
    if expect_fail:
        assert rule in fired, (rule, filename, fired)
    else:
        assert rule not in fired, (rule, filename, fired)
