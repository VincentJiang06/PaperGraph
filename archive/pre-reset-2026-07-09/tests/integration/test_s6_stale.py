"""S6 staleness rebuild (docs/09 §3, docs/11 §8).

A commit lands between a bundle build and the item's claim, mutating a 1-hop
neighbor -> the item is marked stale -> `proof build-tasks` rebuilds it as -r2
(the old bundle files remain, immutable) -> the re-proof verdict cites the -r2
bundle paths.

Concretely: after building bundles for A and B (connected by edge A->B), a NARROW
commit on A bumps A's claim_version. A is in B's 1-hop, so B's queued item is
marked stale; B rebuilds as -r2 before it is ever claimed.
"""

from __future__ import annotations

import pytest

from paperproof.graph import model as graph_model
from paperproof.prooftask import builder
from paperproof.queue import engine
from paperproof.store import jsonl

from tests.fakes import scenario
from tests.fakes.workers import FakeProofWorker, prove_one

pytestmark = pytest.mark.integration


def _narrow_spec():
    return {
        "form": {
            "scope_check": "in_scope",
            "duplicate_check": {"duplicate": False, "duplicate_of": None},
            "wellformed_check": "too_broad",
            "evidence_check": "not_evaluated",
        },
        "assumptions": [],
        "evidence_used": [],
        "language_limits": None,
        "repair_proposals": [{"kind": "narrow", "narrowed_claim": "Solvency and liquidity risk are distinct in the 2022 UK LDI episode."}],
        "docs_requests": [],
        "notes": "too broad",
    }


def test_s6_stale_rebuild(project, pp):
    paths = scenario.paths_for_pp(pp)
    scenario.seed_layer0(paths)
    builder.build_frontier(paths)  # builds -r1 bundles for all four node checks

    b_item = next(i for i in engine.load_items(paths) if i["target_id"] == scenario.B)
    old_ctx = b_item["bundle"]["context_pack"]
    assert old_ctx == "proof/context/CTX-NODE-004.json"
    old_ctx_path = paths.resolve(old_ctx)
    assert old_ctx_path.exists()

    # A NARROW commit on A (NODE-003) bumps A's claim_version; A is in B's 1-hop.
    worker = FakeProofWorker({scenario.A: _narrow_spec(), scenario.B: scenario.node_pass_form()})
    prove_one(paths, scenario.A, worker)

    # B's queued item is now stale, and claim refuses it (V-TASK-01).
    b_item = engine.get_item(paths, b_item["work_item_id"])
    assert b_item["status"] == "stale"

    # rebuild: -r2 bundle, old bundle files still present (immutability).
    builder.build_frontier(paths)
    b_item = engine.get_item(paths, b_item["work_item_id"])
    assert b_item["status"] == "queued"
    assert b_item["bundle"]["context_pack"] == "proof/context/CTX-NODE-004-r2.json"
    assert old_ctx_path.exists(), "old -r1 bundle must remain immutable"
    assert paths.resolve("proof/context/CTX-NODE-004-r2.json").exists()

    # re-prove B; the verdict record cites the -r2 bundle.
    prove_one(paths, scenario.B, worker)
    verdicts = [r for r in jsonl.read_all(paths.resolve("proof/proof_results.jsonl")) if r["target_id"] == scenario.B]
    assert verdicts[-1]["bundle"]["context_pack"] == "proof/context/CTX-NODE-004-r2.json"

    gv = graph_model.load(paths)
    assert gv.node_by_id[scenario.B]["lifecycle_state"] == "active"

    env = pp("verify")
    assert env["ok"] is True
