# 13 Search Program (S1–S5) — the thoroughness track

Five staged spec sets that upgrade evidence search from "a worker improvises a
few queries" (the ai-jobs live run: 24 EUs for a whole paper, one angle at a
time, no stop criterion) to **thoroughness by construction**. The organizing
principle: every "did we search enough?" question becomes a machine-checkable
predicate — a plan is *accounted for*, a wave is *merged and criticized*,
sources are *tiered*, coverage is *measured to saturation*, and recall is
*semantic, not string-lucky*.

**Normativity.** These documents are DESIGN-FROZEN, not yet binding. docs/10
remains the authority on what is implemented. A set becomes binding only via a
docs/00 changelog entry plus a docs/11 worklist (as r3 did). Until then,
implementers build against docs/00–12; these docs answer "what comes next."

## The five sets

| set | doc | one line | adoption |
| --- | --- | --- | --- |
| S1 Search Planning | docs/14 | a claim compiles into a deterministic query plan the worker must account for, query by query | Stage A (v1.1) |
| S2 Search Orchestra | docs/15 | one request fans into parallel angle-workers, a deterministic merger, and a fresh coverage critic | Stage A (v1.1) |
| S3 Source Registry | docs/16 | sources get tiers, fetch recipes (403/PDF workarounds), provenance, and a triangulation rule | Stage A-lite / B (v1.1–1.2) |
| S4 Coverage & Saturation | docs/17 | per-claim coverage ledger + a saturation stop criterion that replaces the crude docs cap | Stage B (v1.2) |
| S5 Semantic Retrieval | docs/18 | hybrid keyword+embedding matching, cross-lingual (CJK↔EN), near-dup clustering — recall stops depending on token luck | Stage C (v2) |

## Why five, and why these

The live run failed on search in five distinct ways, one per set:

```text
S1 ← queries were improvised; nobody could check what was NOT tried.
S2 ← one worker per request; angles serialized; nothing named what was missing.
S3 ← 403s silently cost whole angles; source quality was untyped; fetch
     knowledge evaporated after each worker died.
S4 ← "enough" was vibes; the docs cap dead-lettered a healthy target while
     genuinely thin claims froze with one source.
S5 ← the keyword matcher over-matched period tokens and would miss any
     paraphrase; the project topic was Chinese while the literature is English.
```

## Composition (how a request flows once all five land)

```text
DocsRequest (or sweep cell)
  → S1 compiles a SearchPlan per angle
  → S2 fans a wave: one worker per (angle) with its plan; workers execute
    query-by-query with per-query accounting (S1), using S3 fetch recipes and
    writing S3 provenance
  → merger (code) dedups by content_hash + canonical URL
  → coverage critic (fresh context) fills a closed gap form → code routes
    follow-ups (≤2 rounds)
  → ingest updates the S4 coverage ledger; saturation computed
  → S5 assembles packs by hybrid retrieval; REQUESTED evidence unconditional
  → proof resumes; needs_docs after saturation dead-letters as `saturated`
    (a fact about the world, not a search failure)
```

## Dependency + staging

```text
S2 requires S1 (waves execute plans).      S4 requires S1+S2 (rounds) and
S3 is independent (adopt lite early).       S3-tiers (floors).
S5 is independent of all (swap-in matcher; S4 consumes its scores if present).
Stage A = S1+S2+S3-lite: fixes VOLUME (the run's core failure).
Stage B = S4 (+S3 triangulation): fixes STOPPING (caps → saturation).
Stage C = S5: fixes RECALL (paraphrase + cross-lingual).
```

Every set ships: exact schemas (`*.v1`), closed enums, deterministic
algorithms, V-* rules, CLI/worker-prompt deltas, and test hooks (T-S*-ids) that
move into docs/11 §10-style worklists at adoption. The executing model never
has to invent a search policy — it executes an accounted plan and the code
decides whether the search was thorough.
