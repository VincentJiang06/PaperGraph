# academic-research-plugin — 规划仓（planning phase）

> 一个彻底全新的 DSH profile：**超并行、多 loop 的学术证据探索系统**。
> 核心价值只有一个：**可信度与学术溯源性**——每条论断都携带显式的
> verified / unverified 状态，且必须由 (a) 数据分析、(b) 他人论文结果、
> (c) 严密逻辑推断 三者之一背书。研究是产品；论文散文只是收尾出口。

**当前状态：规划阶段。没有任何实现代码。** 本目录是完整的调研 + 规划文档集，
规划完成并通过多轮 attacker 验证后，由 `.loop/` runbook 驱动持续迭代开发。

## 文档地图

| 文件 | 职责 |
|---|---|
| [PRINCIPLES.md](PRINCIPLES.md) | 需求与设计原则：可信度公理、claim 状态机、从三代失败中继承的禁令 |
| [SURVEY.md](SURVEY.md) | 相关工作调研（十个维度，全部结论带 URL 溯源） |
| [ARCHITECTURE.md](ARCHITECTURE.md) | DSH profile 架构：bundle/patch 组成、模块分拆、与 harness 原语的映射 |
| [EVIDENCE-ENGINE.md](EVIDENCE-ENGINE.md) | 证据引擎：claim 台账契约、三类背书的验证机制、反伪造门 |
| [ORCHESTRATION.md](ORCHESTRATION.md) | 超并行多 loop 编排：loop 分层、写面所有权、预算与停机 |
| [TESTING.md](TESTING.md) | 测试计划：负向测试、held-out eval、跨领域论文级实测、gated-vs-freehand A/B |
| [ATTACK-LEDGER.md](ATTACK-LEDGER.md) | attacker 轮次台账（每个环节的攻击、裁决与修复记录） |
| [.loop/academic-research-build.loop.md](.loop/academic-research-build.loop.md) | 持续迭代开发 runbook（loop-constructor 产出，8 阶段 M0→M8 + 里程碑 1 A/B；linter PASS）。伴随 `.design.json`（源）与 `.loop.json`（渲染）。**⛔ 设计态，未启动。** |

## 阅读顺序与权威边界

PRINCIPLES → ARCHITECTURE → EVIDENCE-ENGINE → ORCHESTRATION → TESTING。
文档冲突时最窄契约赢：证据契约问题归 EVIDENCE-ENGINE，编排问题归 ORCHESTRATION，
验收问题归 TESTING；PRINCIPLES 是所有文档的上位约束。

## 证据基线（本规划自身的溯源）

- DSH 运行时四份架构分析：仓库根 `DSH-架构分析.md`、`dsh-agent-core-architecture.md`、
  `dsh-harness-code-archaeology.md`、`dsh-security-execution-analysis.md`
- 前代项目 Paper Graph（含三代失败档案与四次消融）：`/Users/vince/playground/misc/Paper Graph/`
- 本仓库工程方法论（loop runbook / 攻击电池 / 溯源门先例）：`.loop/`、`mp-automator/.attack/`、
  `serper-harvester/`、`plugin-creator/`
- 外部调研来源：见 SURVEY.md 逐条 URL

**未偿债（R1/A7 攻击轮确认，读者可见，勿伪装为已解决）**：

1. **[E:] 证据指针无内容锚定**：本目录 [E:] 指针为路径级引用，无内容哈希；
   标注"深读"的指针指向本会话调研工件而非独立可解析文件。M0 偿还：全部 [E:]
   升级为 `路径#锚点 + 冻结 hash`。在此之前引用 Paper Graph 档案以其 2026-07-10
   时点快照为准。
2. **超并行相对串行的净收益从未证伪**（A7 fix-audit 五审计者共同点名）：系统名字里
   的"超并行"是结构性下注，但 [TESTING.md](academic-research-plugin/TESTING.md) §5
   的 A/B 只隔离"门体系"（gated vs freehand），**未隔离并行度变量**；
   [ORCHESTRATION.md](academic-research-plugin/ORCHESTRATION.md) §9 的"并行度是参数
   不是结构"是设计断言**不是**已证结论。按 P-2（结构投资需 A/B 证明增益），
   这是一项**未偿债**：必须跑"超并行 vs 同预算串行"对照臂才能兑现。实施期
   里程碑 1 的 A/B 必须含此臂；在它通过前，"超并行值得其成本"是假设不是事实。

## 运行面约定

一切运行、调试、验收都以 **TUI / terminal（headless profile 形态）** 为一等公民；
WebUI 不作为任何调试或验收步骤的载体（用户明确要求，2026-08-17）。
