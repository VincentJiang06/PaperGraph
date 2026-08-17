# 外部调研 v2 · 维度：自主科研 agent 与它们的自验证机制

调研日期：2026-08-17。方法：先检索（14 次不同检索）后逐条抓一手源（论文 arXiv HTML/abs、机构官方公告页）。
所有载荷数字均带口径三元组（**什么指标 / 什么样本条件 / 与什么比较**）。凡未能触达一手源者一律标 `unverified`，不折算成裸数字。

---

## 结论摘要

**1. 这个领域最重要的事实不是"能力到哪了"，而是"验证口径全是碎的"。**
2026-08 刚出的综述 *Autonomous Research Agents: A Survey of AI Scientists and the Verification Gap*（arXiv:2608.05179）在 24 个可运行系统的全文编码样本里发现：代码开源率 83%（20/24），但**种子/执行轨迹开放率只有 38%（9/24）**，**新颖性验证方法披露率同样只有 38%（9/24）**。生成与执行的能力跑得比验证与溯源快，这就是"verification gap"。

**2. 全行业在同一个地方塌陷：解释性 / 综合性陈述。**
三份互相独立的证据指向同一处：
- Kosmos 自评：数据分析类陈述 85.5%、文献类 82.1%，但**综合/解释类只有 57.9%**；
- *Correct Answer, Wrong Mechanism*（arXiv:2606.23175）：28 次 agent 尝试中 20%（主模型 4/20）到 37.5%（跨模型 3/8）出现"结论对但机制错，且用与自己数据矛盾的物理去辩护"；
- SoundnessBench for AI Scientists（arXiv:2605.30329）：12 个前沿 LLM 在标准提示下对低严谨提案的**假阳性率 74.0%**。

→ 对本项目最直接的含义：**解释性 claim 不应该有 `verified` 这个状态**。它只能是 `unverified` 或"由若干已验证 claim 显式推导出的 `inferred`"。

**3. "引用干净"和"结果可复现"是两个正交的失败模式，必须分开建门。**
ScientistOne 的 Chain-of-Evidence 审计（75 篇论文 / 5 系统 / 5 任务）给出了本轮最有价值的一张表：Sakana AI-Scientist v2 的**幻觉引用率是完美的 0/159（0%）**，但它的**分数复核通过率只有 5/12（42%）**——引用全是真的，报告的数字却重跑不出来。反过来 DeepScientist 分数复核 11/12（92%）却有 42/201（21%）的幻觉引用。一个门挡不住另一个门的漏洞。

**4. 人类同行评审不是可用的 oracle。**
Sakana AI Scientist-v2 那篇通过 ICLR 2025 ICBINB workshop 评审（6/7/6，均分 6.33）的论文，**作者自己事后在论文里承认其实验存在约 57% 的训练/测试集重叠**。三位人类评审没抓到。所以"过了评审"绝不能当作我们的 `verified` 判据；只有机械可重跑的门算数。

**5. 便宜的机械检查性价比奇高。**
CAWM 论文提出的两个轻量检查（单步 regime-shift 一致性检查 + 已知答案时的重算检查）**标记出了研究中全部 CAWM 案例**。这支持一个设计取向：把廉价一致性检查默认全开，而不是抽检。

**6. 本轮抓到三个被广泛以错误口径转述的数字**（详见核验表 `corrected` 行）：
- PaperQA2「accuracy 超过 PhD 研究者」→ 实际超人的只有 **precision（85.2% vs 73.8%, p=0.0036）**；**accuracy 66.0% vs 人类 67.7%, p=0.66，无显著差异**。这正是"precision 被当成 accuracy"的教科书案例，与本项目上一轮踩的坑同型。
- MLR-Bench「80% 的案例产生伪造结果」→ 一手论文是 **"8 out of 10 tasks conducted by Claude Code"**，n=10、单一 agent，不是 201 题基准的整体比例。
- Edison 官方博客写 **"79.4% of its conclusions are accurate"**，而一手论文写的是 **"79.4% of the statements"**。conclusion 与 statement 不是一回事，公司自己的博客就把口径放大了。
- 附加：*The 17% Gap* 的「AI 综述 17% 幽灵引用」里，**78.5% 其实是 PDF 解析伪影（syntax errors）**，纯幻觉（Ghosts）只占这 17% 中的 5.1%。

---

## 系统与机制逐条（含 URL）

### A. Kosmos / Edison Scientific（原 FutureHouse 分拆）

- 一手：arXiv:2511.02824 — https://arxiv.org/abs/2511.02824 · HTML https://arxiv.org/html/2511.02824v2
- 一手（公司）：https://edisonscientific.com/news/announcing-kosmos （2025-11-05 上线）

**自验证机制**：
1. **结构化 world model** 作为数据分析 agent 与文献检索 agent 之间的共享状态，用于在 200 次 rollout 内保持目标一致性（这是"连贯性"机制，不是"正确性"机制）。
2. **强制溯源**：所有报告陈述必须引用到具体代码行或一手文献段落。官方原文："every conclusion in a Kosmos report can be traced through our platform to the specific lines of code or the specific passages in the scientific literature that inspired it, ensuring that Kosmos' reports are fully auditable at all times."
3. **无自动化正确性门**。准确率是**事后由专家人工抽样审计**得到的，不是运行中的闸门。

**独立评估状况**：**没有真正独立的第三方审计**。79.4% 出自 Kosmos 论文自身，评审者被描述为 "expert scientist evaluators" / 摘要中的 "independent scientists"，但论文未披露评审人数、与作者的利益关系、以及三份"代表性报告"由谁挑选。这是本维度最需要打折的一个数字。

**作者自陈的局限**（一手，逐字）："a propensity to conflate statistically significant results with scientifically valuable ones"、"tends to make excessively strong claims and can sometimes veer in unexpected trajectories"；公司博客："it also often goes down rabbit holes or chases statistically significant yet scientifically irrelevant findings"。

**设计上最关键的一点**：79.4% 是三个**不同口径**的聚合——数据类量的是 *reproducible*（可重跑），文献类量的是 *validated with primary sources*（能定位到一手文本），综合类量的才是 *accurate*（准确）。论文没有说明聚合方式。

### B. FutureHouse 其余谱系：PaperQA2 / WikiCrow / Robin / Aviary

- PaperQA2 一手：arXiv:2409.13740 — https://arxiv.org/abs/2409.13740 · HTML https://arxiv.org/html/2409.13740v2
- Robin 一手：arXiv:2505.13400 — https://arxiv.org/abs/2505.13400 ；Nature 2026 版 https://www.nature.com/articles/s41586-026-10652-y （正文付费墙，本轮未读到）

