#!/usr/bin/env node
/**
 * G-CTR-SCAN X-2 标定门（GC-0）。
 *
 * `counter_evidence_searched` 是 S 的 0e 前置否决项，§7.2.3 称它是
 * 「逃不过的只有这一条」。这道门决定「什么算搜过」，因此它的**两侧**都要有样本：
 *   · 假阴侧：模板攻击必须判红（否则 0e 退化为「发一条 query 就算搜过」）
 *   · 假阳侧：人写的真反证 query 必须放行（否则 0e 恒不通过 ⇒ 全 ST-N）
 * 03 §5A.0 已把本门的 `power_basis` 诚实降为 `unmeasured`——四个裁定阈值的
 * 假阳率未测。本标定集是把那个「未测」变成「测了一点」的第一步，不是终点。
 */
import { fileURLToPath } from 'node:url'
import { join } from 'node:path'
const rootArg = process.argv.indexOf('--root')
const ROOT = rootArg > -1 ? process.argv[rootArg + 1] : fileURLToPath(new URL('..', import.meta.url))
const { counterQueryOk, K_OP } = await import(join(ROOT, 'src/gates/g-ctr-scan.mjs'))

const CLAIM = {
  payload: { method: 'AlphaFold', metric: '92%' },
  slot_types: { method: 'entity', metric: 'value' },
  metric_frame: { metric: 'accuracy', sample_or_tier: 'CASP14' },
  evidence_refs: [{ work_id: 'W-support-1' }],
}
const filler = n => Array.from({ length: n }, (_, i) => 'filler' + i).join(' ')

// 跨语言夹具：metric_frame 中文、证据英文。快照/锚句由**门**递入（取自 ctx）。
const ZH_SNAP = 'The research and development costs of 106 randomly selected new drugs were obtained '
  + 'from a survey of 10 pharmaceutical firms. Capitalizing out-of-pocket costs to the point of marketing '
  + 'approval at a real discount rate of 10.5% yields a total pre-approval cost estimate of $2558 million (2013 dollars).'
const ZH_ANCHOR = 'Capitalizing out-of-pocket costs to the point of marketing approval at a real discount '
  + 'rate of 10.5% yields a total pre-approval cost estimate of $2558 million (2013 dollars).'
const ZH = { anchorSentence: ZH_ANCHOR, snapshotText: ZH_SNAP }

const CASES = [
  // ── 假阳侧：人写的真反证 query 必须放行 ────────────────────────────────
  ['X-1', 'AlphaFold accuracy CASP14 refute', { resultKeys: ['W-other'] }, true, 'NEG-3 反向文献算子'],
  ['X-2', 'AlphaFold accuracy CASP14 not reproduced', { resultKeys: [] }, true,
   'NEG + NEG-LIT **相邻** = 同一个否定，不是叠算子（标定期修正）'],
  ['X-3', 'AlphaFold accuracy CASP14 retracted', { resultKeys: [] }, true, '零命中允许'],
  ['X-4', 'AlphaFold accuracy CASP14 limitations', { resultKeys: ['W-x'] }, true, '「局限」也是反向文献算子'],

  // ── 假阴侧：模板攻击必须判红 ──────────────────────────────────────────
  ['X-5', 'AlphaFold accuracy CASP14 92%', {}, false, '原句照抄：0 个反向算子'],
  ['X-6', 'AlphaFold accuracy CASP14 refute contradict dispute retracted', {}, false,
   '堆 NEG-LIT：|NEG-LIT ∩ T(Q)| > 2 是模板攻击的指纹'],
  ['X-7', `AlphaFold accuracy CASP14 refute ${filler(12)}`, {}, false,
   `无界填充：载荷外 token 超预算 k_op=${K_OP}`],
  ['X-8', 'accuracy CASP14 refute', {}, false, '删掉锚槽（旧判据下这招能破坏子串关系）'],
  ['X-9', 'AlphaFold accuracy CASP14 refute', { resultKeys: ['W-support-1'] }, false,
   '自捞：反证检索原样捞回自己的支持证据'],
  ['X-10', 'AlphaFold accuracy CASP14 反驳 未能复现 质疑', {}, false, '中文侧堆反向词'],

  // ── 跨语言 metric_frame（外部标定测试 E1）─────────────────────────────
  // 真实用法里 metric_frame 常写中文而 query 写英文，两侧措辞永远对不上。
  // 原判据要求**每个**锚槽字面出现，于是人会写的 query 判红 2/3，
  // 整批 claim 落 not_covered —— R5 第 2 条预测的钳形夹假阳侧。
  // 现在 metric_frame 可由「落在本 claim 材料（载荷/槽值/锚句）上的 ≥2 个 token」代偿，
  // 实体槽仍是硬要求（X-8 守着这一条）。
  ['X-11', 'drug development cost $2558 million refute', { resultKeys: [], ...ZH }, true,
   '★ metric_frame 是中文、query 是英文：靠锚句里的词代偿'],
  ['X-12', 'new drug development cost estimate disputed', { resultKeys: [], ...ZH }, true,
   '★ 另一条人会写的自然语言 query'],
  ['X-13', 'AlphaFold GDT_TS refute', { resultKeys: [], ...ZH }, false,
   '★ 换了话题：0 个 token 落在本 claim 材料上 —— 代偿不得放走跑题的 query'],
  ['X-14', 'cost refute', { resultKeys: [], ...ZH }, false,
   '★ 只有 1 个锚：不指明挑战的是哪个数（原文给了三个成本数）'],
  ['X-15', `drug development cost $2558 million refute ${filler(12)}`, { resultKeys: [], ...ZH }, false,
   '★ 代偿不得削弱 (b′) 上界：无中生有的填充仍然超预算'],
]

