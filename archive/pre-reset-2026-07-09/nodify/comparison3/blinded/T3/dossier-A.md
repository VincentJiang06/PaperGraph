# Investigation: 净效应判断必须分层:2020-2025 的 AI(生成式AI/agents)在'任务级替代'已广泛发生但多为增强、窄自动化;'岗位级净增减'到2025年在总量数据中尚不可归因于AI;而'温和数据=中性 vs 滞后'这一因果二选一,以现有识别手段无法干净区分——只能给出分层、附条件的校准判断。

## Lines of inquiry

### L1 [orientation: neutral]
  - statement: 任务层面:2020-2025 生成式AI/agents 的暴露面很广(多数职业有部分任务可被影响),但已实现的多是任务级增强而非整岗自动化,真正被端到端替代的任务窄。
  - conclusion: [supports/high] 任务级替代确已广泛发生但主要是增强:暴露面覆盖约80%劳动力的部分任务(≥50%任务受影响者仅约19%,含工具则47-56%),而真实使用侧以增强(~57%)压过自动化、集中于编程/写作;端到端整任务替代仍窄。
  - evidence:
      - GPTs are GPTs (Eloundou et al.) — https://arxiv.org/abs/2303.10130 — "around 80% of the U.S. workforce could have at least 10% of their work tasks affected by the introduction of LLMs"
      - Anthropic Economic Index (Claude 3.7) — https://www.anthropic.com/news/anthropic-economic-index-insights-from-claude-sonnet-3-7 — "augmentation still comprising 57% of usage"

### L2 [orientation: neutral]
  - statement: 岗位层面:到2025年,总量与多数行业就业数据未显示可稳健归因于AI的净岗位减少;但特定人群(入门级/年轻、AI高暴露职业)出现边际弱化的早期信号。
  - conclusion: [supports/medium] 岗位级净增减:至2025年总量与行业结构层面无可稳健归因于AI的净减少(Yale);但ADP微观显示22-25岁高暴露(自动化型)职业相对就业下降约16%,构成总量掩盖下的早期人群信号。二者并存。
  - evidence:
      - Yale Budget Lab (Gimbel et al.) — https://budgetlab.yale.edu/research/evaluating-impact-ai-labor-market-current-state-affairs — "measures of exposure, automation, and augmentation show no sign of being related to changes in employment or unemployment to date"
      - Canaries in the Coal Mine (Stanford) — https://digitaleconomy.stanford.edu/publications/canaries-in-the-coal-mine/ — "early-career workers (ages 22-25) in the most AI-exposed occupations have experienced a 16 percent relative decline in employment"

