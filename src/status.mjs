// 状态函数 S —— 01-CONTRACTS.md §1.5 的可执行实现
//
// 这是本项目最承重的一段代码：它是**唯一**把证据核算记录变成 status 的地方。
// 契约要求它是**纯函数**（V1.2：重跑必须得到与存档逐字节相同的值）
// 且是**全函数**（V1.7：完整输入向量空间内每一格都有唯一返回值）。
//
// 实现纪律：
//   1. 逐条对应 §1.5 的步骤编号，不重排、不合并、不"优化"。
//      规范里步骤的**顺序本身是契约**——2d 在 2d′ 之前不是随意的。
//   2. 不读文件、不看时钟、不调模型、不联网。所有输入由调用方备齐。
//   3. 任何"这里规范没说清"的地方，抛 ContractGap 而不是猜。
//      猜出来的默认值会变成一条没人知道存在的规则。

// ── 格结构（§1.5.1.1） ─────────────────────────────────────────────────
//
//         ST-V
//        /    \
//    ST-A      ST-E        ← 同层，互不可比
//        \    /
//         ST-U
//
// ST-C / ST-N 是吸收态，在第 0 步或 2a 已返回，不参与格运算。
export const ST = Object.freeze({
  V: 'verified',
  A: 'attributed',
  E: 'estimated',
  C: 'contested',
  U: 'unverified',
  N: 'not_covered',
})

const LATTICE = [ST.V, ST.A, ST.E, ST.U]
const RANK = { [ST.V]: 3, [ST.A]: 2, [ST.E]: 2, [ST.U]: 1 }

export class ContractGap extends Error {
  constructor(where, detail) {
    super(`契约缺口 @ ${where}: ${detail}`)
    this.name = 'ContractGap'
    this.where = where
  }
}

/** §1.5.1.1 降一档。下界饱和——ST-U 再降还是 ST-U。 */
export function stepDown(x) {
  // §1.5.1.1〔R3/C-1b 修复〕吸收态在 `降一档` 下也必须有定义，而且这条**可达**：
  // G1/G0 证据在 2c 把 base 压成 ST-N 之后，2d′ 的 step-down flag 会对它调用本函数。
  // 移除 2c 里那行提前返回补丁后，穷举 oracle 立刻在 {G1, [F-01]} 上抛
  // 「not_covered 不在格内」——补丁一直在掩盖全函数论证的这个缺口。
  if (x === ST.N || x === ST.C) return x
  switch (x) {
    case ST.V: return ST.A
    case ST.A: return ST.U
    case ST.E: return ST.U
    case ST.U: return ST.U
    default: throw new ContractGap('stepDown', `${x} 不在格 {V,A,E,U} 内`)
  }
}

/**
 * §1.5.1.1 meet —— 格上的下确界。
 * 关键一条：meet(ST-A, ST-E) = ST-U。
 * 两个同层不可比元素的下确界只能是它们共同的下界。语义上也对：
 * 证据等级只撑得起"归因"、同时数值又来自图形几何读数，
 * 那么既没有干净的归因、也没有干净的估计——诚实的答案就是 unverified。
 */
export function meet(x, y) {
  // §1.5.1.1〔R3/C-1b 修复〕吸收态必须在 meet 下有定义。
  // 规范原本写「ST-C / ST-N 是吸收态，在第 0 步/2a 已返回，不参与」，
  // 但 §3.4 给 G0 的上限就是 ST-N，而 2c 要求 `meet(base, 两个上限)`
  // ——那是 ST-N 的第三个入口，既不在第 0 步也不在 2a。
  // 原实现在 2c 里用一行契约里没有的补丁 `if (g === ST.N) return …` 绕过，
  // 于是「S 是全函数」证明的是实现自洽而非规范完备。现按补齐后的 §1.5.1.1 逐点实现。
  if (x === ST.N || y === ST.N) return ST.N
  if (x === ST.C || y === ST.C) return ST.C
  if (!LATTICE.includes(x)) throw new ContractGap('meet', `左操作数 ${x} 不在格内`)
  if (!LATTICE.includes(y)) throw new ContractGap('meet', `右操作数 ${y} 不在格内`)
  if (x === y) return x
  if (x === ST.V) return y
  if (y === ST.V) return x
  if (x === ST.U || y === ST.U) return ST.U
  return ST.U // {A, E} 的两种混合序，下确界都是 U
}

