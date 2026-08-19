/**
 * 写者契约 —— 谁可以写哪个字段。
 *
 * 〔为什么这是产品的第一块代码〕R5 的第 5 条预测：
 *
 * > fail-closed 的稳态是全 ST-N，而唯一的出口本轮刚被留着。
 * > `question_frozen` / `rerun_gate_passed` / `anchor_containment_passed` /
 * > `polarity_scope_passed` / `inference_gate_passed` / `attribution_verdict`
 * > **六个纯自报谓词，一条 deny 规则都没有**。第一个真实 run 几乎必然压倒性
 * > `not_covered`，压力会指向最省力的出口：把两个谓词默认写 true，绿灯就回来了，
 * > **而没有任何门能发现**——门读的是记录，记录是自报的。
 *
 * 那是 §7.2.5 对 flags 做的诊断在**谓词**上的完整复制，而 §7.2.5 只覆盖了 flags 那一半。
 * 所以产品代码的第一件事不是业务逻辑，是**把这半边补上**。
 *
 * 本模块把 01-CONTRACTS §4 的 W-01..W-16 表编码成可执行的所有权判定，
 * 并给出 `denyProducerSubmission()` —— 提交工具的 `tools/pre-execute` 钩子调用它。
 * I-W1 的原话是「status 由门代码计算，从不由 agent 断言」；
 * 本模块让那句话有一个**载体**，而不是一句纪律。
 */

/** 写者角色（§4 的「谁写」列） */
export const WRITER = Object.freeze({
  FETCH_EXECUTOR: 'fetch-executor',   // 我们自建的检索/抓取工具执行器
  PRODUCER: 'producer',               // producer agent（经 claim 提交工具）
  GATE: 'gate',                       // 门代码（确定性脚本，dsh 进程之外）
  VERDICT_SUBAGENT: 'verdict-subagent', // Class-2 裁决 subagent
  REGISTRY_SYNC: 'registry-sync',     // 注册表同步器
  COMPOSER: 'composer',               // 确定性组稿器
  ORCHESTRATOR: 'orchestrator',       // 编排层
})

/**
 * 字段 → 唯一写者。键是 claim 记录里的**顶层字段名**。
 * 依据 01-CONTRACTS §4 W-03 / W-04 / W-14。
 */
