#!/usr/bin/env node
/**
 * L1-c 极性作用域门（GC-0）。
 *
 * 〔为什么它必须有自己的门〕R5 的第 2 条预测：
 * > L1-c 守着产品**唯一**一条文献 ST-V 通道，实现落点为 0，标定集不存在。
 * > 假阳偏高 ⇒ 合法转录被降到 ST-A ⇒ §2.4 矩阵 K-L-T 那个 ✅ 兑现不了
 * > （将是 C-1、C-6 之后同一失败模式的第三次）；假阴偏高 ⇒ P1-C 原始构造复活。
 *
 * 本门是那个标定集的第一版：**两侧都要有样本**——
 * 假阳侧（合法转录必须 pass）与假阴侧（P1-C 构造必须 fail）各占一半，
 * 只测一侧的门会朝那一侧漂。
 */
import { fileURLToPath } from 'node:url'
import { join } from 'node:path'

const rootArg = process.argv.indexOf('--root')
const ROOT = rootArg > -1 ? process.argv[rootArg + 1] : fileURLToPath(new URL('..', import.meta.url))
const { polarityScope } = await import(join(ROOT, 'src/gates/g-polarity.mjs'))

// [id, 句子, 载荷字段, 下一句, 期望 pass, 说明]
const CASES = [
  // ── 假阴侧：必须判 fail（否则 P1-C 的原始构造复活） ────────────────────
  ['NT-L-32a', '该方法并未达到 92% 的准确率。', ['92%'], '', false,
   'P1-C 原始构造（中）：否定句里取数字'],
  ['NT-L-32b', 'The method did not reach 92% accuracy.', ['92%'], '', false,
   'P1-C 原始构造（英）'],
  ['NT-L-32c', '我们无法复现原文报告的 3.2 倍加速。', ['3.2 倍加速'], '', false,
   'NEG-S「无法」'],
  ['NT-L-34',  '如果使用更大的批量，该方法可达 92%。', ['92%'], '', false,
   'NEG-C 条件句 —— 作用域必须延到句末（S2 实现期修正）'],
  ['NT-L-37',  '尚不清楚该方法能否达到 92%。', ['92%'], '', false, 'NEG-Q 疑问未定'],
  ['NT-L-38',  '有人认为该方法达到了 92%。', ['92%'], '', false, 'NEG-R 他人主张'],

  // ── 假阳侧：必须判 pass（否则合法转录被降级，K-L-T 的 ✅ 兑现不了） ─────
  ['NT-L-33',  '该方法达到了 92% 的准确率。', ['92%'], '', true, '绿控：肯定句同载荷'],
  ['NT-L-35',  '该方法并未达到 92% 的准确率。', ['并未达到 92%'], '', true,
   '载荷自带否定词 → 载荷断言的就是那个否定命题'],
  ['NT-L-36',  '该方法达到了 92% 的准确率，但未在中文语料上验证。', ['92%'], '', true,
   '否定在**别的子句**里，作用域不覆盖载荷'],
  ['NT-L-39',  'We report 92% accuracy on the full benchmark.', ['92%'], '', true,
   '绿控（英）'],
  ['NT-L-40',  '该带宽（band）为 92%。', ['92%'], '', true,
   '「band」内含 and，不得被误判为并列连词边界'],

  // ── S3 自攻补入（`.attack/self-attack-s3.json` SA-1 / SA-2） ─────────
  // 词表是**有限枚举**，下面 5 种否定/限定形态此前全部拿到 ST-V，
  // 而 K-L-T 是产品唯一一条文献 ST-V 通道——它们是它的直通车。
  ['NT-L-41', 'The method hardly reaches 92% accuracy.', ['92%'], '', false, '程度否定 hardly'],
  ['NT-L-42', 'The method barely reaches 92% accuracy.', ['92%'], '', false, '程度否定 barely'],
  ['NT-L-43', 'The method falls short of 92% accuracy.', ['92%'], '', false,
   '短语否定 falls short of（同时是重叠匹配去重的回归：它与 short of 是同一个否定，不得被当成双重否定相消）'],
  ['NT-L-44', 'The method achieves at most 92% accuracy.', ['92%'], '', false,
   '上界限定：「至多 92%」与「达到 92%」是两个不同的断言'],
  ['NT-L-45', '该方法仅在理想条件下才能达到 92%。', ['92%'], '', false, '范围限定 仅…才'],
  ['NT-L-46', '该方法真的达到了 92% 吗？', ['92%'], '', false,
   '反问：问号让整个命题都不是断言，作用域覆盖全句'],
  // 假阳侧：双重否定 = 肯定，载荷合法
  ['NT-L-47', '该方法不是没有达到 92% 的准确率。', ['92%'], '', true,
   '**双重否定 = 肯定**。同一子句内 NEG-S 命中偶数次相消——这是 R5 第 2 条预测的假阳侧'],

  // ── R6-04 · 前置位白名单（NEG-P）的两侧标定 ──────────────────────────
  // 独立攻击者的判决：扩表追不上构造，25 条表外形态里 22 条直通 ST-V。
  // 下面的红样本全部取自它当场给出的那批形态；绿样本是**同等重要的另一半**——
  // 一条 fail-closed 判据若没有绿样本，「凡数值皆降级」也能全绿。
  ['NT-L-44',  'AlphaFold achieved less than 92% accuracy on CASP14.', ['92%'], '', false,
   '前置位 than —— 表外比较级，黑名单追不上，白名单接住'],
  ['NT-L-45',  'The method reports below 92% accuracy.', ['92%'], '', false, '前置位 below'],
  ['NT-L-46',  'Accuracy was as low as 92%.', ['92%'], '', false, '前置位 as low as'],
  ['NT-L-47',  'The system reached at most 92% accuracy.', ['92%'], '', false, '前置位 at most（上界限定）'],
  ['NT-L-48',  '准确率低于 92%。', ['92%'], '', false, '前置位 低于'],
  ['NT-L-49',  '准确率不足 92%。', ['92%'], '', false, '前置位 不足'],
  ['NT-L-50',  '该方法号称达到 92%。', ['92%'], '', false, '他人主张 号称（NEG-R 补入）'],
  ['NT-L-51',  'The result was later retracted; the method claimed 92%.', ['92%'], '', false,
   '撤稿 + 他人主张，两者都是 R6-04 当场给出的表外形态'],
  // 绿控：合法转录必须仍然通过，否则修复过修，K-L-T 的 ✅ 兑现不了
  ['NT-L-52',  'AlphaFold reached 92% accuracy on CASP14.', ['92%'], '', true, '绿控：reached'],
  ['NT-L-53',  'Accuracy of 92% was reported.', ['92%'], '', true, '绿控：介词 of'],
  ['NT-L-54',  '92% accuracy was observed on CASP14.', ['92%'], '', true, '绿控：句首（前置位为空）'],
  ['NT-L-55',  '准确率为 92%。', ['92%'], '', true, '绿控：系词 为'],
  ['NT-L-56',  'We obtained 92% accuracy.', ['92%'], '', true, '绿控：obtained'],
  ['NT-L-57',  '该模型取得了 92% 的准确率。', ['92%'], '', true, '绿控：取得了（体标记须被剥掉）'],
]

