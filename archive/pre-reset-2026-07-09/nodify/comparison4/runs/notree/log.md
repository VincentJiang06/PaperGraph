# Investigation log — AI/automation & labor markets, 2020–2025 evidence map

## BIG QUESTION
Systematic evidence map of 2020–2025 **first-hand empirical** studies on AI/automation's
effect on labor markets. Catalogue every important study (design: RCT / quasi-exp /
observational; sample; effect size + direction; key limits). Identify agreements &
disagreements; **stratify by methodological quality**; give weighted per-facet syntheses
(task-level substitution/augmentation; job-level net gain/loss; wages; special populations
esp. youth/entry-level; cross-national differences); and list open questions.

## METHOD (self, no subagents — WORKER BUDGET 0)
Wide, hypothesis-first, red-team every facet, ground every claim in a VERBATIM quote saved
to `sources/S<n>.txt`. Do NOT converge until the FINAL phase. Multi-phase run under forced
compaction: **this log.md is the ONLY memory** carried between phases. Keep it a working
memory (not a transcript), but complete enough that a fresh agent could continue from it alone.

## EVIDENCE-QUALITY LADDER (for stratification)
- Tier A: pre-registered RCT / field experiment (causal, but usually TASK-level & short).
- Tier B: quasi-experiment on real outcomes (DiD, IV) — administrative payroll/earnings/platform data.
- Tier C: observational / correlational (exposure↔outcome, event-study, occupational-mix tracking).
- Tier D: exposure-potential / usage indices & structural models (capability ≠ adoption ≠ impact).
KEY CAVEAT threading everything: **task-level gains (A) ≠ job-level/wage outcomes (B/C) ≠
exposure/usage potential (D).** Never let a Tier-D "80% exposed" headline stand next to a
Tier-B null as if commensurable. New this phase: adoption/usage share (S11,S12) is the
bridge that explains WHY big task-RCT gains (A) have not yet moved macro aggregates (B/C).

## LINES OF INQUIRY (orientation in brackets)
- **L1 [neutral] Task-level: substitution vs augmentation.** RCTs on productivity/quality.
  For: S1 (support +15%), S2 (writing −40% time), S3 (consulting), S9 (coding +55.8%),
  **S24 (legal: big SPEED gains, quality slight), S27 (legal w/ reasoning/RAG: +50–130%,
  quality now significant too).** AGAINST/texture: S3 jagged frontier (−19pp off-frontier);
  **S15 METR RCT: experienced devs 19% SLOWER**; S16 uneven; **S25 (overreliance: trust→less
  scrutiny).** NEW SYNTHESIS: S24→S27 shows the QUALITY effect is MODEL-VINTAGE dependent —
  GPT-4 gave speed-not-quality; reasoning models add quality. So "AI only speeds, doesn't
  improve quality" (a 2023–24 read) is already partly obsolete. Red-team: toy tasks overstate
  real-workflow gains? — S15 (real repos, SLOWER) is the concrete confirmation that it can.
- **L2 [neutral] Job-level net employment / demand.** S4 (robots, historical benchmark),
  S6 (entry-level payroll decline), S5 (Denmark null), **S10 (freelancer demand −2% contracts)**,
  **S13 (Yale: no aggregate disruption in 33 months)**, **S23 (translation demand DOWN vs web-dev
  demand UP — occupation-specific)**, **S17 (PwC: jobs still growing in AI-exposed occ — Tier-D).**
  Red-team (adversarial texture): can any isolate AI from macro (rate hikes, 2022 tech over-hiring
  correction, remote-work unwind)? **S20 (EIG) is the explicit adversarial answer: NO — the exposed-
  occupation hiring drop tracks the 2022 Fed tightening, not AI.**
- **L3 [neutral] Wages / earnings / hours.** S4 (robot wage drop), S5 (null on earnings),
  S6 (adjust via employment not pay), **S10 (freelancer earnings −5%)**, **S14 (Acemoglu:
  ≤0.66% TFP/10yr ceiling)** vs **S18 (Aghion 0.68pp — bigger)**, S11 (only 1–8% of hours AI-assisted).
  DIRECT wage evidence now added: **S21 (German admin, worker-level: experts +0.65%/+€403, non-experts
  −0.3%, bottom decile −3.9%)**, **S17 (PwC 56% AI-skill wage premium — but Tier-D/selection)**,
  **S23 (translation earnings −29.7%)**. Red-team: PwC premium is selection not causal; S21's admin IV
  is the credible causal wage estimate and it's SMALL + heterogeneous.
