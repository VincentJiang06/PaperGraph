"""Template drift guard (docs/11 §10 T-r3-10).

The r3 prompt blocks already ship (landed in r3-core); this test pins them so they
cannot silently regress. The worker prompt templates are the ONLY dispatch prompts
(docs/10 §5), so their text is part of the reproducible contract.

Note on the dash: the SHIPPED docs_worker.txt writes the coverage ranges with a
HYPHEN-MINUS ("2-5", "4-10"), not an en-dash — so this guard asserts the exact
shipped bytes (the whole point of a drift test is to match the shipped file).
"""

from __future__ import annotations

import pytest

from paperproof import prompts

pytestmark = pytest.mark.contract


def test_proof_worker_carries_self_check_block():
    text = prompts.load("proof_worker")
    assert "SELF-CHECK" in text


def test_docs_worker_carries_coverage_and_disconfirming_duty():
    text = prompts.load("docs_worker")
    # coverage numbers (2-5 documents / 4-10 evidence units — shipped with hyphens).
    assert "target 2-5 documents and 4-10 evidence units" in text
    assert "2-5 documents" in text
    assert "4-10 evidence units" in text
    # the disconfirming duty (capturing evidence AGAINST the claim).
    assert "DISCONFIRMING" in text
