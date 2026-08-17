# 外部调研 v2 · 维度：研究 agent 输出质量的评测方法与 LLM-judge 可靠性

调研日期：2026-08-17。所有可失效数字均标注 `as_of`。
方法纪律：每个载荷数字先取一手来源（论文 abstract/HTML/官方仓库/官方 PDF），记录口径三元组（测什么 / 在什么样本或档位上 / 与什么比），再判 `verified | corrected | unverified`。博客二手数字一律不进结论层，只作为"被证伪/待证"记录。

---

## 结论摘要

**1. 这个领域已经有成型的"报告级"评测范式，但它的公信力比宣传的弱一档。**
DeepResearch Bench（100 题 / 22 域，源自 96,147 条真实用户 query）与 ResearchRubrics（101 题 / 2,593 条 rubric / 9 域）是当前两个直接对"研究报告"打分的基准。二者都不是纯专家写 rubric：DeepResearch Bench 的评分标准由 LLM **按任务动态生成**（专家只出题），ResearchRubrics 的 rubric 由"有很强 STEM 背景但不一定是该领域专家"的人写。真正做到"逐条专家手写 rubric"的只有 HealthBench（262 名医生、48,562 条 criteria），那是工业实验室级投入。**结论：对我们这种个人/小队规模，"专家写 rubric"不可复制；可复制的是"专家出题 + 机器判定 + 分歧升级到人"。**

**2. LLM-judge 的可靠性数字被系统性高报，根因是报了 raw agreement 而不是 chance-corrected。**
这是本轮最硬的一手发现（Norman et al., arXiv:2606.19544v1, 2026-06-17，21 个 judge / 9 家厂商 / ~541,000 次判定）：在 MT-Bench 上 exact-match 一致率 0.788–0.851，对应的 Cohen κ 只有 0.376–0.511；**raw agreement 平均虚高 38.6 个百分点（区间 33.8–41.3 pp）**。作者原话式结论：一个宣称"85% agreement"的 judge，其 κ≈0.48。同一篇提出 **consistency–bias paradox**：test-retest ≥0.95 的 judge 可以同时有 >0.10 的位置偏置——"高度可复现但无效"。**结论：judge 上线门槛必须写成 κ 阈值，不能写成 accuracy 阈值。**

**3. 广为流传的 judge 偏置数量级（"verbosity bias 15–30 点""position bias 10–15 点""22–30% 判定翻转"）在一手大规模测量里对不上。**
同一篇 2606.19544 在 bias-audit 协议下测得：position bias 从 0.002（Gemini 2.5 Pro）到 0.192（Qwen 3 8B），跨两个数量级；**verbosity bias 全部 21 个 judge 均 <0.011，其中 17 个 <0.005**。这与营销博客反复复述的"15–30 点"直接冲突。这些博客（futureagi.com、ai-tldr.dev 等）互相引用、无一手出处，是典型的**虚假独立佐证**（多页面复述同一上游 = 一个来源）。**结论：偏置必须自己在自己的 judge 上测，不能引用行业"公认数量级"。**

**4. judge 在难题上确实会塌。** 2606.19544：test-retest 从 MT-Bench 的 0.943 掉到 JudgeBench 的 0.911，16 个 judge 里 7 个的位置翻转率退化 ≥1.5×（但 Claude Opus 4.6 与 Gemini 3.1 Pro 反而在难集上更好——不是单调规律）。短答自动评分的 IRT 研究（arXiv:2605.00238）显示 judge 准确率随难度**单调下降**，最难难度箱上多数模型跌到 2.1%–16.6%。**结论：分数必须按难度分箱报，hard 箱强制人裁抽检。**

**5. 引用核验是这个项目的命门，而且没有模型做得好。**
一手证据链：
- SourceCheckup（Nature Communications, 2025-04-16，800 题 / ~58,000 条 statement–source 对）：**50%–90% 的 LLM 回答"未被其所引来源完全支持"**；但同一篇里 GPT-4o+web search 的**语句级**未支持率只有约 30%——因为"完全支持"是回答级全有全无判定，一条语句坏就整条回答坏。这是本轮最典型的口径陷阱。
- Cited but Not Verified（arXiv:2605.06635, 2026-05-07，14 个 LLM）：链接可达 >94%、相关性 >80%、但**事实支持只有 39%–77%**；且随工具调用从 2 次涨到 150 次，事实支持准确率**相对下降约 42%**（两个前沿模型的平均，不是 42 个百分点）。
- Do You Need a Frontier Model as a Citation Verifier?（arXiv:2607.08700, 2026-07-09，624 对 = 1,248 条 rubric 决策）：**"来源相关性"这一维便宜模型就够**（GPT-5-mini F1=0.908，最好且最便宜之一）；**"事实支持"这一维所有模型置信区间重叠、统计上不可区分**，最好只有 Claude Opus 4.6 的 F1=0.750。judge 成本跨度 49×，**成本不预测准确率**。
- CiteME（arXiv:2407.12861）：LLM 找出被引论文的准确率仅 4.2%–18.5%，CiteAgent（GPT-4o）35.3%，人类 69.7%（2024 年模型，已陈旧）。
**结论：引用链路必须拆成"可确定判定的部分"（链接活、逐字引文命中）与"判定不可靠的部分"（引文是否真支持该断言）。后者不能全托给 judge。**

**6. 抗污染靠数据纪律，不靠技术花招——而本项目还多一层"搜索期污染"风险。**
canary string 已被证伪（GPT-4 会复现 BIG-bench canary，2024-07/10 公开记录）；n-gram / 改写去污在规模化下被击穿（arXiv:2605.19999v1, 2026-05-19 明确指出词面混淆与 n-gram 过滤失效）。有效的是三件事：私有保留集（GSM1k / HLE 私有子集模板）、时间锚定轮换（LiveCodeBench 用发布日期切窗，对 DeepSeek 只在截止日后的 349 题上评）、超差即退役换新。
**但对会上网的 agent，还有 Search-Time Contamination（arXiv:2508.13180v1, 2025-08-12）**：agent 自己把评测集搜出来。实测 HLE 约 3.3–3.44%、GPQA 1.90–4.15%、SimpleQA 0.99–1.20% 的样本被检索到评测集本体；**SimpleQA 上被污染样本准确率 100%，未污染样本仅约 7%**；屏蔽 HuggingFace 后被污染子集准确率掉约 15%。这条对我们是致命的——只要 held-out 题面进了 git / artifact / 博客，评测就死了。

