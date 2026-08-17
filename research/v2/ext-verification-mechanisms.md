# 可自动化的声明验证机制菜单（含精度数字）

调研日期：2026-08-17。所有数字均标注口径三元组与状态。凡带"截至"标记的数字会随时间失效。

---

## 结论摘要

1. **文献里几乎所有"高精度"验证数字都是聚合级（system-level）口径，而本项目要的是逐条（per-claim）口径，两者差一个数量级。** 最典型：FActScore 论文摘要里的 "error rate of <2%" 是"自动估计的 FActScore 与人工 FActScore 在模型层面的差值"，而同一篇论文附录里逐条原子事实的 F1-micro 只有 53.3%–83.2%（随被评模型而变）。AutoAIS 同理：系统级与人工 AIS 的 Pearson 相关高达 0.96，但论文明确警告"不要细读单条 AutoAIS 分数"。**任何按聚合数字选型的方案，落到本项目的逐条 verified/unverified 标签上都会崩。**

2. **决定一个验证器能不能上线的是假阳率（FPR），不是召回率。** 2026-07 的 HALLMARK 直接把这句写成结论：agentic 查证把召回买到 0.98–0.99，但 FPR 同时飙到 0.43–0.48；而规则型 bibtex-updater 用 0.865 的检出率换 0.092 的 FPR。对本项目而言，误标 "unverified" 的成本远高于漏标，因为产品是可信度本身。

3. **确定性机制（DOI 解析、结构化字段匹配、逐字引文匹配、统计量重算）应当是一级门禁；模型型机制（NLI / LLM-judge）只能做二级过滤，且必须记录模型 ID + 调用日期。** 确定性机制可 re-run、可 diff、无模型漂移；模型型机制在 2026 年已被证明存在"信度高但效度低"的系统性问题（21 个 judge 模型、约 541,000 次判断：exact match 0.788–0.849，但 chance-corrected 的 Cohen's κ 只有 0.376–0.511，缺口均值 38.6 个百分点）。

4. **声明分解（decompose-then-verify）不是免费的，对强 verifier 反而是净负。** NAACL 2025 的 Decomposition Dilemmas 给出反例：MiniCheck 在 WiCE claim-level 上，从不分解的 80.01 BAcc 掉到 FActScore 式分解后的 71.11。分解应当是 keep-if-better 的可选路径，而不是流水线的固定一环。

5. **三类 claim 中，"逻辑推断类"在文献里几乎无成熟机制。** 数据推导类有 statcheck / GRIM 这类可重算的确定性工具（statcheck 总体准确率 96.2%–99.9%）；文献引用类有 DOI/Crossref/OpenAlex + NLI 的成熟栈；而推断类只有论证挖掘（Toulmin warrant 检测加权 F1 0.88，但语料是教育对话、不是学术论证），且这条赛道有历史污点——ARCT 上 BERT 的 77% 被证明完全由伪统计线索解释，在对抗集上退化到随机。**这一类必须自建机制，不能指望现成模型。**

6. **本轮亲测到一个直接威胁本项目取证管线的失败模式：从二进制 PDF 抓取时，摘要模型会编造数字。** 同一篇 HALLMARK 论文，走 `arxiv.org/pdf/2607.18360` 得到"2,000 篇 LLM 生成摘要 / DOI 基线召回 45% / FPR 8%"，走 `arxiv.org/html/2607.18360` 得到"2,526 条 BibTeX 条目 / DOI-only 检出率 0.268 / FPR 0.185"。后者与论文正文一致，前者是幻觉。**取证层必须强制 HTML/文本源 + 逐字引用 + 可定位偏移，禁止从二进制 PDF 摘要直接出数字。**

---

## 系统与机制逐条（含 URL）

### 机制菜单总表

