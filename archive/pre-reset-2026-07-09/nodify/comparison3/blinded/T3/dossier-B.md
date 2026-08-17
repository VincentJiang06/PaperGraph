# Investigation: AI agents 2020–2025 对就业的净效应是什么?区分「任务层面替代」与「岗位层面净增减」,并直面因果识别难题——当前温和的就业数据,究竟是净效应本就接近中性,还是效应存在滞后、尚未显现?

## Lines of inquiry

### L1 [orientation: neutral] — Task-level substitution POTENTIAL is large and cognitive-concentrated
  - statement: How much of work is technically exposed to AI substitution at the TASK level (the numerator of the substitution story)?
  - conclusion: [confirmed / high] Task exposure is pervasive and concentrated in writing/coding/analysis; but "exposure" is potential, not realized job loss.
  - evidence:
      - Eloundou et al., "GPTs are GPTs" (arXiv/Science) — https://arxiv.org/abs/2303.10130 — "around 80% of the U.S. workforce could have at least 10% of their work tasks affected by the introduction of LLMs, while approximately 19% of workers may see at least 50% of their tasks impacted."
      - Eloundou et al. — https://arxiv.org/abs/2303.10130 — "When incorporating software and tooling built on top of LLMs, this share increases to between 47 and 56% of all tasks."
      - Acemoglu & Restrepo, "Automation and New Tasks" (NBER 25684) — https://www.nber.org/papers/w25684 — "automation ... may reduce labor demand even as it raises productivity" (task-level displacement mechanism).

### L1.1 [orientation: adversarial] — Exposure ≠ automation; real-world usage skews to AUGMENTATION
  - statement: Does measured task-exposure translate into task SUBSTITUTION, or is AI mostly used to complement humans?
  - conclusion: [supported / moderate-high] Exposure overstates substitution; actual usage is roughly half augmentation, so task-substitution ≠ job displacement one-for-one.
  - evidence:
      - Eloundou et al. — https://arxiv.org/abs/2303.10130 — "We do not make predictions about the development or adoption timeline of such LLMs." (figures = potential exposure, not realized automation)
      - Anthropic Economic Index (Nov 2025) — https://www.anthropic.com/research/anthropic-economic-index-january-2026-report — Claude.ai usage split ~52% augmentation vs ~45% automation; automation briefly overtook augmentation in Aug 2025 then reversed.
      - Acemoglu, "Simple Macroeconomics of AI" (NBER 32487) — https://www.nber.org/papers/w32487 — of tasks exposed, only a minority are profitably automatable => "these macroeconomic effects appear nontrivial but modest."

### L2 [orientation: neutral] — Aggregate JOB-LEVEL net change 2020–2025 is near-flat in the data
  - statement: Do economy-wide employment/unemployment data show an AI-driven net job change?
  - conclusion: [confirmed / high] Through 2025 the aggregate US labor market shows stability, not economy-wide AI disruption — triangulated across independent teams incl. an AI lab.
  - evidence:
      - Budget Lab at Yale (via Fortune, Feb 2026) — https://fortune.com/2026/02/02/ai-labor-market-yale-budget-lab-ai-washing/ — "No matter which way you look at the data, at this exact moment, it just doesn't seem like there's major macroeconomic effects here."
      - Brookings, "New data show no AI jobs apocalypse—for now" — https://www.brookings.edu/articles/new-data-show-no-ai-jobs-apocalypse-for-now/ — "the overall labor market shows more continuity than immediate collapse."
      - Anthropic, "Labor market impacts of AI" — https://www.anthropic.com/research/labor-market-impacts — "We find no systematic increase in unemployment for highly exposed workers since late 2022".

### L2.1 [orientation: adversarial] — Is "flat aggregate" hiding a large NET reallocation? Forecasts diverge
  - statement: Could a near-flat headline mask big offsetting creation/destruction — and what net sign do forward-looking estimates imply?
  - conclusion: [mixed / low-moderate] Employer forecasts imply a large gross churn with a POSITIVE net, but the forecast distribution is enormous; the flat realized data is consistent with a small net so far.
  - evidence:
      - WEF, Future of Jobs Report 2025 — https://www.weforum.org/press/2025/01/future-of-jobs-report-2025-78-million-new-job-opportunities-by-2030-but-urgent-upskilling-needed-to-prepare-workforces/ — 170M roles created, 92M displaced by 2030 => net +78M jobs (~22% churn).
      - Acemoglu (NBER 32487) — https://www.nber.org/papers/w32487 — "no more than a 0.66% increase in total factor productivity (TFP) over 10 years" (modest net macro effect).

