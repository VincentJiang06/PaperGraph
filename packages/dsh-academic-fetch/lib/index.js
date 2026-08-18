/**
 * `dsh-academic-fetch` —— 学术取证工具，把**证据锚点**写进 `tool/result.data.meta`。
 *
 * 〔它为什么必须真的存在于 DSH 里：R6-12〕
 * 独立审计的原话：**取证插件从未接进 profile**。
 *   · profile 的 bundles 只有 base 与 headless，patch 里没有一行提到 academic-fetch；
 *   · 本包的 `cordis.patch.yml`（那条把自己插进树的 insert）没有任何脚本会安装它；
 *   · package.json 的 `main`/`exports` 指向**不存在的** `lib/index.js`；
 *   · `--dump-config` 355 行里 academic 只出现在本地路径注释里。
 * 而 02-ARCHITECTURE §B.2 把它列为 M1 交付件、`data.meta.evidence` 锚点的唯一落点。
 * 换句话说：产品链路一直是用相对路径 import 那个纯函数文件，**DSH 里没有这个工具**。
 *
 * 这个文件是那条断链的另一半。它做的事很少，而且刻意很少：
 *   取一次 → 造锚点（六字段齐全，非法当场拒）→ 把锚点放进 data.meta.evidence。
 * 判定一律不在这里发生 —— 抓取器是 W-02，它**只**负责让「这段字节来自哪里」
 * 可复核。任何 status、任何等级、任何「这条支持我」的话都不归它写。
 *
 * 〔可测性接缝〕`config._fetch` 允许注入抓取实现。理由与 mp-automator 的 `_exec` 相同：
 * 没有接缝，这个文件就只能靠联网才能被验，于是它会像上一版一样**根本没被验过**。
 * 只接受函数值——配置文件里放一个字符串永远替换不掉真的抓取器。
 */
import { defineTool } from '@deepseek-ai/dsh-tools'
import { buildAnchor, validateAnchor } from './anchor.js'

/** Cordis 插件名，Loader 诊断用。 */
export const name = 'academic-fetch'

/** 注入 tools 能力；服务名猜错是**响亮失败**（boot 退出码 1 并点名缺失服务）。 */
export const inject = ['tools']

export const ACADEMIC_FETCH_TOOL = 'academic_fetch'

export function apply(ctx, config = {}) {
  const doFetch = typeof config._fetch === 'function' ? config._fetch : defaultFetch
  const extractorVersion = String(config.extractorVersion ?? 'dsh-academic-fetch-0.1.0')

  /**
   * 工具产出的 schema 与渲染。
   *
   * 〔这一段是实测逼出来的〕初版没写 `output`，于是 `defineTool` 在
   * `options.output.render` 上抛 `Cannot read properties of undefined`——
   * 而这条错误**只在真实 boot 路径上出现**：`dsh --profile … --help` 退出码 0，
   * 连插件树都不加载（实测：把 inject 改成不存在的服务名，--help 仍然 exit 0，
   * 真实 boot 才 exit 1 并点名 `waiting for service: no-such-service`）。
   * 也就是说 profile patch 注释里「inject 猜错是响亮失败」这句话是对的，
   * **但只对真实 boot 成立**——用 --help 当 boot 证据会得到一个假绿。
   *
   * 渲染刻意只给一行摘要：锚点本身走 `data.meta.evidence` 给门看，
   * 不是给模型看的。让模型读到整份锚点，等于邀请它对证据发表看法。
   */
  const anchorOutput = {
    schema: {
      type: 'object', additionalProperties: true,
      properties: { summary: { type: 'string', required: true } },
    },
    render: (_args, value) => [{ type: 'text', text: value.summary }],
  }

  ctx.tools.register(defineTool({
    name: ACADEMIC_FETCH_TOOL,
    output: anchorOutput,
    description:
      'Fetch an academic source and return its bytes together with a verifiable evidence anchor. ' +
      'The anchor (url, http_status, retrieved_at, extractor_version, object_sha256, locator) lands in ' +
      'result.data.meta.evidence and is what makes any later quote checkable. ' +
      'This tool never judges whether a source supports a claim — it only records where the bytes came from.',
    parameters: {
      url: { type: 'string', required: true, description: 'absolute http(s) URL of the source' },
      locator: { type: 'string', required: true, description: 'in-document locator, e.g. p3:l12 or §4.2' },
      work_id: { type: 'string', required: true, description: 'stable work identity (DOI, arXiv id, or corpus id)' },
      // 可选参数**省略** `required`，不能写 `required: false`——
      // 实测 boot 报 `parameters.version_id.required must be true when present`。
      version_id: { type: 'string', description: 'version of that work; defaults to v1' },
      quote: { type: 'string', description: 'the verbatim span to be anchored, if already known' },
    },
    isConcurrencySafe: () => true,
    timeoutMs: 60_000,
    async execute(args) {
      const got = await doFetch(args.url)
      const f = {
        url: args.url, body: got.body, httpStatus: got.status,
        retrievedAt: got.retrievedAt, extractorVersion,
        work_id: args.work_id, version_id: args.version_id ?? 'v1',
        locator: args.locator, quote: args.quote ?? '',
      }
      // 非法抓取在这里就抛：非 200 / 空体 / 缺抽取器版本。
      // 让一条抓不到的证据静默变成一条空证据，是本项目最不能出的错。
      const anchor = buildAnchor(f)
      const bad = validateAnchor(anchor)
      if (bad) throw new Error(`evidence anchor rejected: ${bad}`)
      // 锚点回答「这段字节来自哪里」；证据卡 id 还需要 work_id/version_id/locator
      // （§W-06 的五分量）。把它们一并放进 meta，下游就不必再把参数穿一遍——
      // 每多一次转抄，就多一个「转抄时被改掉」的位置。
      return {
        summary: `fetched ${args.url} (${got.status}, ${Buffer.byteLength(got.body, 'utf8')}B) → ${anchor.object_sha256.slice(0, 12)}…`,
        meta: {
          evidence: anchor,
          work_id: f.work_id, version_id: f.version_id, locator: f.locator,
        },
      }
    },
  }))
}

async function defaultFetch(url) {
  const res = await fetch(url, { redirect: 'follow' })
  return { body: await res.text(), status: res.status, retrievedAt: new Date().toISOString() }
}
