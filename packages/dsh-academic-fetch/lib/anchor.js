/**
 * 证据锚点的构造 —— 本文件**不 import 任何 @deepseek-ai/\* 包**，因此可被单测覆盖。
 *
 * 〔为什么取证工具必须是我们自己的进程内工具〕02-ARCHITECTURE §A 第 1 条：
 * 证据锚点的唯一零风险落点是 `tool/result.data.meta`，而 `meta` 的值来自
 * **工具执行器的返回值**——第三方工具的 `meta` 不受我们控制。
 * 所以这个包存在的全部理由，就是让 `data.meta.evidence` 由我们写。
 *
 * 锚点字段（W-02）：object_sha256 / url / retrieved_at / http_status / bytes / extractor_version
 * 六个字段都是**门下游要用的**，缺一个就有一类判定做不了：
 *   · object_sha256    → source_integrity 的比对基准
 *   · url + retrieved_at → 可复核寻址（G5 的前提）
 *   · http_status      → 200 之外的响应不得当作快照
 *   · bytes            → 截断/空响应的即时判据
 *   · extractor_version → 证据卡 id 的第五分量（M0-1：换抽取器结果会变）
 */
import { createHash } from 'node:crypto'

export const ANCHOR_FIELDS = Object.freeze([
  'object_sha256', 'url', 'retrieved_at', 'http_status', 'bytes', 'extractor_version',
])

export const sha256 = buf =>
  createHash('sha256').update(typeof buf === 'string' ? Buffer.from(buf, 'utf8') : buf).digest('hex')

/**
 * 由一次抓取的结果构造锚点。**任何一个字段缺失或不合法都抛**——
 * 一个字段不全的锚点比没有锚点更坏：它看起来可复核。
 */
export function buildAnchor({ url, body, httpStatus, retrievedAt, extractorVersion }) {
  const problems = []
  if (!url || !/^https?:\/\//i.test(String(url))) problems.push('url 必须是 http(s) 绝对地址')
  if (body === undefined || body === null) problems.push('body 缺失')
  if (!Number.isInteger(httpStatus)) problems.push('http_status 必须是整数')
  if (httpStatus !== 200) problems.push(`http_status=${httpStatus}：非 200 响应不得当作快照`)
  if (!retrievedAt || Number.isNaN(Date.parse(retrievedAt))) problems.push('retrieved_at 必须是可解析的时间戳')
  if (!extractorVersion) problems.push('extractor_version 缺失（证据卡 id 的第五分量）')
  const buf = Buffer.isBuffer(body) ? body : Buffer.from(String(body ?? ''), 'utf8')
  if (buf.length === 0) problems.push('bytes=0：空响应不是快照')
  if (problems.length) throw new Error(`证据锚点不合法：${problems.join('；')}`)

  return {
    object_sha256: sha256(buf),
    url: String(url),
    retrieved_at: new Date(retrievedAt).toISOString(),
    http_status: httpStatus,
    bytes: buf.length,
    extractor_version: String(extractorVersion),
  }
}

/** 锚点完整性校验：下游门在读 meta 之前先过这一关 */
export function validateAnchor(anchor) {
  if (!anchor || typeof anchor !== 'object') return '锚点不是对象'
  const missing = ANCHOR_FIELDS.filter(f => anchor[f] === undefined || anchor[f] === null || anchor[f] === '')
  if (missing.length) return `锚点缺字段：${missing.join('、')}`
  if (!/^[0-9a-f]{64}$/.test(String(anchor.object_sha256))) return 'object_sha256 不是 64 位十六进制'
  if (anchor.http_status !== 200) return `http_status=${anchor.http_status}：非 200 不得当作快照`
  if (!(anchor.bytes > 0)) return 'bytes 必须 > 0'
  return null
}
