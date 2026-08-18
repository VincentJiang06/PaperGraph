# EVIDENCE-ENGINE — 证据引擎设计 v2

> 上位约束：[PRINCIPLES.md](PRINCIPLES.md)（尤其 P-4~P-6、P-9、P-10、P-19、P-20）。
> 本文是 claim 台账、验证通道、反伪造门的**最窄契约权威**。
> v2 变更：吸收两轮外部调研（SURVEY.md §4/§5/§7/§8 与 §12 全部补查维度）；
> 放弃 DVC 依赖改为 per-claim manifest + CAS（§3a 记录决策依据）。

## 1. 工件分层：台账极简，manifest 承重

- **`claims.tsv`**（8 列，故意极简，P-15）：
  ```
  claim_id  kind  claim_text  value  raw_ref  method_ref  status  flags
  ```
  列语义与消费方同 v1（kind ∈ data|source|inference；status 只有门可写；value 对
  source 类是逐字引文、对 data 类是 `数字 单位` 两段、对 inference 类是结论句）。
- **每 claim 一个 JSON manifest**（`manifests/<cid>.json`）——承载全部溯源元数据，
  自包含、无全局 DAG、天然并行安全（外部证据：重型 provenance 框架
  PROV-O/OpenLineage/DVC 全局 DAG 均不适合 agent 内部工作格式；正确模式 =
  DataLad 式自包含 run record + dvc.lock 式内容哈希 + Hypothesis 式引文锚定）。
- **CAS 对象库** `evidence/objects/<sha256[0:2]>/<sha256>`：所有不可变证据对象
  （网页快照、提取文本、PDF、数据文件、transform 输出）。哈希即地址即完整性证明。
  大对象 .gitignore + 独立备份；manifest 与台账进 git——git 的 Merkle 历史就是
  免费哈希链审计日志（威胁模型是 agent 出错而非恶意内部人，不自建透明日志）。

### 数值 claim 的口径三元组（P-20）

value 为数字的 claim，manifest 必须携带 `metric_frame: {指标名, 样本/口径, 对比对象}`；
verify 不是核对"数字是否在来源出现"，而是核对三元组。依据：本项目自己的载荷数字
核验 pass 中 3/9 失真全部是"数字真实但口径被换"（precision 说成 accuracy 对比、
引语一致率说成重跑一致率、合同额说成退款额）。SOTA/"最佳"类 claim 强制携带
时点戳，过期自动加 `dated` flag。

## 2. 状态机 v2

```
（初始）pending
  ├─ data 门三层通过                    → verified-by-data
  ├─ source 门通过（含源完整性）        → verified-by-source
  ├─ inference 门+独立复核通过          → logically-derived
  ├─ 任一门 FAIL / MISSING              → unverified（留在台账，禁止静默删除）
  ├─ 反证环命中实质反驳（stance 对垒）  → contested（双呈现，一等公民态）
  ├─ 源完整性信号命中（撤稿/污染）      → source-contested（降级复核）
  └─ 所引 work 出现新版本               → stale（待复核，绝不静默升级引用）
```

（词汇统一：全文档集一律用 `contested`，不用 disputed——本节是状态枚举唯一权威。）

- **状态置位机制（写权唯一）**：status 列的唯一物理写者是门脚本。admission 写入
  新行时 status 恒为 pending；conductor/worker 永不直接改台账 status。agent 复核
  （RESCUE、inference 有效性、蕴含裁决）的产出是**签名裁决工件**
  （`verdicts/<cid>-<gate>.json`：reviewer_agent_id、verdict、反例构造记录、时间戳），
  门代码校验：工件存在 + reviewer ≠ producer（见下"身份绑 harness 权威"）+
  反例记录非空，然后才写状态。任何字段缺失 = MISSING = FAIL（P-9）。这使 P-19 的
  "置位由确定性代码执行"与 P-5 的"agent 复核权威"相容：LLM 判断是门的输入工件，
  永远不是门本身。
