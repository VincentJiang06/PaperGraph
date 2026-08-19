/**
 * G-CLUSTER —— 独立簇归并（GC-0）。
 *
 * 〔它为什么是本项目最脆的一块〕R5 第 3 条预测：
 * > `independent_cluster_count` 在 S 里只是个被比大小的整数；产生它的 G-CLUSTER
 * > 零实现、零金标集、零假合并率。真实文献里独立簇被三条本项目自己记录过的机制
 * > 系统性压塌——F-02 转引链、F-23 跨语言链（一手样本：11 家中文媒体全部回溯到
 * > 同一条 Nikkei Asia）、F-22 自证回路——再叠预印本/会议/期刊三版同文。
 * > 认真归并 ⇒ K-L-A 与 K-I 拿不到 2 簇；不认真 ⇒ K=2 名存实亡。
 *
 * 本实现的立场：**认真归并，并让代价可见**。
 * `K ≥ 2` 是对「合成共识」的最低防线（§1.5.2），把它做松等于把防线拆了。
 * 因此这里宁可少算簇数，也不虚报独立性——而**少算的代价由 `nominal_source_count`
 * 与独立簇数并排展示**（§5.5 R-I6），让「11 家媒体其实是 1 个簇」这件事对读者可见。
 *
 * 归并分两档（§5A.3.5）：
 *   · `exact` —— 确定性同一（同 DOI / 同 arXiv id / 同规范化标题+作者）。**直接合并。**
 *   · `low`   —— 低置信身份候选（仅标题高度相似、或仅作者集合重合）。
 *                **只提议不执行**，进 `identity_merge_candidates[]` 交人审。
 *
 * 后者是刻意的：自动执行低置信合并会把「归并器假合并率」变成一个没人看得见的旋钮，
 * 而 §1.5.2 的「什么会推翻」一条正是「若假合并率高到使 K=2 事实上等价于 K=1」。
 */

export const CLUSTER_RULES_VERSION = 'g-cluster-2026-08-18'

const norm = s => String(s ?? '').toLowerCase()
  .normalize('NFKC').replace(/[^\p{L}\p{N}]+/gu, ' ').trim()

/** 规范化的作品身份键；返回 null 表示没有确定性身份 */
function exactKey(e) {
  if (e.doi) return 'doi:' + norm(e.doi)
  if (e.arxiv_id) return 'arxiv:' + norm(e.arxiv_id).replace(/v\d+$/, '')  // 版本无关
  if (e.work_id) return 'work:' + norm(e.work_id)
  return null
}

/** 标题 + 首作者 —— 用于识别预印本/会议/期刊三版同文 */
function titleAuthorKey(e) {
  const t = norm(e.title)
  const a = norm((e.authors ?? [])[0])
  return (t && a) ? `ta:${t}|${a}` : null
}

const jaccard = (a, b) => {
  const A = new Set(a), B = new Set(b)
  if (!A.size || !B.size) return 0
  let inter = 0
  for (const x of A) if (B.has(x)) inter++
  return inter / (A.size + B.size - inter)
}

/**
 * @param {object[]} refs 证据引用。可带 doi/arxiv_id/work_id/title/authors/
 *                        domain/lang/cites_source_id/self_cite_group
 * @returns {{independent_cluster_count, nominal_source_count, cluster_map,
 *            identity_merge_candidates, applied_rules, knownLimitation}}
 */
