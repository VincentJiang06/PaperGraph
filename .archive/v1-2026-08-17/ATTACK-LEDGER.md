# ATTACK-LEDGER — 规划文档攻击验证台账

> 协议依据：mp-automator/.attack/r1-ledger.md 先例 + vince-attacker 方法论（P-17）。
> 状态：**规划攻击轮未开始**（等文档集齐：SURVEY.md、TESTING.md 回填完成后启动）。

## 协议（预先冻结）

1. **目标冻结**：攻击前把被攻击文档快照到 scratch 攻击副本，攻击期间不改动。
2. **种子校验**：conductor 在派发前对每轮埋 3-5 个指纹化种子缺陷（记 loc+keywords，
   不进 git），攻击者报告先做 SEED CHECK——种子命中 → run VALID 并剥离种子；
   未命中 → 该透镜作废重跑。
3. **五透镜轮换**（学术域映射）：
   - `coherence` 一致性：文档间契约冲突、最窄权威违背；
   - `gaming` 可作弊性：门/状态机可被作者侧博弈的路径（field-weight 自设类缺陷）；
   - `evidence` 引用实证：文档中每条 [E:] 与 [unverified] 标注的真实性抽查；
   - `reality` 可实现性：与 DSH 实际机制/成本/法律现实的冲突；
   - `foundation` 前提审计：credibility-first、prose 降权、超并行合理性、
     "研究是产品"——核心前提本身（前代 R1 此透镜缺口不许复制）。
4. **PROVE-OR-FLAG**：攻击者必须给出复现/反例构造记录才算 finding（P1/P2/P3），
   否则只能报 flag。
5. **裁决**：跨报告去重 → 归纳根因 → 映射为**结构性重设计**（改文档架构而非打补丁）；
   fix 后由未见修复过程的新鲜上下文做 fix-audit。
6. **诚实记录**：coverage_gaps 如实入账；calibration 清单（"这些成立，别再复审"）
   随每轮产出。

## 计划轮次

| 轮 | 目标 | 透镜重点 | 状态 |
|---|---|---|---|
| A1 | PRINCIPLES.md（含核心前提） | foundation + coherence | 未开始 |
| A2 | ARCHITECTURE.md（含能力映射表） | reality + coherence | 未开始 |
| A3 | EVIDENCE-ENGINE.md | gaming + evidence | 未开始 |
| A4 | ORCHESTRATION.md | reality + gaming | 未开始 |
| A5 | TESTING.md | gaming + foundation | 未开始 |
| A6 | SURVEY.md 溯源抽查 | evidence（URL/数字抽样核验） | 未开始 |
| A7 | fix-audit（A1-A6 修复后） | 新鲜上下文全量 | 未开始 |

## R1 派发记录（2026-08-17，裁决前写入）

- **冻结**：7 份文档快照至 scratchpad `attack-r1/`，sha256 见 `attack-r1-hashes.json`。
- **种子（8 枚，指纹详情在 scratchpad `attack-r1-seeds.json`，此处只记 id/靶）**：
  S1@ORCHESTRATION（轮上限数字矛盾）、S2@EVIDENCE-ENGINE（maker=checker 后门）、
  S3@SURVEY（arXiv ID 改错）、S4@ARCHITECTURE（maxDepth 数字与现实矛盾）、
  S5@PRINCIPLES（自评徽章公理矛盾）、S6@TESTING（held-out 隔离后门）、
  S7@EVIDENCE-ENGINE（NLI 数字改动）、S8@ORCHESTRATION（预算降质量后门）。
- **电池**：11 个新鲜 Claude 透镜攻击者（A1a foundation@PRINCIPLES、A1b coherence@PRINCIPLES、
  A2a reality@ARCHITECTURE、A2b coherence@ARCHITECTURE、A3a gaming@EVIDENCE-ENGINE、
  A3b evidence@EVIDENCE-ENGINE、A4a reality@ORCHESTRATION、A4b gaming@ORCHESTRATION、
  A5a gaming@TESTING、A5b foundation@TESTING、A6 evidence@SURVEY）+ 1 综合分析者（R+1）
  + 1 跨厂商攻击者（DeepSeek V4-Pro，五透镜快扫 4 份核心文档，买 model-tier 独立性）。
