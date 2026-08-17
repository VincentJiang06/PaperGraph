"""Unit tests for id allocation and formats (docs/07)."""

from __future__ import annotations

import pytest

from paperproof import ids

pytestmark = pytest.mark.unit


def test_next_id_allocation_and_widths():
    assert ids.next_id("NODE", []) == "NODE-001"
    assert ids.next_id("NODE", ["NODE-001", "NODE-005"]) == "NODE-006"
    assert ids.next_id("WI", []) == "WI-000001"
    assert ids.next_id("GS", ["GS-000001"]) == "GS-000002"
    assert ids.next_id("PR", ["PR-001", "PR-002", "PR-009"]) == "PR-010"


def test_node_id():
    assert ids.node_id([]) == "NODE-001"
    assert ids.node_id(["NODE-001", "NODE-002"]) == "NODE-003"


def test_edge_id_type_suffixes_coexist():
    assert ids.edge_id("NODE-001", "NODE-002", "supports", []) == "EDGE-001-002"
    assert ids.edge_id("NODE-001", "NODE-002", "depends_on", []) == "EDGE-001-002-dep"
    assert ids.edge_id("NODE-001", "NODE-002", "refutes", []) == "EDGE-001-002-ref"
    # all three can coexist between the same endpoints (distinct ids)
    existing = ["EDGE-001-002", "EDGE-001-002-dep", "EDGE-001-002-ref"]
    assert len(set(existing)) == 3


def test_edge_id_version_reuse_after_rejection():
    existing = ["EDGE-001-002"]
    assert ids.edge_id("NODE-001", "NODE-002", "supports", existing) == "EDGE-001-002-v2"
    existing.append("EDGE-001-002-v2")
    assert ids.edge_id("NODE-001", "NODE-002", "supports", existing) == "EDGE-001-002-v3"
    # -dep versioning is independent of bare supports
    dep = ["EDGE-001-002-dep"]
    assert ids.edge_id("NODE-001", "NODE-002", "depends_on", dep) == "EDGE-001-002-dep-v2"


def test_bundle_ids_and_revisions():
    assert ids.bundle_id("PT", "NODE-001", 1) == "PT-NODE-001"
    assert ids.bundle_id("PT", "NODE-001", 2) == "PT-NODE-001-r2"
    assert ids.bundle_id("CTX", "EDGE-001-002", 1) == "CTX-EDGE-001-002"
    assert ids.bundle_id("DOCSPACK", "EDGE-001-002", 3) == "DOCSPACK-EDGE-001-002-r3"


def test_next_bundle_revision():
    assert ids.next_bundle_revision("PT", "NODE-001", []) == 1
    assert ids.next_bundle_revision("PT", "NODE-001", ["PT-NODE-001"]) == 2
    assert (
        ids.next_bundle_revision("PT", "NODE-001", ["PT-NODE-001", "PT-NODE-001-r2"]) == 3
    )
    # a different target's bundles do not bump this target's revision
    assert ids.next_bundle_revision("PT", "NODE-001", ["PT-NODE-002", "PT-NODE-002-r5"]) == 1
