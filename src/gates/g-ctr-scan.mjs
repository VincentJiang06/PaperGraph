/**
 * G-CTR-SCAN 的 X-2 —— 反证检索 query 的结构判据（GC-0）。
 *
 * 规范：03-EVIDENCE-ENGINE §5A.1 EE-X-3。
 *
 * 〔它守什么〕`counter_evidence_searched` 是 S 的 0e 前置否决项，
 * §7.2.3 称它是「逃不过的只有这一条」——抵御选择性引用的唯一防线。
 * 若「发一条 query」就算搜过，这条防线等于没有。
 *
 * 〔为什么判据是双侧的〕旧判据用 Jaccard **上界**把 query 推离 claim 原文，
 * 而填充是免费且无界的：追加一段常量样板即可把 J 压到任意小。
 * 新判据 (a′) 是**下界**（锚槽必须出现）、(b′) 是**上界**（载荷外 token 有预算），
 * **方向相反，不存在单调安全方向**——这是它挡住模板攻击的全部原因。
 */
import { normalizeQuote, baseNormalize } from '../normalize.mjs'
import { stem } from './g-containment.mjs'

export const TABLE_VERSIONS = Object.freeze({
  NEG: 'neg-2026-08-18', NEG_LIT: 'neglit-2026-08-18',
  COMP: 'comp-2026-08-18', NUM_UNIT: 'numunit-2026-08-18',
  STOP: 'stop-2026-08-18', CLAUSE: 'L1c-clause-2026-08-18',
})
export const K_OP = 8   // 〔裁定，工程常数〕载荷外 token 预算

const NEG = new Set(['不', '未', '没有', '并非', '无', '并不', '否', 'not', 'no', 'never', 'without', 'fails', 'fail'])
// NEG-LIT：反向文献算子词表。
// 〔标定期扩充〕初版只有 15 词，实测把 `AlphaFold accuracy CASP14 not reproduced`
// 这条**人写的真反证 query** 判红（`reproduced` 不在任何受控表里 ⇒ 违反 (b′) 的 E ⊆ OPS）。
// 那正是 R5 警告的钳形夹的假阳侧：词表太窄 ⇒ 真反证被判成伪装 ⇒ 0e 恒不通过 ⇒ 全 ST-N。
// 扩表不削弱 (b′)——k_op = 8 的预算仍然卡着无界填充。
// **本表的假阳率未测**（03 §5A.0 已把 power_basis 诚实降为 unmeasured）。
const NEG_LIT = new Set([
  '反驳', '质疑', '未能复现', '无法复现', '复现失败', '失败', '争议', '撤稿', '更正', '存疑',
  'refute', 'refutes', 'refuted', 'contradict', 'contradicts', 'contradicted',
  'fails', 'failed', 'failure', 'irreproducible', 'unreproducible',
  'retraction', 'retracted', 'dispute', 'disputed', 'criticism', 'critique',
  'rebuttal', 'erratum', 'corrigendum', 'overestimate', 'overstated', 'limitation', 'limitations',
])
/**
 * 中性词表 —— **可以出现，但不算反向算子**。
 *
 * 〔R6-06〕`reproduce / reproduced / reproduction / replicate / replicated / replication`
 * 原本收在 NEG_LIT 里，于是 `AlphaFold 92% accuracy CASP14 replicated` 四条判据全过，
 * 一次**求确证**的检索被记作已做反证检索——而 §7.2.3 称 counter_evidence_searched
 * 是「逃不过的只有这一条」。攻击者的原话：
 *
 *   > 这是钳形夹的实证：为压假阳而扩的表，直接打开了假阴。
 *
 * 修法不是简单删掉：删掉之后 (b′) 会把 `not reproduced` 里的 `reproduced`
 * 判成「越界 token」，一条合法的反证 query 反而判红——钳形夹的另一侧。
 * 两条判据问的本来就是两件事：
 *   (b′) 这个词**允许出现**吗？          → 中性词：允许
 *   (c′) 这个词**构成一次反证**吗？      → 中性词：不构成
 * 分成两张表之后，`replicated` 单独出现零算子判红，`not reproduced` 靠 NEG-1 通过。
 */