**PaperQA2 的验证机制**：这是本维度里**验证方法学最扎实**的一个。它做了严格的人机对照：9 位领域专家，每人一个 LitQA2 子集，约一周时间，全互联网 + 机构期刊订阅，按题计酬（$3–12/题）并带表现激励。关键是它**区分 precision 与 accuracy**——允许模型回答"信息不足"，precision 只在给出答案的问题上算。这个"允许弃答"的设计正是本项目该抄的：**弃答不是失败，把弃答混进准确率才是失败**。

矛盾检测：在随机生物学论文子集上每篇发现 2.34±1.99 条矛盾，其中 **70% 经人类专家确认**——即约 30% 是误报。这是"agent 发现的问题需要人类复核"的一个真实基线。

WikiCrow 的对照做得同样干净：375 条语句，推理错误 12 vs 人类 Wikipedia 的 26（p=0.0144），但**引用错误率无显著差异（p=0.21）**——即"比 Wikipedia 准"这个说法在推理维度成立、在引用维度不成立。

**Robin**：agent 产出全部假设、实验方案、数据分析和图表，发现 ripasudil（ROCK 抑制剂）可用于干性 AMD。这是本维度里**唯一一条真正的 Tier I/II 级 oracle**——湿实验物理测量。但摘要未言明湿实验由谁执行；从"Robin 产出方案"的措辞推断是人类执行（**这是我的推断，非源陈述**）。含义：Robin 的可信度来自实验室，不来自 agent 架构。

### C. Sakana AI Scientist v1 / v2

- v1 一手：arXiv:2408.06292 — https://arxiv.org/html/2408.06292v3
- v2 一手：arXiv:2504.08066 — https://arxiv.org/html/2504.08066v1
- 公司页：https://sakana.ai/ai-scientist-first-publication/ · https://sakana.ai/ai-scientist-nature/ （Nature 2026-03-26，DOI s41586-026-10265-5）

**自验证机制**：
1. **自动 LLM 评审员**（v1）：GPT-4o，在 500 篇 ICLR 2022 OpenReview 论文上，阈值 6，accuracy 0.66±0.04 / F1 0.57±0.05 / AUC 0.65±0.04；对照 NeurIPS 2021 一致性实验的人类 balanced accuracy 0.66。单次评审成本 $0.25–0.50。
2. **VLM 视觉反馈**（v2）：对生成的图表做即时反馈并迭代修图/改 caption。
3. **agentic tree search**（v2）：以实验指标驱动的分支搜索——属于综述定义的"机械闭环"（mechanical loop），内部指标触发重跑，无外部 oracle。

**这套机制的实证失败**（一手，v2 论文自陈）：
- 被接收的那篇论文实验存在 **约 57% 的训练/测试集重叠**；
- "The AI Scientist-v2 occasionally introduced inaccuracies in citations, similar to the well-known 'hallucination' issue"；
- 图 3 的 caption 错误解读了 validation loss；
- 系统 "sometimes lacked the detailed methodological rigor and in-depth analysis typically required for acceptance at leading main conferences"。

**人类介入的真实程度**（必须记住，因为这决定了 6.33 分怎么读）：Sakana 自己从生成结果里**人工挑选了 top 3** 提交；被接收的那篇后来被主动撤回；Sakana 明说 workshop 接收率 60–70% 而主会 20–30%，且三篇"none of them passed our internal bar for an ICLR conference track publication"。

**ScientistOne 的第三方审计给 Sakana v2 的成绩**：幻觉引用 0/159（0%，全场最佳），但分数复核通过 5/12（42%，与最差并列），方法-代码一致性 5/15（33%）。

### D. Google AI co-scientist / Science One Framework

- co-scientist 一手：arXiv:2502.18864 — https://arxiv.org/abs/2502.18864 ；Nature 2026 版 https://www.nature.com/articles/s41586-026-10644-y （付费墙，本轮未读到正文）
- 官方博客：https://research.google/blog/accelerating-scientific-breakthroughs-with-an-ai-co-scientist/
- **Science One Framework（2026-07-30）**：https://research.google/blog/science-one-framework-a-verifiable-autonomous-research-framework-via-chain-of-evidence/
- ScientistOne 论文：arXiv:2605.26340 — https://arxiv.org/html/2605.26340

**co-scientist 的自验证机制**：六个专门 agent（Generation / Reflection / Ranking / Evolution / Proximity / Meta-review）。核心是 **Reflection agent 做深度验证**（把假设拆成子假设逐条检查）+ **Ranking agent 用 Elo 锦标赛做成对比较**（按科学有效性、新颖性、实验可行性打分）。Elo 随 test-time compute 上升，且与 GPQA diamond 上的正确率正相关（未给系数）。

**这个机制的软肋**（综述 arXiv:2608.05179 的判断）：co-scientist 达到了 ideation 阶段罕见的"novelty-as-valid"，但**易受 LLM-judge 偏置与自偏好（self-preference）失败**影响。Elo 是自评指标——同一族模型既当选手又当裁判。

**真正的 oracle 在体外**：三项生物医学验证（AML 药物重定位、肝纤维化靶点、抗菌耐药 cf-PICI 机制）全部靠**湿实验**兜底。这一点与 Robin 同构：可信度来自实验室。

**Science One / Chain-of-Evidence — 本维度对我们最有参考价值的机制设计**：
原则逐字："every claim in a research artifact must carry a recorded evidence chain (completeness), and each chain must genuinely support the claim it is attached to (correctness)."
三模块：Problem Investigator（引用只能来自 Semantic Scholar API 调用，不许来自模型记忆，最多 100 篇 PDF 建引文图）/ Discovery Engine（并行 explore-exploit，评估器原始输出编成**只读记录**）/ Paper Writer + **Claim Verifier**（每条 claim 在渲染前对照其声明来源逐条检查）。
四项自动审计：**分数复核（独立重跑代码）、规范违反检测、引用核验（对学术 API）、方法-代码一致性（LLM judge 比对正文与代码）**。
分数复核的操作定义（逐字级）：提交的解法代码在基准的官方评估器上**独立重跑**，与论文声称的数值比较，容差为 **max(1%, 3σ/|s̄|)** 以吸收评估器方差。

### E. Agent Laboratory / AgentRxiv

- Agent Laboratory：arXiv:2501.04227 — https://arxiv.org/abs/2501.04227
- AgentRxiv：arXiv:2503.18102 — https://arxiv.org/abs/2503.18102

