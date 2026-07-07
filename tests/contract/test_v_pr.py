"""V-PR contract tests (docs/09, docs/11 §4/§6) — the largest fixture set.

Two layers:
  1. one pass_ + one fail_ fixture PER V-PR rule (fixtures/vrules/V-PR-*/), each a
     self-contained {task, context_pack, docs_pack, work_item, result}; the named
     rule must be absent (pass) / present (fail) in failed_rules.
  2. the hostile catalog H01-H18, each caught by its NAMED rule (the mapping is
     asserted). Check order: V-PATH, then the V-PR-03 raw scan before schema
     parse, then schema (V-PR-01), then the semantic rules.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from paperproof.validate.rules import v_path, v_pr

pytestmark = pytest.mark.contract

VRULES = Path(__file__).resolve().parent.parent / "fixtures" / "vrules"


def _run(obj) -> list[str]:
    failures = v_pr.raw_scan(obj["result"])
    vpr_failures, _ = v_pr.check(
        obj["result"],
        task=obj["task"],
        context_pack=obj["context_pack"],
        docs_pack=obj["docs_pack"],
        work_item=obj["work_item"],
    )
    failures += vpr_failures
    return [f.rule_id for f in failures]


def _vpr_cases():
    cases = []
    for rule_dir in sorted(VRULES.glob("V-PR-*")):
        rule = rule_dir.name
        for path in sorted(rule_dir.glob("*.json")):
            cases.append((rule, path.name, path.name.startswith("fail_")))
    return cases


@pytest.mark.parametrize("rule,filename,expect_fail", _vpr_cases())
def test_vpr_fixtures(rule, filename, expect_fail):
    obj = json.loads((VRULES / rule / filename).read_bytes())
    fired = _run(obj)
    if expect_fail:
        assert rule in fired, (rule, filename, fired)
    else:
        assert rule not in fired, (rule, filename, fired)


def test_every_vpr_rule_has_pass_and_fail():
    from paperproof.validate import registry

    vpr_rules = [r for r in registry.rule_ids() if r.startswith("V-PR-")]
    # V-PR-12 is a recompute-at-rest rule (verify), not a form check -> scenario.
    fixtured = {r for r in vpr_rules if (VRULES / r).exists()}
    for r in vpr_rules:
        if r == "V-PR-12":
            continue
        d = VRULES / r
        names = [p.name for p in d.glob("*.json")]
        assert any(n.startswith("pass_") for n in names), r
        assert any(n.startswith("fail_") for n in names), r


# --- hostile catalog (docs/11 §6) ------------------------------------------


def _node_bundle(node_type="definition"):
    task = {"schema_version": "proof_task.v1", "task_id": "PT-NODE-001", "project_id": "p4-ldi",
            "task_type": "NODE_CHECK", "target": {"node_id": "NODE-001"},
            "context_pack": "proof/context/CTX-NODE-001.json", "docs_pack": "docs/docspacks/DOCSPACK-NODE-001.json",
            "output_file": "agent_outputs/proof_results/PT-NODE-001.proof_result.json"}
    ctx = {"schema_version": "context_pack.v1", "pack_id": "CTX-NODE-001", "task_id": "PT-NODE-001",
           "project_id": "p4-ldi", "based_on_snapshot": "GS-000002",
           "target": {"node_id": "NODE-001", "node_type": node_type, "claim": "A single clear proposition."},
           "neighbor_nodes": [{"node_id": "NODE-002"}], "neighbor_edges": [],
           "claim_digest": [{"node_id": "NODE-001", "claim": "x"}, {"node_id": "NODE-002", "claim": "y"}],
           "contract_scope": {}, "forbidden_claims": [], "prior_results": []}
    dp = {"schema_version": "docs_pack.v1", "pack_id": "DOCSPACK-NODE-001", "task_id": "PT-NODE-001",
          "project_id": "p4-ldi", "evidence_units": [{"evidence_id": "EU-001"}], "documents_meta": [{"doc_id": "DOC-001"}]}
    wi = {"work_item_id": "WI-000001", "task_id": "PT-NODE-001", "target_id": "NODE-001",
          "target_type": "node", "output_files": ["agent_outputs/proof_results/PT-NODE-001.proof_result.json"],
          "bundle": {"task_file": "proof/tasks/PT-NODE-001.json", "context_pack": task["context_pack"], "docs_pack": task["docs_pack"]}}
    return task, ctx, dp, wi


def _edge_bundle():
    task = {"schema_version": "proof_task.v1", "task_id": "PT-EDGE-001-002", "project_id": "p4-ldi",
            "task_type": "EDGE_CHECK", "target": {"edge_id": "EDGE-001-002", "source_node_id": "NODE-001", "target_node_id": "NODE-002"},
            "context_pack": "proof/context/CTX-EDGE-001-002.json", "docs_pack": "docs/docspacks/DOCSPACK-EDGE-001-002.json",
            "output_file": "agent_outputs/proof_results/PT-EDGE-001-002.proof_result.json"}
    ctx = {"schema_version": "context_pack.v1", "pack_id": "CTX-EDGE-001-002", "task_id": "PT-EDGE-001-002",
           "project_id": "p4-ldi", "based_on_snapshot": "GS-000002", "target": {"edge_id": "EDGE-001-002"},
           "neighbor_nodes": [{"node_id": "NODE-001"}, {"node_id": "NODE-002"}], "neighbor_edges": [],
           "claim_digest": [{"node_id": "NODE-001", "claim": "x"}, {"node_id": "NODE-002", "claim": "y"}],
           "contract_scope": {}, "forbidden_claims": [], "prior_results": []}
    dp = {"schema_version": "docs_pack.v1", "pack_id": "DOCSPACK-EDGE-001-002", "task_id": "PT-EDGE-001-002",
          "project_id": "p4-ldi", "evidence_units": [{"evidence_id": "EU-001"}], "documents_meta": [{"doc_id": "DOC-001"}]}
    wi = {"work_item_id": "WI-000002", "task_id": "PT-EDGE-001-002", "target_id": "EDGE-001-002",
          "target_type": "edge", "output_files": ["agent_outputs/proof_results/PT-EDGE-001-002.proof_result.json"],
          "bundle": {"task_file": "proof/tasks/PT-EDGE-001-002.json", "context_pack": task["context_pack"], "docs_pack": task["docs_pack"]}}
    return task, ctx, dp, wi


LL = {"allowed": ["Strong wording."], "forbidden": ["Overclaim."]}


def _nres(**over):
    r = {"schema_version": "proof_result.v1", "task_id": "PT-NODE-001", "project_id": "p4-ldi",
         "target_type": "node", "target_id": "NODE-001",
         "form": {"scope_check": "in_scope", "duplicate_check": {"duplicate": False, "duplicate_of": None},
                  "wellformed_check": "single_proposition", "evidence_check": "not_required"},
         "assumptions": [], "evidence_used": [], "language_limits": copy.deepcopy(LL),
         "repair_proposals": [], "docs_requests": [], "notes": "ok"}
    r.update(over)
    return r


def _eres(**over):
    r = {"schema_version": "proof_result.v1", "task_id": "PT-EDGE-001-002", "project_id": "p4-ldi",
         "target_type": "edge", "target_id": "EDGE-001-002",
         "form": {"scope_check": "in_scope", "duplicate_check": {"duplicate": False, "duplicate_of": None},
                  "wellformed_check": "single_proposition", "evidence_check": "not_required", "inference_check": "holds"},
         "assumptions": [], "evidence_used": [], "language_limits": copy.deepcopy(LL),
         "repair_proposals": [], "docs_requests": [], "notes": "ok"}
    r.update(over)
    return r


def _f(form, **kw):
    g = copy.deepcopy(form); g.update(kw); return g


def _pr_hostile(bundle_kind, result):
    task, ctx, dp, wi = (_edge_bundle() if bundle_kind == "edge" else _node_bundle(bundle_kind == "fact" and "fact" or "definition"))
    return _run({"task": task, "context_pack": ctx, "docs_pack": dp, "work_item": wi, "result": result})


# H04-H09, H11-H18: form-level hostiles caught by a named V-PR rule.
def test_hostiles_vpr():
    base = _nres()
    edge = _eres()

    # H04: verdict field
    h04 = _nres(); h04["verdict"] = "pass"
    assert "V-PR-03" in _pr_hostile("node", h04)
    # H05: 3 bridge proposals on gap
    h05 = _eres(form=_f(edge["form"], inference_check="gap"), language_limits=None,
                repair_proposals=[{"kind": "bridge", "claim": f"c{i}", "node_type": "definition"} for i in range(3)])
    assert "V-PR-07" in _pr_hostile("edge", h05)
    # H06: cite EU absent from DocsPack
    h06 = _nres(form=_f(base["form"], evidence_check="sufficient"), evidence_used=["EU-999"])
    assert "V-PR-06" in _pr_hostile("node", h06)
    # H07: confidence numeric
    h07 = _nres(); h07["confidence"] = 0.9
    assert "V-PR-03" in _pr_hostile("node", h07)
    # H08: fact node answers not_required
    assert "V-PR-05" in _pr_hostile("fact", _nres())
    # H09: task_id of a different work item
    assert "V-PR-02" in _pr_hostile("node", _nres(task_id="PT-OTHER-1"))
    # H11: out_of_scope but evidence answered
    h11 = _nres(form=_f(base["form"], scope_check="out_of_scope", wellformed_check="single_proposition", evidence_check="not_required"), language_limits=None)
    assert "V-PR-14" in _pr_hostile("node", h11)
    # H12: too_broad without narrow repair
    h12 = _nres(form=_f(base["form"], wellformed_check="too_broad", evidence_check="not_evaluated"), language_limits=None)
    assert "V-PR-07" in _pr_hostile("node", h12)
    # H13: would-pass form, language_limits null
    assert "V-PR-13" in _pr_hostile("node", _nres(language_limits=None))
    # H14: edge holds + non-empty assumptions
    assert "V-PR-15" in _pr_hostile("edge", _eres(assumptions=["x"]))
    # H15: duplicate_of not in ContextPack
    h15 = _nres(form=_f(base["form"], duplicate_check={"duplicate": True, "duplicate_of": "NODE-777"},
                        wellformed_check="not_evaluated", evidence_check="not_evaluated"), language_limits=None)
    assert "V-PR-08" in _pr_hostile("node", h15)
    # H16: 200-word notes
    assert "V-PR-10" in _pr_hostile("node", _nres(notes=" ".join(["w"] * 200)))
    # H17: bridge proposing node_type=thesis
    h17 = _eres(form=_f(edge["form"], inference_check="gap"), language_limits=None,
                repair_proposals=[{"kind": "bridge", "claim": "c", "node_type": "thesis"}])
    assert "V-PR-09" in _pr_hostile("edge", h17)
    # H18: inference_check on a NODE_CHECK
    assert "V-PR-04" in _pr_hostile("node", _nres(form=_f(base["form"], inference_check="holds")))


def test_hostiles_vpath(tmp_path):
    # H02: correct JSON at wrong output path
    declared = ["agent_outputs/proof_results/PT-NODE-001.proof_result.json"]
    assert "V-PATH-01" in [f.rule_id for f in v_path.check_output_path("agent_outputs/prose/wrong.json", declared)]
    # H03: invalid JSON bytes
    (tmp_path / "agent_outputs").mkdir()
    bad = tmp_path / "agent_outputs" / "out.json"
    bad.write_text("{not json,,,", encoding="utf-8")
    assert "V-PATH-03" in [f.rule_id for f in v_path.check_utf8_json(tmp_path, "agent_outputs/out.json")]

    # H01: a second file outside allowed paths (a canonical dir)
    (tmp_path / "graph").mkdir()
    (tmp_path / "graph" / "logic_nodes.jsonl").write_text("", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    manifest = v_path.build_lease_manifest(tmp_path, ["agent_outputs/proof_results/PT-NODE-001.proof_result.json", "agent_notes/**"])
    (tmp_path / "docs" / "sneaky.txt").write_text("x", encoding="utf-8")
    assert "V-PATH-04" in [f.rule_id for f in v_path.check_lease_scan(tmp_path, manifest)]

    # H10: append a line to a committer-owned file under a lease
    manifest2 = v_path.build_lease_manifest(tmp_path, ["agent_outputs/proof_results/PT-NODE-001.proof_result.json", "agent_notes/**"])
    with (tmp_path / "graph" / "logic_nodes.jsonl").open("a", encoding="utf-8") as fh:
        fh.write('{"node_id":"NODE-999"}\n')
    assert "V-PATH-04" in [f.rule_id for f in v_path.check_lease_scan(tmp_path, manifest2)]
