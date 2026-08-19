# academic-research-plugin — DSH 学术证据探索 profile（v2）

> 一个全新的 DSH profile：**超并行、多 loop 的学术证据探索系统**。
> 产品是**可信度**——每条 claim 携带机器判定的状态，背书通道只有三条：
> 数据分析可重跑 / 他文引证可回溯到原文 / 逻辑推断前提可追。
> **研究是产品，散文只是渲染层。**

**当前状态：规划 + 七轮攻击（R1–R5 · S3 自攻 · R6 独立攻击）+ 产品层跑通 + 外部标定测试。**

`./gates/run_all.sh all` 当前 **31/31 全绿**，退出码判定。产品代码约 3500 行，门与外部测试另有约 6400 行：

| 层 | 模块 | 门 |
|---|---|---|
| profile | `profile/` + `packages/dsh-academic-fetch`（实测可跑：`dsh --profile academic-research`） | patch 生效值逐键比对；dump 里必须有 `tool-academic-fetch` |
| 写者契约 | `src/writer-contract.mjs` | S 读的每个字段都不能是被检查方能写的 |
| **供给侧契约** | `src/gate-ctx.mjs`（构造 ctx 的唯一入口） | 结构 4 条 + 行为 6 条反例 + 1 条绿控 |
| 归一化 | `src/normalize.mjs`（与 Python 复现脚本互为独立实现） | 双实现逐格对拍 |
| 证据引擎 | `g-polarity`（L1-c）· `g-cluster` · `g-ctr-scan`（X-2）· `g-frame` · `g-containment` | 五套两侧标定集；L1-c 另有**外部**标定集（17 句取自真实论文摘要） |
| **把关谓词** | `g-rerun` · `g-freeze` · `g-inference` · `g-attribution` | 四个谓词从 `?? true` 变成真的有门在算 |
| 存储 | `src/cas.mjs`（CAS + 证据卡 + `source_integrity`） | id 五分量敏感、断链当场拒、留存前提可检验 |
| 管线 | `src/pipeline.mjs` → `src/status.mjs`（S） | 端到端 15 条 + 5557 万向量 oracle |
| 组稿 | `src/composer.mjs`（W-10，拒裸数字） | 25 条，豁免须**自证身份** |
| 跨模块 | 全角/半角归一化 | 5 个文本比对入口 × 4 组样本，判定必须一致 |
| 编排 | `src/orchestrator.mjs` · `src/research.mjs`（并行多 loop） | 调度可复现、预算硬闸 |

**核心承诺，以及它被判过假这件事：**

> 从抓取到成稿，中间没有任何一步允许 agent 直接写结论。

这句话在 R6（第一次真正独立的攻击）被判**假**，给出三条互不相干的反例路径，
最短的一条不需要后门、不需要伪造证据、不触发任何门——而当时 22 道门全绿。
根因是所有门都站在 S 的**内部**，没有一道站在它的**供给侧**（`07-ATTACK-LEDGER.md` §S4）。

三条路径现已封死，并新建 `gates/check_supply_contract.mjs` 守着这一侧：
它有 8 条红样本，逐条把 R6 那一版的代码形态倒回去，要求门判红**且理由是它自己声称的那条**
（`gates/test_check_supply_contract.sh`）。红样本本身也被审过——其中三条初版是空心的
（被一条无关的否决救了），由负例套件抓出来。

仍然开着的，写在 §S4 四：L1-c 对**前置位之外**的改写仍是黑名单；
V1.2 已改写为条件式（留存前提成立时才成立），无条件形式与 §8.6.2.1 互斥。

`gates/check_research.mjs` 跑三条线要同一个数字 `92%`：

```
A 线（合法转录）      → 92%〔已验证，来源 1/独立簇 1〕
B 线（从否定句里取）   → 92%〔未验证，来源 1/独立簇 1〕
C 线（5 来源但同源）   → 92%〔未验证，来源 5/独立簇 1〕
```

三条线状态相同则本项目没有存在的理由——这是门的原话。