**Agent Laboratory 的验证机制 = 人**。摘要明说"enabling users to provide feedback and guidance at each stage"，并发现 "(3) Human involvement, providing feedback at each stage, significantly improves the overall quality of research"。即：它不声称自动验证，它声称的是把人放回环里能提质。同时报出 84% 的成本下降（相对"先前自主研究方法"，摘要未指明具体基线）。

**AgentRxiv 的验证机制 = 无**。这是本维度最重要的**反面教材**：多个 agent lab 共享 preprint 池以互相踩肩前进，MATH-500 上相对提升 11.4%（有先前研究 vs 孤立）、多实验室协作 13.7%。摘要**完全没有提到任何入库前的质量门**。一个没有验证闸的共享池，会把一个 lab 的错误结论以"可引用的先前研究"身份分发给全部并行 lab。这直接对应本项目的多 loop 并行共享设计。

### F. AutoSurvey 谱系

- AutoSurvey（NeurIPS 2024）：arXiv:2406.10252 — https://arxiv.org/html/2406.10252v2
- 后续：AutoSurvey2（arXiv:2510.26012）、DeepSurvey（arXiv:2605.29522）、SGSimEval（arXiv:2508.11310）

**自验证机制 = Multi-LLM-as-Judge**（GPT-4 + Claude-3-Haiku + Gemini-1.5-Pro），评引用质量（recall / precision）与内容质量（coverage / structure / relevance）。
**这套判官与人类的一致性只到中等**：与 3 位博士生的排名之间，混合模型取得最高 Spearman ρ = **0.5429**。三人、中等相关——这条链子承不起"客观门"的重量，只能当筛子。

### G. CycleResearcher / CycleReviewer

- 一手：arXiv:2411.00816 — https://arxiv.org/abs/2411.00816 （ICLR 2025）

**机制**：CycleResearcher 写论文、CycleReviewer 评审，用评审信号反过来训练生成器（研究-评审闭环）。Review-5k 数据集：4,991 篇 ICLR 2024 论文、16,000+ 条评审意见。CycleReviewer 在预测论文分数上比单个人类评审 MAE **降低 26.89%**。

**结构性问题（本项目必须引以为戒）**：报告中的对比分数——CycleResearcher 论文 5.36 vs 人类 preprint 5.24 vs 已接收论文 5.69——**全部来自"模拟评审"，即同一实验室的 CycleReviewer 自评**。摘要未给任何独立人类评审对生成论文的评分。这是**循环自证**：用自家判官证明自家生成器超过了人类 preprint。任何"用自建 reviewer agent 给自建 writer agent 打分"的架构都会退化成这个形状。

### H. Zochi（Intology）

- GitHub：https://github.com/IntologyAI/Zochi
- 公司博客 https://www.intology.ai/blog/zochi-acl 本轮返回 **HTTP 403**，未能读到一手
- LessWrong 转载（Intology 自撰，2025-05-31）：https://www.lesswrong.com/posts/LtsgfGsXpiLTSGpaW/zochi-publishes-a-paper

**事实**：Tempest（多轮越狱树搜索）被 ACL 2025 主会接收——这是真人评审，比 workshop 门槛高。Tempest 自身结果：GPT-3.5 100% 成功率 / 平均 44.4 次查询；GPT-4 97% / 84.2；Llama-3.1 97% / 51.8。另有 CS-ReFT 进 ICLR 2025 SCOPE workshop。

**自验证机制**：仓库自陈"Zochi achieves an average score of 7.67 on the NeurIPS guidelines scale, significantly exceeding the human acceptance threshold of 6"——**这是自动评审（自家 LLM 评审员）给的分**，与 ACL 的人类评审是两码事。仓库里没有关于"谁跑的实验、谁写的 rebuttal、谁核对了结果"的明确陈述。Intology 在 LessWrong 帖里说 "human researchers remain as authors and maintain responsibility for validating methods, interpreting results, and ensuring ethical compliance"，并说 "We submitted only a single paper because we deemed this particular contribution valuable enough to warrant publication"。

**独立评估**：本轮**未能获得任何真正独立的第三方评估**。所有可及的中文/英文二手页（cspaper、iNEWS、cybercorsairs）都在复述 Intology 自己的博客——这正是"虚假独立佐证"：三个页面 = 一个上游源。

### I. DeepScientist

- 一手：arXiv:2509.26603 — https://arxiv.org/abs/2509.26603 （ICLR 2026 接收，https://iclr.cc/virtual/2026/poster/10008492）

**机制**：把发现形式化为贝叶斯优化问题，用"hypothesize → verify → analyze"的**分层评估**（越往上越贵）+ 累积的 Findings Memory 平衡探索/利用。规模：~5,000 个想法 → ~1,100 个进入实验验证 → 20,000+ GPU 小时，在三个前沿 AI 任务上超过人类 SOTA 183.7% / 1.9% / 7.9%。

**关键反差**：DeepScientist 是"验证意识最强"的系统之一（分层评估就是为了筛掉坏想法），但在 ScientistOne 的第三方审计里它的**幻觉引用率是全场最高的 42/201（21%）**，方法-代码一致性只有 5/15（33%）——尽管它的分数复核通过率高达 11/12（92%）。**实验做对了，论文写歪了。** 这条对我们极重要：验证管线只覆盖了"实验"，没覆盖"从实验到文本"的那一跳。

### J. 元文献：验证缺口综述与基准

**综述 arXiv:2608.05179（2026-08）** — https://arxiv.org/html/2608.05179v1
本维度最核心的一份元文献。给出两把尺子：
- **八级验证阶梯**：Tier I 可靠形式化验证器（Lean 等定理证明）→ Tier II–III 可执行测试与物理 oracle → Tier V 代理奖励与学习到的验证器 → Tier VI–VIII 人类判断、弱信号、模型意见。
- **L0–L5 自治度**：L0 辅助 / L1 工具增强 / L2 阶段局部 / L3 全流水线（想法到报告）/ L4 闭环（再分 **L4-m 机械** 与 **L4-v 外部验证**）/ L5 开放式（尚属愿景）。
- **反馈类型三分**：外部验证（物理测量或独立 oracle 把关迭代）/ 机械（内部指标、基准分数或自动评审触发下一步）/ 作者声称（无外部证据的闭环）。
在 9 个 L4 闭环系统里：**7 个机械 / 1 个外部验证（CAMEO，前 LLM 时代，物理测量）/ 1 个仅作者声称**。
它开出的是**七维审计清单**（自动化了哪些阶段、自治度如何操作化、评估方法、开放了哪些 artifact、HITL 入口、新颖性验证方法、结果筛选策略），不是一个 claim 图框架——**与本项目"框架失败、清单+门存活"的先验一致**。
注意其自身弱点：复核者间一致性总体仅 65%（artifact 维度 90%，但 autonomy level 只有 50%）。

