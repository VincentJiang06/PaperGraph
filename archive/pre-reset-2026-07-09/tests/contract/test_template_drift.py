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


def test_proof_worker_enumerates_the_exact_proof_result_v1_contract():
    """Root guard (live-run class-fix): the ladder alone is not a contract — the
    template must pin the proof_result.v1 layout key-by-key (the 12 top-level
    keys, the 'form' wrapper, where ids come from) or workers guess the layout
    and V-PR-01/V-PR-03 reject them. Pins the template TO the schema."""
    from paperproof.schemas.proof import ProofResult

    text = prompts.load("proof_worker")
    for field in ProofResult.model_fields:             # all 12 top-level keys
        assert field in text, f"proof_worker omits top-level key {field!r}"
    # the form's inner keys and the duplicate_check shape.
    for field in ("scope_check", "duplicate_check", "wellformed_check",
                  "evidence_check", "inference_check", "duplicate_of"):
        assert field in text, f"proof_worker omits form key {field!r}"
    # layout + hard-rule language that each failed (or nearly failed) live.
    assert "top-level keys" in text                    # exhaustive enumeration
    assert 'INSIDE "form"' in text                     # wrapper vs siblings
    assert "no numeric JSON values" in text            # V-PR-03
    assert 'no "verdict" key' in text                  # V-PR-03
    assert "task_id/project_id/target_id" in text      # allowed id keys, no more


def test_critic_worker_enumerates_the_exact_coverage_report_v1_contract():
    """Root guard: V-WAVE-03 reads the report's 'form' WRAPPER and the schema
    requires wave_id — the template must name both (and render fills {wave_id})
    or the critic cannot produce a valid report even in principle."""
    from paperproof.schemas.search import CoverageReport, CoverageForm, ExpectedSource

    text = prompts.load("critic_worker")
    for field in CoverageReport.model_fields:          # 5 top-level keys
        assert field in text, f"critic_worker omits top-level key {field!r}"
    for field in CoverageForm.model_fields:            # form's inner keys
        assert field in text, f"critic_worker omits form key {field!r}"
    for field in ExpectedSource.model_fields:          # expected_sources entries
        assert field in text, f"critic_worker omits expected_source key {field!r}"
    assert "{wave_id}" in text                         # render-filled placeholder
    assert "top-level keys" in text                    # exhaustive enumeration


def test_docs10_section5_carries_the_template_files_verbatim():
    """docs/10 §5: 'The texts below are canonical — the template files carry
    them verbatim.' This guard makes that sentence mechanically true: each
    ```text block under a '### … (`<name>.txt`…' heading must equal the shipped
    template file byte-for-byte. Editing a template without re-syncing docs/10
    (or vice versa) fails here."""
    from pathlib import Path

    doc = (Path(__file__).resolve().parents[2] / "docs" / "10-v1-design.md").read_text(
        encoding="utf-8").split("\n")
    names = {"proof_worker", "docs_worker", "critic_worker", "compile_worker", "retry_suffix"}
    found: dict[str, str] = {}
    i = 0
    while i < len(doc):
        line = doc[i]
        name = next((n for n in names if line.startswith("### ") and f"`{n}.txt`" in line), None)
        if name is None:
            i += 1
            continue
        j = i + 1
        while not doc[j].startswith("```"):
            j += 1
        k = j + 1
        while doc[k] != "```":
            k += 1
        found[name] = "\n".join(doc[j + 1:k])
        i = k + 1
    assert set(found) == names, f"docs/10 §5 is missing template blocks: {names - set(found)}"
    for name, block in found.items():
        assert block == prompts.load(name).rstrip("\n"), (
            f"docs/10 §5 block for {name}.txt is out of sync with the template file")


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
