#!/usr/bin/env node
// 规范源自洽门（GC-0：离线、确定性、零模型、零网络）
//
// 检查 01-CONTRACTS.md 自身的内部一致性。这是本项目的第一道真门，
// 它的存在本身是对一条一手教训的回应 [E: GROUND-TRUTH-CORRECTIONS.md#D1]：
// 前代 runbook 宣称 "Gate-integrity is pinned, not vibes"，但全量 grep
// 在三个子项目里零命中代码，只命中两处散文——门是空心的。
//
// 用法:  node gates/check_contracts.mjs [路径]
// 退出码: 0 = 全部 PASS，1 = 有 FAIL

import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const FILE = process.argv[2] ?? fileURLToPath(new URL('../01-CONTRACTS.md', import.meta.url))
const text = readFileSync(FILE, 'utf8')

const STATUS_ENUM = ['ST-V', 'ST-A', 'ST-E', 'ST-C', 'ST-U', 'ST-N']

const checks = []
const check = (id, desc, fn) => checks.push({ id, desc, fn })

/** 取 §7.3 起、§7.4 止的区间（作用表 + 别处表 + §7.3.2 散文） */
function section73() {
  const a = text.indexOf('### §7.3 flags')
  const b = text.indexOf('### §7.4')
  if (a < 0 || b < 0) throw new Error('定位不到 §7.3 / §7.4 分节标题')
  return text.slice(a, b)
}

/** §7.2 词表里声明的全部 flag id */
function vocabulary() {
  const ids = [...text.matchAll(/^\| (F-\d+[a-z]?) \| `[^`]+`/gm)].map(m => m[1])
  if (!ids.length) throw new Error('§7.2 词表一条都没解析到——表格格式可能变了')
  return [...new Set(ids)]
}

// ── V7.9 词表与作用表双向完备 ────────────────────────────────────────────
// C-1 的根因：F-14 同时被 S 2b 与 §7.3 的降档表消费，两次条件不同。
// 这类缺陷散文里读不出来（两行分开看都对），只有计数断言抓得住。
check('V7.9', '§7.2 词表与 §7.3/§7.3.1 作用表双向完备且无重复', () => {
  const vocab = vocabulary()
  const s73 = section73()
  const mentioned = new Set([...s73.matchAll(/F-\d+[a-z]?/g)].map(m => m[0]))

  // 重复只在表格部分判（§7.3.2 是散文，本来就会重复提及 F-14）
  const tables = s73.slice(0, s73.indexOf('**§7.3.2'))
  const counts = {}
  for (const m of tables.matchAll(/F-\d+[a-z]?/g)) counts[m[0]] = (counts[m[0]] ?? 0) + 1

  const missing = vocab.filter(f => !mentioned.has(f))
  const extra = [...mentioned].filter(f => !vocab.includes(f))
  const dup = Object.entries(counts).filter(([, c]) => c > 1).map(([f, c]) => `${f}×${c}`)

  const errs = []
  if (missing.length) errs.push(`词表有而作用表无: ${missing.join(' ')}`)
  if (extra.length) errs.push(`作用表有而词表无: ${extra.join(' ')}`)
  if (dup.length) errs.push(`作用表内重复: ${dup.join(' ')}`)
  return errs.length ? errs.join('; ') : null
})

// ── V7.10 状态符号不得越界 ──────────────────────────────────────────────
// V1.1 检查语料里的 status 字段值；这条检查文档正文。
// 规划文档里写出第七个状态符号（哪怕只是散文占位符），实现者就会把它当真。
check('V7.10', `全文 ST-* 符号都落在六值枚举内 (${STATUS_ENUM.join('/')})`, () => {
  const used = [...new Set([...text.matchAll(/ST-[A-Z]+/g)].map(m => m[0]))]
  const oob = used.filter(s => !STATUS_ENUM.includes(s))
  return oob.length ? `越界符号: ${oob.join(' ')}` : null
})

// ── V1.1′ 六值枚举本身必须齐全 ──────────────────────────────────────────
check('V1.1′', '§1.4 六值枚举六个值全部在文档中被定义', () => {
  const undef = STATUS_ENUM.filter(s => !text.includes(s))
  return undef.length ? `枚举值未出现: ${undef.join(' ')}` : null
})

// ── V1.5 禁止聚合字段 ───────────────────────────────────────────────────
// 「N 条断言已 verified」这类聚合数字是把可信度产品变成计分板的第一步。
check('V1.5', '不存在 overall_status / all_verified / pass_rate 字段', () => {
  const banned = ['overall_status', 'all_verified', 'pass_rate']
  const hit = banned.filter(b => new RegExp(`\`${b}\``).test(text))
  // 出现在「禁止」语境里是允许的，只有被定义为字段才失败
  const real = hit.filter(b => new RegExp(`\`${b}\`\\s*[:：]`).test(text))
  return real.length ? `被定义为字段: ${real.join(' ')}` : null
})

// ── D-1 已移除 ──────────────────────────────────────────────────────────
// 这里曾有一条 D-1「[E:] 指针格式可解析」，它只检查指针**非空**：
// `[E: 我瞎编的.md#根本不存在的锚]` 能通过，而且它只跑 01-CONTRACTS 一份文档，
// 另外 6 份的 870 个指针不在任何门的覆盖内。一个独立审计上下文把它判为空心门。
//
// 留着一道空心门比没有门更糟——它制造「这件事已经检查过了」的假象。
// 真正的检查在 gates/check_pointers.mjs（查文件存在性 + 锚点可解析性 + 棘轮欠债表），
// 其负例套件 gates/test_check_pointers.sh 的 R-1 正是这里放过的那一类。
//
// 保留这段注释而不是删干净，是因为「我们曾经有一道空心门」本身是本项目最该记住的教训之一。

// ── 执行 ────────────────────────────────────────────────────────────────
let failed = 0
console.log(`规范源自洽门 — ${FILE}\n`)
for (const c of checks) {
  let err
  try {
    err = c.fn()
  } catch (e) {
    err = `检查器自身抛出: ${e.message}`
  }
  if (err) {
    failed++
    console.log(`FAIL  ${c.id.padEnd(7)} ${c.desc}`)
    console.log(`      └─ ${err}`)
  } else {
    console.log(`PASS  ${c.id.padEnd(7)} ${c.desc}`)
  }
}

console.log(`\n${checks.length - failed}/${checks.length} 通过`)
process.exit(failed ? 1 : 0)
