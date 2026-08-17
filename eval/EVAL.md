# EVAL — the independent, adversarial judge of a finished paper

version: 0.3.0 · updated on its OWN track, separately from the paper workflow (see Isolation Contract)

This is the **frozen harness**, the `prepare.py`/`val_bpb` of this project. The paper workflow
(`WORKFLOW.md`, `gates/`, `runs/`) is the thing being optimized — the `train.py`. This eval is
what it is optimized *toward but never against*. Its whole job is to be the ground truth the
author cannot quietly bend.

---

## Isolation Contract (read first — this is the point of the document)

1. **Two separate tracks, two separate changelogs, two version numbers.** The paper workflow
   evolves in `CHANGELOG.md`; this eval evolves in `eval/CHANGELOG.md`. A change to one does
   **not** accompany a change to the other. They are updated in different sittings, ideally by
   treating "improve the paper/workflow" and "improve the eval" as distinct tasks you do not mix.
2. **The optimizer never edits the eval to pass.** Papers are optimized against the in-loop
   `gates/` (the cheap floor), *not* against this eval. If a paper fails the eval, you fix the
   paper or the workflow — you do **not** soften the eval. The only permitted eval edit that
   coincides with a failing paper is fixing a **demonstrated bug in the eval itself**, and that
   edit must be logged in `eval/CHANGELOG.md` with the evidence. This is the "never weaken a
   test" rule, hardened.
3. **The eval is author-blind where independence is the point.** Its agents re-derive ground
   truth from the thesis alone; they do not read the paper's own `positions.md` or `claims.tsv`
   as authority. The author's scaffolding is the thing under audit, not the yardstick.
4. **The eval runs out-of-loop (held out).** It is not run on every paper revision. It is run at
   ship time, and on a cadence, as a verdict — like a benchmark, not a linter.
5. **No teaching-to-the-eval.** The workflow prompts must not encode this document's rubric as
   checkboxes to satisfy. If the workflow starts naming eval dimensions to game them, that is a
   contract violation to be reverted.

If you find yourself editing this file in the same breath as making a paper pass, stop — that is
the overfit failure this file exists to prevent.

---

## Why this exists (the overfit diagnosis)

Our two `gates/` are **structural and author-facing**: they check that the author tagged every
position, that a paragraph is long enough, that the author's chosen numbers reproduce. They are a
useful floor. But because the same actor writes the paper, the position map, and the ledger — and
knows the gate mechanics — a paper can pass them while being shallow, one-sided, or citing only
the safe claims. Passing the gates is necessary, not sufficient. The gates measure *form*; this
eval measures *whether the paper is actually good and honest*, and it does so with **independent,
adversarial, blind** procedures the author cannot pre-satisfy by construction.

## Karpathy mapping (what we are importing)

| autoresearch | here |
|---|---|
| `train.py` (edited) | the paper + `WORKFLOW.md` + `gates/` |
| `prepare.py` / `evaluate_bpb` (frozen, read-only) | **this eval (`eval/`)** |
| `val_bpb` (objective metric) | the eval scorecard (below) |
| `results.tsv` (keep/discard ledger) | `eval/scoreboard.tsv` (per paper × eval-version) |
| baseline-first, keep-if-better-else-revert | the loop in "How to use it" below |

## Ground truth comes from REAL papers, not from us

The eval's yardstick is not our opinion and not our own `positions.md` — it is the **actual
published literature**. Per topic, an agent fetches real reviews + the camp-representative papers
and distils them into an **answer key** (`eval/corpus/<topic>/answer_key.json`): the field's real
positions (each tied to a fetched URL) and the benchmark empirical claims the literature actually
makes. The paper is then scored *against that external key*. Because the key is derived blind to
our paper and anchored to real sources, a self-serving position map that quietly drops an awkward
camp is caught — the missed position is in the literature but absent from the paper. The eval is
also **calibrated on real papers**: fetch a real published review on the topic and confirm it
covers the key near-completely; if our paper covers less, that gap is real, not a matter of taste.

## How to run (turnkey)
```
# 0. (once per topic) derive the answer key from real papers — eval/protocol.md step 0
#    -> eval/corpus/<topic>/answer_key.json   (dir name = run name)
# 1. mechanical dimensions (D1 screen + D4 reproduce):
python3 eval/harness.py score runs/<slug> --key eval/corpus/<slug>/answer_key.json --arm gated
# 2. judgment panel (D2/D3/D5 + claim audit) — dispatch eval/protocol.md agents into
#    eval/verdicts/<slug>.json, then re-run step 1 (it folds them in + reconciles D1/D2).
# 3. self-test the harness itself:
python3 eval/selftest.py
```
Every run appends a row to `eval/scoreboard.tsv` and writes `eval/reports/<slug>.md`.

## Runnable pieces
- `eval/harness.py` — the executable core: D1 independent-coverage (paper vs the literature key)
  and D4 reproduce-rate (objective). Writes `eval/reports/<slug>.md` + a `scoreboard.tsv` row.
- `eval/protocol.md` — how to derive the answer key from real papers and how to run the judgment
  agents (D2/D3/D5) into `eval/verdicts/<slug>.json`, with strict JSON schemas.
- `eval/corpus/<topic>/answer_key.json` — the external ground truth, from real fetched literature.

## Two tiers (do not conflate them)

- **`gates/` — the in-loop floor.** Fast, deterministic, structural, run every revision by the
  author. Cheap and gameable, but they stop obvious failure. Keep them.
