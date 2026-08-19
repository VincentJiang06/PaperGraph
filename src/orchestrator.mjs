/**
 * 编排层 —— 超大并行的多 loop 论据探索。
 *
 * 用户最初需求的第 3 条：「一个超大并行的带有多个 loop 的论据探索系统」。
 * 前代（PaperGraph）被证明只能靠低效的 LangGraph 执行；这里的立场不同：
 * **编排必须是确定性的，模型只在叶子上出现。**
 *
 * 结构：
 *   一个研究问题 → N 条**独立的论据线**（thread）并行探索
 *   每条线是一个 loop：提出 claim → 取证 → 过门链 → 读 status → 决定下一步
 *   收敛条件是**机器可判的**（不是「模型觉得够了」）：
 *     · 该线的 claim 拿到终态（verified / contested / 或连续 K 轮没有状态提升）
 *     · 或预算耗尽
 *
 * 三条设计约束，每一条都来自前面几轮的结论：
 *
 * 1. **status 决定下一步，不是模型决定。** 一条 unverified 的 claim 该补证据还是该降级，
 *    由 §1.5 的 trace 说了算——trace 里写着它卡在哪一步（0e？2b？2c？），
 *    补什么是**查表**，不是判断。
 *
 * 2. **预算是硬闸，不是建议。** budget_state 是 S 的输入（0f/2e）；
 *    编排层耗尽预算时不是「尽力而为」，是让所有未完成的 claim 落 ST-N。
 *
 * 3. **并行度受控且可复现。** workflow 引擎的并发闸在 profile 里写死
 *    （maxConcurrentAgents: 6）；调度顺序由 thread id 排序决定，不由完成时刻决定，
 *    否则同一批输入两次运行会得到不同的探索路径。
 */

/** 从 S 的 trace 推出「卡在哪一步」——补什么是查表，不是判断 */
export function diagnose(statusRecord) {
  const trace = statusRecord.trace ?? []
  const last = String(trace[trace.length - 1] ?? '')
  const step = last.split(' ')[0]
  const TABLE = {
    '0-required': { blocked_at: '必填字段缺失', remedy: 'complete-record', escalate: false },
    '0-domain':   { blocked_at: '字段取值域外', remedy: 'complete-record', escalate: false },
    '0-flag-driver': { blocked_at: 'flag 与驱动字段不一致', remedy: 'refetch', escalate: true },
    '0a': { blocked_at: '快照被改或丢失', remedy: 'refetch', escalate: false },
    '0b': { blocked_at: '来源被污染', remedy: 'stop', escalate: true },
    '0c': { blocked_at: '一手源不可达', remedy: 'find-other-source', escalate: false },
    '0d': { blocked_at: '引语不是快照子串', remedy: 'fix-quote', escalate: false },
    '0e': { blocked_at: '未做反证检索', remedy: 'counter-search', escalate: false },
    '0f': { blocked_at: '预算耗尽', remedy: 'stop', escalate: true },
    '0g': { blocked_at: '决定性机制未运行', remedy: 'run-gates', escalate: false },
    '2a': { blocked_at: '找到反证', remedy: 'stop', escalate: false },
    '2b': { blocked_at: '独立簇数不足', remedy: 'more-independent-sources', escalate: false },
    '2c': { blocked_at: '证据等级或保留档压上限', remedy: 'upgrade-evidence', escalate: false },
    '2d': { blocked_at: 'flag 上限', remedy: 'address-flags', escalate: false },
    "2d'": { blocked_at: 'flag 降档', remedy: 'address-flags', escalate: false },
    '2e': { blocked_at: '预算降档', remedy: 'stop', escalate: true },
  }
  const key = Object.keys(TABLE).find(k => step === k || step.startsWith(k))
  return key ? { step: key, ...TABLE[key] }
             : { step, blocked_at: '终态', remedy: 'none', escalate: false }
}

const TERMINAL = new Set(['verified', 'contested'])

