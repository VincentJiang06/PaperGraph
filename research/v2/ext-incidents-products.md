# 外部调研 · 维度：真实事故与商业 deep-research 产品对照

> 调研日期：2026-08-17　|　方法：落笔即验证（每个载荷数字先取一手源，再记录口径三元组）
> 本文所有"截至"日期均为抓取当日实测，非引用他人转述。

---

## 结论摘要

**1. 事故不是轶事，是已经可以按年计数的产业现象。**
Damien Charlotin 的 AI Hallucination Cases 数据库在 2026-08-16 收录 **1922 起**法院/仲裁庭已认定或暗示当事人依赖幻觉材料的裁判，最新一条是 2026-08-13。更重要的是内部构成：**Pro Se Litigant（自诉当事人）1111 起，超过律师的 761 起** —— 这不是"律师偷懒"的故事，是"任何人拿 LLM 产出去承担后果"的故事，正好是本项目用户的画像。

**2. 前一轮被坑的那个数字，坑就在这里。**
Deloitte 澳洲事故里流传最广的说法是"退款 44 万澳元 / 29 万美元"。**都是错的。** A$440,000 是合同总额，US$290,000 是它的美元折算；实际退款是合同**最后一期款**，**A$97,000 出头（约 US$63,000）**，占合同额约 22%。本轮已改正并留痕。

**3. 引注污染的规模已经被一手审计量化。**
《柳叶刀》2026-05-07 的审计：在 PMC 开放获取子集 **250 万篇**生物医学论文的 **9,710 万条**已核验参考文献中，发现 **4,046 条**捏造引文，散布在 **2,810 篇**论文里；发生率从 2023 年的**每 2,828 篇 1 篇**升到 2026 年初的**每 277 篇 1 篇**，且 **98.4%** 的受影响论文在审计时点出版方未采取任何行动。

**4. 差异化的核心事实，一句话：这套核验机器已经被造出来了，但只被造成了"尺子"，没人把它做成"产品"。**
Perplexity 2026-07 开源的 WANDR 基准，其评分器会**重新抓取被引页面、检查摘录是否真的出现并支持该论断**；PwC 2026-05 的论文把引注质量拆成 Link Works / Relevant Content / Fact Check 三段。两者都是**离线评测装置**。而在**出货的产品**里 —— OpenAI、Gemini、Claude、Perplexity、Grok —— **没有任何一家给单条断言附核验状态**，全部止步于"挂个链接"。

**5. 而且行业自己的数据说明：只加并行度、不加核验，会让事情变糟。**
PwC 的测量：引注的"链接可达率"是 94–100%，但"事实核验通过率"只有 39–77%；且随着工具调用从 2 次扩到 150 次，**事实核验准确率平均下降约 42%**，GPT-5.4 从 79% 掉到 17%。**对一个"超并行"系统，这是直接的设计红线。**

**6. 撤稿检查是整个赛道的公开空白。**
JMIR 2026-05-01 的对照研究结论：**"没有任何一个现有的免费 GenAI 系统可以被认为在检测或处理撤稿文献上是可靠的。"** 最好的 ChatGPT 5 也只在 15 篇里全对 8 篇（53.3%），SciSpace / ScienceOS / Consensus **零篇全对**。而 Retraction Watch 数据库（截至 2026-08-15 **超过 66,000 条**撤稿）已被 Crossref 收购并可整库下载 —— **数据是免费的、机械的、可离线的，却没人接**。

---

## 逐条发现（含 URL）

### A. 专业服务机构：政府报告事故

#### A-1. Deloitte 澳大利亚 / DEWR（2025）—— 本轮重点纠偏对象

- **委托方**：澳大利亚 Department of Employment and Workplace Relations (DEWR)
- **标的**：Targeted Compliance Framework (TCF) Assurance Review，一份 **237 页**报告，2024-12 立项，7 个月工期，2025-07-04 发布
- **合同额**：**A$440,000**（AusTender 公示）
- **事故**：报告含不存在的学术文献引用（多次引用悉尼大学法学院真实教授 Lisa Burton Crawford 名下并不存在的论著）、以及一段**伪造的联邦法院判词引文**
- **AI 披露**：修订版新增披露，称使用了 "a generative AI large language model (Azure OpenAI GPT-4o) based tool chain licensed by DEWR and hosted on DEWR's Azure tenancy"
- **实际退款**：**A$97,000 以上（约 US$63,000）**，即合同**最后一期款**。DEWR 发言人证实，并称 AusTender 正在更新以反映该退款
- **口径陷阱实录**：搜索结果中同时存在 "Deloitte to Refund $440K"（Facebook/TechJuice）、"refunded $290,000"（Dailymotion）、"Deloitte refunded the Australian government $440K"（LinkedIn）三种错误说法，全部把**合同额**当成了**退款额**；Fortune 的标题 "$290,000 report" 则是合同额的美元折算，本身没错但极易被下游读成退款额
- URL：
  - https://www.cfodive.com/news/deloitte-refunds-60k-report-ai-errors-australian-government-accounting/803321/ （退款额一手转述：DEWR 发言人）
  - https://www.theguardian.com/australia-news/2025/oct/06/deloitte-to-pay-money-back-to-albanese-government-after-using-ai-in-440000-report
  - https://fortune.com/2025/10/07/deloitte-ai-australia-government-report-hallucinations-technology-290000-refund/
  - https://www.dewr.gov.au/assuring-integrity-targeted-compliance-framework/resources/targeted-compliance-framework-assurance-review-final-report （官方页面，本轮 403/超时未能抓取）

#### A-2. Deloitte 加拿大 / 纽芬兰与拉布拉多省（2025–2026）—— 更严重，且仍在进行

