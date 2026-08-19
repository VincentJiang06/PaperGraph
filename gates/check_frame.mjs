#!/usr/bin/env node
// G-FRAME 同源竞争读数 · 两侧标定（GC-0：离线、确定性、零模型、零网络）
//
// 本门是这套系统里第一道**不看转录、只看框架**的门。它的两侧代价方向相反：
//   触发太松 → 每条 claim 都被要求写 discriminator，作者会去写一个应付的
//   触发太紧 → 「只有 36% 的心理学研究可以被复现」照样拿到 attributed
// 所以「该触发」与「不该触发」两侧都必须有样本，缺一侧这门就说不清自己在做什么。
//
// 用法:  node gates/check_frame.mjs
// 退出码: 0 = 全部符合，1 = 有不符

import { frameGate } from '../src/gates/g-frame.mjs'

// 真实语料：OSC 2015 摘要的分号枚举（四个都合法的「复现率」）
const OSC = 'Thirty-six percent of replications had statistically significant results; '
          + '47% of original effect sizes were in the 95% confidence interval of the replication effect size; '
          + '39% of effects were subjectively rated to have replicated the original result.'
const A36 = 'Thirty-six percent of replications had statistically significant results'
const A39 = '39% of effects were subjectively rated to have replicated the original result.'

// 全文快照：分号很多，但与锚句不在同一句 —— 不得误伤
const FULLTEXT = 'We evaluated several systems on CASP14. '
  + 'AlphaFold structures had a median backbone accuracy of 0.96 A r.m.s.d.95. '
  + 'Other results are summarized as follows: method B reached 61%; method C reached 44%; method D reached 12%.'
const A096 = 'AlphaFold structures had a median backbone accuracy of 0.96 A r.m.s.d.95.'

// 单一读数：只给了一个数，不该要求 discriminator
const SINGLE = 'The estimated average out-of-pocket cost per approved new compound is $1395 million.'

// 置信区间不是一个「读数」
const WITH_CI = 'The median investment was $985.3 million (95% CI, $683.6 million-$1228.9 million).'

// 分号之外的并列形态
const AND_CLAUSE = 'The model reached 92% precision and 87% recall on the held-out set.'
const COMMA_LIST = 'Accuracy was 36%, 47%, 39% across the three evaluation criteria.'
const ONE_AND    = 'The system achieved 92% accuracy and was released under an open license.'
const NOUN_AND   = 'The median capitalized research and development investment was estimated at $985.3 million.'
// 逐字取自 Wouters et al., JAMA 323(9):844-853 (2020)。
const WOUTERS = 'After accounting for the costs of failed trials, the median capitalized research and '
  + 'development investment to bring a new drug to market was estimated at $985.3 million '
  + '(95% CI, $683.6 million-$1228.9 million), and the mean investment was estimated at '
  + '$1335.9 million (95% CI, $1042.5 million-$1637.5 million) in the base case analysis.'