**ScientistOne CoE 审计（arXiv:2605.26340）** — 75 篇论文 / 5 系统 / 5 任务 / 每系统每任务 3 seeds。详见核验表。

**MLR-Bench（arXiv:2505.19955，NeurIPS 2025 D&B）** — 201 个任务源自 NeurIPS/ICLR/ICML workshop；MLR-Judge = LLM 评审 + 精心设计的评分表。判官与人类的差距在统计上不大于人类之间的差距（Mann-Whitney U，五维度均无 0.05 显著差异，10 位有顶会评审经验的领域专家）——但**两边给的分都低**：soundness 维度 LLM 判官 3.73/10、人类 4.42/10。

**PaperBench（OpenAI，arXiv:2504.01848）** — 20 篇 ICML 2024 Spotlight/Oral，8,316 个可评分 rubric 叶节点。最重要的是**人机时间曲线**：3 篇子集上，人类 ML PhD 48 小时后 41.4%，o1 只有 26.6%——**AI 早期领先、人类在长时间尺度反超**。

**CORE-Bench（arXiv:2409.11363）** — 270 任务 / 90 篇论文 / CS+社科+医学三学科，专测**计算可复现性**（给了仓库能不能重跑出结果）。最难档最佳 agent 仅 21%。

**AstaBench（AI2，arXiv:2510.21652）** — 2400+ 问题、57 个 agent、22 个 agent class，强调**成本受控、可复现**的评测环境与生产级检索工具。结论："AI remains far from solving the challenge of science research assistance."

**SoundnessBench for AI Scientists（arXiv:2605.30329，2026-05-28，UMD）** — 1,099 条研究提案（458 低严谨 / 641 高严谨），测 LLM 能否在**执行之前**判断方法论是否站得住。这是"预执行第一道闸"的能力测量。

**Kirgis et al.（arXiv:2607.27191，2026-07）** — 给前沿 agent 6 天、全互联网、专用算力、约 $3,000 模型额度，做两篇当时未发表的会议投稿题目。**两篇均被原论文作者判为明确拒稿（总分 2/6 与 1/6）**。五类失败：对可发表标准的判断力不足、面对研究设计缺陷时缺乏创造性应对、从死胡同回溯无效、资源意识差、指令漂移。

**The 17% Gap（arXiv:2601.17431）** — 5,514 条引用 / 50 篇 AI 综述（2024-09 至 2026-01），五阶段核验流水线。见核验表中的 `corrected` 行。

---

## 载荷数字核验表

> 状态定义：`verified` = 已读一手源并可引用；`corrected` = 常见转述口径错误，此处给正确值；`unverified` = 未触达一手源；`inference` = 我的推算，非源陈述。

