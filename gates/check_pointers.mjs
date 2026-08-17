#!/usr/bin/env node
// [E:] 溯源指针门（GC-0：离线、确定性、零模型、零网络）
//
// 这道门的来历值得记下来：check_contracts.mjs 里原本有一条 D-1「指针格式可解析」，
// 它只检查了指针**非空**。一个独立审计上下文指出它是空心的——
// `[E: 我瞎编的.md#根本不存在的锚]` 能过，而且它只跑 01-CONTRACTS 一份文档，
// 另外 6 份的 870 个指针完全不在任何门的覆盖内。
// 在一个以「空心门是头号失败模式」为论点的项目里造出一道空心门，
// 是这轮最该被记住的一条教训。本文件是它的替代。
//
// ── 为什么用棘轮而不是直接判红 ────────────────────────────────────
// 落地时已存在约 50 条不可解析指针。让门立刻判红会造出一道**永红的门**，
// 而永红的门在两周内一定会被 `|| true` 掉——那等于回到空心门，只是更难发现。
// 所以：已知欠债登记在 .attack/pointer-debt.json，门断言两个方向——
//   ① 出现登记外的新不可解析指针 → 红（不可变坏）
//   ② 登记的欠债现在能解析了却没删 → 红（还清了要销账，否则登记表本身会腐）
// 欠债数只能下降。这不是放水，是把「现状」与「不可回退」分开管理。
//
// 用法:  node gates/check_pointers.mjs [--list-unresolved] [--update-debt]
// 退出码: 0 = 通过，1 = 有阻塞项