- **身份绑 harness 权威（A7 fix-audit：不绑自报字段）**：reviewer/producer 的
  身份**不取 manifest 里的自报 writer_agent_id 字符串**，而由门从 session 事件
  日志读取该 claim 的产出 agent 与该裁决工件的产出 agent 的 **harness childId**
  （randomUUID，DSH 子代理树 listChildren/listDescendants 可解析，
  delegationDepth 权威单调 [E: dsh-harness-code-archaeology childId + DSH-架构分析 委托]）。
  manifest 的自报字段仅作交叉核验，冲突以 harness 事件为准。跨厂商为强要求
  （不是"优先"）：验证子代理的 provider 由 preset 强制不同于产出子代理。
- **解读/综合类断言状态上限（接线到状态机，A7 fix-audit RT-8 半修补齐）**：
  kind=inference 且性质为解读综合（scope 声明）的 claim、以及**任何被独立难度
  分类器标为 high-difficulty/contested 的 claim**，在本状态机内**硬顶为
  logically-derived / contested，§3 的 source/data 确定性门也不得把它们升到
  verified-***——难度分类是门的前置判据，写死在 §2 而非只在 TESTING §6b。
  无专家复核时该顶不可突破（TESTING §6b 与本条是同一条规则的两处引用）。
  外部佐证：Kosmos 综合类语句准确率 57.9% 远低于其总体 79.4% [E: SURVEY §2]。
- **级联不变量**：任一前提 claim 被降级，全部依赖它的 inference claim 自动降级
  （evidence-methodology 维度：GRADE indirectness 的机器化）。
- **contested 是一等公民不是失败态**：矛盾用 SciFact 关系对模型表达——stance
  （supports/refutes/mixed/nei + rationale 定位符）挂在 (claim, evidence) 关系上而非
  claim 本体；区分两类矛盾：(a) 时间性过时 → supersedes 链 + 失效不删除；
  (b) 真实学术分歧 → 双呈现并各带引用，裁决逻辑机算（效应方向、幅度、CI 重叠、
  最小证据数门槛——GRADE guidance 36：方向相反本身不构成矛盾）。
- **置信度机算不 LLM 打分**：IPCC 双轴查表（证据量 × 方向一致率），
  只有 verified-by-data 允许数值概率语言（IPCC likelihood 规则的机器化）。
- SCREEN + 权威两层协调保持 v1 设计（机械筛 provisional → 新鲜 agent 复核终态）。

## 3. 三通道验证机制

### 3a. data 通道（可重跑数据分析）

**【决策】放弃 DVC，改 per-claim manifest**。依据：(i) 全局 dvc.yaml 是单一写面，
与超并行取证直接冲突（P-11）；(ii) 两轮调研一致：agent 内部只抄三个机制——
自包含 run record、内容哈希决定重跑、引文锚定；(iii) 前代 DVC 集成的真实价值
（md5 双溯源 + 强制重跑）manifest 完全保留，而其 fail-open 洞（exit 只看 metrics）
在新形态下结构性消失。

- manifest：`{claim_id, cmd, code_hash, input_hashes[]（指向 CAS）, params,
  env_pin（python 版本+依赖锁哈希）, expected: {value, tolerance, unit},
  exec_id, status}`。transform 用纯 python 脚本（notebook 仅作可选渲染层）。
- **容差与单位标准由检查方固定**（P-5，堵"作者自报 tolerance"洞）：门配置持有
  按 claim 类型的容差策略上限（默认相对 1%，计数类 0）；manifest 声明的 tolerance
  只能**收窄**不能放宽，超出策略上限 = FAIL。
