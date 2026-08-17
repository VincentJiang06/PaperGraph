# Ablation v2 — Sonnet 5, five hard economic-analysis topics

A deliberately harder, fairer re-run of the three-mode ablation, built to test three
claims I had flagged as weak in the v1 run: *(1)* use a **weaker author model**
(Sonnet 5, not Opus), *(2)* use **five topics** and aggregate, not N=1, *(3)* use
**hard, contested economic-analysis questions** that need long-chain causal reasoning,
where the tree "should" help most. The hypothesis under test: **the logic tree helps
*more* with a weaker model on harder tasks.**

Same three conditions, isolated single-context runs, the only variable is the framework:
- **raw** — no method, no tools (but the deliverable spec still asks for a
  discussion section + calibration — see the confound note).
- **skills** — the methodology-only skill (diverge-not-decompose, mandatory adversarial
  line, verbatim quotes, distill-then-discard) — no tree, no CLI.
- **tree** — full nodify (`nd` CLI + skill).

15 Sonnet-5 author runs (5 topics × 3 modes). Evaluation: a **blind 3-judge Opus
panel** (mode hidden, citations format-normalized, Latin-square slot rotation),
uniform **mechanical metrics**, and **cold-resume probes** (T1 & T3 × 3 modes).

## The headline: the tree's judged-quality edge nearly vanished

| blind panel, mean of 3 judges × 5 topics | raw | skills | tree |
|---|---|---|---|
| structure / logic | 4.67 | 4.67 | 4.73 |
| evidence quality | 4.27 | **4.60** | 4.40 |
| adversarial rigor | 4.47 | 4.60 | **4.73** |
| calibration | 4.73 | 4.60 | **4.93** |
| **overall** | **4.53** | **4.60** | **4.73** |

**The overall spread is 0.20 points.** In the v1 Opus / single-easy-topic run it was
**2.0 points** (raw 3.0 → tree 5.0). On this harder, fairer test the three modes are
nearly tied, and all three are *good* (4.5–4.7).

Per-topic "overall" winner:

| | T1 AI-jobs | T2 inflation | T3 QE-inequality | T4 China-demog | T5 min-wage |
|---|---|---|---|---|---|
| raw | 5.00 | 4.33 | 5.00 | 4.00 | 4.33 |
| skills | 4.00 | 4.00 | 5.00 | **5.00** | **5.00** |
| tree | **5.00** | **4.67** | 5.00 | 4.33 | 4.67 |

- **tree ≥ raw on all 5 topics** (strictly greater on 3, tied on 2) — it never lost to
  the unstructured baseline.
- **tree vs skills is a wash** (tree wins T1/T2, skills wins T4/T5, tie T3).

## What this does and does not support

**NOT supported: "a weaker model needs the tree more."** The judged gap is *smaller*
here (0.20) than in the Opus run (2.0), not larger. Three reasons the gap compressed,
in order of how much I trust them:
1. **The discipline, not the machinery, is the lever — again, and more starkly.** The
   tree beats raw by only +0.20 and does **not** beat skills-only. A disciplined agent
   with no tooling matched the full framework on judged quality.
2. **Sonnet 5 is still a strong model.** "Weaker than Opus" ≠ weak. The floor the tree
   provides didn't bind because Sonnet rarely hit the floor. Genuinely testing the
   hypothesis needs a genuinely weak model (Haiku) — see Next.
3. **Confound (disclosed): my `raw` prompt was not zero-method.** It still asked for a
   counterpoints/discussion section and calibration. That scaffolds the low end and
   inflates raw (4.53 vs v1's 3.0). A cleaner test would strip those asks from raw.

**Supported: the tree's edge is in disciplined-reasoning dimensions, not evidence.**
The tree leads on **calibration (4.93, highest)** and **adversarial rigor (4.73)**, and
judges repeatedly praised the *enforced* adversarial line — e.g. on T1 the tree article
"deliberately imports disconfirming data (METR slower-but-believed-faster;
Revelio/Ramp heavy-adopters-hire-more)." It does **not** lead on **evidence quality**
(skills 4.60 > tree 4.40): DOC-bundling and one contested-source flag cost it there.

