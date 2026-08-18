#!/usr/bin/env node
/**
 * S 的**规范符合性**门 —— 断言 src/status.mjs 实现了 01-CONTRACTS §1.5，
 * 而不只是「自洽」。
 *
 * 〔为什么存在〕R3 fix-audit 对既有的 1389 万向量穷举 oracle 下了这个判词：
 *
 *   「它断言全函数 / 值域 / 纯 / 格运算单调 / 六值可达 / 4 条 golden，
 *     但**不断言任何『这个输入应该得到哪个状态』**。对 status.mjs 做 10 个
 *     单向抬高状态的变异，9 个存活（oracle 全绿），其中包括把 flag→状态的
 *     整套机制删光。」
 *
 * 也就是说：穷举 oracle 证明的是「这 259 行代码自洽」，不是「它实现了 §1.5」。
 * 一个恒返回 verified 的实现同样自洽、同样纯、同样全函数。
 *
 * 本门补的正是那条缺失的映射断言。两部分：
 *   ① §7.3 作用表 ↔ 实现的 FLAG_CEILING / FLAG_STEPDOWN 双向绑定（此前无门覆盖）
 *   ② 逐条源自 §1.5 的黄金用例，每条标注它检验的**规范子句**
 *
 * 用 --impl <path> 指向别的实现（变异测试用）。
 */
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { join } from 'node:path'

const rootArg = process.argv.indexOf('--root')
const ROOT = rootArg > -1 ? process.argv[rootArg + 1] : fileURLToPath(new URL('..', import.meta.url))
const implArg = process.argv.indexOf('--impl')
const IMPL = implArg > -1 ? process.argv[implArg + 1] : join(ROOT, 'src/status.mjs')

const mod = await import(IMPL.startsWith('/') ? IMPL : join(process.cwd(), IMPL))
const { S, ST, FLAG_CEILING_EXPORT, FLAG_STEPDOWN_EXPORT } = mod

let failed = 0
const fail = m => { failed++; console.log(`FAIL  ${m}`) }

// 基线向量提前定义：§7.3.1 的载体判据是**行为**判据，需要它。
const BASE = Object.freeze({
  kind: 'K-D', source_integrity: 'intact', evidence_grade: 'G5',
  independent_cluster_count: 3, counter_evidence_searched: true,
  counter_evidence_found: false, mechanism_results: [{ gate_class: 'GC-0' }],
  flags: [], budget_state: 'ok', retention_tier: 'A',
  question_frozen: true, rerun_gate_passed: true,
  has_verbatim_quote: false, quote_faithful: 'na',
  anchor_containment_passed: true, polarity_scope_passed: true, attribution_verdict: 'support',
  inference_gate_passed: true, chart_extracted: false,
})
const c = o => ({ ...BASE, ...o })

// ── ① §7.3 作用表 ↔ 实现 双向绑定 ───────────────────────────────────────
// 审计原文：「C-1 修复的承重产物是 §7.3 这张表，但**没有任何门把这张表和实现
// 绑起来**。check_contracts 的 V7.9 只做 flag id 的集合差集，完全不读作用类型列
// 和值列；穷举 oracle 则一个字符都不读 01-CONTRACTS。」
const contracts = readFileSync(join(ROOT, '01-CONTRACTS.md'), 'utf8')
const specCeiling = {}
const specStepdown = new Set()
const NAME2ST = { 'ST-V': 'verified', 'ST-A': 'attributed', 'ST-E': 'estimated',
                  'ST-U': 'unverified', 'ST-C': 'contested', 'ST-N': 'not_covered' }

