#!/usr/bin/env node
// M0 阻塞项门（loop 的 S0 阶段验收）
//
// 〔R5-07 更正〕本行原写作「GC-0：离线、确定性、零模型」——**不成立**。
// C-12a[2] 与 M0-3a[2] 的命令是 `dsh --profile headless "<自然语言 prompt>"`，
// 即**真实模型调用**（攻击者亲手重跑 4.98s；--no-rerun 0.03s vs 完整 20s）。
// 更微妙的是这两条的**全部输出是 2 字节 `1\n`**（sha256 = 4355a46b… = sha256("1\n")），
// 哈希匹配约携带 1 bit 信息——非确定性被命令末尾的 `grep -c` 洗成了确定性。
// 而它们正是 README 诚实声明里两条 M0 阻塞项的唯一闭合证据。
//
// 因此本门的正确定级是：**结构检查是 GC-0；重跑验证的门类取决于被重跑的命令**。
// 下面的 §3 会把「命令会调用模型」的证据单独标出来，不让它们混在「离线确定性」里。
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

import { readFileSync, existsSync, readdirSync, mkdtempSync, writeFileSync, rmSync, statSync, renameSync } from 'node:fs'
import { join } from 'node:path'
import { tmpdir } from 'node:os'
import { createHash } from 'node:crypto'
import { execSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const rootArg = process.argv.indexOf('--root')
const ROOT = rootArg > -1 ? process.argv[rootArg + 1] : fileURLToPath(new URL('..', import.meta.url))
const DIR = join(ROOT, '.loop/m0')

const NO_RERUN = process.argv.includes('--no-rerun')
// --rerun-all 现在是默认行为，保留该 flag 只为不打断既有调用（no-op）。
// --sample N：只重跑第 N 条（模长度），供快速迭代用；**运行会被标记为不完整**。
const sampleArg = process.argv.indexOf('--sample')
const SAMPLE = sampleArg > -1 ? Number(process.argv[sampleArg + 1]) : null

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

  // 〔R3 修复 · gate-hollow〕原本只有 resolved 要求证据，design-changed 完全豁免。
  // 那是个大洞：design-changed 的语义是「我实测了，而实测推翻了一条设计前提」——
  // 承重比 resolved 更大（它会引发文档改写）。12 条记录里 6 条是 design-changed，
  // 独立审计把它们全部改写成纯编造后本门仍 exit 0。
  // 现在：resolved 与 design-changed 同属**已测量**判决，证据要求完全相同。
  // 只有 still-blocked 豁免——它的语义恰恰是「本机测不了」。
  const MEASURED = r.verdict === 'resolved' || r.verdict === 'design-changed'
  if (MEASURED) {
    if (!ev.length) {
      note(id, `verdict=${r.verdict} 却没有 evidence —— 这正是本门要抓的「凭推理写判决」`)
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

  // 已测量判决必须至少有一条**真正可复现**的证据。
  // 全部证据都声明"不可逐字节复现"的记录，和凭推理写的没有区别——
  // 重跑验证在那种记录上无事可做，本门的牙齿就落空了。
  if (MEASURED) {
    const anyReproducible = ev.some(e =>
      /^[0-9a-f]{64}$/.test(String(e.raw_output_sha256 ?? '')) && e.command && !PLACEHOLDER.test(e.command))
    if (!anyReproducible) {
      note(id, `verdict=${r.verdict} 但没有任何一条可复现的证据（全部声明不可逐字节复现）—— 重跑验证无事可做`)
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
  .filter(r => (r.verdict === 'resolved' || r.verdict === 'design-changed') &&
               Array.isArray(r.evidence) && r.evidence.length)
  .flatMap(r => r.evidence.map((e, i) => ({ id: r.id, idx: i, ...e })))
  // 只重跑**声称可复现**的证据。声明了「不可逐字节复现」的条目上没有可比对的哈希，
  // 硬拿它去比只会产出噪声，而噪声会让人学会忽略这道门的输出。
  .filter(e => /^[0-9a-f]{64}$/.test(String(e.raw_output_sha256 ?? '')))

// 〔R5-02 修复〕此前这里用**原始** command 测 DESTRUCTIVE，而 §2 的结构检查用的是
// 剥掉 mktemp 自清理后的 `cmdSansCleanup`。两套口径不一致的后果是一条**通用豁免**：
// 命令末尾加 `; rm -rf "$D"` 就能让整条证据**静默**退出重跑池，
// 而 R-9 的守卫 `anyReproducible` 不测 DESTRUCTIVE，于是整份 resolved 记录可以哈希全编造仍 exit 0。
//
// 真实树上已经生效：M0-4[0] 与 M0-5[2] 带合法 64-hex 哈希却从未被重跑，
// 而报告逐字打印「全部 24 条」——**带哈希的实际有 26 条**。
// 报告在宣称一个它没做到的完整性。
const stripCleanup = c => /mktemp\s+-d/.test(c)
  ? String(c).replace(/;\s*rm\s+-rf?\s+"?\$\{?[A-Za-z_][A-Za-z0-9_]*\}?"?\s*$/, '')
  : String(c)
const excludedFromRerun = []
const rerunnableFinal = rerunnable.filter(e => {
  const c = stripCleanup(e.command ?? '')
  const bad = !e.command ? '缺 command'
    : DESTRUCTIVE.test(c) ? '含破坏性操作'
    : PLACEHOLDER.test(e.command) ? '含未展开占位符' : null
  if (bad) { excludedFromRerun.push({ id: e.id, idx: e.idx, why: bad }); return false }
  return true
})

const rerunResults = []
const SAMPLED = SAMPLE !== null
if (!NO_RERUN && rerunnableFinal.length) {
  // 〔R3 修复 · gate-hollow〕原写法：默认抽一条，索引 = `records.size % rerunnable.length`。
  // 注释自称「用记录总数取模轮转」，但两个操作数都是**仓库状态的常数**
  // （12 与 11），于是 `12 % 11 === 1` 恒等于 1，永不轮转——11 条可重跑证据里
  // 10 条从未被任何一次默认运行验证过。对外宣称的「8/8 全绿」是抽样器
  // 恒定选中同一条好样本的产物，不是记录可复现的证据。
  //
  // 教训：**确定性 ≠ 覆盖**。我把「绿灯必须可复现」这个正确要求，
  // 错误地实现成了「只跑固定的一条」。确定性该管的是「跑哪些」的顺序，
  // 不是「只跑哪一条」。现在默认**全跑**；抽样必须显式索取，
  // 且抽样运行会在报告里被明确标记为不完整。
  const picks = SAMPLE === null
    ? rerunnableFinal
    : [rerunnableFinal[SAMPLE % rerunnableFinal.length]]

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
    // target 与 stash 都必须在**命令跑之前**算好。
    // 〔自我更正〕初版把 stash 块放在了 execSync **之后**的判定段里——
    // 注释写着「事前控制」，位置却是事后，于是命令刚产出的文件被立刻移走，
    // 真实记录全部误红。**注释说一套、位置做另一套**是这类 bug 的典型形状，
    // 而它只在真实记录上暴露，负例套件看不见（负例的命令本来就不产出文件）。
    const cwdResolved = e.cwd ? e.cwd.replace(/^~/, process.env.HOME ?? '~') : ROOT
    const cwdFinal = existsSync(cwdResolved) ? cwdResolved : ROOT
    const target = declared
      ? (declared.startsWith('/') ? declared
         : declared.startsWith('~') ? declared.replace(/^~/, process.env.HOME ?? '~')
         : join(cwdFinal, declared))
      : out
    // ③ 新鲜度。〔R4/gate-hollow 修复〕
    //
    // 原实现比对 mtime：declared 目标的 mtime 必须晚于本次重跑起点。注释还自夸
    // 「这条是三者里唯一无法用『记录多写一个字段』绕过的——它比对的是墙上时钟」。
    // R4 用**五个字符**推翻了它：把 command 写成 `touch <那个陈旧文件>`。
    // mtime 被命令自己刷新，2020 年的伪造文件当场冒充「本次运行产出」，
    // 门打印「25/25 条哈希对上」并 PASS。
    //
    // 教训：**墙上时钟是被测方能写的。** 任何「事后观察某个属性」的判据，
    // 只要那个属性在被测方的写权限内，就不是判据。
    //
    // 现在改为**事前控制**而非事后观察：跑命令之前先把 declared 目标移走。
    // 命令若真的产出它，文件会重新出现且内容正确；命令若只是 `touch`，
    // 得到的是空文件，哈希对不上；命令若什么都不做，文件不存在，同样判红。
    // 陈旧文件这条路被物理切断，而不是被检测。
    let stashed = null
    if (declared && existsSync(target)) {
      stashed = join(tmp, `stash-${rerunResults.length}`)
      renameSync(target, stashed)
    }
    let got = null
    let err = null
    const runStart = Date.now()
    try {
      const cwd = e.cwd ? e.cwd.replace(/^~/, process.env.HOME ?? '~') : ROOT
      // 必须把整条命令套进子 shell 再重定向。
      // 〔R3 修复 · 由负例 R-12b 抓出〕原写法 `${command} > out 2>&1` 在 command
      // 含 `;` 时只把**最后一条语句**的输出重定向进 out，前面的全部丢失。
      // 现有记录都走 output_file / 尾部 shasum 分支，所以这条兜底路径一直是坏的
      // 而没人走过——一个只在负例里才会暴露的洞。
      execSync(`( ${e.command} ) > ${JSON.stringify(out)} 2>&1`, {
        cwd: existsSync(cwd) ? cwd : ROOT,
        timeout: 120_000,
        shell: '/bin/bash',
        stdio: 'ignore',
      })
    } catch (x) {
      // 命令自身非零退出是允许的——我们比对的是输出内容，不是它的退出码
      err = x.status ?? x.message
    }

    // ── 〔R3 修复 · gate-hollow〕重跑绕过 ────────────────────────────────
    // 原实现可被「命令必然失败 + output_file 指向一个早已存在的陈旧文件」
    // 完全绕过：门会打印「重跑验证 1/1 条哈希对上」并 PASS。三个根因叠加：
    //   ① declared 让记录自己声明一个**在门的临时目录之外**的绝对路径；
    //   ② 命令的退出码被 catch 捕获进 err 后**从未被任何一行检查**；
    //   ③ 没有新鲜度检查——门从不追问这个文件是不是**本次运行**产出的。
    // 三条现在各有一道断言。教训：捕获了异常却不断言，等于没捕获。
    let bypass = null


    // ② 退出码：命令失败就不可能产出被记录的输出。
    //    确实有证据命令合法地非零退出（grep 无命中、被测门本就该判红），
    //    但那种情况记录必须**显式声明** exit_code，把它变成一条可检验的断言，
    //    而不是让门默默吞掉。
    if (!bypass && err !== null) {
      const declaredExit = e.exit_code
      if (declaredExit === undefined) {
        bypass = `命令非零退出（${err}）却没有声明 exit_code —— ` +
                 `失败的命令产不出被记录的输出；若非零退出是预期的，在证据里写明 exit_code`
      } else if (Number(declaredExit) !== Number(err)) {
        bypass = `退出码对不上：记录声明 ${declaredExit}，实测 ${err}`
      }
    }

    if (existsSync(target)) {
      got = createHash('sha256').update(readFileSync(target)).digest('hex')
    }
    // 第三种形态：**命令自己把哈希打印到 stdout**。
    // `set -e; D=$(mktemp -d); …; shasum -a 256 "$D/out.txt"` 这一类——
    // 被测内容落在跑完即删的临时目录里，唯一留下的就是那行哈希。
    // 〔R5-02 修复过程中发现〕此前这两条证据被 DESTRUCTIVE 过滤器静默剔除，
    // 从没跑到这里；解除剔除后它们判红，根因是门在哈希别的东西。
    if (got !== e.raw_output_sha256 && existsSync(out)) {
      const printed = readFileSync(out, 'utf8').match(/^([0-9a-f]{64})\s/m)
      if (printed) got = printed[1]
    }
    if (got === null && stashed) {
      bypass = bypass ?? `命令没有产出它声明的 ${target}——原有文件已被本门移走，` +
                         `说明记录里的哈希来自一个**不是这条命令产生**的文件`
    }
    // 无论判定结果如何都把原文件放回去：本门是只读的审计者，不该破坏工作树。
    if (stashed && existsSync(stashed) && !existsSync(target)) renameSync(stashed, target)

    // ── excerpt 必须真的来自重跑输出 ────────────────────────────────
    // 〔R4/机器层 P1-7 修复 · 现存最大的洞〕此前 excerpt 与 answer 与实测输出
    // **完全无绑定**：把 M0-1 的结论改成与实测**完全相反**
    //（"四个库全都拿不到颜色/字号/图层，H0 成立"），command 与 sha256 一字不动，
    // 本门打印「PASS，24/24 条哈希对上」，退出码 0。
    //
    // 哈希证明的是**命令跑过**；而记录里唯一被人读、唯一驱动 doc_action 与
    // 文档改写的那部分，不受任何约束。
    // **R3 把编造从 verdict 层赶走，编造原样搬进了 excerpt 层。**
    //
    // excerpt 自述是「输出里承重的那几行逐字」，那就按字面检验：
    // 它的每一行（去掉纯分隔/省略行）都必须**逐字出现在重跑输出里**。
    // 允许节选（行的子集）与重排，不允许出现输出里没有的行。
    let excerptMiss = null
    if (!bypass && got === e.raw_output_sha256 && existsSync(target)) {
      const outText = readFileSync(target, 'utf8')
      const flat = outText.replace(/[ \t]+/g, ' ')
      const lines = String(e.excerpt ?? '').split('\n')
        .map(l => l.replace(/[ \t]+/g, ' ').trim())
        // `〔…〕` 是本仓库统一的**编者注**约定（解释这条证据的意义），
        // 它本来就不是输出的一部分，排除。其余行一律按逐字核对。
        // 长度下限只排纯分隔行，不排短内容行：`grep -c` 类命令的承重输出
        // 就是一个 `1`，把它当"没有可核对内容"是门在惩罚最干净的那种证据。
        .filter(l => l.length >= 1 && !/^[-=_.·…\s]+$/.test(l) && !/^〔/.test(l))
      const missing = lines.filter(l => !flat.includes(l))
      if (lines.length && missing.length) {
        excerptMiss = `excerpt 有 ${missing.length}/${lines.length} 行不在重跑输出里 —— ` +
                      `第一条：${JSON.stringify(missing[0].slice(0, 60))}`
      }
      if (!lines.length && String(e.excerpt ?? '').trim()) {
        excerptMiss = 'excerpt 全部由分隔符/省略号构成，不含任何可核对的内容行'
      }
    }
    if (excerptMiss) note(e.id, `evidence[${e.idx}] 的 ${excerptMiss}`)

    const hashOk = got === e.raw_output_sha256
    const match = hashOk && !bypass && !excerptMiss
    rerunResults.push({ ...e, got, match, err, bypass, excerptMiss })
    if (bypass) {
      note(e.id, `重跑 evidence[${e.idx}] 不成立：${bypass}`)
    } else if (!hashOk) {
      note(e.id, `重跑 evidence[${e.idx}] 的哈希对不上：记录 ${String(e.raw_output_sha256).slice(0, 12)}… 实测 ${String(got ?? '（无输出）').slice(0, 12)}…`)
    }
  }
  rmSync(tmp, { recursive: true, force: true })
}

// 〔R5-02〕带哈希却进不了重跑池 = 那个 64 位十六进制**没有任何人验过**。
// 它比「声明不可复现」更坏：后者至少诚实，前者看起来像证据。
for (const x of excludedFromRerun) {
  note(x.id, `evidence[${x.idx}] 带 64 位哈希却无法重跑（${x.why}）—— ` +
             `该哈希从未被验证过。要么改成可重跑的命令，要么显式声明 reproducible:false 并给理由`)
}

// ── 报告 ────────────────────────────────────────────────────────────────
const byVerdict = v => [...records.values()].filter(r => r.verdict === v).length
console.log('M0 阻塞项门\n')
console.log(`记录 ${records.size}/${Object.keys(REQUIRED).length}`)
console.log(`  resolved ${byVerdict('resolved')}   design-changed ${byVerdict('design-changed')}   still-blocked ${byVerdict('still-blocked')}`)
if (rerunResults.length) {
  const ok = rerunResults.filter(r => r.match).length
  console.log(`  重跑验证 ${ok}/${rerunResults.length} 条哈希对上` +
    (SAMPLED ? `  ⚠️ 抽样运行（--sample），共 ${rerunnable.length} 条可重跑，本次绿灯不完整`
             : `（全部 ${rerunnableFinal.length} 条）`))
} else if (NO_RERUN) {
  console.log('  重跑验证：已跳过（--no-rerun）⚠️ 本次绿灯不构成「记录来自实测」的证据')
} else {
  console.log('  重跑验证：无可重跑的 resolved 记录')
}
console.log()

if (!problems.length) {
  console.log(`PASS  M0 记录齐全、结构合法、${rerunResults.length} 条证据全部重跑且哈希一致`)
  process.exit(0)
}

console.log(`FAIL  ${problems.length} 处`)
for (const p of problems) console.log(`      ${p}`)
process.exit(1)
