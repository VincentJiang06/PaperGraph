#!/usr/bin/env node
// 成本核算门（GC-0：离线、确定性、零模型、零网络）
//
// `src/cost.mjs` 里那张价目表是**自述数字**——本项目对自述数字的纪律是：
// 要么有门在每次运行时重算它，要么它就会腐。
//
// 本门做三件事：
//   ① 三条手算算例逐格比对（改任何一格价格都会红）
//   ② 峰时窗口的**边界**逐个时刻验（UTC 01/04/06/10 四个端点最容易写错）
//   ③ 归集口径：按阶段、按最终 status 分摊，两者之和必须等于总额
//
// 它守不住的是「官方改了价而我们没改表」—— 那需要人去看官网。
// 与本项目其余全部「外部真值」同一性质，写在这里以免被当成全覆盖。
//
// 用法:  node gates/check_cost.mjs
// 退出码: 0 = 全部符合，1 = 有不符

import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { execFileSync } from 'node:child_process'
import { PRICING, PRICING_VERIFIED_AT, PRICING_SOURCE, isPeak, costOf, CostLedger } from '../src/cost.mjs'

const ROOT = fileURLToPath(new URL('..', import.meta.url))

let bad = 0
const near = (a, b, eps = 1e-9) => Math.abs(a - b) < eps

console.log('成本核算门\n')
console.log(`价目表核对：${PRICING_VERIFIED_AT}  ${PRICING_SOURCE}\n`)

// ── ① 手算算例 ────────────────────────────────────────────────────────
// 每一条的期望值都是**手算**的，写在注释里，不是跑出来的。
const CASES = [
  ['pro 1M 输入(未命中) 离峰',
   { model: 'deepseek-v4-pro', inputCacheMiss: 1e6 },              0.66],   // 1 × 0.66
  ['pro 1M 输入(命中) 离峰',
   { model: 'deepseek-v4-pro', inputCacheHit: 1e6 },               0.022],  // 1 × 0.022
  ['pro 1M 输出 离峰',
   { model: 'deepseek-v4-pro', output: 1e6 },                      1.98],   // 1 × 1.98
  ['flash 1M 输入(未命中) 离峰',
   { model: 'deepseek-v4-flash', inputCacheMiss: 1e6 },            0.22],
  ['flash 1M 输出 离峰',
   { model: 'deepseek-v4-flash', output: 1e6 },                    0.66],
  ['pro 1M 输出 峰时（= 离峰 ×2）',
   { model: 'deepseek-v4-pro', output: 1e6, at: '2026-08-19T02:00:00Z' }, 3.96],
  ['混合：pro 200K 未命中 + 300K 命中 + 50K 输出，离峰',
   { model: 'deepseek-v4-pro', inputCacheMiss: 2e5, inputCacheHit: 3e5, output: 5e4 },
   0.2 * 0.66 + 0.3 * 0.022 + 0.05 * 1.98],                                  // = 0.132+0.0066+0.099
]
console.log(`${'算例'.padEnd(46)}${'实测'.padEnd(12)}${'手算'.padEnd(12)}`)
console.log('─'.repeat(84))
for (const [why, input, want] of CASES) {
  const got = costOf(input).usd
  const ok = near(got, want, 1e-9)
  if (!ok) bad++
  console.log(`${why.padEnd(46)}${got.toFixed(6).padEnd(12)}${want.toFixed(6).padEnd(12)}${ok ? '' : '  ← 不符'}`)
}

// ── ② 峰时窗口的边界 ─────────────────────────────────────────────────
// 官方：峰时 = UTC 01:00–04:00 与 06:00–10:00。四个端点最容易写错成闭区间。
const WINDOW = [
  ['00:59 离峰', '2026-08-19T00:59:00Z', false],
  ['01:00 峰时（左闭）', '2026-08-19T01:00:00Z', true],
  ['03:59 峰时', '2026-08-19T03:59:00Z', true],
  ['04:00 离峰（右开）', '2026-08-19T04:00:00Z', false],
  ['05:59 离峰', '2026-08-19T05:59:00Z', false],
  ['06:00 峰时（左闭）', '2026-08-19T06:00:00Z', true],
  ['09:59 峰时', '2026-08-19T09:59:00Z', true],
  ['10:00 离峰（右开）', '2026-08-19T10:00:00Z', false],
  ['23:00 离峰', '2026-08-19T23:00:00Z', false],
]
console.log('\n峰时窗口边界（UTC 01–04 与 06–10）')
console.log('─'.repeat(84))
for (const [why, at, want] of WINDOW) {
  const got = isPeak(at)
  if (got !== want) { bad++; console.log(`FAIL  ${why}：期望 ${want}，实测 ${got}`) }
}
console.log(`${WINDOW.length} 个端点全部符合`)

