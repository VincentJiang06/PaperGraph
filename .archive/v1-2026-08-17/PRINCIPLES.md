# PRINCIPLES — 需求与设计原则

> 本文档是全部规划的上位约束。每条原则都标注证据来源；无证据的原则不允许存在。
> 证据标注格式：`[E: <路径或出处>]`。

## 0. 使命

构建一个 DSH profile（工作名 `academic-research-plugin`），它是一个
**超并行、多 loop 的学术证据探索系统**：

- **产品是研究，不是论文。** 系统的核心产出是一份经过验证的证据体
  （claim 台账 + 证据工件 + 验证记录），散文式论文只是台账之上的一个薄出口。
  用户原话："核心是做好研究，而不是产出论文，论文的收尾部分非常简单，
  但是会干扰文章的构成。"
- **每条论断携带显式状态。** verified / unverified 不是印象，是机器可查的字段，
  背书通道只有三条：(a) 数据分析（可重跑）、(b) 他人论文结果（可回溯到原文）、
  (c) 严密逻辑推断（前提可追、推理可检）。
- **可信度与溯源性是唯一的北极星。** 所有设计取舍冲突时，向可信度让步。
- **unverified 是信息不是失败。** 高可信度系统的产出必然包含大量 unverified /
  contested 状态——这是被标注的不确定性地图，本身就是研究价值；呈现层按状态
  分层展示而非隐藏，绝不为"报告好看"而软化状态（对 foundation 攻击
  "北极星导致产出不可用"的回应：不可用的是伪装成确定的结论，不是诚实的不确定性）。

### 非目标

- 不做论文排版/润色/投稿工具链（收尾出口保持极简）。
- 不做通用 deep-research 产品（面向的是论文级研究，不是网页摘要报告）。
- 不重建 claim 图/树框架（见 P-1，这是被判死刑的路线）。

### 显式范围裁剪（决策而非遗漏）

- **语种：v1 只支持中文+英文**。跨语言证据链（claim 英文、证据日文等）明确出界；
  升级路径：译文引语无法在原文快照精确命中，需另设 `translated-excerpt` 锚定机制后再开。
- **图表/表格承载的数值证据**：不默认归入 verified-by-source，采用三级阶梯
  source-located → machine-extracted → verified-by-source（已裁决，依据真实图表
  抽取 SOTA **准确率**仅 40-56% [E: SURVEY §12.7 ChartQAPro]；细则见
  EVIDENCE-ENGINE §3d）。
- **verified-by-data 的 v1 边界：仅支持用户提供/已下载数据的重跑验证**，agent
  自主取数分析推迟 v2（已裁决，决定性依据是可靠性梯度而非成本；见
  EVIDENCE-ENGINE §3a）。

---

## 一、从三代失败中继承的禁令

### P-1【最高禁令】不造"结构=质量"框架

Paper Graph 的三代框架（legacy 规范集 → paperproof v2 全实现 13,949 行 → nodify 树/CLI）
被四次严格消融判死：质量增量曲线 v1 +1.0 → v2 +0.13 → v3 **−0.39**（刚性结构在强模型
激进模式下是负资产，压制 reframe 与意外发现）。595 个测试全绿的框架在产品维度归零归档。
[E: /Users/vince/playground/misc/Paper Graph/archive/pre-reset-2026-07-09/nodify/comparison{,2,3,4}/RESULTS.md]
[E: Paper Graph/DESIGN.md 开篇判词 "Four rigorous ablations said it doesn't. We stop building frameworks."]

**质量的真正杠杆是"思维纪律"**——prompt 内嵌的方法论（发散不拆解、强制对抗线、
逐字引文、蒸馏后丢弃），它无需任何工具就贡献了消融中最大的单项增量（raw→skills +1.0）。
[E: comparison/RESULTS.md "the discipline is the biggest single lever"]

### P-2 结构性投资只允许买三样东西

四次消融中唯一跨轮持久复制的结构优势：

