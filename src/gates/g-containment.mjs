/**
 * G-L1-b —— 锚点包含判定（01-CONTRACTS §L1-b）。
 *
 * 〔来历:外部标定测试 T2-1 / T2-2〕
 * 原实现是 `anchorSentence.includes(payloadField)`,对真实文献有系统性假阴:
 *
 *   T2-1  payload `36`,原文写的是 “Thirty-six percent of replications…”
 *   T2-2  payload `replication`,原文写的是 “…subjectively rated to have **replicated**…”
 *
 * 两条都是**完全合法的转录**,被拦掉了。而这类拦截的代价不是"保守一点而已"——
 * 作者会去改 payload 迎合门,最后写出的是门喜欢的句子,不是准确的句子。
 *
 * ── 放松是 fail-open 方向,所以按槽型分开处理 ──────────────────────────
 *
 * 放松包含判定,等于给假阳开门。因此这里**不做**模糊匹配、不做编辑距离、
 * 不做同义词。只允许两类**可证明的等价**,且按 slot_type 分配:
 *
 *   value / comparator 槽 —— 只认**数值等价**。
 *       `36` ≡ `Thirty-six` ≡ `三十六`;`39 percent` ≡ `39%`。
 *       这是一张有限的、双向确定的映射表,不是相似度。
 *       **数字本身必须仍然是同一个数**:`36` 不会匹配 `Forty-six`。
 *
 *   entity 槽 —— 额外认**同词干**。
 *       `replication` ≡ `replicated` ≡ `replications`。
 *       保守的单次后缀剥离,词干长度下界 4,不迭代。
 *
 *   metric / sample 槽 —— **不放松**。判据与样本是 metric_frame 的骨架,
 *       T2-3 那条(声称 36% 却锚在 47% 那句)正是靠它们拦住的;
 *       在这里放松等于把那条也放走。
 *
 * 每一档都在 gates/check_containment.mjs 里有正反两侧样本。
 */
export const CONTAINMENT_VERSION = 'g-containment-2026-08-19'

// ── 数值等价 ─────────────────────────────────────────────────────────
const ONES = { zero:0, one:1, two:2, three:3, four:4, five:5, six:6, seven:7, eight:8, nine:9,
  ten:10, eleven:11, twelve:12, thirteen:13, fourteen:14, fifteen:15, sixteen:16,
  seventeen:17, eighteen:18, nineteen:19 }
const TENS = { twenty:20, thirty:30, forty:40, fifty:50, sixty:60, seventy:70, eighty:80, ninety:90 }
const CN_DIGIT = { 〇:0, 零:0, 一:1, 二:2, 两:3e-9, 三:3, 四:4, 五:5, 六:6, 七:7, 八:8, 九:9 }

/** 英文数词 → 阿拉伯数字。只处理 0–99 + hundred 的直接组合,不做任意大数解析。 */
function enWordsToDigits(text) {
  const tensAlt = Object.keys(TENS).join('|')
  const onesAlt = Object.keys(ONES).join('|')
  return text
    // twenty-one / thirty six
    .replace(new RegExp(`\\b(${tensAlt})[\\s-](${onesAlt})\\b`, 'gi'),
             (_, t, o) => String(TENS[t.toLowerCase()] + ONES[o.toLowerCase()]))
    .replace(new RegExp(`\\b(${tensAlt})\\b`, 'gi'), (_, t) => String(TENS[t.toLowerCase()]))
    .replace(new RegExp(`\\b(${onesAlt})\\b`, 'gi'), (_, o) => String(ONES[o.toLowerCase()]))
}

/** 中文数字 → 阿拉伯数字。只处理 0–99 的常见写法。 */
function cnNumeralsToDigits(text) {
  return text.replace(/[〇零一二三四五六七八九]?十[〇零一二三四五六七八九]?|[〇零一二三四五六七八九]/g, m => {
    if (!m.includes('十')) return String(CN_DIGIT[m] ?? m)
    const [hi, lo] = m.split('十')
    const t = hi === '' ? 1 : (CN_DIGIT[hi] ?? 0)
    const o = lo === '' ? 0 : (CN_DIGIT[lo] ?? 0)
    return String(t * 10 + o)
  })
}

/** 百分号统一:`39 percent` / `39 per cent` / `39 ％` → `39%` */
const unifyPercent = t => t
  .replace(/(\d)\s*(?:percent|per cent|％|%)/gi, '$1%')
  .replace(/(\d)\s*个百分点/g, '$1%')

