# M0 三场景推演记录(2026-07-09)

冻结前把 5 份 schema 对着三个真实形态的调查走了一遍纸面流程。记录露馅点与
修正;没露馅的部分不复述。

## 场景 A — 论文调研(ai-jobs 问题,原用例)

根观点 = 命题("AI agents 2020-2025 主要造成岗位结构重组而非净消失")。
发散(含 adversarial"哪些高AI采用行业就业不降反升")→ 叶子穷尽 → 升格
("2020-2025 有哪些任务被实际替代的直接证据?")→ subagent 调查 → conclude
携证据引用 → 根 synthesis。**全流程无露馅**;compiler 消费 export(V2 接回)。

## 场景 B — 技术选型("该不该迁移到架构 X")

根观点 = 提案命题。发散方向天然独立可答("X 在我们的写负载下失效模式是
什么?"、adversarial"不迁移会烂在哪?")。结论 lean 直接映射决策倾向。
**露馅 1**:evidence 多为内部 benchmark/文档,没有 url——`locator` 字段
(文件路径/页码/小节)必须一等公民,url 与 locator 二选一即可(check 软警
告督促,不硬卡)。已修入 synthesis.v1。

## 场景 C — bug 根因分析

根观点 = 待解释现象;兄弟观点 = 竞争假设(每个假设是一个 viewpoint)。
**露馅 2**:假设被证伪后 `retired`,但一年后读树史看不出**为什么**退休——
node.v1 增加 `status_note`(retired/closed/stuck 的一行原因)。
**露馅 3**:证据是本地日志(`logs/app.log:1234-1260`)——locator 再次确认
必要。
**露馅 4**:竞争假设间"证据互斥"(支持 H1 的证据同时削弱 H2)在 V1 没有
表达位——**接受**:记在两个 synthesis 的 summary/open_questions 里,跨节点
证据复用是 V2 docs 库的正题,V1 不加机制(P4)。

## 通用露馅

**露馅 5**(checkpoint 至上的直接推论):批量 add(--file)不够——观点是
零星成形的,必须有单节点即时落树通道。`nd add` 增加旗标单条模式。
**露馅 6**(trace 硬需求):任何"树为什么长成这样"的问题只能靠事件日志
回答;event.v1 进 V1 冻结集,含只读命令(brief 的调用本身就是"发生过一次
恢复"的证据)。

## 冻结决定

- schema 5 份:envelope / session / node / synthesis / event,全部
  `additionalProperties:false`,`$id` 带版本,运行时加载(P9)。
- CLI 10 组:init / add(双模式) / promote / set-status / conclude / brief /
  show|tree / log / check / export。
- 状态机(全部由 nd 校验,不设引擎):
  - viewpoint:open→expanding(首个子节点自动)→synthesized(conclude 自动)
    →closed(显式);synthesized→expanding(新方向重开,显式);任意→retired。
  - claim:pending→investigating(显式)→concluded(conclude 自动)|
    stuck(显式,带 reason);任意→retired。
  - promote:viewpoint(open|expanding|synthesized)→claim(pending)。
