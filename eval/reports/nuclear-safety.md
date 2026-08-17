# EVAL report — nuclear-safety (arm: gated-v2)

eval-version: 0.3.0 · answer-key: `eval/corpus/nuclear-safety/answer_key.json` (from real literature)

## Verdict: **REVISE**

Kill-criteria tripped:
- ❌ a position was steelman-scored 0 (strawman)
- ❌ a materially-stronger unaddressed objection exists
- ❌ claim-coverage 75% < 100%

## D1 — independent coverage (vs the literature's positions)
screen: **8/8 = 100%** · reconciled with D2: **8/8 = 100%**
- ✅ `K1` Comparative-safety consensus (deaths per TWh) — via "deaths per twh"
- ✅ `K2` Low lifecycle GHG / climate record — via "gco2eq/kwh"
- ✅ `K3` Prevented-mortality / decarbonization value — via "kharecha"
- ✅ `K4` Catastrophic tail-risk / normal accidents — via "fukushima"
- ✅ `K5` Waste longevity & proliferation — via "proliferation"
- ✅ `K6` Nuclear economics / cost (LCOE) — via "lcoe"
- ✅ `K7` 100%-renewables feasibility (nuclear unnecessary) — via "jacobson"
- ✅ `K8` Firm-power / system-cost value of nuclear — via "variable renewables"

## D4 — reproduce-rate (objective rigor input)
12/12

## D2 — steelman fidelity (per position, 0/1/2)
  K1:2, K2:2, K3:2, K4:2, K5:1, K6:1, K7:1, K8:0  → min **0**

## D3 — objection robustness
robust: **False**
- stronger unaddressed objection: By honestly loading Fukushima evacuation (~2,313) and high-end Chernobyl (~27,000) deaths into the numerator, the paper's own concession pushes nuclear to ~0.2-0.5 deaths/TWh — still below coal but now ~an order of magnitude ABOVE wind (~0.035) and solar (~0.019); the paper keeps asserting the thesis's 'comparable to wind and solar' clause and never revisits that its own tail-accounting refutes it.

## D4b — claim completeness & honesty
claim-coverage: **12/16 = 0.75**
- uncited: 'far beneath coal or gas' lifecycle emissions — no ledger row gives a coal/gas gCO2/kWh figure; n1 only compares nuclear to wind/solar, so the 'far lower emissions than fossil fuels' half of the thesis is uncited
- uncited: 'chronic construction overruns such as Vogtle' — asserted with no source row
- uncited: 'spread across the tens of thousands of TWh nuclear has generated' — the denominator of the tail-loading rebuttal, unledgered
- uncited: 'much of the Fukushima evacuation mortality fell on relocated elderly people' — causal/demographic claim doing rebuttal work, unledgered
- ⚠ honesty: 'statistically indistinguishable from wind and solar' asserts equivalence from bare point estimates with no CIs; wind 0.035 > nuclear 0.03, so 'same band' softens
- ⚠ honesty: nuclear 0.03 (c1) is OWID's low-end figure embedding a LOW Chernobyl count; 'already incorporates the accident tolls' obscures that the high-end n7 ~27,000 is NOT inside 0.03
- ⚠ honesty: n1 (IPCC 12g) and n5 (Fukushima 2,313) are sourced to the World Nuclear Association (industry body), not IPCC/official reconstruction directly
- ⚠ honesty: the ~27,000 Chernobyl ceiling understates higher independent projections (TORCH-type)
- ⚠ honesty: the c3 ~821x ratio is best-case: a modestly higher nuclear estimate (0.06-0.07) roughly halves it

## D5 — referee panel
modal verdict: **accept**
- methodology: accept {'thesis': 4, 'evidence': 4, 'counterargument': 4, 'calibration': 5, 'prose': 4}
- counterargument: accept {'thesis': 4, 'evidence': 4, 'counterargument': 4, 'calibration': 4, 'prose': 4}
- evidence: accept {'thesis': 4, 'evidence': 4, 'counterargument': 4, 'calibration': 4, 'prose': 4}