- **标的**：Health Human Resources Plan，**526 页**，省政府支付 **C$1.6 million**
- **事故**：2025-11 记者与学者发现虚假或无法追溯的引注，被用于支撑关于招聘策略、货币激励等的论断；报告发布时**未披露使用 AI**
- **省政府反应**：2025-11-22 起要求 Deloitte 复核整份报告
- **监管升级**：2025-11-28 有人向 **Chartered Professional Accountants Newfoundland and Labrador (CPANL)** 投诉；**2026-03-07 CPANL 正式立案调查**。其 Complaints Authorization Committee 有权暂停/限制执照、移交纪律小组或训诫
- **Deloitte 表态**：承认使用 AI "to support a small number of research citations"，但坚称错误 "do not impact the report findings"，且 "firmly stands behind the recommendations put forward"
- **退款**：截至 2026-03 无退款记录
- **对本项目的意义**：这一起证明了后果的**升级路径**——不是退钱了事，而是进入职业监管程序。Deloitte 的辩护"不影响结论"恰恰是本项目要用机器否定的说法：**引注不成立，结论就不能被称为有据。**
- URL：
  - https://theindependent.ca/news/lji/accounting-watchdog-to-investigate-deloitte-over-fake-citations-in-1-6-million-healthcare-report/
  - https://www.cbc.ca/news/canada/newfoundland-labrador/nl-deloitte-citations-9.6990216
  - https://fortune.com/2025/11/25/deloitte-caught-fabricated-ai-generated-research-million-dollar-report-canada-government/
  - https://oecd.ai/en/incidents/2025-11-26-f9ab

#### A-3. 美国 MAHA Report（2025-05）—— 政府旗舰报告

- **标的**："Make America Healthy Again" Commission 关于儿童慢性病的旗舰报告
- **事故**：NOTUS 2025-05-29 调查发现**至少 7 条引注指向并不存在的研究**（含关于青少年焦虑、直接面向消费者的药品广告、儿童哮喘处方药的虚构研究），另有失效链接与被曲解的结论。被列为作者的研究者向 AFP 等确认自己从未写过这些论文
- **官方回应**：白宫新闻秘书 Karoline Leavitt 称是 "formatting issues"；HHS 发言人 Andrew Nixon 称 "Minor citation and formatting errors have been corrected"。报告被静默更新替换引注
- **后续**：众议院监督委员会民主党 2025-06-02 致函 RFK Jr.，指报告"引用了不存在的科学研究、曲解了某些研究的结论，并可能使用了人工智能"
- **意义**：证明"改一改就好了"的处理方式如何把**核验缺失**降格为**格式问题**——这正是本项目要用不可否认的机器状态去对抗的话术
- URL：
  - https://www.notus.org/health-science/make-america-healthy-again-report-citation-errors
  - https://www.notus.org/health-science/maha-report-update-citations
  - https://www.reuters.com/business/healthcare-pharmaceuticals/trump-administration-report-us-child-health-cited-nonexistent-studies-media-2025-05-30/
  - https://oversightdemocrats.house.gov/download/letter-to-the-honorable-robert-f-kennedy-jr-secretary-u-s-department-of-health-and-human-services
  - https://www.science.org/content/article/trump-officials-downplay-fake-citations-high-profile-report-children-s-health

#### A-4. 法院制裁：金额务必分清

- **Mata v. Avianca, Inc.**（S.D.N.Y., 2023-06-22，Judge P. Kevin Castel）：**Rule 11 制裁 US$5,000**，对律师 Steven Schwartz、Peter LoDuca 及其事务所 Levidow, Levidow & Oberman **连带**科处。涉 6 个完全虚构的判例
- **Coomer v. Lindell**（D. Colo., 2025-07，Magistrate Judge Nina Wang）：一份书状含**近 30 处有缺陷的引注**（虚构判例、错引、误述）。**每名律师罚 US$3,000**，法官称这是 "the least severe sanction adequate to deter and punish"
  - **口径陷阱**：同一案件里的 **US$2.3 million 是陪审团判给 Coomer 的诽谤赔偿**，与 AI 制裁金无关。这两个数字极易被混为一谈
  - **升级**：2026-04-01 报道，联邦法官因**持续出现虚假引注**再度提议制裁 Lindell 的律师
- **Concord Music Group v. Anthropic**（N.D. Cal., 2025-05）：Anthropic 提交的专家声明含由 Claude 生成的错误引注；Anthropic 律师称错误源于用 Claude 做**引注格式化**，属 "honest citation mistake"。**意义**：连模型厂商自己的法务流程都栽在这上面
- URL：
  - https://law.justia.com/cases/federal/district-courts/new-york/nysdce/1:2022cv01461/575368/54/
  - https://www.reuters.com/legal/new-york-lawyers-sanctioned-using-fake-chatgpt-cases-legal-brief-2023-06-22/
  - https://www.npr.org/2025/07/10/nx-s1-5463512/ai-courts-lawyers-mypillow-fines
  - https://www.coloradopolitics.com/2026/04/01/federal-judge-proposes-sanctions-against-mike-lindells-lawyers-for-continued-fake-citations/
  - https://www.reuters.com/legal/litigation/anthropic-expert-accused-using-ai-fabricated-source-copyright-case-2025-05-13/
  - https://reason.com/volokh/2025/05/15/seemingly-nonexistent-citation-in-anthropic-experts-declaration/

---

### B. 系统性追踪器：它到底在数什么

#### B-1. AI Hallucination Cases Database（Damien Charlotin, HEC Paris）

一手抓取 https://www.damiencharlotin.com/hallucinations/ ，页面自述 **Last updated: 16 August 2026**。

- **总量**：**1922 cases identified so far**
- **收录标准（原文）**：只收录"法院或仲裁庭已明确认定（或暗示）当事人依赖了幻觉内容或材料"的裁判；**明确不收录**仅由当事人指控而未经司法认定的案件。作者自述："I am not making that judgment, I let the courts and judges make or imply it"
- **它不数什么（原文）**："It does not track the (necessarily wider) universe of all fake citations or use of AI in court filings" —— 即**它是所有 AI 造假的一个下界，不是全集**
- **作者自认低估**：数据库"necessarily an undercount"
- **按国家**：USA 1313 / Canada 211 / Australia 98 / UK 62 / Israel 55 / Brazil 41 / Italy 15 / France 13 / India 13 …（共 40 个法域）
- **按使用 AI 的一方**：**Pro Se Litigant 1111 / Lawyer 761 / Judge 28 / Expert 14 / Prosecutor 5 / Government Lawyer 3 / Paralegal 2 / Arbitrator 1**
- **按幻觉性质（可多选，故各项之和 > 总数）**：**Fabricated 1601 / Misrepresented 800 / False Quotes 519 / Outdated Advice 33**
- **按被幻觉的对象**：Case Law 1728 / Legal Norm 220 / Exhibits & Submissions 135 / Doctrinal Work 44 / Overturned Case Law 17 / Repealed Law 16
- **起始**：Q2 2023；作者在 FAQ 中称 2025-04 建库时约"每月两三起"，到 2026-02 已达"每天五起"量级
- **作者自建工具**：Charlotin 基于该库开发了自动引注核查器 **PelAIkan**
- **最新条目实例（2026-08-12/13）**：巴西圣保罗州法院对律师科处相当于诉讼标的 2% 的程序罚金并移送 OAB；加拿大新斯科舍上诉法院对一名自诉当事人科处 **C$20,000** 弥偿性讼费——其用 AI 生成的庭审笔录含 39 处不符，并附上了一名真实法庭笔录员的证书、姓名、注册号与签名，而该笔录员否认认证过

