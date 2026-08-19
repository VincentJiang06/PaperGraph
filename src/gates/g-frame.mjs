/**
 * G-FRAME —— 同源竞争读数（01-CONTRACTS §metric_frame 的执行面）。
 *
 * 〔来历:外部标定测试 T2-4〕
 * OSC 2015 摘要在**同一句**里给了四个都合法的"复现率"：
 *
 *   Thirty-six percent of replications had statistically significant results;
 *   47% of original effect sizes were in the 95% confidence interval …;
 *   39% of effects were subjectively rated to have replicated …;
 *   … combining original and replication results left 68% …
 *
 * 「只有 36% 的心理学研究可以被复现」这句话**逐字转录无误**，
 * 锚点包含过、极性过、来源真实——本项目的每一道门都放行。
 * 它错在把四个判据塌成一个，而那不是转录问题，是**框架**问题。
 *
 * ── 这条能做，那条不能做 ──────────────────────────────────────────────
 *
 * 判断一句话的框架对不对，需要理解它在说什么——GC-0 做不到，本门不宣称做到。
 * 但**「原文在同一句里并列给了多个同类读数」是可机器判定的**，
 * 而这恰好是框架塌陷最常见的现场：作者从枚举里挑走一个，丢掉判据。
 *
 * 指纹：**同一句之内**并列出现的多个同量纲的数。
 *
 * 〔范围扩展 · S6 之后〕初版只认分号。分号枚举确实是学术摘要里"同一个量的
 * 多个读法"最标准的写法，但不是唯一的：
 *   "36%, 47%, and 39% respectively"        —— 逗号枚举
 *   "92% precision and 87% recall"          —— and 并列
 * 后者尤其值得触发：一条 claim 若写「模型达到 92%」并锚在这句上，
 * **它确实该说清楚是哪个指标**。
 * 现在按 `;` `，` `,` ` and ` ` 与 ` 一起切，仍然限定在**锚句所在的那一句**内
 * ——跨句的枚举不算，那是另一个量级的问题。
 *
 * 触发之后要求的不是"解释一下"，而是一个可核的东西：
 * **discriminator** —— 一段逐字取自锚句子句、且**不出现在任何兄弟子句**里的文字。
 * 它是这个读数区别于其余读数的那半句话。
 *   36% 的 discriminator = “statistically significant results”
 *   39% 的 discriminator = “subjectively rated”
 * 缺了它，或它在兄弟子句里也出现（= 区分不了），本门判 fail。
 *
 * 〔为什么用逐字而不是让作者写判据说明〕判据说明是自陈，跨语言时更没法核；
 * 逐字片段可以两侧都核：在锚句里、不在兄弟句里。两条都是字符串包含。
 *
 * 〔不宣称的部分〕没有分号枚举的框架塌陷，本门看不见。
 * 「36% 的研究可复现」若写在一篇只给了 36% 一个数的综述里，这里全绿。
 * 那种情形需要跨文献比对，不是本门的量级。
 */
export const FRAME_VERSION = 'g-frame-2026-08-19'

/** 数的量纲类别。只分粗类——同类才算竞争读数。 */
function unitClass(numTok, ctx) {
  if (/%$/.test(numTok)) return 'percent'
  if (/^\$/.test(numTok)) return 'currency'
  // 〔自纠〕初版只认 `%` 字面量，于是 “Thirty-six percent” 被归成 plain、
  // 与兄弟句的 “47%” 不同类，整条门在它本该触发的那个用例上静默放行。
  // 一道在自己的目标用例上不触发的门，等于不存在。
  if (/^\s*(?:percent|per cent)\b/i.test(ctx) || /百分点|%/.test(ctx)) return 'percent'
  return 'plain'
}

/** 一个子句里出现的数（跳过置信区间水平这类非读数用法） */
const NUM_RE = /\$?\d[\d,]*(?:\.\d+)?%?|[〇零一二三四五六七八九十]+(?=个百分点)|(?:thirty|forty|fifty|sixty|seventy|eighty|ninety|twenty)[\s-]?(?:one|two|three|four|five|six|seven|eight|nine)?(?=\s*(?:percent|per cent))/gi
const NON_READING = /(?:confidence\s+interval|\bCI\b|significance\s+level|置信区间)/i

function numbersIn(clause) {
  const out = []
  for (const m of clause.matchAll(NUM_RE)) {
    const after = clause.slice(m.index + m[0].length, m.index + m[0].length + 30)
    if (NON_READING.test(after)) continue
    out.push({ tok: m[0], cls: unitClass(m[0], after) })
  }
  return out
}

