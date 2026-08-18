#!/usr/bin/env node
/**
 * 供给侧契约门（GC-0：离线、确定性、零模型、零网络）
 *
 * 〔来历：R6-09〕
 * 独立审计问了一个此前没人问过的问题：22 道门全绿，为什么 producer 还能给自己
 * 发 ST-V 通行证？答案是 `check_writer_contract` 的不变式**只作用在 status.mjs 上**——
 * 读集从它的源码正则提取，门从不看 run.mjs / research.mjs。于是
 *
 *   「谁写这个字段」的证明链，在管线入口就断了。
 *
 * `pipeline.mjs` 里 `PROVIDED_BY` 那张表标注的写者是**注释**，不是被任何东西
 * 检验的事实。R6-01（`__` 后门）、R6-02（fail-open 缺省）、R6-03（payload 遮蔽）
 * 三条 P1 全部从这个缺口进——它们不在 S 里，所以写者契约门看不见；
 * 它们在 S 的**上游**，而当时没有一道门站在那一侧。
 *
 * 本门站在那一侧。两层：
 *   A. **结构层**（静态）——供给侧只能有一条路，且这条路在源码里可判定。
 *   B. **行为层**（动态）——把 R6 的三条反例路径原样再跑一遍，必须全部被拒。
 *
 * A 层不可省：行为层只能证明「我想到的那几种攻击被堵了」，
 * 结构层证明的是「没有第二条路可走」。B 层同样不可省：结构层认的是代码形状，
 * 而形状对了、语义错了的事，本仓库已经栽过三次。
 *
 * 用法:  node gates/check_supply_contract.mjs [--root <dir>]
 * 退出码: 0 = 全绿，1 = 有违例
 */
