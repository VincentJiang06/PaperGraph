"""Derived DuckDB index (docs/07 §Derived DB, docs/10 §4 db group).

The index is DERIVED from the canonical JSONL and fully rebuildable. `db rebuild`
drops and recreates one table per canonical JSONL file; `db check` reports whether
the manifest hashes still match the live sources (``stale_index``). Deleting
``db/`` and rebuilding from JSONL is a normal operation.
"""

from __future__ import annotations

from .indexer import IndexReader, TABLE_MAP, check, rebuild

__all__ = ["IndexReader", "TABLE_MAP", "check", "rebuild"]