`.loop/m0/` 下有 S0 阶段的 **12 条实测记录**（6 resolved / 6 design-changed），
**26/26 条证据全部重跑且哈希一致**。`07-ATTACK-LEDGER.md` 记着七轮攻击的全部发现，
包括我自己造的空心门、我自己编造的引用、以及我自己报错的数字。

v1 规划已归档于 `.archive/v1-2026-08-17/`，本轮从零重做。

---

## 关于这个仓库（PaperGraph → 本项目）

本仓库原先装的是 **Paper Graph**：一个 claim-graph 研究框架，两代实现（nodify 2,036 行 / paperproof v2 13,949 行）。
它现在装的是它的**后继者**——一个建在 DSH 上的学术证据探索 profile。

**前代没有被删掉，它是本项目最重要的证据来源之一。**

- 前代的全部代码、消融实验、run 记录保留在 `archive/`，并在 commit `71ccea0` 里完整存档
  （含此前从未提交过的 post-reset 门控工作流，1,605 个文件）。
- `00-PREMISE.md` §B 是对前代四次消融的**重新审计**：v1 曾把「三代框架被四次消融判死」当作最高禁令，
  一手考古发现四次消融**只测了第四代**，那条"单调下降曲线"是三个不同实验的三个不同量拼的，
  最差那格的最大分项**是渲染伪影**（作者在同一文件里就说了）。
  **真正被证伪的是度量方法**，不是结构本身。该禁令因此降级为一条有界的、标明证据强度的设计偏置。
- `research/v2/gt-pg-failure.md` 与 `gt-pg-current.md` 是这次考古的完整记录。

换句话说：这个仓库从「一个被自己的消融判死的框架」变成了「对那次判决的复审 + 一个不重蹈覆辙的后继设计」。
前代的价值不在于它的代码能跑，而在于它留下了**可以被检验的失败记录**——
本项目的第一条产品主张（可信度 = 机器判定的状态）正是从那里长出来的。

**发布时会排除部分调研**：`research/v2/` 在**本仓库**是完整的 26 份。
向 public 仓库发布时，其中 5 份对第三方包（`@deepseek-ai/dsh`，npm 公开包）的实现细节逆向档案
会被排除——`gt-profile-plugin.md` / `gt-orchestration.md` / `gt-evidence-substrate.md` /
`gt-exec-security.md` / `GROUND-TRUTH-CORRECTIONS.md`。这不是保密问题（DSH 是公开包），
而是「别把别人包的逆向档案当自己仓库的内容发布」。清单由 `gates/check_publishable.mjs` 强制。

排除是有代价的：发布仓库里指向这 5 份的 `[E:]` 指针读者解析不了。
`gates/check_pointers.mjs` 把它们识别为独立的「已声明排除」状态，不与「欠债」混同；
`gates/check_doc_metrics.mjs` 对**两种仓库形态**分别校验本节的数字。

〔R3 修复〕本节此前写作「在本仓库是 21 份而非 26 份……理由写在 `research/v2/EXCLUDED.md`
（456 个指针解析不了，占 33.8%）」——**描述的是一个不存在的仓库状态**：目录里实际有 26 份、
`EXCLUDED.md` 这个文件不存在、456/33.8% 没有任何口径能得出，且同一份 README 的文档地图
同时写着「26 份调研文件」。自述数字门当时没抓住它，因为正则只匹配「N 份调研文件」的写法。

---

## 文档地图