- **L4 [neutral] Special populations — youth / entry-level.** S6 (22–25 yo −13–16% relative).
  CENTRAL TENSION with L1 (RCTs show novices gain most). Reconciler: **S13** (aggregate flat can coexist
  with concentrated youth effect). **ADVERSARIAL LINE (NEW): S20 (EIG) disputes the AI-attribution
  entirely** — the youth drop predates ChatGPT by ~6mo, aligns with 2022 rate hikes, and is partly a
  mechanical "aging illusion" from a narrow 22–25 band under a hiring freeze; "no evidence junior
  postings fell more than senior." So L4's causal story is now CONTESTED, not settled.
- **L5 [neutral] Cross-national / development-level.** S7 (ILO index: rich>poor exposure),
  S5 (Denmark), **S16 (Kenya field RCT — developing-economy first-hand)**, S10 (global platform),
  **S21 (Germany — worker-level admin, second non-Denmark realized-outcome study).** Red-team: exposure
  in LICs blocked by digital divide → "low exposure" may mislead. Germany + Denmark both show SMALL/NULL
  average with heterogeneity → the "small realized effect in rich admin data" pattern replicates.
- **L6 [ADVERSARIAL — spine of the skeptic case] "GenAI's realized labor-market effect is
  negligible / not yet detectable."** STRENGTHENED: S5 (precise nulls) + **S13 (Yale aggregate null,
  33mo)** + **S14 (modest macro ceiling)** + S11 (tiny share of hours) + **S21 (German admin: no avg
  effect)** + **S26 (Fed: AI-adopting FIRMS not posting fewer jobs — a 4th aggregation level: the firm)**
  + **S20 (the flagship scary stat — S6 youth — may be a monetary-policy confound).**
  Counter-evidence keeping it honest: S6 (canaries), S10 (freelancer demand drop), S23 (translation
  −29.7%), S17 (PwC: real wage/job GROWTH in exposed occ — cuts the OTHER way too). NUANCE: L6 is
  strong for the AGGREGATE and AVERAGE, but S18 (Aghion, bigger macro) + S21 (real within-distribution
  moves) mean "negligible" ≠ "no distributional effect." Must stay alive. Its own red-team: aggregate
  nulls MASK subgroup harm (S6/S21 bottom-decile −3.9%).
- **L7 [neutral] Distributional sign: does AI EQUALIZE or POLARIZE?** Split, and POLARIZE side
  STRENGTHENED this phase. EQUALIZE: S1/S2/S3 (low-skill/novice gain most), **S19 (individual novelty:
  low-skill writers gain most)**. POLARIZE/uneven: **S16 (high +20%/low −10%)**, **S10 (TOP freelancers
  hit worst)**, **S21 (German admin: experts/top-decile GAIN, non-experts/bottom-decile LOSE — "casts
  doubt on AI as leveler")**, **S23 (translators down / web-devs up)**, **S19 (collective HOMOGENIZATION
  even as individuals improve).** Working hypothesis (refined): equalizing for bounded EXECUTION tasks
  at the INDIVIDUAL-OUTPUT level; polarizing at the MARKET/EARNINGS level and for JUDGMENT/expertise
  tasks. The equalize-vs-polarize answer depends on (a) LEVEL (individual output vs market earnings vs
  collective diversity) and (b) whether AI substitutes the top's differentiator. HIGH-VALUE thread.

