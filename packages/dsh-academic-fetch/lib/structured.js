/**
 * 结构化全文抓取 —— 让 ST-V 真正可达。
 *
 * 〔为什么建这个〕外部标定测试的头条结果是：**19 条真实 claim，0 条到达 verified**。
 * §3.4 的天花板要求 G5 = 全文快照 + **稳定可复核定位符**，而此前的抓取只给得出
 * Europe PMC 摘要（G3）或 PDF 抽取文本（G4）——两者都没有可独立寻址的锚。
 * 那不是判定逻辑的问题，加门解决不了；缺的是取证层。
 *
 * ── G5 的真正含义：可独立重新寻址 ────────────────────────────────────
 *
 * 一个「看起来像结构化定位符」的字符串不构成 G5。本模块的立场是：
 * **locator 必须能反查回同一段文本**，否则它只是一个装饰。
 * 因此 `resolveLocator()` 与 `extractPassages()` 是一对，
 * 而 `verifyRoundTrip()` 是把这一对钉死的那条断言。
 *
 * ── G5 是逐段的，不是逐文档的 ────────────────────────────────────────
 *
 * 实测（AlphaFold 那篇 Nature 的 JATS，PMC8371605）：
 *   带 id 的 `<p>`：53 个 · **不带 id 的 `<p>`：27 个**
 * 也就是说，同一份 JATS 文档里有三分之一的段落**没有稳定锚**。
 * 取自那些段落的引语即使在一份 JATS 文档里也够不上 G5——
 * 这条边界必须体现在实现里，否则「拿到了 JATS 就是 G5」会变成一次集体升档。
 *
 * ── 两种源，两种锚 ───────────────────────────────────────────────────
 *   JATS（Europe PMC `/{PMCID}/fullTextXML`）→ `jats:Sec2/Par7`
 *   arXiv LaTeXML HTML（`arxiv.org/html/{id}v{n}`）→ `html:#S3.SS1.p2`
 * 两者都在真实文档上验过：见 gates/check_structured_fetch.mjs 的实测夹具。
 */

/** 去标签，保留文本；解实体。 */
function textOf(xml) {
  return String(xml)
    .replace(/<(?:script|style)[\s\S]*?<\/(?:script|style)>/gi, ' ')
    .replace(/<[^>]+>/g, '')
    .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"')
    .replace(/&#x2019;|&#8217;/g, '’').replace(/&#xa0;|&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/\s+/g, ' ')
    .trim()
}

/** 取出某个标签的全部实例（含属性与内容），支持同名嵌套。 */
function* tagInstances(src, tag) {
  const open = new RegExp(`<${tag}\\b[^>]*>`, 'gi')
  let m
  while ((m = open.exec(src))) {
    if (/\/>$/.test(m[0])) continue
    let depth = 1, i = open.lastIndex
    const scan = new RegExp(`<${tag}\\b[^>]*>|</${tag}\\s*>`, 'gi')
    scan.lastIndex = i
    let s2
    while ((s2 = scan.exec(src))) {
      if (s2[0][1] === '/') { depth--; if (!depth) break } else if (!/\/>$/.test(s2[0])) depth++
    }
    if (!s2) break
    yield { attrs: m[0], inner: src.slice(i, s2.index), start: m.index, end: scan.lastIndex }
    open.lastIndex = s2.index
  }
}

const attr = (tagText, name) => (tagText.match(new RegExp(`\\b${name}=["']([^"']+)["']`, 'i')) ?? [])[1]

/**
 * 从 JATS 里抽出**可寻址**的段落。
 * @returns {{locator:string, text:string, sec:string, secTitle:string}[]}
 */
export function passagesFromJats(xml) {
  const out = []
  const body = (String(xml).match(/<body\b[^>]*>([\s\S]*)<\/body>/i) ?? [])[1] ?? String(xml)
  const walk = (frag, secId, secTitle) => {
    for (const sec of tagInstances(frag, 'sec')) {
      const id = attr(sec.attrs, 'id')
      const title = textOf((sec.inner.match(/<title\b[^>]*>([\s\S]*?)<\/title>/i) ?? [])[1] ?? '')
      walk(sec.inner, id ?? secId, title || secTitle)
    }
    // 只收**本层**的 p（子 sec 里的已在上面递归处理）
    const stripped = frag.replace(/<sec\b[^>]*>[\s\S]*?<\/sec>/gi, ' ')
    for (const p of tagInstances(stripped, 'p')) {
      const pid = attr(p.attrs, 'id')
      const text = textOf(p.inner)
      if (!text) continue
      // 没有 id 的段落**不可寻址** —— 不产出 locator，它够不上 G5。
      out.push({ locator: pid && secId ? `jats:${secId}/${pid}` : (pid ? `jats:${pid}` : null),
                 text, sec: secId ?? null, secTitle: secTitle ?? null })
    }
  }
  walk(body, null, null)
  return out
}

/** 从 arXiv LaTeXML HTML 抽出可寻址段落。锚点形如 `S3.SS1.p2`。 */
export function passagesFromArxivHtml(html) {
  const out = []
  const src = String(html)
  const re = /<(section|div|p)\b[^>]*\bid=["'](S\d[\w.]*)["'][^>]*>/gi
  let m
  const seen = new Set()
  while ((m = re.exec(src))) {
    const id = m[2]
    if (!/\.p\d+$/.test(id) || seen.has(id)) continue   // 只收段落级锚
    seen.add(id)
    const tag = m[1]
    let depth = 1, i = re.lastIndex
    const scan = new RegExp(`<${tag}\\b[^>]*>|</${tag}\\s*>`, 'gi')
    scan.lastIndex = i
    let s2
    while ((s2 = scan.exec(src))) {
      if (s2[0][1] === '/') { depth--; if (!depth) break } else if (!/\/>$/.test(s2[0])) depth++
    }
    const text = textOf(src.slice(i, s2 ? s2.index : src.length))
    if (text) out.push({ locator: `html:#${id}`, text, sec: id.split('.p')[0], secTitle: null })
  }
  return out
}

/**
 * 用 locator 反查原文。**这是 G5 的兑现方式**——
 * 一个解析不回去的定位符不构成「可独立复核寻址」。
 */
export function resolveLocator(doc, locator, kind) {
  const passages = kind === 'jats' ? passagesFromJats(doc) : passagesFromArxivHtml(doc)
  return passages.find(p => p.locator === locator)?.text ?? null
}

/**
 * 回指往返：locator 反查出来的文本必须**逐字包含**引语。
 * 不成立即不得记 G5 —— 由 gates/check_structured_fetch.mjs 守着。
 */
export function verifyRoundTrip(doc, locator, quote, kind) {
  if (!locator) return { ok: false, why: '该段落没有稳定锚（JATS 里约三分之一的 <p> 不带 id）' }
  const text = resolveLocator(doc, locator, kind)
  if (text == null) return { ok: false, why: `locator ${locator} 在文档里解析不到` }
  const norm = s => String(s).normalize('NFKC').replace(/\s+/g, ' ').trim()
  if (!norm(text).includes(norm(quote))) {
    return { ok: false, why: `locator ${locator} 解析到的段落不含该引语（锚点指向了别处）` }
  }
  return { ok: true, passageLength: text.length }
}
