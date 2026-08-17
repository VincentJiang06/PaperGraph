# 人类证据方法学 → 机器可执行 gate（v2 外部调研）

调研日期：2026-08-17。所有数字均按"落笔即验证"规则处理：每个承载判断的数字都给出**口径三元组**（什么指标 / 在什么样本与条件下 / 与什么比较），并标注 `verified` / `corrected` / `unverified`。凡未能触达一手来源者，本文直接写"未核实"，不折算成裸数字。

---

## 结论摘要

1. **人类证据学早就解决了我们要解决的问题，而且解法不是"框架"，是"信号问题 → 确定性算法 → 可推翻判定"三层结构。** Cochrane RoB 2 的形态最值得直接抄：每个偏倚域下挂 2–7 个**近乎事实性**（"reasonably factual in nature"）的信号问题，答案只能是 Y/PY/PN/N/NI（+条件性 NA），然后由**写死的算法**把答案组合映射到 Low / Some concerns / High。算法只给"proposed judgement"，人可以推翻，但**推翻必须写理由**。这正是"artifact + 可重跑客观 gate"的成熟工业实践。

2. **最强的一手经验证据支持"分解到原子事实问题"这一条设计。** 同一篇 2025 年 JMIR 研究里，LLM 在 **信号问题层面**平均准确率 83.2%（95% CI 77.5–88.9），而聚合到**域层面**降到 65.2%（对比 Cochrane 判定）、整体 RoB 判定只有 57.5%–70%。另一项 2024 年 Research Synthesis Methods 研究显示：直接让 LLM 输出 RoB2 判定，F1 只有 0.1–0.2，与平凡基线无异。结论极其明确：**让模型答事实问题，让代码做聚合判定。**

3. **"可重跑"必须成为一等公民，因为模型连自己都对不齐。** Cochrane Evidence Synthesis and Methods 2025 的研究测了 ChatGPT-4o 的**自身重测一致率**（intrarater）只有 74.7%（95% CI 64.8–84.6）；Elicit 的同行评审可行性研究显示换账号重跑，**取值**一致率 90%，但**支撑引文**只有 46%、**推理**只有 30%；开启 high-accuracy 模式后变成 77% / 10% / 0%。→ 我们的 claim 状态必须绑定"证据指针（引文/数据脚本）"而不是"模型当次的解释"，且必须存重跑种子与快照。

4. **IPCC 的校准语言有一条可以直接搬的硬规则**：只有当**置信度为 "high" 或 "very high"** 时，才允许给出定量的 likelihood（概率区间）；证据有限且共识低时，**连 confidence 都不许给**，只能给 evidence/agreement 的定性摘要词。翻译成我们的状态机：**没有到 verified 档，就禁止输出量化断言**——这条比任何"提示词让模型别瞎说"都有效，因为它是类型系统级的禁止。

5. **今天真正可自动化的部分是有边界的，而且边界已被测出来。** BMJ EBM 2026 的 URSE 半自动 GRADE 工具在 115 篇 Cochrane 综述上：**imprecision（按参与者数）准确率 0.97 / F1 0.94**、**I²（异质性）0.90 / 0.90**、**AMSTAR 方法学质量 0.98 / 0.99**，但 **risk of bias 只有 0.73 / 0.70**，整体 GRADE 等级一致率 **63.2%、Cohen's κ = 0.44**。即：**能算的（数、区间、统计量）几乎全自动；要判断的（偏倚、间接性）不行。**

6. **GRADE 官方自己的路线也是"决策规则 + 人类监督"，不是"让 LLM 打分"。** GRADE Working Group 正在开发官方工具 GRADErater，七条原则里明确包含 transparency、human oversight、**implementation of decision rules**、continuous improvement（JCE 2026）。Cochrane / Campbell / JBI / CEE 四家 2025 年 11 月的联合立场声明进一步规定：**任何"做出或建议判断"的 AI 使用都必须完整透明地申报**（系统名与版本、用途、含验证证据的理由、利益冲突、局限），且作者对结论负最终责任。

7. **最重要的方法学教训（也是本轮的元教训）**：本次调研当场抓到两个"数字洗白"实例。(a) `ottosr.com` 首页称 otto-SR "Peer-reviewed in the Annals of Internal Medicine" 并链到 DOI `10.7326/ANNALS-24-02189`——**该 DOI 指向的是同团队另一篇论文**（提示词模板研究），otto-SR 本体截至 2026-08-17 在 Europe PMC 仅有 medRxiv 预印本记录，无期刊记录。(b) 第三方工具 RCT-Reviewer 在其文档页宣称"Achieves 71.0% accuracy … within 8% of expert consensus"——这是 **RobotReviewer 2015 年 JAMIA 论文**在旧版 RoB1 二分标签下对 CDSR 的数字，被原样搬来当作该工具自身的性能声明。**这两个都是"多个二手页面重复同一上游源 = 一个源"的典型形态。**

---

## 系统与机制逐条（含 URL）

### A. GRADE：确定性分级

- **四档确定性**：high / moderate / low / very low。定义（GRADE Handbook 表 5.1，一手）：high = "We are very confident that the true effect lies close to that of the estimate of the effect."；moderate = "…there is a possibility that it is substantially different"；low = "Our confidence in the effect estimate is limited…"；very low = "We have very little confidence…"。
  - https://gdt.gradepro.org/app/handbook/handbook.html
- **5 个降级域 + 3 个升级域**（Cochrane Handbook 第 14 章，一手）：降级 = risk of bias / inconsistency（未解释的异质性）/ indirectness / imprecision / publication bias；升级 = large effect / dose-response gradient / plausible confounding working against the observed effect。
  - https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-14
- **inconsistency 域的判据是四条并列信号，不是单一阈值**（GRADE Handbook 5.2.2，一手，逐字）：① 点估计方差大；② 置信区间"minimal or no overlap"；③ 异质性检验 p < 0.05；④ I² 大。降级"by one or even two levels"。
  - 注意：这四条本身**全部可机器计算**——这是 GRADE 里最容易做成 gate 的一域。
- **Summary of Findings 表**（Cochrane Handbook 14 章）必须含：人群与场景、干预与对照、关键结局清单（**最多七个**）、每个结局的典型负担度量、绝对与相对效应量、参与者数与研究数、逐结局 GRADE 确定性、评论栏、解释性脚注。Handbook 同时要求"Justify and document all assessments of the certainty of the body of evidence"。
- **GRADE 官方自动化：GRADErater**（GRADE Rating Automation Through Enhanced Reasoning），JCE 2026，DOI `10.1016/j.jclinepi.2026.112411`。七条开发原则：(i) 符合现行 GRADE 指南、(ii) 透明、(iii) **人类监督**、(iv) **实现决策规则**、(v) 易用、(vi) 可理解、(vii) 持续改进。已上线首版 https://gradeai.med.up.pt/ ，规则由官方 GRADE 来源导出并经 GRADE 专家验证，后续将与 GRADEpro 集成。
- **GRADE 域间相关性陷阱**（JCE 2024，`10.1016/j.jclinepi.2024.111543`）：异质性会加宽随机效应模型 CI，从而同时触发 imprecision，导致**同一个原因被降级两次**。作者提出用 prediction interval 同时评估 imprecision + inconsistency；在 2,516 个 Cochrane meta 分析上，PI 法与传统法降级层数相同的比例为 **59%**，PI 法降更多的 27%，降更少的 14%。
  - https://www.jclinepi.com/article/S0895-4356(24)00299-3/abstract

### B. PRISMA 2020：哪些条目机器可判

