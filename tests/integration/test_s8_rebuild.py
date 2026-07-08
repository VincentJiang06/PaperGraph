"""S8 derived-index rebuild (docs/09 §3 S8, docs/11 §8).

  * delete db/ -> `db rebuild` -> the /api answers are identical to a first build
    (idempotent: two rebuilds ⇒ identical index_manifest source hashes AND
    identical table contents);
  * corrupt ONE line of a canonical JSONL (graph/logic_nodes.jsonl) -> EVERY CLI
    command that reads it exits 3 naming file+line (the loader refuses to silently
    skip); the corruption is caught by MORE THAN ONE command.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from paperproof.db import indexer
from paperproof.db.indexer import IndexReader
from paperproof.ui.app import create_app

from tests.fakes import scenario

pytestmark = pytest.mark.integration


def _all_table_contents(paths):
    """Every table's full history (id, seq, json) as a comparable structure."""
    reader = IndexReader(paths.resolve(indexer.DB_FILE))
    try:
        return {table: reader.history(table) for _rel, table, _idf in indexer.TABLE_MAP}
    finally:
        reader.close()


def _api_snapshot(pp, project_id):
    client = TestClient(create_app(pp.tmp_path, project_id))
    return {
        "graph": client.get("/api/graph").json(),
        "queue": client.get("/api/queue").json(),
        "record": client.get("/api/record/NODE-002").json(),
        "evidence": client.get("/api/evidence").json(),
        "compiler": client.get("/api/compiler").json(),
        "trace": client.get("/api/trace/NODE-002").json(),
    }


def test_s8_rebuild_idempotent_and_api_stable(project, pp):
    paths = scenario.paths_for_pp(pp)
    scenario.monitor_fixture(paths)

    # First build.
    m1 = indexer.rebuild(paths)
    api1 = _api_snapshot(pp, "p4-ldi")
    tables1 = _all_table_contents(paths)

    # Delete db/ entirely and rebuild from JSONL (a normal operation).
    for f in ("index.duckdb", "index.duckdb.wal", "index_manifest.json"):
        p = paths.resolve(f"db/{f}")
        if p.exists():
            p.unlink()
    m2 = indexer.rebuild(paths)
    api2 = _api_snapshot(pp, "p4-ldi")
    tables2 = _all_table_contents(paths)

    # Idempotent: identical manifest SOURCE hashes + identical table contents +
    # identical /api answers.
    assert m1["sources"] == m2["sources"]
    assert m1["tables"] == m2["tables"]
    assert tables1 == tables2
    assert api1 == api2

    # A second rebuild-in-place over unchanged sources is likewise idempotent.
    m3 = indexer.rebuild(paths)
    assert m3["sources"] == m1["sources"]
    assert _all_table_contents(paths) == tables1

    # A freshly-rebuilt index is not stale.
    assert indexer.check(paths)["stale_index"] is False

    # F15: the S1/S2 canonical files are INDEXED sources — sources/waves tables
    # exist (queryable) and their JSONL is manifest-tracked for staleness.
    assert {"sources", "waves"} <= set(m1["tables"])
    assert "docs/sources.jsonl" in m1["sources"]
    assert "docs/waves.jsonl" in m1["sources"]


def test_s8_wave_and_registry_records_are_indexed(project, pp):
    """F15: after a real wave lifecycle, `db rebuild` indexes docs/waves.jsonl and
    docs/sources.jsonl (one row per append), and a post-rebuild wave append flips
    `db check` to stale."""
    from paperproof.store import jsonl as _jsonl

    paths = scenario.paths_for_pp(pp)
    scenario.seed_docs_facts(paths, [scenario.FACT_CLAIM])
    pp("docs", "request", "--target", "NODE-003", "--need", "Evidence on LDI calls.", "--fan")
    reqs = _jsonl.latest_records(paths.resolve("docs/docs_requests.jsonl"), "request_id")
    pp("docs", "wave", "--request", reqs[-1]["request_id"])

    m = indexer.rebuild(paths)
    assert m["tables"]["waves"] >= 1
    reader = IndexReader(paths.resolve(indexer.DB_FILE))
    try:
        waves = reader.current("waves")
    finally:
        reader.close()
    assert waves and waves[0]["request_id"] == reqs[-1]["request_id"]
    assert indexer.check(paths)["stale_index"] is False
    # an append to a newly-tracked source is DRIFT until the next rebuild.
    _jsonl.append(paths.resolve("docs/waves.jsonl"), {**waves[0], "status": "merging"})
    chk = indexer.check(paths)
    assert chk["stale_index"] is True and "docs/waves.jsonl" in chk["changed_sources"]


def test_s8_corrupt_line_makes_every_reader_exit_3(project, pp):
    paths = scenario.paths_for_pp(pp)
    scenario.monitor_fixture(paths)
    indexer.rebuild(paths)  # a healthy index exists before corruption

    # Corrupt line 1 of a canonical JSONL (not the last line, so the reported
    # line number is meaningful).
    target = paths.resolve("graph/logic_nodes.jsonl")
    lines = target.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 2
    lines[0] = '{"node_id": "NODE-001", THIS IS NOT JSON'
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # EVERY CLI command that reads logic_nodes.jsonl must exit 3 naming file+line;
    # the loader refuses to silently skip. Assert MORE THAN ONE command catches it.
    readers = [
        ("graph", "list-nodes"),
        ("graph", "show", "NODE-001"),
        ("verify",),
        ("db", "rebuild"),
        ("trace", "--node", "NODE-002"),
        ("compiler", "dry-run"),
        ("freeze", "apply", "--target", "NODE-002", "--level", "local"),
    ]
    caught = 0
    for cmd in readers:
        env = pp(*cmd, expect=3)
        assert env["ok"] is False
        blob = " ".join(env["errors"])
        assert "logic_nodes.jsonl" in blob, (cmd, env["errors"])
        assert ":1:" in blob or blob.rstrip().endswith(":1") or ":1" in blob, (cmd, env["errors"])
        caught += 1
    assert caught > 1

    # `db check` only hashes bytes (it does not parse), so it does NOT exit 3 —
    # but it DOES report the index as stale, since the source changed.
    chk = pp("db", "check")
    assert chk["ok"] is True
    assert chk["data"]["stale_index"] is True
