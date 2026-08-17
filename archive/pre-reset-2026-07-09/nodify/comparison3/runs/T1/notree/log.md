# Research Log — US Inflation 2021-2023 demand/supply attribution (notree arm)

Question: Quantitative/semi-quantitative attribution of 2021-2023 US high inflation between
DEMAND side (fiscal transfers + loose money) vs SUPPLY side (supply-chain disruption, tight
labor market, energy/commodity shocks). Approx contributions? Implication for soft-landing
sustainability?

## Planned lines of inquiry (blitz divergence)
- L1: Canonical quantitative decompositions (Bernanke-Blanchard; Shapiro SF Fed supply/demand)
- L2: Demand-side magnitude — fiscal stimulus (ARP/CARES) contribution (SF Fed Jordà; Furman; Cochrane FTPL)
- L3: Supply-side magnitude — supply chain (GSCPI), energy/commodity, food
- L4: Labor-market tightness as driver — wage-price spiral? (Bernanke-Blanchard tightness term; Domash-Summers)
- L5: Monetary/M2 monetarist line (contrarian) — did money supply drive it?
- L6: The 2022-2024 DISINFLATION — what brought it down? supply healing vs demand destruction
- L7 [RED TEAM]: decomposition ill-posed / demand-supply interact / soft-landing already happened

## Findings log (distilled; raw page text discarded, verbatim saved to sources/)
- L1: Bernanke-Blanchard (S01): initial surge = relative price shocks + sectoral shortages, "largely transient";
  labor tightness "little effect early on," became "limited but sustained" later; transience traced to anchored
  expectations. => early inflation SUPPLY-dominated; demand-via-tightness a later, secondary, persistent layer.
- L1: Shapiro SF Fed (S02): sign-restriction split of PCE into supply- vs demand-driven; method has endogeneity/
  set-identification caveats (=> feeds L7).
- L2: Jordà SF Fed (S03): US fiscal transfers raised inflation ~3pp by Q4 2021 (Phillips-curve counterfactual),
  "considerable uncertainty." This is the headline DEMAND-side number and it explains the US-vs-others gap.
- L2: Furman/FactCheck (S04): ARP added ~1-4pp, Furman midpoint 2.5pp; ~1/4 to 1/2 of the 8.5% (Mar-2022) CPI.
- L2/L5: Cochrane FTPL (S09): $5T deficit-financed transfers => fiscal theory story; "all significant inflations
  come from fiscal problems." Contrarian pure-demand read; concedes COVID itself was a supply shock.
- L3: SF Fed 2023 (S05): GSCPI supply-chain shocks ~60% of the above-trend run-up of HEADLINE inflation Apr21-Mar23.
- L3: Fed oil DSGE (S06): oil added ~1pp to HEADLINE (2022Q1) but only 0.17pp to CORE in 2022 => energy big for
  headline, small for core; largely reversed later.
- L4: Domash-Summers (S07): labor super-tight (V/U at sub-2% U levels), wage growth 6.5% (40-yr high); predicted
  disinflation would need big unemployment rise. FORECAST FAILED (see L6) => wage-price-spiral risk overstated.
- L5: CEPR/Borio (S08): cross-country excess M2 growth 2020 correlates ~1:1 with 2021-22 inflation; but long/
  variable lag (inflation peaked ~18mo after M2 peak, M2 already normal) => money as marker of demand, weak as
  standalone mechanism/timing.
- L6: Allianz (S10): 2023 disinflation ~ -7pp; supply-chain -5pp, oil -0.6pp, expectations -0.3pp, Fed demand-cool
  -2pp + expectations-anchor -3pp = -5pp ("half is the Fed"). INTERNAL TENSION: also says "bulk" is supply chain.
- L6: Roosevelt (S12): 73% of core-PCE disinflation from SUPPLY expansion (prices down, quantities up), 87% for
  core goods. => disinflation supply-led, non-recessionary.
- L6: Ferguson-Storm (S13): Fed tightening did <1/5 of the 2022-24 disinflation; rest = supply normalization.
- L6/DEMAND-rebuttal: Shapiro SF Fed 2025 (S14): demand-driven CORE fell 2pp since summer 2022 (largest deliberate
  disinflation since 1969); MP counterfactual = demand inflation would have kept rising absent hikes. => demand
  was real and policy-addressable, Fed did materially cut the demand component.
- L6/L7: Fed FEDS 2025 (S11): surge = "severe imbalances between supply and demand"; anchored LONG-term expectations
  "prevented a larger or more lasting increase" and, with easing imbalances, "allowed inflation to fall... without
  a large increase in unemployment." => official synthesis: BOTH sides; expectations the linchpin of soft landing.
- L7: Method caveats (S15): supply/demand shares only set-identified, noisy, sensitive to item classification =>
  precise numeric split not point-identified; shares are method-dependent, not additive across studies.

## Key cross-study tension (the crux)
Headline vs core, and surge vs disinflation, give different "shares":
- HEADLINE surge: supply (chain+energy) ~60%+; fiscal-demand ~3pp is large but overlaps.
- CORE / persistence: demand (fiscal + tightness + anchored-then-slipping expectations) carries more weight.
- DISINFLATION: mostly supply-led (Roosevelt 73%, Allianz "bulk"), but Fed cut the demand component (Shapiro 2pp).
Studies are NOT additive (different targets, samples, methods) => only a BAND, not a point split, is defensible.

## Graveyard (killed / thin lines)
- Pure monetarist M2 causation as a *timing/mechanism* claim: KILLED as primary — cross-country correlation real
  (S08) but 18-month lag + M2 already-normal-at-peak means M2 is a coincident marker of the fiscal/demand impulse,
  not an independent driver with predictive timing. Kept as supporting evidence for demand side, not its own line.
- "Wage-price spiral drove it" (strong Domash-Summers version): KILLED — the spiral never materialized; disinflation
  came without the predicted unemployment surge (S07 forecast vs S11/S12/S14 outcome).
- "Last-mile / logistics" query drift: KILLED (search returned delivery-logistics noise, irrelevant).
- Point-estimate single split (e.g., "X% demand / Y% supply"): KILLED as ill-posed (S15) — report a band + regime
  dependence instead.
