#!/usr/bin/env node
/**
 * 留出集 二 —— 八条 GWAS claim，**没有参与过任何修复**。
 *
 * 第一批修完后是 8/8，但那一刻它就烧掉了（用例参与过修复）。
 * 这一批换文体：科学计数法。同一个阈值 5×10⁻⁸ 在三篇真实论文里有三种
 * Unicode 写法（U+002D / U+207B / U+2212），本项目此前从未遇到过这一档。
 *
 * 期望与预测写在 PREDICTIONS.md，落盘时间早于本文件第一次运行
 * （哈希见 PREDICTIONS.sha256）。
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
  G1: { f: 'G1-42181176.txt', wid: 'pmid:42181176' },
  G2: { f: 'G2-41560095.txt', wid: 'pmid:41560095' },
  G3: { f: 'G3-41125582.txt', wid: 'pmid:41125582' },
  G4: { f: 'G4-41844886.txt', wid: 'pmid:41844886' },
  G5: { f: 'G5-41075272.txt', wid: 'pmid:41075272' },
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
  ...Object.values(c.payload ?? {})])].join(' ') + ' refute', result_keys: [] })

// [编号, 应判, 预测, 说明, fetch, claim, skeleton]
const CASES = [
  ['J-1', 'attributed', 'attributed', '同句竞争读数 96%，discriminator 说清了是携带者',
   mkFetch('G3', '83% versus 96%'),
   claim({ arm: 'carriers', value: '83%' }, { arm: 'entity', value: 'value' },
         { metric: 'five-year overall survival', sample_or_tier: 'B-ALL children' },
         'carrying novel risk alleles'),
   'Five-year overall survival was {{claim:c1.value}} among carriers.'],

  ['J-2', 'unverified', 'unverified', '同一句，**未**声明取 83 还是 96',
   mkFetch('G3', '83% versus 96%'),
   claim({ arm: 'carriers', value: '83%' }, { arm: 'entity', value: 'value' },
         { metric: 'five-year overall survival', sample_or_tier: 'B-ALL children' }),
   'Five-year overall survival was {{claim:c1.value}}.'],

  ['J-3', 'attributed', 'unverified', '★ 预测会漏：上标负号 U+207B 归一化到 U+2212，与原文的连字符不等',
   mkFetch('G3', '4.8\u2009\u00d7\u200910-3'),
   claim({ measure: 'P value', value: '4.8\u2009\u00d7\u200910\u207b\u00b3' }, { measure: 'entity', value: 'value' },
         { metric: 'P value', sample_or_tier: 'survival difference' }, 'survival difference'),
   'The survival difference had P = {{claim:c1.value}}.'],

  ['J-4', 'attributed', 'attributed', 'U+2212 真负号 + 中间有空格，逐字引用',
   mkFetch('G4', '5\u2009\u00d7\u200910\u2212\u20098'),
   claim({ threshold: 'genome-wide significance', value: '5\u2009\u00d7\u200910\u2212\u20098' },
         { threshold: 'entity', value: 'value' },
         { metric: 'significance threshold', sample_or_tier: 'POAG GWAS' }, 'genome-wide significance'),
   'Genome-wide significance was set at p < {{claim:c1.value}}.'],

  ['J-5', 'attributed', 'attributed', '★ 已知盲点：同一篇摘要自相矛盾（前 four、后 three）',
   mkFetch('G4', 'four novel loci'),
   claim({ cohort: 'European', value: 'four' }, { cohort: 'entity', value: 'value' },
         { metric: 'novel loci', sample_or_tier: 'European cohort' }, 'European cohort'),
   'In the European cohort {{claim:c1.value}} novel loci were identified.'],

  ['J-6', 'unverified', 'attributed', '★ 预测会漏：英文数词 three 不被当成数值载荷，竞争读数 49 不触发',
   mkFetch('G1', 'three BMI-associated loci'),
   claim({ tier: 'genome-wide', value: 'three' }, { tier: 'entity', value: 'value' },
         { metric: 'BMI-associated loci', sample_or_tier: 'admixed Brazilian' }),
   '{{claim:c1.value}} BMI-associated loci reached genome-wide significance.'],

  ['J-7', 'attributed', 'attributed', '竞争读数 one / 237，靠 discriminator + 角色排除',
   mkFetch('G5', '21 suggestive associations'),
   claim({ tier: 'suggestive', value: '21' }, { tier: 'entity', value: 'value' },
         { metric: 'associations', sample_or_tier: 'Pierre Robin Sequence' }, 'suggestive'),
   'We found {{claim:c1.value}} suggestive associations.'],

  ['J-8', 'unverified', 'attributed', '★ 预测 fail-open：千分位逗号被当成子句分隔，374,254 被切碎',
   mkFetch('G4', '374,254 participants'),
   claim({ group: 'total', value: '374,254' }, { group: 'entity', value: 'value' },
         { metric: 'participants', sample_or_tier: 'All of Us POAG' }),
   'The study included {{claim:c1.value}} participants.'],
]

const results = []
for (const [id, should, predicted, desc, fetch, c, skel] of CASES) {
  const root = mkdtempSync(join(tmpdir(), 'hold-'))
  let status, prose
  try {
    const r = runOnce(root, 'r1', [fetch], [c], skel,
      { question: '这个数字站得住吗?', frozen_at: '2026-08-18T00:00:00Z',
        counterSearches: { c1: autoQ(c) } })
    const sr = JSON.parse(readFileSync(join(root, 'claims', 'c1.status.json'), 'utf8'))
    status = sr.status
    if (process.env.DIAG) console.error(`\n[${id}] ${JSON.stringify(sr).slice(0, 700)}`)
    prose = r.prose.trim()
  } catch (e) { status = 'REJECTED'; prose = e.message.slice(0, 80) }
  finally { rmSync(root, { recursive: true, force: true }) }
  results.push({ id, should, predicted, desc, status, prose })
}

console.log('留出集二 · 八条 GWAS claim（未参与过任何修复）\n')
console.log('期望与预测写于运行之前，见 tests/holdout2/PREDICTIONS.md\n')
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
