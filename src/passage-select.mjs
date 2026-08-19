/**
 * 段落选择 —— 成本优化的主要落点，且它是 **GC-0：零模型调用**。
 *
 * 〔为什么这是对的落点〕成本核算（§S18）显示「读全文提 claim」占 45%，
 * 根因是每读一篇吃 22K 输入。而 §S17 已经证明 **G5 本来就是逐段的**：
 * 一条 claim 的证据是**一个段落**，不是一整篇论文。
 * 把整篇送进模型是习惯，不是需求。
 *
 * 实测（AlphaFold 那篇 Nature 的完整 JATS，50 个可寻址段）：
 *   整篇          42,474 字符 ≈ 10.6K token
 *   一个具体问题   命中 1–14 段 ≈ 0.6K–4.3K token
 * 也就是说这一步能砍掉 **60%–94%** 的输入。
 *
 * ── 但省下来的代价是召回，必须一起量 ────────────────────────────────
 *
 * 选窄了会漏掉证据 —— 那不是「判错」，是**根本没看见**，
 * 而没看见在本系统里表现为 `not_covered`，看起来像「诚实地说不知道」。
 * **一个因为省钱而说不知道的系统，比一个贵的系统坏得多**：
 * 它的失效是隐形的。
 *
 * 因此本模块的每次选择都返回 `dropped`，而 gates/check_passage_select.mjs
 * 在真实文献上量**召回率**：已知落在某段里的目标引语，选完之后还在不在。
 *
 * ── 判据：确定性、可解释、宁宽勿窄 ──────────────────────────────────
 *
 * 打分只用三样东西，全部离线可算：
 *   ① 与问题/槽值的词项重合（归一化到段落长度，避免长段落靠体量取胜）
 *   ② 段落里有没有**数字**（本系统的产品是数字的状态，无数字段落的价值低得多）
 *   ③ 节标题的重合（结果节通常比方法节更可能承载数值结论）
 * 不做向量检索、不做模型打分 —— 那两样都会把「零模型调用」这个前提毁掉。
 */
import { stem } from './gates/g-containment.mjs'

export const SELECT_VERSION = 'passage-select-2026-08-19'

const STOP = new Set(['the', 'a', 'an', 'of', 'in', 'on', 'for', 'to', 'and', 'or', 'is', 'was',
  'were', 'are', 'be', 'with', 'by', 'at', 'as', 'that', 'this', 'it', 'we', 'our',
  '的', '了', '是', '在', '和', '与', '对', '有', '这', '那', '被', '为'])

const toks = t => String(t ?? '').normalize('NFKC').toLowerCase()
  .split(/[^\p{L}\p{N}%.$]+/u).filter(x => x && !STOP.has(x) && x.length > 1)

/**
 * @param {{locator:string,text:string,secTitle:string}[]} passages
 * @param {object} q  {question, slots:string[], wantNumber:boolean}
 * @param {object} opts {maxPassages, minScore, alwaysKeepNumeric}
 */
export function selectPassages(passages, q = {}, opts = {}) {
  const maxP = opts.maxPassages ?? 12
  const queryTerms = new Set([...toks(q.question), ...(q.slots ?? []).flatMap(toks)].map(stem))
  if (!queryTerms.size) {
    // 没有查询词就没有选择依据 —— **返回全部**，不假装选过。
    // 悄悄选一个子集比不选更坏：调用方会以为它拿到的是筛过的。
    return { kept: passages, dropped: [], why: '无查询词，未做筛选', version: SELECT_VERSION,
             stats: { total: passages.length, kept: passages.length, dropped: 0 } }
  }

  const scored = passages.map(p => {
    const pt = toks(p.text).map(stem)
    const uniq = new Set(pt)
    let overlap = 0
    for (const t of queryTerms) if (uniq.has(t)) overlap++
    // 归一化：命中词数 / 查询词数。不除以段落长度——长段落承载更多信息是事实，
    // 除以长度会系统性偏向短段落（实测：偏向图注与致谢）。
    const termScore = overlap / queryTerms.size
    const hasNum = /\d/.test(p.text)
    const titleHit = [...queryTerms].some(t => toks(p.secTitle ?? '').map(stem).includes(t))
    return {
      p, overlap,
      score: termScore + (hasNum ? 0.15 : 0) + (titleHit ? 0.25 : 0),
      hasNum, titleHit,
    }
  })

  const minScore = opts.minScore ?? 0.15
  let keep = scored.filter(s => s.score >= minScore)

  // 宁宽勿窄：命中太少时放宽到「有任一查询词 + 有数字」。
  // 〔为什么要这一条〕实测「AlphaFold 在 CASP14 的表现」只命中 1 段——
  // 一个问题的措辞与论文的措辞不重合是常态，而漏掉证据的代价远大于多读几段。
  if (keep.length < (opts.minPassages ?? 3)) {
    keep = scored.filter(s => s.overlap > 0 || (opts.alwaysKeepNumeric !== false && s.hasNum))
  }

  keep.sort((a, b) => b.score - a.score)
  let kept = keep.slice(0, maxP)

  // ── 节级补齐：命中的节，其**数值段**一并保留 ──────────────────────────
  //
  // 〔实测逼出来的〕只按分数取前 K 时，召回是 84%——一节里有多个数值段时
  // 后几个被 maxPassages 截掉了（「Inputs and data sources」4 段只留 1）。
  //
  // 而丢掉一个数值段不是「判错」，是**根本没看见**：
  // 它在本系统里表现为 not_covered，看起来像诚实地说不知道。
  // **一个因为省钱而说不知道的系统，比一个贵的系统坏得多——它的失效是隐形的。**
  //
  // 判据是节级的：一个节既然被判为相关，它的数值段就是这个节的结论所在，
  // 不该因为排在第 13 位而消失。非数值段不补——它们是论述，不是证据。
  const keptSecs = new Set(kept.map(k => k.p.sec).filter(Boolean))
  const seen = new Set(kept.map(k => k.p.locator))
  for (const s2 of scored) {
    if (seen.has(s2.p.locator)) continue
    if (s2.hasNum && keptSecs.has(s2.p.sec)) { kept.push(s2); seen.add(s2.p.locator) }
  }
  const keptSet = new Set(kept.map(k => k.p.locator))
  return {
    kept: kept.map(k => k.p),
    dropped: passages.filter(p => !keptSet.has(p.locator)),
    version: SELECT_VERSION,
    stats: {
      total: passages.length, kept: kept.length, dropped: passages.length - kept.length,
      charsTotal: passages.reduce((s, p) => s + p.text.length, 0),
      charsKept: kept.reduce((s, k) => s + k.p.text.length, 0),
    },
  }
}

/** 省了多少（字符比，token 与字符近似成正比） */
export function savingOf(sel) {
  const { charsTotal, charsKept } = sel.stats
  return charsTotal ? 1 - charsKept / charsTotal : 0
}