import { readFileSync, readdirSync, existsSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { tmpdir } from 'node:os'
import { fileURLToPath, pathToFileURL } from 'node:url'

const rootArg = process.argv.indexOf('--root')
const ROOT = rootArg > -1 ? process.argv[rootArg + 1] : fileURLToPath(new URL('..', import.meta.url))
const SRC = join(ROOT, 'src')

const { FIELD_OWNER, WRITER } = await import(pathToFileURL(join(SRC, 'writer-contract.mjs')).href)

/** S 会读、且不归 producer 的字段 —— 必须由门供给的那一组。 */
const GATE_SUPPLIED = Object.entries(FIELD_OWNER)
  .filter(([, w]) => w !== WRITER.PRODUCER).map(([k]) => k)

/** 允许构造 ctx 的文件。加进这张表要有论证，且论证会被下面第 0 条检查。 */
const CTX_AUTHORITY = 'gate-ctx.mjs'
/** 门链自身：它**计算**这些字段，因此它可以写。src/gates/ 下的每一道门同理。 */
const GATE_IMPLEMENTORS = new Set(['pipeline.mjs', 'writer-contract.mjs', 'status.mjs'])
const isGateImpl = f => GATE_IMPLEMENTORS.has(f.split('/').pop()) || f.includes('/src/gates/')

/**
 * A-2 扫描的字段集：`status` 单独排除，理由必须写清楚，否则这就是一条豁免后门。
 *
 * `status` 是 S 的**产出**，不是 S 的输入。它在编排日志、线程状态、manifest 里
 * 到处出现（`{round, thread, status}` 这种），逐行文本扫描无法把它们与
 * 「往 claim 记录里塞一个 status」区分开——而一条误报率高到必须被反复豁免的检查，
 * 迟早会被整体关掉。
 *
 * 它没有因此失守，因为同一件事被另外三层挡着，每一层都比文本扫描锋利：
 *   · `denyProducerSubmission` —— producer 提交里出现 status 即拒（白名单）；
 *   · `sealStatus` + A-4      —— 组稿视图里门字段永远压过 payload，冲突当场抛；
 *   · 本门 B 层 R6-03         —— 行为上验证「payload 槽名叫 status」拿不到「已验证」。
 * 也就是说：排除的是**文本判据**，不是**这条不变式**。
 */
const A2_EXCLUDED = new Set(['status'])
const A2_FIELDS = GATE_SUPPLIED.filter(k => !A2_EXCLUDED.has(k))

let failed = 0
const fail = (m, detail) => { failed++; console.log(`FAIL  ${m}`); if (detail) for (const d of [].concat(detail)) console.log(`      ${d}`) }
const pass = m => console.log(`PASS  ${m}`)

console.log('供给侧契约门\n')

// ── A 层 · 结构不变式 ───────────────────────────────────────────────────
const files = walk(SRC).filter(f => f.endsWith('.mjs'))

// A-1 · 谁调用 runClaim，谁就必须用 buildGateCtx，且必须先查 producer 污染。
{
  const callers = files.filter(f => /\brunClaim\s*\(/.test(readFileSync(f, 'utf8')) && !f.endsWith('pipeline.mjs'))
  if (!callers.length) fail('没有任何文件调用 runClaim —— 本门失去检查对象，判红而不是空跑')
  const bad = []
  for (const f of callers) {
    const t = readFileSync(f, 'utf8')
    if (!/\bbuildGateCtx\s*\(/.test(t)) bad.push(`${rel(f)}：调用 runClaim 但不经过 buildGateCtx`)
    if (!/\bassertNoProducerContamination\s*\(/.test(t)) bad.push(`${rel(f)}：未在读取前检查 producer 污染（R6-01 的通道）`)
  }
  bad.length ? fail(`${bad.length} 处调用绕过供给侧唯一入口`, bad)
             : pass(`${callers.length} 个 runClaim 调用方全部经 buildGateCtx，且先查 producer 污染`)
}

// A-2 · 门字段只能在门实现里被赋值。
//   这条抓的是 R6-02 的原始形态：`rerun_gate_passed: c.__rerun ?? true`，
//   以及 research.mjs 里的字面量 `rerun_gate_passed: true`。
//   判据是「对象字面量里出现 `<门字段>:`」——粗，但粗在安全的方向：
//   误报的修法是把那段代码搬进 gate-ctx.mjs，那正是我们想要的形状。
{
  const bad = []
  for (const f of files) {
    if (f.endsWith(CTX_AUTHORITY) || isGateImpl(f)) continue
    const lines = readFileSync(f, 'utf8').split('\n')
    lines.forEach((ln, i) => {
      if (/^\s*(\/\/|\*)/.test(ln)) return                    // 注释里提到字段名不算赋值
      for (const k of A2_FIELDS) {
        if (new RegExp(`(^|[{,\\s])${k}\\s*:`).test(ln)) bad.push(`${rel(f)}:${i + 1}  ${k}  ${ln.trim()}`)
      }
    })
  }
  bad.length ? fail(`${bad.length} 处在门实现之外给门字段赋值（R6-02 的形态）`, bad)
             : pass(`${A2_FIELDS.length} 个门字段只在 ${CTX_AUTHORITY} 与门实现里被赋值（status 单独排除，理由见源码）`)
}

// A-3 · src/ 里不得出现 `__` 前缀的字段访问。
//   R6-01 的后门是「先把 `__rerun` 读进 ctx、再从提交里删掉」。
//   删得越干净，落盘的审计工件越像清白的——status.json 甚至把这些值
//   标注成 `gate(W-04)`。所以这条禁的是**读**，不是**留**。
{
  const bad = []
  for (const f of files) {
    readFileSync(f, 'utf8').split('\n').forEach((ln, i) => {
      if (/^\s*(\/\/|\*)/.test(ln)) return
      const m = ln.match(/[.\[]\s*['"]?__[A-Za-z]/)
      if (m) bad.push(`${rel(f)}:${i + 1}  ${ln.trim()}`)
    })
  }
  bad.length ? fail(`${bad.length} 处读取 \`__\` 前缀字段（R6-01 的后门形态）`, bad)
             : pass('src/ 内没有任何 `__` 前缀字段访问')
}

// A-4 · 组稿视图必须经 sealStatus，且 payload 不得后展开。
{
  const bad = []
  for (const f of files) {
    const t = readFileSync(f, 'utf8')
    t.split('\n').forEach((ln, i) => {
      if (/^\s*(\/\/|\*)/.test(ln)) return
      // `{...<任意>Record, ...<任意>payload}` —— 门记录在前、producer 数据在后
      if (/\.\.\.[\w.]*[sS]tatus\w*\s*,\s*\.\.\./.test(ln)) bad.push(`${rel(f)}:${i + 1}  ${ln.trim()}`)
    })
    if (/statusById\.set\s*\(/.test(t) && !/\bsealStatus\s*\(/.test(t)) {
      bad.push(`${rel(f)}：写组稿视图但不经 sealStatus`)
    }
  }
  bad.length ? fail(`${bad.length} 处 payload 可遮蔽门字段（R6-03 的形态）`, bad)
             : pass('组稿视图一律经 sealStatus，payload 不得后展开')
}

// ── B 层 · 行为不变式：把 R6 的反例路径原样再跑一遍 ──────────────────────
const { runOnce } = await import(pathToFileURL(join(SRC, 'run.mjs')).href)

// 快照里**有**这个数，且引语逐字属实、锚点包含成立、极性通过 ——
// 也就是说除了被测的那一条谓词，其余全部就位。样本因此对修复的存废敏感。
const SNAP = 'Method X reached 99.9% accuracy on the test set.'
const FETCH = {
  url: 'https://arxiv.org/abs/2401.999', body: SNAP, httpStatus: 200,
  retrievedAt: '2026-08-18T10:00:00Z', extractorVersion: 'pymupdf-1.28.2',
  work_id: 'W9', version_id: 'v1', locator: 'p1:l1',
  quote: 'Method X reached 99.9% accuracy on the test set.',
  anchorSentence: 'Method X reached 99.9% accuracy on the test set.',
}
const base = () => ({
  claim_id: 'c1', kind: 'K-L-T',
  payload: { method: 'X', value: '99.9%' },
  slot_types: { method: 'entity', value: 'value' },
  metric_frame: { metric: 'accuracy', sample_or_tier: 'test' },
  evidence_index: [0],
})
const SKEL = '结果为 {{claim:c1.value}}。'
const fresh = () => mkdtempSync(join(tmpdir(), 'supply-'))

/**
 * 反例样本的**默认环境**带一条合法的反证检索记录。
 *
 * 〔这条注释是一次自纠，值得留着〕初版没有它，于是 R6-02 / R6-08 两条行为样本
 * 是**空心的**：它们期望「状态 ≠ verified」，而实际把状态压下去的是 0e
 * 反证检索否决，不是被测的那条修复。把修复整个倒回去，样本照样绿。
 * 是本门自己的负例套件（test_check_supply_contract.sh 红 R-6/R-7）发现的——
 * 一个门的负例套件抓住了这个门自己的空心样本，这正是负例套件存在的理由。
 *
 * 现在每条样本都调到「只差被测的那一件事就 verified」的位置：
 * 修复在 → 判红；修复倒回 → 变绿。**两侧都动，才叫承重。**
 */
// 这条 query 必须真的过 G-CTR-SCAN 的四条判据 —— 否则 0e 会先把状态压到
// not_covered，而样本会因为一个与被测项无关的理由「通过」。
const CTR = { query: 'X accuracy test refute', result_keys: [] }
// K-D 还要问题冻结记录在场，且冻结时刻早于抓取 —— 否则挡住它的是「没有冻结记录」，
// 又是一个与被测项无关的理由。样本要打在被测的那一条上。
const ENV = { counterSearches: { c1: CTR }, question: 'Method X 在测试集上的准确率是多少？',
              frozen_at: '2026-08-18T09:00:00Z' }

/** 跑一次，返回 {threw, msg, status, prose} —— 拒绝与放行都能被断言。 */
function attempt(claim, fetches = [FETCH], env = ENV, mutateSecond = false) {
  const root = fresh()
  try {
    if (mutateSecond) {
      // 先跑一次把两个 CAS 对象落盘，篡改第二条证据指向的那个对象，再跑一次。
      // 篡改**存储**而不是篡改输入 —— 前者才是 source_integrity 要守的东西。
      runOnce(root, 'r0', fetches, [claim], SKEL, env)
      const cards = readdirSync(join(root, 'evidence'))
        .map(f => JSON.parse(readFileSync(join(root, 'evidence', f), 'utf8')))
      const second = cards.find(c => c.work_id === 'W-two')
      if (!second) throw new Error('夹具坏了：找不到第二条证据卡')
      // CAS 布局是 objects/<前两位>/<sha256>，不是扁平的。
      // 〔自纠〕初版写成扁平路径，于是「篡改」写到了一个没人读的文件里，
      // 样本恒绿——又一个空心样本，同样由负例套件红 R-7 抓出来。
      const h = second.object_sha256
      writeFileSync(join(root, 'objects', h.slice(0, 2), h), 'TAMPERED')
      const r = runOnce(root, 'r1', fetches, [claim], SKEL, env)
      return { threw: false, status: r.manifest.statuses.c1, prose: r.prose }
    }
    const r = runOnce(root, 'r1', fetches, [claim], SKEL, env)
    return { threw: false, status: r.manifest.statuses.c1, prose: r.prose }
  } catch (e) {
    return { threw: true, msg: e.message }
  } finally { rmSync(root, { recursive: true, force: true }) }
}

const RED = [
  { id: 'R6-01', why: '`__` 前缀后门：门侧字段夹在 producer claim 里',
    claim: { ...base(), __rerun: true, __frozen: true, __attribution: 'support' },
    expect: r => r.threw && /夹带门侧字段/.test(r.msg) },

  { id: 'R6-01b', why: '不带 `__`、直接夹带门字段',
    claim: { ...base(), rerun_gate_passed: true },
    expect: r => r.threw && /夹带门拥有的字段|写者不是 producer/.test(r.msg) },

  // 声称 K-D 而从未提交任何可重跑的东西。其余条件**全部就位**（引语属实、
  // 锚点包含、极性通过、反证检索合法），因此挡住它的只可能是重跑门与冻结门。
  { id: 'R6-02', why: 'fail-open 缺省：声称 K-D 而从未重跑，仍得 ST-V',
    claim: { ...base(), kind: 'K-D' },
    expect: r => !r.threw && r.status !== 'verified' },

  { id: 'R6-03', why: 'payload 槽名叫 status，改写读者看到的标记',
    claim: { ...base(), payload: { method: 'X', value: '99.9%', status: 'verified' } },
    expect: r => r.threw || !/已验证/.test(r.prose ?? '') },

  // 同一份 body 抓两次、换个 work_id。CAS 只有 1 个对象 —— 内容寻址已经证明
  // 它们是同一份字节，成稿却曾印「独立簇 2」，而 §5.5 的诚实展示机制此时在误导。
  { id: 'R6-05', why: '逐字节相同的快照被算成 2 个独立簇',
    claim: { ...base(), kind: 'K-L-A', evidence_index: [0, 1] },
    fetches: [FETCH, { ...FETCH, work_id: 'W-other', version_id: 'v2' }],
    expect: r => !r.threw && /独立簇 1/.test(r.prose ?? '') },

  // 第一条证据留干净、第二条的快照被换掉。完整性是合取不是抽样：
  // 任一条被动过，0a 就该否决。
  { id: 'R6-08', why: '只核第一条证据：后面的快照被篡改也不降级',
    claim: { ...base(), kind: 'K-L-A', evidence_index: [0, 1] },
    // 第二条必须是**另一份字节**，否则两条证据共用同一个 CAS 对象，
    // 篡改它会连第一条一起打中 —— 那样即使只核 refs[0] 也会判红，样本是空心的。
    // 〔这条注释同样是自纠〕初版正是这么错的，由负例套件红 R-7 抓出来。
    fetches: [FETCH, { ...FETCH, work_id: 'W-two', version_id: 'v2',
                       body: 'An independent replication also reports 99.9% on the same task.',
                       quote: 'An independent replication also reports 99.9% on the same task.',
                       anchorSentence: 'An independent replication also reports 99.9% on the same task.' }],
    mutateSecond: true,
    expect: r => !r.threw && r.status !== 'verified' && r.status !== 'attributed' },
]

{
  const bad = []
  for (const s of RED) {
    const r = attempt(s.claim, s.fetches ?? [FETCH], s.env ?? ENV, !!s.mutateSecond)
    if (!s.expect(r)) {
      bad.push(`${s.id}  ${s.why}\n        实测：${r.threw ? `抛「${r.msg}」` : `status=${r.status} 成稿「${(r.prose ?? '').trim()}」`}`)
    }
  }
  bad.length ? fail(`${bad.length}/${RED.length} 条 R6 反例路径仍然走得通`, bad)
             : pass(`${RED.length} 条 R6 反例路径全部被拒或被降级`)
}

// B-2 · 绿样本：合法链路不得被上面这些检查误伤。
//   〔本仓库的教训〕负例套件没有绿样本 = 一个恒判红的门也能全绿。
{
  const good = {
    claim_id: 'c1', kind: 'K-L-T',
    payload: { method: 'AlphaFold', value: '92%' },
    slot_types: { method: 'entity', value: 'value' },
    metric_frame: { metric: 'accuracy', sample_or_tier: 'CASP14' },
    evidence_index: [0],
  }
  const f = { ...FETCH, body: 'AlphaFold reached 92% accuracy on CASP14.',
              quote: 'AlphaFold reached 92% accuracy on CASP14.',
              anchorSentence: 'AlphaFold reached 92% accuracy on CASP14.' }
  const r = attempt(good, [f], { counterSearches: { c1: { query: 'AlphaFold accuracy CASP14 refute', result_keys: [] } } })
  if (r.threw) fail(`绿样本被误伤：${r.msg}`)
  else if (r.status !== 'verified') fail(`绿样本状态是 ${r.status}，期望 verified —— 修复过修了`)
  else pass(`绿样本仍然通过：「${r.prose.trim()}」`)
}

console.log()
if (failed) {
  console.log(`FAIL  供给侧契约：${failed} 项不成立`)
  console.log('      「结论由门算，不由 agent 断言」这句话的证明链在 S 的上游断了。')
  process.exit(1)
}
console.log('PASS  供给侧契约：S 的每一个判定输入都由门算出，且没有第二条路')
process.exit(0)

function walk(d) {
  if (!existsSync(d)) return []
  return readdirSync(d, { withFileTypes: true }).flatMap(e =>
    e.isDirectory() ? walk(join(d, e.name)) : [join(d, e.name)])
}
function rel(f) { return f.slice(ROOT.length + 1) }