- **结构**：27 个编号条目；把子条目（10a/10b 等）单独计则为 **42 条**；每条下挂"reporting elements"，**共 183 个**（Page 等 2026 F1000Research 研究方案，一手）。另有独立的 PRISMA 2020 for Abstracts 清单与流程图。
  - PRISMA 2020 原文：https://pmc.ncbi.nlm.nih.gov/articles/PMC8007028/
- **PRISMA-Check（关键先例）**：Page（PRISMA 2020 作者本人）团队正在建的**遵从性评估工具**，把每个 element 重写成一个或多个 **Yes/No（部分含 N/A）** 的问题；目前 **315 题覆盖 171 个 element、对应 42 条中的 41 条**（摘要条目排除）。答案按确定性规则向上聚合：**某 element 的全部适用问题都为 Yes → 该 element 记为 "reported"；某 item 的全部适用 element 都为 reported → 该 item 记为 "reported"。**
  - 示例（逐字）：element"Report how many reviewers collected data from each report, whether multiple reviewers worked independently or not, and any processes used to resolve disagreements"被拆成 9.1a–9.1d 四个带前置条件的问题。
  - **本轮项目只评其中 200 题 / 95 个 element**，被剔除的那批是"主研究者判断为人和 LLM 都难判、主观性更强"的 element。→ **这是一个官方级别的"可判定性分诊"先例。**
  - https://f1000research.com/articles/15-665 （F1000Research 2026, 15:665；v1 发表 2026-05-04；开放同行评审状态：1 approved with reservations）
- **PRISMA-S**（检索报告扩展）：16 条，全部关于检索的可复现性（平台、数据库、完整检索式、日期、去重等），是**整份 PRISMA 家族里机器可判性最高的一块**。
  - https://www.prisma-statement.org/prisma-search ；原文 https://link.springer.com/article/10.1186/s13643-020-01542-z
- **LLM 自动查 PRISMA 遵从性的实测**（Kataoka 等，arXiv:2511.16707，预印本，2025-11-20 提交）：108 篇 CC 许可综述基准；给结构化 PRISMA 清单（Markdown/JSON/XML/纯文本）时准确率 **78.7–79.7%**，只给正文时 **45.21%**（p<0.0001）；十个模型间准确率 70.6–82.8%；选 Qwen3-Max 扩到 n=120 后 **敏感度 95.1%、特异度 49.3%**。作者结论：human expert verification remains essential。
  - https://arxiv.org/abs/2511.16707

### C. Cochrane RoB 2 / ROBINS-I：信号问题 → 算法 → 判定

一手文件：`Revised Cochrane risk-of-bias tool for randomized trials (RoB 2)`，Higgins/Savović/Page/Sterne 编，**版本日期 22 August 2019**（从 https://www.riskofbias.info/welcome/rob-2-0-tool/current-version-of-rob-2 下载的当前版）。

- **五个域**（个体随机平行组试验版）：① randomization process、② deviations from intended interventions、③ missing outcome data、④ measurement of the outcome、⑤ selection of the reported result。
- **信号问题数**（本版逐条核出）：D1 = 3（1.1–1.3）；D2 = 7（2.1–2.7，"effect of assignment" 变体）/ 6（2.1–2.6，"effect of adhering" 变体）；D3 = 4（3.1–3.4）；D4 = 5（4.1–4.5）；D5 = 3（5.1–5.3）。→ 合计 **22 题（assignment 变体）/ 21 题（adhering 变体）**。
- **响应选项**：Yes / Probably yes / Probably no / No / No information；条件触发的问题另加 Not applicable。逐字："Signalling questions should be answered independently: the answer to one question should not affect answers to other questions in the same or other domains other than through determining which subsequent questions are answered."
- **"No information" 的语义规则（极其可移植）**：逐字——"If the question seeks to identify evidence of a problem, then 'No information' corresponds to no evidence of that problem. If the question relates to an item that is expected to be reported (such as whether any participants were lost to follow up), then the absence of information leads to concerns about there being a problem."
  - → 机器 gate 直译：**缺信息不是中性的**，其默认值取决于该字段是"找问题"还是"应报告项"。
- **算法与可推翻性**：逐字——"The tool includes algorithms that map responses to signalling questions onto a proposed risk-of-bias judgement for each domain."；"the algorithms provide **proposed** judgements, but users should verify these and change them if they feel this is appropriate."；"It is particularly important that reasons are provided for any judgements that **do not follow the proposed algorithms**."
- **域 → 总体的聚合规则**（Table 1，逐字）：Low = 所有域皆 low；Some concerns = 至少一域 some concerns 且无一域 high；High = 至少一域 high，**或** 多域 some concerns 到"substantially lowers confidence in the result"的程度。并规定：某域判 High，则整体判 High，**与是哪个域无关**。
- **证据指针要求**：每个信号问题旁有自由文本框，逐字要求"Brief direct quotations from the text of the study report should be used whenever possible."
- **ROBINS-I V2**（非随机干预研究），launch version 2024-11-22。相对 V1 的两个结构性变化（来自官方资源页与工具文件）：域重组（V1 的 "deviations from intended intervention" 域被移除、其关切被重新分配），以及部分信号问题引入 **"strong" vs "weak" 的 yes/no 分级**，不同强度导向不同的 RoB 判定。
  - https://www.riskofbias.info/welcome/robins-i-v2 ；https://corates.org/resources/robins-i
  - **口径提醒**：网上"ROBINS-I 有七个域"的说法多来自 V1；V2 域数与 V1 不同——本文不给 V2 的确切域数（见"未决"）。

### D. Living systematic review：更新触发器

一手：Elliott 等，"Living systematic review: 1. Introduction—the why, what, when, and how"，J Clin Epidemiol 2017;91:23–30，DOI `10.1016/j.jclinepi.2017.08.010`（OA 副本 https://researchmgt.monash.edu/ws/files/239724873/106996193_oa.pdf ）。

- **定义（逐字）**："a systematic review that is continually updated, incorporating relevant new evidence as it becomes available."
- **何时该做 LSR：三条判据（逐字要点）**
  1. The systematic review is a priority for decision-making.
  2. **Certainty in the existing evidence is low or very low.**（→ 更新触发器直接挂在确定性状态上）
  3. There is likely to be new research evidence.
  - 并且："Embarking on an LSR is not a life sentence. It will be appropriate to cease this form of updating when the conditions specified above no longer hold."
- **时效上限（逐字）**："we propose that LSRs should incorporate relevant new information within a maximum of 6 months of the information becoming available"；实践中"most current LSR pilot projects aim to search most sources **at least monthly** and make the results of these searches visible to end users within another month."
- **三种更新场景（直接可映射为分级重验深度）**
  1. 检索后**无新证据** → 只更新"末次检索日期 + 已筛记录数"；作者建议此场景**仅需编辑审查、无需同行评审**。
  2. **有新证据但暂不纳入** → 必须公开：末次检索日期、新证据细节、是否纳入、**以及不纳入的透明理由**；若理由与协议一致，同行评审可选。
  3. **决定纳入新证据** → 触发下一阶段完整生产（RoB 评估、数据提取、meta 分析更新、结论与含义更新），并触发完整编辑 + 同行评审；但"若新证据对确定性与结论影响可忽略，编辑审查即可"。
- **协议必须预先写死的字段**（Box 3）：各来源的检索频率；筛选频率（最好与检索频率匹配）；新证据是立即并入还是可延迟、若可延迟则延迟决策框架；meta 分析更新的统计方法；使用了哪些 enabling technologies（机器学习/公民科学）；**退出 LSR 模式的具体阈值**。
- **重复 meta 分析的假阳性风险**由该系列第 3 篇处理（Simmonds 等，2017）：反复做 meta 分析会抬高虚假显著性的概率。
- 与自动化的接口由该系列第 2 篇（Thomas 等，2017）给出：搜索、合格性判断、全文获取、数据提取、RoB 评估都是可部分自动化的任务，但主张"human effort 与 machine automation 互相赋能"，而非替代。