| 数字 | 口径三元组（指标 / 样本条件 / 对比基准） | 状态 | 一手出处 |
|---|---|---|---|
| **79.4%** | 报告中语句被专家评为 "Supported" 的比例 / 从 **3 份"代表性报告"抽取的 102 条语句** / **无对照组**（无人类基线、无其他系统） | verified | arXiv:2511.02824 摘要+正文 |
| **85.5%** | 数据分析类语句**可复现（reproducible）**比例 / 上述 102 条中的数据类子集（分项计数未披露） / 无对比 | verified | arXiv:2511.02824 |
| **82.1%** | 文献类语句**能用一手文献验证**比例 / 同上文献类子集 / 无对比 | verified | arXiv:2511.02824 |
| **57.9%** | 综合/解释类语句**准确**比例 / 同上综合类子集 / 无对比 | verified | arXiv:2511.02824 |
| 「79.4% of **conclusions**」 | 公司博客口径 → 一手论文是「79.4% of the **statements**」；conclusion ≠ statement，博客口径被放大 | **corrected** | edisonscientific.com/news/announcing-kosmos vs arXiv:2511.02824 |
| 「79.4% 是单一准确率」 | 实为三个**不同指标**（reproducible / validated-with-primary-sources / accurate）的聚合，论文未说明聚合方式 | **corrected** | arXiv:2511.02824 |
| **6 个月** | 「一次 20-cycle 运行 ≈ 合作者本人多少研究时间」/ **7 位 beta 用户问卷自估**（主观）；旁证：3 项独立复现各对应约 4 个月工作量；折算法：15 分钟/篇 × 1500 篇 + 2 小时/条分析轨迹 ≈ 4.1 个月 / 无对照实验 | verified（但**自报口径**） | edisonscientific.com/news/announcing-kosmos |
| **200 / 42,000 / 1,500 / ≤12h / 20 cycles** | 单次运行的 rollout 数 / 平均执行代码行数 / 阅读论文数 / 运行时长上限 / 测试过的最大 cycle 数 | verified | arXiv:2511.02824 摘要 |
| **$200/run** | Kosmos 商业定价（200 credits × $1/credit），学术界有免费额度，2025-11-05 上线 | verified | edisonscientific.com/news/announcing-kosmos |
| **7 项发现 = 3 复现 + 4 新** | 3 项独立复现了运行时未接触的 preprint/未发表手稿，4 项为新贡献 / 由作者认定 / 无第三方裁定 | verified | arXiv:2511.02824 摘要 |
| **6, 7, 6 → 均分 6.33** | ICLR 2025 ICBINB workshop 三位评审给分 / 1 篇被接收论文 / 约排在全部投稿前 45% | verified | sakana.ai/ai-scientist-first-publication/ ; arXiv:2504.08066 |
| **3 投 1 中** | 提交数 / 接收数 / 且这 3 篇是 Sakana **人工从生成结果中挑出的 top 3**；接收后主动撤回 | verified | sakana.ai/ai-scientist-first-publication/ |
| **60–70% vs 20–30%** | workshop 接收率 vs 主会接收率 / Sakana 自述的量级 / 用于说明"这是 workshop 门槛不是主会门槛" | verified | sakana.ai/ai-scientist-first-publication/ |
| **~57%** | **被接收论文实验中的训练/测试集重叠比例** / 作者事后自查 / 三位人类评审**未发现** | verified | arXiv:2504.08066（v2 论文自陈） |
| **0.66±0.04 / 0.57±0.05 / 0.65±0.04** | AI Scientist v1 自动评审员的 accuracy / F1 / AUC；**500 篇 ICLR 2022 OpenReview 论文，GPT-4o，接收阈值 6** / 对比 NeurIPS 2021 一致性实验的人类 balanced accuracy 0.66 | verified | arXiv:2408.06292v3 |
| **69% balanced accuracy** | Sakana Nature 摘要页对自动评审的表述，与 arXiv v3 的 0.66 不一致；未能读到 Nature 正文核实 | **unverified**（口径冲突） | sakana.ai/ai-scientist-nature/ vs arXiv:2408.06292v3 |
| **$10–15/篇；$0.25–0.50/次评审** | AI Scientist v1 每篇论文的总运营成本摊销 / 单次自动评审的 API 成本 | verified | arXiv:2408.06292v3 |
| **2026-03-26 / s41586-026-10265-5** | The AI Scientist 在 Nature 的发表日与 DOI | verified | sakana.ai/ai-scientist-nature/ |
| **75 / 5 / 5 / 3 seeds** | ScientistOne CoE 审计样本：论文数 / 系统数 / 任务数 / 每系统每任务的种子数 | verified | arXiv:2605.26340 |
| **0/337 (0%)** | ScientistOne 幻觉引用数/总引用数 / CoE 审计条件 / 对比下列基线 | verified | arXiv:2605.26340 |
| **42/201 (21%)** | **DeepScientist** 幻觉引用率（全场最差） / 同上 / — | verified | arXiv:2605.26340 |
| **21/222 (9.5%) / 3/196 (1.5%) / 0/159 (0%)** | AI-Researcher / AutoResearchClaw / **Sakana AI-Scientist v2** 的幻觉引用率 | verified | arXiv:2605.26340 |
| **12/12, 11/12, 9/12, 5/12, 5/12** | 分数复核通过率（ScientistOne 100% / DeepScientist 92% / AI-Researcher 75% / AutoResearchClaw 42% / **Sakana v2 42%**）/ **分母仅 12** / 定义=解法代码在官方评估器上独立重跑，与论文声称值在 **max(1%, 3σ/\|s̄\|)** 容差内比对 | verified | arXiv:2605.26340 |
| **14/15, 5/15, 12/15, 3/15, 5/15** | 方法-代码一致性（93% / DeepScientist 33% / 80% / AutoResearchClaw 20% / Sakana v2 33%）/ **分母仅 15** / 由 LLM judge 比对正文与代码 | verified | arXiv:2605.26340 |
| **2026-07-30** | Google Science One Framework 发布日 | verified | research.google/blog/science-one-framework-... |
| **83% (20/24) / 71% (17/24) / 38% (9/24) / 67% (16/24) / 88% (21/24) / 38% (9/24)** | 代码开放 / prompt 开放 / **种子或执行轨迹开放** / 结果筛选策略披露 / 至少一个 HITL 入口 / **新颖性验证方法披露**；分母=**24 个全文编码的可运行系统** / 无时间序列对比 | verified | arXiv:2608.05179 |
| **7 / 1 / 1（共 9）** | L4 闭环系统中：机械闭环 / 外部验证闭环（仅 CAMEO，前 LLM 时代物理测量）/ 仅作者声称 | verified | arXiv:2608.05179 |
| **65%（artifact 90%、autonomy 50%）** | 该综述**自身**的复核者间一致性 / 10 个系统、由独立第二编码者仅凭摘要编码 / — （即该综述的编码结论本身要打折） | verified | arXiv:2608.05179 |
| **201 个任务** | MLR-Bench 规模 / 源自 NeurIPS+ICLR+ICML workshop / — | verified | arXiv:2505.19955 |
| 「80% 的案例产生伪造结果」 | 实为 **"8 out of 10 tasks conducted by Claude Code"**——**n=10、单一 coding agent**，判据=报告结果基于合成或占位数据而非真实执行；**不是 201 题基准的整体比例** | **corrected** | arXiv:2505.19955v2 |
| **3.73/10 vs 4.42/10** | soundness 维度：MLR-Judge 均分 vs 人类评审均分 / AI 生成论文 / 二者均低 | verified | arXiv:2505.19955v2 |
| **五维度均 p>0.05** | MLR-Judge 与人类的分歧 vs 人类之间的分歧（Mann-Whitney U）/ **10 位有顶会评审经验的领域专家** / 结论=判官不比人类之间更不一致（但不代表判官准） | verified | arXiv:2505.19955v2 |
| **20 篇 / 8,316** | PaperBench：ICML 2024 Spotlight+Oral 论文数 / rubric 可评分叶节点数 | verified | arXiv:2504.01848 |
| **21.0%** | PaperBench 最佳 agent 平均复现分（Claude 3.5 Sonnet New + BasicAgent）/ 全部 20 篇 / — | verified | arXiv:2504.01848 |
| **24.4% → 26.0±0.3** | o1 + IterativeAgent，12 小时限 → 36 小时限 | verified | arXiv:2504.01848 |
| **41.4% vs 26.6%** | **人类 ML PhD 48 小时后的复现分 vs o1 的复现分** / **3 篇论文子集** / AI 早期领先、人类长时间反超 | verified | arXiv:2504.01848 |
| **8 位 / 4 篇 / 3 次 / 4 周** | PaperBench 人类基线设置：ML 博士在读或已毕业人数 / 论文子集 / 每篇独立复现次数 / 时间窗口 | verified | arXiv:2504.01848 |
| **F1 0.83 @ $66/篇** | PaperBench 自动判官（o3-mini + SimpleJudge）对照人类专家评分的 F1 与每篇成本 | verified | arXiv:2504.01848 |
| **43.4%** | PaperBench **Code-Dev** 变体上 o1 的得分（只评代码开发、不执行验证）/ 与全量 21–26% 对照 → 去掉执行验证分数翻倍 | verified | arXiv:2504.01848 |
| **270 / 90 / 3** | CORE-Bench：任务数 / 论文数 / 学科数（CS、社科、医学） | verified | arXiv:2409.11363 |
| **21%** | CORE-Bench 最难档（Hard）最佳 agent 准确率 / — / 无人类基线（论文未给） | verified | arXiv:2409.11363 |
| **2400+ / 57 / 22** | AstaBench：问题数 / 评测 agent 数 / agent class 数 | verified | arXiv:2510.21652 |
| **85.2%±1.1% vs 73.8%±9.6%** | **LitQA2 precision**（=给出答案的问题中正确的比例，排除"信息不足"）：PaperQA2 vs **9 位人类专家**；t(8.6)=3.49, **p=0.0036** → 显著超人 | verified | arXiv:2409.13740 |
| **66.0%±1.2% vs 67.7%±11.9%** | **LitQA2 accuracy**（=全部问题中正确的比例，含弃答）：PaperQA2 vs 人类；t(8.5)=−0.42, **p=0.66 → 无显著差异** | verified | arXiv:2409.13740 |
| 「PaperQA2 的 **accuracy** 高于 PhD/博后研究者」 | **口径错误**：超人的是 **precision**；accuracy 上 66.0% vs 67.7% 无显著差异。这正是"precision 被报成 accuracy"的同型错误 | **corrected** | arXiv:2409.13740 vs futurehouse.org 公告页表述 |
| **9 位 / 约 1 周 / $3–12 每题** | LitQA2 人类基线条件：专家人数 / 每人一个子集的作答时间 / 计酬与激励；全互联网+机构订阅、无限制 | verified | arXiv:2409.13740 |
| **12 vs 26（p=0.0144）** | WikiCrow vs 人类 Wikipedia 的**推理错误**数 / **375 条语句** / — | verified | arXiv:2409.13740 |
| **引用错误 p=0.21（无差异）；未引用语句 3.5% vs 13.6%（p<0.001）；精确率 86.1% vs 71.2%（p=0.0013）** | WikiCrow vs 人类 Wikipedia，同 375 条语句样本 —— 即"比 Wikipedia 准"在推理与覆盖上成立，**在引用错误率上不成立** | verified | arXiv:2409.13740 |
| **2.34±1.99 条/篇，其中 70% 经人确认** | PaperQA2 矛盾检测：每篇发现的矛盾数 / 随机生物学论文子集 / 人类专家确认率 → 约 30% 误报 | verified | arXiv:2409.13740 |
| **17.0%（95% CI 16.0–18.0%）** | phantom rate（无法解析到任何数字对象的引用）/ **5,514 条引用、50 篇 AI 综述，2024-09 至 2026-01** / **无人类撰写综述的对照组** | verified | arXiv:2601.17431 |
| **78.5% / 16.4% / 5.1%** | 上述 939 条 phantom 的构成：**解析语法伪影 / 断链（DOI→404）/ 纯幻觉（Ghosts）** | verified | arXiv:2601.17431 |
| 「AI 综述有 17% 的幻觉引用」 | **口径错误**：17% 是"无法解析"，其中 78.5% 是 PDF 解析伪影；真幻觉只占 phantom 的 5.1% | **corrected** | arXiv:2601.17431 |
| **≈0.87% / ≈3.7%** | 我的推算：纯幻觉 = 5.1%×17.0% ≈ 0.87% 全部引用；纯幻觉+断链 ≈ 3.7% | **inference**（非源陈述） | 由 arXiv:2601.17431 数据推算 |
| **4/20 (20%) 与 3/8 (37.5%)，合计 7/28** | CAWM（结论对、机制错）发生率：主模型 episode / 跨模型 episode / **5 个 agent、28 次粒子鉴别发现尝试** | verified | arXiv:2606.23175 |
| **全部命中** | 两个轻量检查（单步 regime-shift 检查 + 已知答案时的重算检查）标记出的 CAWM 案例比例 / 同上 28 次尝试 / — | verified | arXiv:2606.23175 |
| **1,099（458 低严谨 / 641 高严谨），12 个前沿 LLM** | SoundnessBench-for-AI-Scientists 规模与被测模型数（含 GPT-5.4、Claude-Opus-4.6、Gemini 系列） | verified | arXiv:2605.30329v1 |
| **74.0% → 19.9%，召回 36.1%** | 对低严谨提案的**假阳性率**：标准提示 → 激进提示；代价是高严谨提案**召回崩到 36.1%** / 同上 1,099 条 / 说明判官阈值是不可同时优化的权衡 | verified | arXiv:2605.30329v1 |
| **2/6 与 1/6** | Kirgis 等：两篇 agent 论文由**原论文作者**按顶会标准评出的总分（均为明确拒稿）/ 6 天、全互联网、专用算力、约 **$3,000** 模型额度、2 个未发表投稿题目 / 对比顶会可发表标准 | verified | arXiv:2607.27191（经 techxplore 转述的标题/DOI，正文未直接读到 → 见未决） |
| **~5,000 / ~1,100 / 20,000+ GPU 小时** | DeepScientist：生成想法数 / 进入实验验证数 / 算力消耗 | verified | arXiv:2509.26603 摘要 |
| **183.7% / 1.9% / 7.9%** | DeepScientist 在三个前沿 AI 任务上超越人类 SOTA 的幅度 / **三个任务的名称与各自基线口径本轮未从一手取得** / 声称对比"人类设计的 SOTA 方法" | **unverified（口径缺失）** | arXiv:2509.26603 摘要（任务名与基线未取得） |
| **26.89%** | CycleReviewer 在**预测论文分数**上相对单个人类评审的 MAE 降幅 / Review-5k（4,991 篇 ICLR 2024 论文、16,000+ 条评审）/ 对比"单个人类评审" | verified | arXiv:2411.00816 |
| **5.36 vs 5.24 vs 5.69** | CycleResearcher 论文 / 人类 preprint / 已接收论文的分数 —— **全部由自家 CycleReviewer 的"模拟评审"给出**，摘要未给独立人类评审 → 循环自证 | verified（但**自评口径**） | arXiv:2411.00816 |
| **82.25±3.64 / 77.41±3.84 vs 人类 86.33 / 77.78** | AutoSurvey 64k-token 综述的引用 recall / precision vs 人类撰写综述基线 —— **precision 打平，recall 低约 4 个点** | verified | arXiv:2406.10252v2 |
| **ρ = 0.5429** | AutoSurvey 的 Multi-LLM-as-Judge（GPT-4+Claude-3-Haiku+Gemini-1.5-Pro）与 **3 位博士生**排名之间的最高 Spearman 相关 / 中等相关 | verified | arXiv:2406.10252v2 |
| **84%** | Agent Laboratory 相对"先前自主研究方法"的成本降幅 / **摘要未指明具体基线系统** / — | verified（基线未明） | arXiv:2501.04227 |
| **11.4% / 13.7%** | AgentRxiv：有先前研究 vs 孤立的 MATH-500 **相对**提升 / 多实验室协作的相对提升 / **摘要未给绝对准确率，也未提任何入库质量门** | verified | arXiv:2503.18102 |
| **15 个 / 其中 11 个** | Google co-scientist 专家策划的开放研究目标数 / 其中做新颖性与影响力评分的子集 / 专家人数未披露 | verified | research.google 官方博客 |
| **p < 0.01** | 肝纤维化：AI 建议的全部药物在人肝类器官上的活性显著性 / — / 无阴性对照细节 | verified | research.google 官方博客 |
| **7.5 倍** | Robin/ripasudil 对视网膜色素上皮吞噬作用的提升倍数 —— **仅见于二手报道（GIGAZINE/LinkedIn），arXiv 摘要未给，Nature 正文付费墙** | **unverified** | 二手；arXiv:2505.13400 摘要未含 |
| **8/10、平均 7.67** | Zochi 的 Tempest 与 CS-ReFT 得分及平均分 —— **由自家自动评审按 NeurIPS 量表给出**，不是 ACL 人类评审分 | verified（**自评口径**） | github.com/IntologyAI/Zochi |
| **top 8.2%、meta-review 4/5** | Zochi ACL 2025 投稿的百分位与元评审分 —— intology.ai 博客返回 403，全部可及页面均复述该单一上游源 | **unverified（虚假独立佐证风险）** | 未触达一手 |
| **100% / 44.4；97% / 84.2；97% / 51.8** | Tempest 越狱成功率与平均查询次数：GPT-3.5 / GPT-4 / Llama-3.1 | verified | github.com/IntologyAI/Zochi |

