/**
 * G-ATTRIBUTION —— K-L-A（文献归因类）的 `attribution_verdict`。
 *
 * 原实现：`attribution_verdict: c.__attribution ?? 'support'`。
 * 缺省是 **support** —— 也就是说「这篇文献支持我」这件事，产品默认相信 producer，
 * 而这正是整个项目宣称自己要消灭的那个动作。
 *
 * 判据全部来自已经在场的证据，不引入新的信息源：
 *   contradict —— 锚句的极性把载荷否定/限定掉了（L1-c 判 fail）；
 *   support    —— 引语逐字属实 ∧ 载荷落在引语内 ∧ 极性通过；
 *   unclear    —— 其余（含无引语、载荷不在引语内）。
 *
 * 注意 `unclear` 不是「没查」：§1.5 的 meet 让 unclear 把 K-L-A 压到 ST-U。
 * 换句话说 **拿不准就不许归因**，这与 support 缺省是相反的方向。
 */
export const ATTRIBUTION_VERSION = 'g-attribution-2026-08-18'

/**
 * @param {object} ev { quote_faithful:'pass'|'fail'|'na', polarity_pass:boolean, quote:string, payloadFields:string[] }
 */
export function attributionGate(ev) {
  const params = { attribution_version: ATTRIBUTION_VERSION }
  if (ev.polarity_pass === false) {
    return { verdict: 'contradict', params, reasons: ['锚句极性否定/限定了该载荷'] }
  }
  if (ev.quote_faithful !== 'pass') {
    return { verdict: 'unclear', params, reasons: [`引语未逐字属实（quote_faithful=${ev.quote_faithful}）`] }
  }
  const fields = ev.payloadFields ?? []
  if (!fields.length || !fields.every(f => String(ev.quote ?? '').includes(f))) {
    return { verdict: 'unclear', params, reasons: ['载荷不在引语内 —— 归因缺少落点'] }
  }
  return { verdict: 'support', params, reasons: [] }
}