/** 锚句所在的那一句（`.`/`。` 为界，小数点不算） */
function containingSentence(body, anchor) {
  const i = body.indexOf(anchor)
  if (i < 0) return anchor
  const isEnd = (t, k) => {
    const c = t[k]
    if (/[。]/.test(c)) return true
    if (c !== '.') return false
    return !(/\d/.test(t[k - 1] ?? '') && /\d/.test(t[k + 1] ?? ''))
  }
  let start = i
  while (start > 0 && !isEnd(body, start - 1)) start--
  let end = i + anchor.length
  // 〔F-6 抓到的〕锚句自己就以句号收尾时，不该继续往后吞下一句。
  // 初版从 end 开始扫到**下一个**句号，于是把后面整段无关的分号枚举
  // 都算成了兄弟读数——正是本门最该避免的那种误伤。
  if (!isEnd(body, end - 1)) {
    while (end < body.length && !isEnd(body, end)) end++
    end = Math.min(end + 1, body.length)
  }
  return body.slice(start, end).trim()
}

/**
 * @param {string} body        快照正文
 * @param {string} anchor      锚句（逐字，通常是一个分号子句）
 * @param {string} [discriminator] claim 自带的区分片段
 * @returns {{pass:boolean, triggered:boolean, siblings:string[], why:string|null, version:string}}
 */
export function frameGate(body = '', anchor = '', discriminator = '') {
  const b = String(body), a = String(anchor).trim()
  const base = { triggered: false, siblings: [], why: null, version: FRAME_VERSION }
  if (!a || !b.includes(a)) return { ...base, pass: true, why: '锚句不在快照里 —— 由 G-QUOTE 负责' }

  // 兄弟读数的范围是**锚句所在的那一句**，不是整篇正文。
  // 〔自纠〕初版按整篇切分号，于是在全文快照上必然误伤：
  // Nature 那篇正文里到处是分号 + 数字，与 “0.96 Å 主链精度” 毫无关系，
  // 却被算成它的竞争读数。一道在全文上恒触发的门，等于把 K-L-T 关死。
  const window = containingSentence(b, a)
  // 先把**置信区间括号**整段抹掉，再切子句。
  // 〔标定用例 F-3/F-8 一起逼出来的〕逗号切分会把
  // "…(95% CI, $683.6 million-$1228.9 million)" 切成两半，CI 标记留在前半，
  // 后半只剩两个金额 → 被当成两个竞争读数。
  // 而若改成「整个子句含 CI 就整条排除」，47% 那条**合法的**竞争读数
  // 也会因为句中提到 confidence interval 而被整条丢掉（F-3 由此红过一次）。
  // 正确的粒度是：只抹掉区间本身那一段，句子的其余部分照常参与判定。
  const masked = window.replace(/[（(][^）)]*(?:confidence\s+interval|\bCI\b|置信区间)[^）)]*[）)]/gi, ' ')
  const clauses = masked.split(/[;；，,]|\sand\s|\s与\s/).map(c => c.trim()).filter(Boolean)
  const aMasked = a.replace(/[（(][^）)]*(?:confidence\s+interval|\bCI\b|置信区间)[^）)]*[）)]/gi, ' ')
  const mine = clauses.find(c => aMasked.includes(c) || c.includes(aMasked.replace(/[;；]\s*$/, '').trim()))
  if (!mine) return { ...base, pass: true, why: '锚句不构成分号子句 —— 本门只看分号枚举' }

  const myNums = numbersIn(mine)
  if (!myNums.length) return { ...base, pass: true, why: '锚句子句里没有数' }
  const myCls = new Set(myNums.map(n => n.cls))

  const siblings = clauses.filter(c => c !== mine && numbersIn(c).some(n => myCls.has(n.cls)))
  if (!siblings.length) return { ...base, pass: true, why: '没有同量纲的兄弟读数' }

  // 触发：原文并列给了多个同类读数，必须说清取的是哪一个
  const d = String(discriminator ?? '').trim()
  if (!d) {
    return { ...base, triggered: true, siblings, pass: false,
             why: `原文在同一处并列给了 ${siblings.length + 1} 个同量纲读数，claim 未声明 discriminator（取的是哪一个读法）` }
  }
  if (!mine.includes(d)) {
    return { ...base, triggered: true, siblings, pass: false,
             why: `discriminator ${JSON.stringify(d)} 不是锚句子句的逐字片段` }
  }
  const alsoIn = siblings.filter(c => c.includes(d))
  if (alsoIn.length) {
    return { ...base, triggered: true, siblings, pass: false,
             why: `discriminator ${JSON.stringify(d)} 在 ${alsoIn.length} 个兄弟读数里也出现 —— 区分不了` }
  }
  return { ...base, triggered: true, siblings, pass: true }
}