## Mechanical metrics — the v1 evidence-breadth edge did NOT replicate

| by-mode mean (5 topics) | raw | skills | tree |
|---|---|---|---|
| article length (中文字) | 1755 | 1820 | 1833 |
| distinct sources cited | 12.8 | 12.8 | 12.2 |
| citation traceability | 100% | 100% | 100% |

In v1 the tree had **2× the sources** (18 vs 8–9). Here the three are even. The Sonnet
raw/skills authors cited prolifically (raw averaged 31 inline cites), and tree
DOC-bundling *undercounts* (T5's tree folded ~6 studies into 4 "case-file" DOCs). So on
breadth, the framework did not help.

**Auditability is the one mechanical property that stays a tree win, structurally:** all
5 tree sessions are `nd check`-clean or near-clean with a **verbatim-verified** archive
(quotes checked against saved source text by the framework). raw/skills had good
provenance too here (Sonnet was diligent) — but *unenforced*: nothing verified it.

## Cold-resume (compaction immunity)

Each investigation was "interrupted"; a fresh Opus agent recovered the reasoning state
from disk-only artifacts (tree → `nd brief`; skills → `log.md`; raw → `sources/`), **not
allowed to read the finished article**. Recoverability (0–5), mean of T1 & T3:

| | raw | skills | tree |
|---|---|---|---|
| overall recoverability | **3.0** | **5.0** | **5.0** |
| what's lost | *leanings + next-action* (keeps sources, loses the thinking) | nothing | nothing |

Structured persistence (a disciplined log **or** the tree) fully preserves the
investigation; raw keeps the evidence but loses the reasoning. Tree = skills here
because Sonnet wrote good logs — **the tree's advantage over skills is enforcement, not
magnitude**: `nd brief` is guaranteed to work, whereas a skills log's quality is
author-dependent (it was an empty citation placeholder in the v1 run).

## The honest answer

On a **harder, fairer, five-topic test with a capable model, the logic tree is not a
meaningful article-quality lever over disciplined thinking.** The discipline is the
lever; the tree ≈ discipline on judged quality (+0.20 over raw, ±0 vs skills). Its
defensible, *structural* value is narrower than "better articles":

- **enforced auditability** — a verbatim-verified evidence archive, checked by code, not
  trusted to the author's diligence;
- **guaranteed recoverability** — `nd brief` reconstructs the reasoning state every time,
  not only when the agent happened to keep a good log;
- **a small, consistent calibration / adversarial edge** — the mandatory adversarial line
  and grounded synthesis show up as the panel's best-calibrated, most-disconfirming
  articles.

These compound where discipline-alone degrades: at scale, under real compaction, with
genuinely weak models, or when the output must be *audited* rather than just read. On a
clean single pass by a capable model, they are close to free-and-invisible — which is
exactly why the judged gap is 0.20, not 2.0. **The tree is a floor on rigor and a
guarantee of auditability/recoverability — not a quality multiplier for a good agent
having a good day.**

## Next (to actually test the hypothesis)
- **Haiku** authors, same harness — the only way to see if the floor binds for a truly
  weak model. Sonnet 5 was too strong.
- **Strip the raw prompt** to zero-method (no counterpoints/calibration asks) to
  un-confound the low end.
- Fix the mechanical **source-count** to count studies-per-DOC, not DOC entries, so the
  tree isn't undercounted by bundling.
- Minor `nd` finding surfaced by this run: re-`outline` leaves **orphan section records**
  (append-only; no section-delete) → 2 benign soft warnings on the one article I forced
  to re-outline. Candidate roadmap item: mark superseded sections instead of warning.

## Reproduce
`runs/T{1..5}/{raw,skills,tree}/` — articles + sources + (tree) the `nd` session.
`python3 aggregate.py .` mechanical · `python3 blind.py .` blind · `python3
judge_aggregate.py .` panel. `blinded/KEY.json` slot→mode (withheld from judges).
`results.json` — everything aggregated.