**给本项目的两个硬事实**：
1. **半数以上（1111/1922）是自诉当事人**，不是执业律师。护栏的目标用户不是"专业机构"，是"独自面对后果的个人"。
2. **Misrepresented 800 + False Quotes 519**：接近一半的案件里，被引来源是**真实存在**的，问题出在"它并不支持你说的那句话"。**只做 DOI 可解析性检查的方案，对这一类的召回接近 0。**

- URL：https://www.damiencharlotin.com/hallucinations/ ｜ FAQ：https://artificialauthority.ai/p/hallucinations-case-database-faq

---

### C. 学术文献污染的规模（一手审计）

#### C-1. 《柳叶刀》引注完整性审计（Topaz et al., 2026-05-07）

- **标题**：Fabricated citations: an audit across 2·5 million biomedical papers
- **主导**：Maxim Topaz，哥伦比亚大学护理学院 / Data Science Institute
- **语料口径（关键）**：**PubMed Central 的 Open Access 子集**，**2023-01-01 至 2026-02-18**，约 **250 万篇**论文
- **结果**：在 **9,710 万条已核验参考文献**中识别出 **4,046 条**捏造引文，分布于 **2,810 篇**论文
- **逐年发生率（每 N 篇论文含至少 1 条捏造引文）**：2023 年 **1/2,828** → 2025 年 **1/458** → 2026 年初 **1/277**；自 2023 年增长**超过 12 倍**，2024 年中出现明显拐点，与 AI 写作工具普及期高度吻合
- **出版方无作为**：**98.4%** 的受影响论文在审计时点未见任何出版方处置
- **作者原话（Topaz）**："A medical professional or clinical guideline developer has no way of knowing that the evidence they are relying on does not exist."
- **方法学批评**：Cochrane 的 Ella Flemyng 指出该 AI 检测方法"仅在 500 条记录上验证过，方法细节披露不足"
- **一处二手数字冲突（已纠正）**：Retraction Watch 的报道写作 "**4,406**"，且把语料表述为 "papers indexed in PubMed"。作者所属机构新闻稿、EurekAlert、phys.org、CIDRAP、The Scientist 一致为 **4,046**，语料为 **PMC Open Access 子集**。以 **4,046 / PMC OA** 为准
- URL：
  - https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(26)00603-3/fulltext （403，未直取）
  - https://www.nursing.columbia.edu/news/nearly-3-000-peer-reviewed-medical-papers-have-fake-citations-columbia-nursing-ai-assisted-audit-finds （作者所属机构新闻稿）
  - https://retractionwatch.com/2026/05/07/one-in-277-pubmed-indexed-papers-in-2026-shows-fabricated-references-says-analysis/
  - https://www.eurekalert.org/news-releases/1127364

#### C-2. 预印本平台的更大规模审计（2026-06，经中文源转述）

arXiv 上发布的一项对 **250 万篇论文、1.11 亿条参考文献**的系统性审核称：**仅 2025 一年**，在 arXiv、bioRxiv、SSRN、PubMed Central 中就存在**近 15 万条**由 AI 编造的虚假参考文献；且虚假文献**分散在大量不同论文中**，每篇问题论文通常只含少量虚假条目——意味着这不是少数造假者，而是"用 AI 辅助写作但不做事实核查"的**普遍行为模式**。

> **状态：unverified。** 本轮仅通过《中国社会科学报》经新浪转载的中文报道获得，未取得该 arXiv 预印本编号与原文。且其"250 万篇"与 C-1 的"250 万篇"数值巧合但语料不同（预印本平台 vs PMC OA），存在被下游混淆的高风险。**引用前必须补一手。**
- URL：https://k.sina.com.cn/article_2201275590_8334ccc600101fvgu.html

#### C-3. Retraction Watch 数据库现状（一手）

抓取 https://retractionwatch.com/ 首页（最新文章日期 2026-08-15），原文：
> "The Retraction Watch Database has over 66,000 retractions. Our list of COVID-19 retractions is up to 650, and our mass resignations list has more than 50 entries."

数据库已由 **Crossref 收购**并提供整库下载（https://retractiondatabase.org/ ），每工作日更新。**这意味着撤稿核查在工程上是一次离线数据集 join，不是一次模型调用。**

---

### D. 商业 deep-research 产品对照（核心交付）

#### D-1. 对照表