| 文件 | 职责 | 规模 |
|---|---|---|
| [00-PREMISE.md](00-PREMISE.md) | **前提审计**——本项目押的每一条赌注，其正反证据与强度，以及会推翻它的观测 | 927 行 / 9 条赌注 |
| [01-CONTRACTS.md](01-CONTRACTS.md) | **唯一规范源**——状态模型、claim 种类、证据等级、写权矩阵、身份与独立性、门分级、flag 词表、文件契约、术语表 | 1365 行 / 68 条可检验断言 |
| [02-ARCHITECTURE.md](02-ARCHITECTURE.md) | profile 形态、模块分拆 M0–M8、DSH 能力映射、加载期门、运行时约束 | 867 行 / 27 条能力判定 |
| [03-EVIDENCE-ENGINE.md](03-EVIDENCE-ENGINE.md) | 三通道验证机制、门实现契约、反伪造接线、admission、负向测试 | 1998 行 |
| [04-ORCHESTRATION.md](04-ORCHESTRATION.md) | 拓扑、循环结构、扇出准入、停止与饱和、预算双计数器、检索资源治理、人在环 | 971 行 |
| [05-TESTING.md](05-TESTING.md) | 三层评测、指标纪律、held-out、A/B 证伪、红队、校准、eval-of-eval、人力预算 | 1289 行 |
| [06-SURVEY.md](06-SURVEY.md) | 调研摘要与**载荷数字总表**（全项目引用数字的唯一入口） | 1131 行 / 784 行核验表 |
| [07-ATTACK-LEDGER.md](07-ATTACK-LEDGER.md) | **攻击台账**——每轮的靶标指纹、种子命中率、findings 全量、裁决与修复状态 | 1764 行 / R1 收 164 条 |
| `research/v2/` | 证据基座：26 份调研文件 / 25 维度 / 11,675 行 | ~1.1 MB |
| `.loop/` | 持续迭代开发 runbook（**设计态，不自动启动**） | — |

**阅读顺序**：00 → 01 → 02 → 03/04/05。
**权威规则**：`01-CONTRACTS.md` 是所有共享词汇的唯一定义源，其他文档**只引用不复述**；
若某文档需要一个 §9 术语表里没有的词，必须挂起裁决而非自行造词。

---

## 本轮相对 v1 的五条改进（"更好"的可检验定义）

| # | 标准 | 兑现情况 |
|---|---|---|
| 1 | **地面真值取自一手来源** | 7 位 reader 直读 194 个已安装 DSH 包，产出 **50 处与二手文档的冲突**，其中 12 条改变设计（见 `research/v2/GROUND-TRUTH-CORRECTIONS.md`） |
| 2 | **数字落笔即验证** | **784 行核验表**，每个承重数字带口径三元组（指标/样本/对比）+ 状态 + 一手出处 + as-of 日期；**37 个在落笔时当场纠正**（口径：06-SURVEY §3.3「当场纠正的数字」表的数据行数；语料全库标 `corrected` 的是 50 行，两者不是同一个对象） |
| 3 | **独立性从第一轮就跨厂商** | 攻击轮进行中（见 07） |
| 4 | **v1 的已知债当场还清** | `[E:]` 指针全文强制；超并行 vs 同预算串行的 A/B 已写入 05-TESTING §T4 作为一等实验臂 |
| 5 | **完备性对照** | 攻击轮后拿 v1 的 34 条 findings 做覆盖率 diff，只许更全 |

---

## 本轮最重要的三个发现

**1. v1 的证据台账方案在 DSH 上行不通。** v1 打算把证据建成"自定义 log-only 会话事件"。
一手代码：`ignorable` 字段只读不写（194 包零写入方），这么做会产出**不可 resume 的 session**。
正确落点是 `tool/result.data.meta`——对模型不可见、抗 pruner、抗持久化、与 `tool/call` 由核心校验的 seq 天然绑定。

**2. 超并行不是质量主张。** 公开文献中**不存在任何等算力对照实验**证明扇出提升研究质量；
全部正面数据点都是并行外形下的 test-time scaling 且有混杂，而反向证据更锐（工具调用 2→150 时事实核查掉约 42pp；
某实验室三代把工具调用上限 600→400→300 而分数反升）。
本项目据此把 `hyper-parallel` **重定义为吞吐与核验密度主张**：扇出只用于覆盖率、同一断言的 N 路独立核验、
上下文卫生；**禁止**用于论证链构建、跨 claim 一致性推理、最终裁决。等预算 A/B 是本项目的核心实验，
公开文献里没有人做过。

**3. v1 最高禁令的地基被削弱。** v1 把"永不建造结构框架"当 P-1，理由是"三代框架被四次消融判死"。
一手考古：四次消融**只测了第四代**；那条"单调下降曲线"是三个不同实验的三个不同量拼的；
最差那格的最大分项**是渲染伪影**（作者在同一文件里就说了）；"纪律是最大杠杆"只在 N=1 成立，N=5 时反号。
**真正被证伪的是度量方法**——LLM 评委在 2 档有效分辨率上测不出结构增益；
而本项目的验收指标全部机械可测，这正是它们缺的那把尺子。P-1 已降级为有界的设计偏置 P-1′。

