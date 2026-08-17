#!/usr/bin/env node
// 状态函数 S 的穷举 oracle（loop 的 S1 阶段验收，GC-0）
//
// 01-CONTRACTS V1.7 要求：穷举 S 的输入向量空间，断言每个向量都得到唯一返回值
// 且落在六值枚举内——即 S 是**全函数**。
//
// 为什么必须是穷举而不是抽样：这个函数的缺陷形态是「某个**组合**下无定义」。
// R1 实测到的那条——「图形读数（base=ST-E）+ G4 证据（上限=ST-A）」下 min() 无定义——
// 两个维度单独看都正常，只有它们同时出现才塌。抽样测试正好会漏掉这类。
//
// 本门还带一条**回归测试**：C-1 那条被五个独立攻击者打穿的路径
// （K-D 封闭式 + 重跑通过 + G5 + 单簇）必须真的到达 ST-V。
// 这条是 loop 设计里给 S1 写的 passing_but_wrong 的解药——
// 一个 `return 'ST-N'` 的实现会让全函数/纯/单调三条全绿，只有值域覆盖能抓住它。
//
// 用法:  node gates/check_status_exhaustive.mjs [--full] [--enum|--monotone|--coverage]
// 退出码: 0 = 通过，1 = 有反例

import { S, ST, stepDown, meet, ContractGap } from '../src/status.mjs'

const FULL = process.argv.includes('--full')
const only = ['--enum', '--monotone', '--coverage'].find(f => process.argv.includes(f))

const ENUM_VALUES = new Set(Object.values(ST))

// ── 输入维度 ────────────────────────────────────────────────────────────
const D = {
  kind: ['K-D', 'K-L-T', 'K-L-A', 'K-I'],
  source_integrity: ['intact', 'mutated', 'missing', 'contaminated', 'not_covered', 'na'],
  // has_verbatim_quote × quote_faithful 的有意义组合（其余是同构的）
  quote: [
    { has_verbatim_quote: false, quote_faithful: 'na' },
    { has_verbatim_quote: true, quote_faithful: 'pass' },
    { has_verbatim_quote: true, quote_faithful: 'fail' },
  ],
  counter_evidence_searched: [true, false],
  counter_evidence_found: [true, false],
  budget_state: ['ok', 'degraded', 'exhausted'],
  // 〔R3/P1-2 修复〕原本这里只有 mechanism_empty: [false, true]，
  // 而向量生成器把 gate_class 硬编码成 'GC-0'。于是「GC-2 永不得写 ST-V」
  // ——被四处规范化、被两份下游文档当作唯一依据的那条规则——**从未被枚举到**。
  // 550 万向量全绿与产品最承重的分界线完全无关。
  // 教训：**枚举的是维度，不是空间；没进枚举的维度，穷举再多也照不亮。**
  mechanism: [
    { label: 'empty', value: [] },
    { label: 'gc0', value: [{ gate_class: 'GC-0', gate_id: 'x', verdict: 'pass' }] },
    { label: 'gc1', value: [{ gate_class: 'GC-1', gate_id: 'x', verdict: 'pass' }] },
    { label: 'gc2', value: [{ gate_class: 'GC-2', gate_id: 'x', verdict: 'support' }] },
    { label: 'gc0+gc2', value: [{ gate_class: 'GC-0', gate_id: 'a', verdict: 'pass' }, { gate_class: 'GC-2', gate_id: 'b', verdict: 'support' }] },
  ],
  evidence_grade: ['G5', 'G4', 'G3', 'G2', 'G1', 'G0'],
  retention_tier: ['A', 'B', 'C'],
  independent_cluster_count: [0, 1, 2, 3],
  chart_extracted: [false, true],
  // §7.3 幂集的代表元：空集、每个 ceiling 单独、每个 step-down 单独、
  // 以及会叠加的组合（叠加是 2d′ 的语义，必须被覆盖）
  flags: FULL
    ? [[], ['F-13'], ['F-12'], ['F-03'], ['F-04'], ['F-01'], ['F-02'], ['F-09'], ['F-15'], ['F-24'], ['F-25'],
       ['F-01', 'F-02'], ['F-09', 'F-15', 'F-25'], ['F-03', 'F-01'], ['F-13', 'F-09'],
       ['F-01', 'F-02', 'F-09', 'F-15', 'F-24', 'F-25'], ['F-14'], ['F-14', 'F-01']]
    : [[], ['F-13'], ['F-03'], ['F-01'], ['F-01', 'F-02'], ['F-09', 'F-15', 'F-25'], ['F-03', 'F-01'], ['F-14']],
}

