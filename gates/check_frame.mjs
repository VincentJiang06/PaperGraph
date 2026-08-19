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
// 以下五句逐字取自真实 meta 分析摘要（Europe PMC 开放获取，PMID 见 tests/holdout/snapshots/SOURCES.md）
const META_OR = 'Random effect meta-analysis for stone free rate included data from 36 studies and '
  + 'yielded statistically significant higher stone free rates for LL with a pooled OR = 2.19.'
const META_P  = 'Tissue-type distribution differed by approach with a pooled OR = 1.44 (P = 0.611).'
const META_I2 = 'The pooled healing rate was 0.79 with considerable heterogeneity (I2 = 92%).'
const CI_BARE = 'The pooled results showed lower levels (MD: -70.18U/L; 95%CI=-121.07 - -19.29; p<0.01; I2=98%).'
const RESPECTIVELY = 'The pooled prevalence of diabetic neuropathy, retinopathy, and nephropathy was '
  + '56.8% (95% CI 44.9-68.7), 19.5% (95% CI 3.9-35.2), and 17.7% (95% CI 7.3-28.0), respectively.'
// 逐字取自 Wouters et al., JAMA 323(9):844-853 (2020)。
const WOUTERS = 'After accounting for the costs of failed trials, the median capitalized research and '
  + 'development investment to bring a new drug to market was estimated at $985.3 million '
  + '(95% CI, $683.6 million-$1228.9 million), and the mean investment was estimated at '
  + '$1335.9 million (95% CI, $1042.5 million-$1637.5 million) in the base case analysis.'

// [编号, 期望pass, 正文, 锚句, discriminator, 说明]
// 留出集一 H-6 的真实句子（PMID 42054172，截到分号处 —— 与流水线取到的锚句一致）
const BIOMARKER = 'The pooled results for CA 19-9 showed significantly lower levels in patients ' +
  'receiving irreversible electroporation and immunotherapy compared with those receiving ' +
  'irreversible electroporation alone (MD: -70.18U/L;'
// 同一形态，但真的并列了两个读数 —— 用来证明 F-23 不是靠「一律放行」通过的
const BIOMARKER_TWO = 'The pooled results for CA 19-9 showed lower levels with combination therapy ' +
  '(MD: -70.18U/L) and with monotherapy (MD: -45.02U/L).'

// 〔留出集二 J-6 · §S23〕真实 GWAS 摘要（PMID 42181176）：
// 一句里两个 and —— 前一个是名词短语内部的（左侧无数字），后一个真正分隔两个读数。
const TWO_ANDS = 'The functional role was examined using pharmacological inhibition ' +
  'in human preadipocytes and genetic deletion in mice. We identified three ' +
  'BMI-associated loci reaching genome-wide significance (p \u2264 5 \u00d7 10-8) ' +
  'and 49 additional loci previously implicated in obesity-related traits.'
// 科学计数法：整串是一个 p 值，不是两个读数
const SCI_PVAL = 'Genome-wide significance was set at p < 5 \u00d7 10-8 ' +
  'and the meta-analysis identified 56 variants.'
