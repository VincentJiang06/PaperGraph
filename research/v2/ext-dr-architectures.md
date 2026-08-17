# deep-research agent 架构谱系（2024 → 2026-08）

> 调研时点：2026-08-17。所有"当前排名/最新版本/价格"类陈述均已标注时间，视为会过期。
> 方法：18 次检索 + 逐个抓取一手来源（arXiv 摘要页/HTML、官方 blog、GitHub README、源码文件）。
> 本文严格区分「来源原话」与「我的推断」；推断段落一律以 **【推断】** 开头。

---

## 结论摘要

1. **停机（STOP）是整个谱系上最薄弱、也最没人认真做的一环。** 把 13 个系统的停机机制拆开看，只有两类：
   （a）**预算计数器**——token 预算、depth 递减、iteration cap、tool-call cap。可重跑、确定性，但**与内容无关**：它不知道研究做完没做完，只知道钱花完了。
   （b）**LLM 主观判定**——lead agent"觉得够了"、`action=finish`、critic agent 打分、utility 信号。与内容有关，但**不可重跑**：换个模型版本、换个温度，判定就变。
   **没有任何一个被调研系统拥有"与内容有关且可重跑"的停机门。** 这正是本项目的空白地带。

2. **"并行扇出提升研究质量"这一命题，目前没有任何一篇公开工作给出等算力对照实验。** 所有正向证据（Anthropic 90.2%、Tongyi Heavy 32.9→38.3、W&D 62.2%、Self-Manager）都是 **test-time scaling** 结果：更多算力，恰好摆成了并行形状。Anthropic 自己的方差分析说 token 用量单独解释 BrowseComp 上 80% 的方差——这几乎直接把"多智能体赢了 90.2%"解释成"多花了 15 倍 token"。
   **【推断】** 并行真正稳定买到的是三样东西：**墙钟延迟**、**上下文卫生**（每个 worker 保持短而干净的上下文，规避 long-context 退化）、**探索路径多样性**。第三样只有在下游存在一个**比 worker 更强的裁决步骤**时才会兑换成质量。没有客观裁决器的扇出 = 吞吐量，不是质量。

3. **有一条硬的反向证据，且正好打在本项目的产品定义上**：arXiv 2605.06635 发现，当工具调用从 2 次扩到 150 次时，两个前沿模型的引用**事实核对准确率平均下降约 42%**——"检索得更多"并不产出"引用得更准"。对一个把 credibility 当产品的系统，这条比任何 benchmark 分数都重要。

4. **活下来的架构共性**：外部化工件（outline + evidence memory bank + 报告文件）+ 每轮重建工作区 + 按引用 ID 定向取证写作。WebWeaver / IterResearch / Self-Manager 三条独立线都收敛到这里。**没有一个 SOTA 系统靠 claim-graph 框架取胜**——这与前代项目的教训一致。

5. **2026 年的方向转移**：DeerFlow 从 v1（深研究框架）整个推倒重写成 v2.0（通用 super agent harness，与 v1 零共享代码）；Agon 直接把命题写成"瓶颈已从产出工件转移到裁决主张（judging claims）"。**【推断】** 前者是本项目要抵抗的引力（别把研究质量系统写成通用执行引擎），后者是本项目要抢占的定位。

---

## 系统与机制逐条（含 URL）

### A. 早期开源基线（2024–2025 上半）

#### A1. GPT-Researcher（assafelovic）
- URL: https://github.com/assafelovic/gpt-researcher
- **编排形状**：planner–executor–publisher。原文："The planner generates research questions, while the execution agents gather relevant information. The publisher then aggregates all findings into a comprehensive report."
- **停机**：README 未定义标准研究模式的终止条件（无迭代上限、无 token 门的显式说明）。deep research 模式为"Tree-like exploration with configurable depth and breadth"+"Concurrent processing"。
- **落地成本**（README 原话）：deep research "~5 minutes per deep research"、"~$0.4 per research (using `o3-mini` on 'high' reasoning effort)"。
- **接地方式 —— 这是一个必须记下来的反面教材**：README 原话："By scraping multiple sites per research, and choosing the most frequent information, the chances that they are all wrong is extremely low." 并声明 "We do not aim to eliminate biases; we aim to reduce it as much as possible."
  **【推断】** 这是**教科书级的 false independent corroboration**：网页世界里"最高频"的说法，往往是同一个上游被复制了 N 次。把频次当真值，扇出越大越自信、也越错。本项目必须**按上游来源去重**（不是按 URL 去重）。

#### A2. dzhng/deep-research
- URL: https://github.com/dzhng/deep-research ；README: https://raw.githubusercontent.com/dzhng/deep-research/main/README.md
- **编排形状**：递归 breadth × depth。README："Goal is to keep the repo size at <500 LoC so it is easy to understand and build on top of."
- **停机**：**纯结构性、完全可重跑**——depth 计数递减到 0 即停（"If depth > 0, takes new research directions and continues exploration"；"depth > 0?" 为假则生成报告）。推荐 breadth 3–10（默认 4）、depth 1–5（默认 2）。
- **并行**：`CONCURRENCY_LIMIT` 环境变量控制。
- **【推断】** 这是谱系里停机最"可重跑"的一个，代价是它**完全不看内容**：证据充不充分对它没有意义。它是"预算计数器"这一类的纯净样本。

#### A3. Jina node-DeepResearch
- URL: https://github.com/jina-ai/node-DeepResearch ；方法论文：https://jina.ai/news/a-practical-guide-to-implementing-deepsearch-deepresearch/
- **编排形状**：Search → Read → Reason 单循环。
- **停机（三条，原文引用）**：
  1. token 预算：`while (tokenUsage < tokenBudget && badAttempts <= maxBadAttempts)`
  2. 失败次数：`if (!thisStep.isFinal && badAttempts >= maxBadAttempts)` 触发 "beast mode"
  3. beast mode 强制收敛："decisive and commit to an answer based on available information"
- **一条可直接抄的工程纪律**：原文 "answer generation and evaluation should not be in the same prompt"——**生成与评估必须分 prompt**，并用 few-shot 保证判定一致性。
- **概念区分**：DeepSearch = "atomic building block"，产出 "Concise answer with URLs as references"；DeepResearch 建立其上，产出 "A long structured report with multiple sections, charts, tables and references"。
  **【推断】** 本项目的产品是前者的严格化 + 后者的极薄化：证据层要 DeepSearch 的可判定性，散文层刻意做薄。

#### A4. HuggingFace smolagents / open-deep-research
- URL: https://huggingface.co/blog/open-deep-research ；代码：https://github.com/huggingface/smolagents/tree/main/examples/open_deep_research
- **成绩**：GAIA validation "55.15% on the validation set"；对照 OpenAI Deep Research "near 67% correct answers on 1-shot on average, and 47.6% on especially challenging 'level 3' questions"。
- **最重要的一条消融**：把 code-based actions 换成 JSON-based actions，"performance of the same setup is instantly degraded to 33% average on the validation set"。**同一套 setup、只换动作表示，掉 22 个百分点。**
  **【推断】** 这是全谱系里少见的**单变量受控消融**，而且它证明的不是"多智能体好"，而是"动作表示（可执行代码 vs 结构化 JSON）"这一层的杠杆比编排形状大。对 DSH 这种 TypeScript 运行时：**让 agent 写可执行分析代码、而不是填 JSON 计划**，可能是比扇出更高回报的一步。