- **SEED CHECK 规则**：各 run 报告未命中其靶文档种子 → 该 run 作废不计入收敛；
  命中 → run VALID，种子从发现中剥离。
- **ledger 完整性**：本仓库会话未获 git commit 授权，哈希台账代替 commit 基线
  （degrade gracefully，按 skill 协议如实记录）。

## R1 SEED CHECK 结果（全部 VALID）

11 个 Claude 透镜 run 各命中其靶文档种子（S5×2、S4×2、S2+S7×2、S1+S8×2、S6×2、S3×1），
全部 run VALID，无作废；DeepSeek V4-Pro 命中 S1/S2/S5/S8。种子在裁决时从发现中剥离
（种子只存在于冻结副本，未泄入真实文档——已 grep 确认 128 轮 / maxDepth 5 在真实文档
零残留）。原始产出：197 条 Claude 发现（29 P1）+ 20 条 DeepSeek 发现；裁决压缩为
20 条根因主题 RT-1..RT-20 + 12 个未覆盖 P2 簇（MC），由跨厂商 DeepSeek 独立裁决者复核。

## R1 裁决与修复（RT + MC）

裁决者（DeepSeek，跨厂商 model-tier）确认：RT-1..RT-9 全部 P1、修复方向正确；
RT-12 概括不当（实含 S4 种子，剥离后仅剩引证缺口，降 P3）。以下逐条记修复：

| id | 严重 | 缺陷 | 修复落点 | 状态 |
|---|---|---|---|---|
| RT-1 | P1 | "承重"无定义无判定者，作者自标可逃验证 | EVIDENCE §3b 机器判定承重（被引/被依赖恒承重，非承重需独立审计授予） | 已修 |
| RT-2 | P1 | status 写权跨文档矛盾 + 终态授权 agent（含 maker=checker） | EVIDENCE §2 写权唯一=门 + 裁决工件 + reviewer≠producer；PRINCIPLES P-5 补裁决/写权分离；ORCH 写面矩阵拆 status 列；删除 S2 种子引入的同 agent 复核 | 已修 |
| RT-3 | P1 | data 容差作者自报 + 常数脚本可洗 verified-by-data | EVIDENCE §3a 容差检查方固定 + 新增输入依赖门（反事实探针） | 已修 |
| RT-4 | P1 | 反伪造门不绑定快照字节 + evidence 写者矛盾 | EVIDENCE §3b 第 0 级快照字节锚定（工具执行器直写+事件记 hash）；ORCH 写面矩阵改 evidence 写者 | 已修 |
| RT-5 | P1 | inference conclusion 与 steps 无人把关 | EVIDENCE §3c 复核者收全量+conclusion 强度检查题 | 已修 |
| RT-6 | P1 | 头条指标分母自产可灌水 + L1 同义反复 | TESTING §3 分母改独立审计反向抽取 + 承重×实质分层 + held-out 侧独立测量 | 已修 |
| RT-7 | P1 | 语义漂白均衡（弱化到 NLI 全过） | TESTING §4 防线 5 语义漂白检测 + D4 结论强度一致性 kill | 已修 |
| RT-8 | P1 | 高难/争议 claim 三层无非循环真值信号 | TESTING §6b 无专家时只停 contested/logically-derived 不升 verified；EVIDENCE §2 综合类状态上限 | 已修 |
| RT-9 | P1 | 证据饱和可由 conductor 不派发制造 | ORCH §5 规则 1 改为需实际派发 L2/L4 才计入饱和 | 已修 |
| RT-10 | P2 | TESTING 头部"数字均已核验"过度声明 | TESTING 头部限定为 9 条载荷数字，其余标 not measured beyond survey | 已修 |
| RT-11 | P2 | 状态枚举跨文档漂移（contested/disputed；五态/八态） | EVIDENCE §2 唯一权威 + 全文档统一 contested；PRINCIPLES P-4 指向 | 已修 |
| RT-12 | P3 | maxDepth 引证缺口（S4 剥离后） | 真实文档 maxDepth 3 一致；引证已注明 dsh-tool-subagent 来源 | 已修 |
| RT-13 | P2 | 规划自身 [E:] 无内容锚定 + 深读指针不可解析 | README 证据纪律债声明，M0 偿还项 | 已记债 |
| RT-14 | P2 | PDF 125k/篇 vs 200k/轮 预算冲突 | ORCH §6 effective-tokens 记账 + 全文深读走 verify 队列专属预算 | 已修 |
| RT-15 | P2 | ≥2 源可被两个 preprint 满足 | EVIDENCE §3b venue 层级要求 + preprint-only 降格 | 已修 |
| RT-16 | P2 | 图表 40-56% 误写为"错误率"（实为准确率） | PRINCIPLES 裁剪 + EVIDENCE §3d 口径改准确率 | 已修 |
| RT-17 | P3 | 计数错误（flags 六/七；fixture 12/20） | flags 七项、fixture 27 条统一 | 已修 |
| RT-18 | P2 | admission 并发时序未规定 | EVIDENCE §4 单实例文件锁+字典序+矛盾并存 | 已修 |
| RT-19 | P2 | 北极星致大量 unverified 产出不可用 | PRINCIPLES §0 "unverified 是信息" + ORCH 生产 run 自证型收口 | 已修 |
| RT-20 | P2 | 超并行增益无 falsification | 见下 MC / TESTING §5 需补并行度对照臂（记入 loop 首里程碑） | 部分修+记债 |