let failed = 0
console.log('G-CTR-SCAN X-2 标定门\n')
console.log(`${'用例'.padEnd(6)} ${'实测'.padEnd(6)} ${'期望'.padEnd(6)} 说明`)
console.log('-'.repeat(80))
const ZH_CLAIM = {
  claim_id: 'c2', kind: 'K-L-T', payload: { cost: '$2558 million' }, slot_types: { cost: 'value' },
  metric_frame: { metric: '研发成本', sample_or_tier: '新药' }, evidence_refs: [{ work_id: 'W-dimasi' }],
}
for (const [id, q, opts, want, desc] of CASES) {
  const r = counterQueryOk(opts.anchorSentence ? ZH_CLAIM : CLAIM, q, opts)
  const ok = r.pass === want
  if (!ok) failed++
  console.log(`${id.padEnd(6)} ${(r.pass ? 'pass' : 'fail').padEnd(6)} ${(want ? 'pass' : 'fail').padEnd(6)} ${desc}${ok ? '' : '   ← 偏离'}`)
}

// (a′) 与 (b′) 方向相反这条性质必须可检验：单调加 token 不可能同时满足两者
const grow = counterQueryOk(CLAIM, `AlphaFold accuracy CASP14 refute ${filler(20)}`, {})
const shrink = counterQueryOk(CLAIM, 'refute', {})
console.log()
if (grow.pass || shrink.pass) {
  failed++
  console.log('FAIL  (a′) 下界与 (b′) 上界不是反向的 —— 存在单调安全方向，模板攻击可沿它走')
} else {
  console.log('性质：加 token 撞 (b′) 上界，减 token 撞 (a′) 下界 —— 无单调安全方向 ✓')
}
console.log()
if (failed) { console.log(`FAIL  ${failed} 条偏离`); process.exit(1) }
// 〔自纠〕这两个数原本是**硬编码**的「假阳侧 4 / 假阴侧 6」，补入跨语言用例后
// 4+6 ≠ 15 —— 一条自述数字与实测不符，正是本项目一直在抓的那一类，
// 而它就长在检查别人数字的门里。改成由 CASES 算出来。
const posSide = CASES.filter(c => c[3]).length
console.log(`PASS  X-2 标定集 ${CASES.length} 条（假阳侧 ${posSide} / 假阴侧 ${CASES.length - posSide}）全部符合；双侧判据无单调安全方向`)