- **门四层结构**（依据 DABStep/DSAgentBench 失败模式 + R1 攻击 RT-3）：
  1. 执行成功性门：exit code=0、产物非空、无异常栈；
  2. **输入依赖门**（堵常数脚本洗白，含 ε-依赖变体，A7 fix-audit）：静态检查
     transform 引用了 raw_ref 输入路径 + 反事实探针——门以**多组不同幅度**扰动/
     置换输入重跑，输出变化必须与输入扰动**成比例且量级相当**（不是"仅改变即可"：
     `output += 1e-9*mean(input)` 型 ε-依赖脚本会改变但幅度不成比例，在此 FAIL）；
     常数脚本（输出与输入统计量无相关）直接 FAIL；
  3. 数值门：检查方容差 + 字符串模糊匹配 + 列表归一化（照 DABStep 官方评测器，
     拒绝精确 diff——NBTest/nbval 教训：字符串 diff 对格式波动假红）；
  4. 单位/量纲门：比对前强制单位归一化声明（百分比 vs 小数、百万 vs 十亿）。
- 重跑语义：输入哈希未变可跳过（dvc.lock 语义），门提供 `--full` 强制全量；
  **新鲜度绑定**保持 v1（exec_id + input hash 匹配本次门执行，陈旧产物即 FAIL）。
- 验证循环内置 verify-refine（DS-STAR 模式，上限 10 轮）而非单次执行贴标签。
- **v1 范围决策**：仅支持"用户提供/已下载数据"的重跑验证；agent 自主取数分析
  推迟 v2。决定性依据是可靠性而非成本：封闭式已就位数据任务落在可靠区间
  （~79-90%），自主端到端落在不可靠区间（25-56.7%，取数环节仅 47.8%）。
  v2 开放时走 API 白名单（World Bank > FRED > OECD>Kaggle）+ 全局速率协调。
- 执行层：本地 bash + OS 级进程沙箱（Anthropic sandbox-runtime 同款机制被官方
  定位为无人值守合格隔离；跑论文附带第三方仓库代码才需升级 VM——写明为 v2 触发条件）。
- **标签诚实性**：verified-by-data 语义 = "在声明的分析决策下机械可复现"，不背书
  分析决策的科学正确性；门要求输出可审计的分析决策元数据（变量选择、检验方法、
  排除标准），两者区分写进状态语义。

### 3b. source 通道（他文引证）

**引用只能来自检索 artifact，凭记忆写引用在 schema 上不可能**（CiteME 铁证：
裸模型找引用 4-19% 准确；OpenScholar 证明该架构约束比模型规模更决定引用忠实度）。

manifest：`{claim_id, url, retrieved_at, snapshot_hash, extracted_text_hash,
quote: {exact, prefix32, suffix32}（W3C TextQuoteSelector）, locator（页/节）,
wayback_url?, channel（publisher-API|OA-repo|public-web|user-upload）,
license, signals_snapshot（robots/Content-Signal/RSL 当时值）, snapshot_tier,
work_key, source_version, version_anchor, vor_doi?, retraction_status,
venue_status, forensic_flags, stance_links[]}`

验证阶梯（按确定性递减，每级独立记录）：

0. **快照字节锚定**（堵"真实抓取+伪造提取文本"绕过，R1 攻击 RT-4）：
   快照字节由检索/抓取**工具执行器在抓取执行内直接写入 CAS**，并在 log-only
   工具事件中记录响应内容 sha256（M1 契约）；证据快照**不经过** incoming/。
   反伪造门断言 manifest.snapshot_hash == 该工具事件记录的 hash。
   引语匹配的基底是**门侧对 CAS 快照的确定性抽取**（抽取器与版本 pin 在门配置），
   不信任 worker 自报的提取文本——worker 的 extracted_text 仅作加速缓存。
1. **逐字引语命中冻结快照**（纯确定性，不联网不依赖 LLM）：重算快照 sha256 →
   在门侧抽取文本中精确子串匹配 quote.exact（前后缀消歧）。**此门证明 provenance
   不证明 truth**——诚实表述写死在文档与产品呈现里（P-19）。
2. **书目存在性 + 元数据比对**（Class-1 联网确定性）：Crossref/OpenAlex/S2
   并行查，九字段比对；不存在/作者重合过低/DOI 解析到他文 → FAIL。拦截伪造
   引用（无防护幻觉引用率量级见 SURVEY §4，口径注意 R1 攻击对"11-57%"的
   更正），成本近零。索引主键用 DOI/arXiv-ID（防命名碰撞）。