### E. 自动化尝试与实测性能

#### E1. otto-SR（**预印本，非期刊论文**）

- 一手：`https://ottosr.com/manuscript.pdf`（= medRxiv `10.1101/2025.06.13.25329541`）。**发表状态核实**：Europe PMC 全库检索该标题，**唯一命中 source=PPR（预印本），无期刊记录**（查询日 2026-08-17）。
- **摘要头条数字的口径问题（本文标 `corrected`）**：摘要写 "SR screening (otto-SR: 96.7% sensitivity, 97.9% specificity; human: 81.7% sensitivity, 98.1% specificity)"。但正文里：全文筛选阶段（5 篇综述）otto-SR = 96.2% 敏感 / 96.9% 特异，人类 = **63.3%** 敏感；**剔除一篇被作者称为 outlier 的 "Reinfection" 综述后**，人类加权敏感度才是 81.7%；而 98.1% 是五篇全算的人类特异度。摘要那对 96.7/97.9 在正文中查无对应值。→ **正确表述是："全文筛选阶段、剔除 1/5 篇异常综述后的对比"，不是"筛选总体"。**
- 摘要筛选阶段（正文值，5 篇综述，otto-SR 跑完整检索 n=32,357 条；人类与 Elicit 只在随机代表性子样本 n=1,767 上评）：otto-SR 加权敏感 96.6%（94.1–100.0），特异 93.9%；dual human 敏感 87.3%、特异 95.7%；Elicit 敏感 88.5%、特异 84.2%。**参考标准 = 原作者全文筛选后的最终纳排决定。**
- 数据提取（7 篇综述、4,459 数据点；人类只在 1,453 数据点子样本上评）：otto-SR 加权准确率 93.1%（91.1–97.0），dual human 79.7%（69.1–91.0），Elicit 74.8%（58.8–83.1）。**参考标准是"修正后金标准"**：用 LLM-as-a-judge 比对原作者提取值，再对分歧做盲法裁决。作者自陈的偏倚（逐字）："when otto-SR and the original authors produced identical values, we assumed these were correct without further adjudication… This approach could potentially bias our evaluation against alternative models (e.g., Elicit or dual human reviewers) that disagreed with both reference sources."（作者做了 10% 抽查，称无误）
- Cochrane 复现（2024 年 4 月刊 14 篇取 12 篇；检索更新至 2025-05-08，共 146,276 条引文）：筛选阶段**正确识别全部 64 篇已纳入研究**；错误排除中位数 0 篇（IQR 0–0.25）；额外发现 54 篇原作者疑似遗漏的合格研究（每篇中位数 2，IQR 1–6.25），更新检索再加 14 篇；假阳性纳入 10 篇（其中 9 篇经作者通信可能确有相关数据）。meta 分析：2 篇（nutrition、depression）产生新的统计显著结论，1 篇（alcohol）失去显著性。
- 作者自述的复现性观察（逐字）："All 12 reviews had issues with search reproducibility and 2 reviews lacked methodological clarity."

#### E2. 同团队的**已同行评审**论文（Annals of Internal Medicine, 2025-03）

DOI `10.7326/ANNALS-24-02189`，`Development of Prompt Templates for Large Language Model-Driven Screening in Systematic Reviews`。这是 `ottosr.com` 实际链到的那篇。

- 摘要筛选：10 篇 SR、48,425 条引文；优化提示词 + GPT4-0125-preview 达 **加权敏感度 97.7%（86.7–100%）、特异度 85.2%（68.3–95.9%）**。
- 全文筛选：12,690 篇免费全文；**敏感度 96.5%（89.7–100%）、特异度 91.2%（80.7–100%）**。
- **零样本提示词敏感度只有 49.0%（摘要）/ 49.1%（全文）** ← 本项目最该记住的一个数字：没有提示词工程，模型漏掉一半相关文献。
- 成本口径：10,000 条引文，单人摘要筛选估计 >83 小时 / $1,666.67 USD；其 LLM 方案不到一天 / **$157.02 USD**。（2025-03 的模型与价格，会过期）
- 局限（作者自陈）：回顾性研究；SR 为便利样本；全文评估仅限 PubMed Central 免费全文。

#### E3. Elicit

- **厂商自述**（https://elicit.com/blog/how-we-evaluated-elicit-systematic-review ，2025-03-18）：筛选"correctly screens in 94% of papers"，在正确设定筛选标准前提下 real-world screening recall ~96.4%；报告 93.6% recall / 62.8% specificity；数据提取"94–99% accuracy"，其中 VDI/VDE 外部团队"found Elicit was 99.4% accurate"（1,502/1,511 数据点）。内部评测集 128 条人工核验提取。
- **同行评审的独立评测**（Lagisz 等，Research Synthesis Methods，2026-05-29 在线，DOI `10.1017/rsm.2026.10080`）：7 篇生命/环境科学 SR，人工提取为金标准，每篇 8 篇文章开发提示词 + 8 篇测试。
  - 换 Elicit 账号重跑：**取值一致 90%（476/536）、支撑引文一致 46%、推理一致 30%**；开 high-accuracy 模式：取值 77%（412/536）、引文 10%、推理 **0%**。
  - Elicit 与金标准不符率 **10.6%（22/208）**，人–人不符率 **1.9%（4/208）**。
  - 90 个提示词中 70 个在开发阶段过了 87% 准确率门槛，但迁移到新文章集后只有 48/70（69%）仍 ≥87%。
  - 结论（逐字）："Elicit can complement, but not replace, human data extractors. Elicit may be best used for sanity checks and to evaluate the clarity of data extraction protocols."
  - **口径冲突提示**：厂商的"94–99% 准确率"与本研究的"10.6% 不符率、且引文/推理几乎不可重跑"并不矛盾——它们是**不同指标**（一次性取值命中 vs 跨运行可重跑性 + 相对人–人基线）。把前者当"可信度"用就是洗白。
- otto-SR 预印本对 Elicit 的第三方测量：摘要筛选敏感 88.5% / 特异 84.2%；数据提取准确 74.8%；Elicit 当时不支持全文筛选。

#### E4. RobotReviewer / RCT 分类器

- **RobotReviewer 原始评测**（Marshall/Kuiper/Wallace，JAMIA，DOI `10.1093/jamia/ocv044`，2015 在线/2016 卷期）：用 CDSR 数据算法标注 12,808 篇试验 PDF，标签是 **low vs high/unclear 二分**；用"CDSR 中有 ≥2 次独立 RoB 评估的试验"来估算准确率。结果（逐字）："Model RoB judgments were less accurate than those from published reviews, though the difference was <10% (**overall accuracy 71.0% with ML v 78.3% with CDSR**)."；支撑句抽取（top-3 recall）："60.4% ML text rated 'highly relevant' v 56.5% of text from reviews; difference +3.9%, [−3.2% to +10.9%]"（**不显著**）。
- **前瞻性交叉评测**（Gates/Vandermeer/Hartling，J Clin Epidemiol 2018，PMID 29289761）：1,180 篇试验，逐域算与人类的 Cohen's κ——
  - random sequence generation **0.48**（0.43–0.53）、allocation concealment **0.45**、blinding of participants and personnel **0.42** → moderate
  - overall risk of bias **0.34** → fair
  - blinding of outcome assessors **0.10**、incomplete outcome data **0.14**、**selective reporting 0.02（−0.02–0.05）** → slight（≈随机）
  - 敏感度 0.20–0.76，特异度 0.61–0.95。结论逐字开头："Risk of bias appraisal is subjective."
  - → **同一个工具，"71% 准确率"与"选择性报告域 κ=0.02"描述的是同一件事的两个面。只报前者就是口径失真。**
