# 03-EVIDENCE-ENGINE — 三通道验证机制、门的实现契约、反伪造接线

> **本文件的地位**：这是系统的核心。它回答一个问题——**门具体怎么实现，它往 `S` 的输入里放什么**。
>
> **本文件不定义任何术语。** 状态枚举、状态函数 `S`、三个正交谓词、claim kind、`evidence_grade`、写权矩阵、身份与独立性规则、门的分级 GC-0/1/2、flag 词表、文件与目录契约、`retention_tier`、术语表——**全部在 `01-CONTRACTS.md`**。本文件引用它们时只写「见 01-CONTRACTS §N」，**不复述定义**。凡在本文件里读到看似定义的句子，那是**实现契约**（这段代码必须怎么写），不是术语定义。
>
> **本文件与 `S` 的关系**：`S` 是纯函数（见 01-CONTRACTS §1.5），本文件不重述它的求值顺序。本文件只规定：**每个门产出什么形状的 `mechanism_results[]` 条目**、**什么条件下产出 `pass` / `fail` / `not_applicable`**、以及**哪些 flag 由哪个门设置**（flag 的语义见 01-CONTRACTS §7.2）。
>
> **写作纪律**：每条载重断言带 `[E: <研究文件>#<锚>]` 或一手 URL。语料标 `unverified` 的数字在引用处一并标注。会失效的数字带 as-of 日期。无外部证据、由本文件裁定的规则标 **〔裁定〕** 并写明「什么会推翻它」。
>
> **硬约束**：本文件任何关于 DSH 运行时的陈述不得与 `research/v2/GROUND-TRUTH-CORRECTIONS.md` 冲突。
>
> **B1 边界（binding）**：本文件描述的任何扇出都必须落在 00-PREMISE B1 允许的三处（覆盖率、同一断言的 N 路独立核验、上下文卫生）之内。**论证链构建、跨 claim 一致性推理、最终裁决不得扇出**。本文件出现的每一处并行都标注它属于哪一处。

---

## §0 阅读地图与全局实现不变量

### §0.1 一句话架构

```
抓取工具执行器 ──▶ admission（§8，确定性闸门）──▶ 证据池
                                                    │
                       ┌────────────────────────────┼────────────────────────────┐
                       ▼                            ▼                            ▼
                  数据通道门（§2）           文献通道门（§3）            推断通道门（§4）
                  G-RERUN / G-DEP        G-L0 / G-L1 / G-L2 / G-ENTAIL   G-DAG / G-WARRANT / G-REDERIVE
                       └────────────────────────────┼────────────────────────────┘
                                                    ▼
                        跨通道核算门（§5A）  G-CTR-SCAN / G-CTR-JUDGE / G-CLUSTER
                            （产 counter_evidence_* 与 independent_cluster_count）
                                                    ▼
                            来源完整性门组（§5）  T0 / T1 / T2
                                    图表证据门（§6）
                                    反伪造绑定门（§7）
                                                    ▼
                                          mechanism_results[] + flags[]
                                                    ▼
                                          S（见 01-CONTRACTS §1.5）
                                                    ▼
                                          claims/<id>.status.json
```

**唯一写者**：所有门产物由门代码写（01-CONTRACTS §4 W-04 / W-05 / W-08）。本文件描述的任何机制都不得开出第二条 status 写路径——**注意这是本文件对自己的设计纪律，不是运行时保障**：保障的真实强度分两层，见 01-CONTRACTS §0.2 与本文件 EE-0.5。

### §0.2 统一门输出信封（EE-0，强制）

**每一个门，无论 GC-0 / GC-1 / GC-2，必须输出下列信封。字段缺失即门红。**

```jsonc
{
  "gate_id":        "G-RERUN",          // 本文件定义的门标识
  "gate_class":     "GC-0",             // 取值见 01-CONTRACTS §6.1
  "applicable":     true,               // 适用性判定，先于 verdict
  "applicability":  { "reasons": [...], "unmet": [...] },
  "verdict":        "pass" | "fail" | "not_applicable",
  "power":          0.72,               // 或 null
  "power_basis":    "closed-form" | "construction" | "calibrated-kappa"
                    | "external-frame" | "unmeasured",
  "error_asymmetry": { "fp": "≈0 by construction", "fn": "unmeasured" },
  "params":         { ... },            // 判定用到的全部参数（阈值/容差/快照日期/模型 id）
  "inputs_hash":    "sha256:…",         // 本次判定的全部输入的规范化哈希
  "data_as_of":     "2026-08-14",       // GC-1 必填，GC-0 为 null
  "gate_version":   "…",
  "generator_version": "…",             // 自证签名，见 01-CONTRACTS §4 W-08
  "caveats":        [ ... ]
}
```