1. **强制可审计性**：逐字引文子串校验、content_hash 去重、cite 硬解析
   （v2 尸检结论"唯一值得全额继承的三件便宜货"）；
2. **有界的 resume 状态**：frontier-boxed brief 的日志斜率比线性日志低 3 倍
   （v4 消融唯一实证优势）——对本系统的超长多 loop 直接相关；
3. **结论强制落盘**：一切决定写文件，抗 compaction（防坑清单 P14）。

任何超出这三类的结构投资默认拒绝，除非 A/B 证明其增益。
[E: Paper Graph/archive/pre-reset-2026-07-09/v3/docs/01-anti-failure.md P1–P15]

### P-3 工程防坑清单整体继承（P1–P15 中与本系统最相关的）

- **P1 契约欠规定**：每个 worker prompt 逐键枚举输出 schema + 漂移守卫测试；
- **P3 接线矩阵**：每个 schema 必须有产有销 + 贯穿测试（不许出现无人消费的字段）；
- **P4 复杂度预算写进合同**：机器层压过研究层是 v2 live run 的真实死因
  （8 次校验失败中 5 次是机器层故障）；
- **P5 契约冻结**：项目 init 即冻结 schema set hash；
- **P7 幻觉三件套查杀**：编造引用 / 拼接引文 / 数字自评 → 逐字子串校验 +
  content_hash + cite 硬解析；
- **P11 边界严格、内部自由**：prompt 不许把模型当表格机（403/PDF 要能自主改道）；
- **P12 并行 worker 不相交输出 + 单写者合并**（v2 唯一没出过事的约束）；
- **P15 每个字段必须有消费代码路径**（反 schema 幻想复杂度）。

[E: Paper Graph/archive/pre-reset-2026-07-09/v3/docs/01-anti-failure.md]

---

## 二、可信度公理与 claim 状态机

### P-4 claim 台账是核心工件（不是论文，不是图）

前代 claims.tsv（7 列 TSV：claim_id/kind/claim_text/value/raw_ref/transform_or_source/reproduced）
被验证为性价比最高的证据载体形态。本系统继承 TSV 极简形态并扩展：

- **kind 三分**：`data`（可重跑变换）、`source`（他文引证）、**新增 `inference`**
  （严密逻辑推断：raw_ref = 前提 claim_id 列表，transform_or_source = 可检查的推理链文件）。
  前代只有 data|source 两类，"逻辑推断"无 grounding 契约是已确认的空白。
  [E: pg-contracts 深读 & Paper Graph/gates/rigor.md]
- **状态字段是枚举不是布尔**：核心五态 `verified-by-data / verified-by-source /
  logically-derived / unverified / contested`，加运行三态 `pending / source-contested /
  stale`——**完整状态机以 EVIDENCE-ENGINE §2 为唯一权威**，全部文档统一用
  `contested`（不用 disputed）。nuclear-safety 的 5 条 honesty flags
  证明二元 reproduced 表达不了：点估计无置信区间、转引来源（WNA 转引 IPCC）、
  cherry-picking 窗口、最优情形比率。需增补：不确定度表达、来源独立性分级、敏感性标注。
  [E: Paper Graph/eval/verdicts/nuclear-safety.json]
- **加字段前先有消费它的代码路径**（P15），扩展保持克制。

### P-5 状态判定权不在作者手里

- `reproduced 留 ?，门的输出才是记录`——作者永不自评。
  [E: Paper Graph/gates/rigor.md]
- 阈值与 ground truth 不能由被检方自设：前代 divergence 门的 field-weight 由
  paper.md 自声明（作者可自降阈值 K 到 0.5），是已证实的"裁判尺子在被告手里"缺陷，
  本系统所有阈值由检查方轨道固定，作者轨只读。
  [E: Paper Graph/gates/divergence_gate.py:82-84（field_weight() 从 paper.md 读取）]
