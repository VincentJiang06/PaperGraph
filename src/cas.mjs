/**
 * CAS（内容寻址存储）与证据卡 —— W-01 / W-06。
 *
 * 〔为什么证据卡的 id 是那样算的〕01-CONTRACTS §4 W-06：
 *   evidence_id = sha256(work_id ‖ version_id ‖ locator ‖ normalize(quote) ‖ extractor_version)
 * 五个分量各有理由，缺一个就有一类东西会被误当成同一条证据：
 *   · work_id       —— 不同作品
 *   · version_id    —— 预印本 v1 与 v3 的同一句话，页码/行号可能不同
 *   · locator       —— 同一版本内的不同位置
 *   · normalize(quote) —— 引语本身（归一化后，§1.2.2）
 *   · extractor_version —— **抽取器换了，同一位置抽出的字节可能变**。
 *     M0-1 实测：四个 PDF 库对同一份文件给出的可见性判断各不相同。
 *     不把它计入 id，就会出现「同一个 evidence_id 指向两份不同的抽取文本」。
 */
import { createHash } from 'node:crypto'
import { mkdirSync, writeFileSync, readFileSync, existsSync } from 'node:fs'
import { join } from 'node:path'
import { normalizeQuote } from './normalize.mjs'

export const sha256 = buf =>
  createHash('sha256').update(typeof buf === 'string' ? Buffer.from(buf, 'utf8') : buf).digest('hex')

/** 内容寻址写入：返回 sha256；同内容重复写是幂等的 */
export function putObject(root, bytes) {
  const h = sha256(bytes)
  const dir = join(root, 'objects', h.slice(0, 2))
  mkdirSync(dir, { recursive: true })
  const p = join(dir, h)
  if (!existsSync(p)) writeFileSync(p, bytes)
  return h
}

export function getObject(root, h) {
  const p = join(root, 'objects', h.slice(0, 2), h)
  return existsSync(p) ? readFileSync(p) : null
}

/** W-06 的证据卡 id */
export function evidenceId({ work_id, version_id, locator, quote, extractor_version }) {
  const parts = [work_id, version_id, locator, normalizeQuote(quote ?? ''), extractor_version]
  const names = ['work_id', 'version_id', 'locator', 'quote', 'extractor_version']
  const miss = names.filter((_, i) => parts[i] === undefined || parts[i] === null || String(parts[i]) === '')
  if (miss.length) throw new Error(`evidence_id 的五个分量缺一不可，缺：${miss.join('、')}`)
  return sha256(parts.join(' '))
}

/**
 * 写一张证据卡。
 * object_sha256 必须**已经在 CAS 里**——证据卡指向快照，而不是携带快照；
 * 指向一个不存在的对象就是一条断链，必须当场拒绝而不是留给下游发现。
 */
export function putEvidence(root, card) {
  const required = ['work_id', 'version_id', 'locator', 'quote', 'extractor_version', 'object_sha256']
  const missing = required.filter(k => !card[k])
  if (missing.length) throw new Error(`证据卡缺字段：${missing.join('、')}`)
  if (!getObject(root, card.object_sha256)) {
    throw new Error(`证据卡指向的快照 ${card.object_sha256.slice(0, 12)}… 不在 CAS 里 —— 断链`)
  }
  const id = evidenceId(card)
  const dir = join(root, 'evidence')
  mkdirSync(dir, { recursive: true })
  const full = { evidence_id: id, ...card, normalized_quote: normalizeQuote(card.quote) }
  writeFileSync(join(dir, `${id}.json`), JSON.stringify(full, null, 2) + '\n')
  return full
}

/**
 * source_integrity 的计算（§1.2.1）：快照是否仍与证据卡登记的一致。
 *   intact / mutated / missing / not_covered
 * **它由门算，不由任何 agent 声明**。
 */
export function sourceIntegrity(root, evidenceIdStr) {
  const p = join(root, 'evidence', `${evidenceIdStr}.json`)
  if (!existsSync(p)) return { verdict: 'not_covered', why: '证据卡不存在' }
  const card = JSON.parse(readFileSync(p, 'utf8'))
  const obj = getObject(root, card.object_sha256)
  if (!obj) return { verdict: 'missing', why: '快照不在 CAS 里' }
  if (sha256(obj) !== card.object_sha256) return { verdict: 'mutated', why: 'CAS 内容与其地址不符（存储损坏）' }
  const text = obj.toString('utf8')
  if (!normalizeQuote(text).includes(card.normalized_quote)) {
    return { verdict: 'mutated', why: '证据卡的引语不再是快照的子串' }
  }
  return { verdict: 'intact', why: null }
}