**7. 能力指标必须配完整性指标，且这件事要写进主指标而不是旁挂。**
Why Language Models Hallucinate（arXiv:2509.04664, 2025-09-04）的核心主张：0-1 计分**惩罚弃权**，"模型被优化成好考生，不确定时猜测能提分"；作者的建议不是加一个 hallucination 专项评测，而是**改主流评测的计分**（对自信错误的惩罚重于承认不确定）。HealthBench 也做了配对设计：既报总分，也单独切出 HealthBench Hard（1,000 题，最好模型 o3 仅 0.32）与 Consensus 子集（3,671 例 / 34 条共识 criteria）。

---

## 逐条发现（含 URL）

### A. 给"研究报告"打分的基准及其 rubric 方法学

**A1. DeepResearch Bench**（arXiv:2506.11763，提交 2025-06-13；仓库 as_of 2026-05-11）
- https://arxiv.org/abs/2506.11763 ｜ https://github.com/Ayanami0730/deep_research_bench ｜ https://deepresearch-bench.github.io/
- 100 道 PhD 级研究任务，22 个领域，由领域专家出题；题目分布来自对 **96,147 条匿名用户 query** 的 WebOrganizer 分类，保证贴合真实需求。
- **RACE**（报告质量）：四维 = Comprehensiveness / Insight-Depth / Instruction-Following / Readability；**评分标准由 LLM 按任务动态生成**，权重按任务自适应，且是 reference-based（有参考报告作锚）。默认 judge 为 Gemini 2.5 Pro Preview，成本约 $0.13/query。
- **FACT**（信息获取）：Citation Accuracy = 被正确支持的引用占比；Effective Citations = 每任务可验证支持的引用条数。
- 人类对齐验证：RACE 的 **pairwise agreement 71.33，人类标注者之间的基线 68.44**，样本为 50 个任务 × 每任务 6 对 = **300 对**。FACT 的支持判定（Gemini-2.5-Flash）在 **100 条随机抽样的 statement–URL 对**上与人一致：判"支持"96%、判"不支持"92%。
- 引用准确率榜（as_of 2025-06 论文 v1）：Perplexity Deep Research 90.24% > Grok Deeper Search 83.59% > Gemini-2.5-Pro Deep Research 81.44% > OpenAI Deep Research 77.96%。
- 仓库 2026-05-11 公告：evaluator 迁到 GPT-5.5，overall alignment 71.82，人类基线 68.78。**⚠ 换 evaluator 后新旧榜单不可比。**

**A2. ResearchRubrics**（arXiv:2511.07685v1，2025-11-10）
- https://arxiv.org/html/2511.07685v1
- 101 条 prompt / **2,593 条 rubric item** / 9 个领域；总计投入 **2,800+ 小时人工**。
- rubric 由"有很强 STEM 背景、擅长任务设计与评测"的人撰写，**论文明说不一定是领域专家**——这点很重要，别把它当"专家写 rubric"引用。
- rubric 结构：权重区间 **[−5, +5]**；|4|–|5| 为强制项，|1|–|3| 为可选项；负权惩罚失败模式。评分档位有二值与三值（Satisfied / Partially Satisfied / Not Satisfied）两种。
- judge 与人的一致性用 **Macro F1**（不是 κ）：二值 0.72–0.76（Gemini-2.5-Pro 最高 0.760），**三值只有 0.53–0.57**。→ 档位一细化，judge 立刻不可靠。
- 最好的 agent（Gemini DR）rubric 合规度：三值 0.677 / 二值 0.615。

**A3. HealthBench**（arXiv:2505.08775，2025-05-13）——唯一真正逐条专家手写 rubric 的样本
- https://arxiv.org/abs/2505.08775
- 5,000 段多轮对话；**48,562 条唯一 rubric criteria**；**262 名医生**（从 1,021 名报名者筛出，入门任务后剩 268，再剔除 31 名质量不达标）；60 个执业国家、49 种语言、26 个专科。
- 7 个主题（Emergency referrals 9.6%、Context-seeking 11.9%、Global health 21.9%、Health data tasks 9.5%、Expertise-tailored communication 18.4%、Responding under uncertainty 21.4%、Response depth 7.2%）× 5 个评分轴（Completeness 39%、Accuracy 33%、Context awareness 16%、Communication quality 8%、Instruction following 4%）。
- **Grader 元评测**：统计量为 **Macro F1**（met / not-met 两类 F1 的非加权平均）。GPT-4.1 grader 在共识 criteria 上 **0.709**；医生个体中位数按主题在 **0.569–0.730**；grader 在 7 个主题中的 5 个超过医生平均、6 个进入上半区。元样本 **60,896 条**。**⚠ 口径：这个 0.709 只在 34 条"共识 criteria"（出现 8,053 次）上测，不是全部 48,562 条——是最容易判、人类之间最一致的子集。**
- 子集：HealthBench Consensus 3,671 例；**HealthBench Hard 1,000 例，最好模型 o3 仅 0.32**。
- 模型分：GPT-3.5 Turbo 0.16 / GPT-4o(2024-08) 0.32 / o1 0.42 / GPT-4.1 0.48 / o3 0.60。
- 人机对比：医生改写 2024-09 模型回答时 56.2% 改好、39.8% 改坏；改写 2025-04 模型回答时 46.8% 改好、47.7% 改坏——**人已经不再稳定地优于模型**。

**A4. AstaBench**（arXiv:2510.21652，2025-10-24，Ai2）
- https://arxiv.org/abs/2510.21652 ｜ https://allenai.org/asta/bench
- 2,400+ 题，11 个 benchmark，覆盖科研全流程；评了 **57 个 agent / 22 个 agent 类**；显式控制模型成本与工具访问这类混杂变量，配套"生产级搜索工具"的可复现科研环境。
- Ai2 公告口径：无 agent 在相关 benchmark 上超过 34%（来源为 Ai2 blog/Reddit 公告，非论文正文，标 unverified）。

**A5. 专家偏好平台：Deep Research Comparator**（arXiv:2507.05495，2025-07-07；WWW'26 Companion）
- https://arxiv.org/html/2507.05495v1 ｜ https://dl.acm.org/doi/10.1145/3774905.3793116
- 双盲 A/B：并排展示两个 agent 的**中间步骤流 + 最终报告**，投票四选一（A / B / 平局 / 都差），并支持对单个中间步骤 upvote/downvote、对文本 span 打标。
- 规模：**17 名标注者**（大学生 + 业界研究者，**非领域专家**）、**176 条 query**、1,281 条步骤级反馈、593 条 span 标注。
- Bradley-Terry 排名：GPT Researcher 1135.28 > Perplexity Deep Research 1087.41 > Simple Deepresearch(Gemini 2.5 Flash) 1000.00（基线）。
- **⚠ 176 次比较、48 分的 BT 差距几乎必然落在噪声内**；这个平台的价值在**流程设计**（步骤级 + span 级反馈），不在它的排名结论。

