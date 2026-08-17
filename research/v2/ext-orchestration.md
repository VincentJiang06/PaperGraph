# 外部调研 v2 · 维度：多 agent 编排模式与上下文/成本经济学

- 调研日期：2026-08-17
- 方法：WebSearch（12 次，配额耗尽后转 Serper 脚本补搜 4 批）→ 对每个载荷数字回抓一手来源（论文 abs/HTML/PDF、官方 docs/pricing），记录口径三元组
- 纪律：所有数字带「什么指标 / 什么样本与条件 / 与什么比」；未达一手来源的一律标 `unverified` 并保留原样，不洗成裸数字

---

## 结论摘要

**1. 本轮最重要的一条：已经存在一份直接测量「检索深度 ↔ 引用事实准确率」的一手实验，结论是负相关，而且表层指标完全掩盖它。**
arXiv:2605.06635（*Cited but Not Verified*, 2026-05-07）做了 within-model 的深度消融：同一个模型，工具调用数从 2 增到 150，Fact-Check 准确率**平均下降约 42 个百分点**，而链接可用率（>92%）、话题相关度（>80%）这类表层指标基本不动。这直接判定了本项目的架构问题——**hyper-parallel 必须配 per-loop 验证门，而且门不能建在「链接通不通、格式对不对」上，只能建在「claim 是否被 source 文本支持」上**。表层指标在这里是诱饵。

**2. 扇出本身不是好事，扇出的拓扑才是。**
Google Research + MIT（Kim et al., arXiv:2512.08296 v3, 2026-04-08）在 260 个配置 / 6 个基准 / 5 种架构 / 3 个模型家族上做受控评测：相对单 agent 基线，**+80.8%（可分解的金融推理）到 −70.0%（顺序规划）**。错误放大倍率按架构分层非常干净：**Independent 17.2× > Decentralized 7.8× > Hybrid 5.1× > Centralized 4.4× > 单 agent 1.0×**。论文自己的措辞是「没有中心化验证的架构比有中心化协调的架构更容易传播错误」。→ 本项目要的是**中心化编排 + 编排器持有验证权**，不是 peer 之间自由 handoff。

**3. 能力饱和阈值：单 agent 基线一旦超过约 45%，再加 agent 是负收益。**
同一篇论文的 capability-saturation 结论。含义是：扇出应该用在**覆盖率/广度**（可并行、单 agent 基线低）上，不能用在**推理链**（顺序、单 agent 已经能做）上。且论文明确说 **tool-heavy 任务（例：16 工具的业务流）会吃到 multi-agent 协调开销**——我们的任务恰恰是 tool-heavy，worker 的工具集必须窄且互不重叠。

**4. keep-if-better 循环有一个已被测量的失效模式：改一处、退十处。**
ACL 2026 的 MRDRE（*Beyond Single-shot Writing*）测五个 Deep Research Agent 的多轮改稿：agent 能落实**超过 90%** 的用户反馈，但同时**在 16–27% 的既有内容与引用质量上发生回退**，内容反馈下的 break rate 平均 **31%**；而且论文明确说**提示工程和「专门的改稿子 agent」这两种 inference-time 修法都解决不了**。→ 我们的 keep-if-better 门必须做**逐 claim 的新旧 diff**，拒绝静默删除，不能靠「让一个 reviewer agent 再看一遍」。

**5. Anthropic 那个被到处引用的 token 倍数，口径被普遍讲错了。**
原文是「agents 大约用 4× 于 chat 的 token，multi-agent 系统大约用 15× 于 **chat** 的 token」——**分母是 chat，不是单 agent**。而「token 用量单独解释 80% 的方差」是在 **BrowseComp** 这个评测上的方差分解（三因子合计 95%），**不是**在那个拿到 90.2% 的内部 research eval 上，更不是一条「多烧 token 就更强」的定律。

**6. 上下文治理的路线已经收敛到「重建 > 累积」。**
IterResearch（arXiv:2511.07327, ICLR 2026）用 Markovian workspace 重建（问题 + 演进中的报告 + 上一次交互，O(1) 内存）替代单一膨胀上下文，在 2048 次交互的极长程上把成绩从 **3.5% 拉到 42.5%**；作为纯 prompting 策略也能给前沿模型 **最多 +19.2pp**。Anthropic 自己的 context engineering 文章给的是同一族解法（compaction / 结构化笔记 / 子 agent），并且给了子 agent 的压缩比：子 agent 烧「数万 token」，只回传「通常 1,000–2,000 token」。

**7. 成本经济学（2026-08 现价）已经和 2025 年的直觉不一样了。**
Opus 5 $5/$25 每百万 token，Sonnet 5 $2/$10，Haiku 4.5 $1/$5；cache read 是 base input 的 0.1×，Batch 五折，web search $10/千次，**web fetch 不额外收费**。一个容易被忽略的坑：**Claude 4.7 及以后的模型换了 tokenizer，同样文本约多出 30% token**——任何基于旧模型实测推出来的预算算术要整体上调约 30%。

**8. 一个必须点名的假独立佐证陷阱。**
`research.google` 博客、arXiv:2512.08296、ResearchSquare 预印本、以及 *Nature Machine Intelligence* 上的 "Capable language models can outgrow the benefits of multi-agent coordination"（s42256-026-01268-y, Y. Kim 2026）——**是同一批人（Yubin Kim 等）的同一项工作的不同载体，算一个来源，不是四个**。而且博客版（2026-01-28）写的是「180 个配置 / 4 个基准 / +80.9%」，arXiv v3（2026-04-08）已经是「260 个配置 / 6 个基准 / +80.8%」。引用时必须带版本与日期。

---

## 系统与机制逐条（含 URL）

### A. Anthropic 多 agent 研究系统（orchestrator-worker 的事实标准）

来源（一手）：https://www.anthropic.com/engineering/multi-agent-research-system

