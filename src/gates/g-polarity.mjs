/**
 * L1-c 极性作用域检验（GC-0）—— `sub_mode` 判定式的第二个合取项。
 *
 * 规范：03-EVIDENCE-ENGINE §3.1.1.2 / EE-L-24；01-CONTRACTS §2.2.1 / §1.5 第 1 步。
 *
 * 〔它为什么承重〕K-L-T 是产品**唯一**一条文献 ST-V 通道。旧判据只有「包含检验」，
 * 论证是「载荷的每个 token 都来自源句，所以不可能出现源句没说的限定或因果方向」——
 * 该论证**只对「载荷 == 整句」成立**。载荷是源句 token 的真子集时，
 * 它可以断言源句所**否定**的东西，学术散文里最常见的形态就是否定句里带着数字：
 *
 *     源句：「该方法**并未**达到 92% 的准确率。」
 *     载荷：「92% 的准确率」        ← 包含检验通过，旧判据给 ST-V
 *
 * 本模块把那条洞堵在**路由层**（收窄 sub_mode 的判据），而不是往 T 路径加 GC-2 门——
 * 后者会恢复 C-6 当初要解决的问题。
 *
 * 〔已认账的结构性假阴，未修〕**跨句极性**：
 *     「我们检验了三种方法。没有一种达到 92%。」
 * 算子在**下一句**，A 只取 anchor_span 所在句，因此 L1-c 看不见它。
 * 03 §11.15 已认领这条；本实现在 `knownLimitation` 里把它显式报出来，不静默。
 */

// ── 四类受控极性算子表（表版本入 params；命中哪类写进 polarity_marker） ──
export const OPERATOR_TABLE_VERSION = 'L1c-ops-2026-08-18'

const NEG_S = [ // 句内否定
  '不', '未', '没有', '并非', '无', '尚未', '未能', '难以', '否认', '而非', '并不',
  'not', 'no', 'never', 'failed to', 'fail to', 'without', 'neither', 'nor',
  'unable to', 'rather than', 'contrary to', 'cannot', "did not", "does not", "do not",
  // 〔S3 自攻补入〕程度否定与短语否定。这 8 种形态此前全部拿到 ST-V，
  // 而 K-L-T 是产品**唯一**一条文献 ST-V 通道——它们是它的直通车。
  'hardly', 'barely', 'scarcely', 'falls short of', 'fall short of', 'short of',
  'far from', 'fails to', 'insufficient',
  // 〔R6-04 补入〕独立攻击者在扩表**之后**换一批表外形态复测，25 条里 22 条仍直通。
  // 这些是那一批里属于「句内否定」的部分。补它们是对的，但补表**不是**这条
  // P1 的修法——真正的修法是下面的 NEG-P 前置白名单（见该段注释）。
  '撤稿', '存疑', '是错的', '反驳', '远逊于', '未达', '达不到', '并未',
  'disproved', 'disproven', 'refuted', 'retracted', 'is false', 'overstates',
  'overstated', 'lacks', 'seldom', 'rarely', 'questionable', 'debunked',
]
// 上界限定：「至多 92%」与「达到 92%」是两个不同的断言，取载荷 92% 属越读。
const NEG_LIMIT = [
  '至多', '最多', '不超过', '仅', '只有', '充其量', '低于', '小于', '不足', '少于',
  'at most', 'up to', 'no more than', 'only', 'below', 'fewer than', 'less than',
  'as low as', 'under',
]
// 疑问/反问：句末问号或疑问助词
const NEG_INTERROG = ['吗', '呢', '?', '？']
/**
 * NEG-N —— **空结果表述**。作用域覆盖全句。
 *
 * 〔外部标定集 PMID 42299533 逼出来的〕
 *   "Follow-up BCVA and ΔBCVA were comparable."
 * 整句结论就是「无差异」，而 `comparable` 不在任何算子表里，L1-c 放行。
 *
 * 这一类的共同点是：它们**不带否定词**，却表达空结果。
 * 学术写作里这是报告 null result 最常见的措辞之一——
 * 作者不写 "did not differ"，写 "were comparable / similar / equivalent"。
 * 表外形态的问题（SA-3）在这里是具体的：不是「否定词漏了几个」，
 * 而是「有一整类不含否定词的空结果表述，此前一条都没覆盖」。
 *
 * 作用域覆盖全句的理由与 NEG-C 相同：它限定的是这句话报告的那个发现本身，
 * 而不是句中某个位置之后的部分。
 */