### B. 引用准确率专项评测

**B1. SourceCheckup**（Nature Communications, 2025-04-16, DOI 10.1038/s41467-025-58551-6）
- https://pmc.ncbi.nlm.nih.gov/articles/PMC12003634/
- 800 道医学问题、约 58,000 条 statement–source 对、7 个 LLM（GPT-4o RAG/API、Claude v2.1、Mistral Medium、Gemini 系等）。
- **50%–90% 的回答"未被所引来源完全支持"**。口径：statement 级"支持"= 该模型给出的**至少一个**来源含支撑信息；response 级"完全支持"= 该回答**所有** statement 都被支持（全有全无）。GPT-4o+web search：约 30% 的**语句**未被支持，但**近一半回答**未完全支持。
- 自动核验器 vs 医生共识一致率 **88.7%**，医生之间一致率 **86.1%**，独立医生复核符合度 95.8%。→ 自动核验器已达到"人间一致率"水平，这是把它放进流水线的依据。

**B2. Cited but Not Verified**（arXiv:2605.06635，2026-05-07）
- https://arxiv.org/abs/2605.06635
- 三维度：Link Works（URL 可达）/ Relevant Content（主题相关）/ Fact Check（对源内容的事实核验）。14 个开闭源 LLM。
- 前沿模型：链接有效 >94%、相关性 >80%、**事实准确 39%–77%**；不足一半的开源模型能在 one-shot 下产出带引用的报告。
- **工具调用 2 → 150 次，Fact Check 准确率平均下降约 42%（相对值，两个前沿模型平均）**——检索更多 ≠ 引用更准。

**B3. 引用核验 judge 的成本/能力基准**（arXiv:2607.08700，2026-07-09）
- https://arxiv.org/html/2607.08700
- 624 对 attribution–citation（= 1,248 条 rubric 决策）；标签流程：6 个 LLM judge 组成 council 独立打分 → 人工复核全部决策 → **378 条分歧（60.6%）重点人工裁决**。
- Source Relevance：**GPT-5-mini F1=0.908（最强，且属最便宜档）**；Claude Opus 4.6 0.866；Claude Sonnet 4.6 0.700。
- Factual Support：**所有模型置信区间重叠，统计上不可区分**；最好 Claude Opus 4.6 F1=0.750。
- judge 成本跨度 **49×**，且**成本不预测准确率**（Gemini 3.1 Flash Lite 次便宜却有竞争力，中档模型性价比最差）。
- 作者结论：把引用 rubric 当奖励信号之前，**校准 judge 是前提，但校准不需要最贵的模型**；各模型的假阳/假阴方向性差异很大，需要单独监控。

**B4. CiteME**（arXiv:2407.12861，Press et al. 2024）
- https://arxiv.org/abs/2407.12861
- 任务：给定引用某篇论文的文本片段，找出被引论文（ML 领域）。LLM **4.2%–18.5%**；CiteAgent（GPT-4o）**35.3%**；**人类 69.7%**。
- ⚠ 2024 年模型，已陈旧；且任务是"找出被引论文"，**不是"判断引用是否支持论断"**，两者常被混为一谈。

### C. LLM-judge 可靠性文献

**C1. Reliability without Validity**（arXiv:2606.19544v1，2026-06-17，UC Berkeley School of Information；Norman, Rivera, Hughes）
- https://arxiv.org/html/2606.19544
- 规模：21 个 judge / 9 家厂商 / 3 个能力档 / 3 种协议 / **约 541,000 次判定 / 118 次评测 run**。数据集：MT-Bench 2,391 对、JudgeBench 350 条、RewardBench 2,981 对。
- **核心数字：MT-Bench 上 exact match 0.788–0.851，Cohen κ 0.376–0.511；raw 一致率高估 chance-corrected 一致率 33.8–41.3 pp，队列均值 38.6 pp。** 例：Gemini 3.1 Pro EM=0.849 但 κ=0.511（虚高 33.8 pp）。作者原话式表述：宣称"85% agreement"的 judge，κ≈0.48。
- **Position bias：0.002（Gemini 2.5 Pro）– 0.192（Qwen 3 8B）**，跨近两个数量级。
- **Verbosity bias：21 个 judge 全部 <0.011，17/21 <0.005**（MT-Bench，bias-audit 协议）。
- 难度：test-retest 从 MT-Bench 0.943 → JudgeBench 0.911；16 个 judge 中 7 个位置翻转率退化 ≥1.5×；Claude Opus 4.6 与 Gemini 3.1 Pro 在难集上反而更好。
- **consistency–bias paradox**：test-retest ≥0.95 与 position bias >0.10 可以并存于同一个已上线 judge——"高度可复现但无效"。一个恒定偏好 A 位的 judge 会拿到满分 test-retest 和最大位置偏置。

**C2. Self-Preference Bias in LLM-as-a-Judge**（arXiv:2410.21819v1，2024-10-29）
- https://arxiv.org/html/2410.21819v1
- 8 个 LLM judge，数据集 Chatbot Arena 33,000 段对话（带人类偏好标签）。
- 定义 4.1：Bias = P(Y′=1|S=1,Y=1) − P(Y′=1|S=0,Y=1)，取值 0 = 无偏，趋近 1 = 强偏。
- **GPT-4 = 0.520（最高），= 0.945 − 0.425 的差值。⚠ 这不是"GPT-4 有 52% 概率偏袒自己"。**
- 机理：LLM 系统性地给**低困惑度**文本更高分，与是不是自己生成的无关——自偏好是"熟悉度偏好"的副产品。→ **同族/同厂商模型互评会系统性放大这个偏置。**

**C3. Justice or Prejudice? (CALM)**（arXiv:2410.02736，2024-10-03）
- https://arxiv.org/abs/2410.02736
- 量化 **12 类偏置**，方法是自动化、原则引导的扰动改写。结论：即便最先进的 judge 在特定任务上仍有显著偏置，可靠性有明显改进空间。（摘要未给逐项数值。）

