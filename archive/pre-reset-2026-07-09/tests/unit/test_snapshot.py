"""Unit tests for graph snapshots (docs/07 §Snapshots)."""

from __future__ import annotations

import pytest

from paperproof.paths import paths_for
from paperproof.project import init as project_init
from paperproof.store import jsonl, snapshot

pytestmark = pytest.mark.unit


@pytest.fixture
def initialized(tmp_path, clock):
    paths = paths_for(tmp_path, "p4-ldi")
    project_init(paths)
    return paths


def test_init_creates_gs_000001_over_empty_graph(initialized):
    paths = initialized
    records = jsonl.read_all(paths.snapshots)
    assert len(records) == 1
    assert records[0]["snapshot_id"] == "GS-000001"
    files = records[0]["files"]
    assert set(files) == {
        "graph/logic_nodes.jsonl",
        "graph/logic_edges.jsonl",
        "graph/tombstones.jsonl",
    }
    assert all(f["rows"] == 0 for f in files.values())


def test_take_verify_current(initialized):
    paths = initialized
    assert snapshot.is_current(paths, "GS-000001")
    assert snapshot.latest_snapshot_id(paths) == "GS-000001"


def test_mutation_invalidates_snapshot_then_new_snapshot_current(initialized):
    paths = initialized
    # append a row to a graph file -> GS-000001 no longer current
    jsonl.append(paths.resolve("graph/logic_nodes.jsonl"), {"node_id": "NODE-001"})
    assert not snapshot.is_current(paths, "GS-000001")

    snap = snapshot.take_snapshot(paths)
    assert snap.snapshot_id == "GS-000002"
    assert snapshot.is_current(paths, "GS-000002")
    assert not snapshot.is_current(paths, "GS-000001")
    assert snap.files["graph/logic_nodes.jsonl"].rows == 1


def test_verify_unknown_snapshot_is_false(initialized):
    assert not snapshot.is_current(initialized, "GS-999999")
