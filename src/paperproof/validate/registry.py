"""V-* rule registry: rule_id -> descriptor (docs/09).

In M0 only the V-SPEC and V-PATH families are implemented. The registry lets the
rule-coverage meta-test (M1+) enumerate every rule id the system knows about, and
gives the CLI a stable place to describe failed rules.
"""

from __future__ import annotations

from dataclasses import dataclass

from .envelope import Failure, to_envelope
from .rules import v_commit, v_dr, v_exp, v_path, v_pr, v_q, v_sp, v_spec, v_sweep, v_task

__all__ = [
    "Failure", "to_envelope", "RULES", "rule_ids",
    "v_spec", "v_path", "v_pr", "v_dr", "v_exp", "v_task", "v_q", "v_commit", "v_sweep", "v_sp",
]


@dataclass(frozen=True)
class Rule:
    rule_id: str
    prefix: str
    description: str


def _rule(rule_id: str, description: str) -> Rule:
    return Rule(rule_id=rule_id, prefix=rule_id.rsplit("-", 1)[0], description=description)


# The rule families implemented in M0.
RULES: dict[str, Rule] = {
    r.rule_id: r
    for r in [
        _rule("V-SPEC-01", "all 9 topic sections present, unique, non-empty"),
        _rule("V-SPEC-02", "paper_type in enum; v1 requires single_event_mechanism"),
        _rule("V-SPEC-03", "bfs_plan is a DAG"),
        _rule("V-SPEC-04", "hard_exclusions and forbidden_claims non-empty"),
        _rule("V-SPEC-05", "3-10 seed claims; each <= 2 sentences"),
        _rule("V-SWEEP-01", "first expansion beyond layer 0 requires the sweep evidence floor"),
        _rule("V-PATH-01", "output path exactly matches declared output_files"),
        _rule("V-PATH-02", "project-relative, no traversal, no symlink escape"),
        _rule("V-PATH-03", "valid UTF-8 JSON (or .md), single document"),
        _rule("V-PATH-04", "no writes outside allowed paths (prefix rule)"),
        _rule("V-EDGE-02", "edge_claim not a verbatim restatement of an endpoint claim"),
        _rule("V-PR-01", "schema valid; enums valid; unknown fields rejected"),
        _rule("V-PR-02", "task_id + target match the claimed work item"),
        _rule("V-PR-03", "no verdict/numeric/invented-id fields (raw scan)"),
        _rule("V-PR-04", "inference_check present iff EDGE_CHECK"),
        _rule("V-PR-05", "fact/mechanism nodes may not answer evidence not_required"),
        _rule("V-PR-06", "evidence_used subset of DocsPack"),
        _rule("V-PR-07", "conditional attachments present exactly when required"),
        _rule("V-PR-08", "duplicate_of in ContextPack ids, != target"),
        _rule("V-PR-09", "repair proposal shapes (bridge/narrow)"),
        _rule("V-PR-10", "notes <=150 words; no stray evidence id tokens"),
        _rule("V-PR-11", "narrowed_claim passes V-NODE-02"),
        _rule("V-PR-12", "recorded verdict equals decision-table output"),
        _rule("V-PR-13", "pass => language_limits present; else null"),
        _rule("V-PR-14", "ladder shape: not_evaluated exactly where earlier stage stopped"),
        _rule("V-PR-15", "assumptions iff holds_only_with_assumptions (edge) / evidence gate (node)"),
        _rule("V-DR-01", "exactly one of doc_ref/doc_id and it resolves"),
        _rule("V-DR-02", "can_cite_for AND cannot_cite_for non-empty"),
        _rule("V-DR-03", "no verdict/strength/lifecycle/worker-authored id fields"),
        _rule("V-DR-04", "document source_type enum + origin; web has inline text"),
        _rule("V-DR-05", "kind=quote => quote_match against archived text"),
        _rule("V-DR-06", "not_found => empty lists + non-empty search_log (v1) / query_log (v2)"),
        _rule("V-SP-01", "every plan qid accounted once; executed=false only with blocked+note"),
        _rule("V-SP-02", "the plan's counter query was executed or blocked, never skipped"),
        _rule("V-SP-03", "docs_taken <= urls_seen; documents present => a productive entry"),
        _rule("V-SP-04", "not_found => every entry executed|blocked and none productive"),
        _rule("V-SP-05", "the referenced plan file exists and matches request_id"),
        _rule("V-EXP-01", "lane previous layer fully committed"),
        _rule("V-EXP-02", "based_on_snapshot current (whole graph)"),
        _rule("V-EXP-03", "<=12 nodes; layer = lane frontier + 1"),
        _rule("V-EXP-04", "edge refs resolve (existing id or #index)"),
        _rule("V-EXP-05", "proposed nodes pass V-NODE-02/03"),
        _rule("V-EXP-06", "layer-0 question/thesis rule; none elsewhere"),
        _rule("V-EXP-07", "first proposal requires depends_on lanes complete"),
        _rule("V-TASK-01", "claim refuses stale items until rebuilt"),
        _rule("V-TASK-02", "ContextPack = target + 1-hop + full claim_digest"),
        _rule("V-TASK-03", "DocsPack evidence ids resolve to archived Documents"),
        _rule("V-Q-01", "transitions only along the docs/05 table"),
        _rule("V-Q-02", "claim atomic: no two live leases"),
        _rule("V-Q-03", "every status change has exactly one QueueEvent"),
        _rule("V-Q-04", "blocked_by exist; claimable iff resolved + endpoints active"),
        _rule("V-Q-05", "expired lease => requeue attempt+1; >3 => dead"),
        _rule("V-COMMIT-01", "input-scoped currency"),
        _rule("V-COMMIT-02", "input artifact passed validation"),
        _rule("V-COMMIT-03", "no target frozen"),
        _rule("V-COMMIT-04", "CommitDecision lists every append; replay reproduces post"),
        _rule("V-COMMIT-05", "post-commit graph passes V-GRAPH-01..03"),
        _rule("V-COMMIT-06", "proof verdict commits only onto a provable target"),
    ]
}


def rule_ids() -> list[str]:
    return list(RULES.keys())
