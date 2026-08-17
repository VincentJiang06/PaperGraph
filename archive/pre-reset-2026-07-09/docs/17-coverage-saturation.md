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
  "mandatory_angles": ["official_stats", "academic", "counter", "industry"],
  "triangulated": true,
  "rounds": 2,
  "new_docs_last_round": 0,
  "saturated": true,
  "floor": {"required": "spine_fact", "met": true}
}
```

```text
angles[a]   := productive | tried_empty | tried_blocked | no_attempt.
Angle folding (v2.1 D6 — fixes the reactive-saturation livelock + the counter
over-report). angles[a] folds ONLY from:
  (i)   TERMINAL wave members (a member still running does not count — otherwise
        saturation could latch on an in-flight round): a terminal member marks
        its angle only ATTEMPTED (tried_empty); `productive`/`yes` for a waved
        node comes from the critic verdict (iv), not from (i) alone;
  (ii)  single-request docs_result.v2 query_logs;
  (iii) archived documents REQUESTED-for-this-target, mapped to an angle by the
        producing document's tier:
             T1_official      -> official_stats
             T2_peer_reviewed -> academic
             T3_working_paper -> academic
             T4_industry_data -> industry
        (so `academic` becomes attemptable on the single-request path — the old
        fold left it unreachable and saturation could never be met, livelocking
        the loop);
  (iv)  the wave's CoverageCritic report (coverage_report.v1) — the AUTHORITATIVE
        per-angle verdict: form.angle_covered maps yes->productive,
        tried_empty->tried_empty, tried_blocked->tried_blocked,
        no_attempt->no_attempt, and may RAISE an angle above what (i) shows. For
        a waved node this is the only path to `productive`.
`counter` is special: it folds from (a) an executed-or-blocked counter-kind qid
  in a docs_result.v2 query_log (the single-request path), (b) a TERMINAL
  counter-angle wave member (fold source i), or (c) the CoverageCritic's
  authoritative per-angle verdict (fold source iv) — NEVER from mere request
  completion, cache fulfillments, or v1 results. This keeps the counter angle
  honest (the run over-reported it as covered just because a request completed).
  (A literal "ONLY a v2 query_log" reading would livelock waved nodes — the
  bug S4 exists to prevent — so counter honours the wave/critic fold too.)
rounds      := completed search rounds for this node (terminal waves + completed
               single requests), with the V-COV-05 narrow-reset applied by the
               fold itself (D13).
mandatory_angles := official_stats, academic, counter; industry is added for an
               empirical claim whose scope names market/firm actors (the
               industry-mandatory heuristic — the operationalization of "an
               empirical claim about the labour market must consult industry
               data"). Recorded on the ledger line.
triangulated := whether the node's bindings satisfy S3 V-SRC-04 (docs/16) — part
               of the ledger line, consumed by the spine floor.
saturated   := rounds ≥ 2
               AND every angle in mandatory_angles ∉ {no_attempt}
               AND new_docs_last_round = 0.
```

Everything above is a fold over existing canonical records (requests, waves,
query_logs, EUs, bindings, the source registry) — deterministic, rebuildable, no
new writer. `triangulated` and `mandatory_angles` are fields of the ledger line.

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
  if saturated(T):       no new search. Two sub-cases (v2.1 D1):
    floor UNMET  the re-proof item is born dead ((created)->dead, op=dead_letter)
                 with detail {reason:"saturated", floor_met:false}. This is the
                 ONLY born-dead reason on the docs path.
    floor MET    the worker's insufficient answer CONFLICTS with a met floor
                 (floors are necessary, not sufficient). The Committer records a
                 CommitDecision `human_review` action (this action JOINS the
                 closed CommitAction enum, docs/08) AND still enqueues the
                 re-proof item born dead with detail {reason:"saturated",
                 floor_met:true} — so humans get a queue trace and `queue requeue`
                 resumes the item after review.
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