原文可引用的机制：

- 架构：lead agent 规划，**「The lead agent spins up 3-5 subagents in parallel rather than serially; the subagents use 3+ tools in parallel.」**
- 引用是**独立的一遍**，不是写作时顺带：**「Once sufficient information is gathered, the system exits the research loop and passes all findings to a CitationAgent, which processes the documents and research report to identify specific locations for citations.」**
  → 对我们的意义：Anthropic 自己也把 citation 从生成里剥离成独立 pass。但 2605.06635 的结果说明**「独立 citation pass」只保证引用位置对，不保证引用内容支持 claim**——这两件事必须分开设计。
- 并行化收益：**「These changes cut research time by up to 90% for complex queries」**（口径：up to，复杂查询，来自并行工具调用改造）
- 不适用场景（原文自己划的边界）：**「Some domains that require all agents to share the same context or involve many dependencies between agents are not a good fit for multi-agent systems today. For instance, most coding tasks involve fewer truly parallelizable tasks than research, and LLM agents are not yet great at coordinating and delegating to other agents in real time.」**
  → 这一段和 Google/MIT 的「顺序任务 −70%」是同一个现象的两种表述，互为佐证（且这两个是真独立来源）。

时效性提醒：文中模型是 Claude Opus 4 / Sonnet 4（2025 年），到 2026-08 已迭代多代，90.2% 这个数不能当作当前代际的预期。

### B. Google Research × MIT：agent 系统的扩展律（本轮最强的一手实验）

来源（一手，按可信度排序）：
- arXiv abs（v1 2025-12-09 / v3 2026-04-08）：https://arxiv.org/abs/2512.08296
- arXiv 全文 HTML v3：https://arxiv.org/html/2512.08296v3
- Google 博客（2026-01-28，对应较早版本）：https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/
- 代码：https://github.com/ybkim95/agent-scaling
- 期刊版（同一工作）：https://www.nature.com/articles/s42256-026-01268-y

设计（v3 摘要原文）：**「Across 260 configurations spanning six agentic benchmarks, five canonical architectures (Single-Agent and four Multi-Agent: Independent, Centralized, Decentralized, Hybrid), and three LLM families, we perform controlled evaluations, standardizing tools, prompts, and compute to isolate architectural effects.」**
六个基准：BrowseComp-Plus、Finance-Agent、PlanCraft、WorkBench、SWE-bench Verified、Terminal-Bench。

三条对我们直接可用的结论（原文）：
1. **「a coordination yields diminishing returns once single-agent baselines exceed certain performance」**；正文给出阈值：**「tasks where single-agent performance already exceeds 45% accuracy experience negative returns from additional agents」**
2. **「tool-heavy tasks appear to incur multi-agent overhead」**；正文：**「tool-heavy tasks (e.g., 16-tool business workflows) suffer from multi-agent coordination overhead, with efficiency penalties compounding as environmental complexity increases」**
3. **「architectures without centralized verification tend to propagate errors more than those with centralized coordination」**——错误放大倍率 Independent 17.2× / Decentralized 7.8× / Hybrid 5.1× / Centralized 4.4×，单 agent = 1.0；定义是**「how much extra computational work arises from inter-agent coordination failures, estimated from execution-trace token analysis」**（注意：这是**从执行轨迹 token 估计的额外计算量**，不是「错误率放大 17 倍」——这个口径很容易被讲坏）

模型拟合强度：**R²=0.373**（六基准交叉验证），加入 task-grounded capability metric 后 **R²=0.413**；架构选择预测命中 **87%** held-out 配置。
→ R²≈0.37 意味着**这套扩展律解释了约三分之一的方差**，是有用的先验，不是可以照抄的公式。任何把它当「定律」用的写法都要被自己的验证门拦下。

### C. 引用可验证性：检索深度 vs 事实准确率（本轮的决定性证据）

来源（一手）：
- abs：https://arxiv.org/abs/2605.06635
- 全文 HTML：https://arxiv.org/html/2605.06635v1
- 标题 / 作者 / 日期：*Cited but Not Verified: Parsing and Evaluating Source Attribution in LLM Deep Research Agents*；Hailey Onweller, Elias Lumer, Austin Huber, Pia Ramchandani, Vamse Kumar Subbiah, Corey Feld；2026-05-07（v1）

方法（摘要原文）：用可复现的 **AST parser** 从 Markdown 报告里抽取 inline citation，然后**回抓被引内容**再判定。三个维度：**(1) Link Works**（URL 可达）、**(2) Relevant Content**（话题对齐）、**(3) Fact Check**（对照源内容验证事实准确性）。Fact Check 的判定是二值：事实 **「supported or consistent」** 记 1，**「contradicted, absent, or uncertain」** 记 0。评测 **14 个模型 × 130 个研究 query**，用 rubric-based LLM-as-a-judge，经人工复核校准。

主结果（摘要原文）：**「even the strongest frontier models maintain link validity above 94% and relevance above 80%, yet achieve only 39-77% factual accuracy」**。

深度消融（本项目的核心依据，原文）：**「To directly test the information overload hypothesis, we conducted an ablation study across two models at seven search depth intervals (2–150 tool calls).」** 七个档位：2, 10, 30, 50, 70, 100, 150。
- GPT-5.4：Fact Check **78.6% → 16.7%**
- Claude Opus 4.6：Fact Check **80.0% → 57.9%**
- 摘要表述：**「Fact Check accuracy drops by approximately 42% on average across two frontier models as tool calls scale from 2 to 150, demonstrating that more retrieval does not produce more accurate citations.」**

**口径纠正（我方核算，见核验表 6 行）**：两个模型的绝对降幅分别是 61.9pp 和 22.1pp，均值 **42.0pp**——所以摘要里的「approximately 42%」是**两模型绝对百分点降幅的平均**，不是「相对下降 42%」（相对降幅均值约 53%）。同时，**两个模型的降幅相差近 3 倍**，「42%」这个头条数把模型间差异完全抹平了。