| 产品 | 澄清提问 | 计划审批/编辑 | 中途干预 | **每条断言的核验状态** | **撤稿检查** | 一手依据 |
|---|---|---|---|---|---|---|
| **OpenAI Deep Research**（ChatGPT 产品端） | **有** | **有**（可 review & edit） | 未文档化 | **无** | **无** | help.openai.com 10500283（Cloudflare 拦截，仅 Google 索引摘要） |
| **OpenAI Deep Research API** | **无**（文档明言模型 "expects fully-formed prompts up front and will not ask for additional context"，建议开发者自建澄清层，如用 gpt-5.6 先问） | 无 | 无 | **无** —— annotation 仅含 url / title / start_index / end_index | **无** | developers.openai.com/api/docs/guides/deep-research |
| **Gemini Deep Research**（App） | — | **有**（"Users can also correct the plan presented by Gemini"） | 计划阶段可多轮 | **无** | **无** | gemini.google/overview/deep-research/ |
| **Gemini Deep Research Agent API** | — | **有，且是显式 API 参数**：`collaborative_planning: True` → 返回计划；用 `previous_interaction_id` 多轮改计划；置 `False` 即批准并开跑 | 计划阶段可多轮 | **无** | **无** | ai.google.dev/gemini-api/docs/deep-research |
| **Claude Research** | **无**（"Claude will kick off the research process"） | **无** | 可用自然语言引导（"Claude, please use the research tool to…"） | **无** —— CitationAgent 做的是**归位（attribution）**："identify specific locations for citations"，不是判断来源是否支持该论断 | **无** | support.claude.com/en/articles/11088861（2026-06-02）+ anthropic.com/engineering/multi-agent-research-system |
| **Perplexity Deep Research** | 未文档化 | 未文档化 | 未文档化 | **无** —— 官方表述是 "Every factual claim in Deep Research carries an inline citation"，即**每条断言都挂链接**，与"每条断言都被核验"是两件事 | **无** | perplexity.ai/hub/blog/deep-research-now-in-computer（2026-06-11，403，Google 索引摘要） |
| **Grok DeepSearch** | 未文档化 | 未文档化 | 未文档化 | **无** —— 发布公告通篇未提引注机制或核验机制，只提 "final summary trace" | **无** | x.ai/news/grok-3 |
| *（对照）* **scite** | — | — | — | **部分，但口径不同**：Smart Citations 判定的是"**后续文献**如何引用**某篇文献**"（supporting / contrasting / mentioning），不是"**你写的这句话**是否被**你引的这一篇**支持" | **有**（Collections "flag retractions"） | scite.ai（一手抓取）、scite.ai/features |

#### D-2. 各家架构要点（一手）

- **Claude Research**：orchestrator-worker 模式，lead agent 分派并行 subagent（"3-5 subagents in parallel" 为典型值）。官方数字：**多智能体系统 token 用量约为 chat 的 15×**（agent 约 4×）；**"A multi-agent system with Claude Opus 4 as the lead agent and Claude Sonnet 4 subagents outperformed single-agent Claude Opus 4 by 90.2% on our internal research eval."**（内部评测，非公开基准）。评测采用 LLM judge + 人工，rubric 覆盖 factual accuracy / citation accuracy / completeness / source quality / tool efficiency —— **注意：这些是研发期的评测维度，不是出货给用户的每条断言状态。**
- **Gemini Deep Research API**：模型 `deep-research-preview-04-2026` 与 `deep-research-max-preview-04-2026`；文档给出**每任务成本估算**（非挂牌价）：标准档 **"$1.00 – $3.00 per task"**，Max 档 **"$3.00 – $7.00 per task"**，依据是每任务约 80–160 次搜索、250k–900k input tokens、60k–80k output tokens
- **OpenAI Deep Research**：模型 `o3-deep-research`、`o4-mini-deep-research`，走 Responses API；输出为含内联引注的 message，annotation 带字符区间（start_index / end_index），文档要求 UI 把内联引注做成 "clearly visible and clickable"

#### D-3. 关键不对称 —— 差异化的立论基础

**核验机器已经被造出来了，但都被造成了"尺子"，没有一家把它做成"产品面"。**

- **Perplexity WANDR**（2026-07-14 开源，Apache 2.0）：500 个证据密集任务、**170,495 条**须有出处的记录。其评分方式是 **reference-free** 的：评分器"**在评测时重新抓取该页面。检查页面是否可用且在范围内。然后核验那些摘录是否真的出现并支持每一项要求。**" —— **这正是本项目要做的事，而 Perplexity 把它放在了评测器里，没放进产品里。**
  - 榜单（soft F1 / hard F1）：Perplexity Search as Code **0.363 / 0.133**（$5.20/task、中位 14.9 分钟、3.82M tokens/task）；Anthropic **0.249 / 0.072**；其余最佳 **0.121 / 0.035**
  - **hard F1 最高 0.133 意味着：当前最强系统里，只有约 13% 的记录能做到整棵子树全对。**
- **PwC《Cited but Not Verified》**（arXiv:2605.06635v1，2026-05-07，Onweller / Lumer / Huber / Ramchandani / Subbiah / Feld）：把引注质量拆成三段——**Link Works**（HTTP 可达，二值）、**Relevant Content**（主题相关，LLM-as-judge）、**Fact Check**（该具体事实论断是否被来源内容准确支持）。在 130 个来自 DeepResearch Bench 与 BrowseComp 的查询上评测 14 个模型：
  - **Link Works 94–100%，Fact Check 仅 39–77%** ——"表层引注质量与事实可靠性之间存在关键断裂"
  - **随搜索深度从 2 次工具调用扩到 150 次，Fact Check 准确率平均下降约 42%**；GPT-5.4 最陡，**从 79% 掉到 17%**
- **ACL 2026《Beyond Single-shot Writing: Deep Research Agents are Unreliable at Multi-turn Report Revision》**（Chen / Li / Nie / Zhang / Ye / Zhao）：5 个 DRA 在多轮修订中，虽能处理大部分反馈，但**在此前已覆盖的内容与引注质量上回退 16–27%**，且"无法通过 prompt engineering 或专设修订子智能体等推理期手段轻易解决"

#### D-4. 撤稿：全赛道空白（一手研究）

**《Performance of AI Tools in Citing Retracted Literature: A Content Analysis》**，Labenbacher / Niederer / Hammer / Bader 等，格拉茨医科大学，*J Med Internet Res* 2026;28:e88766，**2026-05-01**。

- **样本口径**：15 篇撤稿论文（截至 2025-05-23 的 10 篇被引最多 + 5 篇最近撤稿），每个工具问 5 个标准化问题、各问 2 遍 = **675 个 prompt**
- **受测**：9 个免费 GenAI 系统（ChatGPT 4、ChatGPT 5、Claude、Gemini、Perplexity、Microsoft Copilot、SciSpace、ScienceOS、Consensus），OpenEvidence 单列
- **结果**：最好的 ChatGPT 5 也只在 **15 篇中全对 8 篇（53.3%）**；**SciSpace、ScienceOS、Consensus 零篇产出完全正确的响应集**；SciSpace 在主题综述中错误率最高（8/15，53.34%）；Consensus 一致性最差（两次作答不一致 19 处，25.33%）
- **结论原文**："No currently available free-access GenAI system can be considered reliable for detecting or handling retracted literature."
- URL：https://www.jmir.org/2026/1/e88766 ｜ https://pmc.ncbi.nlm.nih.gov/articles/13134821

