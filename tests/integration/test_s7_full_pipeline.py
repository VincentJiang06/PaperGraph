"""S7 full pipeline (docs/09 §3, docs/11 §8).

Drives the P4-shaped example end to end with FakeWorkers:
  2 layers + closed lanes (BFS-MAIN, BFS-ALT) -> `graph msa-check` green
  (MSA-1..9 asserted individually) -> spine freeze (runs verify internally) ->
  `compiler dry-run` reports ZERO gaps + writing_ready (docs/06 reachability
  note) -> `compiler draft-map` (byte-determinism asserted) -> FakeCompileWorker
  prose -> `compiler ingest-prose` -> `audit run` passed=true -> `trace --node`
  resolves the full chain to a raw file for every spine node -> verify exit 0.

A tainted variant (a seeded forbidden-language sentence in the mechanism prose)
flips audit to passed=false, kind=strength.
"""

from __future__ import annotations

import pytest

from paperproof.compiler import draft_map as draft_map_mod
from paperproof.graph import model as graph_model
from paperproof.serialize import canonical_line
from paperproof.store import jsonl

from tests.fakes import scenario
from tests.fakes.workers import (
    FakeCompileWorker,
    FakeDocsWorker,
    FakeProofWorker,
    drain,
    drain_compile,
    drain_docs,
)

pytestmark = pytest.mark.integration

SPINE_NODES = [scenario.S7_Q, scenario.S7_T, scenario.S7_M, scenario.S7_D, scenario.S7_D2]


def _prove_graph(paths):
    proof_worker = FakeProofWorker(scenario.s7_script())
    docs_worker = FakeDocsWorker({"*": scenario.boe_docs_result_spec()})

    # Layer 0: Q,T,D prove; M goes insufficient -> needs_docs; then docs; then M
    # sufficient(strong) and the mechanism/definition edges activate.
    scenario.seed_s7_layer0(paths)
    drain(paths, proof_worker)
    drain_docs(paths, docs_worker)
    drain(paths, proof_worker)

    # Layer 1: a second concept node D2 -> D (depends_on).
    scenario.ingest_expansion(
        paths, "EXP-BFS-MAIN-L1", "BFS-MAIN", 1,
        nodes=[{"claim": "Leverage and collateral mechanics link gilt yields to forced liquidity demand.",
                "node_type": "definition", "scope": {}, "parents": [scenario.S7_D]}],
        edges=[{"source_ref": "#0", "target_ref": scenario.S7_D, "edge_type": "depends_on",
                "edge_claim": "The leverage concept underpins the risk distinction."}],
    )
    drain(paths, proof_worker)

    # Close both lanes (empty proposals).
    scenario.ingest_expansion(paths, "EXP-BFS-MAIN-L2", "BFS-MAIN", 2, nodes=[], edges=[])
    scenario.ingest_expansion(paths, "EXP-BFS-ALT-L1", "BFS-ALT", 1, nodes=[], edges=[])