论文自陈的方法学限制（我们必须承接）：只做了**两个**模型的消融；**没有报告相关系数、回归或 p 值**，只给了表和趋势；判定器是 LLM-as-a-judge（有人工校准，但不是全人工）。→ 这条证据**方向可信、量级需自证**：本项目应当在自己的语料上复跑一次深度-准确率曲线，而不是直接引用 42pp。

### D. 多轮改稿的回退（keep-if-better 的反面教材）

来源（一手 PDF）：https://aclanthology.org/2026.acl-long.609.pdf
标题：*Beyond Single-shot Writing: Deep Research Agents are Unreliable at Multi-turn Report Revision*（Bingsen Chen 等，NYU / NYU Shanghai / Alberta / Princeton / Waterloo / Verdent AI；ACL 2026 Long）

摘要原文：**「Our analysis of five diverse DRAs reveals a critical limitation: while agents can address most user feedback, they regress on 16–27% of previously covered content and citation quality.」** 以及 **「these issues are not easily resolvable through inference-time fixes such as prompt engineering and a dedicated sub-agent for revision」**。
正文数据点：**「agents address over 90% of requested edits」**；**「Break rates average 31% under content [feedback]」**；扩展到 4 轮时，未受反馈波及的内容仍在 Turn 4 前后被破坏约 20–30%；被评的五个系统含 Tongyi DR、OpenAI DR 等（Tongyi DR 本身不产引用，单列）。

→ 这是对「循环 = 单调改进」这一直觉最直接的反例，也是对本项目「keep-if-better」的具体要求：**better 必须是逐 claim 可判定的偏序，不能是整篇打分**。

### E. 上下文治理：重建式工作区

来源（一手）：https://arxiv.org/abs/2511.07327 （*IterResearch: Rethinking Long-Horizon Agents via Markovian State Reconstruction* / 副标题在不同版本作 *with Interaction Scaling*；v1 2025-11-10，v2 2026-01-31，ICLR 2026 camera-ready）
配套：https://tongyi-agent.github.io/blog/introducing-tongyi-deep-research/

机制（摘要原文）：批评现有做法是 **「a mono-contextual paradigm that accumulates all information in a single, expanding context window, leading to context suffocation and noise contamination」**；改为每轮重建工作区 = 原问题 + LLM 生成的演进报告（承担 memory）+ 上一次交互，**O(1)** 内存复杂度。配 EAPO（几何折扣奖励的 RL）。
数字：六基准平均 **+14.5pp**；交互规模扩到 **2048** 次时从 **3.5% → 42.5%**；作为纯 prompting 策略对前沿模型 **最多 +19.2pp**（相对 ReAct）。

### F. Anthropic 的上下文工程三件套

来源（一手）：https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

- 前提：**「LLMs have an 'attention budget' that they draw on when parsing large volumes of context. Every new token introduced depletes this budget by some amount.」**；context rot 定义：**「as the number of tokens in the context window increases, the model's ability to accurately recall information from that context decreases.」**
- **Compaction**：**「taking a conversation nearing the context window limit, summarizing its contents, and reinitiating a new context window with the summary」**；Claude Code 的做法是保留架构决策、未解 bug、实现细节，丢弃冗余工具输出；难点原文：**「The art of compaction lies in the selection of what to keep versus what to discard, as overly aggressive compaction can result in the loss of subtle but critical context.」**
- **结构化笔记**：上下文窗口之外持续写笔记、需要时再注入（Claude 玩 Pokémon 的例子，跨数千步维持计数）
- **子 agent 的压缩比（可直接用于我们的预算模型）**：**「each subagent might explore extensively, using tens of thousands of tokens or more, but returns only a condensed, distilled summary of its work (often 1,000-2,000 tokens)」**
- 三者的适用面：compaction 适合需要大量来回的任务；笔记适合有明确里程碑的迭代开发；multi-agent 适合 **「complex research and analysis where parallel exploration pays dividends」**

### G. Context Rot（长上下文退化的对照实验）

来源（一手）：https://www.trychroma.com/research/context-rot （2025-07-14）

- **18 个模型**（Claude Opus 4 / Sonnet 4 / 3.7 / 3.5 / Haiku 3.5；o3、GPT-4.1 全系、GPT-4o、GPT-4 Turbo、GPT-3.5 Turbo；Gemini 2.5 Pro / Flash、2.0 Flash；Qwen3-235B / 32B / 8B）
- 条件：needle-question 相似度 8 档 × 5 个 embedding 模型；干扰项 0 / 1 / 4；haystack 用 Paul Graham 文集 vs arXiv 论文；原序 vs 打乱；LongMemEval 聚焦输入（~300 token）vs 完整输入（~113k token）；repeated-words 复制任务 **1,090 个变体**，长度 25–10,000 词
- 结论原文：**「Model performance degrades as input length increases, often in surprising and non-uniform ways.」** 以及 **「Whether relevant information is present in a model's context is not all that matters; what matters more is how that information is presented.」**

→ 与本项目的接点：证据台账（evidence ledger）不能只做「把证据塞进上下文」，还要管**呈现方式**（干扰项剔除、与当前 claim 的语义距离、结构化而非流水账）。

### H. 单 agent 优先派：OpenAI 指南与 Cognition

**OpenAI, *A practical guide to building agents***（PDF 一手：https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf ；落地页 https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/ ）

- 原文：**「Our general recommendation is to maximize a single agent's capabilities first. More agents can provide intuitive separation of concepts, but can introduce additional complexity and overhead, so often a single agent with tools is sufficient.」**
- 拆分的触发条件是**工具重叠而非工具数量**：**「The issue isn't solely the number of tools, but their similarity or overlap. Some implementations successfully manage more than 15 well-defined, distinct tools while others struggle with fewer than 10 overlapping tools.」**
- 两种模式：**Manager（agents as tools，边 = 工具调用）** vs **Decentralized（handoff，边 = 执行权转移）**；handoff 在 Agents SDK 里就是一种 function
- 结语原文：**「starting with a single agent and evolving to multi-agent systems only when needed」**