### L3 [orientation: neutral]
  - statement: 因果识别难题:以现有数据与方法,'AI净效应本就近中性'与'效应滞后尚未显现'两假设在总量温和数据上观测等价,无法干净区分。
  - conclusion: [open/medium] 因果识别裁决:假设A(近中性,〔另一分支〕/(记录)/0006)与假设B(滞后,〔另一分支〕/(记录)/0003)各具真实机制,且在2020-25温和总量数据上观测等价;叠加强混杂(〔另一分支〕:窗口短、混杂主导),现有识别手段无法干净区分二者。诚实结论=数据欠定(underdetermined),不能据总量温和径直断言中性。
  - evidence:
      - Yale Budget Lab — https://budgetlab.yale.edu/research/evaluating-impact-ai-labor-market-current-state-affairs — "33 months is a short window relative to prior technological transitions"
  ### L3.1 [orientation: neutral]
    - statement: 假设A(近中性):替代被互补、生产率增益与新任务/岗位再创造抵消,净效应本就接近中性——宏观测算显示AI对全要素生产率与就业的净影响温和。
    - conclusion: [supports/medium] 假设A(近中性)机制真实:自底向上宏观测算AI十年TFP增幅≤0.66%(温和),任务级证据显示AI多为增强(客服+14%、新手+34%),互补/生产率/再创造可抵消替代——'温和数据=真中性'有据;但机制成立≠已证净中性。
    - evidence:
      - Acemoglu — Simple Macroeconomics of AI — https://www.nber.org/papers/w32487 — "no more than a 0.66% increase in total factor productivity (TFP) over 10 years"
      - Generative AI at Work (Brynjolfsson/Li/Raymond) — https://www.nber.org/papers/w31161 — "increases productivity, as measured by issues resolved per hour, by 14% on average, including a 34% improvement for novice and low-skilled workers"
  ### L3.2 [orientation: adversarial]
    - statement: 假设B(滞后):效应真实但被延迟——采用/扩散的J曲线、通用技术的组织重构滞后、以及人群/职业层信号被总量掩盖——'尚未显现'而非'不存在'。
    - conclusion: [supports/medium] 假设B(滞后)机制同样真实:通用技术需无形/组织互补投资,早期系统性低估(J曲线);且人群/职业层信号(入门级下降 vs 资深稳增)先于总量出现——'尚未显现'而非'不存在'有据。与假设A在现有总量数据上观测等价。
    - evidence:
      - Productivity J-Curve (Brynjolfsson/Rock/Syverson) — https://www.nber.org/papers/w25148 — "leads to an underestimation of productivity growth in the early years of a new GPT"
      - Canaries in the Coal Mine (Stanford) — https://digitaleconomy.stanford.edu/publications/canaries-in-the-coal-mine/ — "employment for workers in less exposed fields and more experienced workers in the same occupations has remained stable or continued to grow"
  ### L3.3 [orientation: neutral]
    - statement: 混杂因素:2020-2025 就业受疫情冲击与复苏、2022-23 加息、科技业过度招聘的回吐等强噪声主导,AI 的边际信号在总量数据中难以被因果识别出来。
    - conclusion: [supports/medium] 混杂:2020-25就业被疫情冲击/复苏、2022-23加息、科技业过度招聘回吐等强噪声主导;窗口仅~33个月、毕业生信号样本小且'可能早于ChatGPT'——即便有AI效应也难在总量中被因果分离。这是识别失败的核心腿。
    - evidence:
      - Yale Budget Lab (short window) — https://budgetlab.yale.edu/research/evaluating-impact-ai-labor-market-current-state-affairs — "33 months is a short window relative to prior technological transitions"
      - Yale Budget Lab (confound) — https://budgetlab.yale.edu/research/evaluating-impact-ai-labor-market-current-state-affairs — "may also predate ChatGPT"

### L4 [orientation: adversarial]
  - statement: 红队(能力怀疑派):AI agents 在真实岗位上仍不可靠、规模部署迟、历次自动化预言多落空——大的净岗位替代可能被高估,甚至永不到来。
  - conclusion: [mixed/medium] 红队(能力怀疑)部分成立:至2025年agents在长程/多步真实任务上仍不可靠(SWE-bench 70%+的模型长程掉到~23%),企业采用仅~10%——能力与部署双双限制'已实现'替代,故大规模整岗替代在2020-25被高估;但可靠时程在快速外推,'永不到来'的强命题不被支持。
  - evidence:
      - Agent reliability bundle (METR/SWE-Bench Pro) — https://ai2027-tracker.com/predictions/long-horizon-struggle/ — "agents in Mid 2025 are 'impressive in theory but in practice unreliable.'"
      - SWE-Bench Pro long-horizon — https://ai2027-tracker.com/predictions/long-horizon-struggle/ — "models scoring 70%+ on standard SWE-bench drop to ~23% on long-horizon tasks involving multi-file refactors and cross-repository changes"
      - Census BTOS adoption — https://www.census.gov/library/stories/2026/05/ai-use-businesses.html — "crept up from 4.6 percent at the beginning of 2024 to 10 percent in September 2025"