- **真实工作流接受度**（Arno 等，BMC Med Res Methodol 2022，DOI `10.1186/s12874-022-01649-y`）：26 篇 RCT、6 名评审员；共识过程中评审员接受 RobotReviewer 判定的概率与接受同伴判定的概率无差异（**RR 1.02，95% CI 0.92–1.13，p=0.33**）；但即便看到该证据，参与者仍不愿修改标准流程纳入自动化。
- **RCT 分类器**（RobotSearch / Cochrane RCT Classifier，Marshall 等 2018，PMC6030513）：以固定特异度 97.5% 为切点选阈值，ML 在所有敏感度水平上都优于传统数据库检索过滤器。Trialstreamer 预印本报"RCT classifier retrieved 94–97% of RCT articles"。**注：这几个数字我只经二手片段见到，标 `unverified`（见核验表）。**
- **数字洗白实例**：第三方项目 RCT-Reviewer（自述 "RobotReviewer Modernized"）在其文档页元数据中写 "Achieves 71.0% accuracy, 87% precision, and 90% recall"、"Near-human accuracy (71.0%) within 8% of expert consensus"。71.0% 与 78.3% 是 2015 年 JAMIA 论文在旧 RoB1 二分标签下的数字，被移植为该工具的当前性能声明。
  - https://rct-reviewer.github.io/Documentation/

#### E5. ASReview（主动学习筛选优先级）

- 一手（van de Schoot 等，arXiv:2006.12166v3；期刊版 Nature Machine Intelligence 3, 125–133, 2021，DOI `10.1038/s42256-020-00287-7`）：**4 个数据集、每个 15 次运行**（各以 1 篇随机纳入 + 1 篇随机排除作先验）。逐字："The average work saved over sampling at 95% recall for ASReview is **83% and ranges from 67% to 92%**. Hence, 95% of the eligible studies will be found after screening between only 8% to 33% of the studies."
  - **WSS 的定义（逐字）**："WSS is the percentage reduction in the number of records needed to screen that is achieved by using the program instead of screening records at random."→ 基线是**随机筛选**，不是"不筛"。这是最容易被误读成"省了 83% 工作量"的地方。
  - 同文明确："to be sure to detect 100% of relevant records, all records need to be screened, therefore leading to no time savings."
- **独立模拟研究**（Ferdinands 等，Systematic Reviews 2023，DOI `10.1186/s13643-023-02257-7`）：6 个不同学科 SR 数据集 × 4 种分类器 × 2 种特征抽取。逐字："The models reduce the number of publications needed to screen by **91.7 to 63.9%** while still finding 95% of all relevant records (WSS@95)."；"Recall … after screening 10% of all records … **ranges from 53.6 to 99.8%**"。整体最优组合为 Naive Bayes + TF-IDF。
  - → **同一族方法，WSS@95 的跨数据集离散度接近 30 个百分点；单点报"83%"没有可移植性。**

#### E6. LLM 做 RoB（三个口径互相校正的研究）

| 研究 | 设计 | 关键数字（含口径） |
|---|---|---|
| Šuster 等, Res Synth Methods 2024, `10.1002/jrsm.1749` | 零/少样本提示，两种任务：直接预测 RoB2；先答信号问题再决策（decomposition） | 直接预测测试集 n=5,993，**F1 0.1–0.2**，与平凡基线相当；decomposition 设置 n=28,150，F1 相似。结论逐字："Using LLMs as an assisting technology for assessing RoB2 thus currently seems beyond their reach." |
| Lai 等, JAMA Netw Open 2024, `10.1001/jamanetworkopen.2024.12687` | 30 篇 RCT，**改良版 Cochrane ROB 工具（McMaster CLARITY 版）**，3 位专家共识为准据 | ChatGPT 平均正确率 **84.5%（81.5–87.3）**、Claude **89.5%（87.0–91.8）**；但域 1/2/6 敏感度 <0.80，**域 4（缺失结局数据）、5（选择性报告）、6（其他）F1 < 0.50**；两次评估自身一致率 84.0% / 87.3%；单篇耗时 77 秒 / 53 秒 |
| Huang 等, JMIR 2025, `10.2196/70450` | 46 篇 RCT（6 篇调提示词，40 篇作内部验证），RoB2，3 名有经验评审员共识 + Cochrane 判定双重对照 | **信号问题层面平均准确率 83.2%（95% CI 77.5–88.9）**；其余 6 个域平均 65.2%（57.6–72.7）对 Cochrane、74.2%（64.7–83.9）对评审员；**整体 RoB 判定 57.5%（assignment）/ 70%（adhering）对 Cochrane** |
| Rose 等, Cochrane Evid Synth Methods 2025, `10.1002/cesm.70048` | 100 篇 Cochrane 综述随机抽样（25 篇调提示词、75 篇评测），每篇随机取 1 篇试验；全部用 **RoB1**；ChatGPT-4o（2025-02） | 人–GPT "Overall RoB" 一致率 **50.7%（39.3–62.0）**；"RoB due to randomization process" **78.7%（69.4–88.0）**；**GPT–GPT 自身重测一致率 74.7%（64.8–84.6）** |

#### E7. GRADE 自动化实测

- **URSE**（Dos Santos 等，BMJ Evidence-Based Medicine 2026，DOI `10.1136/bmjebm-2024-113123`，同行评审）：一个把 GRADE **改造得更客观**的算法 + Python/React 实现，开源 https://github.com/alisson-mfc/urse ；在 **115 篇 Cochrane 综述**上与人类评估者比对。
  - 整体证据等级一致率 **63.2%，Cohen's κ = 0.44**
  - 逐域 accuracy / F1：**imprecision（按参与者数）0.97 / 0.94**；**risk of bias 0.73 / 0.70**；**I²（异质性）0.90 / 0.90**；**方法学质量（AMSTAR）0.98 / 0.99**
  - 结论逐字："in consideration of the emphasis of the GRADE approach on subjectivity and understanding the context of evidence production, **full automation of the classification process is not opportune**."

### F. 认知状态分类法：IPCC 校准语言（最可移植的一块）

一手：Mastrandrea 等 2010，`Guidance Note for Lead Authors of the IPCC Fifth Assessment Report on Consistent Treatment of Uncertainties`（IPCC 官网 403，取自 MPG 机构库 https://pure.mpg.de/rest/items/item_2147184/component/file_2147185/content ）。AR6 沿用：AR6 WGI SPM 脚注 4 逐字给出同一套 likelihood 表并写明 "This is consistent with AR5."（镜像：https://pure.iiasa.ac.at/id/eprint/19094/1/IPCC_AR6_WGI_SPM.pdf ，2021-08）

- **两个正交轴**：
  - *Confidence*（定性，5 档：very low / low / medium / high / very high），由 **evidence（type, amount, quality, consistency；摘要词 limited / medium / robust）× agreement（low / medium / high）** 的二维格子导出。
  - *Likelihood*（定量，概率区间）：virtually certain 99–100%；very likely 90–100%；likely 66–100%；about as likely as not 33–66%；unlikely 0–33%；very unlikely 0–10%；exceptionally unlikely 0–1%。（AR5 附加词：extremely likely 95–100%、more likely than not >50–100%、extremely unlikely 0–5%）
