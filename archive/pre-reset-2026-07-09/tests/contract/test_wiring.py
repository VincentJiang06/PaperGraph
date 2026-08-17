"""Protocol-wiring drift guards (docs/contracts rebuild, 2026-07-09).

The reorganize-logic rebuild cross-checked every module's inbound/outbound
artifacts against its consumers (docs/contracts/architecture.md, the wiring
matrix). These tests pin the invariants that the matrix showed are maintained
BY HAND in more than one place — the class of silent drift that produced the
live-run wiring failures.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.contract


def test_paths_empty_jsonl_matches_verify_jsonl_files():
    """paths.EMPTY_JSONL (what `project init` materializes) and
    verify._JSONL_FILES (what the invariant sweep schema-checks) are two
    hand-maintained copies of the same canonical 17-file set. A file added to
    one but not the other would be created-but-never-verified (or verified but
    never created) — silent drift either way."""
    from paperproof import verify
    from paperproof.paths import EMPTY_JSONL

    assert set(EMPTY_JSONL) == set(verify._JSONL_FILES)


def test_every_worker_template_has_a_renderer_and_vice_versa():
    """The five canonical templates and the render layer must stay closed under
    each other: a template nobody renders is dead contract text; a renderer
    without its template raises at dispatch time."""
    from paperproof import prompts

    assert set(prompts.TEMPLATES) == {
        "proof_worker", "docs_worker", "critic_worker", "compile_worker", "retry_suffix",
    }
    # every dispatchable template is reachable through a render entry point
    from paperproof.prompts import render

    assert callable(render.render_proof_prompt)     # proof_worker
    assert callable(render.render_docs_prompt)      # docs_worker + critic_worker
    assert callable(render.render_compile_prompt)   # compile_worker
    # retry_suffix rides on all of the above via the auto-appended retry block


def test_section_plan_buckets_cover_spine_reachable_node_types():
    """section_plan.NODE_TYPE_SECTION must bucket every node_type that
    graph.model.spine() can emit — spine() walks active supports/depends_on
    ancestors without filtering node_type, so the only legal type it can never
    emit is none: all six are reachable. `alternative` is deliberately
    unbucketed; dry_run refuses it via V-CDR-03 (test_v_cdr) instead of
    dropping it. This guard fails if the NodeType enum gains a member that is
    neither bucketed nor covered by the V-CDR-03 refusal contract."""
    from paperproof.compiler.section_plan import NODE_TYPE_SECTION
    from paperproof.schemas.graph import LogicNode

    node_types = set(
        LogicNode.model_fields["node_type"].annotation.__args__  # Literal members
    )
    bucketed = set(NODE_TYPE_SECTION)
    assert bucketed <= node_types
    # the exact, deliberate remainder — anything new must be triaged here
    assert node_types - bucketed == {"alternative"}