for (const m of contracts.matchAll(/^\|\s*(F-\d+[a-z]?)\s*`[^`]*`\s*\|\s*`?(ceiling|step-down|indirect|none)`?\s*\|\s*([^|]*)\|/gm)) {
  const [, id, kind, val] = m
  if (kind === 'ceiling') {
    const st = val.trim().match(/ST-[VAEUCN]/)
    if (!st) { fail(`§7.3 的 ${id} 作用类型是 ceiling，但值列读不出 ST-*：${val.trim()}`); continue }
    specCeiling[id] = NAME2ST[st[0]]
  } else if (kind === 'step-down') {
    specStepdown.add(id)
  }
}

if (!Object.keys(specCeiling).length || !specStepdown.size) {
  console.log('FAIL  §7.3 作用表解析出 0 条 —— 表格式变了，本门在空集上无意义，拒绝给绿灯')
  process.exit(2)
}

if (!FLAG_CEILING_EXPORT || !FLAG_STEPDOWN_EXPORT) {
  fail('src/status.mjs 未导出 FLAG_CEILING_EXPORT / FLAG_STEPDOWN_EXPORT —— 无法与 §7.3 比对')
} else {
  for (const [id, st] of Object.entries(specCeiling)) {
    if (FLAG_CEILING_EXPORT[id] !== st)
      fail(`§7.3 说 ${id} 的 ceiling 是 ${st}，实现是 ${FLAG_CEILING_EXPORT[id] ?? '（缺）'}`)
  }
  for (const id of Object.keys(FLAG_CEILING_EXPORT)) {
    if (!(id in specCeiling)) fail(`实现里的 ceiling flag ${id} 在 §7.3 表里没有对应行`)
  }
  for (const id of specStepdown) {
    if (!FLAG_STEPDOWN_EXPORT.has(id)) fail(`§7.3 说 ${id} 是 step-down，实现里没有`)
  }
  for (const id of FLAG_STEPDOWN_EXPORT) {
    if (!specStepdown.has(id)) fail(`实现里的 step-down flag ${id} 在 §7.3 表里不是 step-down`)
  }
}
// §7.3.1〔R4/R4-03 修复〕本门原先只解析 §7.3 主表，**§7.3.1 的 17 个 flag 一个不读**。
// F-10 正落在那里：它写「第 1 步强制 base = ST-E」，而实现里第 1 步读的是 chart_extracted。
// 现在逐条断言：§7.3.1 里每个声称「在第 1 步/第 0 步返回」的 flag，
// 必须在实现里有一条可执行的载体——要么它本身被读，要么它与被读的字段有强制一致约束。
// 定位必须锚在**表格标题本身**，不能 split 字符串「§7.3.1」——该串在散文里也出现，
// 那样切出来的是空集，而空集上所有断言都成立（本项目已因空集吃过一次亏，见指针门的空集闸）。
const m731 = contracts.match(/\*\*§7\.3\.1[\s\S]*?\n\n([\s\S]*?)(?=\n\*\*§7\.3\.2|\n### )/)
const sec731 = m731 ? m731[1] : ''
// 表格里一格可以是 `F-05 / F-06 / F-07` 这样的组，逐个取。
// 明确排除自陈「不作用于 S」的行——它们本来就不该在实现里有载体。
const rows731 = sec731.split('\n').filter(l => /^\|\s*F-\d/.test(l) && !/不作用于\s*`?S`?/.test(l))
const flags731 = [...new Set(rows731.flatMap(l => [...l.matchAll(/F-\d+[a-z]?/g)].map(x => x[0])))]
if (!flags731.length) {
  fail('§7.3.1 解析出 0 个 flag —— 该节格式变了，本门在空集上无意义')
} else {
  // 〔R5-06 修复〕原判据是 `!src.includes(id)`——**纯字符串包含**。
  // 实证：删掉 F-33 的真实驱动行、只留一行提到 F-33 的注释，
  // 门仍打印「PASS §7.3.1 的 15 个 flag 在实现中都有载体」，66 条黄金用例全过。
  // 而这条断言的修复注旁边刚写完「主语与被读字段没有绑定，正是 F-10 那条 P1 的形状」——
  // 它自己检验的恰恰是**主语字符串在不在文件里**。
  //
  // 现改为**行为判据**：裸置位该 flag（其余字段取基线合法值）必须使 S 偏离基线状态。
  // 一条注释改变不了行为，因此这条判据无法被注释满足。
  const baseline = S(BASE).status
  const orphan = flags731.filter(id => {
    try { return S({ ...BASE, flags: [id] }).status === baseline } catch { return false }
  })
  if (orphan.length) {
    fail(`§7.3.1 的 ${orphan.length} 个 flag 在 src/status.mjs 里没有任何载体：${orphan.join(', ')}\n` +
         '        它们声称「在第 0 步/第 1 步已返回」，但实现并不读它们——\n' +
         '        主语与被读字段之间没有绑定，正是 F-10 那条 P1 的形状。')
  } else {
    console.log(`PASS  §7.3.1 的 ${flags731.length} 个 flag 在实现中都有载体`)
  }
}

// ── §3.4 / §1.5.2 / §8.6.2 三张表 ↔ 实现 绑定 ────────────────────────
// 〔R4 修复〕本门此前**只给 §7.3 一张表**建了双向绑定。R4 用独立变异集实证：
//   G1: ST.N → ST.V     双门存活（同一条 claim，正确 not_covered，变异 verified）
//   G3/G2: ST.A → ST.V  双门存活
//   K(K-I): 2 → 1       双门存活（K-I 单簇，正确 unverified，变异 attributed）
// 三张同等承重的表没有任何门守着——修一张表不等于修了这一类。
const specGrade = {}
for (const m of contracts.matchAll(/^\|\s*(G[0-5])\s*\|\s*\*{0,2}(ST-[VAEUCN])\*{0,2}\s*[,，]?[^|]*\|/gm)) {
  specGrade[m[1]] = NAME2ST[m[2]]
}
const specK = {}
for (const m of contracts.matchAll(/`K\((K-[A-Z-]+)\)\s*=\s*(\d)`/g)) specK[m[1]] = Number(m[2])
const specTier = {}
for (const m of contracts.matchAll(/^-\s*Tier\s+([ABC])\s*→\s*([^\n]*)$/gm)) specTier[m[1]] = m[2]

const { GRADE_CEILING_EXPORT, K_EXPORT, TIER_CEILING_EXPORT } = mod
if (!GRADE_CEILING_EXPORT || !K_EXPORT || !TIER_CEILING_EXPORT) {
  fail('src/status.mjs 未导出 GRADE_CEILING_EXPORT / K_EXPORT / TIER_CEILING_EXPORT')
} else {
  if (Object.keys(specGrade).length < 6) {
    fail(`§3.4 只解析出 ${Object.keys(specGrade).length} 行（应为 6 行 G5..G0）——表格式变了，本门在残缺集上无意义`)
  }
  for (const [g, st] of Object.entries(specGrade)) {
    if (GRADE_CEILING_EXPORT[g] !== st)
      fail(`§3.4 说 ${g} 的上限是 ${st}，实现是 ${GRADE_CEILING_EXPORT[g] ?? '（缺）'}`)
  }
  if (Object.keys(specK).length < 4) {
    fail(`§1.5.2 只解析出 ${Object.keys(specK).length} 个 K 值（应为 4 个）`)
  }
  for (const [k, v] of Object.entries(specK)) {
    if (K_EXPORT[k] !== v) fail(`§1.5.2 说 K(${k}) = ${v}，实现是 ${K_EXPORT[k] ?? '（缺）'}`)
  }
  // §8.6.2 是散文不是表：Tier C 明写 `evidence_grade ≤ G2`（仅存在性），
  // 而 §3.4 给 G2 的上限就是实现里 TIER_CEILING.C 应有的值。
  if (!/Tier C/.test(Object.keys(specTier).length ? 'Tier C' : '') && !specTier.C) {
    fail('§8.6.2 的 Tier 耦合规则解析出 0 条')
  } else if (!/G2/.test(specTier.C ?? '')) {
    // 〔R5-05 修复〕原断言写作 `TIER_CEILING_EXPORT.C !== specGrade.G2`——
    // 它比的是**实现**与 **§3.4 的 G2**，**根本没读 §8.6.2 的文本**。
    // 实证：把 §8.6.2 的「Tier C → ≤ G2」改成「≤ G4」，门仍打印
    // 「三张表 ↔ 实现绑定 · Tier 耦合一致」并 exit 0。守门那行是重言式。
    // R4 说「只绑了一张表」，我把 1 补到 2 却报成 3。
    fail(`§8.6.2 的 Tier C 规则里读不到 G2（实际文本：${(specTier.C ?? '（缺）').slice(0, 60)}）`)
  } else if (TIER_CEILING_EXPORT.C !== specGrade.G2) {
    fail(`§8.6.2 说 Tier C 压到 ≤ G2（§3.4 给 G2 的上限是 ${specGrade.G2}），实现的 TIER_CEILING.C 是 ${TIER_CEILING_EXPORT.C}`)
  } else {
    console.log(`PASS  §3.4 / §1.5.2 / §8.6.2 三张表 ↔ 实现绑定 · 等级 ${Object.keys(specGrade).length} 行 / K ${Object.keys(specK).length} 个 / Tier 耦合一致`)
  }
}

if (!failed) console.log(`PASS  §7.3 作用表 ↔ 实现绑定 · ceiling ${Object.keys(specCeiling).length} 条 / step-down ${specStepdown.size} 条 双向一致`)

// ── ② 源自 §1.5 的黄金映射 ──────────────────────────────────────────────

// 每条：[子句, 说明, 输入, 期望状态]
const GOLDEN = [
  ['基线',    'K-D 封闭式 + 重跑过 + G5 + TierA + 3 簇 + 无 flag', c({}), ST.V],

  ['§1.5 0a', 'source_integrity=mutated',        c({ source_integrity: 'mutated' }), ST.U],
  ['§1.5 0a', 'source_integrity=missing',        c({ source_integrity: 'missing' }), ST.U],
  ['§1.5 0b', 'source_integrity=contaminated',   c({ source_integrity: 'contaminated' }), ST.C],
  ['§1.5 0c', 'source_integrity=not_covered',    c({ source_integrity: 'not_covered' }), ST.N],
  ['§1.5 0d', '带逐字引语且 quote_faithful=fail', c({ has_verbatim_quote: true, quote_faithful: 'fail' }), ST.U],
  ['§1.5 0e', 'counter_evidence_searched=false（§7.2.3「逃不过的只有这一条」）',
              c({ counter_evidence_searched: false }), ST.N],
  ['§1.5 0f', 'budget_state=exhausted',          c({ budget_state: 'exhausted' }), ST.N],
  ['§1.5 0g', 'mechanism_results 为空',          c({ mechanism_results: [] }), ST.N],
  ['§1.3',    '必填字段缺失 → not_covered（§9.19 MISSING == FAIL）',
              (() => { const x = c({}); delete x.counter_evidence_searched; return x })(), ST.N],

  ['§1.5 1',  'K-D 封闭式 + 重跑过 → ST-V',      c({ kind: 'K-D', question_frozen: true, rerun_gate_passed: true }), ST.V],
  ['§2.1',    'K-D 开放式（未冻结）永不可达 ST-V', c({ kind: 'K-D', question_frozen: false }), ST.A],
  ['§1.5 1',  'K-D 重跑门不过 → ST-U',           c({ kind: 'K-D', rerun_gate_passed: false }), ST.U],
  // 〔R4/R4-02 修复〕这三条此前只有第一条，且它写作
  //   `c({ kind: 'K-L-T', anchor_containment_passed: true })` → ST-V，
  // 即**本门在为已被 §2.2.1 废止的单合取判据背书**——新增的门反过来给旧判据发绿灯，
  // 是本轮最难堪的一条。K-L-T 现在是两个合取项，三种组合各占一行。
  ['§2.2.1',  'K-L-T 两个合取项全过 → ST-V',
              c({ kind: 'K-L-T', anchor_containment_passed: true, polarity_scope_passed: true }), ST.V],
  ['§2.2.1',  'K-L-T 包含检验过但**极性作用域不过** → 降为 K-L-A（K=2，1 簇不足）',
              c({ kind: 'K-L-T', anchor_containment_passed: true, polarity_scope_passed: false,
                  attribution_verdict: 'support', independent_cluster_count: 1 }), ST.U],
  ['§1.5 1',  'K-L-T 包含检验不过 → 降为 K-L-A 处理（K 值随之为 2，故 1 簇不足）',
              c({ kind: 'K-L-T', anchor_containment_passed: false, polarity_scope_passed: true,
                  attribution_verdict: 'support', independent_cluster_count: 1 }), ST.U],
  ['§2.2.1',  'K-L-T 缺 polarity_scope_passed → 抛 ContractGap（合取项不能省）',
              (() => { const x = c({ kind: 'K-L-T' }); delete x.polarity_scope_passed; return x })(), '抛异常'],
  ['§1.5 1',  'K-L-A support → ST-A',            c({ kind: 'K-L-A', attribution_verdict: 'support' }), ST.A],
  ['§1.5 1',  'K-L-A not-support → ST-U',        c({ kind: 'K-L-A', attribution_verdict: 'not-support' }), ST.U],
  ['§2.3.1',  'K-I 永不可达 ST-V（推断门过也只到 ST-A）',
              c({ kind: 'K-I', inference_gate_passed: true, source_integrity: 'na' }), ST.A],
  ['§1.5 1',  'K-I 推断门不过 → ST-U',           c({ kind: 'K-I', inference_gate_passed: false, source_integrity: 'na' }), ST.U],
  ['§3.5',    '图形几何读数强制 ST-E（覆盖 kind 的结果）——F-10 必须同时置位，见 §7.2.4',
              c({ chart_extracted: true, flags: ['F-10'] }), ST.E],

  ['§6.1/V1.4', '决定性机制含 GC-2 → 永不得写 ST-V',
              c({ mechanism_results: [{ gate_class: 'GC-0' }, { gate_class: 'GC-2' }] }), ST.A],

  ['§1.5 2a', 'counter_evidence_found=true 是吸收态，覆盖任何 base',
              c({ counter_evidence_found: true }), ST.C],
  ['§1.5 2b', '独立簇数不足 K(K-D)=1 → 降一档',  c({ independent_cluster_count: 0 }), ST.A],
  ['§1.5 2b', 'K-L-A 需要 2 簇，只有 1 簇 → 降一档',
              c({ kind: 'K-L-A', independent_cluster_count: 1 }), ST.U],
  ['§1.5 2c', 'evidence_grade=G4 压上限',        c({ evidence_grade: 'G4' }), ST.A],
  ['§1.5 2c', 'retention_tier=C 压上限（§8.6.2）', c({ retention_tier: 'C' }), ST.A],
  ['§1.5 2d', 'F-13 ceiling=ST-U',               c({ flags: ['F-13'] }), ST.U],
  ['§1.5 2d', 'F-03 ceiling=ST-A',               c({ flags: ['F-03'] }), ST.A],
  ['§1.5 2d′','F-01 step-down 降一档',           c({ flags: ['F-01'] }), ST.A],
  ['§1.5 2d′','两条 step-down 叠加降两档',       c({ flags: ['F-01', 'F-02'] }), ST.U],
  // 〔R4 后〕F-14 只能在 `independent_cluster_count == 1` 时置位（§7.2.5 驱动表），
  // 所以「作用类型 none」的正确测法是：**驱动条件成立时，加不加 F-14 结果相同**。
  // 原用例写作裸置位 + 期望 ST-V，在驱动约束下已不合法。
  ['§7.3',    'F-14 作用类型 none —— 驱动条件成立时不改变结果（对照：无 F-14）',
              c({ flags: [], independent_cluster_count: 1 }), ST.V],
  ['§7.3',    'F-14 作用类型 none —— 驱动条件成立时不改变结果（加 F-14 应相同）',
              c({ flags: ['F-14'], independent_cluster_count: 1 }), ST.V],
  ['§7.3',    'F-08 作用类型 none —— 不得影响状态', c({ flags: ['F-08'] }), ST.V],
  ['§1.5 2e', 'budget_state=degraded 降一档',    c({ budget_state: 'degraded' }), ST.A],

  // 〔R4/R4-03〕F-10 的主语与 S 读的字段此前无绑定：`flags:['F-10'], chart_extracted:false`
  // 返回 verified，而 V7.2 断言含 F-10 的 claim 状态 ≤ ST-E。两道门都构造性看不见——
  // 穷举 oracle 把 F-10 从 chart_extracted 派生（反例不可达），本门的 §7.3 正则只吃主表。
  ['§7.2.4',  'F-10 置位但 chart_extracted=false → fail-closed',
              c({ flags: ['F-10'], chart_extracted: false }), ST.N],
  ['§7.2.4',  'chart_extracted=true 但 F-10 未置位 → fail-closed',
              c({ flags: [], chart_extracted: true }), ST.N],
  ['§7.2.4',  '两者一致置位 → §3.5 强制 ST-E',
              c({ flags: ['F-10'], chart_extracted: true }), ST.E],
  ['V7.2',    '含 F-10 且 G4 → meet(ST-E, ST-A) = ST-U（≤ ST-E 成立，== ST-E 恒假）',
              c({ flags: ['F-10'], chart_extracted: true, evidence_grade: 'G4' }), ST.U],

  // 〔R4 后实测扩展〕§7.2.5：F-10 不是特例，整族都能裸置位而 S 返回 verified。
  // 逐条钉死「置位 ⟹ 驱动条件成立」。
  ['§7.2.5',  'F-29 裸置位（counter_evidence_searched 却为 true）→ fail-closed',
              c({ flags: ['F-29'] }), ST.N],
  ['§7.2.5',  'F-28 裸置位（无逐字引语）→ fail-closed',        c({ flags: ['F-28'] }), ST.N],
  ['§7.2.5',  'F-31 裸置位（未找到反例）→ fail-closed',        c({ flags: ['F-31'] }), ST.N],
  ['§7.2.5',  'F-05 裸置位（source_integrity=intact）→ fail-closed', c({ flags: ['F-05'] }), ST.N],
  ['§7.2.5',  'F-16 裸置位（source_integrity=intact）→ fail-closed', c({ flags: ['F-16'] }), ST.N],
  ['§7.2.5',  'F-11 裸置位（budget_state=ok）→ fail-closed',    c({ flags: ['F-11'] }), ST.N],
  ['§7.2.5',  'F-14 裸置位（簇数=3）→ fail-closed',             c({ flags: ['F-14'] }), ST.N],
  // 防过修：驱动条件成立时必须正常放行
  ['§7.2.5',  'F-31 + counter_evidence_found=true → 2a 吸收态 ST-C',
              c({ flags: ['F-31'], counter_evidence_found: true }), ST.C],
  ['§7.2.5',  'F-29 + counter_evidence_searched=false → 0e ST-N',
              c({ flags: ['F-29'], counter_evidence_searched: false }), ST.N],
  ['§7.2.5',  'F-14 + 簇数=1（K-D 的 K=1，不触发 2b）→ 仍 ST-V',
              c({ flags: ['F-14'], independent_cluster_count: 1 }), ST.V],

  // 〔R4 修复〕§3.4 六行此前只有 G4 一行有黄金用例，G5/G3/G2/G1/G0 全空——
  // `G1: ST.N → ST.V` 的变异因此在双门下存活（正确 not_covered，变异 verified）。
  ['§3.4 G5', 'G5 上限 ST-V',  c({ evidence_grade: 'G5' }), ST.V],
  ['§3.4 G4', 'G4 上限 ST-A',  c({ evidence_grade: 'G4' }), ST.A],
  ['§3.4 G3', 'G3 上限 ST-A',  c({ evidence_grade: 'G3' }), ST.A],
  ['§3.4 G2', 'G2 上限 ST-A',  c({ evidence_grade: 'G2' }), ST.A],
  ['§3.4 G1', 'G1 上限 ST-N（不得作为任何 claim 的承重证据）', c({ evidence_grade: 'G1' }), ST.N],
  ['§3.4 G0', 'G0 上限 ST-N',  c({ evidence_grade: 'G0' }), ST.N],

  // §1.5.2 的四个 K 值：每个都用「恰好差一簇」把它钉死
  ['§1.5.2',  'K(K-D)=1 —— 1 簇够，不降档',
              c({ kind: 'K-D', independent_cluster_count: 1 }), ST.V],
  ['§1.5.2',  'K(K-L-T)=1 —— 1 簇够',
              c({ kind: 'K-L-T', independent_cluster_count: 1 }), ST.V],
  ['§1.5.2',  'K(K-L-A)=2 —— 1 簇不够，降一档',
              c({ kind: 'K-L-A', independent_cluster_count: 1 }), ST.U],
  ['§1.5.2',  'K(K-L-A)=2 —— 2 簇够',
              c({ kind: 'K-L-A', independent_cluster_count: 2 }), ST.A],
  ['§1.5.2',  'K(K-I)=2 —— 1 簇不够，降一档（这条变异此前双门存活）',
              c({ kind: 'K-I', source_integrity: 'na', independent_cluster_count: 1 }), ST.U],
  ['§1.5.2',  'K(K-I)=2 —— 2 簇够',
              c({ kind: 'K-I', source_integrity: 'na', independent_cluster_count: 2 }), ST.A],

  // §8.6.2 三档
  ['§8.6.2',  'Tier A 不压上限', c({ retention_tier: 'A' }), ST.V],
  ['§8.6.2',  'Tier B 不压上限', c({ retention_tier: 'B' }), ST.V],
  ['§8.6.2',  'Tier C 压到 ≤ G2 的上限', c({ retention_tier: 'C' }), ST.A],

  // §1.5.1.1 降一档的逐点定义（`降一档(ST-E)=ST-U` 的变异此前双门存活）
  // 〔R5-04 修复〕此前只给 7 条 flag 写了裸置位用例，16 行里 9 行删掉门不判红。
  // 现在**逐行**覆盖：每一条驱动规则都有一个「裸置位 → ST-N」的黄金用例。
  // 这不是穷举癖——R5 实测把这 9 行逐个删掉，8 行删除后裸置位直接 verified。
  ...['F-06', 'F-07', 'F-27', 'F-18', 'F-21', 'F-30', 'F-32', 'F-33', 'F-34', 'F-28a'].map(f =>
    ['§7.2.5', `${f} 裸置位（驱动条件不成立）→ fail-closed`, c({ flags: [f] }), ST.N]),

  // §7.3.1 承诺的**另一面**：驱动条件成立时，该走哪一步就走哪一步。
  // 〔R5-18〕FLAG_DRIVER 在 0a/0b/0c **之后**求值，所以 si 类驱动条件在被求值处恒为假——
  // 这不是缺陷而是设计：si 真的是 contaminated 时 0b 先返回 ST-C（§7.3.1 承诺的那一面），
  // si 是 intact 却带着 F-05 才是管线不一致（fail-closed）。两面各有黄金用例守着。
  ['§7.3.1', 'F-05 + source_integrity=contaminated → 0b 承诺的 ST-C',
             c({ flags: ['F-05'], source_integrity: 'contaminated' }), ST.C],
  ['§7.3.1', 'F-16 + source_integrity=mutated → 0a 承诺的 ST-U',
             c({ flags: ['F-16'], source_integrity: 'mutated' }), ST.U],
  ['§7.3.1', 'F-18 + source_integrity=not_covered → 0c 承诺的 ST-N',
             c({ flags: ['F-18'], source_integrity: 'not_covered' }), ST.N],
  ['§7.3.1', 'F-28 + 引语检验失败 → 0d 承诺的 ST-U',
             c({ flags: ['F-28'], has_verbatim_quote: true, quote_faithful: 'fail' }), ST.U],
  ['§7.3', 'F-34 + Tier C → 经 §8.6.2 压到 ST-A',
             c({ flags: ['F-34'], retention_tier: 'C' }), ST.A],
  ['§7.3', 'F-28a + F-28 同时置位且引语失败 → 仍是 0d 的 ST-U',
             c({ flags: ['F-28', 'F-28a'], has_verbatim_quote: true, quote_faithful: 'fail' }), ST.U],

  ['§1.5.1.1','降一档(ST-E)=ST-U —— 图形读数叠四次降档仍必须触底',
              c({ chart_extracted: true, flags: ['F-10', 'F-01', 'F-02'], independent_cluster_count: 0,
                  budget_state: 'degraded' }), ST.U],
]

let gpass = 0
for (const [clause, desc, input, want] of GOLDEN) {
  let got
  try { got = S(input).status } catch (e) { got = want === '抛异常' ? '抛异常' : `抛异常 ${e.constructor.name}: ${e.message}` }
  if (got === want) gpass++
  else fail(`[${clause}] ${desc}\n        期望 ${want}  实测 ${got}`)
}
if (gpass === GOLDEN.length) console.log(`PASS  §1.5 黄金映射 · ${GOLDEN.length}/${GOLDEN.length} 条`)
else console.log(`      §1.5 黄金映射 · ${gpass}/${GOLDEN.length} 条通过`)

console.log()
if (failed) { console.log(`${failed} 处不符合规范`); process.exit(1) }
console.log('PASS  S 的实现与 01-CONTRACTS §1.5 / §7.3 一致')