**C4. judge 在难题上的退化（IRT 视角）**（arXiv:2605.00238）
- https://arxiv.org/pdf/2605.00238
- 用 IRT 同时估计 judge 能力与题目难度：**准确率随难度单调下降**，且下降速率在模型间差异极大。最难难度箱上：Gemma-3-12B 保留 16.6%，OpenChat-3.5 15.9%，Qwen3.5-9B 4.1%，Phi-3-medium 5.8%，Llama-3.1-8B 2.1%。

### D. 抗污染与保留集纪律

**D1. GSM1k**（arXiv:2405.00332，v1 2024-05-01，v4 2024-11-22，Scale AI，NeurIPS 2024）
- https://arxiv.org/abs/2405.00332 ｜ https://github.com/scaleapi/gsm1k_eval
- 新造一批与 GSM8k 同风格同难度的题（对齐人类解答率、解题步数、答案量级），作为私有保留集测过拟合。
- **摘要口径：准确率下降"最多 8%"**；若干模型家族在几乎所有规模上都有系统性过拟合；**前沿模型过拟合迹象很小**，且所有模型都对保证未见过的新题表现出泛化。
- ⚠ 网上广泛流传的"最多 13%"未在论文摘要中出现（见核验表）。

**D2. Search-Time Contamination**（arXiv:2508.13180v1，2025-08-12）——对本项目最要命的一条
- https://arxiv.org/html/2508.13180v1
- 定义：评测带搜索的 agent 时，**检索步骤本身命中了评测集来源**，从而泄漏答案线索。
- 命中率：HLE 约 3.36%–3.44%（三个 agent）；GPQA 1.90%–4.15%；SimpleQA 0.99%–1.20%。
- 影响：**SimpleQA 上被污染样本准确率 100%，未污染样本约 7%**；HLE 上被污染样本准确率高出 10–20%；GPQA 上检索到污染源**没有**提升准确率。屏蔽 HuggingFace 后，被污染子集准确率下降约 15%。
- 建议缓解：多重搜索过滤器、内部审计（关键词过滤 + 子串匹配）、透明报告（含所用缓解手段）、优先用信息检索型任务而非知识问答型任务。

**D3. 词面花招无效**
- BIG-bench canary string 已被证伪：GPT-4 能复现该 canary（AlignmentForum/LessWrong, 2024-10-22）；Claude 3.5 Sonnet 同样有公开复现记录（HN, 2024-07-11）。https://www.alignmentforum.org/posts/kSmHMoaLKGcGgyWzs/big-bench-canary-contamination-in-gpt-4
- arXiv:2605.19999v1（2026-05-19）明确评估各类手段：私有评测（需可信第三方，有瓶颈）、动态评测（新集很快被抄）、**词面混淆（改写/打乱）无效——现代 LLM 常能绕过**、**n-gram 去污在规模化下越来越难**。该文自己提出的方案（把数据集编码进锚模型的 KV cache / 倒数第二层隐状态）属未经实战验证的新技术路线。
- 系统综述（2026-06）结论：跨污染层级、访问设置与训练阶段，**没有任何一种检测方法是一致可靠的**。

**D4. 时间锚定轮换（真正有效且低成本）**
- LiveCodeBench（arXiv:2403.07974v2）：每道题标注**发布日期**，只在模型训练截止日之后的题上评；对 DeepSeek 因此只剩 **349 题**可用。https://livecodebench.github.io/
- LiveBench（https://livebench.ai/，as_of 2026-08）：23 个客观任务 / 7 个类别，**每六个月刷新一次**（站点自述，标 site-claim）。
- Humanity's Last Exam：公开题目 + **保留一份私有题集**用于检测过拟合。https://agi.safe.ai/

### E. 能力指标 × 完整性指标配对

**E1. Why Language Models Hallucinate**（arXiv:2509.04664，2025-09-04，OpenAI）
- https://arxiv.org/abs/2509.04664
- 论证：幻觉源自二元分类误差的统计压力；**"语言模型被优化成好考生，不确定时猜测能提高考试成绩"**——0-1 计分对弃权是纯惩罚。
- 建议是**社会-技术**性的：**改造主流榜单基准的计分方式**（对自信错误的惩罚重于承认不确定），而不是再加一个专门的幻觉评测。这正是"能力指标必须内建完整性定价"的一手依据。

**E2. 统计功效与样本量**
- Position: Don't Use the CLT in LLM Evals With Fewer Than a Few Hundred Datapoints（arXiv:2503.01747，v1 2025-03-03 / v3 2025-05-28，**ICML 2025 Spotlight**）：https://arxiv.org/abs/2503.01747 —— 少于"几百"条数据点时 CLT 方法**严重低估不确定性**（误差棒过窄）；建议改用其他频率派/贝叶斯方法。
- 自算（可复现，见核验表末）：n=100、p=0.8 时 Wilson 95% CI 半宽 7.8 pp；n=60 时 10.0 pp；n=30 时 13.9 pp；n=12 时 21.0 pp。两臂各 n=60 时，80% 功效下的最小可检测差异约 20.4 pp。

---

## 载荷数字核验表（数字 ｜ 口径三元组 ｜ 状态 ｜ 一手出处）

口径三元组格式：**测什么 / 在什么样本或档位上 / 与什么比**。