| # | 机制 | 覆盖的 claim 类型 | 实测精度 + 口径三元组 | 确定性 / 模型型 | 已知失效模式 |
|---|------|------------------|---------------------|----------------|-------------|
| M1 | DOI 解析（doi.org / Crossref `/works/{doi}`） | 文献引用类（存在性） | 检出率 0.268、FPR 0.185：在 HALLMARK 2,526 条 BibTeX 条目上，仅靠 DOI 是否可解析判定"该文献是否幻觉" | 确定性 | 只能验"存在"，不能验"内容支持claim"；真实文献配错 DOI 时漏判；预印本/无 DOI 文献误判为幻觉 |
| M2 | 书目字段模糊匹配（Crossref query.bibliographic + 校验打分，SBMV 算法） | 文献引用类（存在性 + 元数据正确性） | 真实脏数据上 P 0.9809 / R 0.9456 / F1 0.9629（2,000 条来自 Crossref 元数据的非结构化 reference string，2018-12）；合成数据上 P 0.9923 / R 0.7902 / F1 0.8448（7,374 条记录 × 11 种引用格式，2018-11） | 确定性（检索 + 规则打分） | **同一算法在合成 vs 真实数据上的 F1 差 12 个点**——引用任何"匹配准确率"必须说明数据来源；Crossref 的 relevance score 官方文档没有给出归一化语义，不能当作跨查询可比的置信度 |
| M3 | OpenAlex / Semantic Scholar 交叉字段匹配 | 文献引用类（存在性、作者/年份/期刊一致性） | 未取到官方一手精度数字（见"未决"）；OpenAlex 机构级召回 93%、但检出结果中 24% 属于其他机构（二手转述，未核） | 确定性（API 查询 + 字段比对） | 作者消歧错误；同名论文/预印本-正式版双记录；覆盖偏差（非英语、非期刊文献） |
| M4 | 逐字引文匹配（verbatim quote match against source text） | 文献引用类（引文忠实性） | 无公开的端到端精度测量（见"未决"）。相关侧证：Quote-Tuning 报告可把"逐字引用高质量文档"的比例相对基线提升最多 130% | 确定性（字符串/规范化后精确匹配） | PDF 文本抽取的连字符、连字、双栏乱序会造成假阴；原文改版/预印本与正式版差异；引文正确但语境被截断（"正确引用、错误使用"） |
| M5 | NLI / 蕴含式引用验证（AutoAIS 谱系） | 文献引用类（"这句话是否被这段来源支持"） | TRUE 基准：ANLI(T5-11B) 平均 ROC-AUC 81.5，Q² 80.7，QuestEval 71.4，ROUGE-L 69.2，最优集成 86.0（在 11 个数据集中的 9 个上取平均，排除 VitaminC 与 FEVER） | 模型型 | **系统级好、单条不可靠**：AutoAIS 系统级 Pearson 0.96，但例级"相关性低得多且不稳定"，原作者明确不建议细读单条分数 |
| M6 | 小模型事实核查器（MiniCheck / Bespoke-MiniCheck） | 文献引用类 + 数据推导类（对给定证据段的 grounding） | MiniCheck-FT5（770M）平均 balanced accuracy 74.7，GPT-4 为 75.3，AlignScore 70.4（LLM-AggreFact 的 10 个数据集平均，EMNLP 2024）；公开 leaderboard 上 Bespoke-Minicheck-7B 平均 77.4、Claude-3.5 Sonnet 77.2（11 个数据集，页面无更新日期） | 模型型（但可本地固定权重 → 半确定性） | 数据集数量在论文/leaderboard/后续论文间从 10→11→14 漂移，跨版本数字不可直接比；对高 ROUGE（改写度低）的不可归因样本 TNR 显著偏低 |
| M7 | 检索增强的 LLM 事实评估流水线（FActScore / SAFE / VeriScore） | 文献引用类 + 数据推导类（长文整体事实精度） | FActScore 估计器聚合级 ER <2%，但逐条原子事实 F1-micro 仅 83.2%（InstructGPT 传记）/ 70.5%（ChatGPT）/ 53.3%（PerplexityAI）；SAFE 与众包标注者在约 16k 条事实上一致率 72%，在随机抽取的 100 个分歧样本上 SAFE 胜出 76%，成本比人工便宜 20 倍以上 | 模型型 | 假设"每条 claim 都可验证"（VeriScore 正是为此而生）；聚合分数掩盖逐条错误；SAFE 的 72% 是与**众包**标注者比，不是与领域专家比 |
| M8 | 可验证性过滤 + 声明抽取（VeriScore） | 三类通用的前置步骤（判定 claim 是否"可被验证"） | 人工偏好：VeriScore 抽取的 claim 在 360 个标注项中被选中 334 次（92.8%），SAFE 26 次，Fleiss κ 0.7662；微调 Mistral 抽取器对 GPT-4 抽取结果 exact match 43.7%、RougeL 0.801（300 对）；验证端微调 Llama3 F1 0.841；**人工核验 320 条 claim 时只有 55% 被证据支持、40% 判为 inconclusive** | 模型型 | 微调抽取器与教师模型的 exact match 只有 43.7%——抽取环节本身是高方差的；"inconclusive 40%" 说明大多数真实 claim 落不进二值判定 |
| M9 | 声明分解（decompose-then-verify） | 三类通用的前置步骤 | MiniCheck 在 WiCE claim-level：不分解 80.01 BAcc → FActScore 式分解后 71.11；MiniCheck 在 FELM response-level：48.10 F1 → WiCE 式分解后 68.12；GPT-4o-mini 在 FELM：71.56 → 54.34（FActScore 式分解） | 模型型 | **分解利弱不利强**：对弱 verifier 提升、对强 verifier 净负；四类分解错误（上下文遗漏、歧义、过度分解、改变原意），FActScore 式以过度分解为主，VeriScore 式以上下文遗漏为主 |
| M10 | 去语境化 / molecular facts | 三类通用的前置步骤 | 提出两个判据：decontextuality（可独立解读）与 minimality（补充信息最少）；具体数值未取到（见"未决"） | 模型型 | 补上下文会让 claim 不再原子化，"到底在验哪一部分"变得不明确 |
| M11 | LLM-as-a-judge（作为验证裁判） | 三类通用（尤其推断类的兜底） | 约 541,000 次判断、21 个模型、9 家厂商、118 次运行、3 个基准：MT-Bench exact match 0.788–0.849，但 Cohen's κ 仅 0.376–0.511（缺口 33.8–41.2 pp，均值 38.6 pp）；跨基准排名最多位移 14 位；test-retest 从 MT-Bench 的 0.943 降到更难的 JudgeBench 的 0.911 | 模型型 | **信度 ≠ 效度**：同一 judge 可以自洽（test-retest 0.99）却系统性带位置偏置；难题上退化；"多数投票一致率"不是可信度证据 |
| M12 | 统计量重算（statcheck） | 数据推导类（已发表统计报告的内部一致性） | 总体准确率 96.2%–99.9%，敏感度 85.3%–100%，特异度 96.0%–100%（范围取决于假设与设置，如是否启用单尾检测）；应用结果：>250,000 个 p 值、8 本主要心理学期刊、1985–2013，**半数使用 NHST 的论文含至少一个与检验统计量/自由度不一致的 p 值，八分之一的论文含会改变统计结论的严重不一致** | 确定性（正则抽取 + 重算） | 只覆盖 APA 格式的 NHST 报告；单尾检验、事后校正、四舍五入约定会造成假阳；抽取端依赖 PDF/HTML 文本质量 |
| M13 | 粒度一致性检验（GRIM） | 数据推导类（整数量表均值与样本量的可行性） | 260 篇近期论文抽样，其中 71 篇适用 GRIM，36 篇（50.7%）至少含一个与样本量/量表特性不一致的均值，>20%（16 篇）含多处；向 21 篇索要数据、9 篇回应，全部确认存在报告错误 | 确定性（纯算术） | 仅适用于整数型数据（Likert 等）且需已知条目数与 N；不能定位错误来源 |
| M14 | 论证结构挖掘（Toulmin warrant） | **逻辑推断类**（本项目最缺的一类） | warrant 有无检测加权 F1 0.88；claim 0.91；evidence 0.80。语料：三个子集共 100 / 1,026 / 211 条回答，主题是"某实体是否算智能"，分类器为 Random Forest 等传统 ML | 模型型（浅层特征） | **域外**：语料是教育对话不是学术论证；只判 warrant 有无，不判 warrant 是否成立 |
| M15 | 论证推理理解基准（ARCT 谱系） | 逻辑推断类 | BERT 峰值 77%，仅比未受训人类基线低三个百分点——但该成绩**完全由数据集中的伪统计线索解释**；在作者构造的对抗集上所有模型退化到随机 | 模型型 | 这条路线的历史教训：推断类任务的"高分"极易是 Clever Hans；任何推断类验证器都必须过对抗集 |
| M16 | 引用幻觉检测（URL/引文健康度） | 文献引用类（存在性，面向 agent 自身产出） | 2026-04 实测：Gemini 2.5 Pro Deep Research 幻觉 URL 13.3% [12.7, 13.9]（11,309 条 URL）；OpenAI Deep Research 3.5% [3.0, 4.1]（4,121 条）；Claude 系 3.0%–3.2%；pooled deep research agents 10.7% vs search-augmented 4.8%；用 Wayback Machine 区分"幻觉"与"链接失效"；接入 agentic 自纠后不可解析引用降到 <1%，降幅 6–79× | 确定性（存档比对） | 只验 URL 可解析性，不验内容；Wayback 覆盖不全的站点会误判 |