## STUDY CATALOGUE. Full quotes in sources/S<n>.txt.
| ID | Study (yr) | Tier | Facet/Line | Design/Sample | Effect + direction |
|----|-----------|------|-------|---------------|--------------------|
| S1 | Brynjolfsson, Li, Raymond — Generative AI at Work (2023/QJE25) | A | L1,L4,L7 | Staggered rollout, 5,172 support agents | +15% issues/hr; novices/low-skill gain most, top ~0. AUGMENT, equalizing |
| S2 | Noy & Zhang — Science (2023) | A | L1,L7 | RCT, 453 pros, writing | time −40%, quality +18%; compresses inequality. AUGMENT/equalize |
| S3 | Dell'Acqua et al. — Jagged Frontier (2023) | A | L1,L7 | Pre-reg RCT, 758 BCG consultants, 3 arms | Inside frontier +12.2% tasks, 25% faster, low-skill +43% vs high +17%. OUTSIDE: −19pp correct. AUGMENT w/ jagged caveat |
| S4 | Acemoglu & Restrepo — Robots and Jobs (JPE 2020) | C | L2,L3 | Commuting-zone IV, robots 1990–2007 | +1 robot/1k workers → emp/pop −0.18–0.34pp, wages −0.25–0.5%. NEGATIVE (robots≠AI; historical benchmark) |
| S5 | Humlum & Vestergaard — Small Labor Market Effects (2025) | B | L2,L3,L5,L6 | DiD, ~25k workers/7k workplaces, 11 occ, Denmark | PRECISE NULL earnings & hours (rules out >2%); ~3% time savings. NO macro effect |
| S6 | Brynjolfsson, Chandar, Chen — Canaries in the Coal Mine (2025) | B/C | L2,L4 | Event-study, ADP payroll microdata, since late-2022 | Ages 22–25 in most AI-exposed occ: ~13–16% RELATIVE emp decline; automate-type occ; older stable; adjusts via employment not pay. NEGATIVE entry-level |
| S7 | Gmyrek, Winkler et al. — ILO Refined Global Index (WP140, 2025) | D | L5 | Exposure index, 6-digit occ, ~30k tasks, global | 1 in 4 some exposure; 3.3% highest cat; women 4.7% vs men 2.4%; HIC 34% vs LIC 11%. EXPOSURE potential |
| S8 | Eloundou et al. — GPTs are GPTs (Science 2024) | D | L1,L5 | Task-exposure rubric, US O*NET | ~80% ≥10% tasks affected; ~19% ≥50%; higher-income MORE exposed. EXPOSURE potential |
| S9 | Peng et al. — GitHub Copilot RCT (2023) | A | L1 | RCT, recruited devs, HTTP-server-in-JS task | Treatment 55.8% FASTER. AUGMENT (coding), speed-only, greenfield toy task |
| **S10** | **Hui, Reshef, Zhou — Short-Term Effects, Online Labor Market (2023/OrgSci24)** | **B** | **L2,L3,L7** | **DiD, Upwork freelancers, ChatGPT/DALL-E2/Midjourney launches** | **Exposed: −2% contracts, −5% earnings; TOP performers hit WORST. NEGATIVE demand** |
| **S11** | **Bick, Blandin, Deming — Rapid Adoption of GenAI (NBER w32966, 2024)** | **C/D** | **adoption/L6** | **Nationally-rep survey (RPS), US 18–64, late 2024** | **~32–40% use; ~23–24% at work weekly; 1–8% of hours assisted; adoption faster than PC. Realized productivity SMALL** |
| **S12** | **Anthropic Economic Index (2025–26)** | **D** | **L1** | **Millions of Claude.ai+API convos → O*NET tasks** | **Augmentation ~52–57% vs automation ~43–45% (API 77% automate); concentrated coding/math. USAGE proxy** |
| **S13** | **Yale Budget Lab — Impact of AI on Labor Market (CPS series, 2025–26)** | **C** | **L2,L4,L6** | **Occ-mix dissimilarity vs historical + emp/unemp by AI-exposure quintile, CPS, 33mo** | **NO discernible aggregate disruption; exposure NOT related to emp/unemp changes. NULL (reconciles S5/S6)** |
| **S14** | **Acemoglu — Simple Macroeconomics of AI (NBER w32487, 2024)** | **D/model** | **L2,L3,L6** | **Task-based model + Hulten's theorem (uses S8 exposure)** | **≤0.66% TFP over 10yr (rev <0.53%). MODEST macro ceiling — context, not first-hand** |
| **S15** | **METR — Early-2025 AI & Experienced OSS Devs (arXiv 2507.09089, 2025)** | **A** | **L1** | **RCT, 16 expert devs, 246 real tasks on OWN mature repos; Cursor+Claude 3.5/3.7** | **AI-allowed 19% SLOWER; devs believed +20%. NEGATIVE — contradicts S9** |
| **S16** | **Otis, Clarke, Delecourt, Holtz, Koning — Uneven Impact, Kenya (HBS WP 2023 rev25)** | **A** | **L5,L7** | **Field RCT, 640 Kenyan entrepreneurs, GPT-4 mentor via WhatsApp** | **~0 average; HIGH performers +~20%, LOW performers −~10%. POLARIZING** |
| **S17** | **PwC — Global AI Jobs Barometer 2025** | **D** | **L2,L3,L6** | **~1bn job ads + firm financials, industries by AI-exposure (Felten)** | **AI-skill wage premium 56% (was 25%); wages 2x faster & jobs still growing in AI-exposed occ. POSITIVE but correlational/vendor** |
| **S18** | **Aghion & Bunel — AI and Growth: Where Do We Stand? (FRBSF 2024)** | **D/model** | **L2,L3,L6** | **Task-based model (same as Acemoglu) + historical-analogy, own lit reading** | **~0.68pp/yr extra TFP (range 0.07–1.24; approach-1 0.8–1.3) vs Acemoglu 0.07pp. COUNTER-view: bigger macro upside** |
| **S19** | **Doshi & Hauser — Individual creativity up, collective diversity down (Sci Adv 2024)** | **A** | **L1,L7,quality** | **RCT, 293 writers ×3 arms + 600 evaluators, short-story task** | **Novelty +8.1% (low-skill +10.7%) BUT stories more similar (cosine ↑). EQUALIZES individual / HOMOGENIZES collective** |
| **S20** | **Iscenko & Curto Millet (EIG) — Looking for the Ladder (2026)** | **C** | **L4,L6** | **Re-analysis of Lightcast postings + employment; timing/confound rebuttal of S6** | **DISPUTES S6 AI-attribution: youth decline predates ChatGPT 6mo; = monetary-tightening + 'aging illusion'. ADVERSARIAL to S6** |
| **S21** | **Storm, Gonschor, Schmidt — AI in Demand (Ruhr EP 1185 / IHS, 2025)** | **B** | **L3,L5,L7** | **German OJV linked to worker-level ADMIN records 2017–23, shift-share IV** | **NO avg effect; experts +0.65% (+€403), non-experts −0.3%; bottom decile −3.9% earn / −8 days, top +2.5%. POLARIZE; 'casts doubt on AI as leveler'** |
| **S22** | **Society of Authors (UK) — AI Survey 2024** | **D** | **L4-spec,L2,L3** | **Member survey, 787 resp / 12,500 members, Jan 2024** | **36% translators & 26% illustrators already lost work to GenAI; 43%/37% income devalued. Self-report NEGATIVE (creative occ)** |
| **S23** | **Qiao, Rui, Xiong — AI and Freelancers: Inflection Point? (HICSS 2025)** | **B** | **L2,L3,L7,spec** | **DiD on OLM transactions around ChatGPT; translation (7.6k) & web-dev (15k) vs construction control** | **Translation DISPLACED (earn −29.7%); web-dev PRODUCTIVITY (work & earn UP). OCCUPATION-specific opposite signs** |
| **S24** | **Choi, Monahan & Schwarcz — Lawyering in the Age of AI (Minnesota LR, 2024/25)** | **A** | **L1,L4,L7,spec-legal** | **RCT, law students, realistic legal tasks w/ or w/o GPT-4; time + blind grading** | **Large consistent SPEED gains; quality gains "slight and inconsistent," concentrated in LOWEST-skilled → "equalizing." AUGMENT (legal)** |
| **S25** | **Lee, Sarkar, Tankelevitch et al. (Microsoft/CMU) — GenAI & Critical Thinking (CHI 2025)** | **D** | **quality/L1,L6** | **Survey, 319 knowledge workers, 936 real GenAI work examples** | **Self-report: LESS cognitive effort; trust in AI → LESS critical scrutiny (overreliance). Deskilling PROXY (self-report, not longitudinal)** |
| **S26** | **Fed (FEDS Notes) — AI Adoption & Firms' Job-Posting Behavior (2026)** | **C** | **L2,L6** | **Firm/industry AI adoption↔subsequent job postings; +Census BTOS firm survey (D)** | **NO evidence AI-adopting firms/industries post FEWER jobs (coeffs if anything +). Firm-level NULL. Masks occ-specific** |
| **S27** | **Schwarcz, Manning, Prescott et al. — AI-Powered Lawyering (2026)** | **A** | **L1,L4,L7,spec-legal** | **RCT, law students, RAG (Vincent AI) vs reasoning model (o1-preview) vs none** | **Reasoning/RAG SIGNIFICANTLY raise legal QUALITY (contra GPT-4) +50–130% productivity. Quality effect is MODEL-VINTAGE dependent** |