export const FIELD_OWNER = Object.freeze({
  // ── W-03 · producer 写的：claim 的**内容** ──────────────────────────
  claim_id: WRITER.PRODUCER,
  kind: WRITER.PRODUCER,
  payload: WRITER.PRODUCER,
  // §9.2 载荷槽类型标注：entity / metric / sample / value / comparator。
  // 它是载荷 schema 的一部分（W-03 的内容），由 producer 声明；
  // G-CTR-SCAN 的 (a′) 锚槽覆盖下界与 EE-L-24 都依赖它。
  // 不标注则门只能靠字段名启发式推断槽类型 = 自由文本判据混进 GC-0 门。
  slot_types: WRITER.PRODUCER,
  metric_frame: WRITER.PRODUCER,
  // producer 提出，门逐字核（必须在锚句子句里、且不在任何兄弟读数里）。
  // 提出与核验分离，所以它归 producer——白名单在它第一次出现时拒绝了它，
  // 这正是白名单该有的行为：新字段默认不可写，直到有人写明它归谁。
  discriminator: WRITER.PRODUCER,
  evidence_refs: WRITER.PRODUCER,
  premises: WRITER.PRODUCER,
  tolerance: WRITER.PRODUCER,
  question_id: WRITER.PRODUCER,
  anchor_span_ref: WRITER.PRODUCER,
  // 〔R6 修复期新增〕producer 声明**素材**，门做**判定**——这三个字段是那条
  // 分界线的产物，加进来时必须逐一论证它们为什么不是自报通行证：
  //   question_hash   —— 「我回答的是哪个问题」。是内容。是否**冻结**由 G-FREEZE
  //                      拿它跟门自己写下的冻结记录比对得出，producer 改它只会判红。
  //   rerun_spec      —— 「跑哪个脚本、什么参数」。是内容。脚本本身在 CAS 里，
  //                      G-RERUN **自己执行两次**，producer 递不进来一个「已通过」。
  //   evidence_index  —— 「哪几条抓取支持这条 claim」。是内容。
  //                      它取代了此前的 `__evidence_index`——`__` 前缀正是 R6-01 的后门。
  question_hash: WRITER.PRODUCER,
  rerun_spec: WRITER.PRODUCER,
  evidence_index: WRITER.PRODUCER,

  // ── W-04 · 门代码写的：status 及**全部派生字段** ─────────────────────
  status: WRITER.GATE,
  evidence_grade: WRITER.GATE,
  independent_cluster_count: WRITER.GATE,
  nominal_source_count: WRITER.GATE,
  counter_evidence_searched: WRITER.GATE,
  counter_evidence_found: WRITER.GATE,
  computed_at: WRITER.GATE,
  gate_version: WRITER.GATE,
  inputs_hash: WRITER.GATE,
  mechanism_results: WRITER.GATE,
  retention_tier: WRITER.GATE,
  source_integrity: WRITER.GATE,
  quote_faithful: WRITER.GATE,
  has_verbatim_quote: WRITER.GATE,
  chart_extracted: WRITER.GATE,
  sub_mode: WRITER.GATE,

  // 〔R5 的头号缺口〕以下六个谓词此前**没有任何 deny 规则**。
  // 它们全部是 S 第 1 步的判定输入，决定 base，因此按 W-04 归门代码。
  // producer 声明其中任何一个 = 自己给自己发通行证。
  question_frozen: WRITER.GATE,
  rerun_gate_passed: WRITER.GATE,
  anchor_containment_passed: WRITER.GATE,
  polarity_scope_passed: WRITER.GATE,
  frame_gate_passed: WRITER.GATE,
  inference_gate_passed: WRITER.GATE,
  attribution_verdict: WRITER.GATE,

  // ── W-14 · flags 逐 flag 有 setter，但**没有一个 setter 是 producer** ──
  flags: WRITER.GATE,

  // ── W-13 · 编排层 ────────────────────────────────────────────────────
  budget_state: WRITER.ORCHESTRATOR,
})

/** producer 允许写的字段集合（提交工具 schema 的白名单） */
export const PRODUCER_WRITABLE = Object.freeze(
  Object.entries(FIELD_OWNER).filter(([, w]) => w === WRITER.PRODUCER).map(([k]) => k))

/**
 * 提交工具的 `tools/pre-execute` deny 判定。
 *
 * 返回 `null` 表示放行；返回字符串表示**拒绝**，字符串即拒绝理由。
 *
 * 设计要点：**白名单，不是黑名单**。黑名单会在加字段时静默失守——
 * 新增一个门写的字段而忘了加进黑名单，producer 就能写它。
 * 白名单的失守方向相反：忘了加就是 producer 写不了，红得响亮。
 */
export const SLOT_TYPES = Object.freeze(['entity', 'metric', 'sample', 'value', 'comparator'])