- **停机**：GAIA 是短答案任务，以 final_answer 工具调用结束；不是开放式研究的停机模型。

#### A5. Stanford STORM / Co-STORM
- STORM 论文: https://arxiv.org/abs/2402.14207 ；Co-STORM 论文: https://arxiv.org/abs/2408.15232 ；代码: https://github.com/stanford-oval/storm
- **编排形状（STORM）**：pre-writing 阶段 =（1）发现多视角（perspective discovery，通过调查相似主题的既有文章）；（2）模拟"带视角的写作者 × 主题专家"的多轮对话，专家回答基于可信互联网来源；（3）把收集到的信息整理成 outline；然后按 outline 生成全文。
- **停机**：对话轮数 / 视角数为**预设结构参数**（可重跑的计数器），不是证据充分性判断。
- **Co-STORM**：把人放进循环，用户"observe and occasionally steer the discourse among several LM agents"，并用 **dynamic mind map** 组织已发现信息。目标是 "unknown unknowns"。
- **接地**：句级引用到检索来源；论文自陈的失败模式为 "source bias transfer and over-association of unrelated facts"。
- **批评**：见下表关于"25%"的口径纠正——网络上广泛流传的"比人类好 25%"是对论文口径的严重扭曲。

---

### B. 编排框架线（supervisor / subagent）

#### B1. Anthropic 多智能体研究系统（谱系的事实标准）
- URL: https://www.anthropic.com/engineering/multi-agent-research-system （Simon Willison 的同期解读：https://simonwillison.net/2025/Jun/14/multi-agent-research-system/ ，日期 2025-06-14）
- **编排形状**：orchestrator–worker。lead agent 规划 → 并行拉起 3–5 个 subagent → 各自独立上下文检索 → lead 综合 → **独立的 citation pass**。
- **并行（原文）**："3-5 subagents in parallel"、subagent "3+ tools in parallel"，复杂查询研究时间最多减少 90%。
- **停机（原文）**：lead agent "synthesizes these results and decides whether more research is needed—if so, it can create additional subagents or refine its strategy. Once sufficient information is gathered, the system exits the research loop." —— **纯 LLM 主观判定，无阈值**。
- **成本（原文）**："agents typically use about 4× more tokens than chat interactions, and multi-agent systems use about 15× more tokens than chats"。
- **性能归因（原文，口径极重要）**：在 **BrowseComp** 上 "token usage by itself explains 80% of the variance"；token 用量 + 工具调用次数 + 模型选择三者合计解释 95%。
- **失败模式（原文列举）**：简单查询也拉起 50+ subagent；为不存在的来源无限搜索；agent 重复劳动、任务切分失效；token 消耗限制经济可行性；**需要共享上下文的任务上表现差**；编码任务与实时协调上有局限。
  **【推断】** 这一条自陈是本项目"hyper-parallel"命名的最大风险提示：并行只在 breadth-first、子任务真正独立时有效；学术证据探索中大量子任务是**互相依赖**的（一个 claim 的核验依赖另一个 claim 的口径），天然属于 Anthropic 说的"共享上下文任务"。

#### B2. LangChain Open Deep Research
- URL: https://github.com/langchain-ai/open_deep_research ；配置源码: https://raw.githubusercontent.com/langchain-ai/open_deep_research/main/src/open_deep_research/configuration.py
- **编排形状**：scoping（澄清 + brief）→ supervisor 派生并行 researcher（各自隔离上下文、检索后压缩）→ 最终报告。
- **停机——全谱系最明确的可重跑旋钮（源码默认值，抓取时点 2026-08-17，main 分支）**：
  - `max_researcher_iterations = 6`（supervisor 反思并追问的次数上限）
  - `max_react_tool_calls = 10`（单个 researcher step 内的工具调用上限）
  - `max_concurrent_research_units = 5`（并发研究单元上限）
  - `max_structured_output_retries = 3`、`max_content_length = 50000`
  - 模型分工：`research_model` / `summarization_model` / `compression_model` / `final_report_model` 各自独立可配
- **成绩（README，日期 2025-08-02）**：Deep Research Bench 第 6 名，总分 0.4344；用 GPT-5 时 RACE 0.4943。**此排名到 2026-08 已过期，不可作为现状引用。**
- **【推断】** "supervisor 反思 6 次"是把主观停机**包在**客观计数器里：反思本身是 LLM 判断，但循环有硬顶。这是当前工程界的实际做法，也是本项目的最低基线——但它只保证不发散，不保证做够。

#### B3. ByteDance DeerFlow（v1 → v2.0，方向变化本身是信号）
- URL: https://github.com/bytedance/deer-flow
- **v2.0 是彻底重写**，README 原话："DeerFlow 2.0 is a ground-up rewrite. It shares no code with v1." 原深研究框架保留在 `1.x` 分支，主线开发转向 2.0。
- **v2.0 定位**："an open-source **super agent harness**"，组件为：sub-agents（scoped context）、sandboxes（隔离代码执行）、skills（渐进加载的能力模块）、memory、message gateway。构建在 **LangGraph + LangChain** 上。
- **时间点**：2026-02-28 登上 GitHub Trending 第一。
- **停机**：README 未显式给出研究循环的终止策略（提到 goal evaluation 机制，但无可引用的确定性描述）。
- **【推断——方向判读】** ByteDance 的判断是"DeerFlow 不只是研究工具，而是一个执行 harness"。对本项目这是**要主动拒绝的引力**：一旦把系统写成通用 harness，credibility 就退化成众多能力之一，而它本该是唯一的产品。DSH 本身已经是 harness——本项目应当是 harness 上的**一个薄而硬的研究质量层**，而不是第二个 harness。

#### B4. Skywork DeepResearchAgent / AgentOrchestra
- 代码: https://github.com/SkyworkAI/DeepResearchAgent ；论文: https://arxiv.org/abs/2506.12508
- **编排形状**：层级式——顶层 planner 协调专用 sub-agents，并在执行中动态扩展能力。论文提出 **TEA（Tool-Environment-Agent）协议**，把工具/环境/智能体建模为"first-class, versioned resources with explicit lifecycles"，支持端到端上下文与版本管理，"improving traceability and reproducibility"。
- **成绩（论文摘要原话，v6 版本日期 2026-05-28）**："it achieves 89.04% on the GAIA Test set"。
- **停机**：仓库首页与摘要均未说明 planner 如何判定完成。
- **【推断】** TEA 的"versioned resources + 可复现"方向与本项目"可重跑门"高度同源，值得作为 DSH 侧工具契约的设计参考；但论文本身把可复现当作 traceability 特性，没有把它变成停机判据。

---

### C. 上下文重构 / 记忆库线（本项目最该抄的一支）

