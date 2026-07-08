"""Worker prompt templates (docs/10 §5). Static assets shipped with the package.

The five templates are the ONLY prompts used to dispatch workers, so behavior is
reproducible (S2 adds the coverage critic — docs/15). In M0 they are shipped, not
executed.
"""

from __future__ import annotations

from importlib import resources

TEMPLATES = ("proof_worker", "docs_worker", "compile_worker", "retry_suffix", "critic_worker")


def load(name: str) -> str:
    """Return the verbatim text of a prompt template by name (no .txt suffix)."""
    if name not in TEMPLATES:
        raise KeyError(f"unknown prompt template: {name!r}")
    return resources.files(__package__).joinpath(f"{name}.txt").read_text(encoding="utf-8")
