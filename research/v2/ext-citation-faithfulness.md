# 外部调研 v2 · 维度：引用忠实度与幻觉引用的实证基线

> 调研日期：2026-08-17（今日）。所有会过期的数字都标注了测量时间点。
> 方法约束：每个载荷数字都回到一手来源（论文 PDF/HTML、期刊页、厂商官方文档），并记录**口径三元组**（什么指标 / 在什么样本与条件上 / 与什么对比）。二手转述一律不作为独立佐证。
> 注：本轮 WebSearch 配额在会话中途耗尽，后半程改用 serper（Google）检索 + WebFetch 一手取证；所有落笔数字均来自 WebFetch 到的一手页面或本地 pdftotext 抽取的论文正文，检索引擎摘要仅用于发现线索。

---

## 结论摘要

**1. 本维度最重要的一条实证事实：「链接能打开」和「源真的支持这句话」之间存在 40–60 个百分点的鸿沟，而且这个鸿沟在 2026 年的前沿深度研究产品上依然存在。**
PwC 团队（arXiv:2605.06635，2026-05-07）在 14 个前沿模型的深度研究报告上做了三层拆分测量：链接可访问率 94%+、内容主题相关率 80%+，但**逐条事实核查通过率只有 39–77%**。原话：用户点开一个引用，几乎总能看到一个能打开、主题也对得上的页面，但归因给该源的具体事实主张「可能有近一半是不被支持的」。这条把「表面引用质量掩盖事实失败」（surface-level citation quality masks factual failures）测成了可复现的数字。

**2. 「更深的搜索」不会改善支持率，反而会摧毁它——而表层指标毫无变化。**
同一篇论文的消融实验：GPT-5.4 在 2 次工具调用时事实核查通过率 78.6%，在 150 次工具调用时掉到 16.7%（跌 62 个百分点）；Claude Opus 4.6 从 80.0% 掉到 57.9%。而**链接有效率与相关率在所有搜索深度上都稳定在 92% 以上**。这对「hyper-parallel、多轮 loop」的架构是直接的负面证据：并行度和检索深度必须与「每条 claim 的证据预算」解耦，否则规模化会系统性地劣化忠实度而不被表层监控发现。

**3. 一条陈述缺乏支持时，「多引几个源」救不回来。**
SourceCheckup（Nature Communications 2025-04-16）：把某条陈述的**全部**被引源合并后再判定，**95.1% 原本不被支持的陈述仍然不被支持**。说明失败模式不是「证据分散在多个源里」，而是「该陈述根本没有源」。

**4. 学界对「幻觉」的定义分裂，这是最大的口径污染源。**
Magesh et al.（JELS 2025）给出了目前最清晰的二维分解：**correctness（对不对）× groundedness（引文撑不撑得住）**，并把 hallucination 定义为「incorrect **或** misgrounded」。他们明确点破：LexisNexis 宣称的「100% hallucination-free linked legal citations」只在最狭义上成立——链接确实指向真实法律文书；如果链接的源不相关甚至与结论相反，在他们的定义下仍是幻觉。**本项目的产品差异化恰好落在这条定义线上。**

**5. 供应商自评与独立评测之间存在系统性落差，且大多数「学术 AI」产品根本没有同行评审的独立引文忠实度评测。**
- PaperQA2「超人类」= 只在 **precision** 上超人（85.2% vs 73.8%），在 **accuracy** 上人类略高（67.7% vs 66.0%）且置信区间重叠——这是本轮发现的最典型口径扭曲。
- Elicit 官方称抽取准确率 94–99%；独立研究（Lagisz et al., *Research Synthesis Methods*, 2026-05-29）在高精度模式下测到 value match 77%。
- scite 的 supporting/contrasting 分类，独立评测（Bakker et al. 2023）结论是「整体准确性低」，人工判为 42 条 supporting 的样本 scite 只判出 2 条。
- Undermind、Consensus、SciSpace：**没有找到任何同行评审的、针对「引文是否支持陈述」的独立评测**。只找到撤稿文献识别这一侧面维度（JMIR 2026-05-01），研究型工具在该维度全线 0/15。

**6. 元数据层的幻觉（引文根本不存在）在 2026 年仍未消失，但已不是主要矛盾。**
UPenn 团队（arXiv:2604.03173，2026-04-03）在 22 万条 URL 上测：深度研究产品的**不可解析率** 5–18.5%，其中真正「从未存在过」（Wayback 无任何快照）的 3.0–13.3%。GhostCite（arXiv:2602.06718v2）在纯生成场景（无检索）下测 13 个模型的引文幻觉率 14.23%–94.93%。**结论：URL/DOI 层的错误率是个位数到十几个百分点，语义支持层的错误率是 20–60 个百分点——后者比前者严重 3–5 倍，而现有产品几乎只监控前者。**

---

## 系统与机制逐条（含 URL）

### A. 测「陈述级支持」的关键研究（本项目的方法论母本）

#### A1. SourceCheckup — 医学领域，Nature Communications，58,000 对陈述-源
- URL（一手）：https://pmc.ncbi.nlm.nih.gov/articles/PMC12003634/
- 出处：Wu K, Wu E, Wei K, Zhang A, Casasola A, Nguyen T, Riantawan S, Shi P, Ho D, Zou J. *An automated framework for assessing how well LLMs cite relevant medical references.* Nature Communications 16:3615, 2025-04-16。
- **协议（这是我们要抄的部分）**：
  1. 800 个问题：400 条从 Mayo Clinic 参考文档生成 + 400 条来自 Reddit r/AskDocs（真实、脏、开放式）。这个「干净来源 vs 真实用户问题」的双样本设计是关键——同一模型在两者上的支持率差 50 个百分点。
  2. 用 GPT-4o 把回答**拆成独立医学陈述**；对每条陈述 × 每个被引源做支持判定；共约 58,000 对。
  3. **判定器验证**：3 名美国执业医生独立标注 400 对陈述-源；自动判定与医生共识一致率 **88.7%**，医生之间平均一致率 **86.1%**（即自动判定已接近人类之间的天花板），差异不显著（p=0.21）。另在 110 对 GPT-4o(RAG) 样本上独立验证，医生同意自动打分 **95.8%（91.8–98.7%）**。
  4. **合并源再判**：把某条陈述的全部被引源拼在一起重判，95.1% 仍不支持。
- 机制含义：**判定器可以做到接近人类间一致率，但前提是领域受限 + 判定单元是「一条陈述 × 一个源」的最小对，而不是「整篇报告」。**

#### A2. Cited but Not Verified — 三层拆分（链接/相关/事实），14 个 2026 前沿模型
- URL（一手）：https://arxiv.org/html/2605.06635v1
- 出处：Onweller H, Lumer E, Huber A, Ramchandani P, Subbiah VK, Feld C（PricewaterhouseCoopers, Commercial Technology and Innovation Office）。arXiv:2605.06635v1，2026-05-07。**预印本，未见同行评审。作者为产业实验室。**
- 协议：130 条 query（来自 DeepResearch Bench + BrowseComp）；**确定性 Markdown AST 解析器**抽取「引文-主张」对（不用 LLM，避免抽取器污染）；三个二元维度分别判定：
  - **Link Works**：HTTP 请求判可访问（确定性）
  - **Relevant Content**：LLM-as-a-judge，人工校准
  - **Fact Check**：拉取源内容后 LLM-as-a-judge 判事实是否被支持