#### D-5. 现成引注核查器的可用性 —— 精确率是致命伤

**《Detecting Hallucinated and Suspicious Citations: What Current Tools Can and Cannot Do》**，Badalova & Mayr，arXiv:2607.22693v2，**2026-07-28**。在 **104 条人工核验的参考文献（71 条合法 / 33 条有问题）**上测 5 个现成工具：

| 工具 | TP | TN | FP | FN |
|---|---|---|---|---|
| RefChecker | 32 | 35 | **36** | 1 |
| CheckIfExist | 31 | 37 | **34** | 2 |
| Hallucinator | 29 | 43 | **28** | 4 |
| HalluCiteChecker | 18 | 51 | 20 | 15 |
| HalRef | 24 | 18 | **53** | 9 |

**RefChecker 在 71 条合法引注中误报了 36 条——超过一半。** 作者结论："their performance was not sufficiently reliable to support definitive decisions without further verification"。

---

### E. 中文语境（与用户"写中文课程论文"直接相关）

- **《中华人民共和国学位法》**（2024-04-26 通过）**第三十七条**：学位论文或实践成果被认定存在**代写、剽窃、伪造**等学术不端行为，经学位评定委员会决议，**不授予学位或撤销学位**
- **高校 AIGC 检测已常态化**：东莞理工大学教务部对 2025 届（2025-03-24 通知）与 **2026 届（2026-03-25 通知）**本科毕业设计（论文）全文（含正文、摘要）开展 AIGC 检测，结果作为成绩评定与校优评选参考；桂林电子科技大学 2025 秋季学期起对研究生学位论文试用 AIGC 检测；南京晓庄学院 2025 届起开展 AIGC 检测
- **院系级用量红线**：华东师范大学传播学院与北京师范大学新闻传播学院 2024 年夏联合发布《生成式人工智能（AIGC）学生使用指南》，称**直接生成内容不得超过全文的 20%** —— **口径注意：这是两个学院的联合指南，不是教育部规定，也不是全校规定，不可外推**
- **复旦大学 2024-11 "六个禁止"**：被舆论称为"全球最严 AI 新规"，其中"禁止使用 AI 工具进行语言润色和翻译"引发争议
- **中文侧已有商业化引注真实性检测**：艾思科蓝 2026-06-05 上线 "AiScholar 参考文献真实性检测"，明确以《柳叶刀》审计为宣传依据
- URL：https://jwb.dgut.edu.cn/info/1111/30691.htm ｜ https://finance.sina.cn/tech/2025-03-22/detail-ineqpvce1610911.d.html ｜ https://m.ais.cn/news/headline/40872

**推论**：中国高校的治理重心在**"AI 率"（生成比例）**，而《学位法》的可撤销事由是**"伪造"**。这两者之间有一道缝：一篇 AI 率很低但引注是编的论文，AIGC 检测抓不到，却正踩在《学位法》第三十七条上。**本项目的证据附录恰好补的是这道缝——它证明的不是"我没用 AI"，而是"我说的每句话都能被查证"。**

---

## 载荷数字核验表