2b. **快照-work 身份绑定**（堵"真 DOI + 二手转述"，R1 攻击 MC-7）：门校验
   快照来源 URL ∈ 该 DOI/arXiv-ID 的注册解析位置集（Crossref/OpenAlex
   resolved locations、arXiv canonical、出版社域），或快照内元数据
   （标题/一作）与 registry 记录匹配；两者皆否 → 该快照不能充当此 work 的
   verified 锚点，只能作 `secondhand` 转引证据。manifest 增加
   `preprint_age_days`（预印本年龄，A6 建议：长期未过评审的预印本权重随
   时间衰减，供 eval 与呈现层消费）。
3. **源完整性 L0**（确定性、免费、默认开启不可关）：本地 Retraction Watch CSV
   （每日 git pull）O(1) join 撤稿状态；劫持期刊名单精确匹配（命中硬拒）；
   DOAJ 白名单缺席只降权不判黑（非对称原则）；tortured-phrases 词典正则
   （harvest 与 synthesis 双阶段，阈值分级）。
4. **源完整性 L1**（纯代码统计取证，三值输出 impossible/consistent/n.a. +
   适用域守卫）：GRIM/GRIMMER/DEBIT、statcheck 式 p 值复算。flag 一律
   translate 为"触发人工复核"绝不自动否决（误报毁信任）。
5. **NLI 蕴含二分**（准硬门，ROC-AUC ~92.65）：只做"完全支持 vs 其他"二分，
   部分支持一律打回改写——不让门做它做不好的细分类。
6. **在线复核**（非致命）：重抓 raw_ref + Wayback SPN2 异步锚点（失败只记录）。

- **承重（load-bearing）的判定权不在作者**（R1 攻击 RT-1，堵"自选 bit 逃验证"）：
  默认一切 claim 承重（fail-closed）。机器判定规则：被 prose 出口引用的、
  被任何 inference 作为前提的、或出现在结论链上的 claim 恒为承重且不可撤销；
  其余 claim 的"非承重"标记只能由独立审计 agent（D4 风格、盲于作者、
  id ≠ 作者）授予并附理由工件，门校验授予者身份。`load_bearing` 与授予记录
  入 manifest；停机规则、覆盖率分母、反证选靶全部消费此机器判定值。
- **承重的 source-kind claim 要求 ≥2 个发布者独立的来源**（作用域限定，
  A7 fix-audit：本要求只针对 kind=source；data 类靠重跑门、inference 类靠前提
  DAG，各通道独立性门槛不同，不套用两来源要求）；同一上游的多次转录只计一个
  独立来源（证据谱系防伪独立印证，P-20）；来源分级硬编码
  （registry 元数据 > 出版社 > preprint 正文 > UGC；UGC 不可作唯一证据）；
  **venue 层级要求**（堵"两个低质 preprint 互证"）：承重 source claim 的独立来源中
  至少一个 ∈ {registry 收录的出版社层级}，全 preprint 组合自动加
  `preprint-only` flag 且 verified-by-source 降格为带 flag 呈现。
- **快照分级 T1/T2/T3 与降级触发**（legal-tos 维度全套）：T1 全文快照仅限
  CC 许可/TDM API 通道；T2 短摘录 ≤200 字符 + DOI 锚点 + 定位（默认层）；
  T3 仅元数据 + 内容哈希。七类降级触发（robots/Content-Signal 命中、HTTP 402、
  403/429、付费墙、影子图书馆黑名单硬拒、无许可封顶 T2、离开本地一律封顶 T2）
  硬编码进 fetcher。**verified 要求 ≥T2 锚点**；仅 T3 的引用自动标
  `unverified—source access restricted` 并如实呈现降级原因——法律约束转化为
  可见的证据质量信号而非静默丢失。
