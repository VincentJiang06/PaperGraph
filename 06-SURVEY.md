# 06-SURVEY — 调研摘要与载荷数字总表（本项目的证据基座索引）

> **本文件的地位**：它是 `research/v2/` 语料的**可导航索引**，不是语料的替代品。
> 它回答三个问题：**这一轮查了什么、哪些数字可以用、哪些数字不许用**。
>
> **本文件不含**：术语定义、状态语义、门的分级、写权、flag 词表、留存分档。
> 这些**只在 `01-CONTRACTS.md` 定义一次**。本文件引用时一律写「见 01-CONTRACTS §N」，
> **不复述定义原文**——复述即为回归（可 grep 检测，见 01-CONTRACTS §9.3 / V9.1）。
>
> **本文件不裁决赌注**。押注强度与推翻条件在 `00-PREMISE.md`。本文件只标注「某维度的证据约束了哪条赌注」。
> 按 00-PREMISE 的下游引用规则：**不得引用它的裁决作为证据**，只能引用它指向的一手来源。
>
> **硬约束**：本文件中任何关于 DSH 运行时的陈述，均不得与 `research/v2/GROUND-TRUTH-CORRECTIONS.md`
> （以下简称 **GTC**）冲突。冲突以 GTC 为准。
>
> **写作纪律**：每条载重断言带 `[E: <文件>#<锚>]` 或一手 URL。语料标 `unverified` 的数字，本文件在引用处
> 一并标注，不做洗白。无外部证据、由本文件自行裁定的规则显式标 **〔裁定〕** 并给出「什么会推翻它」。
>
> **撰写日期**：2026-08-17｜**语料快照**：`research/v2/`，全部产出于 2026-08-17

---

## §1 方法说明

### §1.1 本轮的调研装置

本轮由 **25 个独立调研 agent** 产出 **25 份维度文件**，另由撰写阶段汇总出 1 份跨维度更正清单（GTC），
共 **26 个 `.md` 文件**、**11,661 行**（`ls research/v2/*.md | wc -l` 与 `wc -l` 实测，2026-08-17）。
两层分工：

| 层 | 文件前缀 | 维度数 | 取证对象 | 产物形态 |
|---|---|---|---|---|
| **一手真值层** | `gt-*` | **7** | 本机已安装的 **194 个 DSH 包**的代码/README、Paper Graph 全量档案、本仓库工程工件 | 逐条事实（含 `file:line`）+「与二手文档的冲突」段 |
| **外部证据层** | `ext-*` | **18** | 论文一手 HTML/PDF、官方文档与定价页、活体 API 实测 | 逐条发现 + **载荷数字核验表** + 未决与风险 |