#### C1. Tongyi / Qwen DeepResearch（含 Heavy / IterResearch）
- Blog: https://tongyi-agent.github.io/blog/introducing-tongyi-deep-research/ ；技术报告: https://arxiv.org/abs/2510.24701 ；HTML 正文: https://arxiv.org/html/2510.24701v1 ；代码: https://github.com/Alibaba-NLP/DeepResearch
- **模型**：30.5B 总参数 / 每 token 激活 3.3B。
- **ReAct 模式（Table 1）**：HLE 32.9、BrowseComp 43.4、BrowseComp-ZH 46.7、xbench-DeepSearch 75.0、WebWalkerQA 72.2、FRAMES 90.6。
- **Heavy 模式（Figure 6，test-time scaling）**：HLE **38.3**、BrowseComp **58.3**、BrowseComp-ZH **58.1**。
- **IterResearch（blog 原话）**：为解决 "cognitive suffocation" 与 "noise pollution" 而设计；"In each round, the agent reconstructs a streamlined workspace using only the most essential outputs" from the previous round。
- **Research-Synthesis 框架（技术报告原话）**：Parallel Research Phase —— "We deploy **n** parallel agents, each following the context management paradigm but exploring diverse solution paths through different tool usage and reasoning strategies"；Integrative Synthesis Phase —— 综合模型汇总所有并行 agent 的发现产出最终答案。**论文未披露实验中 n 的取值。**
- **停机**：每轮由 agent 决定 "either gathering more information or providing a final answer" —— LLM 主观。
- **【推断】** 这是全谱系里**最接近同模型同训练的并行消融**（32.9 → 38.3 是同一个 30B 模型，只改推理时编排）。但它仍不是等算力对照：Heavy 花了 n 倍算力。因此它证明的是"并行形状的 test-time scaling 有效"，**不是**"同等算力下并行优于串行"。而且 n 未披露，意味着这 5.4 分的增益无法归因到具体扇出宽度——引用这个数字时必须带这个限定。

#### C2. WebWeaver（Alibaba-NLP，OEDR SOTA 线）
- 论文: https://arxiv.org/abs/2509.13312 ；代码: https://github.com/Alibaba-NLP/DeepResearch/tree/main/WebAgent/WebWeaver
- **编排形状（摘要原话）**：dual-agent。**Planner** "operates in a dynamic cycle, iteratively interleaving evidence acquisition with outline optimization to produce a comprehensive, citation-grounded outline linking to a **memory bank of evidence**"。**Writer** "executes a hierarchical retrieval and writing process, composing the report section by section"，"performing targeted retrieval of only the necessary evidence from the memory bank via citations for each part"。
- **它明确攻击的两个失败模式（摘要原话）**："static research pipelines that decouple planning from evidence acquisition" 与 "monolithic generation paradigms that include redundant, irrelevant evidence, suffering from hallucination issues and low citation accuracy"。
- **成绩**：自称在 DeepResearch Bench、DeepConsult、DeepResearchGym 上达到 SOTA（摘要未给具体数字）。
- **停机**：摘要未说明 outline 何时算完成。
- **【推断——这是本项目的核心可抄件】** memory bank 是一个**按引用 ID 寻址的扁平证据存储**，不是 claim graph。写作阶段只按 ID 取回需要的那几条证据。这个结构天然支持一条**完全可重跑的门**：对报告里每一条引用，检查 ①memory bank 里是否存在该 ID、②该条目的原文快照里是否包含被引用的字面片段。这两步都是字符串操作，不需要 LLM。前代项目"claim-graph 框架失败"的教训与"memory bank 成功"的事实并不矛盾：区别在于**引用寻址的扁平工件 vs 需要维护一致性的图**。

#### C3. Self-Manager（并行 agent loop，2026-01）
- 论文: https://arxiv.org/abs/2601.17879
- **摘要原话**：现有 agent 在 subtask 级管理上下文，但"still adhere to a single context window and sequential execution paradigm, which results in mutual interference and blocking behavior"。Self-Manager 让主线程创建多个 subthread，"each with its own isolated context, and manage them iteratively through **Thread Control Blocks**"。
- **成绩**：在 DeepResearch Bench 上 "consistently outperforms existing single-agent loop baselines across all metrics"（摘要未给数字）。
- **【推断】** 论文自己给出的机制解释是**上下文隔离**（消除 mutual interference），不是"多个脑袋更聪明"。这条与我在结论 2 中的判断一致：并行的质量收益主要经由上下文卫生这条路径。摘要未说明消融是否控制了算力——这一点必须标为未决。

#### C4. Kimi-Researcher（Moonshot，端到端 RL 而非工作流）
- URL: https://moonshotai.github.io/Kimi-Researcher/
- **成绩（原文）**：HLE "Pass@1 score of 26.9%"、"Pass@4 accuracy of 40.17%"；xbench-DeepSearch "69% pass@1 (averaged on 4 runs)"。
- **规模（原文）**："explores over 200 URLs per task"；"Kimi-Researcher can run 70+ search queries per trajectory"——**原文自己打了星号，注明该数字 "calculated based on a small set of queries"**。
- **上下文管理（原文）**："A context-management mechanism that allows the model to retain important information while discarding unnecessary documents, thereby extending a single rollout trajectory to over 50 iterations"；消融显示该机制带来 "30% more iterations"。
- **停机**：形式化定义为 `action_t = finish` —— **学到的策略决定**，既不可重跑也不可解释。
- **立场（原文）**："unlike modular approaches, all skills—planning, perception, and tool use—are learned together without hand-crafted rules or workflow templates"。
- **【推断】** Kimi 代表谱系的另一极：把编排烧进模型权重。对本项目**不可复制**（我们不训模型），但它的反证价值在于：即使把停机学进模型，停机依然是不可审计的。本项目的差异化恰恰是把停机做成可审计的门。

#### C5. MiroThinker / MiroFlow（交互缩放）
- 论文: https://arxiv.org/abs/2511.11793 ；代码: https://github.com/MiroMindAI/MiroThinker ；MiroFlow: https://github.com/MiroMindAI/MiroFlow
- **核心主张（摘要原话）**：把 **interaction scaling** 作为继模型规模、上下文长度之后的"第三个维度"；"Unlike LLM test-time scaling, which operates in isolation and risks degradation with longer reasoning chains, interactive scaling leverages environment feedback and external information acquisition to correct errors and refine trajectories"；"research performance improves predictably as the model engages in deeper and more frequent agent-environment interactions"。
- **v1.0（72B，论文）**：GAIA 81.9 / HLE 37.7 / BrowseComp 47.1 / BrowseComp-ZH 55.6；256K 上下文，"up to 600 tool calls per task"。
  - **口径纠正**：README 显示这几个数字的实际口径是 **GAIA-Text-103**（文本子集 103 题）与 **HLE-Text**（纯文本子集），不是完整 GAIA validation（165）也不是完整 HLE。
