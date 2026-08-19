#!/usr/bin/env node
// G-L1-b 锚点包含 · 两侧标定（GC-0：离线、确定性、零模型、零网络）
//
// 本门守着一次**放松**。放松是 fail-open 方向，所以负例侧比正例侧更要紧：
// 每放开一档，就要有一条样本证明那一档没有顺带放走别的东西。
//
// 用法:  node gates/check_containment.mjs
// 退出码: 0 = 全部符合，1 = 有不符

import { anchorContainment, numericForm, stem } from '../src/gates/g-containment.mjs'

const A_OSC36 = 'Thirty-six percent of replications had statistically significant results;'
const A_OSC47 = '47% of original effect sizes were in the 95% confidence interval of the replication effect size;'
const A_OSC39 = '39% of effects were subjectively rated to have replicated the original result;'
const A_CN    = '该方法在测试集上达到三十六个百分点。'
const A_COST  = 'The cost to develop a cancer drug is $648.0 million, a figure significantly lower than prior estimates.'

// [编号, 期望, 载荷, 槽型, 锚句, 说明]
const CASES = [
  // ── 正例：合法转录必须放行（外部标定测试发现的假阴） ──────────────
  ['P-1', true,  { finding: 'replication', value: '36' }, { finding: 'entity', value: 'value' }, A_OSC36,
   'T2-1：36 vs 原文 Thirty-six（数值等价）'],
  ['P-2', true,  { finding: 'replication', value: '39%' }, { finding: 'entity', value: 'value' }, A_OSC39,
   'T2-2：replication vs 原文 replicated（同词干）'],
  ['P-3', true,  { value: '36%' }, { value: 'value' }, A_OSC36,
   '36% vs “Thirty-six percent”（数词 + percent 一起归一）'],
  ['P-4', true,  { value: '36' }, { value: 'value' }, A_CN,
   '中文数字：36 vs 三十六'],
  ['P-5', true,  { value: '36%' }, { value: 'value' }, A_CN,
   '中文百分号：36% vs 三十六个百分点'],
  ['P-6', true,  { drug: 'estimation', value: '$648.0 million' }, { drug: 'entity', value: 'value' }, A_COST,
   'estimation vs 原文 estimates（同词干；逐字比对够不着）+ 数值逐字'],

  // ── 负例：放松不得顺带放走这些 ───────────────────────────────────
  ['N-1', false, { value: '36%' }, { value: 'value' }, A_OSC47,
   '★ T2-3 的核心：声称 36% 而锚在 47% 那句 —— 数值等价**不得**让它通过'],
  ['N-2', false, { value: '46' }, { value: 'value' }, A_OSC36,
   '数词写对了但数错了：Thirty-six ≠ 46'],
  ['N-3', false, { value: '3' }, { value: 'value' }, A_OSC36,
   '★ 子串陷阱：归一化后锚句含 “36”，但载荷 3 不是它的一个合法读数……'],
  ['N-4', false, { metric: 'replication', value: '36' }, { metric: 'metric', value: 'value' }, A_OSC39,
   '★ metric 槽**不放松**：39% 那句里没有字面 “replication”，判据不得靠词干蒙混'],
  ['N-5', false, { sample: 'replication', value: '39%' }, { sample: 'sample', value: 'value' }, A_OSC39,
   '★ sample 槽同样不放松'],
  ['N-6', false, { finding: 'confidence', value: '36' }, { finding: 'entity', value: 'value' }, A_OSC36,
   '词干放松不得跨词：confidence 不在这句里'],
  ['N-7', false, {}, {}, A_OSC36, '载荷为空不得判过（空集 vacuous truth）'],
  ['N-8', false, { value: '95%' }, { value: 'value' }, A_OSC36,
   '锚句里根本没有的数'],
  ['N-9', false, { value: '7' }, { value: 'value' }, A_OSC47,
   '★ 逐字侧的同一个子串陷阱：锚句有 “47%”，载荷 7 不是它的一个合法读数'],
  ['N-10', false, { value: '5' }, { value: 'value' }, A_OSC47,
   '★ 小数/千分位侧：锚句有 “95%”，载荷 5 不得命中'],
  ['N-11', false, { value: '648' }, { value: 'value' }, A_COST,
   '★ 锚句是 “$648.0 million”；只写 648 与原文的量纲读数不同,不得逐字命中'],
]

let bad = 0
console.log('锚点包含门 · 两侧标定\n')
console.log(`${'编号'.padEnd(6)}${'期望'.padEnd(6)}${'实测'.padEnd(6)}${'命中方式'.padEnd(10)}说明`)
console.log('─'.repeat(96))
for (const [id, want, payload, types, anchor, why] of CASES) {
  const r = anchorContainment(payload, types, anchor)
  const how = r.per_slot.map(s => s.matched ?? '×').join(',') || '—'
  const ok = r.pass === want
  if (!ok) bad++
  console.log(`${id.padEnd(6)}${String(want).padEnd(6)}${String(r.pass).padEnd(6)}${how.padEnd(10)}${why}${ok ? '' : '   ← 不符'}`)
}

// 放松档位必须**真的被用到**，否则这门在测一个不存在的能力
const used = new Set()
for (const [, want, payload, types, anchor] of CASES) {
  if (!want) continue
  for (const s of anchorContainment(payload, types, anchor).per_slot) if (s.matched) used.add(s.matched)
}
console.log(`\n实际用到的命中方式: ${[...used].sort().join(' / ')}`)
for (const need of ['exact', 'numeric', 'stem']) {
  if (!used.has(need)) { bad++; console.log(`FAIL  没有任何正例用到 “${need}” —— 这一档没被测到`) }
}

console.log()
if (bad) { console.log(`FAIL  ${bad} 处不符`); process.exit(1) }
const pos = CASES.filter(c => c[1]).length
console.log(`PASS  锚点包含 ${CASES.length} 条（正 ${pos} / 负 ${CASES.length - pos}）全部符合；三档命中方式都有正例覆盖`)
