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
console.log(`PASS  G-CLUSTER 标定集 ${CASES.length} 条（压塌侧 5 / 独立侧 3 / 低置信 1）全部符合`)
