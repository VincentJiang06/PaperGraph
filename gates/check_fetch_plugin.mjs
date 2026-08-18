#!/usr/bin/env node
/**
 * 取证插件门（GC-0：离线、确定性、零模型、零网络）
 *
 * 〔来历：R6-12〕独立审计的原话：**取证插件从未接进 profile**。
 * `--dump-config` 355 行里 `academic-fetch` 命中 0；包的 `main` 指向不存在的
 * `lib/index.js`；那条把自己插进配置树的 `insert` 没有任何脚本会安装它。
 * 02-ARCHITECTURE §B.2 把它列为 M1 交付件、`data.meta.evidence` 锚点的唯一落点——
 * 而产品链路一直是用相对路径 import 那个纯函数文件，**DSH 里没有这个工具**。
 *
 * 修完之后要有一道门守着它，否则下次同样悄悄掉线。难点是：真正能证明它接上了的
 * 是**真实 boot**，而真实 boot 要联网、要调模型，不满足 GC-0。
 *
 * 〔实测出来的分界线，写在这里免得下次又走错〕
 *   · `dsh --profile … --dump-config` —— **不加载插件树**。它能证明配置里有这一行，
 *     证明不了这一行能跑起来。
 *   · `dsh --profile … --help`        —— 同样**不加载插件树**：把 inject 改成
 *     不存在的服务名，--help 仍然 exit 0。拿它当 boot 证据会得到一个假绿。
 *   · `dsh --profile … "<task>"`      —— 真实 boot。破坏 inject 时 exit 1 并点名
 *     `dsh-academic-fetch: pending (waiting for service: no-such-service)`。
 *
 * 本门取中间路线：**把插件真的 apply 一遍**，用桩 ctx 与注入的抓取器。
 * 这样离线、确定，却能抓住我在修 R6-12 时真实踩到的两类错——它们都只在
 * apply 阶段暴露，dump 一律看不见：
 *   ① 漏写 `output` ⇒ defineTool 在 `options.output.render` 上抛；
 *   ② 可选参数写 `required: false` ⇒ boot 报 `must be true when present`。
 *
 * 它**不**替代真实 boot（见 07-ATTACK-LEDGER §S4 的实测记录），只是把
 * 「一改就坏」的那一段搬到了每次都跑得起的地方。
 *
 * 用法:  node gates/check_fetch_plugin.mjs [--root <dir>] [--profile <name>]
 */
import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { homedir } from 'node:os'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { createHash } from 'node:crypto'

const rootArg = process.argv.indexOf('--root')
const ROOT = rootArg > -1 ? process.argv[rootArg + 1] : fileURLToPath(new URL('..', import.meta.url))
const profArg = process.argv.indexOf('--profile')
const PROFILE = profArg > -1 ? process.argv[profArg + 1] : 'academic-research'
const DSH_HOME = process.env.DSH_HOME ?? join(homedir(), '.dsh')
const DEST = join(DSH_HOME, 'profiles', PROFILE)
const INSTALLED = join(DEST, 'node_modules/dsh-academic-fetch/lib/index.js')
const SOURCE = join(ROOT, 'packages/dsh-academic-fetch/lib/index.js')

let failed = 0
const fail = (m, d) => { failed++; console.log(`FAIL  ${m}`); if (d) console.log(`      ${d}`) }
const pass = m => console.log(`PASS  ${m}`)
const sha = f => createHash('sha256').update(readFileSync(f)).digest('hex')

console.log('取证插件门\n')

// ── ① 装上了，而且装的是**当前的源** ──────────────────────────────────
// 〔实测踩到的静默失败〕版本号不变时 npm 认为 `file:…0.1.0.tgz` 与已装的是
// 同一个依赖而跳过安装；给它 `--cache <目录>` 更狠——**退出码 0 而什么都没装**。
// 两次我都拿到了一个「源里有、跑的没有」的假绿。所以这条比的是哈希，不是存在性。
if (!existsSync(INSTALLED)) {
  fail(`取证插件未安装到 profile：${INSTALLED}`, '修法：bash profile/install.sh')
} else if (sha(INSTALLED) !== sha(SOURCE)) {
  fail('已安装的取证插件与仓库源不一致', `源 ${sha(SOURCE).slice(0, 12)}… / 产物 ${sha(INSTALLED).slice(0, 12)}…（npm 跳过了安装）`)
} else {
  pass(`取证插件已安装且与源逐字节一致（${sha(SOURCE).slice(0, 12)}…）`)
}

// ── ② profile 清单确实把它列为 bundle ─────────────────────────────────
{
  const pkg = JSON.parse(readFileSync(join(ROOT, 'profile/package.json'), 'utf8'))
  const bundles = pkg?.dsh?.profile?.bundles ?? []
  bundles.includes('dsh-academic-fetch')
    ? pass(`profile/package.json 的 bundles 含 dsh-academic-fetch（共 ${bundles.length} 个）`)
    : fail('profile/package.json 的 bundles 里没有 dsh-academic-fetch —— 插件不会进配置树（R6-12）')
}