**Cognition, *Don't Build Multi-Agents***（一手：https://cognition.com/blog/dont-build-multi-agents ；作者 Walden Yan；页面日期 **06.12.25**）

- 两条原则原文：**「Share context, and share full agent traces, not just individual messages」**；**「Actions carry implicit decisions, and conflicting decisions carry bad results」**
- 失效机制：**「Subagent 1 and subagent 2 cannot see what the other was doing and so their work ends up being inconsistent with each other.」**
- 他们的解法就是 compaction：**「We introduce a new LLM model whose key purpose is to compress a history of actions & conversation into key details, events, and decisions. This is hard to get right.」**

→ 注意：Cognition 的论域是**编码**（Devin），Anthropic 明确说编码任务可并行性远低于研究。两方并不真的矛盾，Google/MIT 的「架构-任务对齐」原则同时解释了两者。**我们的任务在「可并行的研究」这一侧**，但推理链部分仍适用 Cognition 的告诫。

### I. Google ADK（编排原语层）

来源：https://developers.googleblog.com/en/agent-development-kit-easy-to-build-multi-agent-applications/ ；文档 https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/adk ；模式指南 https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/

要点：把编排显式化为 **workflow agents（Sequential / Parallel / Loop）** 的确定性管道，与 **LLM 驱动的动态路由（LlmAgent transfer）** 二选一或混用。
→ 这正是 DSH 「workflow engine + native subagents」的同构物：**确定性骨架 + 模型驱动的局部决策**。可借鉴的是它把 Loop 作为一等公民（对应我们的 keep-if-better 循环）。

### J. Blackboard（共享工作区）作为研究型编排的第三条路

来源（一手）：https://arxiv.org/abs/2510.01285 （*LLM-Based Multi-Agent Blackboard System for Information Discovery in Data Science*；v1 2025-09-30，v2 2026-01-31）
另有：https://arxiv.org/abs/2507.01701 （blackboard 架构的通用探索）；https://arxiv.org/html/2605.29313v1 （PatchBoard：schema-grounded state mutation，可审计）

摘要原文的动机正中我们要害：**「master-slave multi-agent systems rely on a rigid central controller that requires precise knowledge of each sub-agent's capabilities, which is not possible in large-scale settings where the main agent lacks full observability over sub-agents' knowledge and competencies」**；做法是中心 agent 往共享黑板贴需求，具备能力的下属 agent **自愿认领**。
成绩：**「13%-57% relative improvements in end-to-end success and up to a 9% relative gain in data discovery F1 over the best baseline」**，基准为 KramaBench 及改造版 DSBench、DA-Code。

→ 对我们的意义：黑板 = **证据台账（artifact-centric state）本身就是协调媒介**。这与「keep-if-better 循环 + 可重跑产物」的既有结论天然合拍：worker 不互相喊话，只对台账做**带 schema 的状态变更**（PatchBoard 那一路），编排器对台账行使验证权。这同时保留了 Centralized 的低错误放大（4.4×）和黑板的可扩展性。

### K. 运行时能力与硬约束（DSH 侧可直接落到代码的旋钮）

来源（一手）：
- https://code.claude.com/docs/en/agent-sdk/subagents
- https://code.claude.com/docs/en/agent-teams
- https://code.claude.com/docs/en/costs

- **上下文隔离的精确语义**：**「A subagent's context window starts fresh, with no parent conversation, but isn't empty. The only content you pass from parent to subagent is the Agent tool's prompt string」**；回传只有 final message。→ 父子之间的信息通道**只有两个字符串**，所以证据必须走**文件/台账**，不能指望隐式共享。
- **三个可编程上限**（v0.3.219 / v0.2.127 起）：
  - `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`，默认 **3** 层
  - `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`，默认 **20** 并发，超限返回 `Concurrent subagent limit reached`
  - `maxBudgetUsd` / `max_budget_usd`，对 `total_cost_usd` 计，触顶时拒绝新 subagent、停掉后台 subagent、以 `error_max_budget_usd` 结束
  → **预算即代码**，与前代项目「budgets-in-code」的教训一致，运行时原生支持，不必自造。
- **子 agent 输出扫描**（v2.1.210+）：父读取前扫描 final message 的指令样式（控制标签仿冒、权限配置提及、`Human:`/`Assistant:` 轮次标记），只做中和标注、**不删改措辞**。→ 我们从 web 抓来的证据经 worker 回传时有一层默认防线，但**不能当作充分的注入防护**。
- **规模上限**：**「Subagents work well for a few delegated tasks per turn. For runs that coordinate dozens to hundreds of agents, use the `Workflow` tool, which moves the orchestration into a script the runtime executes outside the conversation context.」** → hyper-parallel 应走 Workflow，不是逐轮 subagent 委派。
- **Opus 5 的委派倾向**：**「Claude Opus 5 delegates to subagents more readily than earlier models, so the depth, concurrency, and spend limits matter most on queries that run Opus 5.」**
- **agent teams 的官方边界**：实验特性、默认关闭（`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`）、**无嵌套团队**、**非交互 `-p` 模式（含 Agent SDK 会话）不会 spawn teammate**。团队规模建议 **3–5**，理由是 **「Token costs scale linearly / Coordination overhead increases / Diminishing returns」**。
  → 结论：**本项目走 subagents + Workflow，不走 agent teams**（我们是 headless 编排，teams 在 `-p` 下根本不生效）。

---

## 载荷数字核验表

一行一个数字：数字 | 口径三元组（指标 / 样本与条件 / 与什么比） | 状态 | 一手出处

