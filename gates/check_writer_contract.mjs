#!/usr/bin/env node
/**
 * 写者契约门 —— 断言「S 读的每一个字段都不是 producer 能写的」。
 *
 * 〔为什么这道门存在〕R5 的第 5 条预测：六个纯自报谓词
 * （question_frozen / rerun_gate_passed / anchor_containment_passed /
 *   polarity_scope_passed / inference_gate_passed / attribution_verdict）
 * **一条 deny 规则都没有**。第一个真实 run 压倒性 not_covered 之后，
 * 压力会指向最省力的出口：把它们默认写 true，绿灯就回来，而没有任何门能发现——
 * **门读的是记录，记录是自报的**。
 *
 * 这道门守的正是那条边界，且判据不是「有没有写 deny 规则」这种可以被措辞满足的东西，
 * 而是一条结构不变式：
 *
 *   ∀ f ∈ S 读取的字段：FIELD_OWNER[f] 存在，且 ≠ producer
 *
 * **读集从 `src/status.mjs` 的源码自动提取**（正则扫 `c.<field>`），
 * 因此「新加一个 S 读的字段却忘了给它配主人」会判红，而不是静默扩大自报面。
 */
import { readFileSync, existsSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

const rootArg = process.argv.indexOf('--root')
const ROOT = rootArg > -1 ? process.argv[rootArg + 1] : fileURLToPath(new URL('..', import.meta.url))

const { FIELD_OWNER, WRITER, PRODUCER_WRITABLE, denyProducerSubmission, KIND_GATED_BY } =
  await import(join(ROOT, 'src/writer-contract.mjs'))

let failed = 0
const fail = m => { failed++; console.log(`FAIL  ${m}`) }
console.log('写者契约门\n')

// ── ① 从 S 的源码提取它实际读取的字段 ───────────────────────────────────
const src = readFileSync(join(ROOT, 'src/status.mjs'), 'utf8')
// S 的入参统一叫 c；FLAG_DRIVER 的谓词入参叫 x。两者都是 claim 记录。
const readFields = new Set()
for (const m of src.matchAll(/\b[cx]\.([A-Za-z_][A-Za-z0-9_]*)\b/g)) readFields.add(m[1])
// 这些是 S 内部造出来的中间量，不是记录字段
for (const k of ['status', 'trace', 'constructor', 'message', 'length', 'some', 'includes', 'filter', 'map']) {
  readFields.delete(k)
}

if (readFields.size < 10) {
  console.log(`FAIL  只从 src/status.mjs 提取到 ${readFields.size} 个读取字段 —— 提取失效，空集上所有断言都成立，拒绝给绿灯`)
  process.exit(2)
}

// ── ② 核心不变式 ────────────────────────────────────────────────────────
const orphan = [...readFields].filter(f => !(f in FIELD_OWNER))
const producerOwned = [...readFields].filter(f => FIELD_OWNER[f] === WRITER.PRODUCER)

if (orphan.length) {
  fail(`S 读取但 §4 写权表里没有主人的字段 ${orphan.length} 个：${orphan.join('、')}\n` +
       '        没有主人 = 谁都能写 = 自报。给它在 src/writer-contract.mjs 里指派写者。')
}
// `kind` 是唯一带论证的例外：它必须由 producer 声明（那是 claim 的内容），
// 而它不构成通行证，是因为**每种 kind 的特权都由门谓词把守**。
// 论证本身在下面被逐条断言——不是一句注释。
const EXEMPT_WITH_ARGUMENT = new Set(['kind'])
const unjustified = producerOwned.filter(f => !EXEMPT_WITH_ARGUMENT.has(f))
if (unjustified.length) {
  fail(`S 读取且 **producer 可写** 的字段 ${unjustified.length} 个：${unjustified.join('、')}\n` +
       '        这是 R5 第 5 条预测的形状：被检查方给自己发通行证。')
}
// kind 的例外论证：每种 kind 的把关谓词必须存在、必须是门代码字段、必须真的被 S 读
for (const [k, preds] of Object.entries(KIND_GATED_BY)) {
  if (!preds.length) { fail(`kind ${k} 没有任何把关谓词 —— 它的例外论证不成立`); continue }
  for (const pred of preds) {
    if (FIELD_OWNER[pred] !== WRITER.GATE) fail(`kind ${k} 的把关谓词 ${pred} 不是门代码字段（当前 ${FIELD_OWNER[pred] ?? '无主'}）`)
    if (!readFields.has(pred)) fail(`kind ${k} 的把关谓词 ${pred} 根本没被 S 读 —— 把关是假的`)
  }
}
// §2 的 kind 枚举必须与本表逐一对应（漏一个 kind = 漏一条把关）
const kindsInSpec = [...new Set([...src.matchAll(/case '(K-[A-Z-]+)':/g)].map(m => m[1]))]
const ungated = kindsInSpec.filter(k => !KIND_GATED_BY[k])
if (ungated.length) fail(`实现里有 kind 分支但 KIND_GATED_BY 没覆盖：${ungated.join('、')}`)
// 〔自我更正〕原条件写作 `!orphan.length && !producerOwned.length`，
// 而 `kind` 是带论证的例外、恒在 producerOwned 里 —— 于是这条检查
// **既不 PASS 也不 FAIL，什么都不打印**。不输出的检查等于不存在。
if (!orphan.length && !unjustified.length) {
  console.log(`PASS  S 读取的 ${readFields.size} 个字段全部有主；` +
    `producer 可写的只有 ${[...EXEMPT_WITH_ARGUMENT].join('、')}，且其特权全部由门谓词把守`)
}

// ── ③ deny 规则必须真的拒（行为判据，不是「有没有这段代码」） ────────────
const probes = [
  ['status', { claim_id: 'c', kind: 'K-D', status: 'verified' }],
  ['polarity_scope_passed', { claim_id: 'c', kind: 'K-L-T', polarity_scope_passed: true }],
  ['counter_evidence_searched', { claim_id: 'c', kind: 'K-D', counter_evidence_searched: true }],
  ['flags', { claim_id: 'c', kind: 'K-D', flags: [] }],
  ['未知字段', { claim_id: 'c', kind: 'K-D', whatever_new_field: 1 }],
]
for (const [name, p] of probes) {
  if (denyProducerSubmission(p) === null) fail(`producer 提交里夹带 \`${name}\` 竟然被放行`)
}
// 防过修：合法提交必须放行
const legit = { claim_id: 'c1', kind: 'K-L-T', payload: {}, evidence_refs: [], premises: [] }
if (denyProducerSubmission(legit) !== null) {
  fail(`合法的 producer 提交被误拒：${denyProducerSubmission(legit)}`)
}
if (!failed) console.log(`PASS  deny 规则对 ${probes.length} 种越权提交全部拒绝，且不误伤合法提交`)

// ── ④ 与 01-CONTRACTS §4 的 W-04 行绑定 ─────────────────────────────────
// 文档说「这些字段的写者是门代码」，代码就必须同意。任一方漂移即红。
const contracts = readFileSync(join(ROOT, '01-CONTRACTS.md'), 'utf8')
const w04 = contracts.split('\n').find(l => /^\| W-04 \|/.test(l))
if (!w04) {
  fail('01-CONTRACTS §4 里找不到 W-04 行 —— 无法绑定')
} else {
  const gateOwned = Object.entries(FIELD_OWNER).filter(([, w]) => w === WRITER.GATE).map(([k]) => k)
  const missing = gateOwned.filter(f => !w04.includes(f))
  if (missing.length) {
    fail(`实现里判给门代码、而 W-04 行没写的字段 ${missing.length} 个：${missing.join('、')}\n` +
         '        W-04 自称「S 实际消费的**全部**判定输入」——它必须真的全。')
  } else {
    console.log(`PASS  W-04 行覆盖了实现里全部 ${gateOwned.length} 个门代码字段`)
  }
}

console.log()
if (failed) { console.log(`${failed} 处不一致`); process.exit(1) }
console.log('PASS  写者契约：S 的判定输入无一可由被检查方书写')
