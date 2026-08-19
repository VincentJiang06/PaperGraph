#!/usr/bin/env node
/**
 * L1-c 的**外部**标定集 —— SA-3 循环性的第一步闭合。
 *
 * 〔为什么存在〕SA-3 认账过一条：L1-c 的算子表是有限枚举，
 * 而它的标定集（18 条）**全部由作者自己出题**——与变异测试当初的循环性同构：
 * 我按自己想得到的否定形态写词表，再按同一批想法写标定集，
 * 于是标定集永远测不出「我没想到的那些形态」。
 *
 * 这份不一样：下面每一句都是**从真实的开放获取论文摘要里逐字取出的**
 * （Europe PMC，`OPEN_ACCESS:Y`，检索式见文件末尾），我没有改动一个字符。
 * 句子里的否定形态是真实作者写的，不是我想出来的。
 *
 * 判据：每一句都在**否定或弱化**一个带数字的发现。
 * 若 L1-c 判 pass（= 没检测到否定），那就是一条**真实存在的假阴**——
 * 一条载荷取自这种句子的 claim 会拿到 ST-V/ST-A。
 *
 * 〔它证明什么、不证明什么〕
 *   证明：这些形态在真实文献里存在，且 L1-c 现在覆盖/不覆盖它们。
 *   不证明：覆盖率。13 句不是一个有代表性的样本，
 *           它们来自单一检索式，偏向医学与心理学。
 *   本文件的用处是**让漏掉的形态有名字**，不是给出一个百分比。
 */
import { polarityScope } from '../../src/gates/g-polarity.mjs'

// 逐字取自真实开放获取摘要。PMID 可核。
//
// ── 这份集子第一时间教了我一件事：我给它的期望是错的 ──────────────────
//
// 初稿把「句中含否定」直接等同于「L1-c 应判 fail」，13 句里报出 6 条假阴。
// 逐条读过之后，6 条里只有 1 条是真的。区别在一个此前没写下来过的判据：
//
//   **载荷是落在被否定的谓词里，还是被独立地肯定断言？**
//
// 这个判据在标注过程中被迫写死成一条可机械套用的话（否则「改标签迎合实现」
// 就是循环性本身）：
//
//   载荷落在**空结果算子所辖的那个子句**内（主语 + 谓语 + 附着的括号）
//   ⇒ 它是被否定的发现的一部分 ⇒ 应判 fail。
//   载荷落在**另一个子句**里 ⇒ 它是独立的肯定断言 ⇒ 应判 pass。
//   子句边界 = `and` / `;` / 分隔从句的逗号 / 句末。
//
// 这条判据对全部 17 句统一套用，没有例外。它改过两条我最初打错的标签
// （42223567、42340512），两条都是因为**同结构不同标签**被自己抓出来的。
//
//   "The 30-day mortality was 16.1% and did not differ according to the delay"
//   —— `16.1%` 是被**肯定**断言的；否定作用在「随延迟而变」上。
//      一条 claim 写「30 天死亡率为 16.1%」是完全合法的转录。
//      L1-c 放行它是**对的**。把它算成假阴，是我的判据错了，不是门错了。
//
//   "Follow-up BCVA and ΔBCVA were comparable."
//   —— 这里没有别的东西可断言：`comparable` 就是这句话的全部结论，
//      而它的意思是「无差异」。载荷取 BCVA 就是在取被否定的那个发现。
//      L1-c 放行它是**错的**——而且是词表缺口：`comparable` 不在任何表里。
//
// 所以下面每一句都带一个**我逐条判过的期望**，以及判它的理由。
// 这比一个「漏掉 N 条」的数字诚实得多，也更有用：
// 它把「L1-c 该不该管这一句」这个问题从直觉变成了可复核的逐条判断。
//
// 〔仍然存在的循环性〕期望是我判的。外部语料解决了**句子**的来源问题，
// 没有解决**标签**的来源问题——那需要另一个人来标。SA-3 只闭合了一半。

