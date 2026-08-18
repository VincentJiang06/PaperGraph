#!/usr/bin/env node
/**
 * 顶层研究门 —— 一个研究问题进去，一份带状态的成稿出来。
 *
 * 这道门验收的是整个产品最核心的那句话：
 *
 * > **同一个数字 `92%`，取证方式不同，读者看到的状态就不同。**
 *
 * 三条线跑同一个数字：
 *   A 合法转录        → 已验证
 *   B 从否定句里取     → 未验证（P1-C）
 *   C 5 个来源但同源   → 未验证，且「来源 5/独立簇 1」对读者可见（合成共识）
 *
 * 若这三条线得到相同的状态，本项目就没有存在的理由。
 */
import { mkdtempSync, rmSync, readFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
const rootArg = process.argv.indexOf('--root')
const ROOT = rootArg > -1 ? process.argv[rootArg + 1] : fileURLToPath(new URL('..', import.meta.url))
const { research } = await import(join(ROOT, 'src/research.mjs'))

const SNAP_POS = 'AlphaFold reached 92% accuracy on CASP14.'
const SNAP_NEG = 'The method did not reach 92% accuracy on CASP14.'
const mkFetch = (id, body, wid, up) => ({
  url: 'https://arxiv.org/abs/' + id, body, httpStatus: 200,
  retrievedAt: '2026-08-18T10:00:00Z', extractorVersion: 'pymupdf-1.28.2',
  work_id: wid, version_id: 'v1', locator: 'p1:l1', quote: body, anchorSentence: body,
  ...(up ? { upstream_id: up } : {}),
})
const mkClaim = (id, kind) => ({
  claim_id: id, kind, payload: { method: 'AlphaFold', value: '92%' },
  slot_types: { method: 'entity', value: 'value' },
  metric_frame: { metric: 'accuracy', sample_or_tier: 'CASP14' },
})
const CS = { query: 'AlphaFold accuracy CASP14 refute', result_keys: [] }   // 零命中（R6-06 (e′)：声称找到就必须抓过它）
const SPEC = () => ({
  question: 'AlphaFold 在 CASP14 上的准确率是多少？',
  threads: [
    { id: 'A', rounds: [{ fetches: [mkFetch('1', SNAP_POS, 'W1')], claim: mkClaim('cA', 'K-L-T'), counterSearch: CS }] },
    { id: 'B', rounds: [{ fetches: [mkFetch('2', SNAP_NEG, 'W2')], claim: mkClaim('cB', 'K-L-T'), counterSearch: CS }] },
    { id: 'C', rounds: [{ fetches: Array.from({ length: 5 }, (_, i) => mkFetch('m' + i, SNAP_POS, 'M' + i, 'nikkei-001')),
                          claim: mkClaim('cC', 'K-L-A'), counterSearch: CS }] },
  ],
  skeleton: 'A：{{claim:cA.value}}。B：{{claim:cB.value}}。C：{{claim:cC.value}}。',
})

let failed = 0
const fail = m => { failed++; console.log(`FAIL  ${m}`) }
console.log('顶层研究门\n')

const root = mkdtempSync(join(tmpdir(), 'research-'))
const r = await research(root, 'run-1', SPEC(), { maxConcurrent: 3 })

// ── ① 同一个数字，三种取证方式，三种状态 ──────────────────────────────
const WANT = { cA: 'verified', cB: 'unverified', cC: 'unverified' }
for (const [id, want] of Object.entries(WANT)) {
  if (r.manifest.statuses[id] !== want) fail(`${id} 期望 ${want}，实测 ${r.manifest.statuses[id]}`)
}
if (r.manifest.statuses.cA === r.manifest.statuses.cB) {
  fail('合法转录与「从否定句里取数字」得到相同状态 —— 本项目没有存在的理由')
}
if (!failed) console.log(`PASS  同一个数字 92%，三种取证方式 → ${Object.values(r.manifest.statuses).join(' / ')}`)

// ── ② 合成共识必须对读者可见 ──────────────────────────────────────────
if (!/来源 5\/独立簇 1/.test(r.prose)) {
  fail(`成稿没有把「5 个来源其实同源」展示给读者：${r.prose.trim()}`)
} else console.log('PASS  合成共识对读者可见（来源 5/独立簇 1）')

// ── ③ 成稿里每个数字都带状态 ──────────────────────────────────────────
const marks = (r.prose.match(/〔/g) ?? []).length
const nums = (r.prose.match(/92%/g) ?? []).length
if (marks !== nums) fail(`成稿里有 ${nums} 个数字但只有 ${marks} 个状态标记`)
else console.log(`PASS  成稿里 ${nums} 个数字全部带状态标记`)

// ── ④ 诊断必须查表得出（每条未终态的线都要有 remedy） ──────────────────
const noRemedy = r.manifest.diagnostics.filter(d => !d.remedy)
if (noRemedy.length) fail(`${noRemedy.length} 条探索日志没有 remedy —— 卡住的线无处可去`)
else console.log(`PASS  ${r.manifest.diagnostics.length} 条探索日志全部带 blocked_at + remedy（查表得出）`)

// ── ⑤ 可复现：同一 spec 两次运行得到相同状态与成稿 ────────────────────
const root2 = mkdtempSync(join(tmpdir(), 'research-'))
const r2 = await research(root2, 'run-1', SPEC(), { maxConcurrent: 1 })
if (r.prose !== r2.prose) fail('同一 spec 两次运行的成稿不同 —— 不可复现')
else if (JSON.stringify(r.manifest.statuses) !== JSON.stringify(r2.manifest.statuses)) {
  fail('同一 spec 两次运行的状态不同')
} else console.log('PASS  同一 spec 在并发度 3 与 1 下得到逐字节相同的成稿')

// ── ⑥ 产物齐全（W-01/06/03/04/08/10/12） ─────────────────────────────
const mani = JSON.parse(readFileSync(join(root, 'runs', 'run-1', 'manifest.json'), 'utf8'))
if (!(mani.evidence_cards >= 7)) fail(`证据卡只有 ${mani.evidence_cards} 张，期望 ≥7（1+1+5）`)
else console.log(`PASS  产物齐全：${mani.evidence_cards} 张证据卡 / ${Object.keys(mani.statuses).length} 条 status.json / manifest`)

rmSync(root, { recursive: true, force: true }); rmSync(root2, { recursive: true, force: true })
console.log()
if (failed) { console.log(`${failed} 处不一致`); process.exit(1) }
console.log('PASS  顶层：同一个数字，取证方式不同，读者看到的状态就不同')
