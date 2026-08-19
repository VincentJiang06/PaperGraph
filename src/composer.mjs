/**
 * 确定性组稿器 —— W-10。
 *
 * 01-CONTRACTS §4 W-10 逐字：写者是**确定性组稿器**；
 * 作者 agent 写 outline 与叙述骨架，**不写数字**；
 * 正文数字一律写成 {{claim:<id>.<field>}}。
 *
 * 〔为什么这是产品诚实性的最后一道闸〕前面所有门都作用在 claim 上，
 * 而读者读的是**成稿**。作者 agent 若能在正文里直接敲一个数字，
 * 整条证据链就在最后一步被绕过——读者看到的数字与任何 claim 都没有关系，
 * 更没有 status。
 *
 * 本模块因此做两件事：
 *   ① **拒绝**骨架里出现裸数字（不在占位符里的数字）
 *   ② 每个占位符渲染时**必带 status 标记**；status 来自 status.json，
 *      组稿器不参与判定、也不能覆盖它
 */

const PLACEHOLDER = /\{\{claim:([A-Za-z0-9_-]+)\.([A-Za-z0-9_]+)\}\}/g

/**
 * 〔R6-07〕W-10 的执行此前是一条 ASCII 正则 + 两条豁免，绕过面很宽。
 * 独立攻击者当场放行的清单：
 *   『百分之九十二』『四千五百二十三名患者』『参数量 9.2e10』『XCII%』
 *   『共纳入 2019 名患者』『死亡 1987 例』『18 人死亡』
 * 后三条最要命——它们不是绕过技巧，是**最普通的学术句子**，而且全是承重数据：
 * 样本量、死亡数。两条豁免（1900–2099 区间、≤20 的整数）本意是放过年份与章节号，
 * 实际放过的是任何落在那个区间里的数。
 *
 * 现在豁免必须**自证身份**，而不是靠数值区间猜：
 *   · 年份 —— 必须写成 `2019 年`，或括号引用形态 `(2019)`；
 *   · 序号 —— 必须带 `第` / `§` / `Section` / `Table` / `Figure` / `Chapter` / `No.`。
 * 说不出自己是年份还是序号的数字，就是承重数字，就得走占位符。
 */
const UNIT = '%|‰|倍|x|ms|秒|分钟|小时|天|年|月|日|个|篇|条|名|例|人|位|项|次|种|组|家|所|元|万元|亿元|美元|分|度|kg|g|mg|km|m|cm|mm|GB|MB|KB'
const BARE_NUMBER = new RegExp(`(?<![\\w.])(\\d+(?:\\.\\d+)?)\\s*(${UNIT})?(?!\\w)`, 'g')
// 科学计数法：`9.2e10` 此前整串逃逸——小数点被 lookbehind 挡住，`e10` 又让 (?!\w) 失败。
const SCI_NUMBER = /(?<![\w.])\d+(?:\.\d+)?[eE][+-]?\d+/g
// 罗马数字 + 单位：`XCII%`。单独的 `I`/`V`/`X` 不算（会误伤变量名与罗马数字章节号）。
const ROMAN_NUMBER = new RegExp(`(?<![A-Za-z])[IVXLCDM]{2,}\\s*(${UNIT})`, 'g')
// 中文数字。单位表与阿拉伯数字共用一张，避免两条通道的口径分叉——
// 〔R6-07〕`四千五百二十三名患者` 正是从口径分叉里漏出去的：`名` 不在旧表内。
const CN_NUMBER = new RegExp(`[〇零一二三四五六七八九十百千万亿两]{2,}\\s*(${UNIT}|百分点|分之)`, 'g')
// 「百分之九十二」：数词在**后**，与上面方向相反，单列。
const CN_PERCENT = /百分之[〇零一二三四五六七八九十百千万两]+/g

const ORDINAL_PREFIX = /(第|§|No\.|Section|Table|Tab\.|Figure|Fig\.|Chapter|表|图)\s*$/i

const STATUS_MARK = {
  verified: '已验证', attributed: '已归因', estimated: '估计值',
  contested: '有反证', unverified: '未验证', not_covered: '未覆盖',
}