## FINDINGS SO FAR (tentative — NOT converged)
- **F1 (L1 — REVISED, now CONTESTED):** Tier-A RCTs show GenAI **augments/speeds bounded
  knowledge tasks** for NOVICES/greenfield work (S1 +15%, S2 −40% time, S9 +55.8%, S3 inside
  frontier). BUT this is NOT a universal speedup: **S15 (RCT) shows experienced devs 19%
  SLOWER** on complex familiar repos. The gain is conditional on task simplicity + user
  inexperience. "Augment" ≠ "always faster/better."
- **F2 (L1 caveat — reinforced):** S3 jagged frontier + S15 slowdown = augmentation is UNEVEN
  and carries overreliance/mis-estimation risk (S15: 39pp gap between perceived and actual).
- **F3 (L2/L4 — the CENTRAL DISAGREEMENT, RECONCILER + now a CONFOUND CHALLENGE):** Real-outcome
  studies split: S5 (Denmark null) & **S13 (Yale aggregate null)** & **S21 (Germany, no avg effect)**
  vs S6 (US ADP youth −13–16%) & S10/S23 (freelancer demand down). RECONCILER (S13): aggregate flat +
  concentrated subgroup can co-exist. NEW CHALLENGE (S20/EIG): the S6 subgroup effect may not be AI at
  all — its timing predates ChatGPT and matches 2022 monetary tightening; "AI exposure" ≈ "interest-rate
  sensitivity." So F3 now has THREE readings: (a) level-of-aggregation reconciler, (b) genuine AI
  subgroup harm, (c) macro-confound artifact. Unresolved — but (c) is now a live, documented rival.