- **SCREEN + 权威裁决两层协调**：机械筛（快、可复现、有词面假阴性）给 provisional
  状态，agent 复核（权威、可 RESCUE）产出**裁决工件**；kill 只对 unrescued 触发。
  [E: Paper Graph/eval/harness.py reconcile() + eval/CHANGELOG.md v0.3.0]
- **裁决权与写权分离（与 P-19 的一致性）**：agent 复核的裁决只是**输入工件**；
  状态置位的唯一执行者是门代码，它校验裁决工件存在、复核者 id ≠ 产出者 id
  （fail-closed）、且裁决附反例构造记录后才写状态。LLM 判断被隔离在
  maker≠checker + PROVE-OR-FLAG 之后，永远不直接写台账。

### P-6 引用的存在性与忠实度由运行时痕迹背书，不由模型散文背书

- 每条引用 URL/DOI 必须**逐字来自检索工具的 RESULT 事件**——禁止凭记忆写、补全、
  修正 URL。这是 serper-harvester 已实装并经 e2e 门验证的纪律，直接查杀学术幻觉引用。
  [E: serper-harvester/news-harvester-preset/skills/harvest/SKILL.md + checks/harvest_e2e.sh]
- 模型散文永远不是地面真值：mp-automator R5 实录 driver 模型伪造过貌似合理的引文；
  只有 session jsonl 的 TOOL-RESULT 块可采信。
  [E: mp-automator/.attack/r1-ledger.md R5 教训]
- 三层结构照搬：模型写暂存区 → 无模型/无网络/无时钟的确定性脚本裁决入库 →
  反伪造门在 session jsonl 层断言逐字出处。
  [E: serper-harvester/README.md "xxxwild adaptation" 节]

---

## 三、质量模型

### P-7 双层质量模型 + Isolation Contract（逐字继承）

环内确定性门（廉价地板，作者每轮自跑）+ 环外文献锚定盲评（真信号，SHIP/REVISE 裁决）
的分离已被量化数据证明必要：**4/4 论文自家双门全绿，独立 eval 3/4 REVISE——过拟合被量化**。
证据探索系统的同构风险完全存在（探索 agent 自建的证据体=作者脚手架，同样会漏掉不利证据线）。
[E: Paper Graph/eval/CHANGELOG.md v0.2.0 "the overfit, exposed"]

Isolation Contract 五条逐字搬入：两轨道两 CHANGELOG 两版本号；评测唯一可改理由 =
有证据的评测自身 bug（须留证）；评审 agent 对作者脚手架盲；评测 held-out 按节奏跑；
禁止 teaching-to-the-eval。
[E: Paper Graph/eval/EVAL.md Isolation Contract]

### P-8 对抗性程序 > rubric 评分

nuclear-safety 踩 3 条 kill-criterion（K8 稻草人、更强未回应反驳、claim 覆盖 75%）时，
3 个 rubric referee 全给 accept。可信度判定必须以对抗性程序为主：
每立场 steelman 辩护人打稻草人分、adversary 升级构造更强反驳、独立审计员脱离台账
反向抽取全部断言查覆盖 + cherry-picking；rubric 评分只作辅助信号。
[E: Paper Graph/eval/verdicts/nuclear-safety.json + eval/reports/nuclear-safety.md]

### P-9 fail-closed 是代码性质不是文档性质

前代每个洞都是同一模式："子检查失败被记录但不进最终判定"（DVC 失败 vs exit code、
面板缺失仍 SHIP、崩溃→None→N/A、honesty_flags 只打印）。规则：