// kind 专属输入。每个 kind 只枚举它自己会读的字段，避免把不相关维度乘进来。
const KIND_SPECIFIC = {
  'K-D': [
    { rerun_gate_passed: true, question_frozen: true },
    { rerun_gate_passed: true, question_frozen: false },
    { rerun_gate_passed: false, question_frozen: true },
    { rerun_gate_passed: false, question_frozen: false },
  ],
  'K-L-T': [
    { anchor_containment_passed: true, attribution_verdict: 'support' },
    { anchor_containment_passed: false, attribution_verdict: 'support' },
    { anchor_containment_passed: false, attribution_verdict: 'partial' },
    { anchor_containment_passed: false, attribution_verdict: 'not-support' },
  ],
  'K-L-A': [
    { attribution_verdict: 'support' },
    { attribution_verdict: 'partial' },
    { attribution_verdict: 'not-support' },
  ],
  'K-I': [{ inference_gate_passed: true }, { inference_gate_passed: false }],
}

// ── 枚举 ────────────────────────────────────────────────────────────────
function* vectors() {
  for (const kind of D.kind)
    for (const specific of KIND_SPECIFIC[kind])
      for (const source_integrity of D.source_integrity)
        for (const q of D.quote)
          for (const counter_evidence_searched of D.counter_evidence_searched)
            for (const counter_evidence_found of D.counter_evidence_found)
              for (const budget_state of D.budget_state)
                for (const mech of D.mechanism)
                  for (const evidence_grade of D.evidence_grade)
                    for (const retention_tier of D.retention_tier)
                      for (const independent_cluster_count of D.independent_cluster_count)
                        for (const chart_extracted of D.chart_extracted)
                          for (const flags of D.flags)
                            yield {
                              kind,
                              ...specific,
                              source_integrity,
                              ...q,
                              counter_evidence_searched,
                              counter_evidence_found,
                              budget_state,
                              mechanism_results: mech.value,
                              evidence_grade,
                              retention_tier,
                              independent_cluster_count,
                              chart_extracted,
                              flags,
                            }
}

// `source_integrity=na` 只对 K-I 合法（V1.8）。其余 kind 取 na 是**非法输入**，
// S 抛 ContractGap 是正确行为，不是缺陷——所以这类向量不计入全函数断言。
const isLegal = v => !(v.source_integrity === 'na' && v.kind !== 'K-I')

// ── 断言 ────────────────────────────────────────────────────────────────
const problems = []
const hit = new Set()
let n = 0
let illegal = 0

for (const v0 of vectors()) {
  const v = withAutoFlags(v0)
  if (!isLegal(v)) {
    illegal++
    // 非法输入必须**抛**，不能悄悄返回一个值
    let threw = false
    try { S(v) } catch (e) { threw = e instanceof ContractGap }
    if (!threw && problems.length < 20) {
      problems.push({ kind: 'V1.8', v, msg: 'source_integrity=na 用在非 K-I 上却没抛 ContractGap' })
    }
    continue
  }

  n++
  let r
  try {
    r = S(v)
  } catch (e) {
    if (problems.length < 20) problems.push({ kind: 'V1.7', v, msg: `合法输入却抛出：${e.message}` })
    continue
  }

  // V1.7 全函数
  if (r === undefined || r.status === undefined) {
    if (problems.length < 20) problems.push({ kind: 'V1.7', v, msg: '返回 undefined' })
    continue
  }
  // V1.1 值域
  if (!ENUM_VALUES.has(r.status)) {
    if (problems.length < 20) problems.push({ kind: 'V1.1', v, msg: `返回枚举外的值 ${r.status}` })
    continue
  }
  hit.add(r.status)

  // V1.2 纯函数——同一向量两次必须逐字节相同
  const r2 = S(v)
  if (r2.status !== r.status || r2.trace.join('|') !== r.trace.join('|')) {
    if (problems.length < 20) problems.push({ kind: 'V1.2', v, msg: `重跑结果不同：${r.status} vs ${r2.status}` })
  }
}

// V1.3 单调 —— 对格上每个元素做符号执行，断言 stepDown 与 meet 都不上升
const RANK = { [ST.V]: 3, [ST.A]: 2, [ST.E]: 2, [ST.U]: 1 }
for (const x of [ST.V, ST.A, ST.E, ST.U]) {
  if (RANK[stepDown(x)] > RANK[x]) problems.push({ kind: 'V1.3', v: { x }, msg: `stepDown(${x}) 上升了` })
  for (const y of [ST.V, ST.A, ST.E, ST.U]) {
    const m = meet(x, y)
    if (RANK[m] > RANK[x] || RANK[m] > RANK[y]) {
      problems.push({ kind: 'V1.3', v: { x, y }, msg: `meet(${x},${y})=${m} 高于某个操作数` })
    }
    // meet 的交换律——2c/2d 里多个上限的求值顺序不影响结果，这条是那句话的证明
    if (meet(y, x) !== m) problems.push({ kind: 'V1.3', v: { x, y }, msg: 'meet 不满足交换律' })
  }
}