---

## 诚实声明：未偿债与阻塞项

**本项目对自己的门押注必须分层说**（00-PREMISE B8）。
**已落地的是文档层 + 状态函数层的门**：`./gates/run_all.sh everything` 当前 **8/8 全绿**，退出码判定，
其中三套负例套件在临时副本（`--root`）上走真实入口证明这些门会红；
`check_status_exhaustive.mjs` 是 `src/status.mjs` 的**穷举 oracle**——**5557 万输入向量、六值全可达、回归 8/8**，
"`S` 是全函数"由此从断言变成了实测。
**尚未落地的是证据层与运行层的门**：判据写成可核对的形式——`gates/` 下**没有任何一道门读过一件证据工件**
（`claims/*`、快照、`status.json`、台账完备性），**也没有任何一道门读过一条运行时痕迹**
（session jsonl 事件、门轨道与 producer 轨道的隔离、gate 自身完整性）。
**第一层的绿不构成对另外两层的任何证据**，它们检查的对象不相交；把前者的存在说成后者也有了，是本项目明令禁止的置信度升级。
B1–B7 里凡落在后两层的"靠门保证"，仍然建立在三条尚未落地的代码上：
gate-integrity 真脚本（且见下第 7 条，它比"写个脚本"难）、走真实入口的负例套件
（`check_doc_metrics` / `check_publishable` / `check_status_exhaustive` 三道**当前无负例套件**）、台账格式门。
在它们落地前，本规划在证据层与运行层的可信度承诺是**设计论证而非已验证性质**。

**M0 阻塞项**（实现前必须解决，不是普通测试用例）。
**S0 阶段已对全部七条做过实测**，记录在 `.loop/m0/*.json`（每条带 verdict / 复现命令 / 原始输出 sha256 / 逐字 excerpt）。
**条目一律保留、只加结论**——一条阻塞项被推翻的过程比它的答案更值钱。

1. **PDF 可见性区分** → **架构前提成立，通道分离在 PDF 路径上可实现**
   〔裁定 · S0 实测，[E: .loop/m0/M0-1.json]〕。PyMuPDF 的 `page.get_texttrace()` **逐 span** 同时给出
   color（RGB）/ size（精确到 0.1pt）/ type（`3` = Tr 3 不可见渲染模式）/ opacity / layer（OCG 名）/ seqno（内容流 z 序）；
   7 段对抗夹具中 **6 段隐藏文本全部归入 `non_rendered_text`**、1 段可见文本归入 `rendered_text`（6/6，零漏）。
   **原文那句「多数抽取库拿不到」只对 pdftotext 与 pypdf 成立**（这两者逐字吐出隐藏文本且零可见性元数据），
   pdfplumber 给颜色与字号但不给渲染模式——所以 **PDF 抽取后端是契约项，不是实现选择**。
   **两条残留**：① 良性真实论文本身就含真正不可见的文本（DeepSeek-V3 图 3 的层叠卡片挡住背后的 span，
   像素渲染差分确认 `changed_px=0`），故良性判据**不得**写成「`non_rendered_text` 为空」；
   ② 朴素阈值在真实论文上精确率仅 **12/163 = 7.4%**（BERT 图注合法使用 3.09pt 字号被误判），必须用像素渲染差分做裁决器。
   **未覆盖**：扫描件 / OCR PDF（其文本层整页都是 Tr 3，本分类器会把整份文档判进 `non_rendered_text`）、
   `/EmbeddedFiles` / `AcroForm` / `/Annots` 三条同样能携带不可见文本的通道；召回是 480 个 span 的抽样结论（漏判 0），不是全量。
