/**
 * 供给侧契约 —— S 的**输入是谁造的**。
 *
 * 〔它为什么存在：R6 的裁决〕
 * R6 对核心承诺（「从抓取到成稿没有任何一步允许 agent 直接写结论」）判**假**，
 * 给了三条互相独立的反例路径，全部在 S 的**上游**：
 *
 *   R6-01  `__` 前缀字段先被读进 ctx、**再**从 submission 删掉，
 *          于是 `denyProducerSubmission` 的白名单从未见过它们。
 *          落盘的 claim 已剥干净，status.json 的 provided_by 还把这些值
 *          标注成 `gate(W-04)` —— 不只是绕过，是**洗白**。
 *   R6-02  四个谓词是 fail-open 缺省（`?? true`），research.mjs 更直接写字面量 true。
 *   R6-03  `{...statusRecord, ...payload}` 的展开顺序，让 producer 只要把
 *          payload 槽命名为 `status` 就改写读者看到的标记。全程合法字段，零门触发。
 *
 * 而 R6-09 说清了为什么 22 道门全绿时这三条同时成立：
 * `check_writer_contract` 的不变式**只作用在 status.mjs 上**，读集从它的源码提取，
 * 门从不看 run.mjs / research.mjs。「谁写这个字段」的证明链在管线入口就断了，
 * `PROVIDED_BY` 那张表标注的写者是**注释**，不是被任何东西检验的事实。
 *
 * 本模块把那段断链接上，做法是让供给侧只有一条路：
 *
 *   ① `assertNoProducerContamination` —— producer 对象里出现任何 `__` 前缀字段
 *      即当场抛。R6-01 的后门是「先读后删」，所以检查必须在**读之前**，
 *      并且针对**原始对象**，而不是删干净之后的副本。
 *   ② `buildGateCtx` —— 是构造 ctx 的**唯一**函数。每个门字段都由门算出来，
 *      没有任何一项从 producer 的字段取值，也没有任何一项有 fail-open 缺省。
 *   ③ `sealStatus` —— 门算出的字段永远压过 payload，且冲突会**报出来**而不是静默。
 *
 * 这三条各自都能被 `gates/check_supply_contract.mjs` 机器检验；
 * 「结论由门算」从此不再是一句注释。
 */
import { PRODUCER_WRITABLE, FIELD_OWNER, WRITER } from './writer-contract.mjs'
import { sourceIntegrity } from './cas.mjs'
import { rerunGate } from './gates/g-rerun.mjs'
import { freezeGate } from './gates/g-freeze.mjs'
import { inferenceGate } from './gates/g-inference.mjs'
import { attributionGate } from './gates/g-attribution.mjs'
import { gradeOfClaim, GRADE_VERSION } from './gates/g-grade.mjs'
import { followingSentenceOf, anchorContainment } from './gates/g-containment.mjs'
import { quoteFaithful } from './normalize.mjs'
import { polarityScope } from './gates/g-polarity.mjs'

export const CTX_VERSION = 'gate-ctx-2026-08-18'

/** S 会读、且不归 producer 所有的字段 —— 也就是「必须由门供给」的那一组。 */
export const GATE_SUPPLIED = Object.freeze(
  Object.entries(FIELD_OWNER).filter(([, w]) => w !== WRITER.PRODUCER).map(([k]) => k))

/**
 * ① producer 对象不得夹带任何 `__` 前缀字段。
 *
 * 为什么单独立一条而不是并进 `denyProducerSubmission`：后者检查的是
 * **提交对象**，而 R6-01 的通道是「原始 claim 对象 → ctx」，提交对象在那之后
 * 才被剥干净。要堵住它，检查必须锚在**原始对象**上、发生在读取之前。
 * 抛而不是返回 denial：这条不是「这次提交不合格」，是「调用方写错了」。
 */
export function assertNoProducerContamination(raw, where = 'producer claim') {
  const dunder = Object.keys(raw ?? {}).filter(k => k.startsWith('__'))
  if (dunder.length) {
    throw new Error(`${where} 夹带门侧字段：${dunder.join(', ')} —— ` +
      '`__` 前缀曾是绕过写者契约白名单的后门（R6-01），现已封死')
  }
  const owned = Object.keys(raw ?? {}).filter(k => k in FIELD_OWNER && FIELD_OWNER[k] !== WRITER.PRODUCER)
  if (owned.length) {
    throw new Error(`${where} 夹带门拥有的字段：${owned.join(', ')}`)
  }
}