export function denyProducerSubmission(payload) {
  if (payload === null || typeof payload !== 'object' || Array.isArray(payload)) {
    return `提交载荷必须是对象，收到 ${Array.isArray(payload) ? 'array' : typeof payload}`
  }
  const allowed = new Set(PRODUCER_WRITABLE)
  // 槽类型取值域受控：producer 可以标注，但不能发明新类型——
  // 否则 (a′) 的「实体槽必须出现」可以靠把实体标成别的类型来绕过。
  if (payload.slot_types && typeof payload.slot_types === 'object') {
    const bad = Object.entries(payload.slot_types)
      .filter(([, v]) => !SLOT_TYPES.includes(v))
      .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
    if (bad.length) {
      return `slot_types 取值域外：${bad.join('、')}。受控取值：${SLOT_TYPES.join(' / ')}（§9.2）`
    }
  }
  // payload 的**槽名**不得与门字段同名。
  // 〔R6-03〕组稿视图此前是 `{...statusRecord, ...payload}`，payload 后展开 ⇒
  // 一个叫 `status` 的槽直接改写读者看到的状态标记：S 判 unverified，
  // 成稿印「已验证，来源 9/独立簇 9」，全程合法字段、零门触发。
  // `sealStatus` 已让门字段压过 payload，这里再堵一层：**想这么命名就该响**，
  // 而不是让攻击静默失败——静默失败的攻击下次会换个写法回来。
  if (payload.payload && typeof payload.payload === 'object') {
    const clash = Object.keys(payload.payload).filter(k => k in FIELD_OWNER && FIELD_OWNER[k] !== WRITER.PRODUCER)
    if (clash.length) {
      return `payload 槽名与门字段冲突：${clash.join('、')}。` +
        '同名槽在组稿视图里可改写读者看到的状态标记（R6-03）。'
    }
  }
  const offending = Object.keys(payload).filter(k => !allowed.has(k))
  if (!offending.length) return null

  const owned = offending.filter(k => k in FIELD_OWNER)
  const unknown = offending.filter(k => !(k in FIELD_OWNER))
  const parts = []
  if (owned.length) {
    parts.push(`以下字段的写者不是 producer：${owned.map(k => `${k}（${FIELD_OWNER[k]}）`).join('、')}`)
  }
  if (unknown.length) {
    // 未知字段一律拒——否则 producer 可以夹带一个门将来会读的名字。
    parts.push(`以下字段不在 §4 的写权表里：${unknown.join('、')}`)
  }
  return parts.join('；') +
    '。I-W1：status 由门代码计算，从不由 agent 断言。'
}

/**
 * 门代码写 status.json 时的自检：**只能写自己拥有的字段**。
 * 反向约束同样必要——门若写了 producer 拥有的字段，就是在替被检查方改答案。
 */
/**
 * `kind` 是唯一一个 **producer 可写、而 S 会读** 的字段，需要单独论证。
 *
 * 它必须由 producer 声明——只有他知道自己在断言什么（这是 claim 的**内容**，W-03）。
 * 使它不构成自报通行证的，是另一条性质：**每种 kind 的特权都由 producer
 * 控制不了的谓词把守**。下表是那条论证的可执行形式，由写者契约门逐条断言：
 *   声称 kind = K 的 claim，要拿到 K 的最高状态，必须先过 GATED_BY[K] 里的谓词，
 *   而那些谓词全部是 W-04 的门代码字段。
 *
 * 若将来有人给某个 kind 加一条不经门谓词的捷径，本表与门会一起判红。
 */
export const KIND_GATED_BY = Object.freeze({
  'K-D':   ['rerun_gate_passed', 'question_frozen'],          // 封闭式 + 重跑过才到 ST-V（§2.1）
  'K-L-T': ['anchor_containment_passed', 'polarity_scope_passed', 'frame_gate_passed'], // 两个合取项（§2.2.1）
  'K-L-A': ['attribution_verdict'],                            // 归因裁决（上限 ST-A）
  'K-I':   ['inference_gate_passed'],                          // 推断门（永不可达 ST-V，§2.3.1）
})

export function denyGateWrite(patch) {
  if (patch === null || typeof patch !== 'object') return '门写入必须是对象'
  const bad = Object.keys(patch).filter(k => FIELD_OWNER[k] && FIELD_OWNER[k] !== WRITER.GATE)
  if (!bad.length) return null
  return `门试图写它不拥有的字段：${bad.map(k => `${k}（属于 ${FIELD_OWNER[k]}）`).join('、')}`
}