2. **`quote_faithful` 的 100% 承诺缺实测** → **实测后承诺被推翻，且拦路的不是抽取管线**
   〔裁定 · S0 实测，[E: .loop/m0/M0-2.json]〕。同工具对照组（引语取自我们自己的抽取文本）**未归一化时逐字子串命中率恒为 100.0%**，
   一旦套上 01-CONTRACTS §1.2.2 的归一化就掉到 **91.7%–100.0%**；中文网页更极端——原始 100.0% / 96.7%，
   套上归一化只剩 **5.0% / 17.5%**。两条根因均已最小复现：(A)「中文专项整串去空白」按串是否含 CJK **分支**，因而非对称，
   中文文档里的纯英文引语永远不可能命中；(B) 跨行连字符还原是上下文相关重写、**不保子串**。
   改成「凡与 CJK 字符相邻的空白一律删除且不按语言分支」后，同工具组回到 99.2%–100.0%，中文网页回到 100% / 96.7%，英文全部不变。
   **残留**：即便用修正规则，**跨工具场景仍不是 100%**（英文 90.0%–100.0%、中文 96.7%–100.0%），
   残余失配来自阅读顺序、连字/私用区字形与公式；语料只有 7 份 PDF + 3 份可测网页，无扫描件、无繁体、无日文；
   "人类复制侧"用 `pdftotext -layout` 与自建 innerText 代理，**没有真的用阅读器或浏览器复制过**。
3. **三处 DSH 实测空缺** → 三条各有结论，其中两条**推翻了原文的前提**
   〔裁定 · S0 实测，[E: .loop/m0/M0-3a.json]、[E: .loop/m0/M0-3b.json]、[E: .loop/m0/M0-3c.json]〕。
   - **`inject` 服务名 = `tools`**（`ToolRuntime` 的 ctx key，不是类名）。**「猜错 = 静默 PENDING」这条前提是错的**：
     写错时 boot 逐字报 `pending (waiting for service: toolRuntime)` 并**退出 1**——是**响亮失败**，不是静默。
   - **headless 调用形式 = `dsh --profile headless "<task>"`**（task 为位置参数）；stdout 只有最终助手消息，成功时 stderr 0 字节。
     退出码的语义见下方「运行面」。
   - **workflow 两行的 entry id = `workflow-worker-thread`（引擎行，出厂 `provider: spawn`）与 `tool-workflow`（模型面工具行）**。
     **「patch 打不中只 warn 不 fail」必须精确化为：warn 只在 `--dump-config` 路径上出现；真实 boot 路径零输出、完全静默。**
     同一个临时 `DSH_HOME`、同一份写错 id 的 patch：`--dump-config` 报 **2 条** `patch: entry ... not found`，
     真实 boot 报 **0 条**（同次命令里 `dsh: AUTH` 证明 boot 确实跑到了 LLM）。
     **这决定了这件事只能靠 `--dump-config` 检测**，真实 boot 那一步再怎么 grep stderr 都抓不到。
     **不要把它与上一条混为一谈**：`inject` 服务名猜错是响亮的 exit 1，patch id 猜错才是静默。
     **残留**：`- insert:` 形式的未命中与 name mismatch 分支未实跑；web profile 未测；
     「打中 `tool-workflow` 且 `disabled: true` 后工具是否真的从模型面消失」**是推断，未跑**。
4. **`run_code` 是否可达 `node:fs`** → **已实测可达，且沙箱零约束**
   〔裁定 · S0 实测，[E: .loop/m0/M0-4.json]〕。同一台机器、同一时刻、同一条 read-only 策略下：
   走内核沙箱的 bash 路径写文件被 `sandbox-exec` **拒绝**（退出码非 0、stderr 命中该后端的 denialSignatures、文件未生成），
   而 `run_code` 的程序体用 `await import('node:fs')` **成功写入并读回**同一个文件；真实 headless 会话里工作区内外两个文件都写成了。
   **机制**：程序体跑在**宿主 DSH 进程的 worker thread** 里（`program pid === host pid`），
   因此根本**没有一个可被 `sandbox-exec` 包住的子进程**。措辞更正两处：`require` 在程序体里不存在
   （`ReferenceError: require is not defined`，程序体是 `new AsyncFunction` 的函数体而非模块作用域），可达路径是 `await import()`；
   worker 的 `env: {}` 已实测生效（`process.env` 键数 = 0），所以"拿不到 API key"是真的——但它只挡凭据，不挡文件系统。
   **残留**：**`node:child_process` 与网络（`node:net` / `fetch` 出网）仍未测**；
   「`run_code` 绕过 `ctx.fs` 围栏」这一半仍只有代码依据，没跑过对照；
   本轮证明的是「一旦 `run_code` 上了模型面，沙箱拦不住它」，不是「出厂就已经上了模型面」（本轮显式设了 `DSH_TOOLS_MODE=both`）。
