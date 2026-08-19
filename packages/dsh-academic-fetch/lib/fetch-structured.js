/**
 * 结构化抓取器 —— 把 §3.3 的 G5 从「够不着」变成「可达」。
 *
 * 两条真实来源，都在真文档上验过（见 gates/check_structured_fetch.mjs）：
 *   Europe PMC   `/{PMCID}/fullTextXML`        → JATS → `jats:Sec2/Par7`
 *   arXiv LaTeXML `arxiv.org/html/{id}v{n}`    → HTML → `html:#S3.SS1.p2`
 *
 * 〔为什么 http 是注入的〕本文件不 import 任何网络库。
 * 抓取动作由调用方（DSH 工具层）提供，本模块只做**解析 + 定位 + 回指验证**。
 * 这样三件事同时成立：
 *   ① 门可以在离线夹具上跑（GC-0 要求确定性、零网络）
 *   ② 真实链路上用真实 HTTP
 *   ③ 「抓到了什么」与「怎么抓的」分开，前者可复核，后者可替换
 */
import { createHash } from 'node:crypto'
import { passagesFromJats, passagesFromArxivHtml, verifyRoundTrip } from './structured.js'

const sha256 = async s => createHash('sha256').update(String(s), 'utf8').digest('hex')

export const FETCH_VERSION = 'structured-fetch-2026-08-19'

export const SOURCES = Object.freeze({
  europepmc: {
    kind: 'jats',
    url: id => `https://www.ebi.ac.uk/europepmc/webservices/rest/${id}/fullTextXML`,
    parse: passagesFromJats,
    idPattern: /^PMC\d+$/,
  },
  arxiv: {
    kind: 'html',
    url: id => `https://arxiv.org/html/${id}`,
    parse: passagesFromArxivHtml,
    idPattern: /^\d{4}\.\d{4,5}(v\d+)?$/,
  },
})

/**
 * 抓一篇的结构化全文，返回**逐段**的证据候选。
 *
 * @param {object} o
 * @param {'europepmc'|'arxiv'} o.source
 * @param {string} o.id            PMCID 或 arXiv id
 * @param {(url:string)=>Promise<{status:number, body:string}>} o.http  由调用方注入
 * @returns {Promise<{work_id, version_id, url, retrievedAt, extractorVersion,
 *                    content_kind, body, passages:{locator,text,secTitle}[],
 *                    addressable:number, unaddressable:number}>}
 */
export async function fetchStructured({ source, id, http, now }) {
  const src = SOURCES[source]
  if (!src) throw new Error(`未知来源 ${source}；支持：${Object.keys(SOURCES).join(' / ')}`)
  if (!src.idPattern.test(id)) throw new Error(`${source} 的 id 形态不对：${JSON.stringify(id)}`)

  const url = src.url(id)
  const res = await http(url)
  // 非 200 当场拒 —— 与 anchor.js 同一条纪律：抓不到就是抓不到，不留半份工件
  if (res.status !== 200) throw new Error(`抓取失败 ${url} → HTTP ${res.status}`)
  const body = String(res.body ?? '')
  if (!body.trim()) throw new Error(`抓取失败 ${url} → 空响应`)

  const all = src.parse(body)
  const passages = all.filter(p => p.locator)

  // 快照正文 = **结构化文档的确定性纯文本渲染**，不是原始标记。
  // 〔为什么〕引语是从段落文本里取的，而下游每一道门（包含/极性/框架/组稿）
  // 比对的都是纯文本。若把原始 XML 当 body，`body.includes(quote)` 恒不成立，
  // G-GRADE 会把一份完美的 JATS 判成 G1（「快照不含 claim 所需段落」）——
  // 实测踩过一次，正是这条。
  // 渲染是确定性的（段落顺序即文档顺序，用 \n\n 连接），因此可复算、可对哈希；
  // 原始标记的哈希单独记在 raw_sha256 里，供审计追到字节。
  const rendered = all.map(p => p.text).join('\n\n')
  return {
    work_id: source === 'europepmc' ? `pmcid:${id}` : `arxiv:${id}`,
    version_id: id.match(/v(\d+)$/)?.[0] ?? 'v1',
    url, retrievedAt: now ?? new Date().toISOString(),
    extractorVersion: FETCH_VERSION,
    content_kind: 'fulltext',
    source_kind: src.kind,
    body: rendered,
    raw: body,
    raw_sha256: await sha256(body),
    passages,
    addressable: passages.length,
    // **不可寻址的段落数必须一并返回**：G5 是逐段的，
    // 一份 JATS 文档里有相当一部分 <p> 不带 id，取自那些段落的引语够不上 G5。
    // 只报「拿到了全文」而不报这个数，会让读者以为整篇都可复核。
    unaddressable: all.length - passages.length,
  }
}

/**
 * 从抓取结果里造一条**证据记录**（喂给管线的那种形态）。
 * 回指往返在这里当场验，验不过就不给 `roundtrip_verified`——
 * 于是 G-GRADE 只会给 G4。**不抛异常**：G4 也是合法证据，只是天花板低一档。
 */
export function evidenceFrom(doc, quote, opts = {}) {
  const hit = doc.passages.find(p => {
    const n = s => String(s).normalize('NFKC').replace(/\s+/g, ' ').trim()
    return n(p.text).includes(n(quote))
  })
  const locator = hit?.locator ?? null
  // 回指验证用**原始标记**（锚点长在标记里），下游比对用纯文本 body。
  const rt = locator ? verifyRoundTrip(doc.raw, locator, quote, doc.source_kind)
                     : { ok: false, why: '引语不在任何可寻址段落里' }
  return {
    url: doc.url, body: doc.body, raw_sha256: doc.raw_sha256, httpStatus: 200,
    retrievedAt: doc.retrievedAt, extractorVersion: doc.extractorVersion,
    work_id: doc.work_id, version_id: doc.version_id,
    locator: locator ?? 'unaddressable',
    content_kind: doc.content_kind,
    quote, anchorSentence: opts.anchorSentence ?? quote,
    retention_tier: opts.retention_tier ?? 'A',
    ...(rt.ok ? { roundtrip_verified: true } : { roundtrip_note: rt.why }),
    ...opts.extra,
  }
}
