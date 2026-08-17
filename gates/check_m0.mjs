#!/usr/bin/env node
// M0 阻塞项门（loop 的 S0 阶段验收，GC-0：离线、确定性、零模型）
//
// M0 阻塞项之所以是阻塞项，正是因为它们「读对了但没跑过」。
// 所以这道门要抓的不是「有没有写记录」，而是**记录是不是真的来自实测**。
//
// loop 设计里给 S0 写的 passing_but_wrong 是：
//   「七份文件全部凭推理写成 verdict=resolved（『按代码应该是这样』），一次都没真跑。」
// 排除它的机制就在本文件的 §3：**随机抽一条 resolved 记录，重跑它的命令，比对 raw_output_sha256**。
// 对不上就判红——因为一个凭空写的 sha256 不可能对得上。
//
// 用法:
//   node gates/check_m0.mjs                 结构检查 + 抽一条重跑
//   node gates/check_m0.mjs --no-rerun      只做结构检查（CI 无网/无 DSH 时）
//   node gates/check_m0.mjs --rerun-all     全部 resolved 记录都重跑（慢）
//   node gates/check_m0.mjs --pick <n>      指定抽第 n 条（用于负例套件）
// 退出码: 0 = 通过，1 = 有阻塞项，2 = 空集（一条记录都没有）

