/**
 * §1.2.2 归一化算法 —— `quote_faithful` 的唯一实现。
 *
 * 规范原文（01-CONTRACTS §1.2.2）：
 *   NFKC → 统一引号/破折号/省略号 → 折叠空白；
 *   PDF 专项做跨行连字符还原与页眉页脚去重；
 *   中文专项做全角/半角统一，并**删除一切与 CJK 字符相邻的空白——不按语言分支**。
 *
 * 「不按语言分支」这句是 S0 实测（M0-2）换来的：原写法「按整串是否含 CJK 决定
 * 要不要整串去空白」是**非对称的**，含 CJK 的快照 + 纯英文引语必然失配，
 * 实测把中文网页命中率打到 5.0%。
 *
 * 〔交叉验证〕`gates/repro/m0_2_normalization.py` 是同一算法的独立 Python 实现，
 * 且它把 S0 记录的 18 格结论钉成了声明式期望。`gates/check_normalize_parity.mjs`
 * 断言两个实现在同一组用例上逐格一致——**两个独立实现吻合本身就是一条证据**，
 * 而单一实现的自洽不是。
 */

// CJK 统一表意文字 + 扩展 A + 兼容 + 全角/标点区
const CJK = '㐀-䶿一-鿿豈-﫿　-〿＀-￯'
const CJK_RE = new RegExp(`[${CJK}]`)

/** 公共前段：NFKC → 统一引号/破折号/省略号 → 折叠空白 */
export function baseNormalize(s) {
  let t = String(s).normalize('NFKC')
  const MAP = [['“', '"'], ['”', '"'], ['‘', "'"], ['’', "'"],
               ['—', '-'], ['–', '-'], ['…', '...']]
  for (const [a, b] of MAP) t = t.split(a).join(b)
  return t.replace(/\s+/g, ' ').trim()
}

/** 现规范：凡与 CJK 相邻的空白一律删除，**不按语言分支** */
export function normalizeQuote(s) {
  let t = baseNormalize(s)
  t = t.replace(new RegExp(`(?<=[${CJK}])\\s+`, 'g'), '')
  t = t.replace(new RegExp(`\\s+(?=[${CJK}])`, 'g'), '')
  return t
}

/**
 * 〔已被证伪，仅供回归对照〕原中文专项规则：按整串是否含 CJK 决定要不要整串去空白。
 * 保留它是为了让「新规则确实修好了旧缺陷」这件事在每次运行里可被重新验证，
 * 而不是一句「已修复」。
 */
export function normalizeQuoteLegacy(s) {
  let t = baseNormalize(s)
  if (CJK_RE.test(t)) t = t.replace(/\s+/g, '')
  return t
}

/** PDF 专项：跨行连字符还原。**上下文相关重写**——引语若在还原窗口内被截断必然失配 */
export function dehyphenate(s) {
  return String(s).replace(/(\w)-\s*\n\s*(\w)/g, '$1$2')
}

/**
 * `quote_faithful` 的判定：归一化后的引语必须是归一化后快照抽取文本的**精确子串**。
 *
 * 返回 `{ verdict, normalizedQuote, normalizedSnapshot, knownLimitation }`。
 * `verdict` ∈ {'pass','fail'}；`knownLimitation` 在命中已认账的结构性缺陷时非空。
 */
export function quoteFaithful(snapshot, quote, { pdf = false } = {}) {
  const s0 = pdf ? dehyphenate(snapshot) : snapshot
  const q0 = pdf ? dehyphenate(quote) : quote
  const ns = normalizeQuote(s0)
  const nq = normalizeQuote(q0)
  const hit = ns.includes(nq)

  // 已认账的结构性缺陷（S0 记录 M0-2 的 BUG-2，**现行 §1.2.2 并未修好**）：
  // 引语截断在跨行连字符还原窗口内时，还原在快照侧生效、在引语侧不生效，两侧必然分叉。
  // 不静默——一条被静默掉的已知缺陷会在下一次重构里被当成「本来就该这样」。
  const truncatedInHyphenWindow = pdf && /-\s*$/.test(quote.replace(/\n$/, '')) &&
    String(snapshot).includes(String(quote))
  return {
    verdict: hit ? 'pass' : 'fail',
    normalizedQuote: nq,
    normalizedSnapshot: ns,
    knownLimitation: (!hit && truncatedInHyphenWindow)
      ? 'BUG-2：引语截断在跨行连字符还原窗口内，现行 §1.2.2 未修（见 gates/repro/m0_2_normalization.py 的期望值）'
      : null,
  }
}
