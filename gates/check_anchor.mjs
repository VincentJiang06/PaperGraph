#!/usr/bin/env node
/**
 * 证据锚点门（GC-0）—— `tool/result.data.meta.evidence` 的六字段。
 *
 * 〔为什么锚点必须由我们自己的工具写〕02-ARCHITECTURE §A 第 1 条：
 * `meta` 的值来自**工具执行器的返回值**，第三方工具的 `meta` 不受我们控制。
 * `packages/dsh-academic-fetch` 存在的全部理由就是这个。
 *
 * 本门守的是：**一个字段不全的锚点比没有锚点更坏——它看起来可复核**。
 */
import { fileURLToPath } from 'node:url'
import { join } from 'node:path'
const rootArg = process.argv.indexOf('--root')
const ROOT = rootArg > -1 ? process.argv[rootArg + 1] : fileURLToPath(new URL('..', import.meta.url))
const { buildAnchor, validateAnchor, ANCHOR_FIELDS } =
  await import(join(ROOT, 'packages/dsh-academic-fetch/lib/anchor.js'))

const GOOD = { url: 'https://arxiv.org/abs/2401.001', body: 'AlphaFold reached 92%.',
  httpStatus: 200, retrievedAt: '2026-08-18T10:00:00Z', extractorVersion: 'pymupdf-1.28.2' }

let failed = 0
const fail = m => { failed++; console.log(`FAIL  ${m}`) }
console.log('证据锚点门\n')

// ① 合法抓取必须产出六字段齐全的锚点
let anchor
try { anchor = buildAnchor(GOOD) } catch (e) { fail(`合法抓取被拒：${e.message}`) }
if (anchor) {
  const miss = ANCHOR_FIELDS.filter(f => anchor[f] === undefined)
  if (miss.length) fail(`锚点缺字段：${miss.join('、')}`)
  else if (validateAnchor(anchor)) fail(`自产锚点通不过自己的校验：${validateAnchor(anchor)}`)
  else console.log(`PASS  合法抓取产出六字段齐全的锚点（${ANCHOR_FIELDS.join(' / ')}）`)
}

// ② 每一类不合法的抓取都必须**当场拒**
const BAD = [
  ['非 200 响应', { ...GOOD, httpStatus: 404 }],
  ['302 也不行', { ...GOOD, httpStatus: 302 }],
  ['空响应', { ...GOOD, body: '' }],
  ['缺 extractor_version', { ...GOOD, extractorVersion: undefined }],
  ['url 不是绝对地址', { ...GOOD, url: '/relative/path' }],
  ['retrieved_at 不可解析', { ...GOOD, retrievedAt: 'yesterday' }],
  ['http_status 不是整数', { ...GOOD, httpStatus: '200' }],
]
let denied = 0
for (const [n, o] of BAD) {
  let threw = false
  try { buildAnchor(o) } catch { threw = true }
  if (threw) denied++; else fail(`${n} 竟然产出了锚点`)
}
if (denied === BAD.length) console.log(`PASS  ${BAD.length} 类不合法抓取全部当场拒绝`)

// ③ 下游校验必须能识别被篡改/残缺的锚点
const TAMPERED = [
  ['缺一个字段', a => { const c = { ...a }; delete c.bytes; return c }],
  ['哈希不是 64 hex', a => ({ ...a, object_sha256: 'deadbeef' })],
  ['http_status 被改成 404', a => ({ ...a, http_status: 404 })],
  ['bytes 归零', a => ({ ...a, bytes: 0 })],
]
let caught = 0
for (const [n, mut] of TAMPERED) {
  if (validateAnchor(mut(anchor))) caught++; else fail(`下游校验放过了「${n}」的锚点`)
}
if (caught === TAMPERED.length) console.log(`PASS  下游校验识别出全部 ${TAMPERED.length} 类残缺/篡改锚点`)

// ④ 同内容必须同哈希（确定性）
if (buildAnchor(GOOD).object_sha256 !== buildAnchor(GOOD).object_sha256) {
  fail('同一次抓取两次构造出的 object_sha256 不同 —— 锚点不是确定性的')
}

console.log()
if (failed) { console.log(`${failed} 处不一致`); process.exit(1) }
console.log('PASS  证据锚点：六字段齐全、非法抓取当场拒、残缺锚点下游可识别')