- **升级/降级的准入规则（第 8 段，逐字）**
  - high agreement **且** robust evidence → 给 confidence 或定量不确定度；
  - high agreement **或** robust evidence（不同时具备）→ 尽可能给 confidence 或定量化，**否则只给 evidence/agreement 摘要词**（如 "robust evidence, medium agreement"）；
  - **low agreement 且 limited evidence → 只给 evidence/agreement 摘要词**（即：不给 confidence，更不给概率）。
- **量化语言的准入门槛（第 11 段准则 E/F，逐字）**："Assign a likelihood for the event or outcomes, **for which confidence should be 'high' or 'very high'**"；准则 F 对概率分布同样要求 confidence 为 high/very high。
- **其他可直接抄的约束**
  - "Confidence should not be interpreted probabilistically, and it is distinct from 'statistical confidence.'"
  - "Presentation of findings with 'low' and 'very low' confidence should be reserved for areas of major concern, and the reasons for their presentation should be carefully explained."
  - "'About as likely as not' should not be used to express a lack of knowledge."（**缺乏知识 ≠ 50/50**）
  - "the degree of certainty in findings that are **conditional on other findings** should be evaluated and reported separately."（条件性结论要单独定级 → 我们的 claim graph 里，派生 claim 不能继承父 claim 的状态）
  - 每条 key finding 都必须在章节正文提供 **traceable account**（可追溯说明）。

### G. 治理层：AI 使用的申报义务

Flemyng 等，`Position Statement on Artificial Intelligence (AI) Use in Evidence Synthesis`，Cochrane × Campbell Collaboration × JBI × Collaboration for Environmental Evidence，Campbell Systematic Reviews，2025-11-10（https://pmc.ncbi.nlm.nih.gov/articles/PMC12603384/ ）。核心条款：

- 作者对综述的内容、方法与结论（**包括使用 AI 的决定本身**）负最终责任；
- **凡 AI"做出或建议判断"**（合格性、偏倚风险、数据提取、合成、确定性评估）**必须申报**，且要报告：系统名与版本、用途、**含验证证据的使用理由**、利益冲突、局限；
- 使用 AI 的决定应在**协议阶段**就考虑并写明，前置投入验证工作；
- 对工具开发者：须公开系统工作原理、透明的测试/验证评估、成文的强弱项。
- 配套的 RAISE（Responsible use of AI in evidence SynthEsis）指南（OSF 项目 https://osf.io/fwaud/overview ）为其框架来源；Page 等 2026 的 PRISMA 自动化方案即声明遵循 RAISE。

---

## 载荷数字核验表

一行一个数字：数字 | 口径三元组（指标 / 样本与条件 / 比较对象） | 状态 | 一手出处。

