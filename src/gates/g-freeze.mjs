/**
 * G-FREEZE —— K-D 的第二个把关谓词 `question_frozen`。
 *
 * 「问题冻结」不是一句流程口号，它有一个可机器判定的核：
 * **问题必须在数据之前存在**。否则就是先看数据、再写一个正好被数据支持的问题
 * （HARKing）——而这条 claim 的 ST-V 会把这套动作洗成「已验证」。
 *
 * 因此本门检三件事，全部可判定：
 *   ① 本次 run 存在冻结记录（GC-0 在 fetch 之前写下）；
 *   ② claim 自称回答的问题，其哈希与冻结记录一致（改了问题 = 换了 run）；
 *   ③ 冻结时刻 ≤ 每一条证据的 retrieved_at（数据晚于问题）。
 *
 * 〔R6-02 的形态〕原实现是 `question_frozen: c.__frozen ?? true` ——
 * 缺省即通过，且 producer 可直接递 true。现在 producer 只能递「我回答的是哪个问题」，
 * 是否冻结由门比对它自己写下的记录得出。
 */
import { createHash } from 'node:crypto'

export const FREEZE_VERSION = 'g-freeze-2026-08-18'

export const questionHash = q =>
  createHash('sha256').update(String(q ?? '').trim()).digest('hex')

/** run 开始时调用：把问题钉在时间轴上。frozenAt 由调用方给，保持可复现。 */
export function freezeQuestion(question, frozenAt) {
  if (!question || !String(question).trim()) throw new Error('不能冻结一个空问题')
  if (!frozenAt) throw new Error('冻结必须带时刻——没有时刻就没有「之前」')
  return { question: String(question), question_hash: questionHash(question), frozen_at: frozenAt }
}

/**
 * @param {object|null} frozen freezeQuestion 的产出
 * @param {object} submission  producer 提交（读 question_hash，W-03 内容字段）
 * @param {string[]} retrievedAts 本 claim 全部证据的 retrieved_at
 */
export function freezeGate(frozen, submission, retrievedAts = []) {
  const params = { freeze_version: FREEZE_VERSION }
  if (!frozen) return { pass: false, reasons: ['本次 run 没有问题冻结记录'], params }
  params.frozen_at = frozen.frozen_at

  const declared = submission?.question_hash
  if (!declared) return { pass: false, reasons: ['claim 未声明它回答哪个问题（question_hash 缺失）'], params }
  if (declared !== frozen.question_hash) {
    return { pass: false, reasons: [`claim 回答的问题与冻结问题不符：${String(declared).slice(0, 12)}… ≠ ${frozen.question_hash.slice(0, 12)}…`], params }
  }

  // ③ 数据必须晚于问题。没有 retrieved_at 的证据无法判定先后 —— 判红，
  //    而不是「无法判定就放过」：后者正是 R6 一路打进来的那种缺省。
  const bad = retrievedAts.filter(t => !t || String(t) < frozen.frozen_at)
  if (bad.length) {
    return { pass: false, params,
      reasons: [`${bad.length} 条证据的 retrieved_at 早于问题冻结时刻（或缺失）—— 问题可能是照着数据写的`] }
  }
  return { pass: true, reasons: [], params }
}
