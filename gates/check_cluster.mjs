#!/usr/bin/env node
/**
 * G-CLUSTER 标定门（GC-0）。
 *
 * 〔为什么两侧都要有样本〕R5 第 3 条预测把这块夹在两个失败之间：
 *   认真归并 ⇒ K-L-A 与 K-I 拿不到 2 簇 ⇒ 归因与推断两条通道再无绿灯；
 *   不认真   ⇒ K=2 名存实亡，合成共识防线拆了。
 * 只测一侧的标定集必然朝那一侧漂。因此下面**压塌侧**与**独立侧**各占一半。
 */
import { fileURLToPath } from 'node:url'
import { join } from 'node:path'
const rootArg = process.argv.indexOf('--root')
const ROOT = rootArg > -1 ? process.argv[rootArg + 1] : fileURLToPath(new URL('..', import.meta.url))
const { cluster } = await import(join(ROOT, 'src/gates/g-cluster.mjs'))

const media = n => Array.from({ length: n }, (_, i) => ({ work_id: 'M' + i, title: 'T' + i, upstream_id: 'nikkei-001' }))

// [id, refs, 期望独立簇数, 期望人审候选数, 说明]
const CASES = [
  // ── 压塌侧：这些**必须**被归成一簇，否则 K≥2 是纸面防线 ────────────────
  ['C-1', media(11), 1, 0, 'F-23 跨语言链：11 家中文媒体同一上游（项目记录的一手样本）'],
  ['C-2', [{ evidence_id: 'A', title: '原始' }, { evidence_id: 'B', title: '转引', cites_source_id: 'A' }], 1, 0,
   'F-02 转引链：B 自陈来源是 A'],
  ['C-3', [{ work_id: 'P1', title: 'a', self_cite_group: 'lab-x' }, { work_id: 'P2', title: 'b', self_cite_group: 'lab-x' }], 1, 0,
   'F-22 自证回路：同一作者组内部互引'],
  ['C-4', [{ arxiv_id: '2401.001v1', title: 'Same Paper', authors: ['x'] },
           { arxiv_id: '2401.001v3', title: 'Same Paper', authors: ['x'] },
           { doi: '10.1/xyz', title: 'Same Paper', authors: ['x'] }], 1, 0,
   '预印本 v1/v3 + 期刊三版同文（arXiv 版本号必须无关）'],
  ['C-5', [{ doi: '10.1/a', title: 'X' }, { doi: '10.1/A', title: 'X' }], 1, 0, 'DOI 大小写归一'],

  // ── 独立侧：这些**必须**保持多簇，否则归因/推断通道全灭 ─────────────────
  ['C-6', [{ work_id: 'W1', title: 'A', authors: ['x'] }, { work_id: 'W2', title: 'B', authors: ['y'] }], 2, 0,
   '两篇真独立'],
  ['C-7', [{ doi: '10.1/a', title: 'A', authors: ['x'] },
           { doi: '10.1/b', title: 'B', authors: ['y'] },
           { doi: '10.1/c', title: 'C', authors: ['z'] }], 3, 0, '三篇真独立'],
  ['C-8', [{ work_id: 'W1', title: 'A', lang: 'zh' }, { work_id: 'W2', title: 'B', lang: 'en' }], 2, 0,
   '**语言不同不代表不独立** —— 判据是自陈上游，不是语种'],

  // ── 低置信：只提议不执行 ──────────────────────────────────────────────
  ['C-9', [{ work_id: 'W1', title: 'Deep Learning for Protein Folding', authors: ['a'] },
           { work_id: 'W2', title: 'Deep Learning for Protein Folding Prediction', authors: ['b'] }], 2, 1,
   '标题高度相似 → **不合并**，进人审队列'],
]