### L3 [orientation: adversarial] — The causal identification problem: neutral vs lagged is UNDERDETERMINED now
  - statement: Can current data even distinguish "net effect is genuinely near-neutral" from "effect exists but is lagged/not yet visible"?
  - conclusion: [confirmed-as-hard / high] No — the two are observationally near-equivalent today; confounds and measure-sensitivity block clean attribution, and self-reports are biased ("AI-washing").
  - evidence:
      - Brookings, "first inning" — https://www.brookings.edu/articles/research-on-ai-and-the-labor-market-is-still-in-the-first-inning/ — "any lasting economic impact would likely take years to show up in employment, output, or productivity data."
      - Brookings, "first inning" — same URL — "The timing of the decline in job postings corresponds better to the macroeconomic shift of rising interest rates than to the launch of LLMs."
      - Budget Lab at Yale (via Fortune) — https://fortune.com/2026/02/02/ai-labor-market-yale-budget-lab-ai-washing/ — "We suspect some firms are trying to dress up layoffs as a good news story rather than bad news, such as past over-hiring." (attribution bias)

### L3.1 [orientation: adversarial] — Does the entry-level decline break the identification tie?
  - statement: Is the young-exposed-worker signal a clean enough wedge to identify AI displacement?
  - conclusion: [weak-lean-lag / low-moderate] It is the strongest disaggregated signal and is triangulated, but even it is jointly explained by a weak macro labor market — not decisive.
  - evidence:
      - Brookings, "no apocalypse" — https://www.brookings.edu/articles/new-data-show-no-ai-jobs-apocalypse-for-now/ — "consistent with emerging evidence that AI may be contributing to unemployment among early-career workers. (It could also be consistent with evidence that a weakening labor market is hurting those same workers.)"
      - Anthropic, "Labor market impacts" — https://www.anthropic.com/research/labor-market-impacts — "suggestive evidence that hiring of younger workers has slowed in exposed occupations".

### L4 [orientation: neutral] — The LAG hypothesis via general-purpose-technology diffusion history
  - statement: Do GPTs historically deliver measured labor/productivity effects only with a multi-year lag, implying today's flat data understates the eventual effect?
  - conclusion: [supported / moderate] Yes — GPT effects lag due to slow complementary reorganization; enterprise integration is still immature, so labor effects are plausibly still ahead.
  - evidence:
      - Brynjolfsson, Rock & Syverson, "Productivity J-Curve" (AEJ:Macro 2021) — https://www.aeaweb.org/articles?id=10.1257%2Fmac.20180386 — "This can lead to underestimation of productivity growth in a new GPTs early years and, later, when the benefits of intangible investments are harvested, productivity growth overestimation."
      - MIT Project NANDA, "GenAI Divide 2025" (via Fortune) — https://fortune.com/2025/08/18/mit-report-95-percent-generative-ai-pilots-at-companies-failing-cfo/ — ~95% of enterprise generative-AI pilots delivered no measurable P&L return.
      - Brookings, "first inning" — https://www.brookings.edu/articles/research-on-ai-and-the-labor-market-is-still-in-the-first-inning/ — "Previous technological revolutions showed up in economic data years or decades later".

### L4.1 [orientation: adversarial] — "This time is faster": record adoption argues against a long lag
  - statement: Gen-AI diffuses faster than any prior GPT — doesn't that compress or eliminate the lag?
  - conclusion: [partial / moderate] Usage diffusion is unprecedentedly fast, which shortens the lag, but usage ≠ productive integration, so a moderate lag survives.
  - evidence:
      - Bick, Blandin & Deming, "Rapid Adoption of Generative AI" (NBER 32966), via Harvard Gazette — https://news.harvard.edu/gazette/story/2024/10/generative-ai-embraced-faster-than-internet-pcs/ — ~39% of individuals used gen-AI two years post-ChatGPT vs ~20% for PCs/internet at comparable horizons.
      - MIT NANDA (via Fortune) — https://fortune.com/2025/08/18/mit-report-95-percent-generative-ai-pilots-at-companies-failing-cfo/ — despite $30-40B invested, 95% of pilots show no return (usage races ahead of ROI => integration lag persists).