| # | 数字 | 口径三元组 | 状态 | 一手出处 |
|---|---|---|---|---|
| 1 | **90.2%** | 指标=相对性能提升；样本=Anthropic **内部 research eval**（未公开，样本量未披露），lead=Claude Opus 4 + subagents=Sonnet 4；比较对象=单 agent Claude Opus 4 | `verified`（但**已过时**：2025 年模型代际） | anthropic.com/engineering/multi-agent-research-system |
| 2 | **80%** | 指标=**方差解释率**（token 用量单因子）；样本=**BrowseComp** 评测（三因子合计解释 95%，另两因子为工具调用数与模型选择）；比较对象=该评测内的性能方差 | `verified` —— **注意：不是 research eval，不是因果律** | 同上，原文「token usage by itself explains 80% of the variance」 |
| 3 | **15×** | 指标=token 消耗倍数；样本=Anthropic 自有数据（"in our data"）；**比较对象 = chat interactions，不是单 agent** | `verified` | 同上，原文「multi-agent systems use about 15× more tokens than chats」 |
| 4 | **4×** | 指标=token 消耗倍数；样本=同上；比较对象=chat interactions（单 agent 侧） | `verified` | 同上 |
| 5 | **≈3.75×** | 指标=multi-agent 相对**单 agent** 的 token 倍数；由 15÷4 推得 | **我方推断（非原文）**，仅作量级参考 | 由第 3、4 行推导 |
| 6 | **42 个百分点（不是 42% 相对降幅）** | 指标=Fact-Check 准确率的**绝对百分点降幅之两模型均值**；样本=同一模型内 7 档深度消融（2/10/30/50/70/100/150 次工具调用），两个前沿模型；比较对象=2 次调用 vs 150 次调用 | **`corrected`** —— 原文写「approximately 42%」，核算为：GPT-5.4 78.6%→16.7%（−61.9pp）、Claude Opus 4.6 80.0%→57.9%（−22.1pp），均值 **−42.0pp**；若按相对降幅平均则约 **53%**，非 42% | arXiv:2605.06635 v1 |
| 7 | **78.6% → 16.7%** | 指标=Fact-Check 准确率；样本=GPT-5.4，深度 2 → 150 次工具调用 | `verified` | arxiv.org/html/2605.06635v1 |
| 8 | **80.0% → 57.9%** | 指标=Fact-Check 准确率；样本=Claude Opus 4.6，深度 2 → 150 次工具调用 | `verified` —— **模型间降幅差近 3 倍，头条数掩盖了它** | 同上 |
| 9 | **39–77%** | 指标=Fact-Check 准确率区间；样本=前沿模型（14 模型 × 130 query，rubric LLM-judge 经人工校准）；比较对象=同批模型间 | `verified` | arXiv:2605.06635 摘要 |
| 10 | **>94% / >80% / >92%** | 指标=Link Works 可达率 / Relevant Content 话题对齐 / 深度消融中表层指标；样本=同上；比较对象=与同批 Fact-Check 分数对照 | `verified` —— **表层指标在深度增加时保持稳定，是诱饵指标** | 同上 |
| 11 | **130** | 指标=研究 query 数；样本=评测全集；比较对象=n/a | `verified` | 同上 |
| 12 | **14** | 指标=被评模型数（OpenAI/Anthropic/Google + 3 开源）；样本=同上 | `verified` | 同上 |
| 13 | **260 / 6 / 5 / 3** | 指标=配置数 / 基准数 / 架构数 / 模型家族数；样本=arXiv **v3（2026-04-08）**；比较对象=n/a | `verified` | arxiv.org/abs/2512.08296 v3 |
| 14 | **180 / 4 / +80.9%** | 同上三项，但取自 **Google 博客（2026-01-28）**，对应论文较早版本 | **`corrected`（版本漂移）** —— 现行版为 260/6/+80.8%，引用须带版本日期 | research.google 博客 vs arXiv v3 |
| 15 | **+80.8% ~ −70.0%** | 指标=相对**单 agent 基线**的性能变化；样本=260 配置；比较对象=最好情形（可分解金融推理）与最差情形（顺序规划） | `verified` | arXiv:2512.08296 v3 摘要 |
| 16 | **17.2× / 7.8× / 5.1× / 4.4× / 1.0×** | 指标=**错误放大**（定义：由 agent 间协调失败引起的额外计算量，由执行轨迹 token 估计，**非错误率**）；样本=Independent / Decentralized / Hybrid / Centralized / 单 agent；比较对象=单 agent = 1.0 | `verified` | arxiv.org/html/2512.08296v3 |
| 17 | **45%** | 指标=单 agent 基线准确率阈值；样本=同上；比较对象=超过该值后增加 agent 为**负收益** | `verified` | 同上 |
| 18 | **R²=0.373 / 0.413** | 指标=交叉验证 R²；样本=六基准全体 / 加入 task-grounded capability metric；比较对象=n/a | `verified` —— **仅解释约 1/3 方差，是先验不是定律** | arXiv:2512.08296 v3 摘要 |
| 19 | **87%** | 指标=最佳架构预测命中率；样本=held-out 配置；比较对象=n/a | `verified` | 同上 |
| 20 | **16–27%** | 指标=**回退比例**（既有内容与引用质量）；样本=五个 Deep Research Agent 的多轮改稿；比较对象=改稿前已覆盖的内容 | `verified` | aclanthology.org/2026.acl-long.609.pdf 摘要 |
| 21 | **>90%** | 指标=用户反馈落实率；样本=同上；比较对象=被请求的编辑总数 | `verified` —— **与第 20 行并列才有意义：改得动，但会连带破坏** | 同上 |
| 22 | **31%** | 指标=break rate 均值；样本=内容型反馈条件下；比较对象=n/a | `verified` | 同上正文 |
| 23 | **+14.5pp** | 指标=平均绝对提升；样本=六个基准；比较对象=现有开源 agent | `verified` | arXiv:2511.07327 |
| 24 | **3.5% → 42.5%** | 指标=任务成绩；样本=交互次数扩展至 **2048** 次；比较对象=低交互次数起点 | `verified` | 同上 |
| 25 | **最多 +19.2pp** | 指标=绝对提升上界；样本=IterResearch 作为**纯 prompting 策略**用于前沿模型；比较对象=ReAct | `verified` | 同上 |
| 26 | **1,000–2,000 token** | 指标=子 agent 回传摘要长度；样本=Anthropic 实践；比较对象=子 agent 自身消耗的「数万 token 或更多」 | `verified` | anthropic.com/engineering/effective-context-engineering-for-ai-agents |
| 27 | **18** | 指标=被测模型数；样本=Context Rot 报告（2025-07-14）；比较对象=n/a | `verified` | trychroma.com/research/context-rot |
| 28 | **~300 vs ~113k token** | 指标=输入长度对照；样本=LongMemEval 聚焦输入 vs 完整输入；比较对象=同任务两种输入构造 | `verified` | 同上 |
| 29 | **1,090** | 指标=repeated-words 任务变体数；样本=长度 25–10,000 词；比较对象=n/a | `verified` | 同上 |
| 30 | **3–5 / 3+** | 指标=并行子 agent 数 / 子 agent 并行工具数；样本=Anthropic Research 产品；比较对象=串行 | `verified` | anthropic.com/engineering/multi-agent-research-system |
| 31 | **up to 90%** | 指标=研究耗时削减上界；样本=复杂查询，来自并行工具调用改造；比较对象=改造前 | `verified`（注意是 up to） | 同上 |
| 32 | **≈7×** | 指标=token 消耗倍数；样本=agent teams，**限定条件：teammates 运行在 plan mode**；比较对象=standard sessions | `verified` —— **「plan mode」这个条件被二手文章普遍丢失** | code.claude.com/docs/en/costs |
| 33 | **3 / 20** | 指标=子 agent 默认嵌套深度上限 / 默认并发上限；样本=Claude Agent SDK（TS v0.3.219+ / Py v0.2.127+）；比较对象=n/a | `verified` | code.claude.com/docs/en/agent-sdk/subagents |
| 34 | **3–5** | 指标=推荐 teammate 数；样本=Claude Code agent teams 官方建议；比较对象=更大团队（协调开销上升、收益递减） | `verified` | code.claude.com/docs/en/agent-teams |
| 35 | **$5 / $25** | 指标=每百万 token 输入/输出定价；样本=**Claude Opus 5**，2026-08-17 查得；比较对象=同表其他型号 | `verified` | platform.claude.com/docs/en/about-claude/pricing |
| 36 | **$2 / $10** | 同上；Claude Sonnet 5（原定 2026-09-01 涨至 $3/$15 的计划**已取消**，$2/$10 成为标准价） | `verified` | 同上 |
| 37 | **$1 / $5** | 同上；Claude Haiku 4.5 | `verified` | 同上 |
| 38 | **$10 / $50** | 同上；Claude Fable 5 | `verified` | 同上 |
| 39 | **0.1× / 1.25× / 2×** | 指标=相对 base input 价的乘数；样本=cache 命中读 / 5 分钟 cache 写 / 1 小时 cache 写 | `verified` | 同上 |
| 40 | **50%** | 指标=Batch API 折扣；样本=输入与输出**双边**；比较对象=标准价 | `verified` | 同上 |
| 41 | **$10 / 千次** | 指标=web search 服务端工具计费；样本=Claude API；比较对象=web fetch **不额外收费** | `verified` | 同上 |
| 42 | **≈+30%** | 指标=同样文本产生的 token 数增幅；样本=**Claude 4.7 及以后模型**的新 tokenizer（Sonnet 4.6 及更早为旧 tokenizer）；比较对象=旧 tokenizer | `verified` —— **旧实测推出的预算算术需整体上调约 30%** | 同上 |
| 43 | **$13 / $150–250 / <$30** | 指标=人均每活跃日成本 / 人均每月 / 90% 用户的每活跃日上限；样本=企业部署均值；比较对象=n/a | `verified` | code.claude.com/docs/en/costs |
| 44 | **13%–57% / 至多 9%** | 指标=端到端成功率相对提升 / 数据发现 F1 相对提升；样本=KramaBench + 改造版 DSBench + DA-Code；比较对象=最强 baseline | `verified` | arxiv.org/abs/2510.01285 |
| 45 | **>15 vs <10** | 指标=工具数；样本=能良好管理的「定义清晰、彼此不同」的工具数 vs 会出问题的「相互重叠」的工具数；比较对象=两类实现 | `verified` —— **判据是重叠度不是数量** | OpenAI 指南 PDF |
| 46 | **150 / 1600+ / 7 / 14 / κ=0.88 / 94% / κ=0.77** | 指标=taxonomy 构建用轨迹数 / MAST-Data 标注轨迹数 / 框架数 / 失效模式数 / 标注者间一致性 / LLM 自动分类准确率 / 与人工的 Cohen's κ；样本=MAST 论文 | `verified` | arxiv.org/abs/2503.13657（v1 2025-03-17，v3 2025-10-26；NeurIPS 2025） |
| 47 | ~~42% / 37% / 21%~~ | 声称=失效在「规格不良 / 协调崩溃 / 验证薄弱」三类间的分布 | **`unverified`** —— 仅见于二手转述，**arXiv 摘要中不存在该分布**；未取得正文表格核实，不得使用 | 二手：futureagi / medium 转述 |
| 48 | ~~13.9%~~ | 声称=context dilution 导致的准确率下降 | **`unverified`** —— 来源为 diffray 博客，未指明一手实验 | diffray.ai/blog/context-dilution/ |
| 49 | ~~78% (OpenAI DR) / 94% (Claude with search)~~ | 声称=商用 deep research agent 的引用准确率 | **`unverified`** —— 出现在搜索结果摘要中，未定位到可核对的一手论文；与第 9 行的 39–77% 口径明显冲突 | 未定位 |
| 50 | **2025-06-12** | 指标=Cognition《Don't Build Multi-Agents》发表日期；页面标注 `06.12.25` | **`corrected`** —— 二手来源称「2026 年 3 月由 Walden Yan 发表」，作者对但**日期错约 9 个月** | cognition.com/blog/dont-build-multi-agents |