### 各机制的补充说明与出处

**M1/M2 —— 书目存在性核验**
- Crossref REST API 会用 `X-Rate-Limit-Limit` / `X-Rate-Limit-Interval` 头广告速率上限，文档示例为 50 请求/秒；带 `mailto` 参数或 User-Agent 内含 `mailto:` 可进入 polite pool。来源：https://raw.githubusercontent.com/CrossRef/rest-api-doc/master/README.md
- 官方文档只说"若查询带 query 参数则按 relevance score 排序"，**没有**给出该分数的归一化语义或跨查询可比性说明。因此把 score 当置信度阈值是无源之举。
- 合成数据实验（2018-11-12）：https://www.crossref.org/blog/matchmaker-matchmaker-make-me-a-match/
- 真实数据实验（2018-12-18）：https://www.crossref.org/blog/reference-matching-for-real-this-time/ ——该文明确说合成串"太完美，与 Crossref 元数据完全一致"，真实世界"应当预期各种错误与噪声"，且"在真实数据集上不带校验的 SBM 反而不如 legacy"。

**M5 —— AutoAIS / NLI 谱系**
- TRUE 基准原文：https://arxiv.org/abs/2204.04991 （ar5iv 全文：https://ar5iv.labs.arxiv.org/html/2204.04991 ）。选 ROC-AUC 正是为了免去逐任务人工定阈值。
- AutoAIS 与人工 AIS 的关系：https://arxiv.org/abs/2212.08037 （ar5iv 全文：https://ar5iv.labs.arxiv.org/html/2212.08037 ）。原文措辞："correlation between system AIS and AutoAIS scores is remarkably strong, with a Pearson coefficient of 0.96"，紧接着对例级说 "Correlation was much lower and more variable here."
- AttributionBench 给出难度上界：**微调后的 GPT-3.5 在二值分类口径下也只有约 80% macro-F1**；作者归因于"模型处理细微信息的能力不足"以及"模型可见信息与人工标注者可见信息之间的差异"。https://aclanthology.org/2024.findings-acl.886/

**M6 —— 小模型核查器与它的口径漂移**
- MiniCheck 论文（EMNLP 2024）：https://arxiv.org/abs/2404.10774 / 全文 https://arxiv.org/html/2404.10774v1 。BAcc 定义为 ½(TPR + TNR)，在 10 个数据集上平均。
- 公开 leaderboard（11 个数据集）：https://llm-aggrefact.github.io/ ——页面**未标注最后更新日期**，截至 2026-08-17 首位为 Bespoke-Minicheck-7B 77.4。
- 反面证据（关键）："Verify with Caution: The Pitfalls of Relying on Imperfect Factuality Metrics"，https://arxiv.org/html/2501.14883v1 ：Bespoke-7B（Avg BAcc 77.4%）与 gpt-4-turbo（76.2%）分数接近，但两者标记为"不可归因"的样本集合在 14 个数据集中的 5 个上 IoU < 50%；在 TofuEval-MediaSum 上所有指标 BAcc 都在 68–72%，但 gpt-4-turbo 低估 headroom 12.3%、MiniCheck-Rbta 高估 11.2%；response-level 偏差最坏 −29.8%，约为 claim-level 的两倍；在至少 6 个系统的 8/14 个数据集上，gpt-4-turbo 平均把 26% 的系统对排错、Bespoke-7B 排错 20%。