/** 一个字符串的数值归一化形态 */
export function numericForm(s) {
  // 〔真实中文文献 T4-1 抓到的〕先 NFKC。中文期刊排版常用全角：
  // `73．55％` 用的是全角句点 U+FF0E 与全角百分号 U+FF05，
  // 而作者转录成半角 `73.55%` 是标准做法。不归一化则两侧永远对不上，
  // 一条完全合法的转录被判成假。
  // 组稿器那边早就在扫描前 NFKC 了（E-3），这边漏了——同一个坑挖了两次。
  return unifyPercent(cnNumeralsToDigits(enWordsToDigits(String(s).normalize('NFKC'))))
    .replace(/\s+/g, ' ')
}

// ── 词干（仅 entity 槽） ─────────────────────────────────────────────
const SUFFIXES = ['ions', 'ion', 'ing', 'ies', 'es', 'ed', 's', 'e']
export function stem(w) {
  const lo = String(w).toLowerCase()
  for (const suf of SUFFIXES) {
    if (lo.endsWith(suf) && lo.length - suf.length >= 4) return lo.slice(0, -suf.length)
  }
  return lo
}
const stemAll = t => String(t).toLowerCase().split(/([^a-z]+)/).map(x => /^[a-z]+$/.test(x) ? stem(x) : x).join('')

/**
 * 数字必须按**边界**比，不能按子串。
 *
 * 〔本门自己的负例 N-3 抓到的〕归一化后锚句是 “36% of replications”，
 * 载荷 `3` 是 “36” 的子串，`includes` 判过。载荷 `3` 与锚句里的 `36`
 * 不是同一个数——**放松数值等价的同时，把子串陷阱一起放进来了**。
 * 左右都要挡：`136` 不得匹配 `36`，`36` 不得匹配 `3`。
 */
const NUM_EDGE = String.raw`(?<![\d.,])`
const NUM_EDGE_R = String.raw`(?![\d.,]*\d)`
const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
function containsWithNumberBoundary(hay, needle) {
  if (!/\d/.test(needle)) return hay.includes(needle)
  return new RegExp(NUM_EDGE + esc(needle) + NUM_EDGE_R).test(hay)
}

/**
 * @param {object} payload      claim 载荷
 * @param {object} slotTypes    每个槽的 slot_type
 * @param {string} anchor       锚句(逐字)
 * @returns {{pass:boolean, per_slot:object[], version:string}}
 */
export function anchorContainment(payload = {}, slotTypes = {}, anchor = '') {
  const fields = Object.entries(payload)
  if (!fields.length) return { pass: false, per_slot: [], version: CONTAINMENT_VERSION,
                               why: '载荷为空 —— 无可比对的槽' }
  const per_slot = fields.map(([k, v]) => {
    const val = String(v)
    const type = slotTypes[k]
    // 含数字的载荷一律走边界比对——逐字命中也不例外，
    // 否则 `3` 会在锚句的 `36%` 上判过（与 numeric 档同一个陷阱）。
    if (containsWithNumberBoundary(anchor, val)) return { slot: k, type, matched: 'exact' }
    if (type === 'value' || type === 'comparator') {
      if (containsWithNumberBoundary(numericForm(anchor), numericForm(val))) {
        return { slot: k, type, matched: 'numeric' }
      }
    }
    if (type === 'entity') {
      if (stemAll(anchor).includes(stemAll(val))) return { slot: k, type, matched: 'stem' }
    }
    return { slot: k, type, matched: null }
  })
  return { pass: per_slot.every(s => s.matched), per_slot, version: CONTAINMENT_VERSION }
}

/**
 * 从快照里取出锚句**紧随其后的那一句**。
 *
 * 〔为什么必须由门算〕原实现读 `fetch.followingSentence` —— 由抓取记录递进来，
 * 也就是由生产方控制。跨句极性一旦参与判定，这个字段就成了判定输入，
 * 而一个能把它递成空串的生产方，可以让任何转折否定消失。
 * 这与 R6-01/02 是同一类洞：**判定输入不能来自被判定方**。
 * 现在它从快照正文里算出来，生产方递什么都不看。
 *
 * 找不到锚句（例如锚句本身是伪造的）返回空串——那种情况由 G-QUOTE 负责判红，
 * 本函数不替它下结论。
 */
export function followingSentenceOf(body = '', anchorSentence = '') {
  const b = String(body), a = String(anchorSentence).trim()
  if (!a) return ''
  const i = b.indexOf(a)
  if (i < 0) return ''
  const rest = b.slice(i + a.length)
  // 句末：`.`/`;`/`。`/`；` 后跟空白或结尾。小数点不算（前后皆数字）。
  let end = 0
  while (end < rest.length) {
    const c = rest[end]
    if (/[。；]/.test(c)) { end++; break }
    if (/[.;]/.test(c)) {
      const prev = rest[end - 1], next = rest[end + 1]
      if (!(/\d/.test(prev ?? '') && /\d/.test(next ?? ''))) { end++; break }
    }
    end++
  }
  return rest.slice(0, end).trim()
}