- **v1.5（README）**：HLE-Text 39.2 / BrowseComp 69.8 / BrowseComp-ZH 71.5 / GAIA-Val-165 80.8；"up to 400 tool calls per task"。
- **v1.7（README，30B mini 与 235B）**：BrowseComp 74.0 / BrowseComp-ZH 75.3 / GAIA-Val-165 82.7 / HLE-Text 42.9；"up to 300 tool interactions per task"。
- **【推断——一条对"越多越好"的内部反证】** 同一实验室三代模型，工具调用上限 600 → 400 → 300 **单调下降**，而分数单调上升。这说明交互预算本身不是驱动力；驱动力是每次交互的信息效率。把这条与 2605.06635 的"2→150 次调用引用准确率降 42%"放在一起看：**扩交互量是有代价的，且代价落在可信度上**。
- **另注**：v1.0 论文的 GAIA 口径与 v1.5/v1.7 README 的 GAIA 口径不同（Text-103 vs Val-165），跨版本比较 GAIA 分数是无效的——这正是本项目要防的口径漂移。

---

### D. 2026 新出现者（本轮新增）

#### D1. EDR / "Don't Stop Early"（Salesforce AI Research，ACL 2026 Industry Track）
- 论文: https://arxiv.org/abs/2604.24978 ；HTML: https://arxiv.org/html/2604.24978 ；ACL: https://aclanthology.org/2026.acl-industry.116/
- **摘要原话**："Enterprise deep research often fails to produce decision-ready reports due to uneven information coverage, context explosion, and **premature stopping**." 三件事：(i) 通过带反思的 outline 生成把请求分解成 coverage-driven objectives；(ii) 用 dependency-guided execution + 显式信息共享来局部化上下文；(iii) "enforces evidence-based completion criteria so agents iteratively collect information until sufficiency conditions are met"。
- **停机机制（正文原话，本轮最关键的一条）**："Each agent has...**explicit termination criteria that specify what information must be collected** to complete the assigned objective."；"During execution, the agent uses tools to gather evidence and evaluates whether termination criteria are satisfied. The loop continues until sufficient evidence is collected."
  - 判据以**结构化 checklist** 形式在**执行前**写死（例：组织结构这一步要求"determining relevant teams, key roles, their responsibilities, reporting relationships, and decision ownership"）。
  - **不是**固定覆盖数或引用阈值，而是**任务特定的、执行前编码好的要求**。
- **并行（正文原话）**：DAG 调度。"The planner assigns an appropriate agent type...defines dependencies based on information requirements, and **determines which steps can execute in parallel**." 上下文按依赖门控共享："Each agent has access to its own tools and to selected outputs from prior steps, as specified by the planner. This controlled information sharing prevents unrelated steps from inheriting irrelevant context."
- **结果（内部 sales enablement 任务，同 GPT-4.1 底座）**：HAA 82.09 / Coverage 4.31 / Readability 3.70 / IIR 0.89；对照 ODR 4.1 = 54.82 / 3.41 / 3.71 / 0.64；DeerFlow 4.1 = 57.60 / 3.54 / 3.70 / 0.70。
- **【推断】** "把终止判据在执行前声明成 checklist"是全谱系里离本项目最近的一步——它把"我做完了吗"从开放式自问变成了**清单 diff**。但它止步于此：清单项的满足与否仍由 LLM 判定。本项目的升级点非常明确：**让每个清单项落成一个返回 pass/fail 的可重跑脚本**（数据重跑、字面引文匹配、URL 存活、来源去重计数），而不是一次模型判断。

#### D2. ScaffoldAgent（utility-guided 动态大纲，2026-06）
- 论文: https://arxiv.org/abs/2606.20122
- **摘要原话**：把 outline 演化建模为带三种操作（Expansion / Contraction / Revision）的结构化决策过程；引入 utility-guided feedback，"estimates the downstream value of each outline operation from **retrieval gain, structural coherence, and trial-generation quality**"；"The resulting utility signal guides node selection, operation scheduling, and **termination** during inference."
- **它要解决的问题（原话）**：既有方法要么写作前固定 outline，要么用局部启发式微调，导致 "scaffold drift under continuous information accumulation and delayed feedback"。
- 摘要未给数字（DeepResearch Bench / DeepResearch Gym 上"consistently improves"）。
- **【推断】** 这是唯一一个把**边际效用递减**明确写成停机信号的系统。三个分量里 retrieval gain 半客观（新证据增量可计数）、后两个是 LLM 判断。**本项目可以把这个信号做纯**：retrieval gain 换成"本轮新增的、按上游去重后的独立来源数"和"本轮新增的、通过字面核验的载荷数字数"——两者都能算，都能重跑。

#### D3. W&D：Scaling Parallel Tool Calling（2026-02）
- 论文: https://arxiv.org/abs/2602.07359
- **摘要原话**："the potential of scaling **width** via parallel tool calling remains largely unexplored"；"Unlike existing approaches that rely on complex multi-agent orchestration to parallelize workloads, our method leverages **intrinsic parallel tool calling** to facilitate effective coordination within a single reasoning step"；"scaling width significantly improves performance on deep research benchmarks while **reducing the number of turns** required to obtain correct answers"。
- **数字（原话）**："without context management or other tricks, we obtain **62.2% accuracy with GPT-5-Medium on BrowseComp, surpassing the original 54.9% reported by GPT-5-High**"。
- **口径警告**：这是**跨推理档位**的比较（width-scaled Medium vs 厂商自报的 High），不是同模型同档位的受控消融；且摘要未说明是否控制了总工具调用/token 预算。"reducing the number of turns" 是**吞吐/效率**主张，不是质量主张。
- **【推断】** 它给出的最有价值的信息不是那个数字，而是**架构方向**：并行不一定要靠多智能体编排，可以靠单步内的 intrinsic parallel tool calling。对 DSH（原生 subagent + 工作流引擎）而言，这意味着"扇出"有两个粒度——subagent 级和工具调用级，后者成本低得多，应当优先。

#### D4. Agon（2026-06，命题最贴近本项目）
- 论文: https://arxiv.org/abs/2606.24177
- **摘要原话（第一句就是本项目的命题）**："Large language models are making research production scalable, **shifting the bottleneck from producing artifacts to judging claims**. We present Agon, a research orchestrator that **validates what can be checked inside the workflow and leaves the remaining judgments to human scientists**."
- 六条设计原则：Prompt Economy、Future-Facing、Minimal Prompts、OmniDisciplinary、**Massive Parallelism**、Zero-Code。
- **规模**：跨领域运行 **444 次 Prompt Economy 循环**，"using only small starting topics and no human-written experimental code"。摘要**未给出并发 agent 数**。
- **失败分类学**：沿 severity / fixability / visibility / capability locus 四轴组织，"separates failures the loops can see and fix from those that require human judgment"。
- 结论口号："machine scales, human steers"。
- **【推断】** Agon 与本项目撞了定位，但它的裁决边界是"能在 workflow 内检查的就检查，剩下交人"。本项目应当把这条边界**往机器侧推**：把"可检查"的定义从 workflow 内一致性扩展到 **(a) 可重跑数据分析、(b) 可字面追溯的论文结果、(c) 严格逻辑推演**——这三类都是机器可判定的，Agon 没有把它们全部纳入。

