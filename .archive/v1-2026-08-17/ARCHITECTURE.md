# ARCHITECTURE — DSH profile 架构与模块分拆

> 上位约束：[PRINCIPLES.md](PRINCIPLES.md)。本文所有 DSH 机制描述的证据基线是仓库根四份
> 架构分析文档 + 本机活例（`~/.dsh/profiles/`、`serper-harvester/`、`plugin-creator/`）。

## 1. 总体形态：最小插件面 + 文件契约 + preset 逻辑

核心张力：DSH 是"一切皆插件"的运行时，而 P-1 禁止造框架。解法：

- **插件只写在 DSH 接缝强制要求处**：搜索 provider、学术 API 工具、预算/审计 waterfall
  钩子。插件面越小越好。
- **研究逻辑本体不进插件**：活在 agent preset（人格/章程）+ markdown 技能（方法论纪律，
  即消融证明的最大质量杠杆）+ workflow 脚本（并行编排）+ 确定性门脚本（Python/Node，
  零模型零网络零时钟）里。
- **状态活在文件与会话事件里**：claim 台账是 TSV，证据是内容寻址文件，
  审计轨是 session JSONL——不建数据库、不建队列、不建图。

这与本仓库两条已验证流水线（plugin-creator、serper-harvester）的形态一致
[E: house-method 深读]，也与 Paper Graph 重置后"极小控制面"一致 [E: PG/DESIGN.md]。

## 2. Profile 组成

```
~/.dsh/profiles/academic-research/
  package.json          # dsh.profile.bundles（有序）+ dependencies（file:/tgz 本地包）
  cordis.patch.yml      # profile 层 patch：模型路由、并发、预算、persona 挂载
  cordis.yml            # 启动时重写的空根（机制固定）
```

```jsonc
// package.json 骨架（形态照抄本机活例 harvest-test/headless）
{
  "name": "dsh-profile-academic-research",
  "private": true,
  "dependencies": {
    "dsh-web-search-serper": "file:...",          // 已有，通用兜底搜索
    "dsh-academic-search": "file:..."             // M1 新建
  },
  "dsh": { "profile": { "bundles": [
    "@deepseek-ai/dsh-base",
    "@deepseek-ai/dsh-headless",                  // P-16：TUI 一等，不用 web-app
    "dsh-web-search-serper",
    "dsh-academic-search"
  ]}}
}
```

要点（全部来自实测机制）：

- headless 形态：`dsh --profile academic-research "<task>"`，exit code 按
  turn/end reason==='completed'——回归测试与批跑的外壳 [E: DSH-架构分析.md headless 章]。
- patch 语义：id 定向 patch 整体替换 config（无深合并）、insert 插新行、
  `!!js` 挂载期求值、`disabled: true` 而非删行 [E: DSH-架构分析.md §2.2]。
- 研究角色的差异化模型：preset 层 agentOptions {provider, model, maxTokens} 可按
  子代理任务覆写——检索 worker 用便宜模型、验证/裁决用强模型 [E: dsh-tool-subagent README]。

## 3. 模块分拆（8 个模块，每个可独立验收）

### M1 `dsh-academic-search` — 学术检索插件（唯一的重插件）

- **为什么必须是插件**：DSH web 缝的现实约束——WebSearchRequest 只有 query+maxResults
  （无时间/域名过滤）、web_fetch 无 PDF 臂、body 上限 10 万字符
  [E: dsh-web/dsh-tool-web README]。学术 API（Semantic Scholar / OpenAlex / Crossref /
  arXiv / Europe PMC…，优先级与配额策略依 SURVEY.md §学术 API 维度）做成**自有模型工具**
  直接走 ctx.tools 注册，不硬塞 WebSearchProvider。
- **检索即取证**：每次检索/抓取在返回结果的同一执行里把原文快照落盘
  （内容寻址，见 M2）并写 log-only 请求事件（照抄 web/deepseek-search-llm-request
  的"请求体落日志"模式 [E: dsh-web-search-deepseek README]）——证据物化在产生瞬间（P-12）。
- 结构照抄 serper-harvester：纯逻辑 lib/（零 @deepseek-ai import，可脱离 dsh 单测）+
  接线层 lib/index.js + `export const Config = z.object(...)`（cordis 加载期不变式，
  缺了 boot 即崩 [E: plugin-creator targets/plugin/BUILD.md 硬规则]）。