- 任何子检查三态 PASS/FAIL/**MISSING，MISSING==FAIL**；
- 聚合器对"必需维度清单"做全集校验，而非对"碰巧在场的字段"做条件校验
  （现成正确范本：skills/papergraph/scripts/validate_eval_bundle.py——讽刺的是它造出来
  却从未接回主 eval，同一契约只允许一个可执行权威）；
- **新鲜度绑定**：验证产物携带本次执行的输入 hash/执行 id，聚合时校验匹配，
  杜绝陈旧 metrics 掩盖失败；
- 每条 pass 规则必须有对应负向测试（删标签/伪造引文/篡改数字必须变红），
  负向测试必须经工具触发并断言被拒，"存在即覆盖"被明令禁止。

[E: Paper Graph/README.md 四条自认缺口 + gates/rigor_gate.py:189 + eval/harness.py load_verdicts()]
[E: mp-automator 测试纪律（种子 S2 作弊模式在 R3/R4 两次抓到自家测试）]

### P-10 检查必须落在运行时痕迹上

本仓库三次踩同一坑（persona patch 打错行全绿但未生效 / 角色包读取检测被字符串拼接绕过 /
dump-config 放过纯 stub 插件）换来的铁律：**当检查与它认证的性质隔着一个执行边界时，
该检查是空心的**。修复形态全部是断言运行系统自己的痕迹（session jsonl 运行时提示词、
真实 boot、工具 RESULT 事件）。
[E: plugin-creator/REPORT.md + .loop-state/DECISIONS.md 三连坑记录]

---

## 四、编排原则

### P-11 并行的前提是写面不相交

- 每 worker：一个 bounded prompt + 有界输入 + 恰一个声明输出
  （结构化返回或预分配不相交路径）；共享工件单写者；chat 文本非持久态，
  orchestrator 按接口逐一校验后才 merge。
  [E: Paper Graph/AGENTS.md 并行契约 + 防坑 P12]
- 证据条目按内容哈希键名（sha256 文件名）天然无冲突——超并行扇出的写面方案。
  [E: serper-harvester dedup.mjs 模式]
- 跨 loop 并行归 conductor 层处理，单个 loop 内部保持克制（本仓库两条流水线
  内部刻意零扇出的先例与理由：单写面 + 串行长杆）。
  [E: PLAN.md 治理规则]

### P-12 证据必须在产生的瞬间物化，抗 compaction

DSH compaction 会侵蚀工具结果（8192 字符 pruner 保头 4096 尾 1024 + 摘要替换），
"证据只活在工具结果文本里"不可靠。所有需要长期存续的证据必须及时物化为：
log-only 会话事件（不进 surface、不被压缩触碰）或文件（大原文走 spillStore/磁盘）。
这是可信度目标下最重要的单条运行时约束。
[E: dsh-agent-core-architecture.md compaction 章 + DSH-架构分析.md]

### P-13 长循环用 harness 原语，不自旋

goal + goal-round-driver（256 轮预算、CAS revision、连续 3 轮同因自动 blocked、
round 预留 + checkpoint 崩溃安全）是现成的长循环原语；armed 激活态不持久化是有意设计，
**跨进程重启的续跑必须是显式编排步骤**（goals.resume），规划必须把"重启后如何续跑"
写成显式流程而不是假设它自动发生。
[E: DSH-架构分析.md goal 章 + dsh-harness-code-archaeology.md]

### P-14 预算护栏预先量化，进设计不进事后

- DSH 无内建美元预算硬顶，tokenMeter 只给用量投影——预算 gate 须自建
  （agent/pre-step waterfall 或 conductor 层）；
- 成本现实：plugin-creator 一次 e2e ≈95 分钟/16 subagents/≈¥6，超并行多 loop
  会按环数倍乘；共享余额护栏（如 DeepSeek 余额 < ¥40 双停）与 per-stage cap
  是既有先例，必须提前进设计。
  [E: plugin-creator/REPORT.md 成本实测 + PLAN.md 护栏]

### P-15 A/B honest test 前置，不许押后

前代最大未完成债务：gated vs freehand 对照**从未跑**——整套门体系"是否真正提升质量"
至死是信仰。本系统把 baseline-first / keep-if-better 写进第一个里程碑：
同一 topic 双臂产出、都过独立 eval、gated 不赢就如实报告，
"do not add more framework to hide it"。
[E: Paper Graph/DESIGN.md "the honest test" + WORKFLOW.md stop rules]

---

## 五、运行面与实现纪律

### P-16 TUI/terminal 是一等运行面

一切运行、调试、验收走 headless/TUI（`dsh --profile <name> "task"`，
exit code 按 turn/end reason）；WebUI 不承载任何调试或验收步骤（用户明确要求）。
[E: 用户指令 2026-08-17；DSH-架构分析.md headless 模式]

### P-17 攻击验证是流程公民，不是事后仪式

每个规划环节与每个交付里程碑都过多攻击者电池：指纹化种子缺陷验证攻击者有效性、
多透镜分工 + 至少一个跨厂商攻击者、PROVE-OR-FLAG（复现才算 finding）、
裁决归纳根因并映射为结构性重设计而非补丁、fix-audit 用没见过修复过程的新鲜上下文。
前代 R1 的 Foundation 透镜缺口（用户中断导致深层前提从未被专门攻击）不许复制——
本项目的核心前提（credibility-first、prose 降权、超并行合理性）安排专门的 foundation 攻击。
[E: mp-automator/.attack/r1-ledger.md 全流程 + coverage_gaps 记录]

### P-18 诚实报告规范

REPORT/验收文档强制配对指标（每个 success 指标配对 integrity/damage 对应项，
否则显式标 not measured）；n=1 比较必须声明；未经门核验的成本数字标 indicative only；
verdict 用 min() fold 且书面结论永不高于 fold 输出。
[E: plugin-creator/REPORT.md 规范 + .loop runbook Run report 章节]

### P-19 信任边界：不受信数据永不影响程序流

从不可信网页/PDF 大规模摄取证据的并行系统是间接提示注入的最大攻击面
（PoisonedRAG：百万级语料 5 条毒文 ~90% 攻击成功率；野外 12 亿 URL 测量发现
15,387 个注入实例，70% 藏在非渲染通道；arXiv PDF 实案 18 篇白字注入）。
架构级确定性边界（CaMeL 原则）而非模型层概率防御：

- loop 状态机、gate 判定、verified/unverified 置位**全部由确定性代码执行**；
  LLM 读到的任何文本只能作为数据进入，永不被状态机解析为指令；
- 抓取即冻结快照（bytes + sha256 + 时间戳），双视图存储（原始 bytes 审计用；
  剥离非渲染通道的规范化视图才送 LLM）；
- **诚实边界写死**：逐字命中冻结快照证明 provenance（源确实说了 X），
  不证明 truth（X 为真）——中毒页面本身能通过逐字命中；真值层靠来源分级 +
  ≥2 发布者独立来源 + 代码内聚合判定（RobustRAG 式隔离-聚合）兜底；
- 残余风险清单（R1-R9）与五类红队剧本进 TESTING §7，作为 attacker 轮验收标准。

[E: SURVEY §12 security-injection（CaMeL arXiv 2503.18813、PoisonedRAG、WARP、
Fact2Fiction 等一手文献）]

### P-20 口径三元组与证据谱系

数字类 claim 的验证必须核对**口径三元组**（测什么指标 / 什么样本 / 与谁对比），
而非字符串出现。依据：本项目载荷数字核验 pass 实测 9 条中 3 条失真，模式统一为
"数字真实存在但口径/对象被换掉"。配套规则：SOTA 类断言强制时点戳并自动过期为
dated；每条数字记录证据谱系，**同一上游来源的多次转录只计一个独立来源**
（防伪独立印证——同一数字在四份报告出现看似交叉验证，实为同源转录）。
[E: SURVEY §12 numbers-verification]

### P-21 gate 阈值现场校准，不引用文献数字

所有 gate 阈值必须用自建 held-out 金标准集现场校准（Elicit 官方 94-99% vs
独立评测 81.4% 的落差；scite F1 数字来自撤稿引文极端样本）；校准集评估本身是
开发 loop 的客观 gate；不同学科设不同先验信任基线（DARPA SCORE 学科差异）。
[E: SURVEY §7 evidence-methodology 校准纪律]

