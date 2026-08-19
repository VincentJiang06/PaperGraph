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

/**
 * 数字的**角色**。只有「效应量/读数」彼此构成竞争读数。
 *
 * 〔留出集 H-3 抓到的〕原实现只分量纲（percent / currency / plain），
 * 于是 meta 分析里的
 *   "included data from **36 studies** and yielded … **OR = 2.19**"
 * 被判成两个同量纲读数 —— **研究数量不是效应量的另一个读法**。
 * 后果是一条完全正常的阳性发现被降级（H-3 假阳）。
 *
 * 学术写作里同一句能出现四五种角色不同的数，逐一排除：
 *   研究数 / 样本量  n = 264 · 36 studies · 3 RCTs
 *   p 值            p < 0.001 · P = .23
 *   异质性          I2 = 60% · I² = 98%
 *   置信区间        已由括号屏蔽处理
 * 它们都不是「这个量的另一个读法」，混进来只会制造假阳。
 */
const ROLE_EXCLUDE = [
  { why: '研究数/样本量', re: /\b(?:n\s*=\s*|N\s*=\s*)$|\b(?:from\s+)?$/,
    after: /^\s*(?:studies|trials|RCTs|patients|participants|subjects|nonunions|cases|篇|项|例)\b/i },
  { why: 'p 值', re: /\b[pP]\s*[<>=≤≥]\s*$/, after: null },
  { why: '异质性', re: /\bI\s*2?\s*[²]?\s*=\s*$/, after: null },
]

/**
 * 标识符里的数字**不是读数**。
 *
 * 〔留出集一 H-8 回归查出来的 · §S22〕生物标志物 `CA 19-9` 里的 `19-9`
 * 被当成了一个竞争读数，于是一条只有单一读数的句子被判成「并列了两个读法」，
 * 要求 claim 给 discriminator —— 假阳。
 *
 * **这是同一个根因的第三次出现。** 前两次的修法与注释都已入库：
 *   · `g-polarity.mjs` 的 NUMERICISH：`CA 19-9` 前面的 `for` 曾被判成否定；
 *   · `src/composer.mjs`：`CA 19-9` 曾被拆成两个"裸数字"。
 * 那条注释的原话是「**「含数字」不等于「是数字」**，这条要在两个模块里同时立住」。
 * 写的时候只数到两个模块 —— G-FRAME 是漏掉的第三个。
 *
 * 判据与另外两处保持一致：紧邻左侧是**大写字母缩写或字母**，
 * 或数字自身形如 `19-9` / `4-1BB` 这种带连字符的标识符片段。
 */
const IDENTIFIER_LEFT = /(?:\b[A-Z][A-Za-z]{0,5}\s*|[A-Za-z])$/
const looksLikeIdentifier = (before, tok, after) =>
  // 前半截：`CA |19|-9` —— 左边是缩写，自身与右边构成 `19-9`
  (IDENTIFIER_LEFT.test(before) && /^[\d.]+-[\d.]/.test(tok + after)) ||
  // 后半截：`CA 19-|9|` —— 左边已经是「缩写 + 数字 + 连字符」。
  // 少了这一条只排掉一半，剩下的那半仍然算作竞争读数（实测：H-8 仍判红）。
  /[A-Za-z]\s*[\d.]+-$/.test(before) ||
  // `IL-|6|` / `p|53|` 这类：左边是字母直接接连字符或直接接数字
  (/^-[A-Za-z\d]/.test(after) && /[A-Za-z]\s?$/.test(before))