- **检索栈三层主干**（依据 SURVEY §5/§12；provider 全部做成可插拔 adapter +
  健康探测 + 降级路由，用 re-runnable gate 定期验证限速与字段契约——生态一年内
  OpenAlex 转收费/Crossref 改限速/S2 收紧，不硬编码任何单一 API 行为）：
  1. 元数据/发现：OpenAlex（API key + credit 预算集中管理，每日免费 10 万 credits）
     + Crossref polite pool（DOI 权威仲裁，mailto 即 10 req/s 免费）；
  2. 领域深化：arXiv、Europe PMC（JATS XML）、Semantic Scholar（1 RPS 只做
     引文语境/嵌入补充）；
  3. 兜底发现：CORE + serper /scholar（结果必须归一化回 DOI 才准入证据库）。
- **通用 web 层**：serper（主搜 + /scholar + scrape 三用）+ Jina Reader（主抓取，
  5 分钟缓存天然去重）为廉价主链（>90% 流量）；Exa `category=publication`
  语义检索做学术补充（10 QPS 集中旁路）；Brave 独立索引做交叉验证信号；
  Firecrawl 做 JS 重渲染降级位；中文走 bocha。降级链：搜索
  serper→Brave→Tavily；抓取 Jina→Firecrawl→serper scrape。
- **全文获取 fallback 链**（XML 优先于 PDF，每级产出记录来源级别）：
  arXiv/EuropePMC 原生 XML → OpenAlex content TEI（100 credits/篇）→
  OA PDF（Unpaywall 位置）→ CORE 副本 → 用户配置的出版商 TDM key →
  预印本替代版（标注版本差异）→ 仅摘要。"仅预印本/仅摘要"是显式证据等级。
- **抽取层双轨**：GROBID（CPU、~120 页/秒）做 100% 论文骨架抽取（题录/章节/
  引文/段落定位），MinerU 按需处理公式/表格重的页面（保留版式框坐标，
  否则"可验证摘录"退化为"可搜索文本"）；避开 marker（许可竞业条款）。
- **信号解析器多方言**：robots.txt 经典语法 + Cloudflare Content-Signal +
  IETF AIPREF 词表 + RSL，归一化为 {crawl, store, ai-input, ai-train,
  redistribute} 五元许可位（快照分级联动见 EVIDENCE-ENGINE §3b）。
- 集中式 API gateway 单例与 per-provider 并发闸门归 ORCHESTRATION §6b。

### M2 `evidence-store` — 证据库（文件契约，不是插件）

- 目录契约（单一 run 内；列契约与写权以 EVIDENCE-ENGINE 为唯一权威）：
  ```
  runs/<slug>/
    claims.tsv          # 台账（kind: data|source|inference；status 列唯一写者=门）
    manifests/<cid>.json# 每 claim 溯源 manifest（EVIDENCE-ENGINE §1/§3）
    verdicts/<cid>-*.json# agent 复核裁决工件（门的输入，EVIDENCE-ENGINE §2）
    evidence/objects/   # CAS 快照（工具执行器抓取时直写 + 事件记 hash）
    transforms/<cid>.py # data 类：确定性无网络变换 → metrics/<cid>.json
    sources/<cid>.txt   # source 类：门侧抽取缓存（校验基底是 CAS 快照）
    inferences/<cid>.md # inference 类：premises/warrant/steps/conclusion/scope
    incoming/           # worker 唯一可写暂存区（拟议行与工件，不含快照字节）
  ```
- **三层入库结构**（P-6，照搬 serper-harvester）：worker 只写 incoming/（拟议行/
  工件，不含快照字节）→ 确定性 admission 脚本（无模型/无网络/无时钟）裁决入库 →
  反伪造门在 session jsonl 层断言每条 URL/引文逐字来自工具 RESULT 事件。
- **写面所有权（对齐 EVIDENCE §2 / ORCH §3，A7 fix-audit 消除三写者矛盾）**：
  证据快照由检索/抓取工具执行器直写 CAS（内容哈希键名天然无冲突，P-11）；
  claims.tsv **新行由 admission 写、status 列唯一写者是门脚本**；
  **orchestrator/conductor 永不物理写台账**（它只派发与读聚合视图）。

### M3 `gates` — 确定性验证门（脚本集）

