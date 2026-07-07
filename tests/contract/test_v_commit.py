"""V-COMMIT contract tests (docs/08 B6/B6b, docs/09).

One golden per verdict->action row, each B6b administrative kind, CommitDecision
replay equality (V-COMMIT-04), byte-determinism, stale-snapshot refusal
(V-COMMIT-01), frozen refusal (V-COMMIT-03), V-COMMIT-06 no-op cancel, and the
rejection cascade.
"""

from __future__ import annotations

import pytest

from paperproof import project as project_mod
from paperproof.committer import apply as committer
from paperproof.committer import replay
from paperproof.graph import model as graph_model
from paperproof.paths import paths_for
from paperproof.prooftask import builder
from paperproof.queue import engine
from paperproof.scoping import build as scoping_build
from paperproof.store import jsonl

from tests.conftest import EXAMPLE_TOPIC
from tests.fakes import scenario
from tests.fakes.workers import FakeProofWorker, prove_one

pytestmark = pytest.mark.contract


def _prove(paths, target, spec, commit=True):
    return prove_one(paths, target, FakeProofWorker({target: spec}), commit=commit)


def _node_oos():
    return {"form": {"scope_check": "out_of_scope", "duplicate_check": {"duplicate": False, "duplicate_of": None},
                     "wellformed_check": "not_evaluated", "evidence_check": "not_evaluated"},
            "assumptions": [], "evidence_used": [], "language_limits": None,
            "repair_proposals": [], "docs_requests": [], "notes": "oos"}


def _node_dup(dup_of):
    return {"form": {"scope_check": "in_scope", "duplicate_check": {"duplicate": True, "duplicate_of": dup_of},
                     "wellformed_check": "not_evaluated", "evidence_check": "not_evaluated"},
            "assumptions": [], "evidence_used": [], "language_limits": None,
            "repair_proposals": [], "docs_requests": [], "notes": "dup"}


def _node_narrow():
    return {"form": {"scope_check": "in_scope", "duplicate_check": {"duplicate": False, "duplicate_of": None},
                     "wellformed_check": "too_broad", "evidence_check": "not_evaluated"},
            "assumptions": [], "evidence_used": [], "language_limits": None,
            "repair_proposals": [{"kind": "narrow", "narrowed_claim": "A tighter single proposition."}],
            "docs_requests": [], "notes": "narrow"}


def _node_docs():
    return {"form": {"scope_check": "in_scope", "duplicate_check": {"duplicate": False, "duplicate_of": None},
                     "wellformed_check": "single_proposition", "evidence_check": "insufficient"},
            "assumptions": [], "evidence_used": [], "language_limits": None,
            "repair_proposals": [], "docs_requests": [{"need": "Evidence for the claim.", "search_hints": ["BoE 2022"]}],
            "notes": "needs docs"}


def _edge_fails():
    return {"form": {"scope_check": "in_scope", "duplicate_check": {"duplicate": False, "duplicate_of": None},
                     "wellformed_check": "single_proposition", "evidence_check": "not_required", "inference_check": "fails"},
            "assumptions": [], "evidence_used": [], "language_limits": None,
            "repair_proposals": [], "docs_requests": [], "notes": "fails"}


def _seed(paths):
    scenario.seed_layer0(paths)


def _prove_nodes(paths, *ids):
    w = FakeProofWorker(scenario.s1_script())
    for nid in ids:
        prove_one(paths, nid, w)


# --- B6 rows ----------------------------------------------------------------


def test_row_pass_strong(project, pp):
    paths = scenario.paths_for_pp(pp)
    _seed(paths)
    res = _prove(paths, scenario.Q, scenario.node_pass_form())
    gv = graph_model.load(paths)
    assert gv.node_by_id[scenario.Q]["lifecycle_state"] == "active"
    assert gv.node_by_id[scenario.Q]["strength"] == "strong"
    assert replay.replay_reproduces(paths, res["commit"]["commit_id"])


def test_row_pass_conditional(project, pp):
    paths = scenario.paths_for_pp(pp)
    _seed(paths)
    _prove_nodes(paths, scenario.Q, scenario.T)
    res = _prove(paths, scenario.EDGE_TQ, scenario.edge_pass_form("holds_only_with_assumptions", ["an assumption"]))
    gv = graph_model.load(paths)
    edge = gv.edge_by_id[scenario.EDGE_TQ]
    assert edge["lifecycle_state"] == "active" and edge["strength"] == "conditional"
    assert edge["assumptions"] == ["an assumption"]
    assert replay.replay_reproduces(paths, res["commit"]["commit_id"])


