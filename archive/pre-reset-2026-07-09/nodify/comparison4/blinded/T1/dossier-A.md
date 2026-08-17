# Investigation: What does 2020–2025 first-hand empirical evidence say about AI/automation's effect on labor markets?

Scope: a systematic evidence map of first-hand empirical studies (RCT / quasi-experiment /
observational), stratified by methodological quality, with per-facet weighted syntheses and open
questions. 27 studies catalogued (`sources/S1–S27.txt`).

**Evidence-quality ladder used to weight everything below.** Tier A = pre-registered RCT / field
experiment (causal, but task-level & short). Tier B = quasi-experiment on real outcomes (DiD/IV on
administrative or platform data). Tier C = observational/correlational. Tier D = exposure/usage
indices & structural models (capability ≠ adoption ≠ impact). The load-bearing caveat throughout:
**task-level gains (A) ≠ job/wage outcomes (B/C) ≠ exposure potential (D)** — never treat a Tier-D
"80% exposed" headline as commensurable with a Tier-B null.

## Lines of inquiry

### L1 [neutral] Task-level: does GenAI substitute or augment, and does it raise output?
  - statement: On bounded knowledge tasks, does GenAI make workers faster and/or better, and for whom?
  - conclusion: **[augmentation-dominant, quality-effect model-vintage-dependent / HIGH confidence for speed on simple tasks, MODERATE for quality and for complex work].** Tier-A RCTs converge: large SPEED gains on well-scoped tasks, concentrated in novices/low-skill; QUALITY gains were small/uneven under GPT-4 but become significant with reasoning models + RAG. Crucially NOT a universal speedup — on complex, familiar work it can *slow experts down*. "Augment" ≠ "always faster/better."
  - evidence:
      - Generative AI at Work (Brynjolfsson, Li, Raymond) — https://arxiv.org/abs/2304.11771 — "Access to AI assistance increases worker productivity, as measured by issues resolved per hour, by 15% on average ... Less experienced and lower-skilled workers improve both the speed and quality of their output while the most experienced and highest-skilled workers see small gains in speed and small declines in quality."
      - Experimental evidence on the productivity effects of generative AI (Noy & Zhang, Science 2023) — https://pubmed.ncbi.nlm.nih.gov/37440646/ — "ChatGPT substantially raised productivity: The average time taken decreased by 40% and output quality rose by 18%."
      - Navigating the Jagged Technological Frontier (Dell'Acqua et al., BCG RCT) — https://mitsloan.mit.edu/sites/default/files/2023-10/SSRN-id4573321.pdf — "consultants using AI were significantly more productive ... For a task selected to be outside the frontier, however, consultants using AI were 19 percentage points less likely to produce correct solutions compared to those without AI."
      - GitHub Copilot RCT (Peng et al.) — https://arxiv.org/abs/2302.06590 — "The treatment group, with access to the AI pair programmer, completed the task 55.8% faster than the control group."
      - [ADVERSARIAL] METR — Early-2025 AI & Experienced OSS Developers — https://arxiv.org/pdf/2507.09089 — "When developers are allowed to use AI tools, they take 19% longer to complete issues" (yet "still believed AI had sped them up by 20%").
      - Lawyering in the Age of AI (Choi, Monahan, Schwarcz) — https://openscholarship.wustl.edu/law_scholarship/964/ — "AI assistance only slightly and inconsistently improved the quality of participants' legal analysis but induced large and consistent increases in speed."
      - AI-Powered Lawyering (Schwarcz et al., 2026) — https://journals.sagepub.com/doi/10.1177/2755323X261427048 — reasoning models + RAG "significantly enhance legal work quality," "a marked contrast with previous research examining older large language models like GPT-4," with productivity gains "of anywhere from 50% to 130%."

### L2 [neutral] Job-level: net employment / labor demand
  - statement: Has realized AI adoption reduced employment or hiring in the aggregate or in exposed segments?
  - conclusion: **[no discernible aggregate effect yet, with real segment-specific displacement / MODERATE-HIGH confidence for the aggregate null, MODERATE for segment losses].** The best realized-outcome evidence (admin payroll, firm postings, occupational-mix tracking) finds NO economy-wide or firm-level disruption through ~2025. Genuine negative demand exists but is *occupation-specific* (freelance translation, copyediting) and coexists with demand *growth* elsewhere (web development). The historical robot benchmark (a different technology) is the one clear negative — and it is not GenAI.
  - evidence:
      - Yale Budget Lab — Evaluating the Impact of AI on the Labor Market (CPS, 33 months) — https://budgetlab.yale.edu/research/evaluating-impact-ai-labor-market-current-state-affairs — "The picture of AI's impact on the labor market that emerges from our data is one that largely reflects stability, not major disruption at an economy-wide level ... no discernible disruption since ChatGPT's release 33 months ago."
      - Fed (FEDS Notes) — AI Adoption and Firms' Job-Posting Behavior — https://www.federalreserve.gov/econres/notes/feds-notes/ai-adoption-and-firms-job-posting-behavior-20260327.html — "there is no evidence of a reduction in job postings for industries or firms which have higher levels of AI adoption."
      - [ADVERSARIAL to null] Short-Term Effects of GenAI on an Online Labor Market (Hui, Reshef, Zhou) — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4527336 — "freelancers in occupations more exposed to generative AI have experienced a 2% decline in the number of contracts and a 5% drop in earnings."
      - AI and Freelancers: Has the Inflection Point Arrived? (Qiao, Rui, Xiong) — https://gwern.net/doc/economics/automation/2024-qiao.pdf — "displacement effects in translation & localization OLM, reducing freelancers' work volume and earnings; 2) productivity effects in web development OLM, increasing freelancers' work volume and earnings."
      - [historical benchmark] Robots and Jobs (Acemoglu & Restrepo, JPE 2020) — https://www.nber.org/papers/w23285 — "one more robot per thousand workers reduces the employment to population ratio by about 0.18-0.34 percentage points."

### L3 [neutral] Wages / earnings / hours
  - statement: Does realized AI use raise, lower, or leave unchanged workers' pay and hours?
  - conclusion: **[small and skill-heterogeneous, not the headline premium / MODERATE confidence].** The credible causal (Tier-B admin-IV) wage signal is ~0 on average but skill-biased upward: experts gain a little, the bottom of the distribution loses a little. The large "+56% AI-skill premium" is Tier-D selection, not a causal return. Occupation-level displacement can be large (translation −29.7%) but is local to a platform/occupation, not economy-wide.
  - evidence:
      - AI in Demand (Storm, Gonschor, Schmidt — German admin IV) — https://irihs.ihs.ac.at/id/eprint/7345/1/ihs-working-paper-2025-storm-gonschor-schmidt-ai-in-demand.pdf — "We find no meaningful displacement or productivity effects on average ... A doubling in the share of AI vacancies implies a moderate earnings increase among expert workers by 0.65% ... In contrast, non-experts face earnings declines of up to -0.3% ... For the lowest decile ... earnings by 3.9%."
      - Large Language Models, Small Labor Market Effects (Humlum & Vestergaard — Denmark admin DiD) — https://bfi.uchicago.edu/working-papers/large-language-models-small-labor-market-effects/ — "estimate precise null effects on earnings and recorded hours at both the worker and workplace levels, ruling out effects larger than 2% two years after."
      - [Tier-D counter, do-not-over-read] PwC 2025 Global AI Jobs Barometer — https://www.pwc.com/gx/en/issues/artificial-intelligence/job-barometer/2025/report.pdf — "Workers with AI skills like prompt engineering command a 56% wage premium (up from 25% last year)" and "Wages are rising 2x faster in industries most vs least exposed to AI."
      - AI and Freelancers (Qiao et al.) — https://gwern.net/doc/economics/automation/2024-qiao.pdf — translation earnings "decrease in worker's earnings from focal jobs by 29.7%."

### L4 [neutral→adversarial] Special populations: youth / entry-level
  - statement: Is GenAI disproportionately reducing entry-level/young-worker employment?
  - conclusion: **[CONTESTED — a real relative decline exists, but its AI attribution is disputed / LOW-MODERATE confidence in the AI-causal reading].** One high-frequency payroll study finds a sharp *relative* decline for 22–25-year-olds in automate-type exposed jobs. A direct re-analysis argues the timing predates ChatGPT and matches the 2022 monetary-tightening cycle plus a cohort "aging illusion." The AI-vs-interest-rate horse race has not been run, so the causal story is not settled.
  - evidence:
      - Canaries in the Coal Mine (Brynjolfsson, Chandar, Chen — ADP payroll) — https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/ — "early-career workers (ages 22-25) in the most AI-exposed occupations have experienced a 16 percent relative decline in employment ... Employment declines are concentrated in occupations where AI is more likely to automate, rather than augment, human labor."
      - [ADVERSARIAL] Looking for the Ladder (Iscenko & Curto Millet, EIG) — https://eig.org/wp-content/uploads/2026/01/TAWP-Iscenko-Millet.pdf — "This hiring slowdown predates any plausible generative AI effect by over six months ... There is no evidence that job postings for junior roles within occupations most exposed to AI have declined more than postings for senior positions."
      - [reconciler] Yale Budget Lab — https://budgetlab.yale.edu/research/evaluating-impact-ai-labor-market-current-state-affairs — "measures of AI exposure, automation, and augmentation show no sign of being related to changes in employment or unemployment to date" (an aggregate null can coexist with a concentrated subgroup effect).

### L5 [neutral] Cross-national / development-level
  - statement: How does exposure and realized impact vary across countries and development levels?
  - conclusion: **[exposure skews rich-country & female; realized effects small/heterogeneous where measured / MODERATE confidence].** Exposure *potential* is concentrated in high-income countries and in female/clerical work — the opposite of the male-manufacturing robot story. Realized-outcome admin studies now exist in two rich economies (Denmark, Germany), both small/null on average with skill heterogeneity; the one developing-economy field RCT (Kenya) is polarizing.
  - evidence:
      - ILO Refined Global Index of Occupational Exposure (Gmyrek, Winkler et al.) — https://www.ilo.org/publications/generative-ai-and-jobs-refined-global-index-occupational-exposure — "one in four workers are in an occupation with some GenAI exposure ... 11% of total employment in LICs vs 34% in HICs" and "female (4.7%) and male employment (2.4%)" in the highest exposure category.
      - The Uneven Impact of GenAI on Entrepreneurial Performance: Kenya field RCT (Otis et al.) — https://www.hbs.edu/faculty/Pages/item.aspx?num=65159 — "High performers benefited by just over 20% from AI advice, whereas low performers did roughly 10% worse with AI assistance."
      - AI in Demand (Germany) — https://irihs.ihs.ac.at/id/eprint/7345/1/ihs-working-paper-2025-storm-gonschor-schmidt-ai-in-demand.pdf — "no meaningful displacement or productivity effects on average, but notable skill heterogeneity."

### L6 [ADVERSARIAL — the skeptic spine] "GenAI's realized labor-market effect is negligible / not yet detectable."
  - statement: Is the honest reading of realized data that AI has, so far, no measurable aggregate labor-market effect?
  - conclusion: **[TRUE for the AGGREGATE and the AVERAGE, FALSE as "no effect at all" / HIGH confidence for the scoped version].** The null replicates across four independent aggregation levels — task-hours, worker-admin (DK/US/DE), occupational-mix, and firm/industry postings — and structural macro models cap the near-term upside as modest. But the null is about the MEAN, not the VARIANCE: real within-distribution and occupation-specific moves exist. "Negligible aggregate effect" is well-supported; "no distributional effect" is not.
  - evidence:
      - The Rapid Adoption of Generative AI (Bick, Blandin, Deming) — https://cepr.org/voxeu/columns/rapid-adoption-generative-ai — "Between 1% and 8% of all work hours in the US are currently assisted by generative AI" (why huge per-task RCT gains have not moved aggregates).
      - The Simple Macroeconomics of AI (Acemoglu) — https://www.nber.org/papers/w32487 — "no more than a 0.66% increase in total factor productivity (TFP) over 10 years."
      - [COUNTER-VIEW, keeps macro unsettled] AI and Growth: Where Do We Stand? (Aghion & Bunel) — https://www.frbsf.org/wp-content/uploads/AI-and-Growth-Aghion-Bunel.pdf — "a median estimate of 0.68pp additional annual total factor productivity (TFP) growth" (~10× Acemoglu, from the same framework with different inputs).
      - Fed — AI Adoption and Firms' Job-Posting Behavior — https://www.federalreserve.gov/econres/notes/feds-notes/ai-adoption-and-firms-job-posting-behavior-20260327.html — "no evidence across the range of models that firm-level AI investment is having a negative impact on subsequent job-posting behavior."

### L7 [neutral] Distributional sign: does AI EQUALIZE or POLARIZE?
  - statement: Does AI compress or widen skill/earnings differences among workers?
  - conclusion: **[LEVEL-DEPENDENT: equalizes individual output quality, polarizes market earnings / MODERATE-HIGH confidence].** On bounded *execution* tasks, AI lifts novices most and compresses the output-quality distribution (equalizing). But at the *market/earnings* level and on *judgment/advice* tasks, it favors experts/top deciles and harms the bottom — and even the individual-equalizing story carries a collective-homogenization cost. "AI democratizes skill" survives only as a statement about one worker's task output, not as an economic (earnings/employment) claim.
  - evidence:
      - [EQUALIZE, individual output] Noy & Zhang — https://pubmed.ncbi.nlm.nih.gov/37440646/ — "Inequality between workers decreased" (ChatGPT benefited lower-ability workers more). Corroborated by Dell'Acqua et al. (below-average +43% vs above +17%) and Choi et al. ("equalizing effect on performance").
      - [POLARIZE, market earnings] AI in Demand (German admin) — https://irihs.ihs.ac.at/id/eprint/7345/1/ihs-working-paper-2025-storm-gonschor-schmidt-ai-in-demand.pdf — "These findings cast doubt on optimistic views of AI as a potential leveler for reducing inequality (Autor 2024)."
      - [POLARIZE, judgment tasks] Kenya field RCT (Otis et al.) — https://www.hbs.edu/faculty/Pages/item.aspx?num=65159 — high performers +~20%, low performers −~10%.
      - [POLARIZE, market demand] Hui, Reshef, Zhou — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4527336 — "those with stronger past performance ... experience larger declines" (top freelancers hit worst).
      - [collective cost] Doshi & Hauser (Science Advances 2024) — https://pmc.ncbi.nlm.nih.gov/articles/PMC11244532/ — GenAI yields "an increase in individual creativity at the risk of losing collective novelty."

### L-quality [neutral] Output quality, homogenization, and worker overreliance (an externality no wage/employment metric captures)
  - statement: Beyond speed and jobs, does AI change the quality of output and the skill/vigilance of the worker?
  - conclusion: **[real but under-measured longitudinally / MODERATE confidence for the mechanism, LOW for long-run skill atrophy].** AI raises individual output but homogenizes it across producers, and self-reports show workers offload cognitive effort and scrutinize AI less as they trust it more — an overreliance channel consistent with the jagged-frontier and expert-slowdown harms. No true longitudinal deskilling study exists yet.
  - evidence:
      - Doshi & Hauser — https://pmc.ncbi.nlm.nih.gov/articles/PMC11244532/ — AI-assisted stories became "more similar to the average of other stories within the same condition."
      - The Impact of GenAI on Critical Thinking (Lee et al., Microsoft/CMU, CHI 2025) — https://www.microsoft.com/en-us/research/publication/the-impact-of-generative-ai-on-critical-thinking-self-reported-reductions-in-cognitive-effort-and-confidence-effects-from-a-survey-of-knowledge-workers/ — "higher confidence in GenAI is associated with less critical thinking, while higher self-confidence is associated with more critical thinking."
      - METR OSS-dev RCT — https://arxiv.org/pdf/2507.09089 — the ~39-point gap between believed (+20%) and actual (−19%) speed is the overreliance mechanism made concrete.

## Dead ends / retired
- **KILLED — "GenAI has already caused aggregate net job loss / mass unemployment (2025)."** No Tier-A/B/C study supports an economy-wide net job loss; Yale (S13), Denmark (S5), Germany (S21) and the Fed firm-postings note (S26) affirmatively find no aggregate/average/firm-level disruption. Only relative/subgroup effects (S6, itself contested) and occupation-specific demand drops (S10/S23) exist.
- **KILLED — "AI uniformly equalizes / democratizes skill (as an economic claim)."** Survives ONLY at the individual-output level on bounded tasks (S1/S2/S3/S24). At the market/earnings level it polarizes (S21 "casts doubt on AI as a leveler"; S16; S10; S23). Never state equalization as an economic finding without specifying the level.
- **DEMOTED (not killed) — "The entry-level youth decline is settled first-hand evidence of AI-caused job loss."** S20/EIG supplies a documented rival cause (2022 monetary tightening + narrow-cohort aging illusion; decline predates ChatGPT ~6mo). Downgraded to CONTESTED; both lines kept alive pending a study that separates AI exposure from interest-rate sensitivity.
- **WATCH (do not adopt) — "The 56% AI-skill wage premium proves AI causally raises wages."** Tier-D selection/composition (who lists AI skills), not a causal return; the Tier-B causal estimate (S21) is far smaller (~0 average, +0.65% experts) and heterogeneous.
- **RETIRED prediction — "AI will eliminate radiologists."** Left as an open gap rather than a finding: clinical accuracy/workload studies exist (e.g., ~44% workload reduction claims) but no clean first-hand employment/wage outcome, and radiologist employment has not collapsed. Flagged under Open gaps, not asserted.

## Root conclusion
**[negligible-realized-aggregate-effect + genuine-distributional-and-occupational-shifts / MODERATE-HIGH confidence, appropriately scoped].**

Weighting by methodological quality, the 2020–2025 first-hand record supports a two-part conclusion.
(1) **On task performance (Tier-A RCTs): GenAI is a real, augmentation-dominant productivity tool** —
large speed gains on well-scoped work, concentrated in novices/low-skill, with quality effects that
were modest under GPT-4 and grow with reasoning models — **but it is not a universal speedup**: on
complex, familiar, expert work it can reduce productivity, and users systematically overestimate its
help. (2) **On realized labor-market outcomes (Tier-B/C admin, platform, and macro data): the average
and aggregate effect through 2025 is small-to-null and not yet clearly detectable**, replicating across
task-hours, worker-level payroll in three countries, occupational-mix tracking, and firm/industry job
postings — a pattern mechanistically explained by adoption still touching only ~1–8% of work hours and
by modest structural-macro ceilings. The two parts reconcile through the diffusion bridge: big per-task
gains × tiny share of hours = small realized macro effect *so far*.

The honest scope is critical: **"negligible" applies to the MEAN and the AGGREGATE, not the VARIANCE.**
Real, first-hand-measured moves exist within the distribution and within specific occupations — small
skill-biased wage divergence (experts up, bottom decile −3.9%), occupation-specific displacement
(freelance translation earnings −29.7%) alongside occupation-specific demand growth (web development),
and a contested but non-trivial relative decline for entry-level workers. The distributional sign is
**level-dependent**: equalizing for individual task output, polarizing for market earnings and
judgment-heavy work. Nothing here is predictive of a later, faster-diffusing, more capable model
generation — the task-level frontier is already moving (S24→S27), so today's realized nulls are best
read as a floor on a young technology, not a ceiling.

## Open gaps
1. **AI vs. interest-rate horse race.** S20 asserts the S6 youth decline is a monetary-tightening confound but runs no econometric decomposition separating AI exposure from interest-rate sensitivity. The single most important unresolved question in L4.
2. **A longitudinal deskilling / skill-atrophy study.** All quality-side evidence (S19, S25) is one-shot or self-report cross-sectional. No study measures actual skill change over months/years of AI use.
3. **Radiology / healthcare realized-labor outcomes.** Clinical accuracy/workload studies exist; a clean employment/wage first-hand study for the occupations most loudly predicted to be automated does not.
4. **Women's realized outcomes by gender.** S7 flags women as most exposed; no realized-outcome (employment/wage) study by gender yet exists.
5. **A US causal worker-level wage study.** The credible causal wage estimate (S21) is German admin data; no comparable US individual-level causal wage study confirms whether AI-tool *use* raises a worker's pay.
6. **A clean firm-level job-CREATION study.** S23 (web dev) and S26 (postings not falling) hint at creation/reallocation; a study isolating AI-driven new-task/new-job creation is missing.
7. **Later-vintage & agentic-AI outcomes.** All realized-outcome studies observe 2023–2024 (pre-agentic) tools. Whether reasoning/agentic models (whose task-quality effect is already larger — S27) change the realized macro picture is untested.
8. **Endogeneity of firm-level adoption.** The firm/industry null (S26) cannot rule out that fast-growing firms both adopt AI and hire — a positive selection that could mask displacement.