// ── ③ 归集口径：分项之和必须等于总额 ──────────────────────────────────
// 一张对不上总额的分项表，比没有分项表更坏：它看起来像审计过的。
{
  const led = new CostLedger({ at: '2026-08-19T12:00:00Z' })
  led.record({ model: 'deepseek-v4-pro',   inputCacheMiss: 2e4, output: 1e3, claimId: 'c1', stage: '读全文' })
  led.record({ model: 'deepseek-v4-pro',   inputCacheMiss: 2e4, output: 1e3, claimId: 'c2', stage: '读全文' })
  led.record({ model: 'deepseek-v4-flash', inputCacheMiss: 1e3, output: 3e2, claimId: 'c1', stage: '反证检索' })
  led.record({ model: 'deepseek-v4-pro',   inputCacheMiss: 8e3, output: 3e3,                 stage: '组稿' })

  const total = led.totalUsd
  const stageSum = Object.values(led.byStage()).reduce((s, v) => s + v.usd, 0)
  if (!near(stageSum, total, 1e-12)) { bad++; console.log(`FAIL  按阶段归集之和 ${stageSum} ≠ 总额 ${total}`) }

  const out = led.byOutcome({ c1: 'verified', c2: 'attributed' })
  const outSum = Object.values(out).reduce((s, v) => s + v.usd, 0)
  if (!near(outSum, total, 1e-12)) { bad++; console.log(`FAIL  按 status 归集之和 ${outSum} ≠ 总额 ${total}`) }

  // 无 claim 的调用（组稿）必须单列，不能被摊进某条 claim
  if (!out['(无 claim)']) { bad++; console.log('FAIL  无 claim 的调用没有单列 —— 它会被悄悄摊进某条 claim 的单价') }
  // 「每条 verified 的单价」是这套核算存在的理由，必须算得出来
  if (out.verified?.usdPerClaim == null) { bad++; console.log('FAIL  算不出每条 verified 的单价') }
  console.log('\n归集口径')
  console.log('─'.repeat(84))
  console.log(`总额 $${total.toFixed(6)}；按阶段之和 $${stageSum.toFixed(6)}；按 status 之和 $${outSum.toFixed(6)}`)
  console.log(`每条 verified $${out.verified.usdPerClaim.toFixed(6)} · 每条 attributed $${out.attributed.usdPerClaim.toFixed(6)}`)
}

// ── ④ 未知模型必须当场抛，不得静默按 0 计 ────────────────────────────
try {
  costOf({ model: 'gpt-9', output: 1e6 })
  bad++; console.log('\nFAIL  未知模型没有抛异常 —— 静默按 0 计会让一整类调用从账上消失')
} catch { /* 期望抛 */ }

// ── ⑤ 台账里的成本表必须与实测一致 ──────────────────────────────────
//
// 〔为什么要有这一条 · §S21〕成本模型现在从真实 JATS 夹具当场量，
// 但**台账 §S18 里那张表仍然是手抄的**。本仓库栽在「PASS 行的自述数字」上
// 已经五次：抄来的数字不随被抄对象一起变，而且没有任何门会红。
// 这一条把台账那张表接回实测：跑一次成本模型，把它打印的四种情形
// 与台账表里的数字逐格比。差一分钱就红。
{
  const modelOut = execFileSync(process.execPath,
    [join(ROOT, 'tests/external/cost-model.mjs')], { encoding: 'utf8' })
  const scen = {}
  // 情形名里本身含空格（「离峰 · 50% 前缀缓存」），所以按**两个以上空格**切列
  for (const m of modelOut.matchAll(/^((?:离峰|峰时) · .+?)\s{2,}\$([\d.]+)/gm)) {
    if (scen[m[1]] == null) scen[m[1]] = m[2]   // 只取首次出现（四种情形那张表）
  }
  const ledger = readFileSync(join(ROOT, '07-ATTACK-LEDGER.md'), 'utf8')
  const rows = [...ledger.matchAll(/^\|\s*(离峰 · [^|]+?|峰时 · [^|]+?)\s*\|\s*\*{0,2}\$([\d.]+)\*{0,2}\s*\|/gm)]
  if (!rows.length) { bad++; console.log('\nFAIL  台账里找不到成本表 —— 无法核对（表被改名或删了？）') }
  let checked = 0
  for (const [, name, val] of rows) {
    const want = scen[name.trim()]
    if (want == null) { bad++; console.log(`\nFAIL  台账写了情形「${name.trim()}」，但成本模型没有输出它`); continue }
    if (want !== val) {
      bad++
      console.log(`\nFAIL  台账「${name.trim()}」写 $${val}，成本模型实测 $${want} —— 台账已过期`)
    }
    checked++
  }
  if (checked) console.log(`\n台账成本表 ${checked} 格与实测逐格核对`)
}

console.log()
if (bad) { console.log(`FAIL  ${bad} 处不符`); process.exit(1) }
console.log(`PASS  台账成本表与实测一致；价目表 ${CASES.length} 条手算算例 + ${WINDOW.length} 个峰时端点 + 归集口径全部符合；未知模型当场抛`)
