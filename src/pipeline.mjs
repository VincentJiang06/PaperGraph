/**
 * 证据管线 —— claim 进，status.json 出。
 *
 * 这是本项目第一条**端到端**的产品链路。它把已经各自成立的几块接起来：
 *   producer 提交（受写者契约约束） → GC-0 门链 → 派生字段 → S → status.json
 *
 * 三条设计约束，全部来自前面几轮攻击的结论：
 *
 * 1. **producer 只写内容**（W-03）。所有进入 S 判定的字段由本管线计算，
 *    提交里出现任何一个即 deny（`denyProducerSubmission`）。
 *    ——R5 第 5 条预测：六个纯自报谓词是 fail-closed 唯一的出口。
 *
 * 2. **门的产出带自证签名**（W-08：`generator_version` + `inputs_hash`）。
 *    前代四份 gate_report 无法复核，就是因为缺这个。
 *
 * 3. **判定发生在 dsh 进程之外**（01-CONTRACTS §4）。本模块是纯函数式的：
 *    输入是记录，输出是记录，不调用模型、不联网。因此它整体是 GC-0。
 */
import { createHash } from 'node:crypto'
import { denyProducerSubmission, denyGateWrite } from './writer-contract.mjs'
import { quoteFaithful } from './normalize.mjs'
import { polarityScope } from './gates/g-polarity.mjs'
import { anchorContainment } from './gates/g-containment.mjs'
import { frameGate } from './gates/g-frame.mjs'
import { cluster } from './gates/g-cluster.mjs'
import { counterQueryOk } from './gates/g-ctr-scan.mjs'
import { S } from './status.mjs'

export const GATE_VERSION = 'pipeline-2026-08-18'

const sha256 = s => createHash('sha256').update(typeof s === 'string' ? s : JSON.stringify(s)).digest('hex')


/**
 * 跑一条 claim。
 *
 * @param {object} submission producer 提交的内容（W-03 字段）
 * @param {object} ctx 门侧上下文：快照文本、锚句、证据卡、预算、机制结果等
 * @returns {{ok:boolean, denial?:string, statusRecord?:object, gateReport?:object}}
 */