- 三通道验证（对应 kind 三分，细节归 EVIDENCE-ENGINE.md；**注意：已放弃 DVC，
  采用 per-claim manifest + CAS**，决策依据见 EVIDENCE-ENGINE §3a）：
  data → manifest 驱动的强制重执行四层门（执行成功/输入依赖/数值/单位）；
  source → 快照字节锚定 + 逐字子串校验 + 书目存在性 + 源完整性；
  inference → 前提 DAG + 独立复核（含 conclusion 强度检查）。
- **门分级词汇**（修"确定性"定义漂移）：Class-0 离线确定性（admission、引语
  匹配、DAG 检查——无模型无网络无时钟）；Class-1 联网确定性（书目 API 比对、
  撤稿 join、URL 健康——确定性算法但依赖网络快照，结果带时间戳缓存）；
  Class-2 裁决输入型（LLM 裁决工件 + 门代码校验）。各文档提到"确定性门"时
  以此分级为准。
- 硬化三原则进代码：fail-closed（MISSING==FAIL）、新鲜度绑定（执行 id + 输入 hash
  进 metric 文件并校验）、阈值检查方固定（P-5、P-9）。
- **源完整性门组**（EVIDENCE-ENGINE §3b 第 3-4 级的实现载体）：L0 确定性免费层
  （本地 Retraction Watch CSV 每日 git pull + O(1) join；劫持期刊名单；DOAJ
  白名单信号；tortured-phrases 正则）默认开启不可关；L1 纯代码统计取证
  （GRIM/GRIMMER/DEBIT、statcheck 复算，三值输出 + 适用域守卫）；
  L2 外部概率层（Argos/Papermill Alarm API）可选插槽，只降权不否决。
  所有门结果记录 gate 版本 + 数据快照日期（RW CSV 的 git commit），可重放验证。
- 每个门自带：黄金自测 run（runs/_smoke 模式）+ 每条规则的反向 fixture +
  对真实外部工件的校准。

### M4 `research-preset` — 研究编排 preset（逻辑本体）