**M7 —— FActScore / SAFE**
- FActScore：https://arxiv.org/abs/2305.14251 、全文 https://ar5iv.labs.arxiv.org/html/2305.14251 。FActScore 的定义是"被可靠知识源支持的原子事实百分比"，即**precision**，不是 accuracy。论文自述 "Our estimator closely approximates FActScore with an error rate of <2%"，该 ER 定义为"真值 FActScore 与估计 FActScore 之差"，在聚合层计算。附录 B.2 的逐条 F1-micro（Inst-LLAMA + retrieval + NP）为 83.2 / 70.5 / 53.3。人工标注成本 $4/篇，标注者一致率 96% / 90% / 88%。
- SAFE：https://arxiv.org/abs/2403.18802 。"SAFE agrees with crowdsourced human annotators 72% of the time"（约 16k 条事实）；"on a random subset of 100 disagreement cases, SAFE wins 76% of the time"；"more than 20 times cheaper than human annotators"。

**M8/M9/M10 —— 抽取与分解**
- VeriScore（Findings of EMNLP 2024）：https://aclanthology.org/2024.findings-emnlp.552/ 、https://arxiv.org/abs/2406.19276 、全文 https://arxiv.org/html/2406.19276v1 。摘要原话指出 FActScore 与 SAFE "assume that every claim is verifiable"，这正是它们不适用于多数生成任务的原因；8 个长文任务、16 个模型；并且发现同一模型在传记任务与长问答任务上的 VeriScore 不必然相关。
- Decomposition Dilemmas（NAACL 2025）：https://arxiv.org/abs/2411.02400 、全文 https://arxiv.org/html/2411.02400v1 。结论句："Decomposition generally benefits weaker verifiers, while it tends to negatively affect stronger verification systems."
- Molecular Facts：https://arxiv.org/abs/2406.20079 ，提出 decontextuality + minimality 两个判据。
- DnDScore：https://arxiv.org/abs/2412.13175 ，指出分解与去语境化的交互此前无人系统研究，且"策略选择会改变最终的事实性分数"。

**M11 —— LLM-judge 的信度/效度分离**
- "Reliability without Validity: A Systematic, Large-Scale Evaluation of LLM-as-a-Judge Models Across Agreement, Consistency, and Bias"，https://arxiv.org/html/2606.19544v1 （2026-06）。约 541,000 次判断、21 个模型、9 家厂商、118 次运行。κ 缺口均值 38.6 pp；Llama 3.3 70B 从 MT-Bench 第 5 位掉到 JudgeBench 第 20 位；Qwen 3 8B 在存在严重位置偏置的同时 test-retest 高达 0.992。

**M12/M13 —— 统计重算**
- statcheck 有效性：https://research.tilburguniversity.edu/en/publications/the-validity-of-the-tool-statcheck-in-discovering-statistical-rep/ （PsyArXiv 2017，两项研究）。官方页面 https://mbnuijten.com/statcheck/ 说明 web 版仅跑默认选项（例如不做单尾检验自动识别）。
- 流行率：Nuijten et al. (2016), Behavior Research Methods 48(4):1205-1226, DOI 10.3758/s13428-015-0664-2。摘要原文见 Europe PMC。
- GRIM：Brown & Heathers，PeerJ Preprints 2016，DOI 10.7287/peerj.preprints.2064v1（正式版为 Social Psychological and Personality Science 2017）。

**M14/M15 —— 推断类的现状**
- Toulmin warrant 检测：https://pmc.ncbi.nlm.nih.gov/articles/PMC8680349/ （Frontiers in Artificial Intelligence, 2021）。
- ARCT 的 Clever Hans 教训：https://aclanthology.org/P19-1459/ （ACL 2019）。

**M16 —— 引用幻觉的当前量级（会快速失效）**
- HALLMARK（2026-07）：https://arxiv.org/abs/2607.18360 / https://arxiv.org/html/2607.18360 。2,526 条 BibTeX 条目、14 种幻觉类型（11 种经验类 + 3 种压力测试类）、3 个难度层、每条 6 项诊断子测试、含抗污染 held-out 划分。原文结论："the order-of-magnitude spread in false-positive rates (FPRs) -- not recall -- governs whether a verifier's flags are mostly true catches or mostly noise"，并指出多数 LLM 会对训练截止之后发表的论文过度标记。
- Deep research agent 的 URL 幻觉（2026-04-03）：https://arxiv.org/html/2604.03173v1 。
- 生成式搜索引擎的引用质量（EMNLP 2023 Findings）：https://arxiv.org/abs/2304.09848 ，四个引擎（Bing Chat、NeevaAI、Perplexity.ai、YouChat），citation recall 51.5%、citation precision 74.5%。注意这是被测对象的质量，不是验证器的精度。

---

## 载荷数字核验表

一行一个数字。状态：`verified`＝已读一手源并可引原文；`corrected`＝流传版本口径失真，此处给出正确口径；`unverified`＝未能触达一手源。