import { readFileSync, existsSync, readdirSync, mkdtempSync, writeFileSync, rmSync } from 'node:fs'
import { join } from 'node:path'
import { tmpdir } from 'node:os'
import { createHash } from 'node:crypto'
import { execSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const rootArg = process.argv.indexOf('--root')
const ROOT = rootArg > -1 ? process.argv[rootArg + 1] : fileURLToPath(new URL('..', import.meta.url))
const DIR = join(ROOT, '.loop/m0')

const NO_RERUN = process.argv.includes('--no-rerun')
const RERUN_ALL = process.argv.includes('--rerun-all')
const pickArg = process.argv.indexOf('--pick')
const PICK = pickArg > -1 ? Number(process.argv[pickArg + 1]) : null

// 00-PREMISE §M0 声明的七条，其中第 3 条拆成三个可独立实测的子项；
// 另加 R1 判出的两条架构实测项与一条会烧掉实现的地雷。
const REQUIRED = {
  'M0-1': 'PDF 可见性区分（通道分离的架构前提）',
  'M0-2': 'quote_faithful 的 100% 承诺缺实测',
  'M0-2b': '多帧 zstd —— Node 内置 API 只解第一帧',
  'M0-3a': 'M1 插件 inject 的确切服务名',
  'M0-3b': 'headless 一次性任务的 CLI 调用形式',
  'M0-3c': 'workflow 引擎行的 entry id（patch 打不中只 warn 不 fail）',
  'M0-4': 'run_code 是否可达 node:fs',
  'M0-5': 'compaction 从未在本机触发',
  'M0-6': '中央限速网关的失效行为未设计',
  'M0-7': 'gate_integrity.sh 自身谁来证明没被改',
  'C-12a': '出厂呈现模式假设是否被 headless bundle 覆盖',
  'C-12b': 'boot 门该把威胁钉在 cordis.patch.yml 还是 settings.yaml',
}

const VERDICTS = ['resolved', 'design-changed', 'still-blocked']

// 实测命令不该有副作用。命中即判红——这既是安全闸，也是一条真实的质量判据：
// 一条会改变世界的「测量」不可重跑，raw_output_sha256 也就失去意义。
//
// 〔更正 · 首次运行后〕原本这里有一条 `>\s*\/`，本意是抓「重定向覆盖系统文件」，
// 实际把 `>/dev/null` 与 `> /tmp/out.txt` 全抓了——而后者**正是本文件 RECORD_SPEC
// 要求的写法**（`cmd > /tmp/out.txt 2>&1; shasum -a 256 ...`）。
// 门在惩罚它自己要求的正确做法，一次性误报 6 条。
// 教训与「空心门」是同一枚硬币的两面：**门的假阳性同样是缺陷**——
// 一道会误伤正确做法的门，会训练出「绕开门」而不是「满足门」的习惯。
// 现在只对**非临时目录**的绝对路径重定向判红。
const TEMP_SINK = String.raw`dev/null|tmp/|private/tmp/|var/folders/`
const DESTRUCTIVE = new RegExp(
  [
    String.raw`\brm\s`,
    String.raw`\bmv\s`,
    String.raw`\bdd\s`,
    String.raw`>\s*/(?!${TEMP_SINK})`, // 重定向到非临时目录的绝对路径
    String.raw`\bgit\s+(push|reset|checkout|tag\s+-f)`,
    String.raw`\bnpm\s+(publish|install|i)\b`,
    String.raw`\bcurl\b[^|]*-X\s*(POST|PUT|DELETE|PATCH)`,
    String.raw`\bkill\b`,
    String.raw`\bchmod\s`,
    String.raw`\bsudo\b`,
  ].join('|'),
  'i',
)

// 记录里出现未展开的占位符 = 命令不可原样重跑，等同于没有证据。
const PLACEHOLDER = /<[a-z_][a-z0-9_-]*>|\$\{?PLACEHOLDER|TODO|XXX/i

const problems = []
const note = (id, msg) => problems.push(`${id}: ${msg}`)

// ── §1 记录存在性 ───────────────────────────────────────────────────────
if (!existsSync(DIR)) {
  console.error('M0 阻塞项门 —— 致命：.loop/m0/ 目录不存在')
  console.error('  S0 阶段一条记录都没有。空集上所有断言都成立，因此本门拒绝给出绿灯。')
  process.exit(2)
}

const files = readdirSync(DIR).filter(f => f.endsWith('.json'))
if (files.length === 0) {
  console.error('M0 阻塞项门 —— 致命：.loop/m0/ 下没有任何 .json 记录')
  process.exit(2)
}

const records = new Map()
for (const f of files) {
  let r
  try {
    r = JSON.parse(readFileSync(join(DIR, f), 'utf8'))
  } catch (e) {
    note(f, `不是合法 JSON：${e.message}`)
    continue
  }
  if (!r.id) { note(f, '缺 id 字段'); continue }
  if (records.has(r.id)) note(r.id, `重复记录（${f} 与之前的文件同 id）`)
  records.set(r.id, { ...r, _file: f })
}

for (const [id, desc] of Object.entries(REQUIRED)) {
  if (!records.has(id)) note(id, `缺记录 —— ${desc}`)
}
for (const id of records.keys()) {
  if (!REQUIRED[id]) note(id, '记录的 id 不在 M0 清单内（写错了 id？还是漏登记了新阻塞项？）')
}

// ── §2 记录结构 ─────────────────────────────────────────────────────────
for (const [id, r] of records) {
  if (!VERDICTS.includes(r.verdict)) { note(id, `verdict 非法：${JSON.stringify(r.verdict)}`); continue }
  for (const k of ['question', 'answer', 'honest_limits']) {
    if (typeof r[k] !== 'string' || !r[k].trim()) note(id, `缺 ${k}`)
  }
  if (!Array.isArray(r.affects)) note(id, '缺 affects 数组（这条前提被规划文档的哪些地方依赖）')

  const ev = Array.isArray(r.evidence) ? r.evidence : []

  // resolved 的门槛最高：必须有可复现的证据
  if (r.verdict === 'resolved') {
    if (!ev.length) {
      note(id, 'verdict=resolved 却没有 evidence —— 这正是本门要抓的「凭推理写 resolved」')
      continue
    }
    for (const [i, e] of ev.entries()) {
      if (!e.command || !String(e.command).trim()) note(id, `evidence[${i}] 缺 command`)
      // 有些证据本来就**不可逐字节复现**：LLM 输出、随目录增长的扫描、文档阅读。
      // 逼它填一个 64 位十六进制等于逼它编——这正是本门要防的那件事的反面。
      // 允许显式声明不可复现，但要付出代价：excerpt 成为唯一可查的东西，不能空；
      // 且 resolved 必须**至少有一条**真正可复现的证据（见下）。
      const hasHash = /^[0-9a-f]{64}$/.test(String(e.raw_output_sha256 ?? ''))
      const declaredIrreproducible = e.reproducible === false ||
        /不可复|未存盘|n\/a|逐字不可|不可逐字/i.test(String(e.raw_output_sha256 ?? ''))
      if (!hasHash && !declaredIrreproducible)
        note(id, `evidence[${i}] 的 raw_output_sha256 既不是 64 位十六进制，也没声明不可复现`)
      if (!e.excerpt || !String(e.excerpt).trim()) note(id, `evidence[${i}] 缺 excerpt（输出里承重的那几行逐字）`)
      // 「命令可原样重跑」这两条检查（占位符 / 破坏性操作）**只服务于重跑验证**。
      // 一条已显式声明不可复现、且给了理由的证据，重跑本来就不适用于它，
      // 再对它查可跑性就是第四次「门惩罚诚实」。
      // 注意豁免不是免费的：resolved 仍必须**至少有一条**真正可复现的证据（见下），
      // 所以这个口子不能被用来把整份记录洗白。
      const waived = e.reproducible === false && String(e.irreproducible_reason ?? '').trim().length >= 10
      if (waived) continue

      // 清理自己 mktemp 出来的临时目录是好习惯，不是破坏性操作
      const selfCleanup = /mktemp\s+-d/.test(e.command ?? "") &&
        /\brm\s+-rf?\s+"?\$\{?[A-Za-z_][A-Za-z0-9_]*\}?"?/.test(e.command ?? "")
      const cmdSansCleanup = selfCleanup
        ? String(e.command).replace(/;\s*rm\s+-rf?\s+"?\$\{?[A-Za-z_][A-Za-z0-9_]*\}?"?\s*$/, "")
        : String(e.command ?? "")
      if (e.command && DESTRUCTIVE.test(cmdSansCleanup))
        note(id, `evidence[${i}] 的 command 含破坏性操作，不可重跑：…${cmdSansCleanup.slice(Math.max(0, cmdSansCleanup.search(DESTRUCTIVE) - 25), cmdSansCleanup.search(DESTRUCTIVE) + 35)}…`)
      if (e.command && PLACEHOLDER.test(e.command))
        note(id, `evidence[${i}] 的 command 含未展开的占位符（不可原样重跑）：${e.command.match(PLACEHOLDER)[0]}`)
    }
  }

  // resolved 必须至少有一条**真正可复现**的证据。
  // 全部证据都声明"不可逐字节复现"的 resolved，和凭推理写的 resolved 没有区别——
  // 重跑验证在那种记录上无事可做，本门的牙齿就落空了。
  if (r.verdict === 'resolved') {
    const anyReproducible = ev.some(e =>
      /^[0-9a-f]{64}$/.test(String(e.raw_output_sha256 ?? '')) && e.command && !PLACEHOLDER.test(e.command))
    if (!anyReproducible) {
      note(id, 'verdict=resolved 但没有任何一条可复现的证据（全部声明不可逐字节复现）—— 重跑验证无事可做')
    }
  }

  // still-blocked 必须说清缺什么条件，否则等同于放弃
  if (r.verdict === 'still-blocked' && (!r.honest_limits || r.honest_limits.length < 20)) {
    note(id, 'verdict=still-blocked 但 honest_limits 太短 —— 必须说清本机缺什么条件')
  }

  // design-changed 必须指出该改哪句。
  // 〔更正〕原本要求 doc_action **精确等于** 'needed'，而实测者写的是
  // 「needed —— 核心一句要改：…」，信息量更大却被判红。门在惩罚更好的做法。
  // 这是本门第三次同类误报（前两次：>/tmp 重定向、诚实声明的不可复现证据）。
  // 记在这里作为一条设计教训：**过严的 schema 会训练出满足 schema 而非说真话的行为**。
  if (r.verdict === 'design-changed' && !/^\s*needed\b/i.test(String(r.doc_action ?? ''))) {
    note(id, 'verdict=design-changed 但 doc_action 不以 needed 开头 —— 实测推翻了前提，文档必须跟着改')
  }

  // 本仓库 public：记录里不得有本机绝对路径
  const blob = JSON.stringify(r)
  if (/\/Users\/[a-z][a-z0-9_-]*\//i.test(blob)) note(id, '记录里有本机绝对路径（仓库是 public 的，换成 ~/）')
}

// ── §3 重跑验证（反自报的唯一机制） ─────────────────────────────────────
const rerunnable = [...records.values()]
  .filter(r => r.verdict === 'resolved' && Array.isArray(r.evidence) && r.evidence.length)
  .flatMap(r => r.evidence.map((e, i) => ({ id: r.id, idx: i, ...e })))
  // 只重跑**声称可复现**的证据。声明了「不可逐字节复现」的条目上没有可比对的哈希，
  // 硬拿它去比只会产出噪声，而噪声会让人学会忽略这道门的输出。
  .filter(e => e.command && !DESTRUCTIVE.test(e.command) && !PLACEHOLDER.test(e.command))
  .filter(e => /^[0-9a-f]{64}$/.test(String(e.raw_output_sha256 ?? '')))

const rerunResults = []
if (!NO_RERUN && rerunnable.length) {
  // 抽样规则：默认抽一条，用记录总数取模轮转（不是随机数——本门必须是确定性的，
  // 否则「这次抽中的那条恰好是真的」会让绿灯不可复现）。
  const picks = RERUN_ALL
    ? rerunnable
    : [rerunnable[PICK !== null ? PICK % rerunnable.length : records.size % rerunnable.length]]

  const tmp = mkdtempSync(join(tmpdir(), 'm0-verify-'))
  for (const e of picks) {
    // ── 被哈希的到底是什么 ─────────────────────────────────────────────
    // 〔更正 · 首次运行后〕原本这里一律 `${command} > out 2>&1` 再哈希 out。
    // 但 RECORD_SPEC 示范的写法是
    //     { ...测量... } > /tmp/x.txt 2>&1; shasum -a 256 /tmp/x.txt
    // ——命令自己把输出重定向进一个文件，末尾的 shasum 只是**取值方式**。
    // 门若哈希整条命令的 stdout，拿到的是 shasum 那行文字，不是被测输出。
    // 首次运行时 M0-2b 因此被误判为「哈希对不上」，而手工重跑证明记录完全诚实。
    //
    // 现在支持两种形态，优先显式声明：
    //   ① 记录带 `output_file` → 跑完哈希该文件
    //   ② 命令以 `shasum -a 256 <path>` / `sha256sum <path>` 结尾 → 哈希 <path>
    //   ③ 都没有 → 哈希命令的 stdout+stderr（最朴素的形态）
    const tail = String(e.command).match(/(?:shasum\s+-a\s+256|sha256sum)\s+("?)([^"'\s;|&]+)\1\s*$/)
    const declared = e.output_file ?? (tail ? tail[2] : null)
    const out = join(tmp, 'out.txt')
    let got = null
    let err = null
    try {
      const cwd = e.cwd ? e.cwd.replace(/^~/, process.env.HOME ?? '~') : ROOT
      execSync(`${e.command} > ${JSON.stringify(out)} 2>&1`, {
        cwd: existsSync(cwd) ? cwd : ROOT,
        timeout: 120_000,
        shell: '/bin/bash',
        stdio: 'ignore',
      })
    } catch (x) {
      // 命令自身非零退出是允许的——我们比对的是输出内容，不是它的退出码
      err = x.status ?? x.message
    }
    const target = declared ? declared.replace(/^~/, process.env.HOME ?? '~') : out
    if (existsSync(target)) {
      got = createHash('sha256').update(readFileSync(target)).digest('hex')
    }
    const match = got === e.raw_output_sha256
    rerunResults.push({ ...e, got, match, err })
    if (!match) {
      note(e.id, `重跑 evidence[${e.idx}] 的哈希对不上：记录 ${String(e.raw_output_sha256).slice(0, 12)}… 实测 ${String(got ?? '（无输出）').slice(0, 12)}…`)
    }
  }
  rmSync(tmp, { recursive: true, force: true })
}

// ── 报告 ────────────────────────────────────────────────────────────────
const byVerdict = v => [...records.values()].filter(r => r.verdict === v).length
console.log('M0 阻塞项门\n')
console.log(`记录 ${records.size}/${Object.keys(REQUIRED).length}`)
console.log(`  resolved ${byVerdict('resolved')}   design-changed ${byVerdict('design-changed')}   still-blocked ${byVerdict('still-blocked')}`)
if (rerunResults.length) {
  const ok = rerunResults.filter(r => r.match).length
  console.log(`  重跑验证 ${ok}/${rerunResults.length} 条哈希对上` + (NO_RERUN ? '' : `（抽样，用 --rerun-all 全跑）`))
} else if (NO_RERUN) {
  console.log('  重跑验证：已跳过（--no-rerun）⚠️ 本次绿灯不构成「记录来自实测」的证据')
} else {
  console.log('  重跑验证：无可重跑的 resolved 记录')
}
console.log()

if (!problems.length) {
  console.log('PASS  M0 记录齐全、结构合法、抽样重跑哈希一致')
  process.exit(0)
}

console.log(`FAIL  ${problems.length} 处`)
for (const p of problems) console.log(`      ${p}`)
process.exit(1)
