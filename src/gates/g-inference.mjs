/**
 * G-INFERENCE —— K-I（逻辑推断类）的把关谓词 `inference_gate_passed`。
 *
 * K-I 永不可达 ST-V（§2.3.1），它的天花板是 ST-A。但「可达 ST-A」本身
 * 也必须有条件，否则 K-I 就成了一条把任意断言写进成稿的免检通道。
 *
 * 可机器判定的条件只有一个，但它是真的：**前提必须自己站得住**。
 *   ① 前提集非空（没有前提的「推断」是断言）；
 *   ② 每条前提都是本 run 里已判定的 claim；
 *   ③ 每条前提的状态 ≥ ST-A（未验证的前提推不出被归因的结论）；
 *   ④ 不自指、不成环（c 以自己为前提是循环论证的机器可判形态）。
 *
 * 〔不宣称的部分〕本门**不判断推理形式是否有效**。那不可机器判定。
 * 所以 K-I 拿到的是 ST-A（「前提可追」），不是 ST-V（「结论已验证」）——
 * 这正是 §2.3.1 给 K-I 设天花板的原因，两者是同一件事的两面。
 */
export const INFERENCE_VERSION = 'g-inference-2026-08-18'
const OK = new Set(['verified', 'attributed'])

/**
 * @param {object} submission  读 premises（claim_id 数组，W-03 内容字段）
 * @param {Map<string,object>} decided 本 run 已判定的 claim（id → statusRecord）
 */
export function inferenceGate(submission, decided = new Map()) {
  const params = { inference_version: INFERENCE_VERSION }
  const prem = submission?.premises
  if (!Array.isArray(prem) || prem.length === 0) {
    return { pass: false, reasons: ['K-I 未给出前提 —— 没有前提的推断是断言'], params }
  }
  params.premises = prem

  const missing = prem.filter(p => !decided.has(p))
  if (missing.length) return { pass: false, params, reasons: [`前提不在本 run 的已判定集里：${missing.join(', ')}`] }

  if (prem.includes(submission.claim_id)) {
    return { pass: false, params, reasons: ['前提包含结论自身 —— 循环论证'] }
  }

  const weak = prem.filter(p => !OK.has(decided.get(p).status))
  if (weak.length) {
    return { pass: false, params,
      reasons: [`${weak.length} 条前提未达 ST-A：${weak.map(p => `${p}=${decided.get(p).status}`).join(', ')}`] }
  }
  return { pass: true, reasons: [], params }
}