- **双视图存储**（P-19）：原始 bytes 仅供审计；规范化正文视图（剥离 HTTP 头/
  HTML 注释/JSON-LD/CSS 隐藏文本——野外测量 70% 注入藏于非渲染通道）才送 LLM；
  双视图 diff 作廉价注入信号。
- 全文获取 fallback 链与 XML 优先原则归 ARCHITECTURE M1；每级产出物记录来源
  级别，"仅预印本/仅摘要"是显式证据等级而非失败。

### 3c. inference 通道（严密逻辑推断）

`inferences/<cid>.md` 契约（v1 基础上增加 warrant）：

```
premises: c3, c7, c12      # 全部是台账内 claim_id
warrant: <grounds→claim 的许可理由（Toulmin），一段>
steps:  1. <每步引用其前提>  2. ...
conclusion: <与台账一致>
scope: <边界条件/敏感性>
```

- **确定性部分**（门脚本）：前提存在且 ∈ {verified-*, logically-derived}；
  DAG 无环；conclusion 一致；steps 引用 ⊆ premises；warrant 非空。
- **裁决部分**（RoB 2 三层范式：LLM 只答局部事实小题、代码算状态）：
  独立复核 agent 接收 **(premises, steps, conclusion, scope)** 全量（隔离的是
  探索推理链与作者上下文，不是结论本身——R1 攻击 RT-5：复核者看不到 conclusion
  时，"steps 各自成立但 conclusion 更强"无人把关），逐步回答"第 N 步是否从
  前提得出"，并额外回答一题："**conclusion 是否不强于 steps 所能支持的结论**
  （量词/范围/因果强度逐项比对）"；链条有效性由代码聚合；PROVE-OR-FLAG——
  复核 agent 必须给出反例构造尝试记录。复核者 id ≠ 生成者 id 由门校验（§2）。
- NLI 前提→结论蕴含作 advisory 信号，不做硬门。

### 3d. 图表/表格证据（多模态降级态，v2 新增）

**核心裁决：图表数值默认不得标 verified-by-source**（真实图表 SOTA 抽取仅
40-56%，错误是自信编造式静默错误，自一致性与准确率仅弱相关 ρ≈-0.35）。

- 三级阶梯：`source-located`（定位到图，不承诺数值）→ `machine-extracted`
  （携带模型名、方法、容差 ±5% 元数据；升级最低门槛 = **不同厂商两模型**独立
  抽取且容差内一致）→ `verified-by-source`（仅三条升级路径：① 数值以文字印在
  图上/正文/表格被 OCR 直读命中；② 图-caption-正文-表格跨模态互证；
  ③ 图族专用管线 + 已发表误差界 + 抽查）。
- 图表类型红黄绿路由表（绿：带数据标签柱/折/散点 + 干净表格数值单元；
  黄：无标签简单图双模型交叉；红：堆叠柱/密集折线/雷达/dashboard/森林图/
  KM 曲线 → 专用工具或人工）。figure-family router 预留位。
- 表格"单元格数值"与"表格支持某声明"拆成两个判定（后者 2026 SOTA 仅 66-69%，
  必须走代码复算或人工）。
- 表格引用保留单元格坐标 + 页码 + 原文区域图像裁片（人工复核只看裁片）；
  人工路径设计为"机器预填 + 人核对"（90.2% 且时间减半 > 纯人工 45.8%）。
- 精度敏感场景（p 值显著性边界、CI 端点）无论图表类型一律强制人工。

## 4. admission 脚本（入库闸门）v2

v1 三态设计（accepted/skipped/rejected、无模型无网络无时钟、幂等）保持，增强：

- **串行化与时序**（R1 攻击 RT-18）：admission 每 run 单实例（文件锁互斥），
  批内按 worker 路径字典序确定性处理；并发 worker 只写各自 incoming/ 子路径，
  永不竞争；矛盾证据并存入库（stance 关系表达矛盾），不在 admission 层合并。