| 数字 | 口径三元组（什么指标 / 在什么样本或档位上 / 与什么相比） | 状态 | 一手出处 |
|---|---|---|---|
| **1922** | 累计收录案件数 / 全球 40 个法域中，法院或仲裁庭已明示或暗示认定当事人依赖幻觉材料的裁判文书 / 截至页面自述 2026-08-16 | **verified** | damiencharlotin.com/hallucinations/ （本轮直接抓取 HTML） |
| USA 1313 / Canada 211 / Australia 98 / UK 62 | 同库按法域分布 / 同上 / — | **verified** | 同上 |
| **Pro Se Litigant 1111 / Lawyer 761** | 同库按"使用 AI 的一方"身份分布 / 同上 / 自诉当事人 > 执业律师 | **verified** | 同上 |
| Fabricated 1601 / Misrepresented 800 / False Quotes 519 | 同库按幻觉性质，**可多选故总和 > 1922** / 同上 / — | **verified** | 同上 |
| **A$440,000** | Deloitte 澳洲—DEWR **合同总额** / TCF Assurance Review，7 个月、237 页 / **≠ 退款额** | **verified** | AusTender 公示，经 Guardian / AFR / CFO Dive 一致转述 |
| **A$97,000+（约 US$63,000）** | Deloitte 澳洲**实际退款额** = 合同最后一期款 / DEWR 发言人 2025-10 表述 / 约占合同额 22% | **corrected**（前轮误把合同额当退款额） | DEWR 发言人，经 CFO Dive / AP 转述；DEWR 官网 403 未直取 |
| ~~"退款 A$440,000 / US$290,000"~~ | — | **驳斥**：均为合同额（及其美元折算）被误读为退款额 | Facebook/TechJuice、Dailymotion、多条 LinkedIn |
| 237 页 | Deloitte 澳洲报告页数 / — / — | **verified** | Fortune, 2025-10-07 |
| **C$1.6 million** | Deloitte 加拿大—纽芬兰与拉布拉多省 **合同额** / 526 页 Health Human Resources Plan / 截至 2026-03 **无退款** | **verified** | CBC / The Independent（LJI） |
| 2026-03-07 | CPANL 正式立案调查 Deloitte 之日 / 投诉受理日 2025-11-28 / — | **verified** | theindependent.ca |
| **US$5,000** | Mata v. Avianca **Rule 11 制裁总额** / 对 2 名律师及事务所**连带**科处 / 涉 6 个虚构判例 | **verified** | Justia 判决文书 Doc 54，2023-06-22 |
| **US$3,000 / 人** | Coomer v. Lindell 制裁 / 每名律师 / 涉近 30 处有缺陷引注 | **verified** | NPR, 2025-07-10；Judge Nina Wang 令 |
| ~~US$2.3M~~ | Coomer 案**诽谤判赔额** / 陪审团判给 Coomer / **与 AI 制裁金无关** | **驳斥（口径陷阱）** | Colorado Politics, 2026-04-01 |
| **4,046** | 捏造参考文献**条数** / PMC **Open Access 子集** 250 万篇论文的 9,710 万条已核验引注中，2023-01-01 至 2026-02-18 / 分布于 2,810 篇论文 | **verified** | Topaz et al., *The Lancet*, 2026-05-07；哥大护理学院新闻稿 |
| ~~4,406 / "papers indexed in PubMed"~~ | — | **corrected**：数字疑为转写错误；语料应为 PMC OA 子集而非全 PubMed | Retraction Watch, 2026-05-07（两处口径均偏） |
| 1/2,828 → 1/458 → 1/277 | 含≥1 条捏造引文的论文占比 / 2023 / 2025 / 2026 年初（截至 02-18 的部分年度） | **verified** | 同上 |
| 98.4% | 受影响论文中出版方**未采取任何行动**的比例 / 审计时点 / — | **verified** | 哥大护理学院新闻稿 |
| **66,000+** | Retraction Watch 数据库撤稿总数 / 网站首页自述 / 另 COVID-19 撤稿 650、集体请辞名单 50+ | **verified** | retractionwatch.com 首页（最新文章 2026-08-15，本轮直取） |
| **94–100% vs 39–77%** | Link Works（HTTP 可达率）vs Fact Check（论断被来源支持率）/ 14 个前沿模型、130 个 DeepResearch Bench + BrowseComp 查询 / 同一批引注上的两个指标 | **verified** | PwC, arXiv:2605.06635v1, 2026-05-07 |
| **~42% 平均下降** | Fact Check 准确率的下降幅度 / 工具调用数从 2 扩到 150 / 同一模型内的纵向比较 | **verified** | 同上 |
| 79% → 17% | GPT-5.4 的 Fact Check 准确率 / 同上深度扩展 / 全场最陡 | **verified** | 同上 |
| **0.363 soft F1 / 0.133 hard F1** | WANDR 榜首（Perplexity Search as Code）/ 500 个任务、170,495 条须有出处的记录、评分器**重抓页面并核验摘录** / Anthropic 0.249/0.072，其余最佳 0.121/0.035 | **verified**（二手） | marktechpost 2026-07-19；一手 research.perplexity.ai 本轮 403/连接失败 |
| $5.20/task、14.9 min 中位、3.82M tokens/task | WANDR 榜首的成本画像 / 同上 500 任务 / — | **verified**（二手，同上） | 同上 |
| **16–27%** | 多轮修订中在**此前已覆盖内容与引注质量**上的回退比例 / 5 个 DRA、Mr Dre 评测套件 / — | **verified** | Chen et al., ACL 2026 long.609 |
| **53.3%（8/15）** | 撤稿文献处理**完全正确**的论文数占比 / ChatGPT 5，15 篇撤稿论文 × 5 问 × 2 次（全体 675 prompts、9 个免费系统）/ 全场最佳 | **verified** | *JMIR* 2026;28:e88766, 2026-05-01 |
| **0** | 完全正确响应集数 / SciSpace、ScienceOS、Consensus / 同上样本 | **verified** | 同上 |
| RefChecker FP=36 / TN=35 | 误报数 / 104 条人工核验引注中的 71 条**合法**引注 / 即合法引注误报率 > 50% | **verified** | Badalova & Mayr, arXiv:2607.22693v2, 2026-07-28 |
| **$1–3 / $3–7 per task** | Gemini Deep Research / Deep Research Max 的**每任务成本估算** / 基于每任务 80–160 次搜索、250k–900k input tokens 的推算 / **非挂牌价（not list price）、非促销价，是官方文档给的估算区间** | **flagged（估算值，非定价表）** | ai.google.dev/gemini-api/docs/deep-research |
| `deep-research-preview-04-2026` / `deep-research-max-preview-04-2026` | Gemini Deep Research 模型 ID / **均带 preview 后缀，随时可变** / — | **verified，但易失效** | 同上 |
| `o3-deep-research` / `o4-mini-deep-research` | OpenAI Deep Research 模型 ID / Responses API / — | **verified** | developers.openai.com/api/docs/guides/deep-research |
| **90.2%** | 多智能体相对单智能体 Opus 4 的提升 / **Anthropic 内部研究评测（internal research eval）**，非公开基准 / — | **flagged（内部评测，不可跨系统比较）** | anthropic.com/engineering/multi-agent-research-system |
| 15× / 4× | token 用量倍数 / 多智能体系统 vs chat；agent vs chat / — | **verified** | 同上 |
| 26.6% | Humanity's Last Exam 准确率 / 3000+ 题，OpenAI deep research，**2025-02 发布时** / — | **verified 但已过时**，2026-08 不可用作现状 | openai.com/index/introducing-deep-research/（403，经 Fortune / HN 一致转述） |
| 280M+ / 300M+ | scite "全文学术文献" vs "文章+预印本+书+专利+数据集"总量 / **同一页面两个不同口径** / — | **flagged（同页异口径，引用须注明是哪一个）** | scite.ai 首页（本轮直取） |
| 20% | "直接生成内容"占全文上限 / **华东师大传播学院 + 北师大新闻传播学院**联合《AIGC 学生使用指南》，2024 夏 / **非教育部规定、非全校规定** | **flagged（院系级，不可外推）** | 新浪财经 2025-03-22 转述 |
| ~15 万条 / 2025 年 | AI 编造的虚假参考文献数 / arXiv + bioRxiv + SSRN + PMC，250 万篇论文 1.11 亿条引注的审核 / — | **unverified** —— 仅得中文二手转述，未取得原始预印本编号 | k.sina.com.cn（《中国社会科学报》） |
| "每条事实性断言都带行内引用" | Perplexity Deep Research 的引注承诺 / 产品文案 / **= 挂链接，≠ 核验** | **verified（措辞），但须防口径误读** | perplexity.ai/hub/blog/deep-research-now-in-computer, 2026-06-11（403，Google 索引摘要） |

