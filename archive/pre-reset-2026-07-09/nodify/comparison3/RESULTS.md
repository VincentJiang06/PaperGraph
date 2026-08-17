# comparison3 — aggressive-research eval, 5 topics · RESULTS + comparison to v2

**The test:** does the logic tree let an aggressively-run strong model (Opus) investigate
*better* than the same aggressive method without a tree? Arms differ only in the tree
(aggression + model held constant). Judged artifact = the **investigation** (node/tree →
uniform dossier), not an article. 5 topics (the same questions as the v2 run), 2 arms,
Opus, budget `max_depth=3 max_children=6 max_open_claims=15`, **no blitz-search workers**
(both single-context, symmetric). Design: `../docs/10-aggressive-research.md`.

## Headline: at 5 topics, tree-governed aggression *loses* to ungoverned aggression

| blind panel, 3 Opus judges × 5 topics (15 scores/arm) | tree | notree | Δ |
|---|---|---|---|
| **grounding / auditability** | **4.40** | 4.27 | **+0.13** |
| coverage | 4.47 | 4.80 | −0.33 |
| depth | 4.60 | 4.80 | −0.20 |
| adversarial completeness | 4.60 | 5.00 | −0.40 |
| convergence | 4.47 | 5.00 | −0.53 |
| calibration | 4.00 | 5.00 | −1.00 |
| **composite** | **4.42** | **4.81** | **−0.39** |

**The tree is behind on 5 of 6 dimensions, ahead only on grounding.** This *flips* the
2-topic pilot (which was a tie with grounding +0.83) — the pilot's small N flattered the
tree. On the fuller 5-topic set, **ungoverned aggressive Opus is the better investigator.**

### Why — and how much is real vs a measurement artifact
Two forces, both disclosed:

1. **Substantive (the larger part): free-roaming aggression found sharper insight.**
   Judges named specific things the *notree* arm surfaced that the systematically-structured
   tree runs missed — on **AI-jobs**, *"the cleanest causal design (freelance quasi-experiment:
   exposed contracts −2%, earnings −5%),"* on **China**, *"the non-obvious reframe that Japan's
   'lost decades' were a workforce-denominator effect… that reframes the whole question."* The
   tree runs were *"systematic, comprehensive, granular"* but narrower and less serendipitous.
   The governor buys systematic coverage + grounding; it appears to **trade away some creative
   reframing.** Even excluding the two most rendering-sensitive dimensions (calibration,
   convergence), the tree is still behind **−0.20**, driven by coverage.

2. **Instrument artifact (the smaller part): asymmetric dossier rendering.** The *notree*
   author **hand-writes** its dossier (crafting calibration prose, framing, a tidy "dead ends"
   section); the *tree* dossier is **machine-generated** from lean/confidence tags + summaries
   (`dossier.py`). This favors notree on prose-sensitive dimensions — it explains most of the
   calibration gap (−1.00) and part of convergence (−0.53). Calibration alone accounts for
   ~0.12 of the 0.39 composite gap. **The tree's calibration lives in structured
   lean/confidence + open_questions, not prose — this rubric under-credits it.** A clean re-run
   needs *symmetric* rendering (both arms machine-rendered, or both hand-written).

### The tree's durable edges (rendering-robust, replicated)
- **grounding/auditability** — judged +0.13, and *mechanically enforced*: tree grounding_rate
  = 1.0 on 4/5 topics (China 0.8), every conclusion tied to a verbatim-verified archived doc.
  The notree arm left some quotes "search-surfaced" and orphaned sources.
- **compaction / recoverability** — cold-resume probes (all 10): **tree 5.0 vs notree 4.8**.
  Both recover well (Opus logs well), but the tree's is *guaranteed* (`nd brief`) and it
  persists the converged answer as a first-class record; the one notree miss (T2) was an
  unlogged final verdict.

### The tree is high-variance; the notree is stable
| per-topic composite | inflation | QE | AI-jobs | China | min-wage |
|---|---|---|---|---|---|
| tree | 4.78 | 4.67 | **3.95** | **4.00** | 4.72 |
| notree | 4.78 | 4.83 | 4.78 | 4.83 | 4.83 |

