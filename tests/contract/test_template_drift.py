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


def test_docs_worker_enumerates_the_exact_docs_result_v2_contract():
    """Root guard (live-run ai-jobs-2 WV-001): five DocsWorkers wrote schema-INVALID
    results — they echoed dispatch metadata (plan_id/angle/work_item_id) and invented
    ids (eu_id, doc_index) — because the template never enumerated the exact output
    keys. This pins the docs_worker template TO the schema: every key the worker must
    emit at each level is named, and the envelope-echo + id-forgery keys are named as
    forbidden. If the docs_result.v2 schema gains/loses a field, this test fails until
    the template is re-synced (docs/03 / docs/08 boundary contract)."""
    from paperproof.schemas.docs import (
        DocsResultV2, DocsResultDocument, QueryLogEntry,
    )

    text = prompts.load("docs_worker")
    for field in DocsResultV2.model_fields:            # 7 top-level keys
        assert field in text, f"docs_worker omits top-level key {field!r}"
    for field in DocsResultDocument.model_fields:      # documents[] keys
        assert field in text, f"docs_worker omits document key {field!r}"
    for field in QueryLogEntry.model_fields:           # query_log[] keys
        assert field in text, f"docs_worker omits query_log key {field!r}"
    # evidence_unit keys the worker authors (doc_ref/doc_id are the XOR reference).
    for field in ("doc_ref", "doc_id", "location", "kind", "quote_or_paraphrase",
                  "summary", "support_direction", "can_cite_for", "cannot_cite_for",
                  "scope"):
        assert field in text, f"docs_worker omits evidence_unit key {field!r}"
    # the exact fields the live-run workers wrongly emitted must be named+forbidden.
    for forbidden in ("plan_id", "angle", "work_item_id", "eu_id", "doc_index"):
        assert forbidden in text, f"docs_worker must name+forbid {forbidden!r}"


def test_critic_worker_template_pinned(project=None):
    """F3 (docs/10 §5, docs/15): the coverage-critic template ships and is the
    5th registered template, carrying its READ-ONLY + closed-form contract and a
    SELF-CHECK block; its {output_file}/{inputs} placeholders are present."""
    assert "critic_worker" in prompts.TEMPLATES
    text = prompts.load("critic_worker")
    assert text.startswith("You are a PaperGraph CoverageCritic.")
    assert "coverage_report.v1 JSON file to {output_file}" in text
    assert "{inputs}" in text
    assert "READ-ONLY" in text
    assert "NO\ndocuments and NO evidence_units keys" in text
    assert "SELF-CHECK before writing" in text
    assert "you never state a verdict" in text