// 千分位逗号：一个数，不是两个
const THOUSANDS = 'We replicated it in an independent sample of 1,079 individuals.'
// 散文里的部分格数词不是读数。**必须与载荷分处不同子句**，
// 否则切不切都不触发 —— 那样的样本没有鉴别力（F-11 第一版就栽在这）。
const PROSE_WORD = 'Two of the mechanisms were validated, and the effect was observed in 42 patients.'
// 研究规模名词（cohorts）与效应量不同类
const COHORT_CNT = 'The analysis pooled three cohorts, and the combined odds ratio was 2.19.'
// 载荷**本身就是**样本数时：角色排除不得把它一起排掉，否则门看不到数而平凡放行
const SAMPLE_PAYLOAD = 'The study included 374,254 participants, with 4,305 individuals ' +
  'diagnosed with POAG and 369,949 controls.'

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
  // ── 数字的角色（留出集 H-3）─────────────────────────────────────────
  // 一句里可以有四五种角色不同的数，只有**效应量**彼此构成竞争读数。
  ['F-16', true,  META_OR, META_OR, '',
   '★★ 研究数不是效应量的另一个读法：`36 studies` 与 `OR = 2.19` 不构成竞争', ['2.19']],
  ['F-17', true,  META_P, META_P, '',
   '★ p 值不是读数', ['1.44']],
  ['F-18', true,  META_I2, META_I2, '',
   '★ I² 异质性不是读数', ['0.79']],
  ['F-19', true,  CI_BARE, CI_BARE, '',
   '★★ 不带括号的置信区间（meta 分析里极常见的分号统计串）不是两个竞争读数', ['-70.18']],

  // ── discriminator 对整句验（留出集 H-1）─────────────────────────────
  ['F-20', true,  RESPECTIVELY, RESPECTIVELY, 'neuropathy',
   '★★ `respectively` 句式：区分项与数值分处不同子句，discriminator 仍应算数', ['56.8%']],
  ['F-21', false, RESPECTIVELY, RESPECTIVELY, '',
   '同句未声明取哪一个 → 拦', ['56.8%']],
  ['F-22', false, RESPECTIVELY, RESPECTIVELY, 'prevalence',
   '★★ discriminator 属实、且不在兄弟读数里，但它只是把指标名重说一遍 —— 什么都没区分', ['56.8%'], ['pooled prevalence']],

  // 〔留出集一 H-8 回归查出来的 · §S22〕标识符里的数字不是读数。
  // 同一根因的第三次出现（前两次在 g-polarity 与 composer）。
  // 两条一起才有鉴别力：标识符在**左半截**和**右半截**都要被排掉，
  // 只排一半的话 `CA 19-9` 里的 `9` 仍然算竞争读数（实测过）。
  ['F-23', true, BIOMARKER, BIOMARKER, '',
   '★★ `CA 19-9` 是标志物名，不是两个读数 —— 全句只有 -70.18 一个读数，无 discriminator 也应放行',
   ['-70.18']],
  ['F-24', false, BIOMARKER_TWO, BIOMARKER_TWO, '',
   '★★ 绿的对照：同一句里**真的**并列了两个读数（-70.18 与 -45.02），此时必须拦',
   ['-70.18']],

  ['F-25', false, TWO_ANDS, TWO_ANDS, '',
   '★★ 两个 and：前一个不切（名词短语），后一个必须切 —— 否则 three 与 49 比不上，平凡放行',
   ['three']],
  ['F-26', true,  SCI_PVAL, SCI_PVAL, '',
   '★★ `5 \u00d7 10-8` 是一个 p 值，不是 10 与 8 两个读数 —— 不得以错误理由触发',
   ['56']],
  ['F-27', true,  THOUSANDS, THOUSANDS, '',
   '★★ 千分位逗号不是子句分隔符 —— 1,079 不得被切成 1 与 079',
   ['1,079']],
  ['F-28', true,  PROSE_WORD, PROSE_WORD, '',
   '★★ 假阳侧：`One of the two` 是散文不是并列读数（of 之后的数词不计）',
   ['42']],

  ['F-29', true,  COHORT_CNT, COHORT_CNT, '',
   '★★ `three cohorts` 是研究规模不是效应量 —— 不得与 OR 2.19 构成竞争读数',
   ['2.19']],

  ['F-30', false, SAMPLE_PAYLOAD, SAMPLE_PAYLOAD, '',
   '★★ 载荷本身是样本数：角色排除不得把它一起排掉 —— 否则 myNums 空集 → 静默放行',
   ['374,254']],
  ['F-31', true,  SAMPLE_PAYLOAD, SAMPLE_PAYLOAD, 'participants',
   '★★ 同句，给了能区分的 discriminator → 放行',
   ['374,254']],

  ['F-14', true,  NOUN_AND, NOUN_AND, 'median',
   '〔空心样本，留作对照〕它看起来覆盖了「名词短语内部的 and」这条判据，实则不能鉴别：' +
   ' 切开后前半句没有数字，本来就不算兄弟读数。真正有鉴别力的是上面的 F-15。'],
]

let bad = 0
console.log('同源竞争读数门 · 两侧标定\n')
console.log(`${'编号'.padEnd(6)}${'期望'.padEnd(6)}${'实测'.padEnd(6)}${'触发'.padEnd(6)}说明`)
console.log('─'.repeat(100))
for (const [id, want, body, anchor, disc, why, payload, metric] of CASES) {
  const r = frameGate(body, anchor, disc, payload ?? [], metric ?? [])
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