const NEUTRAL_LIT = new Set([
  'reproduce', 'reproduced', 'reproduces', 'reproduction', 'reproducibility',
  'replicate', 'replicated', 'replicates', 'replication', 'independent', 'verify', 'verified',
  '复现', '重复实验', '独立验证',
])
const COMP = new Set(['高于', '低于', '优于', '劣于', '大于', '小于', '超过', '不足',
  'higher', 'lower', 'better', 'worse', 'above', 'below', 'exceeds', 'under'])
const NUM_UNIT = t => /^[\d.]+%?$/.test(t) || /^\d+(\.\d+)?(x|倍|ms|s|gb|mb|k|m|b)$/i.test(t)
// STOP：检索语法 + 停用词。
// 〔标定期扩充〕初版中文侧只有 6 个字，于是 `该方法` 这种最常见的中文功能短语
// 被判成「载荷外的越界 token」，一条正常的中文反证 query 就此判红——
// 又一次假阳侧漂移。中文没有空格分词，功能短语会整块出现，表必须按**短语**收。
const STOP = new Set([
  'and', 'or', 'not', 'the', 'of', 'in', 'a', 'an', 'to', 'for', 'on', 'is', 'are', 'was', 'were',
  'site:', 'filetype:', 'intitle:', '"', 'AND', 'OR', 'NOT',
  '的', '了', '与', '和', '在', '是', '被', '对', '从', '及', '等', '中',
  '该方法', '该模型', '该研究', '本文', '论文', '研究', '方法', '模型', '结果', '实验',
])

