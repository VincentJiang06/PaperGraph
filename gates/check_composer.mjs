#!/usr/bin/env node
/**
 * 组稿器门（GC-0）—— 产品诚实性的最后一道闸。
 *
 * 前面所有门都作用在 claim 上，而读者读的是**成稿**。
 * 作者 agent 若能在正文里直接敲数字，整条证据链就在最后一步被绕过。
 * 因此本门的核心红样本是「作者直接敲了一个数字」。
 */
import { fileURLToPath } from 'node:url'
import { join } from 'node:path'
const rootArg = process.argv.indexOf('--root')
const ROOT = rootArg > -1 ? process.argv[rootArg + 1] : fileURLToPath(new URL('..', import.meta.url))
const { compose } = await import(join(ROOT, 'src/composer.mjs'))

const ST = new Map([
  ['c1', { status: 'verified', value: '92%', nominal_source_count: 2, independent_cluster_count: 2 }],
  ['c2', { status: 'unverified', value: '11 家媒体', nominal_source_count: 11, independent_cluster_count: 1 }],
  ['c3', { status: 'contested', value: '3.2 倍', nominal_source_count: 1, independent_cluster_count: 1 }],
])

// [id, 骨架, 期望 ok, 说明]
const CASES = [
  ['W-1', '该方法达到 {{claim:c1.value}}。', true, '合规：数字走占位符'],
  ['W-2', '该方法达到 92% 的准确率。', false, '**作者直接敲数字** —— 绕过整条证据链'],
  ['W-3', '加速比为 3.2 倍。', false, '带单位的裸数字'],
  ['W-4', '见 {{claim:c9.value}}。', false, '占位符指向不存在的 claim'],
  ['W-5', '{{claim:c1.nonexistent_field}}', false, '占位符指向不存在的字段'],
  ['W-6', '2024 年的工作达到 {{claim:c1.value}}。', true, '年份是叙述成分，放行'],
  ['W-7', '第 3 节讨论 {{claim:c1.value}}。', true, '小序号是叙述成分，放行'],
  ['W-8', '本节不含任何数字。', true, '纯叙述'],
  ['W-9', '共有 11 家媒体报道。', false, '把 claim 的数字抄进正文（最隐蔽的一种）'],
  // ── S3 自攻补入（SA-4）：初版只认阿拉伯数字 ────────────────────────
  ['W-10', '该方法达到九十二个百分点。', false, '**中文数字**绕过（初版放行）'],
  ['W-11', '该方法达到 ９２％ 。', false, '**全角数字**绕过（初版放行，NFKC 前不可见）'],
  ['W-12', '共有十一篇论文报道。', false, '中文数字 + 量词'],
  ['W-13', '第三节讨论 {{claim:c1.value}}。', true, '中文小序号是叙述成分，放行（防过修）'],

  // ── R6-07 · 两条区间豁免被换成「自证身份」后的两侧标定 ────────────────
  // 攻击者当场放行的清单里，最要命的三条不是绕过技巧，是**最普通的学术句子**，
  // 而且全是承重数据：样本量、死亡数。旧规则按数值区间猜身份，于是
  // 「共纳入 2019 名患者」因为落在 1900–2099 里而免检。
  ['C-14', '共纳入 2019 名患者。', false, 'R6-07：落在年份区间里的样本量'],
  ['C-15', '死亡 1987 例。', false, 'R6-07：落在年份区间里的死亡数'],
  ['C-16', '18 人死亡。', false, 'R6-07：≤20 的整数曾无条件免检'],
  ['C-17', '参数量 9.2e10。', false, 'R6-07：科学计数法整串逃逸'],
  ['C-18', '准确率 XCII%。', false, 'R6-07：罗马数字'],
  ['C-19', '百分之九十二的样本。', false, 'R6-07：数词在后的中文百分比'],
  ['C-20', '四千五百二十三名患者入组。', false, 'R6-07：中文数字 + 旧单位表没收的「名」'],
  // 绿控：豁免必须仍然成立，否则修复过修 —— 一个把年份和章节号也拦下的组稿器
  // 会逼作者把它们也写成占位符，那是把 W-10 变成噪音
  ['C-21', '2019 年的研究显示 {{claim:c1.value}}。', true, '绿控：年份自证（带「年」）'],
  ['C-22', 'Smith (2019) 报告 {{claim:c1.value}}。', true, '绿控：括号引用形态'],
  ['C-23', '第 3 节讨论了 {{claim:c1.value}}。', true, '绿控：序号自证（带「第」）'],
  ['C-24', 'Table 2 列出 {{claim:c1.value}}。', true, '绿控：Table 前缀'],
  ['C-25', '万一失败，见 {{claim:c1.value}}。', true, '绿控：「万一」是成语不是数字'],
]

let failed = 0
console.log('组稿器门\n')
console.log(`${'用例'.padEnd(6)} ${'实测'.padEnd(6)} ${'期望'.padEnd(6)} 说明`)
console.log('-'.repeat(72))
for (const [id, sk, want, desc] of CASES) {
  const r = compose(sk, ST)
  const ok = r.ok === want
  if (!ok) failed++
  console.log(`${id.padEnd(6)} ${(r.ok ? 'ok' : 'deny').padEnd(6)} ${(want ? 'ok' : 'deny').padEnd(6)} ${desc}${ok ? '' : '   ← 偏离'}`)
}

// 渲染必须带 status 标记 + 名义/独立簇并排（§5.5 R-I6）
const out = compose('{{claim:c2.value}}', ST)
console.log()
if (!/未验证/.test(out.prose)) { failed++; console.log('FAIL  渲染没有带 status 标记') }
if (!/来源 11\/独立簇 1/.test(out.prose)) {
  failed++
  console.log('FAIL  名义来源数与独立簇数没有并排展示（§5.5 R-I6）—— 只给读者看其中一个是误导')
} else {
  console.log(`渲染样例：${out.prose}`)
}
// 六个状态值都要有可读标记，不能出现 ?xxx
for (const s of ['verified', 'attributed', 'estimated', 'contested', 'unverified', 'not_covered']) {
  const p = compose('{{claim:x.value}}', new Map([['x', { status: s, value: 'V' }]])).prose
  if (/\?/.test(p)) { failed++; console.log(`FAIL  状态 ${s} 没有可读标记`) }
}

console.log()
if (failed) { console.log(`FAIL  ${failed} 条偏离`); process.exit(1) }
const denyN = CASES.filter(c => c[2] === false).length
console.log(`PASS  组稿器 ${CASES.length} 条（含 ${denyN} 条 deny）全部符合；渲染带 status 且名义/独立簇并排`)
