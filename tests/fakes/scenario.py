"""Shared scenario scaffolding for the integration tests (S1/S4/S5/S6/determinism).

Provides a Paths builder, a layer-0 seed helper, and form-script builders so each
scenario file stays focused on its assertions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from paperproof.expander import ingest as expander
from paperproof.paths import Paths, paths_for
from paperproof.store import jsonl, snapshot


def paths_for_pp(pp) -> Paths:
    return paths_for(pp.tmp_path, "p4-ldi")


def node_pass_form(evidence: str = "not_required") -> dict[str, Any]:
    return {
        "form": {
            "scope_check": "in_scope",
            "duplicate_check": {"duplicate": False, "duplicate_of": None},
            "wellformed_check": "single_proposition",
            "evidence_check": evidence,
        },
        "assumptions": [],
        "evidence_used": [],
        "language_limits": {"allowed": ["Allowed strong wording."], "forbidden": ["An overclaim to avoid."]},
        "repair_proposals": [],
        "docs_requests": [],
        "notes": "scripted pass",
    }


def edge_pass_form(inference: str = "holds", assumptions: list[str] | None = None) -> dict[str, Any]:
    return {
        "form": {
            "scope_check": "in_scope",
            "duplicate_check": {"duplicate": False, "duplicate_of": None},
            "wellformed_check": "single_proposition",
            "evidence_check": "not_required",
            "inference_check": inference,
        },
        "assumptions": assumptions or [],
        "evidence_used": [],
        "language_limits": {"allowed": ["Allowed edge wording."], "forbidden": ["Edge overclaim."]},
        "repair_proposals": [],
        "docs_requests": [],
        "notes": "scripted edge",
    }


def edge_gap_form(bridges: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "form": {
            "scope_check": "in_scope",
            "duplicate_check": {"duplicate": False, "duplicate_of": None},
            "wellformed_check": "single_proposition",
            "evidence_check": "not_required",
            "inference_check": "gap",
        },
        "assumptions": [],
        "evidence_used": [],
        "language_limits": None,
        "repair_proposals": bridges,
        "docs_requests": [],
        "notes": "gap needs bridges",
    }


def seed_layer0(paths: Paths, actor: str = "test") -> dict[str, Any]:
    """Ingest the S1 layer-0 seed: Q, T, A, B + edges T->Q, A->B, B->T.

    A and B are definition nodes so they can be proven with evidence not_required
    in M1 (no Docs pipeline yet). Returns the ingest result (assigned_ids)."""
    snap = snapshot.latest_snapshot_id(paths)
    proposal = {
        "schema_version": "expansion_proposal.v1",
        "proposal_id": "EXP-BFS-MAIN-L0",
        "project_id": "p4-ldi",
        "bfs_id": "BFS-MAIN",
        "layer": 0,
        "based_on_snapshot": snap,
        "nodes": [
            {"claim": "Why can pension de-risking transform solvency risk into liquidity risk?", "node_type": "question", "scope": {}, "parents": []},
            {"claim": "De-risking via leveraged LDI converts solvency hedging into liquidity stress.", "node_type": "thesis", "scope": {}, "parents": []},
            {"claim": "Solvency risk and liquidity risk are distinct risk categories.", "node_type": "definition", "scope": {}, "parents": []},
            {"claim": "Leveraged LDI links gilt yield movements to collateral demand.", "node_type": "definition", "scope": {}, "parents": []},
        ],
        # A->B (the gap edge) is listed last so it commits last under FIFO drain,
        # after B->T, keeping the bridge-wiring commit free of queued siblings.
        "edges": [
            {"source_ref": "#1", "target_ref": "#0", "edge_type": "supports", "edge_claim": "The thesis, if established, resolves the research question."},
            {"source_ref": "#3", "target_ref": "#1", "edge_type": "supports", "edge_claim": "The transmission mechanism supports the de-risking thesis."},
            {"source_ref": "#2", "target_ref": "#3", "edge_type": "supports", "edge_claim": "The risk distinction underpins the transmission mechanism."},
        ],
    }
    pf = paths.resolve("agent_outputs/expansions/EXP-BFS-MAIN-L0.json")
    pf.parent.mkdir(parents=True, exist_ok=True)
    pf.write_text(json.dumps(proposal), encoding="utf-8")
    return expander.ingest(paths, str(pf), actor)


# Standard target ids after seed_layer0 (deterministic id allocation).
Q, T, A, B = "NODE-001", "NODE-002", "NODE-003", "NODE-004"
EDGE_TQ, EDGE_AB, EDGE_BT = "EDGE-002-001", "EDGE-003-004", "EDGE-004-002"

BRIDGES = [
    {"kind": "bridge", "claim": "Collateral buffers can be outpaced by rapid repricing.", "node_type": "definition"},
    {"kind": "bridge", "claim": "Forced gilt sales amplify the initial yield movement.", "node_type": "definition"},
]


# --- S2/S3 docs-loop scaffolding -------------------------------------------

# A need reused across requests so the fingerprint cache resolves an identical
# second request (docs/04).
DOCS_NEED = "Evidence on the size and speed of LDI collateral calls in 2022."
DOCS_HINTS = ["BoE FSR 2022", "gilt crisis LDI margin"]

# A claim + matching EvidenceUnit engineered so the matcher (score >= 2, scope
# compatible) selects the EU for the claim's DocsPack (docs/04).
FACT_CLAIM = "LDI margin calls created acute liquidity pressure in 2022."


def node_insufficient_form(need: str = DOCS_NEED, hints: list[str] | None = None) -> dict[str, Any]:
    """A fact-node form answering evidence insufficient (=> needs_docs)."""
    return {
        "form": {
            "scope_check": "in_scope",
            "duplicate_check": {"duplicate": False, "duplicate_of": None},
            "wellformed_check": "single_proposition",
            "evidence_check": "insufficient",
        },
        "assumptions": [],
        "evidence_used": [],
        "language_limits": None,
        "repair_proposals": [],
        "docs_requests": [{"need": need, "search_hints": list(hints or DOCS_HINTS)}],
        "notes": "insufficient evidence in pack",
    }


def node_sufficient_form(evidence_ids: list[str]) -> dict[str, Any]:
    """A fact-node form answering evidence sufficient (=> pass strong)."""
    return {
        "form": {
            "scope_check": "in_scope",
            "duplicate_check": {"duplicate": False, "duplicate_of": None},
            "wellformed_check": "single_proposition",
            "evidence_check": "sufficient",
        },
        "assumptions": [],
        "evidence_used": list(evidence_ids),
        "language_limits": {"allowed": ["Strong wording the evidence carries."], "forbidden": ["An overclaim to avoid."]},
        "repair_proposals": [],
        "docs_requests": [],
        "notes": "evidence sufficient",
    }


def node_contradicting_form(evidence_ids: list[str]) -> dict[str, Any]:
    """A fact-node form answering evidence contradicting (=> rejected)."""
    return {
        "form": {
            "scope_check": "in_scope",
            "duplicate_check": {"duplicate": False, "duplicate_of": None},
            "wellformed_check": "single_proposition",
            "evidence_check": "contradicting",
        },
        "assumptions": [],
        "evidence_used": list(evidence_ids),
        "language_limits": None,
        "repair_proposals": [],
        "docs_requests": [],
        "notes": "evidence contradicts the claim",
    }


def boe_docs_result_spec() -> dict[str, Any]:
    """A scripted DocsResult (web source, inline text) whose EvidenceUnit's quote
    is verbatim in the text (V-DR-05) and whose can_cite_for matches FACT_CLAIM."""
    text = (
        "In September 2022 LDI margin calls created acute liquidity pressure as "
        "collateral calls exceeded liquid buffers within days."
    )
    return {
        "documents": [
            {
                "title": "Bank of England Financial Stability Report, Nov 2022",
                "source_type": "official_report",
                "origin": {"kind": "web", "path": None, "url": "https://boe.example/fsr-2022"},
                "citation_key": "BoE2022FSR",
                "text": text,
            }
        ],
        "evidence_units": [
            {
                "doc_ref": 0,
                "doc_id": None,
                "location": "p.12, Section 3.2",
                "kind": "quote",
                "quote_or_paraphrase": "LDI margin calls created acute liquidity pressure",
                "summary": "LDI margin calls created acute liquidity pressure in 2022",
                "support_direction": "supports",
                "can_cite_for": [FACT_CLAIM],
                "cannot_cite_for": ["all de-risking strategies create liquidity crises"],
                "scope": {},
            }
        ],
        "not_found": False,
        "search_log": ["boe fsr 2022 ldi margin calls"],
    }


def seed_docs_facts(paths: Paths, fact_claims: list[str], actor: str = "test") -> dict[str, Any]:
    """Ingest a layer-0 seed: Q, T, and one fact node per claim, each supporting
    T (so the facts are reachable). Returns the ingest result (assigned_ids)."""
    snap = snapshot.latest_snapshot_id(paths)
    nodes = [
        {"claim": "How did leveraged LDI transform solvency risk into liquidity risk in 2022?", "node_type": "question", "scope": {}, "parents": []},
        {"claim": "Leveraged LDI converted solvency hedging into acute liquidity stress in 2022.", "node_type": "thesis", "scope": {}, "parents": []},
    ]
    for c in fact_claims:
        nodes.append({"claim": c, "node_type": "fact", "scope": {}, "parents": []})
    edges = [
        {"source_ref": "#1", "target_ref": "#0", "edge_type": "supports", "edge_claim": "The thesis, if established, answers the research question."},
    ]
    for i in range(len(fact_claims)):
        edges.append({"source_ref": f"#{2 + i}", "target_ref": "#1", "edge_type": "supports",
                      "edge_claim": f"Fact {i + 1} provides empirical support for the thesis."})
    proposal = {
        "schema_version": "expansion_proposal.v1", "proposal_id": "EXP-BFS-MAIN-L0",
        "project_id": "p4-ldi", "bfs_id": "BFS-MAIN", "layer": 0, "based_on_snapshot": snap,
        "nodes": nodes, "edges": edges,
    }
    pf = paths.resolve("agent_outputs/expansions/EXP-BFS-MAIN-L0.json")
    pf.parent.mkdir(parents=True, exist_ok=True)
    pf.write_text(json.dumps(proposal), encoding="utf-8")
    return expander.ingest(paths, str(pf), actor)


# --- S7 full-pipeline scaffolding ------------------------------------------

# Spine ids after seed_s7_layer0 + the layer-1 concept D2 (deterministic).
S7_Q, S7_T, S7_M, S7_D = "NODE-001", "NODE-002", "NODE-003", "NODE-004"
S7_D2 = "NODE-005"
S7_EDGE_TQ = "EDGE-002-001"
S7_EDGE_MT = "EDGE-003-002"
S7_EDGE_DM = "EDGE-004-003-dep"
S7_EDGE_D2D = "EDGE-005-004-dep"


def ingest_expansion(
    paths: Paths,
    proposal_id: str,
    bfs_id: str,
    layer: int,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    actor: str = "test",
) -> dict[str, Any]:
    """Write + `expand ingest` an ExpansionProposal (used for layer 1 and the
    empty lane-closing proposals)."""
    proposal = {
        "schema_version": "expansion_proposal.v1",
        "proposal_id": proposal_id,
        "project_id": "p4-ldi",
        "bfs_id": bfs_id,
        "layer": layer,
        "based_on_snapshot": snapshot.latest_snapshot_id(paths),
        "nodes": nodes,
        "edges": edges,
    }
    pf = paths.resolve(f"agent_outputs/expansions/{proposal_id}.json")
    pf.parent.mkdir(parents=True, exist_ok=True)
    pf.write_text(json.dumps(proposal), encoding="utf-8")
    return expander.ingest(paths, str(pf), actor)


def seed_s7_layer0(paths: Paths, actor: str = "test") -> dict[str, Any]:
    """BFS-MAIN layer 0: Q, T, M(mechanism, needs evidence), D(definition).
    Edges: T->Q, M->T, D->M(depends_on). M's claim = FACT_CLAIM so the docs
    matcher selects the archived BoE EvidenceUnit into M's re-proof pack."""
    proposal = {
        "schema_version": "expansion_proposal.v1",
        "proposal_id": "EXP-BFS-MAIN-L0",
        "project_id": "p4-ldi",
        "bfs_id": "BFS-MAIN",
        "layer": 0,
        "based_on_snapshot": snapshot.latest_snapshot_id(paths),
        "nodes": [
            {"claim": "How did leveraged LDI transform solvency risk into liquidity risk in 2022?", "node_type": "question", "scope": {}, "parents": []},
            {"claim": "Leveraged LDI converted solvency hedging into acute liquidity stress in 2022.", "node_type": "thesis", "scope": {}, "parents": []},
            {"claim": FACT_CLAIM, "node_type": "mechanism", "scope": {}, "parents": []},
            {"claim": "Solvency risk and liquidity risk are distinct risk categories.", "node_type": "definition", "scope": {}, "parents": []},
        ],
        "edges": [
            {"source_ref": "#1", "target_ref": "#0", "edge_type": "supports", "edge_claim": "The thesis, if established, answers the research question."},
            {"source_ref": "#2", "target_ref": "#1", "edge_type": "supports", "edge_claim": "The transmission mechanism supports the de-risking thesis."},
            {"source_ref": "#3", "target_ref": "#2", "edge_type": "depends_on", "edge_claim": "The risk distinction underpins the transmission mechanism."},
        ],
    }
    pf = paths.resolve("agent_outputs/expansions/EXP-BFS-MAIN-L0.json")
    pf.parent.mkdir(parents=True, exist_ok=True)
    pf.write_text(json.dumps(proposal), encoding="utf-8")
    return expander.ingest(paths, str(pf), actor)


