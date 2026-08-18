/**
 * 顶层入口 —— 一个研究问题进去，一份带状态的成稿出来。
 *
 * 这是把前面所有部件接成一个可运行系统的地方：
 *
 *   研究问题
 *     → N 条并行论据线（orchestrator，确定性调度）
 *       → 每轮：取证（anchor + CAS + 证据卡）→ claim → 门链 → S → status
 *         → 读 status 的 trace 查表决定下一步（不是模型判断）
 *     → 全部线到终态或预算耗尽
 *   → 组稿（W-10，拒裸数字）
 *   → 成稿：每个数字带 status + 名义来源/独立簇
 *
 * 模型只在**叶子**上出现：提出 claim、写检索 query、写叙述骨架。
 * 每一片叶子的产出都要过确定性的门，且门的判定进 status，status 进成稿。
 *
 * 〔R6 的程序性发现，值得留在这里〕本文件是 S3 阶段新加的入口，它把 run.mjs 的
 * R6-02 / R6-03 / R6-08 三条缺陷**逐字复制**了一遍——`rerun_gate_passed: true`
 * 这样的字面量、payload 后展开、只核第一条证据。攻击者的结论是：
 * 「这说明缺陷是结构性的，不是笔误。」正确的修法因此不是在两个文件里各改一遍，
 * 而是让**两个文件都无法自己造 ctx**（`src/gate-ctx.mjs`），并由门断言这一点。
 */
import { mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { putObject, putEvidence } from './cas.mjs'
import { runClaim } from './pipeline.mjs'
import { compose } from './composer.mjs'
import { exploreParallel, diagnose } from './orchestrator.mjs'
import { buildAnchor, validateAnchor } from '../packages/dsh-academic-fetch/lib/anchor.js'
import { assertNoProducerContamination, buildGateCtx, sealStatus } from './gate-ctx.mjs'
import { freezeQuestion } from './gates/g-freeze.mjs'

export const RESEARCH_VERSION = 'research-2026-08-18'

/**
 * @param {string} root
 * @param {string} runId
 * @param {object} spec {
 *   question,
 *   threads: [{ id, rounds: [{ fetch, claim, counterSearch }] }],   // 每轮一个尝试
 *   skeleton,
 * }
 * @param {object} [opts] { maxConcurrent, budget, maxRounds }
 */
export async function research(root, runId, spec, opts = {}) {
  for (const d of ['objects', 'evidence', 'claims', 'prose', join('runs', runId), join('gate-reports', runId)]) {
    mkdirSync(join(root, d), { recursive: true })
  }
  const statusById = new Map()
  const decided = new Map()
  const evidenceCount = { n: 0 }

  // 问题冻结先于一切取证 —— 与 run.mjs 同一条理由（顺序即断言）。
  const frozen = spec.question
    ? freezeQuestion(spec.question, opts.frozenAt ?? '1970-01-01T00:00:00Z')
    : null
  if (frozen) writeFileSync(join(root, 'runs', runId, 'question.json'), JSON.stringify(frozen, null, 2) + '\n')

  const threads = spec.threads.map(t => ({
    id: t.id,
    explore: async (round) => {
      const attempt = t.rounds[Math.min(round - 1, t.rounds.length - 1)]
      if (!attempt) return { status: 'not_covered', trace: ['0g → not_covered'], reason: 'no-attempt' }

      // 取证：锚点 → CAS → 证据卡。任何一步不合法都当场抛。
      assertNoProducerContamination(attempt.claim, `[${t.id}] claim`)
      const evidence = []
      for (const f of attempt.fetches ?? []) {
        const anchor = buildAnchor(f)
        const bad = validateAnchor(anchor)
        if (bad) throw new Error(`[${t.id}] 锚点校验失败：${bad}`)
        const h = putObject(root, f.body)
        const card = putEvidence(root, {
          work_id: f.work_id, version_id: f.version_id, locator: f.locator,
          quote: f.quote, extractor_version: f.extractorVersion, object_sha256: h, anchor,
        })
        evidenceCount.n++
        evidence.push({ fetch: f, ref: {
          evidence_id: card.evidence_id, work_id: f.work_id, object_sha256: h,
          ...pick(f, ['doi', 'arxiv_id', 'title', 'authors', 'domain', 'lang',
                      'upstream_id', 'cites_source_id', 'self_cite_group']),
        } })
      }

      const submission = { ...attempt.claim, evidence_refs: evidence.map(e => e.ref) }
      delete submission.evidence_index
      const ctx = buildGateCtx({
        root, submission, evidence, frozen,
        decided, budgetState: opts.budgetState ?? 'ok',
        counterSearch: attempt.counterSearch,
      })
      const r = runClaim(submission, ctx)
      if (!r.ok) throw new Error(`[${t.id}] claim 被拒：${r.denial}`)

      writeFileSync(join(root, 'claims', `${submission.claim_id}.json`), JSON.stringify(submission, null, 2) + '\n')
      writeFileSync(join(root, 'claims', `${submission.claim_id}.status.json`), JSON.stringify(r.statusRecord, null, 2) + '\n')
      writeFileSync(join(root, 'gate-reports', runId, `${submission.claim_id}-r${round}.json`),
        JSON.stringify(r.gateReport, null, 2) + '\n')
      decided.set(submission.claim_id, r.statusRecord)
      statusById.set(submission.claim_id, sealStatus(r.statusRecord, submission.payload ?? {}))
      return r.statusRecord
    },
  }))

  const explored = await exploreParallel(threads, {
    maxRounds: opts.maxRounds ?? 3,
    maxConcurrent: opts.maxConcurrent ?? 6,
    budget: opts.budget,
  })

  const composed = compose(spec.skeleton, statusById)
  if (!composed.ok) throw new Error(`组稿被拒：${composed.denial}`)
  writeFileSync(join(root, 'prose', 'main.md'), composed.prose + '\n')

  const manifest = {
    run_id: runId, research_version: RESEARCH_VERSION, question: spec.question,
    threads: spec.threads.length, rounds: explored.rounds,
    evidence_cards: evidenceCount.n,
    budget_exhausted: explored.budgetExhausted,
    statuses: Object.fromEntries([...statusById].map(([k, v]) => [k, v.status])),
    // 每条线卡在哪、下一步该做什么——**查表得出，不是模型判断**
    diagnostics: explored.log.map(l => ({ ...l })),
    exploration: explored.log,
  }
  writeFileSync(join(root, 'runs', runId, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n')
  return { manifest, prose: composed.prose, statusById }
}

/** 与 run.mjs 同一个理由：`undefined` 进了 ref 会污染归并键。 */
function pick(o, keys) {
  const r = {}
  for (const k of keys) if (o?.[k] !== undefined && o[k] !== null) r[k] = o[k]
  return r
}
