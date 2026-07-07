# 15 S2 — Search Orchestra (waves, merger, coverage critic)

**Status: design-frozen (Stage A). Binding only after a docs/00 adoption entry.**

One worker per request serializes angles and lets whatever that worker didn't
think of stay unsearched forever. S2 turns a request into a **wave**: parallel
angle-workers (each executing its S1 plan), a deterministic merger, and a
*fresh* coverage critic whose closed form routes bounded follow-ups. This is
the multi-modal sweep + completeness critic pattern applied to evidence.

## Wave expansion

A DocsRequest carries `fan` (r3 sweep requests default `fan=true`; reactive
needs_docs requests default single unless the Orchestrator sets it):

```text
wave(DR-x) := one sub-search per angle in {official_stats, academic, industry,
              counter} (news joins only when the claim's period touches the
              last 18 months). Each member gets:
  work item     WI (docs_queue), target_type="request"
  plan          SP-DR-x-<angle> (S1 compiler, angle-specific)
  output        agent_outputs/docs_results/DR-x.<angle>.docs_result.json
Distinct outputs ⇒ members run fully parallel (docs/05 rules).
```

## Wave record (`docs/waves.jsonl`, producer: docs engine)

```json
{
  "schema_version": "search_wave.v1",
  "wave_id": "WV-001",
  "request_id": "DR-006",
  "project_id": "ai-jobs",
  "round": 1,
  "members": [{"angle": "official_stats", "work_item_id": "WI-000016", "plan_id": "SP-DR-006-official_stats"}],
  "status": "open",
  "created_at": "…"
}
```

`status` enum: `open | merging | critic | followup | closed`. Updates append
full records (latest-per-id, as everywhere).

## Merger (code, deterministic — runs when every member is terminal)

```text
1. Concatenate members' documents; dedup by content_hash, then by canonical
   URL: lowercase scheme+host, strip default port, strip fragment, strip the
   frozen tracking-param list {utm_*, gclid, fbclid, ref}, collapse duplicate
   slashes, strip one trailing slash.
2. Concatenate EUs; re-point doc_refs to the deduped table; drop exact-dup EUs
   (same doc, same normalized quote); order docs by content_hash asc, EUs by
   (doc order, location, quote hash).
3. Emit ONE merged docs_result.v2 at docs/merged/DR-x.merged.json; only the
   MERGED result is ingested (single DRES; per-member results stay in
   agent_outputs as provenance).
Same member set ⇒ byte-identical merged file.
```

## Coverage critic (fresh context, adversarial, read-only)

The critic never searches and never adds evidence. It reads: the claim, the
plans, the merged result, the per-member query_logs — and fills a closed form:

```json
{
  "schema_version": "coverage_report.v1",
  "wave_id": "WV-001",
  "form": {
    "angle_covered": {"official_stats": "yes", "academic": "yes", "industry": "no_attempt", "counter": "tried_empty"},
    "primary_source_present": "no",
    "disconfirming_captured": "yes"
  },
  "expected_sources": [
    {"name": "BLS CPS annual averages", "why": "the claim is a US aggregate-employment statement; its primary series is unqueried", "suggested_query": "BLS CPS annual average unemployment 2024"}
  ],
  "notes": "≤100 words"
}
```

Closed enums: `angle_covered[*] ∈ {yes, tried_empty, tried_blocked, no_attempt}`;
`primary_source_present`, `disconfirming_captured` ∈ {yes, no, n/a}. **Code
computes the wave verdict** (the critic never does):

```text
sufficient   iff every mandatory angle ∈ {yes, tried_empty, tried_blocked}
             AND disconfirming_captured ∈ {yes, n/a}
             AND (primary_source_present = yes OR round = R_MAX)
followup     otherwise, while round < R_MAX (=2): the engine opens one
             follow-up member per no_attempt angle + one per expected_source
             (its suggested_query becomes a hint), round += 1.
closed       at R_MAX regardless — the ledger (S4) records what stayed uncovered;
             unbounded search is not a virtue, unmeasured search is the sin.
```

## Rules (V-WAVE)

```text
V-WAVE-01  member outputs are pairwise distinct declared paths
V-WAVE-02  merger determinism: same terminal member set ⇒ byte-identical
           merged result; every merged doc/EU traces to exactly one member
V-WAVE-03  critic form is closed-enum complete; expected_sources ≤3 per round;
           the critic's output contains no documents/evidence_units (read-only)
V-WAVE-04  rounds ≤ 2; every follow-up member cites its origin (angle gap or
           expected_source) in the wave record
V-WAVE-05  only the merged result is ingested; exactly one DRES per wave
```

## Deltas at adoption

```text
CLI      docs wave --request <DR-id> [--fan]; queue list shows wave grouping
Schemas  search_wave.v1, coverage_report.v1, docs_request.v1 + fan flag
Roles    the critic is a distinct bounded worker (fresh context, adversarial)
         — same maker/checker separation as everywhere else in the system
Storage  docs/waves.jsonl, docs/merged/
Tests    T-S2-1 merger goldens (dup content_hash, tracking params, dup EUs)
         T-S2-2 verdict computation table (every angle_covered combination)
         T-S2-3 hostile critic (smuggles evidence_units ⇒ V-WAVE-03)
         T-S2-4 R_MAX close with uncovered angle recorded, no infinite loop
```
