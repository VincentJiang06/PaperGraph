"""`paperproof verify` cross-reference resolution (docs/09 §3, N1 hardening).

The global invariant sweep must resolve every cross-reference, including evidence
ids on node bindings and duplicate_of references. These build a clean S1 project
(terminal verify exit 0), then append a single dangling reference and assert
verify flips to exit 3 naming the offending record + id.
"""

from __future__ import annotations

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