// 〔实现期发现〕分词**不能**用 normalizeQuote：它会删掉 CJK 相邻空白，
// 于是中文 query 归一化后变成一个 token，(a′)/(b′) 全废。
// 中文的词边界不是空格——所以：
//   · token 预算 (b′) 用**保留空格**的 baseNormalize 分词（对拉丁语正确，
//     对中文是「按空格切出来的片段」，仍能约束无界填充）；
//   · 锚槽覆盖 (a′) 改用**子串包含**（中英通用，不依赖分词）。
const tok = s => baseNormalize(String(s ?? ''))
  .split(/[\s,，、;；:：()（）"'"']+/).map(x => x.trim().toLowerCase()).filter(Boolean)

const CLAUSE_SPLIT = /[，；。：,;.!?]/

/**
 * @param {object} claim  { payload, metric_frame, evidence_refs }
 * @param {string} query  producer 发出的反证检索 query
 * @param {object} [opts] { resultKeys:[], supportKeys:[] }
 */
/**
 * @param {object} opts.snapshotText    证据快照全文。只进 (b′) 的词汇基底，不进 (a′)。
 * @param {object} opts.anchorSentence  claim 所引的那句原文。**由门递入，不由 producer 递**——
 *   它现在参与 (a′)/(b′) 的判定，若可由被判定方指定，就等于允许它自带一份词汇表。
 *   调用点在 pipeline，取自 ctx（gate-ctx 从快照算出来的那一份）。
 */
export function counterQueryOk(claim, query, opts = {}) {
  const reasons = []
  const params = { table_versions: TABLE_VERSIONS, k_op: K_OP }

  // ── 记号 ──────────────────────────────────────────────────────────────
  const payloadStr = Object.values(claim.payload ?? {}).map(String).join(' ')
  const TP = new Set(tok(payloadStr))
  const TQ = new Set(tok(query))

  // Slot(P)：实体槽 ∪ {metric, sample_or_tier}。由 schema 枚举，不由散文判断。
  const slots = []
  for (const [k, v] of Object.entries(claim.payload ?? {})) {
    if ((claim.slot_types ?? {})[k] === 'entity') slots.push(String(v))
  }
  const mf = claim.metric_frame ?? {}
  if (mf.metric) slots.push(String(mf.metric))
  if (mf.sample_or_tier) slots.push(String(mf.sample_or_tier))

  // NEG-2 会替换掉数值槽/comparator 槽，那个槽不计入 Slot(P)
  const slotTokens = new Set(slots.flatMap(tok))

  // ── (a′) 锚槽覆盖**下界** ─────────────────────────────────────────────
  //
  // 〔外部标定测试 E1 修复〕原判据要求**每一个**锚槽都字面出现在 query 里。
  // 在真实数据上这条几乎不可能满足：metric_frame 常写中文（「研发成本」），
  // 而 query 是英文；同一个东西在两侧的措辞永远对不上。
  // 实测：三条人会写的自然语言 query，判红 2/3，整批 claim 落 not_covered。
  // 那是 R5 第 2 条预测的钳形夹的**假阳侧**——真反证被判成假。
  //
  // 下界要挡的东西没变：**一句泛泛的「refute」不能算做过反证检索**。
  // 但「是否关于这条 claim」不必靠逐槽字面匹配来证明，
  // 只需要 query 里有**足够多的锚**落在这条 claim 自己的材料上。
  // 材料 = 载荷 ∪ 槽值 ∪ metric_frame ∪ **锚句**（claim 自己引的那句原文）。
  // 锚句进来是关键：真实研究者写 query 时用的正是原文里的词。
  const nq = normalizeQuote(query)
  //
  // 两条边界**取材不同**，这一点要写清楚：
  //   下界 (a′) 只看 载荷 ∪ 槽值 ∪ **锚句** —— 它要证明的是
  //     「这条 query 是关于**这条 claim** 的」。若把整篇快照算进来，
  //     一条关于同一篇论文里**另一个数**的 query 也会通过，下界就废了。
  //   上界 (b′) 额外把**整篇快照**算进来 —— 它要挡的是**无中生有的填充**
  //     （堆词保证零命中），而写在原文里的词不是无中生有。
  const material = [...slots, ...Object.values(claim.payload ?? {}).map(String),
                    String(opts.anchorSentence ?? '')]
  // 按**词干**比，不按字面。原文写 `drugs` 而 query 写 `drug` 是同一个词——
  // 这条在锚点包含门那边已经立过一次（`replication` vs `replicated`），
  // 这里是同一个理由：真实文本总有词形变化，逐字比对会把合法的判成越界。
  const stems = xs => new Set(xs.filter(t => t && !STOP.has(t)).map(stem))
  const materialTokens = stems(material.flatMap(tok))
  const vocabTokens = new Set([...materialTokens, ...stems(tok(String(opts.snapshotText ?? '')))])
  const anchoredTokens = [...TQ].filter(t => materialTokens.has(stem(t)))
  const MIN_ANCHORS = 2

  // 松只给 metric_frame，**不给实体槽**。
  // 〔标定用例 X-8 抓到的〕初版写成「任意 ≥2 个锚 token 即可」，
  // 于是 `accuracy CASP14 refute`（删掉了「AlphaFold」）通过——
  // 一条不点名系统的反证检索会捞回**别的系统**的结果，那不是这条 claim 的反证。
  // 实体槽是这个东西的身份，删掉它 query 就换了对象；
  // 而 metric_frame 是我们自己写的判据名（常是中文），它跟原文措辞对不上
  // 才是那条真问题。两者不该共用一条判据。
  const entitySlots = Object.entries(claim.payload ?? {})
    .filter(([k]) => (claim.slot_types ?? {})[k] === 'entity')
    .map(([, v]) => String(v))
  const missingEntity = entitySlots.filter(e => {
    const n = normalizeQuote(e)
    return n && !nq.includes(n)
  })
  const frameSlots = [mf.metric, mf.sample_or_tier].filter(Boolean).map(String)
  const missingFrame = frameSlots.filter(f => {
    const n = normalizeQuote(f)
    return n && !nq.includes(n)
  })
  params.slot_coverage = { entity_required: entitySlots.length, entity_missing: missingEntity.length,
                           frame_required: frameSlots.length, frame_missing: missingFrame.length,
                           anchored_tokens: anchoredTokens.length, min_anchors: MIN_ANCHORS }
  if (missingEntity.length) {
    reasons.push(`(a′) 实体槽缺失：query 缺少 ${missingEntity.join('、')} —— 换了对象的检索不是这条 claim 的反证`)
  }
  if (missingFrame.length && anchoredTokens.length < MIN_ANCHORS) {
    reasons.push(`(a′) 锚不足：query 缺判据 ${missingFrame.join('、')}，` +
                 `且落在本 claim 材料（载荷/槽值/锚句）上的 token 只有 ${anchoredTokens.length} 个（需 ≥${MIN_ANCHORS}）`)
  }

  // ── (b′) 载荷外 token **预算** ────────────────────────────────────────
  // 〔同一次修复〕「载荷外」的口径从「不在载荷/锚槽里」放宽到
  // 「不在这条 claim 的**材料**里」。原口径把 `drug` `development` `cost`
  // 判成越界 token —— 而这三个词就写在被引的那句原文里。
  // 上界要挡的是**无中生有的填充**（堆词保证零命中），不是原文里的词。
  const E = [...TQ].filter(t => !TP.has(t) && !STOP.has(t) && !slotTokens.has(t) && !vocabTokens.has(stem(t)))
  // NEUTRAL_LIT 进 (b′) 但**不**进 (c′)：允许出现 ≠ 构成反证（R6-06）。
  const inOps = t => NEG.has(t) || NEG_LIT.has(t) || NEUTRAL_LIT.has(t) || COMP.has(t) || NUM_UNIT(t) ||
    // 中文片段：只要它整体由受控词 + 载荷/锚槽内容拼成，就不算越界 token
    (/[\u4e00-\u9fff]/.test(t) &&
     [...NEG, ...NEG_LIT, ...NEUTRAL_LIT, ...COMP].some(w => /[\u4e00-\u9fff]/.test(w) && t.includes(w)))
  const outOfOps = E.filter(t => !inOps(t))
  params.extra_tokens = { count: E.length, budget: K_OP, out_of_ops: outOfOps }
  if (E.length > K_OP) reasons.push(`(b′) 载荷外 token ${E.length} 个，超预算 ${K_OP}`)
  if (outOfOps.length) reasons.push(`(b′) 载荷外 token 有 ${outOfOps.length} 个不在受控词表内：${outOfOps.slice(0, 5).join('、')}`)

  // ── (c′) **恰好一个**受控反向算子 ─────────────────────────────────────
  const hits = []
  // NEG-1 极性取反：否定词与某个锚槽落在**同一归一化子句**内
  const clauses = normalizeQuote(query).split(CLAUSE_SPLIT)
  const neg1 = clauses.some(cl => {
    const ct = new Set(tok(cl))
    const hasNeg = [...ct].some(t => NEG.has(t)) || [...NEG].some(n => /[\u4e00-\u9fff]/.test(n) && cl.includes(n))
    const hasSlot = slots.some(sl => { const n = normalizeQuote(sl); return n && cl.includes(n) })
    return hasNeg && hasSlot
  })
  if (neg1) hits.push('NEG-1')
  // NEG-2 对立值替换：数值槽取值与载荷区间不相交 / 方向相反
  const numsP = [...TP].filter(NUM_UNIT), numsQ = [...TQ].filter(NUM_UNIT)
  const neg2 = numsQ.length > 0 && numsP.length > 0 && numsQ.every(n => !numsP.includes(n)) &&
               [...TQ].some(t => COMP.has(t))
  if (neg2) hits.push('NEG-2')
  // NEG-3 反向文献算子：|NEG-LIT ∩ T(Q)| ≤ 2 且 ≥ 1
  const litHits = [...new Set([
    ...[...TQ].filter(t => NEG_LIT.has(t)),
    ...[...NEG_LIT].filter(w => /[\u4e00-\u9fff]/.test(w) && nq.includes(w)),
  ])]
  if (litHits.length >= 1 && litHits.length <= 2) hits.push('NEG-3')
  if (litHits.length > 2) reasons.push(`(c′) NEG-LIT 命中 ${litHits.length} 个，超过 2 —— 堆反向词是模板攻击的指纹`)

  // 〔标定期修正〕`not reproduced` 这类**同一个否定的两词表达**会同时命中
  // NEG-1（否定词与锚槽同子句）与 NEG-3（reproduced ∈ NEG-LIT），
  // 于是被 (c′) 的「恰好一个」判红。但那不是叠算子——它是一个否定。
  // (c′) 的「≥2 判红」本意是抓**过约束合取**（堆算子保证零命中），不是抓这个。
  // 判据：否定词与反向文献词**相邻**（中间无其它内容 token）时，两者算一个算子。
  const qt = tok(query)
  const adjacent = qt.some((t, i) =>
    NEG.has(t) && qt[i + 1] && (NEG_LIT.has(qt[i + 1]) || NEUTRAL_LIT.has(qt[i + 1])))
  if (adjacent && hits.includes('NEG-1') && hits.includes('NEG-3')) {
    hits.splice(hits.indexOf('NEG-1'), 1)
    params.merged_adjacent_negation = true
  }

  params.counter_operator = hits
  if (hits.length !== 1) {
    reasons.push(`(c′) 受控反向算子命中 ${hits.length} 个，必须恰好 1 个` +
      (hits.length >= 2 ? '（≥2 是过约束合取的指纹）' : '（0 个 = 这不是一条反证 query）'))
  }

  // ── (d′) 结果集**非重复性** ───────────────────────────────────────────
  const key = s => normalizeQuote(String(s ?? '')).toLowerCase()
  const R_counter = new Set((opts.resultKeys ?? []).map(key))
  const R_support = new Set((opts.supportKeys ??
    (claim.evidence_refs ?? []).map(e => e.work_id ?? e.url ?? e.evidence_id)).map(key))
  const subsetOfSupport = R_counter.size > 0 && [...R_counter].every(k => R_support.has(k))
  params.result_sets = { counter: R_counter.size, support: R_support.size }
  if (subsetOfSupport) {
    reasons.push('(d′) 反证检索原样捞回了本 claim 自己的支持证据（允许零命中，不允许自捞）')
  }

  // ── (e′) 结果键必须**可复核** ─────────────────────────────────────────
  // 〔R6-06 的另一半〕攻击者实测：`resultKeys=['我编的']` 过，`resultKeys=[]` 也过。
  // 也就是说 X-2 此前只在检查**一个字符串的形状**——一次从未发生的检索，
  // 只要 query 写得像反证，就被记作已做反证检索。
  //
  // 可机器判定的收紧：**声称找到了什么，就必须抓过它**。
  // 零命中仍然合法（真反证检索确实常常零命中），但零命中 ⇒ counter_evidence_found = false，
  // 二者不能兼得。捏造的键从此当场判红。
  //
  // 这**不**等于「检索真的发生过」——链路里没有真实检索器，那是架构层的空缺，
  // 不是本门能补的。所以下面把 provenance 明写成 self-reported-query 并每次报出来。
  // 两侧都要过同一个 key()：结果键与 work_id 的归一化口径必须一致，
  // 否则 (e′) 会把每一个合法结果键都判成「查无此作品」——一条恒判红的检查
  // 与一条恒放行的检查同样是空心的，只是空在另一侧。
  const known = opts.knownWorkIds instanceof Set ? new Set([...opts.knownWorkIds].map(key)) : null
  const unresolved = known ? [...R_counter].filter(k => !known.has(k)) : []
  if (unresolved.length) {
    reasons.push(`(e′) ${unresolved.length} 个结果键在本 run 里没有对应的证据卡：` +
      `${unresolved.slice(0, 3).join('、')} —— 声称找到了，就必须抓过它`)
  }
  params.counter_search_provenance = 'self-reported-query'
  params.zero_hit = R_counter.size === 0

  return {
    pass: reasons.length === 0, reasons, params,
    found: reasons.length === 0 && R_counter.size > 0,
    knownLimitation: '反证检索的 query 与结果均由上游自报，链路内没有真实检索器；' +
      '本门只能判定 query 的结构与结果键的可复核性（R6-06 架构层未闭合）',
  }
}
