# EVAL CHANGELOG — the eval's OWN track (do not merge with the project CHANGELOG)

This file moves only when the **eval** changes. It must never change in the same commit that
makes a paper pass. Newest first.

## v0.3.0 — 2026-07-10 — fully developed: all dimensions, all topics, self-tested
- **Full 5-dimension panel demonstrated end-to-end on nuclear-safety** (D1 coverage, D2 steelman,
  D3 objection robustness, D4 reproduce, D4b claim audit, D5 3-referee panel) → one scorecard.
- **Answer keys from real literature for all 4 topics** (nuclear, black-death, alcohol-jcurve,
  ai-employment); all 4 papers scored on the scoreboard.
- **D1/D2 reconciliation:** D1 is now a fast SCREEN (has false negatives from vocabulary
  mismatch); D2 (agent) is authoritative and can RESCUE a screen-missed position it judges
  engaged. Coverage kill fires only on unrescued misses. (Testing surfaced this: ai-employment
  "routine-biased technical change" vs the key's "technological change"; nuclear K6 rescued.)
- **`eval/selftest.py`** — the harness's own golden test (offline; guards coverage + verdict).
- Renamed `eval/corpus/nuclear` → `nuclear-safety` so corpus dir == run name (turnkey loop).
- Added a "How to run (turnkey)" section to EVAL.md.
- **Cross-paper finding:** all 4 papers pass our in-loop `gates/`, but on the independent
  literature eval only `black-death` is clean (7/7 SHIP); `nuclear-safety`, `alcohol-jcurve`, and
  `ai-employment` are REVISE with literature-anchored gaps. The overfit, quantified.
- Still open (belongs to the paper-writing phase, per user): run the full D2/D3/D5 panel on the
  other 3 papers; wire the freehand-baseline A/B arm into the scoreboard.

## v0.2.0 — 2026-07-10 — executable + anchored to real papers
- Built `eval/harness.py` (executable): D1 independent-coverage (paper vs a literature-derived
  key) + D4 reproduce-rate (shells out to the rigor gate) + verdict/kill-criteria + scoreboard.
- Built `eval/protocol.md`: answer-key derivation from real papers + D2/D3/D5 agent prompts &
  strict JSON schemas.
- Added real-paper anchoring to `EVAL.md`: the yardstick is the published literature, not our
  own `positions.md`.
- First real answer key `eval/corpus/nuclear/answer_key.json` — 8 positions + 6 benchmark claims,
  each from a real fetched URL (OWID, IPCC/Wikipedia, GISS, Perrow, UCS, Breakthrough, MIT).
- **First real finding:** our `nuclear-safety` paper scores **6/8 = 75% → REVISE** on the
  independent key (missed K6 nuclear-economics/LCOE and K7 100%-renewables), while our own
  in-loop gate said 7/7 PASS — the overfit, exposed. Calibration: a real comprehensive source
  (Wikipedia "Nuclear power debate") covers 7/8 = 88% of the same key, so the gaps are real.
- Still to do on this track: run the D2/D3/D5 judge panel; build answer keys for the other
  topics; add the freehand-baseline A/B into the scoreboard.

## v0.1.0 — 2026-07-10 — independent eval established (spec)
- Split the eval off from the paper workflow as a frozen, out-of-loop, adversarial judge
  (`eval/EVAL.md`), in response to observed overfitting to the in-loop `gates/`.
- Defined the Isolation Contract (separate tracks, author-blind re-derivation, never softened).
- Specified five independent dimensions with kill-criteria: D1 blind coverage re-map, D2 steelman
  fidelity, D3 objection robustness, D4 claim completeness & honesty, D5 blind referee panel.
- Imported Karpathy's baseline-first / keep-if-better loop and the `eval/scoreboard.tsv` ledger.
- Status: **spec only.** The executable/agent-driven runner is not built yet; running the eval
  today means dispatching its procedures by hand per `EVAL.md`. Building the runner is the next
  eval-track task — and lands here, not in the project changelog.