**关于"虚假独立佐证"的处理**：Deloitte 澳洲退款额、《柳叶刀》4,046 两处，本轮出现的大量网页（Yahoo / malaymail / worldcompliance / glassalmanac / newsbytes 等数十条）实际全部回溯到**单一上游**（前者为 DEWR 发言人经 AP、后者为哥大新闻稿经 EurekAlert）。**已按"多页面重复 = 一个来源"计。** 真正起到独立作用的只有：CFO Dive（独立向 DEWR 求证并给出精确数额）与作者机构新闻稿（一手）。

---

## 对本项目的设计含义

### 1. 差异化陈述（可直接写进 README 首屏）

> **市面上所有 deep research 产品交付的是"带链接的报告"；本项目交付的是"带判决的报告"。**
>
> OpenAI、Gemini、Claude、Perplexity、Grok 全都在每条断言后面挂来源链接，但**没有任何一家告诉你这条链接是否真的支持这句话**。判别机器已经存在——Perplexity 自己的 WANDR 评分器会重抓被引页面、核对摘录是否真的出现并支持论断；PwC 把它拆成 Link Works / Relevant Content / Fact Check 三段——但**这些都被造成了实验室里的尺子，没有一把交到用户手上**。
>
> 我们做的就是把这把尺子从评测台搬到交付物上：**每条载荷断言携带一个机器判定的状态（verified / corrected / unverified / contested），以及支撑它的可复跑数据分析、可回溯到原文段落的论文结果，或可检查的逻辑推演。**
>
> 外加一件全行业都没做的事：**撤稿检查**。JMIR 2026 的测量是，最好的免费 GenAI 系统在撤稿文献上的完全正确率只有 53.3%，三个学术专用工具是 0。而 Retraction Watch 的 66,000+ 条撤稿数据由 Crossref 免费整库分发——这是一次离线 join，不是一次模型调用。

### 2. HITL 检查点建议（基于行业收敛点，而非拍脑袋）

**行业收敛到的唯一一个检查点是：开跑前的计划审批。** OpenAI 产品端做（澄清提问 + 可编辑计划），Gemini 两端都做（App 可改计划，API 直接把它做成 `collaborative_planning` 布尔量的三阶段协议）。Claude、Perplexity、Grok 一个都没有。**没有任何一家有跑完之后的裁决检查点。**

据此建议 **2 个强制 + 1 个条件**：

- **CP-0（条件触发）· 澄清提问**：仅在问题欠定义时触发。注意 OpenAI 的做法拆开看很有启发——**API 侧模型明确"不会主动要上下文"，澄清层是产品侧另建的**。所以这一层应由我们自己实现为独立前置步骤，而不是指望模型自觉。DeepSeek v4-flash 承担此层成本可忽略。
- **CP-1（强制）· 研究计划审批**：完全对齐行业收敛点，用户预期已被 OpenAI / Gemini 教育好，零学习成本。计划须包含：子问题分解、每个子问题的证据类型（数据分析 / 论文结果 / 逻辑推演）、以及**预期的不可验证区**。
- **CP-2（强制，行业空白 = 我们的产品面）· 争议裁决**：跑完后**只把"机器判不了"的那一桶**交给人。

**CP-2 必须窄，这是被数据强制的**：Badalova & Mayr 的测量显示 RefChecker 在 71 条合法引注上误报 36 条。**如果把检查器报警的东西全推给人，人会被淹死，然后开始无脑点通过——检查点就退化成了橡皮图章。** 因此三分流：机器判定成立 → 自动过；机器判定确凿不成立（DOI 不可解析 / 页面 404 / 引文原文不存在）→ 自动打回并重跑；**只有真正歧义的进 CP-2**。自动打回的阈值要按**精确率**调，不按召回率调。

### 3. 状态机不能是三态，必须是"存在性 × 支持性"二维

Charlotin 数据库里 **Fabricated 1601、但 Misrepresented 800 + False Quotes 519**——接近一半的司法认定案件中，**来源是真实存在的，错在"它不支持你那句话"**。同理，PwC 的 Link Works 94–100% 对 Fact Check 39–77% 就是这道裂缝的量化。

**一个只做"DOI 能不能解析"的核验器，对这一整类的召回接近 0，却会给出令人安心的绿色。这比不做更危险。**

建议最小状态集：

| 状态 | 含义 | 判定方式 |
|---|---|---|
| `verified` | 来源存在 **且** 原文段落支持该断言 | 重抓 + 定位到具体句子 + 语义蕴含判定 |
| `corrected` | 初判不成立，改写断言后成立 | 记录改写前后与改写理由 |
| `unverified` | 来源存在但**未能确认支持**，或来源不可达 | 落到 CP-2 或明确标注 |
| `contested` | 来源支持，但存在**反向证据 / 已撤稿 / 已被后续文献推翻** | 撤稿库 join + 反向检索 |

`contested` 这一态是撤稿检查和"寻求反证"的落点，也是最难被竞品追平的一格。

### 4. 超并行必须与核验解耦 —— 这是本项目最大的自伤风险

PwC 的测量是**反直觉且直接冲着我们来的**：**工具调用从 2 次扩到 150 次，事实核验准确率平均掉约 42%，GPT-5.4 从 79% 掉到 17%。**

一个"hyper-parallel、multi-loop"的系统如果把核验当成搜索循环的延伸，**并行度越高，产出越不可靠**——我们会亲手把自己的卖点做成缺陷。

工程约束：

- **核验必须是一趟独立的 pass，由对起草过程无记忆的新鲜 agent 执行**，输入只有"断言 + 声称的来源"，看不到起草时的推理链（否则会被起草时的自洽性说服）。
- **核验深度固定，与检索深度无关**。检索可以扇出到几十路；核验对每条断言的动作是定长的（重抓 → 定位 → 判定 → 记录）。
- **核验器的模型选择独立于起草器**，最好换厂商或至少换档位，买独立性。这与 house 方法论里 attacker 用不同厂商买独立性是同一条原理。
- 参考成本锚：WANDR 榜首 **$5.20/task、3.82M tokens/task**。这正是 DeepSeek 定价能吃下的地方——但**本轮未核验 DeepSeek 现价，属另一维度，不得在此推算**。