let failed = 0
console.log('G-CLUSTER 标定门\n')
console.log(`${'用例'.padEnd(6)} ${'簇'.padEnd(5)} ${'期望'.padEnd(5)} ${'人审'.padEnd(5)} 说明`)
console.log('-'.repeat(84))
for (const [id, refs, want, wantCand, desc] of CASES) {
  const r = cluster(refs)
  const ok = r.independent_cluster_count === want && r.identity_merge_candidates.length === wantCand
  if (!ok) failed++
  console.log(`${id.padEnd(6)} ${String(r.independent_cluster_count).padEnd(5)} ${String(want).padEnd(5)} ` +
    `${String(r.identity_merge_candidates.length).padEnd(5)} ${desc}${ok ? '' : '   ← 偏离'}`)
}

// 诚实边界必须可见：没有自陈关系时本门看不见转引
// ── ⓪-b 近似归并 · 两侧标定（SA-5 第二步闭合） ────────────────────────
// ⓪ 只抓逐字节相同。真实转引链里二手来源几乎总会改一两个词，
// 一个字节之差哈希就分开，11 家转载又变成 11 个独立簇。
// 近似归并**可能错并**，所以独立侧的样本比压塌侧更要紧。
{
  const T = 'Researchers report that the new drug development cost is 2.6 billion dollars.'
  const NEAR = [
    ['C-N1', 1, [T, T + ' '], '★ 只差一个尾空格'],
    ['C-N2', 1, [T, T.replace('dollars.', 'dollars, reportedly.')], '★ 加了一个词的转载'],
    ['C-N3', 1, [T, T.replace('Researchers report', 'Researchers reported')], '★ 改了时态'],
    ['C-N4', 2, [T, 'A fresh estimate puts what it takes to bring a medicine to market at about 2.6bn.'],
     '★ 重写型转引 —— 抓不到（已认账，需要语义比对）'],
    ['C-N5', 2, ['The model reached 92% accuracy on CASP14.',
                 'A different team measured 61% accuracy on the same benchmark.'],
     '★ 真独立的两条：句式接近但内容不同，**不得错并**'],
    ['C-N6', 2, ['We evaluate on the CASP14 benchmark using standard protocols.',
                 'We evaluate on the CASP15 benchmark using standard protocols.'],
     '★★ 只差一个字符但是**不同的评测集** —— 近似归并最危险的假阳，必须分开'],
  ]
  for (const [id, want, texts, why] of NEAR) {
    const r = cluster(texts.map((t, i) => ({ evidence_id: `E${i}`, work_id: `W${i}`, anchor_sentence: t })))
    const ok = r.independent_cluster_count === want
    if (!ok) failed++
    console.log(`${id.padEnd(7)} ${String(r.independent_cluster_count).padEnd(4)} ${String(want).padEnd(4)} ${why}${ok ? '' : '   ← 偏离'}`)
  }
  // 近似归并必须在 applied_rules 里标 level:'near'，与确定性归并区分
  const r = cluster([{ evidence_id: 'E0', work_id: 'W0', anchor_sentence: T },
                     { evidence_id: 'E1', work_id: 'W1', anchor_sentence: T + ' ' }])
  const nearRules = r.applied_rules.filter(x => x.level === 'near')
  if (!nearRules.length) {
    failed++
    console.log("FAIL  近似归并没有标 level:'near' —— 可能错并的合并必须与确定性合并可区分")
  } else {
    console.log(`      近似归并已标记：${nearRules.map(x => x.rule).join(', ')}`)
  }
}

const opaque = cluster([{ work_id: 'W1', title: 'A' }, { work_id: 'W2', title: 'B' }])
console.log()
if (!opaque.knownLimitation) {
  failed++
  console.log('FAIL  「证据未自陈上游/转引/自证关系」这条已知边界没有被报出来')
} else {
  console.log(`已知未闭合（每次运行都必须可见）：${opaque.knownLimitation}`)
}

console.log()
if (failed) { console.log(`FAIL  ${failed} 条偏离`); process.exit(1) }
// 〔自纠〕这三个数原本是硬编码的，加了近似归并的 6 条之后就不准了。
console.log(`PASS  G-CLUSTER 标定集 ${CASES.length} 条 + 近似归并 6 条全部符合；近似合并与确定性合并可区分`)