- **F4 (L4 — sharpest mechanism, now CONTESTED):** RCTs say novices gain most (F1) yet S6 says the
  youngest LOSE jobs. Hypothesis still testable: AI augments the novice WORKER but substitutes the
  entry-level TASKS/ROLE → fewer junior hires. BUT **S20 (EIG) is the critique GAP-1 wanted**: it argues
  the pattern is a monetary-tightening hiring freeze + a mechanical "aging illusion" of a narrow 22–25
  band, with "no evidence junior postings fell more than senior." VERDICT SHIFT: S6 is no longer
  uncontested first-hand evidence of AI-caused entry-level loss; the AI attribution is disputed on
  timing/confound grounds. Still unreplicated on the AI side; EIG unreplicated on the confound side.
- **F5 (L5 — replicated pattern):** Exposure skewed to HIGH-income countries (S7: HIC 34% vs LIC 11%) &
  women/clerical — opposite of the male-manufacturing robot story (S4). Realized-outcome admin studies now
  in TWO rich economies — Denmark (S5) and **Germany (S21)** — BOTH show small/null AVERAGE with skill
  heterogeneity. Developing-economy first-hand: **S16 (Kenya)**, POLARIZING. So "rich-country admin data
  finds small realized effects (so far)" is a replicated, cross-national finding.
- **F6 (L6 adversarial — STRENGTHENED but SCOPED):** Aggregate/average skeptic line well-supported: S5 +
  **S13** + **S21** (three admin nulls-on-average: DK, US, DE), **S14** (macro ceiling), **S11** (1–8% of
  hours). And **S20** weakens the single biggest scary stat (S6). BUT the honest scope is "negligible on
  AGGREGATE & AVERAGE," NOT "no effect": S21 shows real within-distribution moves (bottom decile −3.9%),
  S23 real occupation displacement (−29.7%), S18 argues a bigger macro upside is plausible, S17 shows real
  positive wage/job growth in exposed occ. So the null is about the MEAN, not the VARIANCE.
