#!/usr/bin/env node
// 段落选择门（GC-0：离线、确定性、零模型、零网络）
//
// 〔它守什么〕段落选择是成本优化的主要落点（读全文占总成本 45%），
// 而它的失效方式是**隐形的**：选窄了不会判错，会「根本没看见」——
// 表现为 not_covered，看起来像诚实地说不知道。
// **一个因为省钱而说不知道的系统，比一个贵的系统坏得多。**
//
// 因此本门的主断言不是「省了多少」，是**召回率下界**：
// 已知承载数值结论的段落，选完之后必须还在。省了多少是副产品，不是目标。
//
// 夹具：Jumper et al., Nature 596 (2021), PMC8371605 完整 JATS，**CC BY 4.0**。
// 50 个可寻址段，其中 25 个含数值结论。
//
// 〔问题从哪来 —— 这一条决定了这个召回率算不算数〕
// 问题**只由节标题生成**，不由目标段自己的措辞生成。
// 若用目标段的词去问，选中它是必然的，那个召回率是循环的、没有意义。
// 节标题是文档级元数据，与某一段的具体措辞独立。
//
// 用法:  node gates/check_passage_select.mjs
// 退出码: 0 = 召回达标且确有节省，1 = 否

import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { passagesFromJats } from '../packages/dsh-academic-fetch/lib/structured.js'
import { selectPassages, savingOf } from '../src/passage-select.mjs'

const ROOT = fileURLToPath(new URL('..', import.meta.url))
const JATS = readFileSync(join(ROOT, 'tests/external/snapshots/T6-alphafold-full-jats.xml'), 'utf8')
const ALL = passagesFromJats(JATS).filter(p => p.locator)
const NUMERIC = ALL.filter(p => /\d+\.\d+|\d+%/.test(p.text))

const RECALL_FLOOR = 1.0        // 数值段一个都不许丢
const SAVING_FLOOR = 0.30       // 省不到三成就不值得引入这一层的复杂度

let bad = 0
console.log('段落选择门\n')
console.log(`夹具：PMC8371605 完整 JATS（CC BY 4.0）—— ${ALL.length} 个可寻址段，其中 ${NUMERIC.length} 个含数值结论`)
console.log('问题只由**节标题**生成，不由目标段的措辞生成（否则召回率是循环的）\n')

const bySec = {}
for (const p of NUMERIC) (bySec[p.secTitle || '(无标题)'] ??= []).push(p)

let hit = 0, tot = 0, saveSum = 0, n = 0
console.log(`${'节'.padEnd(36)}${'数值段'.padEnd(8)}${'留住'.padEnd(6)}${'省'.padEnd(6)}`)
console.log('─'.repeat(72))
for (const [sec, list] of Object.entries(bySec)) {
  const sel = selectPassages(ALL, { question: sec, slots: [sec] })
  const kept = new Set(sel.kept.map(x => x.locator))
  const k = list.filter(p => kept.has(p.locator)).length
  hit += k; tot += list.length; saveSum += savingOf(sel); n++
  const ok = k === list.length
  if (!ok) bad++
  console.log(`${sec.slice(0, 34).padEnd(36)}${String(list.length).padEnd(8)}${String(k).padEnd(6)}` +
    `${(savingOf(sel) * 100).toFixed(0) + '%'}${ok ? '' : '   ← 丢了数值段'}`)
}

const recall = hit / tot, saving = saveSum / n
console.log('\n' + '─'.repeat(72))
console.log(`召回 ${hit}/${tot} = ${(recall * 100).toFixed(0)}%（下界 ${RECALL_FLOOR * 100}%）` +
  `   平均省 ${(saving * 100).toFixed(0)}%（下界 ${SAVING_FLOOR * 100}%）`)

if (recall < RECALL_FLOOR) { bad++; console.log(`FAIL  召回 ${(recall * 100).toFixed(0)}% 低于下界 —— 丢掉的证据不会判错，会隐形`) }
if (saving < SAVING_FLOOR) { bad++; console.log(`FAIL  只省 ${(saving * 100).toFixed(0)}% —— 不值得引入这一层的复杂度`) }

// ── 两条不得违反的性质 ────────────────────────────────────────────────
{
  // ① 无查询词时**返回全部**，不假装选过。
  //    悄悄选一个子集比不选更坏：调用方会以为它拿到的是筛过的。
  const none = selectPassages(ALL, {})
  if (none.kept.length !== ALL.length) { bad++; console.log('FAIL  无查询词时没有返回全部（悄悄筛过 = 调用方被骗）') }
  else console.log('PASS  无查询词 → 返回全部，并注明未做筛选')

  // ② dropped 必须被报出来，且与 kept 互补无重叠
  const sel = selectPassages(ALL, { question: 'backbone accuracy', slots: ['r.m.s.d'] })
  const kl = new Set(sel.kept.map(p => p.locator)), dl = new Set(sel.dropped.map(p => p.locator))
  const overlap = [...kl].filter(x => dl.has(x))
  if (kl.size + dl.size !== ALL.length || overlap.length) {
    bad++; console.log(`FAIL  kept/dropped 不构成划分（kept ${kl.size} + dropped ${dl.size} ≠ ${ALL.length}，重叠 ${overlap.length}）`)
  } else console.log('PASS  kept 与 dropped 构成划分，丢掉了什么是可查的')
}

console.log()
console.log('〔本门守不住什么〕它量的是**数值段**的召回。')
console.log('  一条结论若只以文字表述、不带数字（「显著优于基线」），本门看不见它被丢掉。')
console.log('  那类结论在本系统里本来也拿不到 ST-V（载荷不是数值），但它能支撑 K-L-A，')
console.log('  所以这是一个真实的、未覆盖的缺口，不是「不适用」。')
console.log()
if (bad) { console.log(`FAIL  ${bad} 处不符`); process.exit(1) }
console.log(`PASS  段落选择：${Object.keys(bySec).length} 个节，数值段召回 ${(recall * 100).toFixed(0)}%，平均省 ${(saving * 100).toFixed(0)}%`)
