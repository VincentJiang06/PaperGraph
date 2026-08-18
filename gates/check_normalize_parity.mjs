#!/usr/bin/env node
/**
 * 归一化双实现对拍门。
 *
 * §1.2.2 现在有两个**独立**实现：
 *   · `src/normalize.mjs`（产品，JS）
 *   · `gates/repro/m0_2_normalization.py`（S0 复现脚本，Python，且把 S0 记录的
 *     18 格结论钉成了声明式期望）
 *
 * 单一实现的自洽不构成证据——恒返回 pass 的实现同样自洽。
 * 两个独立实现在同一组用例上逐格一致，才是。
 * 本门断言这件事，并且**用例来自 Python 那侧的 CASES 表**，
 * 即由已冻结的 S0 结论驱动，不是由 JS 这侧自己出题。
 */
import { readFileSync, existsSync } from 'node:fs'
import { join } from 'node:path'
import { execFileSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const rootArg = process.argv.indexOf('--root')
const ROOT = rootArg > -1 ? process.argv[rootArg + 1] : fileURLToPath(new URL('..', import.meta.url))
const { quoteFaithful, normalizeQuote, normalizeQuoteLegacy, dehyphenate } =
  await import(join(ROOT, 'src/normalize.mjs'))

let failed = 0
const fail = m => { failed++; console.log(`FAIL  ${m}`) }
console.log('归一化双实现对拍门\n')

// ── 用例从 Python 侧提取（它才是 S0 结论的载体） ───────────────────────
const py = join(ROOT, 'gates/repro/m0_2_normalization.py')
if (!existsSync(py)) { console.log(`FAIL  找不到 ${py}`); process.exit(2) }

let cases
try {
  const json = execFileSync('python3', ['-c', `
import json, importlib.util, sys
spec = importlib.util.spec_from_file_location('m', ${JSON.stringify(py)})
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
out = []
for cid, desc, snap, q, deh, exp in m.CASES:
    out.append({'id': cid, 'snapshot': snap, 'quote': q, 'pdf': deh,
                'py_raw': bool(m.check(snap, q, m.IDENTITY, deh)),
                'py_legacy': bool(m.check(snap, q, m.zh_rule_original, deh)),
                'py_fixed': bool(m.check(snap, q, m.zh_rule_fixed, deh)),
                'expected': list(exp)})
print(json.dumps(out, ensure_ascii=False))
`], { encoding: 'utf8', timeout: 60_000 })
  cases = JSON.parse(json)
} catch (e) {
  console.log(`FAIL  从 Python 侧提取用例失败：${String(e.message).slice(0, 200)}`)
  process.exit(1)
}

if (!cases.length) {
  console.log('FAIL  从 Python 侧提取到 0 条用例 —— 空集上所有断言都成立，拒绝给绿灯')
  process.exit(2)
}

// ── 逐格对拍 ────────────────────────────────────────────────────────────
let agree = 0
for (const c of cases) {
  const jsFixed = quoteFaithful(c.snapshot, c.quote, { pdf: c.pdf }).verdict === 'pass'
  const s0 = c.pdf ? dehyphenate(c.snapshot) : c.snapshot
  const q0 = c.pdf ? dehyphenate(c.quote) : c.quote
  const jsLegacy = normalizeQuoteLegacy(s0).includes(normalizeQuoteLegacy(q0))

  if (jsFixed !== c.py_fixed) fail(`[${c.id}] 现规则不一致：JS ${jsFixed} vs Python ${c.py_fixed}`)
  else if (jsLegacy !== c.py_legacy) fail(`[${c.id}] 旧规则不一致：JS ${jsLegacy} vs Python ${c.py_legacy}`)
  else agree++

  // 同时对齐 S0 冻结的期望值：Python 侧已经在断言它，这里再断言 JS 侧
  const [, expLegacy, expFixed] = c.expected
  if (jsFixed !== expFixed) fail(`[${c.id}] JS 现规则偏离 S0 记录的期望：期望 ${expFixed} 实测 ${jsFixed}`)
  if (jsLegacy !== expLegacy) fail(`[${c.id}] JS 旧规则偏离 S0 记录的期望：期望 ${expLegacy} 实测 ${jsLegacy}`)
}

if (!failed) console.log(`PASS  ${cases.length} 条用例 × 2 规则，JS 与 Python 双实现逐格一致，且均与 .loop/m0/M0-2.json 的冻结期望相符`)

console.log()
if (failed) { console.log(`${failed} 处不一致`); process.exit(1) }
console.log('PASS  §1.2.2 的两个独立实现相符')