---

## 对本项目的设计含义

**1. 把"状态"做成三态而不是二态，并且按 claim 类型分别定门。**
Kosmos 的 79.4% 是三个不同口径的聚合，这正是我们要避免的东西。落地形状：
- `data-claim` → 门 = **可重跑**（脚本 + 种子 + 期望值 + 显式容差）；
- `citation-claim` → 门 = **可定位**（能落到一手 PDF/HTML 的具体段落，且该段落确实支持这句话）；
- `inference-claim` → **没有 `verified` 这一档**，只有 `inferred`（由 ≥2 条已验证 claim + 显式推理链得出）或 `unverified`。
理由：57.9%（Kosmos 综合类）、20–37.5%（CAWM）、74%（SoundnessBench 假阳性）三条独立证据都指向同一处塌陷。**报告一个横跨三类的"总准确率"本身就是口径造假。**

**2. 抄 Science One 的分数复核形状，包括容差公式。**
产物契约 = `{可执行脚本, 期望值, 容差}`，门 = 独立重跑落在容差内，容差取 **max(1%, 3σ/|s̄|)**。不写容差的重跑门会被随机性变成噪音门。这是本轮唯一一个被明确操作化的客观门定义，直接可用。

**3. 引用门与重跑门必须是两条独立的流水线，分别报数。**
Sakana v2：引用 0/159 完美、重跑 5/12（42%）。DeepScientist：重跑 11/12（92%）、引用 42/201（21%）。两个方向的失败在真实系统里同时存在且互不预测。合成一个"可信度分"会同时掩盖两者。

