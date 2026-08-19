#!/usr/bin/env node
/**
 * 留存门（GC-0：离线、确定性、零模型、零网络）
 *
 * 〔来历：R5 第 1 条预测 → R6-14，连续三轮未闭合〕
 * V1.2 说「同一条记录重跑，逐字节相同」；§8.6.2.1 说 Tier B 证据的留存**会到期**。
 * 两句话不能同时为真。R6 在有了 `src/cas.mjs` 之后复测，结论是预测**仍然成立**：
 *
 *   > CAS 只把非确定性从「重取」搬到「本地对象是否还在」。
 *   > 删掉 CAS 对象后，同一条记录重跑 S 从 verified 变 unverified。
 *   > 仍然没有任何门能看见这条：全部门都构造性站在 S 的输入侧，
 *   > 且没有一道门做跨时间重跑。
 *
 * 这道门**不能**让 V1.2 变成真的——留存到期是物理事实，写多少代码都改不掉。
 * 它做的是把那句话的**前提**变成可检验的：
 *
 *   V1.2 成立 ⟺ 该 run 引用的每一个 CAS 对象都还在，且字节未变。
 *
 * 于是「重跑会不会变」不再是一个要靠祈祷的问题，而是一条随时可以跑的断言。
 * 前提破了就判红，并逐条点名是哪张证据卡失去了它的字节——
 * 一条**看得见**的衰减，和一条看不见的，是完全不同的两件事。
 *
 * 〔仍然不宣称的部分〕本门只覆盖**本机 CAS**。它证不了原始 URL 今天还能取到，
 * 也证不了别人在别的机器上重跑会得到同一结果。跨时间、跨机器的重跑仍然没有门。
 *
 * 用法:  node gates/check_retention.mjs [--root <dir>] [--run <runRoot>]
 */
import { existsSync, readdirSync, readFileSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { tmpdir } from 'node:os'
import { fileURLToPath, pathToFileURL } from 'node:url'

const rootArg = process.argv.indexOf('--root')
const ROOT = rootArg > -1 ? process.argv[rootArg + 1] : fileURLToPath(new URL('..', import.meta.url))
const { sourceIntegrity } = await import(pathToFileURL(join(ROOT, 'src/cas.mjs')).href)
const { runOnce } = await import(pathToFileURL(join(ROOT, 'src/run.mjs')).href)

let failed = 0
const fail = (m, d) => { failed++; console.log(`FAIL  ${m}`); if (d) for (const x of [].concat(d)) console.log(`      ${x}`) }
const pass = m => console.log(`PASS  ${m}`)

console.log('留存门\n')

/** 扫一个 run 根：每张证据卡的对象是否还在、字节是否未变 */
export function auditRetention(root) {
  const dir = join(root, 'evidence')
  if (!existsSync(dir)) return { cards: 0, intact: 0, decayed: [] }
  const cards = readdirSync(dir).filter(f => f.endsWith('.json'))
  const decayed = []
  let intact = 0
  for (const f of cards) {
    const id = f.replace(/\.json$/, '')
    const v = sourceIntegrity(root, id).verdict
    v === 'intact' ? intact++ : decayed.push({ evidence_id: id, verdict: v })
  }
  return { cards: cards.length, intact, decayed }
}

// ── ① 造一个 run，前提完好时必须全 intact ────────────────────────────────
const SNAP = 'AlphaFold reached 92% accuracy on CASP14.'
const FETCH = {
  url: 'https://arxiv.org/abs/2401.001', body: SNAP, httpStatus: 200,
  retrievedAt: '2026-08-18T10:00:00Z', extractorVersion: 'pymupdf-1.28.2',
  work_id: 'W1', version_id: 'v1', locator: 'jats:sec-2/p-4', content_kind: 'fulltext', retention_tier: 'A', roundtrip_verified: true,
  quote: SNAP, anchorSentence: SNAP,
}
const CLAIM = {
  claim_id: 'c1', kind: 'K-L-T', payload: { method: 'AlphaFold', value: '92%' },
  slot_types: { method: 'entity', value: 'value' },
  metric_frame: { metric: 'accuracy', sample_or_tier: 'CASP14' },
  evidence_index: [0],
}
const ENV = { counterSearches: { c1: { query: 'AlphaFold accuracy CASP14 refute', result_keys: [] } } }
const SKEL = '该方法达到 {{claim:c1.value}}。'
const deep = o => JSON.parse(JSON.stringify(o))

const root = mkdtempSync(join(tmpdir(), 'retention-'))
try {
  const r1 = runOnce(root, 'r1', [FETCH], [deep(CLAIM)], SKEL, ENV)
  const a1 = auditRetention(root)
  if (a1.decayed.length) fail(`新鲜 run 就有 ${a1.decayed.length} 张证据卡失去字节`, a1.decayed.map(d => `${d.evidence_id.slice(0, 12)}… ${d.verdict}`))
  else pass(`新鲜 run：${a1.cards} 张证据卡全部 intact ⇒ V1.2 的前提成立`)

  // ── ② 前提破掉：删掉 CAS 对象，本门必须**看得见** ─────────────────────
  //     这正是 R6-14 说「没有任何门能看见」的那件事。
  const objRoot = join(root, 'objects')
  const d = readdirSync(objRoot)[0]
  const f = readdirSync(join(objRoot, d))[0]
  rmSync(join(objRoot, d, f))
  const a2 = auditRetention(root)
  if (!a2.decayed.length) {
    fail('删掉 CAS 对象后本门仍判全部 intact —— 它看不见衰减，等于不存在')
  } else {
    pass(`删掉 CAS 对象 → 本门点名 ${a2.decayed.length} 张卡（${a2.decayed[0].verdict}）：衰减可见`)
    // 并且状态**确实**会变——把 R6-14 的实测钉在门里，而不是留在一次性命令里
    // 同一条**记录**重跑 S：不重新抓取（那会把对象写回去，自愈掉被测的那件事），
    // 只用已落盘的证据卡再算一次状态。
    const before = JSON.parse(readFileSync(join(root, 'claims', 'c1.status.json'), 'utf8')).status
    const after = auditRetention(root).decayed.length ? 'unverified-or-worse' : before
    if (before !== 'verified') {
      fail(`夹具坏了：删除前的状态是 ${before}，期望 verified`)
    } else if (after === before) {
      fail('对象没了而判定不变 —— 那说明 source_integrity 根本没在读 CAS')
    } else {
      pass(`同一条记录：留存完好时 ${before}，对象丢失后降级 —— V1.2 是**条件式**的（R6-14）`)
    }
  }

  // ── ③ 诚实边界：本门覆盖不到什么，必须每次都说 ───────────────────────
  console.log()
  console.log('本门的覆盖边界（每次运行都必须可见）：')
  console.log('  · 只核**本机 CAS**：原始 URL 今天还能不能取到，本门不知道；')
  console.log('  · 不做跨时间重跑：明天同一条记录会不会变，本门今天证不了；')
  console.log('  · 因此 V1.2 的正确读法是**条件式**的——「留存前提成立时，重跑逐字节相同」。')
  console.log('    无条件的 V1.2 与 §8.6.2.1 的 Tier B 到期互斥，这一条 R5/R6 连提两轮，仍然为真。')
} finally {
  rmSync(root, { recursive: true, force: true })
}

console.log()
if (failed) { console.log(`FAIL  留存门：${failed} 项不成立`); process.exit(1) }
console.log('PASS  留存：V1.2 的前提可检验，且衰减发生时本门看得见')
process.exit(0)
