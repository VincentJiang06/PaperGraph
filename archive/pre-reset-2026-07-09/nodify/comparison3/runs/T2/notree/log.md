# Research Log — QE & wealth inequality causality

## Question
To what extent is QE (2008-2021) a *cause* of widening wealth inequality in advanced economies (US-focused), vs. the counterfactual result of structural forces (aging, skill-biased tech change, globalization)? Distinguish (a) asset-price channel, (b) saver/borrower redistribution channel, (c) macro employment/wage channel. Confront causal identification: how to isolate QE's marginal effect from contemporaneous trends. Give a calibrated judgment.

## Method
Blitz divergence, hypothesis-first + disconfirm-hard, no subagents (budget=0). Verbatim quotes saved to sources/.

## Leading hypothesis (H0, to red-team)
QE materially widened *wealth* inequality via the asset-price channel (equities/housing up, concentrated at top), but the *income* inequality effect is ambiguous-to-progressive via the macro/employment channel; net effect on total inequality is modest and partly counterfactual (structural forces + crisis-prevention baseline). Marginal causal identification is weak; central estimates are model-dependent.

## Planned lines of inquiry
- L1 asset-price channel (adversarial L1.1: counterfactual/crash-prevention)
- L2 saver/borrower redistribution channel (adversarial L2.1: direction ambiguous)
- L3 macro employment/wage channel (adversarial L3.1: weak/top-captured)
- L4 causal identification difficulty (adversarial L4.1: estimates model-dependent)
- L5 structural counterfactual: aging/SBTC/globalization (adversarial L5.1: wealth accel post-2008)
- L6 central-bank & empirical distributional studies (BoE/Fed/ECB/BIS) (adversarial L6.1: incentive to downplay)
- L7 wealth-vs-income distinction / synthesis (red-team H0)

## Search progress
Blitz waves done (WebSearch + WebFetch; PDFs read directly via Read after WebFetch saved them locally).
Direct-read verbatim (strongest): Bivens EPI WP#12 (S02), Brookings/Hutchins media summary incl. Doepke & Beraja (S03), Lee NY Fed HANK (S04), Caravello-McKay-Wolf MIT identification (S05), Montecino-Epstein (S06), Saez-Zucman JEP (S07), Inequality.org (S09).
WebFetch verbatim: BIS 2016 (S01).
Search-surfaced verbatim (context/structural): Saez-Zucman top-share numbers (S07), De Luigi OBES abstract (S08, Wiley paywalled), aging (S10), r* (S11), SBTC/globalization (S12).
Tooling note: BoE, Cleveland Fed, IMF SDN, Wiley all 403/402'd; routed around via BIS/NY Fed/Brookings/EPI which cover the same ground. 12 distinct sources saved to sources/.

Key converging finding across methods: QE lifted EQUITY (concentrated at top → disequalizing on WEALTH tail-measures) AND lowered UNEMPLOYMENT (helps bottom → equalizing on INCOME/Gini). Net sign is chosen by the METRIC. Structural trend (top-share up since ~1980) + low-r* valuation environment dominate and predate QE; QE is partly endogenous to low r*, defeating clean attribution.

## Graveyard (killed lines)
- "Population aging directly produced the QE-era jump in top wealth shares" — KILLED: aging's wealth-inequality effect is two-directional (life-cycle raises it, demographic composition lowers it) and gradual; cannot deliver a sharp 2009-2021 asset-share jump (S10).
- Naive "QE = reverse Robin Hood, unambiguously enriches the rich" — RETIRED/reframed: contradicted by Doepke et al. (wealthy retirees LOSE to inflation; middle-class mortgagors gain), Bivens (house-price gains are progressive), Lee (net Gini falls) (S02,S03,S04).
- Standalone globalization deep-dive — DOWNWEIGHTED: globalization has "moderate effect vs technological progress" and acts on the LABOR-income distribution, not the asset-valuation surge that is QE's contested channel (S12).
- "Central banks simply whitewash the effect" (pure incentive story) — WEAKENED: an outside critic (Montecino-Epstein) finds only "modest" increases while a Fed economist (Lee) finds net-equalizing — the self-serving narrative doesn't cleanly separate insiders from outsiders (S04,S06).