def test_row_needs_repair_narrow(project, pp):
    paths = scenario.paths_for_pp(pp)
    _seed(paths)
    res = _prove(paths, scenario.A, _node_narrow())
    gv = graph_model.load(paths)
    a = gv.node_by_id[scenario.A]
    assert a["lifecycle_state"] == "needs_repair" and a["state_reason"] == "narrow"
    assert a["claim_version"] == 2 and a["claim"] == "A tighter single proposition."
    # an unblocked re-proof item was enqueued
    reproof = [i for i in engine.load_items(paths) if i["target_id"] == scenario.A and i["status"] == "queued"]
    assert reproof
    assert replay.replay_reproduces(paths, res["commit"]["commit_id"])


def test_row_needs_repair_bridge(project, pp):
    paths = scenario.paths_for_pp(pp)
    _seed(paths)
    _prove_nodes(paths, scenario.A, scenario.B)
    res = _prove(paths, scenario.EDGE_AB, scenario.edge_gap_form(scenario.BRIDGES))
    gv = graph_model.load(paths)
    assert gv.edge_by_id[scenario.EDGE_AB]["lifecycle_state"] == "needs_repair"
    assert len([n for n in gv.nodes if n["origin"]["kind"] == "bridge"]) == 2
    assert replay.replay_reproduces(paths, res["commit"]["commit_id"])


def test_row_needs_docs(project, pp):
    paths = scenario.paths_for_pp(pp)
    _seed(paths)
    res = _prove(paths, scenario.A, _node_docs())
    gv = graph_model.load(paths)
    assert gv.node_by_id[scenario.A]["lifecycle_state"] == "needs_docs"
    # a DocsRequest + docs_queue item were created
    reqs = jsonl.latest_records(paths.resolve("docs/docs_requests.jsonl"), "request_id")
    assert reqs and reqs[0]["status"] == "open"
    assert any(i["queue_name"] == "docs_queue" for i in engine.load_items(paths))
    assert replay.replay_reproduces(paths, res["commit"]["commit_id"])


def test_row_rejected_out_of_scope_with_cascade(project, pp):
    paths = scenario.paths_for_pp(pp)
    _seed(paths)
    res = _prove(paths, scenario.A, _node_oos())
    gv = graph_model.load(paths)
    assert gv.node_by_id[scenario.A]["lifecycle_state"] == "rejected"
    assert gv.node_by_id[scenario.A]["state_reason"] == "out_of_scope"
    # cascade: incident edge A->B rejected(endpoint_rejected), tombstoned, item cancelled
    edge = gv.edge_by_id[scenario.EDGE_AB]
    assert edge["lifecycle_state"] == "rejected" and edge["state_reason"] == "endpoint_rejected"
    tombs = jsonl.read_all(paths.resolve("graph/tombstones.jsonl"))
    assert any(t["reason"] == "endpoint_rejected" and t["target_id"] == scenario.EDGE_AB for t in tombs)
    edge_item = next(i for i in engine.load_items(paths) if i["target_id"] == scenario.EDGE_AB)
    assert edge_item["status"] == "cancelled"
    assert replay.replay_reproduces(paths, res["commit"]["commit_id"])


def test_row_rejected_duplicate(project, pp):
    paths = scenario.paths_for_pp(pp)
    _seed(paths)
    res = _prove(paths, scenario.A, _node_dup(scenario.Q))
    gv = graph_model.load(paths)
    a = gv.node_by_id[scenario.A]
    assert a["lifecycle_state"] == "rejected" and a["state_reason"] == "duplicate"
    assert a["state_detail"] == {"duplicate_of": scenario.Q}
    assert replay.replay_reproduces(paths, res["commit"]["commit_id"])


def test_row_rejected_contradicted(project, pp):
    paths = scenario.paths_for_pp(pp)
    _seed(paths)
    _prove_nodes(paths, scenario.Q, scenario.T)
    res = _prove(paths, scenario.EDGE_TQ, _edge_fails())
    gv = graph_model.load(paths)
    assert gv.edge_by_id[scenario.EDGE_TQ]["lifecycle_state"] == "rejected"
    assert gv.edge_by_id[scenario.EDGE_TQ]["state_reason"] == "contradicted"
    assert replay.replay_reproduces(paths, res["commit"]["commit_id"])