// ── 自动置位的 flag ─────────────────────────────────────────────────────
// §7.2 里有些 flag 的 setter 是 GC-0，**条件满足就无条件置位**，不由人挑。
// 测试向量必须还原这一点，否则回归测试是空的。
//
// 这条是本 oracle 自己犯过的错：C-1 回归用例原本写 `flags: []`，
// 于是把 F-14 重新塞回 step-down 集合（即重新引入 C-1 缺陷）时，oracle 给了绿灯——
// 因为向量里根本没有 F-14，那条"牙齿"咬的是空气。
// red-first 抓到了它：三个红样本里只有这一个当时没能判红。
function withAutoFlags(v) {
  const auto = []
  if (v.independent_cluster_count === 1) auto.push('F-14') // §7.2 F-14: count==1 由 GC-0 置位
  if (v.chart_extracted) auto.push('F-10')                 // §7.2 F-10: 图形读数由抽取工具置位
  const flags = [...new Set([...(v.flags ?? []), ...auto])]
  return { ...v, flags }
}

// ── C-1 回归测试（本门的牙齿） ──────────────────────────────────────────
// 五个独立攻击者共识：F-14 被 2b 与 2d 消费两遍，导致 ST-V 全局不可达。
// 这条路径必须真的到达 verified，否则产品的绿灯是空的。
// 全部用例都过 withAutoFlags —— 单簇必然带 F-14，这正是缺陷的触发条件。
const BASE_OK = {
  source_integrity: 'intact', has_verbatim_quote: false, quote_faithful: 'na',
  counter_evidence_searched: true, counter_evidence_found: false, budget_state: 'ok',
  evidence_grade: 'G5', retention_tier: 'A', independent_cluster_count: 3,
  chart_extracted: false, flags: [],
}

// R3 fix-audit 的三条 P1 各配一个回归用例。它们全都能在旧实现上复现，
// 而旧的穷举 oracle 一个都抓不到——这正是「穷举全绿」需要被质疑的理由。
const R3_CASES = [
  {
    name: 'R3/P1-2 · 决定性机制含 GC-2 → 不得为 verified（§6.1 / V1.4）',
    v: { ...BASE_OK, kind: 'K-L-T', anchor_containment_passed: true, attribution_verdict: 'support',
         mechanism_results: [{ gate_class: 'GC-2', gate_id: 'G-L2', verdict: 'support' }] },
    want: ST.A,
  },
  {
    name: 'R3/P1-3 · 必填字段缺失 → not_covered（§1.3 / §9.19 fail-closed）',
    v: (() => { const v = { ...BASE_OK, kind: 'K-L-T', anchor_containment_passed: true,
                            attribution_verdict: 'support',
                            mechanism_results: [{ gate_class: 'GC-0', gate_id: 'x', verdict: 'pass' }] }
                delete v.counter_evidence_searched; return v })(),
    want: ST.N,
  },
  {
    name: 'R3/P1-3b · quote_faithful 取值域外（大小写错）→ not_covered',
    v: { ...BASE_OK, kind: 'K-L-T', anchor_containment_passed: true, attribution_verdict: 'support',
         has_verbatim_quote: true, quote_faithful: 'PASS',
         mechanism_results: [{ gate_class: 'GC-0', gate_id: 'x', verdict: 'pass' }] },
    want: ST.N,
  },
  {
    name: 'R3/P1-4 · K-L-T 锚点失败必须按 K-L-A 的 K=2 处理（堵洗白通道）',
    v: { ...BASE_OK, kind: 'K-L-T', anchor_containment_passed: false, attribution_verdict: 'support',
         independent_cluster_count: 1,
         mechanism_results: [{ gate_class: 'GC-0', gate_id: 'G-L1', verdict: 'pass' }] },
    want: ST.U,
  },
]

