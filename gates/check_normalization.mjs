#!/usr/bin/env node
// 跨模块归一化一致性门（GC-0：离线、确定性、零模型、零网络）
//
// 〔来历〕同一个坑，本项目挖了两次：
//   E-3（外部标定测试）—— 组稿器把全角数字漏掉，`９２％` 绕过整条证据链。
//                        修法：扫描前 NFKC。
//   T4-1（真实中文文献）—— 锚点包含把全角原文 `73．55％` 与半角载荷 `73.55%`
//                        判成不匹配。修法：**同一个** NFKC。
//
// 两次相隔一整轮。原因不是谁粗心，是**「文本比对前要归一化」这件事
// 只被记成了一次修复，没有被记成一条跨模块的约束**。
// 一条只活在某个模块里的约束，等于没有约束——下一个模块会重新踩。
//
// 本门是行为层的：把同一段文本的**全角形态**与**半角形态**分别喂给每一个
// 做文本比对的入口，要求它们给出**同一个判定**。它不看实现怎么写的，
// 因此换实现、换模块、加新模块都不影响它，只要新模块进了下面这张表。
//
// 用法:  node gates/check_normalization.mjs
// 退出码: 0 = 全部一致，1 = 有模块对全角/半角给出不同判定

import { anchorContainment } from '../src/gates/g-containment.mjs'
import { polarityScope } from '../src/gates/g-polarity.mjs'
import { frameGate } from '../src/gates/g-frame.mjs'
import { counterQueryOk } from '../src/gates/g-ctr-scan.mjs'
import { compose } from '../src/composer.mjs'

/** 全角 → 半角的成对样本。左边是中文期刊常见排版，右边是转录后的写法。 */
const PAIRS = [
  ['全角百分号',   '该方法达到 ９２％ 的准确率。',        '该方法达到 92% 的准确率。',        '92%'],
  ['全角句点',     '杀虫率分别为 ７３．５５％ 和 ７８．４５％。', '杀虫率分别为 73.55% 和 78.45%。', '73.55%'],
  ['全角数字',     '样本量为 １０６ 例。',                 '样本量为 106 例。',                '106'],
  ['全角括号逗号', '结果为 ９２％（ｐ ＝ ０．０５）。',      '结果为 92%(p = 0.05)。',           '92%'],
]

// [模块名, (text, payload) => 可比较的判定值]
const ENTRIES = [
  ['G-L1-b  锚点包含', (t, p) => anchorContainment({ v: p }, { v: 'value' }, t).pass],
  ['G-L1-c  极性作用域', (t, p) => polarityScope(t, [p], '').pass],
  ['G-FRAME 同源竞争读数', (t, p) => frameGate(t, t, '', [p]).pass],
  ['X-2     反证 query', (t, p) => counterQueryOk(
    { claim_id: 'c', kind: 'K-L-T', payload: { v: p }, slot_types: { v: 'value' },
      metric_frame: { metric: 'accuracy', sample_or_tier: 'test' }, evidence_refs: [] },
    `accuracy test ${p} 反驳`, { resultKeys: [], anchorSentence: t, snapshotText: t }).pass],
  ['W-10    组稿器裸数字', (t) => compose(t, new Map()).ok],
]

let bad = 0
console.log('跨模块归一化一致性门\n')
console.log('把同一段文本的全角形态与半角形态分别喂给每个做文本比对的入口，')
console.log('要求它们给出同一个判定。不看实现，只看行为。\n')
console.log(`${'模块'.padEnd(24)}${'样本'.padEnd(14)}${'全角'.padEnd(8)}${'半角'.padEnd(8)}`)
console.log('─'.repeat(72))
for (const [name, fn] of ENTRIES) {
  for (const [why, wide, narrow, payload] of PAIRS) {
    let a, b
    try { a = fn(wide, payload) } catch (e) { a = `抛:${e.message.slice(0, 12)}` }
    try { b = fn(narrow, payload) } catch (e) { b = `抛:${e.message.slice(0, 12)}` }
    const ok = String(a) === String(b)
    if (!ok) bad++
    console.log(`${name.padEnd(24)}${why.padEnd(14)}${String(a).padEnd(8)}${String(b).padEnd(8)}${ok ? '' : '  ← 不一致'}`)
  }
}

console.log()
if (bad) {
  console.log(`FAIL  ${bad} 处：同一段文本的全角与半角形态得到不同判定`)
  console.log('      「文本比对前要归一化」必须是一条**跨模块**的约束，')
  console.log('      只在某个模块里修一次，下一个模块会重新踩（E-3 → T4-1 就是这么来的）。')
  process.exit(1)
}
console.log(`PASS  ${ENTRIES.length} 个入口 × ${PAIRS.length} 组全角/半角样本，判定全部一致`)
