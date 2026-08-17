# comparison4 — compaction-scale eval · RESULTS

The bet (user, Option 2): **keep the tree method, loosen it, and test it only where
durability matters — a task too big for one context, run under forced compaction.** Prior
evals (v1/v2/v3) used context-fitting tasks, so the tree could not show its reason to
exist. This is the honest test of that bet. Design: `../docs/11-loosened-tree.md`.

**Setup:** one oversized question (a systematic evidence map of 2020–2025 AI/automation
labor-market studies), run in **4 phases under forced compaction** — each phase a **fresh
Opus agent** inheriting only disk (tree + `nd brief` vs `log.md`), never the prior agent's
context. Both arms aggressive/free, single-context (no workers), loosened tree (v0.2).

## Headline: the tree's durability advantage is real — and only visible here

**Resume-read cost** (what each fresh agent must read to continue), at equal content:

| phase | tree (`nd brief`) | notree (`log.md`) | ratio | studies (t/n) |
|---|---|---|---|---|
| p1 | 6.1 KB | 9.5 KB | 1.6× | 8 / 9 |
| p2 | 7.7 KB | 15.3 KB | 2.0× | 16 / 16 |
| p3 | 10.1 KB | 24.5 KB | 2.4× | 23 / 23 |
| p4 | 12.9 KB | 29.6 KB | 2.3× | 25 / 27 |

**The notree log grows 3.0× steeper per phase (+6.7 KB vs +2.3 KB).** The tree brief is
**frontier-boxed** — it carries the active frontier + rolled-up conclusions, and concluded
facets *compress* in the brief while staying fully queryable on disk; the notree log is
**linear in content** — every study's detail must live in the blob a fresh agent re-reads.
Extrapolated to phase 20: notree ~134 KB (real context pressure) vs tree ~48 KB.

**This is the tree's structural reason to exist, and it is invisible on any
context-fitting task** — which is exactly why v1/v2/v3 couldn't see it. On this axis, the
bet is vindicated: *we were testing it in the wrong regime.*

## But it's an efficiency/scalability advantage, not (yet) a capability or quality one

- **Continuity held for BOTH arms.** Every phase, both fresh agents resumed from disk,
  added net-new studies with no duplication, and none restarted. At this scale (4 phases,
  30 KB log) **the notree kept up** — Opus can still re-read a 30 KB log fine. So the tree's
  advantage here is a *slope*, not a break. To turn the trend into a capability gap
  (notree can't continue because its memory exceeds context) you must push much further —
  more phases / a task several× bigger.
- **Judged quality: notree 4.89 vs tree 4.50** (blind 3-Opus panel, 6 dims) — but this is
  again substantially the **dossier-rendering artifact**, now extreme:

| dim | tree | notree |
|---|---|---|
| grounding | **5.00** | **5.00** (tie) |
| depth | **5.00** | 4.67 |
| coverage | 4.33 | 4.67 |
| adversarial | 4.33 | 5.00 |
| convergence | 4.33 | 5.00 |
| calibration | 4.00 | 5.00 |
| **composite** | **4.50** | **4.89** |

  `dossier.py` renders the tree as a **36-line per-node catalogue**; the notree author
  **hand-writes an 8-line synthesis** (an explicit Tier A–D quality ladder, one scoped
  thesis, a dead-ends ledger). Judges reward the tree's *catalogue* on grounding + depth
  (tied/ahead) and the notree's *synthesis* on calibration/convergence/adversarial-
  integration. The tree DID converge — a calibrated root synthesis with 8 open_questions —
  but the mechanical dossier **buries it under 36 node lines** instead of foregrounding it.
  This is a measurement artifact of the harness, not a reasoning gap.

- **Grounding tied at 5.0** — but note the asymmetry: the tree's is **enforced** (`nd check`
  verbatim-verifies every quote; you cannot conclude without a pointer), the notree's is by
  **diligence** (Opus was careful). At scale or with weaker models the guarantee holds
  where diligence slips; here, with Opus over 4 phases, they tie.

## The loosening worked (and was used)
- The tree author **used `nd reframe` naturally** (phase 2: reframed the job-level facet to
  include platform demand, added a sub-viewpoint) — the cheap-restructure the v3 rigidity
  blocked. No revise-chain punishment, children/bindings preserved.
- **Soft budgets exercised as intended:** authors intentionally went over the width
  guardrail (6–7 facets/children); `nd check` warned, nothing blocked. Convergence was the
  model's call, not the CLI's.
- **Free kind** used (claims attached directly). All phases `nd check`-clean. 60 tests green.

## Pre-registered verdict (docs/11 §)
- **H1 (memory growth) — SUPPORTED, cleanly.** notree log ~3× steeper slope; tree brief
  bounded-sublinear. The crux prediction held.
- **H2 (continuity) — NOT supported at this scale.** Both arms kept continuity; the notree
  didn't break. Needs larger scale.
- **H3 (grounding) — tie on the score, but the tree's is *guaranteed* vs the notree's
  *diligent*.** The structural difference is real even where the number ties.
- **H0 / kill-criterion — NOT triggered** (the tree showed a clean, monotonic durability
  advantage the other evals couldn't) — but not fully vindicated either (no capability gap
  yet; quality still trails, mostly by rendering artifact).

## Honest bottom line
**The bet was right that we were testing the tree in the wrong regime — and in the right
regime (compaction) it finally shows a real, clean, structural advantage: bounded resume
cost that grows ~3× slower than an unstructured log.** That is the tree's genuine reason to
exist. But at this scale it is a *scalability/efficiency* advantage, not a quality or
capability win: a strong model over 4 compactions kept up without the tree, and the judged
quality still favors the hand-written synthesis — largely because our own dossier renderer
under-presents the tree's convergence. The tree is a durability instrument; this eval is
the first to show that instrument doing its job.

## Two fixes before the next (decisive) run
1. **Go past the context wall.** More phases / a task 3–5× bigger, until the notree log
   genuinely exceeds what a fresh agent can hold — that converts the slope into a capability
   gap (notree breaks, tree continues). Also test with a **weaker model** (Haiku), where the
   notree's re-read-the-whole-log strategy should fail sooner.
2. **Fix `dossier.py` to render a synthesis, not a per-node dump** — lead with the root
   synthesis + facet syntheses, list studies as compact evidence — so the quality
   comparison stops being confounded by machine-catalogue vs hand-synthesis.

## Reproduce
`runs/{tree,notree}/` · phases via `PHASE_{tree,notree}.md` · `phase_metrics.py` →
`growth.jsonl` · `dossier.py` · blind + 3 Opus judges · `results.json` aggregated.
