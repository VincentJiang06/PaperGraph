# Nodify 迭代路线图(2026-07-09,基于实测 #1/#2 证据)

> 每项都注明证据来源(docs/05、docs/06 或代码复核)。执行纪律见
> docs/08-test-cases.md 的 Opus 操作守则。优先级 = 价值/成本综合。

## R1 — P2 修复:final.md 陈旧性检查(小,立即)

**证据**:docs/04 §4 声称"assemble 后 final.md 与 records 不一致 = 硬错误",
代码从未实现(已在文档标注 [unenforced])。这正是 v2 时代 retry_suffix /
V-CDR-03 一类的"文档声称、代码不做"。
**做法**:check 在 final.md 存在时,比对其 cite 集合与最新大纲+已注册节的
应有集合;不一致 → hard,错误信息提示重跑 assemble。测试:改注册节后不重
assemble → check 红。验收:TC-H。

## R2 — recall 质量(中,高价值)

**证据**(实测 #2 G4):三个不同查询都返回全部 8 篇、全 global 距离,agent
被迫逐篇读 summary 自行判断——recall 目前只是"库里有没有"的检查器,不是
排序器。
**做法**(保持确定性,语义排序不在本项):
a) 词法打分改为 title+summary+**归档全文**(全文命中权重低于标题/摘要);
b) binding note 纳入打分文本;
c) hits.why 带命中词样本,零命中的条目在 k 内也要标注 "no token match";
d) 建立可量化基准:TC-F(种子库 12 篇 + 15 条带标准答案的查询,
   报告 recall@3)。先测出基线,再改代码,改后必须不劣化。

## R3 — `nd docs bind`(小,顺手)

**证据**(实测 #2):给已归档条目加绑定要靠"重 ingest 同文触发去重合并"
——能用,但是绕路,而且要求手头还留着原文件。
**做法**:`nd docs bind DOC-xxxx --node N --relation supports [--note …]`,
语义与去重合并一致(追加 latest 条目);闭表 20→21,先改 docs/03 再改镜像。

## R4 — 规模行为(中)

**证据**:两轮实测树都 ≤10 节点、深度 ≤3;TREE MAP 新增后,50+ 节点会话的
brief 装箱、check 遍历、TREE MAP 截断行为全部未知。brief 的优先级装箱理论
上成立,但 TREE MAP 排在 STUCK 后,大树下会挤掉 DISCIPLINE WARNINGS——
是否该让 TREE MAP 在超预算时先折叠为"仅前沿+祖先链"?
**做法**:TC-B 先压测取证,再定折叠策略;不要先写代码。

## R5 — retire 卫生(小)

**证据**(代码复核):retire/close 一个 viewpoint 后,其子树的 active 工作
(pending/investigating claim、open viewpoint)原样悬空,check 不报。
**做法**:check soft += "active 节点挂在 retired/closed 祖先下";是否自动
级联留给模型判断(框架不做级联,P4)。验收:TC-D。

## R6 — 节点 statement 修订(中)

**证据**:node.v1 的 `revises` 字段两轮实测零使用——语义(修订后子树/绑定
/synthesis 是否延续)从未定义,属于"schema 有字段、协议无语义"的隐患。
**做法**:先在 docs/00 写清语义(建议:revises 生成新 node_id、旧节点自动
retired(note 指向新id)、绑定与子节点**不**自动迁移、check soft 提示未迁移
项),CLI `nd revise N --statement …`?或裁定砍掉该字段(schema set v4)。
先决策后动手。验收:TC-D。

## R7 — 成本可见性(小)

**证据**(实测 #1 自审):工人聚合抓取 ~25 次 vs 预算口径 8-12;框架对
subagent 成本零感知,预算只活在 prompt 里。
**做法**:不做强制(P4);brief 的 SESSION 行加 events 计数摘要
(ingest N 次 / conclude N 次),技能层把"抓取预算属于整场调查的聚合值"
写明。验收:TC-G(纪律观察项)。

## R8 — 英文会话 + 长度语义(小)

**证据**:两轮全 zh;session.language=en 路径、en 下的字数/长度纪律未验证。
**做法**:TC-A 用 en 跑一遍基线;发现的文案/分词问题按摩擦日志流程处置。

## R9 — 对抗完整性(中,信心项)

**证据**:两轮都是善意 agent;防线(quote 逐字、cite 回溯、schema 拒收)
从未被故意攻击过。v2 的教训是防线要用敌意用例钉死。
**做法**:TC-J——指示 agent 故意:编造引文、引用未归档 DOC id、evidence
全空的结论、绕过 nd 直写 JSONL 后跑 check。全部应被拒/被抓。

## R10 — 语义召回(大,V4 候选,最后)

R2 的词法上限到了再启动;可选依赖、loud degrade(v2 的 S5 教训整套平移)。

## 明确不做

队列/编排机回潮、跨 session 共享库、自动级联删除、WebUI。
