# 外部标定测试 — 三个真实话题

**这是本项目第一份不是自己出的题。** 此前所有标定集都由作者编写
（03 §5A.0 自认 `power_basis = unmeasured`），这一份的六份快照全部来自真实文献
的逐字抓取，payload 全部是文献里真实存在、或真实被人引用的数字。

## 语料

| 键 | 文献 | 获取方式 | G-GRADE 判定 |
|---|---|---|---|
| nature | Jumper et al., *Nature* 596 (2021), AlphaFold | PDF → pymupdf 抽取 | G4（全文，无稳定锚） |
| proteins | Jumper et al., *Proteins* 89 (2021), CASP14 | Europe PMC 摘要 | G3（仅摘要） |
| osc | Open Science Collaboration, *Science* 349 (2015) | Europe PMC 摘要 | G3 |
| dimasi | DiMasi et al., *J Health Econ* 47 (2016) | Europe PMC 摘要 | G3 |
| prasad | Prasad & Mailankody, *JAMA Intern Med* (2017) | Europe PMC 摘要 | G3 |
| wouters | Wouters et al., *JAMA* 323 (2020) | Europe PMC 摘要 | G3 |

引语与锚句**由脚本从快照里切出**（`sentenceWith`），不手打——手打的「逐字引语」
是我们自己造的假证据，S3 已经在这上面栽过一次。

## 三条线各压什么

- **T1 AlphaFold CASP14 精度** — 引语属实性。全网把 `92.4` 归给 Nature 2021，
  而该数字在 Nature 全文里 **0 次命中**（`grep -c '92.4'` = 0）；它出自 *Proteins* 那篇。
- **T2 心理学可复现率** — metric_frame。OSC 2015 一篇给了 36% / 47% / 39% / 68%
  四个都合法的「复现率」，取哪个取决于判据。
- **T3 新药研发成本** — 合成共识 + 真实反证。DiMasi 自己给了三个数
  （$1395M / $2558M / $2870M），世上引用的是中间那个并四舍五入成 “$2.6 billion”；
  Prasad ($648.0M) 与 Wouters ($985.3M) 是真实的反向估计。

## 它找到了什么（三条产品缺陷，均已修 + 配回归）

- **E-1** `evidence_grade` 归门代码所有，却**没有任何门在算它**——从抓取记录读，
  缺省 `?? 'G5'`（最高档）。真实抓取工具根本不设这个字段 ⇒ 真实链路上恒为 G5
  ⇒ §3.4 的天花板恒为 ST-V。R6-02 的同族形态，R6 没查到这一个。
  → 新建 `src/gates/g-grade.mjs`，按 §3.3 从 `content_kind` + `locator` 算，未声明按 G3。
- **E-2** 多条证据取 `Math.max`（最好那条），而同一行注释写着「取全体**最坏**值」。
  代码与自己的注释相反。→ 改为 `Math.min`，并配回归。
- **E-3** 组稿器把 `{{claim:c1.cost}} 十亿美元` 里的「十亿美元」判成裸数字——
  那是**单位**。结果是最普通的中文量纲写法写不出来，作者会转去写阿拉伯数字，
  正好绕开 W-10。**一条把正确写法也拦掉的规则，会把人推向错误写法。**

## 第二轮：修完之后

首轮 13 条里有 4 条判错（2 假阴 / 2 假阳）。全部修完并配了会红的回归，
现在 **13/13 与人工判断一致**：

| | 首轮 | 现在 |
|---|---|---|
| T2-1 `36` vs 原文 `Thirty-six` | unverified（假阴） | attributed |
| T2-2 `replication` vs 原文 `replicated` | unverified（假阴） | attributed |
| T2-4 「只有 36% 的心理学研究可复现」 | attributed（假阳） | **unverified** |
| T3-3 三篇「独立」来源 | attributed，独立簇 3（假阳） | **unverified，来源 3/独立簇 1** |
| T3-4 否定在下一句 | attributed（假阳） | **unverified** |

四道新门/改动，每条都由这份外部语料逼出来：

- **G-L1-b 改写**（`src/gates/g-containment.mjs`）——按 slot_type 分档放松：
  value/comparator 认**数值等价**（`36` ≡ `Thirty-six` ≡ `三十六`），
  entity 认**同词干**，metric/sample **一律逐字**。
  放松是 fail-open 方向，所以负例侧 11 条比正例侧 6 条更多；
  其中 4 条守的是**子串陷阱**——归一化后锚句含 `36`，载荷 `3` 曾经能蒙混过关。
- **跨句极性参与判定**（`g-polarity.mjs`）——下一句以转折词开头且含否定时判 fail。
  非转折句首的否定仍只报告（无关否定的假阳侧）。
  更要紧的是：`followingSentence` 改成**由门从快照算**，
  原先它由抓取记录递进来 = 由生产方控制，递个空串就能让否定消失。
- **每条证据都要自证支持**（`gate-ctx.mjs`）——原实现只检查 `evidence[0]` 的锚点与极性，
  其余证据一次都没被检查过却照样计入独立簇。
  现在锚句不含载荷、或锚句被否定的证据不计入簇，但**仍留在名义来源数里**——
  「引了三篇只有一篇支持」不能看起来跟「只引了一篇」一样。
- **G-FRAME 同源竞争读数**（`src/gates/g-frame.mjs`）——第一道不看转录、只看**框架**的门。
  原文在同一句里用分号并列多个同量纲读数时，claim 必须声明 `discriminator`：
  一段逐字取自锚句、且不出现在任何兄弟读数里的文字。
  它成为 K-L-T 的**第三个合取项**（§2.2.1 与 W-04 同步改了）。

  这道门的边界写在它自己的源码头注里：**没有分号枚举指纹的框架塌陷，它看不见。**
  「36% 的研究可复现」若写在一篇只给了 36% 一个数的综述里，这里全绿。

## 结果

`RESULTS.txt` 是逐条产出。`node tests/external/cases.mjs` 可重跑。

**13 条 claim，0 条达到 `verified`。** 最高只到 `attributed`——因为六份真实文献
没有一份给得出 G5（需要 JATS/TEI 结构化锚，那要真正的 API 集成，我们没有）。