#### D5. 其他 2026 新出现者（已抓摘要，信息量较低但需登记）
- **Self-Optimizing Multi-Agent Systems for Deep Research**（https://arxiv.org/abs/2604.02988）：orchestrator + parallel workers 架构下，让 agent **self-play 探索 prompt 组合**，"can produce high-quality Deep Research systems that match or outperform expert-crafted prompts"。摘要未给适应度信号、未给 benchmark 数字、未说明是否 keep-if-better 选择。**与本项目的"keep-if-better 循环"同源，但可引用信息不足。**
- **AgentDisCo**（https://arxiv.org/abs/2605.11732）：把研究模块拆成 critic（评 outline、改 query）与 generator（取结果、改 outline），"formulates deep research as an adversarial optimization problem between information exploration and exploitation"。称在 DeepResearchBench / DeepConsult / DeepResearchGym 上"comparable to or surpassing leading closed-source systems"，**页面无数字、无单智能体对照**。
- **O-Researcher**（https://arxiv.org/abs/2601.03743）：多智能体蒸馏 + agentic RL 的开放式深研究模型。未深抓。
- **From Model Scaling to System Scaling: Scaling the Harness**（https://arxiv.org/abs/2605.26112）：主张下一个瓶颈是"scaling the harness"——把模型周围的执行层（memory substrate、context constructor、skill-routing、orchestration loop、verification-and-governance layer）当作一等设计对象；呼吁 harness 级 benchmark 去测 "trajectory quality, memory hygiene, context efficiency, communication fidelity, **verification cost**, and safe evolution"。**摘要无任何定量结果**——它是立场文章，不是证据。

---

### E. 评测与可信度审计（本项目的"产品定义"直接依赖这一节）

#### E1. DeepResearch Bench
- 站点: https://deepresearch-bench.github.io/ ；论文: https://arxiv.org/pdf/2506.11763 ；代码: https://github.com/Ayanami0730/deep_research_bench
- **构成**：100 道 PhD 级研究任务（50 中文 + 50 英文），覆盖 22 个领域。
- **两套指标**：**RACE** = "Reference-based Adaptive Criteria-driven Evaluation framework with Dynamic Weighting"（报告质量）；**FACT** = "Framework for Factual Abundance and Citation Trustworthiness"（检索有效性与引用可信度，测两件事：effective citation count 与 citation accuracy）。
- **快照数字（论文发布时点，2025-06）**：Gemini-2.5-Pro Deep Research RACE 最高 48.88、effective citations 111.21；Perplexity Deep Research 的 citation accuracy 最高 90.24%。
- **裁判模型**：Gemini 2.5 Pro Preview，选择理由是性能/成本平衡（$0.13 每 query）。
- **【推断——一个结构性风险】** 这个 benchmark 的核心指标由一个**具体版本的 LLM 裁判**定义。裁判模型换代，历史分数就不可比。这不是这个 benchmark 的缺陷，而是"LLM-as-judge 作为质量定义"这条路线的固有属性。**本项目的对外指标绝不能只有 LLM-judged 分数**，必须有一组不依赖裁判模型的确定性指标。

#### E2. 引用 URL 幻觉的大规模审计（arXiv 2604.03173，2026-04-03 提交）
- **摘要原话**：在 DRBench（53,090 个 URL，10 个模型/agent）与 ExpertQA（168,021 个 URL，3 个模型，32 个学科）上，"**3–13% of citation URLs are hallucinated** — they have no record in the Wayback Machine and likely never existed — while **5–18% are non-resolving overall**"。
- "**Deep research agents generate substantially more citations per query than search-augmented LLMs but hallucinate URLs at higher rates.**"
- 学科效应：non-resolving 率从 Business 的 5.4% 到 Theology 的 11.4%。
- 解法：开源工具 **urlhealth**（用 Wayback Machine 做存活检测与 stale-vs-hallucinated 分类）；自纠实验中，装备 urlhealth 的模型把 non-resolving 引用 "reduce...by **6–79×** to under 1%"。
- **【推断】** urlhealth 是本轮调研里**唯一一个真正可重跑、不依赖 LLM 的接地门**。它应当直接进本项目的 gate 清单——而且要加强：不只查 URL 活着，还要查**被引用的字面片段是否出现在抓取到的正文快照里**（纯字符串匹配，完全确定性）。
- **同时注意**："deep research agent 引用更多但幻觉率更高"这句话，是对"扇出越大越可信"的直接反驳。

#### E3. Cited but Not Verified（arXiv 2605.06635）—— 本轮最重的一条反向证据
- **摘要原话**：提出用可复现 AST parser 从 Markdown 报告里抽取 inline 引用；三维评估 —— (1) **Link Works**（URL 可达）、(2) **Relevant Content**（主题相关）、(3) **Fact Check**（对照来源正文核事实）。评测 14 个开闭源模型，rubric-based LLM-as-a-judge 并经人工校准。
- **结果原话**："even the strongest frontier models maintain **link validity above 94%** and **relevance above 80%**, yet achieve only **39–77% factual accuracy**, while fewer than half of open-source models successfully generate cited reports in a one-shot setting."
- **消融原话（关键）**："Fact Check accuracy **drops by approximately 42% on average** across two frontier models as tool calls scale **from 2 to 150**, demonstrating that **more retrieval does not produce more accurate citations**."
- **口径警告**：摘要用词 "drops by approximately 42%" **未区分相对下降还是绝对百分点下降**；样本量未在摘要给出；判定器是 LLM-as-a-judge（经人工校准）。引用此数时必须带这三条限定。
- **【推断】** 这条把本项目的存在理由说清楚了：**链接活着 ≠ 内容相关 ≠ 支持该主张**。三层是分离的，而工程界普遍只做到第一层。而且"扩检索反而更不准"意味着：一个 hyper-parallel 系统如果只把并行用在"多找"，它会**主动恶化**自己的核心指标。并行必须用在**多验**，不是多找。

#### E4. MAST：多智能体为什么失败（arXiv 2503.13657，NeurIPS 2025）
- **摘要原话**："Despite enthusiasm for Multi-Agent LLM Systems (MAS), **their performance gains on popular benchmarks are often minimal.**"
- 数据集 MAST-Data：跨 **7 个主流 MAS 框架**的 **1600+** 条标注轨迹；分类学 MAST 由 **150 条**轨迹构建，专家标注，**inter-annotator kappa = 0.88**；识别 **14 个失败模式**，聚为 **3 类**：(i) system design issues、(ii) inter-agent misalignment、(iii) task verification。
- **【推断】** 三类里有两类（inter-agent misalignment、task verification）是**扇出制造出来的**失败，单智能体根本没有。也就是说：并行不是零成本地增加算力，它引入了一整类新故障面。对本项目：每增加一个并行边，就必须同时增加一个针对该边的验证门，否则净效应可能为负。