const meetAll = (...xs) => xs.reduce(meet)

// ── §1.5.2 K(kind) ──────────────────────────────────────────────────────
// 数据推导的独立性由**重跑**保证，不由多源保证 → K=1
// 转录只需要一个真实锚点 → K=1
// 归因与推断必须扛住"合成共识"，最低防线是两个独立簇 → K=2
export const K = Object.freeze({
  'K-D': 1,
  'K-L-T': 1,
  'K-L-A': 2,
  'K-I': 2,
})

// ── §3.4 evidence_grade → 状态上限 ──────────────────────────────────────
// G2/G3 在契约里还带**断言类型**限制（G3 仅限"关于摘要内容本身"，G2 仅存在性、
// 不得支撑数值断言）。那两条是**门**的职责，不是 S 的——S 只消费等级给出的状态上界。
// 这个分工写在这里，免得后来的人以为 S 漏检了。
const GRADE_CEILING = Object.freeze({
  G5: ST.V,
  G4: ST.A,
  G3: ST.A,
  G2: ST.A,
  G1: ST.N, // 不得作为任何 claim 的承重证据 → 本项目的证据标准没覆盖它
  G0: ST.N,
})

// ── §8.6.2 retention_tier → 状态上限 ────────────────────────────────────
// Tier C 的真实作用是把 evidence_grade 压到 ≤ G2，因而它对状态的影响**已经**
// 经由 GRADE_CEILING 体现。这里保留一层独立上界只是为了让 2c 的两个上限都显式存在——
// 若将来 tier 有了不经由 grade 的直接影响，改这里而不是改 2c 的结构。
const TIER_CEILING = Object.freeze({
  A: ST.V,
  B: ST.V,
  C: ST.A,
})

// ── §7.3 flag 作用表 ────────────────────────────────────────────────────
// 只列**进入 S 的判定**的那些。§7.3.1 里"已在第 0 步/2a/第 1 步返回"的 flag
// 不在此表——它们若也进 2d/2d′ 就是重复计算（R1/C-1 打穿的正是这一类）。
const FLAG_CEILING = Object.freeze({
  'F-13': ST.U, // unstable-decomposition
  'F-12': ST.U, // metric-frame-mismatch
  'F-03': ST.A, // cherry-picking:window
  'F-04': ST.A, // best-case-ratio
})

const FLAG_STEPDOWN = Object.freeze(new Set([
  'F-01', // uncertainty:no-ci
  'F-02', // secondhand
  'F-09', // preprint-only
  'F-15', // ugc-source
  'F-24', // pricing-promo
  'F-25', // as-of-stale
]))

/**
 * 状态函数 S。
 *
 * @param {object} c 证据核算记录（§1.3 的字段 + kind + 三个正交谓词）
 * @returns {{status: string, trace: string[]}} status 与逐步判定轨迹
 *
 * trace 不是日志——它是**审计工件**。V1.2 要求重跑得到逐字节相同的结果，
 * 而当两次结果不同时，人需要能立刻看出是在哪一步分岔的。
 */
