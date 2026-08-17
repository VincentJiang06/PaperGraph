#!/usr/bin/env node
// 自述数字门（GC-0：离线、确定性、零模型、零网络）
//
// README 与各文档里那些描述**本仓库自身**的数字（行数、断言条数、语料规模、
// 核验表行数）必须与实际相符。它们最容易腐：改一次文档就全错，而没有人会去重数。
//
// 这道门的来历：一个独立审计发现 README 写「01-CONTRACTS 830 行 / 64 条可检验断言」，
// 实际是 1091 行 / 68 条；又写「46 个在落笔时当场纠正」，而 46 既不等于 §3.3 表的 37 行、
// 也不等于语料全库的 50 行 corrected —— 那是全项目唯一一个既无口径、又不匹配任何自算值的规模数。
//
// 一个以「数字落笔即验证」为卖点的项目，自己的自述数字对不上，是最伤的一类缺陷。
// 把它做成门，而不是改一次数字了事。
//
// 用法:  node gates/check_doc_metrics.mjs [--root <dir>] [--fix]
// 退出码: 0 = 全部对上，1 = 有不符

import { readFileSync, writeFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

const rootArg = process.argv.indexOf('--root')
const ROOT = rootArg > -1 ? process.argv[rootArg + 1] : fileURLToPath(new URL('..', import.meta.url))
const FIX = process.argv.includes('--fix')

const read = f => readFileSync(join(ROOT, f), 'utf8')
const lines = f => read(f).split('\n').length - 1

// ── 实测值 ──────────────────────────────────────────────────────────────
// 语料规模按「调研维度」计，不按「本仓库存了几个文件」计。
// 某些仓库刻意不收录部分语料（见 research/v2/EXCLUDED.md），
// 但规划文档里「26 份调研」这个数字描述的是**做过的调研**，不是**发布的文件**——两者不是一回事。
// 因此实测值 = 在场文件数 + 已声明排除数，且 EXCLUDED.md 自身不计入。
const present = readdirSync(join(ROOT, 'research/v2')).filter(f => f.endsWith('.md') && f !== 'EXCLUDED.md')
let declaredExcluded = 0
try {
  const d = read('research/v2/EXCLUDED.md')
  declaredExcluded = new Set([...d.matchAll(/`([A-Za-z0-9_.-]+\.md)`/g)].map(m => m[1])).size
} catch { /* 没有声明就是没有排除 */ }
const corpusFiles = { length: present.length + declaredExcluded, present: present.length, excluded: declaredExcluded }
const corpusLines = present.reduce((s, f) => s + read(join('research/v2', f)).split('\n').length - 1, 0)
const vIds = new Set([...read('01-CONTRACTS.md').matchAll(/\*\*V[0-9]+\.[0-9]+[a-z]?\*\*/g)].map(m => m[0])).size

const actual = {
  '00-PREMISE.md': lines('00-PREMISE.md'),
  '01-CONTRACTS.md': lines('01-CONTRACTS.md'),
  '02-ARCHITECTURE.md': lines('02-ARCHITECTURE.md'),
  '03-EVIDENCE-ENGINE.md': lines('03-EVIDENCE-ENGINE.md'),
  '04-ORCHESTRATION.md': lines('04-ORCHESTRATION.md'),
  '05-TESTING.md': lines('05-TESTING.md'),
  '06-SURVEY.md': lines('06-SURVEY.md'),
  '07-ATTACK-LEDGER.md': lines('07-ATTACK-LEDGER.md'),
}

const readme = read('README.md')
const problems = []
let fixed = readme

// 检查一：README 文档地图里每一行的「N 行」必须与实测相符
for (const [doc, n] of Object.entries(actual)) {
  // 匹配该文档所在表格行里的「<数字> 行」
  const rowRe = new RegExp(`^\\|\\s*\\[${doc.replace(/\./g, '\\.')}\\][^|]*\\|[^|]*\\|([^|]*)\\|`, 'm')
  const row = readme.match(rowRe)
  if (!row) { problems.push({ what: `README 文档地图缺 ${doc} 行`, want: '存在', got: '缺失' }); continue }
  const claimed = row[1].match(/(\d[\d,]*)\s*行/)
  if (!claimed) { problems.push({ what: `${doc} 的规模列没写行数`, want: `${n} 行`, got: row[1].trim() }); continue }
  const c = Number(claimed[1].replace(/,/g, ''))
  if (c !== n) {
    problems.push({ what: `README 写 ${doc}`, want: `${n} 行`, got: `${c} 行` })
    fixed = fixed.replace(row[0], row[0].replace(`${claimed[1]} 行`, `${n} 行`))
  }
}

// 检查二：可检验断言条数
const vClaim = readme.match(/(\d+)\s*条可检验断言/)
if (!vClaim) problems.push({ what: 'README 未声明可检验断言条数', want: `${vIds} 条`, got: '缺失' })
else if (Number(vClaim[1]) !== vIds) {
  problems.push({ what: 'README 写可检验断言', want: `${vIds} 条`, got: `${vClaim[1]} 条` })
  fixed = fixed.replace(vClaim[0], `${vIds} 条可检验断言`)
}

// 检查三：语料规模（文件数 + 行数），README 与 06-SURVEY 必须一致且都对
for (const [file, text] of [['README.md', readme], ['06-SURVEY.md', read('06-SURVEY.md')], ['01-CONTRACTS.md', read('01-CONTRACTS.md')]]) {
  for (const m of text.matchAll(/(\d+)\s*(?:份|个)\s*(?:调研文件|`?\.md`?\s*文件)/g)) {
    if (Number(m[1]) !== corpusFiles.length) {
      problems.push({ what: `${file} 写语料文件数`, want: `${corpusFiles.length}`, got: m[1] })
    }
  }
  for (const m of text.matchAll(/([\d,]{4,})\s*行/g)) {
    const n = Number(m[1].replace(/,/g, ''))
    // 只对「语料总行数」这个量级的数字做比对，避免误伤文档自身行数
    if (corpusFiles.excluded === 0 && Math.abs(n - corpusLines) > 0 && Math.abs(n - corpusLines) < 400 && n > 10000) {
      problems.push({ what: `${file} 写语料总行数`, want: `${corpusLines}`, got: String(n) })
    }
  }
}

// ── 报告 ────────────────────────────────────────────────────────────────
console.log('自述数字门\n')
console.log(`实测: 语料 ${corpusFiles.length} 维度（在场 ${corpusFiles.present} + 已声明排除 ${corpusFiles.excluded}）/ 在场 ${corpusLines} 行；01-CONTRACTS 可检验断言 ${vIds} 条`)
console.log(`      ${Object.entries(actual).map(([d, n]) => `${d.slice(0, 2)}=${n}`).join('  ')}\n`)

if (!problems.length) {
  console.log('PASS  README 与各文档的自述数字全部与实测相符')
  process.exit(0)
}

if (FIX) {
  writeFileSync(join(ROOT, 'README.md'), fixed)
  console.log(`已回填 README（${problems.length} 处）——请复查 diff 后再提交`)
  process.exit(0)
}

console.log(`FAIL  ${problems.length} 处自述数字与实测不符`)
for (const p of problems) console.log(`      ${p.what}: 实际 ${p.want}，文档写 ${p.got}`)
console.log('\n      修法: node gates/check_doc_metrics.mjs --fix （只回填 README 的行数与断言数，其余需人工核对口径）')
process.exit(1)