#### E5. 其他评测（登记，未深抓）
- **FinDeepResearch**（https://arxiv.org/abs/2510.13936）：HisRubric 分级评分框架 + 64 家上市公司 / 8 个金融市场 / 4 种语言 / **15,808 个评分项**，评测 16 种方法（6 个 DR agent、5 个带推理+搜索的 LLM、5 个只带推理的 LLM）。摘要未给具体数字。
- **ReportBench**（https://arxiv.org/pdf/2508.15804）：以学术综述任务评 DR agent。未深抓。
- **DeepResearch Gym / DeepConsult**：被 WebWeaver、ScaffoldAgent、AgentDisCo 共同引用为 OEDR 基准。未深抓。

---

## 载荷数字核验表

| # | 数字 | 口径三元组（什么指标 / 什么样本条件 / 与什么比） | 状态 | 一手出处 |
|---|---|---|---|---|
| 1 | **90.2%** | 相对提升幅度 / Anthropic **内部** research eval，Claude Opus 4 领队 + Claude Sonnet 4 子智能体 / 对比单智能体 Claude Opus 4 | verified（但内部、不可复现；是相对提升，不是绝对准确率） | https://www.anthropic.com/engineering/multi-agent-research-system |
| 2 | **约 15×**（agent 约 4×） | token 消耗倍数 / 多智能体系统 vs 普通 chat 交互，Anthropic 内部观测 / 对比 chat | verified | 同上 |
| 3 | **3–5 个 subagent 并行；3+ 工具并行；时间最多减 90%** | 并发度与墙钟时间 / 复杂查询 / 对比串行 | verified（"最多 90%" 是上界，非均值） | 同上 |
| 4 | **token 用量单独解释 80% 方差；+工具调用数+模型选择 = 95%** | 方差解释率 / **BrowseComp** 评测（短答案可判定任务），**不是**其内部研究 eval / — | verified | 同上 |
| 5 | **HLE 32.9 → 38.3** | HLE 分数 / Tongyi DeepResearch 30.5B-A3B；32.9 = ReAct（Table 1），38.3 = Heavy 模式（Figure 6，n 个并行 IterResearch agent + 综合，**n 未披露**）/ 同模型自比 | verified | https://arxiv.org/html/2510.24701v1 |
| 6 | **BrowseComp 43.4 → 58.3；BrowseComp-ZH 46.7 → 58.1** | 同上口径（ReAct → Heavy） | verified | 同上 |
| 7 | **55.15%** | GAIA **validation set** 平均正确率，单次 / HF smolagents open-deep-research / 对比 OpenAI Deep Research 自报 ~67%（1-shot 平均）、level-3 47.6% | verified（跨系统对比非同模型同设置） | https://huggingface.co/blog/open-deep-research |
| 8 | **33%** | GAIA validation 平均 / **同一 setup**，仅把 code-based actions 换成 JSON-based actions / 对比同 setup 的 55.15% | verified（全谱系少见的单变量受控消融） | 同上 |
| 9 | **GAIA 81.9 / HLE 37.7 / BrowseComp 47.1 / BrowseComp-ZH 55.6** | MiroThinker v1.0 72B pass@1 / **GAIA-Text-103 子集**、**HLE-Text 子集**（论文摘要只写 "GAIA""HLE"）/ 对比其他开源 agent | **corrected**（口径不是完整 GAIA validation-165、不是完整 HLE） | 论文 https://arxiv.org/abs/2511.11793 ；口径见 README https://github.com/MiroMindAI/MiroThinker |
| 10 | **BrowseComp 74.0 / BrowseComp-ZH 75.3 / GAIA-Val-165 82.7 / HLE-Text 42.9** | MiroThinker **1.7**（30B mini 与 235B）/ GAIA 口径已换成 Val-165，与 v1.0 的 Text-103 **不可比** / — | verified（跨版本 GAIA 比较无效） | https://github.com/MiroMindAI/MiroThinker |
| 11 | **工具调用上限 600 → 400 → 300** | MiroThinker v1.0 → v1.5 → v1.7 的每任务上限 / 同实验室自比 / 分数同期上升 | verified（对"交互越多越好"的内部反证） | 同上 |
| 12 | **HLE 26.9 pass@1 / 40.17 pass@4；xbench-DeepSearch 69 pass@1（4 次平均）** | Kimi-Researcher / 注意 pass@1 与 pass@4 不可混引 / — | verified | https://moonshotai.github.io/Kimi-Researcher/ |
| 13 | **70+ 次搜索 / 轨迹；200+ URL / 任务；50+ 迭代** | 规模统计 / **来源自己标注："calculated based on a small set of queries"** / — | verified（但来源自陈样本很小） | 同上 |
| 14 | **上下文管理带来 +30% 迭代数** | 消融 / 单轨迹可延长的迭代数 / 对比无上下文管理 | verified（这是"能跑更久"，不是"答得更准"） | 同上 |
| 15 | **1600+ 轨迹 / 7 个框架；150 条建分类学；14 个失败模式 / 3 类；kappa = 0.88** | MAST 数据集与标注一致性 / — | verified | https://arxiv.org/abs/2503.13657 |
| 16 | "MAST 的 LLM-as-Judge 达 94% 准确、Cohen's kappa 0.77" | — | **unverified**（摘要只写 "high agreement"，未给数字；该数字来自二手检索摘要，未在一手摘要中确认） | 同上（需查正文） |
| 17 | **3–13% 引用 URL 是幻觉；5–18% 无法解析** | URL 有效性 / DRBench 53,090 个 URL（10 个模型/agent）+ ExpertQA 168,021 个 URL（3 个模型、32 学科）/ — | verified | https://arxiv.org/abs/2604.03173 |
| 18 | **non-resolving 5.4%（Business）→ 11.4%（Theology）** | 学科间无法解析率区间 / 同上样本 / — | verified | 同上 |
| 19 | **urlhealth 把 non-resolving 降低 6–79× 至 <1%** | 自纠实验 / 装备工具 vs 未装备 / 效果依赖模型的工具使用能力 | verified | 同上 |
| 20 | "OpenAI Deep Research 引用准确率 78%、Claude with search 94%" | — | **unverified / 疑似二手扭曲**：该数字出现在检索摘要中并被归给 2604.03173，但该论文摘要**不含**按系统拆分的准确率，只给 3–13% / 5–18% 的总体区间。**不得作为载荷数字使用。** | 二手检索摘要；一手 https://arxiv.org/abs/2604.03173 未见 |
| 21 | **link validity >94%；relevance >80%；factual accuracy 仅 39–77%** | 三维引用评估 / 14 个模型中的前沿模型，rubric-based LLM-as-a-judge（经人工校准）/ 三维之间互比 | verified | https://arxiv.org/abs/2605.06635 |
| 22 | **Fact Check 准确率随工具调用 2→150 平均下降约 42%** | 引用事实核对准确率 / 两个前沿模型平均 / 对比自身低调用量档 | verified（**但摘要未说明是相对下降还是绝对百分点**，引用必须带此限定） | 同上 |
| 23 | **62.2%（GPT-5-Medium + width）vs 54.9%（GPT-5-High 原报）** | BrowseComp 准确率 / **跨推理档位**比较，非同档受控消融；未说明是否控总预算 / — | verified（数字属实，**口径不构成"并行提升质量"的受控证据**） | https://arxiv.org/abs/2602.07359 |
| 24 | **+25 个百分点（organization）、约 +10（breadth of coverage）** | 被判为"organized"/"broad"的文章占比之绝对提升 / FreshWiki，由**有经验的 Wikipedia 编辑**评判 / 对比 **outline-driven RAG 基线**（**不是**对比人类作者） | **corrected**（网络流传的"比人类好 25%"是口径扭曲：它是 vs RAG 基线的占比提升，不是 vs 人类） | https://arxiv.org/abs/2402.14207 |
| 25 | **70% 更偏好 Co-STORM（vs 搜索引擎）；78%（vs RAG chatbot）** | 用户研究偏好率 / 参与者自报 / 分别对比搜索引擎与 RAG chatbot | verified | https://arxiv.org/abs/2408.15232 |
| 26 | **Deep Research Bench 第 6 名，总分 0.4344；GPT-5 时 RACE 0.4943** | RACE 分数与排名 / LangChain ODR，**日期 2025-08-02** / 榜单同期其他系统 | verified **但已过期**（2026-08 现状未知，不可作为现状引用） | https://github.com/langchain-ai/open_deep_research |
| 27 | **max_researcher_iterations=6；max_react_tool_calls=10；max_concurrent_research_units=5；max_structured_output_retries=3；max_content_length=50000** | 源码默认值 / LangChain ODR main 分支，抓取时点 2026-08-17 / — | verified（存在版本漂移风险） | https://raw.githubusercontent.com/langchain-ai/open_deep_research/main/src/open_deep_research/configuration.py |
| 28 | **`while (tokenUsage < tokenBudget && badAttempts <= maxBadAttempts)`** | 循环终止条件源码 / Jina DeepSearch / — | verified | https://jina.ai/news/a-practical-guide-to-implementing-deepsearch-deepresearch/ |
| 29 | **breadth 默认 4（范围 3–10）；depth 默认 2（范围 1–5）；<500 LoC** | 递归参数默认值与代码规模目标 / dzhng/deep-research / — | verified | https://raw.githubusercontent.com/dzhng/deep-research/main/README.md |
| 30 | **~5 分钟 / 次；~$0.4 / 次（o3-mini "high" reasoning effort）** | deep research 模式单次时耗与成本 / GPT-Researcher README 自报 / — | verified（自报值，未见第三方复现；o3-mini 定价可能已变，2026-08 未复核） | https://github.com/assafelovic/gpt-researcher |
| 31 | **HAA 82.09 / Coverage 4.31 / IIR 0.89**（对照 ODR 54.82/3.41/0.64；DeerFlow 57.60/3.54/0.70） | 内部 sales-enablement 任务，同 GPT-4.1 底座 / 对比 Open Deep Research 与 DeerFlow | verified 数字，但 **HAA/IIR 的定义未在抓取内容中确认**（不可在本项目文档里当作已知指标复述） | https://arxiv.org/html/2604.24978 |
| 32 | **GAIA Test 89.04%** | GAIA **Test** 集准确率 / AgentOrchestra（Skywork DeepResearchAgent 背后论文），v6 版本 2026-05-28 / 对比强基线 | verified | https://arxiv.org/abs/2506.12508 |
| 33 | "Skywork 在 GAIA 上 82.42，2025-05-10 登顶" | — | **unverified**：仅见于二手检索摘要与厂商稿；GitHub 仓库首页与 AgentOrchestra 论文均未出现该数字（论文给的是 GAIA Test 89.04%）。**不得使用。** | 二手；一手未见 |
| 34 | **100 道任务（50 中 + 50 英）、22 个领域；裁判 = Gemini 2.5 Pro Preview（$0.13/query）** | DeepResearch Bench 构成与裁判模型 / — | verified | https://deepresearch-bench.github.io/ |
| 35 | **Gemini-2.5-Pro DR：RACE 48.88、effective citations 111.21；Perplexity DR：citation accuracy 90.24%** | DeepResearch Bench 榜单快照 / **论文发布时点 2025-06** / 同榜其他系统 | verified **但为 2025-06 快照**，2026-08 现状未知 | 同上 |
| 36 | "2026-08 CellCog Max 在 DeepResearch Bench 排名第 1（GPT-5.5 裁判）" | — | **unverified**：来源为该产品自家营销页，属厂商自报，未见独立榜单确认；连"裁判已换成 GPT-5.5"这一前提也未在 benchmark 官方页确认。**不得使用。** | 厂商页；一手未见 |
| 37 | **"DeerFlow 2.0 is a ground-up rewrite. It shares no code with v1."；2026-02-28 GitHub Trending 第 1；基于 LangGraph + LangChain** | 版本关系与时间点 / 官方 README 自陈 / — | verified | https://github.com/bytedance/deer-flow |
| 38 | **444 次 Prompt Economy 循环** | Agon 跨领域部署规模 / 论文自报，2026-06-23 提交 / — | verified（并发 agent 数**未披露**） | https://arxiv.org/abs/2606.24177 |
| 39 | "DeerFlow 隐式续跑安全上限默认 8" | — | **unverified**：出现在抓取工具的摘要中，未在 README 原文中定位到，可能是抓取端的概括。**不得使用。** | 未证实 |

