# 01-CONTRACTS — 唯一规范源

> **本文件的地位**：本文档集中，任何被多个文档共享的术语、枚举、字段、规则，**只在这里定义一次**。
> 其他文档引用时只能写「见 01-CONTRACTS §x.y」，**禁止复述定义原文**——复述即为回归（可 grep 检测，见 §9.3）。
> 需要新术语时，先改本文件，再改引用它的文档。
>
> **本文件不含**：实现细节、架构图、排期、成本估算。它只回答「这个词是什么意思，谁能写它，什么时候它成立」。
>
> **写作纪律**：每条载重断言带证据指针 `[E: <文件>#<锚>]`，指向 `research/v2/` 语料或一手 URL。
> 语料中标 `unverified` 的数字，本文件在引用处一并标注，不做洗白。
> 无外部证据、由本文件自行裁定的规则，显式标 **〔裁定〕** 并给出「什么会推翻它」。
>
> **硬约束**：本文件中任何关于 DSH 运行时的陈述，均不得与 `research/v2/GROUND-TRUTH-CORRECTIONS.md` 冲突。冲突以该文件为准。

---

## §0 全局公理

**§0.1 产品是可信度，不是文章。** 每条断言携带一个由机器计算的状态；散文只是这些断言的渲染层。正文中不允许出现未被某条 claim 覆盖的数字或比较（§8.4 W-10）。

**§0.2 状态是算出来的，不是断言出来的**——但这条的强制力**分两层，且第二层目前是审计而非结构**〔裁定 · R1/C-2〕。

| 层 | 内容 | 强制手段 | 强度 |
|---|---|---|---|
| ①**工具面** | claim 提交工具的 schema **不含** `status` 字段，出现即 `tools/pre-execute` deny | DSH 工具边界钩子，**结构性** | 硬。agent 无法经正常工具路径写 status |
| ②**文件面** | `.arc/claims/*.status.json` 只由门代码写 | **无文件系统级强制** | 软。见下 |

