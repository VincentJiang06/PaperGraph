"""Committer package (docs/08 B6): the ONLY Logic Graph mutator.

The decision table is imported eagerly (it is a light, dependency-free pure
function shared with the Validator). ``apply`` and ``replay`` are heavier (they
pull the queue engine and graph model) and are imported as submodules on demand
to keep import order simple and cycle-free.
"""

from __future__ import annotations

from .decision_table import compute_verdict, ladder_check

__all__ = ["compute_verdict", "ladder_check"]
