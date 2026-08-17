"""Append-only JSONL store with fcntl locking and path safety (docs/07, docs/08).

JSONL is canonical and append-only: a state change appends a complete new record
for that id; "latest state" = last record per id. History is never rewritten.
Appends take an fcntl lock on the target file. v1 is POSIX-only.
"""

from __future__ import annotations

import fcntl
import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from ..errors import CorruptStateError, UsageError
from ..serialize import canonical_bytes


class PathSafetyError(UsageError):
    """Requested path escapes the project directory (V-PATH-02)."""

    exit_code = 2


def safe_resolve(project_dir: str | Path, relpath: str | Path) -> Path:
    """Resolve ``relpath`` under ``project_dir``, rejecting escape (V-PATH-02).

    Project-relative only: no absolute paths, no upward traversal, no symlink
    escape. Returns the resolved absolute path.
    """
    project_dir = Path(project_dir)
    rel = Path(relpath)
    if rel.is_absolute():
        raise PathSafetyError([f"V-PATH-02: absolute path rejected: {relpath}"])
    # Reject any upward traversal component up front.
    if ".." in rel.parts:
        raise PathSafetyError([f"V-PATH-02: upward traversal rejected: {relpath}"])
    base = project_dir.resolve()
    candidate = (base / rel).resolve()  # follows symlinks -> catches symlink escape
    if candidate != base and base not in candidate.parents:
        raise PathSafetyError([f"V-PATH-02: path escapes project dir: {relpath}"])
    return candidate


@contextmanager
def file_lock(path: str | Path, mode: str = "a") -> Iterator[Any]:
    """Open ``path`` with an exclusive fcntl advisory lock held for the block."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if "b" in mode:
        fh = open(path, mode)
    else:
        fh = open(path, mode, encoding="utf-8")
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        yield fh
    finally:
        try:
            fh.flush()
            os.fsync(fh.fileno())
        except (OSError, ValueError):
            pass
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        fh.close()


def append(path: str | Path, record: Any) -> None:
    """Append one canonical record (pydantic model or dict) to a JSONL file."""
    data = canonical_bytes(record)
    with file_lock(path, "ab") as fh:  # binary append under lock
        fh.write(data)


def read_all(path: str | Path) -> list[dict[str, Any]]:
    """Read every record in append order. Raises CorruptStateError (exit 3) on a
    malformed line, naming file + line (docs/09 §3, S8)."""
    path = Path(path)
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise CorruptStateError(
                    [f"V-STORE: corrupt JSONL at {path}:{lineno}: {exc.msg}"]
                ) from exc
    return records


def latest_by_id(path: str | Path, id_field: str) -> dict[str, dict[str, Any]]:
    """Map id -> the last (newest) record for that id, in append order."""
    latest: dict[str, dict[str, Any]] = {}
    for record in read_all(path):
        key = record.get(id_field)
        if key is not None:
            latest[key] = record
    return latest


def latest_records(path: str | Path, id_field: str) -> list[dict[str, Any]]:
    """Latest record per id, ordered by first appearance of each id."""
    order: list[str] = []
    latest: dict[str, dict[str, Any]] = {}
    for record in read_all(path):
        key = record.get(id_field)
        if key is None:
            continue
        if key not in latest:
            order.append(key)
        latest[key] = record
    return [latest[k] for k in order]


def write_json(path: str | Path, record: Any) -> None:
    """Overwrite a single-object JSON file with one canonical line."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical_bytes(record)
    with file_lock(path, "wb") as fh:
        fh.write(data)


def read_json(path: str | Path) -> dict[str, Any]:
    """Read a single-object canonical JSON file."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise CorruptStateError([f"V-STORE: corrupt JSON at {path}: {exc.msg}"]) from exc
