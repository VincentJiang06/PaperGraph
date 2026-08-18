#!/usr/bin/env node
/**
 * 变异测试 —— 量化「S 的门到底抓不抓得住错的实现」。
 *
 * 〔为什么存在〕R3 fix-audit 对 1389 万向量穷举 oracle 的判词是：
 *   「对 status.mjs 做 10 个**单向抬高状态**的变异，9 个存活（oracle 全绿），
 *     其中包括把 flag→状态的整套机制删光。」
 *
 * 那是别人的断言。本门把它变成**我自己每次都会重新测出来的数字**：
 * 逐个注入语义变异，跑两道门，报各自的击杀率。
 *
 * 这是唯一能回答「绿灯值多少钱」的方法。一道从不判红的门与一道抓得住
 * 全部变异的门，在正常仓库上输出**完全一样**——只有变异体能把它们分开。
 *
 * ── 〔R4 判词，必须写在最前面〕本门自己曾是循环的 ─────────────────────
 * R4 逐条比对后指出：手写的 15 个变异体与 `check_status_spec` 的 33 条黄金用例
 * 是**同一个人按同一张清单写的一对一映射**（M-01↔GC-2、M-02↔0e、M-03↔必填字段……
 * 无一例外）。变异集只覆盖了黄金用例已经覆盖的分支，
 * **100% 因此是构造出来的，不是测出来的**。R4 用自建的独立变异集实测：击杀率 2/10 = 20%。
 *
 * 这正是整套攻击机制要防的相关性错误，而它发生在**专门用来度量辨别力的那道门里**。
 *
 * 修法：变异体按来源分三类，**分开报数**。手写那类不再单独引用其击杀率。
 *   ① hand   手写（与黄金用例同源，**打折看**）
 *   ② derived 由规范表机械派生（逐行取每张表的每一格，与黄金用例无共同作者路径）
 *   ③ external R4 独立攻击者构造的（不同上下文，不同人）
 *
 * 注意变异体全部是**单向抬高状态**或**抹掉约束**的：把 verified 改成
 * unverified 那种变异即使存活也无害。抬高状态才是产品意义上的假阳性。
 */