**未覆盖 P2 簇（MC，裁决者补）修复**：架构契约脱节（ARCH 目录/门通道对齐 v2 manifest+CAS）✓、
确定性门定义漂移（ARCH Class-0/1/2 分级）✓、生产 run SHIP/REVISE 收口（ORCH 双模式）✓、
红队验收循环（TESTING §7 双向验收 + R1-R9）✓、人力/专家未建模（TESTING §6b）✓、
引文快照-work 身份解绑（EVIDENCE §3b 第 2b 级）✓、API gateway 强制（ORCH §6b 工具面收窄）✓、
成本模型 provider 不匹配（ORCH §6 DeepSeek 无 Batch 注记）✓、多模态能力缺失（ARCH 能力表补行）✓、
eval-of-eval 负向测试（TESTING §8）✓、SURVEY verified 印章失真（SURVEY 6 处更正）✓、
held-out 隔离残余（TESTING §2 诚实声明）✓。

**裁决驳回（8 类，不修）**：以"外部服务未实现"论规划可行性、要求证明供应商长期价格稳定、
以 n=1 案例否定原则、把前代成本参考当硬约束、对已诚实标 secondary 的来源继续追责等——
均为对规划阶段不公平的要求或证据强度问题（非文档可修缺陷），如实记录不动。

## A7 fix-audit 结果（5 个新鲜审计者，五透镜，2026-08-17）

**裁决：全部 5 个审计者 FIX_FIRST**——确认 RT-1/2/3/4/5/6/7/8/9/11/14/15/19 修复
REAL 且大多跨文档相容（非 cosmetic，故非 NOT_CONVERGED），但发现修复引入的新矛盾
与半修。28 条残留中约 10 条材料级，已在 R2 修复：

