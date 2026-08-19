#!/usr/bin/env node
/**
 * 基线对照 —— 本项目第一次有对照组。
 *
 * 〔为什么必须有〕此前所有「我们做得好」的说法都建立在
 * 「我们的判定与人工标签一致」上。那只说明**我们没错**，
 * 不说明**别的做法会错**。没有对照组，「更好」这个词没有内容。
 *
 * 三条基线，都是真实世界里在用的做法：
 *
 *   B0 照单全收 —— agent 说什么就是什么。
 *      现实对应：没有验证层的 RAG / 研究助手，模型说「已核实」就写「已核实」。
 *
 *   B1 引语在原文里 —— 逐字引语能在源文档里找到即算数。
 *      现实对应：**绝大多数引文核验工具的判据**。它挡住的是凭空捏造，
 *      挡不住任何「引对了句子、取错了数」的情形。
 *
 *   B2 引语在原文 + 载荷在引语里 —— B1 再加一条包含检验。
 *      现实对应：比较用心的实现。它是本项目 L1-b 的**单合取项**版本，
 *      也就是 R3 之前我们自己的样子。
 *
 * 判据是同一份专家标签（tests/external/cases.mjs 的 expect），
 * 同一批 21 条真实 claim。**把 verified/attributed 都算作「采信」**，
 * unverified/not_covered 算作「不采信」——基线给不出六值状态，
 * 只能二分，所以对照也必须在二分上做，否则是拿我们的粒度去要求它们。
 */
import { SRC, sentenceWith, fetchOf, runOnce, structuredDoc } from './run.mjs'

const norm = s => String(s ?? '').normalize('NFKC').replace(/\s+/g, ' ').trim()

/** 三条基线的判定函数：给一条证据 + 一条 claim，返回「采信 / 不采信」 */
const BASELINES = {
  'B0 照单全收': () => true,
  'B1 引语在原文里': (ev) => norm(ev.body).includes(norm(ev.quote)),
  'B2 引语在原文 + 载荷在引语里': (ev, claim) =>
    norm(ev.body).includes(norm(ev.quote)) &&
    Object.values(claim.payload ?? {}).every(v => norm(ev.quote).includes(norm(v))),
}

export { BASELINES, norm }

// ── 跑对照 ────────────────────────────────────────────────────────────
// 复用 cases.mjs 的 21 条用例与它们的专家标签。
const { results } = await import('./cases.mjs')

/** 我们的状态 → 二分。verified/attributed = 采信；其余 = 不采信。 */
const believed = st => st === 'verified' || st === 'attributed'

const rows = results.map(r => {
  const ev = r.fetches[0] ?? {}
  const truth = believed(r.expect)          // 专家标签（二分）
  const ours = believed(r.status)
  const base = Object.fromEntries(Object.entries(BASELINES)
    .map(([k, fn]) => { try { return [k, fn(ev, r.claim)] } catch { return [k, false] } }))
  return { id: r.id, desc: r.desc, truth, ours, base }
})

const NAMES = ['本系统', ...Object.keys(BASELINES)]
const verdictOf = (row, name) => name === '本系统' ? row.ours : row.base[name]

console.log('基线对照 —— 同一批 21 条真实 claim，同一份专家标签\n')
console.log('判据：verified/attributed = 采信；unverified/not_covered = 不采信。')
console.log('基线给不出六值状态，只能二分，所以对照也在二分上做。\n')

// 逐条
console.log(`${'用例'.padEnd(7)}${'真值'.padEnd(7)}${NAMES.map(n => n.padEnd(16)).join('')}说明`)
console.log('─'.repeat(112))
for (const r of rows) {
  const cells = NAMES.map(n => {
    const v = verdictOf(r, n)
    return ((v === r.truth ? '  ' : '✗ ') + (v ? '采信' : '不采信')).padEnd(16)
  })
  console.log(`${r.id.padEnd(7)}${(r.truth ? '采信' : '不采信').padEnd(7)}${cells.join('')}${r.desc.slice(0, 26)}`)
}