/**
 * ② 构造门侧上下文。**这是唯一允许构造 ctx 的地方。**
 *
 * @param {object} a
 * @param {string} a.root            run 根目录
 * @param {object} a.submission      producer 提交（只读 W-03 内容字段）
 * @param {object[]} a.evidence      [{ref, fetch}]，fetch 带 body/anchorSentence/retrievedAt…
 * @param {object|null} a.frozen     问题冻结记录（g-freeze）
 * @param {Map} a.decided            本 run 已判定的 claim（K-I 的前提查表）
 * @param {string} a.budgetState     编排层拥有（W-13）
 * @param {object} [a.counterSearch] 反证检索记录
 */
export function buildGateCtx({ root, submission, evidence = [], frozen = null,
                              decided = new Map(), budgetState = 'ok', counterSearch }) {
  const first = evidence[0]?.fetch ?? null
  const snapshotText = first ? String(first.body) : ''
  const anchorSentence = first?.anchorSentence ?? ''
  const quote = first?.quote ?? ''

  // ── source_integrity：**每一条**证据都要核 ────────────────────────────
  // 〔R6-08〕原实现只核 refs[0]，于是「第一条留干净、其余随便换」是免费的。
  // 多条证据取最坏值：完整性是合取，不是抽样。
  const RANK = { intact: 0, not_covered: 1, missing: 2, mutated: 3 }
  let si = evidence.length ? 'intact' : 'not_covered'
  const perRef = []
  for (const { ref } of evidence) {
    const v = sourceIntegrity(root, ref.evidence_id).verdict
    perRef.push({ evidence_id: ref.evidence_id, verdict: v })
    if (RANK[v] > RANK[si]) si = v
  }

  // ── 四个把关谓词：全部由门算，全部 fail-closed ────────────────────────
  const kind = submission.kind
  const payloadFields = Object.values(submission.payload ?? {}).map(v => String(v))
  // 下一句由门**从快照里算**，不读 fetch 递进来的值。
  // 跨句极性现在参与判定，这个字段就是判定输入——判定输入不能来自被判定方。
  const followingSentence = followingSentenceOf(snapshotText, anchorSentence)
  const pol = polarityScope(anchorSentence, payloadFields, followingSentence)

  // ── 每一条证据都要自证它在支持这条 claim ──────────────────────────────
  // 〔外部标定测试 T3-3〕原实现只对 evidence[0] 做锚点包含与极性检验，
  // 其余证据**一次都没被检查过**，却照样计入 nominal_source_count 与独立簇数。
  // 真实后果：一条 claim 引 DiMasi + Prasad + Wouters 三篇，成稿印
  // 「来源 3/独立簇 3」，读起来是三方独立支持——而后两篇的锚句里
  // 根本没有那个数（它们讲的是各自不同的估计），其中一篇还正在反驳它。
  //
  // 判据是两条，都已经有门：
  //   ① 这条证据的锚句里有没有这条 claim 的载荷（G-L1-b）
  //   ② 这条证据的锚句（含转折下一句）是不是在否定它（G-L1-c）
  // 任一不成立 ⇒ 它不是这条 claim 的**支持**来源，不计入簇。
  // 它仍然留在证据卡里、仍然可见——排除的是「算作一票」，不是「存在」。
  const perEvidence = evidence.map((e, i) => {
    const f = e.fetch ?? {}
    const a = String(f.anchorSentence ?? '')
    const cont = anchorContainment(submission.payload, submission.slot_types, a)
    const pp = polarityScope(a, payloadFields, followingSentenceOf(String(f.body ?? ''), a))
    return {
      index: i, work_id: e.ref?.work_id ?? f.work_id,
      supports: cont.pass && pp.pass,
      why: cont.pass ? (pp.pass ? null : '锚句被否定') : '锚句不含本 claim 的载荷',
    }
  })
  const supportingRefs = evidence.filter((_, i) => perEvidence[i].supports).map(e => e.ref)
  const qf = quote ? quoteFaithful(snapshotText, quote, { pdf: !!first?.pdf }).verdict : 'na'

  // K-D 的两条。非 K-D 的 claim 不需要它们（S 只在 K-D 分支读），
  // 但缺省仍是 false —— 「不适用」与「通过」必须是不同的值。
  const rr = kind === 'K-D'
    ? rerunGate(root, submission.rerun_spec)
    : { pass: false, reasons: ['非 K-D，重跑门不适用'], params: {} }
  const fz = kind === 'K-D'
    ? freezeGate(frozen, submission, evidence.map(e => e.fetch?.retrievedAt))
    : { pass: false, reasons: ['非 K-D，冻结门不适用'], params: {} }
  const inf = kind === 'K-I'
    ? inferenceGate(submission, decided)
    : { pass: false, reasons: ['非 K-I，推断门不适用'], params: {} }
  const att = attributionGate({ quote_faithful: qf, polarity_pass: pol.pass, quote, payloadFields })

  return {
    snapshotText, anchorSentence,
    followingSentence,
    per_evidence_support: perEvidence,
    supporting_refs: supportingRefs,
    quote,
    source_integrity: si,
    source_integrity_per_ref: perRef,
    evidence_grade: gradeOfClaim(evidence),
    retention_tier: tierOf(evidence),
    budget_state: budgetState,
    counter_evidence_found: false,      // 由 G-CTR-SCAN 在管线内覆盖（ctr.found）
    // 反证检索声称找到的作品，必须是本 run 真抓过的（(e′)，R6-06）
    knownWorkIds: new Set(evidence.map(e => e.ref.work_id).filter(Boolean)),
    rerun_gate_passed: rr.pass,
    question_frozen: fz.pass,
    inference_gate_passed: inf.pass,
    attribution_verdict: att.verdict,
    chart_extracted: evidence.some(e => e.fetch?.chart_extracted === true),
    flags: [],
    counterSearch,
    supply_mechanisms: [
      { gate_id: 'G-RERUN', gate_class: 'GC-0', verdict: rr.pass ? 'pass' : 'fail', params: rr.params, reasons: rr.reasons },
      { gate_id: 'G-FREEZE', gate_class: 'GC-0', verdict: fz.pass ? 'pass' : 'fail', params: fz.params, reasons: fz.reasons },
      { gate_id: 'G-INFERENCE', gate_class: 'GC-0', verdict: inf.pass ? 'pass' : 'fail', params: inf.params, reasons: inf.reasons },
      { gate_id: 'G-ATTRIBUTION', gate_class: 'GC-0', verdict: att.verdict, params: att.params, reasons: att.reasons },
      { gate_id: 'G-INTEGRITY', gate_class: 'GC-0', verdict: si, params: { per_ref: perRef } },
      { gate_id: 'G-GRADE', gate_class: 'GC-0', verdict: gradeOfClaim(evidence),
        params: { grade_version: GRADE_VERSION, per_ref: evidence.map(e => e.ref?.work_id) } },
    ],
    ctx_version: CTX_VERSION,
  }
}

