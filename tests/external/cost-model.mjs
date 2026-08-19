#!/usr/bin/env node
/**
 * 一次研究要花多少钱 —— 按本系统**实际的调用结构**核算。
 *
 * 〔口径 · 必须先说清楚，否则这个数字没有意义〕
 *
 * 这**不是**实跑账单。实跑账单要等真实 DSH 编排接上模型之后才有。
 * 这里做的是：把本系统已经确定下来的调用结构（哪些环节要调模型、
 * 每个环节吃多少上下文、产出多长）代入 2026-08-19 复核过的官方价目表。
 *
 * 因此它的误差来自**用量估计**，不来自价格。用量估计的依据逐条标在下面，
 * 凡是没有依据的地方写「假设」而不是写一个看起来精确的数。
 *
 * 三条已经**不是假设**的量（来自本仓库的实测工件）：
 *   · 一份 JATS 全文的纯文本渲染：**由本文件当场量**（见 FULLTEXT_TOK），
 *     不再写死。〔S21〕这里原先写「51 段 / 约 89K 字符 ⇒ 约 22K token」，
 *     两头都对不上：渲染后是 50 段 / 42,572 字符 = 10.6K token，
 *     原始 XML 才 177K 字符。占比最大的那一行**被高估了 2×**，
 *     而它高估的方向恰好是让这套设计显得更贵 —— 错误方向不总是对自己有利的。
 *   · 一条 claim 的证据卡 + status.json：约 1.2K 字符 ⇒ 约 0.3K token
 *   · 组稿骨架 + 成稿：19 条 claim 的那次运行产出约 2K 字符
 */
import { readFileSync } from 'node:fs'
import { CostLedger, PRICING, PRICING_VERIFIED_AT, estimateTokens } from '../../src/cost.mjs'
import { passagesFromJats } from '../../packages/dsh-academic-fetch/lib/structured.js'
import { selectPassages } from '../../src/passage-select.mjs'

const K = 1000
const fmt = n => n < 0.01 ? `$${n.toFixed(4)}` : `$${n.toFixed(2)}`

/**
 * 调用结构。每一行都标了**这个数从哪来**。
 * pro  = 需要判断的环节（提 claim、选证据、写骨架）
 * flash= 机械环节（抽句、拼 query、格式化）
 */
// ── 夹具实测（先量，再拿去填表；表里不留手写的 token 数）────────────────
const JATS = readFileSync(new URL('./snapshots/T6-alphafold-full-jats.xml', import.meta.url), 'utf8')
const ALL_P = passagesFromJats(JATS).filter(p2 => p2.locator)
const SECS = [...new Set(ALL_P.map(p2 => p2.secTitle).filter(Boolean))]
const FULLTEXT_TOK = estimateTokens(ALL_P.map(p2 => p2.text).join('\n\n'))
// 读一篇全文的输入 = 全文 + 提示词与已判定 claim 的上下文（后者按 2K 估，标为假设）
const PROMPT_OVERHEAD = 2 * 1024
const READ_IN = Math.round(FULLTEXT_TOK + PROMPT_OVERHEAD)

const STAGES = [
  { stage: '选题拆解',     model: 'deepseek-v4-pro',   calls: 1,
    inMiss: 2 * K, out: 2 * K, note: '一次；问题 → 论据线清单' },
  { stage: '检索与筛选',   model: 'deepseek-v4-flash', calls: 12,
    inMiss: 3 * K, out: 0.5 * K, note: '每条论据线 2 次 × 6 线；吃检索结果标题+摘要' },
  { stage: '读全文提 claim', model: 'deepseek-v4-pro', calls: 9,
    inMiss: READ_IN, inHit: 0, out: 1.5 * K,
    note: '★ 全文 token 当场实测（PMC8371605 渲染后）+ 2K 提示词开销（假设）' },
  { stage: '反证检索',     model: 'deepseek-v4-flash', calls: 21,
    inMiss: 1 * K, out: 0.3 * K, note: '每条 claim 一次；query 由槽拼出，上下文很小' },
  { stage: '读反证',       model: 'deepseek-v4-pro',   calls: 6,
    inMiss: READ_IN, out: 1 * K, note: '只对有反证命中的读；假设三分之一命中' },
  { stage: '推断链',       model: 'deepseek-v4-pro',   calls: 4,
    inMiss: 6 * K, out: 1.5 * K, note: 'K-I claim 的前提追溯' },
  { stage: '组稿',         model: 'deepseek-v4-pro',   calls: 2,
    inMiss: 8 * K, out: 3 * K, note: '骨架 + 一次返工；吃全部 claim 的 status' },
]

// 门与判定全部是 GC-0：确定性脚本，**零模型调用**。这一行是这套设计的成本结论。
const GATE_CALLS = 0