### L5 [orientation: neutral] — The entry-level "canary": leading edge of realized displacement
  - statement: Is displacement appearing first, and sharply, among junior workers in exposed occupations?
  - conclusion: [supported / moderate] A real, concentrated entry-level decline exists in exposed occupations, adjusting via headcount and in automation-prone tasks — consistent with early displacement.
  - evidence:
      - Brynjolfsson et al., "Canaries in the Coal Mine" (Stanford, Nov 2025) — https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/ — "early-career workers (ages 22-25) in the most AI-exposed occupations have experienced a 16 percent relative decline in employment ... even after controlling for firm-level shocks."
      - Stanford Canaries — same URL — "employment declines are concentrated in occupations where AI is more likely to automate, rather than augment, human labor" and "adjustments occur primarily through employment rather than compensation."
      - CNBC / NY Fed data — https://www.cnbc.com/2025/11/23/college-graduates-are-struggling-to-find-jobs-ai-is-partly-to-blame.html — young-graduate unemployment elevated (~9.5% for 20-24 BA+; entry-level postings ~45% below 5-yr average).

### L5.1 [orientation: adversarial] — Macro confound: rate hikes + tech over-hiring, not AI
  - statement: Is the entry-level softness cyclical (rates, post-pandemic over-hiring correction) rather than AI-caused?
  - conclusion: [live / moderate] A large share of entry-level softening is cyclical; it predates ChatGPT and engineering roles proved resilient — both forces operate, AI's share is unidentified.
  - evidence:
      - TechCrunch (Jun 2026) — https://techcrunch.com/2026/06/24/ai-was-supposed-to-kill-engineering-jobs-but-new-data-suggests-theyre-the-most-resilient/ — big-tech hiring fell ~25% vs 2019 but engineering roles fell only ~11%; engineers = 55% of 2025 new hires ("most resilient").
      - Brookings, "first inning" — https://www.brookings.edu/articles/research-on-ai-and-the-labor-market-is-still-in-the-first-inning/ — job-posting decline tracks rising interest rates better than the LLM launch.

### L6 [orientation: neutral] — Freelance/gig natural experiment: cleanest task→job substitution
  - statement: Where substitution should show first (text/image gigs), is there causal evidence of job/earnings loss?
  - conclusion: [supported / moderate] Post-ChatGPT, exposed freelancers lost work and earnings, with the best-rated hit hardest — the cleanest causal design available, though modest in size.
  - evidence:
      - Hui, Reshef & Zhou (via Brookings) — https://www.brookings.edu/articles/is-generative-ai-a-job-killer-evidence-from-the-freelance-market/ — exposed freelancers saw "a decline of approximately 2% in the number of new monthly contracts" and "a roughly 5% decrease in their total monthly earnings on the platform."
      - Hui, Reshef & Zhou (via Brookings) — same URL — "those with stronger past performance ... experience larger declines" (quality does not protect).

### L6.1 [orientation: adversarial] — Representativeness: gig ≠ standard employment
  - statement: Do freelance results generalize to the broader labor market?
  - conclusion: [valid caveat / moderate] The authors themselves caution against generalizing; gig demand is more elastic than salaried employment, so this is likely an upper bound.
  - evidence:
      - Hui, Reshef & Zhou (via Brookings) — https://www.brookings.edu/articles/is-generative-ai-a-job-killer-evidence-from-the-freelance-market/ — freelance evidence "may not fully capture the dynamics of traditional employment arrangements or long-term contractual relationships."

### L7 [orientation: adversarial] — Net-effect theory & forecast divergence (red-team of the leading hypothesis)
  - statement: What does theory say the net sign should be, and does the expert forecast spread let us rule out "genuinely near-neutral"?
  - conclusion: [cannot-reject-neutral / moderate] Net sign = displacement − reinstatement + scale; credible academic central estimates are modest, and the order-of-magnitude forecast spread means "genuinely small net effect" remains fully alive — the lag lean is weak, not strong.
  - evidence:
      - Acemoglu & Restrepo (NBER 25684) — https://www.nber.org/papers/w25684 — "Some automation technologies may in fact reduce labor demand because they bring sizable displacement effects but modest productivity gains" ("so-so automation").
      - Acemoglu (NBER 32487) — https://www.nber.org/papers/w32487 — "these macroeconomic effects appear nontrivial but modest" (≤0.66% TFP/10yr).
      - Dario Amodei warning (Axios/Fortune, May 2025) — https://fortune.com/2025/05/28/anthropic-ceo-warning-ai-job-loss/ — AI could eliminate ~half of entry-level white-collar jobs and push unemployment to 10-20% (vendor-incentivized catastrophic tail).

