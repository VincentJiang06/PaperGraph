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
