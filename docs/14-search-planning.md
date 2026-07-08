# 14 S1 — Search Planning & Query Compilation

**Status: ADOPTED / BINDING (Stage A, S1) — docs/00 "Search Program Adoption (2026-07-08, Stage A)"; worklist docs/11 §12.**

The live run's DocsRequests carried a free-text `need` and two hints; each
worker improvised queries and nobody could verify what was *not* tried. S1
makes search **accountable**: code compiles a deterministic SearchPlan from the
claim, the worker executes it query by query, and validation rejects a result
that leaves a plan line unaccounted. Thoroughness stops being the worker's
mood.

## SearchPlan (`docs/plans/SP-<request>.json`, producer: plan compiler, code)

```json
{
  "schema_version": "search_plan.v1",
  "plan_id": "SP-DR-006",
  "request_id": "DR-006",
  "project_id": "ai-jobs",
  "angle": "official_stats",
  "facets": {
    "core_terms": ["unemployment", "nonfarm", "employment", "levels"],
    "scope_terms": ["2021-2025", "united states"],
    "counter_terms": ["decline", "criticism", "contrary"]
  },
  "queries": [
    {"qid": "Q1", "kind": "core",     "text": "unemployment nonfarm employment levels 2021-2025 united states"},
    {"qid": "Q2", "kind": "angle",    "text": "unemployment 2021-2025 united states official statistics"},
    {"qid": "Q3", "kind": "narrow",   "text": "nonfarm employment record 2024 BLS"},
    {"qid": "Q4", "kind": "counter",  "text": "unemployment 2021-2025 united states decline criticism"}
  ],
  "stop": {"max_queries": 8, "min_docs": 2, "min_eus": 4}
}
```

## The plan compiler (deterministic; no LLM)

```text
facets.core_terms   := the ≤6 highest-frequency non-stopword tokens of the
                       request `need` (ties: first occurrence order), minus
                       scope tokens. tokens() per docs/09 §0 — CJK-aware.
facets.scope_terms  := period + casefolded region from the target's scope
                       (contract scope when the target has none).
facets.counter_terms:= the frozen list ["decline","criticism","contrary",
                       "evidence against","refute"] (angle=counter only uses
                       the first three that fit the query template).
queries             := fixed templates per angle, filled from facets, in fixed
                       order, deduplicated, capped at stop.max_queries:
  every angle:  Q1 core:   join(core_terms) + " " + join(scope_terms)
                Q2 angle:  Q1 + " " + ANGLE_SUFFIX[angle]
  hint queries: one per search_hint, verbatim (kind="hint")
  narrow:       core_terms[:3] + strongest hint token (kind="narrow")
  counter:      Q1 + " " + counter_terms[0..1] (kind="counter"; MANDATORY in
                every plan regardless of angle — the disconfirming duty is a
                planned query, not a hope)
ANGLE_SUFFIX := {official_stats:"official statistics", academic:"study
  peer-reviewed", industry:"industry report data", counter:"evidence against",
  news:"news report"}
```

Same request ⇒ byte-identical plan (golden-testable). Plans are bundle-grade
artifacts: immutable once written, embedded in the dispatch prompt.

## Worker accounting (extends docs_result → `docs_result.v2`)

`search_log` (free strings) is replaced by a structured `query_log`:

```json
"query_log": [
  {"qid": "Q1", "executed": true,  "outcome": "productive", "urls_seen": 9, "docs_taken": 2, "note": ""},
  {"qid": "Q4", "executed": true,  "outcome": "empty",      "urls_seen": 4, "docs_taken": 0, "note": ""},
  {"qid": "Q3", "executed": false, "outcome": "blocked",    "urls_seen": 0, "docs_taken": 0, "note": "bls.gov 403; archive fallback also blocked"}
]
```

`outcome` enum: `productive | empty | blocked | offtopic`. Extra worker-initiated
queries are allowed and logged with `qid: "X1"...` (kind extra) — the plan is a
floor, not a ceiling.

## Rules (V-SP)

```text
V-SP-01  every plan qid appears exactly once in query_log; executed=false only
         with outcome=blocked + non-empty note
V-SP-02  the plan's counter query was executed or blocked — never skipped
V-SP-03  docs_taken ≤ urls_seen per entry; Σdocs_taken ≥ |documents| is not
         required (dedup) but |documents| > 0 requires ≥1 productive entry
V-SP-04  not_found=true requires every entry executed|blocked and 0 productive
V-SP-05  the plan file referenced by the result exists and matches request_id
```

## Deltas at adoption

```text
CLI      docs plan --request <DR-id>   (emit/reprint the compiled plan)
Schemas  search_plan.v1; docs_result.v2 (query_log replaces search_log)
Prompts  docs_worker template: "execute every query in THE PLAN below; account
         for each qid; blocked needs a reason; extras welcome as X-ids"
Storage  docs/plans/ under the project; plan files immutable
Tests    T-S1-1 compiler goldens (fixed need ⇒ byte-exact plan, CJK case too)
         T-S1-2 V-SP fixtures (unaccounted qid / skipped counter / dishonest
         not_found each rejected)  T-S1-3 hostile: worker fabricates outcome
         counts (docs_taken > urls_seen) ⇒ V-SP-03
```
