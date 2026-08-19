/**
 * G-GRADE —— `evidence_grade` 的判定（01-CONTRACTS §3.3 / §3.4）。
 *
 * 〔来历:外部标定测试 E-1 / E-2〕
 * 用三个真实话题的六份真实文献跑链路时发现两件事:
 *
 *   E-1  `evidence_grade` 归 W-04 门代码所有(FIELD_OWNER 里写着),
 *        但**没有任何门在算它**——`buildGateCtx` 直接从抓取记录里读,
 *        缺省 `?? 'G5'`。而 G5 是**最高档**,§3.4 给它的上限就是 ST-V。
 *        真实抓取工具 `academic_fetch` 根本不设这个字段 ⇒ 真实链路上恒为 G5
 *        ⇒ 天花板恒为 verified。这是 R6-02 的同族形态,R6 没查到这一个。
 *
 *   E-2  多条证据取 `Math.max`,而同一行的注释写着「取全体**最坏**值」。
 *        代码与自己的注释相反:一条 G1 垃圾证据 + 一条 G5 = G5。
 *
 * 本门按 §3.3 的定义**从抓取记录算**,并且 fail-closed:
 * 说不清自己抓到了什么的记录,拿不到高档位。
 *
 *   G0  没有快照
 *   G1  有快照,但快照里**没有**该 claim 需要的那段(引语不在正文里)
 *   G2  只有题录(声明 content_kind=metadata)
 *   G3  只有标题+摘要,**或未声明 content_kind**——
 *       没说自己是全文,就不能按全文记(这一条是 fail-closed 的落点)
 *   G4  全文快照,但定位符不是稳定锚
 *   G5  全文快照 + 稳定可复核定位符，**且回指往返成立**
 *
 * 〔不宣称的部分〕`content_kind` 由抓取执行器(W-02)声明,本门不验证它说的是真话。
 * 要验证它,需要能独立判断一段字节是全文还是摘要——那不是 GC-0 能做的事。
 * 所以这条链上仍有一个自报环节,只是它的**缺省方向**被扳成了保守的那一侧。
 */
export const GRADE_VERSION = 'g-grade-2026-08-19'

/** 稳定锚:结构化定位符,可独立寻址复核 */
const STRUCTURED_LOCATOR = /^(jats:|tei:|latex:|html:#|xpath:|sec:|§)/i

/**
 * G5 的判据是**可独立重新寻址**，不是「长得像结构化定位符」。
 *
 * 〔真正的 API 集成之后收紧〕原实现只做正则匹配：一个写着 `jats:Sec9/Par99`
 * 的字段——哪怕那个锚在文档里根本不存在——照样拿到 G5。
 * 那等于把 §3.4 里 G5 的依据（「锚点使独立复核寻址成为可能」）
 * 降级成一句自陈。
 *
 * 现在要求抓取器提供 `roundtrip_verified`：用 locator 反查文档，
 * 解析出的段落必须逐字包含该引语（`verifyRoundTrip()` 做的事）。
 * **缺这个字段就够不上 G5** —— 与 content_kind 同一条 fail-closed 纪律：
 * 说不清自己能不能被复核的证据，拿不到最高档。
 *
 * 实测支撑：AlphaFold 那篇 Nature 的 JATS（PMC8371605）里，
 * 51 个正文段落有 50 个带 id、1 个不带——**G5 是逐段的，不是逐文档的**。
 */
const roundTripOk = f => f.roundtrip_verified === true

export const GRADE_ORDER = Object.freeze(['G0', 'G1', 'G2', 'G3', 'G4', 'G5'])

/** 单条证据的等级 */
export function gradeOfEvidence(f = {}) {
  const body = f.body == null ? '' : String(f.body)
  if (!body) return 'G0'
  const quote = String(f.quote ?? '')
  // 引语不在快照里 = 快照不含 claim 所需段落 = §3.3 的 G1 定义
  if (quote && !body.includes(quote)) return 'G1'
  const kind = f.content_kind
  if (kind === 'metadata') return 'G2'
  if (kind === 'abstract') return 'G3'
  if (kind !== 'fulltext') return 'G3'          // 未声明 ⇒ 不得按全文记
  if (!STRUCTURED_LOCATOR.test(String(f.locator ?? ''))) return 'G4'
  return roundTripOk(f) ? 'G5' : 'G4'
}

/**
 * 一条 claim 的等级 = 其全部承重证据里**最差**的那一条。
 * 〔E-2〕这里用 min 不是 max。一条 claim 的可复核性由最弱的那一环决定——
 * 混进一条 G1,整条 claim 就有一段无法独立复核,而那正是 §3.4 要拦的东西。
 */
export function gradeOfClaim(evidence = []) {
  if (!evidence.length) return 'G0'
  const idx = evidence.map(e => Math.max(0, GRADE_ORDER.indexOf(gradeOfEvidence(e.fetch ?? e))))
  return GRADE_ORDER[Math.min(...idx)]
}