// [PMID, 句子, 载荷, 期望 pass, 理由]
const CASES = [
  // ── 载荷落在被否定的谓词里 → L1-c 应判 fail ──────────────────────────
  ['41868795', 'There was no statistically significant difference between the groups (p = 0.139, 0.372, and 0.594, respectively).',
   '0.139', false, '整句唯一的结论就是「无显著差异」，p 值是它的一部分'],
  ['41510676', 'No significant difference in salivary pH was observed between two groups (p = 0.07).',
   '0.07', false, '同上'],
  ['42306011', 'However, there was no significant difference between the groups (p>0.05).',
   '0.05', false, '同上'],
  ['42237004', 'Tissue-type distribution did not differ by approach (P = 0.611).',
   '0.611', false, '同上'],
  ['42338035', 'For other outcomes, no significant association with V̇O2peak was found.',
   'V̇O2peak', false, '「未发现关联」就是全句结论'],
  // ★ 这一条曾经是唯一的**已知未闭合**：**枚举逗号截断作用域**。
  // `no ... difference in A, B, or C (p = …)` —— A/B/C 是并列的检测项，
  // 中间的逗号是枚举分隔而非子句边界，clauseEnd 把它当成了边界，
  // 作用域止于 "salivary pH,"，够不着句末括号里的 p 值。
  //
  // 〔已闭合〕当时的判断是「要区分两种逗号，需要句法分析，非 GC-0 量级」。
  // 那个判断错在**把问题问窄了**：真正需要的不是区分逗号，
  // 而是让作用域够到句末括号。绕开逗号即可——
  //   `(p = …)` / `(95% CI, …)` / `(HR 0.79, …)` 是同一个断言的统计附注，
  //   它属于这句报告的那个发现，不属于它前面碰巧最近的那个子句。
  // 于是空结果算子的作用域延伸到**句末括号**，不管中间隔了几个逗号。
  // 它不误伤并列的肯定断言：`mortality was 16.1% and did not differ … (p = 0.816)`
  // 里的 16.1% 不在句末括号内。
  //
  // 教训：**「当前手段够不着」这个结论本身也要被攻击。**
  // 我把它写进台账 §S7/§S8 两次，都没有回头问一句「够不着的是哪一步」。
  ['42194389', 'There was no statistically significant difference in salivary pH, unstimulated whole saliva (UWS), or stimulated whole saliva (SWS) among the three groups (p = 0.343, p = 0.982, and p = 0.793, respectively).',
   '0.343', false, '★ 曾经的已知未闭合，现已由「句末括号附着于主谓」闭合'],
  ['42299533', 'Follow-up BCVA and ΔBCVA were comparable.',
   'BCVA', false, '★ 全句结论就是「无差异」，而 `comparable` 不在任何算子表里 —— 真词表缺口'],

  // ── 载荷被独立地肯定断言 → L1-c 应判 pass（放行是对的） ──────────────
  ['42057182', 'The 30-day mortality was 16.1% and did not differ according to the delay of explantation (p = 0.816).',
   '16.1%', true, '★ 16.1% 是肯定断言；否定作用在「随延迟而变」上'],
  ['42327481', 'The ovulation rates were 31.5% and 41.6% in the intervention and control groups respectively, indicating no statistically significant difference(p = 0.36).',
   '31.5%', true, '★ 两个率都是肯定断言；否定作用在「两者之差」上'],
  ['42223567', 'Overall survival did not differ (HR 0.79, 95% CI 0.57-1.11).',
   '0.79', false, '★〔标签自纠〕初稿标 pass，理由写「HR 是被报告的测量值」。但同一份集子里' +
   ' 42194389 的 p 值处于**同样的结构**（否定谓词后的括号），我标了 fail —— 两个相反的标签。' +
   ' 一致的判据是：附在被否定谓词上的括号里的值，是那个空结果的一部分。故改判 fail。' +
   ' 把判据写下来才看得见这种不一致，这是这份外部集最先产出的东西。'],
  ['41892318', 'While the overall SNV burden did not differ significantly between groups, PC patients showed distinct mutation distributions and allele frequency patterns, with cancer-exclusive variants occurring predominantly at low allele frequencies.',
   'mutation distributions', true, '载荷取的是转折**之后**那半句的肯定发现'],
  ['42340512', 'In contrast, the proportions of farms showing resistance to benzimidazoles (BZ) and imidazothiazoles (IMD) did not differ significantly from those with susceptible populations.',
   'IMD', false, '★〔标签自纠之二〕初稿标 pass，理由「IMD 是被检对象的名字」。' +
   ' 按上面写死的判据：IMD 在**被否定谓词的主语**里，与 42057182 的 16.1%（在 `and` 之前的另一个子句）' +
   ' 结构不同。同一条判据统一套用即得 fail。'],
  ['42266098', 'At baseline, BMD and Z-scores did not differ at any site (all p > 0.5).',
   '0.5', false, '整句结论是「无差异」'],

  // ── 对照：同一批检索里**肯定**发现的句子，不得误拦 ────────────────────
  ['42181139', 'After adjustment, both gonioscore groups showed significant IOP reduction at 6-month follow-up, with higher IOP reduction in the low gonioscore group (p = 0.034).',
   '0.034', true, '肯定发现'],
  ['42338035b', 'Higher V̇O2peak was significantly associated with lower heart rate across both stress-induction paradigms (b = 0.99 bpm, p = 0.002).',
   '0.99', true, '肯定发现（注意句中有 lower，不是否定）'],
  ['41665767', 'The mean of both groups (in the 6th month) showed a statistically significant difference with a tendency towards group B.',
   'group B', true, '肯定发现'],
  ['42164118', 'The proportions of adamantinomatous craniopharyngioma (ACP) in the juvenile group and adult group were 85.0% and 56.3%, respectively, with a significant difference (P = 0.024).',
   '85.0%', true, '肯定发现'],
]