// [编号, 期望pass, 正文, 锚句, discriminator, 说明]
const CASES = [
  // ── 该触发且该拦 ────────────────────────────────────────────────────
  ['F-1', false, OSC, A36, '',
   '★ T2-4：原文并列 3 个同量纲读数，claim 未声明取的是哪一个'],
  ['F-2', false, OSC, A36, '统计显著',
   'discriminator 不是锚句子句的逐字片段（中文写的，核不了）'],
  ['F-3', false, OSC, A36, 'replication',
   '★ discriminator 逐字属实，但兄弟句 “the replication effect size” 里也有它 —— 区分不了'],

  // ── 该触发且该放行 ──────────────────────────────────────────────────
  ['F-4', true,  OSC, A36, 'statistically significant results',
   '★ 判据说清楚了：这半句只在 36% 那一读里出现'],
  ['F-5', true,  OSC, A39, 'subjectively rated',
   '同一篇的另一个合法读数，判据不同'],

  // ── 不该触发 ────────────────────────────────────────────────────────
  ['F-6', true,  FULLTEXT, A096, '',
   '★ 全文快照：别处有分号枚举，但不在锚句所在的那一句 —— 不得误伤'],
  ['F-7', true,  SINGLE, SINGLE, '', '原文只给了一个数'],
  ['F-8', true,  WITH_CI, WITH_CI, '', '★ 置信区间的 95% 不是一个竞争读数'],
  ['F-9', true,  OSC, '这句话不在快照里。', '', '锚句不在快照里 —— 由 G-QUOTE 负责，本门不越权'],

  // ── 分号之外的并列形态（范围扩展） ─────────────────────────────────
  // 初版只认 `;`。分号是最标准的写法但不是唯一的，下面两种同样是
  // 「同一句里并列多个同量纲读数」，而且第二种尤其该触发。
  ['F-10', false, AND_CLAUSE, AND_CLAUSE, '',
   '★ `and` 并列：92% precision 与 87% recall —— 写「模型达到 92%」必须说是哪个指标'],
  ['F-11', true,  AND_CLAUSE, AND_CLAUSE, 'precision',
   '同上，说清楚了就放行'],
  ['F-12', false, COMMA_LIST, COMMA_LIST, '',
   '★ 逗号枚举：三个同量纲读数'],
  ['F-13', true,  ONE_AND, ONE_AND, '',
   '★ `and` 连的不是两个读数（一个数 + 一段文字）—— 不得误伤'],
  ['F-15', true,  WOUTERS, WOUTERS, 'median',
   '★★ 真实的那句（Wouters 2020）：中位数与均值并列，而 `research and development` 里的' +
   ' and 是名词短语内部的。切开它会让含载荷的半句丢掉 median —— ' +
   ' F-14 的合成样本**不能鉴别**这条判据（切开后前半句没数字，本来就不算兄弟读数），' +
   ' 是负例套件 F-3 抓出来的空心样本。'],
  ['F-14', true,  NOUN_AND, NOUN_AND, 'median',
   '〔空心样本，留作对照〕它看起来覆盖了「名词短语内部的 and」这条判据，实则不能鉴别：' +
   ' 切开后前半句没有数字，本来就不算兄弟读数。真正有鉴别力的是上面的 F-15。'],
]

let bad = 0
console.log('同源竞争读数门 · 两侧标定\n')
console.log(`${'编号'.padEnd(6)}${'期望'.padEnd(6)}${'实测'.padEnd(6)}${'触发'.padEnd(6)}说明`)
console.log('─'.repeat(100))
for (const [id, want, body, anchor, disc, why] of CASES) {
  const r = frameGate(body, anchor, disc)
  const ok = r.pass === want
  if (!ok) bad++
  console.log(`${id.padEnd(6)}${String(want).padEnd(6)}${String(r.pass).padEnd(6)}${String(r.triggered).padEnd(6)}${why}${ok ? '' : '   ← 不符'}`)
  if (!ok) console.log(`${' '.repeat(24)}理由：${r.why}`)
}

// 两侧都必须有样本，且「触发」这件事本身必须真的发生过
const triggered = CASES.filter(([, , b, a, d]) => frameGate(b, a, d).triggered).length
const notTriggered = CASES.length - triggered
if (!triggered) { bad++; console.log('\nFAIL  没有任何样本触发本门 —— 那它测的是一个不存在的能力') }
if (!notTriggered) { bad++; console.log('\nFAIL  没有任何样本不触发 —— 恒触发的门等于把 K-L-T 关死') }

console.log()
if (bad) { console.log(`FAIL  ${bad} 处不符`); process.exit(1) }
const denied = CASES.filter(c => !c[1]).length
console.log(`PASS  同源竞争读数 ${CASES.length} 条（拦 ${denied} / 放 ${CASES.length - denied}；触发 ${triggered} / 不触发 ${notTriggered}）全部符合`)
