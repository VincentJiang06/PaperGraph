# 17 S4 — Coverage Ledger & Saturation (when search is DONE)

**Status: ADOPTED / BINDING (Stage B, v1.2) — docs/00 "Search Program Adoption — S4 Coverage & Saturation + S3 Triangulation" (2026-07-08); worklist docs/11 §12b. SUPERSEDES the r3/m5 flat floor + docs cap.**

The run had two opposite stopping failures: the docs cap dead-lettered a
target that fresh evidence was about to satisfy, while single-source spine
claims sailed toward freeze. "Enough" was a count; it must be a **profile**,
and "stop" must be **saturation** — the loop-until-dry criterion: you stop
searching when searching stops producing, not when a counter hits N.

## The coverage ledger (DERIVED — computed, never stored canonically)

`paperproof docs coverage [--node <id>]` and `/api/coverage` compute, per
non-rejected fact/mechanism node (and per bridge):

```json
{
  "node_id": "NODE-006",
  "eu_counts": {"supports": 4, "refutes": 2, "context": 1},
  "distinct_docs": 5,
  "distinct_publishers": 4,
  "tiers_present": ["T1_official", "T3_working_paper", "T4_industry_data"],
  "angles": {"official_stats": "productive", "academic": "productive",
             "industry": "productive", "counter": "productive"},
  "rounds": 2,
  "new_docs_last_round": 0,
  "saturated": true,
  "floor": {"required": "spine_fact", "met": true}
}
```

```text
angles[a]   := productive | tried_empty | tried_blocked | no_attempt —
               folded from every wave/query_log that targeted this node (S1/S2).
rounds      := completed search rounds for this node (waves + single requests).
saturated   := rounds ≥ 2
               AND every MANDATORY angle ∉ {no_attempt}   (official_stats,
                   academic, counter; industry mandatory for empirical claims
                   whose scope names market/firm actors)
               AND new_docs_last_round = 0.
```

Everything above is a fold over existing canonical records (requests, waves,
query_logs, EUs, bindings) — deterministic, rebuildable, no new writer.

## Floors (replace flat "≥2 EUs/2 docs" with role profiles)

```text
spine_fact / spine_mechanism   ≥2 EUs, ≥2 distinct docs, triangulated (S3),
                               counter angle ∉ {no_attempt}
bridge (repairs a spine edge)  as spine_fact PLUS ≥3 distinct docs — bridges
                               are the argument's most contested premises;
                               the run's bridges are exactly where thin
                               evidence produced churn
non-spine fact/mechanism       ≥1 EU (unchanged)
definition/question/thesis     no floor (evidence not_required path)
```

MSA-4 and V-FRZ-02 delegate to these floors at adoption (superseding the r3
flat rule). `msa-check` prints the per-node ledger line for every miss.

## Saturation replaces the docs cap

```text
needs_docs verdict on target T:
  if NOT saturated(T):   append requests / open the next wave round — ALWAYS.
                         No count-based refusal exists anymore.
  if saturated(T):       no new search. The re-proof item is born dead with
                         reason="saturated" ONLY IF the floor is also unmet;
                         if the floor IS met, the worker's insufficient answer
                         conflicts with a met floor — route to human review
                         with both facts (the form may be right: floors are
                         necessary, not sufficient).
ContextPack gains a per-target "coverage" block (the ledger line) so the
worker KNOWS search is exhausted and answers the honest endgame instead:
narrow the claim to what the evidence carries, or pass conditionally with
tight language_limits. Saturation converts "keep looking" into "this is what
the world's literature says — now write the claim that survives it."
```

## Rules (V-COV)

```text
V-COV-01  ledger determinism: same canonical state ⇒ identical ledger (golden)
V-COV-02  every ContextPack for a fact/mechanism/bridge target embeds the
          target's current ledger line
V-COV-03  the committer consults saturation, never a request count; born-dead
          reason ∈ {saturated} only, and only with the floor unmet
V-COV-04  freeze floors per the role profile table; msa-check reports per-node
V-COV-05  a saturated node whose floor is unmet cannot be narrowed into a
          claim that then freezes with ZERO search history — narrows inherit
          the parent claim's ledger (rounds reset to 0 only if the narrowed
          claim's core_terms change by more than half)
```

## Deltas at adoption

```text
CLI      docs coverage [--node]; /api/coverage; msa-check output extended
Schemas  none canonical (ledger is derived); context_pack.v1 + coverage block
Supersedes  the r3 flat docs cap and the r3 flat ≥2 floor (00 changelog entry
            must say so explicitly)
Tests    T-S4-1 ledger fold goldens incl. angle folding from query_logs
         T-S4-2 saturation truth table (rounds/angles/new_docs combinations)
         T-S4-3 the two run regressions as fixtures: (a) fresh-evidence target
                is NOT dead-lettered pre-saturation; (b) saturated+floor-unmet
                target IS, with reason=saturated
         T-S4-4 V-COV-05 narrow-inheritance
```
