# 04-ORCHESTRATION — 循环结构、扇出位置、预算、检索资源治理、人在环

> **本文件的地位**：它回答「这套系统怎么跑」——外环与内环的形状、扇出允许出现在哪里、什么时候停、钱怎么记、检索资源怎么管、人在哪几个点必须插手。
>
> **它不定义任何共享术语。** 状态枚举与状态函数 `S`、三个正交谓词、claim kind、`evidence_grade`、写权矩阵、身份与独立性规则、门的分级 GC-0/1/2、flag 词表、文件与目录契约、术语表——全部定义在 `01-CONTRACTS.md`。本文件引用时只写「见 01-CONTRACTS §N」，**不复述定义原文**。需要新术语时不自行铸词，写进本文件 §10 的待补词表并回填 01-CONTRACTS §9。
>
> **硬约束**：本文件中任何关于 DSH 运行时的陈述，均以 `research/v2/GROUND-TRUTH-CORRECTIONS.md` 与 `gt-*.md` 为准。冲突以它们为准，**包括与 00-PREMISE 的冲突**（本文件记录了一处，见 §5.6）。
>
> **写作纪律**：每条载重断言带 `[E: <文件>#<锚>]`。语料标 `unverified` 的数字在引用处一并标注。会失效的数字带 `as-of`。无外部证据、由本文件裁定的规则标 **〔裁定〕** 并给出「什么会推翻它」。
>
> **一条贯穿全文的红线**：`hyper-parallel` 在本项目里**不是质量主张，是吞吐与核验密度主张**。任何「因为我们是超并行所以质量更高」的推理链在本文件中都是回归 〔依据 00-PREMISE B1 裁决〕。
>
> **命名预告（全文有效）**：本文件出现三种 `provider`。前两种的消歧见 01-CONTRACTS §9.25（`agentOptions.provider` = LLM 路由；`subagentProvider` = subagent 传输后端）；第三种是**外部检索/抓取服务商**（serper / bocha / Exa / Brave / Jina / Firecrawl / SerpApi / Tavily 及学术 API），本文件一律称**检索供应商**。该第三义项**尚未进 01-CONTRACTS §9.25，需回填**，见 §6.0 与 §10.A T-1。凡本文件中未加限定的 `provider` 字样，按上下文所在层读：§5 与 §2 指 LLM 侧，§6 指检索供应商。

---

## §1 拓扑裁定：Centralized + 黑板台账

### §1.1 裁定

**〔裁定〕拓扑 = Centralized（中心化编排）+ 黑板台账（artifact-centric state）。明确排除 Independent 与 peer 之间的自由 handoff。**

依据是本轮语料里唯一一个明确标准化了工具、提示与算力的受控评测：Google Research × MIT，260 个配置 / 6 个基准 / 5 种架构 / 3 个模型家族（arXiv:2512.08296 **v3, 2026-04-08**）。错误放大倍率按架构分层：

| 架构 | 错误放大 |
|---|---|
| Independent | 17.2× |
| Decentralized | 7.8× |
| Hybrid | 5.1× |
| **Centralized** | **4.4×** |
| 单 agent | 1.0× |

