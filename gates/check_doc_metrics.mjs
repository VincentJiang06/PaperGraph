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

import { readFileSync, writeFileSync, readdirSync, existsSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { execFileSync } from 'node:child_process'

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
const DOCS_FOR_LINKS = ['README.md', '00-PREMISE.md', '01-CONTRACTS.md', '02-ARCHITECTURE.md',
  '03-EVIDENCE-ENGINE.md', '04-ORCHESTRATION.md', '05-TESTING.md', '06-SURVEY.md', '07-ATTACK-LEDGER.md']

const present = readdirSync(join(ROOT, 'research/v2')).filter(f => f.endsWith('.md') && f !== 'EXCLUDED.md')
let declaredExcluded = 0
try {
  const d = read('research/v2/EXCLUDED.md')
  // 只认 ```excluded 围栏块。原实现扫全文反引号，于是文件里「不在此列」那句
  // 提到的三份也被算成排除项（语料数 26 → 34）。给人读的说明不该同时当机器口径。
  const block = d.match(/```excluded\n([\s\S]*?)```/)
  if (!block) throw new Error('EXCLUDED.md 缺 ```excluded 声明块 —— 排除必须是机器可读的')
  // 只计**声明排除且确实不在场**的那几份。
  // 〔自纠〕写成「在场 + 全部声明数」会在开发树里重复计数：那 5 份在开发树里
  // 是在场的，于是 26 变成 31。这条公式要在两棵树上给出同一个数才算对——
  // 发布树 21 在场 + 5 缺席 = 26，开发树 26 在场 + 0 缺席 = 26。
  const declared = [...new Set(block[1].split('\n').map(x => x.trim()).filter(x => /\.md$/.test(x)))]
  declaredExcluded = declared.filter(f => !present.includes(f)).length
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

// ── 穷举 oracle 的向量数 ──────────────────────────────────────────────
// 〔R4/机器层 P2-13 修复〕README 写「550 万」而实测已涨到 2778 万（5 倍偏差），
// 本门此前 PASS ——因为它只认「N 份调研文件 / N 行 / N 条断言」三种句式，
// 向量数根本不在它的视野里。**自述数字门只覆盖它列举过的那几种数字**，
// 这句话本身就是这道门的已知边界，写在这里以免下次又被当成全覆盖。
// 读 oracle 落下的统计工件，而不是每次重跑 60 秒的 oracle。
// 工件缺失 = oracle 没跑过，本门不替它宣称任何数字。
// 〔本门第二次踩空集〕工件缺失时若静默放行，这段检查就等于不存在——
// 我第一版正是这么写的，于是工件没生成、门照样 PASS。
// 缺失即判红：它意味着 oracle 没跑过，本门不替它宣称任何数字。
const statsPath = join(ROOT, 'gates/.oracle-stats.json')
if (!existsSync(statsPath)) {
  problems.push({ what: 'gates/.oracle-stats.json 不存在', want: '先跑 node gates/check_status_exhaustive.mjs', got: '（缺）' })
} else {
  {
    const real = JSON.parse(readFileSync(statsPath, 'utf8')).legal_vectors
    const readme = read('README.md')
    const claim = readme.match(/\*\*(\d[\d,]*)\s*万输入向量/)
    if (claim) {
      const claimed = Number(claim[1].replace(/,/g, '')) * 10000
      // 允许 README 用「万」为单位取整，误差限 1 万
      if (Math.abs(claimed - real) > 10000) {
        problems.push({ what: 'README 写穷举 oracle 向量数', want: `${Math.round(real / 10000)} 万`, got: `${claim[1]} 万` })
      }
    } else {
      problems.push({ what: 'README 未声明穷举 oracle 向量数', want: `${Math.round(real / 10000)} 万`, got: '（缺）' })
    }
  }
}

// ── 台账的自述数字必须与 .attack/*.json 相符 ──────────────────────────
// 〔R6-10〕本门此前**只守 README**，台账不在它的视野里。于是台账写
// 「产品代码 1046 行、门 14 道」而实测 1683 行 / 20 道门，「仍未做」列的四项
// 全部已做，且**根本没有 S3 节**——攻击者正是从这条缝里进来的。
//
// 台账里承重的数字是 findings 的条数与分级，它们全部有机器可读的来源
// （`.attack/*.json`），因此可以逐条比对，而不是靠人记得去更新。
{
  const ledger = read('07-ATTACK-LEDGER.md')
  const countBy = (arr, k) => arr.filter(f => f.severity === k).length
  const checks = []

  const r6p = join(ROOT, '.attack/r6-findings.json')
  if (!existsSync(r6p)) {
    problems.push({ what: '.attack/r6-findings.json 不存在', want: 'R6 全量在场', got: '（缺）' })
  } else {
    const r6 = JSON.parse(readFileSync(r6p, 'utf8'))
    const f = r6.findings ?? []
    checks.push(
      // 两种写法都要收：总览表是 `**15 条**（P1 …`，§S4 正文是 `**15 条**：P1 …`。
      // 尾部锚 `INFO` 是用来把 **R3 那一行**排除掉的——它写 `**92**（P1 31 / P2 42 / P3 19）`，
      // 没有 INFO 档，否则会被当成 R6 的计数而恒判红。
      ['R6 findings 总数', /\*\*(\d+)(?: 条)?\*\*[（：]P1 \d+ \/ P2 \d+ \/ P3 \d+ \/ INFO/, f.length],
      ['R6 P1 数', /P1 (\d+) \/ P2 \d+ \/ P3 \d+ \/ INFO/, countBy(f, 'P1')],
      ['R6 P3 数', /P1 \d+ \/ P2 \d+ \/ P3 (\d+) \/ INFO/, countBy(f, 'P3')],
      ['R6 P2 数', /P1 \d+ \/ P2 (\d+) \/ P3 \d+ \/ INFO/, countBy(f, 'P2')],
      ['R6 flags 数', /另有 (\d+) 条 flags/, (r6.flags ?? []).length],
      ['R6 coverage_gaps 数', /(\d+) 条 coverage_gaps/, (r6.coverage_gaps ?? []).length],
    )
  }

  const s3p = join(ROOT, '.attack/self-attack-s3.json')
  if (existsSync(s3p)) {
    const s3 = JSON.parse(readFileSync(s3p, 'utf8'))
    checks.push(['S3 findings 总数', /\| S3 \|[^|]*\|[^|]*\|[^|]*\|[^|]*\| (\d+)（/, (s3.findings ?? []).length])
  }

  // 每条都必须**匹配得到**，而且**所有出现处**都要对上。
  //
  // 〔这段是一次自纠，留着〕初版用 `ledger.match(re)` 只取**第一个**匹配。
  // 而同一组数字在台账里出现两次（轮次总览表一次、§S4 正文一次），
  // 于是我把 §S4 里的 P1 计数改坏来验红时，门**照样绿**——它比对的是总览表那一处。
  // 一条只守住重复内容中某一份的检查，与不存在的差别很小：腐的那份正是没被守的那份。
  for (const [what, re, real] of checks) {
    const hits = [...ledger.matchAll(new RegExp(re.source, re.flags.includes('g') ? re.flags : re.flags + 'g'))]
    if (!hits.length) {
      problems.push({ what: `台账里找不到「${what}」的写法`, want: String(real), got: '（正则未命中）' })
      continue
    }
    const wrong = hits.filter(m => Number(m[1]) !== real)
    if (wrong.length) {
      problems.push({ what: `台账写${what}（${wrong.length}/${hits.length} 处不符）`,
                      want: String(real), got: [...new Set(wrong.map(m => m[1]))].join('、') })
    }
  }
  if (checks.length) {
    console.log(`台账: ${checks.length} 个自述数字与 .attack/*.json 比对` +
      `（R6 findings / P1 / P2 / flags / coverage_gaps / S3 findings），逐个出现处都要对上`)
  }
}

// ── README 的「N/N 全绿」必须与实际跑的门数相符 ────────────────────────
// 〔本门第三次被自己的边界打中〕头注早就写明「自述数字门只覆盖它列举过的
// 那几种数字」。门数是 README 的**头条数字**，而它一直不在视野里：
// 实测 26 → 30 的过程中 README 一直写着 26，五轮无人察觉。
// 工件由 run_all.sh 落（它是唯一知道「这次真的跑了几道」的一方），
// 缺失即判红 —— 与 oracle 向量数同一条纪律。
{
  const gp = join(ROOT, 'gates/.gate-stats.json')
  if (!existsSync(gp)) {
    problems.push({ what: 'gates/.gate-stats.json 不存在', want: '先跑 ./gates/run_all.sh all', got: '（缺）' })
  } else {
    const { total } = JSON.parse(readFileSync(gp, 'utf8'))
    const m = readme.match(/\*\*(\d+)\s*\/\s*(\d+)\s*全绿\*\*/)
    if (!m) {
      problems.push({ what: 'README 未声明门数（形如 **N/N 全绿**）', want: `${total}/${total}`, got: '（缺）' })
    } else if (Number(m[2]) !== total || Number(m[1]) !== total) {
      problems.push({ what: 'README 写门数', want: `${total}/${total} 全绿`, got: `${m[1]}/${m[2]} 全绿` })
      fixed = fixed.replace(m[0], `**${total}/${total} 全绿**`)
    }
  }
}

// ── 相对链接必须指向真实存在的文件 ────────────────────────────────────
// 〔R3 修复 · 由 README «部分调研未收录» 一节暴露〕那一节把读者指向
// `research/v2/EXCLUDED.md` 说明排除理由，而该文件**根本不存在**；同时还断言
// 「本仓库是 21 份而非 26 份」（实际 26 份）、给出「456 个指针、占 33.8%」
// （无任何口径能得出）。本门当时全数放过，因为它的正则只匹配
// 「N 份调研文件」这一种写法——**门和它要守的那句话擦肩而过**。
//
// 数字断言的形态是无穷的，逐条写正则永远追不上。但「指向一个不存在的文件」
// 是可穷尽的：任何描述仓库状态的散文，只要它把读者指向某处，那个指向就必须成立。
// 这条检查不依赖任何措辞，因此不会被改写绕过。
const brokenLinks = []
for (const doc of DOCS_FOR_LINKS) {
  const text = read(doc)
  if (!text) continue
  for (const m of text.matchAll(/\[[^\]]*\]\(([^)#\s]+)(?:#[^)]*)?\)/g)) {
    const href = m[1]
    if (/^(https?:|mailto:)/i.test(href)) continue
    const target = href.startsWith('/') ? join(ROOT, href.slice(1)) : join(ROOT, dirname(doc), href)
    if (!existsSync(target)) {
      const line = text.slice(0, m.index).split('\n').length
      brokenLinks.push(`${doc}:${line}  ${href}`)
    }
  }
}
if (brokenLinks.length) {
  console.log(`FAIL  ${brokenLinks.length} 条相对链接指向不存在的文件`)
  for (const b of brokenLinks) console.log(`      ${b}`)
  console.log('      指向不存在的文件 = 在描述一个不存在的仓库状态。')
} else {
  console.log('PASS  全部相对链接指向真实存在的文件')
}

console.log(`实测: 语料 ${corpusFiles.length} 维度（在场 ${corpusFiles.present} + 已声明排除 ${corpusFiles.excluded}）/ 在场 ${corpusLines} 行；01-CONTRACTS 可检验断言 ${vIds} 条`)
console.log(`      ${Object.entries(actual).map(([d, n]) => `${d.slice(0, 2)}=${n}`).join('  ')}\n`)

if (!problems.length && !brokenLinks.length) {
  console.log('PASS  README 与各文档的自述数字全部与实测相符')
  process.exit(0)
}

if (FIX && problems.length) {
  writeFileSync(join(ROOT, 'README.md'), fixed)
  console.log(`已回填 README（${problems.length} 处）——请复查 diff 后再提交`)
  // 死链不能自动修（目标文件该不该存在是人的判断），有死链就仍然判红。
  process.exit(brokenLinks.length ? 1 : 0)
}

if (!problems.length) {
  console.log('FAIL  自述数字全部相符，但存在指向不存在文件的链接（见上）')
  process.exit(1)
}

console.log(`FAIL  ${problems.length} 处自述数字与实测不符`)
for (const p of problems) console.log(`      ${p.what}: 实际 ${p.want}，文档写 ${p.got}`)
console.log('\n      修法: node gates/check_doc_metrics.mjs --fix （只回填 README 的行数与断言数，其余需人工核对口径）')
process.exit(1)