- **三级去重键**：L1 `work_key`（VoR DOI > 无版本 arXiv ID > 归一化标题+一作
  指纹）合并同一论文的多 URL/多版本；L2 `locator_key`（work_key+版本+文内定位）
  判同处摘录；L3 `excerpt_hash`（归一化文本 sha256）字节级精确去重。
  **禁止 URL 作主去重键**（同一论文 abs/pdf/html/DOI/S2 多 URL 全逃逸）。
- **同步门只做 L2/L3 精确匹配**；语义去重与矛盾检测全部放异步 reconciler。
  硬性红线："相近但结论不同"的摘录是矛盾证据不是重复——同步语义去重会把
  反证挡在矛盾检测器视野之外（Governed Shared Memory 顺序陷阱）。
- 双时间戳：event_time（所引版本发布时间）+ ingest_time（抓取时间）+
  writer_agent_id / task_id / tool / query 最小 provenance 集。
- 事前去重是第一道防线：orchestrator 派发时显式切分不重叠检索面
  （"X 不归你查"），事后 work_key/excerpt_hash 兜底——两层合起来才完整。

## 5. flags 词汇表 v2

v1 七项保持（point-estimate / secondhand / best-case / window-sensitive /
paywalled-unverified-online / single-source / suspicious-content），新增：

| flag | 含义 | 消费方 |
|---|---|---|
| `dated` | SOTA/最佳类断言超过时点戳有效期 | prose 出口、eval |
| `stale` | 所引 work 出现新版本待复核 | L3 验证环选靶 |
| `retracted` / `venue-hijacked` | 源完整性 L0 命中 | 状态机（source-contested/硬拒） |
| `forensic-flag` | GRIM/statcheck 类 impossible 命中 | 人工复核队列 |
| `chart-extracted` | 数值来自图表机器抽取（含容差元数据） | 状态机 3d 路由 |
| `frame-mismatch` | 口径三元组核对失败 | 状态机（不得 verified） |

## 6. 负向测试清单 v2（每条规则一个反向 fixture，P-9）

v1 十二条全部保留，新增：

13. 同一论文多 URL 重复入库 → work_key 合并（L1 去重生效）；
14. 语义相近但结论相反的摘录被同步门拒收 → 必须 accepted（红线负例）；
15. 引用已撤稿论文且无 flag → L0 门 FAIL；
16. 图表抽取数值直接标 verified-by-source → 状态机拒绝；
17. 数字口径三元组缺失/不匹配 → frame-mismatch FAIL；
18. 非渲染通道注入内容进入规范化视图 → 双视图剥离验证；
19. T3 级证据被标 verified → 状态机拒绝（快照分级联动负例）；
20. 五类注入攻击剧本（TESTING §7）全部不能翻转任何 claim 状态；
21. 常数脚本（不读输入直接输出目标值）→ 输入依赖门 FAIL（RT-3 负例）；
22. manifest tolerance 宽于检查方策略上限 → FAIL；
23. 复核裁决工件的 reviewer_id == producer_id → 门拒绝置终态；
24. worker 伪造提取文本（引语在自报文本命中但不在门侧 CAS 抽取命中）→ FAIL；
25. 快照 hash 与工具事件记录的响应 hash 不匹配 → 反伪造门 FAIL；
26. 作者对被 prose 引用的 claim 标"非承重" → 门拒绝（承重不可撤销负例）；
27. inference 的 conclusion 强于 steps 支持（构造样例）→ 复核题 4 必须抓到。

## 7. 与 DSH 运行时的接线（v1 保持 + 补充）

- 证据物化时机、抗 compaction、反伪造门读 session JSONL——同 v1（P-10/P-12）。
- 反伪造门断言范围明确化：每条 manifest 的 url 与 quote 所属快照，必须能在
  session JSONL 中找到对应检索/抓取工具的 RESULT 事件（含该 URL）；
  admission 时间戳晚于该事件。模型散文不是地面真值。
- Wayback SPN2 异步锚点走后台 continuable 子代理（不阻塞任何 loop）。