| # | 数字 | 口径三元组 | 状态 | 一手出处 |
|---|---|---|---|---|
| 1 | 100 题 / 22 域 | 任务集规模 / DeepResearch Bench 全集，专家出题、题型分布源自 96,147 条真实 query / — | verified | arXiv:2506.11763 (2025-06-13) + GitHub README |
| 2 | RACE 71.33 vs 人类 68.44 | **成对偏好一致率** / 50 任务 × 6 对 = **300 对**，judge=Gemini 2.5 Pro Preview / 与人类标注者之间的一致率比 | verified | arXiv:2506.11763 HTML v1 |
| 3 | FACT 96% / 92% | 与人一致率（分别在"支持"与"不支持"两类上） / **仅 100 条随机 statement–URL 对**，judge=Gemini-2.5-Flash / 与人工判定比 | verified，但 n=100 ⚠ CI 宽 | arXiv:2506.11763 HTML v1 |
| 4 | Perplexity DR 90.24% / OpenAI DR 77.96% | Citation Accuracy = 被正确支持的引用占比 / DeepResearch Bench 100 题，FACT 自动判定 / 系统间横比 | verified-as-reported，**stale (as_of 2025-06)** | arXiv:2506.11763 |
| 5 | GPT-5.5 evaluator 71.82 vs 68.78 | 同 #2 的一致率口径 / 换 evaluator 后重测 / 与人类基线比 | verified (repo, as_of 2026-05-11)，**与 #2 不可跨版本比较** | GitHub Ayanami0730/deep_research_bench |
| 6 | 101 题 / 2,593 rubric / 9 域 / 2,800+ 小时 | 基准规模与人工投入 / ResearchRubrics 全集 / — | verified | arXiv:2511.07685v1 (2025-11-10) |
| 7 | rubric 撰写者"强 STEM 背景，不一定是领域专家" | 标注者资质 / ResearchRubrics / 与"专家写 rubric"的通常说法比 | **corrected**（常被误引为专家写） | arXiv:2511.07685v1 |
| 8 | 二值 F1 0.72–0.76；三值 F1 0.53–0.57 | **Macro F1**（不是 κ） / 3 个 judge 模型在 ResearchRubrics 上 / 与人工 rubric 判定比 | verified | arXiv:2511.07685v1 |
| 9 | Gemini DR 0.677（三值）/ 0.615（二值） | rubric 合规度 / ResearchRubrics 全集 / 系统间横比 | verified | arXiv:2511.07685v1 |
| 10 | 5,000 对话 / 48,562 criteria / 262 医生 / 60 国 / 49 语 / 26 专科 | 基准规模 / HealthBench 全集 / — | verified | arXiv:2505.08775 (2025-05-13) + 全文 |
| 11 | grader macro F1 = 0.709 | Macro F1（met/not-met 两类 F1 非加权均） / **仅 34 条"共识 criteria"（出现 8,053 次），60,896 条元样本** / 与医生个体中位数 0.569–0.730 比 | verified，**⚠ 口径：只在最易判子集上** | HealthBench 全文 |
| 12 | HealthBench Hard 1,000 题，o3 = 0.32 | rubric 得分 / Hard 子集 / 与全集 o3=0.60 比 | verified | HealthBench 全文 |
| 13 | 医生改写 2025-04 模型回答：46.8% 改好 / 47.7% 改坏 | 人类相对模型的净增益 / HealthBench 人机对照 / 与 2024-09 模型的 56.2%/39.8% 比 | verified | HealthBench 全文 |
| 14 | 2,400+ 题 / 11 benchmark / 57 agent / 22 agent 类 | 套件规模 / AstaBench / — | verified | arXiv:2510.21652 (2025-10-24) |
| 15 | "无 agent 超过 34%" | 最高得分 / AstaBench 相关子集 / 系统间横比 | **unverified**（来自 Ai2 公告/Reddit，非论文正文） | allenai.org/blog/astabench |
| 16 | EM 0.788–0.851 vs κ 0.376–0.511；虚高均值 **38.6 pp**（区间 33.8–41.3） | raw exact-match 一致率 vs Cohen κ / **MT-Bench 2,391 对，21 个 judge** / raw 与 chance-corrected 比 | verified | arXiv:2606.19544v1 (2026-06-17) |
| 17 | position bias 0.002 – 0.192 | 该文 bias-audit 协议下的位置偏置统计量（[0,1] 比率，**不是 winrate 百分点**） / MT-Bench，21 judge / 模型间横比 | verified | arXiv:2606.19544v1 |
| 18 | verbosity bias 全部 <0.011，17/21 <0.005 | 同上协议的冗长偏置统计量 / MT-Bench，21 judge / — | verified | arXiv:2606.19544v1 |
| 19 | "verbosity bias 15–30 点""position bias 10–15 点""22–30% 判定翻转""self-preference 10–25%" | 未定义口径 / 未说明样本 / 未说明比较对象 | **unverified，且 #18 与之直接冲突**；来源为互相复述的营销博客（futureagi.com / ai-tldr.dev），**虚假独立佐证** | — |
| 20 | test-retest 0.943 → 0.911；7/16 judge 位置翻转率退化 ≥1.5× | 重测信度与位置翻转率 / MT-Bench → JudgeBench（更难） / 易集与难集比 | verified | arXiv:2606.19544v1 |
| 21 | GPT-4 self-preference = 0.520 | Def 4.1 条件概率差（0.945 − 0.425） / Chatbot Arena 33,000 段对话，8 个 judge / 与其它 judge 横比。**不是"52% 概率偏袒自己"** | verified，但 **stale（2024 年模型）** | arXiv:2410.21819v1 (2024-10-29) |
| 22 | 12 类偏置 | 偏置类别数 / CALM 框架 / — | verified（无逐项数值） | arXiv:2410.02736 (2024-10-03) |
| 23 | 最难难度箱准确率 2.1%–16.6% | 短答自动评分准确率 / IRT 分箱后的最难箱，5 个开源 judge / 与整体准确率比 | verified | arXiv:2605.00238 |
| 24 | 50%–90% 回答"未被完全支持" | **回答级全有全无**（所有 statement 都被支持才算） / 800 题、~58,000 statement–source 对、7 个 LLM / — | verified；**⚠ 同篇语句级仅约 30% 未支持（GPT-4o+search）** | Nat Commun 2025-04-16, PMC12003634 |
| 25 | 自动核验器 88.7% vs 医生间 86.1% | 与医生共识的一致率 / SourceCheckup 抽样复核 / 与医生之间的一致率比 | verified | PMC12003634 |
| 26 | 链接 >94% / 相关 >80% / 事实支持 39%–77% | 三个独立维度的通过率 / 14 个 LLM 的 deep-research 报告引用 / 维度间比 | verified | arXiv:2605.06635 (2026-05-07) |
| 27 | 工具调用 2→150，事实准确率降约 **42%** | **相对降幅**（不是 42 个百分点） / 两个前沿模型的平均 / 少调用与多调用比 | verified（口径已澄清） | arXiv:2605.06635 |
| 28 | GPT-5-mini F1=0.908（source relevance） | F1 / 624 对 attribution–citation（1,248 决策），人工裁决过 378 条分歧 / 与 Claude Opus 4.6 的 0.866、Sonnet 4.6 的 0.700 比 | verified | arXiv:2607.08700 (2026-07-09) |
| 29 | factual support 最好 F1=0.750，**所有模型 CI 重叠** | F1 及置信区间 / 同上 624 对 / 模型间统计可区分性 | verified | arXiv:2607.08700 |
| 30 | judge 成本跨度 **49×**，成本不预测准确率 | 单次评测成本比 / 同上 judge 池 / 成本与 F1 的相关性 | verified | arXiv:2607.08700 |
| 31 | 60.6%（378/624）需人工裁决 | judge council 分歧率 / 624 对 / — | verified（378 与 624 为原文数，比例为自算） | arXiv:2607.08700 |
| 32 | CiteME：LLM 4.2%–18.5% / CiteAgent 35.3% / 人 69.7% | 找出被引论文的准确率（**不是引用支持性判定**） / ML 领域引文片段 / 人机比 | verified，**stale（2024 模型）** | arXiv:2407.12861 |
| 33 | GSM1k 准确率下降"最多 8%" | GSM8k→GSM1k 的准确率落差上界 / 跨模型家族 / 公开集与私有孪生集比 | verified | arXiv:2405.00332 摘要 (v1 2024-05-01 / v4 2024-11-22) |
| 34 | "GSM1k 最多下降 13%" | 同上 | **unverified**（仅见于多个互相复述的博客，论文摘要为 8%） | — |
| 35 | STC 命中率：HLE 3.36%–3.44% / GPQA 1.90%–4.15% / SimpleQA 0.99%–1.20% | 检索结果命中评测集本体的样本占比 / 三个 Sonar 系 agent / benchmark 间横比 | verified | arXiv:2508.13180v1 (2025-08-12) |
| 36 | SimpleQA 污染样本 100% vs 未污染约 7% | 准确率 / 同上 / 污染子集与干净子集比 | verified | arXiv:2508.13180v1 |
| 37 | 屏蔽 HuggingFace 后污染子集准确率降约 15% | 准确率降幅 / 同上 / 屏蔽前后比 | verified | arXiv:2508.13180v1 |
| 38 | 词面混淆无效、n-gram 去污规模化失效 | 缓解手段有效性的定性结论 / 该文的手段评估 / 与私有保留、动态评测比 | verified（定性，无数值） | arXiv:2605.19999v1 (2026-05-19) |
| 39 | GPT-4 复现 BIG-bench canary | canary 机制失效的存在性证据 / 单次公开复现 / — | verified（社区一手复现记录，非同行评议） | AlignmentForum 2024-10-22 |
| 40 | LiveCodeBench 对 DeepSeek 仅剩 349 题 | 时间窗过滤后的可用题量 / 训练截止日之后发布的题 / 与全集比 | verified | arXiv:2403.07974v2 |
| 41 | LiveBench 23 任务 / 7 类 / 每 6 个月刷新 | 套件规模与刷新周期 / LiveBench 官网自述 / — | verified as site-claim (as_of 2026-08) | https://livebench.ai/ |
| 42 | "少于几百条数据点不要用 CLT" | 置信区间方法适用下界 / LLM 评测常见小样本 / CLT 与其它频率派/贝叶斯方法比 | verified，ICML 2025 Spotlight | arXiv:2503.01747 |
| 43 | Wilson 95% 半宽：n=12→21.0pp / n=30→13.9pp / n=60→10.0pp / n=100→7.8pp / n=200→5.5pp（p=0.8） | 二项比例 95% Wilson 区间半宽 / 给定 n 与 p=0.8 / 不同 n 间比 | **verified by re-run**（本文附脚本，确定性可复算） | 自算，脚本见下 |
| 44 | 两臂各 n=60 时 MDD≈20.4pp；n=100→15.8pp | 两独立比例、α=0.05、功效 0.8 的最小可检测差异 / p≈0.8 / 不同 n 间比 | **verified by re-run** | 自算，脚本见下 |
| 45 | 17 标注者 / 176 query / BT 1135.28 vs 1087.41 vs 1000 | 人类偏好排名 / Deep Research Comparator，标注者为学生+业界研究者（**非领域专家**） / 三系统横比 | verified；**⚠ n=176，48 分差距大概率在噪声内** | arXiv:2507.05495 (2025-07-07) |
| 46 | "judge-专家一致度 0.66–0.96，中位 0.83" | 未核实的统计量类型与样本 | **unverified**（转述自医疗领域 scoping review 摘要，未取一手） | arXiv:2605.25273（未验证） |
| 47 | "26 个主流模型幻觉率 22%–94%"（Stanford HAI AI Index 2026） | 未核实口径 | **unverified**（未取一手页面） | — |
| 48 | FActScore：ChatGPT 58.3% / PerplexityAI 71.5% | 原子事实支持比例 / 人物传记生成、对 Wikipedia 检索核验 / 系统间横比 | **unverified**（仅见 Medium 转述，未核对 arXiv:2305.14251 正文） | — |

