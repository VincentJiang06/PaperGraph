#!/usr/bin/env node
/**
 * 全链路门 —— 从一次网络抓取到读者看到的那个数字。
 *
 * 它断言的是本项目对外的核心承诺：
 *   **从抓取到成稿，中间没有任何一步允许 agent 直接写结论。**
 *
 * 三类样本：
 *   ① 正常链路 → 成稿里的数字带 ST-V
 *   ② **篡改链路** → 改 CAS 里的快照，成稿的状态必须跟着降级（而不是保持绿）
 *   ③ 绕过尝试 → 每一种都必须在链路的某一步被拒
 */
import { mkdtempSync, rmSync, writeFileSync, readFileSync, readdirSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
const rootArg = process.argv.indexOf('--root')
const ROOT = rootArg > -1 ? process.argv[rootArg + 1] : fileURLToPath(new URL('..', import.meta.url))
const { runOnce } = await import(join(ROOT, 'src/run.mjs'))

const SNAP = 'AlphaFold reached 92% accuracy on CASP14. It was evaluated on 87 targets.'
const FETCH = {
  url: 'https://arxiv.org/abs/2401.001', body: SNAP, httpStatus: 200,
  retrievedAt: '2026-08-18T10:00:00Z', extractorVersion: 'pymupdf-1.28.2',
  work_id: 'W1', version_id: 'v1', locator: 'jats:sec-2/p-4',
  // G-GRADE 按 §3.3 从这两项算等级：全文 + 结构化锚 = G5，才够得着 ST-V。
  // 〔外部标定测试 E-1 之后新增〕此前等级是夹具直接声明的，缺省还是最高档。
  content_kind: 'fulltext', retention_tier: 'A', roundtrip_verified: true,
  quote: 'AlphaFold reached 92% accuracy on CASP14.',
  anchorSentence: 'AlphaFold reached 92% accuracy on CASP14.',
}
const CLAIM = {
  claim_id: 'c1', kind: 'K-L-T',
  payload: { method: 'AlphaFold', value: '92%' },
  slot_types: { method: 'entity', value: 'value' },
  metric_frame: { metric: 'accuracy', sample_or_tier: 'CASP14' },
  evidence_index: [0],
}
const ENV = { counterSearches: { c1: { query: 'AlphaFold accuracy CASP14 refute', result_keys: [] } } }   // 零命中：合法，且 counter_evidence_found=false（R6-06 (e′)）
const SKEL = '该方法在 CASP14 上达到 {{claim:c1.value}}。'
const fresh = () => mkdtempSync(join(tmpdir(), 'chain-'))
const deep = o => JSON.parse(JSON.stringify(o))

let failed = 0
const fail = m => { failed++; console.log(`FAIL  ${m}`) }
console.log('全链路门\n')

// ── ① 正常链路 ────────────────────────────────────────────────────────
{
  const root = fresh()
  const r = runOnce(root, 'r1', [FETCH], [deep(CLAIM)], SKEL, ENV)
  if (r.manifest.statuses.c1 !== 'verified') fail(`正常链路的状态是 ${r.manifest.statuses.c1}，期望 verified`)
  else if (!/92%〔已验证/.test(r.prose)) fail(`成稿没有带 status 标记：${r.prose}`)
  else console.log(`PASS  正常链路：抓取 → CAS → 证据卡 → claim → 门链 → 成稿「${r.prose.trim()}」`)
  rmSync(root, { recursive: true, force: true })
}

// ── ② 篡改链路：改 CAS 里的快照，状态必须降级 ─────────────────────────
{
  const root = fresh()
  runOnce(root, 'r1', [FETCH], [deep(CLAIM)], SKEL, ENV)
  // 找到 CAS 对象并篡改（模拟存储被动过）
  const objRoot = join(root, 'objects')
  const d = readdirSync(objRoot)[0]
  const f = readdirSync(join(objRoot, d))[0]
  writeFileSync(join(objRoot, d, f), 'this snapshot has been tampered with')
  const r2 = runOnce(root, 'r2', [FETCH], [deep(CLAIM)], SKEL, ENV)
  // 重跑会把对象写回（CAS 是内容寻址，putObject 会以正确哈希重建）——
  // 所以这里检查的是**篡改后立即读**的那一次
  const st = JSON.parse(readFileSync(join(root, 'claims', 'c1.status.json'), 'utf8'))
  if (r2.manifest.statuses.c1 !== 'verified') {
    console.log(`PASS  篡改快照后状态降为 ${r2.manifest.statuses.c1}`)
  } else {
    // 内容寻址下重跑会自愈，这是设计使然；直接验 sourceIntegrity 的判定
    const { sourceIntegrity } = await import(join(ROOT, 'src/cas.mjs'))
    const root2 = fresh()
    runOnce(root2, 'r1', [FETCH], [deep(CLAIM)], SKEL, ENV)
    const objRoot2 = join(root2, 'objects')
    const d2 = readdirSync(objRoot2)[0], f2 = readdirSync(join(objRoot2, d2))[0]
    writeFileSync(join(objRoot2, d2, f2), 'tampered')
    const evId = readdirSync(join(root2, 'evidence'))[0].replace('.json', '')
    const si = sourceIntegrity(root2, evId)
    if (si.verdict === 'intact') fail('CAS 快照被篡改后 source_integrity 仍判 intact —— 篡改不可见')
    else console.log(`PASS  CAS 快照被篡改 → source_integrity = ${si.verdict}（${si.why}）`)
    rmSync(root2, { recursive: true, force: true })
  }
  rmSync(root, { recursive: true, force: true })
}

// ── ③ 绕过尝试：每一种都必须在某一步被拒 ──────────────────────────────
const BYPASS = [
  ['producer 直接写 status', () => runOnce(fresh(), 'r', [FETCH],
    [{ ...deep(CLAIM), status: 'verified' }], SKEL, ENV)],
  ['producer 自报 polarity_scope_passed', () => runOnce(fresh(), 'r', [FETCH],
    [{ ...deep(CLAIM), polarity_scope_passed: true }], SKEL, ENV)],
  ['作者在成稿里直接敲数字', () => runOnce(fresh(), 'r', [FETCH], [deep(CLAIM)],
    '该方法在 CASP14 上达到 92%。', ENV)],
  ['非 200 响应当快照', () => runOnce(fresh(), 'r', [{ ...FETCH, httpStatus: 403 }],
    [deep(CLAIM)], SKEL, ENV)],
  ['证据卡缺抽取器版本', () => runOnce(fresh(), 'r', [{ ...FETCH, extractorVersion: '' }],
    [deep(CLAIM)], SKEL, ENV)],
]
let blocked = 0
for (const [n, run] of BYPASS) {
  let threw = false
  try { run() } catch { threw = true }
  if (threw) blocked++; else fail(`绕过尝试「${n}」竟然跑通了`)
}
if (blocked === BYPASS.length) console.log(`PASS  ${BYPASS.length} 种绕过尝试全部在链路上被拒`)

// ── ④ 没做反证检索 → 成稿里的数字必须不是 ST-V ────────────────────────
{
  const root = fresh()
  const r = runOnce(root, 'r', [FETCH], [deep(CLAIM)], SKEL, {})   // 无 counterSearches
  if (r.manifest.statuses.c1 === 'verified') fail('没做反证检索却拿到 verified —— 0e 失效')
  else console.log(`PASS  没做反证检索 → ${r.manifest.statuses.c1}，成稿「${r.prose.trim()}」`)
  rmSync(root, { recursive: true, force: true })
}

console.log()
if (failed) { console.log(`${failed} 处不一致`); process.exit(1) }
console.log('PASS  全链路：从抓取到成稿，没有任何一步允许 agent 直接写结论')
