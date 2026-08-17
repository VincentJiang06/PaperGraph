"""`paperproof verify` cross-reference resolution (docs/09 §3, N1 hardening).

The global invariant sweep must resolve every cross-reference, including evidence
ids on node bindings and duplicate_of references. These build a clean S1 project
(terminal verify exit 0), then append a single dangling reference and assert
verify flips to exit 3 naming the offending record + id.
"""

from __future__ import annotations

import json

import pytest

from paperproof.graph import model as graph_model
from paperproof.store import jsonl, snapshot

from tests.fakes import scenario
from tests.fakes.workers import FakeProofWorker, drain

pytestmark = pytest.mark.contract

NODES = "graph/logic_nodes.jsonl"
TOMBSTONES = "graph/tombstones.jsonl"


def _clean_s1(paths):
    scenario.seed_layer0(paths)
    drain(paths, FakeProofWorker(scenario.s1_script()))


def test_verify_clean_project_exits_0(project, pp):
    paths = scenario.paths_for_pp(pp)
    _clean_s1(paths)
    assert pp("verify")["ok"] is True


def test_verify_catches_dangling_evidence_binding(project, pp):
    """The evaluator repro: a NODE-003 version with a non-existent
    evidence_binding must make verify exit 3, naming the node + the id."""
    paths = scenario.paths_for_pp(pp)
    _clean_s1(paths)
    assert pp("verify")["ok"] is True  # clean first

    gv = graph_model.load(paths)
    node = dict(gv.node_by_id["NODE-003"])
    node["evidence_bindings"] = ["EU-999-nonexistent"]
    node["created_at"] = "2026-07-07T00:00:01Z"
    jsonl.append(paths.resolve(NODES), node)

    env = pp("verify", expect=3)
    assert env["ok"] is False
    assert "V-XREF" in env["errors"]
    detail = " ".join(env["data"]["detail"].values())
    assert "NODE-003" in detail and "EU-999-nonexistent" in detail


def test_verify_catches_dangling_duplicate_of(project, pp):
    paths = scenario.paths_for_pp(pp)
    _clean_s1(paths)
    assert pp("verify")["ok"] is True  # clean first

    jsonl.append(paths.resolve(TOMBSTONES), {
        "schema_version": "tombstone.v1", "tombstone_id": "TS-900", "project_id": "p4-ldi",
        "target_type": "node", "target_id": "NODE-003", "reason": "duplicate",
        "duplicate_of": "NODE-DANGLING", "commit_id": "CD-000001", "created_at": "2026-07-07T00:00:01Z",
    })

    env = pp("verify", expect=3)
    assert env["ok"] is False
    assert "V-XREF" in env["errors"]
    detail = " ".join(env["data"]["detail"].values())
    assert "NODE-DANGLING" in detail


def test_verify_catches_dangling_node_duplicate_of(project, pp):
    """The rejected(duplicate) node branch: state_detail.duplicate_of must
    resolve to a real node id."""
    paths = scenario.paths_for_pp(pp)
    _clean_s1(paths)

    gv = graph_model.load(paths)
    node = dict(gv.node_by_id["NODE-003"])
    node.update({
        "lifecycle_state": "rejected", "state_reason": "duplicate",
        "state_detail": {"duplicate_of": "NODE-DANGLING"}, "strength": "unassessed",
        "language_limits": None, "created_at": "2026-07-07T00:00:01Z",
    })
    jsonl.append(paths.resolve(NODES), node)

    env = pp("verify", expect=3)
    assert env["ok"] is False
    assert "V-XREF" in env["errors"]
    detail = " ".join(env["data"]["detail"].values())
    assert "NODE-DANGLING" in detail


def test_verify_catches_dangling_latest_proof_result_id(project, pp):
    """P8: a non-rejected node's latest_proof_result_id (when set) must resolve to
    a stored proof result; a dangling id makes verify exit 3, naming node + id."""
    paths = scenario.paths_for_pp(pp)
    _clean_s1(paths)
    assert pp("verify")["ok"] is True  # clean first

    gv = graph_model.load(paths)
    node = dict(gv.node_by_id["NODE-003"])
    node["latest_proof_result_id"] = "PR-999-nonexistent"
    node["created_at"] = "2026-07-07T00:00:01Z"
    jsonl.append(paths.resolve(NODES), node)

    env = pp("verify", expect=3)
    assert env["ok"] is False
    assert "V-XREF" in env["errors"]
    detail = " ".join(env["data"]["detail"].values())
    assert "NODE-003" in detail and "PR-999-nonexistent" in detail


def test_verify_schema_sweeps_the_stored_specs(project, pp):
    """P6: the schema sweep also validates the single-doc canonical specs
    (paper_spec.json, project_contract.json); a schema-invalid spec makes verify
    exit 3 (previously it was never re-validated)."""
    paths = scenario.paths_for_pp(pp)
    _clean_s1(paths)
    assert pp("verify")["ok"] is True  # clean first

    # (a) an unknown field on the stored contract (STRICT extra=forbid).
    good_contract = paths.project_contract.read_text(encoding="utf-8")
    bad = json.loads(good_contract)
    bad["surprise_field"] = "nope"
    paths.project_contract.write_text(json.dumps(bad), encoding="utf-8")
    env = pp("verify", expect=3)
    assert "V-SCHEMA" in env["errors"]
    assert "project_contract" in " ".join(env["data"]["detail"].values())
    paths.project_contract.write_text(good_contract, encoding="utf-8")  # restore
    assert pp("verify")["ok"] is True

    # (b) an out-of-enum paper_type on the stored paper_spec.
    spec = json.loads(paths.paper_spec.read_text(encoding="utf-8"))
    spec["paper_type"] = "not_a_real_paper_type"
    paths.paper_spec.write_text(json.dumps(spec), encoding="utf-8")
    env = pp("verify", expect=3)
    assert "V-SCHEMA" in env["errors"]
    assert "paper_spec" in " ".join(env["data"]["detail"].values())


def test_verify_catches_unattributed_graph_append(project, pp):
    """T-r3-2 (remaps hostile H10): the lease scan deliberately ignores appends
    (docs/05 prefix rule), so a worker's direct graph append is caught by
    verify's snapshot-EOF check — rows on disk beyond the latest snapshot
    belong to no CommitDecision ⇒ V-COMMIT-04, exit 3."""
    paths = scenario.paths_for_pp(pp)
    _clean_s1(paths)
    assert pp("verify")["ok"] is True  # clean first

    gv = graph_model.load(paths)
    node = dict(gv.node_by_id["NODE-003"])  # schema-valid record, no commit
    node["created_at"] = "2026-07-07T00:00:02Z"
    jsonl.append(paths.resolve(NODES), node)

    env = pp("verify", expect=3)
    assert env["ok"] is False
    assert "V-COMMIT-04" in env["errors"]
    detail = str(env["data"].get("detail", ""))
    assert "logic_nodes.jsonl" in detail and "unattributed" in detail
