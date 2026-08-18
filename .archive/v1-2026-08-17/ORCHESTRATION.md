# ORCHESTRATION — 超并行多 loop 编排设计

> 上位约束：[PRINCIPLES.md](PRINCIPLES.md)（尤其 P-11 写面不相交、P-12 证据即时物化、
> P-13 harness 原语、P-14 预算前置）。模块归属见 [ARCHITECTURE.md](ARCHITECTURE.md) M4。
> 外部编排证据（orchestrator-worker 经济学等）由 SURVEY.md §编排维度补充。

## 1. 为什么 DSH 原生并行能替代 LangGraph

Paper Graph 的思路在 LangGraph 上被证明低效（用户判断）；DSH 侧的机制事实：

- 三级现成并发原语：同 turn 兄弟工具调用滚动池（maxParallelToolCalls=10，含并发子代理
  委托）；run_code 子调度池（10）；workflow-worker-thread 的 parallel/pipeline + agent()
  钩子 [E: DSH-架构分析.md §6]。
- plugin-creator battery 阶段已实证 workflow 内 8-agent 受控扇出可行
  [E: plugin-creator e2e 实测]。
- 状态活在文件 + append-only 事件日志（fold 投影冷恢复），没有图框架的序列化/
  checkpoint 开销，也没有"结构=质量"的幻觉（P-1）。
- ralph 模式（每 round 一个 fresh child、inheritsParentContext:false、结构化 handoff）
  是现成的"每轮新子代理"长循环模板 [E: dsh-harness-code-archaeology.md workflow 章]。

## 2. Loop 分层：一个外环 + 五类内环

```
外环 RESEARCH-ROUND（goal + goal-round-driver 驱动，逐轮推进）
  每轮由 conductor 依据 frontier 状态选择派发下列内环的任意组合（可并行）：

  L1 发散环   cartographer 重扫立场空间 → 并行 advocate×P + adversary
              → 立场/证据线覆盖缺口清单
  L2 取证环   对缺证据的 claim 并行派 grounder（每 claim 一个，检索即取证）
              → incoming/ → admission 脚本入库
  L3 验证环   对 pending 状态的 claim 并行派 verifier（data 重跑 / source 校验 /
              inference 检查）→ 门脚本裁决 → 台账状态更新
  L4 反证环   对 verified 的承重 claim 主动搜反证与更强反驳（contradiction hunt）
              → contested 状态或反驳条目
  L5 综合环   蒸馏本轮所得 → 更新 frontier brief（有界 resume 状态，P-2）
              → 计算饱和度指标 → 决定下一轮派发
```

- L1–L4 都是 **workflow 脚本内的 fan-out**（agent()/parallel()/pipeline()），
  同轮可并行多个内环——它们的写面天然不相交（见 §3）。
- L5 是唯一的合并点，单写者 = conductor。
- 层级深度预算：conductor(1) → workflow agent(2) → 其派生的检索子调用(3)，
  恰好贴 maxDepth 默认 3；若需更深显式调 config（认账进设计，P-13/约束表）。

## 3. 写面所有权矩阵（并行不炸的前提，P-11）

| 工件 | 唯一写者 | 并行 worker 的写法 |
|---|---|---|
| `claims.tsv` 行 | admission 脚本（新行 status 恒 pending） | 结构化返回拟议行，不碰文件 |
| `claims.tsv` status 列 | **门脚本（唯一）** | 不可写；复核裁决经 verdicts/ 工件输入门 |
| `evidence/<sha256>` 快照 | **检索/抓取工具执行器**（抓取执行内落盘+事件记 hash）；用户上传物经 admission | 不可写；不经 incoming/ |
| `incoming/` | 各 worker | 每 worker 预分配不相交子路径 |
| `metrics/<cid>.json` | 门脚本（重执行产物） | 不可写 |
| `frontier.md`（L5 brief） | conductor | 只读 |
| `gate_report.md` | 门脚本 | 不可写 |
| session JSONL 审计轨 | harness 自动 | 不可伪造（反伪造门断言层） |

## 4. 外环机制细节（goal 驱动）

- goal 建立时写清 stop 条件与轮预算；goal-round-driver 在 idle 时自动排队
  `<goal_round>` prompt，默认 256 轮上限、连续 3 轮同因自动 blocked——饱和检测
  可直接挂在"连续 N 轮零新增 verified claim"上（blocked code 语义）。