**第二层为什么是软的**：`run_code` **同时绕过**内核沙箱（只管 bash）**和** `ctx.fs` 策略围栏（只管 `ctx.fs` 工具）
[E: GROUND-TRUTH-CORRECTIONS.md#A7]。一个拿到 `run_code` 的 agent 可以直接 `(await import('node:fs')).writeFileSync(...)` 写 status 文件。

**这条已从推论变成实测**〔裁定 · S0 实测，记录 `.loop/m0/M0-4.json`〕：
同机同时刻同一条 read-only 策略下，走内核沙箱的 bash 路径写文件**被 `sandbox-exec` 拒绝**
（退出码非 0、stderr 命中该后端的 denialSignatures、文件未生成），
而 `run_code` 的程序体 `await import('node:fs')` **拿到 fs 并成功写入、读回**。
真实 headless 会话（`DSH_PERMISSION_MODE=read-only`）复现同一结论，且工作区**内外**两个文件都写成、磁盘核实存在。

**机制也定位了**：`run_code` 跑在**宿主进程的 worker thread** 里（实测 `program pid === host pid`），
**根本不存在可被 `sandbox-exec` 包住的子进程**——所以这不是沙箱配置问题，是结构问题。
另两条实测边界：程序体是 `new AsyncFunction` 的函数体，因此 `require` **不在作用域**（`ReferenceError`）；
`process.env` 键数 **= 0**（挡得住凭据，挡不住文件系统）。
`node:child_process` 与网络出站**仍未实测**，那两项继续按最坏假设措辞。
DSH 侧不存在能拦住它的机制。

**因此本文件不得声称「不存在任何一条从 agent 输出到 status 的写路径，这是结构性后果」。**
那句话是假的，而且 00-PREMISE B8 明令：在 gate-integrity 真脚本落地前，
这类保障「一律按 `unverified` 对待，且**不得在下游文档里被引用为已建立的保障**」。
规范源的第一条公理违反了自己前提文档的禁令——R1 两个攻击者独立命中（F003 / F025）。

**准确表述**：*我们能结构性地保证 agent 不能经工具路径写 status；我们只能靠事后审计发现它绕过工具路径写了 status。*

**审计侧的兜底**（诚实地说明它能抓到什么、抓不到什么）：
- 能抓到：`status.json` 的 `inputs_hash` 与门重跑结果不一致 → 该 claim 判 `not_covered`（§4.4）。
  这条对**内容伪造**有效——伪造者必须同时算对 `inputs_hash`，而它是门版本 + 全部输入的哈希。
- **抓不到**：伪造者调用门自己的库函数算出正确 `inputs_hash` 再写文件。
  此时产物与真门产物逐字节不可区分。
- **不能用「门产物自证签名」补**：§8.4 D-8.4 已以同一威胁模型否决过该机制
  （能写文件的执行者同样能调签名函数）。用它兜底会让防篡改论证成环。

**真正的收口在 M0**（`gate_integrity.sh` + 门轨道与 producer 轨道的**进程级**隔离：
门在不给 `run_code`、不给写 `.arc/` 的独立 profile 里跑）。在它落地前，
本条按 §0.2 表格的两层如实陈述，**不得简写成一句公理**。

**§0.3 我们承诺两件可兑现的事，不承诺第三件。**
可承诺：**注入不能改变 status**、**注入必然留痕可复核**。
不可承诺：**阻止注入**。依据：OWASP LLM01:2025 官方措辞逐字为「it is unclear if there are fool-proof methods of prevention for prompt injection」；八个已发表 IPI 防御被自适应攻击全部绕过、ASR 持续 >50% [E: ext-security-injection.md#F6, #V19]。

**§0.4 模型侧能力假设为零。** 截至 2026-08-17 **未找到** deepseek-v4-pro / v4-flash 的公开 IPI 专项评测（语料状态为 `unverified`，不是「不存在」；已知线索：IssueTrojanBench（arXiv 2026-07-22）评测模型含 DeepSeek V4-Pro，只是未取到其专项数字）；现存 DeepSeek 安全数字（100% / 70.27% / 39.7%）全是越狱口径、彼此差 2.5 倍，不可迁移到 IPI [E: ext-security-injection.md#V30, #V31]。架构必须在「模型 100% 会被注入」的前提下仍给出正确 status。

**§0.5 一切「默认值」引出厂组合，不引包 README。** 包 README 的默认值与出厂 `dsh-base/cordis.patch.yml` 的实际生效值多处不一致（如 sandbox 模式、ralph 轮次）[E: GROUND-TRUTH-CORRECTIONS.md#A9, #A10]。

---

## §1 状态模型 — 三个正交谓词与一个派生状态

### §1.1 为什么必须拆

`verified` 这一个词在 v1 里同时承载了两个不同的谓词。安全维度的结论是：把「引语忠于来源」的绿灯当成「来源为真」的绿灯，等于**把审计能力当作真值能力卖** [E: ext-security-injection.md#结论摘要, #一、信任边界论证]。一个被投毒的页面能 100% 通过逐字匹配——这不是实现缺陷，是谓词错配。

支撑该判断的最强一手证据（立场论文，无实验数字）：Schlichtkrull, *Attacks by Content*（EMNLP 2025 Main, arXiv:2510.11238）逐字写道 "Existing defenses, which focus on detecting hidden commands, are ineffective against attacks by content." [E: ext-security-injection.md#B1]

### §1.2 三个正交字段（挂在**证据**上，不挂在 claim 上）

| 字段 | 值域 | 可判定性 | 判定方式 |
|---|---|---|---|
| **`quote_faithful`** | `pass` / `fail` / `na` | **确定性、哈希可判** | 归一化后的逐字引语是否为快照抽取文本的子串。无模型参与。 |
| **`source_integrity`** | `intact` / `mutated` / `missing` / `contaminated` / `not_covered` / `na` | **确定性、精确匹配可判** | 三个子测试全部是精确比对：①字节同一性（`raw_bytes_sha256` 复核）②抓取溯源绑定（本条证据能否绑到一条真实发生过的 `tool/call`/`tool/result`）③注册表成员资格（DOI ∈ 撤稿库、ISSN/域名 ∈ 劫持刊表）。 |
| **`claim_supported`** | **不是布尔值，是一条核算记录** | **确定性不可判** | 只能给证据强度与独立性核算。见 §1.3。 |

**§1.2.1** `source_integrity` 的三个子测试都不是对 claim 的判断，都是对「我引的这份东西还是不是我以为的那份东西」的判断。三者全部可重跑、模型无关，因此同属确定性层。子测试②的必要性：`verified` 的最低门槛是「这次抓取确实发生过」，而 session 日志只能证明发生过、不能提供原文（§8.2）。

**§1.2.1.1 `na` 的唯一合法用途**〔R1/F014〕：**K-I（逻辑推断）的输入是别的 claim，根本不存在抓取事件**，
三个子测试全部无对象。旧值域没有 `na`，于是 K-I 只能落 `not_covered` → `S` 的 0c 在第 1 步之前就返回 ST-N，
**逻辑推断这条通道在契约上整条死掉**——而它是本项目三条背书通道之一。

`na` 的准入条件是可机器判定的，且**只有这一条**：`kind == K-I` 且该 claim 的证据指针全部指向其他 claim
（不含任何 `evidence_id`）。任何其他 kind 取 `na` 即 V1.8 失败。
K-I 的溯源性不由 `source_integrity` 承担，而由**其前提 claim 各自的 status** 承担
（§2.3 的前提可追性 + §1.5 第 1 步 K-I 的 base 上限 ST-A）。

- **V1.8** 语料中不存在 `kind != K-I` 且 `source_integrity == na` 的证据记录；
  也不存在 `source_integrity == na` 却携带非空 `evidence_id` 的记录。

**§1.2.2** 归一化算法（`quote_faithful` 的唯一实现）：NFKC → 统一引号/破折号/省略号 → 折叠空白；PDF 专项做跨行连字符还原与页眉页脚去重；**中文专项做全角/半角统一，并删除一切与 CJK 字符相邻的空白——不按语言分支**（见 §1.2.2.0：原写法「按整串是否含 CJK 决定要不要去空白」是非对称的，实测把中文网页命中率打到 5.0%）[E: ext-reproducibility.md#3 归一化匹配算法]。

判定只有两个出口，**`pass` 当且仅当归一化后的引语是快照抽取文本的精确子串**：

```
归一化(引语) 是 归一化(快照抽取文本) 的子串  → pass
否则                                        → fail  +flag F-28
```

**§1.2.2.0 归一化算法按 S0 实测重写**〔裁定 · S0 实测，[E: .loop/m0/M0-2.json]〕。

S0 对该算法做了端到端实测（7 份 PDF × 每份 120 条引语 + 5 份网页）。**结果推翻了原算法**：

| 臂 | 未归一化的原始子串命中率 | 套上**原** §1.2.2 后 |
|---|---|---|
| 同工具对照（引语直接取自我们自己的抽取文本） | 恒 **100.0%** | **91.7%–100.0%** |
| 中文维基百科页 | 100.0% / 96.7% | **5.0% / 17.5%** |

即：**归一化本身在制造假阴性**，而且中文网页上摧毁了整条通道。两条根因都已最小复现：

- **(A) 「中文专项整串去空白」按「该串是否含 CJK」分支，因此是非对称的。**
  中文文档里的一条**纯英文**引语：引语侧保留空格、快照侧被抹掉，**永远不可能命中**。
  最小复现：`optimal transport` —— `raw substring = True`，`as_written pass = False`。
- **(B) 跨行连字符还原是上下文相关重写。** 引语若在还原窗口内被截断就必然失配。
  最小复现：`German, Arabic, Rus-\n` —— `raw substring = True`，两种规则都 `pass = False`。

**修正后的规则（已实测验证）**：把中文专项改成
**「凡与 CJK 字符相邻的空白一律删除，且不按语言分支」**。效果：

| 臂 | 原规则 | 修正后 |
|---|---|---|
| 同工具对照 | 91.7%–100.0% | **99.2%–100.0%** |
| 中文 PDF | 70.8 / 100 / 88.3 | **100 / 100 / 96.7** |
| 中文网页 | 5.0 / 17.5 | **100 / 96.7** |
| 英文 | — | **全部不变** |

且该规则**不会**让 `the rapist` 误命中 `therapist`（实测确认）——因为它只删 CJK 相邻空白。

**§1.2.2.2 「100% 兑现」这个承诺必须收窄**〔裁定 · S0 实测〕。

即便用上修正规则，**跨工具**场景（作者从自己的 PDF 阅读器复制引语、门拿我们的抽取文本比对）
仍不是 100%：**英文 90.0%–100.0%、中文 96.7%–100.0%**。残余失配来自阅读顺序、连字/私用区字形与公式。

因此本项目对 `quote_faithful` 的准确承诺是：

> **在同工具口径下**（引语来自我们自己的抽取文本，即 producer 从快照里取引语），
> `quote_faithful` 是确定性、哈希可判的谓词，实测命中率 **99.2%–100.0%**。
> **跨工具口径下不承诺 100%**——作者从外部阅读器复制的引语有 0%–10% 的概率因字形与阅读顺序差异而判 fail，
> 此时走 §1.2.2.1 的修复建议通道（F-28a），由 producer 改用快照里的真实跨度。

**这条把一个营销式的「100%」换成了一个有口径、有实测数字、有失败去向的承诺。**
它是本项目仅有的两条「可 100% 兑现」承诺之一——**现在只剩一条半**。
另一条（`source_integrity`）在默认档 Tier B 下也已按 §8.6.2.1 收窄。
产品页上不得再出现不带口径的「100%」。

**实测本身的边界**（`honest_limits` 逐条转述，不得省略）：
引语是**程序按固定种子截取的连续字符段**，不是真人手选（真人倾向在句子边界与完整术语处起止，真实命中率可能更高）；
「人类复制侧」用 `pdftotext -layout` 与自建 innerText 作代理，**没有真的用 Preview/Acrobat 复制、也没有真的取浏览器剪贴板**；
语料规模小——7 份 PDF（4 英 3 中，**全部数字原生**，中文全部来自《软件学报》一家期刊、排版引擎单一）+ 实际只测到 3 份网页；
**完全没有扫描件/OCR PDF，没有 Word 导出 PDF**。

**§1.2.2.1 近似命中是修复建议，不是判定结果**〔裁定 · R1/C-3〕。
`rapidfuzz partial_ratio ≥ 95` 的近似命中**不产生 `pass`**，只产生一条**修复建议**：
门把快照里的真实跨度写进 `claims/<id>.quote-repair.json`（W-16，门轨道写、producer 只读），
并附加 flag `F-28a near-miss-repairable`。
该 claim 要变成 `pass`，唯一路径是 **producer 自己把 claim 里的引语改成那个真实跨度、重新提交、门重跑并拿到精确命中**。
门**永远不代替 producer 改写 claim**。

**为什么这条不能省**：原写法是「≥95 命中 → 把引语改写成快照里的真实跨度后重判 → pass」。
它让 `pass` 的含义从「逐字引语是快照的子串」滑成「存在一个与引语 95% 相似的跨度」，
**哈希可判定性直接没了**——而 `quote_faithful` 是全项目仅有的两条「可 100% 兑现」承诺之一（§0.1）。
更糟的是改写由门执行，等于门在替被检查方修改被检查对象，违反 §4 的写权分离。
R1 两个独立攻击者各自命中此处（F079 / F152）。

**保留近似匹配的理由**：`< 95` 与 `95..99` 的审计含义不同——前者多半是编造，后者多半是抽取噪声
（PDF 连字符、中文空格）。合并成一个 `fail` 会让「抽取管线有 bug」和「producer 在编引语」不可区分。
所以两者都判 `fail`，但带不同的 flag，进不同的队列。

**§1.2.3 抽取质量哨兵（fail-closed）。** 抽取文本为空、或 CJK/拉丁字符比例异常 → `source_integrity = not_covered`，**绝不能因为抽取失败而让匹配「找不到」并静默降级** [E: ext-reproducibility.md#溯源门必须 fail closed 的五个点]。中文 PDF 抽取是该假阴性的最大来源；阈值未标定前，中文引语门偏保守。

### §1.3 `claim_supported` 是核算记录，不是谓词

必填字段（缺任一 → 该 claim 直接 `not_covered`）：

```
claim_supported := {
  evidence_grade            : G0..G5                    // §3
  independent_cluster_count : 整数（按 upstream_id 归并后）  // §5.5
  counter_evidence_searched : bool                       // 必须为 true，否则 S 的 0e 直接返回 ST-N（§1.4.1）
  counter_evidence_found    : bool
  mechanism_results[]       : { gate_class, gate_id, verdict, params, data_as_of }  // §6
  flags[]                   : §7
  budget_state              : ok | degraded | exhausted
}
```

**为什么这一项确定性不可判——三条独立的量化上界**：

1. 「这条引文是否真的支持该断言」这一维，**所有被测模型的置信区间重叠、统计上不可区分**，最好者 Claude Opus 4.6 F1 = 0.750（624 对 attribution–citation = 1,248 条 rubric 决策）[E: ext-evaluation.md#B3, #29]。
2. 逐条（per-claim）口径的最好成绩在 BAcc 74.7–77.4 区间（MiniCheck-FT5 在 LLM-AggreFact 10 个数据集平均 74.7；Bespoke-Minicheck-7B 在公开 leaderboard 11 个数据集平均 77.4）[E: ext-verification-mechanisms.md#M6]。**注意：LLM-AggreFact 的数据集数量在论文（10）/leaderboard（11）/后续论文（14）之间漂移，跨版本数字不可直接比。**
3. LLM-judge 的一致率被系统性高报：MT-Bench 上 exact match 0.788–0.851 对应的 Cohen κ 只有 0.376–0.511，raw agreement 平均虚高 **38.6 个百分点**（区间 33.8–41.3 pp；**样本 = MT-Bench 2,391 对**。⚠️ 不是 541,000——那是全研究规模：21 judge / 9 厂商 / 约 541,000 次判定 / 118 次 run，本数字的分母比它小两个数量级）[E: ext-evaluation.md#C1, #16]。

**因此**：`quote_faithful` 与 `source_integrity` 是**可以 100% 兑现**的产品承诺；`claim_supported` 只能是分级判断。产品语义、门的实现、对外文案三处必须同时保持这条界线。

### §1.4 派生的、面向用户的 claim 状态（唯一枚举）

```
ST ::= verified | attributed | estimated | contested | unverified | not_covered
```

| 标识 | 值 | 中文 | 含义 |
|---|---|---|---|
| ST-V | `verified` | 已核验 | 由 Class-0 或 Class-1 门（§6）确定性判定成立。判定路径不经过任何模型。 |
| ST-A | `attributed` | 已归因 | 锚点存在且完整，但「锚点 ⟹ 断言」这一步由模型或人判断。 |
| ST-E | `estimated` | 已估读 | **仅用于数值断言**，其值来自图形几何读数。必须携带 `epsilon` 与 `method`。 |
| ST-C | `contested` | 有争议 | 找到了反证，或来源命中污染注册表。 |
| ST-U | `unverified` | 未证实 | 决定性机制跑了，没能建立支持。 |
| ST-N | `not_covered` | 未覆盖 | 决定性机制**没跑或不适用**（源不可达、注册表快照过期、GRIM 功率为 0、中文文献无覆盖、预算耗尽）。 |

**§1.4.1 `unverified` 与 `not_covered` 必须分开。** 两者对读者的渲染都不得表述为事实，但审计含义完全不同。把 `not_covered` 静默当成通过，正是前代 rigor 门的实际行为（伪造 metric + 无原始数据 → exit 0 PASS）[E: GROUND-TRUTH-CORRECTIONS.md#C1]。

**准确判据**〔R1/F006 后收紧〕。旧文本写「前者是『我们看了，没找到支持』，后者是『我们没能力看』」，
把 `not_covered` 绑在**能力**上。这造成一处二义：`counter_evidence_searched == false`
（**该看而没看**）按 §1.3 的字段注释应落 ST-U，按 §1.5 的 0e 却落 ST-N。同一输入两个输出，
违反 V1.2 的纯函数性。二者的分界线**不是能力，是程序是否跑完**：

| 状态 | 判据 | 一句话 |
|---|---|---|
| **ST-U** `unverified` | 验证程序**完整跑完了**，结论是「没拿到足够支持」 | 我们看了，没看到 |
| **ST-N** `not_covered` | 验证程序**没跑完**——无论因为跑不了（能力/权限/覆盖盲区）还是因为某个必经步骤没执行 | 我们没看完 |

按这条判据，`counter_evidence_searched == false` 明确落 **ST-N**：反证检索是 §7.2.3 规定的必经步骤，
它没跑，程序就没跑完。§1.3 的字段注释相应改为「必须为 `true`，否则 `S` 的 0e 直接返回 ST-N」。

**为什么这个分界线比「能力」那条好**：能力口径下，「我们本来能搜但偷懒没搜」无处安放——
判 ST-U 是在说「我们看了」（假话），判 ST-N 是在说「我们没能力」（也是假话）。
程序口径下它落在 ST-N 且语义准确：**这条 claim 没有走完我们承诺的流程**。
而且这条口径把「偷懒」和「能力受限」放进同一个桶是**有意的**——
对读者而言两者的后果一样（这条断言不可信），差别只在内部审计，由 flag 区分（F-29 vs F-32/F-33）。

**§1.4.2 `contested` 与 `unverified` 必须分开。** 二元 status 会把「静默语义漂移」全部标成绿灯：SearchGEO 实测，即使判定为「攻击失败」的案例中，复合层攻击仍有 **15.0%** 的输出语义漂移超过 Δ≥0.3 阈值 [E: ext-security-injection.md#V22b]。

**§1.4.3 `human_review_required` 是布尔字段，不是状态值。**〔裁定〕「谁需要看」是工作流属性，「我们知道什么」是认知属性，把二者塞进同一个枚举是 v1 类错误的复发面。人审队列由 `flags` 与 `mechanism_results` 路由。
**什么会推翻**：若交付实践中出现「人审完成」这一状态需要独立于 status 呈现给读者且无法用 flag 表达，则加一个 status 值。

**§1.4.4 不存在聚合 status。** 系统不得产出「全部已验证」这类整体性断言，只能产出逐 claim 状态 [E: ext-multimodal-evidence.md#D7]。门通过率不得作为对外质量指标——它的分母可被压缩（少写载荷数字即可提高通过率）；内部诊断时必须分子分母同露（「142 verified / 187 载荷断言」，不写 76%）[E: ext-evaluation.md#R1]。

### §1.5 状态函数 S — 唯一的计算式

`status = S(kind, quote_faithful, source_integrity, claim_supported)`，按下列顺序求值，**先命中先返回**：

```
S:
  第 0 步 · 前置否决（任一命中 → 立即返回）
    0a  source_integrity ∈ {mutated, missing}      → ST-U   +flag F-16 / F-27
    0b  source_integrity == contaminated           → ST-C   +flag F-05 / F-06
    0c  source_integrity == not_covered            → ST-N   +flag F-18 / F-30 / F-32 / F-33
        含「一手源不可达」。**禁止用二手转述补齐**，见 §8.6.4
    0d  claim 携带逐字引语 且 quote_faithful == fail → ST-U   +flag F-28
    0e  counter_evidence_searched == false          → ST-N   +flag F-29
    0f  budget_state == exhausted                   → ST-N   +flag F-11
    0g  决定性机制未运行（mechanism_results 为空）   → ST-N

  第 1 步 · 按 kind 取基准值 base（§2）
    K-D 数据推导（封闭式）: 重跑门通过 → ST-V        否则 ST-U
    K-D 数据推导（开放式）: 重跑门通过 → ST-A        否则 ST-U      （开放式端到端永不可达 ST-V，§2.1）
    K-L-T 文献转录       : 锚点包含检验通过 → ST-V   否则降为 K-L-A 处理
    K-L-A 文献归因       : 归因裁决 support → ST-A   partial/not-support → ST-U
    K-I 逻辑推断         : 推断门全项通过 → ST-A     否则 ST-U      （K-I 永不可达 ST-V，§2.3.1）
    图形读数的数值断言    : base 强制为 ST-E（覆盖上述结果）        （§3.5）

  「封闭式 / 开放式」的机器判据〔R1/C-9 后收紧〕：**不是一个字段，是一份冻结工件**。

  旧写法是「`question_authored_by == human` 且问句与数据文件在 run 之前即已冻结 → 封闭式」，
  但「已冻结」没有任何机制——没有冻结文件、没有哈希、没有入 manifest。
  它是 K-D 通往 ST-V 的**唯一开关**（开放式端到端永不可达 ST-V），却由被检查方自报。
  对照 04 给 checklist 配了完整的 `runs/<run_id>/checklist.json` + hash 入 manifest + 冻结断言。

  收紧后的判据，三条**全部**满足才是封闭式，缺一即按开放式处理（即 base 最高只能到 ST-A）：

  1. 存在 `runs/<run_id>/questions.frozen.json`，含问句全文、目标数据文件的 `sha256`、
     `frozen_at` 时间戳、冻结者身份（W-12，编排层写，producer 不可写）；
  2. 该文件的 `sha256` 出现在 `runs/<run_id>/manifest.json` 里，且 manifest 的写入事件
     在 session 日志中**早于**本 claim 的第一条 producer `tool/call`（时序由 seq 判定，不由时间戳判定）；
  3. claim 的 `question_id` 能在该冻结文件中精确匹配到一条问句。

  第 2 条是牙齿所在：它把「先看数据再编问题」这个最常见的 p-hacking 形态变成一个**可判定的时序事实**，
  而不是一句纪律。GC-0 门检查这三条，`question_authored_by` 退化为一个仅供人读的说明字段。

  第 2 步 · 单调降级（只能往下，不能往上；顺序固定，每步只读 base 与 S 的输入）
    2a  counter_evidence_found == true              → ST-C（吸收态，覆盖任何 base）
    2b  independent_cluster_count < K(kind)         → base = 降一档(base)
    2c  evidence_grade 上限（§3.4）+ retention_tier 上限（§8.6.2） → base = meet(base, 两个上限)
    2d  §7.3 中作用类型 == ceiling 的已置位 flag     → base = meet(base, 各 ceiling)
    2d′ §7.3 中作用类型 == step-down 的已置位 flag   → 每命中一条执行一次降一档（叠加）
    2e  budget_state == degraded                    → base = 降一档(base) +flag F-11

  返回 base
```

**§1.5.1 单调性不变量（可机器检查）**：`S` 的第 2 步中每一条规则都只能把 base 沿 `ST-V ⊐ {ST-A, ST-E} ⊐ ST-U` 这条链向下移，或移入吸收态 `ST-C` / `ST-N`。**任何提升状态的规则都是缺陷。** 因此 `S` 可以用「对每条规则做一次符号执行、断言输出 ≤ 输入」来自动验证。

**§1.5.1.1 `降一档` 与 `meet` 的完整定义**〔裁定 · R1〕。
上面那条偏序**不是全序**——`ST-A` 与 `ST-E` 明写不可比。旧文本却在 2c/2d 直接写 `min(...)`，
于是「图形读数（base = ST-E）+ G4 证据（上限 = ST-A）」这个**常见**组合下 `min` 无定义，
`S` 不是全函数，V1.2 的「重跑逐字节相同」不可能成立。两个函数因此显式定义如下：

```
格结构（ST-C / ST-N 是吸收态，在第 0 步/2a 已返回，不参与）：

        ST-V
       /    \
   ST-A      ST-E        ← 同层，互不可比
       \    /
        ST-U

降一档(ST-V) = ST-A        降一档(ST-A) = ST-U
降一档(ST-E) = ST-U        降一档(ST-U) = ST-U        （下界饱和，不再下降）

meet(x, y) = 该格中同时 ≤ x 且 ≤ y 的最大元素：
  meet(x, x)        = x
  meet(ST-V, y)     = y
  meet(ST-A, ST-E)  = ST-U      ← 关键一条：两个同层不可比元素的下确界是 ST-U
  meet(ST-U, y)     = ST-U
  （meet 满足交换律与结合律，因此 2c/2d 内多个上限的求值顺序不影响结果）
```

`meet(ST-A, ST-E) = ST-U` 不是权宜之计，是格论里下确界的定义本身，而且语义正确：
若证据等级只撑得起「归因」、同时数值又来自图形几何读数，那么我们既没有干净的归因、
也没有干净的估计，**诚实的答案就是 unverified**。

**§1.5.1.2 `S` 是全函数（可机器检查）**：`降一档` 与 `meet` 在四元素集 {ST-V, ST-A, ST-E, ST-U} 上
逐点定义完毕，第 0 步的七条前置否决覆盖了全部吸收态入口。因此对任意合法输入向量 `S` 都有唯一返回值。
V1.7 用穷举验证这一点。

**§1.5.2 `K(kind)` 的取值**〔裁定〕：`K(K-D) = 1`（数据推导的独立性由重跑保证，不由多源保证）；`K(K-L-T) = 1`（转录只需要一个真实锚点）；`K(K-L-A) = 2`；`K(K-I) = 2`（前提集合的独立簇数）。
**理由**：`K ≥ 2` 是对「合成共识」的最低防线——SearchGEO 的合成共识模式在 Gemini-3-Flash 上 ASR 达 73% [E: ext-security-injection.md#V22]；中文层有现成活体样本：11 家中文媒体全部回溯到同一条 Nikkei Asia 上游 [E: ext-security-injection.md#E3, ext-chinese-ecosystem.md#结论摘要-8]。
**什么会推翻**：若上游簇归并器（§5.5）在金标集上的假合并率高到使 `K=2` 事实上等价于 `K=1`，则必须提高 K 或改用连续的证据强度。

### §1.6 可检验断言

- **V1.1** 对任意 claim，`status` 字段的值必须落在 §1.4 的六值枚举内；出现第七个值即失败。
- **V1.2** 对任意 claim，重跑 `S` 必须得到与存档 `status` 逐字节相同的值（`S` 是纯函数，输入全在 CAS 与注册表快照里）。
- **V1.3** 符号执行 `S` 的第 2 步全部规则，断言每条规则的输出状态在 §1.5.1 的偏序下不高于输入。
- **V1.4** 语料中不存在任何 `status == verified` 且 `mechanism_results` 中含 `gate_class == GC-2` 的 claim（§6.4）。
- **V1.5** 不存在名为 `overall_status` / `all_verified` / `pass_rate` 且被写进交付物的字段。
- **V1.6** 红队用例 RT-1〔R1/C-1 后重写〕：构造一个格式规范、含一句语法完美且**虚假**的数值断言的网页。

  旧写法期望「`quote_faithful = pass` 且 `status ≠ verified`，因为 `independent_cluster_count = 1` 触发 2b」。
  **这是错的**：§1.5.2 定 `K(K-L-T) = 1`，`1 < 1` 为假，2b 根本不触发。R1 的五个攻击者都撞上了这里。
  但正确的修法**不是**让单簇无条件降级（那会让 ST-V 全局不可达，见 §7.3.2），而是**把两个对象分开**：

  | 对象 | kind | 期望 status | 它到底断言了什么 |
  |---|---|---|---|
  | ①「该网页的 span Y 逐字为 Z」 | K-L-T | **ST-V** | 转录属实——网页确实这么写了。这条**是**真的 |
  | ②「Z 为真」（即那个数值本身） | **K-L-A** | **ST-U** | 归因不成立——`K(K-L-A) = 2`，单张伪造网页给不出第二个独立簇 |

  **RT-1 的通过判据因此是三条，缺一即失败**：
  1. 对象①判 ST-V（我们没有把真实的转录误判成假）；
  2. 对象②判 ST-U（我们没有把虚假的事实断言判成 verified）；
  3. **渲染层断言**：对象① 进入正文时必须携带归因（「网页 X 称：Z」），
     **K-L-T 的 claim 永远不得以裸事实形态出现在正文里**（§9.1 的承重定义 + W-10 的 `{{claim:...}}` 解析期检查）。

  第 3 条是这个用例真正的牙齿。faithfulness 与 factuality 的区别不在 status 值上——
  「转录属实」本来就该是 verified——而在**一条 verified 的转录能许可你在正文里写什么**。
  把两者混为一谈才是「把 faithfulness 当 factuality 卖」，而混淆发生在渲染层，不在状态机里
  [E: ext-security-injection.md#RT-1]。

- **V1.7** 穷举 `S` 的输入向量空间（kind 4 值 × quote_faithful 3 值 × source_integrity 5 值 ×
  evidence_grade 6 值 × cluster_count {0,1,2,3} × budget_state 3 值 × flags 幂集的代表元），
  断言每个向量都得到唯一返回值且落在 §1.4 六值枚举内——即 `S` 是全函数（§1.5.1.2）。
  出现任何「无定义」「取决于实现」的组合即失败。

---

## §2 claim 种类（kind）

```
kind ::= data-derived | literature-cited | logically-inferred
```

### §2.1 K-D `data-derived` 数据推导

**必备工件（缺一即 ST-N）**：
1. `analysis/<claim_id>/run.py` — **单文件纯脚本，不是 notebook**，唯一输出 `out.json`（扁平 JSON），禁止在脚本里 print 结论句。
2. `analysis/<claim_id>/uv.lock` — 环境锁；`env_lock_sha256` 入 claim 记录。
3. 显式 `seed` + `PYTHONHASHSEED=0`。
4. 每个输入的 `{path, sha256}`，字节在 CAS 内。
5. `values` + `tolerance`（按字段声明相对/绝对容差）。

**判定**：在**全新临时目录**里从 CAS 按哈希重新物化输入 → `uv sync --frozen` → 沙箱禁网 → 跑 → 与 `values` 按 `tolerance` 做**数值比对**（不是字符串比对）。

**为什么不用 notebook**：papermill 2.7.0 只做参数化与执行，**根本不比对输出**；nbval 才做比对，而它的比对是 false-red 制造机——matplotlib 只比对含内存地址的文本 repr（`<AxesImage at 0x7f2cb3374198>`）、dict 顺序、时间戳、RNG 全会假失败，且**默认不做任何 sanitize** [E: ext-reproducibility.md#B1, #B2]。

**fail-closed 的六个点**（任一触发 → ST-U，并阻断该句渲染为事实陈述）[E: ext-reproducibility.md#2]：①输入 sha256 缺失或不匹配；②非零退出/超时/触发沙箱网络拒绝；③`out.json` 缺失或不符 schema；④任一数值超容差；⑤正文引用了 `out.json` 未产出的 key；⑥正文出现未被任何 claim ref 覆盖的裸数字（白名单：年份、章节号、页码）。

**范围硬限（本项目最重要的能力边界之一）**：K-D 只承接**封闭式**断言——问题由人写成一个可判定的问句 + 一个具体数据文件，agent 只负责写 `run.py`。**开放式端到端分析（选题→选方法→选口径→出结论）不得产出 ST-V。**
依据（四个基准同向，不可相减但形状一致）：DSBench 最佳 agent 34.12%；BLADE 最佳 F1 44.8%；CORE-Bench-Hard 21.48%；REPRO-Bench 最佳 21.4%。最干净的内部对照是 CORE-Bench 内部同一 agent 同一模型下 Easy 60.00% → Hard 21.48%，唯一变量是任务难度 [E: ext-reproducibility.md#F2]。
对照面：封闭式（DABstep hard）已从 2025-06 的 14.55% 涨到 2026 年多家宣称 87–100%——但该基准**已进入饱和/过拟合区间**（单一固定合成支付域、公开榜、SOTA 方法在 dev split 上蒸馏工具库；MotherDuck 另证 450 题中至少 5 题 gold 答案可证为错）[E: ext-reproducibility.md#F1]。因此这些数字只支持「封闭式足以当地基」，不支持「agent 会做数据分析」。

**必须随判定一起说出的话**：ST-V 在 K-D 上只保证「这个数字确实来自这段代码跑这份数据」，**不保证方法正确、样本代表、口径恰当**，也不保证数据本身没被投毒——重跑一万次结果都一样地错 [E: ext-security-injection.md#N7, ext-reproducibility.md#未决 8]。

### §2.2 K-L `literature-cited` 文献引证

**必备工件**：
1. 快照：`{raw_bytes_sha256, text_sha256, extractor, extractor_version, fetched_at, http_status}`，字节在 CAS 内。
2. 逐字引语 + **锚点 `anchor_span`**（快照中的真实文字跨度及其定位符）。
3. `upstream_id`（DOI / arXiv ID+版本号 / 官方域名 / 通稿原始发布机构）——用于 §5.5 的独立性归并。
4. `evidence_grade`（§3）。
5. T0 污染筛查结果 + **该注册表快照的日期**。
6. `metric_frame`（§9.4）三字段非空。

**§2.2.1 两个子模式，边界由机器判定，不由人判断**：

- **K-L-T 转录型**：claim 的**全部载重载荷**（结构化字段中的数字、命名实体、口径三元组、比较对象）能被 `anchor_span` 逐字覆盖。判定式：`normalized(claim.payload) ⊆ normalized(anchor_span)`。**可达 ST-V。**
- **K-L-A 归因型**：claim 是对 `anchor_span` 的转述、概括或蕴含。**上限 ST-A。**

之所以这个边界可以机器判定，是因为 claim 的载重载荷是**结构化字段**，不是散文句子（§0.1、§8.4 W-10）。

**§2.2.2 「这篇文献存在」与「这篇文献支持这句话」必须是两个独立字段，永不合并成一个 `verified`** [E: ext-verification-mechanisms.md#D5]。存在性可做到高精度（DOI 解析、Crossref 字段比对）；语义支持性的天花板见 §1.3。

**§2.2.3 引文层的实证基线（用于设定预期，不用于判定）**：链接可访问率 >94%、内容主题相关率 >80%，但**逐条事实核查通过率只有 39–77%**（14 个前沿模型的深度研究报告）[E: ext-citation-faithfulness.md#结论摘要-1]。同一实验的消融：GPT-5.4 从 2 次工具调用时的 78.6% 掉到 150 次时的 16.7%（跌 62 个百分点），而链接有效率与相关率在所有搜索深度上稳定在 92% 以上 [E: ext-citation-faithfulness.md#结论摘要-2]。**含义：并行度与检索深度必须与「每条 claim 的证据预算」解耦。**
另：一条陈述缺乏支持时，「多引几个源」救不回来——把全部被引源合并后再判定，**95.1% 原本不被支持的陈述仍然不被支持** [E: ext-citation-faithfulness.md#结论摘要-3]。

### §2.3 K-I `logically-inferred` 逻辑推断

**这是一个要新建的机制，不是一个要加的字段。** 前代的 `rigor_gate.py:152-153` 对未知 kind 直接 `ok=False`，任何 `kind=inference` 的行会被计为失败并把复现率拉到 100% 以下 → 门 FAIL。即前代不是「没管推断」，而是「台账里出现推断类 claim 会让论文过不了门」[E: GROUND-TRUTH-CORRECTIONS.md#C5, gt-pg-current.md#C-7]。

**必备工件（全部缺一即 ST-N）**：
1. **前提闭包**：`premises[]` 为 claim_id 列表；门校验所有前提存在、DAG 无环、且**没有一条结论挂在 `unverified` / `not_covered` / `contested` 的前提上** [E: gt-pg-current.md#I-1]。
2. **warrant（推理许可）**，取自**封闭枚举**：`deductive` / `statistical-generalization` / `causal-identification` / `analogy` / `abduction` [E: gt-pg-current.md#I-2]。不声明 warrant，推断通道会立刻退化成第二个字符数门（前代 finding `PG-F-14` 的实证）。

> **§2.3.0 编号命名空间**〔R1/F012〕：本文档集里 `F-<数字>` **专指 §7.2 词表里的 flag**。
> 引用前代（Paper Graph）或本项目历轮攻击的 finding 编号时一律加前缀：
> 前代用 `PG-`，本项目攻击轮用 `R<轮次>-`（如 `R1-F079`）。
> 不加前缀会让 V7.1 的封闭词表检查在自家文档上误判——它会把 `F-14 的实证` 当成一个 flag 引用。
3. **强度不超过最弱前提**：模态/量词降级检查。前代的精确失效是：前提被诚实地放宽了，结论句却原封不动 [E: gt-pg-current.md#I-3]。
4. **口径可比性**：前提之间的 `metric_frame` 必须可比，否则「每个数字都对、拼起来是错的」会被 100% 复现率背书 [E: gt-pg-current.md#I-4]。
5. **独立再推导 + 反例构造记录**：复核者（reviewer ≠ producer，身份取自 harness，§5）独立从前提推一遍，**必须提交反例搜索记录**——找不到反例也要记录搜索过程与预算 [E: gt-pg-current.md#I-5]。
6. **变更传导**：前提变更 → 依赖它的推断结论自动置 `stale` 并重判 [E: gt-pg-current.md#I-7]。

**§2.3.1 K-I 永不可达 ST-V。**〔裁定〕
**理由**：文献里这条赛道没有可用机制。Toulmin warrant 有无检测的加权 F1 0.88 来自**教育对话语料、传统 ML 分类器**，是域外指标，且只判 warrant 有无、不判 warrant 是否成立 [E: ext-verification-mechanisms.md#M14]。更重的教训是 ARCT：BERT 峰值 77%（仅比未受训人类基线低 3 个点）被证明**完全由数据集中的伪统计线索解释**，在对抗集上退化到随机 [E: ext-verification-mechanisms.md#M15]。把「有界反例搜索在预算内失败」直接当成真值，就是重演这个 Clever Hans。
**什么会推翻**：若我们自建的反例搜索器在一个**带已知反例的金标集**上达到可报的召回率，且该结果被跨厂商独立复算（§5.2），则可为 K-I 开一个独立的最高档，并在本文件新增一个 status 值。在那之前，K-I 的最高档是 ST-A。

### §2.4 kind × 可达状态矩阵（规范表）

| kind | ST-V | ST-A | ST-E | ST-C | ST-U | ST-N |
|---|---|---|---|---|---|---|
| K-D 数据推导（封闭式） | ✅ | — | — | ✅ | ✅ | ✅ |
| K-D 数据推导（开放式端到端） | ❌ | ✅ | — | ✅ | ✅ | ✅ |
| K-L-T 文献转录 | ✅ | ✅ | — | ✅ | ✅ | ✅ |
| K-L-A 文献归因 | ❌ | ✅ | — | ✅ | ✅ | ✅ |
| K-I 逻辑推断 | ❌ | ✅ | — | ✅ | ✅ | ✅ |
| 任意 kind + 图形读数数值 | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |

### §2.5 可检验断言

- **V2.1** 不存在 `kind` 值在三值枚举之外的 claim；不存在 `kind == logically-inferred` 且 `status == verified` 的 claim。
- **V2.2** 每条 K-D claim 的 `analysis/<id>/` 下同时存在 `run.py`、`uv.lock`、`out.json`，且不存在 `.ipynb`。
- **V2.3** 每条 K-I claim 的全部 `premises` 在台账中可解析、构成 DAG、且无一条前提的 status ∈ {unverified, not_covered, contested}。
- **V2.4** 每条 K-I claim 的 `warrant` 落在五值封闭枚举内，且 `inferences/<id>.md` 的反例搜索记录段非空（含「未找到反例 + 搜索预算」的显式记法）。
- **V2.5** 负向门（red-first）：向重跑门喂一个伪造 metric、无 transform、无原始数据的 claim，门必须非零退出。前代同样的构造得到 `exit 0 PASS` [E: GROUND-TRUTH-CORRECTIONS.md#C1]。
- **V2.6** 对每条 K-L claim，`normalized(payload) ⊆ normalized(anchor_span)` 的判定结果与其 `sub_mode`（T/A）一致。

---

## §3 证据等级（evidence_grade）— 获取层级维度

### §3.1 为什么需要这一维

v1 缺失该维度。中文场景下「拿到全文」经常不可能，英文场景下也远非常态。没有这一层，系统会把「我看到了标题」伪装成「我核对了结论」[E: ext-chinese-ecosystem.md#设计含义-2]。

### §3.2 实测的可得性上限（口径三元组齐全）

全部为 2026-08-17 对 OpenAlex API 的实测，**默认口径（排除 XPAC 扩展语料）**：

| 指标 | 值 | 占默认口径 324,389,590 的比例 |
|---|---|---|
| works 总数（默认口径） | **324,389,590** | 100% |
| works 总数（`?corpus=all`，含 XPAC） | **516,949,125** | — |
| `is_oa:true` | **123,672,025** | **38.1%** |
| `has_content.pdf:true` | **54,999,764** | **17.0%** |

[E: ext-academic-apis.md#A9, #A10, 核验表 #10/#11/#13/#14]

**口径警告（必须随数字复述）**：任何「OpenAlex 收录 N 篇」的说法，不写明 corpus 口径即为口径失真；网上流传的「250M 篇」是更早期的第三个口径，标 `unverified`，禁止使用 [E: ext-academic-apis.md#核验表 #12]。

**推论（本文件的推论，非测量）**：G5 的真实上限**低于** 17.0%，因为 OpenAlex 内容档案的 `grobid_xml_id` 可能为空——官方明说 "GROBID can't parse every PDF" [E: ext-academic-apis.md#A7]。该损耗量级未测量。

**结论**：「每条论断都可追溯到原文」这个承诺，在现实中最多覆盖约六分之一的文献。这必须写进产品承诺，而不是留给用户发现。
**〔口径 · R1 provenance 轮更正〕** 原文写的是「英文文献」，一手语料**没有「英文」二字**：17.0% 的分母是 OpenAlex **全语种**默认口径 324.4M（OA 占 38.1%、有缓存 PDF 仅 17.0%）。英文子集的该比例本轮从未测量，**不得把 17.0% 搬到英文子集上**——同源另测得 `language:zh` 仅 1.56%，说明中英分布极不均 [E: ext-academic-apis.md#D6]。

### §3.3 等级定义

| 级 | 标识 | 定义 | 典型获取路径 |
|---|---|---|---|
| **G5** | `fulltext+anchor` | 全文快照在手，且 claim 载荷有**稳定可复核的定位符**（TEI/JATS 结构节点、LaTeX 源、HTML 锚） | OpenAlex content API `.grobid-xml`；Europe PMC JATS；arXiv LaTeX 源；出版社 HTML |
| **G4** | `fulltext` | 全文快照在手，但无稳定锚（整篇 PDF 抽取文本） | OpenAlex `.pdf` → 本地解析；`best_oa_location.pdf_url`；用户自备 PDF |
| **G3** | `abstract` | 仅标题 + 摘要 | OpenAlex 语义检索命中、Crossref 摘要、中文库摘要 |
| **G2** | `metadata` | 仅题录（题名/作者/年/刊/DOI） | Crossref/OpenAlex 元数据、中文库题录 |
| **G1** | `snippet` | 搜索引擎返回的片段；无快照，或快照不含 claim 所需段落 | serper / bocha 结果条目 |
| **G0** | `none` | 无任何可复核工件 | — |

### §3.4 硬规则：等级 → 允许的最高状态

| evidence_grade | 允许的最高 status | 依据 |
|---|---|---|
| G5 | ST-V | 锚点使「独立复核寻址」成为可能 |
| G4 | **ST-A** | 逐字包含仍可判（`quote_faithful` 可为 `pass`），但无锚点 → claim 载荷与段落的绑定不可独立复核 |
| G3 | **ST-A，且仅限「关于摘要内容本身」的断言** | OpenAlex 语义检索**只检索标题+摘要**，用它做「这篇论文是否支持某结论」会系统性漏掉只在正文/结果节里出现的证据 [E: ext-academic-apis.md#A6] |
| G2 | **仅存在性断言**；**不得支撑任何数值断言** | [E: ext-chinese-ecosystem.md#设计含义-2 L1] |
| G1 | **不得作为任何 claim 的承重证据**，只能是 `candidate`（§9.6） | 见 §3.4.1 |
| G0 | ST-N | — |

**§3.4.0 `evidence_grade` 还要再过一道正交约束**：`retention_tier`（§8.6）。前者是「我拿到了多少」，后者是「我被允许留多少」。耦合规则见 §8.6.2；两者的下限取交集。

**§3.4.1 为什么 snippet 一票否决。** ①片段级检索在语义上无法支撑句子级断言（片段是检索系统截出来的，不是作者的论证单元）。②片段是 SERP 摘要投毒的直接载体：单个投毒 URL + 约 13 词文本，在被曝光条件下拿到 38–51% 的提及率 [E: ext-security-injection.md#V9, #V10]。③片段没有快照可复核，`source_integrity` 无法计算。

**§3.4.2 G5 门槛比「字符串包含」更严，这是故意的。** 决定图表/表格类证据成败的头号失效模式是「判对了结论、指错了格子」：GPT-4o 在 SciTabAlign 上标签 Macro-F1 88.4，恢复关键单元格的 Macro-F1 只有 **34.8**，且在 exact-match 设定下**没有任何模型能让「标签+依据同时正确」超过 50%** [E: ext-multimodal-evidence.md#E2, #29/#31]。含义：「结论正确」这一信号对「依据正确」几乎没有预测力。因此 ST-V 要求一个可被**只看地址、不看结论的独立复核者**重新取值的锚点。

### §3.5 图形派生数值：强制 ST-E

任何数值来自图形几何读数的断言，`base` 强制为 ST-E，必须携带 `epsilon` 与 `method`，且**禁止参与任何比较、排序、阈值判断**——只允许出现在描述性叙述里，并必须原样显示 ε。

**数字依据**：有印刷数据标签时 MAPE 1.3%–1.8%，去掉标签后升到 7.2%–7.4%（同一模型 Gemini 2.5 Flash、同一批 50 张 Vega-Lite 图，只改标签）[E: ext-multimodal-evidence.md#11/#12]。分族 Adaptive MAPE：scatter 2.63 / bar 3.78 / line 4.35 / **pie 11.58 / radar 28.01** [E: #14]。8% 的误差足以翻转「A 优于 B」这类比较结论。

**图族黑名单（通用 VLM 一律禁用，必须路由到专用管线或人工）**：雷达/极坐标、饼/环形、堆叠柱、稠密多线/序列重叠、对数轴/断轴/双 Y 轴、面积/体积/3D [E: ext-multimodal-evidence.md#D3]。最后一项属未测量区，按最坏假设处理。

**优先级**：先绕开图表——同一数值若在正文/表格/附录/作者数据仓库中存在，走那条路 [E: ext-multimodal-evidence.md#D2 P0]。

### §3.6 中文来源的获取分层（与 G 级的映射）

| 中文层 | 内容 | 映射 |
|---|---|---|
| **CN-T3** | 用户自备 PDF、OA 全文、NCPSSD、ChinaXiv、期刊官网 OA | → G4；解析出稳定锚则 G5 |
| **CN-T2** | 摘要（OpenAlex / 万方 / 维普） | → G3 |
| **CN-T1** | 题录（题名/作者/年） | → G2 |

**中文能力的实测缺口（全部 2026-08-17 实测或一手论文口径）**：

- OpenAlex `language:zh` = **5,059,316 / 324,389,590 = 1.56%**；`language:zh-cn` 只返回 16,356（**错代码陷阱**：用错代码得到一个「看起来正常」的小结果集而非报错）[E: ext-chinese-ecosystem.md#B]
- 中文年产出断崖：2015 年 309,668 → 2023 年 30,177（为 2015 年的 9.7%）[E: 同上]
- 刊级：2023 版北大核心 1,987 种中 OpenAlex 收录 **734 种（37%）**；篇级 1,545,929 / 6,453,244 = **24%**。**口径警告：24% 的分母是万方数据，不是「全部中文论文」，且该论文第四作者供职于北京万方数据股份有限公司、论文自陈选择万方部分因该作者「职务与资源便利」——分母的选择存在利益相关，引用时必须写明「以万方为基准」** [E: ext-chinese-ecosystem.md#核验表, 口径警告 1]
- References 完整率 **7%**（论文口径）/ 随机抽样 `refs>0` 仅 **2%**（`sample=100&seed=42`）→ **引文滚雪球在中文场景基本失效，必须关闭该策略** [E: ext-chinese-ecosystem.md#设计含义-4]
- 《管理世界》《中国社会科学》《历史研究》三个 ISSN 在 OpenAlex `sources` 与 Crossref `journals` 中**命中均为 0** → 以 ISSN/DOI 为主键的检索流水线对最权威的中文期刊会**静默返回空，而不是报错** [E: ext-chinese-ecosystem.md#结论摘要-4]
- `language` 字段本身不可信：有语言标注的中文刊论文中仅 5% 标为中文、**92% 标为英文** → 条目语言必须由本系统按题名字形（CJK 比例）判定后写入 [E: ext-chinese-ecosystem.md#B, #设计含义-3]

**硬规则**：知网/万方/维普全文均为机构订阅 + 反爬，**本系统不得设计任何绕过订阅墙的抓取路径** [E: ext-chinese-ecosystem.md#G]。中文文献的验证能力受限必须由系统**主动声明**，不得静默用英文文献充数 [E: ext-academic-apis.md#D7]。

**§3.6.1 一条方法论级的自查教训（必须固化为规则）**：同一条件下用 OpenAlex 默认排序取前 50 条得到 DOI 46/50、refs 25/50；改用随机抽样得到 DOI 70%、refs 2%——**差 1–2 个数量级**。OpenAlex 默认排序偏向高被引/元数据齐全记录，**默认分页 ≠ 随机样本** [E: ext-chinese-ecosystem.md#B]。任何用 API 分页结果做的比例估计都必须声明抽样方式。

### §3.7 可检验断言

- **V3.1** 不存在 `evidence_grade == G1` 且被列为某条 claim 承重证据的记录。
- **V3.2** 不存在 `evidence_grade ≤ G4` 且 `status == verified` 的 claim。
- **V3.3** 不存在 `evidence_grade == G2` 且 claim 载荷含数值的记录。
- **V3.4** 每条 `status == estimated` 的 claim 都携带非空 `epsilon` 与 `method`，且不被任何比较/排序/阈值类 claim 引用为前提。
- **V3.5** 任何以「N 篇 / 占比」形式出现的外部库统计，其记录中必须含 `corpus` 口径字段与 `as_of` 日期。
- **V3.6** 中文任务的运行清单中，`citation-snowball` 策略处于关闭状态；`language` 字段来源标记为 `self-computed`，不是 `upstream`。

---

## §4 写权矩阵 — 每个工件恰好一个物理写者

> 上一轮最大的缺陷类是跨文档漂移，而写权是漂移的震中。本节穷举，不留「等等」。

### §4.1 不变量（原文，可逐字引用）

> **I-W1 · status 是由门代码计算的，从不由 agent 断言。** 系统中不存在任何一条从 agent 输出到 `status` 字段的写路径。
>
> **I-W2 · 一个工件，一个物理写者。** 若两类主体都需要向同一逻辑记录写入，则该记录**必须拆成两个物理文件**。
>
> **I-W3 · 强制点落在工具边界，不落在网络边界。**

### §4.2 矩阵

| # | 工件 | 唯一物理写者 | 其他主体的权限 | 依据 |
|---|---|---|---|---|
| W-01 | `objects/<sha256>`（CAS：快照原始字节、抽取文本、run 输出） | **我们自建的检索/抓取工具执行器**，在同一次工具执行内写入 | 只读 | 落库 `tool/result` 存的是**截断后**内容；超阈值纯文本结果原文不在日志里 [E: GROUND-TRUTH-CORRECTIONS.md#A2, gt-evidence-substrate.md#E4]。且工具的 canonical value 是 execution-local、不进持久日志 [E: gt-exec-security.md#H-2] |
| W-02 | `tool/result.data.meta.evidence`（抓取锚点：`object_sha256/url/retrieved_at/http_status/bytes/extractor_version`） | **同一个工具执行器的返回值** | 不可写 | 唯一零风险落点：模型不可见、被 pruner 完整保留、被持久化逐字保留、事件类型已知不影响 resume [E: GROUND-TRUTH-CORRECTIONS.md#A1/#E2, gt-evidence-substrate.md#B8/#D4] |
| W-03 | `claims/<id>.json`（**内容**：kind、结构化载荷、metric_frame、证据指针、premises、tolerance） | **producer agent**，经 claim 提交工具，schema 硬校验 | 门只读 | — |
| W-04 | `claims/<id>.status.json`（**status 及全部派生字段**：status、evidence_grade、independent_cluster_count、**nominal_source_count**、counter_evidence_*、computed_at、gate_version、inputs_hash） | **门代码（确定性脚本）** | 任何 agent 不可写；提交工具的 schema **不含** status 字段，出现即 `tools/pre-execute` deny | I-W1、I-W2；前代 `reproduced` 列门既不读也不写，「门的输出才是记录」只兑现在旁路文件里，台账本身永远停在 `?` [E: gt-pg-current.md#C-8]。**`nominal_source_count` 于本轮补入**：写者是门代码（03-EVIDENCE-ENGINE 的 **G-CLUSTER**，与 `independent_cluster_count` **同一写者、同一行为**——同门产出、同门写入、该门自己不做任何降级动作），补入理由是 §5.5 R-I6 要求它与独立簇数**并排展示**，不补则渲染层拿不到这个数。**`cluster_map` 不随之进入 W-04**：它体量大且只用于审计与人审队列，落在 `gate-reports/<run_id>/G-CLUSTER.json`（W-08） |
| W-05 | `ledger/`（per-claim manifest，append-only） | **门代码** | 只读 | — |
| W-06 | `evidence/<evidence_id>.json`（证据卡；id = `sha256(work_id ‖ version_id ‖ locator ‖ normalize(quote) ‖ extractor_version)`） | **抓取工具执行器** | 只读 | 按**来源坐标**内容寻址 → 并行写入天然幂等、去重不需要 embedding、**矛盾在构造上不可能被去重门吃掉** [E: ext-evidence-schema.md#结论摘要-7] |
| W-07 | `verdicts/<gate>/<claim_id>.json`（Class-2 裁决原件，含 `childId/provider/model/prompt_hash/ts`） | **裁决 subagent 自身** | 门只读；裁决是门的**输入**，不是 status | §5、§6 |
| W-08 | `gate-reports/<run_id>/<gate>.json`（含 `generator_version` + `inputs_hash` 自证签名） | **门代码** | 只读 | 前代四份 gate_report 无法从工作树区分「生成的」与「手改的」→ 门产物必须携带自证签名 [E: gt-pg-current.md#未决-3] |
| W-09 | `registries/*`（撤稿库 / 劫持刊表 / 指纹词典）及其 `.meta.json`（含 `snapshot_date`） | **注册表同步器**（独立的确定性脚本） | 只读 | T0 全部做成本地索引，扇出子 agent 不打网络 [E: ext-literature-integrity.md#设计含义-4] |
| W-10 | `prose/`（成稿） | **确定性组稿器** | 作者 agent 写 outline 与叙述骨架，**不写数字** | 正文数字一律写成 `{{claim:<id>.<field>}}`，渲染期解析；解析不到 → 构建失败。这把「口径漂移」从人的自律问题变成编译期错误 [E: ext-reproducibility.md#2] |
| W-11 | `inferences/<claim_id>.md`（warrant、前提、反例搜索记录） | **producer agent（正文段）+ 复核 subagent（再推导段）** —— 两段是**两个物理文件**，`.producer.md` 与 `.reviewer.md`，由门合并渲染 | 互不可写 | I-W2；否则「独立再推导」在文件层就没有独立性 |
| W-12 | `runs/<run_id>/manifest.json`（运行时指纹：`sandbox/mode` 有效值、`approval/policy` 有效值、`result.sandbox.{mode,enforcement}`、每条证据的 `tool/call` callId、`tool/code-dispatch` 的 `<parent>:code:<n>` id、web search provider id） | **编排层** | 只读 | [E: gt-exec-security.md#H-7] |
| W-13 | `budget/`（用量与预算账） | **编排层**，由 session 日志 fold 出 per-step `{turn, step, inputTokens(仅未缓存), cacheReadTokens, cacheWriteTokens?, outputTokens, reasoningTokens?}` | 只读 | per-step 分解**在日志里**，v1 的「读不到」结论只对 tokenMeter 服务成立 [E: GROUND-TRUTH-CORRECTIONS.md#A5, gt-evidence-substrate.md#F3] |
| W-14 | `flags[]` | 见 §7 逐 flag 的 setter | — | — |
| W-15 | git 提交 | **orchestrator，且只在 gate 时提交一次** | 子 agent **永不碰 git** | 消灭 git index 锁竞争 [E: ext-reproducibility.md#2] |
| W-16 | `claims/<id>.quote-repair.json`（近似命中时快照里的真实跨度 + 其字节偏移） | **门代码（GC-0 引语门）** | producer **只读**；producer 只能据此改自己的 `claims/<id>.json`（W-03）后重新提交 | 门给建议、不改被检查对象。若门可直接改 claim，`quote_faithful` 的 `pass` 就不再是「producer 写对了」而是「门帮他写对了」〔裁定 · R1/C-3〕 |

### §4.3 「预算按总量记账」的正确理由

保留 v1 的结论（预算按总量 token 记账，不套缓存折扣公式），但**必须改写理由**：理由是 **DSH 不持有 provider 价目表**，不是「运行时读不到缓存分解」。后者已被一条 `grep usage` 证伪 [E: GROUND-TRUTH-CORRECTIONS.md#A5]。
配套：预算 gate 用 `ctx.tokenMeter.measure()`（与 compaction 同源，不会打架），但它是 4 字符/token 的固定启发式、**对 CJK 与 JSON schema 系统性低估**，不能用作账单口径 [E: gt-evidence-substrate.md#预算与成本记账]。

### §4.4 写权是审计契约，不是文件系统权限（必须诚实写出）

我们**不能**用沙箱强制写权。一手事实：
- 内核沙箱只管文件效应，**不拦网络**；`run_code` 同样不设防，且它**同时绕过**内核沙箱（只管 bash）**和** `ctx.fs` 策略围栏（只管 ctx.fs 工具）[E: GROUND-TRUTH-CORRECTIONS.md#A7, gt-exec-security.md#D]。
- 子代理**不继承**父的沙箱限制作为下限：只捕获父会话的**显式** override，从不捕获部署默认，也不捕获一次性授权 [E: GROUND-TRUTH-CORRECTIONS.md#A8]。
- `toolFilter` **不是权限天花板**，且不向下传递 [E: gt-exec-security.md#B]。

**因此强制手段只能是三层，全部落在工具边界**：①`ctx.tools.guard` 单调否决（无法被后续 listener 翻回允许）；②`tools/pre-execute` 的 `deny`；③`tools/post-execute` 的 `block(feedback)` [E: gt-exec-security.md#H-1]。
**并且必须配一条产物级兜底**：**任何未被 `tool/call` / `tool/code-dispatch` 事件覆盖的断言，一律 `not_covered`。**

### §4.5 并行写入的安全性来源

- CAS 写入：`write tmp/<uuid>` → `os.replace objects/<sha256>`，POSIX rename 原子性 + 相同内容写入天然幂等 [E: ext-reproducibility.md#C1]。
- 一 claim 一文件：消灭合并冲突。
- **不引 DVC / DataLad / git-annex**：见 §8.3 D-8.3。
- **并行的是多个 session（fork/subagent），不是同一 session 的多写者**：DSH 明确「One live writer per session」且跨进程无互斥 [E: gt-evidence-substrate.md#H5, #未决-8]。
- 兄弟委派的工作区副作用协调是**模型的责任**（`dsh-tool-subagent` README 原话），所以多 worker 同时写证据库必须靠内容寻址 + 原子写，不能靠 agent 自律 [E: gt-exec-security.md#H-3]。

### §4.6 可检验断言

- **V4.1** 负向测试：模拟 producer agent 在 claim 提交工具的参数中携带 `status` 字段，**该调用必须被拒绝**，且 session 日志中存在对应的 `tools/pre-execute` deny 记录。「被拒绝」而非「被覆盖」是硬要求——覆盖会让尝试不可见。
- **V4.2** 对 `claims/*.status.json`、`ledger/`、`gate-reports/` 的全部历史写入，其写入者必须在 `checks/` 白名单内（通过文件 mtime + 门自证签名 `generator_version`/`inputs_hash` 交叉验证）。
- **V4.3** `prose/` 渲染产物中，正文的每一个数字都能反解到一个 `{{claim:<id>.<field>}}` 占位符；裸数字扫描（白名单：年份、章节号、页码）命中数为 0。
- **V4.4 live 幂等断言**：同一批输入连续跑两次，第二次的 `accepted == 0`。**本仓库既有流水线从未 live 断言过幂等**（`harvest_e2e.sh` 的 run-2 从不断言，实测 run-2 accepted=8；幂等只在离线单测里被证过）[E: GROUND-TRUTH-CORRECTIONS.md#D2]——这条必须补上。
- **V4.5** `runs/<run_id>/manifest.json` 中若 `sandbox/mode == danger-full-access`，该次运行的全部产物必须被标记为「权限异常，需人工复核」[E: gt-exec-security.md#H-6]。
- **V4.6** 不存在任何 `evidence` 记录其 `object_sha256` 在 CAS 中不存在，或其 `tool/call` callId 在 session 日志中查无此事。

---

## §5 身份与独立性

### §5.1 身份的唯一来源是 harness，不是自报字段

DSH 持久化下列字段到 session header，它们是**机器事实，不是自报字符串**：`parentSession` / `seedLength` / `delegationDepth` / `origin:'subagent'` / `agentPreset`（实测 header 样本含全部字段）[E: gt-evidence-substrate.md#其它可直接使用的原语]。子代理的返回句柄是 harness 分配的 `subagentId`；后台上报带 `source {kind:'subagent-report', senderSessionId}` [E: gt-orchestration.md#C, gt-orchestration.md#K]。

**规则 R-I1**：一切独立性判定使用 harness 侧的 `childId` / `sessionId` / `parentSession` 链；**不得取 manifest 里的自报字段** [E: gt-pg-current.md#I-5]。前代把「独立性」完全交给 prompt 措辞（Cartographer 的 "Do not read the draft…" 写在 prompt 里，零机械强制），结果是**该角色在审计上不存在**——无法从工件判断 positions.md 是独立产出还是 orchestrator 顺手写的 [E: gt-pg-current.md#C-9, #未决-5]。

### §5.2 跨厂商独立性可在脚本内声明

一手代码事实：workflow 脚本的 `agent(prompt, opts)` 支持**五个**选项——`label, phase, schema, provider, model`（`SUPPORTED_AGENT_OPTIONS`）[E: GROUND-TRUTH-CORRECTIONS.md#A11/#E1, gt-orchestration.md#D3]。另一条通路是部署期的多实例 `dsh-tool-subagent`，各带自己的 `agentOptions.{provider, model, maxTokens}` 与不同 `toolName` [E: gt-orchestration.md#D]。

**§5.2.1 必须消歧的同名概念（写错会让整份文档自相矛盾）**：
- `agentOptions.provider` = **LLM 路由**（deepseek-official / anthropic / …）。**可以 per-call 指定。**
- `WorkflowStartRequest.subagentProvider` = **subagent 传输后端**（spawn / fork / …）。作用于整个 run，脚本不可见。
`dsh-workflow-worker-thread` README 的 Script contract 段落漏列了 `provider`；README `:44` 那句 "Provider choice applies to every child in that run and is not visible to the script" 说的是后者 [E: gt-orchestration.md#X4]。

**规则 R-I2**：任何写入 ST-A 的 Class-2 裁决，其 `verdict.provider` 必须与 producer 的 provider **不同**，且该值取自编排脚本传入的 `agentOptions.provider`、并与 `runs/<run_id>/manifest.json` 的运行时指纹交叉校验。
**理由**：self-preference 的机理是**低困惑度偏好**（LLM 系统性给低困惑度文本更高分，与是否自己生成无关），同族/同厂商互评会系统性放大该偏置 [E: ext-evaluation.md#C2]。注意：GPT-4 的 self-preference 统计量 0.520 是 2024 年模型的测量，**数值已陈旧、机理性结论仍可用** [E: ext-evaluation.md#21, #未决-4]。

### §5.3 producer ≠ reviewer 的机械定义

**规则 R-I3**：`reviewer.childId ≠ producer.childId`，**且** reviewer 会话不得包含 producer 的自由文本。实现上：取证/裁决子代理必须走 `spawn`（零父历史）而非 `fork`（带父已完成回合前缀）[E: gt-exec-security.md#H-3]。

**规则 R-I4（局部消息传递）**：并行子代理之间只交换**结构化证据卡 + 快照 id**，禁止自由文本回传；协调者不把子代理的自由文本直接拼进自己的上下文。
**依据**：局部消息传递比全局消息传递 ASR 低约 20%，且非自复制注入在局部模式下 "struggle to compromise more than two agents"（5–6 智能体串行链 + 10–50 智能体社会模拟）[E: ext-security-injection.md#V26]。

**规则 R-I5（深度）**：出厂 `maxDepth: 3` → root(0) → 子(1) → 孙(2) → 曾孙(3)，第 4 层被拒 [E: gt-orchestration.md#C1]。角色分配必须在三层内闭合：协调者(0) → 领域 worker(1) → 验证 worker(2)。若设计需要「验证者再派攻击者」，必须显式提高 `maxDepth` 并记录该决定。

### §5.4 独立性是审计属性，不是隔离属性（必须写清楚）

reviewer ≠ producer 保证的是「这份裁决出自另一个上下文、另一个厂商的模型」，**不保证** reviewer 未被注入、不保证 reviewer 无法访问 producer 的产物目录（§4.4：沙箱不拦网络、run_code 绕过围栏、toolFilter 不是权限天花板）。任何把独立性表述为隔离性的文字都是回归。

### §5.5 来源独立性：按上游簇归并，不按 URL/域名

**规则 R-I6**：每条证据必须携带 `upstream_id`；`independent_cluster_count` 按 `upstream_id` 去重后计算；报告中必须**同时**展示「名义来源数 / 独立簇数」——这两个数的规范字段名分别是 **`nominal_source_count`** 与 `independent_cluster_count`，两者同为 W-04 的派生字段、同由 G-CLUSTER 写入。

**已知的硬样本（可直接做回归用例）**：
- **Unpaywall = OpenAlex 同一后端**。OpenAlex 官方明说 "Unpaywall records are served from the same OpenAlex data"，实测返回体中 `evidence` 与 `updated` 字段值已 literally 变成 `"deprecated"`。把「两个源都说是 OA」记为 2 票，实际只有 1 票 [E: ext-academic-apis.md#G, #D4]。
- **11 个中文域名 = 1 条日经**（腾讯新闻/IT之家/大公网/虎嗅/科普中国/光明网/人民网教育频道等，全部回溯到 Nikkei Asia 同一上游）[E: ext-security-injection.md#E3]。这条有现成 ground truth，应作为固定回归用例。
- **8 个域名 = 1 篇 BadRAG**（arunbaby.com / colrows.com / deepchecks.com / newline.co / instatunnel / 多个 Medium/LinkedIn 复述同一篇论文）[E: ext-security-injection.md#A3]。
- **`zotero-chinese/styles` 的大量 fork** 全是同一份 GB/T 7714—2015 派生物 [E: ext-chinese-ecosystem.md#A]。
- **Feet of Clay 的数字**：作者本人 2025-01-29 写的是 764,000+，多个二手站转载后变成「110 万篇 / 1.2 万篇撤稿研究」——是一个源，不是三个源 [E: ext-literature-integrity.md#设计含义-6]。

**归并键的优先级**：DOI > arXiv ID（**必须带 `vN` 版本号**——arXiv 官方确认「替换版本不生成新 DOI」且 DOI 永远指向最新版，所以裸 DOI 在语义上是「未来某个版本」）[E: ext-evidence-schema.md#结论摘要-4] > 官方域名 > 通稿原始发布机构 > (核心数字, 核心实体, 首次出现时间) 三元组聚类 [E: ext-security-injection.md#D3]。

**§5.5.1 已知的上游继承关系（必须显式建模，否则会重复计票）** [E: ext-academic-apis.md#D4]：
- Crossref → OpenAlex（但 Crossref 对**DOI 存在性与注册元数据**仍是唯一权威，在该维度上它是独立的）
- OpenAlex content archive 的 TEI ← GROBID（解析错误会被继承，不是独立读取原文）
- Semantic Scholar / OpenAlex 都大量吸收 Crossref + arXiv

**§5.5.2 模糊身份解析可以提议合并，绝不能自动执行合并。** bioRxiv 生产系统用标题匹配做 preprint→VoR 关联，作者手工复核 120 篇「未发表」预印本，发现 **37.5% 其实已经发表**——一个生产级模糊匹配器把一个统计量搞错了约 25 个百分点 [E: ext-evidence-schema.md#结论摘要-6]。

### §5.6 可检验断言

- **V5.1** 每条 `status == attributed` 的 claim，其 `verdicts/` 记录中的 `provider` ≠ producer 的 `provider`，且两者的 `childId` 不同。
- **V5.2** 每条裁决记录的 `childId`、`provider`、`model` 可在 session 日志 / run manifest 中被独立复核；不存在只出现在裁决文件里的自报身份。
- **V5.3** 回归用例 RT-2/RT-3：给定 11 家中文媒体转述同一条日经的真实链路，`independent_cluster_count` 必须归并为 **1** [E: ext-security-injection.md#RT-2, #RT-3]。
- **V5.4** 回归用例：给定同时引用 Unpaywall 与 OpenAlex 的 OA 状态断言，`independent_cluster_count` 必须为 **1**。
- **V5.5** 全部裁决/取证子代理的启动记录中 `provider`（传输后端）为 `spawn`；不存在 `fork` 启动的裁决者。
- **V5.6** 全部子代理的 `delegationDepth ≤ 3`（或等于本 profile 显式配置的上限）；越界即失败。
- **V5.7** 所有跨子代理的回传载荷都符合结构化证据卡 schema；不存在自由文本回传路径（对协调者上下文做一次结构扫描）。

---

## §6 门的分级（gate class）

> 语料中「deterministic」一词被用于三件不同的事。本节把它们钉死，任何文档不得再含混。

### §6.1 三个类

| 类 | 标识 | 定义 | 可以判什么 | 不可以判什么 |
|---|---|---|---|---|
| **Class-0** | GC-0 | **离线确定性**：无网络、无模型，输入全在本地 CAS / 注册表快照内 | ST-V、ST-U、ST-N | 任何需要外部实时状态的事 |
| **Class-1** | GC-1 | **联网但算法确定**：需要外部数据源，判定函数本身无模型 | ST-V、ST-C、ST-U、ST-N | 语义支持性 |
| **Class-2** | GC-2 | **消费 LLM 裁决**：门本身是确定性聚合器，但**输入含模型判断** | **最高 ST-A**；以及向下的 ST-C / ST-U / ST-N | **永远不得写 ST-V** |

### §6.2 GC-0 的成员（示例，非穷举）

`quote_faithful` 归一化匹配；`source_integrity` 的哈希部分；schema 完整性；`metric_frame` 三字段非空；K-I 的 DAG 无环与前提闭包；重跑门的数值容差比对；正文裸数字扫描；GRIM / GRIMMER / DEBIT；statcheck 式重算；PPS 指纹词典本地匹配；boot 门。

**§6.2.1 GC-0 的门必须把「适用条件」与「结论」一起输出。** 这是本轮最重要的方法论收获：GRIM 的检出功率有闭式解 `power = max(0, 1 − N·items / 10^d)`，且已用 20,000 次/点的蒙特卡洛验证（N=28 实测 0.718 vs 理论 0.720；**N ≥ 100 且 d=2 时功率恒为 0**）[E: ext-literature-integrity.md#E1]。因此门的输出不是 `pass/fail`，而是：

```
{ test: "GRIM", verdict: "consistent" | "inconsistent" | "not_applicable",
  power: 0.72, N: 28, items: 1, decimals: 2, caveats: [...] }
```

一个 `power: 0.00` 的 "consistent" 与一个 `power: 0.90` 的 "consistent"，证据强度差一个数量级。**丢掉 power 就是在制造假安全**——和我们要消灭的假 `verified` 是同一种病。功率为 0 时输出 `not_applicable` → ST-N，**不是** 通过。

**§6.2.2 statcheck 类的准确率必须带真实口径。** 常被简写为「statcheck 准确率 ~99%」的那个 96.2%–99.9% 区间，真实基础是 **48 篇文章 / 1,120 条人工编码 NHST 结果**，且只统计**完整 APA 格式的 t/F/χ² 且 p<.05**，并且**只在「人工与 statcheck 都抽到」的交集**上计算——而抽取召回率只有 **61.1%–61.2%** [E: ext-literature-integrity.md#E5]。现场画像更刺眼：20 篇文章 737 条 NHST 中 113 条被标记，其中 14 条是抽取错误、**64 条（57%）源于统计校正** [E: 同上]。
**规则**：statcheck 类命中若文中出现 Bonferroni / Greenhouse-Geisser / Huynh-Feldt / Scheffé / Tukey 关键词，自动降级为 F-19（§7），不参与状态降级。

**§6.2.3 GRIMMER test 3 的上游已知误报未修复**（scrutiny 0.6.1 的 vignette 仍带该警告）→ 由 test 3 触发的结果单列为 F-20，不参与自动降级 [E: ext-literature-integrity.md#E2, #未决-7]。

**§6.2.4 SPRITE 不是门。** 它自述为 "a heuristic method for reconstructing plausible samples"，产出的是「与报告统计量相容的可能数据集」，给人看的反例分布。**把它接进自动门是范畴错误** [E: ext-literature-integrity.md#E4]。

### §6.3 GC-1 的成员与硬要求

成员：DOI 解析；Crossref / OpenAlex 字段比对；Retraction Watch 命中；劫持刊 ISSN/域名匹配；URL 存活 + Wayback 存档比对；快照重取后的 hash 比对。

**硬要求**：
1. **每个输出必须携带其数据快照日期与源标识**。RW 仓库 README 自带 `generated on YYYY-MM-DD`，GitLab API 有 `last_activity_at`，PPS 页面有 `Last Update` 戳，Hijacked 表格表头有 `last updated` [E: ext-literature-integrity.md#设计含义-3]。
2. **超龄即降级为 ST-N，不是通过**。建议阈值：RW > 7 天、PPS > 30 天、Hijacked > 90 天。
3. **绿灯的语义是「截至某日无记录」，不是「干净」**。RW 的 EoC/Correction 覆盖据其 README 自述**不完整**——不能拿 RW 的 EoC 缺失当「该文没有 EoC」的证据 [E: ext-literature-integrity.md#A1, #未决-5]。
4. **T0 名录全部本地化**：下载一次、本地查 N 次；扇出的子 agent 不打网络。这是超并行扇出时唯一不会被限速掐死的形态 [E: ext-literature-integrity.md#设计含义-4]。
5. **限速按 host 分桶，由中央网关决定并行度，不由 subagent 数量决定**。最紧的四条：**arXiv 1 请求/3 秒（≈0.33 rps）且禁止并发连接**、Semantic Scholar 有 key **1 rps**（官方措辞是 "introductory"，随时可变）、OpenAlex 语义检索 **1 rps**、CORE 免注册 5 单请求/10 秒（≈0.5 rps）。中间档：DOAJ 2 rps、Crossref polite **列表 3 rps / 单条 10 rps**、NCBI 3 rps（无 key）/ 10 rps（有 key）。宽松：OpenAlex 常规 100 rps [E: ext-academic-apis.md#D2]。
   **arXiv 必须是串行队列，不能是令牌桶。**
   **⚠️ 已失效的旧值**：「Crossref polite pool = 50 rps」是 2025-12-01 之前的值，现已失效 16 倍 [E: ext-academic-apis.md#核验表 #22]。

**§6.3.1 不要用 OpenAlex 的 `is_retracted` 当门。** 2026-08-17 实测 `is_retracted:true` = 134,175，约为 RW 撤稿条数（66,287）的两倍。随机抽样 200 条归因：只有 **81 条（40.5%）** 是 RW 记录里的被撤原文 DOI；**69 条（34.5%）** 其实是**撤稿公告本身**；另有 42 条标题形如 "Retraction: …" 但 RW 无记录。直接当布尔门会把撤稿公告本身判成造假文献 [E: ext-literature-integrity.md#结论摘要-2, #A4]。
**权威源是 Retraction Watch CSV**（Crossref 托管，每工作日更新，无鉴权，2026-08-17 实测全库 71,799 行、其中 `RetractionNature = Retraction` **66,287** 行、去重原文 DOI **62,708** 个）+ Crossref `update-to` 单 DOI 实时校验（注意 `source ∈ {publisher, retraction-watch}` 可并存，必须去重）[E: ext-literature-integrity.md#A1, #A2]。
**许可**：RW 数据仓库**没有 LICENSE 文件**（GitLab API `license: null`）；Crossref 的表述是可自由复用 + 请求署源。**不要在文档里写「RW 数据是 CC0」，那是没有一手依据的转述** [E: ext-literature-integrity.md#核验表末行]。

### §6.4 GC-2 的边界

**GC-2 永远不得写 ST-V。** 依据是 §1.3 的三条量化上界。

**GC-2 的上线门槛写成 κ，不写成 accuracy**：在人标校准集上 Cohen κ ≥ 0.60 方可做终判档的 ST-A；κ ∈ [0.4, 0.6) 只能做**分流器**（把条目路由给人），不能做终判 [E: ext-evaluation.md#设计含义-2]。
**禁止在任何文档里单独出现 raw agreement 数字**——出现必须并排给 κ。

**GC-2 的模型分配（有实测依据）**：
- 「来源相关性」这一维便宜模型就够：GPT-5-mini F1 = 0.908，是最强且属最便宜档；judge 成本跨度 49×，**成本不预测准确率** [E: ext-evaluation.md#B3, #28/#30]。
- 「事实支持」这一维**没有任何模型够好**（最好 F1 = 0.750，所有模型 CI 重叠）→ **绝不能全托给 judge**，必须由 GC-0 的逐字命中 + 人裁抽检兜底 [E: ext-evaluation.md#29]。
- **用分歧率做升级信号，不用投票平均**。现实锚点：624 对中 378 对（60.6%）有分歧并被人工裁决 [E: ext-evaluation.md#31]。不要幻想 5%。

**GC-2 不得参与生成期**：写作阶段禁止调用同一个 rubric judge 自评再改写——那是对 judge 直接做梯度下降。judge 只在**冻结产物**上跑一次 [E: ext-evaluation.md#R4]。

**分数必须按难度分箱报**：judge 在难题上确实塌（test-retest 从 MT-Bench 的 0.943 掉到 JudgeBench 的 0.911；16 个 judge 中 7 个位置翻转率退化 ≥1.5×；短答自动评分在最难难度箱上多数模型跌到 2.1%–16.6%）[E: ext-evaluation.md#20, #23]。

**注意一个反直觉事实**：广为流传的 judge 偏置数量级（"verbosity bias 15–30 点"）在一手大规模测量里**对不上**——21 个 judge 的 verbosity bias 全部 <0.011，其中 17 个 <0.005；而 position bias 跨近两个数量级（0.002–0.192）[E: ext-evaluation.md#17, #18, #19]。那些流传数字来自互相复述的营销博客，是虚假独立佐证。**偏置必须自己在自己的 judge 上测，不引用行业「公认数量级」。**

### §6.5 门的元规则（三类通用）

**§6.5.1 red-first**：门必须先证明自己会红，红案 fixture 由 conductor 播种、且事件形状必须来自**真实捕获**而非手编 [E: gt-house-method.md#A9]。

**§6.5.2 gate 完整性必须是脚本，不是纪律。** 本仓库宣称 "Gate-integrity is pinned, not vibes"（`git status --porcelain -- checks/` 干净 **且** `git diff <gates-baseline-tag> -- checks/` 为空），但全量 grep `gates-baseline|porcelain` 在三个子项目里**零命中代码**，只命中两处散文——**目前完全依赖 conductor 自觉** [E: GROUND-TRUTH-CORRECTIONS.md#D1, gt-house-method.md#A8]。v2 必须把它写成真脚本，否则是空心门。

**§6.5.3 跨越执行边界的检查是空的。** 同一失败类在本仓库连续出现三次（persona mount / role-pack 子串检测 / plugin_load dump-config），每次都是配置层通过、运行时打脸，每次都由新鲜上下文的对抗读者发现，**从来不是门套件发现的**。修法永远相同：**对运行系统自己的痕迹断言**（session jsonl、真实 boot）[E: gt-house-method.md#结论摘要-2]。

**§6.5.4 读 session 日志的门必须处理三个地雷**（任一遗漏都会让整条反伪造链静默失效）：
1. 磁盘是 `.jsonl.zstd`，**多个独立 zstd frame 串接**；Node 内置 `zlib.zstdDecompressSync` / `createZstdDecompress` **只解第一帧**（实测：得到 1 行，实际 3675 行）。必须按 magic `28 B5 2F FD` 手动切帧、或 spawn `zstd -dc`、或走 `readRaw` / `/api/session.export` [E: GROUND-TRUTH-CORRECTIONS.md#A3, gt-evidence-substrate.md#H3]。
2. 按行 `JSON.parse` 之后**必须 `decodeStorageRecord`**，否则 chunk-row 打包行只有 `seq0`、没有 `seq`，seq→事件的映射会有洞 [E: gt-evidence-substrate.md#H4]。
3. 必须用 `surfaceOp === 'append'` 过滤 **append-origin** 事件，否则 pruner/compaction 的替换体会冒充原始结果（原始事件永远在原 seq 处不动）[E: gt-evidence-substrate.md#D2, #D4]。

**§6.5.5 boot 门断言的是加载期不变量，不是「必须 export Config」。** 后者是错的：`cordis/lib/index.js:956` 写着 `if (!runtime.Config) return config;`——Config **不是必需**；真实调用是 Standard Schema v1 接缝 `Config["~standard"].validate`，任何 Standard-Schema 库都行，且**异步 validate 会抛** [E: GROUND-TRUTH-CORRECTIONS.md#A4]。boot 门应断言五条真实加载期不变量：import 失败 / 导出形状非法 / Config 校验抛 / `apply()` 抛 / inject 未解析致 PENDING。

**§6.5.6 以 headless 为载体的 check：失败信号必须由被测方在 stdout 里显式写出，harness 退出码只作二次兜底。**

〔裁定 · S0 实测〕`.loop/m0/M0-3b.json`。**实测事实**：`dsh` 的退出码**只反映 harness 成败，不反映任务成败**——让 agent 跑 `exit 7`，agent 如实报告 `7`，`dsh` 自身仍退出 **0**。因此 `dsh --profile P "$TASK"; test $? -eq 0` 这种写法是一道**恒绿的空心门**：被测任务无论成败，退出码都是 0。

**实测确认的运行契约**（本条的判定全部建在这四行上）：

| 面 | 成功 | 失败 |
|---|---|---|
| 调用形式 | `dsh --profile <name> "<task>"`（task 是**位置参数**，多词按空格拼接） | 同左 |
| **stdout** | **只有**最终助手消息 + 换行，别无他物 | 单个换行（**1 字节**） |
| **stderr** | **0 字节** | 单行 `dsh: <CODE>: <message>`（实测见过 `AUTH` / `INVALID_REQUEST` / `TRANSPORT` / `UNKNOWN`） |
| **退出码** | `0` = harness 跑完一轮并打印了最终消息——**不代表任务成功** | `1` = harness 层失败：profile 不存在 / 缺 task / 未知 flag / 插件树未激活 / LLM 侧 AUTH·INVALID_REQUEST·TRANSPORT |

**规范（机器可判，`gates/` 下的 `check_e2e.sh` 可直接实现）**：

1. **尾标记是唯一的任务成败信号。** 被测方（任务 prompt 强制要求）必须让最终助手消息以一行标记结尾。判定取 **stdout 的最后一个非空行**，并要求该行**整行**匹配

   ```
   ^RESULT: (PASS|FAIL)$
   ```

   —— 无前后空白、无引号、无 markdown 包裹、无同行后缀。**只看最后一个非空行**，不做全文搜索：全文搜索会把模型复述任务说明里的字面量（"…必须以 `RESULT: PASS` 结尾…"）当成结果。

2. **缺失尾标记一律判 FAIL**，理由码 `E-NOMARK`。**不得判 PASS，也不得判「跳过」。** 缺标记恰恰覆盖了最常见的三种真实失效：模型跑飞了、harness 在 AUTH 处死掉（stdout 只有 1 字节换行）、任务被中途截断。**把「没说话」读成「没问题」是本项目要消灭的那类假绿灯。**

3. **与退出码冲突时的裁决是合取，不是择一**：

   ```
   PASS  ⟺  (exit_code == 0)  ∧  (tail_marker == "RESULT: PASS")
   ```

   其余全部为 FAIL。展开成四格：

   | 退出码 | 尾标记 | 判定 | 理由码 |
   |---|---|---|---|
   | 0 | `RESULT: PASS` | **PASS** | — |
   | 0 | `RESULT: FAIL` | FAIL | `E-TASK`（被测方自述失败） |
   | 0 | 缺失 / 不匹配 | FAIL | `E-NOMARK` |
   | ≠ 0 | 任意（含 `RESULT: PASS`） | FAIL | `E-HARNESS`（harness 层失败，stdout 不可信） |

   **「二次兜底」的精确含义**：退出码**只能把 PASS 降成 FAIL，永远不能把 FAIL 抬成 PASS**。退出码为 0 不是任何形式的通过信号。

4. **判定必须发生在 `dsh` 进程之外。** 门脚本负责跑 `dsh`、捕获 stdout/stderr/退出码，再自己判定；被测的 agent 不参与判定，也不写任何门产物（I-W1、§4 W-04）。
5. **stderr 必须原样收进 `gate-reports/<run_id>/<gate>.json`（W-08），但不参与判定。** 它是区分 `E-HARNESS` 四个子因（AUTH / INVALID_REQUEST / TRANSPORT / 插件树未激活）的唯一材料；用于事后归因，不用于判 PASS。

参考实现（**退出码不要用管道接**——`cmd | tail` 的 `$?` 是 `tail` 的）：

```bash
ERR=$(mktemp); OUT=$(mktemp)
dsh --profile "$PROFILE" "$TASK" >"$OUT" 2>"$ERR"; rc=$?
tail_line=$(awk 'NF {last=$0} END {print last}' "$OUT")   # 最后一个非空行
if   [ "$rc" -ne 0 ];                                 then verdict=FAIL; reason=E-HARNESS
elif [ "$tail_line" = 'RESULT: PASS' ];               then verdict=PASS; reason=-
elif [ "$tail_line" = 'RESULT: FAIL' ];               then verdict=FAIL; reason=E-TASK
else                                                       verdict=FAIL; reason=E-NOMARK
fi
```

**干净房手法（实测，可直接用于门基线）**：`DSH_HOME="$(mktemp -d)"` 会自动初始化出厂 profile 模板（headless / web），是隔离实验与快照基线的现成手段；`DEEPSEEK_API_KEY=<无效值>` 可在不消耗模型的前提下把「插件树是否装得起来」与「LLM 是否可达」分开——前者失败逐字为 `did not activate`，后者失败逐字为 `dsh: AUTH`。

**残留（不得省略）** 〔`.loop/m0/M0-3b.json` 的 `honest_limits`〕：
① 只测了 headless profile，**`dsh web` / `--profile web` 的退出码语义未测**。
② **未测长任务超时与 SIGINT/SIGTERM 中断路径的退出码**——本条规范在这两种路径上没有实测依据。
③ 未测 `--patch` overlay 与 `dsh plugin` 子命令的退出码。
④ **未找到把完整轨迹（而非仅最终消息）导出成文件的 CLI 开关**；headless app 的 `--help` 只有 `-h`。轨迹落在 `$DSH_HOME/sessions` 的 jsonl，**该路径未验证解析**——而任何要做**逐轮**判定（而非只判最终消息）的门都会需要它，届时还要一并吃下 §6.5.4 的三个地雷。
⑤ 尾标记本身是**被测方自述**：它能表达「我知道我失败了」，**不能**表达「我以为我成功了但其实没有」。因此 §6.5.6 只解决**信号载体**问题，不解决**判定正确性**问题——承重的正确性判定仍必须由读产物的确定性门做（§6.5.3）。

### §6.6 可检验断言

- **V6.1** 每条 `mechanism_results[]` 记录携带 `gate_class ∈ {GC-0, GC-1, GC-2}`；不存在缺失该字段的记录。
- **V6.2** 不存在 `gate_class == GC-2` 且 `verdict` 直接导致 `status == verified` 的路径（对 `S` 做一次可达性分析）。
- **V6.3** 每个 GC-1 门的输出携带 `data_as_of`；超过该门阈值的输出其结论为 `not_covered`。
- **V6.4** 每个门在 CI 中有对应的 red-case fixture，且该 fixture 使门非零退出。
- **V6.5** gate 完整性脚本存在且被 CI 调用：断言 `git status --porcelain -- checks/` 为空且 `git diff <gates-baseline-tag> -- checks/` 为空。
- **V6.6** 任意读 session 日志的门，在一个含 ≥2 个 zstd frame 的固定 fixture 上必须读出全部记录（负例：只读到第一帧即失败）。
- **V6.7** 每个 GC-2 judge 有一份带日期与 `judge_version` 的 κ 校准记录，且 κ ≥ 0.60 才被标记为终判档；跨 `judge_version` 的分数不得出现在同一张图/表里。
- **V6.8** 文档 lint：任何文档中「确定性 / deterministic / 机器判定」一词出现在描述 GC-2 的段落内即失败。
- **V6.9 headless 载体的失败信号**（§6.5.6）：① 代码 lint——`gates/` 下任何调用 `dsh --profile` 的脚本，其判定表达式不得只依赖退出码；出现 `dsh ...; test $? -eq 0` / `dsh ... && ` 形态即门红。② 三个红样本必须全红：**R-a** 被测方输出 `RESULT: FAIL`（退出码 0）→ 门必须红且理由码 `E-TASK`；**R-b** 被测方不输出尾标记（退出码 0）→ 门必须红且理由码 `E-NOMARK`；**R-c** 退出码为 1 但 stdout 里含 `RESULT: PASS` → 门必须红且理由码 `E-HARNESS`（证明退出码只能降级、不能升级）。③ 正样本必须绿：退出码 0 且最后一个非空行整行为 `RESULT: PASS`。**R-b 是这三条里最重要的一条**——它是「没说话 ≠ 没问题」的机械化。

---

## §7 flags 词汇表 — 诚实标注的受控词表

### §7.1 通用规则

- **F-规则-1** flags **只能降级，不能升级**。
- **F-规则-2** flags **必须进判定**，不是只打印。前代的 honesty flags 从不进判定、只打印，是 SHIP 定义四分之三未实现的一部分 [E: GROUND-TRUTH-CORRECTIONS.md#C3]。
- **F-规则-3** flags **必须在交付物中可见**，且部分 flag 必须原样显示其参数（如 `chart-extracted` 的 ε）。
- **F-规则-4** 词表是**封闭的**。新增 flag 必须先改本文件。

### §7.2 词表

| # | flag | 含义 | 谁设置 | 谁消费 | 依据 |
|---|---|---|---|---|---|
| F-01 | `uncertainty:no-ci` | 点估计无置信区间却被用于等价/比较断言 | GC-0（结构扫描）+ producer 声明 | S 第 2d 步；渲染器 | [E: gt-pg-current.md#C-10] |
| F-02 | `secondhand` | 证据的实际出处不是原始出处（转引链） | GC-1（upstream 解析）| S 2d；独立性核算 | [E: gt-pg-current.md#I-6] |
| F-03 | `cherry-picking:window` | 选择性时间窗/子集 | producer 声明 + GC-2 检测 | S 2d；人审队列 | [E: gt-pg-current.md#C-10] |
| F-04 | `best-case-ratio` | 比率取最优情形，敏感性未披露 | producer 声明 | S 2d；渲染器（必须显示敏感性区间） | [E: gt-pg-current.md#I-3] |
| F-05 | `retraction` | DOI 命中 RW `RetractionNature = Retraction` | GC-1 | S 0b → ST-C（hard block） | [E: ext-literature-integrity.md#A1] |
| F-06 | `expression-of-concern` / `correction` | 命中 EoC / Correction | GC-1 | S 0b；但**缺失不构成「无 EoC」的证据**（覆盖不完整） | [E: ext-literature-integrity.md#A1] |
| F-07 | `hijacked-journal` | ISSN 或域名命中劫持刊表（456 条，表头自述 last updated 2026-07-17） | GC-1 | S 0b → ST-C | [E: ext-literature-integrity.md#B1] |
| F-08 | `predatory-suspect` | 疑似掠夺性期刊 | **仅人工**（Cabells 订阅制、无 API，本项目不可编程访问） | 人审队列 | [E: ext-literature-integrity.md#B2] |
| F-09 | `preprint-only` | 未经同行评议（arXiv / bioRxiv / ChinaXiv） | GC-1 | S 2d：自动降一档 | [E: ext-chinese-ecosystem.md#5] |
| F-10 | `chart-extracted` | 数值来自图形几何读数；**必须携带 `epsilon` 与 `method`** | 抓取/抽取工具 | S 第 1 步强制 ST-E；渲染器必须原样显示 ε | [E: ext-multimodal-evidence.md#D1] |
| F-11 | `budget-degraded` | 判定因时间/token/RPS/美元预算而降级或中止 | 编排层 + 门 | S 2e（degraded 降一档）/ 0f（exhausted → ST-N） | [E: ext-reproducibility.md#5] |
| F-12 | `metric-frame-mismatch` | claim 声明的口径三元组与源文本实际口径不一致；或前提间口径不可比 | GC-2（口径畸变检测维度）+ GC-0（三元组非空） | S 2d；人审队列 | [E: gt-pg-current.md#I-4, ext-evaluation.md#L2] |
| F-13 | `unstable-decomposition` | 同一子命题做 N 次同义改写后独立走检索-判定链，判定不稳定 | GC-1 + GC-2 组合 | S 2d：强制降至 ST-U | [E: ext-security-injection.md#D4, #V16] |
| F-14 | `single-cluster` | `independent_cluster_count == 1` | GC-0 | **仅作记录，不改状态**——独立性是否足够只由 S 2b 的 `K(kind)` 判定，见 §7.3.2 | [E: ext-security-injection.md#D3] |
| F-15 | `ugc-source` | 承重位置出现 UGC 域（Reddit / 知乎 / Wikipedia / 百家号 / CSDN / 论坛） | GC-0（域分级表） | S 2d：UGC 默认不得作为承重证据，升格需人工确认或非 UGC 独立佐证 | 见 §7.2.1 |
| F-16 | `source-mutated` | 复核时快照 hash 不匹配 | GC-1 | S 0a → ST-U | [E: ext-security-injection.md#D7, #RT-9] |
| F-17 | `non-rendered-channel-hit` | 抓取时非渲染通道命中注入模式 | 抓取工具 | **仅告警计数，不参与判定** | 见 §7.2.2 |
| F-18 | `stale-registry` | T0 名录快照超龄 | GC-1 | S 0c → ST-N | [E: ext-literature-integrity.md#设计含义-3] |
| F-19 | `statcheck-correction-suspect` | statcheck 命中但文中出现统计校正关键词 | GC-0 | 不参与降级；人审提示 | [E: ext-literature-integrity.md#E5] |
| F-20 | `grimmer-test3` | 由 GRIMMER test 3 触发（上游已知误报未修复） | GC-0 | 不参与降级；单列 | [E: ext-literature-integrity.md#E2] |
| F-21 | `grim-not-applicable` | `power = 1 − N·items/10^d` 低于阈值 | GC-0 | 输出 `not_applicable` → ST-N，**不是通过** | [E: ext-literature-integrity.md#E1] |
| F-22 | `self-sourced` | 证据链中出现本系统生成的文本指纹（自我佐证回路） | GC-0（输出打标 + 检索时排除） | 排除出独立簇计数 | [E: ext-security-injection.md#R14] |
| F-23 | `translation-chain` | 跨语言转述链 | GC-1（上游簇归并器） | 归并为一簇 | [E: ext-security-injection.md#E3] |
| F-24 | `pricing-promo` | 定价类数字为促销价/introductory 价；必须带 `expires_at` | producer 声明 + GC-0 强制字段 | S 2d；渲染器 | [E: ext-evaluation.md#R7] |
| F-25 | `as-of-stale` | 可失效字段（价格 / API 条款 / 榜单 / 模型分）的 `as_of` 超过该类 TTL | GC-0 | S 2d′（降一档）；建议 TTL：引用幻觉率类 90 天、模型能力类 180 天、定价/榜单 30 天 | [E: ext-verification-mechanisms.md#D8, ext-reproducibility.md#3] |
| F-26 | `human-verified` | 人工签名核验通过 | **仅人工** | **不改 status**；仅在交付层并排显示 | §1.4.3 |
| F-27 | `snapshot-missing` | 快照文件不存在 | GC-0 | S 0a → ST-U | [E: ext-reproducibility.md#3] |
| F-28 | `quote-mismatch` | 归一化后引语**不是**快照抽取文本的精确子串（含近似命中） | GC-0 | S 0d → ST-U | §1.2.2 |
| F-28a | `near-miss-repairable` | F-28 已置位，且 `rapidfuzz partial_ratio ≥ 95` | GC-0 | **不改状态**（状态已由 F-28 定为 ST-U）；门写 `quote-repair.json`，进 **producer 修复队列**而非人审队列 | §1.2.2.1 |
| F-29 | `no-counter-search` | 未执行反证检索 | GC-0 | S 0e → ST-N | 见 §7.2.3 |
| F-30 | `extraction-quality-warning` | 抽取文本为空或字符比例异常 | GC-0（抽取质量哨兵） | S 0c → ST-N | §1.2.3 |
| F-31 | `contested-by` | 反证指针（携带反证的 evidence_id 列表） | GC-1/GC-2 | S 2a → ST-C | [E: ext-security-injection.md#D5] |
| F-32 | `not-covered-zh` | 该 claim 落在中文文献覆盖盲区（T0 污染筛查与开放索引均不覆盖） | GC-1 | S 0c → ST-N；**必须在交付物中显式声明能力受限** | [E: ext-literature-integrity.md#未决-8, ext-academic-apis.md#D7] |
| F-33 | `primary-source-unreachable` | 一手源非 2xx / 空正文 / 反爬拦截页（触发器 T12） | 抓取工具 | S 0c → ST-N；**禁止用二手转述补齐** | [E: ext-legal-tos.md#T12] |
| F-34 | `retention-tier-c` | 权利信号或访问壁垒导致只能留元数据 + 哈希 | 抓取工具 | `evidence_grade ≤ G2`（§8.6.2）→ S 2c | [E: ext-legal-tos.md#Tier C] |
| F-35 | `non-commercial-only` | 许可为 CC BY-NC 或出版商非商业 TDM 许可（触发器 T8） | 抓取工具 | 不改状态；报告中必须打「非商业限定」标记 | [E: ext-legal-tos.md#T8] |
| F-36 | `output-input-independent` | 重跑门检出输出与输入无关（常数脚本 / ε-依赖）——与「数值超容差」是两类失败：后者通常是诚实误差，前者是造假信号 | GC-0（重跑门 G-DEP） | 不改状态（状态已由重跑门 fail → ST-U）；**审计必检项**，且该 claim 的 producer 本轮全部产出进人工抽查队列 | 〔裁定〕本轮语料无对应 flag；依据 03-EVIDENCE-ENGINE 的 G-DEP 需求 |

**§7.2.1 F-15 的成本依据（与原论文作者的语气相反，我们采信其数据）**：WARP 实测屏蔽 UGC 域的质量代价极小——rubric 4.30→4.26，每查询只移除 2.1 个 UGC URL；且 OpenAI Deep Research 的 UGC 引用率仅 **0.4%** 而 Gemini Deep Research 是 **12.1%**，差 30 倍，证明低 UGC 依赖是可设计出来的 [E: ext-security-injection.md#C1, #V12, #D8]。**该文作者的结论语气是「三种防御都不行」，我们采信的是他们的数据而非措辞——若我们读错了其 rubric 指标的含义，F-15 的成本估计会失真** [E: ext-security-injection.md#未决-13]。

**§7.2.2 F-17 为什么只告警不判定**：基于关键词/祈使句模式的注入检测不能当门禁。真实注入 **>90% 不含显式指令**（约 20 万份真实简历的普查，约 1% 含隐藏注入）；困惑度检测 AUROC ≤ 0.68 且**方向是反的**（注入文本困惑度一致地低于自然 UGC）[E: ext-security-injection.md#V15, #V14]。我们的门禁必须是**架构性的**（通道分离 + 写权隔离），不是判别性的。
**架构性的那一半是有效的**：野外普查（1.2B URL / 24.8M host / 15,387 条已验证注入，Common Crawl 2025-10 快照）显示 **10,779 / 15,387 = 70.0%** 的注入落在非渲染通道（HTTP 响应头 7,887 + 结构化数据 1,996 + 注释 675 + meta 221）；且抽取表示本身是 20 倍杠杆——纯文本合规率 3.9%、HTML 标记 1.1%、渲染快照 1.1%、原始 HTTP 响应 0.2%（5,200 次试验 = 100 提示 × 4 表示 × 13 模型）[E: ext-security-injection.md#V5, #V6, #V7]。
**因此**：抓取管线必须把页面拆成互不混合的字段 `rendered_text` / `non_rendered_text` / `structured_data` / `http_headers`，**只有 `rendered_text` 进入可引用证据池**，其余三路单独存档、只用于告警与取证。
**并且**：野外已有 **542 条明确的「强制引用（citation forcing）」注入**——专门冲着「让 AI 引用我」来的。这正是我们被瞄准的形态 [E: ext-security-injection.md#V8]。
**⚠️ 一个可能推翻架构的前提**：若 PDF 抽取管线拿不到「这段文字是否对人可见」的信息（大多数 PDF 文本抽取库确实拿不到颜色/字号/图层），通道分离在 PDF 路径上就失效——而 PDF 恰是学术场景的主要摄取对象。**这条必须前移为架构可行性验证，不能留到测试阶段** [E: ext-security-injection.md#未决-12, #RT-5]。

**§7.2.3 F-29 的必要性**：注入不改引语真伪，只改「引哪一句」——攻击者诱导 agent 只引对其有利的**真实**句子，逐字匹配必然全绿。逃不过的只有「你有没有找过反面」这个可审计的过程字段 [E: ext-security-injection.md#N6, #D5]。因此每条承重 claim 必须附带一次**主动反证检索**，并记录 `counter_evidence_found` 与其快照 id；**找不到反证也要记录搜索过程与预算**。

### §7.3 flags → 状态作用表

〔裁定 · R1/C-1〕本表在 R1 后重写。旧表把两种类型不同的东西混在一个「硬上限」列里：
「强制某个具体状态」给的是一个**状态**（可以喂给 `min()`），「降一档」给的是一个**操作**（不能喂给 `min()`）。
而 §1.5 的 2d 定义是 `base = min(base, ceiling(flags))`——它消费的必须是状态。
类型不匹配意味着实现者必须自己猜，两种猜法给出不同的 status，违反 V1.2 的纯函数性。
现在每条 flag 显式带**作用类型**，且每种作用类型由 `S` 里**唯一一步**消费。

| flag | 作用类型 | 值 | 被 `S` 的哪一步消费 |
|---|---|---|---|
| F-13 `unstable-decomposition` | `ceiling` | ST-U | 2d |
| F-12 `metric-frame-mismatch` | `ceiling` | ST-U | 2d |
| F-03 `cherry-picking:window` | `ceiling` | ST-A | 2d |
| F-04 `best-case-ratio` | `ceiling` | ST-A | 2d |
| F-01 `uncertainty:no-ci` | `step-down` | 降一档 | 2d′ |
| F-02 `secondhand` | `step-down` | 降一档 | 2d′ |
| F-09 `preprint-only` | `step-down` | 降一档 | 2d′ |
| F-15 `ugc-source` | `step-down` | 降一档 | 2d′ |
| F-24 `pricing-promo` | `step-down` | 降一档 | 2d′ |
| F-25 `as-of-stale` | `step-down` | 降一档 | 2d′ |
| F-34 `retention-tier-c` | `indirect` | 压 `evidence_grade ≤ G2` | 2c（经 §8.6.2，不进 2d/2d′） |
| F-08 `predatory-suspect` | `none` | — | 不参与判定（Cabells 订阅制、无 API，**仅人工**）；进人审队列 |
| F-14 `single-cluster` | `none` | — | 不参与判定（**仅作记录**，见 §7.3.2） |
| F-17 / F-19 / F-20 / F-26 / F-28a / F-35 / F-36 | `none` | — | 不参与判定 |

**§7.3.1 不在本表内的 flag（它们在第 0 步或别处已经决定了返回值，若再进 2d 就是重复计算）**：

| flag | 已在哪一步返回 |
|---|---|
| F-05 / F-06 / F-07 | 0b → ST-C |
| F-16 / F-27 | 0a → ST-U |
| F-18 / F-21 / F-30 / F-32 / F-33 | 0c → ST-N |
| F-28 | 0d → ST-U |
| F-29 | 0e → ST-N |
| F-11 | 0f（exhausted）→ ST-N；或 2e（degraded）降一档 |
| F-31 | 2a → ST-C（吸收态） |
| F-10 | 第 1 步强制 base = ST-E |
| F-22 / F-23 | 不作用于 `S`，作用于 §5.5 的**簇归并器**（改的是 `independent_cluster_count` 的值，不是状态） |

**§7.3.2 F-14 为什么不在任何一张表里**〔裁定 · R1/C-1，五个独立攻击者共识〕。

`F-14 single-cluster` 的置位条件是 `independent_cluster_count == 1`，**不带 kind 限定**。
旧表把它列在「降一档」组里，于是它被消费了两遍：
一次在 2b（`independent_cluster_count < K(kind)`，**带** kind 限定），一次在 2d（**不带**）。

后果是产品的绿灯全空。§1.5.2 定 `K(K-D) = 1`、`K(K-L-T) = 1`——单簇是这两条通道的**正常态**，
2b 判 `1 < 1` 为假不降，2d 却必降。而 K-D（封闭式）与 K-L-T 恰恰是**仅有的两个能到达 ST-V 的 kind**，
§2.4 矩阵里那两个 ✅ 因此一条都兑现不了。

**修法**：`F-14` 是一条**记录**，不是一条**规则**。它只负责让「这条 claim 只有一个独立簇」这件事
在台账里可查、可统计、可被人审队列筛选；**独立性是否足够，唯一的判据是 2b 的 `K(kind)`**，
因为只有 2b 知道这条 claim 是什么 kind、单簇对它意味着什么。
`F-14` 因此作用类型为 `none`，不进 2d 也不进 2d′。§7.2 的「谁消费」列本来就写的是 `S 2b`——
旧 §7.3 与它自己的词表矛盾。

### §7.4 可检验断言

- **V7.1** 语料中出现的每一个 flag 都在 §7.2 词表内；出现表外 flag 即失败。
- **V7.2** 每条含 F-10 的 claim 都携带非空 `epsilon` 与 `method`，且其 status == ST-E。
- **V7.3** 每条含 F-24 的 claim 都携带 `expires_at`；过期后重跑 `S` 必须触发 F-25。
- **V7.4** 对每条承重 claim，`counter_evidence_searched == true`；否则 status == ST-N。
- **V7.5** 红队用例 RT-4：一个页面同时在 HTML 注释、`<meta>`、`alt`、`aria-label`、`display:none` 节点、零尺寸元素、屏外定位元素、JSON-LD、HTTP 响应头（`X-AI:` / `X-LLM:`）里各放一条不同注入；期望九条**全部**落入 `non_rendered_*` 字段，**零条**进入可引用证据池，告警计数 = 9 [E: ext-security-injection.md#RT-4]。
- **V7.6** 红队用例 RT-6：构造一条不含任何指令动词的注入（>90% 的野外形态）；期望模式匹配检测器漏报是**可接受的**，但 status 仍因独立簇数不足而拒绝升格 [E: ext-security-injection.md#RT-6]。
- **V7.7** 红队用例 RT-8：一个真实页面同时含支持句与反对句，注入诱导只引支持句；期望 `counter_evidence_found == true`、status 降为 ST-C [E: ext-security-injection.md#RT-8]。
- **V7.8** 架构可行性前置验证（RT-5）：PDF 抽取管线能否把白色/极小字号文本归入 `non_rendered_text`。**该验证失败即为必须先解决的架构前提**，不是一条普通失败用例。
- **V7.9**〔R1/C-1 后新增，检查的是**本文件自身**〕**词表与作用表必须双向完备**：
  §7.2 词表里的每一个 flag，在 §7.3 作用表与 §7.3.1 别处表中**恰好出现一次**；
  §7.3 / §7.3.1 里提到的每一个 flag 都在 §7.2 词表内。
  任一方向出现缺口或重复即失败。
  **为什么这条必须是机器检查**：C-1 的根因正是 `F-14` 同时出现在 2b 的消费路径与 §7.3 的降档表里
  （被消费两遍，且两次的条件不同）。这类缺陷在散文里读不出来——两行分开看都对——
  只有把「每个 flag 恰好被一步消费」写成可判定的计数断言才抓得住。
  本断言可用一段十行的脚本实现：从 §7.2 提取 flag id 集合，从 §7.3/§7.3.1 提取，比对两个方向的差集。
- **V7.10**〔同上〕**状态符号不得越界**：全文出现的所有 `ST-*` 形态的符号必须落在 §1.4 六值枚举内。
  这条与 V1.1 是同一件事的两个作用面——V1.1 检查**语料**里的 status 字段值，V7.10 检查**文档正文**。
  规划文档里写出一个第七个状态符号（哪怕只是散文里的占位符），实现者就会把它当真。

---

## §8 文件与目录契约

### §8.1 布局（规范）

```
<workspace>/.arc/
  objects/<sha[:2]>/<sha256>              # CAS：快照原始字节、抽取文本、run 输出、数据集
  claims/<claim_id>.json                  # 内容（producer 写）
  claims/<claim_id>.status.json           # 状态（门写）—— 与内容物理分离（I-W2）
  evidence/<evidence_id>.json             # 证据卡；id = sha256(work_id‖version_id‖locator‖normalize(quote)‖extractor_version)
  inferences/<claim_id>.producer.md       # warrant + 前提（producer 写）
  inferences/<claim_id>.reviewer.md       # 独立再推导 + 反例搜索记录（reviewer 写）
  analysis/<claim_id>/{run.py, uv.lock, out.json}
  verdicts/<gate_id>/<claim_id>.json      # Class-2 裁决原件（裁决子代理写）
  gate-reports/<run_id>/<gate_id>.json    # 门报告（门写，带自证签名）
  registries/<name>.{csv,xlsx,json} + <name>.meta.json   # 本地化的 T0 名录 + 快照日期
  runs/<run_id>/manifest.json             # 运行时指纹
  prose/                                  # 组稿产物（确定性组稿器写）
  export/ro-crate-metadata.json           # 仅 publish 期生成
```

### §8.2 台账主体是文件，不是自定义 session 事件（D-8.1）

**决定**：per-claim 证据台账落在**文件**上（CAS + per-claim manifest），**不**落在自定义 log-only session 事件上。

**理由（全部一手代码 + 实测）**：
1. `ignorable` 字段**只读不写**——`Session.append` 的签名与实现里根本没有该通道，全 194 包 grep 零写入方 [E: GROUND-TRUTH-CORRECTIONS.md#A1, gt-evidence-substrate.md#B6]。
2. 未知事件类型会让 `assertEventsSupported` 在**四个读入口**（`load`/`inspect`、`readFrom`、`prepare`（resume）、`adoptLivePrefix`（HMR））全部抛 `SessionFormatUnsupportedError`，拒绝解释整份日志 [E: gt-evidence-substrate.md#B4]。已在野证实：第三方插件 `@huanlin/dsh-plugin-yet-another-subagent` 写 `ya-subagent/started`，本机扫描到 6 条，该 session **没有任何 `session/end-seed`**——它从未被成功以 seed 重建过 [E: gt-evidence-substrate.md#C1, #C2]。
3. 唯一逃生口是 mutate `KNOWN_SESSION_EVENT_TYPES`（未冻结的可变 Set，实测可行），但官方 README 明写「registration surface … deferred」，且**日志对没装本插件的进程仍然不可读** [E: gt-evidence-substrate.md#B7]。→ **默认不用**，只作为「若官方开放注册面则升级」的预留路径。
4. 台账需要跨 session / 跨 fork / 跨进程可读、可 diff、可被门脚本独立校验；session 日志做不到（一个 session 只能一个活写者，跨进程无互斥）[E: gt-evidence-substrate.md#H5]。
5. session 日志**没有删除/保留 API**——台账放进去就永远删不掉 [E: gt-evidence-substrate.md#H5]。

**配套决定 D-8.2**：抓取锚点写 `tool/result.data.meta.evidence`（§4 W-02）。自设上限 **8 KB**，大对象只放 sha256 指针——`meta` 有没有隐性上限**未验证**（代码里没看到字节/深度限制，但 wire 层是否对超大 meta 出问题未测）[E: gt-evidence-substrate.md#未决-3]。

**配套事实（必须写进契约）**：自定义 log-only 事件**无法用 `sourceEventSeqs` 引用其依据的 `tool/result` seq**（运行时直接抛错，实测），所以 provenance 链接若走自定义事件就不受核心校验保护 [E: gt-evidence-substrate.md#A6]。这是选 `tool/result.meta` 的又一理由——它与 `tool/call` 的 seq 由核心校验的 `sourceEventSeqs` 天然绑定。

### §8.3 拒绝仓库级锁工具（D-8.3）

**决定**：不用 **DVC / DataLad / git-annex**。

**理由**：三者都建立在仓库级全局锁之上，与超并行多 loop 前提直接冲突。一手证据：`dvc repro` **没有 `--jobs` 并行开关**，官方命令参考页要求并行只能「在不同终端里并发地多次启动 `dvc repro`」；而 troubleshooting 页写着并发启动会撞锁（`Unable to acquire lock`，锁文件 `.dvc/tmp/lock`）；请求并行调度器的 issue **#755 开于 2018-06-08，至今 open** [E: ext-reproducibility.md#A1]。DataLad / git-annex 底层是 git + git-annex，同样吃 git index 锁 [E: ext-reproducibility.md#A2, #C1]。
**这不是配置问题，是设计前提问题。**

**采纳的替代**：自建 CAS（sha256 + 原子 rename，约 30 行）+ 一 claim 一文件 append-only；**抄 DataLad run-record 的六字段 schema**（`cmd` / `dsid` / `exit` / `inputs` / `outputs` / `pwd`）并补它缺的两项（环境锁文件哈希、随机种子）[E: ext-reproducibility.md#A2]；git 提交只由 orchestrator 在 gate 时做一次。

### §8.4 其余采纳/拒绝决定

| 决定 | 裁决 | 理由 |
|---|---|---|
| **D-8.4** Merkle / 哈希链审计日志 | **拒绝** | 威胁模型不成立：能改 claim 记录的人（本机用户/agent）同样能改哈希链的锚点。真正需要的是「输入内容寻址 + 输出可重跑比对」这种**功能性**防篡改（改了数据 → 重跑对不上 → 失败），不是密码学防篡改 [E: ext-reproducibility.md#C2] |
| **D-8.5** papermill / nbval / notebook 验证 | **拒绝** | papermill 不比对输出；nbval 的比对即 false-red 之源 [E: ext-reproducibility.md#B1, #B2] |
| **D-8.6** PROV-O RDF 作为工作格式 | **拒绝** | 成本远超收益；PROV-O 已逾十年、基本被局限于小型研究项目 [E: ext-reproducibility.md#A3] |
| **D-8.7** Process Run Crate 0.5 导出器 | **采纳，仅 publish 期** | MUST 只有三项（`@type` ∈ {CreateAction, ActivateAction, UpdateAction}、`@id`、`instrument`），`result`/`endTime`/`agent` 为 SHOULD；profile 自己明写不保证一致性、不保证可复现——正好是我们要的：导出时从台账一次性生成，零日常成本 [E: ext-reproducibility.md#A3] |
| **D-8.8** 完整 Workflow Run Crate | **拒绝** | 我们没有 workflow 引擎语义，Process 层就够 |
| **D-8.9** perma.cc | **拒绝** | 付费、站点对自动抓取返回 403 无法核价（$10/月数字最早见于 2019-01-07 报道，视为失效）；能力已被本地 CAS 覆盖 [E: ext-reproducibility.md#D2] |
| **D-8.10** Save Page Now (SPN2) 归档 | **采纳，best-effort，不阻断** | 归档 URL 作为可选字段，提交失败不阻断门，也不能因此让 claim 升级——真值锚点是本地快照的 sha256。**注意 SPN2 速率限制无一手来源**（官方 API 文档托管在需登录的 Google Doc），社区口径「匿名 15 URL/分钟」标 `unverified` [E: ext-reproducibility.md#D1] |
| **D-8.11** 快照工具双路 | **采纳** | 静态页/PDF 落地页 → monolith 带 `-M`（去时间戳）；JS 渲染页 → single-file-cli（需本机 Chromium）。**跨时间只比对抽取文本的哈希，不比对快照字节**——两个工具都不保证字节确定性 [E: ext-reproducibility.md#D3] |
| **D-8.12** spill 进证据链 | **拒绝** | spill root 默认在**每进程私有的 OS temp 目录**、跨进程不可预测、可能被系统清理、无删除 API [E: gt-evidence-substrate.md#E5] |
| **D-8.13** 台账格式 | **JSON + schema，不是自由文本 Markdown** | 本仓库自己的攻击台账会腐：`r1-ledger.md` 有截断与重复小节，R3 自己把 "ledger garble" 记为 P3 [E: GROUND-TRUTH-CORRECTIONS.md#D3]。**可信度产品的证据台账若是自由文本会腐，必须有格式门。** 唯一的散文台账 `inferences/*.md` 必须有结构化 front-matter 并被 schema 校验 |
| **D-8.14** 云沙箱（E2B / Modal / Daytona / Cloudflare） | **拒绝（v1）** | 唯一收益是隔离强度，代价是把用户的课程数据/论文 PDF 送出本机。成本口径陷阱：Modal 的 **Sandbox 费率是其普通 function 费率的 3.0 倍**（$0.00003942 vs $0.0000131 /core/s）；Cloudflare 按**活跃 CPU 时间**计费而 E2B/Modal 按**墙钟时间**计费，两个 $/vCPU-h 数字不可直接比 [E: ext-reproducibility.md#E1] |
| **D-8.15** 遥测 | **默认关，且证据 payload 不得含敏感内容** | 开启遥测会把 session-log 记录**逐字镜像**到 OTLP/HTTP logs，**无任何 redaction 规则** [E: gt-evidence-substrate.md#H6] |

### §8.5 抓取工具的自建义务（必须写在契约里）

本机**没有 fetch provider**，`web_fetch` 出厂关闭，`WebFetchBody` 无 PDF 臂；`WebSearchSource` 只有 `url/title/snippet/publishedAt`，没有 DOI/作者/venue/引用数——学术元数据塞进去就丢 [E: gt-exec-security.md#H-4]。因此检索与抓取工具**必须自建**，并**必须自带**：协议白名单、私网/回环/云元数据地址拒绝、重定向逐跳复检、尺寸与超时上限。官方注释直说不挂 fetch provider 是因为「that provider defers SSRF protection and the model would choose the request target」——这是我们要写的代码，不是运行时送的。

**⚠️ 引用任何「抓取上限」数字前必须确认本机实际装了哪个 provider**：流传的「web_fetch body 上限 10 万字符」是**本 build 未安装**的那个 provider 的常量，工具层常量另有其值 [E: GROUND-TRUTH-CORRECTIONS.md#A6]。

### §8.6 留存分档（`retention_tier`）— 与 `evidence_grade` 正交的第二个维度

`evidence_grade`（§3）回答「我拿到了多少」；`retention_tier` 回答「我被允许留下多少、留多久、能不能外发」。**档位由「取得渠道 + 权利信号」决定，不由「内容有多有用」决定**；决策发生在 fetch 时刻，写进 provenance，**只能下调，不能事后上调** [E: ext-legal-tos.md#一、三档证据快照策略]。

| 档 | 保存什么 | 准入 | 能否进交付物 |
|---|---|---|---|
| **Tier A** | 原始字节 + 全文文本 + 解析产物，可反复重读 | 开放许可（CC0/CC BY/CC BY-SA/公共领域）；授权 TDM 通道；开放学术基础设施（arXiv 元数据 CC0、OpenAlex CC0、Crossref 元数据、PMC OA subset）；**用户自有材料**；适用的法域例外 | **否。Tier A 原始件永不进交付物、永不进 Artifact、永不进任何对外分享链接** |
| **Tier B**（**默认档**） | 受硬上限约束的摘录 + 起止偏移/页码/XPath + 回链 + `rendered_text_sha256` | 一般来源 | **是**——这是唯一可以进入最终论文/报告的原文形态 |
| **Tier C** | 仅元数据 + 哈希 + 权利信号头；**不保存任何受版权保护的表达** | 降级触发器命中后的落点 | 仅书目引用 |

**§8.6.1 摘录硬上限（取所有适用规则中最严者）**：Elsevier 渠道 **≤200 字符**（"围绕且不含匹配实体本身"）+ 必须附 DOI 回链；一般来源默认 **≤300 字符/单条**、同一文献累计 **≤1,200 字符**，且不得覆盖任一连续章节的实质部分（避免拼接重构）；**中文来源单条 ≤200 字，并必须指明作者姓名与作品名称**（著作权法第 24 条(二)「适当引用」）[E: ext-legal-tos.md#Tier B]。

**§8.6.2 与 `evidence_grade` 的耦合规则**：
- Tier A → 该文献整篇可达 G5。
- Tier B → **仅该锚点跨度**可达 G5。**同一文献的任何新 claim 都必须重新抓取**，不得复用未保留的正文。
  两条谓词在本档下的准确成色见 §8.6.2.1——旧文本写的「`quote_faithful` 仍可离线复核」**是错的**。
- Tier C → `evidence_grade ≤ G2`（仅存在性）。

**§8.6.2.1 默认档下两条谓词的真实成色**〔裁定 · R1/C-7，本条不在任何已知弱点清单里〕。

R1 攻击者 F138 指出：在**默认**档 Tier B 下，本项目仅有的两条「可 100% 兑现」承诺同时塌。逐条承认并收口。

**① `quote_faithful` 在 Tier B 下离线复核是构造性恒真。**
Tier B 保存的是「围绕引语裁出来的摘录」（§8.6.1）。拿引语去匹配这段摘录，
**匹配成功是裁剪方式的推论，不是对来源的检验**。旧文本的括号注「引语按构造落在保留的摘录内」
把这件事当成好消息写了出来——它恰恰是这条复核为空的证明。

**收口**：`quote_faithful` 的判定**只发生一次**，在抓取工具执行内、对**全量抽取文本**判定
（W-01/W-02 的同一次执行）。判定结果连同下列三项锚定进 `tool/result.data.meta.evidence`：
`verdict` / 归一化引语的 `sha256` / 引语在全文中的字节区间 `[start, end)` / **全文的 `rendered_text_sha256`**。

此后在 Tier B 下可离线复核的是**三件较弱但非空**的事：
1. 保存的摘录哈希 == 锚定的摘录哈希（摘录没被改）；
2. 引语的字节区间落在摘录的字节区间内（摘录确实覆盖了被判定的那段）；
3. 归一化引语的 `sha256` == 锚定值（claim 里的引语没被事后改写）。

不可离线复核的是：**那段引语当初是否真的出现在全文里**。这一条只有在重取到
`rendered_text_sha256` 相同的全文时才能重新判定。

**因此对外的准确措辞是**：`quote_faithful` 是*判定时刻*哈希可判的确定性谓词，
其后由哈希链**背书**而非**重判**。声称它「任何时候都可离线 100% 复核」只在 Tier A 下成立。

**② `source_integrity` 的字节同一性子测试在 Tier B 下依赖重取，而重取实测 3/5 成功。**
本轮一手关门样本：Wiley 402；`sso.agc.gov.sg` / `sal.org.sg` / `irishstatutebook.ie` /
`japaneselawtranslation.go.jp` 403；EUR-Lex 三种 URL 均空正文 [E: ext-legal-tos.md#T12]。

**收口**：重取失败**不得**静默通过，也**不得**判 `mutated`（我们并不知道它变了）。
按 §1.2.3 的 fail-closed 原则落 `not_covered` → ST-N + F-33。
**这意味着一条 Tier B 的 claim 会随时间衰减**：初判可以是 ST-V，复核期重取不到就掉到 ST-N。

这不是缺陷，是诚实——但它有一个**必须写进产品面**的后果：
**`status` 是带时间戳的量，不是永久属性**。`status.json` 必须携带 `computed_at` 与
`revalidated_at`，交付物渲染时必须显示复核时点。任何「本报告 N 条断言已 verified」的表述
若不附复核时点，即为 §9.1 意义上的未覆盖数字。

**③ 由此产生的一条硬约束**：承重程度最高的 claim（进入结论段的）**必须**走 Tier A 通道，
或在 Tier B 下接受「初判 + 衰减」的如实标注。默认档不变（法务约束决定档位，不由我们选），
但**编排层必须在计划阶段就知道哪些 claim 会落在 Tier B**，并把这件事作为
覆盖率风险上报给 CP-1 人在环检查点（04 §7.2），而不是等到复核期才发现结论段大面积掉档。

**§8.6.3 降级触发器（封闭枚举，按序求值，只能下调）** [E: ext-legal-tos.md#二、fetcher 必须硬编码的降级触发器]：
`T0-HARD`（影子图书馆域名 → **硬拒，不发请求**，只写「候选被拒」记录）/ `T1-AUTH`（401/403/407 或登录墙/付费墙/DRM → Tier C，**绝不尝试任何绕过**：不换 UA 伪装、不用 cookie 走私、不试镜像站、不试去墙服务）/ `T2-402`（Payment Required → Tier C，标 `paid_access_available`，**不自动付费**）/ `T3-ROBOTS`（RFC 9309 Disallow 命中 → 不抓取）/ `T4-SIGNAL-TRAIN` / `T5-SIGNAL-INPUT`（`Content-Signal: ai-input=no` → 该条证据**不进 RAG 上下文**）/ `T6-TTL`（出版商 TDM 通道 → 强制 `delete_on_project_end` + `ttl_expires_at`）/ `T7-LEN` / `T8-NC` / `T9-RATE`（arXiv 1 req/3s 且单连接；一般 1 req/s 并发 1）/ `T10-CN`（中国大陆非开放许可来源 → 默认 Tier B）/ `T11-JURIS-EU3` / **`T12-UNREACHABLE`** / `T13-HOLD`（legal hold → 暂停一切自动删除与 TTL 降级）。

**§8.6.4 `T12-UNREACHABLE` 是本项目最重要的一条留存规则，因为它同时是口径纪律**：一手源返回非 2xx、空正文、或被识别为反爬拦截页时，**写 ST-N 并如实上报；禁止用博客/聚合站的转述替代一手源来「补齐」数字**——那正是上一轮 1/3 载荷数字口径失真的机制。本轮调研实测的关门样本：`onlinelibrary.wiley.com` 返回 402；`sso.agc.gov.sg` / `sal.org.sg` / `irishstatutebook.ie` / `japaneselawtranslation.go.jp` 返回 403；`eur-lex.europa.eu` 三种 URL 形式均返回空正文 [E: ext-legal-tos.md#结论摘要-6, #T12]。

**§8.6.5 抓取身份策略**：使用固定、可识别的 User-Agent，**不伪装浏览器**；准备好 Web Bot Auth（Ed25519 + `Signature-Agent`/`Signature-Input`/`Signature`，RFC 9421）。代价是命中更多 403——**这是设计上接受的代价，由 T12 转成诚实的 ST-N，而不是伪造的「已核实」** [E: ext-legal-tos.md#身份策略]。
补充：arXiv 明禁转存再分发（"Store and serve arXiv e-prints … from your servers"），本地缓存自用可以，打进可分发的 artifact 则可能越界 [E: ext-academic-apis.md#D2, #未决-5]。

**§8.6.6 Tier A 的三条强制附加约束**（直接来自 Bartz v. Anthropic 判词点名的减分项「The library copies lacked internal controls limiting access and use.」）：①必须有内部访问控制，语料目录不可被全库导出，每条记录带 purpose tag；②必须有 TTL，到期自动降为 Tier B 而非静默续期；③**必须可被 legal hold 暂停删除**——TTL/删除策略必须是可暂停的，不是无条件定时销毁 [E: ext-legal-tos.md#Tier A 的强制附加约束, #202]。

> **免责标注（照实转录语料的免责声明）**：ext-legal-tos.md 自陈「本文是工程设计输入，不是法律意见；凡标 `unverified` 的条目在写进代码默认值前必须由人复核」。本节把该免责一并继承。**已知未决**：个人学生/自由研究者是否满足 EU DSM Art.3 的 "research organisation" 主体要件——未决；欧盟数据库特殊权利（sui generis, Directive 96/9/EC）对本项目规模的适用性——未核实 [E: ext-legal-tos.md#Tier C 注意, #128]。

### §8.7 可检验断言

- **V8.1** `.arc/` 下不存在 `.dvc/`、`.datalad/`、`.git/annex/`。
- **V8.2** 全量扫描本项目产生的 session 日志，未知事件类型计数为 **0**（即我们从不写自定义事件类型）。
- **V8.3** 每条 `evidence` 记录的 `object_sha256` 在 CAS 中可解析，且 `objects/` 下不存在无任何 manifest 引用的孤儿对象（或孤儿被显式列入 GC 清单）。
- **V8.4** `claims/*.json` 与 `claims/*.status.json` 是不同文件；不存在同时含内容字段与 status 字段的单一文件。
- **V8.5** 台账格式门：`claims/`、`evidence/`、`verdicts/`、`gate-reports/` 下全部文件通过 JSON Schema 校验；`inferences/*.md` 的 front-matter 通过 schema 校验；**校验失败即门红**（对治 D3 的台账腐化）。
- **V8.6** `registries/*.meta.json` 全部含 `snapshot_date`；无该字段的注册表不得被任何门消费。
- **V8.7** 并行压测：N 个并发写者同时写 CAS 与 `claims/`，结束后无损坏文件、无合并冲突、CAS 中相同内容只有一份、`git status` 由 orchestrator 一次提交后干净。
- **V8.8** `export/ro-crate-metadata.json` 满足 Process Run Crate 0.5 的三条 MUST。
- **V8.9** 每条 evidence 记录携带 `retention_tier ∈ {A, B, C}` 与非空 `tier_reason[]`（触发器 ID 列表）；`retention_tier` 的历史序列单调不上升。
- **V8.10** 交付物（`prose/`、`export/`）中不含任何 `retention_tier == A` 的原始件；Tier B 摘录长度全部不超过 §8.6.1 的适用上限；中文摘录全部携带作者与作品名。
- **V8.11** 不存在 `retention_tier == C` 且 `evidence_grade > G2` 的记录。
- **V8.12** 抓取日志中不存在对影子图书馆域名的请求（T0-HARD 是「不发请求」，不是「请求后丢弃」）；不存在同一 URL 在 401/403 后换 UA 重试的记录。
- **V8.13** `legal_hold == true` 时，TTL 清理任务对该记录为 no-op（负向测试：置 hold 后推进时钟，断言文件仍在）。

---

## §9 术语表 — 不在此表的词，其他文档不得发明

> **§9.0 引用规则**：其他文档使用下列术语时，只能写「见 §9.x」，不得重述定义。

| # | 术语 | 定义 | 备注 |
|---|---|---|---|
| §9.1 | **承重 / load-bearing** | 一条 claim 是承重的，当且仅当它被 `{{claim:...}}` 占位符引用进正文，或被另一条 claim 列为前提。**凡进入正文的数字、命名实体、比较，一律是承重的**；正文中不允许出现非承重的数字（白名单：年份、章节号、页码） | 机器可判：裸数字扫描 |
| §9.2 | **载荷 / payload** | claim 的结构化字段集合（数字、命名实体、口径三元组、比较对象），**不是散文句子**。§2.2.1 的包含检验作用于载荷 | — |
| §9.3 | **规范源 / normative source** | 本文件。术语定义只此一份；其他文档复述定义即为回归（lint：对本文件的定义句做 n-gram 检索） | — |
| §9.4 | **口径三元组 / metric frame** | `(什么指标 metric / 在什么样本或档位上 sample_or_tier / 与什么比 comparator)` 三字段。**缺任一项直接判 ST-N，不进 GC-2** [E: ext-evaluation.md#R7] | 一等公民字段 |
| §9.5 | **独立来源 / independent source** | 按 `upstream_id` 归并后的一个簇。**不是 URL，不是域名**（§5.5） | — |
| §9.6 | **候选 / candidate** | 尚未取得可复核快照的检索结果条目。候选**不是证据**，不得进入任何 claim 的证据集（§3.4.1） | G1 只能是候选 |
| §9.7 | **锚点 / anchor span** | 快照抽取文本中的一段真实文字及其可复核定位符。G5 的构成要件（§3.3） | — |
| §9.8 | **快照 / snapshot** | `{url, fetched_at, http_status, raw_bytes_sha256, rendered_text_sha256, extraction_pipeline_version}`。抽取管线版本会改变攻击面，不记录版本就无法复现判定 [E: ext-security-injection.md#D7] | — |
| §9.9 | **CAS / 内容寻址** | `objects/<sha[:2]>/<sha256>` + 原子 rename。并行安全性来自 POSIX rename 原子性 + 相同内容写入幂等 | — |
| §9.10 | **门 / gate** | 一段确定性代码，输入是本地工件（可含裁决文件），输出是 status 与门报告。分三类（§6.1） | 门不是 agent |
| §9.11 | **裁决 / verdict** | GC-2 的**输入**：一个模型（或人）对某条判断给出的结论及其身份指纹。裁决**不是** status | §4 W-07 |
| §9.12 | **warrant / 推理许可** | K-I 中连接前提与结论的步骤类型，取自五值封闭枚举（§2.3） | — |
| §9.13 | **基准饱和 / benchmark-saturation** | 一个公开基准的头部分数集中在天花板附近、区分度下降，且 SOTA 方法针对该基准预热。实例：OmniDocBench 顶部 94.6% 被从业者公开称为 saturated；DABstep hard 已进入饱和/过拟合区间 [E: ext-multimodal-evidence.md#D2, ext-reproducibility.md#F1] | **必须写全称**，不得只写「饱和」 |
| §9.14 | **检索饱和 / search-saturation** | 一次检索扇出的停机条件：新增查询不再带来新的独立簇 | 〔裁定〕**语料中无外部证据支持这个概念**；它是本项目自建的工程停机条件，必须自证（记录「第 k 次扩展带来的新独立簇数」曲线）。**什么会推翻**：若实测该曲线不单调或噪声主导，则改用固定预算 |
| §9.15 | **假独立佐证 / false independent corroboration** | 多个名义来源归并后实为一个上游簇。已知硬样本见 §5.5 | — |
| §9.16 | **静默漂移 / silent drift** | 输出语义偏移但未越过二元判定阈值。实测：判为「攻击失败」的案例中仍有 15.0% 漂移 Δ≥0.3 [E: ext-security-injection.md#V22b] | 二元 status 会把它全标绿 |
| §9.17 | **stale / 陈旧** | 前提变更后依赖它的推断结论进入的中间态，必须重判（§2.3 第 6 项） | 不是 status 值 |
| §9.18 | **TTL** | 某类可失效字段的有效期。见 F-25 的建议值 | — |
| §9.19 | **fail-closed / fail-open** | fail-closed = 异常时落到最保守状态（ST-N 或 ST-U）。**fail-open 是禁止的**：前代唯一的 SHIP 就是缺面板文件导致的 fail-open 产物 [E: GROUND-TRUTH-CORRECTIONS.md#C4] | MISSING == FAIL |
| §9.20 | **maker ≠ checker** | 产出者与复核者的 harness 身份不同（§5.3）。**不是** prompt 措辞 | — |
| §9.21 | **red-first** | 门在被信任之前必须先证明自己会红（§6.5.1） | — |
| §9.22 | **gates-baseline** | conductor 在编写 checks 时打的 git tag；门只在 `git status --porcelain -- checks/` 干净且 `git diff <tag> -- checks/` 为空时算数。**本仓库该机制目前零代码实现** [E: GROUND-TRUTH-CORRECTIONS.md#D1] | v2 必须补脚本 |
| §9.23 | **出厂值 / shipped value** | `dsh-base/cordis.patch.yml` 与各 preset 实际生效的值。**与「包默认值」（包 README/代码 default）不同，冲突时以出厂值为准** [E: GROUND-TRUTH-CORRECTIONS.md#A9] | 引用默认值必须标明是哪一种 |
| §9.24 | **轮预算 / round budget** | 两个**不同**的东西：goal 的 `defaultMaxGoalRounds = 256`（确认）；ralph 的 `maxRounds` README 写 256 但**出厂全部组合覆盖为 64**。引用时必须标明是 goal 还是 ralph [E: GROUND-TRUTH-CORRECTIONS.md#A10] | 不得混谈 |
| §9.25 | **provider（三义）** | ①`agentOptions.provider` = LLM 路由（可 per-call）；②`subagentProvider` = subagent 传输后端（作用于整个 run）；③**检索供应商** = 外部检索/抓取服务商（serper/bocha/Exa…）。见 §5.2.1。第三义在其他文档中一律写全称「检索供应商」，不得裸用 provider | 必须消歧 |
| §9.26 | **held-out** | 永不公开、永不进 git、永不进 artifact 的评测题集。核心闭集 60 题、公开演示集 20 题、季度轮换池 20 题 [E: ext-evaluation.md#3] | — |
| §9.27 | **search-time contamination** | 评测带搜索的 agent 时，检索步骤命中评测集本体。实测命中率 HLE 3.36–3.44% / GPQA 1.90–4.15% / SimpleQA 0.99–1.20%；**SimpleQA 上被污染样本准确率 100% vs 未污染约 7%** [E: ext-evaluation.md#D2] | 我们独有且最危险 |
| §9.28 | **Goodhart 防线** | 门通过率永不对外报告；每个能力指标必须配一个完整性指标成对上报 [E: ext-evaluation.md#R1, #R2] | §1.4.4 |
| §9.29 | **弃权 / abstention** | 明确写「证据不足，未下结论」。主评分采用非对称计分：答对 +1、明确弃权 0、**自信错误 −2**（标为 verified 但人裁判定为错）[E: ext-evaluation.md#R3] | 0-1 计分惩罚弃权，会把系统训成「不确定时猜」 |
| §9.29a | **留存分档 / retention_tier** | `A` / `B` / `C`，见 §8.6。与 `evidence_grade` 正交，**只能下调** | 由取得渠道与权利信号决定 |
| §9.29b | **tier_reason** | 导致当前 `retention_tier` 的降级触发器 ID 列表，取自 §8.6.3 的封闭枚举 | 必填 |
| §9.29c | **legal hold** | 一个人工开关，置位后暂停该记录的一切自动删除与 TTL 降级，直到人工解除 | TTL 必须可暂停，不是无条件定时销毁 |
| §9.30 | **P-1 结构偏置**（前代教训的正确版本） | 在 N≤6、单领域、无 p<0.05 的证据下，**没有**理由相信「结构必然提升推理质量」，因此结构投资必须自证增益（A/B），而不是默认无罪；但同样**没有**理由断言结构必然有害。唯一被多轮复制的结构收益是**可审计性与有界 resume 状态** [E: GROUND-TRUTH-CORRECTIONS.md#B] | **这是一条有界的、标明证据强度的设计偏置，不是最高禁令。** v1 把它当 P-1 最高禁令，地基被一手考古削弱（对象错配、趋势线拼接、−0.39 主要是渲染伪影、"纪律是最大杠杆" 只存在于 N=1、统计量疑似伪造、P12 已被本仓库自身证伪） |

### §9.31 可检验断言

- **V9.1** 文档 lint：其他文档中出现本文件定义句的 5-gram 重复即失败（复述检测）。
- **V9.2** 文档 lint：其他文档中出现不在 §9 表内、且被当作专有名词使用的术语（首字母大写或加粗的名词短语）即报警，需人工确认后回填本表。
- **V9.3** 文档 lint：单独出现的「饱和」「provider」「默认值」「轮预算」「确定性」五个词若未带限定语，即失败（分别见 §9.13 / §9.25 / §9.23 / §9.24 / §6.1，检查项 V6.8）。
- **V9.4** 文档 lint：任何文档中出现 raw agreement 数字而未并排给出 κ，即失败（§6.4）。
- **V9.5** 文档 lint：任何文档中出现「gate pass rate」或百分比形式的门通过率作为对外指标，即失败（§1.4.4）。

---

## §10 本文件自身的已知薄弱处（供攻击者优先瞄准）

诚实记账适用于本文件自己。以下是我知道的弱点：

1. **§1.5 的 `S` 函数从未运行过。** 它是从证据推导出来的设计，不是被测量出来的行为。所有「结构性消灭某类攻击」的判断都是**论证**，不是**证据**——本轮全部安全文献都是「别人的系统被攻击」的结果，没有一条是对我们架构的实测 [E: ext-security-injection.md#未决-11]。RT-1 至 RT-14 跑完之前，这些判断应按「未验证设计假设」对待。
2. **§3.4.2 的 G5 门槛依据来自表格/图表领域**（SciTabAlign），我把它外推到了纯文本文献的锚点要求。该外推未被测量。
3. **§1.5.2 的 `K(kind)` 取值是裁定，不是测量。** 上游簇归并器本身的假合并/漏合并率未知——而 §5.5.2 的 bioRxiv 例子说明生产级模糊匹配器可以把统计量搞错 25 个百分点。
4. **§9.14「检索饱和」无外部证据**，已标注。
5. **§7.2.2 的 PDF 可见性前提可能推翻通道分离**，已标注为必须前移的架构可行性验证。
6. **§2.3.1 关闭了 K-I 的 ST-V 通道**，代价是逻辑推断类断言的最高档只有 ST-A——如果研究的主要产出是推断，这个产品的绿灯密度会很低。这是一个真实的产品风险，不是保守的美德。
7. **中文路径的注入 prevalence 是完全盲区**：本轮检索未找到任何针对中文网页的 IPI 野外测量。**不能假设中文层的注入率低于英文层，只能说没人测过** [E: ext-security-injection.md#未决-18]。
8. **本文件引用的所有 prevalence 与模型分数在 6 个月内会过期。** 野外注入普查基于 2025-10 的 Common Crawl 快照；简历普查显示两年内明显上升；引用幻觉率是 2026-04 快照。凡引用本文件的数字必须连日期一起引用。
9. **§6.5.6 的尾标记契约把「任务是否失败」交给了被测方自述。**〔裁定 · S0 实测〕`.loop/m0/M0-3b.json` 只证明了退出码不可用，**没有**给出一个不依赖被测方配合的替代信号。尾标记能表达「我知道我失败了」，不能表达「我以为我成功了但其实没有」；一个跑飞但自信的 agent 会输出 `RESULT: PASS`。缓解只有两条，都不完整：`E-NOMARK` 判 FAIL（挡住沉默失效），以及承重判定一律交给读产物的确定性门（§6.5.3）。此外**长任务超时与 SIGINT/SIGTERM 路径的退出码语义完全未测**，本条规范在那两条路径上没有实测依据。

---

**文件版本**：v2-draft-1｜**撰写日期**：2026-08-17｜**证据基线**：`research/v2/`（26 文件 / 25 研究维度 = 18 ext + 7 gt，全部产出于 2026-08-17；计数经 06-SURVEY §1.1 实测复核）
