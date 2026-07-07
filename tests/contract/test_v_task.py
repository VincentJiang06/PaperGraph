"""V-TASK contract tests (docs/09): bundle self-containment, 1-hop content,
DocsPack resolution. Staleness/-rN revision (V-TASK-01) is covered by S6.
"""

from __future__ import annotations

import copy

import pytest

from paperproof.prooftask import builder
from paperproof.queue import engine
from paperproof.store import jsonl
from paperproof.validate.rules import v_task

from tests.fakes import scenario

pytestmark = pytest.mark.contract


def _b_context_pack(paths):
    builder.build_frontier(paths)
    b_item = next(i for i in engine.load_items(paths) if i["target_id"] == scenario.B)
    return jsonl.read_json(paths.resolve(b_item["bundle"]["context_pack"]))


def test_v_task_02_valid_context_pack(project, pp):
    paths = scenario.paths_for_pp(pp)
    scenario.seed_layer0(paths)
    ctx = _b_context_pack(paths)
    # a fresh bundle satisfies V-TASK-02
    assert v_task.check_context_pack(paths, ctx) == []
    # the claim_digest covers every non-rejected node
    digest_ids = {d["node_id"] for d in ctx["claim_digest"]}
    assert digest_ids == {scenario.Q, scenario.T, scenario.A, scenario.B}
    # the target is present verbatim
    assert ctx["target"]["node_id"] == scenario.B


def test_v_task_02_corrupted_neighbors_fail(project, pp):
    paths = scenario.paths_for_pp(pp)
    scenario.seed_layer0(paths)
    ctx = _b_context_pack(paths)
    bad = copy.deepcopy(ctx)
    bad["neighbor_nodes"] = []  # B has A as a 1-hop neighbor via edge A->B
    fired = [f.rule_id for f in v_task.check_context_pack(paths, bad)]
    assert "V-TASK-02" in fired


def test_v_task_03_docs_pack_resolution(project, pp):
    paths = scenario.paths_for_pp(pp)
    scenario.seed_layer0(paths)
    # empty DocsPack is valid (M1)
    assert v_task.check_docs_pack(paths, {"evidence_units": []}) == []
    # a DocsPack citing a non-archived doc fails
    bad = {"evidence_units": [{"doc_id": "DOC-999"}]}
    assert "V-TASK-03" in [f.rule_id for f in v_task.check_docs_pack(paths, bad)]