**假独立佐证登记**：第 13–19 行的全部数字来自**同一项工作**（Yubin Kim 等），其载体包括 `research.google` 博客、`arXiv:2512.08296`、ResearchSquare 预印本、以及 *Nature Machine Intelligence* `s42256-026-01268-y`。**计为一个来源**。与之真正独立且方向一致的是 Anthropic 关于「强依赖/需共享上下文的领域不适合 multi-agent」的自述，以及 OpenAI 指南的「先把单 agent 做满」。

---

## 对本项目的设计含义

### D1. per-loop 验证门是必需项，且必须建在「claim ⊆ source 文本」上（最高优先级）

依据：核验表 6–10 行。深度从 2 涨到 150，Fact-Check 掉约 42pp，而 Link Works（>92%）和 Relevant Content（>80%）纹丝不动。

落地：
- 门的判据抄 2605.06635 的三维分解，但**只把 Fact Check 当门，Link/Relevance 当健康度指标**。二值判定沿用其定义：`supported or consistent` → 1，`contradicted, absent, or uncertain` → 0。
- 门必须**回抓源文本再判**（retrieve-then-judge），不能让写作 agent 自证。Anthropic 的 CitationAgent 只解决「引用位置」，不解决「引用是否支持」——这两件事在我们的 schema 里要是两个字段。
- 门放在**每个 loop 结束时**，不是全流程末尾。因为退化是随深度累积的，末尾一次性验证会面对一个已经被污染的大池子。
- 我们的 `verified / unverified` 三态天然对应：判 0 的 claim 不允许升到 `verified`，只能降级留痕。这正是本项目「不洗数字」的机制实现。