// ── ③ **真的 apply 一遍**：dump 看不见的两类错都在这一步暴露 ──────────
if (existsSync(INSTALLED)) {
  const registered = []
  const ctx = { tools: { register: t => registered.push(t) } }
  let mod
  try { mod = await import(pathToFileURL(INSTALLED).href) }
  catch (e) { fail(`插件模块加载失败：${e.message}`) }

  if (mod) {
    if (!Array.isArray(mod.inject) || !mod.inject.includes('tools')) {
      fail(`inject 不含 'tools'：${JSON.stringify(mod.inject)}`,
           '实测：inject 写错时 --dump-config 与 --help 都 exit 0，只有真实 boot 报错')
    } else pass(`inject = ${JSON.stringify(mod.inject)}（服务名错 = 真实 boot 响亮失败）`)

    let applyErr = null
    try { mod.apply(ctx, { _fetch: fakeFetch }) } catch (e) { applyErr = e }
    if (applyErr) {
      fail(`apply() 抛出：${applyErr.message}`,
           'defineTool 的 schema 校验只在 apply 阶段发生 —— dump 一律看不见')
    } else if (registered.length !== 1) {
      fail(`注册了 ${registered.length} 个工具，期望 1 个`)
    } else {
      pass(`apply() 成功注册 ${registered[0].name}（defineTool 的 schema 校验通过）`)

      // ── ④ 行为：合法抓取产出六字段锚点；非法抓取当场拒 ────────────────
      const tool = registered[0]
      const args = { url: 'https://arxiv.org/abs/2401.001', locator: 'p3:l12',
                     work_id: 'W1', quote: 'AlphaFold reached 92% accuracy on CASP14.' }
      let out = null, err = null
      try { out = await tool.execute(args, {}, process.cwd()) } catch (e) { err = e }
      const ev = out?.meta?.evidence
      // 锚点的六字段来自 anchor.js 自己的 ANCHOR_FIELDS，不在这里另抄一份——
      // 抄一份就等于给它开了一条「两边不一致而没人发现」的缝。
      const { ANCHOR_FIELDS } = await import(pathToFileURL(join(ROOT, 'packages/dsh-academic-fetch/lib/anchor.js')).href)
      const SIX = ANCHOR_FIELDS
      if (err) fail(`合法抓取被拒：${err.message}`)
      else if (!ev) fail('产出里没有 meta.evidence —— 锚点没有落点（§B.2 的唯一落点）')
      else {
        const missing = SIX.filter(k => !ev[k])
        // 证据卡 id 的另外三分量必须一并回传，否则下游要把参数再穿一遍
        const cardMissing = ['work_id', 'version_id', 'locator'].filter(k => !out.meta[k])
        if (missing.length) fail(`锚点缺字段：${missing.join('、')}`)
        else if (cardMissing.length) fail(`meta 缺证据卡分量：${cardMissing.join('、')}`)
        else pass(`合法抓取产出 ${SIX.length} 字段锚点 + 证据卡三分量（${String(ev.object_sha256).slice(0, 12)}…）`)
      }

      // 非法抓取必须**当场抛**，而不是变成一条空证据 —— 后者是本项目最不能出的错
      const bad = [
        ['非 200', { status: 404, body: 'not found' }],
        ['空响应体', { status: 200, body: '' }],
      ]
      const leaked = []
      for (const [why, resp] of bad) {
        try {
          await registerFresh(mod, () => resp).execute(args, {}, process.cwd())
          leaked.push(why)
        } catch { /* 期望抛 */ }
      }
      leaked.length ? fail(`${leaked.length} 种非法抓取被放行：${leaked.join('、')}`)
                    : pass(`${bad.length} 种非法抓取全部当场拒（不会变成一条空证据）`)
    }
  }
}

console.log()
if (failed) {
  console.log(`FAIL  取证插件：${failed} 项不成立`)
  console.log('      M1 的交付件必须真的在 DSH 里，而不是只在仓库里。')
  process.exit(1)
}
console.log('PASS  取证插件已接进 profile，且 apply 后行为正确')
process.exit(0)

async function fakeFetch(url) {
  return { body: 'AlphaFold reached 92% accuracy on CASP14. It was evaluated on 87 targets.',
           status: 200, retrievedAt: '2026-08-18T10:00:00Z' }
}
/** 用另一个抓取器重新 apply 一次，拿到独立的工具实例 */
function registerFresh(mod, resp) {
  const reg = []
  mod.apply({ tools: { register: t => reg.push(t) } },
            { _fetch: async () => ({ ...resp(), retrievedAt: '2026-08-18T10:00:00Z' }) })
  return reg[0]
}
