#!/usr/bin/env node
/**
 * CAS 与证据卡门（GC-0）。
 *
 * 它守三件事，每一件都对应一类「看起来有证据、实际没有」的形态：
 *   ① 证据卡 id 的五个分量缺一不可 —— 少一个就会有两条不同的证据共用一个 id
 *   ② 证据卡不得指向不存在的快照（断链必须当场拒，不能留给下游发现）
 *   ③ `source_integrity` 由门算：引语不再是快照的子串即 mutated
 */
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
const rootArg = process.argv.indexOf('--root')
const ROOT = rootArg > -1 ? process.argv[rootArg + 1] : fileURLToPath(new URL('..', import.meta.url))
const { putObject, putEvidence, sourceIntegrity, evidenceId, sha256 } =
  await import(join(ROOT, 'src/cas.mjs'))

let failed = 0
const fail = m => { failed++; console.log(`FAIL  ${m}`) }
const ok = m => console.log(`PASS  ${m}`)
console.log('CAS 与证据卡门\n')

const store = mkdtempSync(join(tmpdir(), 'cas-gate-'))
const SNAP = 'AlphaFold reached 92% accuracy on CASP14. It was evaluated on 87 targets.'
const h = putObject(store, SNAP)
const BASE = { work_id: 'W1', version_id: 'v1', locator: 'p3:l12',
  quote: 'AlphaFold reached 92% accuracy on CASP14.',
  extractor_version: 'pymupdf-1.28.2', object_sha256: h }
const card = putEvidence(store, BASE)

// ① 五个分量各自必须影响 id
const dims = [['work_id', 'W2'], ['version_id', 'v3'], ['locator', 'p9:l1'],
              ['quote', 'It was evaluated on 87 targets.'], ['extractor_version', 'pdfplumber-0.11.10']]
const collide = dims.filter(([k, v]) => evidenceId({ ...BASE, [k]: v }) === card.evidence_id)
if (collide.length) fail(`证据卡 id 对 ${collide.map(([k]) => k).join('、')} 不敏感 —— 两条不同证据会共用一个 id`)
else ok(`证据卡 id 对全部 ${dims.length} 个分量敏感（work/version/locator/quote/extractor 各换一次都得到不同 id）`)

// 缺任一分量必须抛
for (const [k] of dims) {
  let threw = false
  try { evidenceId({ ...BASE, [k]: '' }) } catch { threw = true }
  if (!threw) fail(`缺 ${k} 时 evidenceId 没有抛 —— 缺分量的 id 是假的`)
}

// ② 断链必须当场拒
let denied = false
try { putEvidence(store, { ...BASE, object_sha256: 'f'.repeat(64) }) } catch { denied = true }
if (!denied) fail('证据卡指向不存在的快照竟然写成功了 —— 断链未被拒')
else ok('证据卡指向不存在的快照 → 当场拒绝')

// ③ source_integrity 四态
const cases = [
  ['intact', () => sourceIntegrity(store, card.evidence_id).verdict],
  ['not_covered', () => sourceIntegrity(store, 'a'.repeat(64)).verdict],
  ['mutated', () => {
    // 引语在卡里，但快照对象被换成不含该引语的内容
    const s2 = mkdtempSync(join(tmpdir(), 'cas-mut-'))
    const h2 = putObject(s2, SNAP)
    const c2 = putEvidence(s2, { ...BASE, object_sha256: h2 })
    writeFileSync(join(s2, 'objects', h2.slice(0, 2), h2), 'completely different content')
    return sourceIntegrity(s2, c2.evidence_id).verdict
  }],
]
for (const [want, run] of cases) {
  const got = run()
  if (got !== want) fail(`source_integrity 期望 ${want}，实测 ${got}`)
}
if (!failed) ok('source_integrity 的 intact / not_covered / mutated 三态判定正确')

// ── G-GRADE · 证据等级两侧标定（外部标定测试 E-1/E-2 之后新增） ─────────
// 〔为什么加在这里〕等级是 §3.4 的天花板，天花板错了，后面所有门都白做。
// 而它此前**没有任何门在算**：缺省 G5（最高档），多条证据取 max（最好那条）。
{
  const { gradeOfEvidence, gradeOfClaim } = await import(join(ROOT, 'src/gates/g-grade.mjs'))
  const B = 'AlphaFold reached 92% accuracy on CASP14.'
  const CASES = [
    ['无快照',          {},                                                              'G0'],
    ['引语不在正文',    { body: B, quote: '这句话不在正文里' },                          'G1'],
    ['只有题录',        { body: B, quote: B, content_kind: 'metadata' },                 'G2'],
    ['只有摘要',        { body: B, quote: B, content_kind: 'abstract' },                 'G3'],
    ['未声明 kind',     { body: B, quote: B },                                           'G3'],
    ['全文无稳定锚',    { body: B, quote: B, content_kind: 'fulltext', locator: 'p3:l12' }, 'G4'],
    ['全文+JATS 锚',    { body: B, quote: B, content_kind: 'fulltext', locator: 'jats:sec-2/p-4' }, 'G5'],
  ]
  let bad = 0
  for (const [why, f, want] of CASES) {
    const got = gradeOfEvidence(f)
    if (got !== want) { bad++; console.log(`FAIL  G-GRADE ${why}：期望 ${want}，实测 ${got}`) }
  }
  // 多条证据取**最坏**，不是最好 —— E-2 的回归
  const worst = gradeOfClaim([
    { fetch: { body: B, quote: B, content_kind: 'fulltext', locator: 'jats:x' } },   // G5
    { fetch: { body: B, quote: '不在正文里' } },                                      // G1
  ])
  if (worst !== 'G1') { bad++; console.log(`FAIL  G-GRADE 多条证据应取最坏值 G1，实测 ${worst}`) }
  // 未声明不得拿到最高档 —— E-1 的回归
  if (gradeOfEvidence({ body: B, quote: B }) === 'G5') { bad++; console.log('FAIL  未声明 content_kind 却拿到 G5（fail-open 复发）') }
  if (bad) { failed += bad } else {
    console.log(`PASS  G-GRADE ${CASES.length} 档全部符合；多条取最坏值；未声明不得拿最高档`)
  }
}

rmSync(store, { recursive: true, force: true })
console.log()
if (failed) { console.log(`${failed} 处不一致`); process.exit(1) }
console.log('PASS  CAS 与证据卡：id 五分量敏感、断链当场拒、source_integrity 由门算')

