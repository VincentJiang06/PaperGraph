#!/usr/bin/env node
/**
 * profile 门 —— 断言 `profile/cordis.patch.yml` 写的每一条**都真的生效了**。
 *
 * 〔为什么判据不是「溯源注释存在」〕02-ARCHITECTURE 原本规定的命中判据是
 *   「`--dump-config` 里 `patch: entry` 计数 = 0，且目标行上方出现溯源注释」。
 * S2 实测推翻了后半句：**值与出厂一致的 patch 不产生溯源注释**
 * （把 `maxInlineBytes` 从 50000 改成 50001，注释立刻出现；改回去又消失）。
 *
 * 而「值与出厂一致的行」正是架构**自己推荐写**的那一类
 * （「显式重述出厂值，让漂移在 diff 里可见」）。于是那条判据对它们恒不成立——
 * 它们存在的意义正是「将来出厂值漂移时替我们兜底」，
 * 却**今天无法确认接对了线**。等出厂值真漂了才发现 id 写错，就晚了。
 *
 * 本门因此用**生效值比对**：dump 里该键的值必须逐字等于我们写的值。
 * 这条对 no-op 与有效 patch 一样成立，且不依赖任何注释格式。
 *
 * 三条断言：
 *   ① `--dump-config` 的 stderr 里 `patch: entry` 计数 = 0（id 写错 → 真静默，
 *      唯一抓得住它的地方就是这里，S0 实测 M0-3c）
 *   ② 我们 patch 的每一个键，dump 里的生效值 == 我们写的值
 *   ③ 环境变量接缝已封死：DSH_TOOLS_MODE=code 时 `tools.mode` 仍为 native
 */