## Dead ends / retired
  - Direct employment data on autonomous "AI *agents*" (2024–25) — essentially none exists; true agentic deployment is too recent to appear in labor data. Killed as a data line, but the ABSENCE itself supports the lag reading (most of the causal window post-dates the study period) — folded into the root.
  - A single AI-attributable aggregate productivity number — does not exist (Solow-paradox territory); unresolvable with current national accounts. Retired.
  - OpenAI "gpts-are-gpts" primary page (HTTP 403) — substituted arXiv 2303.10130 abstract for the same verbatim figures.
  - Yale Budget Lab pages would not render via fetch — captured Yale verbatim via Fortune's direct quotes + search-surfaced page text.

## Root conclusion
[lean-lag, but only weakly / low-to-moderate confidence]

Separate the two layers the question asks for — the evidence answers them differently:
1. **Task-level substitution is already real, measurable, and sizable** in exposed cognitive domains: freelance contracts −2% / earnings −5% (clean quasi-experiment, L6); a −16% relative employment decline for 22–25-year-olds in the most exposed occupations (L5); software-error-fixing as the single largest AI task (L1.1). Exposure is pervasive (~80% of workers ≥10% of tasks; ~47–56% of tasks with tooling, L1).
2. **Job-level NET change economy-wide 2020–2025 is near-flat in the data** — a robust, triangulated fact across Yale, Brookings, and even Anthropic's own analysis (L2). Task substitution has NOT yet aggregated into an economy-wide net employment swing.

**On the causal question — near-neutral vs lagged — the honest answer is that current aggregate data cannot decide** (L3): the flat headline is observationally consistent with both, confounded by rate hikes, pandemic over-hiring, remote-work and tariff exposure, and polluted by "AI-washing." My calibrated posterior tilts **~55–60% toward "real but still-emerging/lagged, concentrated at the entry level" and ~40–45% toward "genuinely modest net effect so far,"** for three reasons: (i) genuine agentic AI barely deployed before 2024–25, so most of the causal window has not elapsed; (ii) GPT diffusion history (J-curve) plus a 95% enterprise-pilot failure rate say productive integration is immature — usage has raced ahead of ROI (L4/L4.1); (iii) the one clean disaggregated signal (young exposed workers, triangulated by Stanford + Anthropic) points to early, concentrated displacement (L5). **But this lean is deliberately weak**: Acemoglu's modest bound (≤0.66% TFP/10yr), augmentation-dominant real-world usage (~52%), and a fully sufficient macro rival-cause for the entry-level dip mean "genuinely near-neutral aggregate net effect" cannot be rejected (L7/L5.1). Anyone claiming high confidence in EITHER an imminent jobs apocalypse or a permanent neutrality is over-reaching the evidence.

Bottom line: **task-level displacement is here; job-level net effect is near-zero SO FAR; and the flatness is best read as "early and partly lagged" rather than "proven neutral," but only at low-to-moderate confidence.** The next 2–4 years of disaggregated (occupation × experience) data — not aggregate unemployment — are where the answer will actually be settled.

## Open gaps
  - No direct labor data on autonomous AI *agents* specifically (the named subject); 2024–25 deployment is too recent to have entered employment statistics.
  - No credible instrument separates AI from the macro cycle in the entry-level signal — attribution remains fundamentally underdetermined.
  - Firm-level productivity gains have not aggregated into national output/productivity data (a live Solow-paradox / J-curve question).
  - Expert forecasts span an order of magnitude (WEF net +78M jobs vs Amodei 10–20% unemployment) with no ex-ante way to adjudicate; even 2026 evidence is contested (TechCrunch "engineering most resilient" vs ServiceNow-CEO ">30% grad unemployment" claim).
  - Whether real-world usage stays augmentation-dominant or tips toward automation as agentic capability matures is unresolved and would flip the net-effect sign.