// 留存档取全体**最坏**值,且未声明时按最短档 C 算。
// 〔与 G-GRADE 同一次修复,一并扳向 fail-closed〕缺省此前是 A(最长留存),
// 也就是说「没说留多久」= 「留最久」,而 §8.6.2 的档位上限正是拿它当天花板的。
// 说不清自己能留多久的证据,不该因为没人问就拿到最高天花板。
// 证据等级见 src/gates/g-grade.mjs——
// 它此前也在这里,写成 `Math.max`(取最好)而注释说「取最坏」,
// 且缺省是最高档 G5。两条都由外部标定测试 E-1/E-2 抓出来,已搬进独立的门。
const TIER_ORDER = ['A', 'B', 'C']
const tierOf = ev => ev.length
  ? TIER_ORDER[Math.max(...ev.map(e => Math.max(0, TIER_ORDER.indexOf(e.fetch?.retention_tier ?? 'C'))))]
  : 'C'

/**
 * ③ 组稿视图：门算出的字段永远压过 payload。
 *
 * 〔R6-03〕原写法 `{...statusRecord, ...payload}` 让 payload 后展开，
 * producer 把槽命名为 `status` 即改写读者看到的标记 —— S 判 unverified，
 * 成稿印「已验证，来源 9/独立簇 9」，全程合法字段、零门触发。
 *
 * 这里不只调换顺序（那只是让攻击**静默失败**），而是**报出来**：
 * 一个想把槽叫 `status` 的 producer，要么是在攻击，要么是在犯一个
 * 会让读者看到错东西的错误——两种都该响。
 */
export function sealStatus(statusRecord, payload = {}) {
  const collisions = Object.keys(payload).filter(k => k in statusRecord)
  if (collisions.length) {
    throw new Error(`payload 槽名与门字段冲突：${collisions.join(', ')} —— ` +
      'payload 若后展开即可改写读者看到的状态标记（R6-03）')
  }
  return { ...payload, ...statusRecord }
}
