"""Unit tests for the append-only JSONL store (docs/07, docs/08)."""

from __future__ import annotations

import os
import threading

import pytest

from paperproof.errors import CorruptStateError
from paperproof.store import jsonl
from paperproof.store.jsonl import PathSafetyError

pytestmark = pytest.mark.unit


def test_append_only_and_latest_by_id(tmp_path):
    path = tmp_path / "records.jsonl"
    jsonl.append(path, {"id": "A", "v": 1})
    jsonl.append(path, {"id": "B", "v": 1})
    jsonl.append(path, {"id": "A", "v": 2})  # new version of A appended, not rewritten

    all_records = jsonl.read_all(path)
    assert len(all_records) == 3  # history preserved

    latest = jsonl.latest_by_id(path, "id")
    assert latest["A"]["v"] == 2
    assert latest["B"]["v"] == 1

    ordered = jsonl.latest_records(path, "id")
    assert [r["id"] for r in ordered] == ["A", "B"]  # first-appearance order


def test_concurrent_appends_do_not_corrupt(tmp_path):
    path = tmp_path / "concurrent.jsonl"
    n = 40

    def worker(i: int) -> None:
        jsonl.append(path, {"id": f"WI-{i:03d}", "payload": "x" * 20})

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    records = jsonl.read_all(path)  # would raise if any line were corrupt
    assert len(records) == n
    assert {r["id"] for r in records} == {f"WI-{i:03d}" for i in range(n)}


def test_path_traversal_rejected(tmp_path):
    with pytest.raises(PathSafetyError):
        jsonl.safe_resolve(tmp_path, "../evil.json")
    with pytest.raises(PathSafetyError):
        jsonl.safe_resolve(tmp_path, "/etc/passwd")
    with pytest.raises(PathSafetyError):
        jsonl.safe_resolve(tmp_path, "graph/../../escape.json")
    # a normal project-relative path resolves fine
    resolved = jsonl.safe_resolve(tmp_path, "graph/logic_nodes.jsonl")
    assert str(resolved).startswith(str(tmp_path.resolve()))


def test_symlink_escape_rejected(tmp_path):
    outside = tmp_path.parent / "outside_target"
    outside.mkdir(exist_ok=True)
    (tmp_path / "link").symlink_to(outside, target_is_directory=True)
    with pytest.raises(PathSafetyError):
        jsonl.safe_resolve(tmp_path, "link/secret.json")


def test_corrupt_line_reports_file_and_line(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text('{"id": "A"}\nnot json here\n', encoding="utf-8")
    with pytest.raises(CorruptStateError) as exc:
        jsonl.read_all(path)
    message = "; ".join(exc.value.errors)
    assert "bad.jsonl:2" in message


def test_write_json_single_canonical_line(tmp_path):
    path = tmp_path / "obj.json"
    jsonl.write_json(path, {"b": 2, "a": 1})
    raw = path.read_bytes()
    assert raw.endswith(b"\n")
    assert raw.count(b"\n") == 1
    assert jsonl.read_json(path) == {"b": 2, "a": 1}