import { readFileSync, existsSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

// --root <dir> 让负例套件能在临时副本上跑，而不必改真实文件。
// 一道不能在副本上被测试的门，其负例套件必然要动真文件——那本身就是风险。
const rootArg = process.argv.indexOf('--root')
const ROOT = rootArg > -1 ? process.argv[rootArg + 1] : fileURLToPath(new URL('..', import.meta.url))
const CORPUS = join(ROOT, 'research/v2')
const DEBT_FILE = join(ROOT, '.attack/pointer-debt.json')

const PLAN_DOCS = [
  'README.md', '00-PREMISE.md', '01-CONTRACTS.md', '02-ARCHITECTURE.md',
  '03-EVIDENCE-ENGINE.md', '04-ORCHESTRATION.md', '05-TESTING.md',
  '06-SURVEY.md', '07-ATTACK-LEDGER.md',
]

// 各文档头注里的格式模板，不是真指针
const TEMPLATE_TARGETS = new Set(['<文件>', '<file>', '<研究文件>', '<research 文件>', '文件'])
// 位置性锚点：内容找得到但锚随文件编辑必然漂移。单列，不算 resolved。
const POSITIONAL = /末行|末段|同上|头注/

const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

/** 解析一条 [E: ...] 的内容为 (target, anchor) 对 */
function parsePointer(body) {
  const out = []
  let currentTarget = null
  for (const seg of body.split(/[,，]/)) {
    const s = seg.trim()
    if (!s) continue
    const withFile = s.match(/^([^#\s]+\.md|<[^>]+>)\s*#\s*(.+)$/)
    if (withFile) {
      currentTarget = withFile[1]
      out.push({ target: currentTarget, anchor: withFile[2].trim() })
      continue
    }
    const anchorOnly = s.match(/^#\s*(.+)$/)
    if (anchorOnly && currentTarget) {
      out.push({ target: currentTarget, anchor: anchorOnly[1].trim() })
      continue
    }
    const fileOnly = s.match(/^([^#\s]+\.md)$/)
    if (fileOnly) { currentTarget = fileOnly[1]; out.push({ target: currentTarget, anchor: null }) }
  }
  return out
}

/**
 * 锚点是否可解析。两档：
 *   T1 字面标记 —— 锚以标题 / 表格首格 / 行首加粗的形式出现
 *   T2 约定推导 —— 锚形如 <小节名><分隔><序号>，小节标题存在且该序号项在文件中存在
 * 位置性锚（末行/末段/同上/头注）一律不算 resolved。
 */
function resolveAnchor(text, anchor) {
  if (POSITIONAL.test(anchor)) return { tier: 'positional' }

  const a = esc(anchor)
  const T1 = [
    new RegExp(`^#{1,6}\\s*\\**\\s*${a}[\\s.．、·:：]`, 'm'),   // 标题
    new RegExp(`^#{1,6}\\s*\\**\\s*${a}\\**\\s*$`, 'm'),        // 标题（整行）
    new RegExp(`^\\|\\s*\\**\\s*${a}\\s*\\**\\s*\\|`, 'm'),     // 表格首格
    new RegExp(`^\\|\\s*\\**${a}\\**[\\s.．、·]`, 'm'),         // 表格首格带后缀
    new RegExp(`^\\*\\*\\s*${a}[\\s.．、·:：]`, 'm'),           // 行首加粗
    new RegExp(`^\\d+\\.\\s*\\**${a}\\**`, 'm'),                // 有序列表
    new RegExp(`^[-*+]\\s*\\**\\s*${a}[\\s.．、·:：*]`, 'm'),   // 无序列表项（可加粗）
    new RegExp(`^[-*+]\\s*\\**\\s*${a}\\**\\s*$`, 'm'),         // 无序列表项（整行）
  ]
  if (T1.some(re => re.test(text))) return { tier: 'T1' }

  // T2r：区间锚 —— <小节名><起>-<止> / <前缀>-<起>~<前缀>-<止>
  // 例：核验表1-6、D-3~D-5、E-3~E-7。两个端点都能解析才算 resolved。
  const range =
    anchor.match(/^(.*?)(\d+)\s*[-~－—]\s*(?:\1)?(\d+)$/) ||
    anchor.match(/^([A-Za-z]+)-(\d+)\s*~\s*\1-(\d+)$/)
  if (range) {
    const [, prefix, from, to] = range
    const isIdStyle = /^[A-Za-z]+$/.test(prefix)
    const endpoint = n => (isIdStyle ? `${prefix}-${n}` : `${prefix}${n}`)
    const a1 = resolveAnchor(text, endpoint(from))
    const a2 = resolveAnchor(text, endpoint(to))
    if (['T1', 'T2'].includes(a1.tier) && ['T1', 'T2'].includes(a2.tier)) return { tier: 'T2', via: 'range' }
  }

  // T2：<小节名><可选分隔><序号>
  const two = anchor.match(/^(.+?)[-‐–—]?(\d+[a-z]?)$/)
  if (two) {
    const [, section, n] = two
    const sectionRe = new RegExp(`^#{1,6}.*${esc(section)}`, 'm')
    if (sectionRe.test(text)) {
      const itemRe = [
        new RegExp(`^\\*\\*\\s*${esc(n)}[\\s.．、·]`, 'm'),
        new RegExp(`^${esc(n)}\\.\\s`, 'm'),
        new RegExp(`^\\|\\s*\\**\\s*${esc(n)}\\s*\\**\\s*\\|`, 'm'),
        new RegExp(`^\\d+\\.\\s*\\*\\*${esc(n)}[\\s.．、·]`, 'm'),
      ]
      if (itemRe.some(re => re.test(text))) return { tier: 'T2', via: section }
    }
  }

  // 兜底：锚作为独立 token 出现（模糊，不算 resolved 但与完全找不到区分开）
  if (new RegExp(`(^|[\\s|*(（])${a}([\\s|*).．、·:：）]|$)`, 'm').test(text)) return { tier: 'fuzzy' }
  return { tier: 'missing' }
}

// ── 扫描 ────────────────────────────────────────────────────────────────
const corpusCache = new Map()
const readCorpus = f => {
  if (!corpusCache.has(f)) {
    const p = join(CORPUS, f)
    corpusCache.set(f, existsSync(p) ? readFileSync(p, 'utf8') : null)
  }
  return corpusCache.get(f)
}

// ── 已声明排除的语料 ────────────────────────────────────────────────────
// 某些语料在**某些仓库**里被刻意不收录（例如公开仓不收对第三方包的逆向档案）。
// 指向它们的指针既不是「欠债」（不是我们写错了），也不能算「可解析」（读者确实找不到）。
// 它是第三类状态：**已声明排除**——前提是排除本身被显式记录并说明理由。
// 判据：research/v2/EXCLUDED.md 存在，且文件名以 `\`名字\`` 或表格首列的形式出现在其中。
// 没有这份声明，缺文件就是缺文件，照旧判红。
const excluded = new Set()
const exclDecl = join(CORPUS, 'EXCLUDED.md')
if (existsSync(exclDecl)) {
  const d = readFileSync(exclDecl, 'utf8')
  for (const m of d.matchAll(/`([A-Za-z0-9_.-]+\.md)`/g)) excluded.add(m[1])
}

const stats = { total: 0, T1: 0, T2: 0, fuzzy: 0, positional: 0, missing: 0, noFile: 0, selfCite: 0, declaredExcluded: 0 }
const unresolved = []
const selfCites = []

for (const doc of PLAN_DOCS) {
  const p = join(ROOT, doc)
  if (!existsSync(p)) continue
  const text = readFileSync(p, 'utf8')
  for (const m of text.matchAll(/\[E:([^\]]*)\]/g)) {
    const line = text.slice(0, m.index).split('\n').length
    for (const { target, anchor } of parsePointer(m[1])) {
      if (TEMPLATE_TARGETS.has(target)) continue
      stats.total++

      // 00-PREMISE 自陈「不得引用本文件的裁决作为证据」（其 §下游引用规则）
      if (/^00-PREMISE/.test(target)) {
        stats.selfCite++
        selfCites.push(`${doc}:${line}  [E: ${target}#${anchor ?? ''}]`)
        continue
      }
      if (PLAN_DOCS.includes(target)) continue // 规划文档内部互引，不由本门管

      if (excluded.has(target)) { stats.declaredExcluded++; continue }

      const corpus = readCorpus(target)
      if (corpus === null) {
        stats.noFile++
        unresolved.push({ doc, line, target, anchor, why: '语料文件不存在' })
        continue
      }
      if (!anchor) { stats.T1++; continue } // 只指文件不指锚，可解析

      const r = resolveAnchor(corpus, anchor)
      stats[r.tier]++
      if (r.tier === 'fuzzy' || r.tier === 'positional' || r.tier === 'missing') {
        unresolved.push({
          doc, line, target, anchor,
          why: { fuzzy: '只有模糊子串命中，无正式标记', positional: '位置性锚（随编辑漂移）', missing: '文件中找不到' }[r.tier],
        })
      }
    }
  }
}

// ── 空集闸（vacuous truth） ─────────────────────────────────────────────
// 扫到 0 个指针时必须**报错**，不能继续判定。
// 实证：本仓库路径含空格（"Paper Graph"），而 `new URL(...).pathname` 会把它编码成 %20，
// 于是门读不到任何文件、stats.total = 0、可解析率打印成 NaN%，
// 而两条棘轮断言在空集上都是**真**的——门会全绿。这正是「空集 vacuous truth」。
// 一手教训：house 的 selftest_fidelity.mjs 专门为此播了 EMPTY-RUN 红样本。
if (stats.total === 0) {
  console.error('[E:] 溯源指针门 —— 致命：扫描到 0 个指针实例')
  console.error(`  ROOT = ${ROOT}`)
  console.error('  规划文档一个都没读到。常见原因：ROOT 解析错（路径含空格时 URL.pathname 会给 %20）、')
  console.error('  或 --root 指向了错误的目录。空集上所有断言都成立，因此本门拒绝给出绿灯。')
  process.exit(2)
}

const key = u => `${u.target}#${u.anchor}`

if (process.argv.includes('--list-unresolved')) {
  for (const u of unresolved) console.log(`${u.doc}:${u.line}\t${key(u)}\t${u.why}`)
  process.exit(0)
}

if (process.argv.includes('--update-debt')) {
  const debt = [...new Set(unresolved.map(key))].sort()
  writeFileSync(DEBT_FILE, JSON.stringify({
    note: '已知不可解析的 [E:] 指针。只能减少，不能增加。还清后必须销账，否则本门判红。',
    generated_by: 'node gates/check_pointers.mjs --update-debt',
    count: debt.length,
    pointers: debt,
  }, null, 1) + '\n')
  console.log(`已登记 ${debt.length} 条欠债 → .attack/pointer-debt.json`)
  process.exit(0)
}

// ── 判定 ────────────────────────────────────────────────────────────────
console.log('[E:] 溯源指针门\n')
console.log(`扫描 ${PLAN_DOCS.length} 份规划文档，共 ${stats.total} 个 (目标, 锚) 实例`)
console.log(`  T1 字面标记 ${stats.T1}   T2 约定推导 ${stats.T2}   模糊 ${stats.fuzzy}   位置性 ${stats.positional}   找不到 ${stats.missing}   文件不存在 ${stats.noFile}`)
const resolvable = stats.T1 + stats.T2
const inScope = stats.total - stats.declaredExcluded
console.log(`  可解析率 ${(resolvable / inScope * 100).toFixed(1)}%（分母已剔除已声明排除的部分）`)
if (stats.declaredExcluded) {
  console.log(`  ⚠️  另有 ${stats.declaredExcluded} 个指针（占全部 ${(stats.declaredExcluded / stats.total * 100).toFixed(1)}%）指向本仓库**已声明排除**的语料，`)
  console.log(`      理由见 research/v2/EXCLUDED.md。它们在本仓库内读者确实解析不了——这是取舍，不是缺陷，但也不是零成本。`)
}
console.log()

let failed = 0

if (!existsSync(DEBT_FILE)) {
  console.log('FAIL  欠债登记表不存在 —— 先跑 node gates/check_pointers.mjs --update-debt')
  process.exit(1)
}
const debt = JSON.parse(readFileSync(DEBT_FILE, 'utf8'))
const known = new Set(debt.pointers)
const now = new Set(unresolved.map(key))

const brandNew = [...now].filter(k => !known.has(k))
const settled = [...known].filter(k => !now.has(k))

if (brandNew.length) {
  failed++
  console.log(`FAIL  新增不可解析指针 · ${brandNew.length} 条（棘轮方向：只许减少）`)
  for (const k of brandNew.slice(0, 15)) {
    const u = unresolved.find(x => key(x) === k)
    console.log(`      ${u.doc}:${u.line}  ${k}  —— ${u.why}`)
  }
} else {
  console.log(`PASS  新增不可解析指针 · 0 条（已知欠债 ${known.size} 条）`)
}

if (settled.length) {
  failed++
  console.log(`FAIL  欠债已还清但未销账 · ${settled.length} 条（登记表会腐，必须同步）`)
  for (const k of settled.slice(0, 15)) console.log(`      ${k}`)
  console.log('      修法: node gates/check_pointers.mjs --update-debt')
} else {
  console.log('PASS  欠债登记表与现状一致')
}

if (stats.selfCite) {
  failed++
  console.log(`FAIL  引用 00-PREMISE 的裁决作为证据 · ${stats.selfCite} 处`)
  console.log('      00-PREMISE 自陈「不得引用本文件的裁决作为证据，只能引用它指向的一手来源；本文件是审计记录，不是证据源」')
  for (const s of selfCites.slice(0, 10)) console.log(`      ${s}`)
} else {
  console.log('PASS  无人把 00-PREMISE 的裁决当证据引用')
}

console.log(`\n${failed ? `${failed} 类阻塞项` : '通过'}`)
process.exit(failed ? 1 : 0)