export function compose(skeleton, statusById, opts = {}) {
  const allowYears = opts.allowYears !== false

  // ① 裸数字检查：先把占位符挖掉，再扫剩下的
  // 先 NFKC 归一化：全角数字「９２％」在归一化后变成半角，否则同样绕过。
  // 占位符换成哨兵而不是空格:后面要靠它区分「单位」与「裸数字」。
  // 〔E-3,外部标定测试发现〕骨架 `{{claim:c1.cost}} 十亿美元` 被判成裸数字——
  // 「十亿美元」是**单位**,数字由占位符提供。结果是「X 十亿美元」这种最普通的
  // 中文量纲写法根本写不出来,而作者会转而去写阿拉伯数字,正好绕开 W-10。
  // 一条把正确写法也拦掉的规则,会把人推向错误写法。
  const SENTINEL = '\u0000'
  const masked = String(skeleton).normalize('NFKC').replace(PLACEHOLDER, SENTINEL)
  const bare = []
  for (const m of masked.matchAll(BARE_NUMBER)) {
    const n = Number(m[1])
    const before = masked.slice(0, m.index)
    const after = masked.slice(m.index + m[0].length)
    // 年份豁免要**自证是年份**：`2019 年`，或括号引用 `(2019)`。
    // 光是落在 1900–2099 区间不算——`共纳入 2019 名患者` 就落在那个区间里。
    if (allowYears && !m[2] && Number.isInteger(n) && n >= 1900 && n <= 2099) {
      if (/^\s*年/.test(after)) continue
      if (/[（(]\s*$/.test(before) && /^\s*[）)]/.test(after)) continue
    }
    // 「2019 年」里的 `年` 会被吃进 m[2]，那也是年份，同样放过
    if (allowYears && m[2] === '年' && Number.isInteger(n) && n >= 1900 && n <= 2099) continue
    // 序号豁免要**带序号前缀**：`第 3 节` / `Table 2`。
    // 原规则是「≤20 的无单位整数一律放行」，于是 `18 人死亡` 免检。
    if (!m[2] && Number.isInteger(n) && ORDINAL_PREFIX.test(before.replace(/\s+$/, ""))) continue
    // 标识符豁免要**自证是标识符**：数字长在一个名字里，而不是独立成数。
    // 〔留出集 H-8 抓到的〕生物标志物 `CA 19-9` 里的 `19` 与 `9` 被判成两个裸数字，
    // 于是「CA 19-9 的合并均差为 {{claim}} U/L」这句**根本写不出来**。
    // 这与 E-3 是同一类错误：一条把正确写法也拦掉的规则，会把人推向错误写法。
    //
    // 判据与其余两条豁免同构 —— **自证身份，不靠数值区间猜**：
    //   ① 数字与字母**相连无空格**：`p53` `IL-6` `COVID-19` `H3K27`
    //   ② 全大写缩写 + 空格 + 带连字符的数字串：`CA 19-9` `HbA 1c`
    // 单独一个数不满足任何一条，仍然判红（`共 19 例` 不会被豁免）。
    if (!m[2]) {
      const tail = before.replace(/\s+$/, '')
      // `p53`（字母紧邻）与 `IL-6` `COVID-19`（字母 + 连字符）都是标识符形态
      const glued = /[A-Za-z]$/.test(before) || /[A-Za-z]-$/.test(before)
      const hyphenId = /^-\d/.test(after) || /\d-$/.test(before)              // 数字串内部的连字符
      const abbrev = /\b[A-Z]{2,6}$/.test(tail) && /^-\d/.test(after)         // CA 19-9 形态
      if (glued || abbrev || (hyphenId && /[A-Za-z]/.test(tail.slice(-8)))) continue
    }
    bare.push(m[0].trim())
  }
  for (const re of [SCI_NUMBER, ROMAN_NUMBER, CN_NUMBER, CN_PERCENT]) {
    for (const m of masked.matchAll(re)) {
      // 紧跟在占位符之后 = 量纲后缀,数字已经由占位符带着 status 出场了
      if (/\u0000\s*$/.test(masked.slice(0, m.index))) continue
      bare.push(m[0].trim())
    }
  }
  if (bare.length) {
    return { ok: false, denial:
      `骨架里有 ${bare.length} 个裸数字：${bare.slice(0, 6).join('、')}。` +
      'W-10：作者 agent 不写数字，正文数字一律写成占位符。' +
      '裸数字绕过整条证据链——读者看到的数字与任何 claim 无关，更没有 status。' }
  }

  // ② 渲染：每个占位符必带 status 标记
  const used = [], missing = []
  const prose = String(skeleton).replace(PLACEHOLDER, (_, id, field) => {
    const rec = statusById.get(id)
    if (!rec) { missing.push(`${id}（claim 不存在）`); return '' }
    if (!(field in rec)) { missing.push(`${id}.${field}（字段不存在）`); return '' }
    used.push(`${id}.${field}`)
    const mark = STATUS_MARK[rec.status] ?? `?${rec.status}`
    // 名义来源数与独立簇数必须并排展示（§5.5 R-I6）
    const cl = (rec.independent_cluster_count !== undefined && rec.nominal_source_count !== undefined)
      ? `，来源 ${rec.nominal_source_count}/独立簇 ${rec.independent_cluster_count}` : ''
    return `${rec[field]}〔${mark}${cl}〕`
  })
  if (missing.length) return { ok: false, denial: `占位符指向不存在的东西：${missing.join('、')}` }
  if (!used.length && /\d/.test(skeleton)) {
    return { ok: false, denial: '骨架里有数字但没有任何占位符 —— 不可能是合规的成稿' }
  }
  return { ok: true, prose, used }
}
