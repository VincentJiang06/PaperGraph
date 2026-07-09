"""Append-only JSONL with latest-per-id semantics; canonical single-doc JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import DomainError


def dumps(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def append(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(dumps(record) + "\n")


def read_all(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    where = "/".join(path.parts[-2:])  # e.g. tree/nodes.jsonl
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as e:
                # a corrupt line must surface as a clean, located error, never a
                # raw crash (TC-E corruption-recovery UX)
                raise DomainError([f"{where}:{lineno}: corrupt JSONL line — {e.msg}"])
    return out


def latest_by_id(path: Path, id_key: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for rec in read_all(path):
        out[rec[id_key]] = rec
    return out


def write_json(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