| 数字 | 口径三元组（什么指标 / 什么样本条件 / 与什么比较） | 状态 | 一手出处 |
|------|------------------------------------------------|------|---------|
| FActScore 估计器 ER < 2% | 估计 FActScore 与人工 FActScore 之差 / 在**模型聚合层**计算，非逐条 / 与人工标注的 FActScore 比 | **corrected**（常被转述为"FActScore 准确率 98%"或"逐条误判率 2%"，均错） | https://ar5iv.labs.arxiv.org/html/2305.14251 |
| 83.2% / 70.5% / 53.3% | 逐条原子事实判定的 F1-micro / Inst-LLAMA + retrieval + NP 估计器，分别在 InstructGPT / ChatGPT / PerplexityAI 生成的传记上 / 与人工逐条标注比 | verified | 同上，附录 B.2 Table 9 |
| FActScore 人工标注 $4/篇；标注者一致率 96% / 90% / 88% | 单篇生成的人工标注成本；同一生成的多标注者一致率 / InstructGPT / ChatGPT / PerplexityAI / — | verified | 同上，§3.3 |
| SAFE 72% | 与**众包**人工标注者的逐条一致率 / 约 16,000 条 individual facts / 与众包标注比（非专家） | verified | https://arxiv.org/abs/2403.18802 |
| SAFE 胜出 76% | 在分歧样本上的裁定胜率 / 随机抽取的 **100 个分歧样本** / 与人工标注对比（人工胜 19%） | verified | 同上 |
| SAFE 便宜 20 倍以上 | 标注成本比 / 同一评测任务 / 与人工标注者比 | verified | 同上 |
| MiniCheck-FT5 74.7 | balanced accuracy = ½(TPR+TNR) 的平均 / LLM-AggreFact 的 **10 个**数据集 / 与 GPT-4 的 75.3、AlignScore 的 70.4 比 | verified | https://arxiv.org/html/2404.10774v1 |
| 400× 更低成本 | 推理成本比 / MiniCheck-FT5（770M 参数） / 与 GPT-4 比 | verified | 同上（摘要） |
| Bespoke-Minicheck-7B 77.4 | 平均 balanced accuracy / 公开 LLM-AggreFact leaderboard 的 **11 个**数据集 / 与 Claude-3.5 Sonnet 77.2、gpt-4o 75.9 比 | verified（但页面无更新日期，截至 2026-08-17 抓取） | https://llm-aggrefact.github.io/ |
| ANLI(T5-11B) 平均 ROC-AUC 81.5 | ROC-AUC 的宏平均 / TRUE 基准 11 个数据集中的 **9 个**（排除 VitaminC 与 FEVER，因 SCZS 在 VitaminC 上训练过） / 与 Q² 80.7、QuestEval 71.4、ROUGE-L 69.2、最优集成 86.0 比 | verified | https://ar5iv.labs.arxiv.org/html/2204.04991 |
| AutoAIS Pearson 0.96 | **系统级** AutoAIS 分数与系统级人工 AIS 分数的 Pearson 相关 / Attributed QA 的多个系统 / — | verified；且原文明示例级相关"much lower and more variable" | https://ar5iv.labs.arxiv.org/html/2212.08037 |
| 微调 GPT-3.5 约 80% macro-F1 | macro-F1 / AttributionBench，**二值分类**口径 / 与其他基线比 | verified | https://aclanthology.org/2024.findings-acl.886/ |
| citation recall 51.5% / precision 74.5% | recall＝完全被引用支持的**生成句**占比；precision＝确实支持所配句子的**引用**占比 / 四个生成式搜索引擎（Bing Chat、NeevaAI、Perplexity.ai、YouChat），2023 年数据 / — | verified；**注意这是被测系统的质量，不是验证机制的精度** | https://arxiv.org/abs/2304.09848 |
| statcheck 准确率 96.2%–99.9%；敏感度 85.3%–100%；特异度 96.0%–100% | 与人工编码的不一致判定对比 / 两项研究，范围随假设与设置（如单尾检测开关）变化 / 与人工编码比 | verified（读到机构库登记的论文摘要；未读全文样本量） | https://research.tilburguniversity.edu/en/publications/the-validity-of-the-tool-statcheck-in-discovering-statistical-rep/ |
| 半数论文含至少一个不一致 p 值；八分之一含严重不一致 | 论文级占比 / >250,000 个 p 值、8 本主要心理学期刊、1985–2013、statcheck 能从其中过半数论文提取到 NHST 结果 / — | verified | Europe PMC，DOI 10.3758/s13428-015-0664-2 |
| GRIM：71 篇适用中 36 篇（50.7%）不一致 | 论文级占比 / 260 篇近期主流心理学期刊论文抽样，其中 71 篇适用 GRIM / — | verified | Europe PMC，DOI 10.7287/peerj.preprints.2064v1 |
| Crossref SBMV：P 0.9809 / R 0.9456 / F1 0.9629 | 精确率/召回/F1 / **真实**的 2,000 条非结构化 reference string（取自 Crossref 元数据，人工确认目标 DOI） / 与 legacy 的 0.9895 / 0.8685 / 0.9251 比 | verified | https://www.crossref.org/blog/reference-matching-for-real-this-time/ （2018-12-18） |
| Crossref SBMV：F1 84.5% vs legacy 52.9% | 平均 F1 / **合成**数据：7,374 条 Crossref 元数据记录 × 11 种引用格式 / 与 legacy 比（precision 99.2% vs 99.3%，recall 79.0% vs 42.0%） | verified；**与上一行是同一算法的不同口径，切勿混用** | https://www.crossref.org/blog/matchmaker-matchmaker-make-me-a-match/ （2018-11-12） |
| Crossref 速率上限示例 50 req/s | 由 `X-Rate-Limit-Limit` / `X-Rate-Limit-Interval` 头广告，文档示例值 / — | verified | https://raw.githubusercontent.com/CrossRef/rest-api-doc/master/README.md |
| HALLMARK 基准规模 2,526 条 BibTeX 条目 / 14 种幻觉类型 / 3 难度层 / 每条 6 子测试 | 基准构成 / — / — | verified（**仅 HTML 路径**；PDF 路径给出的"2,000 篇摘要"是幻觉） | https://arxiv.org/html/2607.18360 |
| DOI-only 基线 检出率 0.268 / FPR 0.185 | 幻觉引用检出率与假阳率 / HALLMARK 全集 / 与 LLM、agent、规则型验证器比 | verified（HTML 路径） | 同上 |
| 零样本 LLM FPR 跨度 0.050–0.702；检出率 48%–91% | 假阳率与检出率 / HALLMARK 全集，跨 cohort 各前沿模型（低端 Gemini 2.5 Pro 0.050，高端 DeepSeek-V3.2 0.702） / — | verified（HTML 路径） | 同上 |
| 工具增强 agent 检出率 0.98–0.99、FPR 0.431–0.478 | 同上口径 / GPT-5.1 + Crossref/OpenAlex/arXiv 等配置 / 与规则型 bibtex-updater（0.865 / 0.092）比 | verified（HTML 路径） | 同上 |
| Gemini 2.5 Pro Deep Research URL 幻觉 13.3% [12.7, 13.9] | 不可解析且无存档快照的 URL 占比 / 11,309 条采样 URL，2026-04 / 与 OpenAI Deep Research 3.5%、Claude 3.0–3.2% 比 | verified | https://arxiv.org/html/2604.03173v1 |
| deep research agents 10.7% vs search-augmented 4.8% | 同上口径的合并均值 / 两类系统分组 / 互比 | verified | 同上 |
| LLM-judge：exact match 0.788–0.849 但 Cohen's κ 0.376–0.511 | 与人工判定的一致率 / MT-Bench，21 个 judge 模型、约 541,000 次判断 / 未校正 vs chance-corrected（缺口 33.8–41.2 pp，均值 38.6 pp） | verified | https://arxiv.org/html/2606.19544v1 |
| judge 排名跨基准位移最多 14 位 | 排名位移 / 3 个基准间对比（Llama 3.3 70B：MT-Bench 第 5 → JudgeBench 第 20） / — | verified | 同上 |
| test-retest 0.943 → 0.911 | 重测信度均值 / 16 个 judge，MT-Bench → 更难的 JudgeBench / — | verified | 同上 |
| Bespoke-7B 与 gpt-4-turbo 在 5/14 个数据集上 IoU < 50% | 两个指标判为"不可归因"的样本集合的交并比 / 14 个数据集 / 两者平均 BAcc 仅差 1.2 点（77.4% vs 76.2%） | verified | https://arxiv.org/html/2501.14883v1 |
| 系统排序错误率：gpt-4-turbo 26%、Bespoke-7B 20% | 系统对排序错误的平均比例 / 至少含 6 个系统生成的 8/14 个数据集 / 与真值排序比 | verified | 同上 |
| response-level 偏差最坏 −29.8%，约为 claim-level 的两倍 | headroom 估计偏差 / gpt-4-turbo / claim-level 对比 | verified | 同上 |
| 分解代价：MiniCheck WiCE 80.01 → 71.11 BAcc | balanced accuracy / WiCE claim-level，FActScore 式分解 / 与不分解基线比 | verified | https://arxiv.org/html/2411.02400v1 |
| 分解收益：MiniCheck FELM 48.10 → 68.12 F1；GPT-4o-mini 71.56 → 54.34 | F1 / FELM response-level，WiCE 式分解（前者）/ FActScore 式分解（后者） / 与不分解基线比 | verified | 同上 |
| VeriScore 人工偏好 334/360（92.8%），Fleiss κ 0.7662 | 标注者在成对比较中偏好 VeriScore 抽取 claim 的次数 / 8 个长文任务共 360 个标注项 / 与 SAFE（26 次）比 | verified | https://arxiv.org/html/2406.19276v1 |
| VeriScore 微调抽取器 exact match 43.7%、RougeL 0.801 | 与 GPT-4 抽取 claim 的重合度 / 300 对 / 与教师模型 GPT-4 比 | verified | 同上 |
| VeriScore 人工核验：仅 55% claim 被支持，40% inconclusive | 人工判定分布 / 320 条 claim / — | verified | 同上 |
| Toulmin warrant 有无检测 加权 F1 0.88 | 全类别加权 F1 / 三个子集共 100 / 1,026 / 211 条回答，主题为"某实体是否算智能"，Random Forest 等传统 ML / 与 claim 0.91、evidence 0.80 比 | verified；**域外，非学术论证语料** | https://pmc.ncbi.nlm.nih.gov/articles/PMC8680349/ |
| BERT 在 ARCT 峰值 77%，低于未受训人类基线 3 个点；对抗集上退化到随机 | 准确率 / ARCT 测试集 / 与人类基线、与对抗集比 | verified | https://aclanthology.org/P19-1459/ |
| Quote-Tuning 逐字引用提升"最多 130%" | 逐字引用高质量文档的相对增幅 / — / 与 base model 比 | verified（摘要级；**是生成侧指标，不是验证器精度**） | https://arxiv.org/abs/2404.03862 |
| OpenAlex 机构级召回 93%、检出中 24% 属其他机构 | 召回与精确率 / 单个机构的案例研究 / — | **unverified**（仅见二手转述，未触达一手评测） | 待补 |
| S2AND 作者消歧 B³ F1 90%（旧系统 78.4%） | B³ F1 / Semantic Scholar 作者消歧 / 与前代系统比 | **unverified**（Semantic Scholar 官方 API 博文中未见此数字；未找到一手来源） | 待补 |
| OpenAlex / Semantic Scholar API 速率上限 | 请求数上限 / — / — | **unverified**（官方文档页重定向或为 JS 渲染，未取到） | 待补 |
| 逐字引文匹配的端到端精度 | — | **unverified**（未找到公开的端到端测量；PDF 文本抽取保真度亦无公开量化） | 待补 |