function run({ cacheRate, peak }) {
  const at = peak ? '2026-08-19T02:00:00Z' : '2026-08-19T12:00:00Z'
  const led = new CostLedger({ at })
  for (const s of STAGES) {
    for (let i = 0; i < s.calls; i++) {
      const totalIn = s.inMiss ?? 0
      led.record({
        model: s.model, stage: s.stage,
        inputCacheHit: Math.round(totalIn * cacheRate),
        inputCacheMiss: Math.round(totalIn * (1 - cacheRate)),
        output: s.out ?? 0,
      })
    }
  }
  return led
}

console.log('一次研究的成本核算')
console.log(`价目表核对日期：${PRICING_VERIFIED_AT}（USD / 1M tokens，离峰；峰时 ×2）\n`)
console.log('调用结构')
console.log('─'.repeat(96))
console.log(`${'阶段'.padEnd(14)}${'模型'.padEnd(20)}${'次'.padEnd(5)}${'入/次'.padEnd(9)}${'出/次'.padEnd(9)}依据`)
for (const s of STAGES) {
  console.log(`${s.stage.padEnd(14)}${s.model.padEnd(20)}${String(s.calls).padEnd(5)}` +
    `${((s.inMiss ?? 0) / K + 'K').padEnd(9)}${((s.out ?? 0) / K + 'K').padEnd(9)}${s.note}`)
}
console.log(`${'门与判定'.padEnd(14)}${'（无）'.padEnd(20)}${String(GATE_CALLS).padEnd(5)}${'—'.padEnd(9)}${'—'.padEnd(9)}` +
  'GC-0：确定性脚本，零模型调用')

const base = run({ cacheRate: 0, peak: false })
console.log(`\n总量：${base.calls.length} 次调用 / ${(base.totalTokens / 1e6).toFixed(2)}M token\n`)

console.log('四种情形')
console.log('─'.repeat(96))
console.log(`${'情形'.padEnd(28)}${'总额'.padEnd(12)}${'每条 claim'.padEnd(14)}说明`)
const CLAIMS = 21
for (const [why, o] of [
  ['离峰 · 无缓存',        { cacheRate: 0,    peak: false }],
  ['离峰 · 50% 前缀缓存',  { cacheRate: 0.5,  peak: false }],
  ['离峰 · 80% 前缀缓存',  { cacheRate: 0.8,  peak: false }],
  ['峰时 · 无缓存',        { cacheRate: 0,    peak: true  }],
]) {
  const l = run(o)
  console.log(`${why.padEnd(28)}${fmt(l.totalUsd).padEnd(12)}${fmt(l.totalUsd / CLAIMS).padEnd(14)}` +
    `${o.peak ? '峰时 = 离峰 ×2' : ''}`)
}

// ── 探索轮次：上面那张表是**下界**，不是实际 ──────────────────────────
// STAGES 假设每阶段只跑一轮。而 exploreParallel 的 maxRounds 默认 5、
// noProgressRounds 默认 2 —— 一条论据线拿不到证据会**继续探**，
// 这正是「超并行多 loop」的定义。把单轮的数当成一次研究的成本，
// 是把这个系统最贵的那部分（探索本身）算成了零。
console.log('\n探索轮次的影响（离峰 · 50% 缓存）')
console.log('─'.repeat(96))
console.log(`${'情形'.padEnd(34)}${'总额'.padEnd(12)}${'每条 claim'.padEnd(14)}说明`)
const SCEN = [
  ['1 轮（上表 · 理论下界）',        1.0, '每条线一次拿到证据，无返工'],
  ['平均 2.2 轮（半数线要二探）',    2.2, '一半的线第一轮没拿到可用证据'],
  ['平均 3.5 轮（探索型问题）',      3.5, '开放式问题；多数线要换检索式再探'],
  ['触顶 5 轮（最坏，含预算闸）',    5.0, 'maxRounds 打满'],
]
for (const [why, mult, note] of SCEN) {
  const l2 = run({ cacheRate: 0.5, peak: false })
  const usd = l2.totalUsd * mult
  console.log(`${why.padEnd(34)}${fmt(usd).padEnd(12)}${fmt(usd / CLAIMS).padEnd(14)}${note}`)
}
console.log('轮次乘数是**假设**，不是实测——真实分布要等编排层接上模型跑过才有。')
console.log('写成一张表而不是一个数，是因为这一项的不确定度**大于价格本身的量级**。')

console.log('\n分项（离峰 · 50% 缓存）')
console.log('─'.repeat(96))
const l = run({ cacheRate: 0.5, peak: false })
const st = l.byStage()
const total = l.totalUsd
for (const [k, v] of Object.entries(st).sort((a, b) => b[1].usd - a[1].usd)) {
  const bar = '█'.repeat(Math.round(v.usd / total * 40))
  console.log(`${k.padEnd(14)}${fmt(v.usd).padEnd(10)}${String(Math.round(v.usd / total * 100) + '%').padEnd(6)}${bar}`)
}

