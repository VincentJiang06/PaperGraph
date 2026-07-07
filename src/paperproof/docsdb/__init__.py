"""Docs Database (docs/04): archive, evidence store, matcher, fingerprint cache,
DocsPack builder, and the docs ingestor.

The Docs ingestor / docs engine is the ONLY writer of docs/*.jsonl + docs/raw +
docs/text (docs/08 §3). It never sets proof verdicts and never touches the graph.
"""

from __future__ import annotations

from . import cache, commands, ingest, matcher, pack

__all__ = ["cache", "commands", "ingest", "matcher", "pack"]
