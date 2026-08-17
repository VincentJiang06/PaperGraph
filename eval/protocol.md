# EVAL protocol — how to run the eval (agent orchestration + schemas)

The mechanical dimensions (D1 coverage vs the literature key, D4 reproduce-rate) run in
`harness.py`. The judgment dimensions (answer-key derivation, D2/D3/D5) are run by dispatching
independent agents with the prompts below and saving their **strict JSON** to fixed paths, which
`harness.py` then folds into the scorecard. Every agent here is **blind to the paper's own
scaffolding** (its `positions.md`/`claims.tsv`) — that is the whole point.

## Step 0 — Answer key from REAL papers → `eval/corpus/<topic>/answer_key.json`
Dispatch an agent (web tools) with ONLY the thesis. It fetches real published reviews + the
camp-representative papers and returns the field's positions + benchmark claims, each tied to a
real fetched URL. Schema:
```json
{
  "topic": "<slug>", "thesis": "<verbatim>",
  "positions": [{"id":"K1","name":"...","gist":"one sentence",
                 "key_terms":["distinctive phrase","surname"],"source_url":"<real url>"}],
  "benchmark_claims": [{"claim":"...","value":"...","source_url":"<real url>"}],
  "sources_fetched": ["<url>"]
}
```
Rule: ≥6 positions incl. every serious objection; every `source_url` actually fetched; no
fabrication. This file is the external ground truth — it is derived once per topic and only
updated on the eval track (never edited to match a paper).

## Step 1 — Mechanical scoring (harness)
`python3 eval/harness.py score runs/<slug> --key eval/corpus/<topic>/answer_key.json --arm <arm>`
→ D1 independent-coverage (paper vs the literature's positions) + D4 reproduce-rate, a report in
`eval/reports/<slug>.md`, and a `scoreboard.tsv` row. Missed positions = coverage the author's
own map hid.

## Step 2 — Judgment panel → `eval/verdicts/<slug>.json`
Dispatch these independent agents (they read the paper + the answer key, NOT the paper's
positions.md). Collect into one JSON the harness reads:
```json
{ "steelman_min": 0|1|2, "steelman_by_pos": {"K1":2,"K2":1},
  "objection_robust": true|false, "stronger_objection": "<text or null>",
  "claim_coverage": 0.0-1.0, "honesty_flags": ["..."],
  "referee_verdict": "accept"|"major-revision"|"reject", "referee_scores": {"...":0-5} }
```

- **D2 steelman fidelity (one advocate per answer-key position).** Prompt: "You are the strongest
  proponent of <position K_i (gist)>. Read how this paper treats it. Score 0/1/2 = strawman /
  adequate / genuine-steelman-fairly-answered, and justify." `steelman_min` = the lowest score.
- **D3 objection robustness (adversary).** Prompt: "Given this thesis and paper, construct an
  objection materially STRONGER than the one the paper answered, using the real literature. Is it
  stronger AND unaddressed?" → `objection_robust=false` if such an objection is found.
- **D4 claim completeness & honesty (auditor).** Prompt: "Independently list EVERY empirical
  assertion in this paper. Match to `claims.tsv`. Flag load-bearing assertions with no
  reproducible row, and any cherry-picked window/definition/denominator/source." →
  `claim_coverage`, `honesty_flags`.
- **D5 referee panel (≥3 blind judges, median).** Prompt: "Referee this paper for a serious venue
  on thesis / evidence / counter-argument engagement / calibration / prose. Verdict accept /
  major-revision / reject with reasons. You do not know whether it passed any automated gate." →
  median `referee_verdict`.

## Step 3 — Re-score, verdict, ledger
Re-run `harness.py score …`; it now folds the verdicts and applies all kill-criteria (EVAL.md).
Append to `eval/scoreboard.tsv`. **Never** edit the answer key or thresholds to make a paper pass.

## Calibration (prove the standard is real, not self-serving)
Periodically fetch a REAL published paper/review on the topic and run at least D1 coverage on its
text (`harness.py cover <fetched.txt> --key …`). A real literature review should cover the key
near-completely; if our paper covers less, the gap is real. This anchors the eval's standard to
actual published work, per the project rule that the eval is tested against objective web papers.