一手真值层共报告 **50 处与二手文档的冲突**，GTC 从中抽取会**改变设计**的 **34 条**
（A 组 12 条运行时事实 / B 组 7 条前代证据重估 / C 组 7 条前代文档-代码落差 / D 组 4 条本仓库实践落差 /
E 组 4 条新机会）[E: GROUND-TRUTH-CORRECTIONS.md#头注]。

**⚠️ 一处必须当场更正的元数字**：本轮任务书与 `01-CONTRACTS.md` 文末的证据基线分别写作「23 文件」与
「22 文件」，实测为 **26 文件 / 25 个研究维度**。这是本文件对自己上游的第一条更正，**修法在 01-CONTRACTS
文末的「证据基线」行**。之所以要写出来：一个以「不让任何断言绕过证据审计」为价值主张的文档集，
连自己的语料规模都写错，是最廉价的攻击入口。

### §1.2 规模数字（全部为本文件自算，附计数规则）

| 数字 | 计数规则（口径） | 状态 |
|---|---|---|
| **26** 个语料文件 | `ls research/v2/*.md \| wc -l` | verified（自算，可复跑） |
| **25** 个研究维度 | 26 − GTC（GTC 是汇总件不是维度件） | verified（自算） |
| **11,661** 行 | `wc -l research/v2/*.md` 的 total 行 | verified（自算） |
| **784** 行核验表记录 | 18 张 `## 载荷数字核验表` 的数据行；**排除**表头与分隔行；含 `V4a/V4b/V4c` 这类子行 | verified（脚本自算，规则见左） |
| 分状态：**verified 642 / corrected 50 / unverified 79 / 其他 13** | 同一行按关键词优先级 `corrected > unverified > verified` 归一类；「其他」= 三词均未出现（如 `vendor-reported`、`media-selftest`、`flagged`） | verified（脚本自算） |
| **50** 处 gt 层冲突 / 抽取 **34** 条 | 前者为 GTC 头注自述；后者为 A1–A12 + B1–B7 + C1–C7 + D1–D4 + E1–E4 逐条计数 | 50 = 语料自述；34 = 自算 |

**必须随规模数字一起说的三句话**（否则这几个数就是装饰）：

1. **「784 行」不等于「784 个数字」。** 一行可以承载多个数字（`ext-academic-apis.md` 第 52 行一次给出四个
   工具的版本与日期），也可以是一条**否定性记录**（「Europe PMC 官方未公布任何限速数字」）。
   行数是**可审计单元数**，不是数字数。要按数字计，必须重新定义计数规则并重跑。
2. **`gt-*` 七维**没有 `## 载荷数字核验表` 这一节，其证据形态是「逐条事实 + file:line」与
   「与二手文档的冲突」。所以 784 这个分母**只覆盖外部证据层**，一手真值层的核验密度不在其中。
3. **状态分类是脚本按关键词做的，不是人逐行判的。** 关键词优先级会把「`verified`（数值）/ 口径不可比」
   这类混合状态归入 `verified`（例：`ext-academic-apis.md` 第 49 行 marker 76.0%）。
   要拿这三个数做质量论证之前，必须先人工复核一遍分类。**本文件不用它们做任何质量论证。**

### §1.3 相对上一轮的五处方法升级

上一轮的实证故障是：约三分之一的载荷数字口径失真，机制是「一手源不可达 → 静默回落到博客二手源」
[E: ext-legal-tos.md#结论摘要-6]。本轮的五处升级全部是针对这条机制的：

**U1 · 一手来源优先，且「一手不可达」是一等公民状态。**
不再允许用聚合站转述补齐一手源。本轮实测到的关门样本被逐条记录而不是绕过：
`onlinelibrary.wiley.com` 402、`sso.agc.gov.sg` / `sal.org.sg` / `irishstatutebook.ie` /
`japaneselawtranslation.go.jp` 403、`eur-lex.europa.eu` 三种 URL 形式均空正文
[E: ext-legal-tos.md#结论摘要-6]；`intology.ai` 403，导致 Zochi 的「top 8.2%」全链路无一手
[E: ext-science-agents.md#未决-4]；`thelancet.com` 403、`openai.com` 全站 Cloudflare 拦截
[E: ext-incidents-products.md#一手源未能直取]。
该规则已被上收为契约（01-CONTRACTS §8.6.4 的 `T12-UNREACHABLE`）。

**U2 · 落笔即验证：数字必须在写下的同一次动作里回抓一手源。**
最强的自证是**本轮当场纠正了自己**：`ext-chinese-ecosystem.md` 先用 OpenAlex 默认排序取前 50 条得到
「DOI 92%、refs 50%」，改用 `sample=100&seed=42` 随机抽样后得到「DOI 70%、refs 2%」——**refs 差 25 倍**，
原因是默认分页偏向元数据齐全记录。该行在核验表里被**划掉并标 `corrected → 已废弃`**，而不是删除
[E: ext-chinese-ecosystem.md#载荷数字核验表]。这条已上收为 01-CONTRACTS §3.6.1。

**U3 · 口径三元组是强制列。** 每个载荷数字必须写出 `(指标 / 样本或档位 / 对比基准)`。
该三元组随后被提升为契约的一等公民字段（见 01-CONTRACTS §9.4）。**升级的直接产出**是一批
「数值正确但口径被掉包」的发现，它们在旧方法下会全部通过：PaperQA2 的 85.2% 是 **precision** 不是
**accuracy**[E: ext-citation-faithfulness.md#核验表-17]；1.07% 的分母是**论文**不是**引文**（引文级约
0.034%）[E: 同上 #24]；85.1% 是**判定器与人工的一致率**不是模型的引文质量分 [E: 同上 #31]。

**U4 · 防伪独立印证：按上游簇归并，不按域名。**
本轮抓到的活体样本：11 家中文媒体回溯同一条 Nikkei Asia [E: ext-security-injection.md#E3]；
8 个域名复述同一篇 BadRAG [E: 同上 #A3]；Feet of Clay 的「764,000+」被二手转成「110 万 / 1.2 万」
[E: ext-literature-integrity.md#核验表]；Tavily 的「10 QPS / 100 QPS」逐字等于 Exa 官方表，是张冠李戴
后多站转抄形成的假共识 [E: ext-web-providers.md#核验表 T-FALSE]；`research.google` 博客 / arXiv v3 /
ResearchSquare / *Nature MI* 是同一批人同一项工作的四个载体，**算一个来源**
[E: ext-orchestration.md#结论摘要-8]。该维度已上收为 01-CONTRACTS §5.5 与 §9.15。

**U5 · 跨厂商与跨通道取证。**
同一篇论文走 `arxiv.org/pdf/...` 与 `arxiv.org/html/...` 得到两组互相矛盾的数字，**PDF 路径那组是幻觉**
（「2,000 篇摘要 / 召回 45% / FPR 8%」vs 正文一致的「2,526 条 BibTeX / 检出率 0.268 / FPR 0.185」）
[E: ext-verification-mechanisms.md#结论摘要-6]。这条直接产出了「取证层禁止从二进制 PDF 摘要直接出数字」
这一硬约束。**注意边界**：跨厂商在本轮只用于**取证通道**，不是「跨厂商裁决者」——后者是 01-CONTRACTS
§5.2 规定的运行时机制，本轮语料本身**没有**跨厂商复算过任何一个数字。

### §1.4 方法本身的三个已知弱点（预注册，供攻击者优先瞄准）

1. **本轮没有任何一个数字被第二个 agent 独立复算过。** U5 只做到了「同一 agent 换通道」。
   「跨厂商独立印证」在本轮**是缺席的**，不是弱化的。谁把 §1.3 的五处升级读成「本轮数字经过交叉复核」，
   读错了。
2. **并行调研本身制造了一条负面数据点。** 多个兄弟调研 subagent **共享 WebSearch 会话配额**，
   至少三个维度在第 2–14 次检索时配额耗尽，被迫降级到 serper/curl 兜底，并各自留下「反证检索做得不够」
   的自陈 [E: ext-orchestration.md#U9, ext-multimodal-evidence.md#R1, ext-academic-apis.md#未决-8,
   ext-incidents-products.md#未决与风险]。这条已被 00-PREMISE B1 采信为反对超并行的第 7 条证据。
3. **状态标签由产出该数字的同一个 agent 自评。** `verified` / `corrected` / `unverified` 没有独立复核层。
   §1.2 的 642/50/79 三个数因此**只能读作「作者自评分布」**，不能读作「质量分布」。

---

## §2 逐维度摘要

> **读法**：每节给出「结论 / 最重要的 2–3 个发现 / 它约束了本项目的哪条决定」。
> 「约束了什么」一律指向 00-PREMISE 的赌注编号或 01-CONTRACTS 的节号，**不复述那边的内容**。

### A 组 · 一手真值层（`gt-*`，7 维）

#### §2.A1 `gt-evidence-substrate` — 证据底座

**结论**：per-claim 证据台账**可以**写成自定义 log-only session 事件并被 JSONL 无损持久化，
但那样做会让该 session 在标准读路径上**不可 resume**——这不是配置问题，是写入 API 的能力缺口。

**三个最重要的发现**：①`ignorable` 字段**只读不写**，`Session.append` 的签名与实现里根本没有该通道，
全 194 包 grep 零写入方；未知事件类型会让 `assertEventsSupported` 在**四个读入口**全部抛错并拒绝解释
整份日志。已在野证实代价：第三方插件写 `ya-subagent/started` 的那个 session **没有任何 `session/end-seed`**。
②落库的 `tool/result` 存的是**截断后**内容，超阈值纯文本结果原文**不在日志里**——反伪造门的比对基底
必须是 CAS 快照文件，日志只用于绑定「这次抓取确实发生过」。③磁盘是**多 frame zstd 串接**，
Node 内置 zstd API **只解第一帧**（实测得到 1 行、实际 3675 行）。

**约束了什么**：01-CONTRACTS §4 W-01/W-02（CAS 与 `tool/result.data.meta.evidence` 的写权）、
§8.2（台账落文件不落自定义事件）、§6.5.4（读日志的门必须处理的三个地雷）；
GTC A1/A2/A3/A5 与 E2/E3。另：v1「tokenMeter 读不到 per-step 缓存分解」的**结论对、理由错**——
per-step 分解逐 step 都在日志里，理由必须改为「DSH 不持有 provider 价目表」（01-CONTRACTS §4.3）。

#### §2.A2 `gt-exec-security` — 执行与安全边界

**结论**：沙箱词汇 = **纯文件效果**，网络与进程完全不管；能真正强制「证据必须来自被记录的工具调用」
的机制只有工具边界上的三条。

**三个最重要的发现**：①bwrap 参数无 `--unshare-net`、Seatbelt profile 是 `(allow default) (deny file-write*)`、
Landlock grant 只有读写路径——**任何「用 DSH 沙箱做网络围栏」的设计一律是假的**。
②`run_code` 对沙箱包**零依赖**，用 `new AsyncFunction` 在 worker 自己的 realm 里直接求值，
README 自陈 "containment, not a security boundary"；它**同时绕过**内核沙箱与 `ctx.fs` 策略围栏。
③`toolFilter` 不是权限天花板（三处一手明文否认），且不向下传递；子代理拿的是全新扁平 scope。
④本机**没有任何 fetch provider 包**，`web_fetch` 在出厂组合里是关的；`WebSearchSource` 只有
`url/title/snippet/publishedAt`，没有 DOI/作者/venue。

**约束了什么**：01-CONTRACTS §4.4（写权是审计契约不是文件系统权限）、§5.3（取证子代理必须走 `spawn`）、
§8.5（检索抓取工具必须自建及其自带义务）、§4 W-12（运行时指纹）；00-PREMISE B5 的天花板一节；
GTC A6/A7/A8。

#### §2.A3 `gt-house-method` — 房内方法论

**结论**：房内方法论由三个可分离层构成（loop runbook / gate 完整性 / attacker battery），**必须整体继承**；
而其中最贵的一条经验是「**跨越执行边界的检查是空的**」。

**三个最重要的发现**：①同一失败类在本仓库连续出现三次（persona mount / role-pack 子串检测 /
plugin_load dump-config），每次都是配置层通过、运行时打脸，每次都由**新鲜上下文的对抗读者**发现，
**从来不是门套件发现的**。修法永远相同：对运行系统自己的痕迹断言。
②runbook 宣称 "Gate-integrity is pinned, not vibes"，但全量 grep `gates-baseline|porcelain` 在三个子项目里
**零命中代码**，只命中两处散文——目前完全依赖 conductor 自觉；仓库里有 22 个 `gates-baseline-*` tag，
证明机制被真实使用过，但**校验没有实现**。
③成本是量出来的不是估出来的：plugin-creator 真实 e2e run-2 = 93.35 分钟 / 16 subagents / 30 steps /
CNY 5.58；对照基线 58.6 分钟 / 7 subagents / ~CNY 12。且房内自评为 "better-governed, not better-output"。

**约束了什么**：01-CONTRACTS §6.5.1（red-first）、§6.5.2（gate 完整性必须是脚本）、§6.5.3、
§9.21/§9.22；00-PREMISE B8（我们**当前不押**自己的门，须先补三条代码）；GTC D1。

#### §2.A4 `gt-orchestration` — 编排原语

**结论**：**不存在「一个」并发上限**，存在五条互不相同、由不同代码强制的并发闸门；
而 DSH 出厂把 `subagent` 与 `subagent_fork` 都设成 `continuable`，即**默认扇出路径恰恰是那条运行时不设上限的**。

**三个最重要的发现**：①五条闸门的实测值：一条 assistant 消息内并排调 `subagent` = `maxParallelToolCalls` 默认
**10**；workflow 的 `agent()`/`parallel()` = `maxConcurrentAgents` 本机实测 **12**（硬顶 16）；
`continuable` 后台子代理 = **无任何上限**；one-shot 后台任务 = 每 owner **10**（超限直接报错，**不排队**）；
`run_code` 内部子调用 = `maxParallelSubCalls` **10**。真正的兜底只剩 `maxDepth: 3` 与宿主内存。
②workflow 的 `agent(prompt, opts)` 代码支持**五个**选项 `label, phase, schema, provider, model`——
`provider` 可用意味着**跨厂商验证者可在 workflow 内直接声明**，而 `dsh-workflow-worker-thread` README 的
Script contract 段落漏列了它。③`defaultMaxGoalRounds = 256` 代码确认；但 `dsh-tool-ralph` 的 README 写
`maxRounds` 默认 256 而**出厂 composition 压到 64**——两个轮预算是不同的东西。

**约束了什么**：01-CONTRACTS §5.2 与 §5.2.1（provider 的两义消歧）、§5.3 R-I5（深度三层闭合）、
§9.24（轮预算）、§9.25；00-PREMISE B1 的「并行粒度优先级」；GTC A10/A11/A12 与 E1。

#### §2.A5 `gt-pg-current` — 前代系统现状

**结论**：前代 post-reset 系统只有 **608 行**可执行代码（`wc -l` 实测），**文件契约值得逐字继承，
两个门 + eval harness 的判定实现一条都不能继承**——它们几乎全是 fail-open 的，且被逐条实跑复现。

**三个最重要的发现**：①**rigor 门根本不重执行**：`rigor_gate.py:189` 只比对 metric 文件；
伪造一个 metric、无 dvc.yaml、无 transform、无原始数据 → **exit 0 PASS**。
文档宣称「门重执行」是假的。②「4/4 双门全绿、独立 eval 3/4 REVISE」这个流传结论需要修正得更狠：
真实是 4/4 双门全绿；独立 eval 3 个 REVISE + 1 个 **fail-open 的假 SHIP**（缺面板文件所致）；
真正跑完 D1–D5 完整面板的只有 1 个，结论是 REVISE——**0/4 真正拿到过发布裁决**。
③第三种 claim kind 不是「没实现」，是**会被现有门主动判死**：`rigor_gate.py:152-153` 对未知 kind 直接
`ok=False`，会把复现率拉到 100% 以下 → 门 FAIL。

**约束了什么**：01-CONTRACTS §2.3（K-I 是要新建的机制及其六项必备工件）、§4 W-04（status 的物理写者）、
§5.1（独立性取自 harness 而非 prompt 措辞）、§9.19（fail-closed）；00-PREMISE B6（押文件契约、
**不押任何门的判定实现**）；GTC C1–C7。

#### §2.A6 `gt-pg-failure` — 前代失败考古

**结论**：v1 继承的最高禁令（「四次严格消融判死了结构框架」）**地基被一手数据严重削弱**；
「判死」这个措辞在一手文件中根本不存在，作者每轮都写了限定语。

**三个最重要的发现**：①四次消融的独立样本量分别是 N=1/5/5/1 topic，评委恒为 3 个 Opus，
评分被压缩在 4–5 两档；**没有任何一项跨臂质量差在 topic 级达到 p<0.05**（tree−skills +0.134, t=0.43；
skills−raw +0.068, t=0.19；tree−notree −0.389, t=−2.12, p≈0.10）。
②那个 −0.39 里最大的一项是**渲染伪影且可机械证明**：calibration 一项 tree=4.0（15/15 全是 4）、
notree=5.0（15/15 全是 5），方差为零；原因是 `comparison3/dossier.py` 只在 `status ∈ {retired, stuck}`
时才输出 Dead ends 段，而 tree 臂 5 个 topic 的 `dead_ends` 全为 0——**评委在给「有没有那一节」打分**。
③一手 RESULTS.md 自身有一处推理错误并被 v1 整段继承：它写「纪律不是机器才是杠杆」，
而它自己那张表给出 raw 4.53 / skills 4.60 / tree 4.73，即**纪律增量 +0.07 < 机器增量 +0.13**。
④对象错配：13,949 行的 paperproof v2 **从未被任何消融测过**，它死在 live run 的 worker 输出契约上。

**约束了什么**：00-PREMISE B2（把 P-1 从最高禁令降级为有界设计偏置 + 四类结构白名单）、
01-CONTRACTS §9.30；GTC B1–B7。**这是本轮唯一一个「推翻上一轮最高级别继承结论」的维度。**

#### §2.A7 `gt-profile-plugin` — profile 与插件机制

**结论**：profile 只需三个文件；整棵插件树 = 「空根 `[]` + 一串 patch」；
**`export const Config` 不是强制的**，v1 在这一点上过度断言。

**三个最重要的发现**：①`cordis/lib/index.js:956` 第一行是 `if (!runtime.Config) return config;`——
没有 `Config` 的插件不会在 load 期崩溃；有 `Config` 时走 **Standard Schema v1 接缝
`Config["~standard"].validate`**，schemastery 与 zod 皆可，且**只支持同步校验**（异步会抛）。
真正会让 boot 崩的 load 期不变式有**五条**（import 失败 / 导出形状非法 / Config 校验抛 / `apply()` 抛 /
inject 未解析致 PENDING）。②`--dump-config` 的输出 **≠** 实际 boot 的树（CLI 在 `composeProfile` 里额外追加
`agent-presets.roots` 与 telemetry disable 两层，`runDumpConfig` 不加）——**把 dump 当 boot 真值会漏配置**，
这正是 §2.A3 那条「配置层检查是空的」的又一实例。③`isConcurrencySafe` 只 gate 同一条 assistant 消息里
相邻兄弟工具调用能否重叠，只有精确返回 `true` 才并行，其余一律 exclusive（fail-closed）。

**约束了什么**：01-CONTRACTS §6.5.5（boot 门断言五条加载期不变量）、§9.23（出厂值 vs 包默认值）；
GTC A4/A9/E4。**⚠️ 本维度与 `ext-web-providers` 是本轮仅有的两个尚未被任何 v2 成文文档引用的维度**（见 §6.4）。

### B 组 · 产品定义与竞争面（3 维）

#### §2.B1 `ext-incidents-products` — 真实事故与商业产品对照

**结论**：这套核验机器**已经被造出来了，但只被造成了「尺子」，没人把它做成「产品」**——
这是本项目差异化陈述的一手依据。

**三个最重要的发现**：①事故已可按年计数：AI Hallucination Cases 数据库在 2026-08-16 收录 **1922 起**，
其中 **Pro Se Litigant 1111 起 > 律师 761 起**——用户画像正是「任何人拿 LLM 产出去承担后果」。
②引注污染规模已被一手审计量化：PMC OA 子集 250 万篇论文的 9,710 万条已核验引注中发现 **4,046 条**
捏造引文，分布于 2,810 篇；发生率从 2023 年的 1/2,828 升到 2026 年初的 **1/277**；**98.4%** 的受影响论文
出版方未采取任何行动。③在出货产品里（OpenAI/Gemini/Claude/Perplexity/Grok）**没有任何一家给单条断言
附核验状态**，全部止步于挂链接；而 Perplexity 的 WANDR 与 PwC 的三层拆分都只是**离线评测装置**。
④撤稿检查是公开空白：JMIR 2026-05-01 的结论是没有任何现有免费 GenAI 系统在处理撤稿文献上可靠，
研究型工具 SciSpace/ScienceOS/Consensus **零篇全对**。

**约束了什么**：00-PREMISE B3（可信度是产品，**大仓位**）；01-CONTRACTS §1.4.4（不存在聚合 status）。
本维度还贡献了上一轮口径事故的完整解剖（Deloitte 澳洲退款额，见 §3.3）。

#### §2.B2 `ext-dr-architectures` — deep-research 架构谱系

**结论**：**停机（STOP）是整个谱系上最薄弱的一环**——13 个系统只有两类停机机制，
「与内容有关且可重跑」的停机门**一个都没有**。这正是本项目的空白地带。

**三个最重要的发现**：①两类停机分别是「预算计数器」（可重跑但与内容无关）与「LLM 主观判定」
（与内容有关但不可重跑）。②活下来的架构共性是外部化工件 + 每轮重建工作区 + 按引用 ID 定向取证写作
（WebWeaver / IterResearch / Self-Manager 三条独立线收敛到此），**没有一个 SOTA 系统靠 claim-graph 框架取胜**。
③2026 年的方向转移：DeerFlow 从深研究框架整个推倒重写成通用 super agent harness（与 v1 零共享代码），
Agon 直接把命题写成「瓶颈已从产出工件转移到裁决主张」——前者是本项目要**抵抗的引力**，
后者是要**抢占的定位**。

**约束了什么**：00-PREMISE B1（扇出的正向证据全是 test-time scaling，无一篇等算力对照实验）与 B2；
01-CONTRACTS §8.1（扁平 CAS + 一 claim 一文件，不建 claim graph）。

#### §2.B3 `ext-science-agents` — 自主科研 agent 与自验证机制

**结论**：这个领域最重要的事实不是「能力到哪了」，而是「**验证口径全是碎的**」——
24 个可运行系统里代码开源率 83%，但**种子/执行轨迹开放率只有 38%**，新颖性验证方法披露率同样 38%。

**三个最重要的发现**：①全行业在**解释性/综合性陈述**上同时塌陷：Kosmos 自评数据分析类 85.5%、
文献类 82.1%、**综合解释类只有 57.9%**；*Correct Answer, Wrong Mechanism* 测到 20%–37.5% 的「结论对但机制错，
且用与自己数据矛盾的物理去辩护」；SoundnessBench 测到 12 个前沿 LLM 对低严谨提案的**假阳性率 74.0%**。
②「引用干净」和「结果可复现」是两个**正交**的失败模式：Sakana AI-Scientist v2 幻觉引用率 **0/159（0%）**
但分数复核只有 **5/12（42%）**；DeepScientist 分数复核 11/12（92%）却有 42/201（21%）幻觉引用。
③**人类同行评审不是可用的 oracle**：Sakana 那篇通过 ICLR workshop 评审（均分 6.33）的论文，
作者自己事后承认实验存在约 **57% 的训练/测试集重叠**，三位人类评审没抓到。

**约束了什么**：01-CONTRACTS §2.3.1（K-I 永不可达 ST-V）、§1.3；00-PREMISE B4。
本维度另贡献四条 `corrected`（见 §3.3），其中 PaperQA2 的 precision/accuracy 掉包与上一轮踩的坑**同型**。

### C 组 · 验证机制（5 维）

#### §2.C1 `ext-verification-mechanisms` — 可自动化的声明验证机制菜单

**结论**：文献里几乎所有「高精度」验证数字都是**聚合级（system-level）口径**，
而本项目要的是**逐条（per-claim）口径，两者差一个数量级**。按聚合数字选型的方案，落到逐条标签上都会崩。

**三个最重要的发现**：①最典型的口径陷阱：FActScore 摘要里的 "error rate < 2%" 是模型层面的差值，
同一篇附录里**逐条原子事实的 F1-micro 只有 53.3%–83.2%**；AutoAIS 系统级 Pearson 0.96，
论文明确警告「不要细读单条分数」。②**决定验证器能否上线的是假阳率（FPR），不是召回率**：
agentic 查证把召回买到 0.98–0.99，FPR 同时飙到 0.43–0.48；规则型 bibtex-updater 用 0.865 的检出率
换 0.092 的 FPR。③**分解（decompose-then-verify）不是免费的**：MiniCheck 在 WiCE claim-level 上
从不分解的 80.01 BAcc 掉到 FActScore 式分解后的 71.11——分解应当是 keep-if-better 的可选路径。
④三类 claim 中**逻辑推断类在文献里几乎无成熟机制**，且这条赛道有历史污点（ARCT 上 BERT 的 77%
被证明完全由伪统计线索解释，对抗集上退化到随机）。

**约束了什么**：01-CONTRACTS §1.3（`claim_supported` 的三条量化上界之一）、§2.3.1 的推翻条件、
§6.1（三个门类）、§6.4。本维度还贡献了 U5 那条 PDF-vs-HTML 幻觉的实测。

#### §2.C2 `ext-citation-faithfulness` — 引用忠实度的实证基线

**结论**：「链接能打开」和「源真的支持这句话」之间存在 **40–60 个百分点的鸿沟**，
且这个鸿沟在 2026 年的前沿深度研究产品上依然存在。

**三个最重要的发现**：①三层拆分测量（14 个前沿模型）：链接可访问率 >94%、内容主题相关率 >80%、
**逐条事实核查通过率只有 39–77%**。②**更深的搜索不会改善支持率，反而摧毁它，而表层指标毫无变化**：
GPT-5.4 从 2 次工具调用的 78.6% 掉到 150 次的 16.7%（跌 62 个百分点），Claude Opus 4.6 从 80.0% 掉到
57.9%，同期链接有效率与相关率稳定在 92% 以上。**限定必须一起带**：单篇预印本，仅两个模型做深度消融，
未报相关系数/回归/p 值，判定器是 rubric-based LLM-as-a-judge。③**「多引几个源」救不回来**：
把某条陈述的**全部**被引源合并后再判定，**95.1% 原本不被支持的陈述仍然不被支持**。
④学界对「幻觉」的定义分裂：Magesh 等的二维分解 correctness × groundedness，
把 hallucination 定义为「incorrect **或** misgrounded」——**本项目的产品差异化恰好落在这条定义线上**。

**约束了什么**：01-CONTRACTS §2.2.3（引文层实证基线，且明写「并行度与检索深度必须与每条 claim 的证据预算
解耦」）；00-PREMISE B1 的第 1 条反对证据。本维度贡献 7 条 `corrected`（见 §3.3）。

#### §2.C3 `ext-literature-integrity` — 文献污染筛查与取证元科学

**结论**：免费且确定性的污染门**只有一层，但这一层很扎实**；其余各层必须按「适用条件」分级，
且适用条件本身必须是门的输出而不是门的假设。

**三个最重要的发现**：①**权威源是 Retraction Watch CSV**（Crossref 托管、每工作日更新、无鉴权），
2026-08-17 实测全库 71,799 行、其中 `RetractionNature = Retraction` **66,287** 行、去重原文 DOI **62,708** 个。
②**不要用 OpenAlex 的 `is_retracted` 当门**：实测 134,175，约为 RW 撤稿数两倍；随机抽样 200 条归因，
只有 81 条（40.5%）是被撤原文 DOI，69 条（34.5%）其实是**撤稿公告本身**——直接当布尔门会把撤稿公告
判成造假文献。③**GRIM 的检出功率有闭式解** `power = max(0, 1 − N·items/10^d)`，已用 20,000 次/点蒙特卡洛
验证（N=28 实测 0.718 vs 理论 0.720；**N ≥ 100 且 d=2 时功率恒为 0**）——一个不带 N/items/小数位判定的
GRIM 门会在大样本论文上给出「全部通过」的假安全感。④statcheck 的 96.2%–99.9% 是被严重压缩的口径：
真实基础是 48 篇 / 1,120 条人工编码，只统计完整 APA 的 t/F/χ² 且 p<.05，且只在人机都抽到的交集上算，
而**抽取召回率只有 61.1%–61.2%**；现场 20 篇 737 条 NHST 的 113 条 flag 里，14 条是抽取错误、
**64 条（57%）源于统计校正**。

**约束了什么**：01-CONTRACTS §6.2.1（门必须把适用条件与结论一起输出）、§6.2.2、§6.2.3、§6.2.4、
§6.3（GC-1 的四条硬要求）、§6.3.1、flags F-05/F-06/F-07/F-08/F-18/F-19/F-20/F-21。
**这是本轮方法论收获密度最高的一维**。

#### §2.C4 `ext-multimodal-evidence` — 图表/表格承载的数值证据

**结论**：**表格已近饱和，图表远未解决**；因此第一条路由规则不是「图表怎么读」，而是「**能不能不读图表**」。

**三个最重要的发现**：①最致命的失效模式是「判对了结论、指错了格子」：GPT-4o 在 SciTabAlign 上
标签 Macro-F1 **88.4**，恢复关键单元格的 Macro-F1 只有 **34.8**，且 exact-match 设定下**没有任何模型
能让「标签+依据同时正确」超过 50%**——「结论正确」这一信号对「依据正确」几乎没有预测力。
②**头号可门控变量是有没有印刷数据标签**，不是模型强弱：同一模型、同一批 50 张 Vega-Lite 图，
有标签 MAPE 1.3%–1.8%、去掉标签 7.2%–7.4%。分族 Adaptive MAPE：scatter 2.63 / bar 3.78 / line 4.35 /
**pie 11.58 / radar 28.01**。③**错误结构是「漏」不是「编」**：遗漏占错误类型的 60%–74%，
幻觉率仅 0.08%–6%——守门重心应从反幻觉转向反漏项，**这与文本类验证的直觉相反**。
④自洽性只能当分诊信号：抽样离散度与准确率的 Spearman ρ 仅 −0.30 ~ −0.37（解释方差约 9%–14%）。
⑤人机协作真实天花板约 **0.85–0.91**，三条独立证据线都落在这个带里。

**约束了什么**：01-CONTRACTS §3.4.2（G5 门槛比字符串包含更严的依据）、§3.5（图形派生数值强制 ST-E
及图族黑名单）、flag F-10、§9.13（基准饱和必须写全称）。

#### §2.C5 `ext-human-methodology` — 人类证据方法学 → 机器可执行 gate

**结论**：人类证据学早就解决了我们要解决的问题，解法不是「框架」，是「**信号问题 → 确定性算法 →
可推翻但要留痕的判定**」三层结构；Cochrane RoB 2 的形态最值得直接抄。

**三个最重要的发现**：①**最强的一手经验证据支持「分解到原子事实问题」**：同一篇 JMIR 研究里，
LLM 在**信号问题层面**平均准确率 83.2%（95% CI 77.5–88.9），聚合到**域层面**降到 65.2%、
整体 RoB 判定只有 57.5%–70%；另一项研究显示直接让 LLM 输出 RoB2 判定 F1 只有 0.1–0.2，与平凡基线无异。
**结论：让模型答事实问题，让代码做聚合判定。**
**〔口径 · R1〕以下一致率数字均为 raw agreement，原研究未报 κ。按本项目 §1.3 的一手证据，raw agreement 相对 chance-corrected 的 κ 平均虚高 38.6 个百分点（区间 33.8–41.3 pp，MT-Bench 2,391 对 / 21 个 judge），因此下列数字只能读作上界，不能与本项目对自己设定的「一致率 ≥85% 并报出 κ」门槛直接比较。**

②**「可重跑」必须是一等公民，因为模型连自己都对不齐**：ChatGPT-4o 的自身重测一致率只有 74.7%
（95% CI 64.8–84.6）；Elicit 换账号重跑取值一致率 90%、但支撑引文只有 46%、推理只有 30%。
③**IPCC 有一条可直接搬的硬规则**：只有当置信度为 high 或 very high 时才允许给出定量 likelihood；
证据有限且共识低时**连 confidence 都不许给**——翻译成本项目就是「没到 verified 档就禁止输出量化断言」，
这是**类型系统级**的禁止而不是提示词纪律。④可自动化边界已被测出来：URSE 在 115 篇 Cochrane 综述上
imprecision 0.97/0.94、I² 0.90/0.90、AMSTAR 0.98/0.99，但 **risk of bias 只有 0.73/0.70**，
整体 GRADE 等级一致率 63.2%、κ = 0.44——**能算的几乎全自动，要判断的不行**。

**约束了什么**：01-CONTRACTS §1.2/§1.3 的谓词切分形态、§6.1 的三个门类分工、§6.4（κ 而非 accuracy 作为
上线门槛）；00-PREMISE B4。本维度另贡献两个「数字洗白」活体样本（见 §3.3 与 §4）。

### D 组 · 证据基础设施（5 维）

#### §2.D1 `ext-academic-apis` — 学术检索 API 与全文获取

**结论**：2026 年最大的结构性变化是 **OpenAlex 从「完全免费」转为「免费数据 + 付费服务」**；
而超并行系统的真正瓶颈**不是 token，是每 host 的 RPS，且最紧的几个是硬 1 rps 量级**。

**三个最重要的发现**：①**单实体 lookup（`/works/{id}`）成本为 $0**（实测
`x-ratelimit-credits-used: 0`）——「已知 DOI/ID 取全量元数据」这条路径无限免费，**这一条几乎决定了
本项目的检索架构**。②**Unpaywall 已不是独立信源**：OpenAlex 官方明说 "Unpaywall records are served from
the same OpenAlex data"，实测返回体的 `evidence` / `updated` 字段值已 literally 变成 `"deprecated"`——
用它去交叉验证 OpenAlex 的 OA 状态是典型的假独立佐证。③**全文可得性的天花板**：默认口径 324,389,590 篇中
`is_oa:true` 123,672,025（**38.1%**）、`has_content.pdf:true` 54,999,764（**17.0%**）——
「每条论断都可追溯到原文」在现实中最多覆盖约六分之一的英文文献，**必须写进产品承诺**。
④最紧的四条限速：**arXiv 1 请求/3 秒且禁止并发连接**、Semantic Scholar 有 key 1 rps、
OpenAlex 语义检索 1 rps、CORE 免注册 ≈0.5 rps。

**约束了什么**：01-CONTRACTS §3.2（可得性上限与 corpus 口径警告）、§3.3（evidence_grade 的获取路径列）、
§5.5.1（已知上游继承关系）、§6.3 硬要求第 5 条（限速按 host 分桶）；00-PREMISE B1 的第 8 条反对证据。

#### §2.D2 `ext-web-providers` — 通用检索/抓取供应商层

**结论**：这一层的真实瓶颈不是钱，是**每供应商节流上限**，而且**各家的节流指标根本不是同一个东西**——
七家用了四种互不可比的单位（QPS / RPM / 并发浏览器数 / 每小时配额）。

**三个最重要的发现**：①**最贵的不是最快的**：同样 1000 次 Google SERP，serper.dev Starter 档
**$1.00/1k 且 50 QPS**；SerpApi Starter 档 **$25/1k 且 200 次/小时**——价格差 25 倍，
吞吐差约 900 倍（派生折算）。对超并行系统，SerpApi 低档位**在物理上就跑不动扇出**。
②**发现层与取证层必须分开建模**：SERP 类返回的是片段，只有取证层（Jina Reader / Firecrawl scrape /
Exa contents / Tavily extract）返回可逐字引用的正文。
③**两个合规硬点直接咬到「可重跑证据库」这个产品形态**：Brave 官方 FAQ 明写存储 API 结果需订阅
**显式授予存储权**的计划，通用 ToS 不覆盖；Jina 免费的 1000 万 token 明确标注 **CC-BY-NC**。
④意外收获：Firecrawl 有 `GET /search/research/papers` 的 Research Index，论文类端点官方定价表标为
**Free（0 credit）**——本维度唯一「学术专用且不计费」的通用供应商能力（**但其字段契约页 404，
契约本身 `unverified`**）。⑤Jina AI 已并入 Elastic（页脚实读 `Elastic © 2020-2026`），
定价/条款存在再次变更的结构性风险。

**约束了什么**：**目前尚未被任何 v2 成文文档引用**（grep 实证，见 §6.4）。
本维度与 01-CONTRACTS §3.4.1（snippet 一票否决）、§6.3 第 5 条（中央限速网关）、§8.6（留存分档）
在主题上直接对应，但那几节的证据指针指向别的维度——**这是一个必须在下游文档中闭合的接线缺口**。

#### §2.D3 `ext-evidence-schema` — KG-free 证据库与记忆的工程 schema

**结论**：现有系统的去重键几乎都是错的，且错法一致（用 URL 或用语义相似度）；
正确解是**按「来源坐标」内容寻址去重，绝不按「内容」去重**。

**三个最重要的发现**：①**语义相似度去重会主动吃掉矛盾**——这是本维度最重要的负面结论。
生产系统 MemClaw 的复盘原文：矛盾的自然表述（"XX is AA" 然后 "XX is BB"）在文本上近乎相同，
而近重复门是**同步 pre-commit** 的、矛盾检测器是**异步 post-commit** 的，
**管线顺序保证了矛盾写入永远到不了矛盾检测器**。②**主流 agent memory 的矛盾语义全部不适用于科学证据**：
mem0 的更新提示词规定「矛盾即删除」，Graphiti 的失效判定是**纯时间性**的；两者都假设「世界状态单值、
新的覆盖旧的」，这对「2019 年队列研究 vs 2026 年 RCT 结论相反」完全不成立。
③**DOI 不是版本锚**：arXiv 官方确认替换版本不生成新 DOI 且 DOI 永远指向最新版——
唯一的版本锚是带 `vN` 后缀的 arXiv ID。④**模糊身份解析可以提议合并，绝不能自动执行**：
bioRxiv 生产系统的标题匹配把 120 篇「未发表」预印本中的 **37.5%** 判错（其实已发表），
把一个统计量搞错了约 25 个百分点。

**约束了什么**：01-CONTRACTS §4 W-06（证据卡 id = `hash(work_id, locator, extractor_version)`）、
§5.5 归并键优先级、§5.5.2、§8.1 布局。

#### §2.D4 `ext-reproducibility` — 可复现与溯源基础设施

**结论**：不要用仓库级锁工具，自建 CAS；不要做 notebook 验证；不要做哈希链；
**封闭式与开放式的能力差是 2–4 倍，断层就在「谁定义问题」这条线上**。

**三个最重要的发现**：①**DVC / DataLad / git-annex 与超并行前提直接冲突**：
`dvc repro` **没有 `--jobs` 并行开关**，官方要求并行只能「在不同终端里并发地多次启动」，
而 troubleshooting 页写着并发会撞锁（`.dvc/tmp/lock`）；请求并行调度器的 issue **#755 开于 2018-06-08，
至今 open**。**这不是配置问题，是设计前提问题。**
②**notebook 验证路线整体跳过**：papermill 2.7.0 只做参数化与执行、**根本不比对输出**；
nbval 才做比对，而它的比对是 false-red 制造机（matplotlib 只比对含内存地址的文本 repr、
dict 顺序、时间戳、RNG 全会假失败，且默认不 sanitize）。
③**哈希链是过度设计**：威胁模型不成立——能改 claim 记录的人同样能改哈希链的锚点；
真正需要的是「输入内容寻址 + 输出可重跑比对」这种**功能性**防篡改。
④范围判定的核心输入：封闭式（DABstep hard）从 2025-06 的 14.55% 涨到 2026 年多家宣称 87–100%
（**但已进入基准饱和/过拟合区间**），开放式端到端仍在 21–45%（DSBench 34.12%、BLADE F1 44.8%、
CORE-Bench-Hard 21.48%、REPRO-Bench 21.4%）；最干净的内部对照是 CORE-Bench 同一 agent 同一模型
Easy 60.00% → Hard 21.48%。

**约束了什么**：01-CONTRACTS §2.1（K-D 的必备工件、fail-closed 六点、开放式端到端不得产出 ST-V）、
§8.3（拒绝仓库级锁工具）、§8.4 的 D-8.4 至 D-8.11、§9.13。

#### §2.D5 `ext-chinese-ecosystem` — 中文学术与 deep-research 生态

**结论**：中文文献在国际开放索引中的覆盖是「**结构性残缺**」而非「稍微少一点」；
且失败模式是**静默返回空而不是报错**——这比覆盖率低危险得多。

**三个最重要的发现**：①**顶刊按 ISSN 查不到**：《管理世界》(1002-5502)、《中国社会科学》(1002-4921)、
《历史研究》(0459-1909) 三个 ISSN 在 OpenAlex `sources` 与 Crossref `journals` 中**命中均为 0**；
改用刊名检索才发现存在**无 ISSN 的残桩记录**。任何以 ISSN/DOI 为主键的中文流水线会静默失败。
②**引文关系缺失直接杀死引文滚雪球**：论文口径 references 完整率 **7%**，我方随机抽样
（`sample=100&seed=42`）复现出 `refs>0` 仅 **2%**——该策略在中文场景**必须关闭**。
③**语言字段本身不可信且有错代码陷阱**：有语言标注的中文刊论文中仅 5% 标为中文、**92% 标为英文**；
`language:zh-cn` 只返回 16,356 而 `language:zh` 是 5,059,316——**用错代码得到一个「看起来正常」的
小结果集而非报错**。④**国标换版了**：`GB/T 7714—2025` 于 2025-12-02 发布、2026-07-01 实施，
2015 版状态已变为「废止」，而 `zotero-chinese/styles`（6.3k star）README 至今仍写 2015 版——
**引文格式的工具链与国家标准之间存在一个公开的版本裂口**。

**约束了什么**：01-CONTRACTS §3.6（中文获取分层与实测缺口）、§3.6.1（默认分页 ≠ 随机样本）、
§3.7 的 V3.6、flag F-23/F-32；00-PREMISE B7（**押小**：主动声明能力受限，不建全库检索）。

### E 组 · 编排、评测与成本（3 维）

#### §2.E1 `ext-orchestration` — 多 agent 编排模式与上下文/成本经济学

**结论**：**扇出本身不是好事，扇出的拓扑才是**；而唯一一个明确标准化算力的受控评测，
结论是「看拓扑与任务，不看扇出」。

**三个最重要的发现**：①Google Research × MIT 在 **260 个配置 / 6 个基准 / 5 种架构 / 3 个模型家族**上
标准化了工具、提示与算力：相对单 agent 基线从 **+80.8%**（可分解的金融推理）到 **−70.0%**（顺序规划）；
**错误放大 Independent 17.2× > Decentralized 7.8× > Hybrid 5.1× > Centralized 4.4× > 单 agent 1.0×**
（口径是「由 agent 间协调失败引起的额外计算量，从执行轨迹 token 估计」，**不是错误率放大 17 倍**）；
能力饱和阈值：**单 agent 基线已超过约 45% 时，增加 agent 为负收益**。
**限定必须一起带**：R² = 0.373（加 task-grounded capability metric 后 0.413），只解释约三分之一方差。
②**keep-if-better 循环有一个已被测量的失效模式：改一处、退十处**——agent 能落实 >90% 的用户反馈，
但同时在 **16–27%** 的既有内容与引用质量上发生回退，内容反馈下的 break rate 平均 **31%**，
且论文明确说提示工程与「专门的改稿子 agent」两种 inference-time 修法**都解决不了**。
③**上下文治理已收敛到「重建 > 累积」**：IterResearch 的 Markovian workspace 重建在 2048 次交互的极长程上
把成绩从 **3.5% 拉到 42.5%**，作为纯 prompting 策略也能给前沿模型最多 **+19.2pp**。
④Anthropic 那个 token 倍数的口径被普遍讲错：原文分母是 **chat**，不是单 agent。

**约束了什么**：00-PREMISE B1 的裁决与三条硬约束（拓扑 = Centralized + 黑板台账、45% 准入判据、
并行粒度优先级）；01-CONTRACTS §5.3 R-I4（局部消息传递）。

#### §2.E2 `ext-evaluation` — 输出质量评测方法与 LLM-judge 可靠性

**结论**：**LLM-judge 的可靠性数字被系统性高报，根因是报了 raw agreement 而不是 chance-corrected**；
judge 上线门槛必须写成 κ 阈值，不能写成 accuracy 阈值。

**三个最重要的发现**：①一手大规模测量（21 个 judge / 9 家厂商 / 约 541,000 次判定）：MT-Bench 上
exact-match 0.788–0.851 对应的 Cohen κ 只有 0.376–0.511，**raw agreement 平均虚高 38.6 个百分点
（区间 33.8–41.3 pp）**。同一篇提出 **consistency–bias paradox**：test-retest ≥0.95 的 judge 可以同时有
>0.10 的位置偏置——「高度可复现但无效」。
②**广为流传的偏置数量级在一手测量里对不上**：verbosity bias **全部 21 个 judge 均 <0.011**，
其中 17 个 <0.005；而 position bias 跨近两个数量级（0.002–0.192）。那些「15–30 点」的数字来自互相
复述的营销博客，是典型的假独立佐证——**偏置必须自己在自己的 judge 上测**。
③**引用核验是命门而没有模型做得好**：「来源相关性」这一维便宜模型就够（GPT-5-mini F1 = 0.908，
最强且最便宜档之一，judge 成本跨度 49× 而**成本不预测准确率**）；「事实支持」这一维**所有模型
置信区间重叠、统计上不可区分**，最好只有 F1 = 0.750。
④**我们独有且最危险的污染面是 search-time contamination**：实测 HLE 3.36–3.44% / GPQA 1.90–4.15% /
SimpleQA 0.99–1.20% 的样本被检索到评测集本体；**SimpleQA 上被污染样本准确率 100% vs 未污染约 7%**。

**约束了什么**：01-CONTRACTS §1.3（三条量化上界之一与之三）、§1.4.4（Goodhart 防线）、
§6.4（GC-2 的全部边界）、§9.26（held-out）、§9.27、§9.28、§9.29（非对称计分）、§9.4。

#### §2.E3 `ext-cost-economics` — 成本经济学（provider-specific）

**结论**：本轮最大的发现是**一个时间炸弹**——DeepSeek 在 **2026-08-16 16:00 UTC**（即语料写作前约 24 小时）
刚完成全线涨价并改为分时计价，网上几乎所有「2026 年 DeepSeek 定价」文章报的仍是**已作废的旧统一价**。

**三个最重要的发现**：①新价卡是干净的「三的幂」结构，可直接写进代码：
输出 = 缓存未命中输入 × **3**；pro = flash × **3**（CNY 口径精确，USD 因四舍五入有 ±5% 偏差）；
未命中 = 命中 × **30**；峰时 = 谷时 × **2**。
②**DeepSeek 没有 Batch API**（官方文档导航、定价页、限流页三处一致缺失），而 Anthropic/OpenAI/Google
三家都有且都是 50% off——这正是「套用他家数字」最容易踩的坑；DeepSeek 的功能替代品是分时谷时计价
（同样约 2× 杠杆），但**谷时不提供任何吞吐豁免，超限直接 429 且无排队**，因此调度器必须自建。
③**在 DeepSeek 的价格水平上，搜索 API 费用会反超 token 费用成为第一成本项**：
实测一次 deep research 总花费 $1.10，其中 **$0.77（70%）是 77 次网页搜索的调用费**（**n = 1**）。
④谷时占 **17/24 h = 70.8%**，峰时换算北京时间正好是 09–12 与 14–18——重型扇出跑批天然应压在夜里。

**约束了什么**：00-PREMISE B9（成本前提可承受，**中仓位，但基准 24 小时前刚移动**）；
01-CONTRACTS §4 W-13（预算账的写者）与 §4.3（按总量记账的**正确理由**是 DSH 不持有 provider 价目表）、
flag F-24（`pricing-promo` 必须带 `expires_at`）。

### F 组 · 对抗与合规（2 维）

#### §2.F1 `ext-security-injection` — 间接提示注入与证据中毒

**结论**：我们的机制能**结构性消灭「引语层」的一整类攻击**，但对**「内容层」攻击零防护**——
一个被投毒的页面能完美通过逐字匹配。这不是实现缺陷，是**谓词错配**。

**三个最重要的发现**：①**通道分离是本轮实证支撑最扎实的单条设计**：野外普查（1.2B URL / 24.8M host /
15,387 条已验证注入，Common Crawl 2025-10 快照）显示 **10,779 / 15,387 = 70.0%** 的注入落在非渲染通道；
且**抽取表示本身是 20 倍杠杆**——纯文本合规率 3.9%、HTML 标记 1.1%、渲染快照 1.1%、原始 HTTP 响应 0.2%
（5,200 次试验 = 100 提示 × 4 表示 × 13 模型）。野外已有 **542 条明确的「强制引用」注入**，
**这正是我们被瞄准的形态**。
②**不要把「检测注入」当主防线**：真实注入 **>90% 不含显式指令**（约 20 万份真实简历普查，约 1% 含隐藏注入）；
困惑度检测 AUROC ≤ 0.68 **且方向是反的**（注入文本困惑度一致地低于自然 UGC）。
③**「多源交叉验证」这条支柱本身可攻击**：合成共识模式在 Gemini-3-Flash 上 ASR 达 **73%**；
且判为「攻击失败」的案例中仍有 **15.0%** 输出语义漂移 Δ≥0.3。
④**攻击面不止在读网页，还在拆命题**：input-only 威胁模型（只改 claim 措辞、不碰语料）对三套
搜索增强事实核查系统拿到 ASR **18.8%–31.4%**。⑤官方口径给我们的威胁模型背书：
OWASP LLM01:2025 逐字写「it is unclear if there are fool-proof methods of prevention」。

**约束了什么**：01-CONTRACTS §0.3（承诺两件、不承诺第三件）、§0.4（模型侧能力假设为零）、
§1.1（谓词错配的论证）、§1.4.2、§5.5、flag F-13/F-14/F-15/F-16/F-17/F-22/F-31、§7.2.2 的通道分离硬约束
与 RT-4/RT-5/RT-6/RT-8；00-PREMISE B5（四类结构性消灭、**八类明写不防**）。
**这是被 01-CONTRACTS 引用次数最多的一维（34 次）。**

#### §2.F2 `ext-legal-tos` — 抓取、存储与再分发的法律/ToS 层

**结论**：法律风险的重心已经从「**用了什么**」移到「**怎么拿到的**」。

**三个最重要的发现**：①Bartz v. Anthropic 把取得渠道和下游用途彻底切开：训练本身
"spectacularly transformative"，但从盗版站下载并留存这一步被判 "inherently, irredeemably infringing
even if the pirated copies are immediately used for the transformative use and immediately discarded"；
判词还点名 "The library copies lacked internal controls limiting access and use."——
**本地语料库缺访问控制本身就是被写进判词的减分项**。
②**机读偏好标准三足鼎立，但三家都明确说自己不产生法律效力**（IETF AIPREF 原话
"Preferences do not themselves create rights, obligations, or prohibitions"）；
**唯一被准官方文件写死为必须遵守的是 robots.txt（RFC 9309）**。
③**出版商 TDM 授权允许的是「项目期内本地留存 + 极短摘录对外」，不允许长期语料库**：
Elsevier 的对外 snippet 上限 **200 字符**「围绕且不含匹配实体本身」+ 必须附 DOI 回链；
Springer Nature 与 Wiley 形状相同。
④**Cloudflare 2026-09-15 会改默认值**：对新接入域名等，在展示广告的页面上默认阻断 Training 与 Agent、
放行 Search，多用途爬虫按最严格类别判定。⑤见 §1.3 U1 的关门样本清单。

**约束了什么**：01-CONTRACTS §8.6（留存分档三档）、§8.6.1（摘录硬上限）、§8.6.2、§8.6.3（14 个降级触发器）、
§8.6.4（`T12-UNREACHABLE` 同时是口径纪律）、§8.6.5、§8.6.6、flag F-33/F-34/F-35。
**该维度自陈「本文是工程设计输入，不是法律意见」，该免责已被 01-CONTRACTS §8.6 末尾整体继承。**

---

## §3 载荷数字总表

### §3.1 表的读法（列定义与选录规则）

| 列 | 含义 |
|---|---|
| **数字** | 载荷值本身。多值行用 `/` 分隔并在口径列说明各值对应什么 |
| **口径三元组** | `指标 / 样本或档位 / 对比基准`（术语见 01-CONTRACTS §9.4）。**缺任一项的数字不得进入本表** |
| **状态** | `verified` / `corrected` / `unverified` / `vendor-reported` / `flagged`，取自语料原判，**本文件不改判** |
| **一手出处** | 语料记录的一手来源（论文 ID、官方页、实测命令）。完整 URL 在语料内，本表只给可定位标识 |
| **as-of** | **数据本体的日期**，不是采集日。采集日全部为 2026-08-17。两者不同时以本体日期为准 |
| **消费方** | 撰写本文件时（2026-08-17）已知引用该数字的 v2 文档。`—` 表示两份已成文文档均未引用，**不表示不重要** |

**选录规则**〔裁定〕：全表 **784 行**仍在语料内，本表**不是它的全量转录**，收录三类：
（a）已被 `00-PREMISE.md` 或 `01-CONTRACTS.md` 引用的；
（b）状态为 `corrected` 或 `unverified` 的（安全上必须集中列出）；
（c）会直接进入代码默认值的硬约束（限速、价格、阈值、许可门槛）。
其余行**按维度给出定位指针**（每节标题即 `research/v2/<file>.md#载荷数字核验表`），不隐藏。
**什么会推翻这条裁定**：若下游文档在本表之外引用了语料数字，则说明选录规则漏了一类，
本表必须扩表。该情况可由一条 lint 检出：**对每份下游文档中出现的数字，
若它在语料某张核验表里存在、却不在本表中，即报警。**
（该 lint 尚未实现——按 §7 第 5 条的同一理由，**在它落地之前这条裁定是纪律不是机制**。）

**消费方列可机器校验，且已跑过一次**：对每个 `01-CONTRACTS §x` / `00-PREMISE Bx` 标注，
在对应文件中 grep 该数字串应有命中；命中为 0 即本表该行标注错误。
**2026-08-17 实跑结果：约 100 个探针，查出 15 处过度声称，已全部改为 `—` 并在 §7 第 3 条记账。**
该校验的已知盲点（数字串写法差异导致的漏判）同样记在 §7 第 3 条。

### §3.2 主表

#### §3.2.1 学术检索与全文获取 `[E: ext-academic-apis.md#载荷数字核验表]`

| 数字 | 口径三元组 | 状态 | 一手出处 | as-of | 消费方 |
|---|---|---|---|---|---|
| OpenAlex works **324,389,590** | works 总数 / **API 默认口径（排除 XPAC）** / vs `corpus=all` 的 516,949,125 | verified（实测） | `api.openalex.org/works` | 2026-08-17 | 01-CONTRACTS §3.2 |
| `is_oa:true` **123,672,025（38.1%）** | OA 论文数与占比 / 分母为默认口径 324.4M / — | verified（实测） | 同上 filter | 2026-08-17 | 01-CONTRACTS §3.2 |
| `has_content.pdf` **54,999,764（17.0%）** | 有缓存 PDF 的论文数与占比 / 分母同上 / vs 官方"50M+" | verified（实测） | 同上 + fulltext 页 | 2026-08-17 | 01-CONTRACTS §3.2, §3.4 |
| 单实体 lookup **$0 / 0 credit** | 每次调用成本 / `/works/{id}` / vs list $0.0001 | verified（实测响应头） | `x-ratelimit-credits-used: 0` | 2026-08-17 | — |
| 免费额度 **$1/天**；无 key **$0.10/天** | 每日 API 美元预算 / 注册免费档 vs 匿名档 / 10× | verified（文档+实测） | help.openalex.org/access/pricing（页面 2026-08-11 更新） | 2026-08-11 | — |
| 语义检索 **1 rps、最多 50 条、2000 字符** | 端点级限制 / semantic search / vs 常规 100 rps | verified | help.openalex.org/api/semantic-search | 2026-08-17 | 01-CONTRACTS §6.3-5 |
| OpenAlex 硬上限 **100 rps** | 每秒请求上限 / 全档位统一 / — | verified | help.openalex.org/api/authentication | 2026-08-17 | 01-CONTRACTS §6.3-5 |
| **arXiv 1 请求 / 3 秒，单连接** | 请求频率上限 / API + OAI-PMH + RSS 全适用 / **全信源最严** | verified | info.arxiv.org/help/api/tou.html | 2026-08-17 | 01-CONTRACTS §6.3-5, §8.6.3 T9 |
| Crossref polite **列表 3 rps / 单条 10 rps，并发 3** | 每秒请求上限 / polite pool，区分单条与列表 / vs public 1 & 5 | verified（文档+实测头） | crossref.org 文档页 + `x-rate-limit-limit: 3` | 2026-08-17 | 01-CONTRACTS §6.3-5 |
| Semantic Scholar 有 key **1 rps**（措辞 "introductory"） | 每秒请求上限 / 个人 key 全端点 / vs 无 key 实测 429 | verified（**措辞不稳定**） | semanticscholar.org/product/api | 2026-08-17 | 01-CONTRACTS §6.3-5 |
| CORE 免注册 **5 单请求 / 10 秒（≈0.5 rps）** | 请求频率上限 / 未注册档 / — | verified（文档） | core.ac.uk/services/api | 2026-08-17 | 01-CONTRACTS §6.3-5 |
| NCBI **3 rps 无 key / 10 rps 有 key** | 每秒请求上限 / 有无 api_key 两档 / — | verified | ncbi.nlm.nih.gov/books/NBK25497 | 2026-08-17 | 01-CONTRACTS §6.3-5 |
| DOAJ **2 rps，突发队列 5** | 每秒请求上限 / 全部 API 路由 / — | verified | doaj.org/api/docs | 2026-08-17 | 01-CONTRACTS §6.3-5 |
| **Unpaywall = OpenAlex 同一后端** | 数据来源关系 / OA 状态字段 / — | verified（文档+实测返回 `"evidence":"deprecated"`） | help.openalex.org/access/unpaywall | 2026-08-17 | 01-CONTRACTS §5.5, V5.4 |
| 内容档案 **50M+ PDF ~250TB / ~43M TEI ~20TB**；单篇 **$0.01**，免费档 **~100 篇/天** | 文件数与体积 / 单价 / 日额度 | verified（文档，未实扣） | help.openalex.org/access/fulltext | 2026-08-17 | 01-CONTRACTS §3.3（G5 获取路径） |
| GROBID 参考文献 **~0.87 F1** | F1 / **PMC 独立集 1,943 篇 PDF、90,125 条参考文献** / bioRxiv 同类集 ~0.90 | verified | github.com/kermitt2/grobid | 2026-08-17 | — |
| GROBID **~10.6 PDF/秒（~915k/天）** | 吞吐 / **16 核机器、full-text 模式** / — | verified（**16 核口径，非单核**） | 同上 | 2026-08-17 | — |
| OmniDocBench v1.6：MinerU2.5-Pro **95.75** / Marker **78.44** / MinerU-Pipeline **86.47** | Overall / **v1.6_full，1,651 页、10 类文档、5 语言** / **同一把尺子** | verified（第三方同框，**唯一可比口径**） | github.com/opendatalab/OmniDocBench | 2026-08-17 | — |
| MinerU 商用门槛 **100M MAU 或月营收 $20M** + **强制署名** | 许可触发条件 / MinerU Open Source License（3.1.0 起） / vs 1.x AGPLv3 | verified | MinerU LICENSE.md | 2026-03-29（版本变更日） | — |
| marker **权重**免费门槛 **$5M 融资/营收** | 许可阈值 / **模型权重**（非代码，代码 Apache-2.0） / vs 2025 年的 $2M | verified | marker README + datalab.to/blog/introducing-lift | 2026-06-18 | — |

#### §3.2.2 通用检索/抓取供应商 `[E: ext-web-providers.md#载荷数字核验表]`

> **本节全部行的消费方为 `—`**：该维度尚未被任何 v2 成文文档引用（见 §6.4）。
> **节流单位互不可比**：QPS / RPM / 并发浏览器数 / 每小时配额是四种不同的东西，**不得合表比较**。

| 数字 | 口径三元组 | 状态 | 一手出处 | as-of |
|---|---|---|---|---|
| serper Starter **50 QPS**；Standard/Scale/Ultimate **100/200/300 QPS** | 每秒查询数 / 四档 / — | verified | serper.dev 首页定价卡（浏览器实读） | 2026-08-17 |
| serper **$1.00 / 1k**（$50 / 50k credits，credits **6 个月过期**） | 每千 credit 价 / Starter 充值档 / vs SerpApi Starter $25/1k | verified | 同上 | 2026-08-17 |
| Tavily Production **1,000 RPM** / Development **100 RPM**；`/crawl` 100 / `/research` 20 RPM | 每分钟请求数 / **环境而非计划决定** / — | verified | docs.tavily.com/documentation/rate-limits | 2026-08-17 |
| Tavily **无官方 QPS、无官方并发数** | 指标缺失 / 官方 rate-limit 页 / — | verified（确认「未发布」） | 同上 | 2026-08-17 |
| Exa `/search` **10 QPS**；`/contents` **100 QPS**；`/answer` 10 QPS | 每秒查询数 / 全体非 Enterprise / — | verified | exa.ai/docs/reference/rate-limits | 2026-08-17 |
| Firecrawl 并发浏览器 **2 / 5 / 50 / 100 / 150** | **同时在跑的浏览器数（≠RPM）** / Free…Scale 五档 / — | verified | docs.firecrawl.dev/rate-limits + pricing.md | 2026-08-17 |
| Jina `r.jina.ai` **20 / 500 / 500 / 5000 RPM** | 每分钟请求数 / 无 key / Free / Paid / Premium key / — | verified | jina.ai/reader 限速表（浏览器实读） | 2026-08-17 |
| Brave Search **50 QPS**；Answers **2 QPS** | 每秒查询数 / 两个计划 / — | verified | brave.com/search/api CAPACITY 字段 | 2026-08-17 |
| SerpApi **50 / 200 / 1,000 / 3,000 / 6,000 / 20,000 / 50,000 / 100,000 次每小时** | **每小时配额（≠瞬时并发）** / 八档 / 每小时 = 月额度的 20% | verified | serpapi.com/pricing | 2026-08-17 |
| SerpApi Production **≈0.83 QPS 均值** | 由 3,000/小时折算 / Production 档 / vs serper Starter 50 QPS | verified（派生）；**运营含义 unverified** | 3,000÷3,600 | 2026-08-17 |
| Brave：**存储 API 结果需订阅显式授予存储权的计划**，通用 ToS 不覆盖 | 许可条件 / Search 计划 / — | verified | brave.com/search/api FAQ | 2026-08-17 |
| Jina 免费 **10M tokens = CC-BY-NC 仅非商业** | 授权口径 / Toy Experiment 档 / 付费档无此限 | verified | jina.ai/reader 定价卡原文 | 2026-08-17 |
| **Firecrawl Research Index（论文）= Free（0 credit）** | credit 消耗 / `GET /search/research/papers` / vs `/search` 2 credits/10 结果 | verified（两处官方提及）；**字段契约 unverified**（features 页 404） | pricing.md + api-reference/endpoint/search | 2026-08-17 |
| SerpApi 缓存 **1 小时，命中免费且不计入月额度**；Legal Shield 最高 **$200 万**（Production 及以上） | 缓存 TTL 与计费 / 保额与档位 / — | verified | serpapi.com/search-api + /pricing | 2026-08-17 |
| Jina AI 已并入 **Elastic**（页脚实读 `Elastic © 2020-2026`） | 公司归属 / jina.ai 页脚与侧栏 / — | verified（实读） | jina.ai | 2026-08-17 |

#### §3.2.3 文献污染筛查与取证统计 `[E: ext-literature-integrity.md#载荷数字核验表]`

| 数字 | 口径三元组 | 状态 | 一手出处 | as-of | 消费方 |
|---|---|---|---|---|---|
| RW CSV **71,799 行** | 全部数据行（含 Retraction+Correction+EoC+Reinstatement）/ 全库 / 对治「71,799 = 撤稿数」这一误读 | verified（自算） | gitlab.com/crossref/retraction-watch-data | 2026-08-14（README 数据生成日） | 01-CONTRACTS §6.3.1 |
| 其中 `RetractionNature == "Retraction"` **66,287 行** | 撤稿类记录数 / 同上（另 EoC 3,586 / Correction 1,502 / Reinstatement 160 / 空 264）/ — | verified（自算） | 同上 | 2026-08-14 | 01-CONTRACTS §6.3.1, flag F-05 |
| 去重原文 DOI **62,708 个** | 去重后 `OriginalPaperDOI` 数（65,589 行有非空 DOI）/ 同上 / — | verified（自算） | 同上 | 2026-08-14 | 01-CONTRACTS §6.3.1 |
| OpenAlex `is_retracted:true` **134,175** | works 数 / 全库 324,389,590 / 约为 RW 撤稿数的 **2 倍** | verified（live API） | `api.openalex.org/works?filter=is_retracted:true` | 2026-08-17 | 01-CONTRACTS §6.3.1 |
| 抽样归因 **81 / 69 / 42 / 6 / 2（n=200）** | `is_retracted:true` 随机 200 条：被撤原文 81（40.5%）/ **撤稿公告本身 69（34.5%）** / 标题形如 Retraction 但 RW 无记录 42 / … | verified（自测） | 同上 + RW CSV 比对 | 2026-08-17 | 01-CONTRACTS §6.3.1 |
| Crossref `update-type:retraction` **74,607** | works 数 / 含 publisher 与 retraction-watch 双来源，**未去重** / vs RW 66,287 | verified（live API） | api.crossref.org | 2026-08-17 | 01-CONTRACTS §6.3.1（去重要求） |
| 劫持刊表 **456 条** | 数据行数 / RW Hijacked Journal Checker，表头自述 "last updated July 17, 2026" / vs 二手「400 条」「450+」 | verified（自测） | docs.google.com 导出 xlsx | 2026-07-17 | 01-CONTRACTS flag F-07 |
| PPS tortured 指纹词典 **8,282 条** | **指纹条数**（CSV 8,283 行含表头）/ 页面更新戳 2026-08-13 / **不是被标记论文数** | verified（自测下载） | dbrech.irit.fr PPS 导出 | 2026-08-13 | **—**（§6.2 引用 PPS 机制，未引用该数字） |
| GRIM 功率 `power = max(0, 1 − N·items / 10^d)` | 检出功率闭式解 / 单题项、两位小数、随机错误均值；**20,000 次/点蒙特卡洛验证**（N=28 实测 0.718 vs 理论 0.720；**N≥100 且 d=2 时恒为 0**）/ — | verified（自算+仿真） | 语料 §E1 | 2026-08-17 | 01-CONTRACTS §6.2.1, flag F-21 |
| statcheck **96.2%–99.9%** 总准确率 | 与人工编码的一致 / **48 篇 / 1,120 条**人工编码，仅完整 APA 的 t/F/χ² 且 p<.05，**且只在人机都抽到的交集上算** / 敏感度 85.3–100%、特异度 96.0–100% | verified（一手 PDF） | Nuijten 等 validity 预印本 | — | 01-CONTRACTS §6.2.2 |
| statcheck **抽取召回率 61.1%–61.2%** | 1,120 条中只抽到 684/685 / 同上样本 / **上一行的区间是在这 61% 的交集上算的** | verified（一手 PDF） | 同上 | — | 01-CONTRACTS §6.2.2 |
| 现场 flag 构成 **14 / 64 / 113（20 篇，737 条）** | 20 篇 737 条 NHST 中 113 条被标记；14 条抽取错误、**64 条（57%）源于统计校正** / 2024 准实验 / — | verified | 语料 §E5 | 2024 | 01-CONTRACTS §6.2.2, flag F-19 |
| Cabells **20,274 本**期刊；DOAJ **23,320 本** | 掠夺性名录规模 / 白名单规模 / 互为参照 | verified | Cabells 博客 2026-02-03；DOAJ live API | 2026-01-30 / 2026-08-17 | **—**（F-08 引用 Cabells，未引用该数字） |
| STM Integrity Hub **40 家出版商 / 12.5 万篇每月 / ~1,000 篇拦截每月** | 参与数与筛查量 / 协会自述 / — | verified（协会自述，无独立核验） | 2025-12-08 行业刊物 | 2025-12-08 | 01-CONTRACTS §6.1（T2 不可作门） |
| 标准化撤稿率 Elsevier **3.97/万篇** vs Hindawi **320.02/万篇** | 撤稿率 / 10 家出版商 46,087 条撤稿，基于 RW 库 1997–2026 / 跨两个数量级 | verified（摘要） | arXiv:2602.19197 | 2026-02 | — |

#### §3.2.4 引用忠实度与判定器 `[E: ext-citation-faithfulness.md, ext-verification-mechanisms.md, ext-evaluation.md]`

| 数字 | 口径三元组 | 状态 | 一手出处 | as-of | 消费方 |
|---|---|---|---|---|---|
| **链接可达 >94% / 主题相关 >80% / 事实核查 39–77%** | 三层指标 / 130 条 query（DeepResearch Bench + BrowseComp），14 个模型，引文用确定性 Markdown AST 抽取 / 同一批引文 | verified（arXiv 预印本，PwC 产业实验室） | arXiv:2605.06635v1 | 2026-05-07 | 01-CONTRACTS §2.2.3；00-PREMISE B1 |
| **GPT-5.4 78.6% → 16.7%**（Claude Opus 4.6 80.0% → 57.9%） | Fact-Check 通过率 / 工具调用 7 档 2/10/30/50/70/100/150 / **同实验中 Link Works 与 Relevant Content 始终 >92%** | verified（预印本；**未报相关系数/回归/p 值**） | 同上 | 2026-05-07 | 01-CONTRACTS §2.2.3；00-PREMISE B1 |
| **−42.0 个百分点**（两模型绝对降幅均值；相对降幅均值约 53%） | 降幅口径 / 同上 / **原文写 "approximately 42%"，两模型降幅相差近 3 倍** | **corrected** | 同上（本轮核算） | 2026-05-07 | 00-PREMISE B1 |
| **95.1%** | 原本不被支持的陈述，合并**全部**被引源后仍不被支持的比例 / GPT-4o(RAG) 的不支持陈述子集 / — | verified | Nat Commun 16:3615 | 2025-04-16 | 01-CONTRACTS §2.2.3 |
| **50%–90%** | **response-level 未完全支持率** / 800 医学问题、约 58,000 对陈述-源 / 跨 7 个模型的**范围** | verified | 同上 | 2025-04-16 | 01-CONTRACTS §2.2.3（间接） |
| **F1 = 0.750**（Claude Opus 4.6，最好者） | 「引文是否支持断言」维的 F1 / 624 对 = 1,248 条 rubric 决策 / **所有模型置信区间重叠、统计上不可区分** | verified | arXiv:2607.08700 | 2026-07-09 | 01-CONTRACTS §1.3-1, §6.4 |
| **F1 = 0.908**（GPT-5-mini） | 「来源相关性」维的 F1 / 同上 / **最强且属最便宜档；judge 成本跨度 49×，成本不预测准确率** | verified | 同上 | 2026-07-09 | 01-CONTRACTS §6.4 |
| **378 / 624 = 60.6%** | 有分歧并被人工裁决的对数 / 同上 / — | verified | 同上 | 2026-07-09 | 01-CONTRACTS §6.4 |
| **EM 0.788–0.851 vs κ 0.376–0.511；虚高均值 38.6 pp（区间 33.8–41.3）** | raw exact-match 一致率 vs Cohen κ / **MT-Bench，21 个 judge / 9 家厂商 / 约 541,000 次判定** / raw vs chance-corrected | verified | arXiv:2606.19544v1 | 2026-06-17 | 01-CONTRACTS §1.3-3, §6.4, V9.4 |
| **verbosity bias 全部 <0.011（17 个 <0.005）；position bias 0.002–0.192** | 偏置量级 / 同上 21 个 judge / **与流传的「15–30 点」直接冲突** | verified | 同上 | 2026-06-17 | 01-CONTRACTS §6.4 |
| **test-retest 0.943 → 0.911；16 个 judge 中 7 个位置翻转率退化 ≥1.5×** | 重测信度 / MT-Bench → JudgeBench（更难） / — | verified | 同上 | 2026-06-17 | 01-CONTRACTS §6.4 |
| **MiniCheck-FT5 74.7 / Bespoke-Minicheck-7B 77.4** | 平均 balanced accuracy / LLM-AggreFact **10 个**（论文）vs **11 个**（leaderboard）数据集 / **跨版本数字不可直接比** | verified | arXiv:2404.10774v1；llm-aggrefact leaderboard | 2026-08-17（榜单抓取日） | 01-CONTRACTS §1.3-2 |
| **80.01 → 71.11 BAcc** | 分解代价 / MiniCheck 在 WiCE claim-level，FActScore 式分解 / vs 不分解基线 | verified | arXiv:2411.02400v1 | — | 01-CONTRACTS（未直接引，机制见 §6.1） |
| **FActScore 逐条 F1-micro 53.3%–83.2%** | 逐条原子事实判定 / Inst-LLAMA + retrieval + NP，三种被评模型 / 与人工逐条标注比 | verified | arXiv:2305.14251 附录 B.2 | — | — |
| **agentic 查证召回 0.98–0.99、FPR 0.431–0.478**；规则型 bibtex-updater **0.865 / 0.092** | 检出率与假阳率 / HALLMARK 全集 / 互比 | verified（**仅 HTML 路径**） | arXiv:2607.18360（HTML） | 2026-07 | — |
| **非解析率 5.4–18.5%；幻觉率 3.0–13.3%** | non-resolving（4xx/5xx/超时，403 排除）与 hallucinated（且 Wayback 无快照）/ DRBench 10 个模型 53,090 条 URL / — | verified（预印本） | arXiv:2604.03173v1 | 2026-04-03 | — |
| **16.0% → 0.6%（26×）** | GPT-5.1 的 non-resolving URL 率，给予 `urlhealth` 自纠错前后 / 435 个 ExpertQA 问题 / 均 p<10⁻³⁵；**小模型无法利用反馈** | verified（预印本） | 同上 | 2026-04-03 | — |
| **Toulmin warrant 有无检测 加权 F1 0.88** | 全类别加权 F1 / 三子集 100/1,026/211 条回答，**教育对话语料、传统 ML 分类器** / — | verified；**域外，且只判 warrant 有无** | aclanthology P19 系；语料 §M14 | — | 01-CONTRACTS §2.3.1 |
| **ARCT：BERT 峰值 77%，低人类基线 3 点；对抗集退化到随机** | 准确率 / ARCT 测试集 / **被证明完全由伪统计线索解释** | verified | aclanthology.org/P19-1459 | 2019 | 01-CONTRACTS §2.3.1 |
| **search-time contamination：HLE 3.36–3.44% / GPQA 1.90–4.15% / SimpleQA 0.99–1.20%** | 检索命中评测集本体的样本占比 / 三基准 / **SimpleQA 上被污染样本准确率 100% vs 未污染约 7%** | verified | arXiv:2508.13180v1 | 2025-08-12 | 01-CONTRACTS §9.27 |

#### §3.2.5 图表/表格数值证据 `[E: ext-multimodal-evidence.md#载荷数字核验表]`

| 数字 | 口径三元组 | 状态 | 一手出处 | as-of | 消费方 |
|---|---|---|---|---|---|
| **标签 Macro-F1 88.4 / 关键单元格 Macro-F1 34.8** | GPT-4o 在 SciTabAlign 上的两个指标 / SciTab 扩展 / **exact-match 设定下无任何模型能让「标签+依据同时正确」超 50%** | verified | EMNLP 2025 Findings（SciTabAlign） | 2025 | 01-CONTRACTS §3.4.2 |
| **MAPE 1.3%–1.8%（有标签）→ 7.2%–7.4%（无标签）** | 数值读取误差 / **同一模型 Gemini 2.5 Flash、同一批 50 张 Vega-Lite 图，只改标签** / 互比 | verified | 语料 §B（#11/#12） | 2026 | 01-CONTRACTS §3.5 |
| 分族 Adaptive MAPE：scatter **2.63** / bar **3.78** / line **4.35** / pie **11.58** / radar **28.01** | 数值读取误差 / ExChart-Bench，同一模型 / 族间互比 | verified | 语料 §（#14） | 2026 | 01-CONTRACTS §3.5（图族黑名单） |
| **结构正确率 194/200（97.0%）** 而同批无标签图数值 MAPE >7% | 表结构生成正确率 vs 数值误差 / 200 张 ChartQA 图 / **结构正确率不得作为任何验证信号** | verified | 语料 §C | 2026 | **—**（§3.4.2 用的是 88.4/34.8 那一对，不是本行） |
| 自洽性与准确率 **Spearman ρ = −0.30 ~ −0.37**（p<0.001） | 抽样离散度与抽取准确率的相关 / WB-ChartExtract / **解释方差仅约 9%–14%** | verified | 语料 §C | 2026 | 01-CONTRACTS（未直接引；机制见 §6.1 GC-2 边界） |
| 遗漏占错误类型 **60%–74%**；幻觉率 **0.08%–6%** | 错误结构分布 / 27 项研究的系统综述 / — | verified | 语料 §G（2026-07 综述） | 2026-07 | 01-CONTRACTS（未直接引） |
| 人机协作天花板 **~0.85–0.91** | 抽取准确率 / 三条独立证据线（Claude 3.5 Sonnet 91.0% [90.4–91.6]；AutoForest 82.5%→90.2%；LEADS 0.85 vs 0.80）/ 纯人工 89.0% | verified | 语料 §G | 2026 | — |
| ChartQA **90.5%** vs ChartQAPro **55.81%**（同一 Claude Sonnet 3.5） | 准确率 / 干净基准 vs 真实难度基准 / **同一模型** | verified | 语料 §A | 2025–2026 | **—**（§9.13 的实例是 OmniDocBench 与 DABstep） |
| TEDS 与人类判断相关仅 **r = 0.68**（同研究 LLM-as-judge r = 0.93） | 指标效度 / 表格结构评测 / — | verified | 语料 §D | 2026 | 01-CONTRACTS（未直接引） |

#### §3.2.6 注入与证据中毒 `[E: ext-security-injection.md#载荷数字核验表]`

| 数字 | 口径三元组 | 状态 | 一手出处 | as-of | 消费方 |
|---|---|---|---|---|---|
| **10,779 / 15,387 = 70.0%** 注入在非渲染通道 | 条数占比 / HTTP 头 7,887 + 结构化数据 1,996 + 注释 675 + meta 221 / 渲染元素 4,608（30.0%） | verified（分项加总闭合） | arXiv:2604.27202 | **Common Crawl 2025-10 快照** | 01-CONTRACTS §7.2.2 |
| 普查规模 **1.2B URL / 24.8M host / 15,387 条已验证注入** | 计数 / CC-MAIN-2025-43 约半个语料 + Censys + Shodan / — | verified | 同上 | 2025-10 | 01-CONTRACTS §7.2.2 |
| 合规率 纯文本 **3.9%** / HTML **1.1%** / 渲染快照 **1.1%** / 原始 HTTP **0.2%** | 模型执行注入指令的比例 / **5,200 次试验 = 100 提示 × 4 表示 × 13 模型** / 表示间互比（**20 倍杠杆**） | verified | 同上 | 2025-10 | 01-CONTRACTS §7.2.2 |
| **强制引用（citation forcing）542 条** | 意图分类条数 / 同一 15,387 条集合（声誉操纵 1,521 条之一）/ **三大类相加 20,453 > 15,387，疑为多标签** | verified（分项）；多标签性质 unverified | 同上 | 2025-10 | 01-CONTRACTS §7.2.2 |
| **约 13 词**即可达平台期 | 最短投毒长度 / 单簇消融（8 词 15–43%、13 词 72–100% 条件提及率）/ — | verified | arXiv:2605.24245v1（WARP） | 2026-05 | 01-CONTRACTS §3.4.1 |
| **38–51%** 提及率 | **曝光条件下**的提及率，SERP 摘要场景、单个投毒 URL / 被攻击对象是 **STORM / Co-STORM / OmniThink 三个开源流水线** / 无条件提及率 21.7% | verified | 同上 | 2026-05 | 01-CONTRACTS §3.4.1 |
| UGC 引用率 OpenAI DR **0.4%** vs Gemini DR **12.1%**（差 30×） | 最终报告中被引 URL 里 UGC 的占比 / WARP 侦察集 / 开源三系统 16.9–18.9% | verified | 同上 | 2026-05 | 01-CONTRACTS §7.2.1 |
| 屏蔽 UGC 的质量代价：rubric **4.30 → 4.26**，每查询只移除 **2.1 个** UGC URL | 质量分与移除量 / WARP 实测 / — | verified；**我们采信其数据而非其结论语气** | 同上 | 2026-05 | 01-CONTRACTS §7.2.1（含误读风险自陈） |
| 困惑度检测 **AUROC ≤ 0.68**，且注入文本困惑度**低于**自然 UGC | 检测器判别力 / WARP 三种注入方法 / 随机基线 0.5 | verified | 同上 | 2026-05 | 01-CONTRACTS §7.2.2 |
| 简历中约 **1%** 含隐藏注入；**>90%** 不含显式指令 | 普查占比 / hireEZ 约 **20 万份**真实简历，跨多年 / — | verified | arXiv:2605.28999 摘要 | 2026-05 | 01-CONTRACTS §7.2.2, V7.6 |
| 合成共识 ASR **73%**（Gemini-3-Flash）；该后端整体 ASR 31.4%；Claude-Sonnet-4.6 **0.0%** | 背书腐化 ASR / **44 query × 4 领域 × 13 后端 = 6,000+ 案例** / 后端互比 | verified | arXiv:2606.16821v2（SearchGEO） | 2026-06 | 01-CONTRACTS §1.5.2 |
| 判为「攻击失败」的案例中仍有 **15.0%** 语义漂移 Δ≥0.3 | 静默漂移率 / Mode 3（复合层）/ 二元 ASR | verified | 同上 | 2026-06 | 01-CONTRACTS §1.4.2, §9.16 |
| input-only ASR **19.5% / 18.8% / 31.4%** | 事实核查判定被翻转的比例，**只改 claim 措辞、不碰语料** / HiSS / LEMMA / DEFAME，MOCHEG 1,642 条 / 干净准确率 77.5%/66.1%/… | verified | arXiv:2602.02569（DECEIVE-AFC） | 2026-01-31 | **—**（F-13 的指针是 #D4/#V16） |
| **8 个已发表 IPI 防御全被自适应攻击绕过，ASR 持续 >50%** | ASR / 8 个防御 / 各自宣称的低 ASR | verified | Findings of NAACL 2025 | 2025 | 01-CONTRACTS §0.3 |
| 现有防御只覆盖 **53 个攻击中的 13 个** | 综述统计 / 自动事实核查全部攻击类别 / — | verified | arXiv:2509.08463（EMNLP 2025 Main） | 2025 | — |
| 局部消息传递 ASR 低约 **20%**；自复制注入 GPT-4o **+13.92%** / GPT-3.5 **+209%** | ASR 相对差 / **5–6 智能体串行链 + 10–50 智能体社会模拟** / 全局消息传递 | verified | 语料 §V26 | — | 01-CONTRACTS §5.3 R-I4 |
| DeepSeek **100% / 70.27% / 39.7%** | **越狱/有害提示拒答口径，非 IPI** / R1、V3；**均非 v4-pro/v4-flash** / 各自参照模型不同 | verified 为各自口径；**作为「抗注入能力」是 corrected——口径不适用** | blogs.cisco.com 等三家 | 2025-01-31 起 | 01-CONTRACTS §0.4 |

#### §3.2.7 编排、评测与成本 `[E: ext-orchestration.md, ext-evaluation.md, ext-cost-economics.md]`

| 数字 | 口径三元组 | 状态 | 一手出处 | as-of | 消费方 |
|---|---|---|---|---|---|
| **+80.8% ~ −70.0%** | 相对单 agent 基线的成绩变化 / **260 配置 / 6 基准 / 5 架构 / 3 模型家族，标准化工具·提示·算力** / 端点为可分解金融推理 vs 顺序规划 | verified | arXiv:2512.08296 v3 | 2026-04-08 | 00-PREMISE B1 |
| 错误放大 **Independent 17.2× > Decentralized 7.8× > Hybrid 5.1× > Centralized 4.4× > 单 agent 1.0×** | **由 agent 间协调失败引起的额外计算量，从执行轨迹 token 估计**（**不是错误率放大 17 倍**）/ 同上 / 互比 | verified | 同上 | 2026-04-08 | 00-PREMISE B1 |
| 能力饱和阈值 **约 45%** | 单 agent 基线超过该值后增加 agent 为负收益 / 同上；**R² = 0.373（加 capability metric 后 0.413）** / — | verified；**待标定参数** | 同上 | 2026-04-08 | 00-PREMISE B1（准入判据） |
| **180 / 4 / +80.9%** | 同三项，但取自 **Google 博客版**（较早版本）/ vs 现行 260/6/+80.8% / — | **corrected（版本漂移）** | research.google 博客 | 2026-01-28 | 00-PREMISE B1 |
| **16–27% 回退；内容反馈下 break rate 平均 31%** | 多轮改稿中在既有内容与引用质量上的回退比例 / 5 个 DRA、Mr Dre 评测套件 / 落实反馈 >90% | verified | ACL 2026 long.609 | 2026 | 00-PREMISE（B1 相关）；01-CONTRACTS 未直接引 |
| **3.5% → 42.5%**（2048 次交互）；纯 prompting 最多 **+19.2pp** | 长程成绩 / IterResearch Markovian workspace 重建 / vs 单一膨胀上下文 | verified | arXiv:2511.07327（ICLR 2026） | 2026 | 00-PREMISE B1（上下文卫生） |
| 子 agent 压缩比：烧「数万 token」，回传 **1,000–2,000 token** | 上下文压缩量级 / Anthropic 多 agent 研究系统 / — | verified（逐字） | anthropic.com/engineering/multi-agent-research-system | 2025-06 | 00-PREMISE B1 |
| **agents ≈ 4× chat；multi-agent ≈ 15× chat** | token 总量倍数 / Anthropic 自家 Research 系统，BrowseComp / **基线是 chat，不是单 agent** | verified（逐字），**已 14 个月** | 同上 | 2025-06 | 00-PREMISE B1, B9 |
| **多智能体 ≈ 单 agent 的 3.75×（15/4），不是 15×** | 倍数换算 / 同上 / 单 agent | **corrected** | 由上一行推导 | 2025-06 | 00-PREMISE B9 |
| **token 用量单独解释 80% 方差**（三因子合计 95%） | 方差解释率 / **BrowseComp 评测上的方差分解，不是那个拿 90.2% 的内部 eval** / — | verified（逐字） | 同上 | 2025-06 | 00-PREMISE B1 |
| **90.2%** | 多智能体相对单智能体 Opus 4 的提升 / **Anthropic 内部研究评测（未公开、样本量未披露）** / — | **flagged（内部评测，不可跨系统比）** | 同上 | 2025-06 | 00-PREMISE B1 |
| DeepSeek v4-pro 输出 **$1.98 谷 / $3.96 峰** per 1M；输入 miss **$0.66/$1.32**；输入 hit **$0.022/$0.044** | 挂牌单价 / 官方目录价 / — | verified（抓两次一致 + CNY 算术闭合） | api-docs.deepseek.com/quick_start/pricing | **2026-08-16 16:00 UTC 生效** | **—**（B9 消费的是比例结构与生效时刻，**不是单价值**） |
| DeepSeek v4-flash 输出 **$0.66/$1.32**；输入 miss **$0.22/$0.44**；输入 hit **$0.007/$0.014**（CNY 精确 ¥0.05/¥0.10） | 同上 | verified（含舍入说明） | 同上 | 2026-08-16 | **—**（同上） |
| 峰时窗口 **01:00–04:00 + 06:00–10:00 UTC**；谷时占 **17/24 h = 70.8%** | 计费时段定义 / 官方 / — | verified（占比为算术推导） | 同上 + news260813 | 2026-08-16 | **—** |
| 缓存命中 = 未命中 **1/30（96.7% off）**；pro = flash **×3**；输出 = 未命中输入 **×3**；峰 = 谷 **×2** | 价格比 / 官方目录价，CNY 口径精确 / — | verified | 同上 | 2026-08-16 | 00-PREMISE B9 |
| **DeepSeek 无 Batch API** | 能力有无 / 官方文档导航 + 定价页 + 限流页三处一致缺失 / Anthropic/OpenAI/Google 均有且 50% off | verified（负面证据，三处一手） | 同上 | 2026-08-17 | 00-PREMISE B9 |
| 并发 **pro 500 / flash 2500**，超限 429 **无排队**，扩容免费 | 并发上限 / 账号级 / — | verified | api-docs.deepseek.com/quick_start/rate_limit | 2026-08-17 | **—** |
| 中文 **1 汉字 ≈ 0.6 token** | 分词换算 / DeepSeek tokenizer / 英文 1 字符 ≈ 0.3 token | verified | api-docs.deepseek.com/quick_start/token_usage | 2026-08-17 | **—**（§4.3 陈述 CJK 低估，未引用该换算） |
| 单次 deep research 实测 **$1.10**：token $0.304 + 搜索 77 次 **$0.77（70%）** + 代码 $0.03 | 单次运行实付 / **n = 1**，o4-mini-deep-research / — | verified（算术闭合）；**n=1，可推广性存疑** | til.simonwillison.net | 2025-10 | **—**（B9 只消费「搜索配额是显式预算」这条定性结论） |
| 内置 web search **$10 / 1,000 searches**（Anthropic 与 OpenAI 同价） | 工具调用费 / 官方 / serper ≈$1/千次 | verified | platform.claude.com/docs/en/about-claude/pricing | 2026-08-17 | **—** |
| held-out 规模：核心闭集 **60 题** / 公开演示 **20 题** / 季度轮换 **20 题** | 任务集规模建议 / 语料 §3 / — | 语料给出的设计建议（非测量） | ext-evaluation.md#3 | 2026-08-17 | 01-CONTRACTS §9.26 |

#### §3.2.8 可复现、schema 与中文 `[E: ext-reproducibility.md, ext-evidence-schema.md, ext-chinese-ecosystem.md]`

| 数字 | 口径三元组 | 状态 | 一手出处 | as-of | 消费方 |
|---|---|---|---|---|---|
| DVC issue **#755 开于 2018-06-08，至今 open** | 并行调度器请求的状态 / DVC 仓库 / `dvc repro` 无 `--jobs` 开关 | verified | github.com/iterative/dvc issue #755 | 2026-08-17（查询日） | 01-CONTRACTS §8.3 |
| DSBench **34.12%** / BLADE 最佳 F1 **44.8%** / CORE-Bench-Hard **21.48%** / REPRO-Bench **21.4%** | 端到端开放式数据分析成绩 / 四个基准，最佳 agent / **四基准同向但不可相减** | verified | 语料 §F2 | 2025–2026 | 01-CONTRACTS §2.1 |
| CORE-Bench **Easy 60.00% → Hard 21.48%** | 同一 agent 同一模型 / **唯一变量是任务难度** / 内部对照 | verified | 同上 | 2025–2026 | 01-CONTRACTS §2.1（最干净的对照） |
| DABstep hard **14.55% → 87–100%** | 封闭式成绩 / 2025-06 → 2026 年多家宣称 / **已进入基准饱和/过拟合区间**（单一固定合成支付域、公开榜、dev split 蒸馏；MotherDuck 另证 450 题中至少 5 题 gold 答案可证为错） | verified（数值）+ 饱和警告 | 语料 §F1 | 2025-06 / 2026 | 01-CONTRACTS §2.1, §9.13 |
| bioRxiv 标题匹配假阴性 **37.5%**（120 篇复核） | preprint→VoR 关联的错误率 / 生产系统 / **把统计量从 42.0% 拉到 67.0% 量级，约 25 个百分点** | verified | 语料 §10 | — | 01-CONTRACTS §5.5.2 |
| 一篇论文（NumPy/Nature）在 Semantic Scholar 上挂 **7 个不同标识符** | 标识符数 / DOI/ArXiv/CorpusId/PubMed/PMC/MAG/DBLP / URL 数无上界 | verified（实测） | Semantic Scholar API | 2026-08-17 | **—**（§5.5 定了归并键优先级，未引用该数字） |
| OpenAlex `is_retracted:true` **134,175** vs Crossref `update-type:retraction` **74,607**（差 1.8×） | 撤稿口径 / 同日实时查询 / 互比 | verified（live） | 两家 API | 2026-08-17 | 01-CONTRACTS §6.3.1 |
| `language:zh` **5,059,316 / 324,389,590 = 1.56%**；`language:zh-cn` 仅 **16,356** | 中文论文数与占比 / OpenAlex 全库实时 / **错代码陷阱** | verified（实测可复跑） | api.openalex.org | 2026-08-17 | 01-CONTRACTS §3.6 |
| 中文年产出 **2015 年 309,668 → 2023 年 30,177（9.7%）** | 按出版年计数 / `language:zh` 全库 / 同库跨年自比 | verified（实测） | 同上 | 2026-08-17 | 01-CONTRACTS §3.6 |
| 刊级 **734 / 1,987 = 37%**；篇级 **1,545,929 / 6,453,244 = 24%** | 收录率 / 2023 版北大核心 1,987 种刊；**篇级分母为万方数据，非「全部中文论文」** / — | verified + **利益相关口径警告**（论文第四作者供职万方，自陈因该作者「职务与资源便利」而选万方） | arXiv:2512.16339 §3.1 / Table 2 | 2025-12（论文） | 01-CONTRACTS §3.6 |
| References 完整率 **7%**（论文口径）；随机抽样 `refs>0` 仅 **2%** | 字段完整率 / OpenAlex 中该批中文论文 vs `sample=100&seed=42` 随机 100 条 / — | verified | 同上 + 实测 | 2026-08-17 | 01-CONTRACTS §3.6（引文滚雪球必须关闭） |
| 语言字段 **5% 标中文、92% 标英文** | 字段准确率 / 1,537,378 篇有语言标注的中文刊论文 / 真值 = 全部为中文刊 | verified（论文注明此后已改善） | arXiv:2512.16339 §5.3 | 2025-12 | 01-CONTRACTS §3.6 |
| 三个顶刊 ISSN 在 OpenAlex `sources` 与 Crossref `journals` 命中**均为 0** | 刊级可检索性 / 《管理世界》《中国社会科学》《历史研究》按 p-ISSN 精确查询 / 刊名模糊检索可查到无 ISSN 残桩 | verified（实测） | 两家 API | 2026-08-17 | 01-CONTRACTS §3.6 |
| `GB/T 7714—2025` 发布 **2025-12-02**、实施 **2026-07-01**；2015 版状态「废止」 | 国家标准状态 / 单一标准条目 / — | verified | openstd.samr.gov.cn | 2026-07-01（实施日） | — |
| BrowseComp-ZH **289 题 / 11 领域**，官方榜首 **42.9%**（OpenAI DeepResearch）；通义自报 **46.7** | 准确率 / 289 题全集、20+ 系统 / **42.9% 是 2025-04 论文口径，不是 2026-08 实时榜** | verified（各自口径） | arXiv:2504.19314；arXiv:2510.24701 Table 1 | 2025-04 / 2025-10 | **—** |
| Elsevier 对外 snippet 上限 **200 字符**（围绕且不含匹配实体本身）+ 必须附 DOI 回链 | 摘录硬上限 / ScienceDirect TDM 条款 / 一般来源本项目自设 300/1,200 字符 | verified（条款原文） | Elsevier TDM 条款 | 2026-08-17 | 01-CONTRACTS §8.6.1 |
| Cloudflare **2026-09-15** 起改默认值 | 默认策略变更日 / 新接入域名 + 现有客户新站点 + 未改设置的免费客户，在展示广告页面上默认阻断 Training 与 Agent、放行 Search / — | verified | blog.cloudflare.com | **2026-09-15（未来生效日）** | 本文件 §5.3（定时失效） |

### §3.3 当场纠正的数字（必须单列，因为错误版本仍在网上流传）

> **为什么单列**：这些数字的**错误版本仍是网上的主流版本**。任何下游 agent 只要做一次普通检索，
> 拿回来的大概率是错的那个。本节的用法是**否定式白名单**：见到左列的形态，一律按右列改写或拒收。
> 语料全库共 **50 行**标 `corrected`（§1.2 脚本自算）。本节共 **37 行**（自算，2026-08-17）：
> 大部分取自那 50 行中语义影响最大的一批，另有少数取自标 `unverified` 的**作废旧值**行
> （如 OpenAlex「250M 篇」、DeepSeek 旧统一价）——它们不是口径错，是**已经失效但仍在流传**，
> 危害形态相同，故并列于此。未收录的 `corrected` 行在各维度核验表内原地可查。

#### A. 口径掉包类（数值对，指标错——最危险，因为逐字复制不会被抓）

| 流传的错误版本 | 正确版本与口径 | 出处 | 消费方 |
|---|---|---|---|
| 「PaperQA2 的 **accuracy** 超过 PhD 研究者，85.2% vs 73.8%」 | 超人的只有 **precision**（85.2±1.1 vs 73.8±9.6, p=0.0036）；**accuracy 66.0±1.2 vs 人类 67.7±11.9, p=0.66，无显著差异且 CI 大幅重叠** | arXiv:2409.13740 vs futurehouse.org 公告页 | 00-PREMISE B4；本轮**同型错误**曾在上一轮踩过 |
| 「深度扩展使事实核查准确率下降 **约 42%**」 | 是**绝对百分点降幅的两模型均值 −42.0 pp**（相对降幅均值约 53%），且两模型降幅相差近 3 倍 | arXiv:2605.06635 正文核算 | 00-PREMISE B1 |
| 「**1.07%** 的引文无效」 | 1.07% 的分母是**论文**（604/56,381），不是引文；**引文级比例约 0.034%** | arXiv:2602.06718v2 | — |
| 「LLM 引文准确率 **85.1%**」 | 85.1%/77.6% 是**自动引文判定器与人工标注的一致率**，不是模型的引文质量分 | Gao et al., EMNLP 2023 | — |
| 「Elicit 只有 **10%** 的引文能对上原文」 | quote match 10% 与 reasoning match 0% 衡量的是**跨重复运行的一致性（可复现性）**；与人工金标准比对的是 **value match 77%** | Lagisz et al., RSM 2026-05-29 | — |
| 「FActScore 准确率 **98%** / 逐条误判率 2%」 | "ER < 2%" 是**模型聚合层**的估计误差；**逐条 F1-micro 只有 53.3%–83.2%** | arXiv:2305.14251 附录 B.2 | 01-CONTRACTS §1.3（机制） |
| 「BadRAG：0.04% 语料 → **98.2% 攻击成功率 + 74.6% 系统失效**」 | 98.2% 是**检索命中率**不是端到端 ASR；74.6% 是 **GPT-4 在触发场景下的拒答概率**不是系统失效率；0.04% 的分母约 25,000 段（对应 SQuAD 23,215），不是「数百万级语料」 | arXiv:2406.00083v2 | 01-CONTRACTS §5.5（假独立佐证样本） |
| 「Kosmos 的 **79.4% 结论**是准确的」 | 一手论文写的是 **79.4% of the statements**；且它是三个**不同指标**（reproducible / validated-with-primary-sources / accurate）的聚合，论文未说明聚合方式 | arXiv:2511.02824 vs edisonscientific.com 公告 | 00-PREMISE B4 |
| 「MLR-Bench：**80% 的案例产生伪造结果**」 | 一手是 **"8 out of 10 tasks conducted by Claude Code"**——**n=10、单一 coding agent**，不是 201 题基准的整体比例 | arXiv:2505.19955v2 | 00-PREMISE B4 |
| 「AI 综述有 **17% 的幻觉引用**」 | 17% 是「无法解析」；其中 **78.5% 是 PDF 解析伪影**，真幻觉只占其中 **5.1%** | arXiv:2601.17431 | 00-PREMISE B4 |
| 「otto-SR 敏感度 96.7% / 特异度 97.9% vs 人类 81.7% / 98.1%」 | 正文可核的是**全文筛选阶段**；人类 81.7% 是**剔除 1/5 篇 outlier 综述后**的加权值、98.1% 是五篇全算值；96.7/97.9 在正文中无对应值 | 语料 §E | — |
| 「Deloitte 澳洲退款 **A$440,000 / US$290,000**」 | 那是**合同总额**及其美元折算；**实际退款是合同最后一期款 A$97,000+（约 US$63,000），约占合同额 22%** | DEWR 发言人 2025-10，经 CFO Dive / AP 转述 | 00-PREMISE B3（上一轮口径事故的原型） |
| 「STORM 比人类作者好 **25%**」 | **+25 个百分点是「organization」维被判为 organized 的文章占比之绝对提升，对比的是 outline-driven RAG 基线，不是人类作者** | 语料 §（#24） | — |
| 「手工专家数据抽取准确率 **45.8%**」 | 真实口径是**限时实验室任务中 4 名专家用 RevMan 手工完成的准确率**，不是 Cochrane 双人独立抽取的准确率——**作为「人类基线」引用属口径掉包** | arXiv:2606.02403v2 用户研究节 | — |
| 「RCT-Reviewer 达到 71.0% accuracy / 87% precision / 90% recall」 | 71.0%/78.3% 是 **RobotReviewer 2015 JAMIA** 在 RoB1 二分标签下的数字，被移植为该工具自身的性能声明 | rct-reviewer.github.io vs JAMIA | — |
| 「PPS 检测器命中 **47,822** 篇论文」 | 47,822 是**单条**指纹（`"surface region" AND "surface area"`）在 Dimensions 的命中数，是词典中最高的一条；**指纹命中数之和 1,455,119 是重复计数上界，不是去重论文数** | PPS CSV 自算 | — |
| 「Feet of Clay：**110 万篇**引用约 **1.2 万篇**撤稿研究」 | 作者本人 2025-01-29 写的是 **764,000+**；「110 万 / 1.2 万」是多个二手站转载同一篇 The Conversation 后的变体——**是一个源，不是三个源** | The Conversation 2025-01-29 | 01-CONTRACTS §5.5 |
| 「RW 数据是 **CC0**」 | RW 数据仓库**没有 LICENSE 文件**（GitLab API `license: null`）；Crossref 的表述是可自由复用 + 请求署源 | GitLab API + Crossref 博客 | 01-CONTRACTS §6.3.1 |
| 「4,406 条捏造引文 / 语料是 **PubMed**」 | 数字应为 **4,046**（疑为转写错误）；语料是 **PMC OA 子集**，不是全 PubMed | Retraction Watch 2026-05-07（两处口径均偏） | 00-PREMISE B3 |
| 「Coomer 案 AI 制裁 **US$2.3M**」 | US$2.3M 是**诽谤判赔额**，与 AI 制裁无关；Rule 11 制裁是 **US$3,000 / 人** | Colorado Politics 2026-04-01 vs Judge Wang 令 | — |

#### B. 时效失效类（曾经对，现在错）

| 流传的错误版本 | 正确版本与生效日 | 出处 | 消费方 |
|---|---|---|---|
| Crossref polite pool **50 rps** | **2025-12-01 前的旧值**；现值列表 3 rps / 单条 10 rps，**失效 16 倍** | crossref.org 公告 | 01-CONTRACTS §6.3-5（已带 ⚠️） |
| OpenAlex 收录 **250M 篇** | 早期快照口径；现值默认口径 **324,389,590**（`corpus=all` 516,949,125） | api.openalex.org 实测 | 01-CONTRACTS §3.2（标 `unverified`，**禁止使用**） |
| OpenAlex「API key 必需，否则 **409**」/「**100,000 credits**/天」 | 2026-01 公告的预告口径与旧 credit 面额；现状是无 key 仍可用、超限返 **429**，免费档 **$1/天 = 10,000 credits**（面额改过 10 倍，**吞吐量等价**） | 公告 vs 实测响应头 | — |
| marker 权重免费门槛 **$2M** | **2025 年口径**；现值 **$5M** 融资/营收 | marker README + datalab.to blog | — |
| DeepSeek「谷时窗口 **16:30–00:30 UTC**」「cache hit **$0.028**/MTok」 | 全部作废；现行峰时 01:00–04:00 + 06:00–10:00 UTC，v4-pro cache hit $0.022 谷 / $0.044 峰 | api-docs 现行值比对 | 00-PREMISE B9 |
| DeepSeek 旧统一价 pro **$0.435/$0.87**、flash **$0.14/$0.28** | 2026-08-16 16:00 UTC 起作废；**沿用会低估 1.5×–12×**。注意旧价本身标 `unverified`（官方页已下线，仅二手） | api-docs.deepseek.com/news/news260813 | 00-PREMISE B9 |
| PPS 使用 **276** 条 tortured 指纹 | 那是 **2021-10 的状态**；现值 **8,282** 条，相差 30 倍 | PPS CSV 2026-08-17 下载 | — |
| Cognition《Don't Build Multi-Agents》「2026 年 3 月由 Walden Yan 发表」 | 作者对，**日期错约 9 个月**：页面标注 `06.12.25`，即 **2025-06-12** | cognition.com/blog | — |
| Google×MIT「**180 配置 / 4 基准 / +80.9%**」 | 博客版（2026-01-28）口径；现行 arXiv v3 是 **260 / 6 / +80.8%**——**引用必须带版本与日期** | research.google vs arXiv v3 | 00-PREMISE B1 |
| OpenAI deep research HLE **26.6%** | **2025-02 发布时**的值，2026-08 **不可用作现状** | openai.com（403，经 Fortune/HN 一致转述） | — |
| 中文覆盖「默认排序前 50 条：DOI 92%、refs 50%」 | **本轮自查发现的抽样偏倚**：改随机抽样后 DOI 70%、**refs 2%**（差 25 倍）；OpenAlex 默认排序偏向元数据齐全记录 | api.openalex.org 实测 | 01-CONTRACTS §3.6.1 |

#### C. 张冠李戴 / 假共识类

| 流传的错误版本 | 判定 | 出处 | 消费方 |
|---|---|---|---|
| Tavily「`/search` 与 `/answer` **10 QPS**、`/contents` **100 QPS**」 | **逐字等于 Exa 官方 rate-limit 表**；Tavily 官方只发 RPM，且**根本没有 `/contents` 端点**（叫 `/extract`）。判为把 Exa 的表张冠李戴，多站转抄形成假共识 | exa.ai/docs/reference/rate-limits vs docs.tavily.com | — |
| Jina「并发 **2 / 50 / 500**」 | 2026-08-17 浏览器实读官方表**只有 RPM/TPM 两列，无并发列**；一手无此数字 | jina.ai/reader | — |
| marker README「ahead of MinerU and docling」 | 基于 marker **自选 benchmark**；**同框口径**（OmniDocBench v1.6）下结论**相反**（MinerU2.5-Pro 95.75 > Marker 78.44） | OmniDocBench | — |
| 「LLM-judge verbosity bias **15–30 点**」「位置偏置 10–15 点」「22–30% 判定翻转」 | 一手大规模测量（21 judge / ~541,000 判定）测得 verbosity bias **全部 <0.011**；这些数字来自互相引用、无一手出处的营销博客 | arXiv:2606.19544v1 | 01-CONTRACTS §6.4 |
| `research.google` 博客 / arXiv:2512.08296 / ResearchSquare / *Nature MI* 「四个来源一致」 | **同一批人同一项工作的四个载体，算一个来源** | 语料 §结论摘要-8 | 00-PREMISE B1（假独立佐证登记） |
| 「E2B 默认 2 vCPU $0.000028/s」（多篇博文） | 与一手一致（2 × $0.000014），但**非独立来源**——全部回溯到同一价目表 | 语料 §E | — |

### §3.4 本表未收录部分的定位

未进入 §3.2 的核验表行（本表 **134 行**，自算；语料全表 **784 行**）按维度原地可查，入口一律为
`research/v2/<维度文件>.md#载荷数字核验表`。数量最大的五个维度依次为：
`ext-science-agents`（72 行）、`ext-multimodal-evidence`（55）、`ext-academic-apis`（54）、
`ext-web-providers`（51）、`ext-orchestration`（50）。
`gt-*` 七维**没有核验表**，其证据入口是各文件的「逐条事实」与「与二手文档的冲突」两节。

---

## §4 不可引用清单（do-not-use）

> **规则**：本节的数字**在任何 v2 文档、任何代码默认值、任何对外文案中一律不得出现**，
> 包括「有人说……」式的转述。若下游确实需要该量级，必须重新取一手源并新建一行核验记录。
> 分类不是按「有多假」，是按**为什么不能用**——因为解封路径不同。

### §4.1 一手源不存在或未触达（解封路径：拿到一手源）

| 数字 | 为什么不可用 | 解封路径 |
|---|---|---|
| MAST「**42% / 37% / 21%** 失效分布」 | **arXiv 摘要中不存在该分布**；仅见于 futureagi / medium 二手转述 | 取正文表格核实 |
| 「Open Deep Research 平均每篇报告 **91.9 个错误**」 | 未能在正文中定位到该数字与其定义 | 取论文正文 |
| 「Skywork 在 GAIA 上 **82.42**，2025-05-10 登顶」 | GitHub 仓库首页与 AgentOrchestra 论文均未出现该数字（论文给的是 GAIA Test 89.04%） | 取一手榜单 |
| 「DeerFlow 隐式续跑安全上限默认 **8**」 | 出现在抓取工具的摘要中，未在 README 原文中定位到，**可能是抓取端的概括** | 读 README 原文 |
| CharXiv **descriptive 题人类准确率 92.1%** | 仅见二手摘要；NeurIPS PDF 超限、OpenReview 反爬、charxiv.github.io 排行榜未上线 | 取 NeurIPS 正式版 |
| 「GPT-5 在堆叠柱状图上 **59.2%**」 | ACM 全文 403；两个 ChartBench 的摘要均无此数 | 取 ACM 全文 |
| 「Kimi K3 以 **91.20** 领跑 BrowseComp-ZH」 | 仅见于 WebSearch AI 摘要；官方榜单最高 42.9% | 取官方 leaderboard 仓库 |
| Zochi「**top 8.2%**、meta-review 4/5」 | intology.ai 博客 403；**全部可及页面均复述该单一上游源**（假独立佐证） | 取博客原文或 OpenReview |
| 人类只召回 **23.6%** 投毒句 / 区分精度 48.6% | 在署名综述（arXiv:2509.08463）一手 HTML 中未找到；疑出自 arXiv:2202.09381 | 定位真实出处后按真实出处引 |
| 「注入传播到 **48%** 的并行运行智能体」 | 仅片段，未取全文 | 取 arXiv:2604.12986 全文 |
| 「只有 **1%** 的综述有完全可复现的检索策略」 | 仅见于 otto-SR 预印本的引用，未触达一手 | 取 Rethlefsen 等原文 |
| S2AND 作者消歧 **B³ F1 90%** | Semantic Scholar 官方 API 博文中未见此数字，未找到一手来源 | 取一手评测 |
| ROBINS-I V2 的**确切域数** | 二手在「六域」与「七域」间冲突，未打开官方 V2 工具文件逐域核对 | 打开官方工具文件 |
| Europe PMC 覆盖量与限速 | 站内**自相矛盾**（RestfulWebService 页 10.2M/6.5M vs developers 页 6.4M/3.2M，差 1.6–2×）；限速**官方未公布任何数字** | 向 Europe PMC 求证 |

### §4.2 厂商自报且无法独立复核（解封路径：独立复算，不是找更多转述）

| 数字 | 为什么不可用 |
|---|---|
| 竞品 CPM「GPT-5 $488 / Exa $402 / Perplexity $709 / **Anthropic $5,194**」 | **由竞争对手 Parallel 测量并发布**（厂商自利数据），2025-08 基准，距今 12 个月 |
| Cloudflare「超过一半的网页请求来自 bot/agent」「超过 20% 的域」等网络级统计 | Cloudflare 自报、自身网络样本、**无独立验证，属营销语境** |
| 「自适应注入仍以 **85%** 击败已设防 LLM；复合攻击 **97.6%**」 | 疑为厂商营销内容（particula.tech 博客） |
| Google「恶意类别相对增长 **32%**；间接注入占 2026 注入事件 **55%+**」 | 只到 helpnetsecurity / CSA 转述，**未找到 Google 一手报告** |
| Unit 42「可见明文 37.8% / HTML 属性伪装 19.8% / CSS 抑制 16.9%」 | 数字如其所报，但**分母未披露** |
| Elicit「recall 96.89% / specificity 92.54% / accuracy 93.21%」 | 仅见检索摘要，未取一手页面 |
| Elicit「94–99% accuracy」「99.4% accurate」 | 厂商自设金标准；**未披露**金标准是否双人校验、逐字段准确率、评审者身份、置信区间、评测代码与数据 |
| mem0「LoCoMo 92.5 / LongMemEval 94.4」 | 页面**未说明该分数是准确率、J score 还是 LLM 裁判分**；且二手转述的「91.6 / 94.8」与官方页当前值不符，**两者至少一个已过期** |
| scite「280M+」vs「300M+」 | **同一页面两个不同口径**（「全文学术文献」vs「文章+预印本+书+专利+数据集」），引用须注明是哪一个 |

### §4.3 口径不适用（数字为真，但用在我们的问题上是范畴错误）

| 数字 | 为什么不可用于本项目 |
|---|---|
| DeepSeek「**100%** / 70.27% / 39.7%」安全数字 | 全是**越狱/有害提示拒答**口径，**不是 IPI**；测的是 R1、V3，**均非 v4-pro/v4-flash**；三者彼此差 2.5 倍。**作为「抗注入能力」引用是口径不适用**（见 01-CONTRACTS §0.4） |
| 「存在 deepseek-v4-pro / v4-flash 的公开 IPI 专项评测」 | **截至 2026-08-17 未找到**。唯一线索 IssueTrojanBench 未取到其专项数字。**架构必须假设模型侧能力为零** |
| ChatGPT 生成医学内容「47% 捏造 / 46% 真实但有误 / 7% 完全正确」 | 仅二手转述，未取一手；且是 **GPT-3.5 代际（2023-05 前后）**，**不可作为 2026 基线** |
| 通用 LLM 在法律查询上幻觉 **58%–88%** | 未取一手；模型代际为 2023–2024（GPT-3.5/PaLM/Llama 2） |
| CiteME「LLM 找出被引论文准确率 4.2%–18.5%，人类 69.7%」 | **2024 年模型，已陈旧**；作为当前能力上界会误导 |
| Anthropic **90.2%** | Anthropic **内部研究评测**，未公开、样本量未披露，算力未控，2025 模型代际。**不可跨系统比**（`flagged`） |
| SPRITE 的输出 | 它自述为 "a heuristic method for reconstructing plausible samples"，产出的是给人看的反例分布——**把它接进自动门是范畴错误**（01-CONTRACTS §6.2.4） |
| statcheck 在 **187** 个「漏检严重」测试对象上的结论 | 那 187 个是**人工构造的文本串，不是真实论文**；引用其结论必须带这个口径 |
| E2B Hobby「一次性 **$100** 额度」 | 是**一次性促销额度**，不可用于长期成本建模 |
| perma.cc「**$10/月**」 | 数字最早见于 2019-01-07 报道，站点对自动抓取返回 403 无法核价，**视为失效**（01-CONTRACTS §8.4 D-8.9） |
| SPN2「匿名 15 URL/分钟」 | 官方 API 文档托管在**需登录的 Google Doc**；社区口径标 `unverified`（01-CONTRACTS §8.4 D-8.10） |
| 「web_fetch body 上限 **10 万字符**」 | 是**本 build 未安装**的那个 provider 的常量；工具层常量另有其值。**引用抓取上限前必须确认本机实际装了哪个 provider**（GTC A6） |

### §4.4 派生值依赖未验证前提（可用但必须原样带出前提）

| 数字 | 依赖的未验证前提 |
|---|---|
| Jina Reader **≈$0.25–0.75 / 1k 页** | **单页输出 5k–15k tokens 是语料作者的假设，不是官方数字** |
| DeepSeek 口径下一篇论文 ≈ **12,000–18,000 token / $0.003–$0.020** | 语料作者的推导（本地抽取纯文本 × 0.3 tok/char），**未实测** |
| SerpApi Production **≈0.83 QPS** | 由小时配额折算的**均值**，官方口径是小时配额且未禁止小时内突发——**不是瞬时墙** |
| DeepSeek 涨幅「输出峰时 **4.55×**、缓存命中峰时 **12.14×**」 | 依赖旧统一价那一行，而那一行本身标 `unverified`（官方页已下线） |
| serper 入门档 **$1.00/千次** | 仅二手；官方 `/pricing` 返回 404。**必须用真实账单确认** |
| Brave 免费「每月约 **1,000 次** Search」 | 官方只给 "$5 free credits"，次数是折算 |

---

## §5 证据基座的到期机制

### §5.1 为什么必须有到期机制

本轮语料里最快的一次失效发生在**写作前 24 小时**：DeepSeek 于 2026-08-16 16:00 UTC 全线改价并改为分时计价，
而网上几乎所有「2026 年 DeepSeek 定价」文章（含 2026-08 新写的）报的仍是旧统一价
[E: ext-cost-economics.md#结论摘要-1]。若本项目的成本模型晚写 24 小时并照抄检索结果，
它会低估 1.5×–12×。**这不是理论风险，是本轮实际躲开的一枚地雷。**

01-CONTRACTS §10 第 8 条已把「本文件引用的所有 prevalence 与模型分数在 6 个月内会过期」写成自陈弱点。
本节把它变成**可执行的重测责任表**。

### §5.2 按 F-25 的既有三类做责任分派

**本节不新增任何 TTL 词汇。** TTL 的三类与其建议值**已经在 01-CONTRACTS §7.2 的 F-25 里定义**
（定价/榜单类、引用幻觉率类、模型能力类），本节只回答那里没有回答的问题：
**每一类具体覆盖本项目的哪些数字，以及到期后谁去重测。**

| F-25 的类（见 01-CONTRACTS §7.2） | 覆盖本项目的哪些数字 | 失效机制 | 到期后谁负责重测 |
|---|---|---|---|
| **定价 / 榜单类** | DeepSeek 六行价卡；OpenAlex `$1/天` 与各档单价；serper/Exa/Firecrawl/Jina/Brave/SerpApi 全部价与节流；BrowseComp-ZH 榜首 42.9% | 供应商单方面改，**不发通知、旧页面下线**（DeepSeek 就是在语料写作前 24 小时改的） | 成本/供应商层维护者。重测 = 重抓官方定价页 **+ 用真实账单交叉验证**（serper 的 $1.00/千次至今只有二手，见 §4.4） |
| **引用幻觉率类** | 引文事实核查 39–77%；URL 非解析 5.4–18.5% / 幻觉 3.0–13.3%；注入 prevalence 全部（70.0%、3.9%/1.1%/0.2%、约 1% 简历）；AI Hallucination Cases 1922 起；PMC 捏造引文 1/277 | 底层现象本身在动，且**方向是恶化**（简历普查显示两年内明显上升；PMC 从 1/2,828 恶化到 1/277） | 可信度产品定义的维护者。重测 = 回原论文看是否有新版本 + 回数据库重查计数 |
| **模型能力类** | F1 = 0.750 / 0.908；κ 0.376–0.511 与全部 judge 偏置量；DABstep hard；DSBench 34.12% / CORE-Bench 21.48%；图表 MAPE 全组 | 模型代际迭代 + **基准饱和**（见 01-CONTRACTS §9.13） | 评测层维护者。重测 = **在我们自己的 held-out 上重跑**，不是去抓新榜单（抓新榜单会把 search-time contamination 直接引进来，见 01-CONTRACTS §9.27） |

### §5.2.1 两类数字落不进 F-25 的现有三类 ——〔需要新增词汇，本文件不自行创造〕

以下两类在本项目里真实存在，但**不属于 F-25 的任何一类**，也**不在 01-CONTRACTS §9 的术语表内**。
按引用规则，本文件**不为它们发明名字**，只描述并上报：

1. **注册表快照类**（RW 71,799/66,287/62,708；劫持刊 456；PPS 8,282；DOAJ 23,320；Cabells 20,274）。
   它们由注册表同步器自动维护（01-CONTRACTS §4 W-09），**且 GC-1 门已经有自己的超龄阈值**
   （见 01-CONTRACTS §6.3 硬要求第 2 条）。所以这一类**不需要 F-25，需要的是「同步器的巡检周期」**——
   那是运行参数，不是 flag。**风险**：若有人把注册表数字当作普通引文数字挂 F-25 的 TTL，
   会得到一个比 GC-1 阈值宽得多的到期时间，**门看起来还是绿的**。
2. **结构性事实类**（Bartz v. Anthropic 判词；GRIM 功率闭式解；`dvc repro` 无 `--jobs`；
   `ignorable` 只读不写；`cordis/lib/index.js:956`）。它们**不按时间过期**，只在**上游改变自己**时失效
   （法律修订、软件改版、DSH 升级）。正确的机制是**触发式重测**而非定期 TTL：
   **DSH 版本变化 → 重跑 gt 层七维；法域改革 → 重跑 `ext-legal-tos`**。

**处理方式**〔裁定〕：这两类**暂不进 F-25**，按上面的机制各自处理；
若下游确实需要给它们一个 flag，**必须先改 01-CONTRACTS §7.2 与 §9，再改本文件**。
**什么会推翻**：若实现阶段发现「触发式重测」在工程上无法落地（例如无法可靠检测 DSH 版本变化），
则结构性事实类也必须退回定期 TTL，届时需要新增词汇。

### §5.3 三条已知的**定时**失效（有明确日期，必须进日历）

| 日期 | 会失效的是什么 | 影响 |
|---|---|---|
| **2026-09-15** | Cloudflare 对新接入域名等在展示广告页面上**默认阻断 Training 与 Agent**、放行 Search；多用途爬虫按最严格类别判定 [E: ext-legal-tos.md#结论摘要-3] | 本项目抓取器若自我声明为 agent，会在越来越多站点上撞墙 → 命中更多 T12 → 更多 ST-N。**这是设计上接受的代价**（见 01-CONTRACTS §8.6.5），但**命中率会在这一天阶跃** |
| **2026-12-31** | Gemini 3.7 Flash 的 $0.75/$3.75 标注 "through Dec 31 2026" [E: ext-cost-economics.md#核验表-24] | 仅影响对照组数字，不影响本项目主 provider |
| **滚动** | Semantic Scholar 的 1 rps 官方措辞是 **"introductory"**（随时可变）[E: ext-academic-apis.md#核验表-25]；Gemini deep research 模型 ID **均带 `preview` 后缀**（随时可变）[E: ext-incidents-products.md#核验表] | 限速网关的配置必须**能在不改代码的情况下改值**，否则一次上游调整就要发版 |

### §5.4 重测的两条硬纪律

**D-5.1〔裁定〕重测不是「再搜一次」，是「重跑同一条取证命令」。**
本表里凡标 `verified（实测）` 的行都附有可复跑的命令或端点（如
`api.openalex.org/works?filter=is_oa:true` 的 `meta.count`）。重测必须走同一条命令并**记录两次的差**；
用检索引擎「看看现在是多少」等于把一手降级为二手，正是 §1.3 U1 要根除的机制。
**什么会推翻**：若某条命令的端点被下线且无等价替代，则该行只能改判为 `not_covered` 并进 §4，
**不得**用二手值续命。

**D-5.2 到期不等于变假，到期等于「失去 verified 资格」。**
过期数字的正确处理是降级 + 打 flag（**见 01-CONTRACTS §7.2 F-25 与 §1.5 第 2e 步**），
不是删除。删除会让「我们曾经据此做过决定」这件事不可审计。

---

## §6 覆盖缺口

> 分四类，因为解法不同：**没查到的** / **被环境挡住的** / **公开空白** / **本文档集内部的接线缺口**。

### §6.1 本轮没能查到（有一手源，我们没拿到）

| 缺口 | 卡在哪 | 下一轮获取路径 |
|---|---|---|
| `GB/T 7714—2025` 标准正文 | 国家标准全文公开系统对该条目**未提供免费全文**；变更清单来自一所职业学院的摘要页 | 购买/申领标准正文；**在此之前格式化器只支持 2015 版并显式声明** |
| 知网开放平台条款与价格 | `open.cnki.net` 返回 **503** | 在确认前，**架构不得假设存在任何知网可编程通道** |
| 博查 / 秘塔 / 阿里 IQS 的 API 单价 | 价格页**需登录**（博查文档 302 至登录页；阿里云市场页 JS 渲染取不到正文，且另有 ¥3.6/千次、¥1/千次 两个相差 10–36× 的说法） | 由用户在已登录环境下补一次，或按调用量实测反推。**取到后必须分辨促销价与刊例价** |
| serper 实际档位表 | 官方 `/pricing` 返回 **404**（疑需登录） | **用真实账单确认**，不是再搜一次 |
| arXiv:2507.19302 的具体数字 | 摘要页无数值，未下载全文 | 取全文。**若属实它解释了中文年产出断崖的机制（CNKI 停止向 OpenAlex 供数）**，对判断「这个缺口会不会自己修复」很关键 |
| NCPSSD 的规模与是否有 API | 各高校图书馆转述页数字互相矛盾（2000 余种刊/930 万篇、2500 万条、1000 万余条） | 单独花一轮确认。**若存在批量接口，中文社科的证据获取难度会显著下降** |
| Firecrawl Research Index 的字段契约 | `features/research-index` 页 **404** | 直接打端点观察返回体 |
| UHGEval 等中文幻觉基准 | 未取一手 | **中文场景下「引用忠实度」的可测量性目前无结论** |

### §6.2 被环境限制挡住（站点主动拒绝我们）

**这一类的正确处理不是想办法绕过，而是记录为 `not_covered`**（见 01-CONTRACTS §8.6.3 `T12-UNREACHABLE`
与 §8.6.5 的抓取身份策略——**不伪装浏览器是设计上接受的代价**）。

| 被挡住的源 | 返回 | 影响的结论 | 下一轮路径 |
|---|---|---|---|
| `onlinelibrary.wiley.com` | **402 Payment Required** | Wiley TDM 条款（非商业 + ORCID token + 仅官方 API）标 `unverified` | 用机构订阅身份取；或直接按最严解读设默认值 |
| `sso.agc.gov.sg`、`sal.org.sg` | **403** | 新加坡 s244「违反数据库使用条款即无合法访问」标 `unverified`，且与 2026 改革提案**矛盾未决** | 取官方 PDF |
| `japaneselawtranslation.go.jp` | **403** | 日本 Art.30-4 条文与但书标 `unverified` | 取官方译本 PDF |
| `irishstatutebook.ie` | **403** | 爱尔兰法域未覆盖 | — |
| `eur-lex.europa.eu` | 三种 URL 形式**均空正文** | EU DSM Art.3/Art.4 条文未直读（依 `legislation.gov.uk` 保留条文与 `digital-strategy.ec.europa.eu` PDF 替代） | 用 EUR-Lex 的 PDF 直链或 OJ 存档 |
| `thelancet.com` | **403** | 4,046 条捏造引文的**方法学细节**未取全文（Flemyng 的批评正是针对方法披露不足） | 取全文 |
| `openai.com` 全站 + `help.openai.com` | **Cloudflare 全局拦截**（WebFetch 与 curl 均 403） | OpenAI Deep Research 的「澄清提问 + 可编辑计划」**仅有摘要级证据** | 浏览器工具直取 |
| `perplexity.ai/hub`、`research.perplexity.ai` | 403 / 连接失败 | WANDR 的 soft/hard F1 只有二手 | **WANDR 已 Apache 2.0 开源——直接读仓库里的 grader 代码比读博客更硬** |
| `intology.ai` | **403** | Zochi 全部指标无一手（见 §4.1） | 取 OpenReview |
| `dewr.gov.au` + AusTender | 403 + 超时 | Deloitte 澳洲退款额只到发言人转述 | 浏览器工具直取 AusTender CN 记录，锁定合同号与退款后金额 |
| `api.core.ac.uk` | **两次 40 秒超时 + 文档页 403** | **在实机验证连通性之前，不要把 CORE 写进任何路径** | 换网络环境实测；确认是地域因素还是服务侧 |
| PPS 部分页面、Cabells、STM Integrity Hub | 需登录 / 订阅制 / 仅对出版商开放 | 这三层**永远只能作为人工复核提示，不能作门**（见 01-CONTRACTS §6.1 与 flag F-08） | 不解封——这是**产品设计的一部分**，不是缺陷 |

**⚠️ 一条必须一起说的元事实**：本轮**多个兄弟调研 subagent 共享 WebSearch 会话配额**，
至少三个维度在第 2–14 次检索时配额耗尽并降级到 serper/curl 兜底，各自留下「反证检索做得不够」的自陈
[E: ext-orchestration.md#U9, ext-multimodal-evidence.md#R1, ext-academic-apis.md#未决-8]。
所以 §6.1 与 §6.2 的清单**本身可能不完整**——它记录的是「我们知道自己没查到的」，
不是「我们没查到的全部」。

### §6.3 公开空白（不是我们没查到，是没人做过）

这一类最重要，因为它同时是**产品机会**和**不可承诺项**。

| 空白 | 证据 | 对本项目的含义 |
|---|---|---|
| **等算力条件下「并行 vs 串行」的对照实验** | 整个 deep-research 谱系里没有任何一篇公开工作给出 [E: ext-dr-architectures.md#结论摘要-2] | 00-PREMISE B1 把它降级为 `unverified` 前提并预注册了 M2 实验——**做出来就是贡献** |
| **中文网页的 IPI 野外测量** | 本轮检索未找到任何一篇 [E: ext-security-injection.md#未决-18] | **不能假设中文层的注入率低于英文层，只能说没人测过**（01-CONTRACTS §10 第 7 条） |
| **「与内容有关且可重跑」的停机门** | 13 个被调研系统一个都没有 [E: ext-dr-architectures.md#结论摘要-1] | 这是本项目的空白地带，也是它必须自建的机制 |
| **逐字引文匹配的端到端精度** | 未找到任何公开的端到端测量；PDF 文本抽取保真度亦无公开量化 [E: ext-verification-mechanisms.md#核验表末段] | 01-CONTRACTS §1.2 把 `quote_faithful` 宣称为「100% 可兑现」，其**归一化算法本身的假阴性率是未测量的**（中文 PDF 抽取是最大来源，见 §1.2.3） |
| **Undermind / Consensus / SciSpace 的独立引文忠实度评测** | 未找到任何同行评审的 [E: ext-citation-faithfulness.md#R7] | 竞品全线空白 → 00-PREMISE B3 的大仓位依据之一 |
| **中文核验基础设施** | 是**公开空白**而非「我们没做好」〔依据 00-PREMISE B7 反对证据〕 | B7 押小：主动声明能力受限（flag F-32），不建全库检索 |
| **概率性商业侦测层的 false positive rate** | Papermill Alarm / STM / Cabells / Signals / ImageTwin，**没有一家公布过带口径的 FPR** [E: ext-literature-integrity.md#结论摘要-5] | 这类层永远只能进人审队列 |
| **deepseek-v4-pro / v4-flash 的 IPI 专项评测** | 截至 2026-08-17 不存在 | 01-CONTRACTS §0.4「模型侧能力假设为零」的直接依据 |

### §6.4 本文档集内部的接线缺口（本文件的原创发现）

对 `00-PREMISE.md` 与 `01-CONTRACTS.md` 做 `grep -c '<维度文件名>'` 得到：
**25 个研究维度中有 2 个尚未被任何 v2 成文文档引用**（2026-08-17 实测）。

| 未被引用的维度 | 核验表规模 | 主题上本应对接的契约节 | 风险 |
|---|---|---|---|
| **`ext-web-providers`** | 51 行 | 01-CONTRACTS §3.4.1（snippet 一票否决）、§6.3 硬要求第 5 条（中央限速网关）、§8.5（抓取工具自建义务）、§8.6（留存与许可） | 这几节目前的证据指针指向**别的维度**。特别是 **Brave 的存储权限制**与 **Jina 免费额度的 CC-BY-NC**——两条会直接咬到「可重跑证据库」这个产品形态的合规硬点，**当前在契约里没有落点** |
| **`gt-profile-plugin`** | 无核验表（形态为逐条事实） | 01-CONTRACTS §6.5.5（boot 门的五条加载期不变量）、§9.23（出厂值） | 那两节的证据指针走的是 GTC A4/A9，**而 GTC 是该维度的二级摘要**。契约的 DSH 事实链因此比它看起来短一层——不是错，但**攻击者会问「五条不变量的一手 file:line 在哪」，答案在这份没被引用的文件里** |

**〔裁定〕这两条不是本文件能修的，必须由下游文档修。**
本文件的责任是**把它变成可见的、可 grep 的缺口**，而不是替它们补一句引用。
**什么会推翻**：若后续文档（如架构文档、实现文档）自然消费了这两维，缺口自动关闭，
**重跑上面那条 grep 即可确认**，不需要人工判断。

---

## §7 本文件自身的已知薄弱处（供攻击者优先瞄准）

诚实记账适用于本文件自己。

1. **§1.2 的三个状态分布数（642/50/79）是脚本按关键词归类的，不是人逐行判的。**
   已知的误分类形态：「`verified`（数值）/ 口径不可比」被归入 `verified`。
   **本文件不用这三个数做任何质量论证**，但下游若拿它们论证「本轮 82% 的数字是可靠的」，
   那是本文件的措辞没挡住——**这句话本身就是禁止的**（分母可压缩，见 01-CONTRACTS §1.4.4）。
2. **§3.2 是选录，不是全录。** 选录规则写在 §3.1 并给出了推翻条件，但**选录本身是我做的判断**，
   我可能漏掉了某个会成为下游承重的数字。缓解措施是 §3.4 给出了全部未收录行的定位指针。
3. **「消费方」列的初稿是我读两份文档得到的，随后跑了 §3.1 承诺的那条 grep 校验，
   在约 100 个探针里查出 **15 处过度声称**并已改为 `—`。**
   典型形态是「契约引用了该机制、但没有引用该数字」——例如 01-CONTRACTS §6.2 把
   PPS 指纹词典列为 GC-0 成员，但从未出现 `8,282` 这个数；00-PREMISE B9 消费的是 DeepSeek 的
   **比例结构与生效时刻**，而**不是六行单价值**。
   **剩余风险**：探针是我按行挑的，不是全表自动展开；数字串在两份文档里的写法可能不同
   （如 `1 请求 / 3 秒` 与 `1 请求/3 秒` 只差一个空格，第一次 grep 会漏），
   所以**仍可能有漏判的过度声称，也可能有把「其实被引用了」误判成 `—` 的低报**。
   这仍是本文件里最可能被抓到硬伤的一列——但它现在是**被测量过的**，不是**被声称过的**。
4. **§4 的不可引用清单不完整。** 语料共 79 行标 `unverified`，§4 共 **45 行**（自算）。
   未收录的多为「未取得」类，已在 §6.1/§6.2 以缺口形式出现——**但两处的边界是我划的，可能有漏网**。
5. **§5 的到期机制没有实现。** 它是一张责任表，不是一段代码。
   **在 F-25 的 GC-0 检查真正落地之前，本节的全部内容是纪律而不是机制**——
   而本仓库自己的教训正是「纪律层的检查是空的」（见 §2.A3 与 GTC D1）。
6. **本文件没有独立复核过语料中的任何一个数字。** 它索引证据，不生产证据。
   任何「本文件核实了……」的读法都是错的：核实发生在 25 个调研 agent 那一层，
   **而那一层没有跨厂商复算**（§1.4 第 1 条）。
7. **§6.3 的「公开空白」是一个否定性断言，而否定性断言的证据强度取决于检索的完备性——
   而本轮的检索完备性被配额耗尽损害过**（§6.2 末段）。正确读法是「本轮检索未找到」，
   不是「不存在」。本文件在措辞上尽力守住了这条线，但**任何一处滑成「不存在」都是缺陷**。

---

**文件版本**：v2-draft-1｜**撰写日期**：2026-08-17
**语料基线**：`research/v2/`（**26 文件 / 25 个研究维度 / 11,661 行**，全部产出于 2026-08-17）
**上游更正**：本文件更正了任务书的「23 文件」与 `01-CONTRACTS.md` 文末的「22 文件」（见 §1.1）
