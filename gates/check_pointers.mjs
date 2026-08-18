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

/**
 * 解析一条 [E: ...] 的内容为 (target, anchor) 对。
 *
 * 〔R3 修复 · gate-hollow〕原实现对**任何不匹配三种形态的段**静默丢弃：
 * 不计入 stats.total、不进 unresolved、不报错。于是本门引入了它取代 D-1 时
 * 要消灭的**同一类空心**——D-1 放过 `[E: 我瞎编的.md#不存在的锚]`，
 * 本门放过 `[E: 我瞎编的#不存在的锚]`（少一个 .md 后缀即可）。
 * 负例 R-1 只覆盖了有 .md 后缀的那一半。
 *
 * 现在第二个返回值是**无法解析的原文段**，调用方必须把它们计入不可解析。
 */
function parsePointer(body) {
  const out = []
  const junk = []
  let currentTarget = null
  // 分隔符：逗号与分号，全角半角都算。
  // 〔R3 修复〕原本只 split 逗号，于是 `A.md#x；B.md#y` 整条被当成一段、
  // 三种形态都不匹配、被静默丢弃 —— 全角分号在本文档集里是通用分隔符。
  for (const seg of body.split(/[,，;；]/)) {
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
    if (fileOnly) { currentTarget = fileOnly[1]; out.push({ target: currentTarget, anchor: null }); continue }

    // ── 以下三类原本全被静默丢弃，逐类认领 ────────────────────────────
    // (a) S0 实测记录：`.loop/m0/M0-2.json`。它们是承重引用
    //     （01-CONTRACTS §1.2.2.0 的裁定就挂在上面），却从来没被本门检查过。
    const record = s.match(/^((?:\.loop\/|\.attack\/)[^#\s]+\.json)(?:\s*#\s*(.+))?$/)
    if (record) { currentTarget = record[1]; out.push({ target: currentTarget, anchor: record[2]?.trim() ?? null }); continue }

    // (b) 省了 .md 后缀的规划文档：`00-PREMISE#B4-5`。
    //     这正是审计点名的那一类——D-1 放过带 .md 的，本门放过不带 .md 的。
    const bareStem = s.match(/^([A-Za-z0-9][A-Za-z0-9_-]*)\s*#\s*(.+)$/)
    if (bareStem && PLAN_DOCS.includes(bareStem[1] + '.md')) {
      currentTarget = bareStem[1] + '.md'
      out.push({ target: currentTarget, anchor: bareStem[2].trim() })
      continue
    }

    // (c) 外部标识符（URL / arXiv / DOI）：合法引用，但本门是离线的，判不了。
    //     单列一档，既不冒充可解析，也不混进欠债。
    if (/^(https?:\/\/|arxiv:|arXiv:|doi:|DOI:)/i.test(s)) { out.push({ target: '(外部)', anchor: s, external: true }); continue }

    // (c2) 仓库内相对路径（复现脚本、门代码、夹具）：`gates/repro/x.py`、`src/status.mjs`。
    //      它们是承重引用——§7.2.2 的裁定就挂在一条复现脚本上——存在性必须被检查。
    const repoPath = s.match(/^((?:gates|src|checks|scripts)\/[^\s#]+\.[a-z0-9]{1,4})(?:\s*#\s*(.+))?$/i)
    if (repoPath) { currentTarget = repoPath[1]; out.push({ target: currentTarget, anchor: repoPath[2]?.trim() ?? null }); continue }

    // (d) 打捞：段首带中文标签时（`一手：arXiv:…`、`同向记录 ext-x.md#R9`），
    //     上面几条的锚定正则都不匹配。在段内任意位置搜一次可识别的目标。
    //     打捞不到才算无法解析——但打捞**只认完整形态**，不猜。
    const salvageFile = s.match(/([^\s#，,;；]+\.md)\s*#\s*([^，,;；]+)$/)
    if (salvageFile) { currentTarget = salvageFile[1]; out.push({ target: currentTarget, anchor: salvageFile[2].trim() }); continue }
    const salvageUrl = s.match(/(https?:\/\/\S+|(?:arxiv|doi):\s*\S+)/i)
    if (salvageUrl) { out.push({ target: '(外部)', anchor: salvageUrl[1], external: true }); continue }

    // (e) 锚点续写省掉了井号：`[E: ext-orchestration.md#B, 核验表13-19]`
    //     第二段是**同一目标**的另一个锚，只是作者没敲那个 `#`。人读得懂，旧解析器读不懂。
    //     〔R4/机器层 P1-9 修复〕本门此前宣称「不再静默丢弃」，实测**仍在丢**：
    //     全 9 份文档 1635 个段里有 145 个（8.9%）落在这一形态上被无声吞掉，
    //     而宣称的 92.2% 可解析率的分母正好把它们排除在外。
    //     最刺眼的证据：同一个锚 `假独立佐证登记`，在 04-ORCHESTRATION 写成
    //     `#假独立佐证登记` 被正常解析，在 00-PREMISE 少个井号就被丢弃——
    //     **指针的可解析性取决于作者有没有敲那个符号。**
    if (currentTarget && !/^[<（(]/.test(s)) {
      out.push({ target: currentTarget, anchor: s })
      continue
    }

    // 三种形态都不匹配 —— 不许静默丢弃。
    // 纯散文注解（不含 # 且不像文件名）是合法的补充说明，不计；
    // 但凡带 # 的、或形如「名字.扩展名」的，都是**长得像指针却解析不了**的东西，
    // 必须暴露出来。
    if (/#/.test(s) || /^[^\s]+\.[a-z0-9]{1,5}$/i.test(s)) junk.push(s)
  }
  return { pointers: out, junk }
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
const readCorpus = (f, base = CORPUS) => {
  const key = `${base}::${f}`
  if (!corpusCache.has(key)) {
    const p = join(base, f)
    corpusCache.set(key, existsSync(p) ? readFileSync(p, 'utf8') : null)
  }
  return corpusCache.get(key)
}

// ── 已声明排除的语料 ────────────────────────────────────────────────────
// 某些语料在**某些仓库**里被刻意不收录（例如公开仓不收对第三方包的逆向档案）。
// 指向它们的指针既不是「欠债」（不是我们写错了），也不能算「可解析」（读者确实找不到）。
// 它是第三类状态：**已声明排除**——前提是排除本身被显式记录并说明理由。
// 判据：research/v2/EXCLUDED.md 存在，且文件名出现在它的 ```excluded 围栏块里。
// 没有这份声明，缺文件就是缺文件，照旧判红。
//
// 〔口径与 check_doc_metrics 共用同一个块〕原实现扫全文反引号，于是
// EXCLUDED.md 里「这几份**不在此列**」那句提到的文件也会被当成已排除——
// 一句说明反而扩大了豁免面。两道门读同一个围栏块，就不会各自漂。
const excluded = new Set()
const exclDecl = join(CORPUS, 'EXCLUDED.md')
if (existsSync(exclDecl)) {
  const d = readFileSync(exclDecl, 'utf8')
  const block = d.match(/```excluded\n([\s\S]*?)```/)
  if (!block) throw new Error('EXCLUDED.md 缺 ```excluded 声明块 —— 排除必须是机器可读的')
  for (const line of block[1].split('\n')) {
    const f = line.trim()
    if (/\.md$/.test(f)) excluded.add(f)
  }
}

const stats = {
  unparseable: 0, external: 0, total: 0, T1: 0, T2: 0, fuzzy: 0, positional: 0, missing: 0, noFile: 0, selfCite: 0, declaredExcluded: 0 }
const unresolved = []
const selfCites = []

for (const doc of PLAN_DOCS) {
  const p = join(ROOT, doc)
  if (!existsSync(p)) continue
  const text = readFileSync(p, 'utf8')
  for (const m of text.matchAll(/\[E:([^\]]*)\]/g)) {
    const line = text.slice(0, m.index).split('\n').length
    const { pointers, junk } = parsePointer(m[1])
    // 无法解析的段：形状像指针却三种形态都不匹配。计入 total 并直接判不可解析，
    // 否则它就是一条免检通道（见 parsePointer 头注）。
    for (const j of junk) {
      stats.total++
      stats.unparseable++
      unresolved.push({ doc, line, target: '(无法解析)', anchor: j, why: '[E:] 内容不符合任何指针形态' })
    }
    for (const { target, anchor, external } of pointers) {
      if (TEMPLATE_TARGETS.has(target)) continue
      stats.total++
      // 外部标识符：本门离线，无法判定；单列，不计入可解析率的分子分母。
      if (external) { stats.external++; continue }

      // 00-PREMISE 自陈「不得引用本文件的裁决作为证据」（其 §下游引用规则）
      if (/^00-PREMISE/.test(target)) {
        stats.selfCite++
        selfCites.push(`${doc}:${line}  [E: ${target}#${anchor ?? ''}]`)
        continue
      }
      // 〔R4 修复 · gate-hollow〕原写作 `if (PLAN_DOCS.includes(target)) continue`，
      // 注释是「规划文档内部互引，不由本门管」——于是 9 份规划文档之间的引用
      // **一条都没被检查过**。实证：往 05-TESTING 追加
      // `[E: 01-CONTRACTS.md#这个锚点根本不存在XYZ]`，门退出码 0。
      // 那正是本门声称取代 D-1 的那一类，而且发生在引用量最大的地方
      // （01-CONTRACTS 是唯一规范源，被其余八份反复引用）。
      // 现在与语料文件同等对待：文件必存在（同一目录下），锚点必可解析。
      if (PLAN_DOCS.includes(target)) {
        const planText = readCorpus(target, ROOT)
        if (planText === null) {
          stats.noFile++
          unresolved.push({ doc, line, target, anchor, why: '规划文档不存在' })
          continue
        }
        if (!anchor) { stats.T1++; continue }
        const pr = resolveAnchor(planText, anchor)
        stats[pr.tier]++
        if (pr.tier === 'fuzzy' || pr.tier === 'positional' || pr.tier === 'missing') {
          unresolved.push({ doc, line, target, anchor, why: pr.why ?? '锚点在规划文档中找不到' })
        }
        continue
      }

      if (excluded.has(target)) { stats.declaredExcluded++; continue }

      // S0 实测记录 / 攻击台账：判文件是否存在即可。
      // 记录**内部**的结构由 check_m0.mjs 负责，本门不重复。
      if (/\.json$/.test(target) || /^(gates|src|checks|scripts)\//.test(target)) {
        if (existsSync(join(ROOT, target))) { stats.T1++; continue }
        stats.noFile++
        unresolved.push({ doc, line, target, anchor, why: '被引用的仓库内文件不存在' })
        continue
      }

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

// 〔R3 修复 · gate-hollow〕棘轮的键原本只由 (目标, 锚) 构成，**不含出处文档**。
// 于是「新增坏指针」被定义成「新增一个此前没见过的 (目标,锚) 组合」，
// 而不是「新增一条不可解析的引用」——已登记的 109 个坏 pair 成了 109 张
// **通用免死金牌**：任何文档、任意数量的全新伪造引用只要复用其中之一，门恒绿。
// 其中还包括本门自己的反面教材字符串 `我瞎编的.md#根本不存在的锚`
// （R2 写台账时被 --update-debt 一并登记了进去）。
//
// 现在键含出处文档，且登记表是**多重集**（记出现次数）：
//   · 在新文档里复用一个已知坏 pair → 新键 → 红
//   · 在同一文档里增加该 pair 的出现次数 → 计数上升 → 红
// 「欠债只能下降」这条主张因此从「坏引用的**种类**不可变坏」
// 恢复成读者真正关心的「引用质量不可变坏」。
const key = u => `${u.doc}\t${u.target}#${u.anchor}`
const keyLabel = k => { const [d, r] = k.split('\t'); return `${d}  ${r}` }
const countKeys = us => {
  const m = {}
  for (const u of us) m[key(u)] = (m[key(u)] ?? 0) + 1
  return m
}

if (process.argv.includes('--list-unresolved')) {
  for (const u of unresolved) console.log(`${u.doc}:${u.line}\t${u.target}#${u.anchor}\t${u.why}`)
  process.exit(0)
}

if (process.argv.includes('--update-debt')) {
  const counts = countKeys(unresolved)
  const total = Object.values(counts).reduce((a, b) => a + b, 0)
  writeFileSync(DEBT_FILE, JSON.stringify({
    note: '已知不可解析的 [E:] 指针。键 = 出处文档 + 目标 + 锚，值 = 出现次数。' +
          '种类与次数都只能减少。还清后必须销账，否则本门判红。',
    key_format: '<出处文档>\\t<目标>#<锚>',
    generated_by: 'node gates/check_pointers.mjs --update-debt',
    distinct: Object.keys(counts).length,
    occurrences: total,
    pointers: Object.fromEntries(Object.entries(counts).sort(([a], [b]) => a < b ? -1 : 1)),
  }, null, 1) + '\n')
  console.log(`已登记 ${Object.keys(counts).length} 种 / ${total} 次欠债 → .attack/pointer-debt.json`)
  process.exit(0)
}

// ── 判定 ────────────────────────────────────────────────────────────────
console.log('[E:] 溯源指针门\n')
console.log(`扫描 ${PLAN_DOCS.length} 份规划文档，共 ${stats.total} 个 (目标, 锚) 实例`)
console.log(`  T1 字面标记 ${stats.T1}   T2 约定推导 ${stats.T2}   模糊 ${stats.fuzzy}   位置性 ${stats.positional}   找不到 ${stats.missing}   文件不存在 ${stats.noFile}`)
console.log(`  外部标识符 ${stats.external}（URL/arXiv/DOI，本门离线判不了，单列）   无法解析 ${stats.unparseable}（形似指针但不符任何形态）`)
const resolvable = stats.T1 + stats.T2
const inScope = stats.total - stats.declaredExcluded - stats.external
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
if (Array.isArray(debt.pointers)) {
  console.log('FAIL  欠债登记表还是旧的「只按指针文本作键」格式（数组）——')
  console.log('      该格式让已登记的坏 pair 成为跨文档通用的免死金牌。')
  console.log('      修法: node gates/check_pointers.mjs --update-debt')
  process.exit(1)
}
const known = debt.pointers ?? {}
const nowCounts = countKeys(unresolved)

// 新增 = 新键，或已知键的出现次数上升
const brandNew = Object.entries(nowCounts)
  .filter(([k, n]) => n > (known[k] ?? 0))
  .map(([k, n]) => ({ k, n, was: known[k] ?? 0 }))
const settled = Object.entries(known)
  .filter(([k, n]) => (nowCounts[k] ?? 0) < n)
  .map(([k, n]) => ({ k, n, now: nowCounts[k] ?? 0 }))

if (brandNew.length) {
  failed++
  console.log(`FAIL  新增不可解析指针 · ${brandNew.length} 处（棘轮方向：种类与次数都只许减少）`)
  for (const { k, n, was } of brandNew.slice(0, 15)) {
    const u = unresolved.find(x => key(x) === k)
    console.log(`      ${keyLabel(k)}  ${was} → ${n} 次  —— ${u?.why ?? ''}`)
  }
} else {
  const dk = Object.keys(known).length
  const dn = Object.values(known).reduce((a, b) => a + b, 0)
  console.log(`PASS  新增不可解析指针 · 0 条（已知欠债 ${dk} 种 / ${dn} 次）`)
}

if (settled.length) {
  failed++
  console.log(`FAIL  欠债已还清但未销账 · ${settled.length} 处（登记表会腐，必须同步）`)
  for (const { k, n, now } of settled.slice(0, 15)) console.log(`      ${keyLabel(k)}  ${n} → ${now} 次`)
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