const NEG_N = [
  'comparable', 'similar', 'equivalent', 'on par with', 'no different',
  'did not reach significance', 'not statistically significant',
  // 空结果动词短语。它们此前只被 NEG-S 的 `not` 命中，而 NEG-S 的作用域
  // 只往**后**延——"BMD and Z-scores did not differ" 里的主语在算子之前，够不着。
  'did not differ', 'do not differ', 'does not differ', 'were not different',
  'no significant difference', 'no statistically significant difference',
  'no significant association', 'no significant effect', 'no difference',
  '相当', '相仿', '接近', '无差异', '无显著差异', '未达显著', '未见差异', '无统计学差异',
  // 〔真实中文文献 T4-5 抓到的〕中文空结果同样把被否定的主语放在算子**之前**：
  //   「但对SPH、平均草茎长度、LSP、SSP生物学产量和经济没有显著影响。」
  // 「没有」是 NEG-S，作用域只往后延，够不着它前面的 SPH。
  // 与英文那一批同理，归入 NEG-N 取子句作用域。
  '没有显著影响', '没有显著差异', '无显著影响', '无显著相关性', '无显著相关',
  '没有显著相关', '无统计学意义', '未见显著', '差异不显著', '相关性不显著',
]

const NEG_C = [ // 条件让步
  '若', '如果', '除非', '假设', '即便', '在……情况下',
  'if', 'unless', 'assuming', 'provided that', 'would', 'could',
]
const NEG_Q = [ // 疑问未定
  '是否', '能否', '有待', '尚不清楚',
  'whether', 'remains unclear', 'it is unknown',
]
const NEG_R = [ // 他人主张
  '声称', '据称', '有人认为', '号称', '自称',
  'claimed', 'alleged', 'purported', 'reportedly', 'claims to',
]
const TABLES = [['NEG-S', NEG_S], ['NEG-N', NEG_N], ['NEG-C', NEG_C], ['NEG-Q', NEG_Q], ['NEG-R', NEG_R],
                ['NEG-L', NEG_LIMIT], ['NEG-I', NEG_INTERROG]]

/**
 * NEG-P · 载荷**前置位**白名单 —— 本门唯一一条 fail-closed 的判据。
 *
 * 〔为什么必须有它：R6-04〕
 * 独立攻击者的判决是：L1-c 是**有限枚举对开放类**，而它守着产品唯一一条
 * 文献 ST-V 通道。冻结版本下 22 条表外形态中 20 条直通；作者现场扩表后，
 * 攻击者换一批表外形态复测，**25 条里仍有 22 条直通**。原话：
 *
 *   > 扩表的速度追不上构造的速度。
 *
 * 这句话是对的，而且它对**任何**黑名单都成立。所以补词表不是修法，只是止血。
 *
 * 修法是换一个方向：在**最危险的那一个位置**上，把默认从「不在黑名单就放行」
 * 翻成「不在白名单就判红」。那个位置是**紧邻数值载荷之前的那个词**——
 * `less than 92%` / `at most 92%` / `below 92%` / `as low as 92%` / `低于 92%` /
 * `不足 92%`，全部是同一个句法位置在改写同一个数字的含义。
 *
 * 翻转之后，性质变了：
 *   · 黑名单：自然语言新增一种否定形态 = 一条免费的 ST-V 直通车；
 *   · 白名单：自然语言新增一种否定形态 = 一次**降级**。
 * 失守方向从「悄悄放行」变成「吵闹地拦住」，这正是 §1.1 fail-closed 的原话。
 *
 * 代价是真实的、且必须说清楚：合法但没被收进白名单的写法会被降到 ST-A。
 * 因此标定集里**绿样本与红样本同等重要**，缺了绿样本，这条判据会退化成
 * 「凡数值皆降级」——那也是一种空心门，只是红的那一侧空。
 *
 * 它**不**覆盖的部分（诚实边界）：整句范围内的否定仍然靠黑名单，
 * 前置位之外的改写（后置的 `, but this was later retracted`、跨句否定）
 * 同样不在其内。R6-04 的这一半仍然开着，见 07-ATTACK-LEDGER §S4。
 */