### D2. 拓扑选 Centralized + 黑板台账，明确排除 Independent 与自由 handoff

依据：核验表 16 行（错误放大 Independent 17.2× vs Centralized 4.4×）+ 第 J 节（黑板）+ 第 K 节（父子间只有两个字符串通道）。

落地：
- 编排器**独占验证权**，worker 无权把自己的产出标成 `verified`。
- worker 之间**不互相喊话**，只对**证据台账**做带 schema 的状态变更（PatchBoard 那一路的「schema-grounded state mutation」），台账即黑板即产物。这同时满足：低错误放大、可审计、artifact-centric、可重跑。
- 台账是文件，不是上下文。父子间只能传字符串，所以「worker 读台账 → 追加 evidence 记录 → 回传一行摘要 + 记录 id」是唯一可靠的形状。

### D3. 扇出只用在覆盖率维度，禁止用在推理链维度

依据：核验表 15、17 行 + Anthropic 的边界自述。

落地：
- **可扇出**：候选文献检索、多来源交叉抓取、同一 claim 的独立复核、不同子问题的并行探索（这些单 agent 基线低、可并行）。
- **不可扇出**：论证链构建、跨 claim 的一致性推理、最终裁决（这些是顺序任务，−70% 的区间）。
- 加一条**准入判据**：给某个子任务加 worker 之前，先问「单 agent 在这个子任务上的基线是否已经超过约 45%」。超过就不加。这个阈值来自单一来源且 R² 只有 0.37，所以**在我们自己的语料上要重测一次**，先按 45% 作为默认值。
- worker 的工具集**窄且互不重叠**（依据：tool-heavy 任务吃协调开销；OpenAI 的判据是重叠度而非数量）。

### D4. keep-if-better 必须是逐 claim 偏序 + 反回退门

依据：核验表 20–22 行。改稿能落实 >90% 的反馈，却在 16–27% 的既有内容与引用质量上回退，break rate 31%，**而且提示工程和专职改稿子 agent 都修不好**。

落地：
- 「better」的定义不能是整篇打分，必须是**逐 claim 的集合比较**：新版本必须满足「`verified` claim 集合 ⊇ 旧版本的 `verified` claim 集合」，否则拒绝合并。
- 每次迭代产出 claim-level diff：新增 / 升级 / 降级 / **静默消失**。静默消失是硬失败，直接打回。
- 不要指望「再派一个 reviewer agent」能解决——论文已经测过这条路。要靠**机械 diff**，不是靠再一次模型判断。

### D5. 上下文：重建式工作区 + 台账外存，不做累积式长上下文

依据：第 E、F、G 节。

落地：
- 每个 loop 的 worker 上下文 = 研究问题 + 当前台账的**相关切片** + 上一次交互，对齐 IterResearch 的 O(1) 形状。不把历史全量带进去。
- 台账切片要管**呈现**而不只是**存在**（Context Rot：「what matters more is how that information is presented」）——按与当前 claim 的语义距离筛，剔除干扰项，结构化而非流水账。
- 子 agent 的回传严格限长（对齐 Anthropic 的 1,000–2,000 token 量级），长内容一律落台账、回传 id。
- compaction 只在编排器主线用，且写明保留优先级（未决 claim、矛盾证据、失败的检索路径），避免「过度压缩丢掉细微但关键的上下文」。

### D6. 预算即代码，用运行时原生旋钮而不是自造

依据：第 K 节 + 核验表 33、35–43 行。