/**
 * 跑一组并行论据线。
 *
 * @param {object[]} threads  [{id, explore(round, prevStatus) -> statusRecord}]
 * @param {object} opts { maxRounds, maxConcurrent, budget, noProgressRounds, ledger }
 * @returns {{results, rounds, log, budgetExhausted, cost}}
 *
 * 〔ledger〕可选的 CostLedger（src/cost.mjs）。thread 的 explore() 若返回
 * `{ record, usage }`，usage 会被逐条记账并按**阶段**与**最终 status** 归集。
 * 归集到 status 是刻意的：本项目的产品是逐条 claim 的状态，
 * 那么「拿到一条 verified 值多少钱」才是真正要优化的那个数，
 * 而一个笼统的「这次跑了多少钱」回答不了它。
 */
export async function exploreParallel(threads, opts = {}) {
  const maxRounds = opts.maxRounds ?? 5
  const maxConcurrent = opts.maxConcurrent ?? 6
  const noProgressLimit = opts.noProgressRounds ?? 2
  let budget = opts.budget ?? Infinity

  // 调度顺序由 thread id 排序决定，**不由完成时刻决定**——
  // 否则同一批输入两次运行会得到不同的探索路径，整个 run 不可复现。
  const ordered = [...threads].sort((a, b) => String(a.id) < String(b.id) ? -1 : 1)
  const state = new Map(ordered.map(t => ({ id: t.id, status: null, rounds: 0, noProgress: 0, done: false }))
    .map(s => [s.id, s]))
  const log = []
  let budgetExhausted = false

  for (let round = 1; round <= maxRounds; round++) {
    const active = ordered.filter(t => !state.get(t.id).done)
    if (!active.length) break

    // 并发闸：分批，每批 maxConcurrent 条。批内并行，批间串行。
    for (let i = 0; i < active.length; i += maxConcurrent) {
      const batch = active.slice(i, i + maxConcurrent)
      const settled = await Promise.all(batch.map(async t => {
        const s = state.get(t.id)
        if (budget <= 0) { budgetExhausted = true; return { t, s, rec: null } }
        budget -= 1
        const raw = await t.explore(round, s.status)
        // explore 可以返回裸 statusRecord（老形态），也可以返回 {record, usage}
        const rec = raw && raw.record !== undefined ? raw.record : raw
        if (opts.ledger && raw && raw.usage) {
          for (const u of [].concat(raw.usage)) {
            opts.ledger.record({ ...u, claimId: u.claimId ?? t.id, stage: u.stage ?? `round-${round}` })
          }
        }
        return { t, s, rec }
      }))

      for (const { t, s, rec } of settled) {
        s.rounds = round
        if (!rec) {
          // 预算耗尽：未完成的一律落 ST-N，不是「尽力而为」
          s.status = { status: 'not_covered', trace: ['0f → not_covered'], reason: 'budget-exhausted' }
          s.done = true
          log.push({ round, thread: t.id, status: 'not_covered', note: '预算耗尽' })
          continue
        }
        const prev = s.status?.status
        s.status = rec
        const d = diagnose(rec)
        if (TERMINAL.has(rec.status)) { s.done = true }
        else if (rec.status === prev) {
          s.noProgress += 1
          if (s.noProgress >= noProgressLimit) s.done = true
        } else { s.noProgress = 0 }
        log.push({ round, thread: t.id, status: rec.status, blocked_at: d.blocked_at, remedy: d.remedy,
                   ...(d.escalate ? { escalate: true } : {}) })
      }
    }
  }

  return {
    results: Object.fromEntries([...state].map(([id, s]) => [id, s.status])),
    rounds: Math.max(0, ...[...state.values()].map(s => s.rounds)),
    log, budgetExhausted,
    cost: opts.ledger ? {
      usd: opts.ledger.totalUsd,
      tokens: opts.ledger.totalTokens,
      calls: opts.ledger.calls.length,
      byStage: opts.ledger.byStage(),
    } : null,
    budgetLeft: budget === Infinity ? null : budget,
  }
}