- 机制含义：**「确定性抽取 + 分层判定 + 分层记分」正是本项目应采用的骨架**。用 AST 解析代替 LLM 解析，把不确定性只留在最后一层。

#### A3. DeepTRACE — 8 维社会技术审计，303 query × 9 系统
- URL（一手）：https://arxiv.org/abs/2509.04499 ；PDF 正文：https://r.jordan.im/download/language-models/venkit2025.pdf
- 出处：Venkit PN, Laban P, Zhou Y, Huang K-H, Mao Y, Wu C-S（Salesforce AI Research）。arXiv:2509.04499v1，2025-09-02。语料快照日期 **2025-08-27**。
- 协议：303 个问题（168 debate + 135 expertise）× 9 个系统 = 2,727 个样本；浏览器脚本抓取「query / 回答文本 / 内嵌引文 / 源 URL」四元组；LLM（GPT-5）把回答拆成陈述；用 Jina.ai Reader 抓源全文。
- **必须记住的三个削弱项**：
  1. 事实支持判定与人工标注的 **Pearson r = 0.62（作者自称 moderate）**，仅在 100 条任务上验证。这比 SourceCheckup 的一致率弱得多。作者自己写明这是框架的 limiting factor，之所以用是因为要跑 ~80,000 次判定，人工不可行。
  2. **约 15% 的 URL 因付费墙/404 抓不到全文，被直接排除**在支持率计算之外。真实支持率只会更低。
  3. 论文内部数字不自洽：正文写 Gemini(DR) citation accuracy「only 40.3%」，表 1 是 **50.3%**。（见下方核验表 corrected 条目。）
- 指标定义（可直接借用）：
  - *Citation Accuracy*：被声称的引文中，源内容确实支持该陈述的比例（citation 矩阵与 factual-support 矩阵的逐元素重合）。
  - *Unsupported Statements*：相关陈述中，不被**任何**列出的源支持的比例。
  - *Citation Thoroughness*：已写出的正确引文数 / 所有本可写出的正确引文数。
  - *Source Necessity*：用 Hopcroft-Karp 最小顶点覆盖算出「支撑全部相关陈述所必需的源」占列出源的比例。
  - 阈值表（作者定的可接受线）：Citation Accuracy ≥90 可接受、50–90 边缘、<50 有问题；Unsupported Statements <10 可接受、>25 有问题。

#### A4. 法律域：hallucination 的二维定义（correctness × groundedness）
- URL（一手）：https://onlinelibrary.wiley.com/doi/full/10.1111/jels.12413 （正文 HTTP 402；本地经 pdftotext 从公开 PDF 抽取正文核对）
- 出处：Magesh V, Surani F, Dahl M, Suzgun M, Manning CD, Ho DE. *Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools.* Journal of Empirical Legal Studies, 2025, 22(2):216–242（Stanford RegLab/HAI）。**评测执行完成于 2024-04**，之后 LexisNexis 已发布第二代产品，论文明确声明结果不代表第二代。
- 定义（原文抽取）：
  - *Correct*：事实正确且切题（部分正确也计为 correct）；*Incorrect*：含任何事实错误；*Refusal*：拒答或答非所问。
  - *Grounded*：关键事实命题对相关法律文书作出有效引用；*Ungrounded*：关键命题没有引用；***Misgrounded*：关键命题有引用，但源不支持该命题**（误读源或引用了不适用的源）。
  - **Hallucination ≡ incorrect **或** misgrounded**。correct-but-ungrounded 记为 *incomplete*，不算幻觉。
- 方法学质量（本轮所有研究中最高）：**预注册**（OSF）；202 条人工构造 query；三名标注者初标，第四名独立标注者在不接触初标的情况下重标 48 条分层抽样；**Cohen κ = 0.77，一致率 85.4%**；数据集公开于 huggingface.com/reglab，且**保留 50% 随机样本不公开**以防模型记忆污染。

### B. 元数据层幻觉（引文/URL 是否存在）

#### B1. UPenn：non-resolving vs hallucinated vs stale 的三分法
- URL（一手）：https://arxiv.org/html/2604.03173v1
- 出处：Rao D, Wong E, Callison-Burch C（University of Pennsylvania）。arXiv:2604.03173v1，2026-04-03。**预印本。**
- 定义（本项目应直接采纳）：
  - *Non-resolving*：HTTP 4xx/5xx、连接错误或超时（403 因反爬被排除）。
  - *Hallucinated*：non-resolving **且** Wayback Machine 在任何时间戳都无快照 → 该 URL 很可能从未存在。
  - *Stale*：non-resolving 但 Wayback 有快照 → 是真实的链接腐烂，不是捏造。
  - 关系式：Hallucinated = Non-resolving − Stale。
- 规模：DRBench 10 个模型 53,090 条 URL；ExpertQA 3 个模型 168,021 条 URL（32 个学科）。另用无头浏览器复核 600 条状态模糊的 URL。
- 修复实验：给模型一个 `urlhealth` 工具做自我纠错，435 个 ExpertQA 问题上 non-resolving 从 16.0%→0.6%（GPT-5.1）、4.9%→0.8%（claude-sonnet-4-5）、6.1%→0.1%（gemini-2.5-pro），p<10⁻³⁵。但小模型（gpt-5-nano）不会用反馈，无效。
- **对本项目的直接价值：URL 层的错误是可以用确定性工具 + 一次自我纠错循环压到 <1% 的。这一层不该再是我们的问题。**

#### B2. GhostCite：13 个模型 × 40 领域 × 375,440 条生成引文
- URL（一手）：https://arxiv.org/html/2602.06718v2 ；PDF：https://arxiv.org/pdf/2602.06718
- 出处：Xu Z 等（17 位作者）。arXiv:2602.06718v2 [cs.CR]，2026-05-14；IEEE S&P 2026 poster。**预印本。**
- 协议：要求模型按严格 JSON schema 输出领域参考文献（作者/标题/venue/年份/类型），批量大小 10/20/30，开/关联网检索，共 22,800 次 API 调用产出 375,440 条引文。
- 验证器 CiteVerifier 四级级联：本地缓存 → 学术库（DBLP、Google Scholar via ScrapingDog）→ 网络检索兜底 → LLM 重解析兜底；标题归一化后 Levenshtein 相似度阈值 θ=0.9。四级全过不了 = Invalid。
- 真实语料侧：8 个会议（NeurIPS/AAAI/ICML/IJCAI/USENIX/CCS/S&P/NDSS）2020–2025 共 56,381 篇论文、约 220 万条引文。区分 *Error citation*（元数据错）与 *Ghost citation*（穷尽人工检索也找不到）。

### C. 深度研究产品与生成式搜索的引文表现