- **重启续跑是显式步骤**：armed 不持久化，恢复流程 = `dsh --profile academic-research`
  → goals.resume（写进 runbook 的操作步骤，不假设自动发生）[E: P-13]。
- checkpoint：round driver 每轮先 sessions.flush 再预留轮次——崩溃安全由 harness 保证。
- 人类消息不消耗轮配额且自动让路——用户可随时介入不打断预算核算。

## 5. 饱和与停机规则（每条都机器可判）

1. **证据饱和**（防"不派发/空壳派发洗收敛"，RT-9 + A7 fix-audit）：仅当一轮
   **实际派发了 L2 与 L4**（agent-start 事件为准）、**且派发产出非退化**
   （每个 grounder 返回 ≥1 候选或显式"用查询 Q 检索 N 源、命中 0"的结构化空报告；
   adversary 返回实际检索面与最强反驳尝试；cartographer 的"无缺口"结论是**可审计
   工件**，由独立审计随机抽查其检索面是否覆盖 answer-key 立场）、且 admission 无新增
   accepted、且 L1 覆盖清单无未探索缺口时，该轮才计入饱和计数；连续 K 轮（默认 2）
   满足 → 收敛。诚实残余：派发工作的"实质充分性"不能完全机器判定（语义），
   空壳派发的精修形态靠 cartographer 检索面抽查兜底，非零漏报——记入 coverage_gaps；
2. **状态收敛**：pending/unverified 承重 claim 数为 0 且 L4 反证环连续一轮空手 → 候选；
3. **预算停机**：全局 token/¥ 预算触顶 → blocked（不静默降质量）；
4. **轮预算**：goal round 上限触发 → blocked({code:'round-limit'})；
5. **零变更护栏**：连续 2 轮文件树零变更 → stop-failure（反空转，house 先例）。

候选 ≠ 完成：候选进入 held-out eval 轨，SHIP/REVISE 由 eval 裁决（P-7）。

**生产 run 的收口（区分两种模式，堵"任意课题无 answer key"缺口）**：held-out
answer-key 式 eval 是**开发/回归**模式（固定任务集）。用户任意课题的**生产** run
不预置 answer key，其收口是**自证型质量报告**而非 SHIP/REVISE 判决：交付
(1) 台账状态分布（verified-* / contested / unverified 占比）、(2) 承重 claim 的
证据链、(3) 独立审计 agent（盲于台账，D4 风格）对最终报告的反向抽取覆盖率 +
honesty flags、(4) 对抗环（D3 风格）对头部结论的最强反驳。"质量"以可信度指标
如实呈现，系统不自评总分（P-2/P-5）。开发轨的 A/B 与 held-out 证明的是"这套
生产流程平均产出更可信"，生产轨据此获得可信度而非逐 run 判决。

**验证门挂在每个内环出口，不在终稿一次性做**：外部实证显示工具调用从 2→150 时
事实核查准确率平均掉 ~42%（两前沿模型消融均值）——研究越深引用越漂移。
每个内环收口时对本环新增/修改的 claim 跑 L1 确定性门，keep-if-better 的 better
定义里含"引用支持率不回退"；并行深度本身不得放大溯源错误（回归指标见 TESTING §3）。

## 6. 成本模型与预算（预先量化，P-14；数据出处见 SURVEY §12 cost-economics）

**成本模型骨架**：`C_run ≈ C_lead + N×C_worker + V×C_judge + S×c_search`。
校准锚点：多 agent ≈15x chat token（Anthropic 官方口径，且 token 用量单独解释
80% 性能方差——**预算即质量旋钮**）；商业 run 价带 $0.9-$30（OpenAI DR 实测）到
$200（Kosmos 200-rollout 级）；开源全包 $0.2-$2。

- **预算分档暴露为一级参数**（像 Kosmos credits）：quick / standard / exhaustive
  三档，每档写死 fan-out 规模 N、per-agent token 上限、检索/抓取配额；
  15x 是均值，递归 spawn 或超大 tool result 可再 ×10——per-run 与 per-agent
  硬熔断写进代码（budgets-in-code，house R-F 教训）。
- **effort-scaling 规则进代码不进 prompt**：简单题 1 agent/3-10 次调用、
  对比题 2-4 subagents、复杂题 >10（Anthropic 实测规则）。