---

## 对本项目的设计含义

### D-1. 停机门：把"执行前声明的清单"升级为"可重跑的脚本"
- 采纳 EDR（2604.24978）的核心动作：**在执行前把每个 objective 的终止判据写成结构化 checklist**，而不是让 agent 在运行中自问"够了吗"。
- 但**不要停在 EDR 停的地方**（清单满足与否由 LLM 判定）。本项目的每个清单项必须落成一个返回 `pass/fail` 的可执行检查：
  - `rerun_ok`：该数字对应的数据分析脚本重跑，输出与文中一致（哈希/数值比对）。
  - `quote_ok`：该数字的引文字面片段，在抓取到的来源正文快照里能被**字符串精确匹配**到（纯确定性，无 LLM）。
  - `url_alive`：URL 可解析（urlhealth 式，Wayback 兜底）。
  - `frame_present`：该数字带完整口径三元组（什么指标 / 什么样本条件 / 与什么比）——结构化字段非空检查。
  - `origin_deduped`：支持该主张的来源，按**上游出处**（而非 URL）去重后计数 ≥ N。
- **停机 = 所有 checklist 项 pass，或预算耗尽（两者都必须记录到 ledger）。** 预算耗尽时报告必须显式标注哪些项未 pass——这就是任务书里说的"不许把 unverified 洗成一个裸数字"。

### D-2. 并行的定位：把并行用在"多验"而不是"多找"
- 全谱系的正向并行证据都是 test-time scaling，没有等算力对照（见结论 2）。同时 2605.06635 给出了"扩检索 → 引用准确率降约 42%"的反向证据。
- 因此本项目的 hyper-parallel 必须重新定义扇出对象：
  - **不扇出"再多搜十个方向"**（这会放大 false corroboration 并恶化引用准确率）；
  - **扇出"对同一条载荷数字做 N 路独立核验"**：一路重跑数据、一路回到 PDF 原文抓字面、一路做口径推演、一路找反证（disconfirming evidence）。这几路的输出是**可比较的 pass/fail**，天然适配 keep-if-better。