5. **compaction 从未在本机触发** → **已触发，且 meta 逐字保留 6/6**
   〔裁定 · S0 实测，[E: .loop/m0/M0-5.json]〕。把 `compaction-basic` 的 `thresholdRatio` 压到 **0.02** 跑一次真实 headless 会话，
   会话日志里出现 **6 条 `compaction/prune`** 与 **6 条带 `surfaceOp {op:'replace'}` 的 `tool/result` 替换体**；
   6/6 替换体的 `data.meta` 与被替换原事件的 `data.meta` **JSON 逐字相同**，`data` 里除 `message` 外的所有字段亦逐字相同，
   6/6 原事件仍留在日志原 seq 处。整个证据锚点方案的地基由此从「读对了」变成「跑过了」。
   触发前的对照仍然成立且重要：本机 160 个 session、182,582 行日志里 `compaction/prune` = 0——
   **零 replace 是压力从未到阈值，不是机制不存在**。
   **残留**：触发靠人为压阈值，自然使用下多久触发一次仍未知；只跑到 **pressure 分支**，
   `context-overflow` 分支与 `compactRegion` 的 **LLM 摘要分支都没跑到**（摘要分支会不会丢 meta，**未测**）；
   `meta` 的 8 KB 隐性上限**未验证**。
6. **中央限速网关的失效行为未设计** → **已定失效行为，且「DSH 侧零支撑」被推翻**
   〔裁定 · S0 实测，[E: .loop/m0/M0-6.json]〕。`dsh-mcp-client` 提供真实可用的子进程托管
   （spawn + 指数退避重连 + 每次 outage 的尝试预算 + `failOnStartupError`）：网关起不来时 `dsh` **退出码 1、stdout 0 字节、一个 turn 都没跑**。
   但两条实测推翻了原前提：① 网关**中途崩溃后被静默换进程**（pid 71338→71389），五次调用全部成功、DSH 自身 stderr **0 行**、退出码 0——
   令牌桶与跨 agent 缓存被静默清零而取证链上无任何记录；② stdio 传输下网关是**每 harness 进程一个子进程**（两个并发 `dsh` 拿到两个不同 pid），
   **不是跨进程单例**。故失效行为定为：启动期 fail-closed（`failOnStartupError: true`，**出厂默认是 `false`**）、
   运行期允许被监管重启但必须在证据上留痕（`gateway_boot_id` 变更后的证据判 `source_integrity=not_covered`）、**降级直连一律禁止**。
   **残留**：只测 stdio，**streamable-http（跨进程共享的唯一形态）一次都没跑过**；
   `gateway_epoch` 方案只有设计、无实现、无红样本，且它防不了「网关自己报一个假 epoch」。
7. **`gate_integrity.sh` 自身谁来证明没被改** → **现有锚点方案被实测判死，自指问题在本仓库仍未闭合**
   〔裁定 · S0 实测，[E: .loop/m0/M0-7.json]〕。详见 00-PREMISE §B8 第 1 条的重写。两句话版本：
   **git tag 不是不可变锚点**（git 2.55.0：`receive.denyDeletes` 与 `receive.denyNonFastForwards` 对 `refs/tags/*` 全部不生效，
   tag 的非快进强推与删除都 ACCEPTED，同一次实验里 `refs/heads/*` 双双 REJECTED；默认配置下 tag 连 reflog 都不写）；
   **且「从 tag 检出干净副本执行」这个候选解被红样本证伪**——把 `gate_integrity.sh` 换成只 `echo OK` 的假货并提交，
   从**仓库内**入口调用得到**退出码 0**。本仓库能真正做到的最强形态是「锚点换 40 位 commit sha + 仓库外 pinned runner」
   （同一份被篡改的仓库：仓库内入口 exit 0，仓库外 pinned runner exit 3），
   **但本仓库 `git remote` 数为 0，那个"仓库外"今天并不存在**。这是**带条件的部分答案**，不是解决。