---

## 对本项目的设计含义

### D1. 选型必须按"逐条口径"，聚合口径数字一律不得进门禁
本项目的产品是**每条 claim 一个 verified/unverified 标签**。因此可用的候选精度只有 per-claim 数字：FActScore 逐条 F1 53–83%、AttributionBench 微调 GPT-3.5 约 80% macro-F1、MiniCheck 系 BAcc 74.7–77.4。**聚合级数字（FActScore ER<2%、AutoAIS Pearson 0.96）在本项目中没有使用价值，只能作为"为什么不能用聚合指标"的反面教材写进方法论。** 这条应写死成 lint 规则：任何引用了论文摘要级"error rate / correlation"的门禁设计，在 attacker 轮次直接判失败。

### D2. 门禁按 FPR 而不是 recall 调参；召回由"多机制并联 + 人审队列"补
HALLMARK 的结论直接可用：把 recall 从 0.87 推到 0.99 的代价是 FPR 从 0.09 涨到 0.47。本项目应采取三态而非二态输出——`verified` / `unverified` / `needs-human`——并把模型型机制的输出默认落进第三态，只有确定性机制（DOI 解析成功 + 字段全匹配 + 逐字引文命中）才允许直接落 `verified`。

### D3. 机制分层：一级确定性门禁，二级模型型过滤，三级人审
- **一级（可 re-run、可 diff、无模型）**：DOI 解析、Crossref/OpenAlex 字段比对、逐字引文规范化匹配、statcheck/GRIM 统计重算、URL 存档比对。这些天然满足"re-runnable objective gates"的要求——同一输入两次运行必须同一结果，可作为 keep-if-better 的裁决基准。
- **二级（模型型，需记录 model-id + 日期 + prompt hash）**：NLI 蕴含（M5）、MiniCheck 类小模型（M6）、LLM-judge（M11）。二级只能把 `needs-human` 收窄，不能把 `unverified` 翻成 `verified`。
- **三级**：人审队列。SAFE 的 20× 成本优势说明自动化值得做，但 VeriScore 的"仅 55% 被支持、40% inconclusive"说明人审队列不可能清零。