let pass = 0, failed = 0
console.log('L1-c 极性作用域门\n')
console.log(`${'用例'.padEnd(11)} ${'实测'.padEnd(6)} ${'期望'.padEnd(6)} 说明`)
console.log('-'.repeat(76))
for (const [id, sent, payload, next, want, desc] of CASES) {
  const r = polarityScope(sent, payload, next)
  const ok = r.pass === want
  if (ok) pass++; else failed++
  console.log(`${id.padEnd(11)} ${(r.pass ? 'pass' : 'fail').padEnd(6)} ${(want ? 'pass' : 'fail').padEnd(6)} ${desc}${ok ? '' : '   ← 偏离'}`)
}

// ── 跨句极性 · 两侧标定 ───────────────────────────────────────────────
// 外部标定测试 T3-4 让这条已认账的假阴在真实数据上兑现：
//   Prasad & Mailankody 摘要「…is $2.7 billion.」「However, this analysis lacks…」
// 单取上句判 pass，成稿印「已归因」——而那篇正是在反驳这个数。
// 现在按**下一句是否以转折词开头**分两档，两侧都要有样本。
const A_PRASAD = 'A recent estimate of R&D spending is $2.7 billion (2017 US dollars).'
const CROSS = [
  ['X-1', false, A_PRASAD, '$2.7 billion', 'However, this analysis lacks transparency and independent replication.',
   '★ T3-4：转折句首 + 否定 → 参与判定'],
  ['X-2', false, '该方法达到 92%。', '92%', '然而，我们没有复现出这一结果。', '中文转折句首 + 否定'],
  ['X-3', true,  A_PRASAD, '$2.7 billion', 'No funding was received for this study.',
   '★ 非转折句首的否定 → 不参与判定（无关否定的假阳侧）'],
  ['X-4', true,  A_PRASAD, '$2.7 billion', 'However, the estimate was later updated.',
   '转折句首但无否定 → 不得判 fail'],
  ['X-5', true,  A_PRASAD, '$2.7 billion', '', '没有下一句'],
]
console.log()
console.log('跨句极性')
console.log('─'.repeat(88))
for (const [id, want, anchor, payload, next, desc] of CROSS) {
  const r = polarityScope(anchor, [payload], next)
  const ok = r.pass === want
  if (ok) pass++; else failed++
  console.log(`${id.padEnd(11)} ${(r.pass ? 'pass' : 'fail').padEnd(6)} ${(want ? 'pass' : 'fail').padEnd(6)} ${desc}${ok ? '' : '   ← 偏离'}`)
}
// 非转折的否定仍必须**被报出来**，不能因为不判定就静默
const quiet = polarityScope(A_PRASAD, ['$2.7 billion'], 'No funding was received for this study.')
if (!quiet.knownLimitation) {
  failed++
  console.log('FAIL  非转折句首的跨句否定既不判定也不报告 —— 那等于它不存在')
} else {
  console.log(`\n已知未修（每次运行都必须可见）：${quiet.knownLimitation}`)
}

console.log()
if (failed) { console.log(`FAIL  ${failed}/${CASES.length + CROSS.length + 1} 条偏离`); process.exit(1) }
// 〔自我更正〕这行原本把「假阴侧 6 / 假阳侧 5」**硬编码**在字符串里，
// 补入自攻用例后 6+5 ≠ 18 —— 一个自述数字与实测不符，正是本项目一直在抓的东西。
const negSide = CASES.filter(c => c[4] === false).length
const posSide = CASES.filter(c => c[4] === true).length
console.log(`PASS  L1-c 标定集 ${CASES.length} 条（假阴侧 ${negSide} / 假阳侧 ${posSide}）+ 跨句 ${CROSS.length} 条全部符合，且非转折跨句否定保持可见`)
