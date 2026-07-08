# v3 防坑清单 — v2 每一次真实事故的根因与 v3 强制对策

> 本文是 v3 的工程底线。每一条都来自 v2 的**真实事故**(不是假设),给出根因、
> v3 的设计对策、以及**强制机制**(哪个测试/哪段代码保证它不再发生)。
> 构建 loop 的合同断言直接引用本文的 P 编号;一条 P 没有对应的强制机制,
> 就不允许标记完成。

## P1 — 契约欠规定:worker 猜输出格式

- **事故**:v2 首次 live run,5/5 个 DocsWorker 输出 schema 非法——回显派发
  元数据(plan_id/angle/work_item_id)、自造 id(eu_id/doc_index)、类型写错
  (计数写成列表、列表写成裸字符串)。模板只描述了"做什么",从未逐键列出
  "输出长什么样"。
- **根因**:契约放在 prose 里,模型只能猜布局。
- **v3 对策**:**enumerate-the-schema 教义**。每个 worker prompt 必须:逐键
  枚举输出 JSON 的每一层、点名禁止的键、给出闭合枚举的合法取值、并附一个
  合法样例。schema 文件是唯一权威,prompt 由它对照维护。
- **强制**:漂移守卫测试——解析 prompt 文本,断言 argue.result.v3 的每个
  key、每个枚举值、每个禁键名都出现在 prompt 里;schema 加减字段时测试立即
  变红,直到 prompt 重新同步。(v2 后期补上的这类测试让重派发一次通过。)

## P2 — 文档声称,代码不做(docs-as-program 的失败)

- **事故**:docs/07 写明 retry_suffix 会自动附加——渲染代码从未接线;
  dry_run 的 docstring 声称 V-CDR-03 成立——代码从未检查(重建时证实该路径
  真实可达);docs/10 §5 的"canonical 模板文本"与实际文件字节漂移。
- **根因**:把 prose 文档当程序,却没有任何机制把 prose 绑定到代码。
- **v3 对策**:反转权威方向——**schema 与测试是法律,文档只是导读**。文档
  里任何值得强制的句子必须指向一个测试 id;没有测试的声称一律用"目前"
  措辞并标注 `[unenforced]`。
- **强制**:loop 合同规定 Evaluator 抽查文档声称 vs 测试对照;文档中出现
  `[unenforced]` 之外的规范性断言而无测试引用 → gate FAIL。

## P3 — 组件各自正确,接线是断的

- **事故**:critic 模板要求输出 wave_id,但没有任何环节把 wave_id 告诉
  critic(schema 必填 → critic 原则上不可能合法输出);compile_worker 模板
  存在但没有渲染器和 CLI 命令;expand 层与 sweep 层的顺序在两份文档里互相
  矛盾。
- **根因**:先分模块实现、后拼接;接口从没被当作一等公民设计与测试。
- **v3 对策**:**接口先行**。12 份 schema 在写任何代码之前冻结;每个接口
  必须同时存在:生产者路径 + 消费者路径 + 一个贯穿测试(producer 写出 →
  consumer 读入,断言语义)。模板占位符({question} 等)与渲染器填充集
  一一对应。
- **强制**:接线矩阵测试——枚举全部 schema id,断言每个 schema 在代码里
  至少有一个写入点和一个读取点(字符串级扫描 + 贯穿用例);模板占位符集合
  == 渲染器填充集合(双向)。

## P4 — 机器压过研究:为编排而编排

- **事故**:11 态队列 + 900s 租约 + 波次合议 + Committer/Validator 分权,
  代码与测试的大头都花在机器本身;live run 的大多数失败发生在机器层
  (队列状态、路径清单、锁竞争),而不是研究内容层;commit/queue 锁竞争
  作为已知缺陷一直 deferred。
- **根因**:在还不知道研究流程长什么样时,先造了通用编排机。
- **v3 对策**:删光。没有队列、没有租约、没有状态机引擎。并发故事只有一句
  话:**argue 任务天然不相交(独立 workdir + 独立结果文件),树与 docs 的
  一切写入由主会话经 pt 串行执行**。pt 的每个命令 ≤ 一次原子落盘意图。
- **强制**:CLI 封闭清单 ≤ 15 条命令(测试镜像双向断言);核心包代码预算
  ≤ 2500 行(测试统计,超出需在 loop 中显式升级合同);禁止出现
  status machine / lease / lock 之类的模块名(评审项)。