- agent preset 目录（agent.cordis.yml：conductor 章程 persona complete:true +
  includeRuntimeContext:false，照抄 plugcreator 形态）+ vendor/roles/ 角色包
  （cartographer / advocate / adversary / grounder / verifier / auditor——bounded prompt
  继承 Paper Graph 全部角色文本资产 [E: PG/WORKFLOW.md]）+ workflows/*.workflow.js
  （并行扇出脚本，逐字节保真纪律）+ skills/（方法论技能：发散纪律、
  取证纪律、诚实报告纪律——思维纪律是最大质量杠杆，P-1）。
- 多 loop 编排细节归 ORCHESTRATION.md；长循环用 goal + goal-round-driver（P-13）。

### M5 `eval` — held-out 评测轨（独立目录、独立 CHANGELOG）

- Isolation Contract 逐字继承（P-7）；answer key 从真实文献独立派生、
  评审对作者脚手架盲；对抗性程序为主（P-8）。
- 聚合器采 validate_eval_bundle.py 的 fail-closed 模式为唯一可执行权威
  （必需文件全集、集合相等、逐字段校验），不许契约分叉 [E: pg-code 深读]。
- 评审 agent 的输入输出留档为一等工件（前代面板 JSON 是手工聚合、独立性不可审计
  的教训 [E: pg-code risks]）。

### M6 `attack` — 攻击电池（复用 house 协议）

- 种子校验 + 五透镜（映射为学术域：一致性/可作弊性/引用实证/可复现性/前提审计）+
  跨厂商攻击者 + PROVE-OR-FLAG + 根因裁决 → 结构性重设计；ledger 形态照抄
  mp-automator/.attack/r1-ledger.md。规划期与交付里程碑都要过（P-17）。

### M7 `prose-exit` — 论文出口（刻意薄）

- 从台账 + 证据体装配散文；每个实证句引用 claim_id；出口不得引入台账外断言
  （出口自身有一条确定性检查：散文中的实证句 ⊆ 台账）。不做排版/投稿工具链。

### M8 `bench` — 回归与实测外壳

- headless 批跑（`dsh --profile academic-research "<topic task>"` + exit code）+
  append-only scoreboard.tsv（行永不删除）+ 跨领域论文级实测集与 A/B 协议
  （细节归 TESTING.md；A/B 前置为里程碑，P-15）。

## 4. 模块依赖与开发顺序

```
M2 evidence-store 契约 + M3 gates（含负向测试）   ← 第一优先：契约先行+先红后绿
  → M1 dsh-academic-search（检索即取证）
  → M4 research-preset（最小单 loop 跑通）
  → M8 bench 首个 A/B（gated vs freehand，honest test 前置）   ← 里程碑 1
  → M5 eval 轨收敛 → M4 扩展多 loop 超并行 → M6 攻击轮 → M7 prose 出口
```

依据：P-15（A/B 前置）、P-3/P5（契约冻结先行）、pg-code 教训
（打包早于收敛导致契约分叉——skill 化/发布一律放最后）。

## 5. 能力映射表：外部调研结论 → DSH 原语（三档判定）

> 完整性批评者指出"外部结论默认 DSH 能实现"是规划风险。逐条判定：
> **原生** = harness 已提供；**profile 层** = 本项目在 profile/插件/脚本层实现；
> **harness 改造** = 需要改 DSH 本体（尽量避免）。

| 外部调研得出的需求 | 判定 | 依据（本地深读） |
|---|---|---|
| supervisor 显式停止 + 迭代硬上限 | **原生** | goal round 上限 256 可配 + blocked/complete 语义 |
| 受控并行 fan-out | **原生** | workflow parallel/pipeline + 滚动池 10 + maxDepth |
| 每轮重建精简 workspace（IterResearch 式） | **原生** | ralph 模式 fresh child + inheritsParentContext:false |
| 暂停等待人类输入（HITL） | **原生** | goal pause/resume；人类消息自动让路且不耗轮配额 |
| 异常 subagent 取消/重试/兜底 | **原生** | settlement 无条件通知 + agent() 失败→null + 崩溃 closers |
| 多模型分层（检索便宜/裁决强档） | **原生** | tool-subagent agentOptions {provider, model} per 实例 |
| 反伪造审计轨 | **原生** | JSONL 持久化 + chunk-rows 无损 codec + sourceEventSeqs |
| per-subagent findings 压缩返回 | **profile 层** | 角色包 prompt + structured_output 工具（机制原生，纪律自建） |
| 学术 API 集中限速/共享缓存 | **profile 层** | M1 插件内宿主平面单例服务（DSH 服务模式支持） |
| 成本预算硬顶 | **profile 层** | agent/pre-step waterfall gate 自建；tokenMeter 投影原生 |
| "所有 claim 达标"停止条件 | **profile 层** | conductor 读台账后显式 goal complete/blocked |
| 检索即取证（快照+log-only 事件） | **profile 层** | M1 工具执行内落盘（照 deepseek-search 请求落日志模式） |
| PDF 抓取/解析 | **profile 层** | web seam 无 pdf 臂 → M1 自建工具绕开 seam，不改 harness |
| 语义检索供应商（Exa 类） | **profile 层** | 新 provider 或工具（serper provider 先例） |
| 并行写去重 | **profile 层** | content-addressed 文件 + admission 脚本 |
| 多模态图表抽取（跨厂商双模型） | **profile 层** | pi-ai 多 provider 字典路由（本机已验证 kimi vision 路由 [E: mp-automator R4]）；仅单视觉源可用时 machine-extracted 不得升级为"跨厂商双模型一致"锚点（诚实降级，EVIDENCE §3d 阶梯，无 cross-checked 独立态） |

**结论：全部需求落在原生/profile 层，零 harness 改造**——唯一逼近改造的是
WebSearchRequest 词汇不足（无时间/域名过滤、无 PDF），解法是绕开 seam 用自有工具（M1 已定）。

## 6. 运行时约束清单（规划期就要认账的硬事实）

| 约束 | 出处 | 设计应对 |
|---|---|---|
| compaction 裁剪工具结果（8192 字符） | dsh-agent-core | 证据落盘在产生瞬间（M1/M2） |
| goal armed 不持久化 | dsh-harness-code-archaeology | 重启续跑是显式编排步骤（ORCHESTRATION） |
| 子代理 approval 固定 never | 同上 | headless 下父层预放权 + 门管质量 |
| 沙箱不拦网络 | dsh-security-execution | 溯源靠反伪造门而非网络管制；敏感数据不进 run |
| 无美元预算硬顶 | dsh-execution 深读 | 预算 gate 自建 + 余额护栏（P-14） |
| maxDepth 默认 3 | dsh-tool-subagent | loop 嵌套深度进设计预算，需更深显式配置 |
| 中文 token 启发式计价误差 | dsh-execution 深读（推断） | 预算护栏留余量 |