### 5. 核验状态必须持久化到断言级，并在每次改稿后重跑

ACL 2026 的测量：多轮修订中，DRA 在**此前已覆盖内容与引注质量上回退 16–27%**，且 prompt 工程与专设修订子 agent 都救不了。

含义很直接：**一条曾经 `verified` 的断言，会在改稿时被悄悄改坏，而报告级的"已核验"图章不会掉。** 所以：

- 核验状态存在**断言级**，不是报告级；
- 每条断言存**内容哈希**，文本一变状态即失效回落到 `unverified`，必须重跑；
- 交付物里给出**状态直方图**（verified / corrected / unverified / contested 各多少条），让退化可见。

### 6. 撤稿检查是投入产出比最高的差异化点

它同时满足三个条件：**全赛道空白**（JMIR 2026 已实证）、**数据免费且机械**（Crossref 分发 Retraction Watch 全库，66,000+ 条，每工作日更新）、**工程量极小**（DOI 集合的一次 join，不需要模型）。

建议做成硬门禁：**任何引用命中撤稿库的断言，一律强制降级为 `contested` 并推 CP-2，不允许自动过。**

### 7. 中文交付物需要一份"可辩护的证据附录"

《学位法》第三十七条的可撤销事由是**代写、剽窃、伪造**；而高校的 AIGC 检测抓的是**生成比例**。**一篇 AI 率合格但引注是编的论文，检测抓不到，却正踩在第三十七条上。**

因此中文交付物应默认附带一份证据附录：每条载荷断言 → 状态 → 来源 → 原文定位（页/段/句）→ 若为数据结论则附可复跑脚本与哈希。**它证明的不是"我没用 AI"，而是"我说的每句话都能当场被查证"**——这恰好是 AIGC 检测覆盖不到、而学位委员会真正在意的那一面。

### 8. 动机弹药（用于 README / 立项陈述的开场）

按"离用户有多近"排序，而不是按机构大小：

1. **1922 起司法认定案件中，1111 起是自诉当事人**——不是大所律师，是自己扛后果的个人。
2. **加拿大那起的走向**：不是退钱了事，而是 2026-03-07 进入省注册会计师协会的**职业纪律调查**；Deloitte 的辩解是"错误不影响结论"——**这正是本项目用机器状态要否定的那句话。**
3. **每 277 篇生物医学论文就有 1 篇含捏造引文，且 98.4% 的受影响论文出版方至今零动作**——上游不会替你把关。
4. **最强的 deep research 系统 hard F1 只有 0.133**——不是"AI 差不多够用了"，是"最好的也只有约 13% 的记录整棵子树全对"。
5. **搜得越深，核验越差（平均 -42%）**——所以"更强的搜索"不是解，"独立的核验"才是。

---

## 未决与风险

### 一手源未能直取（已在核验表标注状态）

| 目标 | 障碍 | 当前依赖 | 建议后续动作 |
|---|---|---|---|
| DEWR 官方页面 / AusTender 原始合同记录 | 403 + 超时 | DEWR 发言人经 CFO Dive / AP 转述 | 用浏览器工具（Claude-in-Chrome）直取 AusTender CN 记录，锁定合同号与退款后金额 |
| openai.com 全站 + help.openai.com | Cloudflare 全局拦截（WebFetch 与 curl 均 403） | Google 索引摘要 | OpenAI Deep Research 的"澄清提问 + 可编辑计划"目前**仅有摘要级证据**，写进对照表前建议实机截图 |
| perplexity.ai/hub 与 research.perplexity.ai | 403 / 连接失败 | marktechpost 转述 + Google 索引摘要 | WANDR 已 Apache 2.0 开源，**直接读仓库里的 grader 代码**比读博客更硬，且能拿到 soft/hard F1 的精确定义 |
| thelancet.com 原文 | 403 | 作者机构新闻稿（一手性高） | 若要引用方法学细节，须取全文；Flemyng 的批评正是针对方法披露不足 |
| ACL 2026 long.609 PDF | PDF 解析失败 | ACL Anthology 摘要页（含完整 abstract） | 16–27% 这个数已在 abstract 里，够用；若要拆解到每个 DRA 需读正文 |

### 方法学与时效风险

- **Charlotin 数据库是下界不是全集**：作者自述 "necessarily an undercount"，且只收录**已进入司法认定**的案件。用它论证"规模"是稳的，用它论证"总量"是错的。另注意 Nature 分类**可多选**，各项之和（1601+800+519+33）远大于 1922，**不可相加**。
- **《柳叶刀》审计的检测方法披露不足**：Cochrane 的 Ella Flemyng 指其 AI 方法"仅在 500 条记录上验证过"。4,046 这个数应表述为"该方法识别出"，而非"确实存在"。
- **2025 年初的基准数字已死**：26.6% HLE 等发布期数字在 2026-08 无参考价值，**不得用作现状描述**。
- **模型 ID 全部带 preview**：`deep-research-preview-04-2026` 等随时可变，写进设计文档须标注抓取日期。
- **Gemini 每任务成本是估算区间不是价目表**：$1–3 / $3–7 来自官方文档基于 token 用量的推算。**本轮未发现任何一家 deep research 产品的促销价/引导价与列表价之争**，但 Gemini 这组数字属于"官方给的估算"这一第三类，**引用时必须写明它既不是挂牌价也不是促销价**。
- **C-2（15 万条虚假引注）仅有中文二手**：与 C-1 的"250 万篇"数值巧合但语料完全不同，**极易被下游合并成一个错误陈述**。引用前必须补原始预印本，否则弃用。
- **DeepSeek 定价本轮完全未核验**：属另一维度。第 4 条设计含义里的成本论证只到"WANDR 榜首 $5.20/task"为止，**不得据此推算我方成本优势倍数**。
- **serper.dev / bocha 的配额与价格本轮未核验**：本轮 WebSearch 在第 2 次调用即耗尽会话配额（200/200，疑与同会话其他 subagent 共享），全程改用 serper 脚本 + curl 兜底。**这本身是一条运行时风险：并行 subagent 会互相抢搜索配额。** 超并行设计必须把搜索配额当作显式预算来分配，而不是假定无限。