// 汇总
console.log('\n汇总')
console.log('─'.repeat(112))
console.log(`${'做法'.padEnd(30)}${'一致'.padEnd(8)}${'假阳'.padEnd(8)}${'假阴'.padEnd(8)}说明`)
const summary = {}
for (const n of NAMES) {
  let agree = 0, fp = 0, fn = 0
  for (const r of rows) {
    const v = verdictOf(r, n)
    if (v === r.truth) agree++
    else if (v && !r.truth) fp++
    else fn++
  }
  summary[n] = { agree, fp, fn }
  const note = fp > 0 ? `${fp} 条**不该采信却采信了**` : (fn > 0 ? `${fn} 条该采信却拦了` : '无错')
  console.log(`${n.padEnd(30)}${`${agree}/${rows.length}`.padEnd(8)}${String(fp).padEnd(8)}${String(fn).padEnd(8)}${note}`)
}

// 每条基线各漏了什么 —— 这比一个百分比有用
console.log('\n各基线放走了什么（假阳逐条）')
console.log('─'.repeat(112))
for (const n of NAMES.slice(1)) {
  const missed = rows.filter(r => verdictOf(r, n) && !r.truth)
  if (!missed.length) { console.log(`${n}：无`); continue }
  console.log(`${n}（${missed.length} 条）：`)
  for (const m of missed) console.log(`    ${m.id}  ${m.desc}`)
}

// 假阴也要逐条 —— 只报假阳会让「更严格 = 更好」这个错误结论看起来成立
console.log('\n各基线误拦了什么（假阴逐条）')
console.log('─'.repeat(112))
for (const n of NAMES.slice(1)) {
  const wrong = rows.filter(r => !verdictOf(r, n) && r.truth)
  if (!wrong.length) { console.log(`${n}：无`); continue }
  console.log(`${n}（${wrong.length} 条）：`)
  for (const m of wrong) console.log(`    ${m.id}  ${m.desc}`)
}

console.log('\n最值得看的一行')
console.log('─'.repeat(112))
const b0 = summary['B0 照单全收'].agree, b1 = summary['B1 引语在原文里'].agree
console.log(`「引语在原文里」是**绝大多数引文核验工具的判据**，它在这 21 条上是 ${b1}/${rows.length}，`)
console.log(`而「照单全收」是 ${b0}/${rows.length} —— 只多对 ${b1 - b0} 条。`)
console.log('原因不神秘：**真实文献里的错误不是凭空捏造引语，是引对了句子、取错了数**。')
console.log('捏造引语很容易挡，也很少发生；难挡的是每一个字都属实的误读。')

console.log('\n〔这份对照证明什么、不证明什么〕')
console.log('  证明：在这 21 条上，三条常见做法各会放走哪些错误，我们不会。')
console.log('  **不证明「我们是最好的」**——理由三条，都要说：')
console.log('    ① 用例是我们选的，且部分正是为展示我们处理的失效模式而选；')
console.log('    ② 标签是我们打的（外部语料解决了句子来源，没解决标签来源）；')
console.log('    ③ 没有跟任何**真实系统**比过（Elicit / Consensus / Scite / 各家深研）。')
console.log('  基线是「做法」，不是「产品」。跟产品比要用它们的真实输出，本项目还没做过。')
console.log()
console.log('  ④ **最要紧的一条**：我们的 21/21 有相当一部分是「修到符合标签为止」的结果——')
console.log('     这一轮里 T2-1/T2-2/T2-4/T3-3/T3-4 都是先判错、再改代码改到判对的。')
console.log('     基线没有受过这个待遇，它们是固定算法，一次都没为这批用例调过。')
console.log('     所以两侧的数字**可信度不对等**：')
console.log('       · 基线那几列是硬的 —— 「B1 会放走 T1-1」这件事与我们调不调无关；')
console.log('       · 我们那一列是软的 —— 它同时包含「设计对了」和「拟合了这批题」。')
console.log('     要把我们那一列变硬，需要一批**没参与过修复的**用例。本轮没有。')

const ours = summary['本系统']
process.exit(ours.agree === rows.length ? 0 : 1)
