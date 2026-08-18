/**
 * G-RERUN —— K-D（数据分析类）的重跑门。
 *
 * 〔为什么它必须真的执行〕
 * R6-02 的原话：`rerun_gate_passed: c.__rerun ?? true`。也就是说 K-D 这条
 * 「产品最强的一条 ST-V 通道」，它的把关谓词在出厂产品里是一个 fail-open 默认值。
 * `KIND_GATED_BY['K-D'] = ['rerun_gate_passed','question_frozen']` 这条门断言
 * 因此在真实链路上**为空**：它只检查「谓词存在、是门字段、被 S 读」，
 * 唯独不检查**有没有门在算它**。
 *
 * 一个接受自报值的重跑门，不是门，是纪律。所以本门**自己执行脚本**：
 * 从 CAS 取出脚本对象（内容寻址 ⇒ 被钉死、可审计），跑两次，比对输出摘要。
 * producer 能提供的只有「哪个脚本、什么参数」，判定权在门这一侧。
 *
 * 〔信任边界，必须写明〕本门执行的是 producer 提供的代码。它跑在同一个
 * OS 用户下，有超时与 cwd 隔离，但**没有沙箱**。这不是可以被忽略的细节：
 * 把它写在这里，是因为「门执行不可信代码」是一个真实的攻击面，
 * 而假装它不存在比它本身更危险。脚本对象在 CAS 里 ⇒ 事后可逐字节复核。
 *
 * 〔它证明什么、不证明什么〕
 *   证明：这段脚本在本机跑两次给出逐字节相同的输出。
 *   不证明：这段脚本做的是它自称的那件分析。
 * 后者不可机器判定，因此 §7.2 从不宣称 K-D 的 ST-V 等于「结论正确」。
 */
import { execFileSync } from 'node:child_process'
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { getObject, sha256 } from '../cas.mjs'

export const RERUN_VERSION = 'g-rerun-2026-08-18'
const RUNS = 2                 // 两次一致即判定确定性；更多次只是线性加成本
const TIMEOUT_MS = 10_000

/**
 * @param {string} root  run 根目录（CAS 所在）
 * @param {object} spec  { script_sha256, argv?, expected_output_sha256? }
 * @returns {{pass:boolean, reasons:string[], params:object}}
 */
export function rerunGate(root, spec) {
  const reasons = []
  const params = { rerun_version: RERUN_VERSION, runs: RUNS }

  // fail-closed 的第一层：没有重跑规格 = 没重跑过。
  // 〔R6-02 的教训〕缺省值必须站在「没做」那一侧，而不是「做了」那一侧。
  if (!spec || typeof spec.script_sha256 !== 'string') {
    return { pass: false, reasons: ['没有重跑规格（script_sha256 缺失）—— 未做重跑'], params }
  }

  // getObject **返回 null**（不抛）表示对象不在。漏掉这条 null 会让下一行
  // 的 sha256(null) 抛 TypeError，把「脚本不在 CAS 里」这条判定变成一次崩溃——
  // 而崩溃在只看退出码的调用方眼里跟「拦截成功」长得一模一样（R3 栽过一次）。
  let script = null
  try { script = getObject(root, spec.script_sha256) } catch { /* 下面统一判 */ }
  if (script === null || script === undefined) {
    return { pass: false, reasons: [`脚本对象不在 CAS 里：${spec.script_sha256.slice(0, 12)}…`], params }
  }

  // 脚本必须**确实**是它自称的那份字节。CAS 是内容寻址的，这一步在
  // getObject 内部已经成立；此处再核一次，是因为「地址即内容」这件事
  // 一旦哪天被改成 mtime 索引就会静默失守。
  if (sha256(script) !== spec.script_sha256) {
    return { pass: false, reasons: ['CAS 取出的字节与地址不符'], params }
  }

  const dir = mkdtempSync(join(tmpdir(), 'g-rerun-'))
  const file = join(dir, 'analysis.mjs')
  writeFileSync(file, script)
  const digests = []
  try {
    for (let i = 0; i < RUNS; i++) {
      let out
      try {
        out = execFileSync(process.execPath, ['--no-addons', file, ...(spec.argv ?? [])], {
          cwd: dir, timeout: TIMEOUT_MS, encoding: 'buffer',
          env: { PATH: process.env.PATH ?? '', NODE_OPTIONS: '' },
        })
      } catch (e) {
        return { pass: false, reasons: [`第 ${i + 1} 次执行失败：${String(e.message).split('\n')[0]}`], params }
      }
      digests.push(sha256(out))
    }
  } finally {
    rmSync(dir, { recursive: true, force: true })
  }

  params.output_sha256 = digests
  if (new Set(digests).size !== 1) {
    reasons.push(`${RUNS} 次输出摘要不一致：${digests.map(d => d.slice(0, 8)).join(' / ')} —— 分析不确定`)
    return { pass: false, reasons, params }
  }
  // 若 producer 声明了期望输出，则它必须对上。声明了却对不上比没声明更糟：
  // 那是**记录与实际分叉**，正是本项目全部门存在的理由。
  if (spec.expected_output_sha256 && spec.expected_output_sha256 !== digests[0]) {
    reasons.push(`输出摘要与提交声明不符：实测 ${digests[0].slice(0, 12)}… 声明 ${String(spec.expected_output_sha256).slice(0, 12)}…`)
    return { pass: false, reasons, params }
  }
  return { pass: true, reasons: [], params }
}