#### C1. LiveResearchBench（Salesforce AI Research）
- URL（一手）：https://arxiv.org/html/2510.14240v5 ；OpenReview：https://openreview.net/pdf?id=ghwbZ3uhEd
- arXiv:2510.14240v5，最新版 2026-04-18。100 条专家策划 query，7 个领域、10 类任务，六阶段构造流水线（用户访谈 → 专家起草 → 前沿模型生成澄清问题 → 专家精修 → GPT-5 生成 checklist → 人工校验）。
- 引文相关的两个维度：*Citation Traceability*（未引用主张计数）与 *Citation Accuracy*（rubric 树：①识别 claim 与其源 URL ②URL 是否可访问 ③可访问则判内容是否充分支持）。三类错误 E1 无效 URL / E2 相关但无关联 URL / E3 不被支持的主张。
- 判定用 Gemini 2.5 Pro + GPT-5 双判取平均；人类一致率：Presentation 98.3%、Analysis Depth 92.5%、**Citation Traceability 85.9%**。
- 关键定性结论（原文）：在 wide information search 类任务上，**大部分错误来自「不被支持的主张」，而不是无效或不相关 URL**。与 A2 完全一致。

#### C2. Google AI Overviews 审计（Oumi，受 NYT 委托）
- URL：https://oumi.ai/blog/oumis-study-finds-50-of-ai-overviews （2026-04-14）
- **厂商自发布（Oumi 用自研 HallOumi++ 判定），代码与详细方法未公开** → 归为 vendor-reported。
- 协议：4,000+ 条 SimpleQA 难题；Patchright 浏览器自动化抓取 AI Overview 截图与引用链接；OCR 转文本；抓取被引源文本片段；GPT-5 判正确性，HallOumi++ 判支持性；抽样人工复核显示 0% 假阳、约 3% 假阴。
- 三个数字的口径差别极具教学价值：**91% 的概览包含正确答案 → 67% 的 claim 被引用源支持 → 只有 39% 同时「正确且全部被支持」**。同一批样本，三个口径，三个结论。

### D. 学术 AI 产品：引文如何与主张绑定 + 独立评测状况

| 产品 | 引文-主张绑定机制（一手描述） | 独立评测状况 |
|---|---|---|
| **PaperQA2**（FutureHouse） | RCS（Retrieval + Contextual Summarization）：对每个候选片段生成带相关性打分的上下文摘要，摘要 prompt 内含文献计量元数据（引用数、期刊质量估计），再挑最高质量摘要进入生成；答案引用具体片段。开源：https://github.com/Future-House/paper-qa | **仅有厂商自评**（arXiv:2409.13740，FutureHouse 自研自评，未见期刊版）。唯一的第三方对照来自竞品 Ai2：Nature 版 OpenScholar 正文称「PaperQA2 在 citation accuracy 上与 OpenScholar 持平甚至更优，但其回答常常只依赖一两篇论文」。 |
| **OpenScholar**（Ai2） | 4,500 万篇开放获取论文的检索库 → 专用 retriever → 自训 reranker → **推理期自反馈循环**（生成自然语言反馈 + 追加检索，多轮精修）。Ai2 官方明确：**没有显式的引文校验步骤**，是靠「只能引用实际检索到的片段」这一构造性约束抑制幻觉；官方也承认参数化知识仍可能产生不带链接的无支持引文。 | 论文经 **Nature 同行评审**（2026-02-04），但评测由厂商设计与执行（ScholarQABench 是 Ai2 自建）。citation accuracy 用 citation F1（recall + precision，沿用 ALCE 定义）。 |
| **Elicit** | 官方称「每一条抽取都由源文中的引文或图表支持」（https://elicit.com/solutions/systematic-review）。系统综述流程含检索 / 标题摘要筛选 / 全文抽取。 | **有独立评测**：Lagisz et al., *Research Synthesis Methods*, 2026-05-29（Cambridge FirstView）。另有多篇医学/环境科学领域的抽取一致性研究。见核验表。 |
| **Consensus** | 「Consensus Meter」按官方说法基于从论文结论中**抽取的原文句子**做分类，而非生成式摘要；对论文抽取 population/methods/results/outcomes/sample size 等字段（SMU 图书馆页描述）。 | **未找到同行评审的独立「引文是否支持陈述」评测**。侧面证据：撤稿文献识别 0/15（Labenbacher 2026）；MIT Tech Review 自测 18/21 撤稿论文被引用且不提示。 |
| **scite** | Smart Citations：用深度学习模型把引文语境分类为 supporting / mentioning / contrasting，并展示引用处的原文语境句。 | **有独立评测且结论负面**：Bakker, Theis-Mahon & Brown, *Hypothesis* 35(2), 2023。见核验表。 |
| **Undermind** | 自适应多步 Deep Search，声称阅读全文与图表并逐源引用（https://app.undermind.ai/）。 | **未找到任何独立准确性/引文忠实度评测**。仅有产品评述（Giustini D, PMC12352444, 2025）与图书馆评估页，均为定性。Katina Magazine（2024-11-12）明确写「尚无对 Undermind 相对人工筛选的正式基准测试」。 |
| **SciSpace** | 官方发布过自评基准（如「SciSpace vs Elicit vs Consensus：200 条复杂查询，3 个独立 AI 评审」，2026-06-08，https://scispace.com/resources/...）。 | **未找到同行评审的独立引文忠实度评测**。侧面证据：撤稿识别 0/15，且在主题概述中引用撤稿文献而不标注的比例最高（8/15）。厂商自评基准用「AI 评审」而非人工，且是自家发布，不可作为独立证据。 |

### E. 判定器与 claim 抽取本身的可靠性（本项目的隐藏风险面）

#### E1. ALCE：自动引文评测的祖师爷，以及一个极易被误引的数字
- URL（一手）：https://ar5iv.labs.arxiv.org/html/2305.14627 ；ACL Anthology：https://aclanthology.org/2023.emnlp-main.398/ ；代码：https://github.com/princeton-nlp/ALCE
- Gao T 等，EMNLP 2023。定义（本项目应直接采纳）：
  - *Citation Recall*：某条陈述至少有一个引文，且所有引文拼接后能蕴含该陈述 → 记 1，否则 0，在全部陈述上取平均。
  - *Citation Precision*：一个引文若 (a) 单独无法支持该陈述，**且** (b) 去掉它不影响其余引文能否支持该陈述，则记为 irrelevant。precision 只在该陈述 recall=1 时才计。**「必要性」是 precision 的核心，不是「相关性」。**
  - 判定器：TRUE（在多个 NLI 数据集上微调的 T5-11B）。

#### E2. Claimify（Microsoft Research）：claim 抽取器本身会造出源里没有的东西
- URL（一手）：https://aclanthology.org/2025.acl-long.348.pdf
- Metropolitansky D, Larson J，ACL 2025 Long Papers #348。
- 三维评测框架：*Entailment*（抽出的 claim 是否被源句蕴含）、*Coverage*（源中可核查内容被覆盖的比例）、*Decontextualization*（claim 脱离上下文后是否仍可核查）。
- **NLI 模型不可用**：作者先用 Nie et al. (2020) 的预训练 NLI 模型判蕴含，发现严重缺陷；改用 LLM prompt，在 80 条人工标注样本上，LLM 判定只与人工冲突 5 次，而 NLI 模型冲突 21/26 次（两种配置）。
- 对本项目最关键的一条：**「先抽 claim 再核查」这条流水线里，抽取阶段就已经在制造不被源支持的 claim**（DnD 方法 89.1% 蕴含率 = 约 11% 的 claim 本身就超出了源文）。任何 claim-graph 式设计都必须先过抽取自检门。