**EE-0.1** `applicable == false` ⇒ `verdict` 必须是 `not_applicable`。**`not_applicable` 永远不得被任何聚合器当作 `pass`**。这一条是对前代最严重缺陷的直接对治：前代的 rigor 门对「伪造 metric + 无 transform + 无原始数据」返回 `exit 0 PASS` [E: GROUND-TRUTH-CORRECTIONS.md#C1]。
**不遵守会发生什么**：`not_covered` 被静默计为通过，产品的绿灯变成「我们没看」的同义词。这是 01-CONTRACTS §1.4.1 要拆开 `unverified` 与 `not_covered` 的全部理由。

**EE-0.2** `power` 与 `power_basis` 必须成对出现，且 `power_basis` 取值受限于上面五值。各值的含义与本文件各门的归属：

| `power_basis` | 含义 | 本文件中的门 |
|---|---|---|
| `closed-form` | 检出功率有解析式且已被蒙特卡洛验证 | G-GRIM（`power = max(0, 1 − N·items/10^d)`，见 01-CONTRACTS §6.2.1） |
| `construction` | 假阳率由构造给出（≈0），假阴率未测 | G-L1、G-RETRACT、G-HIJACK、G-PROV、G-ADMIT |
| `calibrated-kappa` | 上线门槛是本项目自建校准集上的 Cohen κ | 全部 GC-2 门（G-L2、G-ENTAIL、G-WARRANT、G-CHART-*） |
| `external-frame` | 只有外部基准的精度数字，必须连口径三元组一起写进 `params` | G-L0 |
| `unmeasured` | 无任何可报数字 | G-REDERIVE 的反例搜索召回率 |

**EE-0.3 `unmeasured` 的门可以判 `fail`，不得单独把状态推到最高档。** 降级方向的误判是安全的（多判 `unverified`），升级方向不是。
**例外与它的理由**：G-L1 的 `power_basis` 是 `construction` 而不是 `unmeasured`，因为「归一化后的字符串是冻结快照抽取文本的子串」是一个**哈希可复核的事实**，不是估计量——它的假阳率由构造给出。**但它的假阴率确实未测**（见 §3.3.4）。这两件事必须分开写，合并写就是我们要消灭的那种口径失真。

**EE-0.4 GC-2 的门必须在 `params` 里写 `{provider, model, prompt_hash, judge_version, kappa, kappa_calibration_date, kappa_set_size}`。** 缺任一即门红。κ 阈值见 01-CONTRACTS §6.4。

**EE-0.5 任何门都不得写 `status` 字段。** 门写 `mechanism_results[]` 条目与 flags；`status` 由 `S` 算。
**这条的强制力分两层，必须按 01-CONTRACTS §0.2 的两层表如实陈述**：①工具面（claim 提交工具 schema 不含 `status`，出现即 `tools/pre-execute` deny）是**结构性**的；②文件面（`.arc/claims/*.status.json`）**没有文件系统级强制**，因为 `run_code` 同时绕过内核沙箱与 `ctx.fs` 围栏。
**本文件不得把「系统中不存在任何一条从 agent 输出到 status 的写路径」当作已建立的保障引用**——那句话已在 R2 从规范源删除。准确表述：*能结构性保证 agent 不能经工具路径写 status；只能靠事后审计发现它绕过工具路径写*。真正的收口在 M0（`gate_integrity.sh` + 门轨道与 producer 轨道的进程级隔离），见 01-CONTRACTS §0.2。
**这条对本文件的直接后果**：§5A、§7 中一切「门自己算、producer 伪造不了」的论证，其上界都是「伪造者没有 `run_code`，或有 `run_code` 但没有调用门自己的库函数」。凡本文件写「不可伪造」处，一律读作「经工具路径不可伪造」。

**EE-0.6 门报告是全集，`mechanism_results[]` 是判定路径上的子集。**
每个门无论是否在判定路径上，都必须把 EE-0 信封写进 `gate-reports/<run_id>/<gate>.json`（01-CONTRACTS §4 W-08）。一个门的信封**被复制成该 claim 的 `mechanism_results[]` 条目，当且仅当该门在这条 claim 的判定路径上**。判定路径由三条规则唯一确定，全部可机器判定：
- ① **文献通道按 kind 路由分叉**（§3.1.1）：`sub_mode == T` 的判定路径**不含任何 GC-2 门**。
- ② **子门不单独进 mechanism_results**：G-DEP 之于 G-RERUN（§2.4），其 verdict 经父门传导。
- ③ **只否决门只在判否决时写条目**：G-CTR-JUDGE（§5A.2）判「不构成反证」时只写 gate-report，不写 `mechanism_results[]` 条目。

**不遵守会发生什么**：01-CONTRACTS V1.4 断言「不存在 `status == verified` 且 `mechanism_results` 含 `gate_class == GC-2` 的 claim」。若把「跑过的门」等同于「判定所依据的门」，一条 `applicable=false / verdict=not_applicable` 的 GC-2 审计记录就会让每一条本该 ST-V 的 K-L-T claim 违反 V1.4——**产品绿灯再一次全空，而且这次是被一条「我们跑了但不适用」的记录清空的**。
**机器检查**：`mechanism_results[] ⊆ gate-reports[]`（按 `gate_id + inputs_hash` 匹配），且路由外的门不出现在前者中（NT-G-6）。

**EE-0.7 每个信封必须携带 `computed_at`；复核期重跑产出的信封必须同时携带 `revalidated_at`。**
依据是 01-CONTRACTS §8.6.2.1 的收口：默认档 Tier B 下 `source_integrity` 的字节同一性子测试依赖重取，而重取本轮实测 3/5 成功，因此 **`status` 是带时间戳的量，不是永久属性**。两个字段的语义在 01-CONTRACTS §8.6.2.1，本节不重述。
**不遵守会发生什么**：一条初判 ST-V、复核期重取不到的 claim 会以「已核验」的形态停在交付物里，而它此刻真实的状态是 ST-N。**没有时点的 verified 是一句过期的话。**

### §0.3 本文件的裁决索引

| 编号 | 裁决 | 位置 |
|---|---|---|
| 〔裁定 D-1〕 | 容差二制式：regime 由**实测**决定，不由声明决定 | §2.2 |
| 〔裁定 D-2〕 | 容差带宽上限 `σ̂/|s̄| ≤ 0.10`，超出即 `not_applicable` | §2.2.4 |
| 〔裁定 D-3〕 | 禁网由容器网络命名空间提供；容器不可用即 `not_applicable`，不得用「沙箱模式已配置」充数 | §2.3 |
| 〔裁定 D-4〕 | 依赖性检查（反常数 / 反 ε-依赖）是重跑门的**子测试**，失败即重跑门 `fail` | §2.4 |
| 〔裁定 D-5〕 | 本项目不做「从散文抽 claim」，抽取误差前移到 producer 侧的结构化载荷提交 | §3.1 |
| 〔裁定 D-6〕 | L0 采用规则型验证器而非工具增强 agent，理由是 FPR 不是 recall | §3.2.2 |
| 〔裁定 D-7〕 | K-I 的量词/模态用受控枚举 + 偏序，散文强度不参与判定 | §4.2.3 |
| 〔裁定 D-8〕 | 独立复核者盲判：先只给前提与 warrant，不给结论 | §4.4.1 |
| 〔裁定 D-9〕 | 图表 P1（印刷标签）走视觉模型时上限 ST-A；只有当标签是 PDF 文本对象时才回到文献通道并可达 ST-V | §6.2.2 |
| 〔裁定 D-10〕 | `estimated` 的禁止参与由**结构化载荷的引用图**强制，不由散文扫描强制 | §6.7 |
| 〔裁定 D-11〕 | admission 不得调用时钟；`retrieved_at` 由抓取工具在 fetch 时写入 | §8.1 |
| 〔裁定 D-12〕 | 扰动下的**崩溃**既不计敏感也不计不敏感；它是第三种观测，必须换扰动级别重试，全级别崩溃即 `not_applicable` | §2.4.1 |
| 〔裁定 D-13〕 | 文献通道**没有固定流水线**，只有按 `sub_mode` 分叉的两条判定路径；K-L-T 路径不含任何 GC-2 门 | §3.1.1 |
| 〔裁定 D-14〕 | `counter_evidence_searched` 由**门自算的同快照扫描**与**工具痕迹校验**共同决定，永不读 producer 的自报布尔 | §5A.1 |
| 〔裁定 D-15〕 | 簇归并的低置信合并**允许自动执行**（因为它只降不升），但**不得回写 `work_id` 身份**；两种合并是两个操作 | §5A.3 |

### §0.4 本文件引入的新标识符（01-CONTRACTS §9 的回填候选）

01-CONTRACTS §9.31 的 V9.2 要求：其他文档中出现不在 §9 表内、且被当作专有名词使用的术语即报警，需人工确认后回填。**本文件确实引入了下列标识符，全部在此显式声明，没有一个是悄悄造的**：

| 标识符 | 性质 | 是否需要回填 §9 |
|---|---|---|
| `G-*`（门 id）、`EE-*`（实现规则 id）、`NT-*`（负向用例 id） | 本文件内部编号 | 否——它们是编号不是术语 |
| `applicable` / `power_basis` / `error_asymmetry` / `caveats` | 门输出信封字段（§0.2） | **是**——它们跨文档被 `mechanism_results[]` 消费 |
| `regime ∈ {deterministic, stochastic}` | K-D 的容差制式（§2.2.1） | **是**——与 GC-0/1/2 同名不同义，不消歧会制造混淆 |
| `ni_polarity ∈ {evidence_of_problem, expected_to_be_reported}` | 信号问题字段（§4.3.1） | **是** |
| `quantifier` / `modality` 五值与三值枚举 | K-I 强度偏序（§4.2.3） | **是** |
| `CLEAN / FLAGGED / SUSPECT / NOT_COVERED` | **来源完整性门组的内部中间态**，取自语料 [E: ext-literature-integrity.md#2]，经 §5.1 的映射表转成 01-CONTRACTS §1.2 的 `source_integrity` 与 flags | **是，且需要人工确认**——它与 `source_integrity` 值域部分同形但不同义，是本文件最可能被读成「第二套状态枚举」的地方。若评审认为风险大于收益，应删掉这四个名字，直接在 §5.1 写映射 |
| `decorative_input` / `perturbation_crash` / `input_insensitive` / `perturbation_undetermined` | G-DEP 的 `caveats` 取值 | 否——`caveats` 是自由标签位，但若要进判定则必须先进 §7.2 的 flag 词表 |
| `differs` / `same` / `undetermined` | G-DEP 逐 (输入, 扰动级, key) 的**观测三值**（§2.4.1） | 否——门内部观测值，只出现在门的 `params`，不跨文档消费 |
| 扰动阶梯 `P-a` / `P-b` / `P-c` | G-DEP 的扰动级编号（§2.4.1） | 否——编号不是术语 |
| `counter_candidates[]` | G-CTR-SCAN 产出、G-CTR-JUDGE 消费的候选反证跨度列表（§5A.1） | 否——门间内部结构，不进交付物 |
| `counter_search`（`tool/result.data.meta.evidence` 的子对象，含 `claim_id / polarity / query_norm`） | 抓取工具执行器必须写的反证检索痕迹（§5A.1） | **是**——它是抓取工具契约的一部分，02/04 必须接住 |
| `cluster_map` / `nominal_source_count` | G-CLUSTER 的产出（§5A.3）；`nominal_source_count` 即 01-CONTRACTS §5.5 R-I6 要求与独立簇数并排展示的「名义来源数」 | **是**——进交付物，跨文档消费 |
| `polarity ∈ {support, counter}` | 检索工具调用参数上的受控字段（§5A.1） | **是**——它是工具 schema 的一部分，落在 01-CONTRACTS §4.4 的强制点上 |

**这一节本身就是对 V9.2 的兑现**：不是「我没造词」，而是「我造了这些，逐条列出，等回填」。

---

## §1 三通道共享的前置：证据的可用形态

在任何通道门跑之前，证据必须已经通过 admission（§8）并具备下列形态。**这一节不是设计选择，是上游研究的硬结论。**

### §1.1 通道分离摄取是三条通道共同的地基

抓取管线必须把页面拆成互不混合的字段 `rendered_text` / `non_rendered_text` / `structured_data` / `http_headers`，**只有 `rendered_text` 进入可引用证据池**（规则原文见 01-CONTRACTS §7.2.2）。
数字依据：野外普查 1.2B URL / 24.8M host / 15,387 条已验证注入（Common Crawl 2025-10 快照），**10,779 / 15,387 = 70.0%** 的注入落在非渲染通道（HTTP 响应头 7,887 + 结构化数据 1,996 + 注释 675 + meta 221）；抽取表示本身是 20 倍杠杆——纯文本合规率 3.9%、HTML 标记 1.1%、渲染快照 1.1%、原始 HTTP 响应 0.2%（5,200 次试验 = 100 提示 × 4 表示 × 13 模型）[E: ext-security-injection.md#V5, #V6, #V7]。

**⚠️ 一个可能推翻本节的架构前提**：若 PDF 抽取管线拿不到「这段文字是否对人可见」的信息，通道分离在 PDF 路径上失效，而 PDF 是学术场景的主要摄取对象。这条必须在 M0 前移验证（RT-5），不是测试阶段的事 [E: ext-security-injection.md#未决12, #RT-5]。**本文件全部三条通道的门在 PDF 路径上的有效性都以这条为前提。**

### §1.2 三条通道对同一份证据的三种用法

| 通道 | 消费证据的哪一部分 | 主门 | 可达状态上限（见 01-CONTRACTS §2.4） |
|---|---|---|---|
| K-D 数据 | CAS 中的**数据字节** + `run.py` + 环境锁 | G-RERUN + G-DEP（GC-0） | 封闭式 ST-V / 开放式 ST-A |
| K-L 文献 | 快照的 `rendered_text` + `anchor_span` | G-L0（GC-1）/ G-L1（GC-0）/ G-L2（GC-2） | K-L-T ST-V / K-L-A ST-A |
| K-I 推断 | **其他 claim 的 status.json**，不直接消费证据 | G-DAG（GC-0）+ G-WARRANT / G-REDERIVE（GC-2） | ST-A |

**注意 K-I 那一行的特殊性**：推断通道的输入是别的 claim 的状态，因此它是三条通道里**唯一会被状态传导污染**的一条——一个前提被降级，所有依赖它的推断必须重判（`stale` 语义见 01-CONTRACTS §9.17）。这条链是 §4.6 的全部内容。

---

## §2 数据通道：重跑门（G-RERUN）与依赖性门（G-DEP）

必备工件与六个 fail-closed 点见 01-CONTRACTS §2.1，本节不重述；本节写**门代码怎么实现**。

### §2.1 G-RERUN 的执行序列

```
1. 建全新临时目录 T（每次判定一个，判定后删除；不复用）
2. 从 CAS 按 {path, sha256} 逐个物化输入到 T   ← 任一 sha256 不匹配/缺失 → verdict=fail
3. cp analysis/<claim_id>/{run.py, uv.lock} → T
4. uv sync --frozen                            ← 非零退出 → verdict=fail
5. 在禁网容器内执行：
     PYTHONHASHSEED=0 SEED=<claim.seed> python run.py
   硬超时 = claim.budget.wall_s（缺省见 §2.5）
6. 读 T/out.json                               ← 缺失/不符 schema → verdict=fail
7. 逐字段数值比对（§2.2）                        ← 任一超容差 → verdict=fail
8. 交叉检查：claim 引用的每个 key ∈ out.json 的 key 集合
9. 调 G-DEP（§2.4）                             ← G-DEP fail → G-RERUN fail
```

**第 7 步必须是数值比对，不是字符串比对。** 这是绕开 nbval 全部假失败面的关键：nbval 比对的是含内存地址的富输出文本 repr（`<AxesImage at 0x7f2cb3374198>`）、dict 顺序、时间戳、RNG，且默认不做任何 sanitize；papermill 则根本不比对输出 [E: ext-reproducibility.md#B1, #B2]。
**不遵守会发生什么**：门变成 false-red 制造机，两周内会被关掉或被加白名单绕过——这正是「空心门」的标准诞生路径。

**逐字段比对的类型规则（EE-D-1）**：
- 标量：按 §2.2 的容差判定。
- 数组：先比长度（长度不等即 fail），再逐元素按同一容差判定。
- 对象/字典：**默认按键集合 + 逐键递归**，键顺序不参与比对。
- 集合语义（无序）必须由 producer 在 `tolerance` 中显式声明 `"unordered": true`，**否则按有序处理**。默认有序是故意的：默认无序会让「顺序错了但集合对了」这种真实缺陷静默通过。

### §2.2 显式容差公式〔裁定 D-1〕

**采用的公式**（语料中唯一一个被明确操作化的客观门定义，逐字采纳）：

> 提交的解法代码在基准的官方评估器上**独立重跑**，与论文声称的数值比较，容差为 **`max(1%, 3σ/|s̄|)`** 以吸收评估器方差。
> [E: ext-science-agents.md#Science One / Chain-of-Evidence, #设计含义2；一手：arXiv:2605.26340]

语料对这条的评语逐字是「**这是本轮唯一一个被明确操作化的客观门定义，直接可用**」[E: ext-science-agents.md#设计含义2]。

**但这条公式单独用会开一个洞**：它的下界 1% 对确定性脚本过于宽松（一个确定性脚本重跑应当逐位相同），而它的上界没有封顶（σ 大时容差可以宽到任何断言都能「复现」）。因此本文件采用**二制式**：

#### §2.2.1 regime 是测出来的，不是声明的

```
测定过程（每条 K-D claim 判定时执行一次）：
  以 R=5 个互不相同的 seed 各跑一次 run.py（其中一次用 claim 声明的 seed）
  若 5 次的 out.json 逐字节相同        → regime = deterministic
  否则                                  → regime = stochastic
```

**术语消歧（必读）**：这里的 `regime = deterministic / stochastic` 说的是**脚本本身在换 seed 后是否逐字节可重现**，与 01-CONTRACTS §6.1 的门分级（GC-0/1/2）**没有关系**。G-RERUN 无论落在哪个 regime 都是 GC-0——它的判定函数不含模型。混用这两个意思会让「重跑门是确定性的吗」这个问题无法回答。

**为什么必须是测出来的**：若 regime 由 producer 声明，攻击面立刻出现——声明 `stochastic` 即可换到宽容差。测定把这条路堵死：一个真正确定性的脚本无论怎么声明都会被判为 `deterministic`，一个真正随机的脚本无论怎么声明都会被判为 `stochastic`。
**若 producer 的声明与实测不符**：不判门红，改判 regime 并按实测 regime 重算容差，同时在 `caveats` 里记录不一致。**理由**：声明与实测不符最常见的原因是 producer 不知道自己用的库有隐藏随机性，把它判成造假是假阳性；而按实测走已经消灭了它的收益。

#### §2.2.2 deterministic regime 的容差

```
逐字段：|v_rerun − v_claim| ≤ atol + rtol · |v_claim|
默认    rtol = 1e-9，atol = 0（producer 可在 tolerance 中按字段覆盖，只能收紧不能放宽）
```
默认值取自语料给出的 claim schema 示例 `"tolerance": {"value": {"rel": 1e-9}, "p": {"rel": 1e-6}}` [E: ext-reproducibility.md#2 数据类 claim 最小 schema]。1e-9 是浮点重排噪声带，不是「差不多就行」。

#### §2.2.3 stochastic regime 的容差

```
逐字段：|v_rerun − v_claim| ≤ max(0.01, 3·σ̂_f / |s̄_f|) · |s̄_f|
其中    s̄_f = R 次重跑中字段 f 的样本均值
        σ̂_f = R 次重跑中字段 f 的样本标准差（无偏，R−1 分母）
        R    = 5〔裁定〕
```
`v_claim` 是 claim 记录里冻结的值（由 claim 声明的 seed 那一次产出）。判定用 `s̄_f` 作为中心而不是 `v_claim`，因为 `v_claim` 本身是随机变量的一次抽样。

**R = 5 的理由**〔裁定〕：R 是成本与 σ̂ 稳定性的折中。R=5 时 σ̂ 的相对标准误约 35%，这是明知的粗糙；语料没有给出任何关于 R 的建议值，所以这是本文件的裁定而不是引用。
**什么会推翻**：若在自建的封闭式回归集上，同一 claim 用 R=5 与 R=20 估出的容差带宽差异导致 verdict 翻转的比例 > 5%，则 R 必须提高，或改为「先跑 R=5，若 σ̂/|s̄| 落在 [0.005, 0.02] 的判定敏感带内则加跑到 R=20」的两段式。

#### §2.2.4 容差带宽的硬上限〔裁定 D-2〕

```
若 σ̂_f / |s̄_f| > 0.10  →  该字段 applicable = false，verdict = not_applicable
```
**理由**：容差带 3σ/|s̄| > 0.30 意味着「复现」这个词已经不携带信息。锚点是同一语料里的另一条实测：**8% 的误差足以翻转「A 优于 B」这类比较结论**——这是图表读数章节给出的判据，被用来限定 `estimated` 不得参与比较 [E: ext-multimodal-evidence.md#D1, #12]。一个 30% 宽的容差带比那个 8% 大近四倍。
**什么会推翻**：若真实研究任务中出现大量**合法**的高方差量（小样本 bootstrap、罕见事件率、重尾分布的均值），使 `not_applicable` 成为多数状态，则改为按 claim 的**下游用途**分档：仅描述性使用的量放宽到 0.30，进入任何比较/排序/阈值的量收紧到 0.05。

#### §2.2.5 `|s̄_f| ≈ 0` 的退化

相对容差在 `s̄_f → 0` 时退化。规则：若 `|s̄_f| < atol_floor_f`，则该字段必须由 producer 在 `tolerance` 中声明绝对容差 `atol_f`；**未声明即 `applicable = false` → `not_applicable`**（不是 pass）。`atol_floor_f` 默认取 `1e-12`〔裁定，工程常数〕。
**不遵守会发生什么**：一个恒为 0 附近的字段会以任意精度「通过」相对容差判定——这是一个结构上不会红的检查。

### §2.3 重跑环境契约〔裁定 D-3〕

| 要素 | 实现 | 不遵守会发生什么 |
|---|---|---|
| 输入按哈希物化 | 从 CAS `objects/<sha[:2]>/<sha256>` 复制到临时目录，复制后重算 sha256 校验 | 数据被换掉而门看不见；「可重跑」退化为「同一台机器上碰巧还在的那份文件」 |
| 锁文件 | `uv sync --frozen`，`env_lock_sha256` 入 claim 记录并参与 `inputs_hash` | 依赖漂移会让重跑在几周后无声失败，且失败原因指向 claim 而不是环境 |
| 种子 | 显式 `seed` + `PYTHONHASHSEED=0` | 字典/集合迭代顺序变化会制造假失败，进而催生「加白名单绕过」 |
| **禁网** | **pinned OCI 镜像 + 容器网络命名空间关闭**（`container run --network none` 语义） | 见下 |
| 数值比对 | §2.1 第 7 步 + §2.2 | 见 §2.1 |
| 临时目录 | 每次判定新建，判定后删除，不复用 | 上一次 run 的残留会让第二次「通过」 |

**关于禁网，必须诚实写出的一手事实**：
- DSH 的内核沙箱**只管文件效应，不拦网络**。`SandboxMode` 类型注释逐字："Network and process visibility are outside this vocabulary."；bwrap 参数里**没有** `--unshare-net`；Seatbelt profile 是 `(allow default)` 打底只 `(deny file-write*)`；Landlock 只表达路径 grant [E: gt-exec-security.md#A-1~A-4, GROUND-TRUTH-CORRECTIONS.md#A7]。
- `run_code` **完全不经过 `ctx.sandbox`**，且它**同时绕过**内核沙箱（只管 bash）**和** `ctx.fs` 策略围栏（只管 ctx.fs 工具）[E: GROUND-TRUTH-CORRECTIONS.md#A7, gt-exec-security.md#D]。
- 子代理**不继承**父的沙箱限制作为下限 [E: GROUND-TRUTH-CORRECTIONS.md#A8]。

**因此**：
**EE-D-2**〔裁定 D-3〕 重跑必须在**容器网络命名空间关闭**的进程里执行，**不得**用「`sandbox/mode` 已配置为 workspace-write」或任何 DSH 沙箱声明来充当禁网证据。
**EE-D-3** 重跑器**不得**走 `run_code` 路径（它绕过一切围栏）；只能走 bash 路径下的容器执行。
**EE-D-4** 若本机不具备容器执行能力，G-RERUN 的 `applicable = false`，`verdict = not_applicable` → ST-N。**fail-closed，不降级为「沙箱内跑一次算了」。**
**不遵守会发生什么**：一个联网的分析脚本可以在重跑时去线上重新拉一遍数据，于是「输入按哈希物化」这一整套变成装饰品；更糟的是它会**稳定地重现**——重跑门会给它盖 ST-V。

**逃生口与迁移**：`sandbox-exec` 的弃用时间线未知（apple/containerization #737 至 2026-05-12 无 Apple 回复）；把「同一 `run.py` 能在 pinned OCI 镜像里跑」写进契约，使切换到 `container run`（1.0.0 于 2026-06-09 发布，1.2.2 于 2026-08-08）成为零改动操作 [E: ext-reproducibility.md#未决3]。

### §2.4 G-DEP：输出必须真依赖输入（反常数 / 反 ε-依赖）〔裁定 D-4〕

**这是本节最重要的门，因为没有它，G-RERUN 是一个几乎不会红的检查。**
论证：一个把结论数字**硬编码**在 `run.py` 里的脚本，会完美通过输入哈希校验、完美通过环境锁、完美通过禁网、完美通过数值比对——因为它每次都输出同一个数。它拿到的是 ST-V。前代的实测形态与此同类：伪造一个 metric、无 dvc.yaml、无 transform、无原始数据 → **exit 0 PASS** [E: GROUND-TRUTH-CORRECTIONS.md#C1]。

G-DEP 是 G-RERUN 的**子测试**，它的 `verdict` 直接决定 G-RERUN 的 `verdict`（G-DEP fail ⇒ G-RERUN fail ⇒ base = ST-U）。它**不需要新的 flag**——降级路径已经由 01-CONTRACTS §1.5 第 1 步覆盖。

#### §2.4.0 观测三值与扰动阶梯〔裁定 D-12〕（本节的地基，先于四个子检查）

**为什么这一小节存在**：前一版把 C-3 的通过条件写成「脚本**要么**非零退出，**要么**输出差异 > τ_f」，又在 C-4 里把崩溃计为「敏感」。两条合起来给出一条完整的绕过：**一个把结论硬编码、同时对输入做严格校验（校验和 / 行数断言 / schema 断言）的 `run.py`，在每一次扰动下都崩溃，于是每一次都被计为「敏感」，G-DEP 全绿，G-RERUN 全绿，硬编码的数字拿到 ST-V。** 崩溃与「对输入不敏感」在旧写法里可以互相顶替——而 G-DEP 存在的全部理由就是抓这一类。

**修法**：把「敏感 / 不敏感」这个二值判断拆成**三值观测**，并让崩溃单独占一个值，任何一侧都不吃它。

```
逐 (输入 i, 扰动级 P, 被引用 key f) 产出一个观测：
  differs       ← 脚本退出码 == 0 且 out.json 有效 且 |v'_f − v_f| >  τ_f
  same          ← 脚本退出码 == 0 且 out.json 有效 且 |v'_f − v_f| ≤  τ_f
  undetermined  ← 脚本非零退出 / 超时 / out.json 缺失或不符 schema
                  （**不产生任何关于依赖性的信息**）
τ_f 是该字段按 §2.2 算出的容差带；regime 与 τ_f 在 G-DEP 内沿用 G-RERUN 本次判定的实测值，不重测。
```

**三值的判定规则（这是 D-12 的全部内容）**：
- `differs` 是**唯一**能满足敏感性断言的观测。
- `same` 是敏感性断言的**反证**。
- `undetermined` **既不满足也不反证**。它不进任何合取/析取，只触发**扰动级升降**（见下）与 `caveats`。

**扰动阶梯（固定三级，按序尝试，级别定义写死在门代码里，producer 不可参数化）**：

| 级 | 构造 | 破坏了什么合法域 | 用途 |
|---|---|---|---|
| **P-a** | 数值列相对扰动 `δ = 1e-2`；**保 dtype、保符号、保整数性**（整数列用 `±max(1, ceil(|v|·δ))`）；非数值列做保结构的合法变更（类别标签整体重命名，保持基数与频次分布） | 值域约束（如「年龄 ∈ [0,120]」「概率 ∈ [0,1]」）可能被破坏 | 首选，信噪比最高 |
| **P-b** | **行子采样**：固定 seed 丢弃 10% 的行，列集合、dtype、每个单元格的值全部不变 | **构造上不破坏任何逐值域约束**——它只改变行数与样本组成 | P-a 崩溃时的降级路径；**任何真实依赖输入的聚合量在 P-b 下几乎必然变化** |
| **P-c** | 空输入：schema 相同、数值列全 NaN、行数保留（原 C-3） | 破坏「非空/非 NaN」类断言 | 抗硬编码的最强一击，也是 P-a 落在数值精度以下时的兜底 |

**级间规则**：对每个输入 `i`，门按 `P-a → P-b → P-c` 逐级执行，**每一级都跑，不因前一级得到 `differs` 就跳过**（跳过会让攻击者只需要让一级产生差异）。三级全部执行完毕后才做判定。

**为什么 P-b 是这条修复的关键**：旧 C-4 把崩溃计为通过的理由是「扰动经常破坏数据的合法域，判红是假阳性」。这个理由**只对 P-a / P-c 成立**。P-b 不改变任何一个单元格的值，因此「合法域被破坏」这条辩护在 P-b 上不存在——一个在 P-b 下崩溃的脚本，是在对输入做**精确规模或精确内容**的断言（行数固定、校验和固定）。那不是稳健性，那是**扰动检测器**，而扰动检测器正是硬编码脚本用来把自己伪装成「敏感」的部件。

#### §2.4.1 四个子检查

**C-1 · 输入敏感性（正向）**
断言：**每个被正文引用的 `out.json` key，至少存在一个 (输入 i, 扰动级 P) 使该 key 的观测为 `differs`**。
- 断言不成立且该 key 的观测集合中**存在 `same`** ⇒ 该 key 与全部声明输入无因果依赖 ⇒ `verdict = fail`，设 F-36（01-CONTRACTS §7.2）。
- 断言不成立且该 key 的观测**全部为 `undetermined`** ⇒ 见 C-4。

**C-2 · 输入必要性（反向）**
断言：**每个声明输入，至少有一个被引用的 key 对它产出过 `differs`**。
不满足 ⇒ 该输入是装饰性的。**处理**：不判 fail，记 `caveats: ["decorative_input:<path>"]`，并在门报告中单列。
**理由**〔裁定〕：装饰性输入的常见来源是「脚本读了但只用于校验/日志」，判红是假阳性；但它同时是「看起来有数据」这种伪装的签名，必须可见。
**什么会推翻**：若在自建回归集上，装饰性输入与硬编码作弊高度共现（> 50%），则升级为 fail。
**注意与 C-4 的边界**：一个输入的观测若**全部为 `undetermined`**，它不是装饰性输入（我们根本不知道），不得记 `decorative_input`。

**C-3 · 空输入检测（抗硬编码）〔本轮重写〕**
P-c 级的专有断言：**`same` 即致命**。
```
若存在被引用 key f 使 P-c 观测 == same   ⇒  verdict = fail   （该数字与输入无关）
若 P-c 观测 == differs                  ⇒  计入 C-1 的敏感性证据
若 P-c 观测 == undetermined             ⇒  不计入任何一侧，进入 C-4
```
**与旧写法的差别就是那个「要么」被删掉了**：旧写法允许「非零退出」独立满足 C-3，于是崩溃可以替代差异。现在崩溃在 C-3 里**什么都不是**。
**这仍然是抓硬编码最直接的一击**：一个硬编码脚本若不设扰动检测，P-c 必然给出 `same` → 直接 fail；若设了扰动检测，它会在 P-c 崩溃 → 落进 C-4 的 `not_applicable` 分支 → ST-N。**两条路都拿不到 ST-V，这就是「不能互相顶替」的机器含义。**

**C-4 · 崩溃的语义〔本轮重写〕**
崩溃（非零退出 / 超时 / `out.json` 缺失或不符 schema）产出 `undetermined`，**既不计敏感，也不计不敏感**。逐条规则：
```
1. 记 caveats: ["perturbation_crash:<path>:<级别>"]。
2. 该 (输入, 级别) 的观测不进入 C-1 / C-2 / C-3 的任何断言。
3. 若某输入 i 在 P-a / P-b / P-c 三级上**全部** undetermined
      ⇒ 该输入的依赖性 **不可测定**
      ⇒ 记 caveats: ["perturbation_undetermined:<path>"]
      ⇒ G-DEP 的 applicable = false，verdict = not_applicable   （EE-0.1：**不得当作 pass**）
      ⇒ G-DEP 是 G-RERUN 的子测试 ⇒ G-RERUN 也输出 not_applicable ⇒ ST-N
4. 若某 key 在全部 (输入 × 级别) 上都没有 differs，且观测集非空但全为 undetermined
      ⇒ 同 3，not_applicable，**不是 pass 也不是 fail**。
```
**EE-D-5** 崩溃不得被计为「敏感」。**EE-D-6** 扰动阶梯的三级必须全部执行，级别定义写死在门代码里，`params` 中必须逐级记录 `{level, exit_code, out_json_valid, per_key_observation}`。

**为什么落 `not_applicable` 而不是 `fail`**：我们确实不知道这个脚本依不依赖输入——判 fail 是在断言我们没有测到的东西（升级方向的误判是危险的，见 EE-0.3；但**判 fail 属于降级方向，本身是安全的**，我们仍不这么做，因为 `fail` 与 `not_applicable` 对读者的含义不同，而 01-CONTRACTS §1.4.1 要求这两件事永不合并）。落 `not_applicable` → ST-N 的实际效果与 fail 一样都拿不到 ST-V，但台账里记的是真话：**「我们没能测」，不是「我们测出它是假的」**。
**这条的成本必须写出来**：一个对输入做严格校验的**诚实**脚本（例如开头 `assert df.shape[0] == 10000`）会落 ST-N。它的修复路径是明确且单向的——**producer 放宽校验使脚本能在固定的三级扰动阶梯下运行**，而不是给 producer 一个声明位。任何「producer 可声明本脚本对扰动敏感」的开关都会立刻重建被本条删除的那个绕过。

#### §2.4.2 成本与预算

每条 K-D claim 的重跑次数 = `R(=5) + 3 × n_inputs`（扰动阶梯三级 × 每个输入，§2.4.0）。对 3 个输入的典型 claim 是 **14 次**（旧版是 11 次，因为旧版只有 P-a 与 P-c 两级）。
**这是本轮修复付出的直接成本：+27%。** 它买的是「崩溃不能顶替敏感」——即 G-DEP 从「可被一行 `assert` 整体绕过」变成「绕过的收益是 ST-N」。
**这是本文件里最贵的门。** 预算耗尽时的行为由 01-CONTRACTS §1.5 的 0f / 2e 覆盖（`budget_state`），门本身只负责在超预算时输出 `not_applicable` 并设 F-11。
**并行归属**：G-DEP 的 `n_inputs` 次扰动重跑**互相独立、输出是可比较的 pass/fail**，属于 00-PREMISE B1 允许的第 2 类扇出（同一断言的 N 路独立核验）。它买的可测属性是 `verified 断言数 / 预算`。

#### §2.4.3 G-DEP 能力边界（必须与结论一起说出）

G-DEP 只能证伪「输出不依赖输入」。它**不能**证明：
- 输出依赖的是**正确的那部分**输入（脚本可以读了 A 列却应该读 B 列）；
- 方法正确、样本代表、口径恰当（01-CONTRACTS §2.1 已写明 ST-V 在 K-D 上的语义边界）；
- 数据本身没被投毒。**重跑一万次结果都一样地错**（00-PREMISE B5 的 N7）[E: ext-security-injection.md#N7]。

**§2.4.0 的修复没有解决的那一类（必须与修复一起说出）**：
**依赖注入式硬编码。** 攻击构造是 `out = HARDCODED + (f(x) − C)`，其中 `C` 恰好等于原始输入上的 `f(x)`。在原始输入上它返回 `HARDCODED`；在任何扰动下 `f(x)` 移动，输出跟着移动 → 观测为 `differs` → C-1 / C-3 全部满足 → G-DEP 判 pass。
**为什么 G-DEP 抓不到**：G-DEP 检验的命题严格是「输出是否随输入变化」，而这个构造**确实**随输入变化。它伪造的是**函数形式**，不是依赖关系。
**唯一的减损不在本门**：这一类只能被「`run.py` 的人工/复核者阅读」或「同一断言的第二条独立实现路径」抓到，两者都不在 G-DEP 的能力范围内。**在自建回归集上标定之前，本文件不声称 G-DEP 能抓硬编码的全部形态；它能抓的是「输出与输入无关」与「用崩溃伪装敏感」这两类。**

### §2.5 K-D 的范围硬限与预算

范围硬限（只承接封闭式断言，开放式端到端不得产出 ST-V）与其四个基准依据见 01-CONTRACTS §2.1，本节不重述。

**门侧的落点〔按 01-CONTRACTS §1.5 在 R2 的收紧同步重写〕**：封闭式/开放式的判据**不是一个字段，是一份冻结工件**。`question_authored_by` 已退化为仅供人读的说明字段，**G-RERUN 不得读它来分支**。G-RERUN 必须以 GC-0 的方式检查 01-CONTRACTS §1.5 的三条硬条件（该三条的规范表述在 01-CONTRACTS §1.5，本节不重述），门侧的实现契约是：

**EE-D-7** 分支判据由一个 GC-0 子检查产出布尔 `closed_form`，其输入是 `runs/<run_id>/questions.frozen.json`、`runs/<run_id>/manifest.json` 与 session 日志的 seq 序列。三条中的**第 2 条（manifest 写入事件的 seq 早于本 claim 的第一条 producer `tool/call`）必须按 seq 判定，不得按时间戳判定**——时间戳可被时钟漂移与手写覆盖，seq 是核心分配的单调量（读取 seq 的三个地雷见 §7.1 EE-F-1/2/3，任一遗漏都会让这条时序判据静默失效）。
**EE-D-8** 三条中任一不满足 ⇒ 按开放式处理（base 上限 ST-A），**不是判门红**。理由：缺冻结文件的常见原因是编排层没跑到那一步，判红会把一条诚实的开放式分析变成失败。
**不遵守会发生什么**：若分支仍由自报字段决定，开放式分析只要自称封闭式就能拿 ST-V——这是一条绕过全部范围限制的直路，也是 R1 攻击者 C-9 命中的那一条。**并且**：`question_authored_by` 若仍留在 claim 提交工具的 schema 里，它必须被 `tools/pre-execute` 拒绝（NT-D-13），因为一个仅供人读的字段一旦可写，下一个实现者就会去读它。

**每 claim 时间/token 预算的必要性**：CORE-Bench 里 hard 任务单价是 easy 的 4.6 倍（$2.96 vs $0.64，GPT-4o 2024 价）；移植到 DeepSeek v4 绝对值会低一个量级，但「难任务成本非线性上升」的形状不变 [E: ext-reproducibility.md#5]。因此超预算即 `not_applicable`，**不是无限重试**。

---

## §3 文献通道：L0 / L1 / L2 三层

### §3.0 为什么必须是三层且分开记分

一手实证：链接可访问率 >94%、内容主题相关率 >80%，但**逐条事实核查通过率只有 39–77%**（130 条 query，14 个前沿模型的深度研究报告，引文用**确定性 Markdown AST 解析器**抽取）[E: ext-citation-faithfulness.md#6, #7]。
同一实验的深度消融：GPT-5.4 从 2 次工具调用时的 78.6% 掉到 150 次时的 16.7%（跌 62 个百分点），Claude Opus 4.6 从 80.0% 掉到 57.9%，而**链接有效率与相关率在所有搜索深度上稳定在 92% 以上** [E: ext-citation-faithfulness.md#8]。
**限定必须一起带**：单篇 arXiv 预印本（PwC 产业实验室，2026-05-07 v1），仅两个模型做深度消融，未报相关系数/回归/p 值，判定器是 rubric-based LLM-as-a-judge（有人工校准）[E: ext-citation-faithfulness.md#R1]。**方向可信、量级待自证。**

三层的划分直接采纳语料给出的形状 [E: ext-citation-faithfulness.md#D1]：

| 层 | 判什么 | 门 | gate_class | 能写什么 |
|---|---|---|---|---|
| **L0 存在性** | DOI/URL 可解析；元数据比对；Wayback 三分类 | G-L0 | GC-1 | 只能否决，不能支撑内容断言 |
| **L1 定位性** | 被引用的**具体文字**能在冻结快照的 `rendered_text` 中命中 | G-L1 | GC-0 | 支撑 K-L-T 的 ST-V |
| **L2 支持性** | 那段文字是否真的蕴含该 claim | G-L2 | GC-2 | **只能收窄，永不写 ST-V** |

L1 是我们的差异点。语料对它的定位逐字是：「这是 L0 与 L2 之间**被所有现有系统跳过**的一层」[E: ext-citation-faithfulness.md#D1]。同一语料同时记录：逐字引语的伪造率与 L1 的业界基线**是空白**（只找到线索 arXiv:2601.15476 的 FCR/FFR 指标与 analemma.ai 的说法，均未取一手核验）[E: ext-citation-faithfulness.md#R9]。**这既可能意味着机会，也可能意味着我们低估了难度——两句必须一起说。**

### §3.1 抽取阶段是第一个误差源〔裁定 D-5〕

**证据**：claim 抽取器本身会造出源里没有的东西。四种抽取方法的「抽出的 claim 被源句+上下文+问题蕴含」的比例：Claimify 99.0% / VeriScore 99.2% / SAFE 96.6% / **DnD 89.1%**（73,229 条去重 claim；判定用经验证的 LLM prompt——在 80 条人工样本上仅 5 次冲突，而 NLI 模型冲突 21/26 次）[E: ext-citation-faithfulness.md#33, #E2]。句级「该句是否含可核查事实」的判断准确率最好也只有 91.8% [E: ext-citation-faithfulness.md#34]。
语料的推论逐字：「**前代项目『claim-graph 框架失败』的一个可能的具体机制就在这里：框架假设 claim 抽取是无损的预处理，实际它是最大的单点误差源。**」[E: ext-citation-faithfulness.md#D3]

#### §3.1.1 本项目的处理〔裁定 D-5〕

**本项目不做「从散文抽 claim」。** producer agent 直接提交**结构化载荷**（载荷的含义见 01-CONTRACTS §9.2），因此上面那条流水线的第一段（散文 → claim）在本项目里不存在。
**代价与它的位置**：误差没有消失，它被移到了 producer 侧——producer 仍然会造出源里没有的载荷。

##### §3.1.1.1 文献通道没有固定流水线，只有按 `sub_mode` 分叉的两条路径〔裁定 D-13〕

**前一版在这里写了一条固定流水线**：`producer → G-ENTAIL（GC-2）→ G-L1（GC-0）→ G-L2（GC-2）`。
**这条流水线在契约上让 ST-V 不可达**：01-CONTRACTS §6.1 规定 **GC-2 永不写 ST-V**，而 01-CONTRACTS V1.4 进一步断言「不存在 `status == verified` 且 `mechanism_results` 含 `gate_class == GC-2` 的 claim」。一条固定流水线意味着每条 K-L claim 的 `mechanism_results` 里必然躺着两条 GC-2 记录，于是 01-CONTRACTS §2.4 矩阵里 K-L-T 那个 ✅ **一条也兑现不了**——三条背书通道（K-D 封闭式 / K-L-T / 其余）当场少一条。这与 R1 的 F-14 缺陷是同一种病：一条规则在别处被消费了第二遍，把产品的绿灯清空。

**修法：路由，不是流水线。** 路由判据是 01-CONTRACTS §2.2.1 的判定式本身，纯字符串操作、天然 GC-0：

```
G-L1 无条件先跑（GC-0，无模型、哈希可判）
      ├─ L1-b 载荷包含检验：normalized(payload) ⊆ normalized(anchor_span) ?
      │
      ├── 命中 ⇒ sub_mode = T ⇒ 走【转录路径】
      │        判定路径 = { G-L0(GC-1，否决器) , G-L1(GC-0) , G-CLUSTER(GC-1) , G-CTR-SCAN(GC-0) }
      │        **路径内不含任何 GC-2 门。** base = ST-V（S 第 1 步 K-L-T 分支）
      │
      └── 未命中 ⇒ sub_mode = A ⇒ 走【归因路径】
               判定路径 = { G-L0(GC-1) , G-ENTAIL(GC-2) , G-L2(GC-2) , G-CLUSTER(GC-1) , G-CTR-SCAN(GC-0) }
               base 上限 = ST-A（S 第 1 步 K-L-A 分支）
```

**EE-L-20** `sub_mode` 由 G-L1 的 L1-b 子检验**计算**得出，**不由 producer 声明、不由任何模型判断**。producer 的 claim 记录里若出现 `sub_mode` 字段，提交工具必须 `deny`（同 `status` 的处理，01-CONTRACTS §4 W-03）。
**EE-L-21** **转录路径上的 GC-2 门一律不产出 `mechanism_results[]` 条目**（EE-0.6 ①）。G-ENTAIL / G-L2 在 `sub_mode == T` 时可以照跑并写 `gate-reports/`（作为观测数据，用于测量 §3.1 那条「producer 造出源里没有的东西」的发生率），但它们的信封**不进判定**。
**机器检查**：对每条 `sub_mode == T` 的 claim 断言 `mechanism_results[].gate_class` 中不含 `GC-2`（NT-L-28）；这条与 01-CONTRACTS V1.4 是同一断言的两个方向。
**EE-L-22** 未命中即**降级到归因路径，不是判 fail**。这与 01-CONTRACTS §1.5 第 1 步「K-L-T 锚点包含检验不通过 → 降为 K-L-A 处理」逐字一致，本节只写它的实现落点。

**G-ENTAIL 与 G-L1 的分工必须写清楚，否则会被读成同一个门**：
- **G-L1** 判的是**字面包含**——载荷里的每个数字、命名实体、口径三元组、比较对象是否逐字出现在锚点跨度内。确定性、哈希可判、无模型。
- **G-ENTAIL** 判的是**没有超出源**——载荷里是否混入了源句没说的限定、条件、因果方向。这一步只能由模型做（NLI 模型在这个任务上被实测不可用，见上），因此是 GC-2。

**为什么转录路径可以不要 G-ENTAIL——以及这条论证的边界**：
`sub_mode == T` 的定义就是「载荷的每一个字段都逐字落在锚点跨度内」。载荷里**不可能出现源句没说的限定或因果方向**，因为载荷里的每个 token 都来自源句。G-ENTAIL 在这条路径上要判的那件事，**已经由包含检验在构造上排除**。
**但它排除的只是「多说」，不是「少说」**：载荷可以逐字包含却**漏掉**源句里的关键限定（源句「在小鼠中 X 上升 30%」，载荷只取 `{entity: X, delta: 30%}`）。这一类由两条既有契约接住，本节只指出落点：
1. `metric_frame` 三字段（01-CONTRACTS §9.4）**本身是载荷的一部分**，因此 `sample_or_tier`（「在小鼠中」）必须同样通过包含检验；三字段缺任一直接 ST-N。
2. 渲染层：**K-L-T 的 claim 永远不得以裸事实形态出现在正文里**，必须携带归因（01-CONTRACTS §1.6 V1.6 第 3 条 + W-10 的解析期检查）。
**残留**：**存在于源句、但不落进三元组任一字段的限定语**（「初步结果」「未经重复」「p = 0.06」）仍然会被漏掉。减损见 EE-L-23，它不完全消除该风险。

**EE-L-23**〔裁定〕`anchor_span` 必须以**句子边界**起止（由确定性分句器判定，中英文各一份规则，版本入 `params`），不得是句内片段；门必须把整段 `anchor_span` 原样写进 gate-report，交付层的归因渲染必须能展开到整句。
**理由**：这把「漏限定」从不可见变成可见——复核者与读者看到的是整句，而不是被裁出来的半句。
**它不解决什么**：限定语可以在**上一句**或**同段的别处**（「以上结果均为初步」）。整句闭合抓不到跨句限定。**这是 §10 的 N6（选择性引用）在转录路径上的具体形态，不是一个已解决的问题。**
**什么会推翻**：若确定性分句器在中文双栏 PDF 抽取文本上的句界准确率低到使合法 anchor 大量被拒（假阳性 > 10%），则改为「整句闭合是软要求 + 强制展开显示前后各一句」。

**归因路径上仍然是 G-ENTAIL 在前**，理由是它便宜且能在 L2 之前拦掉「字面都对但拼出了源里没有的意思」这一类。

**覆盖率必须与蕴含率成对上报**：抽取阶段**漏掉**的可核查内容（coverage）与抽取阶段**编造**的内容（entailment）都要单独计数并报出 [E: ext-citation-faithfulness.md#D3]。只报其一就是我们自己在做本项目批判的口径扭曲。

#### §3.1.2 分解不做固定环节

声明分解（decompose-then-verify）**不是免费的，对强 verifier 反而是净负**：MiniCheck 在 WiCE claim-level 从不分解的 80.01 BAcc 掉到 FActScore 式分解后的 71.11；同一工作反向的例子是 MiniCheck 在 FELM response-level 从 48.10 F1 升到 WiCE 式分解后的 68.12，而 GPT-4o-mini 在 FELM 从 71.56 掉到 54.34 [E: ext-verification-mechanisms.md#M9]。结论句逐字："Decomposition generally benefits weaker verifiers, while it tends to negatively affect stronger verification systems."
**落点**：分解是一个 keep-if-better 的开关，由同一批门在同一批 claim 上跑两遍取胜者，不是流水线的固定一环 [E: ext-verification-mechanisms.md#D4]。粒度向 molecular facts（去语境化但最小化）靠，不向 FActScore 式极端原子化靠（后者的主导错误正是过度分解）。
**并行归属**：两条分支同时跑、按客观门结果择优——属 B1 允许的第 2 类扇出。

### §3.2 L0 存在性门（G-L0，GC-1）

#### §3.2.1 判定器组成

```
1. 标识符抽取（DOI / arXiv ID+vN / PMID / PMCID / URL）
2. 直接解析：doi.org 解析、Crossref /works/{doi}、arXiv API、Europe PMC
3. 熵过滤：识别 PDF 解析伪影，与「真幻觉」分开计桶
4. 书目字段模糊匹配（Crossref query.bibliographic + 校验打分）—— 只提议，不合并
5. URL 三分类：live / stale / hallucinated
6. 分档输出
```

**第 3 步是硬要求**：引用核验必须先分离「解析失败」和「真幻觉」。一手锚点：某项工作里 **78.5% 的「幽灵引用」其实是 PDF 解析伪影** [E: ext-science-agents.md#设计含义4]。
**不遵守会发生什么**：我们会把自己的 PDF 抽取链路 bug 报成模型幻觉，然后据此做错误的架构决策。

**第 5 步的三分类定义直接采纳一手**：*Non-resolving* = HTTP 4xx/5xx、连接错误或超时（403 因反爬被排除）；*Hallucinated* = non-resolving **且** Wayback 在任何时间戳都无快照；*Stale* = non-resolving 但 Wayback 有快照。关系式 `Hallucinated = Non-resolving − Stale`（DRBench 10 个模型 53,090 条 URL；ExpertQA 3 个模型 168,021 条 URL）[E: ext-citation-faithfulness.md#26, #B1]。

**第 4 步只提议不合并**：模糊身份解析可以提议合并，绝不能自动执行——bioRxiv 生产系统用标题匹配做 preprint→VoR 关联，作者手工复核 120 篇「未发表」预印本，发现 **37.5% 其实已经发表**，把一个统计量搞错了约 25 个百分点 [E: ext-evidence-schema.md#结论摘要6]（同一事实见 01-CONTRACTS §5.5.2）。

#### §3.2.2 per-claim 精度上界与选型〔裁定 D-6〕

**语料明令**：任何按聚合级数字选型的方案，落到逐条 verified/unverified 标签上都会崩；这条应写死成 lint 规则 [E: ext-verification-mechanisms.md#D1]。因此下表**全部是逐条口径**，并带完整口径三元组。

| 候选判定器 | 逐条口径的精度 | 口径三元组 | 采纳？ |
|---|---|---|---|
| DOI-only 解析 | 检出率 **0.268** / FPR **0.185** | 幻觉引用检出率与假阳率 / HALLMARK 全集 2,526 条 BibTeX 条目 / 与 LLM、agent、规则型比 | 采纳为**否决器**，不作为唯一判据 |
| 零样本 LLM | FPR 跨度 **0.050–0.702**，检出率 48%–91% | 同上 / 跨 cohort 各前沿模型（低端 Gemini 2.5 Pro 0.050，高端 DeepSeek-V3.2 0.702） | **拒绝**（FPR 跨一个数量级，不可调参） |
| 工具增强 agent | 检出率 **0.98–0.99**，FPR **0.431–0.478** | 同上 / GPT-5.1 + Crossref/OpenAlex/arXiv 等配置 | **拒绝**〔裁定 D-6〕 |
| 规则型 bibtex-updater | 检出率 **0.865**，FPR **0.092** | 同上 | **采纳为主判定器** |

[E: ext-verification-mechanisms.md#M1, #M16, 载荷数字核验表 DOI-only / 零样本 / 工具增强 / 规则型四行；一手 https://arxiv.org/html/2607.18360]

**〔裁定 D-6〕理由**（逐字采纳 HALLMARK 的结论）："the order-of-magnitude spread in false-positive rates (FPRs) -- not recall -- governs whether a verifier's flags are mostly true catches or mostly noise" [E: ext-verification-mechanisms.md#M16]。对本项目，误标 `unverified` 的成本远高于漏标——因为产品是可信度本身，一个 FPR 0.45 的门会让 45% 的真文献被打成可疑，门在两周内就会被绕过。
**什么会推翻**：若在自建的中文 + 英文混合标注集上，规则型的检出率跌到 < 0.5（例如中文文献缺 DOI 导致规则失效），则 L0 在中文路径上必须改为「规则型 + 人审队列」，而不是换成 agent 型。

**元数据匹配的口径陷阱（必须随数字复述）**：Crossref SBMV 的 P 0.9809 / R 0.9456 / F1 0.9629 是在 **2,000 条真实脏 reference string**（取自 Crossref 元数据、人工确认目标 DOI，2018-12）上测的；同一算法在**合成数据**（7,374 条记录 × 11 种引用格式，2018-11）上是 P 0.9923 / R 0.7902 / F1 0.8448。**同一算法两个口径差 12 个 F1 点，切勿混用** [E: ext-verification-mechanisms.md#M2]。

#### §3.2.3 L0 绿灯的语义纪律

**EE-L-1** L0 `pass` 的**唯一**含义是「该标识符在 `data_as_of` 这一天可解析，且元数据字段与声明一致」。它**不构成**任何关于内容的承诺。
**渲染层强制**：L0 绿灯在交付物中的措辞由门生成，不由作者写；模板里禁止出现「该文献可信」「已核实」这类词（lint 见 §9）。
**不遵守会发生什么**：这正是 01-CONTRACTS §2.2.2 要求「文献存在」与「文献支持这句话」永不合并的原因；合并后 L0 的高精度会被当成 L2 的高精度卖。

**L0 不该消耗产品的差异化叙事**：一次 `urlhealth` 式自纠错循环就能把 non-resolving 从 16.0% 压到 0.6%（GPT-5.1，435 个 ExpertQA 问题，p<10⁻³⁵；claude-sonnet-4-5 4.9%→0.8%、gemini-2.5-pro 6.1%→0.1%；**小模型 gpt-5-nano 不会用反馈，无效**）[E: ext-citation-faithfulness.md#27]。把它做成默认必过的前置门，叙事重量全压在 L1/L2 上 [E: ext-citation-faithfulness.md#D9]。
**附带推论**：执行核验的子代理不能用太小的模型——工具使用能力不足会让整个自纠错循环失效 [E: 同上]。

### §3.3 L1 定位性门（G-L1，GC-0）

#### §3.3.1 门做什么

归一化匹配算法是 `quote_faithful` 的唯一实现，其定义在 01-CONTRACTS §1.2.2，**本节不重述**。本节写实现契约：

**EE-L-2** G-L1 的比对基底**只能是 CAS 中的快照抽取文本**，不能是 session 日志中的 `tool/result` 内容。
一手依据：spill 落库的 `tool/result` 存的是**截断后**内容（loop 用 post-execute 后的最终 content 建事件），超阈值纯文本结果的原文**不在日志里**；本机 `spill-policy` 的 `maxInlineBytes` **没有包默认值**，出厂组合配置为 **50000 UTF-8 字节** [E: GROUND-TRUTH-CORRECTIONS.md#A2, gt-evidence-substrate.md#E2, #E4]。
**不遵守会发生什么**：任何超过 50000 字节的抓取（学术全文的常态）在门里只能看到 head/tail 预览 + locator，逐字匹配会**静默变成对预览的匹配**——一个只能命中文章开头 4KB 的引语门。

**EE-L-3** `anchor_span` 必须携带**可复核定位符**（TEI/JATS 结构节点、LaTeX 源位置、HTML 锚，或抽取文本内的字符区间 + 其所在结构路径），不能只有引语字符串。
理由见 01-CONTRACTS §3.4.2（G5 门槛比字符串包含更严的依据：SciTabAlign 标签 Macro-F1 88.4 vs 关键单元格恢复 34.8）。

**EE-L-4** 抽取质量哨兵必须在匹配之前跑（01-CONTRACTS §1.2.3），**不能让抽取失败表现为「找不到」**。
**不遵守会发生什么**：中文扫描版 PDF 的抽取文本为空 → 所有引语都「不命中」 → 全部降为 ST-U，而真实语义是 ST-N。这不是保守，这是把「我们没能力看」伪装成「我们看了没找到」。

#### §3.3.2 快照与冻结

快照的字段构成见 01-CONTRACTS §9.8。工程契约：
- **跨时间只比对抽取文本的哈希，不比对快照字节**——monolith 与 single-file-cli 都不保证字节确定性（monolith 需 `-M` 去时间戳，single-file-cli 未做承诺）[E: ext-reproducibility.md#D3, #未决7]。
- SPN2 归档 best-effort，失败不阻断，**也不能因此让 claim 升级**；真值锚点是本地快照的 sha256。SPN2 的速率限制**无一手来源**（官方 API 文档托管在需登录的 Google Doc），社区口径「匿名 15 URL/分钟」标 `unverified` [E: ext-reproducibility.md#D1]。

#### §3.3.3 L1 的假阳源（构造上的，必须承认）

`power_basis: construction` 的意思是假阳率由构造给出**近似为零**，但不是恰好为零。两处已知的构造性假阳：
1. **中文路径的整串去空白**。01-CONTRACTS §1.2.2 规定中文专项做全角/半角统一并**整串去空白**后比对（因为中文 PDF 抽取的空格位置不可靠）。去空白会让跨越换行/分栏边界的字符序列拼接成一个连续串，从而使一个原文中**并不连续**的载荷在归一化空间里命中。
   **缓解**：中文路径的命中必须额外断言「命中跨度在原始抽取文本中的字符跨距 ≤ 载荷长度 × 1.5」〔裁定，工程常数〕；超出即降为 `fail`。
   **什么会推翻**：若真实中文 PDF 的抽取在正常段落里就产生 > 1.5 倍的跨距膨胀，该常数需按实测标定。
2. **NFKC 归一化的字符折叠**。NFKC 会把不同码位折叠为同一字符，理论上可制造非预期命中。量级未测。

**这两条必须写进 `caveats`，并进入 §9 的负向 fixture。**

#### §3.3.4 L1 的假阴率是公开空白，这是我们的风险也是我们的机会

**逐字引文匹配（M4）没有任何公开的端到端精度测量，PDF 文本抽取保真度也无公开量化。语料把它列为「本项目一级门禁里唯一『确定性但精度未知』的环节」，并建议自建小规模标注集自测** [E: ext-verification-mechanisms.md#未决2；同向记录 ext-citation-faithfulness.md#R9]。

**因此**：
**EE-L-5** M1 里程碑前必须自建 L1 标注集（建议 ≥200 条，英文/中文各半，含扫描版 PDF、双栏 PDF、含连字符换行的段落、含页眉页脚的段落），报出 L1 的**假阴率**，并把该数字写进产品输出的元数据。
**在该数字存在之前，任何对外文案不得声称 L1 的精度。** 这一条本身就是产品可信度的一部分。

#### §3.3.5 L1 的真实杠杆：验证寻址，不是验证结论

一手实证：同一模型同一样本，标签预测 Macro-F1 **88.4** 而恢复关键单元格依据的 Macro-F1 只有 **34.8**（GPT-4o，SciTabAlign 372 条 2 分类子集）；最佳成绩也只有 50.8（Qwen 2.5 72B + CoT）；exact-match 设定下**没有任何模型能让「标签+依据同时正确」超过 50%** [E: ext-multimodal-evidence.md#29, #30, #31]。
**含义**：「结论正确」这一信号对「依据正确」几乎没有预测力。
**落点（EE-L-6）**：每条 K-L claim 的复核必须包含一次**只看 address 不看结论的反向取值**——独立复核者拿到 `{work_id, version_id, locator}`，在不知道 claim 结论的情况下从快照中取出该跨度的文字，与 `anchor_span` 逐字比对。
**并行归属**：反向取值与正向核验是同一断言的两路独立核验，属 B1 允许的第 2 类扇出。
**附带推论**：不应把「更长的推理」当作定位质量的杠杆——CoT 在 SciTab 上反而更差（GPT-4 zero-shot 3-class 64.80 → in-context+CoT 62.77）[E: ext-multimodal-evidence.md#23, #24]。

### §3.4 L2 支持性门（G-L2，GC-2）

#### §3.4.1 硬边界

**EE-L-7** G-L2 **只能收窄，不能写 ST-V**。这是 01-CONTRACTS §6.1 对 GC-2 的规定，本节不重述其理由。
**EE-L-8** G-L2 的判定单元必须是「**一条陈述 × 一个源**」的最小对。
依据：判定器在**领域受限 + 最小对**条件下可达 88.7% 与医生共识的一致率（3 名美国执业医生独立标注 400 对陈述-源；医生之间平均一致率 86.1%，差异不显著 p=0.21）[E: ext-citation-faithfulness.md#5, #A1]；而在**开放域 + 「陈述 vs 全部源」**的判定单元下，同类判定与人工标注只有 Pearson r = 0.62（作者自称 moderate，仅在 100 条任务上验证；另有约 15% 的源因付费墙/404 抓不到全文被**排除**在支持率计算之外，真实支持率只会更低）[E: ext-citation-faithfulness.md#12, #A3]。

#### §3.4.2 per-claim 精度上界（选型的唯一依据）

| 维度 | 最好的逐条成绩 | 口径三元组 | 结论 |
|---|---|---|---|
| **来源相关性** | GPT-5-mini **F1 = 0.908** | F1 / 624 对 attribution–citation（=1,248 条 rubric 决策），6 个 LLM judge council 独立打分 + 人工复核全部决策 + 378 条分歧（60.6%）重点人工裁决 / 与 Claude Opus 4.6 的 0.866、Sonnet 4.6 的 0.700 比 | **便宜模型就够**；judge 成本跨度 **49×** 且**成本不预测准确率** |
| **事实支持** | Claude Opus 4.6 **F1 = 0.750**，**所有模型 CI 重叠、统计上不可区分** | 同上 624 对 | **没有任何模型够好** → 绝不能全托给 judge |
| 小模型核查器 | MiniCheck-FT5 BAcc **74.7**（10 数据集平均）/ Bespoke-Minicheck-7B **77.4**（leaderboard 11 数据集，页面无更新日期，截至 2026-08-17 抓取） | balanced accuracy = ½(TPR+TNR) / LLM-AggreFact | **数据集数量在论文(10)/leaderboard(11)/后续论文(14)间漂移，跨版本数字不可直接比** |
| 归因二分类 | 微调 GPT-3.5 约 **80% macro-F1** | macro-F1 / AttributionBench 二值分类口径 | 与上同量级 |

[E: ext-evaluation.md#28, #29, #30, #31; ext-verification-mechanisms.md#M6, #M5 补充说明]

**同一指标家族的反面证据必须一起带**：Bespoke-7B（BAcc 77.4%）与 gpt-4-turbo（76.2%）分数只差 1.2 点，但两者标记为「不可归因」的样本集合在 14 个数据集中的 5 个上 **IoU < 50%**；response-level 偏差最坏 **−29.8%**，约为 claim-level 的两倍 [E: ext-verification-mechanisms.md#M6 补充说明]。**含义：分数接近不等于判一样的东西。**

#### §3.4.3 禁止事项

**EE-L-9 禁止用通用 NLI 模型做 L2。** 实测：某工作先用预训练 NLI 模型判蕴含发现严重缺陷，改用 LLM prompt 后，在 80 条人工标注样本上 LLM 判定只与人工冲突 5 次，而 NLI 模型冲突 21/26 次（两种配置）[E: ext-citation-faithfulness.md#E2]。
**EE-L-10 禁止把「多引几个源」当补救。** 把某条陈述的**全部**被引源合并后重判，**95.1%** 原本不被支持的陈述仍然不被支持 [E: ext-citation-faithfulness.md#4]。正确动作是换检索策略重找证据，或把 claim 拆细/弱化，**不是补引文** [E: ext-citation-faithfulness.md#D5]。
**EE-L-11 禁止用投票平均，用分歧率做升级信号。** 现实锚点：624 对中 **378 对（60.6%）** 有分歧并被人工裁决 [E: ext-evaluation.md#31]。**不要幻想 5% 的人审率。**
**EE-L-12 GC-2 不得参与生成期。** 写作阶段禁止调用同一个 rubric judge 自评再改写——那是对 judge 直接做梯度下降；judge 只在**冻结产物**上跑一次 [E: ext-evaluation.md#R4]。
**EE-L-13 判定器与被判系统不得同源。** 跨厂商规则见 01-CONTRACTS §5.2 的 R-I2。语料记录的循环论证形态：某评测用 GPT-5 判 GPT-5(DR) 的输出，后者在所有维度上都是最优；**未见任何研究系统性地测量「自家模型判自家输出」的偏差幅度** [E: ext-citation-faithfulness.md#R3]。

#### §3.4.4 判定器的领域内校准是产品的一部分

判定 prompt 必须在本项目自己的领域样本上做一次小规模人工校准。规模锚点：SourceCheckup 用 400 对 / Claimify 用 80 条 / DeepTRACE 用 100 条——**100 量级就足以给出可报告的一致率** [E: ext-citation-faithfulness.md#D2]。校准集规模的另一个锚点：200 条按难度分三箱各约 65 条（n=65 时 Wilson 半宽约 9.7 pp，勉强可用；n=100 才到 7.8 pp）[E: ext-evaluation.md#设计含义]。
**输出形式**：「我们的 `attributed` 标签在 N 条人工样本上与人类一致率为 κ = X」本身就是可交付的信任凭证 [E: ext-citation-faithfulness.md#D2]。κ 阈值与「禁止单独出现 raw agreement」的规则见 01-CONTRACTS §6.4。

#### §3.4.5 措辞扰动一致性（F-13 的实现）

对同一子命题做 N 次同义改写（低频同义词、间接实体指代、双重否定、多跳化）后**独立**走检索-判定链；判定不稳定即设 F-13 [E: ext-security-injection.md#D4, #V16, #RT-7]。
**N 的取值**〔裁定〕= 5，与 RT-7 的用例形状对齐 [E: ext-security-injection.md#RT-7]。
**这一路扇出属 B1 允许的第 2 类**（同一断言的 N 路独立核验），且它的输出是可比较的一致/不一致，天然适配客观裁决。
**注意它防的是什么**：input-only 威胁模型（只改 claim 措辞，不碰语料）对三套搜索增强事实核查系统拿到 ASR **18.8%–31.4%**；我们的子命题措辞由**已读过上游不可信文本的 LLM** 生成，**分解步骤是目前完全没设防的攻击面** 〔依据 00-PREMISE B5 N5, ext-security-injection.md#V16〕。

### §3.5 文献通道的记分纪律

**EE-L-14** L0 / L1 / L2 三层**独立记分、独立门限**，产物中不得合成为一个数。
**EE-L-15** 报告级指标必须成对出现：`precision`（在敢下结论的地方对得多准）与 `coverage`（敢下结论的比例）。**只报其一就是我们自己在做本项目批判的口径扭曲。这一条应写进门脚本，让单指标报告直接构建失败** [E: ext-citation-faithfulness.md#D6]。
锚点：某系统的「超人类」只在允许弃答的 precision 上成立（85.2% ± 1.1 vs 人类 73.8% ± 9.6），accuracy 上人类均值更高且置信区间大幅重叠（66.0% ± 1.2 vs 67.7% ± 11.9）[E: ext-citation-faithfulness.md#17]；另一个系统幻觉率低是因为 **62% 的问题它不作答** [E: ext-citation-faithfulness.md#15]。
**EE-L-16** 每条 claim 的证据预算与检索深度/并行度**解耦**。依据是 §3.0 的深度消融曲线：并行度和检索深度必须与「每条 claim 的证据预算」解耦，否则规模化会系统性地劣化忠实度而**不被表层监控发现** [E: ext-citation-faithfulness.md#D4]。
gate 设在「每条 claim 至少绑定 k 个已定位的证据片段」上，**不设在「检索轮数」或「并行子代理数」上**。规模化方向是「更多 claim 各自被独立核验」，不是「一个报告读更多源」。

### §3.6 中文路径的门行为

中文层的实测缺口（OpenAlex `language:zh` 占比 1.56%、北大核心刊级收录 37%/篇级 24%（**以万方为基准，且该分母存在利益相关**）、References 完整率 7%（论文口径）/随机抽样 `refs>0` 仅 2%、三个顶刊 ISSN 命中为 0、`language` 字段 92% 标错）见 01-CONTRACTS §3.6，本节不重述。**门侧的落点只有三条**：

**EE-L-17** `citation-snowball` 策略在中文任务中**关闭**（引文滚雪球在中文场景基本失效）。
**EE-L-18** 以 ISSN/DOI 为主键的检索流水线对最权威的中文期刊会**静默返回空而不是报错**，因此中文路径的 L0 必须把「空结果」与「确认不存在」分开：空结果 → `not_applicable` → ST-N + F-32，**不是** `fail`。
**不遵守会发生什么**：《管理世界》《中国社会科学》《历史研究》三个 ISSN 在 OpenAlex `sources` 与 Crossref `journals` 中命中均为 0——把这个空当成「不存在」，等于把中国最权威的三本期刊判成幻觉。
**EE-L-19** L1 在中文路径上的假阴率**未知且已知偏高**（中文 PDF 抽取是最大假阴来源），在 §3.3.4 的标定完成前，中文引语门**偏保守**（宁可多判 ST-U/ST-N）。

**本轮调研的一条硬结论必须写进产品语义**：**没有找到任何针对中文学术文献（CNKI/万方/维普）引文幻觉率或核验可行性的实证研究。若本项目要覆盖中文文献，L0/L1 的可行性是完全未知的空白** [E: ext-citation-faithfulness.md#R6]。

---

## §4 推断通道：从零建的机制

### §4.0 为什么是「建」不是「加」

- 前代的 `rigor_gate.py:152-153` 对未知 kind 直接 `ok=False`：台账里出现 `kind=inference` 的行会被计为失败并把复现率拉到 100% 以下 → 门 FAIL。**前代不是「没管推断」，而是「台账里出现推断类 claim 会让论文过不了门」** [E: GROUND-TRUTH-CORRECTIONS.md#C5]。
- 文献里这条赛道没有可用的现成件：Toulmin warrant 有无检测的加权 F1 0.88 来自**教育对话语料、传统 ML 分类器**（三个子集共 100 / 1,026 / 211 条回答，主题是「某实体是否算智能」，分类器为 Random Forest 等），是域外指标，且**只判 warrant 有无、不判 warrant 是否成立** [E: ext-verification-mechanisms.md#M14]。
- 更重的教训是 ARCT：BERT 峰值 77%（仅比未受训人类基线低 3 个点）被证明**完全由数据集中的伪统计线索解释**，在对抗集上退化到随机 [E: ext-verification-mechanisms.md#M15]。

K-I 永不可达 ST-V 的裁定与理由见 01-CONTRACTS §2.3.1，**本节不重述**。本节只写门。

### §4.1 门的总形状：照抄 RoB 2

**这是本轮最强的一条可移植结构**：Cochrane RoB 2 的形态是「每个域下挂 2–7 个**近乎事实性**（原文 "reasonably factual in nature"）的信号问题，答案只能是 Y/PY/PN/N/NI（+条件性 NA），然后由**写死的算法**把答案组合映射到判定；算法只给 proposed judgement，人可以推翻，**但推翻必须写理由**」[E: ext-human-methodology.md#C, #结论摘要1]。

**它有直接的量化支持**：同一篇 2025 JMIR 研究里，LLM 在**信号问题层面**平均准确率 **83.2%（95% CI 77.5–88.9）**，聚合到**域层面**降到 **65.2%**，整体判定只有 **57.5%–70%**；另一项 2024 Research Synthesis Methods 研究显示，直接让 LLM 输出域级判定，**F1 只有 0.1–0.2，与平凡基线无异** [E: ext-human-methodology.md#结论摘要2]。
**结论极其明确：让模型答事实问题，让代码做聚合判定。**

因此 K-I 的门是三段：

```
G-DAG      （GC-0）  前提闭包 + 无环 + 前提状态 + 口径可比性 + 强度偏序
G-WARRANT  （GC-2）  warrant 声明 + 该 warrant 的信号问题集（模型答）+ 表驱动聚合（代码判）
G-REDERIVE （GC-2）  独立复核者盲判再推导 + 反例搜索记录
```

**整个 K-I 门的 gate_class 是 GC-2**，因为它的输入含模型判断（01-CONTRACTS §6.1）。G-DAG 单独是 GC-0，但它只能否决不能支撑。

### §4.2 G-DAG（GC-0）

必备工件（前提闭包、warrant、强度不超最弱前提、口径可比性、独立再推导+反例记录、变更传导）见 01-CONTRACTS §2.3，本节写判定实现。

#### §4.2.1 前提闭包与无环

```
1. 解析 claim.premises[] 为 claim_id 列表
2. 全部 claim_id 必须在台账中可解析          → 否则 not_applicable（缺件）
3. 以 premises 边构图，做拓扑排序             → 有环即 fail
4. 读每个前提的 claims/<id>.status.json
   若任一前提 status ∈ {unverified, not_covered, contested} → fail
```
第 4 步的依据见 01-CONTRACTS §2.3 第 1 项。**注意它读的是 status.json（门写的）而不是 claim.json（producer 写的）**——这是写权分离（01-CONTRACTS §4 W-03 / W-04）在推断通道的直接兑现。
**不遵守会发生什么**：producer 可以在自己的 claim.json 里声称前提已验证，推断结论就凭空拿到 ST-A。

#### §4.2.2 口径可比性

**可机器判的部分**：前提之间的 `metric_frame`（三字段，见 01-CONTRACTS §9.4）做结构比对——`metric` 字段串不等即标记；`sample_or_tier` 与 `comparator` 不等即标记。
**不可机器判的部分**（例如两个不同名称但实质相同的指标）交 GC-2 的口径畸变检测维度，设 F-12。
**为什么这一项必须存在**：前代的精确失效形态是「每个数字都对、拼起来是错的」，而 100% 复现率会为它背书 [E: gt-pg-current.md#I-4]。
**实测锚点**：同一系统同一基准因类别纳入与 prompt 配置不同而差 **16.70 pp**（75.14 vs 58.44）；「预印本发表率」因队列窗口不同可在 **20%–67%** 间任取 [E: ext-evidence-schema.md#D 必填字段]。**指标名相同不代表口径相同。**

#### §4.2.3 强度不超过最弱前提〔裁定 D-7〕

前代的精确失效是：前提被诚实地放宽了，结论句却原封不动 [E: gt-pg-current.md#I-3]。要机器判这一条，必须先让「强度」成为结构化字段。

```
quantifier ∈ {none, some, exists, most, all}        偏序：none ≺ exists ≼ some ≺ most ≺ all
modality   ∈ {possible, probable, necessary}        偏序：possible ≺ probable ≺ necessary
```
**判定**：结论的 `(quantifier, modality)` 在乘积偏序下必须 **≤ 前提集合中的最弱者**。超出即 `fail`。
**〔裁定 D-7〕的边界**：这两个枚举**只覆盖量词与模态**，不覆盖散文措辞的强度（「显著」「大幅」「基本」）。**散文强度不参与判定**——它由 01-CONTRACTS §4 W-10 的确定性组稿器约束（正文数字一律写成占位符），不由本门约束。
**理由**：语料没有给出任何可机判的散文强度尺度；发明一个会造出一个不会红也不会绿的检查。
**什么会推翻**：若在真实任务中出现大量无法用五值量词表达的合法断言（如「在 X 条件下通常成立」），则该字段改为「受控枚举 + 自由文本限定语」，限定语的比对交 GC-2 并设 F-12。

### §4.3 G-WARRANT（GC-2）：warrant 显式化与信号问题

warrant 的五值封闭枚举见 01-CONTRACTS §2.3 第 2 项。**本节给每类 warrant 的信号问题集**——这是 K-I 门的实体内容。

#### §4.3.1 信号问题的通用契约

**EE-I-1** 每题必须是「近乎事实性」的问题，值域固定为 `Y / PY / PN / N / NI`，条件触发的题另加 `NA`。
**EE-I-2** 每题必须携带 `ni_polarity ∈ {evidence_of_problem, expected_to_be_reported}`，因为「缺信息」不是中性的。RoB 2 的原文规则逐字：若问题旨在识别某问题的证据，`No information` 对应「无该问题的证据」；若问题涉及一个**本应被报告**的事项，信息缺失导致对存在该问题的担忧 [E: ext-human-methodology.md#C]。
**EE-I-3** 每题必须带**原文直引**（RoB 2 逐字要求 "Brief direct quotations from the text of the study report should be used whenever possible."）；本项目把「原文」解释为**前提 claim 的 anchor_span 或 out.json 字段**，不是 producer 的转述。
**EE-I-4** 信号问题**必须独立作答**：一题的答案不得影响同域或他域其他题的答案，除非是通过决定后续哪些题被作答（RoB 2 逐字规则）[E: ext-human-methodology.md#C]。实现上：每题一次独立调用，不共享上下文；**这一路扇出属 B1 允许的第 2 类**。
**EE-I-5** 聚合是**表驱动的纯函数**，代码写死，可单元测试。门输出 `{proposed, final, override_reason?}`；**`final != proposed && override_reason == null` 直接判门红** [E: ext-human-methodology.md#设计含义2]。
**EE-I-6** 人可以推翻算法判定，但**推翻必须写理由**（RoB 2 逐字："It is particularly important that reasons are provided for any judgements that do not follow the proposed algorithms."）。人的推翻设 F-26，**不改 status**（01-CONTRACTS §7.2）。

#### §4.3.2 五类 warrant 的信号问题集

下表是**本文件的构造**，不是语料的引用——语料只给了形状（RoB 2）与它的量化支持，没有给学术论证的题库。因此整表标〔裁定〕。
**什么会推翻整表**：若在自建的 K-I 金标集上，信号问题层的模型准确率**不显著高于**域层直答（即 RoB 2 形状带来的 83.2% vs 65.2% 落差在我们的域上不复现），则这套题库是装饰，应当撤掉并把 K-I 改为纯人审。

| warrant | 信号问题（Y/PY/PN/N/NI） | `ni_polarity` |
|---|---|---|
| `deductive` | ①前提集合是否显式且完备（无隐含前提）？②推理形式是否属于受控的有效式清单？③中项/关键词在各前提中是否同义？④是否存在换质换位错误？ | ①③④ = expected_to_be_reported；② = evidence_of_problem |
| `statistical-generalization` | ①抽样框是否被显式描述？②样本量与置信区间是否给出？③是否存在已知的选择效应？④外推的目标域是否与样本域一致？⑤是否报告了不响应/缺失？ | ①②⑤ = expected_to_be_reported；③④ = evidence_of_problem |
| `causal-identification` | ①识别策略是否被显式声明？②主要混杂是否被枚举并处理？③时序是否满足（因先于果）？④干预点/处理定义是否明确？⑤是否报告了敏感性分析？ | ①④⑤ = expected_to_be_reported；②③ = evidence_of_problem |
| `analogy` | ①相关相似性是否被显式列出？②已知的不相似性是否被列出并评估？③目标域是否存在会破坏类比的结构差异？ | ①② = expected_to_be_reported；③ = evidence_of_problem |
| `abduction` | ①备择解释是否被枚举？②「最佳」的判据是否显式？③该解释是否可被某个观测证伪？④是否存在与自身数据矛盾的辩护？ | ①②③ = expected_to_be_reported；④ = evidence_of_problem |

`abduction` 第 ④ 题的依据是一条实测失效形态：*Correct Answer, Wrong Mechanism* —— 28 次 agent 尝试中 20%（主模型 4/20）到 37.5%（跨模型 3/8）出现「结论对但机制错，且**用与自己数据矛盾的物理去辩护**」[E: ext-science-agents.md#结论摘要2, 00-PREMISE#B4-5]。

#### §4.3.3 聚合表

```
域级（每个 warrant 一个域）：
  任一 evidence_of_problem 题为 Y/PY  → domain = high_concern
  任一 expected_to_be_reported 题为 N/NI → domain = high_concern
  存在 PN/NI 但无上述命中             → domain = some_concern
  全部为期望方向的确定档              → domain = low_concern

推断门总判：
  domain == high_concern              → G-WARRANT verdict = fail
  domain == some_concern              → verdict = pass，且设 caveat（进人审队列）
  domain == low_concern               → verdict = pass
```
**注意这个聚合表只有一个域**（一条 K-I claim 只有一个 warrant）。它比 RoB 2 简单，因此 RoB 2 的「某域 High 则整体 High」规则在这里退化为恒等。**若将来允许一条推断挂多个 warrant，必须逐字采用 RoB 2 的规则：某域判 High 则整体判 High，与是哪个域无关** [E: ext-human-methodology.md#C]。

#### §4.3.4 廉价一致性检查默认全开

两个便宜检查作为每条 K-I claim 的**默认后置**（不是抽检）[E: ext-science-agents.md#设计含义11]：
- **regime-shift 单步检查**：只用 claim 本身，问「如果条件 X 变了，这个论断还成立吗」，看它的解释是否与自己的数据矛盾。
- **重算检查**：在有已知答案时重算一遍。

一手锚点：CAWM 的两个轻量检查**抓到了全部案例** [E: ext-science-agents.md#设计含义11]。**口径警告**：该「全部案例」的分母是 28 次 agent 尝试中被判定出问题的那部分，样本极小，不能读成「这两个检查的召回率是 100%」。

### §4.4 G-REDERIVE（GC-2）：独立复核者的提问结构

复核者的身份规则（`reviewer.childId ≠ producer.childId`、必须走 `spawn` 而非 `fork`、跨厂商 provider）见 01-CONTRACTS §5.2 / §5.3，**本节不重述**。本节写**问什么、怎么问**。

#### §4.4.1 三段式盲判〔裁定 D-8〕

```
第 1 段（盲）：只给 premises[]（含其 anchor_span / out.json 值）+ warrant 类型，
              不给结论、不给 producer 的任何自由文本。
              问：从这些前提出发，用这个 warrant，你能推出什么？强度是多少？
              输出：{derived_payload, quantifier, modality, 推导步骤}

第 2 段（对照）：给出 producer 的结论。
              问：你的推导与它一致吗？不一致处在哪一步？
              输出：{agreement ∈ {same, weaker, stronger, different}, 差异定位}

第 3 段（反例）：给出结论。
              问：构造一个满足全部前提但不满足结论的实例。
              输出：{counterexample | not_found, 搜索过程, 预算消耗}
```

**〔裁定 D-8〕第 1 段必须盲。** 理由：不盲的复核会退化成「读一遍然后说同意」——这正是前代的实证形态。前代把「独立性」完全交给 prompt 措辞（Cartographer 的 "Do not read the draft…" 写在 prompt 里，零机械强制），结果是**该角色在审计上不存在**：无法从工件判断 positions.md 是独立产出还是 orchestrator 顺手写的 [E: gt-pg-current.md#C-9, #未决5]。
**机械强制点**：第 1 段的复核者会话必须走 `spawn`（零父历史），其输入载荷是结构化前提卡，**不含 producer 的自由文本**——这是 01-CONTRACTS §5.3 R-I4「局部消息传递」在推断通道的落点，依据是局部消息传递比全局消息传递 ASR 低约 20% [E: ext-security-injection.md#V26]。
**什么会推翻**：若盲判段的产出在真实任务中大量与结论「different」而人裁认为 producer 是对的（即盲判制造了大量假阳性），则改为「盲判 + 一次带结论的复议」两轮，且以复议为准。

#### §4.4.2 反例搜索记录的格式契约

`inferences/<claim_id>.reviewer.md` 的反例搜索段（文件分离规则见 01-CONTRACTS §4 W-11）必须含：

```yaml
counterexample_search:
  strategy: [...]           # 用了哪些构造策略
  queries: [...]            # 若走检索，逐条查询 + 其快照 id
  budget: { wall_s: , tokens: , tool_calls: }
  result: found | not_found
  found_instance: {...}     # result==found 时必填
```
**「找不到反例也要记录搜索过程与预算」**（01-CONTRACTS §2.3 第 5 项）。
**不遵守会发生什么**：`not_found` 无法与「没搜」区分，`counter_evidence_searched` 这个字段就失去意义，而它是 `S` 第 0e 步的输入。

#### §4.4.3 为什么有界反例搜索失败不等于真值

**这是 K-I 上限为 ST-A 的工程理由**（裁定本身在 01-CONTRACTS §2.3.1）：把「有界反例搜索在预算内失败」直接当成真值，就是重演 ARCT 的 Clever Hans——BERT 的 77% 完全由伪统计线索解释，在对抗集上退化到随机 [E: ext-verification-mechanisms.md#M15]。
**G-REDERIVE 的 `power_basis` 因此是 `unmeasured`**：我们不知道自建反例搜索器的召回率。按 EE-0.3，它可以判 fail，不能单独把状态推到最高档——而 K-I 的最高档本来就是 ST-A，两者一致。

#### §4.4.4 并行归属与深度

反例搜索可以扇出（多个搜索策略并行），属 B1 允许的第 2 类。
但**推断链本身不得扇出**——它落在 00-PREMISE B1「明确禁止的扇出」里（论证链构建、跨 claim 一致性推理、最终裁决）。
深度约束：角色分配必须在三层内闭合（协调者 0 → 领域 worker 1 → 验证 worker 2），出厂 `maxDepth: 3` [E: gt-orchestration.md#B]（规则见 01-CONTRACTS §5.3 R-I5）。**「验证者再派攻击者」会用到第 3 层，仍在预算内；「攻击者再派子攻击者」越界。**

### §4.5 变更传导（stale）

01-CONTRACTS §2.3 第 6 项要求前提变更 → 依赖它的推断结论自动置 `stale` 并重判。实现契约：

**EE-I-7** 每条 K-I claim 的 `inputs_hash`（EE-0 信封字段）必须包含**全部前提的 `status.json` 的哈希**。
**EE-I-8** 门运行器在每轮开始时重算所有 K-I claim 的 `inputs_hash`；不匹配即该 claim 进入 `stale`（不是 status，见 01-CONTRACTS §9.17），必须重跑 G-DAG / G-WARRANT / G-REDERIVE。
**EE-I-9** 派生 claim **不继承**父 claim 的状态，必须独立走门。依据（IPCC 逐字）："the degree of certainty in findings that are conditional on other findings should be evaluated and reported separately" [E: ext-human-methodology.md#设计含义1]。**这直接杀死「claim graph 里状态沿边传染」这一类前代失败。**

**成本诚实**：这条链意味着一次前提降级可能引发一大片 K-I 重判。这是设计上接受的代价——替代方案（不重判）会让台账里出现「结论基于一个已被撤稿的前提」而无人发现。

### §4.6 K-I 的产品后果（必须写出来的风险）

K-I 的最高档是 ST-A。**如果研究的主要产出是推断，这个产品的绿灯密度会很低。这是一个真实的产品风险，不是保守的美德**（同 01-CONTRACTS §10.6）。
**缓解只有一条，且它不改变上限**：把可以下沉到 K-D / K-L 的载荷下沉——一条「A 比 B 高 37%」的推断，若能改写成一条 K-D 的重跑断言，就不应该走 K-I。门侧的落点是 §9 的一条 lint：**K-I claim 的载荷若全部由数值构成且其前提均为 K-D，报警提示可下沉**。

---

## §5 来源完整性门组：T0 / T1 / T2

`source_integrity` 的值域与三个子测试的构成见 01-CONTRACTS §1.2。**本节写这三层怎么实现，以及它们的输出怎么映射到那个值域。**

### §5.1 三层结构与四态输出

语料给出的四态是 `CLEAN / FLAGGED / SUSPECT / NOT_COVERED` [E: ext-literature-integrity.md#2]。**映射到 01-CONTRACTS 的字段如下**（这是映射表，不是新定义）：

| 门组输出 | 触发 | → `source_integrity` | → flags | → `S` 的哪一步 |
|---|---|---|---|---|
| `CLEAN` | T0 全部通过 **且** 全部快照在 freshness 窗口内 | `intact` | — | 不触发前置否决 |
| `FLAGGED` | T0 红灯（撤稿 / EoC / 劫持刊 / 强指纹命中） | `contaminated` | F-05 / F-06 / F-07 | 0b → ST-C |
| `SUSPECT` | T1/T2 黄灯 | **不改** `source_integrity` | F-19 / F-20 / F-21 | 2d（部分不改状态，见 01-CONTRACTS §7.3） |
| `NOT_COVERED` | DOI 缺失 / 非英文 / 预印本无对应记录 / T0 数据源抓取失败 / 快照超龄 | `not_covered` | F-18 / F-32 | 0c → ST-N |

**EE-S-1 `NOT_COVERED` 绝不能静默当成 `CLEAN`。** 这是本维度对「不把不确定洗成确定」这条产品原则最直接的落地 [E: ext-literature-integrity.md#2]。

**注意 SUSPECT 那一行**：T1/T2 的黄灯**不动** `source_integrity`。理由：T1（取证统计）判的是**论文内部数值的自洽性**，T2（商业黑箱）判的是**可疑度**，两者都不是「我引的这份东西还是不是我以为的那份东西」这个谓词（01-CONTRACTS §1.2.1）。把它们塞进 `source_integrity` 会污染一个本来完全确定性、可重跑的字段。

### §5.2 T0-撤稿门（G-RETRACT，GC-1）：必须打在原文 DOI 集合上

#### §5.2.1 权威源与实测量级

**权威源是 Retraction Watch CSV**（Crossref 托管的 GitLab 仓库，每工作日更新，无鉴权，`curl` 可直取，实测 63 MB）：
- 2026-08-17 实测全库 **71,799 行**；其中 `RetractionNature = Retraction` **66,287** 行；**去重原文 DOI 62,708 个** [E: ext-literature-integrity.md#A1, #结论摘要1]。
- 数据快照自带日期：README 的 `generated on YYYY-MM-DD`（本次抓取时为 `generated on 2026-08-14`），GitLab API `last_activity_at = 2026-08-14T23:00Z`。
- 字段：`Record ID / Title / Journal / Publisher / RetractionDate / RetractionDOI / OriginalPaperDOI / OriginalPaperPubMedID / RetractionNature / Reason / Paywalled / Notes`。`RetractionNature ∈ {Retraction, Correction, Expression of concern, Reinstatement}`。
- **许可**：仓库**没有 LICENSE 文件**（GitLab API `license: null`）；Crossref 的表述是元数据可自由复用 + 请求署源。**不要在文档里写「RW 数据是 CC0」，那是没有一手依据的转述** [E: ext-literature-integrity.md#A1, 核验表末行]。

**辅助源**：Crossref `/works/{doi}` 的 `update-to` 数组（每项含 `{type, DOI, source, label, updated}`，`source ∈ {publisher, retraction-watch}`）。**同一撤稿可能同时来自两个 source，必须去重**——实测抽 400 条得到 publisher 258 + retraction-watch 281，和 > 400 [E: ext-literature-integrity.md#A2]。

#### §5.2.2 为什么门必须打在原文 DOI 集合上

**EE-S-2 撤稿门的键是 RW 的 `OriginalPaperDOI` 去重集合（62,708 个，as-of 2026-08-14），不是任何厂商的布尔字段。**

实测依据：2026-08-17 OpenAlex `is_retracted:true` = **134,175**，约为 RW 撤稿条数（66,287）的两倍。随机抽样 200 条归因：
- **81 条（40.5%）** 是 RW 记录里的被撤原文 DOI；
- **69 条（34.5%）** 其实是**撤稿公告本身**（匹配 RW 的 `RetractionDOI`）；
- 另有 **42 条**标题形如 "Retraction: …/Correction to …" 但 RW 无记录。

即 `is_retracted` 是「被撤论文 ∪ 撤稿公告 ∪ 部分更正公告」的并集 [E: ext-literature-integrity.md#结论摘要2, #A4]。上游论文（Hauschke & Nazarovets, *(Non-)retracted academic papers in OpenAlex*, arXiv:2403.13339, J. Information Science 2025）逐字点名："Despite accurate metadata sourced from Crossref database, OpenAlex consolidated this information into a single boolean field, 'is_retracted,' leading to misclassifications of papers."

**不遵守会发生什么**：**把撤稿公告本身判成造假文献**。一篇论文被撤稿后，期刊发布的撤稿声明是一份合法、可引用的记录；把它标红意味着系统会拒绝引用「某某论文已于某日被撤稿」这一事实的原始出处。这是一个会**每三次误判就出现一次**的缺陷（34.5% 的抽样占比）。

**另一处不得单源的实证**：同日（2026-08-17）OpenAlex `is_retracted:true` = 134,175 而 Crossref `update-type:retraction` = 74,607，相差 1.8 倍。两个口径都「正确」，含义不同，任何一个单独用都会给出错误的撤稿率 [E: ext-evidence-schema.md#结论摘要5]。**两源不一致时 → `disputed` → 走人审，不做静默取舍** [E: ext-evidence-schema.md#D 记录层]。

#### §5.2.3 Reinstatement 不是布尔

`RetractionNature` 含 `Reinstatement`——**撤稿可以被撤销**，因此该字段必须按枚举处理而不是 boolean [E: ext-evidence-schema.md#E 反模式6]。
**实现**：同一 `OriginalPaperDOI` 的多条记录按 `RetractionDate` 排序，取**最新状态**；若最新是 `Reinstatement`，则不设 F-05。

#### §5.2.4 绿灯的措辞纪律（EE-S-3）

**EE-S-3 撤稿门绿灯在任何产物中的措辞由门生成，逐字模板为：**

> 截至 `{registry}` 的 `{snapshot_date}` 快照，未发现该 DOI 的撤稿记录。

**禁止**出现的等价物：「该文献未被撤稿」「文献可信」「已通过污染筛查」「clean」。
**理由（两条独立）**：
1. **假阴性来自「尚未被 RW 收录」**——撤稿有滞后，且各出版商撤稿延迟差异极大 [E: ext-literature-integrity.md#设计含义1, #F]。
2. **EoC/Correction 的覆盖据 RW README 自述不完整**（逐字："Some other update types, such as expressions of concern and corrections, are also included in the data, but these are not as comprehensive as retractions."）→ **不能拿 RW 的 EoC 缺失当「该文没有 EoC」的证据** [E: ext-literature-integrity.md#A1, #未决5]。

语料把这条列为「应写进 attacker 的必检清单」[E: ext-literature-integrity.md#未决5]。**因此 §9 有一条对应的 lint。**

#### §5.2.5 差异化窗口有限（不影响设计，影响优先级）

现有产品在这一层全线失守：研究型工具在「5 个撤稿相关问题全对」上 SciSpace / ScienceOS / Consensus 均为 **0/15**；在主题概述中引用撤稿文献**且未作任何提示**的篇数 SciSpace 8/15 [E: ext-citation-faithfulness.md#41, #42]。但同一语料记录：某产品在两个月内从 18/21 改善到 5/21，**说明这个能力是可修的，先发优势窗口有限，且该数字会快速过期（2025-06 / 2025-08 快照）** [E: ext-citation-faithfulness.md#43, #D7]。

### §5.3 T0-劫持刊门（G-HIJACK，GC-1）

- 数据：Retraction Watch Hijacked Journal Checker，实际载体是 Google 表格；**`?format=csv` 已 400，只有 `?format=xlsx` 可用**（实测 106 KB），解析后 **456 条**数据行，表头自述 "First created: May 30, 2022; last updated July 17, 2026" [E: ext-literature-integrity.md#B1]。
- 列结构同时给出被劫持**域名**与 **ISSN**，因此可做两种确定性匹配：URL host 匹配 + ISSN 匹配。
- **EE-S-4 降级链必须存在**：导出失败 → 用上次 mirror + 标记 `stale` → 超过 90 天 → `not_covered`。**绝不能让抓取失败静默变成「未命中」** [E: ext-literature-integrity.md#未决3]。
- **绿灯不构成期刊可信度证明**：列表**极小**（456 条），只覆盖已被举报的头部案例，**假阴性巨大** [E: ext-literature-integrity.md#设计含义1]。

**掠夺性期刊（F-08）本项目不可编程访问**：Cabells 订阅制、无公开 API（2026-01-30 计 20,274 本期刊）；STM Integrity Hub 仅对出版商开放。**在设计文档里显式列为「本项目无法覆盖」** [E: ext-literature-integrity.md#结论摘要5, #设计含义1]。

### §5.4 T0-指纹门（G-FINGERPRINT，GC-0）

- 数据：PPS 指纹词典 CSV dump 本地 mirror（共 **15,261 条**指纹；其中 tortured 8,282 条已实测下载）[E: ext-literature-integrity.md#结论摘要6, #设计含义1]。
- **PPS 的论文级结论不可批量获取**（只有指纹词典可下载）→ 本项目只能复用词典，不能复用它的「哪些论文有问题」的判断。
- PPS 用 Dimensions 的邻近算子（`"A B C"~5` = 三词出现在 5 词窗口内），本地实现需复刻该语义。**本地匹配与 PPS 官方结果不会完全一致，这个差异必须在文档中承认，不能宣称「与 PPS 一致」** [E: ext-literature-integrity.md#未决4]。
- **单条指纹命中不等于问题论文**；PPS 自己也靠人工策展控 FP，**无量化 FP 率** → 只能给黄灯 [E: ext-literature-integrity.md#设计含义1]。

### §5.5 T1-纯代码取证（GC-0）

GRIM 的功率闭式解、statcheck 的真实口径、GRIMMER test 3 的上游误报、SPRITE 不是门——**这四条的定义与依据全部在 01-CONTRACTS §6.2.1 / §6.2.2 / §6.2.3 / §6.2.4，本节不重述。** 本节只写三条实现契约：

**EE-S-5 T1 的门输出必须把「适用条件」和「结论」一起输出。** 一个 `power: 0.00` 的 `consistent` 与一个 `power: 0.90` 的 `consistent`，证据强度差一个数量级。**丢掉 power 就是在制造假安全** [E: ext-literature-integrity.md#设计含义5]。信封字段见 EE-0。
**EE-S-6 T1 黄灯不参与 `source_integrity`**（见 §5.1 的映射表）。
**EE-S-7 许可证分流**：GRIM / GRIMMER / DEBIT / SPRITE 参照 MIT 的 `scrutiny` / `rsprite2` 实现；**statcheck 类功能必须从 APA 报告规格独立重写**——CRAN 的 `statcheck` 是 GPL-3，直接翻译其 R 源码到 TypeScript 会触发 GPL 传染 [E: ext-literature-integrity.md#未决6]。**这个决定必须记录在代码注释里。**

**T1 的现实收益必须诚实标注**：现场误报画像显示，20 篇文章 737 条 NHST 中 113 条被标记，其中 14 条是抽取错误、**64 条（57%）源于统计校正** → 对「造假筛查」用途而言，这批 flag 里约七成不是造假信号 [E: ext-literature-integrity.md#E5]。**T1 是一个高噪声层，它的价值在于便宜且完全本地，不在于准。**

### §5.6 T2-外部概率性（永不参与自动判定）

- Papermill Alarm / STM Integrity Hub / Cabells / Signals / ImageTwin：**没有一家公布过带口径的 false positive rate** [E: ext-literature-integrity.md#结论摘要5]。
- PubPeer：`/v3/publications` POST 端点实测技术可达，但 robots.txt 明确 `ai-train=no`、`use=reference` 并 Disallow ClaudeBot——**能访问 ≠ 被授权**。
  **EE-S-8 PubPeer 门默认关闭**，做成「需用户自行申请 key 后启用」的可选模块；**未授权时的行为是 `not_covered`，不是静默跳过** [E: ext-literature-integrity.md#未决2]。
- **EE-S-9 T2 的输出只能是「建议人工复核」标签，绝不进入 `S` 的任何降级路径。**

### §5.7 新鲜度与限速

**EE-S-10 每个 GC-1 门的输出必须携带 `data_as_of` 与源标识**；超龄阈值（RW > 7 天、PPS > 30 天、Hijacked > 90 天）见 01-CONTRACTS §6.3。超龄即 `not_covered`，**不是通过**。

**EE-S-11 T0 全部本地化**：下载一次、本地查 N 次，**扇出的子 agent 不打网络**。这是超并行扇出时唯一不会被限速掐死的形态 [E: ext-literature-integrity.md#设计含义4]。

**限速按 host 分桶、由中央网关决定并行度**（规则与全部速率数字见 01-CONTRACTS §6.3 第 5 项）。本节只补一条**门侧的落点**：
**EE-S-12** 任何 GC-1 门在被限速拒绝时，输出 `not_applicable` + F-11，**不得重试到成功**——无限重试会把一次限速变成一次超预算，而超预算的语义（ST-N）与限速的语义（ST-N）相同，重试只是在烧钱。

---

## §6 图表与表格证据

### §6.1 状态上限

图形派生数值强制 ST-E、`epsilon` 与 `method` 必填、禁止参与比较/排序/阈值、图族黑名单——**全部在 01-CONTRACTS §3.5，本节不重述。** 本节写门。

### §6.2 升级路径与准入条件（按实测误差率设阈值）

| 路径 | 触发条件（机器可判） | 门 | gate_class | 允许的最终状态 | 数字依据（含口径） |
|---|---|---|---|---|---|
| **P0 绕开图表** | 同一数值在正文/表格/附录/作者数据仓库中存在 | 走文献通道 G-L1 | GC-0 | ST-V | 表格结构抽取近饱和；但数值-类型抽取仍是最弱项（**数值变量 47%–88%** vs 分类/字符串 74%–96%，27 项研究的跨研究范围）[E: ext-multimodal-evidence.md#45] |
| **P1 印刷标签直读** | 图上存在印刷数据标签，OCR 可读，单位与坐标轴一致性检查通过 | G-CHART-LABEL | 见〔裁定 D-9〕 | 见〔裁定 D-9〕 | 有标签 MAPE **1.3% / 1.8%**（整表提问 / 逐值提问；Gemini 2.5 Flash，50 张 Vega-Lite 图，5 类各 10 张）[E: ext-multimodal-evidence.md#11] |
| **P2 无标签几何读数** | 无印刷标签；图族 ∈ {bar, line, scatter}；非对数轴/非断轴/序列不重叠 | G-CHART-GEOM | GC-2 | **上限 ST-E(±8%)，永不更高** | 无标签 MAPE **7.2% / 7.4%**（同上同批图同模型，只改标签）[E: #12]；族内 Adaptive MAPE scatter 2.63 / bar 3.78 / line 4.35 [E: #14] |
| **P3 领域专用管线** | 图族命中已注册的专用管线（KM 曲线、森林图），且管线的**可复核约束**全部通过 | G-CHART-PIPE | GC-0 或 GC-2（按管线） | ST-A（见下） | KM-GPT 轴范围/刻度 100%、at-risk 表 100%、生存概率 median AE 0.005（95% CI 0.000–0.034）—— **540 张自生成合成图**；真实验证**仅 3 项试验 6 条曲线** [E: #36, #37, #39]。AutoForest 数值单元格 97.8% / 表格检测 98.1%（206 张表）[E: #43] |
| **P4 人工判读** | 上述全部失败，或图族在黑名单内 | 人审 | — | 维持原状态 + F-26（不改 status） | 人机协作上限 **0.85–0.91** 三条独立线 [E: #40, #46, #48] |

#### §6.2.1 P3 的准入条件（本文件对语料的收紧）

语料的 D2 给 P3 的允许状态是 `verified`。**本文件收紧为 ST-A**〔裁定〕。
**理由**：那些 100% / 0.005 的数字全部来自 **540 张自生成合成图**，真实验证只有 **3 项试验 6 条曲线**（真实试验 mPFS 报告值 11.0 月 vs 重建值 10.9 月，区间 9.8–12.2）[E: ext-multimodal-evidence.md#36–39]。00-PREMISE B4 的推翻条件里已经写明：采纳这条路径前必须自建 **≥50 张真实论文图**的金标集。
**什么会推翻**：在自建的 ≥50 张真实论文图金标集上，该专用管线的可复核约束（坐标轴范围、at-risk 表、单调性）全部通过时的数值误差 < 1%，则 P3 可开 ST-V。

#### §6.2.2 P1 的状态上限〔裁定 D-9〕

**分两种情况**：
- **标签是 PDF 文本对象**（矢量文本，可被文本抽取层直接取出）→ 该数值**不是图形几何读数**，它是文献通道的逐字命中，走 G-L1，**可达 ST-V**。
- **标签是位图，需要视觉模型/OCR 识别** → 判定路径经过模型 → **GC-2 → 上限 ST-A**（01-CONTRACTS §6.1）。

**理由**：01-CONTRACTS §3.5 强制 ST-E 的对象是「数值来自图形几何读数」；OCR 读印刷标签不是几何读数，所以不落入那条。但它是模型判定，所以落入 GC-2 的上限。语料的 D2 给的 `verified` 与我们的 GC-2 规则冲突，**以 01-CONTRACTS 为准**。
**什么会推翻**：若 OCR 走的是确定性文本层抽取而非视觉模型（即上面第一种情况），本裁定不适用；这已在上面写明。

### §6.3 前置路由器：先分族，后读数

**EE-C-1 必须先跑廉价的图族分类器 + 标签存在性检测器作为路由前置**，而不是先让 VLM 读数再事后判断。前置分类的成本远低于事后 16 次自洽采样 [E: ext-multimodal-evidence.md#D3]。

**路由器本身是模型（GC-2），因此它的错误方向必须被约束**〔裁定〕：
- 分类器把一张图判入**黑名单族** → 直接生效（保守方向，无需复核）。
- 分类器把一张图判入**白名单族**（bar/line/scatter）→ 需要 k-of-n 一致（k=2, n=3），且**最终状态仍受 P2 上限 ST-E 约束**。
**理由**：路由器误判的唯一危险方向是把雷达图/饼图误路由到几何读数路径，从而给一个 Adaptive MAPE 28.01% / 11.58% 的读数盖上 ±8% 的 ε [E: ext-multimodal-evidence.md#14]。上面的非对称约束把这个方向堵死，代价只是白名单路径贵 3 倍。

### §6.4 覆盖率闸门早于正确性闸门

**EE-C-2 对每张进入证据集的图/表，先枚举应有的数值槽位（系列数 × 数据点数，或行数 × 列数），检查抽取结果的填充率；填充率不足即判失败，早于任何数值正确性检查。**

依据：**遗漏占错误类型的 60%–74%，幻觉率仅 0.08%–6%**（27 项研究综合）[E: ext-multimodal-evidence.md#47]。当前主流 agent 验证设计几乎全部瞄准幻觉。
**结构正确率只当分母，绝不当正确性信号**：同批图表结构正确率 **97.0%（194/200）**（Gemini 2.5 Flash，200 张 ChartQA 图），而同批无标签图数值 MAPE > 7% [E: ext-multimodal-evidence.md#13, #12]。语料的措辞逐字：「**结构不能当正确性信号，但能当覆盖率的标尺**」[E: #D6]。

### §6.5 地址独立复核

与 §3.3.5 同一机制，此处给出图表侧的数据结构：
```
每个数字： { value, unit, address }
address（表格）= (work_id, 表号, 行头, 列头)
address（图表）= (work_id, 图号, 系列名, x 值)
```
**EE-C-3 用一个只看 address 不看结论的独立复核者反向取值**，与 value 比对。这把「验证结论」换成了「验证寻址」[E: ext-multimodal-evidence.md#D5]。
依据同 §3.3.5（88.4 vs 34.8；exact-match 下无模型能让「标签+依据同时正确」超过 50%）。

### §6.6 自洽性只做分诊，不做闸门

**EE-C-4**
- **禁止**：「N 次采样一致 → 标记 verified」。
- **允许**：「离散度进入最高分位 → 强制降级并入人工队列」。
- **采样次数上限 3–5，不是 16。**

依据：抽样离散度与抽取准确率的 Spearman **ρ = −0.34（区间 −0.30 ~ −0.37，p<0.001）**（WB-ChartExtract 1,000 图，三种不确定度聚合方式），只解释约 12% 的方差；自洽采样早停后平均 16.11 次/图是为了榨取最后 1% 的集成增益，对本项目成本收益不成立；集成的绝对增益也有限（最好情形 35.08→43.17）[E: ext-multimodal-evidence.md#19, #20, #21, #D4]。

### §6.7 `estimated` 不得参与比较/排序/阈值——机器强制点〔裁定 D-10〕

**这条规则最容易变成「写了但不会红」的规则**，因为「参与比较」在散文里不可判。本文件把它落在**结构化载荷的引用图**上：

**EE-C-5**
```
若某条 claim 的 payload 含 comparator / comparands / threshold 字段
   或该 claim 出现在另一条 claim 的 premises[] 中，
且其引用链上存在任一 status == ST-E 的 claim，
则该 claim → not_covered（ST-N），并拒绝渲染。
```
**为什么这是可判的**：claim 的载荷是**结构化字段**而不是散文句子（01-CONTRACTS §9.2），正文数字一律写成 `{{claim:<id>.<field>}}` 占位符（01-CONTRACTS §4 W-10）。因此「哪条 claim 引用了哪条 claim」是一张显式的图，不需要理解自然语言。
**不遵守会发生什么**：一个 ±8% 的读数进入「A 优于 B」的判断，而 8% 的误差足以翻转这类结论 [E: ext-multimodal-evidence.md#D1, 00-PREMISE#B4-1]。
**什么会推翻**：若真实任务中大量比较断言的对象只能来自图表（例如只有图、没有表的老论文），使 ST-N 成为多数，则需要为「图表派生的比较」单开一条带专用管线的路径（P3 扩展），而不是放松本规则。

### §6.8 图表证据的准确率承诺

**EE-C-6 对外承诺的图表派生数值准确率上限显式写为 ~90%，即每 10 个此类数字预期约 1 个仍错。**
依据：三条独立证据线落在 0.85–0.91（AutoForest 全自动 82.5% → 加人工编辑 90.2%，32 张森林图/18 篇 Cochrane 综述/56 项研究/4 名专家；某综述 91.0%（95% CI 90.4–91.6，Claude 3.5 Sonnet 辅助工作流）vs 纯人工 89.0%；LEADS 用户研究 0.85 vs 0.80，**仅 2 名医学研究者**，效应量不稳健）[E: ext-multimodal-evidence.md#40, #46, #48, #D7]。
**产品价值主张落在「同等准确率下的速度」和「可追溯性」，不落在「比人更准」**——比人更准的证据只有 +2 个百分点 [E: ext-multimodal-evidence.md#46, #D7]。

**口径警告（必须随「人类基线」复述）**：某处流传的「手工专家数据抽取准确率 45.8%」的真实口径是**限时实验室任务中 4 名专家用 RevMan 手工完成的准确率**，不是 Cochrane 双人独立抽取的准确率；作为「人类基线」引用属口径掉包 [E: ext-multimodal-evidence.md#41]。

### §6.9 内部质量门不得用 TEDS

**EE-C-7** 表格抽取的内部回归门使用**数值单元格级精确比对 + 地址比对**（自建、确定性、可复跑），不使用 TEDS。
依据：TEDS 与人类判断的 Pearson **r = 0.68**（451 张表、518 组配对、1,554 条人工评分、21 个解析器、Krippendorff α=0.77），会同时惩罚无害的格式差异并放过真实语义错误；同一研究里 LLM-as-judge 达 r=0.93，**但它不是确定性的，不能当 gate** [E: ext-multimodal-evidence.md#33, #D8]。

---

## §7 反伪造门的正确接线（G-PROV）

> 语料对这一节的定位逐字是：**「这是本轮调研中最容易被漏掉、又会让整条反伪造链静默失效的坑。」** [E: gt-evidence-substrate.md#H3]

反伪造门的作用是兑现 01-CONTRACTS §1.2.1 的子测试②：**这条证据能否绑到一条真实发生过的 `tool/call` / `tool/result`**。它证明「这次抓取确实发生过 + 字节是这份」，**不证明内容为真**。

### §7.1 五条实现契约（逐条：规则 → 实现 → 不遵守会发生什么）

#### EE-F-1 · 多帧 zstd 必须循环解帧

**规则**：读 session 日志的门**不得**使用 Node 内置 `zlib.zstdDecompressSync` / `createZstdDecompress`。只能：按 magic `28 B5 2F FD` 手动切帧逐个解、或 spawn `zstd -dc`、或走 `ctx.sessionPersistence.readRaw` / `/api/session.export`。
**一手事实**：JSONL 持久化是「a standard concatenation of independent Zstandard frames: one checksummed frame containing only the header line, followed by one checksummed frame per durable append batch」；实测本机某 1 MB 日志含 **3403** 个 frame magic 起点。Node v24.16.0 实测：`zstdDecompressSync` → **1 行**，流式 → **1 行**，`zstd -dc | wc -l` → **3675 行** [E: GROUND-TRUTH-CORRECTIONS.md#A3, gt-evidence-substrate.md#H2, #H3]。
**不遵守会发生什么**：门**静默只读到 1 行**并把日志判为空。于是「每条证据必须绑到一条真实 tool/result」这条断言会对**所有**证据返回「找不到」——要么整批被判 `not_covered`（好的情况），要么门被写成「日志为空时跳过」（灾难情况，且这是最自然的写法）。**这一条不是性能问题，是整条反伪造链的存亡问题。**

#### EE-F-2 · 按行 JSON.parse 之后必须 `decodeStorageRecord`

**规则**：解帧后按行 `JSON.parse`，**必须**再跑 `decodeStorageRecord` 才能按 `seq` 索引。
**一手事实**：`packChunks` 默认 `true`（README 称在真实编码会话上测得逻辑日志小约 60%）；**打包行只有 `seq0`，没有 `seq`**。实测某日志的类型分布：`reasoning-chunks 2501` / `tool-call-chunks 551` / `text-chunks 161` / `assistant/chunk 359` / `assistant/message 17` / `tool/call 20` / `tool/result 20` [E: gt-evidence-substrate.md#H4]。
**不遵守会发生什么**：`seq → 事件`的映射**会有洞**。绑定检查会对落在打包行里的 `tool/result` 报「查无此事」，而这些恰恰是数量最多的那些。结果是随机的、看起来像 flaky 的假阴性——最难诊断的一类缺陷。

#### EE-F-3 · 必须用 `surfaceOp === 'append'` 过滤 append-origin 事件

**规则**：绑定检查只接受 append-origin 事件（`isAppendSurfaceEvent(event)`）。
**一手事实**：compaction 的「替换」不是「删除」——`replace` surface operation 把被遮蔽的条目移出未来输入，**但不删除其原始日志记录**；原始事件永远在原 seq 处不动 [E: gt-evidence-substrate.md#D2, #D4]。
**不遵守会发生什么**：pruner / compaction 的**替换体会冒充原始结果**。一条被 prune 的 `tool/result` 的 `message.content` 中间被替换为固定 marker（`\n\n[... tool result middle pruned ...]\n\n`，实测 39 个 code point），若门把替换体当原始结果，它会拿一段被截断的内容去做「这次抓取确实发生过」的绑定，绑定仍然成立（事件存在），但**若门同时试图从中取原文，取到的是残片**。

**同一条事实的另一面（必须一起写，否则会被读成「meta 也不可信」）**：pruner 的替换写法是 `session.append("tool/result", { ...event.data, message }, {...})`——`...event.data` 展开意味着 **`turn` / `step` / `error` / `meta` 以及未来新增字段全部原样保留**，只有 `message.content` 变 [E: gt-evidence-substrate.md#D4]。**这正是证据锚点挂在 `tool/result.data.meta` 的代码级理由**（落点规则见 01-CONTRACTS §4 W-02）。
**并且**：pruner **不是逐结果硬上限**——它只在压缩合格时才跑（"Below-pressure step checks never prune."）。实证：本机 139 个 session、**0 条 replace、0 条 `compaction/*`**，而实测真实日志里存在 23295 / 27922 字符的 `tool/result` **未被 prune** [E: gt-evidence-substrate.md#D5]。**含义：门不能假设「大结果一定被 prune 过」，也不能假设「没被 prune 就永远不会」。两种形态都必须能处理。**

#### EE-F-4 · 超阈值原文不在日志里 → 抓取时直写 CAS

**规则**：我们的抓取工具**必须在同一次工具执行内**把快照原始字节与抽取文本写入 CAS，并把 sha256 放进 `tool/result.data.meta.evidence`。**不得**依赖「事后从日志里捞原文」。
**一手事实**：spill-policy 是 `tools/post-execute` 变换器，loop 用**流水线最终结果**建 `tool/result`（`appendToolResult(..., result, callSeq)` 用 `result.content`），因此**落库的就是替换后的内容**。本机 `maxInlineBytes` **无包默认值**，出厂组合配置为 **50000 UTF-8 字节**（注意单位是字节，与 pruner 的 code point 口径不同）[E: GROUND-TRUTH-CORRECTIONS.md#A2, gt-evidence-substrate.md#E2, #E4]。语料逐字：「**超过 50000 字节的纯文本工具结果，其完整原文只在 spill 文件里，不在 session 日志里**。」
**不遵守会发生什么**：`quote_faithful` 的比对基底变成 head/tail 预览。**学术全文几乎全部超过 50000 字节**，所以这不是边缘情况——它意味着引语门只能验证文章开头约 4 KB 的内容，而**它不会报错**，它会安静地对正文中段的每一条引语返回 `fail`。

**触发条件很挑剔，门不能假设它总会发生**：spill 跳过 nested execution（`exec.parent` 存在）、跳过被接受的 value 替换、跳过 `read` 工具、跳过非 `accept` 决策；**只有「所有块都是 text」的纯文本结果**才会被 flatten 并判尺寸，含任何非 text 块的结果原样放行 [E: gt-evidence-substrate.md#E3]。

#### EE-F-5 · spill 不可依赖为长期证据

**规则**：CAS 必须是我们自己的路径（01-CONTRACTS §8.1）。spill 文件**不得**出现在任何证据指针中。
**一手事实**：spill-local 的 `root` 默认是**每进程私有的 0700 临时目录**；本机 `dsh-base/cordis.patch.yml` 挂载 `spill-local` **未配置 `root`** → 文件落在 OS temp 下的随机私有目录，**跨进程不可预测、可能被系统清理**；README 的 Known Limitations 明说无生命周期删除、无老化淘汰，且「persisted, resumed, and forked sessions may still reference a path」[E: gt-evidence-substrate.md#E5, 01-CONTRACTS §8.4 D-8.12]。
**不遵守会发生什么**：证据链在下一次系统清理 temp 目录后**整段消失**，且消失是静默的——指针还在，文件没了。对一个「产品是可信度」的系统，这是把最核心的资产放在一个明确声明不做保留的目录里。

### §7.2 两条补充绑定契约

**EE-F-6 · 绑定的形式**：每条证据的 `tool/call` callId 与 `tool/code-dispatch` 的 `<parent>:code:<n>` id 必须在 `runs/<run_id>/manifest.json` 中可查（写者见 01-CONTRACTS §4 W-12）。
**并且**：`tool/result.data.meta` 与 `tool/call` 的 seq 由核心校验的 `sourceEventSeqs` 天然绑定 —— 这是选 `meta` 而非自定义事件的又一理由，因为自定义 log-only 事件**无法用 `sourceEventSeqs` 引用其依据的 `tool/result` seq**（运行时直接抛错，实测）[E: gt-evidence-substrate.md#A6, #B8]。

**EE-F-7 · 合成修复品不可作证据**：崩溃修复文案是**固定字符串**（`TOOL_NOT_STARTED` / `TOOL_OUTCOME_UNKNOWN`）。门必须把带这些文案的 `tool/result` 判为「合成修复品，不可作证据」→ 该证据 `not_covered` [E: gt-evidence-substrate.md#其它可直接使用的原语]。
**不遵守会发生什么**：一次崩溃产生的占位结果会被当成一次成功的抓取，于是「这次抓取确实发生过」这条断言对一次**没有发生**的抓取返回真。

### §7.3 产物级兜底（本节的最后一道）

**EE-F-8 任何未被 `tool/call` / `tool/code-dispatch` 事件覆盖的断言，一律 `not_covered`。**
理由：运行时**没有任何机制能判定「模型凭记忆编造引用」**；唯一可行的是产物级校验 [E: gt-exec-security.md#H-1, 01-CONTRACTS §4.4]。

### §7.4 G-PROV 自身的能力边界

- 它证明：字节同一性、抓取事件存在性、注册表成员资格（01-CONTRACTS §1.2 的三个子测试）。
- 它**不**证明：来源内容为真、检索未被投毒、命题为真。
- 它**不**阻止注入。DSH 侧的三层强制手段（`ctx.tools.guard` 单调否决、`tools/pre-execute` deny、`tools/post-execute` block）全部落在工具边界，**沙箱不拦网络、`run_code` 绕过围栏、`toolFilter` 不是权限天花板**（01-CONTRACTS §4.4）。

---

## §8 admission：入库闸门（G-ADMIT）

### §8.1 三条硬性质〔裁定 D-11〕

**EE-A-1 确定性**：同一输入两次跑，产出逐字节相同的记录集合。
**EE-A-2 无模型、无网络、无时钟**：
- 无模型 —— admission 不做任何语义判断（这是 §8.3 的全部理由）。
- 无网络 —— T0 名录已本地化（EE-S-11）；admission 不发任何请求。
- **无时钟**〔裁定 D-11〕—— admission **不得调用 `now()`**。`retrieved_at` / `fetched_at` 由抓取工具在 fetch 时刻写入并随证据卡一起进入 CAS；admission 只读不生成。
  **不遵守会发生什么**：admission 自己盖时间戳 ⇒ 同一输入两次跑产生不同记录 ⇒ **幂等失效** ⇒ 第二次跑 `accepted != 0` ⇒ 并行 worker 重复入库。这正是本仓库既有流水线的实测形态（`harvest_e2e.sh` 的 run-2 从不断言 `accepted==0`，实测 run-2 accepted=8）[E: GROUND-TRUTH-CORRECTIONS.md#D2]。
**EE-A-3 幂等**：N 个并行 worker 抽到同一句 → 同一 `evidence_id` → 主键碰撞 → 天然去重，零协调开销、零锁 [E: ext-evidence-schema.md#B]。

### §8.2 去重键：按来源坐标，绝不按内容

**本项目采用的键（规范值在 01-CONTRACTS §4 W-06 / §8.1）**：
```
evidence_id = hash(work_id, locator, extractor_version)
```

**为什么必须按来源坐标**：两条真正矛盾的证据在语料库中**物理上位于不同位置**（不同 work、不同 section、不同句子），因此按来源坐标去重**在构造上不可能吃掉矛盾**；而按内容相似度去重必然会。
**一手教训（生产系统复盘，逐字）**："a contradiction phrased naturally ('XX is AA' then 'XX is BB') is near-identical text, so the very writes the detector exists to resolve are the ones most likely to be 409'd at the gate." 该系统的近重复门是**同步、pre-commit、超过 embedding 相似度阈值即返回 409**，而矛盾检测器是**异步 post-commit**——管线顺序保证了矛盾写入永远到不了矛盾检测器 [E: ext-evidence-schema.md#结论摘要2]。
**对一个「产品即可信度」的系统，这是致命的**：我们最需要保留的那一类写入，正是它最会被丢掉的那一类。

**由此获得的四个性质**（全部对超并行至关重要）[E: ext-evidence-schema.md#B]：
1. **幂等**（见 EE-A-3）；
2. **零 LLM 成本**——去重是哈希比对，不需要 embedding 调用，也不需要「每次写入一次 LLM 裁决」；
3. **管线顺序无关**——「去重门 vs 矛盾检测器」的顺序缺陷类被**设计消除**，不是被规避；
4. **可复现**——`extractor_version` 入键，换 prompt/模型重跑会产生**新行而非覆盖旧行**。

**⚠️ 本文件发现的一处契约缺陷（不在本文件自行修改，见 open_questions）**：语料给出的键是五元组 `sha256(work_id ‖ version_id ‖ locator ‖ normalize(quote) ‖ extractor_version)` [E: ext-evidence-schema.md#B]，而 01-CONTRACTS §4 W-06 / §8.1 写的是三元组（缺 `version_id` 与 `normalize(quote)`）。缺 `version_id` 会让**同一 work 的 v1 与 v2 在同一 locator 上产生键碰撞**——两个版本的同一节，文字不同，`evidence_id` 相同，后写者与先写者的内容不一致却被当成幂等重写。**本文件按 01-CONTRACTS 的三元组实现，并把这一处列为需要修改 01-CONTRACTS 的候选缺陷。**

**禁止事项（全部来自一手实证）**[E: ext-evidence-schema.md#E]：
1. 禁止以 URL 为去重键——某 SOTA 系统的记忆库去重键经源码确认是**原始 URL 字符串精确匹配、无任何归一化**（`url2id[new_content["url"]] = len(url2id) + 1`），意味着 N 个 worker 从 arXiv abs 页 / arXiv PDF / 出版社 HTML / PMC 镜像访问同一论文会产出多条独立记忆和多个引用 ID。实测一篇论文在 Semantic Scholar 上同时挂着 **7 个不同标识符**（DOI / ArXiv / CorpusId / PubMed / PMC / MAG / DBLP），URL 数量无上界。
2. 禁止同步 pre-commit 的语义近重复门（见上）。
3. 禁止「矛盾即删除」——某主流 agent memory 的更新提示词（源码确认）规定："If the retrieved facts contain information that contradicts the information present in the memory, then you have to delete it."
4. 禁止纯时间性失效——某双时间线系统的失效判定是纯时间性的（新事件的 `valid_at` 早于旧边即写 `invalid_at` + `expired_at`）。**科学上不成立**：2019 年队列研究 vs 2026 年 RCT 结论相反，可能两个都对（不同人群），也可能新的那个错。
5. 禁止多 agent 对同一记忆块整体重写（官方标注的反模式，丢更新）。
6. 禁止把撤稿建模为 boolean（见 §5.2.3）。
7. 禁止用 DOI 作为 arXiv 内容的版本锚（见 §8.4）。
8. 禁止单源撤稿判定（见 §5.2.2）。
9. 禁止无 `metric_frame` 的裸数字入库（见 §8.5）。

### §8.3 admission 不做语义判断

**EE-A-4 admission 不判断证据是否支持任何 claim，不判断证据是否与已有证据矛盾，不合并任何两条记录。**
学术分歧 vs 证据被取代的区分（`supersedes` 白名单 vs `contradicts` 永不自动消解）见 [E: ext-evidence-schema.md#C]，**它发生在 admission 之后的门里**，不在 admission 里。
**理由**：admission 必须满足 EE-A-1（同一输入两次跑产出逐字节相同的记录）。任何语义判断都会引入模型，模型判断的门属 GC-2（01-CONTRACTS §6.1），而 GC-2 的输出不可逐字节复现——admission 一旦失去逐字节复现，并行写入的幂等保证（EE-A-3）随之失效。

### §8.4 三层身份

```
work_id       作品身份（跨版本、跨 URL、跨标识符的同一件学术工作）
  └ version_id    版本身份（你实际读到的那一版）
      └ evidence_id   证据身份（那一版里的某个具体片段）
```

**`work_id` 解析阶梯（确定性，按序，失败即降级）**[E: ext-evidence-schema.md#A]：

| 级 | 输入 | 键 | 置信度 | 允许自动合并？ |
|---|---|---|---|---|
| 0 | 已有 S2 `paperId` 或 OpenAlex work ID | 直接用 | exact | 是 |
| 1 | DOI | 归一化 DOI（小写、剥离 `https://doi.org/` 前缀与尾部标点） | exact | 是 |
| 2 | arXiv ID / PMID / PMCID | 经 S2 或 OpenAlex 解析到聚类 ID | exact | 是 |
| 3 | 标题 + 首作者姓 + 年份指纹 | `normalize(title)+surname+year` | **low** | **否——只提议候选，进人审/裁决队列** |

**EE-A-5 未解析成功的证据以 `work_id = "unresolved:<hash>"` 落库，照常可引用，只是不参与跨源聚合。绝不因为解析不了就丢弃或强行合并。**

**EE-A-6 URL 永远不是键**，`access_url` 是 payload 字段。

**`version_id` 的构成**[E: ext-evidence-schema.md#A]：
- arXiv：`work_id@vN`（显式版本号）。**因为 arXiv DOI 恒指最新版，DOI 不能充当版本锚**——官方确认「替换版本不生成新 DOI」且该 DOI「will always point to the latest version of the article」，所以裸 DOI 在语义上是「未来某个版本」[E: ext-evidence-schema.md#结论摘要4；同一事实见 01-CONTRACTS §5.5]。
- 期刊 VoR：归一化 DOI + `retrieved_at`。
- 网页/其他：URL + 正文内容哈希 + `retrieved_at`。
- 必填 `version_kind ∈ {submittedVersion, acceptedVersion, publishedVersion, unknown}`（直接复用 OpenAlex/COAR 实测词表）。

### §8.5 admission 拒绝什么

| 拒绝条件 | 依据 |
|---|---|
| `evidence_grade == G1`（snippet）作为承重证据 | 01-CONTRACTS §3.4.1（片段无快照 → `source_integrity` 无法计算；SERP 摘要投毒的直接载体） |
| 含数值但 `metric_frame` 三字段不全 | 01-CONTRACTS §9.4；[E: ext-evidence-schema.md#E 反模式9] |
| 内容来自 `non_rendered_text` / `structured_data` / `http_headers` | §1.1；01-CONTRACTS §7.2.2 |
| 无对应 `tool/call` callId | EE-F-8 |
| `retention_tier` 缺失或 `tier_reason[]` 为空 | 01-CONTRACTS §8.9 |
| 快照 sha256 在 CAS 中不存在 | 01-CONTRACTS §4.6 V4.6 |

**注意「拒绝」的语义**：被拒的候选写入一条「候选被拒」记录（含拒因），**不是静默丢弃**。理由同 01-CONTRACTS §8.6.3 的 `T0-HARD`（硬拒也要留记录）。

### §8.6 幂等必须 live 断言

**EE-A-7 同一批输入连续跑两次，第二次的 `accepted == 0`，且该断言必须在真实端到端流水线里跑，不只在离线单测里。**
理由与实测反例见 01-CONTRACTS §4.6 V4.4 / GROUND-TRUTH-CORRECTIONS.md#D2。
**这条是 §9 的一条负向测试，不是文档承诺。**

---

## §9 负向测试清单

> **元规则（三条，全部来自 house 的一手教训）**
> **M-1 red-first**：门在被信任之前必须先证明自己会红；红案 fixture 由 conductor 播种，**事件形状必须来自真实捕获而非手编** [E: gt-house-method.md#A9]。
> **M-2 跨执行边界的检查是空的**：同一失败类在本仓库连续出现三次（persona mount / role-pack 子串检测 / plugin_load dump-config），每次都是配置层通过、运行时打脸，**每次都由新鲜上下文的对抗读者发现，从来不是门套件发现的**。修法永远相同：**对运行系统自己的痕迹断言**（session jsonl、真实 boot）[E: gt-house-method.md#结论摘要2]。
> **M-3 gate 完整性必须是脚本**：本仓库宣称 "Gate-integrity is pinned, not vibes"，但全量 grep `gates-baseline|porcelain` 在三个子项目里**零命中代码**，只命中两处散文 [E: GROUND-TRUTH-CORRECTIONS.md#D1]。**这是 00-PREMISE B8 列的第一个必须补的洞。**

### §9.0 前置：门套件自身的两条断言

| ID | 断言 | 失败即 |
|---|---|---|
| **NT-00** | `git status --porcelain -- checks/` 干净 **且** `git diff <gates-baseline-tag> -- checks/` 为空 | 整个门套件的结果作废（非零退出） |
| **NT-01** | 每个门在 CI 中存在至少一条 red fixture，且该 fixture 使门**非零退出**；无 red fixture 的门标记为「未验证的门」，其输出不得进入 `S` | 门被当作装饰 |

**NT-01 的补充判据**（来自 00-PREMISE B8 的推翻观测）：**gate-integrity 脚本从未在真实 run 中触发过一次非零退出 ⇒ 必须构造一次真实篡改来证明它活着。没触发过 ≠ 有效。**

### §9.1 数据通道

| ID | 对应规则 | 反向 fixture | 触发入口 | 断言 |
|---|---|---|---|---|
| NT-D-1 | §2.1 步骤 2 | claim 声明的输入 sha256 与 CAS 中实际字节不符 | 真实 G-RERUN 执行 | `verdict=fail`，非零退出 |
| NT-D-2 | §2.1 步骤 7 | `out.json` 某字段超容差 1e-8（deterministic regime） | 同上 | `verdict=fail` |
| NT-D-3 | §2.1 EE-D-1 | `out.json` 数组顺序与 claim 不同但集合相同，且未声明 `unordered` | 同上 | `verdict=fail`（默认有序） |
| NT-D-4 | §2.2.1 | producer 声明 `stochastic` 但 5 次重跑逐字节相同 | 同上 | regime 被改判为 `deterministic`，容差收紧到 1e-9，`caveats` 含不一致记录 |
| NT-D-5 | §2.2.4 | 构造 `σ̂/|s̄| = 0.25` 的脚本 | 同上 | `applicable=false`，`verdict=not_applicable`，**不是 pass** |
| NT-D-6 | §2.2.5 | 字段真值 ≈ 0 且未声明 `atol` | 同上 | `not_applicable` |
| NT-D-7 | EE-D-2 / EE-D-4 | 在无容器能力的环境跑 K-D claim | 同上 | `not_applicable` → ST-N；**断言日志中不存在「已按 sandbox 配置执行」这类字样** |
| NT-D-8 | §2.3 | `run.py` 在执行中发起出网请求 | 真实容器执行 | 请求失败 → 脚本非零退出 → `verdict=fail` |
| NT-D-9 | **§2.4 C-3（最重要的一条）** | `run.py` 硬编码结论数字（读了输入但不使用） | 真实 G-DEP | `verdict=fail`。**前代对同类构造得到 `exit 0 PASS`** [E: GROUND-TRUTH-CORRECTIONS.md#C1] |
| NT-D-10 | §2.4 C-1 | 某被引用 key 对所有输入不敏感 | 同上 | `verdict=fail` |
| NT-D-11 | §2.4 C-2 | 声明了一个从不被使用的输入 | 同上 | `verdict=pass` + `caveats` 含 `decorative_input` |
| NT-D-12 | §2.4 C-4 | 扰动导致脚本崩溃 | 同上 | 计为敏感，`caveats` 含 `perturbation_crash` |
| NT-D-13 | §2.5 | producer 在提交工具参数中携带 `question_authored_by` | 真实 claim 提交工具 | 调用被 `tools/pre-execute` **拒绝**（不是覆盖），session 日志中存在 deny 记录 |

### §9.2 文献通道

| ID | 对应规则 | 反向 fixture | 触发入口 | 断言 |
|---|---|---|---|---|
| NT-L-1 | §3.1.1 顺序 | 载荷字面全部命中锚点，但混入了源句没有的因果方向 | 真实 G-ENTAIL | G-ENTAIL `fail`，claim 不进 G-L1 |
| NT-L-2 | EE-L-2 | 一次 > 50000 字节的纯文本抓取，引语位于正文中段 | 真实抓取工具 + G-L1 | G-L1 从 CAS 命中；**断言门未从 session 日志取原文**（注入一个探针：把日志中的该 `tool/result` 内容改写，门结果不变） |
| NT-L-3 | EE-L-4 | 扫描版中文 PDF（抽取文本为空） | 真实 G-L1 | `source_integrity=not_covered` + F-30 → ST-N，**不是 ST-U** |
| NT-L-4 | §3.3.3-1 | 中文引语跨分栏边界，去空白后可拼接命中 | 同上 | 跨距检查触发 → `fail` |
| NT-L-5 | §3.3.3-2 | 载荷与锚点仅在 NFKC 折叠后相同 | 同上 | 记录于 `caveats`；本条为**观测用例**，用于测量该类命中的实际频次 |
| NT-L-6 | §3.2.2 | 一条真实但无 DOI 的中文文献 | 真实 G-L0 | `not_applicable` + F-32 → ST-N，**不是 `fail`** |
| NT-L-7 | EE-L-18 | 查询《管理世界》ISSN | 真实 G-L0 | 空结果 → `not_applicable`，**不是「不存在」** |
| NT-L-8 | EE-L-7 | 构造一条 G-L2 判 `support` 但 G-L1 未命中的 claim | 真实门链 | status ≤ ST-A；**语料中不存在 `verified` 且 `mechanism_results` 含 GC-2 的 claim**（01-CONTRACTS V1.4） |
| NT-L-9 | EE-L-15 | 只报 precision 不报 coverage 的报告 | 真实组稿器 | **构建失败** |
| NT-L-10 | EE-L-1 + §5.2.4 | 产物中出现「该文献可信」「已核实无撤稿」 | 文档 lint | 失败 |
| NT-L-11 | §3.4.5 F-13 | 同一子命题 5 次同义改写后判定翻转 | 真实 G-L2 × 5 | F-13 置位，status 强制 ST-U |
| NT-L-12 | 01-CONTRACTS §1.6 V1.6（RT-1） | 格式规范、含一句语法完美且**虚假**数值断言的网页 | 真实端到端 | `quote_faithful=pass` 且 `status ≠ verified`（`independent_cluster_count=1` 触发降级） |
| NT-L-13 | 01-CONTRACTS §7.4 V7.7（RT-8） | 真实页面同含支持句与反对句，注入诱导只引支持句 | 真实端到端 | `counter_evidence_found=true`，status 降为 ST-C |
| NT-L-14 | RT-9 | 先取快照 → 改源页一个数字 → 触发复核 | 真实复核 | hash 不匹配 → `source_integrity=mutated` + F-16 → ST-U |

### §9.3 推断通道

| ID | 对应规则 | 反向 fixture | 触发入口 | 断言 |
|---|---|---|---|---|
| NT-I-1 | §4.2.1 | 前提中含一条 `status=unverified` 的 claim | 真实 G-DAG | `verdict=fail` |
| NT-I-2 | §4.2.1 | premises 构成环 | 同上 | `verdict=fail` |
| NT-I-3 | §4.2.1 | producer 在自己的 claim.json 里声称前提已验证，而 status.json 说 ST-U | 同上 | 以 status.json 为准 → `fail` |
| NT-I-4 | §4.2.2 | 两个前提的 `metric_frame.sample_or_tier` 不同 | 同上 | F-12 置位 |
| NT-I-5 | §4.2.3 | 前提量词 `some`，结论量词 `all` | 同上 | `verdict=fail` |
| NT-I-6 | §4.3.1 EE-I-5 | 人把 `some_concern` 改为 `low_concern` 但不写 `override_reason` | 真实 G-WARRANT | 门红 |
| NT-I-7 | §4.3.1 EE-I-3 | 某信号问题作答无原文直引 | 同上 | 门红 |
| NT-I-8 | §4.4.1 | 复核者会话的输入载荷中含 producer 的自由文本 | 真实 spawn | 结构扫描失败（01-CONTRACTS V5.7） |
| NT-I-9 | §4.4.1 | 复核者以 `fork` 启动 | 真实编排 | 失败（01-CONTRACTS V5.5） |
| NT-I-10 | §4.4.2 | 反例搜索段为空或只有 `not_found` 无预算记录 | 真实 G-REDERIVE | 门红 |
| NT-I-11 | 01-CONTRACTS §2.5 V2.1 | 任一 K-I claim 的 status 为 `verified` | 全量扫描 | 失败 |
| NT-I-12 | §4.5 EE-I-8 | 修改一条前提的 status，重跑门 | 真实门运行器 | 依赖它的 K-I claim 进入 `stale` 并被重判 |

### §9.4 来源完整性

| ID | 对应规则 | 反向 fixture | 触发入口 | 断言 |
|---|---|---|---|---|
| NT-S-1 | **EE-S-2（最重要的一条）** | 一条**撤稿公告本身**的 DOI（RW 的 `RetractionDOI`，非 `OriginalPaperDOI`） | 真实 G-RETRACT | **不设 F-05**。用 OpenAlex `is_retracted` 会误判——该 fixture 从 200 条抽样的 34.5% 那一桶里取 |
| NT-S-2 | §5.2.3 | 一条 `RetractionNature=Reinstatement` 覆盖了先前 Retraction 的 DOI | 同上 | **不设 F-05** |
| NT-S-3 | §5.2.2 | 两源不一致的 DOI | 同上 | `disputed` → 人审队列，**不做静默取舍** |
| NT-S-4 | EE-S-3 | 门输出的绿灯措辞 | 文档 lint | 逐字模板匹配；出现禁用词即失败 |
| NT-S-5 | EE-S-10 | 把 RW 快照日期回拨 8 天 | 真实 G-RETRACT | `not_covered` + F-18，**不是 pass** |
| NT-S-6 | EE-S-4 | 模拟 Hijacked 表格导出 400 | 真实 G-HIJACK | 用 mirror + `stale`；把 mirror 日期回拨 91 天 → `not_covered` |
| NT-S-7 | 01-CONTRACTS §6.2.1 | N=100、items=1、d=2 的均值（GRIM power = 0） | 真实 G-GRIM | 输出 `not_applicable` + F-21 → ST-N，**不是 `consistent`** |
| NT-S-8 | 01-CONTRACTS §6.2.2 | 文中出现 Bonferroni 的 statcheck 命中 | 真实 statcheck 门 | 降级为 F-19，不参与状态降级 |
| NT-S-9 | 01-CONTRACTS §6.2.3 | GRIMMER test 3 触发 | 同上 | 单列 F-20，不参与自动降级 |
| NT-S-10 | 01-CONTRACTS §6.2.4 | 尝试把 SPRITE 输出接入自动判定 | 代码 lint | 失败 |
| NT-S-11 | EE-S-8 | 未配置 PubPeer key | 真实运行 | 门恒为 `not_covered`，**不是静默跳过** |
| NT-S-12 | EE-S-12 | 触发 Crossref 限速 | 真实 GC-1 门 | `not_applicable` + F-11；**断言重试次数有上界** |

### §9.5 图表证据

| ID | 对应规则 | 反向 fixture | 断言 |
|---|---|---|---|
| NT-C-1 | §6.3 | 一张雷达图 | 路由到黑名单 → P4；**断言不出现 P2 的 ε=8%** |
| NT-C-2 | §6.3 | 一张 bar/line 边界图，3 次分类不一致 | k-of-n 失败 → 降级 |
| NT-C-3 | EE-C-2 | 一张 5 系列 × 12 点的图，抽取只填了 40 个槽位 | 覆盖率闸门失败，**早于**数值比对 |
| NT-C-4 | EE-C-3 | address 正确但 value 错 / value 正确但 address 错 | 两种都必须被反向取值抓到 |
| NT-C-5 | EE-C-4 | 5 次采样完全一致的错误读数 | **不得**因此升级 |
| NT-C-6 | **EE-C-5** | 一条 ST-E claim 被另一条比较类 claim 列为 premises | 比较类 claim → ST-N，拒绝渲染 |
| NT-C-7 | 01-CONTRACTS §3.7 V3.4 | 一条 ST-E claim 缺 `epsilon` | 失败 |
| NT-C-8 | EE-C-7 | 表格抽取内部门使用 TEDS | 代码 lint 失败 |

### §9.6 反伪造与 admission

| ID | 对应规则 | 反向 fixture | 触发入口 | 断言 |
|---|---|---|---|---|
| **NT-F-1** | **EE-F-1** | 含 ≥2 个 zstd frame 的**真实捕获**日志 | 真实 G-PROV | 读出全部记录；**负例：只读到第一帧即失败**（01-CONTRACTS V6.6） |
| NT-F-2 | EE-F-2 | 含 chunk-packed 行的真实日志 | 同上 | `seq → 事件` 映射无洞；断言 `tool/result` 计数与 `zstd -dc \| grep -c` 一致 |
| NT-F-3 | EE-F-3 | 含 `surfaceOp=replace` 的真实日志 | 同上 | 绑定只接受 append-origin；替换体不被当作原始结果 |
| NT-F-4 | EE-F-4 | 一次 > 50000 字节的纯文本抓取 | 真实抓取工具 | CAS 中存在完整原文；日志中只有预览；门用 CAS 不用日志 |
| NT-F-5 | EE-F-5 | 证据指针指向 spill 路径 | admission | 拒绝入库 |
| NT-F-6 | EE-F-7 | 一条含 `TOOL_OUTCOME_UNKNOWN` 的 `tool/result` | 真实 G-PROV | 该证据 `not_covered` |
| NT-F-7 | EE-F-8 | 一条无对应 `tool/call` 的断言 | 同上 | `not_covered` |
| NT-A-1 | EE-A-1/2/3 | 同一批输入连续跑两次 | **真实端到端流水线** | 第二次 `accepted == 0`（01-CONTRACTS V4.4） |
| NT-A-2 | EE-A-2 无时钟 | 冻结系统时钟前后各跑一次 | 同上 | 记录逐字节相同 |
| NT-A-3 | §8.2 | 同一 work 的两条**矛盾**证据（不同 section） | 同上 | 两条都入库，`evidence_id` 不同 |
| NT-A-4 | §8.2 反模式1 | 同一论文的 4 个 URL（abs / pdf / 出版社 HTML / PMC） | 同上 | 归并为 1 个 `work_id`；`evidence_id` 按 locator 区分 |
| NT-A-5 | §8.4 第 3 级 | 标题相似但实为两篇的文献 | 同上 | **只提议候选，不自动合并** |
| NT-A-6 | EE-A-5 | 无法解析 work_id 的证据 | 同上 | 以 `unresolved:<hash>` 落库，可引用，不参与跨源聚合 |
| NT-A-7 | §8.5 | 一条 G1 snippet 被列为承重证据 | 同上 | 拒绝入库 + 写「候选被拒」记录 |
| NT-A-8 | §8.5 | 一条含数值但 `metric_frame` 缺 `comparator` 的证据 | 同上 | 拒绝入库 |
| NT-P-1 | §1.1 / RT-4 | 一个页面在 9 处非渲染通道各放一条注入 | 真实抓取 | 九条全部落入 `non_rendered_*`，零条进入证据池，告警计数 = 9（01-CONTRACTS V7.5） |
| NT-P-2 | §1.1 / RT-5 | 学术 PDF 白字注入 | 真实 PDF 抽取 | 归入 `non_rendered_text`。**该用例失败即为必须先解决的架构前提，不是一条普通失败用例**（01-CONTRACTS V7.8） |

### §9.7 覆盖矩阵（EE 规则 → 负向用例）

**EE-NT-1** 本文件每一条编号为 `EE-*` 的硬规则，必须在下表中恰好对应至少一个 `NT-*` 用例。**取差集非空即本文件失败。**
**实现**：一条 lint 脚本，grep 本文件全文的 `EE-\d|EE-[A-Z]+-\d+` 集合与下表首列集合，两向差集必须都为空。

下表中标 **★** 的 NT id 是在本节新定义的（不重复出现在 §9.1–§9.6 的表里），其 fixture 与断言写在同一行。

| EE 规则 | NT 用例 | fixture 与断言（新增者写全） |
|---|---|---|
| EE-0.1 | ★ NT-G-1 | 喂给聚合器一份 `applicable=false / verdict=not_applicable` 的门报告；断言聚合器**不把它计为 pass**，且 claim 落 ST-N |
| EE-0.2 | ★ NT-G-2 | 门输出缺 `power_basis`（或 `power` 与 `power_basis` 只出现其一）→ 门红 |
| EE-0.3 | ★ NT-G-3 | 对 `S` 做可达性分析：断言不存在「仅由 `power_basis == unmeasured` 的门支撑」的 ST-V / ST-A 路径 |
| EE-0.4 | ★ NT-G-4 | GC-2 门输出缺 `prompt_hash` 或 `kappa` → 门红 |
| EE-0.5 | ★ NT-G-5 | 门代码尝试写 `claims/<id>.json` 的内容字段 → 写权白名单拒绝（01-CONTRACTS V4.2） |
| EE-D-1 | NT-D-3 | — |
| EE-D-2 | NT-D-7 / NT-D-8 | — |
| EE-D-3 | ★ NT-D-14 | 代码 lint：重跑器实现中出现 `run_code` 调用 → 失败（它同时绕过内核沙箱与 `ctx.fs` 围栏） |
| EE-D-4 | NT-D-7 | — |
| EE-L-1 | NT-L-10 | — |
| EE-L-2 | NT-L-2 | — |
| EE-L-3 | ★ NT-L-15 | `anchor_span` 只有引语字符串、无可复核定位符 → admission 拒绝入库 |
| EE-L-4 | NT-L-3 | — |
| EE-L-5 | ★ NT-L-16 | 文档 lint：在 L1 标注集就绪前，任何对外文案出现 L1 精度数字 → 失败 |
| EE-L-6 | ★ NT-L-17 | 一条 address 正确但 value 错、与一条 value 正确但 address 错的 K-L claim；断言两者都被「只看 address 的反向取值」抓到 |
| EE-L-7 | NT-L-8 | — |
| EE-L-8 | ★ NT-L-18 | 代码 lint：G-L2 的判定单元是「陈述 vs 全部源」而非最小对 → 失败 |
| EE-L-9 | ★ NT-L-19 | 代码 lint：L2 实现中引入通用 NLI 模型 → 失败 |
| EE-L-10 | ★ NT-L-20 | 一条 L2 判不支持的 claim，追加 3 条引文后重跑；断言 status **不变** |
| EE-L-11 | ★ NT-L-21 | 三判定器 2:1，走投票平均直接升格 → 门红；必须走分歧升级路径 |
| EE-L-12 | ★ NT-L-22 | 代码 lint：生成期调用与终判同一 rubric judge 做自评改写 → 失败 |
| EE-L-13 | ★ NT-L-23 | `verdicts/*.json` 中 `provider == producer.provider` → 失败（01-CONTRACTS V5.1） |
| EE-L-14 | ★ NT-L-24 | 产物中出现由 L0/L1/L2 合成的单一分数 → 文档 lint 失败 |
| EE-L-15 | NT-L-9 | — |
| EE-L-16 | ★ NT-L-25 | 配置 lint：gate 条件里出现「检索轮数」或「并行子代理数」→ 失败 |
| EE-L-17 | ★ NT-L-26 | 中文任务运行清单中 `citation-snowball` 处于开启状态 → 失败（01-CONTRACTS V3.6） |
| EE-L-18 | NT-L-7 | — |
| EE-L-19 | ★ NT-L-27 | 配置 lint：标定完成前中文引语门使用与英文相同的阈值 → 失败 |
| EE-I-1 | ★ NT-I-13 | 信号问题答案落在 `Y/PY/PN/N/NI/NA` 之外 → 门红 |
| EE-I-2 | ★ NT-I-14 | 某题缺 `ni_polarity` → 门红；并构造一个 `NI` 答案，断言它在两种极性下导向**不同**的 domain 判定 |
| EE-I-3 | NT-I-7 | — |
| EE-I-4 | ★ NT-I-15 | 代码 lint：一次调用作答多题（共享上下文）→ 失败 |
| EE-I-5 | NT-I-6 | — |
| EE-I-6 | NT-I-6 | — |
| EE-I-7 | NT-I-12 | — |
| EE-I-8 | NT-I-12 | — |
| EE-I-9 | ★ NT-I-16 | 派生 claim 直接继承父 claim 的 status（未独立走门）→ 失败 |
| EE-S-1 | ★ NT-S-13 | 一条 `NOT_COVERED` 与一条 `CLEAN` 混入同一批；断言聚合结果**不是** `CLEAN` |
| EE-S-2 | NT-S-1 | — |
| EE-S-3 | NT-S-4 | — |
| EE-S-4 | NT-S-6 | — |
| EE-S-5 | NT-S-7 | — |
| EE-S-6 | ★ NT-S-14 | T1 黄灯改写了 `source_integrity` → 失败 |
| EE-S-7 | ★ NT-S-15 | 代码 lint：statcheck 类实现缺少「从 APA 规格独立重写」的许可决定注释 → 失败 |
| EE-S-8 | NT-S-11 | — |
| EE-S-9 | ★ NT-S-16 | 对 `S` 做可达性分析：断言不存在从 T2 输出到任何降级的路径 |
| EE-S-10 | NT-S-5 | — |
| EE-S-11 | ★ NT-S-17 | 一次扇出运行中，抓取日志里对 RW / PPS / Hijacked 域名的请求计数 = 0 |
| EE-S-12 | NT-S-12 | — |
| EE-C-1 | NT-C-1 / NT-C-2 | — |
| EE-C-2 | NT-C-3 | — |
| EE-C-3 | NT-C-4 | — |
| EE-C-4 | NT-C-5 | — |
| EE-C-5 | NT-C-6 | — |
| EE-C-6 | ★ NT-C-9 | 文档 lint：对外文案出现「图表数值已核验」或高于 ~90% 的准确率承诺 → 失败 |
| EE-C-7 | NT-C-8 | — |
| EE-F-1 | NT-F-1 | — |
| EE-F-2 | NT-F-2 | — |
| EE-F-3 | NT-F-3 | — |
| EE-F-4 | NT-F-4 | — |
| EE-F-5 | NT-F-5 | — |
| EE-F-6 | ★ NT-F-8 | 一条证据的 `tool/call` callId 在 `runs/<run_id>/manifest.json` 中查无此事 → `not_covered`（01-CONTRACTS V4.6） |
| EE-F-7 | NT-F-6 | — |
| EE-F-8 | NT-F-7 | — |
| EE-A-1 | NT-A-1 | — |
| EE-A-2 | NT-A-2 | — |
| EE-A-3 | NT-A-1 | — |
| EE-A-4 | ★ NT-A-10 | 代码 lint：admission 实现中出现模型调用或网络调用 → 失败 |
| EE-A-5 | NT-A-6 | — |
| EE-A-6 | ★ NT-A-11 | 一条以 URL 为 `evidence_id` 组成部分的记录 → schema 校验失败 |
| EE-A-7 | NT-A-7 | — |
| EE-NT-1 | 自指 | 由本节的 lint 脚本本身覆盖；该脚本必须先在一个**故意删掉一行**的副本上红过一次（M-1） |

> **编号唯一性也是一条门**：CI 必须断言全文 `NT-*` id 无重复（§9.6 的通道分离两条已编为 **NT-P-1 / NT-P-2**，与 admission 的 NT-A-* 分开）。重复 id 会让「某用例通过」这句话失去所指——**这正是「自由文本台账会腐」的一个微型实例**（01-CONTRACTS §8.4 D-8.13）。

---

## §10 本引擎的能力边界：逐条对齐 00-PREMISE B5 的「不防的八类」

> **纪律**：下表的「我们做什么」全部是**减损**，不是解决。任何把减损写成解决的措辞都是回归。
> **并且**：00-PREMISE B5 的诚实标注同样适用于本表——**这些减损全部是设计论证，不是对我们架构的实测**。RT-1…RT-14 跑完之前按「未验证设计假设」对待 [E: ext-security-injection.md#未决11]。

| # | 攻击类 | 本引擎做的减损 | **明确不解决什么** | 残余风险的可观测指标 |
|---|---|---|---|---|
| **N1** | **内容攻击**（页面是真的、引语逐字命中、快照可复核，但内容本身是假的）。EMNLP 2025 逐字："Existing defenses, which focus on detecting hidden commands, are ineffective against attacks by content." | ①独立簇计数（§8.4 + 01-CONTRACTS §5.5）；②强制反证检索（F-29）；③L2 的跨厂商判定与分歧率升级 | **内容真伪本身不可判。**一条被 5 个真正独立的簇一致陈述的假事实，本引擎会给 ST-A。这是 `claim_supported` 确定性不可判的直接后果（01-CONTRACTS §1.3） | 人裁抽检中「status ≥ ST-A 但人裁判错」的比例。按 01-CONTRACTS §9.29 的非对称计分，自信错误 −2 |
| **N2** | 检索层投毒（每问 5 条恶意文本 → 90% ASR；改进版每问 1 条即 85–98%）。**口径：这是已知目标问题的定向攻击，「5 条」是每问 5 条，不是 5 条污染整库** | ①`upstream_id` 归并使同源投毒只算 1 票；②检索饱和曲线记录（01-CONTRACTS §9.14，自建概念，需自证）；③非渲染通道分离切断 70% 的野外注入载体 | **不阻止投毒文档进入检索结果。**被引的每一句都真实存在于被投毒文档中，逐字匹配 100% 通过 | 每次任务的「名义来源数 / 独立簇数」比值分布；比值接近 1 是健康信号，远大于 1 说明大量假独立佐证 |
| **N3** | 伪造权威 / 合成共识（Gemini-3-Flash 上 73% ASR；同框架下 Claude-Sonnet-4.6 为 0.0%——**后端间差异极大**） | `K(kind) ≥ 2` 的独立簇门槛（01-CONTRACTS §1.5.2）+ 已知硬样本作固定回归用例（11 中文域名 = 1 条日经；8 域名 = 1 篇 BadRAG；Unpaywall = OpenAlex 同一后端） | **归并器本身的假合并/漏合并率未知。**若归并器把 5 个真独立源误并为 1，我们会过度降级；若漏并，`K=2` 事实上等价于 `K=1`（01-CONTRACTS §10.3） | 在固定回归用例上的归并正确率；RT-2 / RT-3 的通过率 |
| **N4** | UGC 投毒（~13 词、单个 URL，曝光条件下 38–51% 提及率；困惑度检测 AUROC ≤0.68 **且方向反了**） | F-15：UGC 域默认不得作为承重证据。成本依据：屏蔽 UGC 的质量代价极小（rubric 4.30→4.26，每查询只移除 2.1 个 UGC URL）；且 UGC 引用率可设计（0.4% vs 12.1%，差 30 倍） | **不检测投毒本身。**F-17 只告警不判定——真实注入 >90% 不含显式指令。**且我们采信的是该论文的数据而非其结论语气；若我们读错了其 rubric 指标含义，F-15 的成本估计会失真** [E: ext-security-injection.md#未决13] | F-15 命中率；被 F-15 挡下的证据中经人审判为「本应采用」的比例 |
| **N5** | 输入侧 / claim 侧攻击（input-only 对三套搜索增强事实核查系统 ASR 18.8%–31.4%） | F-13 措辞扰动一致性（§3.4.5，N=5 同义改写独立走链） | **分解步骤本身仍由已读过上游不可信文本的 LLM 生成。**这是 00-PREMISE 明确点名的「目前完全没设防的攻击面」——F-13 是检测，不是隔离 | F-13 命中率；RT-7 的判定翻转率 |
| **N6** | 选择性引用（注入不改引语真伪，只改「引哪一句」；逐字匹配必然全绿） | F-29 强制反证检索 + 记录搜索过程与预算；反证必须在**同一快照内**搜（RT-8） | **无法判定「这一句是不是最相关的那一句」。**反证检索只能发现同一快照内的反对句，发现不了「作者在别处限定了该结论」 | RT-8 通过率；`counter_evidence_found` 的整体比例（长期为 0 是可疑信号，不是健康信号） |
| **N7** | 数据层投毒（可重跑保证可复现，不保证正确） | ①输入 sha256 冻结使**替换**可检测；②G-DEP 使**硬编码**可检测；③ST-V 在 K-D 上的语义边界必须随判定一起说出（01-CONTRACTS §2.1） | **数据本身被投毒时，重跑一万次结果都一样地错。**G-DEP 检的是「输出依赖输入」，不是「输入正确」 | 数据来源的 `evidence_grade` 与 `upstream_id` 分布；来源分级为 unknown 的 K-D claim 占比 |
| **N8** | 静默语义漂移（即使 ASR 判为「失败」，复合层攻击仍有 **15.0%** 的输出语义漂移 Δ≥0.3） | 六值状态枚举（含 `contested` 与 `not_covered`）而非二元（01-CONTRACTS §1.4.2） | **六值仍是离散的。**我们没有连续的 `evidence_strength` 量；一个漂移 Δ=0.29 的输出与 Δ=0.0 的输出在状态上无差别 | 无直接指标。**这是本引擎最弱的一条**——见 §11.4 |

〔依据 00-PREMISE B5 不防的八类；ext-security-injection.md#一, #V1-V3, #V5-V10, #V14, #V15, #V16, #V22, #V22b, #V26, #C1, #D8〕[E: https://arxiv.org/abs/2510.11238]

**关于「被结构性消灭的四类」（S1–S4）**：本文件不重复 00-PREMISE 的论证。**只补一句门侧的落点**：S1（引语伪造）与 S2（子代理改判定）在本文件里的兑现物分别是 §3.3 的 G-L1 与 EE-0.5 + 01-CONTRACTS §4；S3（原地替换）是 NT-L-14；S4（跨子代理传播）是 §4.4.1 的结构化载荷 + `spawn`。**这四条同样是论证，不是实测。**

---

## §11 本文件自身的已知薄弱处（供攻击者优先瞄准）

**11.1 § 2.4 的 G-DEP 从未运行过。** 它是本文件里最重要的新增门（没有它 G-RERUN 是一个几乎不会红的检查），但它的假阳率、假阴率、成本全部是推演。特别是 C-1 的扰动幅度 `δ = 1e-2` 是一个凭空取的常数——太小会漏掉真实依赖，太大会让合法脚本崩溃。**这个常数必须在自建回归集上标定，标定前 G-DEP 的 `power_basis` 应记为 `unmeasured` 而不是 `construction`。**

**11.2 §3.3 的 L1 是本项目的差异化卖点，而它的精度是公开空白。** 语料明确记录逐字引文匹配没有任何公开的端到端精度测量 [E: ext-verification-mechanisms.md#未决2]。我把它读成「机会」，但同一语料也写了「也可能意味着我们低估了难度」[E: ext-citation-faithfulness.md#R9]。**在 §3.3.4 的标定完成之前，把 L1 当成差异点是一个未验证的商业假设。**

**11.3 §4.3.2 的信号问题表是我造的。** 语料给了形状（RoB 2）与它的量化支持（83.2% vs 65.2%），但没有给学术论证的题库。这五组题**没有任何实证支持**，它们可能既不「近乎事实性」也不覆盖真实的推断失效模式。§4.3.2 已写明推翻条件。

**11.4 §10 的 N8（静默漂移）没有真正的减损。** 00-PREMISE B4 的裁决里保留了一个连续量 `evidence_strength`，而 01-CONTRACTS 的六值枚举里没有它——`claim_supported` 是核算记录，含 `evidence_grade` 与 `independent_cluster_count` 两个离散量，但没有连续强度。**本文件也没有引入。** 这意味着 15.0% 的静默漂移在我们的状态空间里同样不可见。这是一个真实的、已知的、未被处理的缺口。

**11.5 §6 的图表门依赖一个模型路由器。** §6.3 用非对称约束把路由器的危险方向堵住了，但这条约束本身假设「分类器判黑名单是保守的」。若分类器把 bar 图误判为 radar，我们只是损失覆盖率；若它把 radar 判为 bar 而 k-of-n 三次都同意，我们会给一个 28.01% Adaptive MAPE 的读数盖上 ±8% 的 ε。**k=2/n=3 是裁定，没有实测支持。**

**11.6 §8.2 发现的 `evidence_id` 三元组 vs 五元组冲突未解决。** 本文件按 01-CONTRACTS 实现，但同时指出它会在同一 work 的多版本上产生键碰撞。**在 01-CONTRACTS 修改之前，多版本文献的证据可能被静默覆盖。** 这是一条真实的数据丢失路径。

**11.7 §5 的 T0 在中文路径上基本失效。** RW 库以英文文献为主，PPS 依赖 Dimensions 索引，Hijacked 列表以国际刊为主。**若覆盖中文文献，`not_covered` 会成为多数状态** [E: ext-literature-integrity.md#未决8]。§5 没有给出任何中文侧的替代数据源——因为语料里没有。

**11.8 本文件引用的全部 prevalence 与模型分数在 6 个月内会过期。** 野外注入普查基于 2025-10 的 Common Crawl 快照；引用幻觉率是 2026-04 快照；RW 全库数是 2026-08-17 实测（快照 generated 2026-08-14）；judge 分数绑定具体模型版本。**凡引用本文件的数字必须连日期一起引用。**

**11.9 §2.3 的禁网方案依赖容器可用性，而这是一个部署前提，不是代码。** 若部署环境不装容器运行时，全部 K-D claim 落 ST-N。**这在工程上是正确的 fail-closed，在产品上是一个可能让整条数据通道失效的单点。**

---

**文件版本**：v2-draft-1｜**撰写日期**：2026-08-17｜**规范源**：`01-CONTRACTS.md`（全部术语）｜**前提源**：`00-PREMISE.md`（B1 / B2 / B4 / B5 / B8 为 binding）｜**证据基线**：`research/v2/`（23 文件，全部产出于 2026-08-17）｜**DSH 运行时事实以 `research/v2/GROUND-TRUTH-CORRECTIONS.md` 为准**