| 数字 | 口径三元组 | 状态 | 一手出处 |
|---|---|---|---|
| otto-SR 96.7% 敏感 / 97.9% 特异 vs 人类 81.7% / 98.1% | 摘要标为 "SR screening"；正文可核的是**全文筛选阶段**，且人类 81.7% 是**剔除 1/5 篇 outlier 综述后**的加权值，98.1% 是五篇全算值；96.7/97.9 在正文中无对应值 | **corrected**（正确表述：全文筛选、剔除一篇异常综述后的对比；五篇全算时 otto-SR 96.2%/96.9%、人类 63.3% 敏感） | ottosr.com/manuscript.pdf（=medRxiv 10.1101/2025.06.13.25329541）摘要 vs 正文 §3 |
| otto-SR 摘要筛选 96.6% 敏感 / 93.9% 特异 | 加权敏感/特异 / 5 篇综述完整检索 n=32,357 引文（人类与 Elicit 仅在 n=1,767 随机子样本）/ 参考标准 = 原作者全文筛后最终纳排 | verified | 同上，正文 §3 |
| dual human 摘要筛选 87.3% 敏感 / 95.7% 特异；Elicit 88.5% / 84.2% | 同上口径，子样本 n=1,767 | verified | 同上 |
| otto-SR 数据提取 93.1%（91.1–97.0）vs dual human 79.7%（69.1–91.0）vs Elicit 74.8% | 加权变量级准确率 / 7 篇综述 4,459 数据点（人类仅 1,453 数据点子样本）/ 参考标准 = 盲法裁决构造的"修正金标准"，作者承认该标准对与两个参考源都不一致的系统不利 | verified（带作者自陈偏倚） | 同上，正文 §4 + Methods 8.9 |
| otto-SR 复现 12 篇 Cochrane 综述、146,276 引文、正确识别全部 64 篇纳入研究、额外发现 54 篇（中位 2，IQR 1–6.25）、2 篇新增显著 / 1 篇失去显著 | 复现口径：2024-04 刊 14 篇取 12 篇，只复现各篇**预设主要结局**（与 Cochrane 全结局做法不同）；检索更新至 2025-05-08 | verified | 同上，正文 §5 |
| otto-SR 为**预印本**，非期刊论文 | 发表状态 / Europe PMC 标题精确检索，2026-08-17 / 唯一命中 source=PPR | verified（并 **corrected** 厂商页"Peer-reviewed in the Annals of Internal Medicine"的说法：该 DOI 指向同团队另一篇提示词模板论文） | Europe PMC REST 查询；Crossref 10.7326/ANNALS-24-02189 |
| 97.7% 敏感 / 85.2% 特异（摘要筛选）；96.5% / 91.2%（全文筛选） | 加权敏感/特异 / 10 篇 SR、48,425 条引文（全文段 12,690 篇免费全文）、GPT4-0125-preview + 优化提示词 / 参考标准 = 原 SR 作者全文筛后决定 | verified | Annals Intern Med 2025, DOI 10.7326/ANNALS-24-02189 |
| 零样本提示敏感度 49.0%（摘要）/ 49.1%（全文） | 同上样本与参考标准，仅提示词策略不同 | verified | 同上 |
| $157.02 vs $1,666.67 / 10,000 条引文 | 直接筛选成本 / 10,000 引文、2025-03 的模型与价格 / 比较对象 = 单人（非双人）摘要筛选的估算成本（>83 小时） | verified（**会过期**：模型与价格均已变动） | 同上 |
| Elicit 换账号重跑：取值 90%、引文 46%、推理 30%；high-accuracy 模式 77% / 10% / 0% | 跨账号重跑的逐项完全匹配率 / 7 篇 SR、536 个可分析取值 / 比较对象 = 同一提示词的另一次运行 | verified | Res Synth Methods 2026, DOI 10.1017/rsm.2026.10080 |
| Elicit 与金标准不符 10.6%（22/208）；人–人不符 1.9%（4/208） | 不符率 / 同一 208 个取值 / 比较对象 = 人工金标准 | verified | 同上 |
| Elicit "94–99% accuracy"、"99.4% accurate"（1,502/1,511） | 厂商自述提取准确率 / 内部 128 条核验提取 + VDI/VDE 外部评测 / 比较对象 = 人工"金标准"提取 | verified 为**厂商声明**（非独立评测）；与上两行同行评审结果指标不同，不可互换 | elicit.com/blog/how-we-evaluated-elicit-systematic-review（2025-03-18） |
| Elicit 筛选 93.6% recall / 62.8% specificity（调整后 recall ~96.4%） | 厂商自述 / 58 篇已发表 SR 的问题重建 + 语义检索得到的"不相关"文献 / 参考标准 = 原 SR 的纳入文献 | verified 为**厂商声明** | 同上 |
| RobotReviewer 71.0% vs CDSR 78.3% | 整体准确率 / 12,808 篇试验 PDF 训练、以 CDSR 中有 ≥2 次独立评估的试验估准确率；标签为 **low vs high/unclear 二分（RoB1）** / 比较对象 = 已发表综述的人类判定 | verified | JAMIA, DOI 10.1093/jamia/ocv044 |
| 支撑文本 60.4% vs 56.5%（差 +3.9%，CI −3.2 到 +10.9） | top-3 recall 下"highly relevant"评级比例 / 20 名盲法评审 / 比较对象 = CDSR 人工抽取文本 | verified（**不显著**，常被引作"机器抽取优于人工"） | 同上 |
| RobotReviewer 逐域 κ：0.48 / 0.45 / 0.42 / 0.34（overall）/ 0.10 / 0.14 / **0.02**（选择性报告） | Cohen's κ / 1,180 篇试验、前瞻性交叉设计 / 比较对象 = 人类评审员 | verified | J Clin Epidemiol 2018, PMID 29289761 |
| 评审员接受机器判定 vs 接受同伴判定 RR 1.02（0.92–1.13, p=0.33） | 共识过程中被采纳的相对风险 / 26 篇 RCT、6 名评审员 / 比较对象 = 同伴人类判定 | verified | BMC Med Res Methodol 2022, DOI 10.1186/s12874-022-01649-y |
| ASReview WSS@95 平均 83%，范围 67–92%（即筛 8–33% 记录找到 95% 相关文献） | Work Saved over Sampling @95% recall；**基线是随机筛选** / 4 个数据集 × 15 次运行，各以 1 篇随机纳入 + 1 篇随机排除作先验 / 比较对象 = 随机顺序筛选 | verified | arXiv:2006.12166v3（期刊版 Nat Mach Intell 2021, 10.1038/s42256-020-00287-7） |
| WSS@95 跨模型范围 63.9–91.7%；筛完 10% 记录时 recall 53.6–99.8% | 同 WSS 定义 / 6 个不同学科 SR 数据集 × 4 分类器 × 2 特征抽取 / 比较对象 = 随机筛选 | verified | Syst Rev 2023, DOI 10.1186/s13643-023-02257-7 |
| LLM 直接预测 RoB2 F1 0.1–0.2 | 宏/微 F1（论文未在摘要区分）/ 直接预测测试集 n=5,993；decomposition 设置 n=28,150 / 比较对象 = 平凡基线与监督式系统 | verified | Res Synth Methods 2024, DOI 10.1002/jrsm.1749 |
| ChatGPT 84.5%（81.5–87.3）/ Claude 89.5%（87.0–91.8）正确率；域 4/5/6 的 F1 < 0.50 | 逐域正确评估率 / 30 篇 RCT、**改良版 Cochrane ROB 工具（CLARITY 版）**、每篇评两次 / 参考标准 = 3 位专家共识 | verified（注意：高"正确率"与低 F1 并存 = 标签不平衡） | JAMA Netw Open 2024, DOI 10.1001/jamanetworkopen.2024.12687 |
| 信号问题层面 83.2%（77.5–88.9）；域层面 65.2%（对 Cochrane）/ 74.2%（对评审员）；整体 RoB 57.5%–70% | 准确率 / 46 篇 RCT（40 篇内部验证）、RoB2 / 双参考标准：Cochrane 综述判定 与 3 名评审员共识 | verified | JMIR 2025, DOI 10.2196/70450 |
| 人–GPT overall RoB 一致 50.7%（39.3–62.0）；randomization 域 78.7%；**GPT–GPT 自身一致 74.7%（64.8–84.6）** | 逐项一致率 / 100 篇 Cochrane 综述抽样（75 篇评测）、每篇 1 篇试验、全部 **RoB1**、ChatGPT-4o（2025-02）/ 参考标准 = 综述中的人类共识判定 | verified | Cochrane Evid Synth Methods 2025, DOI 10.1002/cesm.70048 |
| URSE 整体一致 63.2%、κ=0.44；imprecision 0.97/0.94、I² 0.90/0.90、AMSTAR 0.98/0.99、risk of bias 0.73/0.70 | 一致率 / κ / 逐域 accuracy 与 F1 / 115 篇 Cochrane 综述、**GRADE 的一个"增强客观性"改造版** / 比较对象 = 人类评估者的证据等级 | verified | BMJ Evid Based Med 2026, DOI 10.1136/bmjebm-2024-113123 |
| LLM 查 PRISMA：给结构化清单 78.7–79.7% vs 仅正文 45.21%（p<0.0001）；Qwen3-Max 敏感 95.1% / **特异 49.3%** | 条目级判定准确率 / 108 篇 CC 许可 SR（开发队列）→ n=120（全集）、10 个模型 × 5 种输入格式 / 参考标准：摘要未明示（见"未决"） | verified（**预印本**，arXiv:2511.16707，2025-11-20） | https://arxiv.org/abs/2511.16707 |
| PRISMA 2020 = 27 条 / 计子条目为 42 条 / 183 个 reporting elements | 条目计数 / PRISMA 2020 原文结构 / — | verified | Page 等 2026 F1000Research 15:665 正文；PRISMA 2020 原文 PMC8007028 |
| PRISMA-Check = 315 题覆盖 171 个 element、对应 42 条中的 41 条；本轮只评 200 题 / 95 个 element | 工具规模 / 研究方案声明（工具"currently includes"）/ — | verified（工具**在建**，尚无性能数据） | F1000Research 2026, 15:665, DOI 10.12688/f1000research.180216.1 |
| PRISMA-S = 16 条 | 条目计数 / 检索报告扩展 / — | verified | prisma-statement.org/prisma-search；Syst Rev 2021, 10.1186/s13643-020-01542-z |
| RoB 2 = 5 域；信号问题 22 题（assignment 变体）/ 21 题（adhering 变体）；D1=3, D2=7/6, D3=4, D4=5, D5=3 | 题数计数 / **个体随机平行组试验版、2019-08-22 版本** / — | verified（逐题从官方 PDF 核出） | riskofbias.info 当前版指南 PDF（22 August 2019） |
| SoF 表结局数上限 = 7 | 表格设计约束 / Cochrane 标准 SoF 表 / — | verified | Cochrane Handbook ch.14 |
| GRADE = 5 降级域 + 3 升级域，4 档确定性 | 域计数与档次 / GRADE 干预效应评级 / — | verified | Cochrane Handbook ch.14；GRADE Handbook §5 |
| PI 法 vs 传统法降级层数相同占 59%，PI 降更多 27%、更少 14% | 降级层数一致性 / 2,516 个 Cochrane meta 分析（每个中位 7 项研究，IQR 5–11）、用经验阈值 / 比较对象 = 分别评 imprecision 与 inconsistency 的传统做法 | verified | J Clin Epidemiol 2024, DOI 10.1016/j.jclinepi.2024.111543 |
| LSR：新证据纳入上限 6 个月；实践中至少每月检索 | 时效承诺 / LSR 方法学建议（2017 年提出，明言"expect this proposed upper limit to reduce over time"）/ — | verified（**2017 年的建议，已 9 年，可能过时**） | J Clin Epidemiol 2017;91:23–30, DOI 10.1016/j.jclinepi.2017.08.010 |
| IPCC likelihood 表：99–100 / 90–100 / 66–100 / 33–66 / 0–33 / 0–10 / 0–1 % | 概率区间定义 / IPCC 校准语言，AR5 定义、AR6 沿用（"This is consistent with AR5"）/ — | verified | Mastrandrea 等 2010 Guidance Note（MPG 镜像）；AR6 WGI SPM 脚注 4（IIASA 镜像） |
| "likelihood 仅在 confidence 为 high 或 very high 时给出" | 语言准入规则 / IPCC 主笔人指引第 11 段准则 E/F / — | verified（逐字） | 同上 Guidance Note |
| "只有 1% 的综述有完全可复现的检索策略"（Rethlefsen 等） | 可复现检索策略比例 / 未触达一手 / — | **unverified**（仅见于 otto-SR 预印本的引用；未读到 Rethlefsen 原文的样本与判定标准） | 待查 |
| RCT 分类器"retrieved 94–97% of RCT articles"；固定特异度 97.5% | 召回率 / 未触达一手正文 / — | **unverified**（仅见 Trialstreamer 2020 预印本片段与 Marshall 2018 摘要片段） | 待查 PMC6030513 与 Trialstreamer 原文 |
| RCT-Reviewer "71.0% accuracy, 87% precision, 90% recall" | 该第三方工具的自我性能声明 / 无自测样本描述 / — | **corrected**：71.0%/78.3% 是 RobotReviewer 2015 JAMIA 在 RoB1 二分标签下的数字，被移植为本工具性能；87%/90% 疑似支撑句抽取指标的再框定 | rct-reviewer.github.io/Documentation/ 元数据 vs JAMIA 10.1093/jamia/ocv044 |
| ROBINS-I V2 的确切域数 | 域计数 / V2 launch version 2024-11-22 / — | **unverified**（二手来源在"六域"与"七域"间冲突；未打开官方 V2 工具文件逐域核对） | 待查 riskofbias.info/welcome/robins-i-v2 官方 PDF |