# --- B6b administrative kinds ----------------------------------------------


def test_b6b_park_unpark(project, pp):
    paths = scenario.paths_for_pp(pp)
    _seed(paths)
    _prove(paths, scenario.A, scenario.node_pass_form())
    park = committer.park(paths, scenario.A, "not_needed")
    cd = _commit(paths, park["commit_id"])
    assert cd["kind"] == "park"
    assert graph_model.load(paths).node_by_id[scenario.A]["lifecycle_state"] == "parked"
    assert replay.replay_reproduces(paths, park["commit_id"])

    un = committer.unpark(paths, scenario.A)
    assert _commit(paths, un["commit_id"])["kind"] == "unpark"
    assert graph_model.load(paths).node_by_id[scenario.A]["lifecycle_state"] == "pending_proof"


def test_b6b_freeze_unfreeze_and_frozen_refusal(project, pp):
    paths = scenario.paths_for_pp(pp)
    _seed(paths)
    _prove(paths, scenario.A, scenario.node_pass_form())
    fz = committer.freeze_batch(paths, [scenario.A], "FRZ-001")
    assert _commit(paths, fz["commit_id"])["kind"] == "freeze_batch"
    assert graph_model.load(paths).node_by_id[scenario.A]["frozen"] is True
    assert replay.replay_reproduces(paths, fz["commit_id"])

    # V-COMMIT-03: frozen record refuses mutation (park uses the frozen flag).
    with pytest.raises(Exception) as exc:
        committer.park(paths, scenario.A, "not_needed")
    assert "V-COMMIT-03" in "; ".join(getattr(exc.value, "errors", [str(exc.value)]))

    uf = committer.unfreeze_batch(paths, [scenario.A], "FRZ-001")
    assert _commit(paths, uf["commit_id"])["kind"] == "unfreeze_batch"
    gv = graph_model.load(paths)
    assert gv.node_by_id[scenario.A]["frozen"] is False
    assert gv.node_by_id[scenario.A]["lifecycle_state"] == "pending_proof"


def test_b6b_contract_reopen(project, pp):
    paths = scenario.paths_for_pp(pp)
    _seed(paths)
    _prove(paths, scenario.A, scenario.node_pass_form())
    cr = committer.contract_reopen(paths, [scenario.A], "CTR-001")
    assert _commit(paths, cr["commit_id"])["kind"] == "contract_reopen"
    assert graph_model.load(paths).node_by_id[scenario.A]["lifecycle_state"] == "pending_proof"
    assert replay.replay_reproduces(paths, cr["commit_id"])


# --- V-COMMIT-01 stale refusal ---------------------------------------------


def test_v_commit_01_stale_refusal(project, pp):
    paths = scenario.paths_for_pp(pp)
    _seed(paths)
    builder.build_frontier(paths)
    # validate B (do not commit)
    b = _prove(paths, scenario.B, scenario.node_pass_form(), commit=False)
    # narrow A -> bumps A (a 1-hop neighbor of B)
    _prove(paths, scenario.A, _node_narrow())
    # committing B now finds its bundle stale
    result = committer.apply_proof_verdict(paths, b["proof_result_id"])
    assert result.get("stale") is True
    assert engine.get_item(paths, b["work_item_id"])["status"] == "stale"


# --- V-COMMIT-06 no-op cancel on a tombstoned target -----------------------


def test_v_commit_06_noop_cancel(project, pp):
    paths = scenario.paths_for_pp(pp)
    _seed(paths)
    _prove_nodes(paths, scenario.A, scenario.B)
    # validate the A->B edge but do not commit it
    e = _prove(paths, scenario.EDGE_AB, scenario.edge_pass_form("holds"), commit=False)
    # re-open A and reject it -> cascade tombstones the A->B edge; the edge's
    # validated item survives the cascade (only queued/blocked/stale/failed cancel).
    committer.contract_reopen(paths, [scenario.A], "CTR-1")
    _prove(paths, scenario.A, _node_oos())
    # committing the edge's stale-but-validated verdict is a no-op cancel (V-COMMIT-06)
    result = committer.apply_proof_verdict(paths, e["proof_result_id"])
    assert result.get("cancelled") is True
    assert engine.get_item(paths, e["work_item_id"])["status"] == "cancelled"