def s7_script() -> dict[str, Any]:
    """Scripted proof worker table for the whole S7 pipeline, keyed by target id."""
    return {
        S7_Q: node_pass_form(),
        S7_T: node_pass_form(),
        # mechanism M: insufficient -> needs_docs -> (docs) -> sufficient(strong).
        S7_M: [node_insufficient_form(), node_sufficient_form(["EU-001"])],
        S7_D: node_pass_form(),
        S7_D2: node_pass_form(),
        S7_EDGE_TQ: edge_pass_form("holds"),
        S7_EDGE_MT: edge_pass_form("holds"),
        S7_EDGE_DM: edge_pass_form("holds"),
        S7_EDGE_D2D: edge_pass_form("holds"),
    }


def monitor_fixture(paths: Paths) -> dict[str, Any]:
    """An S7-shaped project state that exercises all six Overview questions
    (docs/12 §9) at once, built with FakeWorkers:

      * BFS-MAIN seed loop fully proved + committed (Q,T,A,B + bridges active);
      * the thesis locally frozen                       -> frozen = 1;
      * a fresh BFS-MAIN layer-1 expansion (3 definition nodes + 2 depends_on
        edges) opens new work:
          NODE-007 claimed by worker-1, NODE-008 claimed by worker-2  -> working=2;
          the two edges blocked_by their endpoints                     -> blocked=2;
          NODE-009 proved to *validated* (not committed)               -> committable=1;
          open (queued/claimed/blocked) work items                     -> open=4.

    Returns the expected counts + key ids so both the API test and the S8 test can
    assert against one deterministic fixture.
    """
    from paperproof.freeze import apply as freeze_mod
    from paperproof.prooftask import builder
    from paperproof.queue import engine

    from tests.fakes.workers import FakeProofWorker, drain, prove_one

    seed_layer0(paths)
    drain(paths, FakeProofWorker(s1_script()))
    freeze_mod.apply(paths, T, "local")

    ingest_expansion(
        paths, "EXP-BFS-MAIN-L1", "BFS-MAIN", 1,
        nodes=[
            {"claim": "Collateral haircuts widened materially during the stress window.", "node_type": "definition", "scope": {}, "parents": [B]},
            {"claim": "Repo funding tightened as haircuts widened.", "node_type": "definition", "scope": {}, "parents": [B]},
            {"claim": "Dealer intermediation capacity contracted under the funding strain.", "node_type": "definition", "scope": {}, "parents": [B]},
        ],
        edges=[
            {"source_ref": "#0", "target_ref": "#1", "edge_type": "depends_on", "edge_claim": "Haircut widening underpins the repo funding tightening."},
            {"source_ref": "#1", "target_ref": "#2", "edge_type": "depends_on", "edge_claim": "Repo tightening underpins the dealer capacity contraction."},
        ],
    )
    builder.build_frontier(paths, "test")

    def _wi(target_id: str) -> str:
        return next(i["work_item_id"] for i in engine.load_items(paths)
                    if i["target_id"] == target_id and i["status"] == "queued")

    engine.claim(paths, queue_name="proof_queue", agent="worker-1", wi_id=_wi("NODE-007"))
    engine.claim(paths, queue_name="proof_queue", agent="worker-2", wi_id=_wi("NODE-008"))
    prove_one(paths, "NODE-009", FakeProofWorker({"NODE-009": node_pass_form()}), commit=False)

    return {
        "expected": {"open": 4, "working": 2, "blocked": 2, "committable": 1, "frozen": 1, "dead": 0},
        "frozen_id": T,
        "claimed": {"worker-1": "NODE-007", "worker-2": "NODE-008"},
        "validated_node": "NODE-009",
    }


def s1_script() -> dict[str, Any]:
    """A scripted worker table for the whole S1 loop keyed by target id."""
    return {
        Q: node_pass_form(),
        T: node_pass_form(),
        A: node_pass_form(),
        B: node_pass_form(),
        EDGE_TQ: edge_pass_form("holds"),
        EDGE_BT: edge_pass_form("holds"),
        # first proof -> gap (bridges); re-proof -> pass(conditional)
        EDGE_AB: [
            edge_gap_form(BRIDGES),
            edge_pass_form("holds_only_with_assumptions", ["Rapid repricing outpaces collateral buffers."]),
        ],
        # bridge nodes/edges (created by the Committer as NODE-005/006 + edges)
        "NODE-005": node_pass_form(),
        "NODE-006": node_pass_form(),
        "EDGE-005-004-dep": edge_pass_form("holds"),
        "EDGE-006-004-dep": edge_pass_form("holds"),
    }
