#!/usr/bin/env node
// 发布前门（GC-0：离线、确定性、零模型、零网络）
//
// 这个仓库是 public 的。本门在推送前检查三件事：
//   ① 没有硬编码密钥
//   ② 没有本机绝对路径（会泄露用户名与目录结构，且对读者无意义）
//   ③ 没有被排除的第三方内部调研混进来
//
// 它是对一条运行要求的机械化：「上传的时候记得做好 api 隔离」。
// 一次性人工检查会在第二次推送时失效；门不会。
//
// 用法:  node gates/check_publishable.mjs [目录]
// 退出码: 0 = 可发布，1 = 有阻塞项

import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, relative, basename } from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = process.argv[2] ?? fileURLToPath(new URL('..', import.meta.url))

// 不扫描的目录（归档是历史，按原样保留；node_modules 不是我们的内容）
const SKIP_DIRS = new Set(['.git', 'node_modules', '.archive', '.venv', '__pycache__'])

// ② 本机绝对路径：只认用户主目录前缀，`~/...` 是可以的
const LOCAL_PATH = /\/Users\/[a-z][a-z0-9_-]*\//gi

// ③ 排除清单：第三方（DSH）内部实现的逆向调研。
//    DSH 本身是 npm 公开包，这不是保密问题——是「别把别人包的逆向档案当自己仓库的内容发布」。
//    自己项目的考古（gt-pg-*）与自己仓库的方法论（gt-house-method）不在此列。
const EXCLUDED_BASENAMES = new Set([
  'gt-profile-plugin.md',
  'gt-orchestration.md',
  'gt-evidence-substrate.md',
  'gt-exec-security.md',
  'GROUND-TRUTH-CORRECTIONS.md',
])

// ① 密钥形态。刻意保守——宁可误报让人看一眼，不可漏报。
const SECRET_PATTERNS = [
  { name: 'OpenAI/Anthropic 风格 key', re: /\b(sk|pk)-[A-Za-z0-9_-]{24,}\b/g },
  { name: 'AWS access key id', re: /\bAKIA[0-9A-Z]{16}\b/g },
  { name: 'GitHub token', re: /\bgh[pousr]_[A-Za-z0-9]{30,}\b/g },
  { name: 'Google API key', re: /\bAIza[0-9A-Za-z_-]{35}\b/g },
  { name: 'Slack token', re: /\bxox[baprs]-[0-9A-Za-z-]{10,}\b/g },
  { name: 'PEM 私钥', re: /-----BEGIN (RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----/g },
  { name: '赋值给 key/token/secret 的长字面量', re: /\b(api[_-]?key|auth[_-]?token|secret|password)\s*[:=]\s*["'][A-Za-z0-9_\-+/]{20,}["']/gi },
]

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    if (SKIP_DIRS.has(name)) continue
    const p = join(dir, name)
    const st = statSync(p)
    if (st.isDirectory()) walk(p, out)
    else if (st.size < 8 * 1024 * 1024) out.push(p)
  }
  return out
}

const files = walk(ROOT)
const problems = { secrets: [], paths: [], excluded: [] }

for (const f of files) {
  const rel = relative(ROOT, f)

  if (EXCLUDED_BASENAMES.has(basename(f))) {
    problems.excluded.push(rel)
    continue
  }

  let text
  try {
    text = readFileSync(f, 'utf8')
  } catch {
    continue // 二进制
  }

  for (const { name, re } of SECRET_PATTERNS) {
    for (const m of text.matchAll(re)) {
      const line = text.slice(0, m.index).split('\n').length
      problems.secrets.push({ rel, line, name, sample: m[0].slice(0, 18) + '…' })
    }
  }

  const seen = new Set()
  for (const m of text.matchAll(LOCAL_PATH)) {
    if (seen.has(m[0])) continue
    seen.add(m[0])
    const line = text.slice(0, m.index).split('\n').length
    problems.paths.push({ rel, line, sample: m[0] })
  }
}

console.log(`发布前门 — ${ROOT}`)
console.log(`扫描 ${files.length} 个文件\n`)

let failed = 0

// ① 密钥
if (problems.secrets.length) {
  failed++
  console.log(`FAIL  硬编码密钥 · ${problems.secrets.length} 处`)
  for (const p of problems.secrets.slice(0, 20)) {
    console.log(`      ${p.rel}:${p.line}  [${p.name}]  ${p.sample}`)
  }
  console.log('      注：本门刻意保守，英文词里的 sk- 前缀（如 risk-oversight）也会命中，逐条人看一眼再放行')
} else {
  console.log('PASS  硬编码密钥 · 0 处')
}

// ② 绝对路径
if (problems.paths.length) {
  failed++
  console.log(`FAIL  本机绝对路径 · ${problems.paths.length} 处（泄露用户名与目录结构，且对读者无意义）`)
  const byFile = {}
  for (const p of problems.paths) (byFile[p.rel] ??= []).push(p)
  for (const [rel, ps] of Object.entries(byFile)) {
    console.log(`      ${rel}  ×${ps.length}   例: ${ps[0].sample}`)
  }
  console.log('      修法: 换成 ~/ 或 <repo>/ 或 $DSH_PKGS/ 之类的可移植占位')
} else {
  console.log('PASS  本机绝对路径 · 0 处')
}

// ③ 排除内容
if (problems.excluded.length) {
  failed++
  console.log(`FAIL  被排除的第三方内部调研混入 · ${problems.excluded.length} 个文件`)
  for (const r of problems.excluded) console.log(`      ${r}`)
} else {
  console.log('PASS  被排除的第三方内部调研 · 0 个')
}

console.log(`\n${failed ? `${failed} 类阻塞项，不可发布` : '可发布'}`)
process.exit(failed ? 1 : 0)