8. **（S0 新增）多帧 zstd 是已确认的地雷** 〔裁定 · S0 实测，[E: .loop/m0/M0-2b.json]〕。
   DSH 的 session JSONL 落盘是**多个独立 zstd frame 串接**，而 Node 内置 zstd API **只解第一帧**：
   本机 `~/.dsh/sessions` 下 **155 个 session 日志全部多帧、无一例外**，Node 内置 API 合计只读到 **155 行**
   （每文件恰好第一帧那一行），`zstd -dc` 合计 **182,212 行**。单文件对照：28 frame 的日志，`zstd -dc` 55 行、
   `zlib.zstdDecompressSync` 1 行、流式 `createZstdDecompress` 1 行、手动按 magic `28 B5 2F FD` 切帧循环回到 55 行。
   **任何 Node 写的日志门若不循环解帧，会静默只读到 1 行并误判日志为空**——这不是边缘情况，是必然发生。
   **残留**：只在 macOS 26.5.2 / Node v24.16.0 / DSH 0.1.0-rc.6 这一个组合上测过（Node 未来若改成自动串帧，本结论失效——红样本门正为此存在）；
   `ctx.sessionPersistence.readRaw` 与 `/api/session.export` 两条替代读法**未验证**能否拿到全部帧。
   **口径说明**：本条的 155 / 182,212 与第 5 条的 160 / 182,582 是**同一目录在两个不同时刻的快照**——
   `~/.dsh/sessions` 随每次 DSH 运行增长，这类聚合数字不可逐字节复比，可复比的是单文件那一组。

**运行面**：一切运行、调试、验收走 headless + 门脚本 CLI（`dsh --profile`，**exit code + stdout 内容断言**）。
〔裁定 · S0 实测，[E: .loop/m0/M0-3b.json]〕**`dsh` 的退出码只反映 harness 成败，不反映任务成败**：
让 agent 跑 `exit 7`，agent 如实回答 `7`，`dsh` **仍然退出 0**（同一条命令里 `dsh_exit=0`）。
退出码 1 只覆盖 harness 层失败（profile 不存在 / 缺 task / 未知 flag / 插件树未激活 / LLM 侧 AUTH·INVALID_REQUEST·TRANSPORT）。
因此**「exit code 判定」这四个字单独用是空的**：任何以 dsh headless 为载体的 check，其"失败"信号必须由**被测方在 stdout 里显式写出**
（约定机器可判的尾标记，例如最终消息必须以 `RESULT: PASS` / `RESULT: FAIL` 结尾），harness 退出码只作二次兜底。

**这条失效有边界，不要读成全盘失效。** `gates/` 下的门是纯 node/bash 脚本、跑在 **dsh 之外**，
它们的退出码**完全可靠**，当前 8/8 的绿不因此打折。失效的**只是以 dsh headless 为载体的验收**——
即端到端 run 与等预算 A/B 两臂的成败判定：那些地方 `dsh` 恒返回 0，退出码判据是空的，
必须改写成「跑完后由门脚本读产物并判定」。

〔裁定 A-1〕本轮一手语料中**不存在独立于 headless 的 TUI 包**（`dsh web` 只是 `--profile web` 的别名），
因此"terminal 一等"的准确含义即 headless + 标准输出 + 门脚本报告；若用户所指 TUI 是某个未读到的包，该裁定需重做。
**运行面的残留**：只测了 headless profile——`dsh web` 的退出码语义、长任务超时与 SIGINT/SIGTERM 中断路径、
`--patch` overlay 与 `dsh plugin` 子命令的退出码**全部未测**；且**未找到把完整轨迹（而非仅最终消息）导出成文件的 CLI 开关**，
轨迹落在 `$DSH_HOME/sessions` 的 jsonl，**该路径未验证解析**（并受上面第 8 条的多帧 zstd 地雷约束）。
