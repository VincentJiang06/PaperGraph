#!/usr/bin/env node
// 结构化抓取门（GC-0：离线、确定性、零模型、零网络）
//
// 〔它守什么〕G5 的判据是**可独立重新寻址**，不是「locator 长得像结构化的」。
// 本门在真实文档上验这一对：`extractPassages` 与 `resolveLocator` 必须互逆，
// 且回指往返（locator → 段落 → 逐字含引语）成立。
//
// 夹具是 **CC BY 4.0** 的真实 JATS（Jumper et al., Nature 596, 2021, PMC8371605），
// 逐字取自 Europe PMC 的 `/PMC8371605/fullTextXML`，保留被引用的两个 <sec>。
// 用真实文档而不是合成 XML 是刻意的：合成夹具由我按自己对 JATS 的理解造，
// 而我的理解正是缺陷的来源（本轮已两次栽在这上面，见 §S15）。
//
// 用法:  node gates/check_structured_fetch.mjs
// 退出码: 0 = 全部符合，1 = 有不符

import { readFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { passagesFromJats, passagesFromArxivHtml, resolveLocator, verifyRoundTrip } from '../packages/dsh-academic-fetch/lib/structured.js'
import { fetchStructured, evidenceFrom } from '../packages/dsh-academic-fetch/lib/fetch-structured.js'
import { gradeOfEvidence } from '../src/gates/g-grade.mjs'

// 〔同步树抓到的〕原写作 `dirname(new URL('..'))` 再拼 `academic-research-plugin/…`——
// 把仓库目录名硬编码进了路径。在开发树（目录就叫这个名）能跑，
// 换成任何别的目录名（比如发布用的克隆）立刻 ENOENT。
// 路径必须相对**本文件**，不能相对目录名。
const ROOT = fileURLToPath(new URL('..', import.meta.url))
const JATS = readFileSync(join(ROOT, 'tests/external/snapshots/T5-alphafold-jats.xml'), 'utf8')
const QUOTE = 'AlphaFold structures had a median backbone accuracy of 0.96 Å r.m.s.d.95'

let bad = 0
const check = (why, cond, detail = '') => {
  if (cond) { console.log(`PASS  ${why}`) } else { bad++; console.log(`FAIL  ${why}${detail ? ' —— ' + detail : ''}`) }
}

console.log('结构化抓取门\n')
console.log('夹具：Jumper et al., Nature 596 (2021), PMC8371605 —— CC BY 4.0，逐字取自 Europe PMC fullTextXML\n')

// ── ① 解析：真实 JATS 抽出可寻址段落 ─────────────────────────────────
const ps = passagesFromJats(JATS)
const anchored = ps.filter(p => p.locator)
check(`真实 JATS 抽出 ${ps.length} 段，其中 ${anchored.length} 段可寻址`, anchored.length > 0)
check('locator 形态是 jats:<sec>/<par>', anchored.every(p => /^jats:\w+\/\w+$/.test(p.locator)),
  anchored.find(p => !/^jats:\w+\/\w+$/.test(p.locator))?.locator)

// ── ② 互逆：每个 locator 都能反查回同一段文本 ─────────────────────────
const notInverse = anchored.filter(p => resolveLocator(JATS, p.locator, 'jats') !== p.text)
check(`${anchored.length} 个 locator 全部可反查回同一段文本（解析与定位互逆）`,
  notInverse.length === 0, notInverse[0]?.locator)

// ── ③ 回指往返：四种情形 ─────────────────────────────────────────────
const hit = anchored.find(p => p.text.includes(QUOTE))
check('目标引语落在某个可寻址段落里', !!hit)
check('回指往返成立（正例）', verifyRoundTrip(JATS, hit.locator, QUOTE, 'jats').ok)
check('锚点指向别处 → 不成立',
  !verifyRoundTrip(JATS, anchored.find(p => p.locator !== hit.locator).locator, QUOTE, 'jats').ok)
check('锚点不存在 → 不成立', !verifyRoundTrip(JATS, 'jats:Sec99/Par99', QUOTE, 'jats').ok)
check('无锚（null）→ 不成立', !verifyRoundTrip(JATS, null, QUOTE, 'jats').ok)

// ── ④ 与 G-GRADE 接上：G5 只给回指往返成立的 ─────────────────────────
const doc = await fetchStructured({ source: 'europepmc', id: 'PMC8371605',
  http: async () => ({ status: 200, body: JATS }), now: '2026-08-19T00:00:00Z' })
const ev = evidenceFrom(doc, QUOTE)
check(`真实引语 → ${ev.locator} → G-GRADE 判 G5`, gradeOfEvidence(ev) === 'G5', gradeOfEvidence(ev))

const fake = evidenceFrom(doc, 'AlphaFold achieved a median GDT_TS of 92.4 in CASP14')
check('伪造引语 → 无可寻址段落 → 不得到 G5', gradeOfEvidence(fake) !== 'G5', gradeOfEvidence(fake))
check('伪造引语的 roundtrip_verified 缺席（而不是 false）', fake.roundtrip_verified === undefined)

// ★ 伪造 roundtrip_verified 能走多远？
// 〔本门纠正了我对自己已知边界的描述〕初稿写「抓取器撒谎则 G-GRADE 信它」，
// 并用「伪造引语 + 伪造 roundtrip」做样本 —— 结果它拿不到 G5，
// 因为 `body.includes(quote)` 那一关先把它拦在 G1。**这个洞比我写的窄。**
// 真正的洞要同时满足：引语**真的**在正文里，但 locator 指向别处。
const forgedFake = { ...fake, locator: hit.locator, roundtrip_verified: true }
check('伪造引语 + 伪造 roundtrip → 仍被 body.includes(quote) 拦在 G1',
  gradeOfEvidence(forgedFake) === 'G1', gradeOfEvidence(forgedFake))

const wrongAnchor = anchored.find(p => p.locator !== hit.locator).locator
const forgedReal = { ...ev, locator: wrongAnchor, roundtrip_verified: true }
check('〔已知边界〕真引语 + 错锚点 + 伪造 roundtrip → 拿到 G5。本门如实记录这个洞',
  gradeOfEvidence(forgedReal) === 'G5', gradeOfEvidence(forgedReal))

// ── ⑤ 快照正文是纯文本渲染，不是原始标记 ─────────────────────────────
check('快照 body 是纯文本渲染（下游门比对的是文本）', !/<\/?sec\b|<\/?p\b/.test(doc.body))
check('原始标记的哈希单独保留（raw_sha256）', /^[0-9a-f]{64}$/.test(doc.raw_sha256))
check('body 含目标引语（否则 G-GRADE 会判 G1）', doc.body.includes(QUOTE))

// ── ⑥ 不可寻址段落数必须被报出来 ─────────────────────────────────────
check('抓取结果报告不可寻址段落数（G5 是逐段的，不是逐文档的）',
  typeof doc.unaddressable === 'number')

// ── ⑦ arXiv 侧：锚点形态 ─────────────────────────────────────────────
const HTML = '<section id="S1"><p id="S1.p1">First paragraph text here.</p>' +
             '<p id="S1.p2">Second paragraph.</p></section>' +
             '<section id="S2"><p id="S2.p1">Another section paragraph.</p></section>'
const hs = passagesFromArxivHtml(HTML)
check(`arXiv HTML 抽出 ${hs.length} 段，锚点形如 html:#S1.p1`,
  hs.length === 3 && hs[0].locator === 'html:#S1.p1', JSON.stringify(hs.map(h => h.locator)))
check('arXiv 侧回指往返成立',
  verifyRoundTrip(HTML, 'html:#S2.p1', 'Another section paragraph', 'html').ok)

// ── ⑧ 抓取失败当场拒，不留半份工件 ───────────────────────────────────
for (const [why, res] of [['非 200', { status: 404, body: 'x' }], ['空响应', { status: 200, body: '  ' }]]) {
  let threw = false
  try { await fetchStructured({ source: 'europepmc', id: 'PMC1', http: async () => res }) } catch { threw = true }
  check(`${why} → 当场抛`, threw)
}
let badId = false
try { await fetchStructured({ source: 'arxiv', id: 'not-an-id', http: async () => ({ status: 200, body: 'x' }) }) } catch { badId = true }
check('id 形态不对 → 当场抛（不去网络上碰运气）', badId)

console.log()
console.log('〔已知边界 · 已收窄〕`roundtrip_verified` 由抓取器写，但它能骗到的范围有限：')
console.log('  引语不在正文里 → 被 body.includes(quote) 拦在 G1，伪造这个字段没用。')
console.log('  剩下的洞是「真引语 + 错锚点 + 伪造 roundtrip」：读者按 locator 去查会查到别的段落。')
console.log('  堵它需要门侧持有原始标记并自行重验 —— CAS 现在只存渲染文本，')
console.log('  那是一次存储层改动，本轮没做。上面第 ④ 组最后两条把这个洞钉在测试里。')
console.log()
if (bad) { console.log(`FAIL  ${bad} 处不符`); process.exit(1) }
console.log('PASS  结构化抓取：解析与定位互逆、回指往返四情形、G5 只给验过的、失败当场拒')