- **`eval/` — the out-of-loop judge.** Slow, adversarial, independent, blind, run at ship/on
  cadence. This is the real quality signal and the anti-overfit ground truth.

---

## The scorecard — five dimensions, each independent and adversarial

Each dimension re-derives its own ground truth or attacks the paper; none trusts the author's
scaffolding. Each yields a number and a kill-criterion (an automatic fail regardless of the rest).

### D1 — Independent coverage (vs the literature)
- **Procedure:** the field's positions come from the **answer key derived from real fetched
  papers** (never the paper's own `positions.md`). `harness.py` (the SCREEN) marks each position
  engaged iff one of its distinctive `key_terms` appears in a real paragraph (≥200 chars). This is
  fast and reproducible but has **false negatives from vocabulary mismatch** (e.g. a paper that
  writes "routine-biased technical change" misses a key that says "…technological change").
- **D1 is a screen; D2 is authoritative.** When the D2 panel has run, a screen-missed position is
  **rescued** if D2 judged it actually engaged (steelman ≥ 1); the coverage kill-criterion fires
  only on positions that are screen-missed **and** unrescued (D2-confirmed absent, or D2 not yet
  run → provisional). So the mechanical screen never fails a paper D2 would clear.
- **Metric:** `independent-coverage = engaged / independent-positions`.
- **Catches:** a cozy, self-authored position map that omits the positions most awkward for the
  thesis. (The in-loop gate cannot catch this — it trusts the author's map.)
- **Kill-criterion:** any independently-derived position left unengaged **and** unaddressed.

### D2 — Steelman fidelity (adversarial advocate)
- **Procedure:** for each independent position, an advocate *for that position* reads the paper's
  treatment and scores it 0/1/2 = strawman / adequate / genuine-steelman-fairly-answered.
- **Metric:** mean steelman-fidelity (0–2); report each position's score.
- **Catches:** the long-but-empty paragraph that clears the gate's char threshold without
  actually representing the opponent at their strongest.
- **Kill-criterion:** any engaged position scored 0 (strawman).

### D3 — Objection robustness (adversary escalation)
- **Procedure:** an adversary given the thesis + paper tries to construct an objection
  *materially stronger* than the one the paper answered. Independent judges rate whether the new
  objection is (a) stronger and (b) unaddressed by the paper.
- **Metric:** robust = no materially-stronger unaddressed objection found.
- **Catches:** answering a deliberately weak "strongest objection."
- **Kill-criterion:** a materially-stronger, unaddressed objection exists.

### D4 — Claim completeness & honesty (independent claim audit)
- **Procedure:** an auditor extracts EVERY empirical assertion in the paper *independently of*
  `claims.tsv`, then (a) matches them to ledger rows, (b) flags load-bearing assertions with no
  ledger row, (c) flags cherry-picking — a suspiciously chosen window, definition, denominator,
  or source — and (d) flags transforms whose cleaning choice materially moves the number.
- **Metric:** `claim-coverage = ledgered / total-empirical-assertions`; plus a list of honesty
  flags.
- **Catches:** ledgering only the safe numbers while the load-bearing claim goes uncited; a
  number that reproduces but is cherry-picked.
- **Kill-criterion:** a load-bearing empirical claim with no reproducible ledger row, or an
  unresolved cherry-picking flag on a load-bearing number.

### D5 — Referee panel (blind, N independent judges)
- **Procedure:** N (≥3) independent referee agents, blind to the gate results and to each other,
  score the paper on a fixed rubric — thesis clarity, evidence quality, engagement with
  counter-arguments, calibration/honesty about limits, prose — and return accept / major-revision
  / reject with reasons. Use the median.
- **Metric:** median rubric score (per axis + overall) and the modal verdict.
- **Catches:** everything the first four dimensions quantify but a human referee would still
  reject.
- **Kill-criterion:** modal verdict = reject.

## Verdict

- **SHIP** iff: no kill-criterion tripped, `independent-coverage = 1.0`, mean steelman-fidelity
  ≥ 1.5, objection robust, `claim-coverage = 1.0` with zero unresolved honesty flags, and referee
  modal verdict ∈ {accept, major-revision-with-score ≥ band}.
- Otherwise **REVISE**, with the specific dimension(s) that failed. Revision happens in the paper
  or the workflow — never in this file.

The bands (the ≥ thresholds) may be tuned **only** on this eval's own track, with a logged reason,
and only to make the eval *harder or more accurate* — never to admit a paper that was failing.

## How to use it (the keep-if-better loop we import from Karpathy)

1. **Baseline first.** Before crediting the workflow, write a *freehand* draft of the topic (one
   agent, no gates, no cartographer) and run this eval on it. Record the scorecard. This is `val`
   for "no workflow."
2. **Variant.** Produce the gated-loop draft. Run this eval on it too.
3. **Keep-if-better.** The workflow earns its place only if the gated draft beats the freehand one
   *on this independent eval* — not on the gates it was built to pass. If it doesn't, say so.
4. **Ledger it.** Append both to `eval/scoreboard.tsv` (paper, arm, eval-version, the five
   metrics, verdict). Never delete a row; a worse result is data.

## What this eval deliberately does NOT do

- It does not replace the `gates/` — the cheap floor still runs in-loop.
- It does not judge on taste alone — every dimension re-derives ground truth or attacks the paper,
  so its verdict is reproducible by re-running the procedure, not by trusting one opinion.
- It does not get softened to let a paper through. Ever.