export function S(c) {
  const trace = []
  const ret = (step, status) => {
    trace.push(`${step} → ${status}`)
    return { status, trace }
  }

  // ── 第 0 步之前 · 必填字段 fail-closed ──────────────────────────────
  // §1.3：「必填字段（缺任一 → 该 claim 直接 not_covered）」
  // §9.19：「fail-open 是禁止的；MISSING == FAIL」
  //
  // 〔R3/P1-3 修复〕原实现只对 5 个字段抛，其余静默走通。最要命的是
  // `counter_evidence_searched`：0e 写成 `=== false`，所以**字段缺失时不触发**，
  // 而 §7.2.3 恰恰称它是「逃不过的只有这一条」——它是最容易漏掉的那一个。
  // 实测：省略该字段的 K-L-T 向量返回 verified。
  // 穷举 oracle 抓不到，因为它只枚举 true/false，从不枚举「字段缺失」。
  const REQUIRED = [
    'evidence_grade', 'independent_cluster_count', 'counter_evidence_searched',
    'counter_evidence_found', 'mechanism_results', 'flags', 'budget_state',
    'source_integrity', 'kind', 'retention_tier',
  ]
  const missing = REQUIRED.filter(k => c[k] === undefined || c[k] === null)
  if (missing.length) {
    trace.push(`必填字段缺失: ${missing.join(', ')}`)
    return ret('0-required', ST.N)
  }

  // 值域校验也是 fail-closed 的一部分：`quote_faithful: 'PASS'`（大小写错）
  // 原本会静默绕过 0d。取值域外即视为「程序没跑完」。
  if (c.quote_faithful !== undefined && !['pass', 'fail', 'na'].includes(c.quote_faithful)) {
    trace.push(`quote_faithful 取值域外: ${JSON.stringify(c.quote_faithful)}`)
    return ret('0-domain', ST.N)
  }
  if (!['ok', 'degraded', 'exhausted'].includes(c.budget_state)) {
    trace.push(`budget_state 取值域外: ${JSON.stringify(c.budget_state)}`)
    return ret('0-domain', ST.N)
  }

  // ── 第 0 步 · 前置否决（任一命中，立即返回） ────────────────────────
  const si = c.source_integrity

  if (si === 'mutated' || si === 'missing') return ret('0a', ST.U)
  if (si === 'contaminated') return ret('0b', ST.C)
  if (si === 'not_covered') return ret('0c', ST.N)

  // §1.2.1.1 `na` 只对 K-I 合法（它的输入是别的 claim，没有抓取事件）。
  // 其余 kind 取 na 是 V1.8 失败，不是 S 该容忍的输入。
  if (si === 'na' && c.kind !== 'K-I') {
    throw new ContractGap('0', `source_integrity=na 只允许 kind=K-I，本条是 ${c.kind}（V1.8）`)
  }
  if (si !== 'intact' && si !== 'na') {
    throw new ContractGap('0', `source_integrity 取值 ${JSON.stringify(si)} 不在值域内`)
  }

  // ── §7.3.1 flag ↔ 驱动字段 一致性（fail-closed） ──────────────────
  // 〔R4/R4-03 修复，实测扩为 15 条〕R4 报的是一个实例（F-10 与 chart_extracted 无绑定），
  // 实测发现它是**整族**：§7.3.1 的每个 flag 都能在驱动字段说「不」的情况下置位，
  // 而 S 照样返回 verified —— F-29/F-28/F-31/F-05/F-16/F-11 逐条实测均如此。
  //
  // 根因：这些 flag 在设计上是**输出标注**（门判定后贴的标签），但 schema 允许它们
  // 作为**输入**出现。规范用 flag 做主语（「每条含 F-29 的 claim……」），
  // 实现用驱动字段做条件——**主语和条件是两套词汇，中间没有桥**。
  // V7.2 之类以 flag 为主语的断言因此全部落空。
  //
  // 修法不是给 F-10 打特例，是把 §7.3.1 那张表本身变成可执行约束：
  // flag 置位 ⟹ 其驱动条件必须成立。不成立 = 贴标签的门与写字段的门不一致
  // = 程序没跑完 ⇒ 按 §9.19「MISSING == FAIL」判 ST-N。
  const FLAG_DRIVER = {
    'F-05': x => x.source_integrity === 'contaminated',
    'F-06': x => x.source_integrity === 'contaminated',
    'F-07': x => x.source_integrity === 'contaminated',
    'F-16': x => x.source_integrity === 'mutated' || x.source_integrity === 'missing',
    'F-27': x => x.source_integrity === 'mutated' || x.source_integrity === 'missing',
    'F-18': x => x.source_integrity === 'not_covered',
    'F-21': x => x.source_integrity === 'not_covered',
    'F-30': x => x.source_integrity === 'not_covered',
    'F-32': x => x.source_integrity === 'not_covered',
    'F-33': x => x.source_integrity === 'not_covered',
    'F-28': x => x.has_verbatim_quote === true && x.quote_faithful === 'fail',
    'F-29': x => x.counter_evidence_searched === false,
    'F-11': x => x.budget_state === 'exhausted' || x.budget_state === 'degraded',
    'F-31': x => x.counter_evidence_found === true,
    // 〔R5 后实测〕本行被下面的 §7.2.4 双向绑定**完全覆盖**：删掉它门仍判红。
    // 因此驱动表逐行删除的诚实数字是 **17 行被钉住 + 1 行冗余**，不是 18/18。
    // 保留它是为了让这张表与 §7.3.1 逐行对齐（表的完整性本身是可读性资产），
    // 但不得把它计入「被负例钉住的规则数」。
    'F-10': x => x.chart_extracted === true,
    'F-14': x => x.independent_cluster_count === 1,
    // 〔R5-03 修复〕规则句是**全称**的（「§7.3.1 的每一个 flag」），但表只抄了 §7.3.1，
    // 漏掉 §7.3 主表里同样有真实状态通路的两条：
    'F-34': x => x.retention_tier === 'C',            // §7.3 indirect：压 evidence_grade ≤ G2
    'F-28a': x => Array.isArray(x.flags) && x.flags.includes('F-28'), // §7.3：F-28 已置位是它的前提
  }
  if (Array.isArray(c.flags)) {
    for (const f of c.flags) {
      const driver = FLAG_DRIVER[f]
      if (driver && !driver(c)) {
        trace.push(`flag ${f} 已置位，但 §7.3.1 规定的驱动条件不成立`)
        return ret('0-flag-driver', ST.N)
      }
    }
  }

  // §7.2.4〔R4/R4-03 修复〕F-10 与 chart_extracted 必须同真同假。
  // V7.2 / §7.3.1 的主语是「含 F-10 的 claim」，而第 1 步读的是 chart_extracted——
  // 两者此前无任何绑定，`flags:['F-10'], chart_extracted:false` 直接返回 verified。
  // 不一致 = 抽取工具没把两处都写完 ⇒ 按 §9.19 fail-closed。
  if (Array.isArray(c.flags) && c.flags.includes('F-10') !== (c.chart_extracted === true)) {
    trace.push(`F-10 与 chart_extracted 不一致: flags=${JSON.stringify(c.flags)} chart_extracted=${c.chart_extracted}`)
    return ret('0-domain', ST.N)
  }

  if (c.has_verbatim_quote && c.quote_faithful === 'fail') return ret('0d', ST.U)
  if (c.counter_evidence_searched === false) return ret('0e', ST.N)
  if (c.budget_state === 'exhausted') return ret('0f', ST.N)
  if (!Array.isArray(c.mechanism_results) || c.mechanism_results.length === 0) return ret('0g', ST.N)

  // ── 第 1 步 · 按 kind 取 base ────────────────────────────────────────
  let effectiveKind = c.kind
  let base
  switch (c.kind) {
    case 'K-D':
      // 封闭式 / 开放式不是自报字段，是三条硬条件（§1.5 R1/C-9 后收紧）。
      // 调用方必须把三条的**合取结果**放进 question_frozen。
      if (c.question_frozen === undefined) {
        throw new ContractGap('1/K-D', 'question_frozen 缺失——封闭式判据是三条硬条件的合取，不能省')
      }
      base = c.rerun_gate_passed
        ? (c.question_frozen ? ST.V : ST.A) // 开放式端到端永不可达 ST-V（§2.1）
        : ST.U
      break

    case 'K-L-T':
      // §1.5：锚点包含检验不过 → **降为 K-L-A 处理**（不是判 ST-U）
      //
      // 〔R3/P1-4 修复〕「降为 K-L-A 处理」必须改**有效 kind**，不能只改 base。
      // 原实现只改 base，于是 2b 仍用 K('K-L-T')=1 而不是 K('K-L-A')=2，
      // 造出一条洗白通道：同样的证据，声明成 K-L-T 再让锚点检验失败（→ attributed），
      // 比诚实声明成 K-L-A（→ unverified）拿到**更高**的 status。
      // 实测复现：两条只差 kind 的向量，(a) attributed / (b) unverified。
      // §2.2.1 / §1.5〔R4/R4-02 修复〕K-L-T 是**两个合取项**：
      // 包含检验 ∧ 极性作用域检验（L1-c）。载荷是源句 token 的真子集时，
      // 它可以断言源句所否定的东西（「该方法**并未**达到 92% 的准确率」→ 载荷取「92% 的准确率」），
      // 旧判据下 base = ST-V。R3 那一轮只改了 §2.2.1 的散文，
      // 没改自称「唯一的计算式」的 §1.5，也没进实现——规范与实现分叉了整整一轮。
      if (c.polarity_scope_passed === undefined) {
        throw new ContractGap('1/K-L-T', 'polarity_scope_passed 缺失——K-L-T 是两个合取项，不能省（§2.2.1）')
      }
      if (c.anchor_containment_passed && c.polarity_scope_passed) {
        base = ST.V
      } else {
        effectiveKind = 'K-L-A'
        base = c.attribution_verdict === 'support' ? ST.A : ST.U
        trace.push(`1 K-L-T 合取项未全过（包含=${c.anchor_containment_passed} 极性=${c.polarity_scope_passed}）→ 降为 K-L-A（K=2）`)
      }
      break

    case 'K-L-A':
      base = c.attribution_verdict === 'support' ? ST.A : ST.U
      break

    case 'K-I':
      base = c.inference_gate_passed ? ST.A : ST.U // K-I 永不可达 ST-V（§2.3.1）
      break

    default:
      throw new ContractGap('1', `kind ${JSON.stringify(c.kind)} 不在 §2 的封闭枚举内`)
  }
  trace.push(`1 kind=${c.kind} → ${base}`)

  // §6.1 + V1.4 · 决定性机制含 GC-2 → 上限 ST-A
  //
  // 〔R3/P1-2 修复，本轮最重的一条〕原实现**从不读 mechanism_results 的内容**，只判非空。
  // 于是「GC-2 永远不得写 ST-V」——被 §6.1 表、§6.4、V1.4、V6.2 四处规范化、
  // 被两份下游文档当作唯一依据的规则——在唯一的可执行规范里**没有任何载体**。
  // 实测：一条机制全为 GC-2 的 K-L-T claim 直接返回 verified。
  //
  // 更糟的是穷举 oracle 看不见它：向量生成器把 gate_class 硬编码成 'GC-0'，
  // 只让 mechanism_results 的**长度**变化。550 万向量全绿与这条产品最承重的
  // 分界线完全无关。这是本轮对「穷举即覆盖」这个直觉最有力的反例——
  // **枚举的是维度，不是空间；没进枚举的维度，穷举再多也照不亮。**
  if (c.mechanism_results.some(m => m?.gate_class === 'GC-2')) {
    base = meet(base, ST.A)
    trace.push(`1 mechanism_results 含 GC-2 → meet(base, ST-A) = ${base}`)
  }

  // §3.5 图形几何读数强制 ST-E，覆盖上述结果
  if (c.chart_extracted) {
    base = ST.E
    trace.push(`1 chart_extracted → ${base}`)
  }

  // ── 第 2 步 · 单调降级 ──────────────────────────────────────────────
  // 2a 吸收态，覆盖任何 base
  if (c.counter_evidence_found === true) return ret('2a', ST.C)

  // 2b 独立簇数不足 —— **唯一**判定独立性是否足够的地方。
  // F-14 single-cluster 在这里**不参与**（R1/C-1：它被 2b 与 2d 消费两遍，
  // 而 K(K-D)=K(K-L-T)=1 意味着单簇是正常态，2d 必降会让 ST-V 全局不可达）。
  const kNeeded = K[effectiveKind]
  if (kNeeded === undefined) throw new ContractGap('2b', `K(${effectiveKind}) 未定义`)
  if (typeof c.independent_cluster_count !== 'number') {
    throw new ContractGap('2b', 'independent_cluster_count 缺失或非数值')
  }
  if (c.independent_cluster_count < kNeeded) {
    base = stepDown(base)
    trace.push(`2b cluster ${c.independent_cluster_count} < K(${effectiveKind})=${kNeeded} → ${base}`)
  }

  // 2c 证据等级上限 + 留存分档上限
  const g = GRADE_CEILING[c.evidence_grade]
  if (g === undefined) throw new ContractGap('2c', `evidence_grade ${JSON.stringify(c.evidence_grade)} 不在 G0..G5 内`)
  const t = TIER_CEILING[c.retention_tier]
  if (t === undefined) throw new ContractGap('2c', `retention_tier ${JSON.stringify(c.retention_tier)} 不在 A/B/C 内`)

  // G1/G0 的上限是 ST-N —— 吸收态，不能喂给 meet（meet 只定义在 {V,A,E,U} 上）。
  // 语义：本项目的证据标准根本没覆盖这条 claim，而不是"覆盖了但没通过"。
  // 〔R3/C-1b 修复〕此处原有一行契约里没有的提前返回补丁，现已由 meet 的
  // 吸收态定义承接（§1.5.1.1），走正常的 meet 路径，不再特判。

  base = meetAll(base, g, t)
  trace.push(`2c meet(grade=${g}, tier=${t}) → ${base}`)

  // 2d ceiling 类 flag
  const flags = Array.isArray(c.flags) ? c.flags : []
  const ceilings = flags.map(f => FLAG_CEILING[f]).filter(Boolean)
  if (ceilings.length) {
    base = meetAll(base, ...ceilings)
    trace.push(`2d ceilings ${flags.filter(f => FLAG_CEILING[f]).join(',')} → ${base}`)
  }

  // 2d′ step-down 类 flag —— 每命中一条降一档，**叠加**。
  // 叠加而非"命中任意一条降一档"，是为了关掉"已经有一个缺陷了，多几个免费"这个博弈面。
  const downs = flags.filter(f => FLAG_STEPDOWN.has(f))
  for (const f of downs) {
    base = stepDown(base)
    trace.push(`2d′ ${f} → ${base}`)
  }

  // 2e 预算降级
  if (c.budget_state === 'degraded') {
    base = stepDown(base)
    trace.push(`2e budget=degraded → ${base}`)
  }

  trace.push(`返回 ${base}`)
  return { status: base, trace }
}

export default S


// 导出给 gates/check_status_spec.mjs 与 §7.3 作用表做双向绑定比对。
// 〔R3 修复〕此前没有任何门读过 §7.3 的作用类型列与值列。
export const FLAG_CEILING_EXPORT = FLAG_CEILING
export const FLAG_STEPDOWN_EXPORT = FLAG_STEPDOWN

export const GRADE_CEILING_EXPORT = GRADE_CEILING
export const K_EXPORT = K
export const TIER_CEILING_EXPORT = TIER_CEILING