[E: ext-orchestration.md#B, #核验表16]

**口径必须随数字一起说，否则这条证据会被讲坏**：「错误放大」的原文定义是**「由 agent 间协调失败引起的额外计算量，从执行轨迹 token 估计」**，**不是「错误率放大 17 倍」** [E: ext-orchestration.md#核验表16]。同一工作的拟合强度 **R² = 0.373**（加入 task-grounded capability metric 后 0.413），即只解释约三分之一方差——**这是有用的先验，不是定律** [E: ext-orchestration.md#核验表18]。

**假独立佐证登记（必须写出）**：`research.google` 博客（2026-01-28，180 配置 / 4 基准 / +80.9%）、arXiv:2512.08296 v3（260 / 6 / +80.8%）、ResearchSquare 预印本、以及 *Nature Machine Intelligence* `s42256-026-01268-y`，**是同一批人的同一项工作的不同载体，计为一个来源，不是四个**；且博客版与 arXiv v3 之间已发生一次版本漂移 [E: ext-orchestration.md#结论摘要8, #假独立佐证登记]。与它真正独立且同向的只有两条：Anthropic 自述「需要所有 agent 共享同一上下文、或 agent 间强依赖的领域，今天不适合多智能体」[E: ext-orchestration.md#A]；OpenAI 工程指南「先把单 agent 做满」[E: ext-orchestration.md#H]。Nature MI 版本本轮未直读（认证跳转），期刊版可能是第三个数字版本 [E: ext-orchestration.md#U5]。

**诚实的下限**：Centralized 的 4.4× 仍是单 agent 的 4.4 倍。中心化是**最不坏**的多智能体拓扑，不是无成本的拓扑。这条必须写进任何「我们选了正确架构」的表述里。

### §1.2 编排器独占 status 写入权

status 的唯一物理写者是门代码，见 01-CONTRACTS §4 W-04 与不变量 I-W1。本文件不重复该规则，只声明它在编排层的两个操作后果：

1. **worker 的返回值 schema 中不含 status 字段**；提交工具在 `tools/pre-execute` 上对携带 status 的调用做 `deny`（不是覆盖——覆盖会让尝试不可见，见 01-CONTRACTS V4.1）。
2. **编排器自己也不写 status**。编排器写的是 `runs/<run_id>/manifest.json`（W-12）与 `budget/`（W-13）。「编排器独占 status 写入权」这句业界常用表述在本项目里的准确形态是：**编排器独占「何时调用门」的权力，门独占「status 值」的写入**。把这两件事合并表述会与 01-CONTRACTS §4 冲突。

### §1.3 worker 之间不互相喊话

**规则 O-1**：worker 之间**不存在**直接消息通道。worker 只能对台账做**带 schema 的状态变更**（PatchBoard 那一路的 schema-grounded state mutation），台账即黑板即产物 [E: ext-orchestration.md#J, #D2]。

依据有两条，一条来自架构，一条来自安全：

- **架构**：DSH 的父子之间只有两个字符串通道（prompt 进、final message 出），长内容根本传不过去；且工具结果超过出厂 `tool-result-pruner` 阈值 8192 字符会被头尾截断（head 4096 / tail 1024），出厂 `spill-policy` 的 `maxInlineBytes` 是 50000 [E: gt-orchestration.md#设计含义7]。**证据原文必须落盘 + 传路径，不能靠工具结果原样带回。**
- **安全**：局部消息传递比全局消息传递 ASR 低约 20%，非自复制注入在局部模式下「struggle to compromise more than two agents」。该规则的规范形态见 01-CONTRACTS §5.3 R-I4。

**规则 O-2（DSH 控制面工具的使用边界）**：`send_message` / `report` / `list_agents` **不得作为协调总线**。一手依据：

- `send_message` 只对 depth-1 直接子有效，消息成为子的下一个 FIFO turn、**不能改向正在进行的 turn**、**本调用不返回子的回复** [E: gt-orchestration.md#K2]。
- `report` 出厂 `reportDelivery: wakeup`，每次上报开一个父 turn；**无限流**；**嵌套只上报一层**（孙只报给它的直接父）[E: gt-orchestration.md#K5]。超并行下 N 个子各报一次 = N 个父 turn = N 次模型请求。
- `list_agents` **无游标、无上限**，持久化的子会话永远留在列表里 → 长跑 + 大量持久子会话会线性膨胀父的每次请求 [E: gt-orchestration.md#K4]。**不得作为常规轮询手段**，只在续跑清算时调用一次（见 §2.8 R3）。
- **结算通知不是持久信箱**：父被 dispose 时 `keepInbox: false`，未认领的结算通知被 durable 地取消；resume 后的父读不到任何未决通知 [E: gt-orchestration.md#C3, #设计含义6]。

**因此**：子代理的每条结论必须由子代理自己写进 workspace 的持久台账文件，通知/report 只当作「提醒去读台账」的信号 [E: gt-orchestration.md#设计含义6]。这是本轮 DSH 一手调研对架构最硬的一条约束。

### §1.4 中心化不是隔离

reviewer ≠ producer、编排器持有验证权，这些买到的是**审计属性**，不是隔离属性。沙箱不拦网络、`run_code` 同时绕过内核沙箱与 `ctx.fs` 围栏、`toolFilter` 不是权限天花板、子代理不继承父沙箱作为下限——规范表述见 01-CONTRACTS §4.4 与 §5.4。本文件在 §6.5 给出这条事实在检索治理上的完整后果，并且**不**在任何地方把中心化说成隔离。

### §1.5 可检验断言

- **V-4.1** 全量扫描本项目的 session 日志与台账：不存在任何 worker→worker 的自由文本载荷；所有跨 agent 回传载荷通过结构化 schema 校验（与 01-CONTRACTS V5.7 同一断言，本文件不重复定义，只声明本编排形状必须使它成立）。
- **V-4.2** `runs/<run_id>/manifest.json` 中记录本 run 使用的拓扑标识与扇出路径标识；不存在 `topology == independent` 的 run。
- **V-4.3** 负向测试：构造一个 worker 返回体携带 `status` 字段，断言 `tools/pre-execute` 产生 deny 记录且台账无写入。

---

## §2 循环结构：一个外环 + 四个内环

### §2.1 总图

```
                      ┌──────────── 外环 O（有界批次序列） ────────────┐
   CP-1 计划审批 ──▶  │                                                │
                      │   ┌── L1 覆盖环 ──┐                            │
                      │   │  发现 → 候选   │  ← 允许扇出（覆盖率）      │
                      │   └───────┬───────┘                            │
                      │           ▼                                    │
                      │   ┌── L2 取证环 ──┐                            │
                      │   │ 抓取→快照→CAS │  ← 允许扇出（多来源交叉）  │
                      │   └───────┬───────┘                            │
                      │           ▼                                    │
                      │   ┌── L3 核验环 ──┐                            │
                      │   │ N 路独立核验  │  ← 允许扇出（同一 claim）  │
                      │   └───────┬───────┘                            │
                      │           ▼                                    │
                      │      STOP 求值（§4）                           │
                      │           │ 未停 → 回 L1（keep-if-better 门）  │
                      └───────────┼────────────────────────────────────┘
                                  ▼ 停机
                      ┌── L4 裁决与组稿环 ──┐
                      │  单上下文，零扇出   │  ← 禁止扇出（B1）
                      └──────────┬──────────┘
                                 ▼
                         CP-2 争议裁决（人）
```

L1/L2/L3 构成外环的一「批」；L4 只在 STOP 成立后跑一次。**跨 claim 一致性推理、论证链构建、最终裁决全部落在 L4，即零扇出区**——这是 00-PREMISE B1 明确禁止扇出的三处 〔依据 00-PREMISE B1 裁决〕。

### §2.2 外环 O 由什么驱动

**〔裁定〕外环 = 一串有界的 `workflow` run，每个 run 是一批；批与批之间的续跑状态活在 `.arc/` 台账里，不活在任何 harness 的会话状态里。`goal` 只承担一件事：给「人授权继续」这个动作一个持久的记录点。**

逐条排除：

| 候选原语 | 为什么不作为外环驱动 | 一手依据 |
|---|---|---|
| `ralph` | 一轮一个 child、**轮内无扇出**；「完成」是 worker 自述、**无独立评审**；普通子失败即终止、**不重试**；只有轮数一个总量界（无 token / 价格 / 时长预算）。其出厂轮上限见 01-CONTRACTS §9.24 | [E: gt-orchestration.md#F3, #F4] |
| `goal` 自动续跑 | `activation` **永不持久化**：fresh cache 与每个 `agent/session-start` 边都会 disarm，即使 replay 找到 active 的持久 phase。resume / fork 之后 goal 仍在但不会自动跑 | [E: gt-orchestration.md#A1, #A2] |
| `agent teams` | 不适用：该原语属 Claude Agent SDK，**不属 DSH**；且其官方边界包含「非交互 `-p` 模式不会 spawn teammate」。本项目是 headless 编排 | [E: ext-orchestration.md#K]（来源为 code.claude.com 文档，非 DSH） |
| 单个超长 `workflow` run | `workflow` 无 journaling、无 resume；父 turn 全程阻塞到整个 workflow 落定 | [E: gt-orchestration.md#E7, #设计含义1] |

**`workflow` 作为「批」的驱动是唯一合适的选择**，理由是它是五条扇出路径里**唯一会排队而不是失败**的一条（FIFO 信号量 `acquireSlot()`），且支持结构化 schema 返回、`phase()/log()` 叙事事件 [E: gt-orchestration.md#E3, #设计含义1]。

**必须显式配置、不得依赖推导的两个数**：

- `maxConcurrentAgents` 出厂为 `0`，解析式是 `min(16, max(1, availableParallelism()-2))`；**本机实测 `availableParallelism() = 14` → 有效并发 12，硬顶 16**；在 2 核 CI 上会退化成 1 [E: gt-orchestration.md#E4, #未决3]。
- `maxTotalAgents` 引擎默认 1000，per-run 覆写**只能降不能升**；`maxItemsPerCall` 默认 4096 [E: gt-orchestration.md#E4]。**大批量扇出必须主动分批**，因为 `AGENT_CAP` / `ITEM_CAP` 是 fatal，会终止整个 run [E: gt-orchestration.md#设计含义9]。

**`workflow` 的一个设计陷阱必须写进脚本纪律**：`parallel()` / `pipeline()` 把非 fatal 错误吞成 `null`，而 `null` 同时表示「thunk 抛了非 fatal 错」「child 非正常结束」「要了 schema 但没拿到 structured」三件事 [E: gt-orchestration.md#E5, #设计含义9]。**规则 O-3：每个 thunk 必须自己返回 `{ ok: true, ... } | { ok: false, reason }`，绝不依赖 `null` 语义。** 否则「某篇论文抓取失败」与「某篇论文查无此说」会退化成同一个 `null`——对一个以可信度为产品的系统，这是把 ST-U 与 ST-N 混为一谈（两者的区别见 01-CONTRACTS §1.4.1）。

### §2.3 内环 L1 · 覆盖环

| 项 | 内容 |
|---|---|
| **输入** | 冻结 checklist 中尚未闭合的子问题；台账当前的独立簇集合（按 `upstream_id` 归并，见 01-CONTRACTS §5.5） |
| **动作** | 多角度并行查询。中文通道一次派发 3–6 个不同措辞的查询而不是翻页——bocha 单次上限 50 条且**完全忽略分页**（第 1/2/3 页返回相同结果集）[E: ext-chinese-ecosystem.md#设计含义1] |
| **输出** | 候选（见 01-CONTRACTS §9.6）。候选**不是**证据 |
| **写面** | `evidence/<evidence_id>.json`，`evidence_grade = G1`（W-06 的写者，即抓取/检索工具执行器）。〔裁定〕见下 |
| **扇出** | 允许（覆盖率维度） |
| **停机贡献** | Δ独立簇数（SAT-2 的主信号，§4.3） |

**〔裁定〕候选落 `evidence/` 并携带 `evidence_grade = G1`，不新增目录。**
理由：01-CONTRACTS §3.4.1 已经规定 G1 不得作为任何 claim 的承重证据、只能是候选；语义隔离已经由 `evidence_grade` 承担，再加一个物理目录是重复建模，而且要改 01-CONTRACTS §8.1 的布局。
**什么会推翻**：若候选条目的量级使 `evidence/` 的 schema 门（V8.5）或 CAS 的孤儿对象扫描（V8.3）不可用，则应在 §8.1 增设 `candidates/` 并回填 01-CONTRACTS。

### §2.4 内环 L2 · 取证环

| 项 | 内容 |
|---|---|
| **输入** | L1 产出的候选（G1） |
| **动作** | 经中央网关（§6）抓取 → 通道分离 → 快照落 CAS → 写证据卡；`retention_tier` 与 `cache_policy_used` 在 fetch 时刻决定并写入 provenance |
| **输出** | 证据卡（`evidence_grade` ≥ G2，视获取层级） |
| **写面** | W-01（CAS）、W-02（`tool/result.data.meta.evidence`）、W-06（证据卡）。三者的唯一物理写者都是工具执行器 |
| **扇出** | 允许（多来源交叉抓取）；**宽度由网关决定，不由 worker 数量决定** |
| **回传** | 只回传句柄（`evidence_id` + `object_sha256`），不回传正文。对齐 1,000–2,000 token 量级的子 agent 回传上限 [E: ext-orchestration.md#F, #核验表26] |

**上下文卫生是这一环扇出的第二个正当理由，且它是三条独立线共同支持的**：IterResearch 每轮重建 O(1) 工作区（六基准 +14.5pp；交互扩到 2048 次时 3.5% → 42.5%；作为纯 prompting 策略对前沿模型最多 +19.2pp）[E: ext-orchestration.md#E, #核验表23-25]；Anthropic 的子 agent 压缩比 [E: ext-orchestration.md#核验表26]；Context Rot 在 18 个模型上证明长输入退化「often in surprising and non-uniform ways」[E: ext-orchestration.md#G]。在 DSH 的原生 subagent 上这几乎零成本，**应当无条件采纳** 〔依据 00-PREMISE B1 并行可靠买到的三样〕。

### §2.5 内环 L3 · 核验环

| 项 | 内容 |
|---|---|
| **输入** | 一条载荷 claim + 它声称的证据指针。**不含起草时的推理链** |
| **动作** | N 路独立核验，四路各司其职：① 重跑数据（K-D 通道）② 回原文抓字面（`quote_faithful`）③ 口径推演（`metric_frame` 三元组比对）④ 主动反证检索（`counter_evidence_searched`） |
| **输出** | `verdicts/<gate_id>/<claim_id>.json`（GC-2 裁决原件）、`analysis/<claim_id>/`（K-D 工件）、`inferences/<claim_id>.reviewer.md` |
| **写面** | W-07 / K-D 工件 / W-11 的 reviewer 半边。**核验 worker 不写 status**（W-04） |
| **扇出** | 允许（同一条载荷断言的 N 路独立再核验）——这是 00-PREMISE B1 押注的第二处 |
| **身份** | reviewer ≠ producer，走 `spawn` 非 `fork`，跨厂商 `agentOptions.provider`。规范定义见 01-CONTRACTS §5.2 / §5.3 |

**两条不可让步的工程约束**：

1. **核验深度固定，与检索深度无关。** 检索可以扇出到几十路；核验对每条断言的动作是定长的（重抓 → 定位 → 判定 → 记录）[E: ext-incidents-products.md#设计含义4]。依据是本轮最重的一条反向证据：同一模型工具调用从 2 次扩到 150 次（七档 2/10/30/50/70/100/150），Fact-Check 通过率 GPT-5.4 **78.6% → 16.7%**、Claude Opus 4.6 **80.0% → 57.9%**，而 Link Works >92%、Relevant Content >80% 基本不动 [E: ext-orchestration.md#C, #核验表7-10]。
   **限定必须一起带**：摘要写的「approximately 42%」经核算是**两模型绝对百分点降幅的均值 −42.0pp**（相对降幅均值约 53%），且两模型降幅相差近 3 倍；单篇预印本（2026-05-07 v1），仅两个模型做深度消融，**未报相关系数、回归或 p 值**，判定器是 rubric-based LLM-as-a-judge（有人工校准）[E: ext-orchestration.md#核验表6, #U1]。→ **方向可信、量级待我们自证**（M1 的自检基准，§9.3）。
2. **跨厂商独立性在 workflow 内直接声明**：`agent(prompt, { provider, model })`，代码支持 5 个选项（`SUPPORTED_AGENT_OPTIONS` = label/phase/schema/provider/model），README 的 Script contract 段落漏列了 `provider` [E: GROUND-TRUTH-CORRECTIONS.md#A11, gt-orchestration.md#X4]。`agentOptions.provider` 与 `subagentProvider` 的消歧见 01-CONTRACTS §9.25。

### §2.6 内环 L4 · 裁决与组稿环

| 项 | 内容 |
|---|---|
| **输入** | 全部台账（claim + status + verdicts + flags） |
| **动作** | 跨 claim 一致性检查、论证链构建（K-I 的前提闭包）、最终裁决、组稿 |
| **输出** | `prose/` 与 `export/` |
| **写面** | `prose/` 的唯一物理写者是确定性组稿器（W-10）；作者 agent 写 outline 与叙述骨架，**不写数字** |
| **扇出** | **禁止**。这三类任务落在 −70% 那一侧（顺序规划）[E: ext-orchestration.md#核验表15]，且 Anthropic 自述强依赖领域不适合多智能体 [E: ext-orchestration.md#A] |

**为什么可以收回单一上下文**：DeepSeek v4 上下文 1M / 最大输出 384K（as-of 2026-08-17）[E: ext-cost-economics.md#A1]；按语料的推导，一个核验 agent 可同时持有 50–80 篇论文全文 [E: ext-cost-economics.md#设计含义4]。**该推导标 `unverified（推导值）`**——它建立在「典型 arXiv 论文正文抽取后约 40,000–60,000 英文字符 → 12,000–18,000 token/篇」这一未实测的换算上，接入后必须用真实 `usage` 回填 [E: ext-cost-economics.md#E2]。

**GC-2 不得参与生成期**：写作阶段禁止调用同一个 rubric judge 自评再改写——那是对 judge 直接做梯度下降；judge 只在冻结产物上跑一次。规范表述见 01-CONTRACTS §6.4。

### §2.7 keep-if-better 是逐 claim 偏序，不是整篇打分

**规则 O-4**：外环的每一批产出必须通过反回退门才允许合并：新版本的 `verified` claim 集合必须 ⊇ 旧版本的 `verified` claim 集合；产出 claim-level diff（新增 / 升级 / 降级 / **静默消失**）；**静默消失是硬失败，直接打回**。

依据（ACL 2026 Long，五个 Deep Research Agent 的多轮改稿）：agent 能落实**超过 90%** 的用户反馈，同时在 **16–27%** 的既有内容与引用质量上回退，内容型反馈下的 break rate 平均 **31%**；论文明确说**提示工程与「专职改稿子 agent」这两种 inference-time 修法都解决不了** [E: ext-orchestration.md#D, #核验表20-22]。

→ **不要指望再派一个 reviewer agent 能解决这条**。要靠机械 diff。这也是为什么反回退门归 GC-0（离线、无模型参与），不归 GC-2。

### §2.8 跨进程重启后如何续跑（显式步骤，不会自动发生）

**这是本节最容易被写成谎话的地方。** DSH 不会替我们续跑：`goal` 的 `activation` 永不持久化 [E: gt-orchestration.md#A1]；`workflow` 无 journaling / 无 resume [E: gt-orchestration.md#设计含义1]；结算通知在父 dispose 时被 durable 取消 [E: gt-orchestration.md#C3]。因此续跑是**五个显式步骤**：

| 步 | 动作 | 为什么必须显式 |
|---|---|---|
| **R1** | **人类授权**（检查点 CP-5，§7.2）。`goal` 以 disarmed 状态复活，必须有人类授权的 `resume` 重新 arm | harness 强制，不是我们加的 [E: gt-orchestration.md#A2, #设计含义5] |
| **R2** | **从台账重建工作集**：扫 `.arc/`，算出（未闭合 checklist 项 ∪ 因预算而 ST-N 的 claim ∪ 前提变更导致 stale 的推断）。**绝不从会话通知重建** | resume 后的父读不到任何未决通知 [E: gt-orchestration.md#C3] |
| **R3** | **孤儿子代理清算**：`list_agents` 调用**一次**（非轮询）枚举残留的 continuable 子，逐个 `interrupt_agent`；它们已写入台账的记录靠 CAS + 一 claim 一文件天然幂等 | continuable 后台子代理**运行时不设任何上限**，唯一兜底是 `maxDepth`、宿主内存与 LLM 侧 429 [E: gt-orchestration.md#结论摘要1, #设计含义1]；`list_agents` 无游标无上限，只能一次性用 [E: gt-orchestration.md#K4] |
| **R4** | **写新的运行时指纹** `runs/<run_id>/manifest.json`（W-12）。若 `sandbox/mode == danger-full-access`，本次运行全部产物标「权限异常，需人工复核」（01-CONTRACTS V4.5） | 子代理只捕获父会话的**显式** override，不捕获部署默认，也不捕获一次性授权 [E: GROUND-TRUTH-CORRECTIONS.md#A8] |
| **R5** | **起新 `workflow` run**，显式设 `maxConcurrentAgents` 与 `maxTotalAgents`，不依赖 `availableParallelism()` 推导 | 该推导随机器变化（2 核 CI 上退化为 1）[E: gt-orchestration.md#未决3] |

**续跑的幂等断言必须是 live 的，不是离线的。** 本仓库既有流水线从未 live 断言过幂等（`harvest_e2e.sh` 的 run-2 从不断言，实测 run-2 `accepted=8`）[E: GROUND-TRUTH-CORRECTIONS.md#D2]。本项目必须补上：见 01-CONTRACTS V4.4。

### §2.9 可检验断言

- **V-4.4** 外环 run 序列：断言每个 `runs/<run_id>/manifest.json` 都能从上一个 run 的台账状态被独立重算出其工作集（R2 是纯函数）。
- **V-4.5** 负向测试：杀掉进程后重启，断言**没有任何工作自动开始**（CP-5 未授权前必须是静止的）。这条测的是「我们没有把 harness 不提供的能力写进承诺」。
- **V-4.6** `workflow` 脚本静态检查：不存在任何直接消费 `agent()` 返回 `null` 作为业务语义的分支（规则 O-3）。红样本：构造一个返回 `null` 的 thunk，断言脚本把它记为 `{ ok: false }` 而非「无发现」。
- **V-4.7** keep-if-better 反回退门的红样本：喂一个「静默删除一条 `verified` claim」的新版本，门必须非零退出。

---

## §3 扇出的准入判据

> 这是本文件最重要的一节。扇出不是默认动作，是需要过闸的动作。

### §3.1 三处允许、三处禁止（继承自 00-PREMISE B1，不得放宽）

**允许扇出的三处，每处附它买的可测属性** 〔依据 00-PREMISE B1 裁决〕：

| # | 位置 | 买什么可测属性 | 落在哪个内环 |
|---|---|---|---|
| F-A | 覆盖率维度（候选文献检索、多来源交叉抓取、不同子问题并行探索） | 按上游簇去重后的独立来源数 | L1 / L2 |
| F-B | 同一条载荷断言的 N 路独立核验 | `verified` 断言数 / 预算 | L3 |
| F-C | 上下文卫生（每个 worker 短而干净的上下文，回传严格限长） | 单 worker 上下文长度中位数 | L1 / L2 / L3 |

**禁止扇出的三处**：论证链构建、跨 claim 一致性推理、最终裁决。全部收回 L4 的单一上下文。

### §3.2 准入判据 A1–A5（五条全过才允许扇出）

**规则 O-5**：任何一条新的并行边在合入编排前，必须逐条通过下列五条。任一不过 → 该子任务串行执行。

| id | 判据 | 机器可判形式 | 依据 |
|---|---|---|---|
| **A1** | 该子任务有一个机器可判的验收指标 | 存在一个 GC-0 或 GC-1 的门，其输出对该子任务的产物是 pass/fail | 没有客观裁决器的扇出 = 吞吐量，不是质量 〔依据 00-PREMISE B1 并行可靠买到的三样〕 |
| **A2** | 该子任务的**单 agent 基线已被测量**，且低于能力饱和阈值 | `baseline_measured == false` → **禁止扇出**；`baseline ≥ θ_sat` → 禁止扇出 | 见 §3.3 |
| **A3** | 下游存在一个不弱于 worker 的客观裁决步骤 | 该并行边的输出必须流入某个门，而不是流入另一个 agent 的上下文 | 同 A1 |
| **A4** | worker 的工具集在白名单内且**与其他角色不重叠** | 工具集交集检查（见 §3.4） | 判据是重叠度不是数量：「>15 个定义清晰、彼此不同的工具」可以管好，「<10 个相互重叠的工具」会出问题 [E: ext-orchestration.md#H, #核验表45] |
| **A5** | 新增的这条并行边配了一个针对**该边输出**的确定性检查 | CI 中存在该检查及其 red-case fixture | MAST：inter-agent misalignment 与 task verification 两类失败是**扇出新造出来的**，单智能体没有 [E: ext-dr-architectures.md#E4, #D-7] |

**A2 的可失败性是这条闸门成立的关键。** 一个「无法失败的检查」等于没有检查——所以缺省行为是**禁止**：没有基线测量就不许扇出，而不是「没测就放行」。

**MAST 的口径警告**：其被广泛转述的「42% / 37% / 21%」失效分布**在 arXiv 摘要中不存在**，标 `unverified`，**本项目文档中不得使用** [E: ext-orchestration.md#核验表47, #U3]。可用的是：1600+ 条跨 7 个主流 MAS 框架的标注轨迹、150 条建分类学、专家标注 κ=0.88、14 个失败模式聚为 3 类 [E: ext-orchestration.md#核验表46]。

### §3.3 能力饱和阈值 θ_sat：待标定参数

**〔裁定〕`θ_sat = 45%` 作为初始值，标为待标定参数，且在标定前它只作为「禁止扇出」的方向使用，不作为「应当扇出」的依据。**

原文：「tasks where single-agent performance already exceeds 45% accuracy experience negative returns from additional agents」[E: ext-orchestration.md#B, #核验表17]。

**必须随该数字一起说的四条限定**：

1. 来自**单一工作**（其四个载体计为一个来源，见 §1.1）。
2. **R² = 0.373**——只解释约三分之一方差 [E: ext-orchestration.md#核验表18]。
3. 其**六个基准里没有一个是文献研究**；BrowseComp-Plus 最接近但仍是找信息而非评证据 [E: ext-orchestration.md#U2]。
4. 同一工作还给出一条对我们直接不利的结论：**tool-heavy 任务（例：16 工具的业务流）会吃到多智能体协调开销，且效率惩罚随环境复杂度复合增长**——**我们的任务恰恰是 tool-heavy** [E: ext-orchestration.md#B, #结论摘要3]。

**什么会推翻它**：在我们自己的任务族上重测，若拟合不成立或阈值明显不同则重设；**若 R² < 0.2 则该判据整体作废，改用「该子任务是否有客观裁决器」（即 A1/A3）作为唯一准入** 〔依据 00-PREMISE B1 会推翻它的观测〕。

**如何测「单 agent 基线」（否则 A2 不可操作）**：对每个候选扇出的子任务，在 held-out 题集（见 01-CONTRACTS §9.26）上用该子任务**自己的机器可判指标**跑一次单 agent 臂，记录 `baseline`、`n`、`指标名`、`测量日期`，写进 `runs/` 并随该并行边的合入 PR 一起提交。没有这份记录，A2 判 false。

### §3.4 worker 工具集：窄且互不重叠

**规则 O-6**：每个 worker 角色持有一个**封闭的**工具白名单；任意两个角色的白名单交集必须为空（只读的台账查询工具除外）。

〔裁定〕初始角色—工具映射（下表 `<provider>` 指**检索供应商**，见 §6.0）：

| 角色 | 所在环 | 工具白名单 | 显式禁止 |
|---|---|---|---|
| 发现 worker | L1 | `search.<provider>`（经网关）、`ledger.read` | 任何抓取工具、任何写工具、任何绕过网关的供应商直连 |
| 取证 worker | L2 | `fetch.<provider>`（经网关）、`snapshot.commit`、`ledger.read` | 任何检索工具、`run_code`、`bash` |
| 复算 worker | L3-① | `bash`（沙箱内）、`analysis.materialize`、`ledger.read` | 一切网络工具 |
| 字面核验 worker | L3-② | `quote.match`（GC-0，纯本地）、`ledger.read` | 一切网络工具、一切写工具 |
| 口径核验 worker | L3-③ | `frame.compare`、`ledger.read` | 同上 |
| 反证 worker | L3-④ | `search.<provider>`（经网关）、`fetch.<provider>`（经网关）、`ledger.read` | 写工具 |
| 裁决 agent | L4 | `ledger.read`、`structured_output` | **一切网络工具、一切写工具** |

**注意反证 worker 与发现/取证 worker 的工具白名单有交集**——这违反 O-6 的字面。〔裁定〕**允许这一处例外，并把它记为已知的协调开销来源**：反证检索必须能同时发起检索与取证，否则它无法在同一快照内找到反对句（01-CONTRACTS 的 RT-8 要求）。**什么会推翻**：若实测显示该角色与发现/取证 worker 之间出现重复工作或结果污染，则把反证拆成两个串行子步骤，各持一半工具。

**这一层的强制手段只能落在工具边界**：`ctx.tools.guard` 单调否决 / `tools/pre-execute` 的 `deny` / `tools/post-execute` 的 `block(feedback)`。`toolFilter` **不是权限天花板**，且不向下传递——规范表述见 01-CONTRACTS §4.4。

### §3.5 并行粒度优先级：先吃满哪一层

**〔裁定〕优先级 P0 → P3，但 P0 带一个必须先验证的前提。**

| 级 | 路径 | 强制上限 | 本机实测 | 备注 |
|---|---|---|---|---|
| **P0** | Code Mode `run_code` 内部子调用 | `maxParallelSubCalls` 默认 10 | 10 | **仅在 `code` / `both` 呈现模式下存在，而出厂默认是 `native`**；且宿主必须挂 `code-runtime`（`dsh-base` 不含，只有 web-app / headless 有）[E: gt-orchestration.md#J1, #J2, #J3, #X5] |
| **P1** | `workflow` 脚本 `agent()` / `parallel()` | `maxConcurrentAgents` | **12**（硬顶 16） | **唯一会排队而不是失败的路径** [E: gt-orchestration.md#E3, #设计含义1] |
| **P2** | 一条 assistant 消息里并排调 `subagent` 工具 | `maxParallelToolCalls` 默认 10 | 10 | 出厂 `subagent` 是 continuable，调用在 inbox 接受后立即返回 → **这个 10 限制的是「同时在创建中的子代理数」，不是「同时在工作的子代理数」** [E: gt-orchestration.md#设计含义1, #C6] |
| **P3** | continuable 后台子代理 | **运行时不设上限** | — | `dsh-subagent` 整包无 Config，续接管理器无 per-parent 计数；唯一兜底是 `maxDepth`、宿主内存、LLM 侧 429 [E: gt-orchestration.md#结论摘要1] |
| — | one-shot 后台（Task） | `maxConcurrentJobsPerOwner` 10，**超限抛错不排队**，与 `bash(run_in_background)` 共用同一桶 | 10 | [E: gt-orchestration.md#H1, #H3] |

**P0 的前提必须前移验证。** 00-PREMISE B1 的配套约束写的是「先把 `run_code` 内的工具调用级并行吃满（`maxParallelSubCalls` 默认 10）」〔依据 00-PREMISE B1 配套的三条硬约束〕，但该闸门**只在 `code`/`both` 呈现模式下存在，出厂默认是 `native`** [E: gt-orchestration.md#X5]。**〔裁定〕若本 profile 不显式选用 Code Mode 且确认宿主挂了 `code-runtime`，则 P0 层不存在，优先级从 P1 开始。** 这不是可以留到实现阶段发现的事——它决定我们的最细粒度扇出能不能用。已列入 §10 未决。

**P2 的两个陷阱**：① 并行组在遇到第一个非并行安全的调用时**立即中断**，而 `get_goal` / `update_goal` 全是 exclusive——所以「一条消息里放 20 个 `subagent` 调用」只有在中间不夹 exclusive 工具时才连得成一个组 [E: gt-orchestration.md#G2]。② `maxParallelToolCalls` 是**可热改的用户 Settings 项**（下一个 tool group 生效），**不能当安全边界** [E: gt-orchestration.md#G1, #设计含义2]。

**深度**：出厂 `maxDepth = 3` → root(0) → 子(1) → 孙(2) → 曾孙(3)，第 4 层被拒 [E: gt-orchestration.md#C1]。角色分配必须在三层内闭合（01-CONTRACTS §5.3 R-I5）：编排器(0) → 领域 worker(1) → 核验 worker(2)。**「核验者再派攻击者」需要显式提高 `maxDepth` 并记录该决定。**

**一条出厂配置必须显式覆盖**：三个 shipped preset 把 `subagent_fork` 也设成了 `continuable`，而 continuable fork 子会先装 `report` 工具与其 prompt 段落、位于继承历史之前，从而**让全部继承前缀的 KV cache 失效**。本 profile 应显式把 `subagent_fork` 配回 `one-shot` 以保住 fork 的缓存收益 [E: gt-orchestration.md#X3]。（这与 §5.3 的缓存前缀约束是同一件事的两面。）

### §3.6 扇出宽度是四个上界的最小值

```
width(subtask) = min(
    W_admit,     // A1–A5 全过才 > 1，否则 = 1
    W_gateway,   // 中央限速网关按 host 许可的瞬时并发（§6）
    W_budget,    // 预算的函数：W ∝ 剩余 E 与剩余 N_search（§5）
    W_path       // 所选扇出路径的硬上限（§3.5 表）
)
```

**`width` 是预算的函数，不是常数** [E: ext-cost-economics.md#风险4]。这条必须写进代码，否则一次扇出 + 重试风暴很容易触顶 **LLM 侧**的账号级并发（DeepSeek pro 500 / flash 2500，**429 无排队**，可免费申请扩容，as-of 2026-08-17）[E: ext-cost-economics.md#A5]。注意这一条与 §6 的检索供应商限速是**两套独立的墙**：LLM 侧宽（2500 路 flash），检索侧窄（最紧的是 arXiv 的 0.33 rps 且禁并发）——**瓶颈几乎必然先出现在检索侧和本机，不在 LLM 侧**。

**并行的隐性成本我们自己实测到过**：本轮多个兄弟调研 subagent **共享 WebSearch 会话配额**，导致至少三个维度的调研在第 2–14 次检索时配额耗尽，被迫降级到 serper/curl 兜底，并各自留下「反证检索做得不够」的自陈 [E: ext-orchestration.md#U9, ext-academic-apis.md#未决8, ext-incidents-products.md#方法学与时效风险]。**这是一条来自我们自己运行的、关于扇出的负面数据点**，必须进 `W_gateway` 的建模。

### §3.7 可检验断言

- **V-4.8** 每条并行边在 `runs/` 下有一份 A1–A5 的准入记录；缺任一条即门红。
- **V-4.9** 负向测试：提交一条无 `baseline_measured` 记录的并行边，准入门必须拒绝（A2 的缺省行为是禁止）。
- **V-4.10** 角色工具白名单交集检查：除 §3.4 明列的一处例外外，任意两角色交集为空；新增交集需在本文件登记后才允许。
- **V-4.11** 每条并行边在 CI 中有对应的确定性检查与 red-case fixture（A5）；fixture 必须能使该检查非零退出。

---

## §4 停止与饱和

### §4.1 空白位：被调研系统的停止条件要么内容盲、要么不可复现

| 系统 | 停止条件 | 问题 |
|---|---|---|
| Jina DeepSearch | `while (tokenUsage < tokenBudget && badAttempts <= maxBadAttempts)` | **内容盲**：只看预算与失败次数 [E: ext-dr-architectures.md#核验表28] |
| dzhng/deep-research | breadth 默认 4（3–10）、depth 默认 2（1–5） | **内容盲**：固定递归参数 [E: ext-dr-architectures.md#核验表29] |
| LangChain ODR | `max_researcher_iterations=6`、`max_react_tool_calls=10`、`max_concurrent_research_units=5` | **内容盲**：固定计数（源码默认值，抓取时点 2026-08-17，存在版本漂移风险）[E: ext-dr-architectures.md#核验表27] |
| EDR / "Don't Stop Early" | 执行前写死的结构化 checklist，「enforces evidence-based completion criteria」 | **内容感知，但不可复现**：清单项的满足与否仍由 LLM 判定 [E: ext-dr-architectures.md#D1] |
| ScaffoldAgent | utility 三分量（retrieval gain / structural coherence / trial-generation quality）引导 termination | **半内容感知，不可复现**：三分量里 retrieval gain 半客观，后两个是 LLM 判断 [E: ext-dr-architectures.md#D2] |

**因此这是本项目的空白位**：一个**同时内容感知且可复现**的停机判据。做法是采纳 EDR 的动作（执行前冻结 checklist），但**不停在 EDR 停的地方**——每个清单项落成一个返回 `pass/fail` 的可重跑脚本 [E: ext-dr-architectures.md#D-1]。

### §4.2 停机判据 STOP

```
STOP(run, r) := SAT-1 ∨ SAT-2 ∨ SAT-3 ∨ SAT-4          // r = 当前外环轮次

SAT-1  覆盖闭合
       ∀ item ∈ checklist(run) :  verdict(item) == pass
       // checklist 在 CP-1 通过时冻结，写入 runs/<run_id>/checklist.json，hash 入 manifest
       // not_applicable 不计为 pass（见 §4.6）

SAT-2  检索饱和（见 01-CONTRACTS §9.14）
       ∃ 连续 k 个 "有效派发轮" r-k+1 .. r，满足
         Δcluster(每轮) == 0            // 主信号，model-free
       ∧ Δstatus_up(每轮) == 0          // 并列信号，model-influenced（见 §4.5）

SAT-3  预算耗尽
       E ≥ E_cap  ∨  N_search ≥ N_cap   // 双计数器，任一触顶（§5.4）
       → budget_state = exhausted（见 01-CONTRACTS §1.3 与 F-11）

SAT-4  空转
       futile_ratio(最近 k 轮) ≥ θ_futile
```

**四个 SAT 全部的输入只有三样：台账文件、session 日志事件、冻结的 checklist。** 三样都可存档、可重放，因此 `STOP` 与 01-CONTRACTS §1.5 的 `S` 同形——**是一个可以对存档输入重跑并得到逐字节相同结果的纯函数**。

**我们不声称 `STOP` 是 model-free。** `Δstatus_up` 的一部分（ST-A 的取得）经过 GC-2，而 GC-2 消费模型裁决（01-CONTRACTS §6.1）。我们声称的是**可复算性**：同一批存档输入重跑得到同一个停机决定。这两件事必须分开说——把「可复算」讲成「无模型参与」正是本项目要消灭的那类混淆。

### §4.3 内容感知从哪来：两个计数器

- **`Δcluster(r)`** = 第 r 轮新增的、按 `upstream_id` 归并后的**独立簇**数（01-CONTRACTS §5.5 / §9.5）。**这是主信号，纯 GC-0/GC-1，model-free。**
- **`Δstatus_up(r)`** = 第 r 轮由门写入的 status 提升事件数（`claims/*.status.json` 的 append-only 序列上，状态沿 01-CONTRACTS §1.5.1 的偏序向上移动的次数）。**并列信号，model-influenced。**

**报告必须同时给两条曲线**，且分子分母同露（01-CONTRACTS §9.28 Goodhart 防线）。

用「新增独立簇数」而不是「新增来源数」，是因为已知的硬样本会让后者虚高：11 个中文域名回溯到同一条 Nikkei Asia 上游；8 个域名回溯到同一篇 BadRAG；Unpaywall 与 OpenAlex 是同一后端 [E: ext-security-injection.md#E3, #A3, ext-academic-apis.md#G]。规范表述见 01-CONTRACTS §5.5。

### §4.4 防「不派发洗收敛」

**攻击形态**：worker 什么都不做（或只做零成本动作），于是 `Δcluster = 0`、`Δstatus_up = 0`，SAT-2 成立，系统宣布「饱和」并停机——把「我们没找」洗成「没什么可找的」。这与 01-CONTRACTS §1.4.1 要区分 `unverified` 与 `not_covered` 是同一类病，只是发生在编排层。

**机器可判的防线：「有效派发轮」的定义。** 一轮 r 是有效派发轮，当且仅当**同时**满足：

```
(a) 事件侧：session 日志中属于第 r 轮的、工具名 ∈ 检索/取证工具集的
    tool/call 或 tool/code-dispatch 事件数 ≥ D_min
(b) 台账侧：第 r 轮向台账写入的记录数 ≥ D_min，其中每条记录是
    一张证据卡，或一条显式的 no-result 记录
    （no-result 记录必须携带：归一化 query 串、检索供应商 id、fetched_at、
      http_status 或供应商返回码）
```

**不满足 (a)∧(b) 的轮次不计入 SAT-2 的 k 窗口**，并使 `idle_rounds += 1`。`idle_rounds` 连续超限 → 外环**不是停机成功，而是进入 blocked**，路由到 CP-5（§7.2）由人裁定。

两侧都要检查的原因：只查 (a) 会被「发一堆请求但不落台账」绕过；只查 (b) 会被「凭记忆编造台账条目」绕过——后者正是 01-CONTRACTS §4.4 末条产物级兜底要拦的形态。

**`no-result` 记录是这条防线的关键零件**：它把「我找了，没找到」变成一条**可审计的、带查询串的正向记录**，而不是一个静默的空集。没有它，「不派发」与「派发但无收获」在台账上不可区分。

### §4.5 防「空壳派发」

**攻击形态**：为了满足 §4.4 的 (a)，worker 发一堆无意义调用；或者派发了但产出不可验收，于是每轮都「有效」，系统永远不停，烧完预算才由 SAT-3 兜底。

**机器可判的防线：`futile` 派发的定义。** 一次派发是 `futile`，当且仅当满足其一：

```
f1  它有 tool/call 事件，但零台账增量（既无证据卡也无 no-result 记录）
f2  它的 worker 返回 null —— 即要了 schema 却没拿到 structured value
f3  它写入的记录全部是重复内容（CAS 命中已有 object_sha256 且 evidence_id 已存在）
```

`f2` 的一手依据：`workflow` 的 `agent(prompt, { schema })` 拿不到 structured 就返回 `null`；且**一次干净的 turn 若没提交必需的结构化值，`stopReason` 报 `error`，driver 不会重问** [E: gt-orchestration.md#E5, #设计含义3]。→ **脚本必须把 `null` 当「未验证」，不能当「无发现」**（与规则 O-3 同源）。

`futile_ratio = futile 派发数 / 总派发数`，逐轮记账。SAT-4 用它停机——**继续派发只在烧钱时，停机是正确行为**，但停机报告必须显式标注 `futile_ratio` 及其分子分母。

### §4.6 停机时必须落什么

**停机不等于成功。** 停机报告（`gate-reports/<run_id>/stop.json`，写者是门代码，W-08）必须包含：

1. 触发的是哪个 SAT（可以多个）。
2. checklist 逐项 verdict。**`not_applicable` 单列，不计入 pass**——一个 `power = 0.00` 的 "consistent" 与一个 `power = 0.90` 的 "consistent" 证据强度差一个数量级，丢掉功率就是制造假安全。规范表述见 01-CONTRACTS §6.2.1。
3. 未 pass 的清单项 → 对应 claim 落 ST-N，并携带原因（01-CONTRACTS §1.5 第 0 步）。**禁止把未 pass 的项从报告里省掉。**
4. 两条曲线：`Δcluster(r)` 与 `Δstatus_up(r)`，逐轮。
5. `futile_ratio`、`idle_rounds`、双计数器的终值与上限。

**SAT-3 触发时，全部未完成 claim 的 `budget_state` 置 `exhausted`**，由 `S` 的 0f 走到 ST-N（01-CONTRACTS §1.5）。这是「预算耗尽不许洗成结论」的机制实现。

### §4.7 诚实标注

- **「检索饱和」这个概念在语料中没有外部证据支持**，它是本项目自建的工程停机条件，必须自证——规范表述与「什么会推翻它」见 01-CONTRACTS §9.14。本节给的是它的机器可判操作化，不是它的正当性证明。
- `k`、`D_min`、`θ_futile`、`idle_rounds` 上限**全部是本文件的裁定值**（§8 参数表），没有一个来自外部测量。它们的第一次标定在 M1。
- SAT-2 的两条曲线在 M1 之前**不能**被用来对外声称「我们知道什么时候够了」。

### §4.8 可检验断言

- **V-4.12** `STOP` 是纯函数：对同一批存档输入（台账快照 + session 日志 + 冻结 checklist）重跑，得到逐字节相同的停机决定与停机报告（`generator_version` / `inputs_hash` 除外）。
- **V-4.13** **红样本 RS-1（不派发洗收敛）**：构造一个连续 k 轮零工具事件、零台账增量的轮次序列，断言 SAT-2 **不成立**，且 `idle_rounds` 达限后 run 进入 blocked 而非 complete。
- **V-4.14** **红样本 RS-2（空壳派发）**：构造 k 轮，每轮有 ≥ D_min 次工具调用但零台账增量，断言这些轮不计入 SAT-2 窗口且 `futile_ratio = 1.0`，SAT-4 触发。
- **V-4.15** **红样本 RS-3（no-result 伪造）**：构造一条无供应商 id / 无归一化 query 的 `no-result` 记录，断言台账 schema 门（01-CONTRACTS V8.5）非零退出。
- **V-4.16** 停机报告中 `not_applicable` 的计数不为零时，断言不存在任何因该项而被判 pass 的 claim（覆盖 01-CONTRACTS F-21 的路径）。
- **V-4.17** 停机报告必须同时含 `Δcluster` 与 `Δstatus_up` 两条曲线；缺任一条即门红。

---

## §5 预算与成本

### §5.1 双计数器

**规则 O-7：预算有且只有两个计数器——`E`（token 当量）与 `N_search`（检索次数）。预算闸门必须同时管这两个，任一触顶即触发状态转移。**

理由是成本结构：Simon Willison 的单次 deep research 实测，总花费 $1.10 中 **$0.77（70%）是 77 次网页搜索的调用费**，token 只占 $0.304 [E: ext-cost-economics.md#C1]。**口径警告：n = 1，一次运行、一个任务、一个模型，不是平均值**；但算术闭合校验通过（60,506 × $2/1M + 22,883 × $8/1M = $0.3041，与作者所述吻合），内部自洽 [E: ext-cost-economics.md#C1]。
在 DeepSeek 的价格水平上这个比例只会更极端——DeepSeek 的 token 比 o4-mini 便宜约 3–6×，而 serper 的单价并不便宜同样的倍数 [E: ext-cost-economics.md#设计含义3]。**只管 token 会漏掉一半成本。**

### §5.2 `E` 的定义与 DeepSeek 特化的塌缩形式

通用式 [E: ext-cost-economics.md#设计含义1]：

```
C_run = Σ_agents [ T_miss·P_miss + T_hit·P_hit + T_out·P_out ]   ← token 项
      + N_search · P_search  + N_rerank · P_rerank + C_fixed      ← 检索与其他外部服务
```

DeepSeek 特化后整张价卡塌缩成一个基准数 × 两个开关（as-of **2026-08-17**，价卡生效于 **2026-08-16 16:00 UTC**）：

```
P_miss(tier, t) = B(tier) · K(t) · $0.22 / 1M
P_hit           = P_miss / 30
P_out           = P_miss · 3
    B(flash) = 1, B(pro) = 3          ← 模型分层，精确 3×
    K(off-peak) = 1, K(peak) = 2      ← 分时，峰时 01:00–04:00 与 06:00–10:00 UTC

有效输入当量  E := T_miss + T_hit/30 + 3·T_out
C_tokens      =  B · K · E · $0.22 / 1,000,000
```

[E: ext-cost-economics.md#A1, #设计含义1]

`(T_miss, T_hit, T_out)` 三者都能从 `usage.prompt_cache_hit_tokens` / `prompt_cache_miss_tokens` / `completion_tokens` 直接读到 [E: ext-cost-economics.md#A4]。

**`0.22`、`30`、`3`、峰谷窗口全部是配置项，不是代码常量。** DeepSeek 在 12 个月内至少三次改动计价结构（2025-09 取消谷时折扣 → 2026 年中重新引入 → 2026-08-16 全线上调）[E: ext-cost-economics.md#A8]。价卡进配置文件，带 `fetched_at` 与来源 URL；启动时若超龄则告警而非静默使用 [E: ext-cost-economics.md#设计含义6]。这与 01-CONTRACTS F-25 的 `as-of-stale` 是同一条纪律在编排层的实例。

**Batch API 在 DeepSeek 上不存在。** 三处官方页面（文档导航 / 定价页 / Rate Limit 页）一致缺失 [E: ext-cost-economics.md#A7]。**不要在任何计划里写「用 Batch API 拿 50% 折扣」——上一轮正是在这里出的错** [E: ext-cost-economics.md#设计含义2]。替代品是谷时调度，杠杆量级相近但性质完全不同：它是钟点不是队列，DeepSeek 不替我们排队；且**不给任何吞吐豁免**，并发上限与 429 无排队在谷时完全一样 [E: ext-cost-economics.md#设计含义2]。

### §5.3 缓存：可用，但有一条硬架构约束

DeepSeek 的磁盘 KV cache **默认对所有用户开启、无需改代码、无写入费、无存储费**；命中部分降至 1/30 [E: ext-cost-economics.md#A4, #设计含义2]。

**架构约束（这是本节对编排形状影响最大的一条）**：缓存按请求边界切分 cache prefix unit，**必须完全匹配（"fully matches"）**某个已持久化的前缀单元才算命中 [E: ext-cost-economics.md#A4]。→ **所有子代理必须共享逐字节相同的前缀**（system prompt + 工具定义 + 共享上下文），**任何随机化、时间戳、agent 编号、run_id 必须放在前缀之后**。这条与 §3.5 末尾「把 `subagent_fork` 配回 `one-shot`」是同一件事的两面：continuable fork 子会在继承历史**之前**插入 `report` 工具与其 prompt 段落，从而让全部继承前缀的缓存失效 [E: gt-orchestration.md#X3]。

**三条不许洗白的限定**：

1. **TTL 无保证**（"usually within a few hours to a few days"），且是 **best-effort，不保证 100% 命中** [E: ext-cost-economics.md#A4]。→ **不能把缓存命中当作确定性收益写进预算**；悲观预算按 `h = 0` 算，实际账单按 `usage` 回填。
2. **本次涨价中缓存命中输入的涨幅最大**（峰时约 12×，基于二手旧价推导，旧价标 `unverified`）[E: ext-cost-economics.md#A3]。→ `E` 公式里的 `30` 必须是配置项；不要把架构建立在「缓存必然便宜」的假设上 [E: ext-cost-economics.md#风险2]。
3. 输出价是输入价的 3 倍，所以**缓存主要救「长上下文、短输出」的证据勘探 agent；对「长输出」的组稿 agent 几乎无效** [E: ext-cost-economics.md#设计含义2]。这正好与我们「散文薄」的定位同向：一篇一万字中文成稿 ≈ 6,000 输出 token，pro 谷时约 $0.0119——**中文成稿本身的 token 成本可以忽略** [E: ext-cost-economics.md#A6]。

### §5.4 双闸门与状态转移

```
budget_state:  ok  →  degraded  →  exhausted        // 见 01-CONTRACTS §1.3
    ok → degraded    :  E ≥ α·E_cap  ∨  N_search ≥ α·N_cap        〔裁定〕α = 0.8
    degraded → exhausted : E ≥ E_cap  ∨  N_search ≥ N_cap
```

- `degraded` 的后果：`S` 的 2e 降一档 + F-11（01-CONTRACTS §1.5、§7.2）。编排层的后果：`W_budget` 收缩，扇出宽度下降（§3.6）。
- `exhausted` 的后果：`S` 的 0f → ST-N + F-11。编排层的后果：SAT-3 触发停机（§4.2）。

**〔裁定〕`α = 0.8`。** 理由：需要一段「知道快没钱了但还能有序收尾」的区间，否则预算耗尽会发生在一次扇出的中途，留下一批半成品 claim。**什么会推翻**：若实测显示 `degraded` 区间内的产出质量与 `ok` 区间无差别（降一档是过度惩罚），或 0.8 太晚导致收尾不完整，则重设。

**闸门必须在调用前判定，不是调用后记账。** 三个已知的会炸预算的乘数必须有硬闸：Tavily research 单次可吃 15–250 credits（250 倍方差）、Firecrawl 的 +4 credits 进阶模式与 PDF 按**页**计费、Jina 的 ReaderLM-v2（3 倍 token）[E: ext-web-providers.md#D6]。Jina 有现成的 `X-Token-Budget` 可直接当熔断器 [E: ext-web-providers.md#D6]。

### §5.5 预算的分配单位是 claim，不是 run

**规则 O-8**：成本以 claim 为单位记账，`每个 verified claim 的边际成本` 是一等指标。

依据：准确率从 45% 抬到 58%（+13pp）成本要涨 8×（$300 → $2,400 CPM）[E: ext-cost-economics.md#C2]。**口径警告（严重）**：这是 **Parallel 自己发布的、关于自己竞争对手的**数据，属厂商自利数据，未经独立复现，且是 2025-08 的基准（距今约 12 个月）；**竞品那几行必须标 `unverified`**，只有「Parallel 自家产品的挂牌 CPM」可标为厂商挂牌价 [E: ext-cost-economics.md#C2]。可用的是那条定性形状——**质量是买来的，且边际成本陡峭**——它与「token 用量单独解释 80% 方差」互相印证（后者的口径见 §5.7）。

→ **不要设一个全局的「质量档位」，要设 per-claim 的。** 一次运行里绝大多数 claim 是低风险的（背景陈述、方法描述），少数是载荷 claim（见 01-CONTRACTS §9.1 / §9.2）。把 8× 的预算花在载荷 claim 上，其余用 flash 一遍过 [E: ext-cost-economics.md#设计含义5]。

**模型分层**（B(pro)/B(flash) 精确 3×）：flash 承担有确定性验收的任务（检索、抽取、去重、格式化、初筛、结构化字段提取）；pro 承担产品本身（跨证据冲突裁决、逻辑推断链构造、终判档裁决）。**不要为省钱把裁决环节降级到 flash——那是拿产品换 3 倍的一个小数** [E: ext-cost-economics.md#设计含义2]。

### §5.6 记账为什么按总量 token，以及一处必须更正的跨文档冲突

**「预算按总量 token 记账」的理由是 DSH 不持有 provider 价目表**——规范表述与被证伪的旧理由见 01-CONTRACTS §4.3。本文件只补一条编排层的操作细节：per-step 的 `inputTokens` / `cacheReadTokens` / `cacheWriteTokens` / `outputTokens` **逐 step 都在 session 日志里**（有实测样本），所以 `budget/` 由编排层从日志 fold 出（W-13）[E: GROUND-TRUTH-CORRECTIONS.md#A5, #E3]。预算 gate 用 `ctx.tokenMeter.measure()`（与 compaction 同源），但它是 4 字符/token 的固定启发式、**对 CJK 与 JSON schema 系统性低估**，不能用作账单口径（01-CONTRACTS §4.3）。

**⚠️ 一处必须更正的跨文档冲突。** 00-PREMISE B9 的裁决写着「预算即代码：用运行时原生旋钮（`maxBudgetUsd` / 并发上限 / 深度上限），不自建预算中间件」〔依据 00-PREMISE B9 裁决〕。但：

- `maxBudgetUsd` / `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` / `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` 的来源是 **code.claude.com 文档，即 Claude Agent SDK，不是 DSH** [E: ext-orchestration.md#K]。
- DSH 一手事实：**`maxParallelToolCalls` 之外没有任何 token / 成本闸**；goal README、workflow README、ralph README 都各自声明「无 token 预算词汇」[E: gt-orchestration.md#设计含义7]；ralph 的 Known Limitations 逐字写「Only round count bounds aggregate effort」——无 token / 价格 / 时长预算 [E: gt-orchestration.md#F4]。

**〔裁定〕以 DSH 一手为准：本运行时不存在原生的美元预算旋钮。「预算即代码」这条纪律保留，但它的落点是我们自建的闸，而不是 harness 送的旋钮。** 强制点只能落在工具边界（01-CONTRACTS §4.4 的三层：`ctx.tools.guard` 单调否决 / `tools/pre-execute` deny / `tools/post-execute` block）。并发与深度确有原生旋钮（§3.5），美元预算没有。
**什么会推翻**：若后续版本的 DSH 引入等价旋钮，且在已安装包里可被 grep 到，则改回用原生旋钮。**本条已列入 §10，需回填 00-PREMISE B9。**

### §5.7 必须随成本数字一起带的口径

- **「多智能体用 15× token」的分母是 chat，不是单 agent。** 原文是「agents 大约用 4× 于 chat，multi-agent 大约用 15× 于 chat」；「多智能体是单智能体的 15 倍」是错误转述，正确的是 15/4 ≈ 3.75×（我方推导，仅作量级参考）[E: ext-orchestration.md#核验表3-5, ext-cost-economics.md#F]。
- **「token 用量单独解释 80% 方差」是在 BrowseComp 上的方差分解**（三因子合计 95%），**不是**那个拿到 90.2% 的内部 research eval 上的，**也不是一条因果律** [E: ext-orchestration.md#核验表2]。
- **Anthropic 侧的全部成本参照已过时**：90.2% / 15× / 80% 都基于 2025 年的 Opus 4 / Sonnet 4；且 Claude 4.7 及以后换了 tokenizer，同样文本约多出 30% token——任何基于旧模型实测推出的预算算术要整体上调约 30% [E: ext-orchestration.md#U6, #核验表42]。
- **serper 的「starting at $0.30 / 1000」是最高量档口径，不是新用户实付价。** 实际入门档按 $1.00/千次建模（Starter $50 / 50k credits）；官方 `/pricing` 页返回 404，档位表本轮未取到一手确认，标 `unverified` [E: ext-cost-economics.md#D3, ext-web-providers.md#B]。
- **bocha 的单价三个数相差 36×**（目录价 ¥0.036/次 vs 资源包 ¥3.6/千次 vs「约 ¥1/千次」），官方定价页托管在需登录的飞书 wiki、正文 DOM 为空，全部 `unverified`。**这是当前成本模型里最大的数值空洞——检索侧占总成本约四成，而其中一半的单价不确定。接入前必须用真实账单实测** [E: ext-cost-economics.md#D4, #未决4, ext-web-providers.md#未决3]。

### §5.8 可检验断言

- **V-4.18** 每次运行落一份 `budget/usage.json`，含逐 agent 的 `(T_miss, T_hit, T_out)` 与当时的 `B`、`K`；账单可事后按 §5.2 的式子完全重算。
- **V-4.19** 预算闸门的红样本：喂一批使 `N_search` 超限而 `E` 远未超限的调用，断言闸门在**调用前**拒绝，且 `budget_state` 转 `exhausted`（证明两个计数器都是活的，不是只有 token 那一个）。
- **V-4.20** 价卡文件含 `fetched_at` 与来源 URL；超龄时启动告警。红样本：把 `fetched_at` 回拨，断言告警触发。
- **V-4.21** 前缀稳定性检查：对同一 profile 的 N 个子代理请求，断言其请求前缀的字节哈希相同（缓存架构约束的机器检查）。红样本：在前缀里插入 run_id，断言检查失败。
- **V-4.22** 文档 lint：本仓库任何文档中出现「Batch API」与「DeepSeek」共现且未标注「不存在」，即失败。

---

## §6 检索资源治理

### §6.0 一处必须先消歧的命名

本节大量出现 `provider` 一词，指的是**外部检索/抓取服务商**（serper / bocha / Exa / Brave / Jina / Firecrawl / SerpApi / Tavily 以及学术 API）。**这是第三个义项**——01-CONTRACTS §9.25 只消歧了两个（`agentOptions.provider` = LLM 路由；`subagentProvider` = subagent 传输后端）。本节一律写作**检索供应商**或在表中写 `provider / 端点` 并由上下文限定；**该第三义项需回填 01-CONTRACTS §9.25，已列入 §10。** 在回填之前，本节任何裸 `provider` 均按「检索供应商」读。

### §6.1 中央限速网关是硬需求

**规则 O-9：所有出网请求经单一网关；网关是独立进程（或 SQLite + 文件锁的跨进程实现）；子代理不持有裸 API key。**

三条依据，缺一不可：

1. **子代理可能是独立进程，任何「每 agent 内存计数器」的方案在超并行下必然击穿** [E: ext-web-providers.md#D2]。
2. **DSH 侧没有主动限流**：在 `dsh-llm` 与 `dsh-llm-deepseek` 中 grep `concurren|semaphore|inFlight|maxSockets` **零命中** → 限流是被动的（429 + 退避），不是主动的 [E: gt-orchestration.md#I6]。出厂重试策略是 normal / **2 次** / 500ms→10s / ±10% jitter / 5 个 retryable code；`always` 模式**无次数上限**，会重试永久性失败（认证、配额、非法请求）[E: gt-orchestration.md#I2, #I5]。
3. **学术 API 侧的硬 RPS 直接封顶扇出**：20 个并行 agent 各自发语义检索，平均每个要等 20 秒 [E: ext-academic-apis.md#D1]〔依据 00-PREMISE B1 反对证据8〕。**并行度必须由中央网关决定，不能由 subagent 数量决定。**

### §6.2 分级：per-host 令牌桶 / 串行队列 / 滑动窗口

**桶的单位不统一，所以检索供应商抽象层不能只暴露 `rateLimit: number`。** 建议形状 `{ unit: 'qps'|'rpm'|'concurrent'|'per_hour', value, scope, source: 'official'|'derived'|'assumed', verifiedAt }`；`source: 'assumed'` 的桶必须持续告警，逼着人去补一手数字 [E: ext-web-providers.md#D7]。

**学术侧的限速值与 01-CONTRACTS §6.3 第 5 条同源；若两处数字出现分歧，以 01-CONTRACTS 为准。** 本节补的是队列**形态**（令牌桶 / 串行队列 / 滑动窗口）与商用检索供应商侧——这两块 01-CONTRACTS 不覆盖。

**学术侧（as-of 2026-08-17）** [E: ext-academic-apis.md#D2, 01-CONTRACTS §6.3 第 5 条]：

| 级别 | 源 | 上限 | 队列形态 |
|---|---|---|---|
| **最紧** | **arXiv** | **1 请求 / 3 秒（≈0.33 rps）且禁止并发连接** | **必须是串行队列，不能是令牌桶** |
| 最紧 | Semantic Scholar（有 key） | 1 rps（官方措辞 "introductory"，随时可变） | 令牌桶；**不应进关键路径**（keyless 实测已直接 429）[E: ext-academic-apis.md#未决3] |
| 最紧 | OpenAlex 语义检索 | 1 rps | 令牌桶 |
| 最紧 | CORE（免注册） | 5 单请求 / 10 秒（≈0.5 rps） | **本轮实测不可达**（两次 40s 超时 + 文档页 403）→ **在实机验证连通性之前不进任何路径** [E: ext-academic-apis.md#未决1] |
| 中间 | DOAJ | 2 rps | 令牌桶 |
| 中间 | Crossref polite | **列表 3 rps / 单条 10 rps**。⚠️ **「polite pool = 50 rps」是 2025-12-01 之前的值，现已失效 16 倍** | 令牌桶 |
| 中间 | NCBI | 3 rps（无 key）/ 10 rps（有 key） | 令牌桶 |
| 中间 | Europe PMC | **未公布** → 保守设 3 rps + 指数退避 + 熔断 | **未文档化的限速比严格的限速危险，因为没有预警** |
| 宽松 | OpenAlex 常规 | 100 rps | 令牌桶 |

**商用检索/抓取侧（as-of 2026-08-17）** [E: ext-web-providers.md#D2, #核验表A]：

| 级别 | 检索供应商 / 端点 | 一手上限 | 备注 |
|---|---|---|---|
| **P0** | Brave **Answers** | 2 QPS | 三个子代理同时发一次就超 |
| P0 | Exa `/search`、`/answer` | 各 10 QPS | 扇出 20 路语义检索直接 429 |
| P0 | Tavily `/research` | 20 RPM | 每 3 秒才 1 次，且单次可能吃 250 credits |
| P0 | Tavily `/crawl` | 100 RPM（**Production 也不涨**） | 唯一不随环境升级的端点 |
| P1 | Firecrawl | 并发浏览器 Standard 50 **且** `/scrape` 500 RPM | **两套独立限制**，必须建模为 `min(并发槽, RPM 桶)` |
| P1 | SerpApi | Production 3,000 次/小时 | **小时配额语义 → 滑动窗口计数器，不是令牌桶** |
| P2 | serper | 50 QPS（Starter 档） | 扇出主力 |
| P2 | Brave **Search** | 50 QPS | 独立索引，值得当二号发现源 |
| P2 | Jina Reader `r.jina.ai` | 500 RPM（付费）≈8.3 QPS | 取证主力 |
| P2 | Exa `/contents` | 100 QPS | **发现与取证必须拆成两个桶**（比它的 `/search` 宽 10 倍）|
| **P3** | bocha / LangSearch | **未知** | 按 1 QPS 保守接，拿到一手数字前持续告警 |

**一条被广泛转抄的假数字必须点名**：「Tavily `/search` 10 QPS、`/contents` 100 QPS」与 **Exa 官方限速表逐字相同**，而 Tavily 无 `/contents` 端点、官方只发 RPM——判定为把 Exa 的表张冠李戴，多站转抄形成假共识 [E: ext-web-providers.md#核验表A T-FALSE]。同类：「Jina 并发 2 / 50 / 500」在 2026-08-17 浏览器实读官方表中不存在（只有 RPM/TPM 两列），标 `unverified`。

**规则 O-10：任一子代理收到 429，整个供应商桶集体退避**，而不是只让那个 agent 睡——否则其余子代理会继续撞墙、把退避时间无限拉长 [E: ext-web-providers.md#D2]。Tavily 的 429 带 `retry-after` 头。

### §6.3 绝不暴露给子代理的检索供应商

**规则 O-11**：下列检索供应商 **只由编排层在单点调用**，不进任何 worker 的工具白名单：

| 检索供应商 | 理由 |
|---|---|
| **Brave Answers** | ① 2 QPS，三个子代理并发就超 ② **它替你做了总结，等于把「证据判定」外包给别人的模型**，与本项目「机器判定可追溯」的定位直接冲突 [E: ext-web-providers.md#D3] |
| **Exa `/search` / `/answer`** | 10 QPS 是硬墙；只在 serper + Brave 都没打中时由编排层升级调用 [E: ext-web-providers.md#D3] |
| **Tavily `/research`** | 20 RPM + 单次最高 250 credits（相对 basic search 1 credit 是 250 倍方差）[E: ext-web-providers.md#核验表B] |
| **SerpApi** | 吞吐结构与超并行冲突、单价最高；只在「这条证据必须站得住且可能被质疑抓取合法性」时打一发（Production+ 档带法务保险），**不做扇出** [E: ext-web-providers.md#D3] |

**还有一类必须由网关而非 worker 处理的：合规红线。**

- **Brave 结果不得长期落盘**（除非买带 storage rights 的计划，而该计划的名称与价格本轮未取到一手）。方案：Brave 返回只用于**路由决策**（决定去抓哪个 URL），落盘的是从原站取回的全文 + 原始 URL；Brave 供应商适配器的返回对象打 `ephemeral: true`，序列化器**拒绝写盘** [E: ext-web-providers.md#D5, #未决8]。
- **Jina 免费额度是 CC-BY-NC**：用户写课程论文属非商业可用，但插件若对外分发或商用必须走付费 key [E: ext-web-providers.md#D5]。
- **robots 检查主动打开**（Jina 侧设 `X-Robots-Txt`）：Firecrawl 与 Jina 的 ToS 都不承诺 robots 合规，Jina 的检查是显式 opt-in [E: ext-web-providers.md#D5]。「是否遵守 robots」必须是证据元数据的一部分。留存分档与降级触发器（含 `T3-ROBOTS`、`T9-RATE`、`T12-UNREACHABLE`）的规范定义见 01-CONTRACTS §8.6.3。

**T0 名录全部本地化**：撤稿库 / 劫持刊表 / 指纹词典下载一次、本地查 N 次，**扇出的子 agent 不打网络**。这是超并行扇出时唯一不会被限速掐死的形态——规范表述见 01-CONTRACTS §6.3 第 4 条与 W-09。

### §6.4 跨 agent 的检索结果缓存层

**规则 O-12**：网关持有一个跨 agent 的检索结果缓存（query 归一化 + 结果持久化）。同一 query 在不同子代理间重复发出是最贵的浪费；**这比任何 prompt 优化都值钱** [E: ext-cost-economics.md#设计含义3]。

**缓存语义直接决定「可重跑」能不能成立**，而四家的语义完全不同 [E: ext-web-providers.md#D4]：

| 检索供应商 | 缓存默认 | 可控参数 | 对可重跑的含义 |
|---|---|---|---|
| Exa | **默认吃缓存** | `maxAgeHours`（0=总是实时，-1=永不实时） | **危险默认**：不设参数就可能拿到旧内容却当成「今天取的」。凡「截至今日」类断言必须 `maxAgeHours: 0` 并记录该参数 |
| Jina Reader | 缓存一段时间（**TTL 未公布**） | `X-No-Cache`、`X-Cache-Tolerance`、`DNT` | 复现时必须固定同一 `X-Cache-Tolerance`，否则两次运行不可比 |
| SerpApi | 1 小时 | `no_cache` | 正面：1 小时内重跑同查询免费且结果一致，天然适合验证者复算 |
| Firecrawl / Tavily / Brave / serper | 未公布缓存控制参数 | — | 视为「每次都是新抓」，但**不能假设**；必须记录取回时间戳 |

→ 证据记录必填 `fetched_at`、`provider`（= 检索供应商 id）、`endpoint`、`cache_policy_used`（把参数原样存下来）。**没有 `cache_policy_used`，「可重跑」就是空话** [E: ext-web-providers.md#D4]。

### §6.5 「绕过网关」的诚实执行论证

> 这一节必须写得比舒服的版本更难看，否则它就是假的。

**我们不声称网络被拦住。** 一手事实（规范表述见 01-CONTRACTS §4.4）：内核沙箱只管文件效应、`SandboxMode` 类型注释逐字写「Network and process visibility are outside this vocabulary.」；`run_code` **同时绕过**内核沙箱（只管 bash）**和** `ctx.fs` 策略围栏（只管 ctx.fs 工具）；`toolFilter` 不是权限天花板且不向下传递；子代理不继承父沙箱作为下限 [E: GROUND-TRUTH-CORRECTIONS.md#A7, #A8, gt-exec-security.md#D, #B]。

**我们声称的是：绕过网关取得的字节无法变成任何 claim 的承重证据。** 机制是产物级兜底——每条证据必须能绑到一条真实发生过的 `tool/call` / `tool/code-dispatch` 事件（这是 `source_integrity` 的子测试②，见 01-CONTRACTS §1.2.1 与 §4.4 末条）；绑不上 → `source_integrity = not_covered` → `S` 的 0c → ST-N（01-CONTRACTS §1.5）。**因此绕过网关对攻击者的收益是零：它不能让任何 claim 升格，只能制造一条 ST-N。**

**这条论证的四条边界，必须一并写出，否则它是谎话**：

- **(b1) 正确的表述是「绕过没有收益」，不是「绕过不可能」。** 一个被攻陷的 worker 完全可以先绕过网关取内容、再通过网关重放同一个 URL 以取得合法事件。此时它拿到的是同一份内容——绕过的唯一收益是省掉限速。
- **(b2) `run_code` 的**子工具调用**是被覆盖的**：每个 binding 都走完整的 pre-execute → guards → execute → post-execute → result 管线，并逐条落 `tool/code-dispatch-start` / `tool/code-dispatch` 日志 [E: gt-orchestration.md#J4]〔依据 00-PREMISE B1 配套的三条硬约束〕。真正无痕的是程序体里**不经工具 binding** 直接发起的网络 IO——那类字节没有事件，落到 (b1)。
- **(b3) 网关与产物门保护的是不同的东西。** 网关保护**配额、合规与可重跑**（`cache_policy_used`、robots、`retention_tier` 都在 fetch 时刻决定，见 01-CONTRACTS §8.6）；产物门保护**可信度**。绕过网关会真实地打爆 429、越过 robots、丢失留存决策——**这些损害产物门一条也发现不了**。所以网关不是优化项，产物门也替代不了它。
- **(b4) 因此网关的强制手段只能落在工具边界**（01-CONTRACTS §4.4 的三层）+ 子代理不持裸 API key + 网关是独立进程。这些都不在网络边界上，而且它们**不构成隔离**（01-CONTRACTS §5.4）。

### §6.6 中文通道的两条编排后果

1. **扩召回靠多角度并行查询，不靠翻页**（bocha 单次上限 50 条且完全忽略分页）→ 一个中文检索子任务一次派发 3–6 个不同措辞的查询 [E: ext-chinese-ecosystem.md#设计含义1]。这是 F-A 类扇出在中文通道上的具体形状。
2. **按断言的语言/属地路由，而非按用户界面语言**：bocha 与 serper 索引重叠极小（本轮同一主题在两边得到几乎不相交的结果集）；中文政策、统计、国内机构走 bocha，国际论文与英文一手文档走 serper [E: ext-chinese-ecosystem.md#设计含义1]。
3. **中文任务关闭 citation-snowball**——规范表述与依据见 01-CONTRACTS §3.6 与 V3.6。这是一条编排层必须执行的能力关闭，不是一条建议。

### §6.7 可检验断言

- **V-4.23** 全量扫描：不存在任何 worker 会话持有裸 API key（环境变量与工具参数双向扫描）。
- **V-4.24** 网关红样本：向 arXiv 桶并发提交 2 个请求，断言第二个被串行化（不是被令牌桶放行）。
- **V-4.25** 429 集体退避红样本：注入一个 429 响应，断言同一供应商的其余在途请求全部退避，而不是只有触发者退避。
- **V-4.26** 每条证据记录含非空 `cache_policy_used`；缺失即门红。
- **V-4.27** 负向测试（(b1) 的机器化）：构造一条 `evidence` 记录，其 `object_sha256` 存在于 CAS 但其 `tool/call` callId 在 session 日志中查无此事，断言该 claim 判 ST-N（这是 01-CONTRACTS V4.6 在编排层的实例）。
- **V-4.28** Brave 结果不落盘：断言序列化器对 `ephemeral: true` 的对象抛错；红样本为一次尝试写盘。

---

## §7 人在环检查点

### §7.1 行业收敛点与空白

**行业收敛到的唯一一个检查点是：开跑前的计划审批。** OpenAI 产品端做（澄清提问 + 可编辑计划），Gemini 两端都做（App 可改计划，API 把它做成 `collaborative_planning` 布尔量的三阶段协议）；Claude、Perplexity、Grok 一个都没有。**没有任何一家有跑完之后的裁决检查点** [E: ext-incidents-products.md#设计含义2]。

**口径提醒**：OpenAI 侧的证据本轮只到摘要级（openai.com 全站被 Cloudflare 拦截，WebFetch 与 curl 均 403），写进对照表前建议实机确认 [E: ext-incidents-products.md#一手源未能直取]。

### §7.2 检查点清单：2 个强制 + 4 个条件触发

| id | 类型 | 位置 | 触发条件 | 人做什么 | 依据 |
|---|---|---|---|---|---|
| **CP-0** | 条件 | 外环之前 | 问题欠定义 | 回答澄清问题 | API 侧模型明确「不会主动要上下文」，澄清层是产品侧另建的——**这一层必须由我们实现为独立前置步骤，不能指望模型自觉** [E: ext-incidents-products.md#设计含义2] |
| **CP-1** | **强制** | 外环之前 | 总是 | 审批研究计划：子问题分解、每个子问题的证据类型（K-D / K-L / K-I，见 01-CONTRACTS §2）、**预期的不可验证区**、以及**冻结的 checklist**（§4.2 SAT-1 的输入） | 完全对齐行业收敛点，用户预期已被教育好，零学习成本 [E: ext-incidents-products.md#设计含义2] |
| **CP-2** | **强制** | L4 之后 | 总是（但入口极窄，见 §7.3） | 只裁决「机器判不了」的那一桶 | 行业空白 = 我们的产品面 [E: ext-incidents-products.md#设计含义2] |
| **CP-3** | 条件 | R4 之后 / 任意时刻 | `sandbox/mode == danger-full-access` | 复核该 run 的全部产物 | 01-CONTRACTS V4.5 |
| **CP-4** | 条件 | fetch 之后 | F-08（`predatory-suspect`，Cabells 订阅制无 API，本项目不可编程访问）；`legal hold` 置位；F-26 的签名核验 | 人工判定 / 置 hold | 01-CONTRACTS §7.2 F-08、§9.29c |
| **CP-5** | 条件（**harness 强制**） | 跨进程重启后 | 总是；以及 `idle_rounds` 超限使外环 blocked（§4.4） | 授权续跑 / 裁定阻塞 | `goal` 的 activation 永不持久化，resume 后必须人类重新 arm [E: gt-orchestration.md#A1, #A2] |

**CP-5 值得单独说一句**：它不是我们加的检查点，是 harness 强制的。任何宣称「无人值守跑一夜」的表述都与这条事实冲突 [E: gt-orchestration.md#设计含义5]。

### §7.3 CP-2 必须窄，且按精确率设阈

**这是被数据强制的，不是保守的美德。** 现成引注核查器 RefChecker 在 **71 条合法引注上误报 36 条**（我方算术：对合法引注的误报率约 50.7%）[E: ext-incidents-products.md#D-5, #设计含义2]。**如果把检查器报警的东西全推给人，人会被淹死，然后开始无脑点通过——检查点就退化成橡皮图章。**

**三分流（规则 O-13）**：

```
机器判定成立                                  → 自动过
机器判定确凿不成立（DOI 不可解析 / 页面 404 /
  引文原文不存在 / quote_faithful == fail）   → 自动打回并重跑
只有真正歧义的                                 → 进 CP-2
```

**自动打回的阈值按精确率调，不按召回率调** [E: ext-incidents-products.md#设计含义2]。理由与 01-CONTRACTS §6.4 的 κ 分级同源：κ ∈ [0.4, 0.6) 的 judge 只能做**分流器**（把条目路由给人），不能做终判——**分流器正是 CP-2 的入口机制**。

### §7.4 CP-2 的硬容量闸

**〔裁定〕`|CP-2 队列| ≤ min(20, 0.10 × 载荷 claim 总数)`。超出即触发「收缩发现宽度 / 提高自动打回阈值」，而不是把队列加长。**

理由：CP-2 队列长度若不设硬容量，会随发现宽度线性增长——而发现宽度正是超并行最容易放大的那一维。橡皮图章不是人的问题，是队列长度的问题。
**什么会推翻**：若实测 CP-2 的人工推翻率（人判「机器判错」的比例）长期极低，说明分流器过严（该自动过的进了队列），应放宽入口而不是缩容量；若长期极高，说明自动打回阈值过松。两个方向都要求重设，而不是维持 20。

### §7.5 人的裁决写在哪里

- **人不改 status。** F-26（`human-verified`）**不改 status**，仅在交付层并排显示——规范表述见 01-CONTRACTS §7.2 与 §1.4.3。「谁需要看」是工作流属性，「我们知道什么」是认知属性。
- **算法给 proposed judgement，人可推翻，但推翻必须写理由。** 这是 Cochrane RoB 2 的成熟工业形态：信号问题（近乎事实性，答案只能是 Y/PY/PN/N/NI）→ 写死的算法 → proposed judgement → 人可推翻 + 必须写理由 [E: ext-human-methodology.md#结论摘要1, #C]。
- **这个形状有实测支撑**：同一篇 2025 JMIR 研究里，LLM 在**信号问题层面**平均准确率 83.2%（95% CI 77.5–88.9），聚合到**域层面**降到 65.2%，整体 RoB 判定只有 57.5%–70%；另一项 2024 Research Synthesis Methods 研究显示直接让 LLM 输出 RoB2 判定，**F1 只有 0.1–0.2，与平凡基线无异** [E: ext-human-methodology.md#结论摘要2]。→ **让模型答事实问题，让代码做聚合判定。**
- **边界同样被测出来了**（BMJ EBM 2026 半自动 GRADE 工具，115 篇 Cochrane 综述）：**能算的几乎全自动**（imprecision 按参与者数 0.97/F1 0.94、I² 0.90/0.90、AMSTAR 0.98/0.99），**要判断的不行**（risk of bias 仅 0.73/0.70；整体 GRADE 等级一致率 63.2%、Cohen's κ = 0.44）[E: ext-human-methodology.md#结论摘要5]。

### §7.6 一条不能省的产品行为

**中文交付物默认附带证据附录**：每条载荷断言 → status → 来源 → 原文定位 → 若为数据结论则附可复跑脚本与哈希。它证明的不是「我没用 AI」，而是「我说的每句话都能当场被查证」——这恰好是 AIGC 检测覆盖不到、而学位委员会真正在意的那一面 [E: ext-incidents-products.md#设计含义7]。

### §7.7 可检验断言

- **V-4.29** CP-1 通过时 checklist 被冻结并写入 `runs/<run_id>/checklist.json`，其 hash 入 manifest；后续任何对 checklist 的修改使该 run 的停机报告标为无效。红样本：跑到一半改 checklist，断言门红。
- **V-4.30** CP-2 队列容量闸：注入 100 条歧义项，断言队列被截到上限且触发「收缩发现宽度」的记录，而不是排出 100 条。
- **V-4.31** 断言不存在任何由人工输入直接写入 `claims/*.status.json` 的路径（F-26 只写 flags）。
- **V-4.32** 负向测试：不经 CP-5 授权重启进程，断言外环不自动开始（与 V-4.5 同一断言的人在环视角）。

---

## §8 与既有 house 先例的张力

### §8.1 先例的准确形状

本仓库两条已完成流水线（`plugin-creator`、`serper-harvester`）的**构建阶段是刻意串行的**：`D0::loop`、`D1::staged (6 seams)`、`D2::plan_execute_verify for build stages, retry for live smoke, review for acceptance`、`D3::on_the_loop` [E: gt-house-method.md#A3]。构建 seam 之间没有扇出。

**扇出只出现在一个地方：attacker battery。** `plugin-creator` 的 battery 阶段一次扇出 8 个 agent [E: gt-house-method.md#M12]；而扇出之后**必须有一次 synthesis pass (R+1)**——一个新鲜上下文读所有 findings + flags 的并集，猎交互缺陷 [E: gt-house-method.md#结论摘要1 L3 段, gt-house-method.md#86]。

**因此先例的形状恰恰是 00-PREMISE B1 押的那个形状**：覆盖率维度扇出（五透镜并行覆盖）+ 单一上下文综合（synthesis pass 做跨发现的一致性推理）。**本项目的 L1/L2/L3 扇出 + L4 零扇出是同一形状的放大版，不是对先例的背离。**

### §8.2 房内自己量到的、对扇出不利的数据（不得洗白）

| 装置 | 时长 | subagents | 花费 |
|---|---|---|---|
| plugin-creator 真实 e2e run-2（新设计） | 93.35 分钟 | 16 | CNY 5.58 |
| plugin 目标 run（新设计） | 95.6 分钟 | 16 | CNY 6.48 |
| 对照基线 | 58.6 分钟 | 7 | ~CNY 12 |

[E: gt-house-method.md#结论摘要4]

**房内自己的结论措辞是「新设计更贵」，而 CNY 一栏方向相反（5.58 < 12）。** 引用这组数字时必须三个数一起给：新设计在**墙钟时长与 subagent 数**上更贵，在 **CNY** 上更便宜；「更贵」这个判词覆盖的是前两项。**只取有利的一项是口径失真**，正是本项目要消灭的行为。

真正致命的一条是质量：**B15 头对头，基线赢**；房内把这条写成 **"better-governed, not better-output"**——**治理不等于质量，这句话应当贴在本项目的墙上** [E: gt-house-method.md#结论摘要4]〔依据 00-PREMISE B8〕。

### §8.3 那么本设计的扇出凭什么成立

三条，全部是**结构差异**，不是「我们更聪明」：

1. **扇出对象不同。** 先例扇出的是**构建**（写代码、改配置），那是强依赖的顺序任务，落在 −70% 那一侧。本设计扇出的是**覆盖与多验**——候选检索、多来源交叉抓取、同一条载荷断言的 N 路独立核验——单 agent 基线低、天然可并行 〔依据 00-PREMISE B1 裁决〕。
2. **下游有客观裁决器。** 探索路径多样性**只有在下游存在一个比 worker 更强的客观裁决步骤时**才兑换成质量；没有客观裁决器的扇出 = 吞吐量，不是质量 〔依据 00-PREMISE B1 并行可靠买到的三样〕。本设计的每条并行边都被 A1/A3/A5 强制配一个 GC-0/GC-1 门（§3.2）。先例的 attacker battery 也满足这条（adjudicate 是脚本强制的）。
3. **先例本身就是同形的。** 见 §8.1。真正的差异只在规模。

**但第 3 条也带来一条警告**：house 自己量到的是「新设计更贵且产物质量并没有更好」。本项目把规模再放大一个量级，**默认预期应当是「更贵」，并提前接受它**；正当性只能来自 `每个 verified claim 的边际成本`（§5.5）与 M2 的等预算 A/B（§9.3），不能来自「我们并行了所以更好」。

### §8.4 降级路径（三档，带机器可判的触发条件）

| 档 | 形状 | 触发条件（任一） | 附带动作 |
|---|---|---|---|
| **D0 全扇出**（默认） | L1 / L2 / L3 均扇出 | — | — |
| **D1 只保留取证扇出** | L1 收为串行多角度查询（仍多 query，但单 worker）；L2 保留扇出；L3 收为串行四路 | ① 我们自己的深度 × Fact-Check 七档曲线显示**核验路径**的准确率也随并行度下降 ② `futile_ratio` 在连续 3 个 run 中 ≥ θ_futile ③ 中央网关下的实际有效并行度长期 < 4 | 在 run 报告中记录降级原因与触发数据 |
| **D2 单线程深挖 + 强核验** | 全部串行；只保留 L3 的四路作为串行 checklist | ① D1 触发条件仍成立 ② 等预算 A/B 显示扇出臂的 `verified 载荷断言数 / 预算` 不高于单线程臂，或其 false-claim rate 更高 | **`hyper-parallel` 这个名字必须改** 〔依据 00-PREMISE B1 会推翻它的观测〕 |

**「有效并行度长期 < 4 则退回少而深、名字必须改」是 00-PREMISE 预注册的推翻条件，不是本文件新增的**——本文件只把它变成一条带机器判据的降级路径 〔依据 00-PREMISE B1 会推翻它的观测〕。

### §8.5 从 house 继承的编排纪律（引用，不复述）

| 编号 | 纪律 | 对本文件哪一节生效 |
|---|---|---|
| M5 | red-first，红样本由 conductor 写、事件形状取自真实捕获 [E: gt-house-method.md#M5] | §4.8 的 RS-1/2/3、§3.7 V-4.11、§5.8 V-4.19 |
| M6 | 跨执行边界就要跨过去断言 [E: gt-house-method.md#M6] | §6.5 的全部论证、§4.4 的事件侧检查 |
| M7 | 双层记账：成功数必须配 integrity 对子，由 grep 门强制 [E: gt-house-method.md#M7] | §4.6 停机报告的五项必填 |
| M11 | 把「太严的门」也当缺陷记——逼着记录说假话的门和放行假话的门一样坏 [E: gt-house-method.md#M11] | §7.4 的 CP-2 容量闸双向推翻条件 |
| M12 | 成本按 subagent 数 × 真实时长记，并提前接受「更贵」 [E: gt-house-method.md#M12] | §5.5、§8.3 末段 |
| M13 | 立刻补 `checks/gate_integrity.sh`（规范表述见 01-CONTRACTS §6.5.2 与 §9.22）[E: gt-house-method.md#M13] | 全部门的第一行 |
| M14 | 台账本身要有格式门（规范表述见 01-CONTRACTS D-8.13）[E: gt-house-method.md#M14] | §4.4 的 `no-result` schema、V-4.15 |

**一条 house 的未决问题在本文件里仍然未决**：`gate_integrity.sh` 自己也在 `checks/` 里，谁来证明它没被改？本仓库无答案 [E: gt-house-method.md#未决1]。已列入 §10。

---

## §9 参数汇总与标定计划

### §9.1 全部可调参数（含来源与状态）

| 参数 | 值 | 来源 | 状态 |
|---|---|---|---|
| `θ_sat`（能力饱和阈值） | 45% | arXiv:2512.08296 v3 | **待标定**（单一来源，R²=0.373，六基准无一是文献研究）|
| `maxConcurrentAgents` | **显式配置**（本机推导值 12，硬顶 16） | gt-orchestration.md#E4 | 必须显式配，不依赖推导 |
| `maxTotalAgents` | 显式配置（引擎默认 1000，只能降） | gt-orchestration.md#E4 | — |
| `maxDepth` | 3（出厂） | gt-orchestration.md#C1 | 若需第 4 层必须显式提高并记录 |
| `maxParallelToolCalls` | 10（出厂，**可热改的用户设置**） | gt-orchestration.md#G1 | **不是安全边界** |
| `maxParallelSubCalls` | 10 | gt-orchestration.md#J1 | **仅 code/both 呈现模式；出厂是 native** |
| `maxConcurrentJobsPerOwner` | 10（超限抛错不排队） | gt-orchestration.md#H1 | 与 `bash(run_in_background)` 共用 |
| `k`（SAT-2 窗口） | 3 | 本文件 | **〔裁定〕无外部依据，M1 标定** |
| `D_min`（有效派发下限） | 3 | 本文件 | **〔裁定〕无外部依据，M1 标定** |
| `θ_futile` | 0.5 | 本文件 | **〔裁定〕无外部依据，M1 标定** |
| `idle_rounds` 上限 | 2 | 本文件 | **〔裁定〕无外部依据，M1 标定** |
| `α`（degraded 触发比） | 0.8 | 本文件 | **〔裁定〕M1 标定** |
| CP-2 队列容量 | `min(20, 0.10 × 载荷 claim 数)` | 本文件 | **〔裁定〕双向推翻条件见 §7.4** |
| `E` 公式中的 `30` / `3` / `$0.22` | as-of 2026-08-17 | ext-cost-economics.md#A1 | **配置项，30 天内视为会变** |
| 峰时窗口 | 01:00–04:00 + 06:00–10:00 UTC | ext-cost-economics.md#A1 | **配置项** |
| 各检索供应商桶 | 见 §6.2 | 各供应商官方页 | bocha 标 `assumed`，持续告警 |

### §9.2 标定的顺序

M0（架构定稿前，阻塞）→ 确认 Code Mode 前提（§3.5 P0）与 RT-5（01-CONTRACTS V7.8）。
M1（第一个端到端 run）→ 深度 × Fact-Check 七档曲线（2/10/30/50/70/100/150，在我们自己的语料上，判定器交叉厂商）；`k` / `D_min` / `θ_futile` / `idle_rounds` / `α` 的首次标定；每次 run 记账。
M2（首批 checkable-answer eval）→ 等预算 A/B（A = 单线程深挖 vs B = N 路扇出 + 客观裁决），任务集 ≥12 个 checkable-answer 问题，两臂**同一渲染器**产出；`θ_sat` 在我们任务族上重测并报 R²。
〔依据 00-PREMISE B1 何时检验, #B2 两条配套纪律〕

### §9.3 M1 的深度曲线为什么是产品证据而不是内部调优

本轮最强的一条证据（−42.0pp）恰恰来自一个只测了两个模型、没报统计检验、用 LLM-as-judge 的单篇预印本。**一个以「不洗数字」为卖点的系统，不能把它当定论引用** [E: ext-orchestration.md#D8]。跑出我们自己的曲线，既是 per-loop 门触发深度的参数来源，也是这个系统「产品即可信度」的第一个自证——公开文献里不存在等算力并行 vs 串行的对照实验，我们做出来就是贡献 [E: ext-dr-architectures.md#未决1]〔依据 00-PREMISE B1 何时检验〕。

---

## §10 本文件自身的已知薄弱处（供攻击者优先瞄准）

1. **§4 的 `STOP` 从未运行过。** 它与 01-CONTRACTS §1.5 的 `S` 一样，是从证据推导出来的设计，不是被测量出来的行为。RS-1/RS-2/RS-3 跑通之前，「同时内容感知且可复现的停机判据」应按未验证设计假设对待。
2. **`k` / `D_min` / `θ_futile` / `idle_rounds` / `α` / CP-2 容量六个数全是裸裁定**，没有一个来自外部测量。它们中任何一个取值不当，SAT-2 都会退化：`k` 太小 → 提前收敛；`D_min` 太小 → §4.4 的防线形同虚设。
3. **§4.2 的 `Δstatus_up` 经过 GC-2，因此 `STOP` 不是 model-free。** 本文件已在正文写明并把主信号放在 `Δcluster` 上，但如果 `Δcluster` 在实测中噪声主导（01-CONTRACTS §9.14 已预注册这个风险），SAT-2 会被迫更依赖那条 model-influenced 的信号。
4. **§3.5 的 P0 层可能根本不存在。** 出厂呈现模式是 `native`，`code-runtime` 只由 web-app / headless 挂载。若不选 Code Mode，00-PREMISE B1 的「先吃满工具调用级并行」这条配套约束在本运行时无处落地。**这是 M0 阻塞项。**
5. **§3.4 的角色—工具映射有一处自认的例外**（反证 worker 与发现/取证 worker 工具集重叠），而 OpenAI 的判据恰恰是重叠度而非数量。这条例外是已知的协调开销来源。
6. **§6.5 的执行论证保护的是「升格」，不保护「资源」。** 一个被攻陷或只是写得差的 worker 绕过网关，会真实地打爆配额、越过 robots、丢失留存决策，而产物门一条也发现不了。§6.5 (b3) 已写明，但这意味着网关本身是一个**没有强隔离兜底的软约束**。
7. **§8.2 的 house 数据对本设计不利，且我们没有反驳它，只有结构性解释。** 「治理不等于质量」在本项目上是否成立，M2 之前无答案。
8. **`gate_integrity.sh` 的自指问题无解**（谁证明它没被改）。house 无答案，本文件也没有。
9. **本文件引用的全部检索供应商限速与价格在 30–90 天内会变。** 峰谷窗口有被取消的先例（2025-09-04）；Crossref polite pool 已经失效过 16 倍。凡引用本文件的数字必须连 as-of 日期一起引用。

### §10.A 待回填 01-CONTRACTS 的条目（本文件不自行铸词）

| # | 需要动的地方 | 内容 | 为什么不能留在本文件里 |
|---|---|---|---|
| T-1 | §9.25（provider 的义项） | 增加**第三义项**：外部检索/抓取服务商。见 §6.0 | 本文件与 04 之外的文档都会用到这个词；不消歧就是下一轮漂移的震中 |
| T-2 | §9 新增 | `E`（token 当量）、`N_search`——两个预算计数器的名字。定义式见 §5.2 | 预算是跨文档共享概念（01-CONTRACTS §1.3 的 `budget_state` 已依赖它们，但没有名字） |
| T-3 | §9 新增 | `有效派发轮` / `futile 派发` / `no-result 记录`——停机判据的三个零件。定义见 §4.4、§4.5 | 台账 schema 要落 `no-result` 记录，schema 归 01-CONTRACTS 管 |
| T-4 | §9 新增 | `Δcluster` / `Δstatus_up` 两条曲线的名字。见 §4.3 | 交付物要展示它们 |
| T-5 | §9 新增或本文件保留 | 编排标识：外环 `O`、内环 `L1..L4`、检查点 `CP-0..CP-5`、扇出位 `F-A/F-B/F-C`、准入判据 `A1..A5`、规则 `O-1..O-13`、停机项 `SAT-1..SAT-4` | **这些是本文件的局部编号，不是共享术语**；除非其他文档要引用，否则不必进 §9。列在这里是为了让 lint（01-CONTRACTS V9.2）不误报 |
| T-6 | 00-PREMISE §B9 裁决 | 更正 `maxBudgetUsd` 的归属：它属 Claude Agent SDK，不属 DSH。见 §5.6 | 这是一条会让下游写出不存在的 DSH 能力的错误 |
| T-7 | 01-CONTRACTS 文件尾 + 00-PREMISE 文件尾 | 语料文件数：实测 **26** 个（`ls -1 research/v2 \| wc -l`，2026-08-17），01-CONTRACTS 写 22、本轮任务书写 23 | 一个以「不洗数字」为产品的文档集，自己的基线计数不能有三个版本 |

---

**文件版本**：v2-draft-1｜**撰写日期**：2026-08-17｜**证据基线**：`research/v2/`（**实测 26 文件**，2026-08-17；注意 01-CONTRACTS 文件尾写 22、本轮任务书写 23，三者不一致，见 §10.A T-7）｜**规范源**：`01-CONTRACTS.md`
