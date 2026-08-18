#!/usr/bin/env node
/**
 * 编排层门（GC-0）—— 超大并行多 loop 论据探索。
 *
 * 它守三件事：
 *   ① **下一步由 status 的 trace 查表决定，不由模型判断**
 *      （§1.5 的 trace 里写着卡在哪一步，补什么是查表）
 *   ② **调度可复现**：同一批输入两次运行得到逐字节相同的探索路径
 *      （调度顺序由 thread id 排序决定，不由完成时刻决定）
 *   ③ **预算是硬闸**：耗尽时未完成的一律落 ST-N，不是「尽力而为」
 */
import { fileURLToPath } from 'node:url'
import { join } from 'node:path'
const rootArg = process.argv.indexOf('--root')
const ROOT = rootArg > -1 ? process.argv[rootArg + 1] : fileURLToPath(new URL('..', import.meta.url))
const { exploreParallel, diagnose } = await import(join(ROOT, 'src/orchestrator.mjs'))

let failed = 0
const fail = m => { failed++; console.log(`FAIL  ${m}`) }
console.log('编排层门\n')

// ── ① 诊断表：§1.5 的每一个否决/降档步都要有 remedy ────────────────────
const STEPS = ['0-required', '0-domain', '0a', '0b', '0c', '0d', '0e', '0f', '0g',
               '2a', '2b', '2c', '2d', "2d'", '2e']
const noRemedy = STEPS.filter(s => diagnose({ trace: [`${s} → x`] }).remedy === 'none')
if (noRemedy.length) fail(`§1.5 的这些步没有 remedy：${noRemedy.join('、')} —— 卡在那里的线无处可去`)
else console.log(`PASS  §1.5 的 ${STEPS.length} 个否决/降档步全部有查表得到的 remedy`)
// escalate 必须只给真的该升级的（污染 / 预算 / 一致性断裂）
const esc = STEPS.filter(s => diagnose({ trace: [`${s} → x`] }).escalate)
if (!esc.includes('0b') || !esc.includes('0f')) fail('污染(0b)与预算耗尽(0f)必须升级')
else console.log(`PASS  升级项恰为 ${esc.join('、')}（污染 / 预算 / flag 一致性断裂）`)

const S = (st, tr) => ({ status: st, trace: [tr] })
const mk = (id, seq) => ({ id, explore: async r => seq[Math.min(r - 1, seq.length - 1)] })
const THREADS = () => [
  mk('t2', [S('unverified', '2b → unverified'), S('verified', '2c verified')]),
  mk('t1', [S('not_covered', '0e → not_covered')]),
  mk('t3', [S('contested', '2a → contested')]),
]

// ── ② 调度必须可复现 ─────────────────────────────────────────────────
const a = await exploreParallel(THREADS(), { maxRounds: 4, maxConcurrent: 2 })
const b = await exploreParallel(THREADS(), { maxRounds: 4, maxConcurrent: 2 })
if (JSON.stringify(a.log) !== JSON.stringify(b.log)) {
  fail('同一批输入两次运行的探索日志不同 —— 调度不可复现，整个 run 无法复核')
} else console.log(`PASS  调度可复现（两次运行的 ${a.log.length} 条日志逐字节相同）`)
// 并发度不同也必须得到相同的**结果**（并发只影响速度，不影响判定）
const c = await exploreParallel(THREADS(), { maxRounds: 4, maxConcurrent: 1 })
if (JSON.stringify(a.results) !== JSON.stringify(c.results)) {
  fail('并发度不同导致结果不同 —— 判定被调度影响了')
} else console.log('PASS  并发度 2 与 1 得到相同结果（并发只影响速度，不影响判定）')

// ── ③ 终态与停滞 ──────────────────────────────────────────────────────
if (a.results.t2.status !== 'verified') fail(`t2 应在第 2 轮转 verified，实测 ${a.results.t2.status}`)
if (a.results.t3.status !== 'contested') fail('t3 应在第 1 轮即终态 contested')
const t1Rounds = a.log.filter(l => l.thread === 't1').length
if (t1Rounds > 3) fail(`t1 一直卡在 0e 却跑了 ${t1Rounds} 轮 —— 停滞检测失效，会烧光预算`)
else console.log(`PASS  停滞线在 ${t1Rounds} 轮后停止（连续无状态提升 → 停）`)

// ── ④ 预算是硬闸 ─────────────────────────────────────────────────────
const d = await exploreParallel(THREADS(), { maxRounds: 9, maxConcurrent: 3, budget: 2 })
const starved = Object.values(d.results).filter(r => r?.reason === 'budget-exhausted')
if (!d.budgetExhausted) fail('预算给 2 却没有耗尽标记')
else if (!starved.length) fail('预算耗尽时未完成的线没有落 ST-N —— 「尽力而为」是不诚实的默认')
else console.log(`PASS  预算耗尽 → ${starved.length} 条未完成的线落 not_covered（不是尽力而为）`)

console.log()
if (failed) { console.log(`${failed} 处不一致`); process.exit(1) }
console.log('PASS  编排层：下一步查表得出、调度可复现、预算是硬闸')