- **三大成本杠杆**：① 缓存友好架构——system prompt/工具 schema/共享文献上下文
  全放稳定前缀（前缀禁时间戳/随机 id），N=10 共享前缀成本降 ~87%（读 0.1x）；
  ② 裁判分层——可验证二元判定用小模型短裁决（精度损失 <2pp、输出成本降 ~800x），
  开放式评审用强模型或异构小模型陪审团；③ 离线批处理——**同步探索 + 异步验证
  双轨**：引用核验/批量抽取/离线评审攒批到验证队列，不阻塞主 loop。
  **成本杠杆的 provider 依赖注意**（R1 攻击 MC）：Batch API flat 50% off 与
  1.25x/0.1x 缓存乘数是 Anthropic/OpenAI/Gemini 口径；本机主 provider 是
  DeepSeek（deepseek-official），其缓存/批处理定价不同、Batch 支持需实测确认。
  杠杆③的"双轨"结构（异步不阻塞）与模型无关、始终成立；其 50% 折扣数字仅在
  对应 provider 上兑现——预算模型按实际路由的 provider 定价表计算，不套用
  Anthropic 数字（cost-economics 数字全部标注为 provider-specific）。
- **学术场景最大单项成本是 PDF 全文**（≈125k token/篇）：共享文献库走缓存前缀
  或摘要分层（先 abstract/结构化摘要，进入 verify 队列才升级全文）；学术 API
  多免费是相对通用 DR 的结构性成本优势，API 支出（OpenAlex credits、serper 等）
  做成与 token 支出并列的显式预算项。
- **预算记账口径（防 125k/篇 vs 200k/轮 的表面冲突）**：DSH tokenMeter 只暴露
  **总量投影**（tokenUsage/contextPressure/contextBreakdown，4 字符/token 启发式 +
  provider usage 锚），**不暴露 per-step 缓存读/未缓存输入分解**
  [E: dsh-agent-core-architecture.md tokenMeter]——因此预算记账用**总量 token**，
  不套用 effective-tokens 的"缓存读×0.1"公式（那是成本估算的一个模型，不是运行时
  可读的记账量，A7 fix-audit）。冲突的真正消解靠**分账户**：全文深读走 verify 队列
  的独立 token 预算（异步轨），轮预算（探索/编排面）与之分离核算——两个预算池各自
  按总量 token 计，互不挤占。缓存友好架构（前缀稳定）作为**降成本设计偏置**而非
  记账项：省下的钱在 provider 账单上体现，不进 DSH 的轮预算算术。各档位数值由
  bench 实测校准（P-14）。

| 参数 | 初始值 | 依据 |
|---|---|---|
| 同轮内环并行度 | ≤3 个内环 | 滚动池 10 的余量 + 单写者合并带宽 |
| 单内环 fan-out | ≤8 agent | plugin-creator battery 实证规模 |
| 检索 worker 模型 | 便宜档 | agentOptions 多模型分工 |
| 机械验证裁决 | 小模型 + 10-token 短裁决 | SLMJury（二元判定损失 <2pp） |
| 开放式评审 | 强档或 PoLL 陪审团 | 便宜 7-8x 且与人类相关性更高 |
| 每轮 token 软预算 | 按档位（standard 初始 200k），bench 校准 | agent/pre-step 预算 gate |
| 全局余额护栏 | DeepSeek 余额 < ¥40 停 | house 先例 [E: PLAN.md] |

## 6b. 检索资源治理（API gateway，架构必备而非事后加装）

- **集中式 API gateway 单例**（宿主平面服务，M1）：单例限速器 + 请求去重 +
  磁盘缓存 + 指数退避；所有 subagent 经它取数，绝不各自打 API。依据：学术 API
  配额是全局稀缺资源（S2 每 key 1 RPS、arXiv 每 3 秒 1 次、CORE 0.5 req/s、
  OpenAlex 每日 10 万 credits），事后加装会导致封 key。
