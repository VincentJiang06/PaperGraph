#!/usr/bin/env node
/**
 * 端到端管线门 —— 本项目第一条产品链路的验收。
 *
 * 它断言的不是「代码跑得起来」，而是**几条产品主张在真实链路上成立**：
 *   ① 合法转录拿得到 ST-V（否则 §2.4 矩阵 K-L-T 的 ✅ 是空头支票）
 *   ② 从否定句里取数字**拿不到** ST-V（P1-C，产品层闭合）
 *   ③ producer 夹带任何判定字段 → 拒绝（R5 第 5 条预测的守卫）
 *   ④ 没做反证检索 → ST-N（§7.2.3「逃不过的只有这一条」）
 *
 * 两侧都要有样本：只测「该红的红」的门会朝保守方向漂，
 * 把合法转录也判掉——那正是 R5 第 2 条预测的钳形夹的一侧。
 */
import { fileURLToPath } from 'node:url'
import { join } from 'node:path'

const rootArg = process.argv.indexOf('--root')
const ROOT = rootArg > -1 ? process.argv[rootArg + 1] : fileURLToPath(new URL('..', import.meta.url))
const { runClaim, GATE_VERSION } = await import(join(ROOT, 'src/pipeline.mjs'))

const CTX = {
  snapshotText: '该方法达到了 92% 的准确率。我们在三个数据集上验证了这一结果。',
  anchorSentence: '该方法达到了 92% 的准确率。',
  quote: '该方法达到了 92% 的准确率',
  source_integrity: 'intact', evidence_grade: 'G5', retention_tier: 'A',
  budget_state: 'ok', counter_evidence_found: false,
  // `counter_evidence_searched` **不再由 ctx 递进来**——它必须由 G-CTR-SCAN 算出来。
  counterSearch: { query: '该方法 92% 准确率 反驳', result_keys: [] },
  rerun_gate_passed: true, question_frozen: true, inference_gate_passed: true,
  attribution_verdict: 'support', chart_extracted: false, flags: [],
}
const SUB = { claim_id: 'c-001', kind: 'K-L-T', payload: { metric: '92%' },
              slot_types: { metric: 'value' },
              metric_frame: { metric: '准确率' },
              evidence_refs: [{ work_id: 'W1' }, { work_id: 'W2' }] }
const NEG = { ...CTX, anchorSentence: '该方法并未达到 92% 的准确率。',
              snapshotText: '该方法并未达到 92% 的准确率。', quote: '该方法并未达到 92% 的准确率' }

// [id, submission, ctx, 期望（'deny' 或状态值）, 说明]
const CASES = [
  ['E-1', SUB, CTX, 'verified',
   '合法转录 → ST-V（假阳侧的对照：门不得把合法转录判掉）'],
  ['E-2', SUB, NEG, 'attributed',
   'P1-C：从否定句里取数字 → **拿不到 ST-V**，落 sub_mode=A'],
  ['E-3', { ...SUB, polarity_scope_passed: true }, NEG, 'deny',
   'producer 夹带 L1-c 的结论（R5 第 5 条预测的最省力出口）'],
  ['E-4', { ...SUB, status: 'verified' }, CTX, 'deny', 'producer 夹带 status（I-W1）'],
  ['E-5', SUB, { ...CTX, counterSearch: undefined, counter_evidence_searched: true }, 'not_covered',
   '没有 counter_search 记录却递一个 true 进来 → 仍判 0e（fail-closed，§7.2.3）'],
  ['E-5b', SUB, { ...CTX, counterSearch: { query: '该方法 92% 准确率 反驳 质疑 争议 撤稿', result_keys: [] } },
   'not_covered', '模板攻击 query（堆 NEG-LIT）→ 不算搜过 → 0e'],
  // 〔R6-06 修复后改写〕`counter_evidence_found` 不再由 ctx 递进来——它同样由
  // G-CTR-SCAN 算：声称找到 W-counter，就必须核对本 run 确实抓过它 ((e′))。
  // 原写法 `{...CTX, counter_evidence_found: true}` 现在会被管线覆盖掉，
  // 于是这条用例**自动变成了「递一个 true 进来无效」的回归**——正是想要的形状。
  ['E-6', SUB, { ...CTX, knownWorkIds: new Set(['W-counter']),
                 counterSearch: { query: '该方法 92% 准确率 反驳', result_keys: ['W-counter'] } },
   'contested', '找到反例（结果键可复核）→ 2a 吸收态'],
  ['E-6b', SUB, { ...CTX, counter_evidence_found: true }, 'verified',
   '递一个 counter_evidence_found=true 进来无效 —— 它由门算（R6-06）'],
  ['E-6c', SUB, { ...CTX, knownWorkIds: new Set(),
                 counterSearch: { query: '该方法 92% 准确率 反驳', result_keys: ['我编的'] } },
   'not_covered', '捏造的结果键 → (e′) 判红 → 不算搜过 → 0e'],
  ['E-7', SUB, { ...CTX, budget_state: 'exhausted' }, 'not_covered', '预算耗尽 → 0f'],
  ['E-8', SUB, { ...CTX, evidence_grade: 'G1' }, 'not_covered', 'G1 不得承重 → §3.4'],
  ['E-9', { ...SUB, evidence_refs: [{ work_id: 'W1' }] }, CTX, 'verified',
   'K(K-L-T)=1，单簇够 —— 转录只需要一个真实锚点'],
  ['E-10', { ...SUB, kind: 'K-L-A' }, { ...CTX, attribution_verdict: 'support' }, 'attributed',
   'K-L-A 上限 ST-A（2 簇达标）'],
  ['E-11', { ...SUB, kind: 'K-L-A', evidence_refs: [{ work_id: 'W1' }] },
   { ...CTX, attribution_verdict: 'support' }, 'unverified',
   'K(K-L-A)=2，单簇不足 → 降一档'],
  ['E-12', SUB, { ...CTX, quote: '该方法达到了 99% 的准确率' }, 'unverified',
   '引语不是快照的子串 → 0d'],
]

let pass = 0, failed = 0
console.log('端到端管线门\n')
console.log(`${'用例'.padEnd(6)} ${'实测'.padEnd(12)} ${'期望'.padEnd(12)} 说明`)
console.log('-'.repeat(84))
for (const [id, sub, ctx, want, desc] of CASES) {
  const r = runClaim(sub, ctx)
  const got = r.ok ? r.statusRecord.status : 'deny'
  const ok = got === want
  if (ok) pass++; else failed++
  console.log(`${id.padEnd(6)} ${got.padEnd(12)} ${String(want).padEnd(12)} ${desc}${ok ? '' : '   ← 偏离'}`)
}

// 门产出必须带自证签名（W-08）——前代四份 gate_report 无法复核正是因为缺它
const rep = runClaim(SUB, CTX)
for (const k of ['generator_version', 'inputs_hash']) {
  if (!rep.gateReport?.[k]) { failed++; console.log(`FAIL  gate_report 缺自证签名字段 ${k}（W-08）`) }
}
// 同输入必须同 inputs_hash（S 的纯函数性延伸到管线）
if (rep.gateReport.inputs_hash !== runClaim(SUB, CTX).gateReport.inputs_hash) {
  failed++; console.log('FAIL  同输入两次运行的 inputs_hash 不同 —— 管线不是确定性的')
}

console.log()
if (failed) { console.log(`FAIL  ${failed}/${CASES.length} 条偏离`); process.exit(1) }
console.log(`PASS  端到端 ${CASES.length} 条（含 2 条 deny、1 条假阳对照）全部符合；gate_report 带自证签名且确定性`)
