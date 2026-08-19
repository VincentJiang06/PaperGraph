#!/usr/bin/env node
/**
 * 外部标定测试 —— 三个真实研究话题,真实文献,真实数字。
 *
 * 〔它为什么存在〕本项目此前所有标定集都是作者自己出的题(03 §5A.0 自认
 * `power_basis = unmeasured`)。这是第一份**不是我们出的题**:
 * 六份真实文献的逐字快照,payload 全部是文献里真实存在或真实被引用的数字。
 *
 * 三条线各压一个不同的子系统:
 *   T1 AlphaFold CASP14 精度 —— 引语属实性。全网把 `92.4` 归给 Nature 2021,
 *      而该数字在 Nature 全文里 **0 次命中**;它出自 Proteins 2021 那篇。
 *   T2 心理学可复现率      —— metric_frame。同一篇 OSC 2015 给了 36%/47%/39%/68%
 *      四个都合法的"复现率",取哪一个取决于判据。
 *   T3 新药研发成本        —— 合成共识 + 反证。DiMasi 2016 自己给了三个数
 *      ($1395M/$2558M/$2870M),世上引用的是中间那个并四舍五入成 "$2.6 billion";
 *      Prasad 2017 与 Wouters 2020 是真实的反向估计。
 *
 * 引语与锚句**从快照里程序化切出**,不手打——手打的"逐字引语"是我们自己
 * 造的假证据,这条在 S3 已经栽过一次。
 */