### L5 [orientation: neutral]
  - statement: 扩散/时序:具备自主执行力的 agents 直到 2024-2025 才成熟并开始规模部署,'暴露≠已实现替代'——这为'太早/滞后'解读提供了机制性先验。
  - conclusion: [supports/high] 扩散/时序:具自主执行力的agents与企业规模采用直到2024-25才起步(生产用AI 2023/9仅3.7%→2025/9约10%;可靠时程仅~50分钟),而任务暴露潜力达47-56%——'暴露≠已实现',给'太早/滞后'解读强机制先验。
  - evidence:
      - Census BTOS adoption — https://www.census.gov/library/stories/2026/05/ai-use-businesses.html — "the number of businesses using AI rose from 3.7% in September 2023 to 5.4% in February 2024"
      - GPTs are GPTs (exposure ceiling) — https://arxiv.org/abs/2303.10130 — "this share increases to between 47 and 56% of all tasks"
      - METR time horizon — https://ai2027-tracker.com/predictions/long-horizon-struggle/ — "50% success horizon for frontier models at ~50 minutes on human expert tasks"

### L6 [orientation: adversarial]
  - statement: 红队(替代加速派):净岗位流失其实已比总量数据承认的更快到来——AI 归因的裁员、招聘冻结、入门级岗位收缩——'温和总量=无事'的读法本身被总量口径掩盖。
  - conclusion: [mixed/medium] 红队(替代加速)只在局部命中:AI归因裁员真实且上升(2025年54,836起)、自动化型/入门级职业确已下降——总量口径确会掩盖局部替代;但AI裁员相对总churn微小、非首要原因,总量'温和'并非纯口径假象。强形式(净流失已大规模到来)不成立。
  - evidence:
      - Challenger 2025 Year-End — https://www.challengergray.com/blog/2025-year-end-challenger-report-highest-q4-layoffs-since-2008-lowest-ytd-hiring-since-2010/ — "So far this year, AI has been responsible for 54,836 announced layoff plans."
      - Canaries in the Coal Mine (Stanford) — https://digitaleconomy.stanford.edu/publications/canaries-in-the-coal-mine/ — "employment declines are concentrated in occupations where AI is more likely to automate, rather than augment, human labor."

## Root conclusion

[mixed/medium] 分层校准判断。任务层:AI在2020-25已产生广泛任务级影响,但已实现以增强为主、端到端整任务替代窄(〔另一分支〕,高置信)。岗位层:总量无可归因于AI的净减少,但入门级/高暴露(自动化型)职业出现真实早期人群下降信号(〔另一分支〕,中置信)。识别:'本就中性'与'滞后未显现'两假设机制皆真、在温和总量上观测等价且被强混杂淹没,现有手段无法干净区分——数据欠定,不能据总量温和径直判为中性(〔另一分支〕)。权衡:采用与可靠能力直到2024-25才起步(〔另一分支〕)使'太早/滞后'成为更强的默认解释;'替代加速'强形式不成立、仅局部命中(〔另一分支〕);'能力永缺→永不到来'亦不被支持(〔另一分支〕)。净判断:2020-25的净岗位效应很可能确实接近中性至轻微负,但这更像'尚早'的产物而非已证的长期中性;方向性证据(入门级信号、采用曲线、可靠时程外推)整体偏向'效应真实、正待显现'而非'内在中性'。置信度:任务层高;岗位层总量中;'中性vs滞后'之分低。

## Open gaps

  - 何种识别策略能把AI边际从疫情/加息/科技回吐中干净剥离(暴露×采用双差、IV、职业层高频面板)?
  - 入门级人群信号会随时间上移到资深与更多职业(滞后兑现),还是稳定/回撤(一次性重置)?
  - agent可靠时程跨过整工作日阈值后,采用与替代是否非线性加速,把滞后效应集中释放?
  - 增强带来的生产率是否通过产出扩张/新任务再创造把净就业拉回正(reinstatement)?
  - 雇主'AI归因'裁员口径的可信度——真实驱动还是重组说辞?
  - 2026+总量数据延长窗口后,是否开始显现Yale所述尚未出现的滞后效应?
