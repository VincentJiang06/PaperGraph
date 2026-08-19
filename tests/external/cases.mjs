#!/usr/bin/env node
/**
 * 12 条 claim,全部取自这三个话题上**真实存在的引用行为**。
 * 每条附「正式发表的论文/综述实际怎么写」,用于最后的差距对照。
 */
import { mkdtempSync, rmSync, readFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { SRC, sentenceWith, fetchOf, runOnce } from './run.mjs'

const pad = (s, n) => String(s).padEnd(n)
const results = []

function run(id, { topic, desc, realWorld, fetches, claim, skeleton, counterSearch, expectNote }) {
  const root = mkdtempSync(join(tmpdir(), 'ext-'))
  let out
  try {
    const cs = counterSearch === 'AUTO' ? autoQuery(claim) : counterSearch
    const env = {
      question: '这个数字站得住吗?', frozen_at: '2026-08-18T00:00:00Z',
      ...(cs ? { counterSearches: { [claim.claim_id]: cs } } : {}),
    }
    const r = runOnce(root, 'r1', fetches, [claim], skeleton, env)
    const st = JSON.parse(readFileSync(join(root, 'claims', `${claim.claim_id}.status.json`), 'utf8'))
    out = { status: st.status, trace: st.trace.join('→'), prose: r.prose.trim(),
            k: st.independent_cluster_count, n: st.nominal_source_count }
  } catch (e) {
    out = { status: 'REJECTED', trace: e.message.slice(0, 90), prose: '(无成稿)', k: 0, n: 0 }
  } finally { rmSync(root, { recursive: true, force: true }) }
  results.push({ id, topic, desc, realWorld, expectNote, ...out })
}

/**
 * 由 claim **自己的槽**拼出反证 query —— 真实编排层会这么自动生成。
 *
 * 〔为什么不用自然语言〕本测试的第一轮用的是人会写的那种 query
 * (`drug development cost refute`),X-2 判红 2/3:(a′) 要求锚槽字面出现在
 * query 里,而中文 metric 名不会出现在英文 query 中;(b′) 又把 `drug`
 * `development` `cost` 这些普通领域词判成越界 token。
 * 那一轮的数字保留在报告里——它本身就是结果。
 */
const autoQuery = (claim, op = '反驳') => {
  const slots = [...Object.values(claim.metric_frame ?? {}), ...Object.values(claim.payload ?? {})]
  return { query: [...new Set(slots)].join(' ') + ' ' + op, result_keys: [] }
}
const CTR = q => ({ query: q, result_keys: [] })

/**
 * 首轮那批**人会写的**自然语言 query。X-2 当时判红 2/3。
 * E1 修复后重跑，看还剩几条 —— 这是本轮唯一一个「可用性」侧的度量。
 */
export const NATURAL = {
  T1: 'AlphaFold CASP14 GDT_TS refute',
  T2: 'psychology replication rate refute',
  T3: 'drug development cost refute',
}
// discriminator：逐字取自锚句、且不出现在任何兄弟读数里的片段。
// 原文在同一处并列给了多个同量纲读数时，G-FRAME 要求 claim 声明它取的是哪一个。
const base = (id, payload, slot_types, metric_frame, discriminator) => ({
  claim_id: id, kind: 'K-L-T', payload, slot_types, metric_frame, evidence_index: [0],
  ...(discriminator ? { discriminator } : {}),
})

// ── T1 · AlphaFold CASP14 精度 ────────────────────────────────────────
run('T1-1', {
  topic: 'T1', desc: '把 92.4 归给 Nature 2021(全网最常见的写法)',
  realWorld: '大量综述与新闻写「median GDT_TS 92.4 (Jumper et al., Nature 2021)」;该数字在 Nature 全文 0 次命中',
  fetches: [fetchOf('nature', '0.96')],
  claim: base('c1', { system: 'AlphaFold', value: '92.4' },
              { system: 'entity', value: 'value' }, { metric: 'GDT_TS', sample_or_tier: 'CASP14' }),
  skeleton: 'AlphaFold 在 CASP14 的中位 GDT_TS 为 {{claim:c1.value}}。',
  counterSearch: 'AUTO',
})
run('T1-2', {
  topic: 'T1', desc: '同一个 92.4,归给真正的出处 Proteins 2021',
  realWorld: '正确引用;CASP14 论文摘要逐字含该数',
  fetches: [fetchOf('proteins', '92.4')],
  claim: base('c1', { system: 'AlphaFold', value: '92.4' },
              { system: 'entity', value: 'value' }, { metric: 'GDT_TS', sample_or_tier: 'CASP14' }),
  skeleton: 'AlphaFold 在 CASP14 的中位 GDT_TS 为 {{claim:c1.value}}。',
  counterSearch: 'AUTO',
})
run('T1-3', {
  topic: 'T1', desc: 'Nature 自己的精度陈述 0.96 Å',
  realWorld: 'Nature 正文原话,承重结论',
  fetches: [fetchOf('nature', '0.96')],
  claim: base('c1', { system: 'AlphaFold', value: '0.96' },
              { system: 'entity', value: 'value' }, { metric: 'backbone r.m.s.d.95', sample_or_tier: 'CASP14' }),
  skeleton: 'AlphaFold 的中位主链精度为 {{claim:c1.value}} Å。',
  counterSearch: 'AUTO',
})

// ── T2 · 心理学可复现率 ───────────────────────────────────────────────
run('T2-1', {
  topic: 'T2', desc: '36%,判据 = 统计显著',
  realWorld: 'OSC 2015 原文四个数之一,最常被引',
  fetches: [fetchOf('osc', 'Thirty-six')],
  claim: base('c1', { finding: 'replication', value: '36' },
              { finding: 'entity', value: 'value' },
              { metric: '复现率(判据:统计显著)', sample_or_tier: '100 项心理学研究' },
              'statistically significant results'),
  skeleton: '在统计显著判据下,复现率为 {{claim:c1.value}}%。',
  counterSearch: 'AUTO',
})
run('T2-2', {
  topic: 'T2', desc: '39%,判据 = 主观评定',
  realWorld: '同一篇论文的另一个合法数字',
  fetches: [fetchOf('osc', '39%')],
  claim: base('c1', { finding: 'replication', value: '39%' },
              { finding: 'entity', value: 'value' },
              { metric: '复现率(判据:主观评定)', sample_or_tier: '100 项心理学研究' },
              'subjectively rated'),
  skeleton: '在主观评定判据下,复现率为 {{claim:c1.value}}。',
  counterSearch: 'AUTO',
})
run('T2-3', {
  topic: 'T2', desc: '声称 36%,但锚句取的是 47% 那一句',
  realWorld: '张冠李戴:判据与数字错配,人工审稿极难发现',
  fetches: [fetchOf('osc', '47%')],
  claim: base('c1', { finding: 'replication', value: '36%' },
              { finding: 'entity', value: 'value' },
              { metric: '复现率', sample_or_tier: '100 项心理学研究' }),
  skeleton: '复现率为 {{claim:c1.value}}。',
  counterSearch: 'AUTO',
})
run('T2-4', {
  topic: 'T2', desc: '逐字属实,但框成「只有 36% 的心理学研究可复现」',
  realWorld: '媒体与部分综述的标准写法。转录无误,框架把四个判据塌成一个',
  fetches: [fetchOf('osc', 'Thirty-six')],
  claim: base('c1', { finding: 'replication', value: '36' },
              { finding: 'entity', value: 'value' },
              { metric: '复现率', sample_or_tier: '100 项心理学研究' }),
  skeleton: '只有 {{claim:c1.value}}% 的心理学研究可以被复现。',
  counterSearch: 'AUTO',
  expectNote: '本项目**抓不到**:我们验转录,不验框架',
})

// ── T3 · 新药研发成本 ─────────────────────────────────────────────────
run('T3-1', {
  topic: 'T3', desc: '$2.6 billion 归给 DiMasi 2016',
  realWorld: '全世界通行写法。原文写的是 $2558 million,「2.6」不在原文里',
  fetches: [fetchOf('dimasi', '$2558 million')],
  claim: base('c1', { cost: '2.6', unit: 'billion USD' },
              { cost: 'value', unit: 'metric' }, { metric: '研发成本', sample_or_tier: '106 种新药' }),
  skeleton: '研发一款新药的成本为 {{claim:c1.cost}} 十亿美元。',
  counterSearch: 'AUTO',
})
run('T3-2', {
  topic: 'T3', desc: '$2558 million 逐字引用 DiMasi 2016',
  realWorld: '严谨写法',
  fetches: [fetchOf('dimasi', '$2558 million')],
  claim: base('c1', { cost: '$2558 million' }, { cost: 'value' },
              { metric: '资本化上市前研发成本', sample_or_tier: '106 种新药' }),
  skeleton: '资本化的上市前研发成本为 {{claim:c1.cost}}。',
  counterSearch: 'AUTO',
})
run('T3-3', {
  topic: 'T3', desc: '同一个数,三份"独立"来源(DiMasi + Prasad 提及 + Wouters 提及)',
  realWorld: '综述常见:引三篇看似独立的文献支持同一个数,而后两篇是在**转述并质疑**它',
  fetches: [fetchOf('dimasi', '$2558 million'), fetchOf('prasad', '$2.7 billion'), fetchOf('wouters', '$2.8 billion')],
  claim: { claim_id: 'c1', kind: 'K-L-A', payload: { cost: '$2558 million' },
           slot_types: { cost: 'value' }, metric_frame: { metric: '研发成本', sample_or_tier: '新药' },
           evidence_index: [0, 1, 2] },
  skeleton: '研发成本为 {{claim:c1.cost}}。',
  counterSearch: 'AUTO',
})
run('T3-4', {
  topic: 'T3', desc: 'Prasad 的那句提及,单独拿来当支持证据',
  realWorld: '「$2.7 billion」出现在一篇**反驳它**的论文里,否定在下一句',
  fetches: [fetchOf('prasad', '$2.7 billion')],
  claim: base('c1', { cost: '$2.7 billion' }, { cost: 'value' },
              { metric: '研发成本', sample_or_tier: '新药' }),
  skeleton: '研发成本为 {{claim:c1.cost}}。',
  counterSearch: 'AUTO',
  expectNote: '跨句否定 —— 03 §11.15 已认账的结构性假阴',
})
run('T3-5', {
  topic: 'T3', desc: 'Prasad 自己的结论 $648.0 million',
  realWorld: '真实的反向估计,同一问题差 4 倍',
  fetches: [fetchOf('prasad', '$648.0 million, a figure')],
  claim: base('c1', { cost: '$648.0 million' }, { cost: 'value' },
              { metric: '研发成本(肿瘤药)', sample_or_tier: '10 种药' }),
  skeleton: '研发成本为 {{claim:c1.cost}}。',
  counterSearch: 'AUTO',
})
run('T3-6', {
  topic: 'T3', desc: 'Wouters 的中位估计 $985.3 million',
  realWorld: '第三个独立估计',
  fetches: [fetchOf('wouters', '$985.3 million')],
  // 〔G-FRAME 抓到了我没注意到的东西〕Wouters 那句同时给了**中位数** $985.3M
  // 与**均值** $1335.9M —— 两个同量纲读数。我写这条用例时只看见了中位数，
  // 是门告诉我这句需要 discriminator 的。这是它第一次在**我没为它设计的用例**上触发。
  claim: base('c1', { cost: '$985.3 million' }, { cost: 'value' },
              { metric: '资本化研发投入(中位)', sample_or_tier: '63 种新药' }, 'median'),
  skeleton: '研发投入中位数为 {{claim:c1.cost}}。',
  counterSearch: 'AUTO',
})

// ── T4 · 真实中文文献 ────────────────────────────────────────────────
// 本项目第一次在真实中文语料上跑整条链路。此前 CJK 归一化、中文否定表、
// 中文数字处理**只在作者自己造的句子上验过**——那正是 SA-3 那条循环性。
run('T4-1', {
  topic: 'T4', desc: '全角数字 73．55％（全角句点+全角百分号）',
  realWorld: '中文期刊排版常用全角。作者转录成半角 73.55% 是标准做法',
  fetches: [fetchOf('cnNema', '73．55％')],
  claim: base('c1', { rate: '73.55%' }, { rate: 'value' },
              { metric: '杀虫率', sample_or_tier: '滤液浓100%下72h' }, '73．55％'),
  skeleton: '杀虫率为 {{claim:c1.rate}}。',
  counterSearch: 'AUTO',
  expectNote: '半角载荷 vs 全角原文 —— 靠 NFKC 归一化',
})
run('T4-2', {
  topic: 'T4', desc: '同句里两个并列读数（73．55％ 与 78．45％）',
  realWorld: '两种制剂各一个杀虫率，写「杀虫率为 73.55%」不说是哪一种',
  fetches: [fetchOf('cnNema', '73．55％')],
  claim: base('c1', { rate: '73.55%' }, { rate: 'value' },
              { metric: '杀虫率', sample_or_tier: '滤液浓100%下72h' }),
  skeleton: '杀虫率为 {{claim:c1.rate}}。',
  counterSearch: 'AUTO',
  expectNote: 'G-FRAME 在中文上该触发',
})
run('T4-3', {
  topic: 'T4', desc: '中文空结果「无显著相关性」',
  realWorld: '把一个空结果当成支持性证据',
  fetches: [fetchOf('cnRice', '无显著相关性')],
  claim: base('c1', { relation: '相关性', target: '供氮水平' },
              { relation: 'entity', target: 'entity' },
              { metric: '反射率差值与氮素的关系', sample_or_tier: '水稻叶片' }),
  skeleton: '反射率差值与供氮水平的 {{claim:c1.relation}} 已被报告。',
  counterSearch: 'AUTO',
})
run('T4-4', {
  topic: 'T4', desc: '中文上界限定「小于2%」',
  realWorld: '原文写「绝对差值一般小于2%」，转录成「差值为 2%」',
  fetches: [fetchOf('cnRice', '小于2%')],
  claim: base('c1', { diff: '2%' }, { diff: 'value' },
              { metric: '上下表面反射率绝对差值', sample_or_tier: '水稻叶片' }),
  skeleton: '上下表面反射率绝对差值为 {{claim:c1.diff}}。',
  counterSearch: 'AUTO',
})
run('T4-5', {
  topic: 'T4', desc: '中文子句边界：「但」前后一正一负',
  realWorld: '取「但」之后被否定的那半句当支持证据',
  fetches: [fetchOf('cnJuncus', '没有显著影响')],
  claim: base('c1', { effect: 'SPH' }, { effect: 'entity' },
              { metric: '移栽期对 SPH 的影响', sample_or_tier: '蔺草' }),
  skeleton: '移栽期对 {{claim:c1.effect}} 有影响。',
  counterSearch: 'AUTO',
})
run('T4-6', {
  topic: 'T4', desc: '同句「但」之前的肯定发现（不得误伤）',
  realWorld: '「随着移栽的推迟，SFP显著增强」是真实的肯定结论',
  fetches: [fetchOf('cnJuncus', 'SFP显著增强')],
  claim: base('c1', { effect: 'SFP' }, { effect: 'entity' },
              { metric: '移栽推迟对 SFP 的影响', sample_or_tier: '蔺草' }),
  skeleton: '移栽推迟使 {{claim:c1.effect}} 增强。',
  counterSearch: 'AUTO',
  expectNote: '★ 假阳侧：中文否定不得越过「但」打中前半句',
})

// ── 报告 ──────────────────────────────────────────────────────────────
// 条数由 results 算出来。手写的自述数字会腐——本文件初稿写「12 条」而实际 13 条，
// 正是本项目一直在抓的那一类，作者在自己的测试报告里又犯了一次。
console.log(`外部标定测试 — 三个真实话题 / ${new Set(results.map(r => r.topic)).size} 组语料 / ${results.length} 条 claim\n`)
console.log(`${pad('用例', 7)}${pad('状态', 12)}${pad('簇', 6)}说明`)
console.log('─'.repeat(100))
let topic = null
for (const r of results) {
  if (r.topic !== topic) { topic = r.topic; console.log() }
  console.log(`${pad(r.id, 7)}${pad(r.status, 12)}${pad(`${r.n}/${r.k}`, 6)}${r.desc}`)
  console.log(`${' '.repeat(25)}成稿: ${r.prose}`)
  if (r.expectNote) console.log(`${' '.repeat(25)}⚠  ${r.expectNote}`)
}
console.log()
const byStatus = results.reduce((a, r) => (a[r.status] = (a[r.status] ?? 0) + 1, a), {})
console.log('状态分布:', JSON.stringify(byStatus))
export { results }
