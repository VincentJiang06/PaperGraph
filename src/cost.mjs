/**
 * Token 计量与成本核算（W-16）。
 *
 * 〔为什么要有〕本项目的编排是**超并行多 loop** —— 探索型 agent 的成本
 * 不是「一次调用」而是「一棵调用树」，而树的形状由数据决定，事前估不准。
 * 不计量就只能事后看账单，那时已经花完了。
 *
 * 〔口径 · 来源与日期〕DeepSeek 官方 pricing 页，2026-08-19 复核。
 * 单位 **USD / 1M tokens**。峰时 = UTC 01:00–04:00 与 06:00–10:00
 * （北京时间 09–12 与 14–18），其余时段离峰价 = 峰时价的一半。
 *
 *                       flash 离峰 / 峰时      pro 离峰 / 峰时
 *   input  (cache hit)   0.007 / 0.014         0.022 / 0.044
 *   input  (cache miss)  0.22  / 0.44          0.66  / 1.32
 *   output               0.66  / 1.32          1.98  / 3.96
 *
 * 这张表是**自述数字**，因此：① 带核对日期；② 由 gates/check_cost.mjs
 * 在每次运行时重算三条已知算例，任何一格被改动都会红。
 * 它守不住的是「官方改了价而我们没改表」——那需要人去看官网，
 * 与本项目其余所有「外部真值」同一性质。
 */

export const PRICING_VERIFIED_AT = '2026-08-19'
export const PRICING_SOURCE = 'https://api-docs.deepseek.com/quick_start/pricing'

/** USD per 1M tokens，离峰价。峰时 = 离峰 × 2。 */
export const PRICING = Object.freeze({
  'deepseek-v4-flash': { cacheHit: 0.007, cacheMiss: 0.22, output: 0.66 },
  'deepseek-v4-pro':   { cacheHit: 0.022, cacheMiss: 0.66, output: 1.98 },
})

/** 峰时判定：UTC 01–04 与 06–10。传入 Date 或 ISO 串。 */
export function isPeak(when) {
  const d = when instanceof Date ? when : new Date(when)
  const h = d.getUTCHours()
  return (h >= 1 && h < 4) || (h >= 6 && h < 10)
}

/**
 * 一次调用的成本。
 * @param {object} u  {model, inputCacheHit, inputCacheMiss, output, at}
 * @returns {{usd:number, peak:boolean, breakdown:object}}
 */
export function costOf({ model, inputCacheHit = 0, inputCacheMiss = 0, output = 0, at }) {
  const p = PRICING[model]
  if (!p) throw new Error(`未知模型 ${model}；定价表只覆盖 ${Object.keys(PRICING).join(' / ')}`)
  const mult = at != null && isPeak(at) ? 2 : 1
  const M = 1e6
  const hit = inputCacheHit / M * p.cacheHit * mult
  const miss = inputCacheMiss / M * p.cacheMiss * mult
  const out = output / M * p.output * mult
  return {
    usd: hit + miss + out,
    peak: mult === 2,
    breakdown: { cacheHit: hit, cacheMiss: miss, output: out },
  }
}

/**
 * 一次研究运行的计量账本。
 *
 * 〔为什么记「每条 claim 分摊到多少」而不只记总量〕
 * 本项目的产品是**逐条 claim 的状态**，那么成本也应当按 claim 归集——
 * 否则「这次研究花了多少」是个孤立的数，回答不了
 * 「拿到一条 verified 值多少钱」这个真正要优化的问题。
 */
export class CostLedger {
  constructor({ at } = {}) { this.calls = []; this.at = at }
  /** @param {object} c {model, inputCacheHit, inputCacheMiss, output, claimId, stage} */
  record(c) {
    const r = costOf({ ...c, at: c.at ?? this.at })
    this.calls.push({ ...c, usd: r.usd, peak: r.peak })
    return r
  }
  get totalUsd() { return this.calls.reduce((s, c) => s + c.usd, 0) }
  get totalTokens() {
    return this.calls.reduce((s, c) => s + (c.inputCacheHit ?? 0) + (c.inputCacheMiss ?? 0) + (c.output ?? 0), 0)
  }
  /** 按阶段归集 */
  byStage() {
    const m = {}
    for (const c of this.calls) {
      const k = c.stage ?? '(未标阶段)'
      m[k] ??= { calls: 0, usd: 0, tokens: 0 }
      m[k].calls++; m[k].usd += c.usd
      m[k].tokens += (c.inputCacheHit ?? 0) + (c.inputCacheMiss ?? 0) + (c.output ?? 0)
    }
    return m
  }
  /** 按 claim 归集；`statuses` 是 claimId → status，用来算「每条 verified 的单价」 */
  byOutcome(statuses = {}) {
    const m = {}
    for (const c of this.calls) {
      const st = c.claimId ? (statuses[c.claimId] ?? '(未判定)') : '(无 claim)'
      m[st] ??= { calls: 0, usd: 0, claims: new Set() }
      m[st].calls++; m[st].usd += c.usd
      if (c.claimId) m[st].claims.add(c.claimId)
    }
    return Object.fromEntries(Object.entries(m).map(([k, v]) =>
      [k, { calls: v.calls, usd: v.usd, claims: v.claims.size,
            usdPerClaim: v.claims.size ? v.usd / v.claims.size : null }]))
  }
}

/** 粗略 token 估算。**只用于事前预算，不得用于记账**——记账必须用 API 返回的真实用量。 */
export function estimateTokens(text) {
  const s = String(text ?? '')
  const cjk = (s.match(/[　-鿿＀-￯]/g) ?? []).length
  const rest = s.length - cjk
  // CJK 约 1 token/字；拉丁约 1 token/4 字符。两者都是粗估，误差 ±20% 量级。
  return Math.ceil(cjk + rest / 4)
}