---

## 载荷数字核验表

> 状态定义：`verified` = 已读一手来源并可引原文；`corrected` = 常见流传版本口径有误，此处给出正确口径；`unverified` = 未能触达一手来源，不得洗成裸数字。
> 「口径三元组」= 指标 / 样本与条件 / 对比基准。

| # | 数字 | 口径三元组 | 状态 | 一手出处 |
|---|---|---|---|---|
| 1 | **50%–90%** | 指标：一条回答中存在≥1条不被其所引源支持的陈述（**response-level 未完全支持率**）／样本：800 个医学问题（400 Mayo Clinic + 400 Reddit r/AskDocs）、约 58,000 对陈述-源／对比：跨 7 个有完整结果的模型的**范围**，不是某一个模型的值 | verified | Wu et al., Nat Commun 16:3615 (2025-04-16)，https://pmc.ncbi.nlm.nih.gov/articles/PMC12003634/ |
| 2 | **55%** | 指标：GPT-4o(RAG) 的 response-level **完全**支持率（整条回答所有陈述都被支持）／样本：同上 800 题／对比：Gemini Ultra 1.0(RAG) 34.5%，其余模型更低 | verified | 同上 |
| 3 | **约 80% vs 约 30%** | 指标：GPT-4o(RAG) 的**陈述级**支持率／样本：Mayo Clinic 生成问题 vs Reddit r/AskDocs 真实问题／对比：同一模型、同一判定器，仅问题来源不同。数值为论文图 1b 读数，非表格精确值 | verified（图读数，近似） | 同上 |
| 4 | **95.1%** | 指标：原本不被支持的陈述，在把该陈述的**全部**被引源合并后仍不被支持的比例／样本：GPT-4o(RAG) 的不支持陈述子集／对比：无（是「补救无效」的证据） | verified | 同上 |
| 5 | **88.7% / 86.1%** | 指标：自动支持判定器与 3 名美国执业医生共识的一致率 / 医生之间的平均一致率／样本：400 对陈述-源／对比：判定器 vs 医生共识（p=0.21，无显著差异） | verified | 同上 |
| 6 | **94%+ / 80%+ / 39–77%** | 指标：单条引文的 Link Works（HTTP 可访问，确定性）／ Relevant Content（主题相关，LLM-judge）／ Fact Check（事实被源支持，LLM-judge）／样本：130 条 query（DeepResearch Bench + BrowseComp），14 个模型的深度研究报告，引文用确定性 Markdown AST 解析器抽取／对比：三层指标在**同一批引文**上的对照 | verified（arXiv 预印本，PwC 产业实验室） | Onweller et al., arXiv:2605.06635v1 (2026-05-07)，https://arxiv.org/html/2605.06635v1 |
| 7 | **Claude Opus 4.5: 98.7 / 95.7 / 76.8**；**GPT-5.4: 100.0 / 93.7 / 47.7**；**Gemini 3.1 Pro: 94.1 / 80.7 / 48.5** | 指标：同 #6 的三层（Link / Relevant / Fact Check），单位 %／样本：同 #6／对比：同表内各模型 | verified（同上，预印本） | 同上 |
| 8 | **78.6% → 16.7%** | 指标：GPT-5.4 的 Fact Check 通过率／样本：工具调用次数从 2 次提升到 150 次的消融实验／对比：**同一实验中 Link Works 与 Relevant Content 始终 >92%**。Claude Opus 4.6 同实验为 80.0%→57.9%；全体平均降幅约 42% | verified（同上，预印本） | 同上 |
| 9 | **40–80%** | 指标：Citation Accuracy（被写出的引文中，源确实支持该陈述的比例）／样本：303 个问题 × 9 个系统 = 2,727 样本，语料快照 2025-08-27／对比：跨系统的**范围** | verified | Venkit et al., arXiv:2509.04499v1 (2025-09-02)，https://arxiv.org/abs/2509.04499 |
| 10 | **GPT-5(DR) 12.5% / YouChat(DR) 74.6% / PPLX(DR) 97.5% / Copilot(TD) 90.2% / Gemini(DR) 53.6%** | 指标：%Unsupported Statements（相关陈述中不被任何列出源支持的比例）／样本：同 #9 的深度研究配置／对比：同表。生成式搜索（非 DR）配置为 23–47% | verified | 同上（本地 pdftotext 抽取表 1 原文核对） |
| 11 | **Gemini(DR) citation accuracy = 50.3%，不是 40.3%** | 指标：同 #9／样本：同 #9／对比：**论文自身表 1 与正文不一致**——正文写「only 40.3%」，表 1 为 50.3%。引用时必须注明以表 1 为准并标注该不一致 | **corrected** | 同上（表 1 vs §4 正文，逐字核对） |
| 12 | **Pearson r = 0.62** | 指标：DeepTRACE 的 LLM 事实支持判定与人工标注的相关系数（作者自评 moderate）／样本：2 名标注者、100 条事实核查任务／对比：同框架下置信度打分的 r=0.72（substantial）。另：约 15% 的源 URL 因付费墙/404 抓不到全文被**排除**在支持率计算外 | verified | 同上（§3.1.1） |
| 13 | **Lexis+ AI 17% / Westlaw AI-AR 33% / Ask Practical Law AI 18% / GPT-4 43%** | 指标：hallucination 率，定义为回答 **incorrect 或 misgrounded**（misgrounded = 关键命题有引用但源不支持）／样本：202 条预注册人工构造法律 query，**评测执行完成于 2024-04**／对比：四个系统横比 | verified | Magesh et al., JELS 2025;22(2):216–242，https://onlinelibrary.wiley.com/doi/full/10.1111/jels.12413 |
| 14 | **Lexis+ AI 65% / Westlaw 41% / Ask Practical Law 19%** | 指标：accurate（correct **且** grounded）的 query 占比／样本：同 #13／对比：同上。**注意论文内部不一致**：正文写 Westlaw 41%，图 1 题注写 42% | **corrected**（正文 41%，图注 42%，须并列注明） | 同上（§6 正文 vs 图 1 题注） |
| 15 | **18% / 25% / 62%** | 指标：incomplete 率（拒答，或 correct-but-ungrounded——按其定义**不算幻觉**）／样本：同 #13／对比：Lexis+ / Westlaw / Ask Practical Law。**这解释了为什么 Ask Practical Law 幻觉率低：它大量不作答** | verified | 同上 |
| 16 | **Cohen κ = 0.77，一致率 85.4%** | 指标：最终三分类标签（correct / incomplete / hallucinated）的评分者间信度／样本：第四名独立标注者在不接触初标的情况下重标 48 条分层抽样／对比：与 Dahl et al. 2024 同类法律任务可比 | verified | 同上（§5.4） |
| 17 | **85.2% ± 1.1 vs 73.8% ± 9.6（precision）**；**66.0% ± 1.2 vs 67.7% ± 11.9（accuracy）** | 指标：LitQA2 上 PaperQA2 vs 人类专家的 **precision**（作答题目中答对的比例，允许选「信息不足」而不计入）与 **accuracy**（全部题目中答对的比例，选「信息不足」计为错）／样本：248 道多选题，9 名 PhD/PhD 在读者，约一周，可用任意在线工具与机构订阅，$3–12/题／对比：agent vs 人类。**「超人类」只在 precision 上成立；accuracy 上人类均值更高且置信区间大幅重叠** | **corrected**（广泛流传的「PaperQA2 超越人类专家 85.2% vs 73.8%」把 precision 说成 accuracy 比较） | Skarlinski et al., arXiv:2409.13740，https://ar5iv.labs.arxiv.org/html/2409.13740 ；摘要原文见 https://huggingface.co/papers/2409.13740 |
| 18 | **2.34 ± 1.99 条/篇，其中 70% 被人工确认** | 指标：PaperQA2 在随机生物学论文中识别出的矛盾数（mean ± SD, N=93 篇）／样本：93 篇随机生物学论文／对比：无基线（不是「比人类多」的比较） | verified | 同上（摘要原文） |
| 19 | **78–90%** | 指标：GPT-4o **无检索**时生成的引文中「论文根本不存在」的比例（人工核对生成标题是否存在）／样本：ScholarQABench 子集／对比：与 OpenScholar 的 citation F1 对照。**注意：论文表 3 的分域值为 CS 78.7%、Biomedicine 94.8%，摘要写的 78–90% 区间与表内生物医学值不一致**，引用时应给分域值 | **corrected**（摘要区间与分域表不一致；生物医学域实测 94.8%） | Asai et al., *Nature* 650(8103):857–863 (2026-02-04)，https://pmc.ncbi.nlm.nih.gov/articles/PMC12935541/ ；预印本 arXiv:2411.14199 |
| 20 | **OpenScholar-8B 超 GPT-4o 6.1%、超 PaperQA2 5.5%** | 指标：correctness（**绝对百分点**，非相对提升）／样本：ScholarQABench 中的 ScholarQA-Multi 多文献综合任务（108 题）／对比：三系统横比。**厂商（Ai2）自建基准 + 自评，但论文经 Nature 同行评审** | verified（vendor-designed benchmark） | 同上 |
| 21 | **51% / 70%（win rate）** | 指标：专家在成对比较中偏好模型回答而非专家撰写回答的比例／样本：ScholarQA-Multi 的 108 条问答对，16 名专家标注者，约 500 次细粒度评估／对比：OS-8B 50.8% / OS-GPT4o 70.0% / GPT-4o 单独 31.9%。**「偏好」不等于「引文更忠实」**，论文归因主要是覆盖广度与深度 | verified（vendor 自评） | 同上 |
| 22 | **「PaperQA2 在 citation accuracy 上与 OpenScholar 持平甚至更优」** | 指标：citation F1／样本：ScholarQABench／对比：竞品对手方（Ai2）在自家 Nature 论文正文中承认——因此这是**对 PaperQA2 有利的对手方陈述**，证据力强于厂商自评 | verified | 同上（Nature 版正文） |
| 23 | **14.23% – 94.93%** | 指标：生成引文被判 Invalid（四级级联检索 DBLP/Google Scholar/网络/LLM 重解析后仍找不到，标题 Levenshtein 相似度阈值 0.9）的比例／样本：13 个 LLM × 40 个 arXiv CS 领域 × 375,440 条引文（22,800 次 API 调用）／对比：最低 DeepSeek 14.23%，最高 Hunyuan-A13B 94.93%，约 6.7 倍差距。中位区间：GPT-5 50.92%、Gemini-2.5-Pro 59.47%、Claude-Sonnet-4 21.84% | verified（arXiv 预印本） | Xu et al., arXiv:2602.06718v2 (2026-05-14)，https://arxiv.org/html/2602.06718v2 |
| 24 | **1.07%** | 指标：**含至少一条无效引文的论文**占比（604 / 56,381 篇），**分母是论文不是引文**／样本：8 个会议 2020–2025 共 56,381 篇、约 220 万条引文／对比：无效引文绝对数 739 条（136 条元数据错 + 603 条 ghost）。**常见误引把它说成「1.07% 的引文无效」——实际引文级比例约 0.034%** | **corrected** | 同上 |
| 25 | **+80.9%（0.89% → 1.61%）** | 指标：含无效引文的论文占比的**相对增幅**／样本：2025 年 vs 2020–2024 年均值，同一 8 会议语料／对比：年度间纵比 | verified | 同上 |
| 26 | **非解析率 5.4–18.5%；幻觉率 3.0–13.3%** | 指标：*non-resolving*（HTTP 4xx/5xx/超时，403 排除）与 *hallucinated*（non-resolving **且** Wayback 无任何快照）／样本：DRBench 10 个模型 53,090 条 URL／对比：gemini-2.5-pro-deepresearch 18.5%/13.3%；openai-deepresearch 10.1%/3.5%；claude-3-7-sonnet-with-search 8.5%/3.2%；claude-3-5-sonnet-with-search 7.8%/3.0% | verified（arXiv 预印本） | Rao, Wong & Callison-Burch, arXiv:2604.03173v1 (2026-04-03)，https://arxiv.org/html/2604.03173v1 |
| 27 | **16.0% → 0.6%（26×）** | 指标：GPT-5.1 的 non-resolving URL 率，在给予 `urlhealth` 自检工具做智能体自纠错前后／样本：435 个 ExpertQA 问题／对比：claude-sonnet-4-5 4.9%→0.8%（6.4×）、gemini-2.5-pro 6.1%→0.1%（79×），均 p<10⁻³⁵。**小模型（gpt-5-nano）无法利用反馈** | verified（同上，预印本） | 同上 |
| 28 | **91% / 67% / 39%** | 指标：①概览包含正确答案的比例 ②claim 被其引用源支持的比例 ③**同时**正确且全部被支持的概览比例／样本：4,000+ 条 SimpleQA 难题的 Google AI Overviews，2025 末–2026 初采集，浏览器自动化 + OCR + 源抓取，GPT-5 判正确性、HallOumi++ 判支持性／对比：同一批样本的三个口径 | **vendor-reported**（Oumi 自研判定器、自发布、方法与代码未公开；受 NYT 委托） | https://oumi.ai/blog/oumis-study-finds-50-of-ai-overviews (2026-04-14) |
| 29 | **Citation Association：Deerflow+ 77.0 / Open Deep Research 76.9 / Gemini DR 52.1 / Perplexity Sonar DR 36.6 / OpenAI o3 DR 25.6** | 指标：LiveResearchBench 的 Citation Association 分（0–100 rubric 树复合分，非百分比支持率）／样本：100 条专家 query／对比：同表各系统。**不能当作「支持率」引用** | verified | Wang et al., arXiv:2510.14240v5 (2026-04-18)，https://arxiv.org/html/2510.14240v5 |
| 30 | 「Open Deep Research 平均每篇报告 91.9 个错误」 | 指标：未能在正文中定位到该数字与其定义／样本：—／对比：— | **unverified**（仅见于检索引擎摘要，正文未核到；**不得使用**） | — |
| 31 | **85.1% / 77.6%** | 指标：**自动引文判定器与人工标注的一致率**（citation recall / citation precision 两个判定各自的一致率），**不是模型的引文质量分**／样本：100 条 ASQA + ELI5 抽样，判定器为 TRUE（T5-11B NLI）／对比：人工标注为金标准。**极易被误引为「LLM 引文准确率 85%」** | **corrected** | Gao et al., EMNLP 2023，https://ar5iv.labs.arxiv.org/html/2305.14627 |
| 32 | **ASQA 84.8/81.6；ELI5 69.3/67.8；QAMPARI 22.9/24.9** | 指标：citation recall / citation precision（precision 的核心是「必要性」：去掉该引文是否影响其余引文的支持力）／样本：ALCE 三个数据集，最佳配置 ChatGPT + Rerank／对比：数据集间横比。**长尾/开放式问答（ELI5）与多答案问答（QAMPARI）显著更差** | verified | 同上 |
| 33 | **Claimify 99.0% / VeriScore 99.2% / SAFE 96.6% / DnD 89.1%** | 指标：抽取出的 claim 被「源句 + 上下文 + 问题」蕴含的比例／样本：73,229 条去重 claim；判定用经验证的 LLM prompt（80 条人工样本上仅 5 次冲突，而 NLI 模型冲突 21/26 次）／对比：四种 claim 抽取方法横比。**约 11% 的 DnD claim 本身就超出源文所述** | verified | Metropolitansky & Larson, ACL 2025 Long #348，https://aclanthology.org/2025.acl-long.348.pdf |
| 34 | **句级覆盖准确率 91.8%；元素级 87.9%** | 指标：Claimify 判断「该句是否含可核查事实」的准确率 / 元素级覆盖准确率／样本：人工标注研究为金标准；63% 的句子被标为含事实主张；元素级分析覆盖 81% 标签一致的句子／对比：DnD 76.9%、VeriScore 宏 F1 62.5% | verified | 同上 |
| 35 | **19.9%（35/176）** | 指标：完全捏造引文（穷尽 Google Scholar/Scopus/PubMed/WorldCat/出版社库人工检索仍无对应文献）占比／样本：GPT-4o 生成的 6 篇心理健康综述（各约 2000 词）共 176 条引文，3 种疾病 × 2 种专精程度／对比：主题分层——重性抑郁 6.0%(4/68)、暴食障碍 28.0%(17/60)、躯体变形障碍 29.0%(14/48)；泛综述 16.7% vs 专精综述 24.3% | verified | Linardon et al., JMIR Mental Health, 2025-11-12，https://pmc.ncbi.nlm.nih.gov/articles/PMC12658395/ |
| 36 | **45.4%（64/141）** | 指标：**非捏造**引文中含著录错误的比例（作者/年份/标题/期刊/卷/期/页/DOI 任一有误）／样本：同 #35 的 141 条真实引文／对比：DOI 错 37.8%(51/135)、年份错 23.4%(33/141)、作者错 14.9%(21/141)。**综合：176 条中只有 77 条（43.8%）完全正确** | verified | 同上 |
| 37 | **77% / 10% / 0%** | 指标：Elicit 高精度模式的 value match / quote match / reasoning match。**关键更正：quote match 与 reasoning match 衡量的是「跨重复运行的一致性（可复现性）」，不是「引文是否忠实于原文」**；value match 才是与人工金标准的正确性比对／样本：7 个生命科学与环境科学系统综述，每个 8 篇调 prompt + 8 篇测试，共 90 条 prompt／对比：标准模式 quote match 46%、reasoning match 30%，重复抽取的值一致率 90% | **corrected**（二手常把「quote match 10%」转述成「只有 10% 的引文能对上原文」） | Lagisz et al., *Research Synthesis Methods*, FirstView, 2026-05-29，https://www.cambridge.org/core/journals/research-synthesis-methods/article/.../C97DAEC70C3173A260F0B12E729E7250 ；预印本 https://ecoevorxiv.org/repository/view/9909/ |
| 38 | **94%（内部）/ 99.4%（VDI/VDE）；筛选 recall 93.6%、specificity 62.8%** | 指标：Elicit 抽取准确率与筛选表现／样本：内部 128 条人工金标准（由 LLM 评判 Elicit 输出 vs 金标准+全文）；筛选样本由 58 篇已发表系统综述构造（正例=综述纳入文献，负例由 Consensus 检索 + LLM 过滤生成）／对比：厂商自设。**未披露：金标准是否双人校验、逐字段准确率、评审者身份、置信区间、评测代码与数据** | **vendor-reported** | https://elicit.com/blog/how-we-evaluated-elicit-systematic-review (2025-03-18) |
| 39 | Elicit「recall 96.89% / specificity 92.54% / accuracy 93.21%」 | 指标：系统综述筛选表现／样本：未核实／对比：未核实 | **unverified**（仅见检索摘要，未取一手页面） | https://elicit.com/blog/evaluating-elicit-slr (2026-05-06)，未 fetch |
| 40 | **scite：人工判 42 supporting / 39 mentioning / 17 contrasting，scite 判 2 supporting / 96 mentioning** | 指标：Smart Citation 分类的召回/精确/F 值／样本：324 条引用中被 scite 分类的 98 条，来源为「引用了撤稿论文的系统综述」（**非随机、领域特殊**）／对比：作者独立判定为金标准；F 值域 0.0–0.58。作者结论原文：整体准确性低，scite 更难分辨 supporting 与 contrasting，倾向于全部标成 mentioning | verified | Bakker C, Theis-Mahon N, Brown SJ, *Hypothesis* 35(2), 2023，https://journals.indianapolis.iu.edu/index.php/hypothesis/article/view/26528 |
| 41 | **ChatGPT-5 53.3% / Claude 46.7% / Gemini 40% / ChatGPT-4 40% / Perplexity 33.3% / Copilot 26.7% / SciSpace 0% / ScienceOS 0% / Consensus 0%** | 指标：5 个撤稿相关问题全部答对（5/5）的文献数占比／样本：9 个工具 × 15 篇撤稿论文（10 篇高被引 + 5 篇最新，截至 2025-05-23）× 5 问 × 2 次 = 675 条 prompt；两名独立评分者 Cohen κ=0.73／对比：通用工具中位 40%，研究型工具 0% | verified | Labenbacher et al., *J Med Internet Res* 2026-05-01，https://pmc.ncbi.nlm.nih.gov/articles/13134821 |
| 42 | **SciSpace 8/15、Claude 6/15、Perplexity 6/15、ScienceOS 6/15、Consensus 6/15、ChatGPT-4/5 3/15、Copilot 2/15** | 指标：在主题概述中引用撤稿文献**且未作任何提示**的文献数／样本：同 #41 的 15 篇撤稿论文／对比：同表 | verified | 同上 |
| 43 | **Elicit 5/21、Perplexity 11/21、Ai2 ScholarQA 17/21、Consensus 18/21** | 指标：在回答中引用撤稿论文且不提示撤稿的篇数／样本：Weikuan Gu 团队（University of Tennessee, Memphis）整理的 21 篇撤稿医学影像论文，MIT Technology Review 于 2025-06 自测／对比：2025-08 复测时 Consensus 降至 5/21。**媒体自测，非同行评审** | **media-selftest**（非同行评审，但方法与分母公开） | https://www.technologyreview.com/2025/09/23/1123897/ai-models-are-using-material-from-retracted-scientific-papers/ (2025-09-23) |
| 44 | ChatGPT 生成医学内容「47% 捏造 / 46% 真实但有误 / 7% 完全正确」 | 指标：引文三分类占比／样本：ChatGPT（**GPT-3.5 时代，2023-05 前后**）生成的医学内容／对比：无 | **unverified**（仅二手转述，未取到一手论文；且模型代际过旧，**不可作为 2026 基线**） | 二手：https://www.mdpi.com/2306-5729/11/5/122 转引 |
| 45 | 通用 LLM 在法律查询上幻觉 58%–88% | 指标：幻觉率／样本：Dahl et al. 2024 的法律问答集，模型为 GPT-3.5/PaLM/Llama 2 世代／对比：跨模型范围 | **unverified**（未取一手；模型代际为 2023–2024，**引用时必须标注代际**） | 二手：Stanford HAI 新闻页转引 |
| 46 | **Aljamaan RHS 中位数：ChatGPT-3.5 = 11、Bing = 11、Perplexity = 7、SciSpace = 1、Elicit = 1；Bard 500 条全部生成失败** | 指标：Reference Hallucination Score（满分 11 = 完全幻觉；标题/期刊/作者/DOI 各 2 分为主要错误，日期/链接/与关键词相关性各 1 分为次要错误）／样本：6 个工具 × 10 条医学 prompt × 10 条引用 = 每工具 500 条引用；PubMed DOI 优先核验，辅以标题+作者+Google Scholar；人工核验／对比：工具横比。**测量时间 2024 上半年，ChatGPT-3.5 代际** | verified（**但「SciSpace 629 / Elicit 597 条正确标识符」的分母存疑——大于 500，疑为字段级计数而非引用级，此子项标 unverified**） | Aljamaan et al., *JMIR Med Inform*, 2024-07-31，https://pmc.ncbi.nlm.nih.gov/articles/PMC11325115/ |