# --- determinism ------------------------------------------------------------


def test_commit_decisions_byte_identical(tmp_path_factory, monkeypatch):
    monkeypatch.setenv("PAPERPROOF_NOW", "2026-07-07T00:00:00Z")
    monkeypatch.setenv("PAPERPROOF_ACTOR", "test")

    def run(root):
        paths = paths_for(root, "p4-ldi")
        project_mod.init(paths)
        scoping_build.build(paths, str(EXAMPLE_TOPIC), None)
        scoping_build.accept(paths)
        scenario.seed_layer0(paths)
        _prove_nodes(paths, scenario.A, scenario.B)
        _prove(paths, scenario.EDGE_AB, scenario.edge_gap_form(scenario.BRIDGES))
        return paths.resolve("commit/commit_decisions.jsonl").read_bytes()

    a = run(tmp_path_factory.mktemp("cd_a"))
    b = run(tmp_path_factory.mktemp("cd_b"))
    assert a == b


def _commit(paths, commit_id):
    for r in jsonl.read_all(paths.resolve("commit/commit_decisions.jsonl")):
        if r["commit_id"] == commit_id:
            return r
    raise AssertionError(commit_id)


# --- V-COMMIT-04 replay is genuine, not tautological -----------------------


def _rewrite_commit(paths, commit_id, transform):
    """Rewrite commit_decisions.jsonl applying ``transform`` to the target CD.
    (Test-only corruption of an append-only file to attack the replay check.)"""
    import json

    path = paths.resolve("commit/commit_decisions.jsonl")
    records = jsonl.read_all(path)
    for r in records:
        if r["commit_id"] == commit_id:
            transform(r)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")


def _bridge_commit(paths):
    _seed(paths)
    _prove_nodes(paths, scenario.A, scenario.B)
    res = _prove(paths, scenario.EDGE_AB, scenario.edge_gap_form(scenario.BRIDGES))
    return res["commit"]["commit_id"]


def test_replay_true_on_honest_commit(project, pp):
    paths = scenario.paths_for_pp(pp)
    cid = _bridge_commit(paths)
    assert replay.replay_reproduces(paths, cid) is True


def test_replay_false_when_action_record_id_corrupted(project, pp):
    """Corrupting an action's record id => the reconstructed post-state no longer
    matches the actual post-state => False. Proves cd['actions'] content is used."""
    paths = scenario.paths_for_pp(pp)
    cid = _bridge_commit(paths)
    assert replay.replay_reproduces(paths, cid) is True

    def corrupt(cd):
        for a in cd["actions"]:
            if a["action"] == "append_node":
                a["record"]["node_id"] = "GARBAGE-999"
                break

    _rewrite_commit(paths, cid, corrupt)
    assert replay.replay_reproduces(paths, cid) is False


def test_replay_false_when_action_record_field_corrupted(project, pp):
    paths = scenario.paths_for_pp(pp)
    cid = _bridge_commit(paths)

    def corrupt(cd):
        for a in cd["actions"]:
            if a["action"] == "update_edge":
                a["record"]["lifecycle_state"] = "active"  # commit actually set needs_repair
                break

    _rewrite_commit(paths, cid, corrupt)
    assert replay.replay_reproduces(paths, cid) is False


def test_replay_false_when_a_graph_action_dropped(project, pp):
    paths = scenario.paths_for_pp(pp)
    cid = _bridge_commit(paths)

    def drop(cd):
        for i, a in enumerate(cd["actions"]):
            if a["action"] == "append_edge":
                cd["actions"].pop(i)
                break

    _rewrite_commit(paths, cid, drop)
    assert replay.replay_reproduces(paths, cid) is False


def test_replay_false_when_graph_action_record_nulled(project, pp):
    paths = scenario.paths_for_pp(pp)
    cid = _bridge_commit(paths)

    def null_it(cd):
        for a in cd["actions"]:
            if a["action"] == "append_node":
                a["record"] = None
                break

    _rewrite_commit(paths, cid, null_it)
    assert replay.replay_reproduces(paths, cid) is False