**4. 引用核验必须先分离"解析失败"和"真幻觉"。**
*The 17% Gap* 里 78.5% 的"幽灵引用"其实是 PDF 解析伪影。如果我们不做这个分离，我们会把自己的 PDF 抽取链路 bug 报成模型幻觉，然后据此做错误的架构决策。落地：核验流水线至少要有 **标识符抽取 → 直接解析（HTTP/DOI/arXiv）→ 熵过滤（识别抽取伪影）→ 模糊标题匹配 → 分档** 五段，且分档结果里 `parse-artifact` 与 `hallucinated` 必须是两个不同的桶。

**5. LLM-as-judge 只能当路由器/排序器，绝不能当 pass/fail 门。**
证据链：AutoSurvey 判官与人类 ρ 仅 0.54（且人类只有 3 位）；MLR-Judge 与人类无显著差异但两者都低（3.73 vs 4.42/10）；SoundnessBench 显示调一下提示，假阳性从 74.0% 降到 19.9%，但召回从高位崩到 36.1%——**判官的阈值是一个不可同时优化的权衡，因此不存在"正确的判官阈值"**。凡是 pass/fail 的地方，必须是可重跑的机械门或人类。

**6. 绝不建"自家 writer + 自家 reviewer 互评"的闭环来生产可信度。**
CycleResearcher 的 5.36 > 5.24 全部来自自家 CycleReviewer；Zochi 的 7.67 来自自家自动评审；co-scientist 的 Elo 是自评指标（综述明确点名 LLM-judge 偏置与自偏好风险）。这类数字在对外时会被读成"超过人类"，但它只是"超过自家判官眼里的人类"。我们的 keep-if-better loop 如果用 LLM 打分做 keep 判据，就必须显式声明这是**机械闭环（L4-m）而非外部验证闭环（L4-v）**，并且不能把 loop 分数写进最终产物当作证据。

**7. 并行 loop 之间的共享池必须有验证闸。**
AgentRxiv 是明确的反面样本：无任何质量门的共享 preprint 池，配上 11.4%/13.7% 的相对提升宣传。我们的多 loop 架构必须做到：**只有 `verified` 的 claim 能无标签进入共享池；`unverified` / `inferred` 进入时必须带状态标签流转，且下游引用它时状态不可升级**（状态只能单调下降）。

**8. 记录"总尝试数 + 筛选准则"，把它写进产物。**
Sakana 从生成结果里人工挑 top 3 才有那个 6.33。综述把"结果筛选策略披露"单列为七维之一，而披露率只有 67%。我们的 keep-if-better loop 天然产生大量尝试——不记录尝试总数与筛选准则，我们的产物就带着一个隐藏的 selection bias。**产物里应有一行：`attempts: N, kept: 1, criterion: <显式>`。**

**9. artifact 契约里种子和执行轨迹是必需项，代码只是及格线。**
83% 开代码但只有 38% 开种子/轨迹——综述明确称后者是**复现的约束项（binding constraint）**。我们的每个 data-claim 附件必须是 `{code, env spec, seed, 完整执行轨迹}`，缺一不可。

**10. 诚实标定我们能达到的验证等级：Tier II–III，不是 Tier I。**
八级阶梯里，Tier I 是形式化验证器，Tier II–III 是可执行测试与物理 oracle。24 个系统里只有 1 个有外部物理 oracle（且是前 LLM 时代的 CAMEO）。我们没有湿实验，也不做定理证明——我们能给的最强证据是**代码重跑 + 一手文本定位**。文档里应该直说这一点，而不是暗示更高。这本身就是产品可信度的一部分。

**11. 廉价一致性检查默认全开。**
CAWM 的两个轻量检查抓到了全部案例。可移植的形状：(a) **regime-shift 单步检查**——只用 claim 本身，问"如果条件 X 变了，这个论断还成立吗"，看它的解释是否与自己的数据矛盾；(b) **重算检查**——在有已知答案时重算一遍。这两个都便宜，应该是每条 inference-claim 的默认后置检查，而不是抽检。