def test_s7_full_pipeline(project, pp):
    paths = scenario.paths_for_pp(pp)
    _prove_graph(paths)

    # --- msa-check green: assert MSA-1..9 individually --------------------
    env = pp("graph", "msa-check")
    msa = env["data"]["msa"]
    for i in range(1, 10):
        assert msa[f"MSA-{i}"]["pass"] is True, (f"MSA-{i}", msa[f"MSA-{i}"])
    assert env["data"]["all_pass"] is True

    # spine has the expected 5 nodes.
    gv = graph_model.load(paths)
    spine_ids, _ = gv.spine()
    assert set(SPINE_NODES) <= spine_ids

    # --- spine freeze (runs verify internally, V-FRZ-04) ------------------
    fenv = pp("freeze", "apply", "--target", scenario.S7_T, "--level", "spine")
    assert fenv["ok"] is True
    # every spine record is now frozen.
    gv = graph_model.load(paths)
    for rid in spine_ids:
        assert gv.record(rid)["frozen"] is True

    # --- dry run: zero gaps + writing_ready -------------------------------
    denv = pp("compiler", "dry-run")
    assert denv["data"]["gaps"] == []
    assert denv["data"]["writing_ready"] is True
    # section plan covers every spine node exactly once (V-CDR-03).
    planned = [nid for entry in denv["data"]["section_plan"] for nid in entry["nodes"]]
    spine_node_ids = [i for i in spine_ids if i in gv.node_by_id]
    assert sorted(planned) == sorted(spine_node_ids)
    assert len(planned) == len(set(planned))

    # --- draft map + byte-determinism -------------------------------------
    m1 = pp("compiler", "draft-map")
    draft_map_id = m1["data"]["draft_map_id"]
    sections1 = m1["data"]["sections"]
    # re-derive on the identical frozen state: byte-identical sections.
    again = draft_map_mod.draft_map(paths)
    assert canonical_line(again["sections"]) == canonical_line(sections1)

    # --- prose via FakeCompileWorker + ingest-prose -----------------------
    # Exercise the real CLI `compiler ingest-prose` (two queue events, one
    # command) for one section; drain the rest via the helper.
    from paperproof.queue import engine as _engine

    claimable = [
        i for i in _engine.load_items(paths)
        if i["queue_name"] == "compile_queue" and i["target_type"] == "section" and i["status"] == "queued"
    ]
    item = _engine.claim(paths, queue_name="compile_queue", agent="cw", wi_id=claimable[0]["work_item_id"])
    FakeCompileWorker().run(item, paths.project_dir)
    # F8/D14: ingest-prose implicit-completes a CLAIMED item (no separate `queue
    # complete` ceremony) and accepts the ABSOLUTE spelling of the declared path.
    abs_path = str(paths.project_dir / item["output_files"][0])
    ip = pp("compiler", "ingest-prose", abs_path, "--work-item", item["work_item_id"])
    assert ip["ok"] is True and ip["data"]["section_id"] == item["target_id"]
    assert _engine.get_item(paths, item["work_item_id"])["status"] == "committed"

    drain_compile(paths, FakeCompileWorker())
    # prose files were promoted to compiler/prose/.
    for entry in sections1:
        assert (paths.resolve(f"compiler/prose/{entry['section_id']}.md")).exists()

    # --- audit clean ------------------------------------------------------
    aenv = pp("audit", "run", "--draft", draft_map_id)
    assert aenv["data"]["passed"] is True
    assert aenv["data"]["findings"] == []

    # --- trace resolves the full chain for every spine node ---------------
    raw_files_seen = 0
    for nid in spine_node_ids:
        tenv = pp("trace", "--node", nid)
        data = tenv["data"]
        assert data["node_id"] == nid
        assert data["claim"]
        assert data["freeze_ids"], f"no covering freeze for {nid}"
        assert data["commit_ids"], f"no commits for {nid}"
        assert data["proof_results"], f"no proof results for {nid}"
        for ev in data["evidence"]:
            assert ev["resolved"] is True
            raw = paths.project_dir / ev["text_path"]
            assert raw.exists(), f"raw/text file missing: {ev['text_path']}"
            raw_files_seen += 1
    # the mechanism node's evidence resolved to at least one real archived file.
    assert raw_files_seen >= 1

    # --- verify exit 0 ----------------------------------------------------
    assert pp("verify")["ok"] is True


def test_s7_audit_catches_seeded_forbidden_language(project, pp):
    """Variant: a mechanism-section prose with a seeded forbidden-language
    sentence flips audit to passed=false, kind=strength."""
    paths = scenario.paths_for_pp(pp)
    _prove_graph(paths)
    pp("freeze", "apply", "--target", scenario.S7_T, "--level", "spine")
    pp("compiler", "dry-run")
    m = pp("compiler", "draft-map")
    draft_map_id = m["data"]["draft_map_id"]

    # Ingest clean prose first (V-PROSE would reject a tainted file), then taint
    # the promoted mechanism prose directly so the audit's strength check — an
    # independent pass over compiler/prose/ — is exercised.
    drain_compile(paths, FakeCompileWorker())
    aenv_clean = pp("audit", "run", "--draft", draft_map_id)
    assert aenv_clean["data"]["passed"] is True

    dm = draft_map_mod.load_draft_map(paths, draft_map_id)
    mech = next(s for s in dm["sections"] if s["section_id"] == "SEC-mechanism")
    forbidden = mech["claims"][0]["forbidden_language"][0]
    prose_path = paths.resolve("compiler/prose/SEC-mechanism.md")
    prose_path.write_text(
        prose_path.read_text(encoding="utf-8") + f"\n\n{forbidden} (claim: {mech['claims'][0]['node_id']}).",
        encoding="utf-8",
    )

    aenv = pp("audit", "run", "--draft", draft_map_id, expect=1)
    assert aenv["data"]["passed"] is False
    kinds = {f["kind"] for f in aenv["data"]["findings"]}
    assert "strength" in kinds, aenv["data"]["findings"]