落地：
- 直接用 `maxBudgetUsd` / `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` / `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`，不自建预算中间件。默认并发 20、深度 3 是可用起点。
- 模型分层：编排器与裁决门用 Opus 5（$5/$25），检索/抓取 worker 用 Sonnet 5（$2/$10），机械性分类用 Haiku 4.5（$1/$5）。
- **web fetch 不额外收费、web search $10/千次** → 检索策略应偏向「少而准的 search + 多次 fetch」，这与 D1 的「回抓源文本再判」在成本上是同向的，很划算。
- 预算算术**上调 30%**（新 tokenizer），并把 cache read 0.1× 纳入模型：台账的稳定前缀应该做成可缓存的。
- 走 **subagents + Workflow**，不走 agent teams：teams 是实验特性、无嵌套、且**在 `-p` / Agent SDK 会话下根本不 spawn teammate**，与我们的 headless 编排不兼容。

### D7. 框架选型：不引入 LangGraph 一类的编排框架

依据：第 K 节（DSH/Claude Agent SDK 原生已提供隔离、并发、深度、预算、Workflow）+ LangGraph 侧**找不到任何一手的、可复现的对比测量**（见「未决与风险」）。

落地：durable execution 是真需求（长跑、崩溃恢复、去重），但它应当由**台账的幂等追加 + 可重跑产物**满足，而不是引入一层图状态机。我们的可重跑性来自「产物 + 客观门」，不来自框架的 checkpoint。

### D8. 把「本项目自证」写进设计

本轮最强的证据（42pp 那条）恰恰来自一个只测了两个模型、没报统计检验、用 LLM-as-judge 的单篇预印本。一个以「不洗数字」为卖点的系统，**不能把它当定论引用**。

落地：把「深度 × Fact-Check 准确率」曲线做成本项目的**内建自检基准**——在自己的语料上跑 2/10/30/50/70/100/150 七档，产出自己的曲线，用它来标定 per-loop 门的触发深度。这既是验证门的参数来源，也是这个系统「产品即可信度」主张的第一个自证。

---

## 未决与风险

**U1. 42pp 那条证据的强度有限，必须自证。** 单篇预印本（2026-05，v1），仅两个模型做深度消融，无相关系数/回归/p 值，判定器为 LLM-as-judge（有人工校准）。方向可信、量级待定。→ 见 D8，做内建自检基准。另需持续关注该论文是否出现 v2 或同行评议版本。

**U2. 45% 能力饱和阈值来自单一工作，且 R² 仅 0.373。** 该阈值在我们的「学术证据探索」任务族上没有被测过（其六基准里没有一个是文献研究）。BrowseComp-Plus 最接近但仍是找信息而非评证据。→ 按默认值用，但列为待标定参数。

**U3. MAST 的失效分布（42/37/21）无法核实。** 仅见二手转述，arXiv 摘要不含该分布。未取得正文表格。→ 已标 `unverified`，本项目文档中不得使用。如需该分布，须回抓 arXiv PDF 正文表格。

**U4. LangGraph 的「迁移潮」缺一手证据。** 所有指控（抽象层过重、API 频繁变更、调试困难、生态耦合）都来自 SEO 博客与论坛零散经验，**没有一份可复现的对比测量**。HN 上有具体但零散的抱怨（如 2025-06「state 是个 JSON 导致运行时类型错误」）。另有一条可核实的硬事实：2026-06-12 报道的 LangGraph 自托管漏洞链（SQL 注入 + 不安全反序列化 → RCE，已修补，thehackernews.com），但我未回抓官方 advisory/CVE 编号确认。→ 本维度的框架选型结论（D7）**建立在 DSH 原生能力已足够**，而不是建立在「LangGraph 不行」的证据上；后者不足以支撑论断。

**U5. Nature MI 版本未直读。** `s42256-026-01268-y` 触发 idp.nature.com 认证跳转，未取得摘要原文。因确认为同一工作的期刊版，不影响结论，但**同行评议版可能修订了数字**（arXiv v3 的 260/6 与博客的 180/4 已有一次漂移，期刊版可能是第三个版本）。→ 引用时一律用 arXiv v3 + 日期，并注明存在期刊版未核。

**U6. Anthropic 那篇多 agent 文章的模型代际已过时。** 90.2%、15×、80% 都基于 2025 年的 Opus 4 / Sonnet 4。到 2026-08 已迭代到 Opus 5 / Sonnet 5 / Fable 5，且 tokenizer 已变（+30% token）。**这些数字不能外推到当前代际**，尤其 15× 这类成本倍数。→ 全部标注日期；成本估算一律用 2026-08 现价重算。

**U7. 黑板架构的证据来自数据科学场景，不是文献研究。** 13%–57% 的提升在 KramaBench / DSBench / DA-Code 上取得，任务是「在数据湖里找相关数据」。与「在文献里找支持某 claim 的证据」结构相似但不等同。→ 作为架构灵感采纳，不引用其数字作为本项目的预期收益。

**U8. 未覆盖但相关的方向（留给下一轮）：** (a) 具体的 durable-execution 方案对比（Temporal / Restate / DBOS / Cloudflare Workflows）只做到二手层面，未回抓任一官方文档；(b) 「引用准确率」在**中文/非英文文献**上的表现完全没有证据；(c) 多 agent 辩论 / self-consistency 与「验证门」两条路线的直接对比，本轮未找到一手实验；(d) 学术数据库（arXiv/PubMed/Semantic Scholar/OpenAlex）API 的具体配额与可重跑性约束，属另一维度但会直接约束扇出宽度。

**U9. 方法论自查：本轮的搜索预算在中途耗尽。** WebSearch 200 次会话配额在第 12 次检索后触顶（此前会话已消耗），后续改用 Serper 脚本补搜。这不影响已核实的数字，但意味着**「反证检索」做得不够**——我主要在找「扇出何时有害」的证据并找到了，但没有系统检索「扇出在文献研究场景下有效」的反面证据。→ 下一轮应专门做一次 disconfirming search。