### D4. 分解走 keep-if-better，不做固定流水线环节
Decomposition Dilemmas 的"利弱不利强"意味着：分解与否应当是一个可 A/B 的开关，由同一批 gate 在同一批 claim 上跑两遍取胜者。这正好吃满 DSH 的原生并行——两条分支同时跑、按客观 gate 结果择优，而不是靠先验拍板。粒度上应向 molecular facts（去语境化但最小化）靠，而不是 FActScore 式的极端原子化（其主导错误正是过度分解）。

### D5. 三类 claim 的机制配比（明确标出第三类的空缺）
- **data-derived（数据推导类）**：覆盖最好。statcheck（96.2–99.9%）+ GRIM（纯算术）+ 本项目自己的 re-runnable 分析脚本。**这一类应当做到 100% 确定性**——凡是需要模型判断的数据结论，说明分析脚本没写完。
- **literature-cited（文献引用类）**：覆盖次好但分层明显。存在性（M1/M2/M16，确定性，可做到高精度）→ 引文忠实性（M4，确定性但工程脆）→ 语义支持性（M5/M6/M7，模型型，天花板约 75–80% BAcc）。**"这篇文献存在"和"这篇文献支持这句话"必须是两个独立字段，不能合并成一个 verified。**
- **logically-inferred（逻辑推断类）**：**最缺**。现成机制只有 M14（域外，F1 0.88 但只判 warrant 有无）与 M15（历史教训：77% 全是伪线索）。本项目必须自建，建议路径：(a) 强制把 warrant 显式写出来（Toulmin 的 claim / grounds / warrant / qualifier / rebuttal 五元组），(b) 对每个 warrant 派并行 subagent 做**反例搜索**（找一个满足 grounds 却不满足 claim 的实例），(c) 只有"反例搜索在给定预算内失败"才标 `verified-by-inference`，且必须记录搜索预算——这是把不可判定问题转成可 re-run 的有界搜索。这条是本项目相对文献的真正增量。