---

## 对本项目的设计含义

### D1. 把「引文核验」拆成三个**独立记分、独立门限**的层级，而不是一个 verified 布尔值
证据链：#6/#7（94% 链接有效 → 80% 相关 → 39–77% 支持）、#26（URL 层错误 3–13%）、#29（LiveResearchBench 明确说错误主要来自「不被支持的主张」而非坏链接）。

推论（我方推断，非来源陈述）：本项目的 claim 状态机至少要有三个正交轴：
- **L0 存在性**（确定性）：DOI/URL 可解析；Crossref/OpenAlex/S2/DBLP 元数据比对；Wayback 三分类（hallucinated / stale / live，采纳 #26 的定义）。
- **L1 定位性**（确定性）：被引用的**具体文字**能在源全文中精确子串匹配到（或经归一化后匹配）。这是 L0 与 L2 之间被所有现有系统跳过的一层。
- **L2 支持性**（可判但不确定）：源文的这段文字是否真的蕴含该 claim。

**只有 L0 和 L1 可以做硬门（确定性、可重跑）。L2 必须以「多判定器 + 分歧即降级」的方式产出，且分歧率本身要作为产品指标暴露出来。**

### D2. 判定器的可靠性上限是我们的产品上限——必须按「一条陈述 × 一个源」的最小对来判，且必须领域内校准
证据链：#5（SourceCheckup 在医学域达到 88.7% 一致率，接近医生间 86.1% 的天花板，判定单元是最小对）对比 #12（DeepTRACE 在开放域只有 r=0.62，判定单元是「陈述 vs 全部源」）；#33（NLI 模型在 claim 蕴含判定上不可用，LLM prompt 才行）。