| A7 发现 | 严重 | 缺陷 | R2 修复 | 状态 |
|---|---|---|---|---|
| C1 | P2 | ARCHITECTURE M2 line 114 漏改（台账单写者=orchestrator，与新分权矛盾） | ARCH M2 写面所有权对齐 EVIDENCE §2/ORCH §3（orchestrator 永不写台账） | 已修 |
| C2 | P2 | 超并行-vs-串行 A/B 债未在读者可见文件 surface（5 审计者共同点名） | README 未偿债 #2 + TESTING §5 臂 B（并行度证伪臂） | 已修 |
| G1 | P2 | reviewer≠producer 只绑自报 writer_agent_id 字符串 | EVIDENCE §2 改绑 harness childId（session 事件权威身份） | 已修 |
| G2 | P2 | 头条分母仍可被作者散文选择性叙述洗白 | TESTING §3 分母 = 台账承重集 ∪ 散文，两侧并集抽取 | 已修 |
| G3 | P2 | 反事实探针无幅度阈值，ε-依赖脚本可过 | EVIDENCE §3a 输入依赖门改"成比例且量级相当" | 已修 |
| G4 | P2 | 饱和只校验派发发生、不校验实质，空壳派发可伪收敛 | ORCH §5.1 加派发产出非退化 + cartographer 检索面抽查 + 诚实残余 | 已修 |
| G5 | P2 | RT-8"无专家不升 verified"只在 TESTING §6b，未接入 EVIDENCE §2 状态机权威 | EVIDENCE §2 难度分类硬顶写进状态机前置判据 | 已修 |
| R1 | P2 | gateway 网络围栏过度声明（DSH 沙箱不拦网、toolFilter 非天花板、sandbox-runtime 非 DSH 原语） | ORCH §6b 改纵深防御 + 诚实边界（可信度靠"无事件不算数"非网络拦截） | 已修 |
| R2 | P2 | effective-tokens 公式依赖 DSH 不暴露的 per-step 缓存分解 | ORCH §6 改总量 token 记账 + 分账户；缓存作降成本偏置非记账项 | 已修 |
| coh-3 | P3 | cross-checked 态名不在 EVIDENCE §3d 权威枚举 | ARCH 能力表改"跨厂商双模型一致锚点"措辞 | 已修 |
| coh-4 | P3 | "≥2 发布者独立来源"字面波及 data/inference 类 | EVIDENCE §3b 作用域限定为 kind=source | 已修 |
| ev-* | P2/P3 | SURVEY 更正未完全落地（Elicit 46%、XBench 拼写、11-57% 归属） | SURVEY body：Elicit→44.6%、xbench-DeepSearch 正名、11-57% 归属更正 | 已修 |

**A7 快照瑕疵（非文档缺陷）**：fix-audit 快照 `fixed-r1/` 只含 6 份主文档，未含
SURVEY.md 与 ATTACK-LEDGER.md → 多个审计者报告"这两个文件缺失"及"[E: SURVEY §x]
不可解析"。这是快照裁剪产物（两文件在真实目录存在），前轮裁决已把"以快照裁剪定罪"
列为驳回类，如实记录不作为缺陷。

## 收敛状态（诚实声明）

- 完成轮次：R1 攻击（11 Claude 透镜 + V4-Pro 跨厂商 + 综合）→ 裁决（V4-Pro 独立
  裁决者）→ R1 修复 → A7 fix-audit（5 新鲜审计者）→ R2 修复。
- **未跑 R3 fix-audit**（对 R2 diff 的再审计）：按 attacker 协议，"最后一轮含修复
  但无 fix-audit = 未收敛"。本规划的 R2 修复**未经独立 fix-audit**——记为
  coverage_gap，实施期（loop 首轮）应对 R2 diff 补一轮 fix-audit。当前状态：
  **material 缺陷已闭，但收敛性未经第三方独立确认**（诚实降级，P-18）。
- 独立性层级：R1/A7 均达 model-tier（Claude 透镜 + 跨厂商 DeepSeek 裁决/攻击）；
  R2 修复由 conductor（Fable）执行，其 fix-audit 缺席是唯一的独立性缺口。