function numbersIn(clause) {
  const out = []
  for (const m of clause.matchAll(NUM_RE)) {
    const after = clause.slice(m.index + m[0].length, m.index + m[0].length + 30)
    if (NON_READING.test(after)) continue
    const before = clause.slice(Math.max(0, m.index - 24), m.index)
    if (looksLikeIdentifier(before, m[0], after)) continue
    // 角色排除：不是「这个量的另一个读法」的数，不参与竞争
    if (ROLE_EXCLUDE.some(r => r.re.test(before) && (!r.after || r.after.test(after)))) continue
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
export function frameGate(body = '', anchor = '', discriminator = '', payloadValues = [], metricTerms = []) {
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
  // 置信区间有两种写法，都要屏蔽：
  //   带括号  "(95% CI, 683.6-1228.9)"        —— 初版只处理了这种
  //   不带括号 "; 95%CI=-121.07 - -19.29; "   —— 留出集 H-8 抓到的
  // 后者在 meta 分析里极常见（分号分隔的统计串）。不屏蔽则区间的上下界
  // 会被当成两个竞争读数，一条正常的合并估计被判成「没说是哪一个」。
  // 只屏蔽**置信区间那一段**，不屏蔽整个括号。
  //
  // 〔负例套件 F-4 抓到的 fail-open〕原实现把「含 CI 的整个括号」抹掉。
  // 而真实 meta 分析里载荷与统计量常常在**同一个括号**里：
  //   "(MD: -70.18U/L; 95%CI=-121.07 - -19.29; p<0.01; I2=98%)"
  // 整括号一抹，**载荷 -70.18 也没了** → 本门看不到任何数 → 平凡放行。
  // 那是 fail-open：一句该被检查的话，因为格式而完全绕过了这道门。
  //
  // 现在按「CI 标记 + 紧随其后的区间」定点屏蔽，两种写法都覆盖：
  //   "95% CI, $683.6 million-$1228.9 million"  （逗号 + 货币）
  //   "95%CI=-121.07 - -19.29"                  （等号 + 负数）
  const CI_SPAN = /(?:confidence\s+interval|\bCI\b|置信区间)\s*[=:：,，]?\s*\[?[^);；]{0,60}?[-–—]\s*[-−+]?[$¥€£]?[\d.]+[^);；\]]{0,12}\]?/gi
  const maskCI = t => t.replace(CI_SPAN, ' ')
  const masked = maskCI(window)
  // 分号/逗号一律切；`and` / `与` **只在两侧各有一个数时**才切。
  // 〔真实文献 T3-6 抓到的〕`the median capitalized research and development
  // investment … $985.3 million` 里的 and 是名词短语内部的，
  // 切开之后含载荷的那半句丢掉了 “median”，于是 discriminator 判成
  // 「不是锚句子句的逐字片段」—— 一个理由完全错误的红。
  // 而 `92% precision and 87% recall` 里的 and 确实分开两个读数。
  // 区别不在词性，在**两侧是否各自带一个数**：本门要找的就是并列的读数。
  const hasNum = t => /\d/.test(t)
  const clauses = masked.split(/[;；，,]/).flatMap(seg => {
    const parts = seg.split(/\sand\s|\s与\s/)
    return parts.length > 1 && parts.every(hasNum) ? parts : [seg]
  }).map(c => c.trim()).filter(Boolean)
  const aMasked = maskCI(a)
  // 锚句所在的那个子句 = **含本 claim 载荷**的那一个。
  // 〔真实中文文献 T4-1 抓到的〕原实现取「第一个是锚句子串的子句」，
  // 于是在 `…分别为100％，75％，和50％，结果发现，…杀虫率分别为73．55％和78．45％`
  // 这种句子上选中了 `分别为100％` —— 一个与载荷无关的子句，
  // 于是 discriminator「不是锚句子句的逐字片段」，判红的理由完全是错的。
  // 一道理由错了的红，和放行一样坏：它把人引去改一个没坏的地方。
  const inAnchor = clauses.filter(c => aMasked.includes(c) || c.includes(aMasked.replace(/[;；]\s*$/, '').trim()))
  const pv = (payloadValues ?? []).map(String).filter(Boolean)
  // 优先取含**带数字的载荷**的子句。
  // 〔留出集 H-2 抓到的〕原实现取「含任一载荷值」的子句，而实体槽
  // （`prevalence`）会命中一个**没有数字**的子句：
  //   "The pooled prevalence of diabetic neuropathy" ← 选中了这个
  //   "was 56.8%" / "19.5%" / "and 17.7%"            ← 三个真正的读数在这里
  // 于是 myNums 为空，本门判「锚句子句里没有数」直接放行 —— **静默失守**。
  // 三个并列患病率该触发而没触发，H-2 判对纯属巧合。
  const numeric = pv.filter(v => /\d/.test(v))
  const pick = vals => inAnchor.find(c => vals.some(v =>
    c.includes(v) || c.normalize('NFKC').includes(v.normalize('NFKC'))))
  const mine = (numeric.length ? pick(numeric) : null)
    ?? (pv.length ? pick(pv) : null)
    ?? inAnchor.sort((x, y) => y.length - x.length)[0]
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
  // discriminator 对**整个锚句**验，不只对数值子句验。
  // 〔留出集 H-1 抓到的〕英文的 `respectively` 句式里，区分项与数值**分处不同子句**：
  //   "The pooled prevalence of diabetic neuropathy, retinopathy, and nephropathy
  //    was 56.8%, 19.5%, and 17.7%, respectively."
  // `neuropathy` 在前半句，`56.8%` 在后半句。要求 discriminator 出现在数值子句里，
  // 等于要求作者用一种原文没有的句式转录 —— 而这正是本门要避免的那类
  //「把人推向错误写法」。
  // 判据的实质从来是**「它区分得开吗」**，那由下面「不出现在兄弟读数里」来保证；
  // 「它属实吗」由「出现在锚句里」来保证。两条各管一半，不必挤在同一个子句上。
  if (!aMasked.includes(d) && !a.includes(d)) {
    return { ...base, triggered: true, siblings, pass: false,
             why: `discriminator ${JSON.stringify(d)} 不是锚句的逐字片段` }
  }
  const alsoIn = siblings.filter(c => c.includes(d))
  if (alsoIn.length) {
    return { ...base, triggered: true, siblings, pass: false,
             why: `discriminator ${JSON.stringify(d)} 在 ${alsoIn.length} 个兄弟读数里也出现 —— 区分不了` }
  }
  // discriminator 不得只是把**指标名**重说一遍。
  //
  // 〔标定用例 F-22 抓到的〕`respectively` 句式里，兄弟子句往往只剩裸数字：
  //   "…of diabetic neuropathy, retinopathy, and nephropathy was 56.8%, 19.5%, and 17.7%…"
  // 兄弟读数是「19.5%」「and 17.7%」，不含主语里的任何词。
  // 于是「不出现在兄弟读数里」这一条被**平凡地满足**——
  // 主语里任何一个词都能当 discriminator，包括 `prevalence` 这个
  // 三个读数**共享**的中心词，它什么都区分不了。
  //
  // 补的判据是：discriminator 与 metric_frame 的指标名不得互为包含。
  // 指标名是「这个量叫什么」，而 discriminator 要回答「取的是哪一个读数」——
  // 用前者答后者等于没答。
  const mt = (metricTerms ?? []).map(x => String(x).toLowerCase().trim()).filter(Boolean)
  const dl = d.toLowerCase()
  const echoes = mt.find(m => m.includes(dl) || dl.includes(m))
  if (echoes) {
    return { ...base, triggered: true, siblings, pass: false,
             why: `discriminator ${JSON.stringify(d)} 只是把指标名 ${JSON.stringify(echoes)} 重说了一遍 —— 它回答的是「这个量叫什么」，不是「取的是哪一个读数」` }
  }
  return { ...base, triggered: true, siblings, pass: true }
}