import { readFileSync, existsSync } from 'node:fs'
import { join } from 'node:path'
import { execFileSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const rootArg = process.argv.indexOf('--root')
const ROOT = rootArg > -1 ? process.argv[rootArg + 1] : fileURLToPath(new URL('..', import.meta.url))
const profArg = process.argv.indexOf('--profile')
const PROFILE = profArg > -1 ? process.argv[profArg + 1] : 'academic-research'

let failed = 0
const fail = m => { failed++; console.log(`FAIL  ${m}`) }

console.log('profile 门\n')

// ── 解析我们自己的 patch（格式受控，只需支持我们写得出的形态） ──────────
const patchPath = join(ROOT, 'profile/cordis.patch.yml')
if (!existsSync(patchPath)) { console.log(`FAIL  找不到 ${patchPath}`); process.exit(2) }
const patchSrc = readFileSync(patchPath, 'utf8')

/** 把 `key: value` 的 value 归一成可比较的字符串 */
const norm = v => v.trim().replace(/^['"]|['"]$/g, '')

const entries = []
let cur = null
for (const raw of patchSrc.split('\n')) {
  const line = raw.replace(/\s+#.*$/, '')
  if (/^\s*#/.test(line) || !line.trim()) continue
  const idm = line.match(/^- id:\s*(\S+)/)
  if (idm) { cur = { id: idm[1], keys: [], disabled: false, stack: [] }; entries.push(cur); continue }
  if (!cur) continue
  if (/^\s+disabled:\s*true/.test(line)) { cur.disabled = true; continue }
  // 键必须带**路径**：`tool-subagent` 同时有顶层 `provider: spawn` 与嵌套的
  // `agentOptions.provider: deepseek-official`，扁平取键名会把两者当同一个。
  // 〔本门第一次运行就抓到了这个我自己的解析 bug——它报的是「生效值 spawn，
  //   我们写的是 deepseek-official」，而两者其实是不同的键。〕
  const kv = line.match(/^(\s+)([A-Za-z_][\w-]*):\s*(.*)$/)
  if (kv) {
    const [, indent, k, v] = kv
    const depth = indent.length
    while (cur.stack.length && cur.stack[cur.stack.length - 1].depth >= depth) cur.stack.pop()
    if (!v.trim()) { cur.stack.push({ k, depth }); continue }   // 容器键
    const path = [...cur.stack.filter(x => x.k !== 'config').map(x => x.k), k]
    cur.keys.push({ k, path: path.join('.'), v: norm(v), depth })
  }
}

if (!entries.length) {
  console.log('FAIL  从 profile/cordis.patch.yml 解析出 0 条 patch —— 空集上所有断言都成立，拒绝给绿灯')
  process.exit(2)
}

// ── 跑 dump ─────────────────────────────────────────────────────────────
let dump = '', derr = ''
try {
  dump = execFileSync('dsh', ['--profile', PROFILE, '--dump-config'],
    { encoding: 'utf8', timeout: 120_000, stdio: ['ignore', 'pipe', 'pipe'] })
} catch (e) {
  derr = String(e.stderr ?? '')
  dump = String(e.stdout ?? '')
  if (!dump) { console.log(`FAIL  dsh --profile ${PROFILE} --dump-config 跑不起来：${e.message}`); process.exit(1) }
}
// stderr 单独再取一次（execFileSync 成功时不给 stderr）
try {
  derr = execFileSync('bash', ['-c',
    `dsh --profile ${PROFILE} --dump-config 2>&1 >/dev/null`], { encoding: 'utf8', timeout: 120_000 })
} catch { /* 忽略 */ }

// ── ① id 写错 = 真静默，唯一抓得住它的地方 ──────────────────────────────
const notFound = (derr.match(/patch: entry/g) ?? []).length
if (notFound) {
  fail(`${notFound} 条 patch 的 id 匹配不到目标行（真实 boot 路径上完全静默，只有 --dump-config 的 stderr 会说）`)
  for (const l of derr.split('\n').filter(l => /patch: entry/.test(l)).slice(0, 10)) console.log(`      ${l.trim()}`)
} else {
  console.log('PASS  patch id 全部匹配到目标行（stderr 里 `patch: entry` 计数 0）')
}

// ── ② 生效值比对 ────────────────────────────────────────────────────────
const L = dump.split('\n')
const blockOf = id => {
  const i = L.findIndex(l => l === `- id: ${id}`)
  if (i < 0) return null
  let j = i + 1
  while (j < L.length && !L[j].startsWith('- id: ') && !L[j].startsWith('# ==')) j++
  return L.slice(i, j)
}

let checked = 0
for (const e of entries) {
  const blk = blockOf(e.id)
  if (!blk) { fail(`patch 里的 id \`${e.id}\` 在 dump 里根本不存在`); continue }
  const text = blk.join('\n')
  if (e.disabled) {
    checked++
    if (!/^\s+disabled: true$/m.test(text)) fail(`\`${e.id}\` 我们写了 disabled: true，dump 里没有生效`)
  }
  for (const { k, path, v, depth } of e.keys) {
    checked++
    // 用**缩进深度**限定，嵌套同名键才不会互相冒充。
    const hits = blk.filter(l => new RegExp(`^\\s{${depth}}${k}:\\s*(.+)$`).test(l))
    if (!hits.length) { fail(`\`${e.id}.${path}\` 在 dump 里找不到（我们写的值是 ${v}）`); continue }
    const got = norm(hits[0].split(/:(.+)/)[1] ?? '')
    if (got !== v) fail(`\`${e.id}.${path}\` 生效值是 ${got}，我们写的是 ${v}`)
  }
}
if (!failed) console.log(`PASS  ${entries.length} 条 patch / ${checked} 个键的生效值与 profile/cordis.patch.yml 逐字一致`)

// ── ③ 环境变量接缝必须已被封死 ──────────────────────────────────────────
// headless 把 tools 行 config 整键换成 `mode: !!js process.env.DSH_TOOLS_MODE`。
// 不写死，呈现模式就由**启动进程的环境变量**决定，而 dump 只会原样打印那个表达式。
let dumpCode = ''
try {
  dumpCode = execFileSync('bash', ['-c',
    `DSH_TOOLS_MODE=code dsh --profile ${PROFILE} --dump-config 2>/dev/null`], { encoding: 'utf8', timeout: 120_000 })
} catch { /* 下面按空处理 */ }
const modeOf = d => {
  const i = d.split('\n').findIndex(l => l === '- id: tools')
  if (i < 0) return null
  return (d.split('\n').slice(i, i + 6).find(l => /^\s+mode:/.test(l)) ?? '').split(':')[1]?.trim() ?? null
}
const m1 = modeOf(dump), m2 = modeOf(dumpCode)
if (m1 === null || m2 === null) fail('读不到 tools.mode，无法验证环境变量接缝')
else if (m1 !== m2) fail(`环境变量接缝没封死：不设 DSH_TOOLS_MODE 时 mode=${m1}，DSH_TOOLS_MODE=code 时 mode=${m2}`)
else console.log(`PASS  环境变量接缝已封死（DSH_TOOLS_MODE 变化不影响 tools.mode=${m1}）`)

// ── ④ 取证插件必须真的在配置树里（R6-12） ────────────────────────────
// 审计原话：`--dump-config` 355 行里 `academic-fetch` 命中 0，
// M1 的交付件在 DSH 里根本不存在。这条断言比对的是 dump 本身，不是仓库里的文件。
{
  const hit = /^-\s*id:\s*tool-academic-fetch\s*$/m.test(dump)
  if (!hit) {
    fail('`--dump-config` 里没有 tool-academic-fetch —— 取证插件没接进 profile（R6-12）')
    console.log('      修法：bash profile/install.sh')
  } else {
    console.log('PASS  取证插件在配置树里（dump 含 tool-academic-fetch）')
  }
}

console.log()
if (failed) { console.log(`${failed} 处不一致`); process.exit(1) }
console.log('PASS  profile 的每一条 patch 都真的生效了')
