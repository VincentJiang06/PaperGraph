#!/usr/bin/env node
/**
 * 留出集 —— 八条 meta 分析 claim，**没有参与过任何修复**。
 *
 * 期望与预测写在 PREDICTIONS.md，落盘时间早于本文件第一次运行。
 * 跑出什么报什么；**不许为了让它变绿而改代码，除非那个改动同时能在
 * 外部标定集上站住**——否则就是把留出集变成又一批拟合过的题。
 */
import { readFileSync, mkdtempSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const { runOnce } = await import(join(HERE, '../../src/run.mjs'))
const snap = f => readFileSync(join(HERE, 'snapshots', f), 'utf8').trim()

/** 句末判定：`.` 后跟空白，小数点不算 */
function sentenceWith(text, needle) {
  const i = text.indexOf(needle)
  if (i < 0) throw new Error(`快照里没有 ${JSON.stringify(needle)}`)
  const isEnd = k => /[。；]/.test(text[k]) ||
    (/[.;]/.test(text[k]) && (k + 1 >= text.length || /\s/.test(text[k + 1])))
  let end = i + needle.length
  while (end < text.length) { if (isEnd(end)) { end++; break } end++ }
  let start = i
  while (start > 0) { if (isEnd(start - 1)) break; start-- }
  return text.slice(start, end).trim()
}

const SRC = {
  H1: { f: 'H1-diabetes.txt', wid: 'pmid:42258428' },
  H2: { f: 'H2-stones.txt',   wid: 'pmid:41385459' },
  H3: { f: 'H3-lipus.txt',    wid: 'pmid:42299555' },
  H4: { f: 'H4-chd.txt',      wid: 'pmid:41792680' },
  H5: { f: 'H5-resus.txt',    wid: 'pmid:42116301' },
  H6: { f: 'H6-ire.txt',      wid: 'pmid:42054172' },
}
for (const k of Object.keys(SRC)) SRC[k].body = snap(SRC[k].f)

const mkFetch = (key, needle) => {
  const s = SRC[key], sent = sentenceWith(s.body, needle)
  return {
    url: `https://europepmc.org/article/MED/${s.wid.split(':')[1]}`,
    body: s.body, httpStatus: 200, retrievedAt: '2026-08-19T00:00:00Z',
    extractorVersion: 'europepmc-abstract-1', work_id: s.wid, version_id: 'v1',
    locator: 'abstract', content_kind: 'abstract', retention_tier: 'A',
    quote: sent, anchorSentence: sent,
  }
}
const claim = (payload, slot_types, metric_frame, discriminator) => ({
  claim_id: 'c1', kind: 'K-L-T', payload, slot_types, metric_frame, evidence_index: [0],
  ...(discriminator ? { discriminator } : {}),
})
const autoQ = c => ({ query: [...new Set([...Object.values(c.metric_frame ?? {}),
  ...Object.values(c.payload ?? {})])].join(' ') + ' 反驳', result_keys: [] })

// [编号, 应判, 预测, 说明, fetch, claim, skeleton]
const CASES = [
  ['H-1', 'attributed', 'attributed', '三个并列合并患病率，discriminator 说清了是 neuropathy',
   mkFetch('H1', '56.8%'),
   claim({ outcome: 'prevalence', value: '56.8%' }, { outcome: 'entity', value: 'value' },
         { metric: 'pooled prevalence', sample_or_tier: 'diabetic patients' }, 'neuropathy'),
   '糖尿病神经病变的合并患病率为 {{claim:c1.value}}。'],

  ['H-2', 'unverified', 'unverified', '同一句，**未**声明取哪一个读数',
   mkFetch('H1', '56.8%'),
   claim({ outcome: 'prevalence', value: '56.8%' }, { outcome: 'entity', value: 'value' },
         { metric: 'pooled prevalence', sample_or_tier: 'diabetic patients' }),
   '合并患病率为 {{claim:c1.value}}。'],

  ['H-3', 'attributed', 'attributed', '阳性发现 OR = 2.19，不得被否定表误伤',
   mkFetch('H2', 'OR = 2.19'),
   claim({ measure: 'OR', value: '2.19' }, { measure: 'entity', value: 'value' },
         { metric: 'pooled OR', sample_or_tier: 'stone free rate' }),
   '结石清除率的合并 OR 为 {{claim:c1.value}}。'],

  ['H-4', 'unverified', 'unverified', '空结果：no statistically significant difference',
   mkFetch('H2', 'MD = -1.09 min'),
   claim({ measure: 'MD', value: '-1.09' }, { measure: 'entity', value: 'value' },
         { metric: 'pooled MD', sample_or_tier: 'operative time' }),
   '手术时间的合并均差为 {{claim:c1.value}} 分钟。'],

  ['H-5', 'unverified', 'attributed', '★ 预测会漏：`nonsignificant` 不在任何算子表里',
   mkFetch('H3', 'risk ratio of 1.13'),
   claim({ measure: 'risk ratio', value: '1.13' }, { measure: 'entity', value: 'value' },
         { metric: 'pooled RR', sample_or_tier: 'healing rate' }),
   '愈合率的合并风险比为 {{claim:c1.value}}。'],

  ['H-6', 'attributed', 'attributed', '三个并列 OR，discriminator 说清了是 heart failure',
   mkFetch('H4', 'OR = 4.12'),
   claim({ factor: 'heart failure', value: '4.12' }, { factor: 'entity', value: 'value' },
         { metric: 'OR', sample_or_tier: 'undernutrition' }, 'heart failure'),
   '心力衰竭的 OR 为 {{claim:c1.value}}。'],

  ['H-7', 'attributed', 'attributed', '★ 假阳侧：significantly lower 是方向词不是否定',
   mkFetch('H5', 'RR = 0.77'),
   claim({ measure: 'RR', value: '0.77' }, { measure: 'entity', value: 'value' },
         { metric: 'RR', sample_or_tier: 'return of spontaneous circulation' }, 'return of spontaneous circulation'),
   '自主循环恢复的 RR 为 {{claim:c1.value}}。'],

  ['H-8', 'attributed', 'attributed', '★ 已知盲点：I² = 98%，系统对异质性一无所知',
   mkFetch('H6', 'MD: -70.18U/L'),
   claim({ marker: 'CA 19-9', value: '-70.18' }, { marker: 'entity', value: 'value' },
         { metric: 'pooled MD', sample_or_tier: 'CA 19-9' }),
   'CA 19-9 的合并均差为 {{claim:c1.value}} U/L。'],
]

const results = []
for (const [id, should, predicted, desc, fetch, c, skel] of CASES) {
  const root = mkdtempSync(join(tmpdir(), 'hold-'))
  let status, prose
  try {
    const r = runOnce(root, 'r1', [fetch], [c], skel,
      { question: '这个数字站得住吗?', frozen_at: '2026-08-18T00:00:00Z',
        counterSearches: { c1: autoQ(c) } })
    status = JSON.parse(readFileSync(join(root, 'claims', 'c1.status.json'), 'utf8')).status
    prose = r.prose.trim()
  } catch (e) { status = 'REJECTED'; prose = e.message.slice(0, 80) }
  finally { rmSync(root, { recursive: true, force: true }) }
  results.push({ id, should, predicted, desc, status, prose })
}

console.log('留出集 · 八条 meta 分析 claim（未参与过任何修复）\n')
console.log('期望与预测写于运行之前，见 tests/holdout/PREDICTIONS.md\n')
console.log(`${'编号'.padEnd(6)}${'应判'.padEnd(12)}${'预测'.padEnd(12)}${'实测'.padEnd(12)}${''}说明`)
console.log('─'.repeat(104))
for (const r of results) {
  const mark = r.status === r.should ? '  ' : '✗ '
  console.log(`${r.id.padEnd(6)}${r.should.padEnd(12)}${r.predicted.padEnd(12)}${(mark + r.status).padEnd(12)}${r.desc}`)
}

const correct = results.filter(r => r.status === r.should).length
const predictedRight = results.filter(r => r.status === r.predicted).length
console.log('\n' + '─'.repeat(104))
console.log(`判定正确 ${correct}/${results.length}`)
console.log(`预测命中 ${predictedRight}/${results.length}   ← 我事前对系统行为的把握程度`)

const surprises = results.filter(r => r.status !== r.predicted)
if (surprises.length) {
  console.log(`\n意外（实测 ≠ 预测）${surprises.length} 条 —— 这些是我事前不知道的：`)
  for (const s of surprises) console.log(`  ${s.id}  预测 ${s.predicted}，实测 ${s.status}  ${s.desc}`)
}
const known = results.filter(r => r.status !== r.should && r.status === r.predicted)
if (known.length) {
  console.log(`\n事前已预告的失败 ${known.length} 条 —— 预测到了，但仍然是真实的缺陷：`)
  for (const s of known) console.log(`  ${s.id}  ${s.desc}`)
}
export { results }