---

## 对本项目的设计含义

### 1. claim 状态机应直接复刻 IPCC 的"两轴 + 准入门槛"，而不是自造一套形容词

建议的最小状态定义（每个 claim 必带）：

```
claim.evidence_base ∈ {limited, medium, robust}      # 证据的类型/数量/质量/一致性
claim.agreement     ∈ {low, medium, high}            # 独立来源间的一致程度
claim.status        ∈ {verified, supported, unverified, contested}
claim.quantified    : 仅当 status == verified 时才允许非空
```

**硬规则（从 IPCC 直译，都是机器可执行的）**
- `evidence_base == limited && agreement == low` → **禁止**赋 status，只能输出 `(limited evidence, low agreement)` 这种二元摘要。
- 只有 `verified`（≈ IPCC 的 high/very high confidence）才允许发布**量化断言**（区间、百分比、效应量）。这一条把"数字洗白"从"提示词纪律"变成"类型错误"。
- **条件性 claim 单独定级**："the degree of certainty in findings that are conditional on other findings should be evaluated and reported separately." → 派生 claim 不继承父 claim 状态，必须独立走 gate。这直接杀死"claim graph 里状态沿边传染"这一类前代失败。
- **"缺信息" ≠ 50/50**："'About as likely as not' should not be used to express a lack of knowledge."
- 每个 claim 必须挂 **traceable account**：证据指针 + 评估过程，而不是模型的自然语言解释。

### 2. gate 的形态照抄 RoB 2：信号问题（模型答）→ 确定性算法（代码判）→ 可推翻但要留痕

这是本轮最强的一条，而且有直接的量化支持：**同一模型在信号问题层面 83.2%，在聚合判定层面掉到 57.5–70%**（JMIR 2025）。所以：

- **模型只答"近乎事实性"的原子问题**（RoB 2 原话："reasonably factual in nature"），每题带受限值域。
- **值域抄 RoB 2**：`Yes / Probably yes / Probably no / No / No information`（+ 条件触发时的 `Not applicable`）。`Probably` 档的语义是"作了判断"，definitive 档是"有确凿证据"——**这个区分本身就是我们要的 verified/unverified 边界**，直接把它做成字段。
- **"No information" 的默认值必须按问题类型分流**（RoB 2 原文规则）：若该问题是"找问题"，NI = 无该问题的证据（偏向通过）；若该问题问的是"本应报告的事项"，NI = 该项存疑（偏向不通过）。→ 在 gate schema 里给每个问题加一个 `ni_polarity: evidence_of_problem | expected_to_be_reported` 字段。
- **聚合由代码做，且写死**：域级 = 表驱动映射；总体 = "任一域 High → 总体 High；任一域 Some concerns 且无 High → 总体 Some concerns"。RoB 2 明言"某域判 High 则整体 High，与是哪个域无关"——这是一个可单元测试的纯函数。
- **算法只给 proposed judgement，可被推翻，但推翻必须写理由**（RoB 2 原文："It is particularly important that reasons are provided for any judgements that do not follow the proposed algorithms."）。→ 我们的 gate 输出应是 `{proposed, final, override_reason?}`，`final != proposed && override_reason == null` 直接判失败。
- **每题必须带原文直引**（RoB 2："Brief direct quotations from the text of the study report should be used whenever possible."）。

### 3. "可重跑"必须是硬门，不是美德

- ChatGPT-4o 对同一试验的**自身重测一致率只有 74.7%**；Elicit 换账号重跑**引文一致率 46%、推理 30%**（high-accuracy 模式下 10% / 0%）。
- 因此：**claim 的可信度绝不能锚在"模型这次说了什么"上**。锚点只能是 (a) 可重跑的数据分析脚本 + 输入快照，(b) 可定位到源文本 span 的引文指针（offset/hash，不是模型转述的句子），(c) 可复算的逻辑推导。
- 建议给每个 verified claim 强制一个 `rerun_key`：`{artifact_hash, script_path, seed, model_id, prompt_hash}`，并把"换一次运行是否仍过 gate"做成 keep-if-better 循环的一个自动检查项（k-of-n 自洽性投票，而非单次输出）。
- **注意"agreement 不等于 correct"**：otto-SR 自陈的偏倚——当模型与原作者一致时被直接判为正确，这会系统性地压低第三方系统的分数。我们的自洽性投票必须只用作**触发复核的信号**，不能直接晋级为 verified。

### 4. 可自动化边界（TODAY，按证据）：三档分诊

| 档 | 任务 | 证据 | 处理 |
|---|---|---|---|
| **A. 机器可判定（可做成硬 gate）** | 统计量计算（I²、CI、prediction interval、OIS/样本量）、报告项存在性检查（PRISMA-S 的 16 条、检索式/日期/去重是否给出）、参与者与研究计数、结构完整性、引文可定位性、数据可重算性 | URSE：imprecision 0.97/0.94、I² 0.90/0.90、AMSTAR 0.98/0.99；GRADE inconsistency 的四条判据本身全部可算 | **纯代码 gate，不经模型**。判定即终局 |
| **B. 模型可辅助 + 代码聚合（gate 用，但需二次证据）** | 筛选/纳排、原子事实抽取、信号问题作答、reporting element 的"有没有报告" | 优化提示词筛选 97.7%/85.2%（摘要）、96.5%/91.2%（全文）；信号问题层 83.2%；PRISMA 条目 敏感 95.1% / **特异 49.3%** | **模型答题 + 代码聚合 + 强制引文指针 + k-of-n 自洽**。**高敏感低特异 → 只能当"标红待审"过滤器，不能当"通过"判据** |
| **C. 今天不可自动判定（必须留人 / 或标 unverified）** | 偏倚风险的域级与总体判定、间接性（indirectness）、选择性报告、GRADE 总体确定性等级、"重要性/优先级"类判断 | RobotReviewer 选择性报告 κ=0.02；LLM overall RoB 一致率 50.7%；LLM 域 4/5/6 的 F1<0.50；URSE 整体 κ=0.44 且 RoB 域仅 0.73/0.70；GRADE 官方结论"full automation … is not opportune" | **禁止机器晋级**。要么走人类裁决，要么 claim 停在 `supported`/`unverified` 并在产出中如实标注 |