export function cluster(refs = []) {
  const items = refs.map((e, i) => ({ i, e, root: i }))
  const find = x => { while (items[x].root !== x) x = items[x].root = items[items[x].root].root; return x }
  const union = (a, b, rule, log) => {
    const ra = find(a), rb = find(b)
    if (ra === rb) return
    items[rb].root = ra
    log.push({ merged: [refs[a], refs[b]].map(r => r.evidence_id ?? r.work_id ?? r.title ?? '?'), rule, level: 'exact' })
  }
  const applied = []

  // ── ⓪ 内容同一：逐字节相同的快照必然是同一个来源 ──────────────────────
  // 〔R6-05〕「逐字节相同的快照可以算作 2 个独立簇」——同一份 body 用两个
  // work_id 抓两次即得 K=2，K-L-A / K-I 的最低防线直接失效，而 §5.5 的诚实
  // 展示机制此时在**主动误导**：它印「来源 2/独立簇 2」。
  //
  // 这条规则排在最前，且**不看任何自陈字段**：内容寻址的哈希是本项目里
  // 唯一一个 producer 无法伪造的身份——改一个字节，哈希就变，簇也就真的分开了。
  // 它同时是 SA-5 / R5 第 3 条预测的部分闭合：不自陈上游的转引，只要正文
  // 逐字节相同就会被归并。**只是部分**——改写过的转引仍然逃得掉，见文末 knownLimitation。
  const byContent = new Map()
  items.forEach(({ i, e }) => {
    const k = e.object_sha256
    if (!k) return
    if (byContent.has(k)) union(byContent.get(k), i, 'same-content-sha256', applied)
    else byContent.set(k, i)
  })

  // ── ⓪-b 近似同一：改写过的转载 ────────────────────────────────────────
  //
  // 〔SA-5 的第二步闭合〕⓪ 只抓**逐字节**相同。真实的转引链里，
  // 二手来源几乎总会改一两个词、换个标点、加个 "reportedly"——
  // 一个字节之差，哈希就分开，11 家转载又变成 11 个独立簇。
  //
  // 判据是 **5 字符 shingle 的 Jaccard 重合度**：确定性、离线、可复算，
  // 不需要任何自陈字段，producer 也伪造不了（要伪造就得真的把正文改得不像）。
  // 阈值 0.82 是**高**阈值：它抓的是「同一段话改了几个词」，
  // 不是「两篇讲同一件事的独立报道」——后者的重合度远在此之下。
  //
  // 这条与 ⓪ 的关键差别：它可能**错并**。所以它归并的对，
  // 在 applied_rules 里标 level:'near'，人审队列看得见是哪一条规则合的。
  const SHINGLE_K = 5
  const NEAR_DUP_THRESHOLD = 0.82
  const shinglesOf = t => {
    const n = String(t ?? '').toLowerCase().replace(/\s+/g, ' ').trim()
    if (n.length < SHINGLE_K) return new Set()
    const out = new Set()
    for (let i = 0; i + SHINGLE_K <= n.length; i++) out.add(n.slice(i, i + SHINGLE_K))
    return out
  }
  // 名字必须与文件里既有的 `jaccard`（按**数组**算）区分开。
  // 〔标定用例 C-9 抓到的〕初版就叫 jaccard，在 cluster() 作用域内遮蔽了外层那个，
  // 而外层那个被 ⑥ 低置信候选按数组调用（`.length`）——
  // 到我这里变成 `.size`，`undefined` 是 falsy，于是**低置信候选一条都生不出来**，
  // 人审队列静默清空。同名不同签名的遮蔽，是最不响的一类破坏。
  const jaccardSet = (a, b) => {
    if (!a.size || !b.size) return 0
    let inter = 0
    for (const x of a) if (b.has(x)) inter++
    return inter / (a.size + b.size - inter)
  }
  //
  // **数字守卫**：文本重合度再高，只要两边的数字不同，就不是同一段话。
  // 〔标定用例 C-N6 抓到的，也是这条规则最危险的假阳〕
  //   "We evaluate on the CASP14 benchmark using standard protocols."
  //   "We evaluate on the CASP15 benchmark using standard protocols."
  // 只差一个字符，Jaccard 接近 1，却是**两个不同的评测集**。
  // 而数字恰恰是本项目全部判定的核心对象——把两个数不同的句子并成一簇，
  // 等于亲手制造一次「合成共识」，正是这道门要防的东西。
  const digitsOf = t => String(t ?? '').match(/\d+(?:\.\d+)?/g)?.sort().join(',') ?? ''
  const raw = items.map(({ e }) => e.anchor_sentence ?? e.quote ?? '')
  const texts = raw.map(shinglesOf)
  const digits = raw.map(digitsOf)
  for (let a = 0; a < items.length; a++) {
    for (let b = a + 1; b < items.length; b++) {
      if (find(a) === find(b)) continue
      if (digits[a] !== digits[b]) continue          // 数字不同 ⇒ 不是同一段话
      const j = jaccardSet(texts[a], texts[b])
      if (j >= NEAR_DUP_THRESHOLD) {
        const before = applied.length
        union(a, b, `near-duplicate(jaccard=${j.toFixed(3)})`, applied)
        // 近似归并要与确定性归并区分开：它可能错并，人审队列据此排查
        if (applied.length > before) applied[applied.length - 1].level = 'near'
      }
    }
  }

  // ── ① 确定性同一：同 DOI / arXiv / work_id ────────────────────────────
  const byExact = new Map()
  items.forEach(({ i, e }) => {
    const k = exactKey(e)
    if (!k) return
    if (byExact.has(k)) union(byExact.get(k), i, 'exact-id', applied)
    else byExact.set(k, i)
  })

  // ── ② 预印本/会议/期刊三版同文：同标题 + 同首作者 ─────────────────────
  const byTA = new Map()
  items.forEach(({ i, e }) => {
    const k = titleAuthorKey(e)
    if (!k) return
    if (byTA.has(k)) union(byTA.get(k), i, 'same-title-first-author', applied)
    else byTA.set(k, i)
  })

  // ── ③ F-02 转引链：B 自陈其来源是 A ⇒ 同簇 ────────────────────────────
  const byId = new Map(refs.map((e, i) => [e.evidence_id ?? e.work_id, i]))
  items.forEach(({ i, e }) => {
    const src = e.cites_source_id
    if (src && byId.has(src)) union(byId.get(src), i, 'citation-chain(F-02)', applied)
  })

  // ── ④ F-23 跨语言链：同一上游的不同语种转载 ───────────────────────────
  //    一手样本：11 家中文媒体全部回溯到同一条 Nikkei Asia。
  //    判据是**自陈的上游**，不是语言本身——语言不同不代表不独立。
  const byUpstream = new Map()
  items.forEach(({ i, e }) => {
    const up = e.upstream_id
    if (!up) return
    if (byUpstream.has(up)) union(byUpstream.get(up), i, 'cross-language-chain(F-23)', applied)
    else byUpstream.set(up, i)
  })

  // ── ⑤ F-22 自证回路：同一作者组内部互引 ───────────────────────────────
  const bySelf = new Map()
  items.forEach(({ i, e }) => {
    const g = e.self_cite_group
    if (!g) return
    if (bySelf.has(g)) union(bySelf.get(g), i, 'self-citation-loop(F-22)', applied)
    else bySelf.set(g, i)
  })

  // ── ⑥ 低置信身份候选：**只提议不执行** ────────────────────────────────
  const candidates = []
  for (let a = 0; a < items.length; a++) {
    for (let b = a + 1; b < items.length; b++) {
      if (find(a) === find(b)) continue
      const ta = norm(refs[a].title).split(' ').filter(Boolean)
      const tb = norm(refs[b].title).split(' ').filter(Boolean)
      const j = jaccard(ta, tb)
      const sameAuthors = jaccard((refs[a].authors ?? []).map(norm), (refs[b].authors ?? []).map(norm))
      if (j >= 0.8 || sameAuthors >= 0.9) {
        candidates.push({
          pair: [refs[a].evidence_id ?? refs[a].title, refs[b].evidence_id ?? refs[b].title],
          title_jaccard: Number(j.toFixed(3)),
          author_overlap: Number(sameAuthors.toFixed(3)),
          level: 'low',
          note: '低置信身份候选：**未合并**，进人审队列。自动执行低置信合并会把归并器的假合并率变成没人看得见的旋钮（§1.5.2「什么会推翻」）',
        })
      }
    }
  }

  const roots = new Set(items.map((_, i) => find(i)))
  const clusterMap = {}
  items.forEach((_, i) => { (clusterMap[find(i)] ??= []).push(refs[i].evidence_id ?? refs[i].title ?? i) })

  return {
    independent_cluster_count: roots.size,
    nominal_source_count: refs.length,
    cluster_map: clusterMap,
    identity_merge_candidates: candidates,
    applied_rules: applied,
    rules_version: CLUSTER_RULES_VERSION,
    // 诚实边界：本实现只处理**自陈**的链路（cites_source_id / upstream_id / self_cite_group）。
    // 没有自陈时它看不见转引——而真实语料里自陈往往缺失。
    // 诚实边界（更新）：⓪ 抓逐字节相同、⓪-b 抓改写过的转载（shingle 重合 ≥0.82）。
    // 仍然抓不到的是**重写**的转引——二手来源用自己的话复述同一个数，
    // 文本重合度低于阈值。那需要的是语义比对，不是 GC-0 的量级。
    knownLimitation: refs.some(e => !e.cites_source_id && !e.upstream_id && !e.self_cite_group)
      ? '部分证据未自陈上游/转引/自证关系。本门可抓：同身份键、逐字节同文、改写过的转载（shingle 重合 ≥0.82）；'
        + '抓不到：用自己的话复述同一个数的重写型转引（需要语义比对，非 GC-0 量级）'
      : null,
  }
}