const C1_CASES = [
  {
    name: 'K-D 封闭式 + 重跑通过 + G5 + Tier A + 单簇 + 无 flag',
    v: {
      kind: 'K-D', rerun_gate_passed: true, question_frozen: true,
      source_integrity: 'intact', has_verbatim_quote: false, quote_faithful: 'na',
      counter_evidence_searched: true, counter_evidence_found: false,
      budget_state: 'ok', mechanism_results: [{ gate_class: 'GC-0', gate_id: 'G-RERUN', verdict: 'pass' }],
      evidence_grade: 'G5', retention_tier: 'A', independent_cluster_count: 1,
      chart_extracted: false, flags: [],
    },
    want: ST.V,
  },
  {
    name: 'K-L-T 转录 + 锚点包含通过 + G5 + 单簇（RT-1 的对象①）',
    v: {
      kind: 'K-L-T', anchor_containment_passed: true, attribution_verdict: 'support',
      source_integrity: 'intact', has_verbatim_quote: true, quote_faithful: 'pass',
      counter_evidence_searched: true, counter_evidence_found: false,
      budget_state: 'ok', mechanism_results: [{ gate_class: 'GC-0', gate_id: 'G-L1', verdict: 'pass' }],
      evidence_grade: 'G5', retention_tier: 'B', independent_cluster_count: 1,
      chart_extracted: false, flags: [],
    },
    want: ST.V,
  },
  {
    name: 'K-L-A 归因 + 单簇（RT-1 的对象②：单张伪造网页给不出第二簇）',
    v: {
      kind: 'K-L-A', attribution_verdict: 'support',
      source_integrity: 'intact', has_verbatim_quote: true, quote_faithful: 'pass',
      counter_evidence_searched: true, counter_evidence_found: false,
      budget_state: 'ok', mechanism_results: [{ gate_class: 'GC-2', gate_id: 'G-L2', verdict: 'support' }],
      evidence_grade: 'G5', retention_tier: 'B', independent_cluster_count: 1,
      chart_extracted: false, flags: [],
    },
    want: ST.U, // K(K-L-A)=2，单簇触发 2b：ST-A → ST-U
  },
  {
    name: '图形读数(ST-E) + G4 证据(上限 ST-A) —— 旧实现在此处无定义',
    v: {
      kind: 'K-D', rerun_gate_passed: true, question_frozen: true,
      source_integrity: 'intact', has_verbatim_quote: false, quote_faithful: 'na',
      counter_evidence_searched: true, counter_evidence_found: false,
      budget_state: 'ok', mechanism_results: [{ gate_class: 'GC-0', gate_id: 'x', verdict: 'pass' }],
      evidence_grade: 'G4', retention_tier: 'A', independent_cluster_count: 1,
      chart_extracted: true, flags: [],
    },
    want: ST.U, // meet(ST-E, ST-A) = ST-U
  },
]

const regressions = []
for (const c of [...C1_CASES, ...R3_CASES]) {
  let got
  const vec = withAutoFlags(c.v)
  try { got = S(vec).status } catch (e) { got = `抛出：${e.message}` }
  if (got !== c.want) regressions.push({ ...c, got })
}

// ── 报告 ────────────────────────────────────────────────────────────────
console.log('状态函数 S · 穷举 oracle\n')
console.log(`枚举 ${n.toLocaleString()} 个合法向量（另 ${illegal.toLocaleString()} 个非法向量断言抛出）`)
console.log(`  ${FULL ? '完整 flag 幂集代表元' : '默认 flag 代表元（--full 展开）'}`)
console.log(`  命中的状态值: ${[...hit].sort().join(', ')}\n`)

let failed = 0
const report = (id, desc, bad, fmt) => {
  const hits = problems.filter(p => p.kind === id)
  if (only && !only.includes(id.toLowerCase().replace('v', ''))) { /* 允许 --enum 等过滤，但默认全跑 */ }
  if (hits.length || bad) {
    failed++
    console.log(`FAIL  ${id.padEnd(6)} ${desc}`)
    for (const p of hits.slice(0, 5)) console.log(`      ${p.msg}\n        ${JSON.stringify(p.v)}`)
    if (fmt) fmt()
  } else {
    console.log(`PASS  ${id.padEnd(6)} ${desc}`)
  }
}

report('V1.7', 'S 对每个合法输入向量都有唯一返回值（全函数）')
report('V1.1', 'S 的返回值恒落在六值枚举内')
report('V1.2', 'S 是纯函数（同一向量重跑逐字节相同）')
report('V1.3', '格运算单调：stepDown 与 meet 都不上升，且 meet 可交换')
report('V1.8', '`source_integrity=na` 用在非 K-I 上必须抛 ContractGap')

// 值域覆盖 —— 抓 `return 'ST-N'` 这类退化实现
const missing = [...ENUM_VALUES].filter(s => !hit.has(s))
if (missing.length) {
  failed++
  console.log(`FAIL  覆盖   六个状态值每个都要被至少一个合法向量命中`)
  console.log(`      从未命中: ${missing.join(', ')} —— 退化实现（如恒返回同一个值）会让上面几条全绿`)
} else {
  console.log('PASS  覆盖   六个状态值全部可达')
}

// C-1 回归
if (regressions.length) {
  failed++
  console.log(`FAIL  回归   产品绿灯 + R3 回归（${regressions.length}/${C1_CASES.length + R3_CASES.length} 条不符）`)
  for (const r of regressions) console.log(`      ${r.name}\n        期望 ${r.want}，实得 ${r.got}`)
} else {
  console.log(`PASS  回归   产品绿灯 + R3 fix-audit 回归 ${C1_CASES.length + R3_CASES.length}/${C1_CASES.length + R3_CASES.length}`)
}

console.log(`\n${failed ? `${failed} 项失败` : '全部通过'}`)
process.exit(failed ? 1 : 0)