## P5 — 协议久久不冻结

- **事故**:v2 的 schema 在 r2/r2.1/r3/S1-S5/v2.1/v2.1.1 十几轮变更中持续
  漂移,每轮都要回补文档、fixture、模板,三处经常不同步。
- **根因**:协议演化没有版本纪律,"改一个字段"没有成本感知。
- **v3 对策**:schema 文件带 `$id` 与版本号;**项目一旦 init,该项目引用的
  schema 集合冻结**(spec 里记录 schema set hash);修改协议 = 新版本号 +
  迁移说明,旧项目不受影响。
- **强制**:`pt validate` 校验项目内每条记录的 schema 字段可解析且属于冻结
  集;schema 目录的哈希清单测试(改动任何 schema 而不 bump 版本 → 红)。

## P6 — 模型自评(maker = checker)

- **事故根源**(v2 设计层面反复出现):worker 想自己下 verdict;后期靠
  "worker 填表、代码算裁决"救回来。v3 没有裁决表了,风险回来了。
- **v3 对策**:分层判断——argue 层只报告(findings/stance/confidence),
  **论点层(主会话)判断是否充分**;观点层的 synthesis 由主会话写,但
  **compiler 阶段强制回查**(compile.thesis 必须列出每个 synthesis 引用的
  based_on 证据链,断链 → check 失败)。发散的独立性自标由抽查 critic
  监督(advisory)。
- **强制**:compile check:每个进入文章的结论都能沿
  synthesis → argue.result → sources → docs.entry → 归档文件走通;走不通的
  结论不允许出现在 outline 里。

## P7 — 幻觉三件套:编造引用、拼接引文、数字评分

- **事故**:v2 live run 抓到 worker 用 " … " 拼接两段不相邻原文当 verbatim
  quote(V-DR-05);更早版本 worker 自造引用与数值分数。
- **v3 对策**(v2 唯一值得全额继承的三件便宜货):
  1. quote 逐字校验:ingest 时与归档 text 做 whitespace-normalized 子串
     匹配,不匹配自动降级 paraphrase + 告警;
  2. content_hash 去重:同一 URL/文件两个任务重复抓,只归档一份;
  3. 引用可回溯:文章里每个 `(cite: DOC-xxxx)` 必须解析到归档条目。
- **强制**:三个都在 pt 代码路径上(ingest / compile check),各配对应
  fixture 测试(真引文过、拼接引文降级、假 DOC id 拒绝)。

## P8 — 缓存自动"视为已解决"

- **事故**:v2 早期(r2.2 修掉)matcher 命中即自动 fulfil 请求——搜索是否
  充分是判断问题,缓存无权替模型决定。
- **v3 对策**:recall 只提供材料,永不改变任何状态。记忆化发生在
  **emit 时**:`pt argue emit` 把 top-k recall 命中(文件引用)内嵌进任务包,
  小模型无需自觉、也无权跳过("必读后再搜"写进 prompt)。
- **强制**:recall 代码路径无任何写操作(测试断言 recall 前后项目文件哈希
  不变);argue prompt 漂移测试包含 recall-first 指令。

## P9 — 同一事实手工维护两份

- **事故**:paths.EMPTY_JSONL 与 verify._JSONL_FILES 两份 17 文件清单;
  docs/10 §5 与模板文件的字节双份。重建时靠事后测试拴住,但双份本身就是坑。
- **v3 对策**:**单一来源原则**——schema 只在 v3/schemas/ 存在,代码运行时
  加载它们做校验(不手写第二份 pydantic 镜像);canonical 文件清单只在
  paths 模块一处定义,验证器 import 它。
- **强制**:评审项 + 接线矩阵测试自然覆盖(第二份清单没有生产路径就活不了)。

## P10 — 文档里的行号锚点必然过期

- **事故**:重建当天,architecture.md 里的 file:line 锚点就被 fresh-reader
  查出 3 处 off-by-one(代码同日在改)。
- **v3 对策**:文档锚点用**符号名**(module.function),不用行号;需要精确
  位置的断言一律写成测试而不是 prose。
- **强制**:评审项(Evaluator 检查 v3 文档不含 `:\d+` 形式的代码锚点)。

## P11 — prompt 把模型当表格机,没有自主性