推论：不要复用通用 NLI 模型做 L2。判定 prompt 必须在本项目自己的领域样本上做一次小规模人工校准（SourceCheckup 用 400 对 / Claimify 用 80 条 / DeepTRACE 用 100 条——**100 量级就足以给出可报告的一致率**），并把该一致率写进产品输出的元数据里。「我们的 verified 标签在 N 条人工样本上与人类一致率为 X%」本身就是可交付的信任凭证。

### D3. claim 抽取器是第一个误差源，必须自带蕴含自检门
证据链：#33（DnD 抽取的 claim 只有 89.1% 被源句蕴含）、#34（句级判「是否含可核查事实」的准确率最好也只有 91.8%）。

推论：流水线顺序应为「抽取 → **蕴含自检（claim ⊑ 原句）** → 核验」。抽取阶段就漏掉的可核查内容（coverage）和抽取阶段就编造的内容（entailment）都要单独计数并报出。**前代项目「claim-graph 框架失败」的一个可能的具体机制就在这里：框架假设 claim 抽取是无损的预处理，实际它是最大的单点误差源。**

### D4. 深度/并行度必须与「每条 claim 的证据预算」解耦——这是对 hyper-parallel 架构的直接约束
证据链：#8（GPT-5.4 从 2 次工具调用到 150 次，事实核查通过率 78.6%→16.7%，而链接与相关性指标纹丝不动）、#10（DeepTRACE：PPLX(DR) 列 7.7 个源、生成 30.1 条陈述，不支持率 97.5%；GPT-5(DR) 列 18.3 个源、141.6 条陈述、每陈述 1.4 个引文，不支持率仅 12.5%）。