console.log('L1-c 外部标定集 —— 句子逐字取自真实开放获取论文摘要（Europe PMC, OPEN_ACCESS:Y）\n')
console.log(`${'PMID'.padEnd(11)}${'实测'.padEnd(6)}${'期望'.padEnd(6)}${'命中'.padEnd(22)}理由`)
console.log('─'.repeat(112))

const wrong = []
for (const [pmid, sent, payload, want, why] of CASES) {
  const r = polarityScope(sent, [payload], '')
  const ok = r.pass === want
  if (!ok) wrong.push({ pmid, sent, payload, want, got: r.pass, why })
  const hits = (r.params.polarity_marker.join(',') || '—').slice(0, 20)
  console.log(`${pmid.padEnd(11)}${(r.pass ? 'pass' : 'fail').padEnd(6)}${(want ? 'pass' : 'fail').padEnd(6)}${hits.padEnd(22)}${why}${ok ? '' : '   ← 偏离'}`)
}

console.log('\n' + '═'.repeat(112))
const neg = CASES.filter(c => !c[3]).length
console.log(`外部句子 ${CASES.length} 条（应拦 ${neg} / 应放 ${CASES.length - neg}），偏离 ${wrong.length} 条`)
for (const w of wrong) {
  console.log(`\n  PMID ${w.pmid}  期望 ${w.want ? 'pass' : 'fail'}，实测 ${w.got ? 'pass' : 'fail'}`)
  console.log(`    ${w.sent}`)
  console.log(`    载荷 ${JSON.stringify(w.payload)} —— ${w.why}`)
}

console.log('\n〔口径〕来自单一检索式，偏医学与心理学，**不是有代表性的样本**。')
console.log('      句子是外部的，**标签是我打的** —— SA-3 的循环性只闭合了一半。')

// 本文件是**度量 + 回归**：
//   · 已知未闭合的那一条（枚举逗号）不判红，但每次运行必须打印出来。
//   · 其余任何一条偏离都判红 —— 那意味着 L1-c 在真实句子上退化了。
// 空集：曾经的那一条（42194389 枚举逗号）已闭合。
// 白名单为空时下面那段判定会走「不再出现」分支——所以它也一并改了：
// 空集是合法状态，非空集才要求那些条目真的仍然出现。
const KNOWN_OPEN = new Set()
const regressions = wrong.filter(w => !KNOWN_OPEN.has(w.pmid))
const stillOpen = wrong.filter(w => KNOWN_OPEN.has(w.pmid))
// 白名单**非空**时，其中每一条都必须真的仍然出现——
// 一条已经修好却还挂在豁免名单上的条目，是一个永远绿的假豁免。
if (KNOWN_OPEN.size) {
  const vanished = [...KNOWN_OPEN].filter(p => !stillOpen.some(w => w.pmid === p))
  if (vanished.length) {
    console.log(`\nFAIL  ${vanished.length} 条已知未闭合项不再出现（${vanished.join('、')}）`)
    console.log('      要么它被修好了（请更新 KNOWN_OPEN 并写明怎么修的），要么本文件失效了')
    process.exit(1)
  }
  console.log(`\n已知未闭合（每次运行都必须可见）：${stillOpen.length} 条`)
} else {
  console.log('\n已知未闭合：0 条')
}
if (regressions.length) {
  console.log(`FAIL  ${regressions.length} 条在真实句子上退化`)
  process.exit(1)
}
// 〔自纠〕这行原写「除已知的枚举逗号一条外全部符合」，闭合之后就不准了。
// 文案里写死具体豁免项，等于把一条会腐的自述数字塞进 PASS 行。
console.log(KNOWN_OPEN.size
  ? `PASS  外部句子 ${CASES.length} 条：除 ${KNOWN_OPEN.size} 条已知未闭合外全部符合`
  : `PASS  外部句子 ${CASES.length} 条全部符合，无已知未闭合项`)
process.exit(0)
