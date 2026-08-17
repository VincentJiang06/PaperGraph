# Research Log — Minimum wage & employment (2015-2024 US natural experiments)

Question: Does raising the minimum wage reduce employment? Use 2015-2024 US state/city
"natural experiments" as primary evidence; reconcile Card-Krueger near-zero results with
competitive-market disemployment prediction. Roles of monopsony, cost pass-through,
non-wage margins (hours/benefits/hiring bar/automation). Is the effect nonlinear in the
size of the hike / min-wage-to-median ratio? Give a calibrated judgment.

## Method: aggressive blitz — wide, disconfirm-hard, kill thin fast, converge.

## Planned lines of inquiry
- L1 Best recent quasi-experiments (Cengiz bunching; Seattle; state panels) — near-zero?
  - L1.1 [adv] Seattle hours-loss / negative studies; design critiques
- L2 Monopsony as the reconciling mechanism
  - L2.1 [adv] Monopsony overstated / can't explain aggregate zero
- L3 Cost pass-through (prices rise) preserves employment
  - L3.1 [adv] pass-through incomplete; demand response
- L4 Non-wage margins: hours, benefits, scheduling, hiring bar, automation
  - L4.1 [adv] margins small / headcount IS the margin
- L5 Nonlinearity: bite / Kaitz index / min-to-median ratio threshold
  - L5.1 [adv] even high-bite cities show small effects
- L6 Reconciling theory + meta-analysis / publication bias (Dube vs Neumark)
  - L6.1 [adv] Neumark: near-zero is spurious (bad controls)
- L7 Calibrated dose-response & worker heterogeneity (teens/low-skill)

## Running notes — findings (distilled; raw page text discarded)

L1 near-zero (SUPPORTED/high): Cengiz-Dube-Lindner-Zipperer 2019 (138 state changes 1979-2016,
bunching): low-wage jobs "essentially unchanged"; agg employment elasticity 0.024 (s.e..025),
own-wage 0.41 ruling out < -0.45; "no evidence of disemployment ... higher levels." Dube-Lindner
2024 meta: median OWE -0.13 (72 studies), 71% small-neg/positive; retains ~87% of earnings gains.
  [correction] Early WebSearch snippet claimed "rule out below -0.06" — WRONG; primary source says
  agg elasticity CI rules out below -0.074 (Meer-West), own-wage rules out below -0.45. Fixed.

L1.1 Seattle (ADV, real negative): Jardim et al 2017 (UI admin data, $11->$13): hours -6-7%,
wages +3%, payroll -$74/mo/job; hiring of new low-wage entrants declined. The leading US negative
natural experiment — but on HOURS margin + hiring, contested (EPI critique; later work: incumbents
roughly break even, loss falls on reduced new hiring).

L2 monopsony (SUPPORTED-partial/med-high): Azar et al 2024 (ReStud, retail, local MW 2010-16):
employment effect sign FLIPS with concentration — negative low-HHI, "positive in the most highly
concentrated markets"; "direct empirical evidence supporting the monopsony model." Dube-Lindner
restate: non-concentrated OWE ~-0.50 vs concentrated +1.8.

L2.1 (ADV): monopsony alone can't explain the FULL price pass-through + non-falling profits.
Dube-Lindner: imperfect competition "falls short in accounting for a substantial increase in output
prices or a limited pass-through to firm owners." So no single model wins.

L3 pass-through (SUPPORTED/high): Dube-Lindner "most papers find full pass-through" (sometimes
overshifting). Ashenfelter-Jurajda 2021 (McDonald's): 0.2 price elasticity wrt wages, 0.7 wage
elasticity wrt MW -> prices rise (Big Mac). Firms recoup via consumers, not headcount.
L3.1 (ADV): competitive model ALSO predicts pass-through; pass-through predicts job loss UNLESS
output demand ~inelastic. Dube-Lindner: competitive model "correctly emphasizes ... price
pass-through but fails to predict the lack of employment effects—except under ... completely
inelastic output demand." Pass-through necessary, not sufficient.

L4 non-wage margins (SUPPORTED/med-high): Clemens-Kahn-Meer 2018: employer health-insurance
declines offset 9% of wage gains (very-low-wage occ). Hours (Seattle). Lordan-Neumark 2018:
MW cuts share of automatable employment held by low-skilled, raises their nonemployment.
L4.1 (ADV): automation channel weak in biggest low-wage sector — Ashenfelter-Jurajda: "no
association between ... touch screen ordering technology and minimum wage hikes." Dube-Lindner:
mostly NO hours reduction conditional on employment except Seattle. So margins real but bounded/
heterogeneous; automation bites specific subgroups (older/low-skill/mfg), not fast food (yet).

L5 nonlinearity (SUPPORTED-direction/med; threshold fragile): Clemens-Strain 2021: states raising
MW >= $2.50/hr -> OWE -1.01 (young low-skill) vs +0.46 for smaller hikes; "very high degree of
non-linearity." Cengiz: no heterogeneity by Kaitz bite up to 2016 (within observed US range still
flat). Dube-Lindner: "identifying turning points ... essential"; thresholds "fragile," false-discovery
risk. So: dose-response is real but the turning point is not yet cleanly located in US data.

L6 RED-TEAM leading "zero" hypothesis (genuine tension/med): Neumark-Shirley 2022: 79.3% of
estimates negative, 55.4% neg+sig@10%, stronger for teens/young/less-educated, "even more
strongly" for directly-affected workers. Preponderance is NEGATIVE.
L6.x reconciliation: Neumark-Shirley (sign) and Dube-Lindner (magnitude) are BOTH right — most
estimates are negative but SMALL. Dube rubric: OWE > -0.4 = "small negative or positive." Sign
modestly negative; magnitude small at observed bites. This dissolves much of the apparent tension.

L7 calibration (converge): CBO 2019 ($7.25->$15 nat'l ~doubling): median 1.3M jobs lost, CBO range
"about zero and 3.7 million," 17M raised. National uniform hike = very high bite in low-wage states
-> more negative tilt, consistent with L5 nonlinearity. Heterogeneity: teens OWE -0.17/-0.25.

## Dead ends / retired
- "-0.06 CI" claim from a search snippet: misread of Cengiz; corrected to -0.074/-0.45 from source.
- IZA dp14124 expected = grocery Renkin-Montialoux-Siegenthaler; ACTUAL = Ashenfelter-Jurajda
  McDonald's paper. Repurposed (still a clean pass-through + anti-automation source), not killed.
- "Profits absorb the cost" as a separate line: killed/folded — under free entry firms mostly can't
  cut profits (Dube-Lindner); pass-through to prices dominates. Not a distinct reconciling channel.
- EITC-interaction & poverty-incidence lines: out of scope for the employment question; not pursued.
- curl downloads sandboxed (network blocked); CBO cbo.gov 403 to fetch tools -> used pdftotext on
  WebFetch-saved binaries + one accessible restatement page for CBO numbers.