- 并行的第二个正当理由是**上下文卫生**（IterResearch 的"每轮重建工作区"、Self-Manager 的"每 subthread 独立上下文"、Anthropic 的"隔离上下文 + 压缩"三条独立线都指向它）。这一条在 DSH 的原生 subagent 上几乎零成本，应当无条件采纳。
- **并行粒度优先级**：W&D 指出单步内的 intrinsic parallel tool calling 比多智能体编排便宜得多。**先把工具调用级并行吃满，再考虑 subagent 级扇出。**

### D-3. 证据存储：扁平 memory bank + 引用 ID 寻址，绝不建 claim graph
- WebWeaver 的结构（planner 产出 citation-grounded outline → 指向 memory bank；writer 按引用 ID 定向取证、逐节写作）与前代"claim-graph 框架失败"的教训并不冲突：**区别在于扁平、可寻址的工件 vs 需要维护全局一致性的图**。
- 这个结构直接给出可重跑门：报告里每个引用 ID → memory bank 条目 → 原文快照 → 字面匹配。三步全是文件与字符串操作。
- 散文层做薄（本项目既定立场）在这个结构下是自然结果：writer 只是把已通过门的证据按 outline 串起来。

### D-4. 接地三层必须分开度量
2605.06635 证明 link-works / relevance / fact-check 是三个分离的量（>94% / >80% / 39–77%）。本项目的 verified 状态必须**同时**满足三层，且三层各自留痕。只做第一层（URL 活着）等于什么都没做。

### D-5. 生成与评估必须分 prompt、分 agent
Jina 的工程结论（"answer generation and evaluation should not be in the same prompt"）与 AgentDisCo 的 critic/generator 解耦是同一条。本项目应更进一步：**评估侧尽量不用 LLM**；必须用 LLM 时，评估 agent 与生成 agent 使用不同模型/不同厂商，并记录裁判模型版本（否则历史结论不可比——DeepResearch Bench 的裁判依赖问题就是前车之鉴）。

### D-6. 对外指标不能只有 LLM-judged 分数
DeepResearch Bench 的核心指标绑定在具体裁判模型版本上。本项目应输出一组**裁判无关的确定性指标**作为主指标：
`载荷数字总数 / 其中 verified 数 / corrected 数 / unverified 数`、`引文字面匹配率`、`URL 存活率`、`按上游去重后的独立来源中位数`、`可重跑分析的重跑通过率`。这些数字任何人拿到工件都能重算——这才是"可重跑的产品"。

### D-7. 每增加一条并行边，就配一个验证门
MAST 的三类失败里，inter-agent misalignment 与 task verification 是扇出**新造出来**的故障面。本项目的规则应写死：**新增一个并行分支，必须同时新增一个针对该分支输出的确定性检查**，否则不允许合入编排。

### D-8. 抵抗"通用 harness"引力
DeerFlow 从深研究框架推倒重写为通用 super agent harness，是这个赛道的典型漂移路径。DSH 本身已是 harness；本项目应当是**薄而硬的研究质量层**，成功标准是 credibility 指标，不是能力广度。任何"顺手把它做成通用执行引擎"的提案都应视为范围蔓延。

---

## 未决与风险

### 未决（需要下一轮或自研实验解决）
1. **等算力并行 vs 串行的对照实验，公开文献里不存在。** 这是本项目最大的知识缺口，也是"hyper-parallel"命名的正当性来源。**建议本项目自己做这个实验并把它当作产品证据的一部分**：固定 token 预算，A = 单线程深挖，B = N 路扇出 + 客观裁决，比较 `verified 载荷数字数 / 预算`。这个实验本身就是本项目方法论的示范。
2. **2605.06635 的"约 42% 下降"是相对还是绝对百分点，摘要未定义**；样本量未知。需要读正文才能作为载荷数字使用。
3. **EDR 的 HAA / IIR 指标定义未确认**（抓取内容只给了数值）。在引用 82.09 / 0.89 之前必须读正文，否则会重蹈"口径扭曲"的覆辙。
4. **Tongyi Heavy 模式的并行 agent 数 n 未披露**，因此 32.9→38.3 的增益无法归因到扇出宽度，也无法据此设计我们自己的扇出宽度。
5. **Self-Manager / AgentDisCo / Self-Optimizing MAS 三篇的消融是否控制了算力，摘要未说明**；这三篇是"并行提升质量"最可能的正面证据来源，需要读正文。
6. **ScaffoldAgent 的 utility 三分量（retrieval gain / structural coherence / trial-generation quality）各自如何计算，摘要未给。** 如果 retrieval gain 是可计算的，它可以直接改造成本项目的边际效用停机信号。
7. **DeepResearch Bench 2026-08 的现状榜单与裁判模型未经一手确认**（唯一见到的说法来自厂商营销页）。若本项目要对标该榜，必须先确认当前裁判模型。
8. **未深抓**：O-Researcher（2601.03743）、ReportBench、DeepResearchGym、DeepConsult、FinDeepResearch 正文、"Why Your Deep Research Agent Fails"（未找到 arXiv ID）。

### 风险
1. **口径漂移是这个领域的常态，不是例外。** 本轮就抓到三例：MiroThinker 的 GAIA 在 Text-103 与 Val-165 之间换过、STORM 的"25%"被广泛说成"比人类好"、"引用准确率 78%/94%" 无法在被归属的论文里找到。**本项目一旦引用外部 benchmark 数字而不带口径，就自己变成了它声称要消灭的东西。**
2. **false independent corroboration 是被主流开源项目当作 feature 实现的**（GPT-Researcher 的"取最高频信息"）。这意味着我们的扇出如果照抄主流做法，会系统性地制造伪独立佐证。必须按上游出处去重，且把"这 N 个来源是否同源"本身做成一个可检查项。
3. **扩检索与可信度是负相关的**（2605.06635）。一个名字里带 "hyper-parallel" 的系统如果把并行用错方向，会主动恶化自己的产品定义。这条风险应当写进项目的红线。
4. **LLM-as-judge 的历史不可比性**：裁判模型换代 → 所有历史分数失效。本项目的内部 keep-if-better 循环如果用 LLM 打分做适应度，会在模型升级时发生静默的基线漂移。适应度信号必须以确定性指标为主。
5. **扇出制造新故障面**（MAST：14 个失败模式中两大类为多智能体独有）。并行度不是免费的算力，它是有故障预算的。
6. **版本漂移**：本文引用的 LangChain ODR 默认值、MiroThinker 版本号、DeerFlow 分支状态都是 2026-08-17 抓取时点的快照，几周内即可能变化。凡引用这些值的规划文档必须带日期。
7. **单点抓取风险**：本文多数论文只读了 abstract 页而非正文。凡标注 verified 的数字都是"我读到了这句原话"，不是"我复核了实验"。第 2、3、5 条未决项正是这个限制的直接后果。