- **事故**(你亲自点名的 v2 失败):prompt 全是步骤指令,worker 没有判断
  空间;遇到 403/PDF/意外页面就死;搜索质量平庸。
- **v3 对策**:**边界严格,内部自由**。prompt 结构固定为三段:
  (1) 目标与判断责任(你要回答什么、什么算好答案、必须主动找反证);
  (2) 资源(工具、recall 命中、上下文路径、预算);
  (3) 输出契约(P1 的逐键枚举)。
  中间"怎么搜、搜几轮、信谁"完全交给模型;argue 用 Sonnet(不再用特小
  模型硬扛)。
- **强制**:prompt 评审项(三段结构);live smoke 观察项(worker 遇阻时
  是否自主改道而不是死循环)。

## P12 — 并行输出互踩

- **事故**:v2 规则"并行 worker 必须不同 task_id + 不同输出文件"执行良好,
  没出过事——这是要**保持**的约束而不是修复项。
- **v3 对策**:每个 argue 任务独占 `argue/tasks/T-xxxx/` workdir + 唯一结果
  文件;树/docs 写入全部主会话串行。
- **强制**:emit 分配 workdir 唯一性由 id 分配器保证(max+1,复用 v2 的
  ids 思路);ingest 校验结果文件路径 == 任务声明路径。

## P13 — 构建期运维坑(浪费真实工时的琐碎地雷)

- **事故**:zsh 里 `$P` 不分词(命令+参数存变量 → exit 127);macOS BSD
  grep 不支持 `\|`/`\s`(静默空结果,两次误导排查);CLI envelope 用管道
  解析时被 stderr 混流干扰。
- **v3 对策**:写进 loop 的 Hard constraints:shell 命令全字面量;文本扫描
  用 python 不用 grep 交替;envelope 解析统一 `python -c json.load`。
- **强制**:loop runbook 硬约束条目;违反导致的排查工时由 Evaluator 记录。

## P14 — 长构建被 compaction 吃掉状态

- **事故**:v2 构建横跨多次上下文压缩,靠 .loop/state/ 磁盘文件活下来;
  凡是只存在于对话里的决定都丢过。
- **v3 对策**:一切决定落盘——loop 的 progress/contract/log 照旧;v3 额外
  规定:**每个 gate 报告写明"本 gate 对应防坑清单的哪些 P 已被强制"**。
- **强制**:gate 报告模板含 P-覆盖表;Evaluator 核对。

## P15 — spec 幻想复杂度

- **事故**:v2 的 topic 文件 9 大节 + P1-P7 解析规则 + 六种 paper 模式,
  实际只用了一种模式,大半字段从未影响运行。
- **v3 对策**:spec.v3 只有 5 个字段(topic/boundary_note/budgets/language/
  schema_set)。任何新增字段必须先有消费它的代码路径。
- **强制**:接线矩阵测试覆盖 spec 字段(无读取点的字段 → 红)。

---

## 强制机制索引(loop 合同将逐条引用)

| P | 强制机制 | 形态 |
|---|---|---|
| P1 | prompt↔schema 漂移守卫 | 契约测试 |
| P2 | 文档声称→测试对照抽查 | Evaluator 评审项 |
| P3 | 接线矩阵(每 schema 有产有销)+ 贯穿测试 + 占位符双向对账 | 契约测试 |
| P4 | CLI 封闭清单镜像 + 代码行数预算 | 契约测试 |
| P5 | schema 冻结哈希清单 + pt validate | 契约测试 + 运行时 |
| P6 | compile check 证据链走通 | 运行时 + 契约测试 |
| P7 | quote 逐字 / hash 去重 / cite 回溯 | 运行时 + fixture 测试 |
| P8 | recall 零写入 + emit 内嵌命中 | 契约测试 |
| P9 | schema 单一来源(运行时加载,无镜像) | 架构约束 + 评审项 |
| P10 | 文档禁行号锚点 | 评审项 |
| P11 | prompt 三段结构 | 评审项 + live smoke |
| P12 | workdir 唯一 + 输出路径校验 | 运行时 |
| P13 | loop 硬约束(字面量命令/python 扫描) | 运维纪律 |
| P14 | gate 报告 P-覆盖表 | loop 流程 |
| P15 | spec 字段消费路径覆盖 | 契约测试 |