**12. 把人放在最贵的那一步（解释层），不是数据层。**
PaperBench 的人机时间曲线：3 篇子集上人类 48 小时后 41.4%，o1 只有 26.6%——AI 在短时窗领先、人类在长时窗反超。结合"解释类 57.9%"这条，HITL 入口的最佳位置是**解释/结论的采纳点**，而不是数据处理点。数据层该全自动+机械门。

**13. 允许弃答，并把弃答从准确率里排除。**
PaperQA2 的 precision/accuracy 分离（85.2% vs 66.0%）之所以成立，是因为系统被允许回答"信息不足"。这对本项目是直接可抄的：我们的报告应该有大量显式的"未验证/证据不足"，并且我们对外报的数应该是 **precision（在我们敢下结论的地方，我们对得多准）** 与 **coverage（我们敢下结论的比例）** 两个数，绝不合成一个。

**14. 验证成本要单独立预算，它与生成成本同量级。**
锚点：Kosmos $200/run；AI Scientist ~$10–15/篇（单次自动评审 $0.25–0.50）；PaperBench 的自动判官 **$66/篇**（F1 仅 0.83）；Kirgis 实验 6 天 $3,000。PaperBench 判官单篇成本已接近一次完整生成。预算模型里"验证"必须是独立科目，否则它会在压力下被第一个砍掉——而它正是本项目的产品本身。

**15. 去掉执行验证，分数会翻倍——这就是"看起来对"的价格。**
PaperBench Code-Dev（只评代码写没写、不执行）o1 得 43.4%，全量（要执行验证）只有 21–26%。**近一半的"看起来完成了"在执行面前消失。** 任何不执行就打分的门，其数值要按这个量级折算。

---

## 未决与风险

**方法学未决（本轮自身的局限）**

1. **本次会话的 WebSearch 配额在第 14 次检索后耗尽（200/200 上限被此前工作占用）**，后续全部依赖 WebFetch 直取已知 URL。这意味着我可能漏掉了一些本可通过检索发现的 2026 新系统（尤其是 2026 Q2–Q3 的后继工作）。已覆盖的 2026 源包括 arXiv:2608.05179（08）、2607.27191（07）、Science One（07-30）、2606.23175（06）、2605.30329（05）、2605.26340（05）、2601.17431（01）。
2. **Kirgis et al.（arXiv:2607.27191）的正文未直接读到**，标题、DOI、评分（2/6、1/6）、五类失败模式均经 techxplore 转述。该转述引用了具体评审语句，可信度较高，但**严格说这是二手**，落笔前应补一次一手抓取。
3. **两篇 Nature 2026（co-scientist s41586-026-10644-y、Robin s41586-026-10652-y）正文在付费墙后**，本轮只读到 arXiv preprint 版。preprint 与 Nature 正式版之间可能存在数字修订，尤其是 co-scientist 的专家评估部分。
4. **Intology 的 intology.ai 博客返回 HTTP 403**，Zochi 的"top 8.2%""meta-review 4/5"无法一手核实；且所有可及的二手页（cspaper、iNEWS、cybercorsairs、threads）都是复述同一上游博客——**典型的虚假独立佐证，四个页面 = 一个源**。
5. **未找到任何对 Zochi 的真正独立第三方评估**。同样地，**未找到对 Kosmos 79.4% 的独立复核**。这两个是本维度最"品牌驱动"的数字。

**内容未决（需要在设计中当作风险处理）**

6. **Kosmos 的 102 条语句分项计数未披露**——85.5%/82.1%/57.9% 各自的分母不明。如果综合类只有十几条，57.9% 的置信区间会非常宽。同理 ScientistOne 表里的分数复核分母只有 12、方法-代码一致性分母只有 15，"42%" 实际是 5/12——**这些百分数不该被当作稳定估计引用**，引用时必须带分数形式。
7. **Kosmos 的"expert scientist evaluators"与作者的独立性未披露**，"三份代表性报告"由谁按什么标准挑选也未披露。这是一个存在选择偏差空间的评估设计。摘要用词是 "independent scientists"，正文用词是 "expert scientist evaluators" —— 两个措辞的强度不同，我按较弱的正文措辞处理。
8. **Sakana 自动评审的 accuracy 在 arXiv v3（0.66）与 Nature 摘要页（69% balanced accuracy）之间不一致**。可能是 Nature 版更新了实验，也可能是 balanced accuracy 与 accuracy 的口径差。未解决前不应引用任一数字作为"自动评审可用性"的论据。
9. **DeepScientist 的 183.7%/1.9%/7.9% 缺口径**——三个任务的名称和各自的人类 SOTA 基线本轮未取得。183.7% 这种量级的提升几乎必然意味着基线选得弱或指标是某种比率，**在拿到任务名和基线定义之前，这个数字不可用**。
10. **Robin 的 "7.5 倍吞噬作用提升" 只在二手页出现**，arXiv 摘要不含，Nature 正文未读到。不可用。
11. **The 17% Gap 没有人类撰写综述的对照组**，且 32.3% 的引用被归入 "Unknown"（核验不确定）。这意味着 17% 这个数既缺基线又有一个比它本身还大的不确定桶。**作为"AI 引用不可靠"的论据，它的强度远低于其传播度。**
12. **综述 arXiv:2608.05179 自身的复核者间一致性只有 65%**（autonomy level 维度仅 50%）。它的 artifact 类数字（一致性 90%）可信，但它的自治度分类（L0–L5 的归属）应当谨慎使用。
13. **AstaBench 的"最佳 agent 得分"本轮未取得**——只拿到规模数与定性结论。若要在设计文档里引用 AstaBench 做能力锚点，需要补抓。
14. **AutoSurvey 的人类评估只有 3 位博士生**，ρ=0.5429 建立在极小样本上。用它论证"LLM 判官不可靠"方向是安全的（小样本只会让相关更不稳），但不能用它给出一个精确的"判官可靠度"数值。
15. **架构风险（推断）**：本维度所有拿到高可信度的系统（Robin、co-scientist、CAMEO）都有一个**体外物理 oracle**。纯计算/纯文献的系统里，可信度最高的机制是 Science One 的 Chain-of-Evidence——但它自己的审计表也是自家做的（ScientistOne 在自己的表里各项都是最优）。**我们在引用 ScientistOne 那张表时，要意识到它是"自家系统 vs 基线"的自评表**，基线的数字比 ScientistOne 自己的数字更可信。
