"""V-EDGE-02 contract tests (docs/09): edge_claim must not verbatim-restate an
endpoint claim. Wired into the commit-time graph check (V-COMMIT-05 path) and
verify via graph_record_checks. The bridge-synthesized edge_claim must PASS.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from paperproof.validate.rules import v_node_edge

pytestmark = pytest.mark.contract

VRULES = Path(__file__).resolve().parent.parent / "fixtures" / "vrules" / "V-EDGE-02"


def _run(fixture: dict) -> list[str]:
    failures = v_node_edge.graph_record_checks(fixture["nodes"], fixture["edges"])
    return [f.rule_id for f in failures]


@pytest.mark.parametrize("path", sorted(VRULES.glob("*.json")))
def test_v_edge_02_fixtures(path):
    fixture = json.loads(path.read_bytes())
    fired = _run(fixture)
    if path.name.startswith("fail_"):
        assert "V-EDGE-02" in fired, (path.name, fired)
    else:
        assert "V-EDGE-02" not in fired, (path.name, fired)


def test_bridge_synthesized_edge_claim_passes_v_edge_02():
    """The Committer's synthesized bridge edge_claim satisfies V-EDGE-02."""
    x_claim = "Solvency and liquidity risk are distinct categories."
    b_claim = "Leveraged LDI links gilt yields to collateral demand."
    edge_claim = f"Bridge premise supporting the inference: {x_claim}"
    ok, _ = v_node_edge.edge02_ok(edge_claim, x_claim, b_claim)
    assert ok


def test_edge_claim_equal_to_endpoint_fails_v_edge_02():
    ok, _ = v_node_edge.edge02_ok("Alpha claim.", "alpha claim.", "Beta.")
    assert not ok