export const PRE_WHITELIST_VERSION = 'L1c-pre-2026-08-18'
const PRE_ALLOWED = [
  // 英文：断言性动词 / 系词 / 中性介词与限定词
  'reached', 'reaches', 'reach', 'achieved', 'achieves', 'achieve', 'attained', 'attains',
  'scored', 'scores', 'obtained', 'obtains', 'yields', 'yielded', 'gives', 'gave',
  'reports', 'reported', 'shows', 'showed', 'records', 'recorded', 'hit', 'hits',
  'is', 'was', 'are', 'were', 'be', 'of', 'to', 'at', 'with', 'by', 'the', 'a', 'an',
  'and', 'or', 'about', 'report', 'show', 'record', 'observe', 'observed', 'observes',
  'we', 'they', 'it', 'that', 'this', 'these', 'those',
  // 中文：断言性动词与中性助词
  '达到', '达', '为', '是', '取得', '到', '有', '共', '计', '的', '率',
]
// 数值型载荷才走这条判据 —— 「实体名前面是什么词」不改变实体的身份。
const NUMERICISH = /[\d０-９〇一二三四五六七八九十百千万亿]/

/** 取 `at` 之前紧邻的那个词（英文按词、中文按连续 CJK 串）；句首返回 '' */
export function precedingToken(sentence, at) {
  const before = sentence.slice(0, at).replace(/[\s（(【\[「『"'']+$/u, '')
  if (!before) return ''                                  // 句首：允许
  const last = before[before.length - 1]
  if (/[，；。：,;.!?、—–-]/.test(last)) return ''          // 标点后：允许
  const cjk = before.match(/[\u4e00-\u9fff]+$/u)
  if (cjk) return cjk[0]
  const en = before.match(/[A-Za-z]+$/u)
  return en ? en[0].toLowerCase() : ''
}

/**
 * 中文串按**后缀**匹配白名单：「准确率达到」的末尾是「达到」。
 *
 * 体标记（了/过/着）先剥掉：「达到**了** 92%」与「达到 92%」是同一个断言，
 * 而白名单若按字面比对就会把前者判红。
 * 〔这一条是标定集的绿样本发现的〕NT-L-33 / NT-L-36 都是「达到了」，
 * 缺了它们，这条 fail-closed 判据会退化成「凡中文数值皆降级」。
 */
function preAllowed(tok) {
  if (!tok) return true
  const t = tok.toLowerCase().replace(/[了过着]+$/u, '')
  if (!t) return true
  if (PRE_ALLOWED.includes(t)) return true
  return PRE_ALLOWED.some(w => /[\u4e00-\u9fff]/.test(w) && t.endsWith(w))
}

// 子句边界符（受控表，版本入 params）——与分句器同一套实现的下一级切分
export const CLAUSE_BOUNDARY_VERSION = 'L1c-clause-2026-08-18'
const BOUNDARY_CHARS = '，；。：,;.!?'
const BOUNDARY_WORDS = ['而', '但', '然而', 'however', 'but', 'and', 'or']

/** 该 token 所在**子句**的结束边界（保守：算子起点到子句末） */
/**
 * 子句**起点**：从算子位置往回找最近的子句边界。
 *
 * 〔外部标定集逼出来的〕空结果表述（NEG-N）的语法位置在谓语，
 * 而它否定的主语在它**之前**：
 *   "Follow-up BCVA and ΔBCVA were comparable."
 * 只往后延的作用域够不着 BCVA，于是整句判 pass。
 *
 * 但作用域也不能扩到全句——那会打中并列的**肯定**断言：
 *   "The 30-day mortality was 16.1% and did not differ according to the delay"
 * 这里 16.1% 是肯定断言，`and` 是子句边界，否定只作用于后半句。
 * 两条真实句子把边界卡在了同一个位置：**子句**。
 */
function clauseStart(text, from) {
  let start = 0
  for (let i = from - 1; i >= 0; i--) {
    if (BOUNDARY_CHARS.includes(text[i])) { start = i + 1; break }
    let hit = false
    for (const w of BOUNDARY_WORDS) {
      if (text.startsWith(w, i)) {
        if (/^[a-z]+$/i.test(w)) {
          const before = text[i - 1], after = text[i + w.length]
          if (/[A-Za-z]/.test(before ?? '') || /[A-Za-z]/.test(after ?? '')) continue
        }
        start = i + w.length
        hit = true
        break
      }
    }
    if (hit) break
  }
  return start
}

function clauseEnd(text, from) {
  let end = text.length
  for (let i = from; i < text.length; i++) {
    if (BOUNDARY_CHARS.includes(text[i])) { end = i; break }
    for (const w of BOUNDARY_WORDS) {
      if (text.startsWith(w, i) && i > from) {
        // 英文并列连词要求词边界，避免 "band" 里的 "and"
        if (/^[a-z]+$/i.test(w)) {
          const before = text[i - 1], after = text[i + w.length]
          if (/[A-Za-z]/.test(before ?? '') || /[A-Za-z]/.test(after ?? '')) continue
        }
        end = i
        i = text.length
        break
      }
    }
  }
  return end
}

/** 命中的算子 → 作用域区间集合 */
export function scopeOf(sentence) {
  const scopes = []
  const lower = sentence.toLowerCase()
  for (const [cls, words] of TABLES) {
    for (const w of words) {
      const needle = w.toLowerCase()
      let idx = 0
      while ((idx = lower.indexOf(needle, idx)) !== -1) {
        // 英文算子要求词边界
        if (/^[a-z]/.test(needle)) {
          const before = sentence[idx - 1], after = sentence[idx + needle.length]
          if (/[A-Za-z]/.test(before ?? '') || /[A-Za-z]/.test(after ?? '')) { idx += needle.length; continue }
        }
        // 〔实现期发现的规范缺陷 · 已回改 03 §3.1.1.2〕
        // 规范原写「作用域 = 算子起点到**子句**结束边界」，四类算子统一。
        // 但条件让步 NEG-C 的语义是**限定后件**，而中文最常见的条件句形态是
        // 「如果……，主句」——从句以逗号收尾，于是被限定的主句正好落在作用域**外**，
        // NEG-C 对该形态几乎完全失效（实测：「如果使用更大的批量，该方法可达 92%。」
        // 取载荷 92% 时 L1-c 通过）。
        // 因此 NEG-C 的作用域延到**句末**：它限定的是后面整个句子。
        // NEG-C（条件让步）与 NEG-I（疑问/反问）的作用域都覆盖**整句**：
        // 前者限定后件，后者让整个命题都不是断言——
        // 「该方法真的达到了 92% 吗？」里的 92% 不是一条被断言的数值。
        const end = (cls === 'NEG-C' || cls === 'NEG-I') ? sentence.length : clauseEnd(sentence, idx)
        // NEG-N 的作用域覆盖**整个子句**（含算子之前的主语），理由见 clauseStart。
        const start = (cls === 'NEG-I') ? 0 : (cls === 'NEG-N' ? clauseStart(sentence, idx) : idx)
        scopes.push({ cls, marker: w, start, end, mStart: idx, mEnd: idx + needle.length })
        idx += needle.length
      }
    }
  }
  return scopes
}

/** 载荷各字面字段在句中的命中区间 */
export function spansOf(sentence, payloadFields) {
  const spans = []
  for (const f of payloadFields) {
    const v = String(f ?? '').trim()
    if (!v) continue
    let idx = 0
    while ((idx = sentence.indexOf(v, idx)) !== -1) {
      spans.push({ value: v, start: idx, end: idx + v.length })
      idx += v.length
    }
  }
  return spans
}

const overlaps = (a, b) => a.start < b.end && b.start < a.end

/**
 * L1-c 判定。
 *
 * @param {string} anchorSentence  anchor_span 所在的整句
 * @param {string[]} payloadFields 载荷的各字面字段
 * @param {string} [followingSentence] 紧随其后的一句，**仅用于报告已知假阴**，不参与判定
 * @returns {{pass:boolean, params:object, caveats:string[], knownLimitation:string|null}}
 */
/**
 * 转折句首标记。只认**句首**——句中的 however 不是回指上一句的。
 * 这张表和 NEG-* 各表一样是有限枚举，SA-3 认账的那条边界同样适用于它。
 */
const CONTRAST_INITIAL = /^(?:(?:however|but|yet|nevertheless|nonetheless|although|though|in contrast|by contrast|on the contrary|conversely)\b|然而|但是|但|不过|可是|相反|与此相反)/i

export function polarityScope(anchorSentence, payloadFields, followingSentence = '') {
  const scopes = scopeOf(anchorSentence)
  const spans = spansOf(anchorSentence, payloadFields)

  // 〔S3 自攻补入 · 假阳侧〕双重否定 = 肯定。
  // 「该方法**不是没有**达到 92%」语义上等于「达到了」，载荷 92% 是合法转录，
  // 而初版命中两个 NEG-S 并判 fail——R5 第 2 条预测的钳形夹的假阳侧。
  // 判据：同一子句内 NEG-S 命中数为**偶数**时相消。
  // 计数前必须**合并重叠匹配**：`falls short of` 与 `short of` 是同一个短语的
  // 两次匹配，不是两个否定。
  // 〔自我更正〕初版直接按命中数计数，于是这类短语被当成双重否定相消而放行——
  // 相消规则本身制造了一个新的假阴。
  const negSByClause = new Map()
  const bySeen = new Map()
  for (const sc of scopes) {
    if (sc.cls !== 'NEG-S') continue
    const list = bySeen.get(sc.end) ?? []
    // 比的是**算子文本本身**的位置是否重叠，不是作用域——
    // 同一子句里两个否定的作用域必然重叠（都延到子句末），
    // 按作用域去重会把真正的双重否定也并成一个。
    if (list.some(x => sc.mStart < x.mEnd && x.mStart < sc.mEnd)) continue
    list.push(sc); bySeen.set(sc.end, list)
    negSByClause.set(sc.end, (negSByClause.get(sc.end) ?? 0) + 1)
  }
  const cancelled = new Set([...negSByClause].filter(([, n]) => n % 2 === 0).map(([k]) => k))

  const hits = []
  for (const sc of scopes) {
    if (sc.cls === 'NEG-S' && cancelled.has(sc.end)) continue
    for (const sp of spans) {
      if (!overlaps(sc, sp)) continue
      // 载荷**自身已纳入该算子**时不算落在否定作用域内：
      // 判据是载荷**包含算子本身**，不是载荷覆盖整个作用域。
      // 〔自我更正〕初版写作 `sp.end >= sc.end`，于是「并未达到 92%」这个
      // 自带否定词的载荷被误判为落在否定作用域内——门在惩罚最诚实的那种载荷写法。
      if (sp.start <= sc.start && sp.end > sc.start) continue
      hits.push({ ...sc, span: sp.value })
    }
  }
  // NEG-P：数值载荷的前置词必须在白名单内。fail-closed。
  const preHits = []
  for (const sp of spans) {
    if (!NUMERICISH.test(sp.value)) continue
    // 载荷已经被某个算子命中时不必重复报——同一件事报两次会让 params 失真。
    if (hits.some(h => overlaps(h, sp))) continue
    // 载荷**自身含否定算子**时跳过：这时 producer 断言的就是那个否定命题
    // （「该方法并未达到 92%」取载荷「并未达到 92%」）。前置位判据打不到它，
    // 打到的只会是它前面那个无关的主语。——NT-L-35 的形态。
    if (scopes.some(sc => sc.mStart >= sp.start && sc.mEnd <= sp.end)) continue
    const tok = precedingToken(anchorSentence, sp.start)
    if (!preAllowed(tok)) preHits.push({ cls: 'NEG-P', marker: tok, span: sp.value })
  }

  let pass = hits.length === 0 && preHits.length === 0

  // ── 跨句极性 ────────────────────────────────────────────────────────
  // 原先这里只**报告**，不参与判定（03 §11.15 认领为未修）。
  // 外部标定测试 T3-4 让它在真实数据上兑现了：Prasad & Mailankody 摘要写
  //   “A recent estimate of R&D spending is $2.7 billion (2017 US dollars).”
  //   “However, this analysis lacks transparency and independent replication.”
  // 单独取上句，L1-c 判 pass，成稿印「已归因」——而那篇论文正是在反驳这个数。
  //
  // 现在分成两档，判据是**下一句是否以转折词开头**：
  //   转折词开头 + 含否定 → 参与判定（判 fail）。
  //       “However/But/Yet/然而/但是…” 在语法上就是回指上一句的，
  //       它后面的否定作用于上句的断言，不是一条无关的新陈述。
  //   非转折词开头 + 含否定 → 仍然只报告。
  //       “…is $2.7 billion. No funding was received.” 的 No 与那个数无关，
  //       把它算进来是假阳。
  //
  // 〔为什么这样切而不是全都算〕这条规则的两侧都有代价，而且方向相反：
  // 收得太紧漏掉真反驳，放得太松把无关否定算成反驳。转折词是句法上的
  // 回指标记，是这两者之间唯一一条**不靠语义理解**就能划的线。
  let knownLimitation = null
  let crossFail = null
  if (pass && followingSentence) {
    const nextScopes = scopeOf(followingSentence)
    const neg = nextScopes.find(s => s.cls === 'NEG-S' || s.cls === 'NEG-C' || s.cls === 'NEG-N')
    if (neg) {
      if (CONTRAST_INITIAL.test(followingSentence.trimStart())) {
        crossFail = `NEG-X:${neg.marker}`
      } else {
        knownLimitation = '跨句极性：下一句含否定算子但非转折句首，只报告不判定（无关否定的假阳风险）'
      }
    }
  }

  if (crossFail) pass = false

  return {
    pass,
    params: {
      operator_table_version: OPERATOR_TABLE_VERSION,
      clause_boundary_version: CLAUSE_BOUNDARY_VERSION,
      pre_whitelist_version: PRE_WHITELIST_VERSION,
      polarity_marker: [...[...hits, ...preHits].map(h => `${h.cls}:${h.marker}`),
                        ...(crossFail ? [crossFail] : [])],
      scopes_found: scopes.length,
      spans_found: spans.length,
    },
    // NEG-C（条件让步）刻意**不**进 counter 池，避免制造假 ST-C
    caveats: pass ? [] : (hits.length ? ['payload_in_negated_scope'] : ['payload_pre_token_not_whitelisted']),
    counterCandidate: hits.some(h => ['NEG-S', 'NEG-Q', 'NEG-R'].includes(h.cls)),
    knownLimitation,
  }
}
