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
]

let failed = 0
console.log('G-CTR-SCAN X-2 标定门\n')
console.log(`${'用例'.padEnd(6)} ${'实测'.padEnd(6)} ${'期望'.padEnd(6)} 说明`)
console.log('-'.repeat(80))
for (const [id, q, opts, want, desc] of CASES) {
  const r = counterQueryOk(CLAIM, q, opts)
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
console.log(`PASS  X-2 标定集 ${CASES.length} 条（假阳侧 4 / 假阴侧 6）全部符合；双侧判据无单调安全方向`)