The notree arm is rock-steady (4.78–4.83); the tree swings 3.95–4.78. **Tree quality depends
heavily on how well the author built the tree** — the AI-jobs tree came out flat (2 viewpoints/
8 claims) and the China tree missed the killer reframe, and both scored ~4.0. The tree adds a
floor on *rigor* but not on *insight*, and a weak build shows.

## Comparison to before (same 5 questions)
The tree's *overall-quality* advantage has declined monotonically as each run got fairer,
harder, and more node-focused — leaving only grounding/auditability as durable:

| run | model | artifact | tree vs best non-tree arm (overall/composite) | tree's edge |
|---|---|---|---|---|
| **v1** | Opus | article, 1 easy topic | **+1.0** (tree 5.0 vs skills 4.0) — won | grounding (100% verbatim) + evidence depth |
| **v2** | Sonnet | article, 5 hard topics | **+0.13** (tree 4.73 vs skills 4.60) — ~tie | grounding/evidence + calibration |
| **v3** | Opus | *investigation*, 5 hard, aggressive | **−0.39** (tree 4.42 vs notree 4.81) — **lost** | grounding (+0.13, enforced 1.0) + recoverability |

**The through-line across all three runs: grounding/auditability is the tree's one durable,
replicated edge.** On overall quality it goes from ahead (careful, weak baseline) to behind
(aggressive, strong baseline). The tree is **not a quality lever** — and in the aggressive
regime built to be its best case, it is a modest quality *cost* for the auditability guarantee.

## The honest verdict on the strategic bet
"Unleash Opus to be aggressive + let the tree govern it" — the thesis of this whole
direction — **did not pay off on investigation quality.** Ungoverned aggressive Opus roams
more freely and finds sharper designs and reframes; the tree's structure grounds and
audits everything but constrains that reach. The tree's defensible value is now narrow and
consistent: **enforced grounding/auditability + guaranteed recoverability + forced persistence
of the converged answer** — structural guarantees for when output must be *trusted, audited, or
resumed*, not a way to make a strong model think better. That is a real product niche
(compliance, long-running/interruptible investigations, multi-agent handoff) — but it is not
"the tree makes the research better," even under aggression.

## Caveats (don't over-read)
- **N=5, 3 judges** — margins of ±0.1–0.4 are suggestive, not definitive; the coverage/insight
  losses (judges naming specific missing findings) are the most trustworthy signal.
- **Conservative config** — no blitz-search workers, small budget. *Fuller* wildness (parallel
  workers, bigger budget) is still untested and could change the picture.
- **Asymmetric dossier rendering** is a genuine confound inflating the calibration/convergence
  gaps — fix before trusting those dimensions (see Next).
- The **notree arm is a very strong baseline**: Opus + the full aggressive method + a
  disciplined log. This isolates the tree's *tooling* delta, the right question.

## Framework-debug payoff (this run's other job)
- Budget-key fix from the pilot **held** — all 4 new tree authors used
  `--budget max_depth/max_children/max_open_claims` cleanly, no budget friction.
- **New bug surfaced (2 independent probers):** `nd docs for-node <id>` returns empty even when
  bindings exist (provenance lives in synthesis `based_on.evidence` + `docs/index.jsonl`
  bindings). Logged in `FRICTION.md` (item 6).
- **`dossier.py` fixed:** evidence with `url:null` (pointing by doc_id) now resolves via the
  docs index (T2 tree had lost all 45 evidence URLs).

## Next
1. **Symmetric rendering** — machine-render *both* arms' dossiers from structured records (or
   have both hand-write), then re-judge, to remove the prose-rendering confound before trusting
   the composite.
2. **Fuller wildness** — blitz-search workers + bigger budget, to test whether real aggression
   (not just in-context) changes the coverage/insight gap.
3. **Decide the product thesis honestly:** across v1→v2→v3 the tree is an *auditability &
   recoverability* instrument, not a quality multiplier. Build for that, or find the regime
   (scale, weak models, compliance, interruption) where the structural guarantees dominate.

## Reproduce
`runs/T{1..5}/{tree,notree}/` · `dossier.py` · `tree_metrics.py` · `blind.py` → 3 Opus judges
→ `judge_aggregate.py` · probes via `PROBE_PROMPT.md` (`results_probes.json`) ·
`blinded/KEY.json` slot→arm (withheld) · `results.json` aggregated · topic map:
T1 inflation · T2 QE · T3 AI-jobs · T4 China · T5 min-wage.