**#43/#44 的复算脚本**（确定性，任何时候可重跑得到同一结果）：
```python
import math
z = 1.96
def wilson(p, n):
    d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return c-h, c+h, h
for n in [12, 20, 30, 60, 80, 100, 200]:
    lo, hi, h = wilson(0.8, n)
    print(f'n={n:4d} Wilson95=[{lo:.3f},{hi:.3f}] halfwidth={h*100:.1f}pp')
def mdd(n, p=0.8):                       # 两独立比例, alpha=.05 双侧, power=.8
    return (1.96 + 0.84) * math.sqrt(2*p*(1-p)/n)
for n in [30, 60, 100, 200]:
    print(f'two-arm n={n} each -> MDD = {mdd(n)*100:.1f}pp')
```

---

## 对本项目的设计含义

### 1. 三层评测分工（谁判什么，硬边界）

**L1 · 确定性 in-loop gate（零 LLM，每条 load-bearing claim 必过）**
这一层是本项目"可信度即产品"的地基，必须做到 100% 机器判定、可重跑、无歧义：

| 闸门 | 判定方式 | 依据 |
|---|---|---|
| `source_id` 存在性 | claim 的 source_id 必须在 evidence store 中存在 | schema 校验 |
| 链接存活 + 归档 | HTTP 可达 + 本地快照存在 | 前沿模型链接有效率仍只有 >94%，剩下的 <6% 是死链（#26） |
| **逐字引文命中** | claim 携带的 verbatim quote 必须在抓取到的源文本中（规范化后）逐字命中 | 纯字符串匹配；这是把"引用核验"里唯一确定可判的部分从 judge 手里拿回来 |
| **数字可重算** | (a) 类 claim 必须挂可重跑脚本，exit 0 且 stdout 数字与正文位级一致 | 本文 #43/#44 即示范 |
| **口径三元组非空** | `metric` / `sample_or_tier` / `comparator` 三字段缺任一 → 直接判 unverified，**不进 judge** | 直接对治上一轮 1/3 口径畸变 |
| `as_of` 日期 | 可失效字段（价格 / API 条款 / 榜单 / 模型分）必须有日期戳 | #4 已因换 evaluator 而不可比 |
| **促销价枚举** | 定价类 claim 必须有 `pricing_type: list \| promo \| intro`，promo 必须带 `expires_at` | 上一轮被促销价烧过 |
| **上游去重** | source_id 按 upstream domain/DOI 归一，同一上游只计 1 个独立源 | 虚假独立佐证（#19 即活样本） |
| 状态穷尽 | 每条 claim 必须是 `verified \| corrected \| unverified` 之一，无空值 | — |