import { readFileSync, mkdtempSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const ROOT = join(HERE, '../..')
const { runOnce } = await import(join(ROOT, 'src/run.mjs'))

const snap = f => readFileSync(join(HERE, 'snapshots', f), 'utf8').trim()

/** 从快照里切出**包含给定子串**的那一句(逐字,不加工) */
function sentenceWith(text, needle) {
  const i = text.indexOf(needle)
  if (i < 0) throw new Error(`快照里没有 ${JSON.stringify(needle)} —— 夹具坏了`)
  // 句末:句点/分号后跟空格+大写,或文本末尾。小数点不算句末。
  // 中文句号/分号也是句末。〔T4-6 抓到的夹具 bug〕不认 `。` 时两句被当成一句，
  // 前一句的否定打中了后一句的载荷 —— 那是**夹具**造出来的假阳，不是门的。
  // 〔自纠〕初版还加了一句 `!/\d/.test(text[k+2])`，本意是躲小数点，
  // 但小数点的判据是「前后都是数字」，而这里已经要求后面是空白——
  // 那个多余的守卫反而让 `results; 47%` 里的分号不算句末（k+2 是 '4'），
  // 锚句一口气吞掉三个并列子句，T2-2 与 T3-6 因此回归。
  // 守卫写在错的位置，比没有守卫更难查。
  const isEnd = k => {
    const c = text[k]
    if (/[。；]/.test(c)) return true
    if (!/[.;]/.test(c)) return false
    return k + 1 >= text.length || /\s/.test(text[k + 1])
  }
  let end = i + needle.length
  while (end < text.length) { if (isEnd(end)) { end++; break } end++ }
  let start = i
  while (start > 0) { if (isEnd(start - 1)) break; start-- }
  return text.slice(start, end).trim()
}

const SRC = {
  nature:   { file: 'T1a-nature-alphafold.txt', work_id: 'doi:10.1038/s41586-021-03819-2',
              url: 'https://www.nature.com/articles/s41586-021-03819-2', doi: '10.1038/s41586-021-03819-2',
              title: 'Highly accurate protein structure prediction with AlphaFold',
              authors: ['Jumper J'], locator: 'p1:results', content_kind: 'fulltext' },
  proteins: { file: 'T1b-proteins-casp14.txt', work_id: 'doi:10.1002/prot.26257',
              url: 'https://onlinelibrary.wiley.com/doi/10.1002/prot.26257', doi: '10.1002/prot.26257',
              title: 'Applying and improving AlphaFold at CASP14',
              authors: ['Jumper J'], locator: 'abstract', content_kind: 'abstract' },
  osc:      { file: 'T2-osc2015.txt', work_id: 'doi:10.1126/science.aac4716',
              url: 'https://www.science.org/doi/10.1126/science.aac4716', doi: '10.1126/science.aac4716',
              title: 'Estimating the reproducibility of psychological science',
              authors: ['Open Science Collaboration'], locator: 'abstract', content_kind: 'abstract' },
  dimasi:   { file: 'T3a-dimasi2016.txt', work_id: 'doi:10.1016/j.jhealeco.2016.01.012',
              url: 'https://doi.org/10.1016/j.jhealeco.2016.01.012', doi: '10.1016/j.jhealeco.2016.01.012',
              title: 'Innovation in the pharmaceutical industry: New estimates of R&D costs',
              authors: ['DiMasi JA'], locator: 'abstract', content_kind: 'abstract' },
  prasad:   { file: 'T3b-prasad2017.txt', work_id: 'doi:10.1001/jamainternmed.2017.3601',
              url: 'https://doi.org/10.1001/jamainternmed.2017.3601', doi: '10.1001/jamainternmed.2017.3601',
              title: 'R&D Spending to Bring a Single Cancer Drug to Market',
              authors: ['Prasad V'], locator: 'abstract', content_kind: 'abstract' },
  // ── T4 · 真实中文文献（本项目第一次在中文语料上跑整条链路） ──────────
  cnNema:   { file: 'T4a-cn-nematode.txt', work_id: 'pmid:386886',
              url: 'https://europepmc.org/article/CBA/386886', doi: undefined,
              title: '生防制剂与呋喃丹颗粒剂防治根结线虫幼虫的效果',
              authors: ['佚名'], locator: 'abstract', content_kind: 'abstract' },
  cnRice:   { file: 'T4b-cn-rice.txt', work_id: 'pmid:382278',
              url: 'https://europepmc.org/article/CBA/382278', doi: undefined,
              title: '水稻叶片上下表面反射率差异及其与氮素状况的关系',
              authors: ['佚名'], locator: 'abstract', content_kind: 'abstract' },
  cnJuncus: { file: 'T4c-cn-juncus.txt', work_id: 'pmid:391824',
              url: 'https://europepmc.org/article/CBA/391824', doi: undefined,
              title: '种植密度、母本大小和移栽期对蔺草生长、开花及产量的影响',
              authors: ['佚名'], locator: 'abstract', content_kind: 'abstract' },
  wouters:  { file: 'T3c-wouters2020.txt', work_id: 'doi:10.1001/jama.2020.1166',
              url: 'https://doi.org/10.1001/jama.2020.1166', doi: '10.1001/jama.2020.1166',
              title: 'Estimated R&D Investment Needed to Bring a New Medicine to Market',
              authors: ['Wouters OJ'], locator: 'abstract', content_kind: 'abstract' },
}
for (const k of Object.keys(SRC)) SRC[k].body = snap(SRC[k].file)

/** 造一次抓取。quote/anchorSentence 一律从快照里切,不手打。 */
function fetchOf(key, needle, opts = {}) {
  const s = SRC[key]
  const sent = sentenceWith(s.body, needle)
  return {
    url: s.url, body: s.body, httpStatus: 200,
    retrievedAt: '2026-08-19T00:00:00Z', extractorVersion: 'pymupdf-1.28.2',
    work_id: opts.work_id ?? s.work_id, version_id: 'v1', locator: s.locator,
    doi: opts.doi === null ? undefined : (opts.doi ?? s.doi),
    title: s.title, authors: s.authors,
    quote: sent, anchorSentence: sent,
    // 等级不再由夹具声明——由 G-GRADE 从 content_kind + locator 算出来（E-1 修复后）
    content_kind: s.content_kind, retention_tier: 'A',
    ...opts.extra,
  }
}
export { SRC, sentenceWith, fetchOf, runOnce, ROOT }