- **gateway 强制的真实机制与诚实边界**（A7 fix-audit：DSH 沙箱不拦网络、
  toolFilter 非权限天花板、sandbox-runtime 是外部产品非 DSH 原语——不能声称硬围栏）：
  防绕过靠**纵深**而非单一硬边界：
  1. **不给出网工具**——检索/取证子代理的 preset 不挂 bash/run_code/自由 fetch，
     只挂 gateway 工具（这是"可用工具面"的真实收窄，即使 toolFilter 不是权限
     天花板，没挂载的工具确实调不到）；
  2. **确定性兜底（真正的防线）**——即便某子代理拿到了出网能力，绕过 gateway
     取的内容**没有 gateway 工具的 RESULT 事件**，其快照 hash 无法在反伪造门
     （EVIDENCE §3b 第 0 级）找到对应事件 → 该证据 FAIL，无法进入 verified。
     可信度不依赖"网络被拦住"，只依赖"无事件的证据不算数"；
  3. 数据分析子代理需联网时经 gateway 代理（本项目自建的 http 代理进程 + 域名
     白名单，**不是** DSH 原语；若不自建则该子代理默认无网，跑本地已下载数据，
     与 EVIDENCE §3a 的 v1 范围一致）。
  诚实残余：恶意子代理仍可用出网能力做**读取**（数据外泄面），本项目不处理敏感
  数据（约束表，ARCHITECTURE §6）；网络管制不是可信度机制而是数据安全机制，二者分离。
- **per-provider 并发闸门**：QPS 天花板相差 30 倍（serper 50-300 QPS、Exa 10、
  Jina ~8、Brave 50、OECD 60 req/**小时**）——每 provider 一张 (QPS, RPM, 并发)
  预算表 + 独立信号量；低并发源（Exa、Brave Answers）做集中旁路，不进每个
  子 agent 工具箱。
- **重负载改走批量数据集**：需要扫描数千篇论文时，先增量镜像相关切片到本地
  （S2 Datasets / OpenAlex dump / arXiv OAI-PMH，全免费），本地并行分析——
  同时满足"本地快照冻结证据版本"的 gate 要求。
- **429/重试策略按 provider 特性分化**（Jina 5 分钟缓存可激进重试；
  Exa/bocha 必须指数退避），写进 provider 配置而非统一策略。

## 6c. 采集面冻结（安全，P-19 的编排落点）

plan-then-execute：查询模板、域名白/黑名单、抓取预算、并发上限在任何不受信内容
进入上下文**之前**固定；单条页面的注入至多污染该条证据，不能扩大抓取面、不能改变
后续工具调用序列；任何 agent 不得因读到的文本修改配置/白名单/预算。对同一 claim
的多轮验证使用不同措辞的独立检索（降低检索面可预测性，防 Fact2Fiction 式定向投毒）。
失败路径也要确定性：超时、重试上限、预算熔断（防御性注入造成的 DoS 也是攻击面）。

## 7. 上下文经济

- worker 一律 spawn 后端（全新会话、prompt 自足）；需要"基于当前证据状态"判断的
  verifier 可用 fork 后端（父会话平衡前缀）[E: dsh-harness-code-archaeology.md subagent 章]。
- conductor 上下文只保 frontier brief + 台账摘要，原始证据永不进 conductor 上下文
  （防 compaction 侵蚀 + KV cache 前缀稳定，P-12 + KV 纪律）。
- 长命跟踪（如"等一篇在检索中被限流的文献"）用 continuable 子代理 + settlement
  兜底通知，不占外环轮次。

## 8. HITL 检查点（人在环，位置预先定死）

商业 DR 产品共同实践 + "错误理解研究问题的整次运行是最大浪费源"（critic 结论）：

1. **启动前——问题澄清**（必选）：scope 步骤先返回"thesis 问句 + in/out 边界 +
   什么证据能推翻 thesis"给用户确认后才建 goal。headless 批跑模式下此确认可由
   任务文件预填（显式跳过是决策不是默认）。
2. **首轮后——方向确认**（可配置，默认开）：L1 首轮立场空间图 + 探索计划落盘，
   goal pause 等确认。
3. **候选后——eval 前**（必选）：候选冻结，人工可注入私有 PDF/更正方向后再进 eval 轨。

机制：goal pause/resume 原生；人类消息自动让路且不耗轮配额——介入零成本。
用户中途投喂材料 = 写入 incoming/ 走同一 admission 门（不开侧门）。

## 9. 与 house 先例的张力及处理

既有两条流水线内部刻意零扇出（单写面 + 串行长杆）[E: PLAN.md]；本系统的超并行成立
条件已在 §3 解决（写面不相交 + 确定性合并）。跨内环并行归 conductor 层调度
（house 先例：跨流水线并行归 conductor 不归单个设计）。若 bench 实测显示并行合并
成为质量瓶颈，降级路径是明确的：内环串行化不改契约——并行度是参数不是结构。