**L2 · Rubric judge（需判断、可批量，但必须先校准）**
只做三件事，且都产出三值（support / partial / not-support），**partial 一律降级为 unverified**：
1. **引文支持性**：逐字引文命中之后，该引文是否真的支持这条断言。
2. **口径畸变检测**：claim 声明的三元组与源文本实际口径是否一致——把上一轮的失败模式变成显式 judge 维度。
3. **逻辑链检查**（(c) 类 claim）：前提是否都已 verified、是否有 ≥2 步跳跃。
报告级的 RACE 四维（覆盖度/深度/指令遵循/可读性）可以跑，但**只作为诊断，不进 gate、不进对外分数**。

**judge 的模型选择**（直接来自 #28–#30）：
- "来源相关性"这类维度用便宜模型即可（GPT-5-mini F1=0.908，且属最便宜档；成本跨度 49× 但不预测准确率）→ 我们的 **v4-flash 完全可以承担这一维**。
- **"事实支持"这一维没有任何模型够好**（最好 F1=0.750，且所有模型 CI 重叠）→ **绝不能全托给 judge**，必须由 L1 的逐字命中 + L3 的人裁抽检兜底。
- judge council 至少 3 路且**必须跨厂商**（自偏好机理是低困惑度偏好，同族互评会系统性放大，#21）。生成用 deepseek-v4-pro，judge 至少一路非 DeepSeek。
- **用分歧率做升级信号，而不是投票平均**。参照 #31：624 对里 378 对（60.6%）有分歧并被人工裁决——这是"人要看多少"的现实锚点，不要幻想 5%。

**L3 · 人（用户本人 / 领域专家）**
1. 选题与研究问题是否值得做（judge 完全无能）。
2. **judge 分歧项 + partial 项 + hard 难度箱的抽检（≥30%）**：judge 在难题上确实塌（#20、#23）。
3. 新颖性与贡献判断。
4. 中文成稿的学术规范终检（GB/T 7714 引注格式、术语一致性）。
5. **每季度重跑一次 judge 元评测的人工标注**（见下）。

### 2. judge 上线与再校准协议（硬性）

- **上线门槛写成 κ，不写成 accuracy。** 依据 #16：raw 一致率平均虚高 38.6 pp，"85% agreement" 实际 κ≈0.48。建议阈值：在人标校准集上 **Cohen κ ≥ 0.60** 方可上线；κ ∈ [0.4, 0.6) 只能做"分流器"（把条目路由给人），不能做终判。
- **禁止在任何文档里单独出现 raw agreement 数字**——出现必须并排给 κ。
- **校准集规模 200 条**，按难度分三箱各约 65 条（n=65 时 Wilson 半宽约 9.7 pp，勉强可用；n=100 才到 7.8 pp，#43）。参照 #28 的 624 对（1,248 决策）是"做得好"的上限，业界常见实践是 50–200 条。
- **同时报 position-flip 率**：一致性 ≠ 有效性（consistency–bias paradox，#16）。每条 pairwise 判定双向各跑一次，翻转即计。自己测自己的偏置，**不引用行业"公认数量级"**（#19 已被一手证伪）。
- **触发再校准的事件**：换 judge 模型、改 judge prompt、换 rubric 版本。#5 是活教训——换 evaluator 后旧分数直接不可比。每次再校准都要给新旧版本一个显式的 `judge_version`，跨版本分数**禁止同图对比**。

### 3. 最小可信 held-out 任务集规模

**推荐：总量 60–100 题，覆盖 6–8 个域，每域 8–12 题；其中中文课程论文/文献综述场景不少于 20 题。**

论证（两条独立的锚）：
- **同类基准的经济上限锚**：DeepResearch Bench 100 题 / 22 域，ResearchRubrics 101 题 / 9 域（2,800+ 小时人工）。两个由专业团队独立建的"研究报告"基准都落在 **~100 题 / 9–22 域** 这个量级，说明对"每题都要人参与出题与校验"的任务，100 题就是经济上限；ResearchRubrics 的 2,800+ 小时说明再往上不可承受。AstaBench 的 2,400 题是 Ai2 级投入，不可参照。
- **统计功效锚**（自算，#43/#44）：
  - n=12（单域下限）：Wilson 半宽 ±21.0 pp → **只够发现灾难性回归，不许报点估计差异**。
  - n=60：±10.0 pp；两臂各 60 时最小可检测差异 20.4 pp。
  - n=100：±7.8 pp；两臂各 100 时 MDD 15.8 pp。
  - **规则：n=60 时任何 <10 pp 的变化写"无信号"；n=100 时任何 <8 pp 写"无信号"。** 且因 n<几百，**禁用 CLT/Wald 区间，一律用 Wilson 或 Clopper-Pearson**（#42）。

**分层结构**：
- 核心闭集 **60 题**（永不公开、永不进 git、永不进 artifact）
- 公开演示集 **20 题**（可展示，分数只用于对外说明，不作为质量结论）
- 季度轮换池 **20 题**（每季度新造，替换核心闭集中最老的 15 题即 25%）

### 4. 抗污染纪律（对"会上网的 agent"特化）

- **技术花招不做**：不用 canary string（#39 已证伪）、不做 n-gram 去污、不做改写混淆（#38）。
- **做数据隔离**：核心闭集的题面与参考答案只存本机加密目录（例如 macOS 加密 sparsebundle 或 `age` 加密文件），**不进 git、不进 artifact、不发任何公开渠道**。这是 GSM1k / HLE 私有子集的模板（#33）。
- **做时间锚定**：每道题标注 `created_at`；跑评测时优先用"晚于被测模型训练截止日"的题（LiveCodeBench 模板，#40）。
- **做 search-time 防护**（本项目独有、且最危险，#35–#37）：
  1. 评测 run 期间给搜索工具挂 denylist：我们自己的域名、GitHub/gist、HuggingFace、任何可能承载题面的地方。
  2. **记录每次 run 检索到的全部 URL**，run 后用题面关键子串扫描一遍，命中即把该题标为"本次污染"并从分数中剔除、单独报告。
  3. 报告必须显式给出"污染样本占比"和"干净子集分数"两个数——SimpleQA 上污染样本 100% vs 干净 7% 的差距说明不这么做等于没评。