export function runClaim(submission, ctx) {
  // ── ① 写者契约：producer 不得夹带任何判定字段 ────────────────────────
  const denial = denyProducerSubmission(submission)
  if (denial) return { ok: false, denial }

  const mech = []
  const record = { ...submission }

  // ── ② GC-0 门链 ──────────────────────────────────────────────────────
  // 引语门（§1.2.2）
  const hasQuote = typeof ctx.quote === 'string' && ctx.quote.length > 0
  record.has_verbatim_quote = hasQuote
  if (hasQuote) {
    const q = quoteFaithful(ctx.snapshotText ?? '', ctx.quote, { pdf: !!ctx.pdf })
    record.quote_faithful = q.verdict
    mech.push({ gate_id: 'G-QUOTE', gate_class: 'GC-0', verdict: q.verdict,
                known_limitation: q.knownLimitation ?? undefined })
  } else {
    record.quote_faithful = 'na'
  }

  // 锚点包含检验（K-L 路径的第一个合取项）。判定见 src/gates/g-containment.mjs：
  // 按 slot_type 分档——value/comparator 认数值等价，entity 认同词干，
  // metric/sample 一律逐字。原实现是裸 `includes`，对真实文献有系统性假阴
  // （`36` vs 原文 `Thirty-six`、`replication` vs 原文 `replicated`）。
  const payloadFields = Object.values(submission.payload ?? {}).map(v => String(v))
  const anchorSent = ctx.anchorSentence ?? ''
  const cont = anchorContainment(submission.payload, submission.slot_types, anchorSent)
  const containment = cont.pass
  record.anchor_containment_passed = containment
  mech.push({ gate_id: 'G-L1-b', gate_class: 'GC-0', verdict: containment ? 'pass' : 'fail',
              params: { containment_version: cont.version, per_slot: cont.per_slot } })

  // L1-c 极性作用域（第二个合取项）
  const pol = polarityScope(anchorSent, payloadFields, ctx.followingSentence ?? '')
  record.polarity_scope_passed = pol.pass
  mech.push({ gate_id: 'G-L1-c', gate_class: 'GC-0', verdict: pol.pass ? 'pass' : 'fail',
              params: pol.params, known_limitation: pol.knownLimitation ?? undefined })
  // G-FRAME：原文在同一处并列给了多个同量纲读数时，claim 必须声明
  // discriminator（逐字取自锚句、且不出现在兄弟读数里）。
  // 「只有 36% 的心理学研究可以被复现」逐字转录无误、极性无误、来源真实，
  // 错在把四个判据塌成一个——那是框架问题，包含与极性两道门都看不见。
  const frm = frameGate(ctx.snapshotText ?? '', anchorSent, submission.discriminator)
  record.frame_gate_passed = frm.pass
  mech.push({ gate_id: 'G-FRAME', gate_class: 'GC-0', verdict: frm.pass ? 'pass' : 'fail',
              params: { frame_version: frm.version, triggered: frm.triggered,
                        sibling_readings: frm.siblings.length, why: frm.why },
              known_limitation: frm.triggered ? undefined
                : '本门只看分号并列的同量纲读数；没有这个指纹的框架塌陷看不见' })
  record.sub_mode = (containment && pol.pass && frm.pass) ? 'T' : 'A'

  // 簇归并（G-CLUSTER）。它是本项目最脆的一块：R5 第 3 条预测说真实语料上
  // 独立簇会被转引链 / 跨语言链 / 自证回路 / 三版同文系统性压塌。
  // 本管线的立场是**认真归并、让代价可见**——少算的部分由 nominal_source_count
  // 与独立簇数并排展示（§5.5 R-I6）。
  // 只对**支持本 claim** 的证据归并成簇。一条锚句里没有这个载荷、
  // 或正在否定它的文献，不该算作支持它的一个独立来源（外部标定测试 T3-3）。
  const supporting = ctx.supporting_refs ?? submission.evidence_refs
  const cl = cluster(supporting)
  record.independent_cluster_count = cl.independent_cluster_count
  // 名义来源数仍按**全部**证据算——排除掉的那些必须仍然可见，
  // 否则「引了三篇、只有一篇支持」会看起来跟「只引了一篇」一样。
  record.nominal_source_count = (submission.evidence_refs ?? []).length || cl.nominal_source_count
  record.supporting_source_count = cl.nominal_source_count
  mech.push({ gate_id: 'G-CLUSTER', gate_class: 'GC-0', verdict: 'pass',
              params: { rules_version: cl.rules_version, applied_rules: cl.applied_rules,
                        cluster_map: cl.cluster_map },
              known_limitation: cl.knownLimitation ?? undefined })

  // G-CTR-SCAN：`counter_evidence_searched` 必须由**门算出来**，不能由上游递进来。
  // 它是 0e 的前置否决项，§7.2.3 称它是「逃不过的只有这一条」——
  // 若它可以被递一个 true 进来，那条防线就只是纪律。
  // 判据是 X-2 的四条结构判据（双侧：锚槽覆盖下界 + 载荷外 token 预算），
  // 只有当 producer 真的发过一条**结构上像反证**的 query 时才置 true。
  // 没有 counter-search 记录 = 没搜过。fail-closed，不接受上游递一个 true 进来。
  // 〔实现期发现〕初版只在有记录时才覆盖，于是「递 true 但没发 query」这条
  // 攻击直接穿过去了——**由门计算**这句话必须对「没有输入」也成立。
  let ctr = null
  if (!ctx.counterSearch) {
    record.counter_evidence_searched = false
    mech.push({ gate_id: 'G-CTR-SCAN', gate_class: 'GC-0', verdict: 'fail',
                reasons: ['没有 counter_search 记录 —— 未做反证检索（0e）'] })
  }
  if (ctx.counterSearch) {
    ctr = counterQueryOk(submission, ctx.counterSearch.query, {
      resultKeys: ctx.counterSearch.result_keys ?? [],
      knownWorkIds: ctx.knownWorkIds,
      // 锚句取自 ctx（门从快照算的那一份），不取 submission 上的任何字段
      anchorSentence: ctx.anchorSentence ?? '',
      snapshotText: ctx.snapshotText ?? '',
    })
    record.counter_evidence_searched = ctr.pass
    mech.push({ gate_id: 'G-CTR-SCAN', gate_class: 'GC-0',
                verdict: ctr.pass ? 'pass' : 'fail',
                params: ctr.params, reasons: ctr.pass ? undefined : ctr.reasons,
                known_limitation: ctr.knownLimitation })
  }

  // ── ③ 本管线**自己算出来的**字段，与**从别的写者接住的**字段，必须分开 ──
  //
  // 〔实现期发现〕初版把两者混在一起交给 `denyGateWrite` 自检，于是
  // `budget_state`（编排层拥有，W-13）被当成「门在写它不拥有的字段」而拒绝。
  // 那是自检**误报**，但它指出了一个真问题：**转抄不是书写，可两者在记录里长得一样**。
  // 分开之后契约更锋利——自检只管本管线派生的字段，转抄的字段各自由其写者负责，
  // 且此处逐一列出来源，让「这个值是谁写的」在代码里可读，而不是靠记忆。
  const computed = {
    has_verbatim_quote: record.has_verbatim_quote,
    quote_faithful: record.quote_faithful,
    anchor_containment_passed: record.anchor_containment_passed,
    polarity_scope_passed: record.polarity_scope_passed,
    sub_mode: record.sub_mode,
    independent_cluster_count: record.independent_cluster_count,
    nominal_source_count: record.nominal_source_count,
    mechanism_results: mech,
    ...(ctr ? { counter_evidence_searched: record.counter_evidence_searched } : {}),
  }
  const gateDenial = denyGateWrite(computed)
  if (gateDenial) return { ok: false, denial: gateDenial }

  // 从别的写者接住的（每一项都标注写者，便于审计）
  const PROVIDED_BY = {
    source_integrity: 'fetch-executor(W-02)', evidence_grade: 'gate(W-04)',
    retention_tier: 'gate(W-04)', budget_state: 'orchestrator(W-13)',
    counter_evidence_searched: 'gate(W-04)', counter_evidence_found: 'gate(W-04)',
    rerun_gate_passed: 'gate(W-04)', question_frozen: 'gate(W-04)',
    inference_gate_passed: 'gate(W-04)', attribution_verdict: 'gate(W-04)',
    chart_extracted: 'gate(W-04)', flags: 'gate(W-14)',
  }
  for (const k of Object.keys(PROVIDED_BY)) if (k in ctx) record[k] = ctx[k]
  Object.assign(record, computed)
  // 门算出来的永远压过递进来的——否则「由门计算」只是一句话。
  record.counter_evidence_searched = ctr ? ctr.pass : false
  // 〔R6-06〕找到与否同样由门算：声称找到 ⇒ (e′) 已核对该作品确被抓过。
  record.counter_evidence_found = ctr ? ctr.found : false

  // ── ⑤ S ──────────────────────────────────────────────────────────────
  let s
  try { s = S(record) } catch (e) { return { ok: false, denial: `S 抛出契约缺口：${e.message}` } }

  const inputsHash = sha256({ submission, ctx: { ...ctx, __v: GATE_VERSION } })
  const statusRecord = {
    claim_id: submission.claim_id,
    status: s.status,
    evidence_grade: record.evidence_grade,
    independent_cluster_count: record.independent_cluster_count,
    nominal_source_count: record.nominal_source_count,
    counter_evidence_searched: record.counter_evidence_searched,
    counter_evidence_found: record.counter_evidence_found,
    sub_mode: record.sub_mode,
    caveats: pol.caveats,
    // §5.5 R-I6：名义来源数必须与独立簇数**并排展示**。
    // 「11 家中文媒体全部回溯到同一条 Nikkei Asia」这种情况下两个数差 11 倍，
    // 而只给读者看其中一个都是误导。
    identity_merge_candidates: cl.identity_merge_candidates,
    gate_version: GATE_VERSION,
    inputs_hash: inputsHash,
    trace: s.trace,
    provided_by: Object.fromEntries(
      Object.entries(PROVIDED_BY).filter(([k]) => k in ctx)),
  }
  const gateReport = {
    run: submission.claim_id,
    generator_version: GATE_VERSION,   // W-08 自证签名
    inputs_hash: inputsHash,
    mechanism_results: mech,
    known_limitations: mech.map(m => m.known_limitation).filter(Boolean),
  }
  return { ok: true, statusRecord, gateReport }
}