推论：**「每条陈述的引文数」是比「检索了多少源」更强的忠实度预测量**。本项目的 loop 应该在「每条 claim 至少绑定 k 个已定位的证据片段」上设 gate，而不是在「检索轮数」或「并行子代理数」上设 gate。规模化的方向应是「更多 claim 各自被独立核验」，而不是「一个报告读更多源」。#8 是本轮最强的反直觉证据，且**它恰好只能通过分层指标看到**——这本身就是我们要卖的东西。

### D5. 「多引几个源」不是补救措施，缺证据就必须降级为 unverified
证据链：#4（合并全部被引源后 95.1% 仍不被支持）。

推论：keep-if-better 循环里，若某条 claim 在 L2 判为不支持，正确动作是「换检索策略重找证据」或「把 claim 拆细/弱化」，而不是「补引文」。补引文只会提高 citation thoroughness 这类表层指标，不改变支持率。

### D6. 允许 abstain，并且**必须同时报 precision 与 accuracy**
证据链：#17（PaperQA2 的「超人类」只在允许弃答的 precision 上成立；accuracy 上人类 67.7% ≥ agent 66.0%）、#15（Ask Practical Law AI 幻觉率低是因为 62% 的问题它不作答）。

推论：本项目的报告级指标必须成对出现：`已核验 claim 的正确率（precision）` 与 `全部 claim 中被核验且正确的比例（accuracy/coverage）`。**只报其一就是我们自己在做本轮所批判的口径扭曲。** 这一条应该写进 gate 脚本，让单指标报告直接构建失败。

### D7. 撤稿/更正状态是独立的第四个门，且是现有产品最薄弱的一环
证据链：#41（研究型工具 SciSpace/ScienceOS/Consensus 全对率 0/15）、#42（SciSpace 8/15 引用撤稿文献不提示）、#43（MIT Tech Review 自测 Consensus 18/21）。