- **做退役**：一旦公开切片分数与私有切片分数的差距超过容忍度（建议 10 pp），立即退役该公开切片换新。
- **"改过就降级"**：任何一次针对某批失败题去改 prompt / skill / 流程之后，那批题立刻从 held-out 降级为 dev 集，**永久不再计入对外分数**。

### 5. 反 Goodhart 规则（硬约束，写进 profile 的规则文件）

**R1（本轮最重要）· in-loop gate 的通过率永远不得作为质量指标对外报告。**
理由：`gate pass rate = verified / (verified + unverified)`，**分母可被压缩**。要提高它有两条路——把研究做扎实，或者少写载荷数字、只写容易过闸的句子、避开口径难判的断言。后者远比前者便宜，所以只要把它当目标，系统必然滑向"写得少而安全"。
- gate pass rate **只在内部作为诊断**，且**必须分子分母同时露出**（"142 verified / 187 载荷断言"，不写 "76%"）。
- 对外只报三个数：(i) **每千字载荷断言密度**，(ii) **verified 断言的绝对条数**，(iii) 冻结 held-out 集上由**未参与生成**的 judge + 人裁给出的分数。

**R2 · 每个能力指标必须配一个完整性指标，成对上报；任何一个单独出现即视为无效报告。**
强制配对表：

| 能力指标 | 必须配对的完整性指标 |
|---|---|
| 覆盖广度 / 主题命中数 | 每条断言的**去上游重**独立源计数 |
| 断言总数 | verified 占比（且分子分母同露） |
| 报告长度 | 每千字 verified 断言密度 |
| 引用条数 | 逐字引文命中率 + 链接存活率 |
| 速度 / 成本 | hard 难度箱的人裁抽检错误率 |
| 任务完成率 | **弃权率**（明确写"证据不足，未下结论"的条目占比） |

**R3 · 把弃权定价写进主评分，不另开幻觉专项评测。**
直接采纳 #E1 的主张：0-1 计分惩罚弃权，会把系统训成"不确定时猜"。主评分采用非对称计分——**答对 +1、明确弃权 0、自信错误 −2**（自信错误 = 标为 verified 但人裁判定为错）。这样"少写以求高通过率"和"多写以求高覆盖"都不占便宜。

**R4 · judge 不得参与生成期。** 写作阶段禁止调用同一个 rubric judge 自评再改写——那就是对 judge 直接做梯度下降。judge 只在**冻结产物**上跑一次。若确需自检，自检必须用**不同的 prompt + 不同厂商的模型**，且其输出不进最终分数。

**R5 · judge 与生成器不得同源。** 见 #21 的机理（低困惑度偏好）。

**R6 · 分数必须按难度分箱报，禁止只报总分。** 依据 #20（7/16 judge 在难集上位置翻转率退化 ≥1.5×）与 #23（最难箱准确率跌到 2.1%–16.6%）。hard 箱强制 ≥30% 人裁抽检，且 hard 箱分数**不得与 easy 箱合并成单一数字**。参照 HealthBench 单独切出 Hard 子集（o3 从 0.60 掉到 0.32，#12）。

**R7 · 口径三元组是一等公民。** 缺任一项直接判 unverified，不进 judge、不进报告。并对下列两类做强制标注：`pricing_type`（list/promo/intro）与 `as_of`。

**R8 · 独立性判定按上游归一。** 同一上游 domain/DOI 的多个页面只计 1 个独立源。"三个来源都这么说"在归一后可能只是 1 个来源（#19 就是本轮抓到的实例）。

**R9 · 每个数字必须能回答"这是相对值还是绝对值"。** #27 的"下降 42%"是相对降幅，不是 42 个百分点；#24 的 50%–90% 是回答级全有全无口径，同篇语句级只有约 30%。这两类混淆是本领域最高频的失真。

---

## 未决与风险

1. **中文场景没有对标基准。** 本轮 12+ 次检索未找到面向中文学术报告/课程论文的、有公开 rubric 方法学的研究报告基准。ResearchRubrics/DeepResearch Bench/HealthBench 全部以英文为主（HealthBench 覆盖 49 种语言但 rubric 语言分布未查）。**风险：我们的 judge 校准与偏置测量全部在英文证据上做，跨语言泛化未验证。** 缓解：核心闭集里的 ≥20 道中文题必须单独做一次 judge 元评测，κ 单独报，不与英文合并。

2. **#46 / #47 / #48 三个数字未取一手。** 分别是"judge-专家一致度 0.66–0.96 中位 0.83"（医疗 scoping review）、"26 个模型幻觉率 22%–94%"（Stanford HAI AI Index 2026）、"FActScore ChatGPT 58.3% / PerplexityAI 71.5%"。若后续文档要引用，必须先取一手。

3. **#4 的引用准确率榜已过期且不可跨版本比较。** 2025-06 的数字与 2026-05 换 GPT-5.5 evaluator 后的数字不可同图。任何引用必须带 evaluator 版本。

4. **#21（self-preference 0.520）与 #32（CiteME 4–18%）都是 2024 年模型的测量，对 2026 前沿模型很可能已陈旧。** 机理性结论（低困惑度偏好、同族互评放大）可继续用；数值不可继续用。

5. **"事实支持"这一维没有可靠自动判定手段**（#29：所有模型 CI 重叠，最好 F1=0.750）。这意味着本项目"可信度即产品"的核心承诺，在最关键的一环上**必须依赖人的抽检**，无法全自动。这是设计上不可回避的成本，必须在 profile 的对外说明里写清楚，不能宣称"全自动可信"。

6. **arXiv:2605.19999 提出的抗污染方案（隐状态编码）属未经实战验证的技术路线**，与本文件"靠数据纪律不靠技术花招"的结论相反。本轮采信其**证伪部分**（词面混淆与 n-gram 去污失效），不采信其**新方案部分**。

7. **judge 元评测本身的成本未估算。** 200 条人标校准集 × 每季度重跑，加上 hard 箱 30% 抽检，是一笔持续的人力开销（用户本人的时间）。若不可承受，退路是把 L2 judge 的角色从"终判"降为"分流器"（κ 只需 ≥0.4），把所有终判集中到 L1 确定性闸门 + L3 人裁——代价是载荷断言密度会显著下降。这个权衡需要在 profile 设计阶段显式决策。

8. **Deep Research Comparator 的排名结论（#45）不可引用作证据**（n=176，非专家标注者，BT 差距在噪声内）。可引用的只有它的**流程设计**：步骤级 upvote/downvote + span 级标注 + 四选一（含"都差"选项）。