import { readFileSync, writeFileSync, mkdtempSync, rmSync, cpSync, mkdirSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { tmpdir } from 'node:os'
import { execFileSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const rootArg = process.argv.indexOf('--root')
const ROOT = rootArg > -1 ? process.argv[rootArg + 1] : fileURLToPath(new URL('..', import.meta.url))
const SRC = readFileSync(join(ROOT, 'src/status.mjs'), 'utf8')

// 每条：[编号, 说明, 原文, 替换文]
// 全部经过「原文必须在 src/status.mjs 中恰好出现一次」的校验——
// 匹配不到就是变异器自己坏了，那会让击杀率虚高。
const HAND = [
  ['M-01', '删掉 GC-2 上限（§6.1/V1.4：GC-2 永不得写 ST-V）',
   'if (c.mechanism_results.some(m => m?.gate_class === \'GC-2\')) {',
   'if (false && c.mechanism_results.some(m => m?.gate_class === \'GC-2\')) {'],

  ['M-02', '删掉 0e 反例检索否决（§7.2.3「逃不过的只有这一条」）',
   'if (c.counter_evidence_searched === false) return ret(\'0e\', ST.N)',
   'if (false) return ret(\'0e\', ST.N)'],

  ['M-03', '把必填字段检查改成 fail-open（§9.19 MISSING == FAIL）',
   'if (missing.length) {',
   'if (false && missing.length) {'],

  ['M-04', '删掉 K-L-T 锚点失败时的有效 kind 降级（洗白通道）',
   "effectiveKind = 'K-L-A'",
   "effectiveKind = 'K-L-T'"],

  ['M-05', '把 K-D 开放式也放行到 ST-V（§2.1 开放式永不可达 ST-V）',
   '? (c.question_frozen ? ST.V : ST.A)',
   '? ST.V'],

  ['M-06', '让 K-I 可达 ST-V（§2.3.1 K-I 永不可达 ST-V）',
   'base = c.inference_gate_passed ? ST.A : ST.U',
   'base = c.inference_gate_passed ? ST.V : ST.U'],

  ['M-07', '清空 ceiling flag 表（把 flag→状态机制删掉一半）',
   'const FLAG_CEILING = Object.freeze({',
   'const FLAG_CEILING = Object.freeze({} ) || Object.freeze({'],

  ['M-08', '清空 step-down flag 表（另一半）',
   'const FLAG_STEPDOWN = Object.freeze(new Set([',
   'const FLAG_STEPDOWN = Object.freeze(new Set()) || Object.freeze(new Set(['],

  ['M-09', '删掉 0b 污染否决（contaminated → 不再是 ST-C）',
   "if (si === 'contaminated') return ret('0b', ST.C)",
   "if (false) return ret('0b', ST.C)"],

  ['M-10', '删掉 2a 反例命中吸收态（counter_evidence_found 不再判 ST-C）',
   "if (c.counter_evidence_found === true) return ret('2a', ST.C)",
   "if (false) return ret('2a', ST.C)"],

  ['M-11', '删掉 0d 引语否决（quote_faithful=fail 不再判 ST-U）',
   "if (c.has_verbatim_quote && c.quote_faithful === 'fail') return ret('0d', ST.U)",
   'if (false) return ret(\'0d\', ST.U)'],

  ['M-12', '删掉 0f 预算耗尽否决',
   "if (c.budget_state === 'exhausted') return ret('0f', ST.N)",
   "if (false) return ret('0f', ST.N)"],

  ['M-13', '删掉 0g 决定性机制为空的否决',
   'if (!Array.isArray(c.mechanism_results) || c.mechanism_results.length === 0) return ret(\'0g\', ST.N)',
   'if (false) return ret(\'0g\', ST.N)'],

  ['M-14', '把 §3.5 图形读数强制 ST-E 删掉（数值来自像素却按普通证据判）',
   'if (c.chart_extracted) {',
   'if (false && c.chart_extracted) {'],

  ['M-16', '删掉 §7.2.5 flag ↔ 驱动字段一致性（15 个 flag 可裸置位）',
   'const driver = FLAG_DRIVER[f]',
   'const driver = null && FLAG_DRIVER[f]'],

  ['M-17', '删掉 §7.2.4 F-10 与 chart_extracted 的绑定（V7.2 当场落空）',
   "if (Array.isArray(c.flags) && c.flags.includes('F-10') !== (c.chart_extracted === true)) {",
   "if (false && c.flags.includes('F-10') !== (c.chart_extracted === true)) {"],

  ['M-18', '把 K-L-T 退回单合取项（去掉极性作用域检验 L1-c）',
   'if (c.anchor_containment_passed && c.polarity_scope_passed) {',
   'if (c.anchor_containment_passed) {'],

  ['M-15', '恒返回 verified（最粗暴的一条：任何门都必须抓住）',
   'export function S(c) {',
   'export function S(c) { if (globalThis.__MUT15) return { status: ST.V, trace: [] } ;'],
]

// ② 由规范表机械派生：逐格把上限抬到 ST-V / 把 K 降到 1。
// 生成规则是「对表的每一行做同一种抬高」，不挑分支，因此不可能只覆盖我已想到的地方。
// 〔关键〕必须跳过**退化变异体**：G5 的上限本来就是 ST-V，「抬到 ST-V」什么也没改；
// K(K-D) 与 K(K-L-T) 本来就是 1，「降到 1」同理。它们必然「存活」，
// 却不是门的洞——退化变异体**虚高分母，让门看起来比实际差**，
// 那是另一种形式的不诚实，和虚高击杀率一样要防。
const { GRADE_CEILING_EXPORT: GC, K_EXPORT: KK, FLAG_CEILING_EXPORT: FC, ST: STV } =
  await import(join(ROOT, 'src/status.mjs'))
const derived = []
const degenerate = []
for (const g of ['G5', 'G4', 'G3', 'G2', 'G1', 'G0']) {
  if (GC[g] === STV.V) { degenerate.push(`D-${g}（${g} 的上限本来就是 ST-V）`); continue }
  derived.push([`D-${g}`, `§3.4 ${g} 的上限抬到 ST-V`, `  ${g}: ST.`, `  ${g}: ST.V, //`])
}
for (const k of ['K-D', 'K-L-T', 'K-L-A', 'K-I']) {
  if (KK[k] === 1) { degenerate.push(`D-K-${k}（K(${k}) 本来就是 1）`); continue }
  derived.push([`D-K-${k}`, `§1.5.2 K(${k}) 降到 1`, `  '${k}': `, `  '${k}': 1, //`])
}
for (const f of ['F-13', 'F-12', 'F-03', 'F-04']) {
  if (FC[f] === STV.V) { degenerate.push(`D-${f}（${f} 的 ceiling 本来就是 ST-V）`); continue }
  derived.push([`D-${f}`, `§7.3 ${f} 的 ceiling 抬到 ST-V`, `  '${f}': ST.`, `  '${f}': ST.V, //`])
}
const DERIVED = derived.filter(([, , from]) => SRC.split(from).length - 1 === 1)

// ③ R4 独立攻击者构造的（不同上下文）。保留其原始编号以便追溯。
const EXTERNAL = [
  ['X-05', '§1.5.1.1 降一档(ST-E) 改为不降（R4 构造）',
   '    case ST.E: return ST.U', '    case ST.E: return ST.E'],
  ['X-07', '把 2e 的降档挪到 2c 之前（顺序变了，单调性不破）',
   "  if (c.budget_state === 'degraded')", "  if (false && c.budget_state === 'degraded')"],
]

const MUTANTS = [...HAND.map(m => ['hand', ...m]),
                 ...DERIVED.map(m => ['derived', ...m]),
                 ...EXTERNAL.map(m => ['external', ...m])]

const GATES = [
  ['规范符合性门 check_status_spec', 'gates/check_status_spec.mjs'],
  ['穷举 oracle  check_status_exhaustive', 'gates/check_status_exhaustive.mjs'],
]

const results = []
const tmp = mkdtempSync(join(tmpdir(), 'mutants-'))

for (const [origin, id, desc, from, to] of MUTANTS) {
  const n = SRC.split(from).length - 1
  if (n !== 1) {
    results.push({ origin, id, desc, broken: `变异锚点在 src/status.mjs 中出现 ${n} 次（应为 1 次）` })
    continue
  }
  const dir = join(tmp, id)
  mkdirSync(join(dir, 'src'), { recursive: true })
  mkdirSync(join(dir, 'gates'), { recursive: true })
  writeFileSync(join(dir, 'src/status.mjs'), SRC.replace(from, to))
  for (const f of ['check_status_spec.mjs', 'check_status_exhaustive.mjs'])
    cpSync(join(ROOT, 'gates', f), join(dir, 'gates', f))
  cpSync(join(ROOT, '01-CONTRACTS.md'), join(dir, '01-CONTRACTS.md'))
  if (id === 'M-15') writeFileSync(join(dir, 'src/status.mjs'),
    SRC.replace(from, to).replace('const trace = []', 'const trace = []; globalThis.__MUT15 = 1'))

  const killed = {}
  for (const [label, rel] of GATES) {
    let ok = true
    try {
      execFileSync('node', [join(dir, rel), '--root', dir, '--impl', join(dir, 'src/status.mjs')],
        { stdio: 'ignore', timeout: 300_000 })
    } catch { ok = false }
    killed[label] = !ok            // 门非零退出 = 抓住了这个变异体
  }
  results.push({ origin, id, desc, killed })
}
rmSync(tmp, { recursive: true, force: true })

console.log('S 的变异测试\n')
console.log(`注入 ${MUTANTS.length} 个**单向抬高状态 / 抹掉约束**的语义变异，看每道门抓住几个。`)
if (degenerate.length) {
  console.log(`已剔除 ${degenerate.length} 个**退化变异体**（改了文本没改语义，必然存活，会虚高分母）：`)
  for (const d of degenerate) console.log(`  · ${d}`)
}
console.log()

const broken = results.filter(r => r.broken)
if (broken.length) {
  console.log(`FAIL  ${broken.length} 个变异锚点失效（变异器自己坏了，击杀率会虚高）`)
  for (const r of broken) console.log(`      ${r.id}  ${r.broken}`)
  console.log()
}

const live = results.filter(r => r.killed)
const width = Math.max(...GATES.map(g => g[0].length))
console.log(`${'变异'.padEnd(6)} ${GATES.map(g => g[0].padEnd(width)).join(' ')}  说明`)
console.log('-'.repeat(76))
for (const r of live) {
  const cells = GATES.map(g => (r.killed[g[0]] ? '抓住' : '**存活**').padEnd(width))
  console.log(`${r.id.padEnd(6)} ${cells.join(' ')}  ${r.desc}`)
}

console.log()
const rates = {}
const ORIGINS = [
  ['hand',     '手写（与黄金用例同源，**打折看**）'],
  ['derived',  '规范表机械派生（独立）'],
  ['external', 'R4 独立攻击者构造（独立）'],
]
for (const [label] of GATES) {
  const k = live.filter(r => r.killed[label]).length
  rates[label] = { k, n: live.length }
  console.log(`${label}：合计击杀 ${k}/${live.length}（${(k / live.length * 100).toFixed(0)}%）`)
  for (const [o, oname] of ORIGINS) {
    const sub = live.filter(r => r.origin === o)
    if (!sub.length) continue
    const sk = sub.filter(r => r.killed[label]).length
    console.log(`    ${oname}：${sk}/${sub.length}`)
  }
}
console.log()
const indep = live.filter(r => r.origin !== 'hand')
const indepKilled = indep.filter(r => r.killed[GATES[0][0]]).length
console.log(`**唯一可引用的数字**：规范符合性门在**独立来源**变异体上的击杀率 ${indepKilled}/${indep.length}`)
console.log('（手写那部分与黄金用例同源，其击杀率不构成辨别力的证据 —— R4 判词。）')
console.log()

const specLabel = GATES[0][0]
const specKilled = rates[specLabel].k
const survivors = live.filter(r => !r.killed[specLabel])
if (survivors.length) {
  console.log(`FAIL  ${survivors.length} 个抬高状态的变异体在规范符合性门下存活`)
  for (const r of survivors) console.log(`      ${r.id}  ${r.desc}`)
  console.log('      每一个存活者都是一条**真实的假阳性通道**：错成这样，门也是绿的。')
} else {
  console.log(`PASS  规范符合性门抓住全部 ${specKilled} 个变异体`)
}
if (broken.length) console.log(`FAIL  ${broken.length} 个变异锚点失效 —— 变异器坏了，上面的击杀率不可信`)
process.exit(survivors.length || broken.length ? 1 : 0)
