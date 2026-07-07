"""Expander ingest package (docs/08 B3): validate an ExpansionProposal (V-EXP)
and hand it to the Committer, which assigns ids and appends the records. The
Expander never writes graph files.
"""

from __future__ import annotations

from . import ingest

__all__ = ["ingest"]