// ── 优化后：段落选择的实测效果 ────────────────────────────────────────
//
// 〔为什么这一段要现场跑，而不是抄一个常数〕
// 这里原本写的是 `const SELECT_SAVING = 0.50`，从 check_passage_select 的
// 输出里**手抄**过来。本仓库已经在这一类上栽过四次（PASS 行的自述数字）：
// 抄来的数字不会随被抄对象一起变，选择器一改，成本表就开始说谎，而且没有任何门会红。
// 现在它由**同一份真实 JATS 夹具当场跑出来**——选择器变了，这张表跟着变。
//
// 与门里同一条纪律：问题只由**节标题**生成，不由目标段的措辞生成。
let charsAll = 0, charsSel = 0
for (const sec of SECS) {
  const sel = selectPassages(ALL_P, { question: sec, slots: [sec] })
  charsAll += ALL_P.reduce((a, p2) => a + p2.text.length, 0)
  charsSel += sel.kept.reduce((a, p2) => a + p2.text.length, 0)
}
const SELECT_SAVING = 1 - charsSel / charsAll
const OPTIMIZED = STAGES.map(s2 => /读全文|读反证/.test(s2.stage)
  ? { ...s2, inMiss: Math.round((s2.inMiss - PROMPT_OVERHEAD) * (1 - SELECT_SAVING) + PROMPT_OVERHEAD) } : s2)

function runOpt({ cacheRate, peak }) {
  const at = peak ? '2026-08-19T02:00:00Z' : '2026-08-19T12:00:00Z'
  const led = new CostLedger({ at })
  for (const s2 of OPTIMIZED) for (let i = 0; i < s2.calls; i++) {
    const t = s2.inMiss ?? 0
    led.record({ model: s2.model, stage: s2.stage,
      inputCacheHit: Math.round(t * cacheRate), inputCacheMiss: Math.round(t * (1 - cacheRate)),
      output: s2.out ?? 0 })
  }
  return led
}
console.log('\n优化后（只送可寻址段落）')
console.log('─'.repeat(96))
console.log(`实测夹具：PMC8371605 完整 JATS，${ALL_P.length} 段 / ${SECS.length} 个节标题各问一次`)
console.log(`整篇渲染 ${(FULLTEXT_TOK / K).toFixed(1)}K token；选择后平均省 **${(SELECT_SAVING * 100).toFixed(0)}%** 正文`)
console.log(`（提示词开销 ${PROMPT_OVERHEAD / K}K 不参与压缩，所以按整次调用算省得少一些）`)
console.log('（此处两个数由本文件当场跑出，不是抄来的常数；召回率由 gates/check_passage_select.mjs 单独守）')
console.log(`${'情形'.padEnd(28)}${'优化前'.padEnd(12)}${'优化后'.padEnd(12)}${'降幅'.padEnd(8)}`)
for (const [why, o] of [
  ['离峰 · 无缓存', { cacheRate: 0, peak: false }],
  ['离峰 · 50% 前缀缓存', { cacheRate: 0.5, peak: false }],
  ['离峰 · 80% 前缀缓存', { cacheRate: 0.8, peak: false }],
]) {
  const a = run(o).totalUsd, b = runOpt(o).totalUsd
  console.log(`${why.padEnd(28)}${fmt(a).padEnd(12)}${fmt(b).padEnd(12)}${((1 - b / a) * 100).toFixed(0) + '%'}`)
}
console.log('降幅小于 50% 是对的：段落选择只作用于两个读全文的阶段，')
console.log('而输出 token 与其余阶段不受影响 —— **省的是输入，不是全部**。')

console.log('\n优化落点（按占比排序，不按好改排序）')
console.log('─'.repeat(96))
const top = Object.entries(st).sort((a, b) => b[1].usd - a[1].usd)[0]
console.log(`最大项是「${top[0]}」，占 ${Math.round(top[1].usd / total * 100)}%。`)
console.log(`它之所以大，是因为**每读一篇全文就吃 ${(READ_IN / K).toFixed(1)}K 输入**，而全文是不可压缩的证据本身。`)
console.log('三条可试的方向，代价各不相同：')
console.log('  ① 前缀缓存：同一篇被多条 claim 反复读时，第二次起走 cache hit（差 30×）')
console.log('  ② 只送**可寻址段落**而不是整篇：G5 本来就是逐段的，读全文是习惯不是需求')
console.log(`  ③ 用 flash 先筛段落、pro 只读候选段：把 ${(READ_IN / K).toFixed(1)}K 拆成 flash 全量 + pro 只读候选段`)
console.log('\n〔本文件不做的事〕它不宣称这是实跑账单。用量是估的，依据逐条标在上面；')
console.log('  价格不是估的，是 2026-08-19 对官方页复核的。两者的可信度不同，不能混着说。')
