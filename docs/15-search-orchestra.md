# 15 S2 — Search Orchestra (waves, merger, coverage critic)

**Status: ADOPTED / BINDING (Stage A, S2) — docs/00 "Search Program Adoption —
S2 Search Orchestra (2026-07-08)"; worklist docs/11 §12 T-S2-1..4.**

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

A round>1 follow-up member (a reopened `no_attempt` angle or an
`expected_source`) is opened at the SAME angle as a round-1 member, so its
output path carries a round+origin discriminator and NEVER reuses — hence never
silently overwrites — the round-1 member's already-committed result:

```text
output (round>1)  agent_outputs/docs_results/DR-x.<angle>.r<round>.<origin-slug>.docs_result.json
```

`<origin-slug>` is the member's `origin` (`angle:<name>` / `expected_source:<name>`)
lowercased to `[a-z0-9-]`. Origins are pairwise-distinct within a round, so the
paths are too — every member across the whole wave lifecycle owns a distinct
output file [V-WAVE-01]. The merger reads each member's own committed file, so
round-1 and round-2 evidence both survive into the single ingested merged set.

## Wave record (`docs/waves.jsonl`, producer: docs engine)

```json
{
  "schema_version": "search_wave.v1",
  "wave_id": "WV-001",
  "request_id": "DR-006",
  "project_id": "ai-jobs",
  "round": 1,
  "members": [{"angle": "official_stats", "work_item_id": "WI-000016", "plan_id": "SP-DR-006-official_stats", "round": 1, "origin": null}],
  "status": "open",
  "created_at": "…"
}
```

`status` enum: `open | merging | critic | followup | closed`. Updates append
full records (latest-per-id, as everywhere).

Each member also carries `round` (the round it was opened in; the initial fan is
round 1) and `origin` — null for round-1 members, and for a follow-up member the
gap it repairs (`angle:<name>` or `expected_source:<name>`). Both operationalize
V-WAVE-04 (a follow-up member must cite its origin *in the wave record*, and a
follow-up is identifiable by round > 1).

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

The merged result is code-produced from already-validated members, so its ingest
runs V-DR (a corruption guard) but NOT V-SP: the query-plan accounting is a
per-member check (each member validated against its own SP-DR-x-<angle> plan at
`complete_member`). The merged query_log is the concatenation of the members'
query_logs, so a fully-empty (not_found) merge still carries a non-empty search
record for V-DR-06.

## Coverage critic (fresh context, adversarial, read-only)

The critic is a **distinct bounded worker** (fresh context, adversarial,
read-only): the same maker/checker separation as ProofWorker/DocsWorker. It
rides its own `critic_queue` (WorkItem target_type=`wave`), its output lands in
`agent_outputs/coverage_reports/`, and it is validated (V-WAVE-03) then
committed like any other worker output — no evidence is written.

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
Storage  docs/waves.jsonl, docs/merged/, agent_outputs/coverage_reports/;
         work_item.v1 queue_name gains `critic_queue`, target_type gains `wave`
Tests    T-S2-1 merger goldens (dup content_hash, tracking params, dup EUs)
         T-S2-2 verdict computation table (every angle_covered combination)
         T-S2-3 hostile critic (smuggles evidence_units ⇒ V-WAVE-03)
         T-S2-4 R_MAX close with uncovered angle recorded, no infinite loop
```

## Operationalization (S2 build — pinned here per CLAUDE.md doc-sync)

```text
* `docs wave --request <DR> [--fan]` STARTS the wave (members + wave record);
  the merge → critic → verdict rounds are driven by code (deterministic merger +
  verdict; the bounded critic is the only LLM). A wave supersedes any pending
  single docs item for the DR (cancelled) so the wave owns the search.
* WaveMember carries `round` + `origin` (see the wave record above). A round>1
  member's output path carries a `.r<round>.<origin-slug>` discriminator (see
  §Wave expansion) so a follow-up never overwrites a round-1 member's committed
  result; `paperproof verify` sweeps V-WAVE-01 (pairwise-distinct member output
  paths) + V-WAVE-02 (closed-wave merge determinism/traceability) at rest, so a
  path collision at rest is caught (exit 3), not merely test-only.
* The critic rides `critic_queue` (target_type=`wave`); its coverage_report.v1
  lands in agent_outputs/coverage_reports/ and is V-WAVE-03-validated.
* `fan=false` (reactive/`docs request`) runs as a single official_stats member —
  the pre-S2 single-search behaviour, unchanged.
```