推论：接 Retraction Watch / Crossref 的 `update-to` 关系做确定性检查，成本极低而竞品全线失守——这是一个可以立刻拿下的差异化点。注意 #43 的后续：Consensus 在两个月内从 18/21 改善到 5/21，说明这个能力是可修的，**先发优势窗口有限，且该数字会快速过期（2025-06/2025-08 快照）**。

### D8. 借用现成的、经同行评审的指标定义，不要自造
- Citation recall / precision 的定义直接用 ALCE（#31/#32），特别是 precision 的「**必要性**」判据：去掉这个引文是否影响其余引文对该陈述的支持力。这比「相关性」严格得多，且能直接惩罚「撒引文」行为。
- hallucination 的二维分解直接用 Magesh（correctness × groundedness，#13），并保留 `misgrounded` 这个词——它精确命名了本项目要解决的问题。
- URL 三分类直接用 UPenn 的 hallucinated / stale / live（#26），避免把链接腐烂误判为捏造。
- Source Necessity（最小顶点覆盖，DeepTRACE）是一个便宜且不易作弊的反「源堆砌」指标。

### D9. 一次 `urlhealth` 式自纠错循环就能把 L0 压到 <1%，应作为默认基线而非卖点
证据链：#27（26×–79× 的降幅，p<10⁻³⁵，但小模型无法利用反馈）。

推论：L0 层不该消耗产品的差异化叙事。把它做成默认的、必过的确定性前置门，然后把所有叙事重量压在 L1/L2 上。同时注意该证据也说明：**执行核验的子代理不能用太小的模型**——工具使用能力不足会让整个自纠错循环失效。

### D10. 「干净问题 vs 真实问题」的双样本设计应写进我们的评测集
证据链：#3（同一模型同一判定器，Mayo Clinic 生成问题支持率约 80%，Reddit 真实问题约 30%，差 50 个百分点）。

推论：任何只在「从文档反向生成的问题」上评测的系统都会系统性高估自己。本项目的自测集必须含一半来自真实、脏、开放式的用户问题，并**分开报数**。

---

## 未决与风险

### R1. 2026 年最相关的三篇证据都是未经同行评审的 arXiv 预印本
#6/#7/#8（PwC，2605.06635）、#23/#24（GhostCite，2602.06718）、#26/#27（UPenn，2604.03173）。其中 PwC 那篇是本维度的核心论据（三层拆分 + 深度消融），却出自产业实验室、无同行评审、且其测试的模型版本（GPT-5.2/5.4、Claude Opus 4.5/4.6、Gemini 3.1 Pro）在几个月内就会过时。**风险：把产品定位建立在一篇预印本的核心数字上。缓解：把「分层测量」这个方法论当作论据（它被 LiveResearchBench #29 和 DeepTRACE 独立复现），而不是把 39–77% 这个具体区间当论据。**

### R2. 不同研究的 "unsupported" 互不可比，横向拼图是危险的
DeepTRACE 的 PPLX(DR) 97.5% 不支持率（分母：相关陈述；判定：GPT-5，r=0.62；排除 15% 抓不到的源）与 PwC 的 39–77% fact-check 通过率（分母：引文-主张对）与 SourceCheckup 的 50–90%（分母：整条回答）**是三件不同的事**。任何把它们并列成「业界不支持率 30%–97%」的表述都是本项目要批判的行为。**本文件的核验表刻意把三元组写全，就是为了让下游文档无法在不注明口径的情况下引用。**

### R3. 判定器与被判系统同源导致的循环论证
DeepTRACE 用 GPT-5 判 GPT-5(DR) 的输出，后者在所有维度上都是最优；LiveResearchBench 用 Gemini 2.5 Pro + GPT-5 双判，被判系统里也有它们。**未见任何研究系统性地测量「自家模型判自家输出」的偏差幅度。** 本项目必须做跨厂商判定（至少两家不同供应商的模型，分歧即降级），并把这个设计本身作为可验证的方法学声明。

### R4. 付费墙与全文获取是核验的物理瓶颈，且会系统性地抬高观测到的支持率
DeepTRACE 明确排除了约 15% 抓不到全文的源（#12）。同理，L1 精确子串匹配对付费墙论文根本无法执行。**风险：我们的 verified 覆盖率会在开放获取比例低的学科（医学临床、法学、部分社科）急剧下降，而这些恰是错误代价最高的学科。** 未解决：是否接受「仅摘要级核验」作为一个独立的、明确降级的状态。

### R5. 时效性与代际混淆
本文件中 #44（47% 捏造，GPT-3.5 时代）、#45（58–88%，2023–2024 代际）、#46（RHS，2024 上半年）、#13/#14（法律工具，**测于 2024-04**，LexisNexis 已出第二代）都会被下游当成「当前基线」误用。**缓解：任何引用这些数字的下游文档必须携带模型代际或测量日期。建议在本项目的 gate 脚本里对「无日期的外部数字」直接报错。**

### R6. 中文与非英文文献的核验基础设施基线缺失
本轮所有研究的核验源均为 DBLP / Crossref / PubMed / Semantic Scholar / Google Scholar，语料以英文为主（GhostCite 是 arXiv CS，SourceCheckup 是英文医学，Magesh 是美国法）。**未找到任何针对中文学术文献（CNKI/万方/维普）引文幻觉率或核验可行性的实证研究。** 若本项目要覆盖中文文献，L0/L1 的可行性是完全未知的空白。

### R7. 三家产品（Undermind / Consensus / SciSpace）缺乏任何独立引文忠实度评测
只找到侧面维度（撤稿识别、产品评述、图书馆定性评估）。**这既是风险也是机会**：机会在于我们可以做第一份可重跑的独立评测；风险在于我们无法用「比 X 好多少」来定位——只能用绝对指标 + 公开的核验脚本。

### R8. 判定「支持」本身在概念上不是二元的
Magesh 在局限性中承认 groundedness 存在光谱（例如引用了被推翻但仍有起点价值的判例，他们计为 misgrounded）。已有 2026 年的工作在提出超越二元 supported/unsupported 的分类法（Sarkar A, *From Binary Groundedness to Support Relations*，https://advait.org/files/sarkar_2026_groundedness_taxonomy.pdf——**本轮未取一手核验，仅记录线索**）。**未决：本项目的 verified/unverified 二元状态是否需要第三态（partial / context-dependent）。二元是产品简洁性的来源，也可能是可攻击点。**

### R9. 本轮未覆盖但相邻的空白
- 逐字引语（verbatim quote）的伪造率：只找到线索（arXiv:2601.15476 提出 FCR/FFR 指标；analemma.ai 的 quote-backed citation verification 称「quote validity 是主要瓶颈」），**均未取一手核验**。L1 定位性这一层的业界基线因此仍然空白——这既可能意味着机会，也可能意味着我们低估了难度。
- 判定成本：DeepTRACE 跑了约 80,000 次支持判定；本项目在 hyper-parallel 下的判定调用量级与成本未估算。
- 对抗性场景：现有全部研究都是良性输入，没有测「源页面本身含误导内容」或「被引论文已被更正」时的表现。
