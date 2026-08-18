/**
 * 一次完整的 run —— 把全部环节串起来。
 *
 *   抓取（W-02 锚点） → CAS（W-01） → 证据卡（W-06） → producer 提交（W-03）
 *   → 门链 + S（W-04） → status.json → 组稿（W-10） → 成稿
 *
 * 这是本项目对外的**唯一**入口。它承载的那条断言——
 * 「从一次网络抓取到读者看到的那个数字，中间没有任何一步允许 agent 直接写结论」——
 * 曾经**是假的**：R6 在这个文件里找到三条互相独立的反例路径（R6-01 `__` 后门 /
 * R6-02 fail-open 缺省 / R6-03 payload 遮蔽），其中最短的一条不需要后门、
 * 不需要伪造证据、不触发任何门。三条全部在 S 的**上游**，而当时没有一道门站在那一侧。
 *
 * 现在这个文件不再自己造 ctx：它只负责搬运素材，判定一律交给 `src/gate-ctx.mjs`，
 * 而 `gates/check_supply_contract.mjs` 逐条断言本文件没有绕过它。
 *
 * run 目录布局（01-CONTRACTS §4）：
 *   runs/<run_id>/manifest.json     运行时指纹（W-12）
 *   objects/<sha256>                CAS（W-01）
 *   evidence/<evidence_id>.json     证据卡（W-06）
 *   claims/<id>.json                claim 内容（W-03）
 *   claims/<id>.status.json         status 及派生字段（W-04）
 *   gate-reports/<run_id>/*.json    门产出，带自证签名（W-08）
 *   prose/                          成稿（W-10）
 */
import { mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { putObject, putEvidence } from './cas.mjs'
import { runClaim } from './pipeline.mjs'
import { compose } from './composer.mjs'
import { buildAnchor, validateAnchor } from '../packages/dsh-academic-fetch/lib/anchor.js'
import { assertNoProducerContamination, buildGateCtx, sealStatus } from './gate-ctx.mjs'
import { freezeQuestion } from './gates/g-freeze.mjs'

export const RUN_VERSION = 'run-2026-08-18'

/**
 * @param {string} root      run 根目录
 * @param {string} runId
 * @param {object[]} fetches [{url, body, httpStatus, retrievedAt, extractorVersion, work_id, version_id, locator, quote}]
 * @param {object[]} claims  producer 的提交（含 evidence_ref_index 指向 fetches 下标）
 * @param {string} skeleton  作者 agent 写的叙述骨架
 * @param {object} [env]     { budget_state, counterSearches: {claim_id: {query, result_keys}} }
 */
export function runOnce(root, runId, fetches, claims, skeleton, env = {}) {
  for (const d of ['objects', 'evidence', 'claims', 'prose', join('runs', runId), join('gate-reports', runId)]) {
    mkdirSync(join(root, d), { recursive: true })
  }
  const log = []

  // ── ⓪ 问题冻结 —— 必须在**任何一次抓取之前** ──────────────────────────
  // 顺序即断言：G-FREEZE 判 K-D 是否 question_frozen 的方式，是比对冻结时刻
  // 与每条证据的 retrieved_at。若这段挪到抓取之后，那条判据就恒真而无声。
  // 冻结时刻由调用方给（env.frozen_at），保证同一份输入重跑逐字节相同。
  const frozen = env.question
    ? freezeQuestion(env.question, env.frozen_at ?? '1970-01-01T00:00:00Z')
    : null
  if (frozen) writeFileSync(join(root, 'runs', runId, 'question.json'), JSON.stringify(frozen, null, 2) + '\n')

  // ── ① 抓取 → 锚点 → CAS → 证据卡 ──────────────────────────────────────
  const cards = []
  for (const f of fetches) {
    const anchor = buildAnchor(f)                 // 非法抓取在这里就抛
    const bad = validateAnchor(anchor)
    if (bad) throw new Error(`锚点校验失败：${bad}`)
    const h = putObject(root, f.body)
    if (h !== anchor.object_sha256) throw new Error('CAS 地址与锚点哈希不符')
    cards.push(putEvidence(root, {
      work_id: f.work_id, version_id: f.version_id, locator: f.locator,
      quote: f.quote, extractor_version: f.extractorVersion, object_sha256: h,
      anchor,   // W-02 的锚点原样留存，供复核
    }))
    cards[cards.length - 1].object_sha256 = h
    log.push({ step: 'fetch', url: anchor.url, object_sha256: h })
  }

  // ── ② 每条 claim 过门链 ───────────────────────────────────────────────
  const statusById = new Map()
  const decided = new Map()          // K-I 的前提查表：只认本 run 已判定的 claim
  for (const c of claims) {
    // 〔R6-01〕检查必须锚在**原始对象**上、发生在读取之前。
    // 原缺陷是「先把 `__` 字段读进 ctx，再从提交里删掉」——删得越干净，
    // 审计工件越像清白的。
    assertNoProducerContamination(c, `claim ${c.claim_id}`)

    const idxs = c.evidence_index ?? []
    // 〔R6-05〕递给 G-CLUSTER 的键此前只有 evidence_id/work_id/upstream_id/
    // cites_source_id，于是六条归并规则里四条是**死代码**，逐字节相同的两份
    // 快照能算成 2 个独立簇。归并器做得到，是管线没喂给它。
    const evidence = idxs.map(i => ({
      fetch: fetches[i],
      ref: {
        evidence_id: cards[i].evidence_id,
        work_id: cards[i].work_id,
        object_sha256: cards[i].object_sha256,
        ...pick(fetches[i], ['doi', 'arxiv_id', 'title', 'authors', 'domain', 'lang',
                             'upstream_id', 'cites_source_id', 'self_cite_group']),
      },
    }))
    const submission = { ...c, evidence_refs: evidence.map(e => e.ref) }
    delete submission.evidence_index

    const ctx = buildGateCtx({
      root, submission, evidence, frozen,
      decided, budgetState: env.budget_state ?? 'ok',
      counterSearch: (env.counterSearches ?? {})[c.claim_id],
    })

    const r = runClaim(submission, ctx)
    if (!r.ok) throw new Error(`claim ${c.claim_id} 被拒：${r.denial}`)
    writeFileSync(join(root, 'claims', `${c.claim_id}.json`), JSON.stringify(submission, null, 2) + '\n')
    writeFileSync(join(root, 'claims', `${c.claim_id}.status.json`), JSON.stringify(r.statusRecord, null, 2) + '\n')
    writeFileSync(join(root, 'gate-reports', runId, `${c.claim_id}.json`), JSON.stringify(r.gateReport, null, 2) + '\n')
    decided.set(c.claim_id, r.statusRecord)
    // 〔R6-03〕门字段压过 payload，且冲突当场抛——不让攻击静默失败。
    statusById.set(c.claim_id, sealStatus(r.statusRecord, submission.payload ?? {}))
    log.push({ step: 'claim', id: c.claim_id, status: r.statusRecord.status })
  }

  // ── ③ 组稿 ───────────────────────────────────────────────────────────
  const composed = compose(skeleton, statusById)
  if (!composed.ok) throw new Error(`组稿被拒：${composed.denial}`)
  writeFileSync(join(root, 'prose', 'main.md'), composed.prose + '\n')

  // ── ④ 运行时指纹（W-12） ──────────────────────────────────────────────
  const manifest = {
    run_id: runId, run_version: RUN_VERSION,
    evidence_cards: cards.length, claims: claims.length,
    statuses: Object.fromEntries([...statusById].map(([k, v]) => [k, v.status])),
    log,
  }
  writeFileSync(join(root, 'runs', runId, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n')
  return { manifest, prose: composed.prose, statusById }
}

/** 只取在场的键——`undefined` 进了 ref 会让归并键判断被 `'undefined'` 污染。 */
function pick(o, keys) {
  const r = {}
  for (const k of keys) if (o?.[k] !== undefined && o[k] !== null) r[k] = o[k]
  return r
}