- **F7 (L7 — POLARIZE side now the stronger read):** DISTRIBUTIONAL sign is UNSETTLED but the polarizing
  evidence has grown. Equalizing at INDIVIDUAL-OUTPUT level: S1/S2/S3, S19 (low-skill writers gain most).
  Polarizing at MARKET/EARNINGS level: S16, S10, **S21 (experts/top-decile gain, non-experts/bottom-decile
  lose; explicitly "casts doubt on AI as leveler")**, **S23 (occupation-specific opposite signs)**, and
  even S19 (collective HOMOGENIZATION). KEY REFINEMENT: the equalize claim survives at the level of one
  worker's output quality; it FAILS at the level of market earnings/employment. "AI democratizes skill" is
  NOT safe as an economic (as opposed to task-output) statement.
- **F8 (adoption bridge):** Adoption is historically FAST (S11: faster than PC/internet) yet still touches
  only ~1–8% of work hours. Key mechanistic reconciler: huge per-task RCT gains × tiny share of hours =
  small realized macro effect (consistent S5/S13/S14/S21).
- **F9 (L3 WAGES — NEW, was the thinnest facet):** Direct GenAI wage evidence is now three-sided and
  DIVERGENT by tier. (a) Tier-B causal (S21, German admin IV): AVERAGE wage effect ~0, but experts +0.65%
  (+€403/yr) and non-experts −0.3%; bottom earnings-decile −3.9%. (b) Tier-D correlational (S17, PwC): a
  large +56% "AI-skill wage premium" and wages rising 2x faster in exposed industries — but this is
  selection/composition, not a causal return. (c) Occupation displacement (S23: translators −29.7% focal
  earnings). SYNTHESIS: the credible causal wage signal is SMALL and HETEROGENEOUS (skill-biased upward),
  not the headline 56%. Wage facet upgraded from THIN to "small-but-skill-polarizing (Tier-B)."
- **F10 (QUALITY / homogenization / overreliance — addresses GAP-6):** Beyond speed/employment, AI reshapes
  OUTPUT and the WORKER. S19 (Tier-A RCT): AI raises individual creativity/quality (esp. low-skill writers)
  but homogenizes outputs (individual-gain / collective-diversity-loss). **S25 (Microsoft/CMU survey, 319
  workers): trust in AI → LESS critical scrutiny; workers self-report reduced cognitive effort → an
  overreliance/deskilling channel** (pairs with S3 jagged frontier + S15 slowdown, where overreliance
  actively HARMS output). Quality story = "each piece a bit better, the whole more homogeneous, the worker
  less vigilant." A distinct externality not captured by wage/employment metrics. STILL under-studied
  longitudinally (S25 is self-report + cross-sectional — no true skill-atrophy-over-time measurement yet).
- **F11 (L1 legal + model-vintage — NEW):** The task-level QUALITY gain is not fixed; it tracks model
  capability. GPT-4 in law (S24) gave big SPEED but only "slight and inconsistent" QUALITY; reasoning
  models + RAG in law (S27) "significantly enhance legal work quality," +50–130% productivity — "a marked
  contrast" with GPT-4. Implication for the whole map: the many 2023–24 Tier-A RCTs (incl. the S15 slowdown)
  measured an EARLIER model generation; the augmentation frontier is moving, so today's null/small quality
  findings are a floor, not a ceiling. Caveat: still task-level, still toy tasks, still says nothing about
  whether firms translate the task gain into wages/jobs (the L1→L2/L3 gap that F8 explains).
- **F12 (L2 firm-level — NEW):** Adds a fourth level of aggregation to the L6 null. S26 (Fed): across firms
  and industries, higher AI adoption/investment is NOT associated with fewer job postings (coefficients if
  anything positive); Census BTOS: most firms use AI to augment, AI-related staffing cuts reported by ~2%.
  So the "no realized aggregate effect (yet)" finding now replicates at task-hours (S11), worker-admin
  (S5/S13/S21), and FIRM/industry-posting (S26) levels. Same load-bearing caveat: total postings mask
  occupation-specific pressure (S6/S10/S23), and adoption is endogenous.

## GRAVEYARD (killed / retired lines)
- **STILL UNSUPPORTED (candidate kill, keep watching):** "GenAI already caused AGGREGATE net job
  loss / mass unemployment (2025)." No Tier-A/B/C study supports an economy-wide net job loss; S13, S5,
  S21 affirmatively find NO aggregate/average disruption. Only relative/subgroup effects (S6, now
  confounded by S20) and sector-specific demand drops (S10/S23) exist. Retire unless overturned.