### D6. 取证管线的硬约束（本轮亲测得出）
- 禁止从二进制 PDF 直出数字。优先级：论文 HTML（arxiv.org/html/、ar5iv、aclanthology landing page）> 官方文档页 > 结构化 API（Europe PMC / Crossref REST，返回 JSON 可逐字校验）> PDF。
- 每个数字必须携带**逐字引用片段**与可复现的抓取 URL；无法给出逐字片段的数字自动降级为 `unverified`。
- 同一数字必须能从**两条不同抓取路径**复现（如 arxiv HTML + ACL Anthology），否则标注单路径来源。HALLMARK 的 PDF/HTML 分歧正是这条规则救回来的。

### D7. 假独立佐证的工程化防御
把"来源"归并到**上游标识**而非 URL：DOI / arXiv ID / 官方域名。三个博客转述同一篇论文 = 一个源。实现上要求每条 evidence 记录 `upstream_id`，credibility 聚合时按 `upstream_id` 去重后再计数。Crossref 那个 84.5% vs 96.3% 的例子说明：即便是同一机构的两篇官方博文，也可能是两个不同口径的实验，不能当作互相佐证。

### D8. 基准数字的时效与口径漂移必须编码进数据结构
LLM-AggreFact 的数据集数量在论文（10）、leaderboard（11）、后续论文（14）之间漂移；leaderboard 页面本身无更新日期。因此每条外部 benchmark 数字在本项目中都应存为 `{value, metric, sample_condition, comparator, source_url, fetched_at, source_date}`，并设置 staleness 提醒（建议引用幻觉率类数字 90 天、模型能力类数字 180 天）。

### D9. 不要把 LLM-judge 的自洽当可信度
"Reliability without Validity" 的 38.6 pp κ 缺口意味着：本项目若用多模型投票一致率作为 credibility 分数，会系统性高估。若必须用 judge，报告的必须是 chance-corrected 指标，且要在难样本子集上单独报告——test-retest 从 0.943 掉到 0.911 说明难度是主要退化轴。更稳妥的做法：judge 只用来做**分流**（决定送哪条确定性 gate），不用来做**裁定**。

### D10. 与"前代 claim-graph 框架失败"的对齐
本轮证据支持那个教训：文献里所有试图把验证做成通用图/框架的路线（AutoAIS、通用 decompose-then-verify）都在例级失效；而活下来的是**窄而确定性的重算工具**（statcheck、GRIM、DOI 解析、URL 存档比对），它们的共同点是"输入固定 → 输出固定 → 可 diff"。本项目的机制菜单应当按这个标准排序：**能写成脚本的绝不交给模型**。

---

## 未决与风险

**未决（需下一轮补）**
1. OpenAlex 与 Semantic Scholar 的官方速率限制、以及 `paper/search/match` 端点是否返回可用的 matchScore——两处官方文档页在本轮均因重定向或 JS 渲染取不到（`docs.openalex.org/...` 301 到 help 首页；`api.semanticscholar.org/api-docs/` 只返回导航壳）。这直接影响并行扇出的预算设计。
2. 逐字引文匹配（M4）没有任何公开的端到端精度测量，PDF 文本抽取保真度也无公开量化。这是本项目一级门禁里唯一"确定性但精度未知"的环节，建议自建小规模标注集自测。
3. Molecular Facts（M10）与 DnDScore 的具体数值未取到（arXiv HTML 版本号猜测失败，PDF 路径不可信）。
4. S2AND 的 B³ F1 90%（旧 78.4%）只见于二手转述，Semantic Scholar 官方 API 博文中未出现该数字，需要找到一手来源或删除。
5. OpenAlex "机构级召回 93%、24% 误检"同样只有二手来源。
6. statcheck 有效性论文只读到机构库登记的摘要，未读到全文中样本量（多少篇文章、多少条统计量）与那两项研究的具体设置差异——96.2% 与 99.9% 之间的 3.7 个点具体由什么假设造成，尚不明。
7. 本轮 WebSearch 预算在第 16 次搜索后耗尽（200/200，为会话级共享额度），部分方向（如 2026 年新出的科学声明验证系统、中文学术库的核验接口）未能覆盖。

**风险**
- **R1 时效**：M16 的所有引用幻觉率（13.3% / 3.5% / 10.7% 等）是 2026-04 的快照，模型版本迭代后会显著变化，且论文自己就展示了接入自纠工具后降到 <1%。任何写进设计文档的绝对值都必须带日期。
- **R2 leaderboard 漂移**：LLM-AggreFact 页面无更新时间戳，77.4 这个数字随时可能被顶替，且数据集集合本身在变。
- **R3 域外迁移**：Toulmin warrant 的 F1 0.88 来自教育对话语料，学术论证的 warrant 更长、更隐含、更依赖领域知识，直接迁移大概率大幅退化。这是 D5 中"必须自建"的主要依据。
- **R4 本轮方法论自身的残余风险**：表中标 `verified` 的数字里，有一批（Decomposition Dilemmas 的具体 BAcc、VeriScore 的 334/360 与 43.7%、HALLMARK 的各档 FPR）是通过 HTML 全文抓取 + 摘要模型转述得到的，我未逐字复核每一处表格单元。虽然 HTML 路径比 PDF 路径可信得多（PDF 路径已被证实会编造），但在把这些数字写进对外文档前，建议再走一次逐字引用复核。此处标注为"HTML 路径 verified，未做第二路径复现"。
- **R5 口径混用**：M2 那两行 Crossref 数字（F1 0.9629 vs 0.8448）最容易被后续引用者混成一个"Crossref 匹配准确率"。任何引用必须连带说明"真实脏数据"还是"合成 11 种格式"。
