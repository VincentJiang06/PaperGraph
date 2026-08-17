# Research log — AI agents 2020-2025 net employment effect (notree arm)

Question: Net effect of AI agents 2020-2025 on employment. Distinguish (a) task-level
substitution vs (b) job-level net change. Confront causal identification: is the observed
MILD employment data because the AI net effect is genuinely near-neutral, or because the
effect is LAGGED and not yet in the data? Give a calibrated judgment.

## Leading hypothesis (to red-team)
H0: Net employment effect 2020-2025 is small/near-neutral IN THE DATA SO FAR, but this is
mostly because true "AI agents" (autonomous agentic systems) barely diffused before 2024-25.
Task-level substitution is real & measurable; job-level net effect is muted by
complementarity + slow GPT diffusion. The mild data is OBSERVATIONALLY CONSISTENT with both
"neutral" and "lagged," but weight of evidence (GPT diffusion history + 2025 entry-level
signals) leans toward "real but lagged & just beginning," NOT "inherently neutral."
Calibration target: lean-lag, low-moderate confidence, honest that data can't yet decide.

## Lines of inquiry (planned)
L1 task-level exposure/substitution (Eloundou; Felten) — exposure ≠ automation
L2 job-level net change — actual 2020-25 labor data (mild) — red team: it's just not there
L3 causal identification problem head-on — quasi-experiments, confounds
L4 LAG hypothesis — GPT diffusion history, J-curve, Solow paradox — adversarial: faster now
L5 entry-level canary — 2025 junior-hiring declines (Brynjolfsson/Stanford) — macro confound
L6 freelance/gig natural experiments — cleanest substitution — representativeness
L7 net-effect theory & macro forecasts — Acemoglu modest vs catastrophic; new tasks

## Search wave log

### Wave 1-3 distilled findings (sources saved to sources/s01..s15)
- TASK-LEVEL (potential): Eloundou — ~80% of workers >=10% of tasks exposed, ~19% >=50%;
  47-56% of tasks with LLM tooling. Explicitly EXPOSURE, not automation forecast. [s01]
- TASK-LEVEL (realized usage): Anthropic Economic Index Nov 2025 — ~52% augmentation vs
  ~45% automation on Claude.ai; software-error-fixing = biggest single task. So actual use
  skews toward augmentation, not pure substitution. [s09]
- AGGREGATE JOB-LEVEL (the "mild data"): Yale Budget Lab — "stability, not major disruption";
  no clear exposure<->unemployment relationship through Aug 2025 [s06]. Brookings — "no AI jobs
  apocalypse—for now"; occupational mix change only marginally faster & PREDATES ChatGPT [s07].
  Anthropic's OWN data — "no systematic increase in unemployment for highly exposed workers
  since late 2022" [s09]. => Aggregate near-flat is a robust, triangulated FACT.
- IDENTIFICATION (the crux): Brookings first-inning — effect "would likely take years to show
  up"; job-posting decline "corresponds better to rising interest rates than to the launch of
  LLMs"; results sensitive to AI measure; confounds = pandemic over-hiring, remote-work,
  tariffs [s08]. Fortune/Yale "AI-washing" — firms dress up over-hiring layoffs as AI [s06].
  => neutral vs lagged is OBSERVATIONALLY UNDERDETERMINED right now.
- ENTRY-LEVEL CANARY: Stanford — 16% relative employment decline for ages 22-25 in most
  exposed occupations, headcount-not-wages, automation-not-augmentation, after firm controls
  [s02]. Grad unemployment ~9.5% (20-24) / entry postings ~45% below avg / SWE listings ~65%
  of Feb-2020 [s13]. BUT engineering "most resilient" (-11% vs -25% overall), softening
  predates ChatGPT, tracks rates [s13,s08]. => strongest disaggregated signal, still confounded.
- CLEAN QUASI-EXPERIMENT: Hui/Reshef/Zhou freelancers — post-ChatGPT ~2% fewer contracts,
  ~5% lower earnings in exposed gigs; TOP freelancers hit harder; DiD design [s04].
  Caveat: gig != traditional employment [s04].
- LAG MECHANISM: Brynjolfsson-Rock-Syverson J-curve — GPT effects lag due to unmeasured
  complementary intangibles [s05]. MIT NANDA — 95% of enterprise GenAI pilots no ROI [s12].
  => productive/organizational diffusion still immature => effect plausibly ahead of the data.
- "FASTER THIS TIME" (anti-lag): Bick et al — gen-AI usage ~39% in 2yr vs ~20% for PC/internet;
  ChatGPT fastest-adopted consumer app [s14]. Compresses but doesn't erase the lag (usage !=
  integration).
- NET-EFFECT SPECTRUM: Acemoglu-Restrepo task framework (displacement - reinstatement +
  scale; "so-so automation" can cut labor demand) [s15]; Acemoglu macro <=0.66% TFP/10yr,
  "nontrivial but modest" [s03]; WEF employer forecast NET +78M jobs by 2030 (170M-92M) [s10];
  Amodei 10-20% unemployment / 50% entry-level gone [s11, vendor incentive]. Order-of-magnitude
  disagreement = itself evidence of deep uncertainty.

### Graveyard (killed / retired lines)
- "Direct employment data on autonomous AI *agents* (2024-25)": essentially NONE exists — true
  agentic deployment is too recent to be in labor data. Killed as a data line, but the ABSENCE
  is itself evidence for the lag reading (most of the causal window hasn't elapsed). Folded into root.
- "Single aggregate AI-attributable productivity number": doesn't exist (Solow-paradox territory);
  unresolvable with current national data. Retired.
- OpenAI gpts-are-gpts page returned HTTP 403; substituted arxiv 2303.10130 abstract for verbatim.
- Yale Budget Lab pages don't render via WebFetch (JS/truncation); captured Yale verbatim via
  Fortune's direct quotes + search-surfaced page text instead.

### Red-team of leading hypothesis (H0 = "real but lagged")
Strongest refutations found: (1) Acemoglu's modest bound — even the FULL effect may be small,
so flat data may just be near-neutrality, not a lag. (2) Real-world usage is augmentation-
dominant (~52%), consistent with complementarity, not displacement. (3) The entry-level signal
has a fully sufficient RIVAL cause (rates + tech over-hiring). => H0 survives but only WEAKLY;
"genuinely near-neutral aggregate net effect so far" cannot be rejected. Posterior stays ~55-60/40-45.