- **KILLED (was WOUNDED):** "AI uniformly EQUALIZES / democratizes skill." Phase-1 leaned this way (F1).
  Now DEAD as a general economic claim: S16, S10, and esp. **S21** (worker-level admin: experts gain /
  non-experts lose, "casts doubt on AI as a leveler") + S23 show it polarizes at the earnings/market
  level. It SURVIVES ONLY in a narrow sense — individual-output quality on bounded tasks (S1/S2/S19).
  Never state equalization as an economic finding; specify the level.
- **NEW — DEMOTED, not killed:** "The S6 entry-level youth decline is settled first-hand evidence of
  AI-caused job loss." **S20 (EIG)** provides a documented rival cause (2022 monetary tightening +
  narrow-cohort 'aging illusion'; decline predates ChatGPT ~6mo). Downgraded to CONTESTED. Keep both
  alive; needs a study that separates AI from interest-rate exposure to resolve.
- **NEW — WATCH (do not adopt):** "AI-skill wage premium proves AI causally raises wages" (from S17/PwC
  56%). This is a Tier-D selection/composition correlation; the Tier-B causal estimate (S21) is far
  smaller and heterogeneous. Do not cite the 56% as a causal wage effect.

## GAPS / TODO FOR NEXT PHASE (updated; ✔ = done, ~ = partial)
1. ✔✔ GAP-1 (critique of S6): DONE — **S20 (EIG)** is the direct AI-attribution rebuttal (monetary-policy
   confound + aging illusion). NOW OPEN: a study that ECONOMETRICALLY SEPARATES AI exposure from
   interest-rate sensitivity (S20 asserts correlation but doesn't run the horse-race). Is S6 replicated
   in another country's admin data with age detail?
2. ✔ GAP-2 (direct wage study): DONE — **S21 (German admin IV)** = credible causal wage estimate (small,
   skill-heterogeneous) + **S17 (PwC 56% premium, Tier-D)** for the correlational upper bound. Could still
   use a US causal wage/earnings study with individual data (does AI-tool USE causally raise a worker's pay?).
3. ✔ Adoption/diffusion — S11/S12 done. Optional: firm-level adoption→earnings link.
4. ~ Augment-vs-substitute field studies + NEGATIVE + job-CREATION: added **S23** (translation displaced /
   web-dev demand GROWS — a creation case). STILL WANT: radiology/medical, legal, a call-centre replication
   beyond S1, and a clean firm-level job-CREATION study.
5. ✔ Cross-national admin beyond Denmark: **S21 (Germany)** added. STILL WANT US admin-payroll with age
   detail to test the S6 pattern directly (and outside Anglosphere/EU).
6. ✔ Quality/homogenization: **S19 (Doshi-Hauser)** added (individual up / collective diversity down).
   STILL WANT a LONGITUDINAL deskilling/skill-atrophy study over months (S19 is one-shot).
7. ✔ Macro counter-view: **S18 (Aghion-Bunel, 0.68pp)** now catalogued opposite S14 (0.07pp) — macro
   question shown UNSETTLED within one framework.
8. Verify exact figures across drafts (unchanged): S6 (13%/16%), S1 (14%/15%), S12 (52%/57%), S11
   (32/24/11 vs 40/23/9). Also cross-check S17 PwC vintage (2025 "56%" vs 2026 barometer) and S23's
   Demirci-et-al "21% postings decline" secondhand cite (get Demirci primary if used).
9. ✔(legal) / ✗(radiology,women): LEGAL now covered — **S24 (GPT-4 RCT) + S27 (reasoning/RAG RCT)**.
   STILL OPEN: RADIOLOGY/healthcare first-hand LABOR study (clinical accuracy/workload studies exist —
   e.g. Swedish trial ~44% workload cut — but no clean employment/wage outcome; note radiologist
   employment kept GROWING despite 2016 "stop training radiologists" prediction). WOMEN's realized
   outcomes by gender still absent (S7 flags women most exposed; no realized-outcome study).
10. ✔ Firm-level: **S26 (Fed job-posting null + Census BTOS)** added — the firm/industry aggregation level.
11. ~ Deskilling/quality: **S25 (Microsoft/CMU critical-thinking survey)** added — overreliance channel,
    but self-report + cross-sectional. A TRUE longitudinal skill-atrophy study over months remains the
    single most under-served gap on the whole map.

## PHASE LOG
- **Phase 1:** created log + L1–L6 + evidence ladder; catalogued S1–S9 (4 Tier-A RCTs, 2 Tier-B,
  1 Tier-C, 2 Tier-D). Central tensions: F3 (null vs youth-decline), F4 (novice-augment vs
  entry-level job loss). No convergence.
- **Phase 2 (this):** added S10–S16 (7 new studies). NEW: S15 METR (Tier-A RCT, devs 19% SLOWER —
  first adversarial task-RCT), S16 Kenya (Tier-A field RCT, POLARIZING), S10 Upwork (Tier-B,
  real demand −5% earnings), S11 adoption + S12 Anthropic usage (bridge exposure→impact), S13
  Yale aggregate null, S14 Acemoglu macro ceiling. RESTRUCTURED log: added **L7 (distributional
  equalize-vs-polarize)** and findings **F7/F8**; revised F1 (equalizing now CONTESTED) and F3
  (added S13 reconciler); populated Graveyard (aggregate-mass-unemployment unsupported;
  equalization WOUNDED). L6 skeptic case materially strengthened but kept honest by S10/S6.
  NOT converged. Next phase priorities: GAP 1 (replicate/critique S6), GAP 2 (a direct wage
  study), GAP 4/6 (a NEGATIVE or job-creating field study + a deskilling/quality study),
  GAP 7 (Aghion counter-view to Acemoglu).
- **Phase 3 (this):** added S17–S23 (7 new studies), targeting the two thinnest facets — WAGES and
  SPECIFIC-GROUPS. WAGES: S21 (German admin IV — first credible CAUSAL worker-level wage estimate: small,
  experts +0.65%/+€403, non-experts −0.3%, bottom decile −3.9%), S17 (PwC Tier-D 56% AI-skill premium —
  correlational), S23 (translation earnings −29.7%). SPECIFIC-GROUPS: S20 (EIG rebuttal of S6 — the youth/
  entry-level AI story is now CONTESTED, credited to 2022 monetary tightening + aging illusion), S22 (SoA
  survey — translators/illustrators self-report work loss), S23 (occupation-specific: translators down /
  web-devs up). Plus S18 (Aghion macro counter to S14) and S19 (Doshi-Hauser homogenization → new F10).
  RESTRUCTURE: added findings F9 (wages) & F10 (quality/homogenization); revised F3–F7; L4 gained an
  ADVERSARIAL line (S20); L7 polarize-side strengthened. GRAVEYARD: KILLED "AI uniformly equalizes"
  (was wounded); DEMOTED S6-as-settled to CONTESTED; added WATCH on the PwC 56% causal misread. No
  convergence. Next-phase priorities: GAP-1b (AI-vs-interest-rate horse race), GAP-4/9 (radiology/legal/
  women realized outcomes; a firm-level job-creation study), GAP-6 (longitudinal deskilling).
- **Phase 4 (FINAL — this):** added S24–S27 (4 new studies) to close the thinnest gaps, then CONVERGED.
  S24 (Choi/Monahan/Schwarcz legal RCT — GPT-4: speed↑, quality slight, equalizing) + S27 (Schwarcz et al.
  legal RCT — reasoning/RAG: quality now significant, +50–130%) close the LEGAL gap and yield **F11
  (task-quality gain is MODEL-VINTAGE dependent — the 2023–24 RCTs are a floor, not a ceiling)**. S26 (Fed
  firm/industry job-posting NULL + Census BTOS) closes the FIRM-level gap → **F12 (the aggregate null now
  replicates at a 4th level: firms)**. S25 (Microsoft/CMU critical-thinking survey) adds the overreliance/
  deskilling channel to F10. RESTRUCTURE: added F11, F12; folded S25 into F10. Wrote `dossier.md` (the
  calibrated, methodological-quality-weighted synthesis). STILL-OPEN gaps carried to dossier: radiology/
  healthcare realized-labor study; women's realized outcomes by gender; a TRUE longitudinal deskilling
  study; the AI-vs-interest-rate econometric horse-race (S20's confound claim untested). CONVERGED.