> 一句话：**能算的自动化，能查存在性的半自动化，需要判断的不自动化。** 这条线是被实测数字画出来的，不是保守主义。

### 5. 连续循环（LSR 三场景）直接映射成 DSH 的 continuation loop

```
场景 1  新检索无新证据      → 只更新 {last_search_at, n_screened}；不重跑下游；最轻校验
场景 2  有新证据、暂不并入  → 必须公开：last_search_at + 新证据清单 + 并入与否 + 不并入的理由
                              （理由若与协议一致 → 无需完整重验）
场景 3  决定并入            → 触发完整下游重跑：RoB → 提取 → meta → 结论 → 含义
                              但深度按影响分级：若对确定性与结论"影响可忽略" → 轻审即可
```

- **启动/退出判据也照抄**：启动 = ①决策优先级高 ②现有证据确定性 low/very low ③预期会有新证据；三条不再成立就退出（"not a life sentence"）。→ 我们的 loop 应把"退出阈值"写进任务协议，而不是靠人喊停。
- **协议必须预置的字段**（LSR Box 3 直译）：各来源检索频率、筛选频率、是否立即并入、延迟并入的决策框架、meta 更新的统计方法、用了哪些自动化、多久回顾一次 scope/方法、退出阈值。
- **重复检验的假阳性风险**是已知的（LSR 系列第 3 篇）：每次并入新证据就重跑显著性检验，会抬高虚假显著率。我们的 keep-if-better 循环若以"指标变好"为门，必须做同样的多重比较控制，否则会系统性地"择优选噪声"。

### 6. 报告层：产出物结构照抄 SoF 表 + PRISMA-Check 的向上聚合

- **SoF 表的九件套**（人群与场景 / 对比 / ≤7 个关键结局 / 典型负担 / 绝对与相对效应 / 参与者数与研究数 / 逐结局确定性 / 评论 / 解释性脚注）可以直接当作我们"证据表"artifact 的 schema。**"最多七个结局"这条上限值得保留**——它是对"什么算 load-bearing"的强制排序。
- **向上聚合规则**照抄 PRISMA-Check：`所有适用子问题为 Yes → element = reported`；`所有适用 element = reported → item = reported`。全程无加权、无打分、无模型裁量。
- **可判定性分诊要显式**：PRISMA-Check 明确剔除了"人和 LLM 都难判、主观性更强"的 element，并在论文里说明。我们也应该维护一份 `undecidable.md`，把已知不可机判的检查项列出来并说明为什么——**这比假装全覆盖诚实得多，也是本项目的卖点本身**。

### 7. 治理与申报（合规成本很低，但是差异化卖点）

Cochrane/Campbell/JBI/CEE 联合立场声明要求：凡 AI"做出或建议判断"，必须申报系统名与版本、用途、**含验证证据的理由**、利益冲突、局限；且这些决定应在协议阶段确定。→ 我们可以**默认生成**这份申报块（model_id、prompt_hash、该任务的已知性能与出处、已知局限），作为每份产出的固定尾注。这几乎零成本，却让产出直接满足四大证据合成机构 2025 年的标准。

### 8. 元规则：把本轮抓到的两个洗白模式做成 lint

- **模式 1：状态洗白**（"peer-reviewed in X" → 实为预印本 / 指向的是另一篇论文）。→ 每条外部引用必须带 `venue_type ∈ {peer-reviewed, preprint, vendor-page, blog, unknown}`，且 peer-reviewed 必须能在 Crossref/Europe PMC 命中**同一标题**。
- **模式 2：口径移植**（把 A 工具在旧标签体系下的数字搬来当 B 工具的现指标）。→ 数字字段必须结构化为 `{value, metric, sample, condition, comparator, source_doi}`；任何缺 comparator 或 condition 的数字，**默认 unverified，不允许进入正文**。
- **模式 3：虚假独立佐证**。→ 引用图上做去重：多个来源若能追到同一 upstream DOI，计为 1 个独立源。IPCC 的 `agreement` 轴正是为此存在的（"evidence is most robust when there are multiple, consistent **independent** lines of high-quality evidence"）。

---

## 未决与风险

1. **ROBINS-I V2 的确切域数与信号问题数未核**。二手来源在"六域"与"七域"之间冲突（V1 是七域）。官方 launch version（2024-11-22）PDF 未逐域打开核对。→ 在本项目引用非随机研究偏倚工具前必须补核。

2. **PRISMA 自动化的关键实测仍是预印本**。Kataoka 等（arXiv:2511.16707）的 95.1% 敏感 / 49.3% 特异是当前最直接的证据，但为预印本，且摘要未说明参考标准如何建立（谁做的人类判定、几人、如何裁决）。Page 等的 PRISMA-Check 验证研究（F1000Research 15:665）**只是研究方案**，尚无结果——这是本领域最值得盯的一个待发表结果。

3. **"1% 的综述有完全可复现的检索策略"未核**。这个数字如果成立，对本项目的价值主张（可重跑）是极强的支撑，但目前只见于 otto-SR 预印本的引用。必须读 Rethlefsen 等原文，确认样本（哪些期刊/年份）与"fully reproducible"的判定标准。

4. **RCT 分类器的召回率数字未核**（"94–97%"、固定特异度 97.5%）。这类数字对"我们要不要自建检索过滤器"有直接影响。

5. **otto-SR 的"修正金标准"存在结构性偏袒风险，作者已自陈**：当 otto-SR 与原作者一致时直接判为正确，未裁决。作者做了 10% 抽查称无误，但 10% 抽查对系统性错误的检出力有限。→ **不要把 93.1% vs 79.7% 当作"机器优于人类"的定论引用**；正确表述是"在一个由该系统参与构造的修正标准下"。

6. **时效性风险**：本文多个数字会过期——(a) LLM 筛选成本（$157.02 / 10,000 引文，2025-03 模型与价格）；(b) 各 LLM RoB 数字绑定具体模型版本（GPT-4o 2025-02、GPT4-0125-preview 2024）；(c) LSR 的"6 个月上限"是 2017 年的建议，原文自己说预期会缩短；(d) GRADE Handbook 将在 2026 年底被 GRADE Book 全面取代（本文未核实该替换的完成情况，标 unverified）。凡引用这些数字必须带日期。

7. **领域外推风险**：几乎所有实测都在**医学/健康干预类系统综述**上做的（Cochrane 语料占绝对多数）。Elicit 的可行性研究是生命与环境科学，Ferdinands 的 6 个数据集跨学科——两者的性能离散度都明显更大（WSS@95 跨数据集差近 30 个百分点）。**不要把 Cochrane 语料上的数字外推到我们的目标领域**，除非在目标领域重测。

8. **IPCC 规则的移植限制**：IPCC 的 confidence 是**专家团队的集体判断**，其"agreement"轴依赖真实存在的多条独立证据线。在一个自动化系统里，"多个 agent 同意"**不是** independent lines of evidence——这正是 IPCC 那句 "multiple, consistent **independent** lines" 里 independent 一词在防的东西。若把 k-of-n 自洽性当作 agreement 轴的输入，会系统性地高估确定性。这是本项目最容易犯、也最致命的一个设计错误，须在 gate 层显式禁止。

9. **本文未覆盖但相邻的方向**（若后续需要）：AMSTAR 2 / ROBIS（评综述本身的质量，条目更偏结构化，可能比 GRADE 更好自动化）、GRADE-CERQual（定性证据）、SWiM（无法 meta 分析时的合成报告）、Cochrane RoB 2 的 Excel 实现（其内置算法可直接作为我们聚合函数的对拍参照）、PRISMA-trAIce（2025 年发布的 AI 使用报告扩展，与治理层直接相关，本文未展开）。
