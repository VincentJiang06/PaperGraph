# 外部调研 v2 · 维度：文献污染筛查与取证元科学

> 核心命题：**"有出处"不等于"可信"。当出处本身是造假论文、掠夺性期刊或被劫持刊名时，`verified-by-source` 是一个负价值的标签——它把污染洗白成证据。**
>
> 调研时间：2026-08-17（所有 live API 数字均为当日实测，脚本可复跑）
> 方法：先检索（12 次 WebSearch，配额用尽后转为直接抓一手），再逐条抓一手页面 / 直接打 API / 下载原始数据集自算。凡本文件出现的载荷数字，均在"载荷数字核验表"里带口径三元组与状态。

---

## 结论摘要

1. **免费且确定性的污染门只有一层，但这一层很扎实。** Retraction Watch 全库以 CSV 形式公开托管在 Crossref 的 GitLab（每个工作日更新，无需 key、无需注册、无 LICENSE 文件但 Crossref 明示"metadata 可自由复用、请求引用"）。2026-08-17 实测全库 71,799 行、其中 `RetractionNature = Retraction` 66,287 行、去重原文 DOI 62,708 个。**这是本项目唯一可以做成 hard gate（红灯即拦截）的污染数据源。**

2. **不要用 OpenAlex 的 `is_retracted` 当门。** 2026-08-17 实测 OpenAlex `is_retracted:true` = 134,175，约为 RW 撤稿条数的两倍。我随机抽样 200 条做了归因：只有 **81 条（40.5%）**是 RW 记录里的"被撤原文 DOI"；**69 条（34.5%）**其实是撤稿公告本身（匹配 RW 的 `RetractionDOI`）；另有 42 条标题形如 "Retraction: …/Correction to …" 但 RW 无记录。也就是说 `is_retracted` 是"被撤论文 ∪ 撤稿公告 ∪ 部分更正公告"的并集，直接当布尔门会把**撤稿公告本身判成造假文献**。这类结构性缺陷 Hauschke & Nazarovets 已在论文里点名（单一布尔字段坍缩了 Crossref 的分层语义）。

3. **纯代码取证统计（GRIM/GRIMMER/DEBIT/SPRITE/statcheck）能装进 DSH，但它们的适用条件极窄，且"窄"是可计算的。** GRIM 的检出功率有闭式解：`power = 1 − N·items / 10^d`（`d` = 报告小数位）。我用 20,000 次/点的蒙特卡洛验证了这个式子（N=28 实测 0.718 vs 理论 0.720；N≥100 且 d=2 时功率恒为 0）。**推论：GRIM 对 N≥100 的两位小数均值完全无效；对多题项量表均值（items>1）几乎立刻失效。** 一个不带 N/items/小数位判定的 GRIM 门，会在大样本论文上给出"全部通过"的假安全感。

4. **statcheck 的 96.2%–99.9% 准确率是一个被严重压缩过口径的数字。** 一手（Nuijten 等的 validity 预印本 PDF）里那个区间是在 **48 篇文章、1,120 条人工编码 NHST 结果**上算的，且只统计 **t/F/χ²、p<.05、完整 APA 格式**的结果，并且**只在"人工与 statcheck 都抽到"的交集**上计算敏感度/特异度。真正的瓶颈在抽取端：statcheck 只抽到了 1,120 条中的 **684/685 条（61.1%–61.2%）**。另一份 2024 年的现场数据更刺眼：20 篇被标记文章的 113 条 flag 里，**14 条是 statcheck 抽取错误、64 条（57%）源于统计校正**——对"造假筛查"这个用途来说，这批 flag 里近七成不是造假信号。

5. **凡是"概率性 + 商业"的层（Papermill Alarm / STM Integrity Hub / Cabells / Signals / ImageTwin），对本项目都不可用作门，只能作为"人工复核提示"。** 它们要么只对出版商开放（STM Integrity Hub：40 家出版商、每月筛 12.5 万篇），要么订阅制无公开 API（Cabells：2026-01-30 计 20,274 本期刊），要么有 API 但不公布准确率（Papermill Alarm）。**没有一家公布过带口径的 false positive rate。**

6. **"不可编程访问"的清单同样是产品设计的一部分**：PubPeer 无公开授权 API（`/v3/publications` POST 端点实测可用，但 robots.txt 明确 `ai-train=no` 且 Disallow ClaudeBot——能访问 ≠ 被授权）；PPS 的**指纹词典可公开下载 CSV**（tortured 8,282 条已实测下载），但**被标记论文列表没有导出端点**；DOAJ 自 2026-03-17 起把 OAI-PMH / Public Data Dump / Journal CSV 的"当前版本"变成付费，免费版滞后一个月；Cabells 无公开 API。

7. **给本项目的一句话结论**：把污染筛查做成**三层分级门 + 一个显式的"未覆盖"状态**，而不是一个布尔标签。T0（确定性免费）能给红/绿；T1（纯代码取证）只能在**适用条件成立时**给黄，且必须把适用条件本身写进证据；T2（外部概率性）永远只能给"待人工复核"，绝不参与自动判定。

---

## 系统与机制逐条（含 URL）

### A. 撤稿 / 关注声明（确定性、免费、可复跑）

**A1. Retraction Watch database（Crossref 托管，CSV 全量）**
- URL：https://gitlab.com/crossref/retraction-watch-data ；文档 https://www.crossref.org/documentation/retrieve-metadata/retraction-watch/
- 访问方式：`git clone` 或直接 `curl https://gitlab.com/crossref/retraction-watch-data/-/raw/main/retraction_watch.csv`（实测 63 MB，无鉴权、无 rate limit）。
- 更新频率：README 原文"updated every working day by Retraction Watch"；仓库 README 自带生成日期戳（本次抓取时为 `generated on 2026-08-14`），`last_activity_at` = 2026-08-14T23:00Z。**这是一个可直接当"数据新鲜度断言"的字段——DSH 的门可以用它做 freshness check。**
- 字段：`Record ID / Title / Journal / Publisher / RetractionDate / RetractionDOI / OriginalPaperDOI / OriginalPaperPubMedID / RetractionNature / Reason / Paywalled / Notes`。`Reason` 是受控词表（分号分隔），`RetractionNature ∈ {Retraction, Correction, Expression of concern, Reinstatement}`。
- 许可：**仓库内没有 LICENSE 文件**（GitLab API `license: null`）。Crossref 官方博客的表述是"While Crossref metadata is freely available to reuse without a license, if you make use of the Retraction Watch retraction metadata in a published work, we kindly request that you provide a citation to the source."（2025-01-29）。→ 结论：可自由用，**但要在产物里署源**；不要在文档里写"CC0"，那是没有一手依据的转述。
- 一手的覆盖度自述（README 原文）："Some other update types, such as expressions of concern and corrections, are also included in the data, but these are not as comprehensive as retractions." → **EoC/Correction 的覆盖不完整，不能拿 RW 的 EoC 缺失当"该文没有 EoC"的证据。**

**A2. Crossref REST API（DOI 级实时查询）**
- 端点：`https://api.crossref.org/works?filter=update-type:retraction`；单 DOI 查 `https://api.crossref.org/works/{doi}` 看 `update-to` 数组。
- `update-to` 每项含 `{type, DOI, source, label, updated}`，`source ∈ {publisher, retraction-watch}`，RW 来源另带 `record-id`。**同一撤稿可能同时来自两个 source，必须去重**（我抽的 400 条里 publisher 258 + retraction-watch 281，和 > 400）。
- 限速：响应头 `x-rate-limit-limit: 3`、`x-rate-limit-interval: 1s`，`x-api-pool: polite-array`（带 mailto 进 polite pool）。→ DSH 的并发扇出必须给 Crossref 单独设 ≤3 rps 的令牌桶，否则会被降级。
- 文档：https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-filters/ ；教程 https://crossref.gitlab.io/tutorials/get-rw-metadata/

**A3. PubMed E-utilities（生物医学子集，免费、无 key 可低速用）**
- `esearch.fcgi?db=pubmed&term="Retracted Publication"[PT]` → 33,934（2026-08-17）；`"Expression of Concern"[PT]` → 3,824。
- 定位：**只是交叉校验层**。它的覆盖显著小于 RW（RW 66,287 撤稿记录），因为只覆盖 PubMed 索引的生物医学文献。可用来抓 RW 漏收的少量条目，不能反过来当权威。

**A4. OpenAlex（覆盖最大，但语义最脏）**
- `https://api.openalex.org/works?filter=is_retracted:true` → 134,175（2026-08-17，全库 324,389,590 works）。
- 已知缺陷论文：Hauschke & Nazarovets,《(Non-)retracted academic papers in OpenAlex》，https://arxiv.org/abs/2403.13339 （J. Information Science, 2025）。原文："Despite accurate metadata sourced from Crossref database, OpenAlex consolidated this information into a single boolean field, 'is_retracted,' leading to misclassifications of papers." 并提示 2023-12-22 至 2024-03-19 期间的数据需要重取。
- 我自己的抽样复核（可复跑，见下）证明这个缺陷**在 2026-08 仍然存在**，不是历史问题。

### B. 期刊层污染（劫持刊 / 掠夺性刊 / 白名单）

**B1. Retraction Watch Hijacked Journal Checker**
- 页面：https://retractionwatch.com/the-retraction-watch-hijacked-journal-checker/
- 实际数据载体是一个 Google 表格（`docs.google.com/spreadsheets/d/1ak985WGOgGbJRJbZFanoktAN_UFeExpE`）。**`?format=csv` 导出 400；`?format=xlsx` 导出 200 可用**（实测 106 KB）。解析后 456 条数据行，表头自述 "First created: May 30, 2022; last updated July 17, 2026"。
- 列结构：`Hijacked Journal Title / URL (Hijacked) / ISSN (Hijacked) / Original journal / ISSN (Original) / URL (Original Journal)`。**同时给出被劫持域名和 ISSN，因此可以做两种确定性匹配：URL host 匹配 + ISSN 匹配。**
- 风险：这是一个**无版本号、无 API、无 ETag 契约**的第三方表格导出，随时可能变。DSH 侧必须把它 mirror 到本地 + 记录抓取日期 + 在导出失败时降级为"未覆盖"而不是"通过"。

**B2. Cabells Predatory Reports**
- 规模：截至 2026-01-30 共 20,274 本期刊（https://blog.cabells.com/2026/02/03/cabells-predatory-reports-database-hits-20000-deceptive-journals/ ）。判定用 70+ 条行为指标（v1.1 清单）。
- 访问：**订阅制，一手页面未提及任何 API 或数据导出**。→ 对本项目不可编程访问，列入"NOT accessible"。

**B3. DOAJ（白名单，不是黑名单）**
- API：`https://doaj.org/api/search/journals/*` → 2026-08-17 实测 23,320 本期刊，免费无 key。
- **2026-03-17 起的重大变化**（https://blog.doaj.org/2026/03/03/doajs-new-premium-metadata-services/ + https://www.doaj.org/docs/premium ）：OAI-PMH / Public Data Dump / Journal CSV 分裂为免费版（滞后约一个月）与付费 Premium 版（OAI-PMH 实时 / Data Dump 1 天内 / Journal CSV 1 小时内）。网站搜索、API、widgets、Atom feed 保持免费。Public Data Dump 需逐案邮件申请（https://www.doaj.org/docs/public-data-dump/ ），全量 dump 对付费用户每日生成、对所有人每月生成。有面向低收入国家与 DOAJ 支持机构的豁免。
- 定位：**DOAJ 收录 = 弱正信号；未收录 ≠ 掠夺性**（大量正规订阅制期刊本来就不在 DOAJ）。只能用作"期刊可信度加分项"，绝不能反向当门。

### C. 文本指纹筛查（PPS）

**PPS（Problematic Paper Screener），Guillaume Cabanac 等**
- 入口：https://www.irit.fr/~Guillaume.Cabanac/problematic-paper-screener/ （302 跳到 APEX 应用 https://dbrech.irit.fr/pls/apex/f?p=9999:1 ）
- 检测器（首页导航栏，2026-08-13 更新戳）：**Annulled / Concerning / Feet of Clay / Tortured / Suspect / SCIgen / Mathgen / Citejacked / Seek&Blastn / Problematic Cell Lines**，共 10 个。数据源自述为 Crossref（含 RW 库）、Dimensions API、PubMed、PubPeer。
- **关键机制**：FAQ 原文 "The Problematic Paper Screener screens the published literature that is indexed by Dimensions. It does not screen documents on demand: no upload functionnality is provided." → **PPS 不能对本项目手上的任意 PDF 做筛查**，它只筛 Dimensions 已索引的已发表文献。
- **可编程访问的边界（实测）**：
  - ✅ **指纹词典可公开下载 CSV**，URL 形如 `https://dbrech.irit.fr/pls/apex/f?p=9999:5::IR%5Btortured%5D_CSV::::`。实测全部成功：tortured 8,282 条、mathgen 5,737、sbir 500、suspect 397、scigen 257、dada 49、citejacked 39。tortured CSV 三列：`Fingerprint / Expected Text / Nb Retrieved Papers`。
  - ❌ **被标记论文列表没有导出端点**（page 3 "All Problematic Papers" 报告经 AJAX 加载，HTML 里不含 `_CSV` 链接；构造 `f?p=9999:3::CSV::::` 请求失败）。
  - ❌ 部分页面需登录（`f?p=9999:2` 是 Sign In）。
  - → **设计含义：本项目应当把 PPS 的指纹词典 mirror 下来在本地做纯代码匹配（这是可复跑的），而不是去爬 PPS 的结论页。**
- 误报态度：FAQ 里只写"administrators will review them and add the most promising ones (with low false positive rate)"——**FP 由人工策展控制，从未发布过量化 FP 率**。
- 一个必须记住的口径陷阱：tortured CSV 里 `Nb Retrieved Papers` 是**单条指纹在 Dimensions 的命中论文数**，不是"被判定有问题的论文数"。最高一条（`"surface region" AND "surface area"`，期望词 surface area）= 47,822。8,282 条命中数**求和 = 1,455,119，但这是重复计数的上界**，绝不是去重论文数（中位数只有 10；303 条 0 命中；仅 1,512 条 ≥100 命中）。

### D. 后发表评议 / 商业侦测层（概率性，不可作门）

**D1. PubPeer**
- 无公开文档化 API。浏览器插件用的端点 `POST https://pubpeer.com/v3/publications?devkey=...` 实测**可用**（我用 `devkey=test` 拿到了 `total_comments / last_commented_at / users / url`）。
- **但**：`https://pubpeer.com/robots.txt` 声明 `Content-Signal: search=yes, ai-train=no, use=reference`，并对 `ClaudeBot`、`CCBot`、`Google-Extended`、`Bytespider` 等 `Disallow: /`。→ **技术可达 ≠ 授权**。本项目若要用，必须走 PubPeer 官方申请 key 的路径，并在设计文档里明确"未获授权前该门恒为 UNAVAILABLE"。
- 学术界常用的替代路径：已发表的 PubPeer 衍生数据集（例如 2012–2021 的 189,426 条评论 / 101,272 篇被评论文献的抓取数据集）——但那是**历史快照，不是实时门**。

**D2. Clear Skies Papermill Alarm / Oversight**
- API 用法（作者 Adam Day 本人的说明文，2022-10-17 发布、2024-09-05 编辑）：https://clearskiesadam.medium.com/how-to-use-the-papermill-alarm-api-719b8b3b8253 。输入是 JSON `{"id", "title", "abstract"}`；接入方式为与出版商直签、RapidAPI 自助、或经 STM Solutions / Morressier 转售。
- **该文未给出任何准确率 / 精确率 / 验证样本**。Oversight 是其仪表盘产品（覆盖 2016 年以来的已发表文献与投稿数据）。
- 定位：黑箱概率打分，**没有可核验的口径三元组**，本项目只能当"人工复核建议"。

**D3. STM Integrity Hub**
- 只对出版商开放的协作平台，约 20 个独立检测信号（跨出版商重复投稿、参考文献核验、tortured phrases、元数据模式、AI 生成检测等），第三方接入包括 Clear Skies、Cactus、PubPeer。
- 规模（CSE Science Editor，2025-12-08，https://www.csescienceeditor.org/article/the-stm-integrity-hub/ ）：40 家出版商、每月筛查 >125,000 篇、每月拦截约 1,000 篇疑似论文工厂投稿。**未公布检出率或误报率。**
- 定位：对本项目**完全不可访问**（非出版商）。列入 "NOT accessible"。

### E. 纯代码取证统计（可完全本地实现，无外部依赖）

**E1. GRIM（Granularity-Related Inconsistency of Means）**
- 一手：Brown & Heathers, "The GRIM Test", *Social Psychological and Personality Science* 8(4):363–369, 2017, DOI 10.1177/1948550616673876（绿色 OA 记录：https://research.rug.nl/en/publications/b53973dd-be97-4d67-84c6-42bae2253240 ）。
- 适用条件（缺一不可）：① 数据为整数/离散（Likert 等）；② 已知 N；③ 已知题项数 items；④ 均值报告小数位 d 已知。
- **功率闭式解**：`power = max(0, 1 − N·items / 10^d)`。我做了 20,000 次/点的蒙特卡洛验证：N=10→0.897（理论 0.900）、N=28→0.718（0.720）、N=50→0.504（0.500）、N=90→0.099（0.100）、N=99→0.010（0.010）、N≥100→0.000。d=3 时 N=500 功率 0.500、N=999 功率 0.001。items=2 且 d=2 时 N=50 功率已经归零。
- 误报来源：题项数被误判（多题项均值被当成单题项 → 假阳性）、百分比数据的"两位免费小数"、缺失值导致的有效 N 与报告 N 不一致、四舍五入约定（scrutiny 提供 `up_or_down` / `up` / `down` / `ceiling` / `floor` 等选项）。
- 实现：R 包 `scrutiny`（`grim()` / `grim_map()` / `grim_plot()`），CRAN 0.6.1（2025-12-02，MIT）。算法本身十几行，**完全可以在 DSH 里用 TypeScript 重写，不需要 R 运行时**。

**E2. GRIMMER**
- 检验"均值 + 标准差 + N"是否互相可能（Anaya 2016；scrutiny 用 Allard 的 Analytic-GRIMMER）。三个条件：重构的平方和必须为整数；重构 SD 必须与报告值一致；平方和的奇偶性必须与整数和的奇偶性一致。**先跑 GRIM 再跑自己的三个测试，所以 GRIMMER 蕴含 GRIM。**
- **已知误报**：scrutiny 官方 vignette 明确警告 "GRIMMER's test 3 can flag consistent values as inconsistent"，并建议用 `show_reason = TRUE` 谨慎解读第三项，直到修复发布。→ **本项目若实现 GRIMMER，必须把"由 test 3 触发"的结果单独降级，不能与 test 1/2 同权。**
- 同样依赖 items 参数；items 报错会直接制造假阳性。

**E3. DEBIT（Descriptive Binary）**
- 一手：Heathers & Brown 2019, https://osf.io/5vb3u/ 。**只适用于二元（0/1）数据**，输入 mean + sample SD + N；二元数据的 SD 由 mean 与 N 唯一决定（`sd = sqrt(n/(n−1) · m(1−m))`），因此 mean/SD/N 三者只要有一组不自洽即为不一致。
- 实现：`scrutiny::debit()`（目前只支持 `formula = "mean_n"`）。
- 适用面极窄：**必须先确认变量确实是二元的**——把连续变量误当二元是 DEBIT 的主要假阳性来源，而这一步机器很难自动判断，需要从文中确认。

**E4. SPRITE**
- 一手：Heathers, Anaya, van der Zee & Brown, "Recovering data from summary statistics: SPRITE", PeerJ Preprints 26968 (2018)。原文自述为 **"a heuristic method for reconstructing plausible samples"**——**它不是一个判定检验，它产出的是"与报告统计量相容的可能数据集"**，用来让人看出分布是否荒谬（例如必须存在大量极端值）。
- 实现：R 包 `rsprite2` 0.2.1（2023-07-06，MIT），另有 MATLAB / Python / 两个 web 实现。
- **设计含义：SPRITE 永远不能自动产出 verified/unverified，它只能产出"给人看的反例图"。** 把它接进自动门是范畴错误。

**E5. statcheck**
- 实现：CRAN `statcheck` 1.5.0（2024-02-16，GPL-3）；另有 web app。做的事：从文本抽取 APA 格式的完整 NHST 结果（t / F / r / χ² / Z / Q），重算 p 值，比对报告值。
- **准确率的真实口径**（一手 PDF：Nuijten 等的 validity 研究，https://osf.io/download/tcxaj/ ）：
  - 参考集 = Wicherts et al. (2011) 人工编码的 49 篇文章（JEP:LMC + JPSP），剔除 1 篇已撤稿后为 **48 篇 / 1,120 条 NHST 结果**，且只含**完整报告的 t/F/χ² 且 p<.05** 的结果。
  - **抽取召回率只有 61.1%–61.2%**（1,120 条中抽到 684/685 条）。
  - 敏感度 85.3%–100%、特异度 96.0%–100%、总准确率 96.2%–99.9%——**这些只在"人工与 statcheck 都抽到"的交集上计算，且区间来自 3 个 CRAN 版本 × 是否开启单尾检测**。
  - 已知系统性弱点：无法处理校正后的 p 值（Bonferroni / Greenhouse-Geisser / Huynh-Feldt / Scheffé / Tukey），会把正确应用校正的结果标成不一致。
- **现场误报画像**（Nuijten & Wicherts 2024, AMPPS, https://journals.sagepub.com/doi/10.1177/25152459241258945 ）：在 20 篇文章 / 737 条 NHST 结果的人工复核子样本中，113 条被标记，其中 **14 条是 statcheck 抽取错误**（全部来自同一篇，把表格下一行的两位数字并进了 p 值），**64 条（57%）源于统计校正**。→ 对"造假筛查"用途而言，这批 flag 里约七成不是造假信号。
- 另有一份 2024 年的批评（Böschen, https://arxiv.org/abs/2408.07948 ），论点是 statcheck 死板绑定 APA 格式、稍有偏离即漏检；其测试对象是 **187 条人工构造的文本串**，不是真实论文——**引用时必须带这个口径，否则会被当成"在真实文献上的漏检率"**。
- 政策效果（同 AMPPS 2024，8,814 篇文章 / 147,784 条统计量的准实验，非随机）：引入 statcheck 的期刊不一致率 8.8%→4.3%，对照期刊 7.4%→6.4%；决策性不一致 1.2%→0.3% vs 1.0%→0.8%。作者自陈 "Our study was observational…there can be selection effects and other potential confounding factors."

### F. 撤稿生态的当前量级（用于设定预期，不用于判定）

- 我从 RW 全库自算（口径：按**撤稿公告年份**，非论文发表年份，且只数 `RetractionNature = Retraction`）：2023 年 13,217、2024 年 6,217、2025 年 5,794、2026 年（至数据快照 2026-08-14）1,203（全类型 1,221）。2023 年的峰值主要由 Hindawi 大规模清理造成——注意这是我的归因推断，本轮未核验其定量份额。
- 出版商间差异（arXiv:2602.19197，2026-02-22，基于 RW 库 1997–2026）：10 家出版商共 46,087 条撤稿，标准化撤稿率从 Elsevier 的 3.97/万篇到 Hindawi 的 320.02/万篇——**跨两个数量级**。→ 这意味着"期刊/出版商"本身就是一个高信息量的先验特征。

---

## 载荷数字核验表

| 数字 | 口径三元组（什么指标 / 什么样本或条件 / 与什么比较） | 状态 | 一手出处 |
|---|---|---|---|
| 71,799 | Retraction Watch CSV 全部数据行（含 Retraction+Correction+EoC+Reinstatement）/ 2026-08-17 下载、README 标注数据生成于 2026-08-14 / 无比较对象 | verified（自算） | https://gitlab.com/crossref/retraction-watch-data/-/raw/main/retraction_watch.csv |
| 66,287 | 其中 `RetractionNature == "Retraction"` 的行数（另 EoC 3,586 / Correction 1,502 / Reinstatement 160 / 空 264）/ 同上 / 对比"71,799 = 撤稿数"这一常见误读 | verified（自算） | 同上 |
| 62,708 | 去重后的 `OriginalPaperDOI` 数（65,589 行有非空 DOI，即 6,210 行无原文 DOI）/ 同上 / 对比"RW 记录数 = 可 DOI 匹配的被撤论文数" | verified（自算） | 同上 |
| 13,217 | **按撤稿公告年份**落在 2023 且 `Nature=Retraction` 的记录数 / RW 全库 2026-08-14 快照 / 对应媒体"2023 年逾 1 万篇撤稿"的说法 | verified（自算） | 同上 |
| 6,217 / 5,794 / 1,203 | 同口径的 2024 / 2025 / 2026（至 2026-08-14 快照）年数 / 同上 / 显示 2023 是异常峰而非新常态 | verified（自算） | 同上 |
| 3 rps（无 key）/ 10 rps（有 key） | NCBI E-utilities 官方请求速率上限 / 官方 E-utilities 指南原文 "post no more than three URL requests per second"、有 key "up to 10 requests per second by default" / 用于设定 PubMed 校验层的扇出预算 | verified | https://www.ncbi.nlm.nih.gov/books/NBK25497/ |
| 74,607 | Crossref REST API 中 `filter=update-type:retraction` 命中的 works 数（= 带撤稿类 `update-to` 的记录，含 publisher 与 retraction-watch 双来源，未去重）/ 2026-08-17 实时 / 对比 RW 的 66,287 | verified（live API） | `https://api.crossref.org/works?filter=update-type:retraction&rows=0` |
| 281 / 258 | 400 条抽样中 `update-to.source` 为 `retraction-watch` / `publisher` 的条目数（和 > 400，说明同一记录可两源并存）/ 前 2 页 ×200 条 / 说明必须去重 | verified（自测） | 同上 API |
| 3 请求/秒 | Crossref polite pool 限速（响应头 `x-rate-limit-limit: 3`, `x-rate-limit-interval: 1s`）/ 2026-08-17 带 mailto 的请求 / 用于设定 DSH 扇出上限 | verified（响应头） | `curl -D - https://api.crossref.org/works?rows=0` |
| 134,175 | OpenAlex `is_retracted:true` 的 works 数 / 2026-08-17 实时（全库 324,389,590 works）/ 约为 RW 撤稿数的 2 倍 | verified（live API） | `https://api.openalex.org/works?filter=is_retracted:true` |
| 81 / 69 / 42 / 6 / 2（n=200） | OpenAlex `is_retracted:true` 随机抽样 200 条的归因：匹配 RW `OriginalPaperDOI` 81；仅匹配 RW `RetractionDOI`（即撤稿公告本身）69；标题形如 Retraction/Correction 但 RW 无记录 42；其他未匹配 6；无 DOI 2 / `sample=200&seed=42`，RW 快照 2026-08-14 / 用于证明 `is_retracted` 不是"被撤论文"的干净集合 | verified（自测，可复跑） | OpenAlex API + RW CSV |
| 33,934 | PubMed `"Retracted Publication"[PT]` 记录数 / 2026-08-17 实时（PubMed 全库 41,020,383）/ 对比 RW 的 66,287，体现学科覆盖差 | verified（live API） | NCBI E-utilities esearch |
| 3,824 | PubMed `"Expression of Concern"[PT]` 记录数 / 同上 / 对比 RW 的 3,586 条 EoC | verified（live API） | 同上 |
| 456 | Retraction Watch Hijacked Journal Checker 的数据行数 / 从 Google 表格 xlsx 导出后解析，表头自述"last updated July 17, 2026" / 对比二手报道的"400 entries (2025-12)""450+" | verified（自测） | `https://docs.google.com/spreadsheets/d/1ak985WGOgGbJRJbZFanoktAN_UFeExpE/export?format=xlsx` |
| 8,282 | PPS tortured-phrase **指纹词典条数**（CSV 8,283 行含表头）/ 2026-08-17 下载，页面更新戳 2026-08-13 / **不是被标记论文数** | verified（自测下载） | `https://dbrech.irit.fr/pls/apex/f?p=9999:5::IR%5Btortured%5D_CSV::::` |
| 276 | PPS 当年使用的 tortured 指纹数 / **2021-10 的状态**（WCRI 2022 摘要），当时命中论文 N=1,694 / 与今天的 8,282 相差 30 倍 | verified（历史值，仍被大量二手页面当"现值"引用） | https://arxiv.org/pdf/2210.04895 |
| 47,822 | **单条**指纹 `"surface region" AND "surface area"` 在 Dimensions 的命中论文数（词典中最高的一条）/ 2026-08-17 CSV / **不是 tortured 检测器的论文总数** | corrected（一次 WebFetch 摘要曾把它读成"检测器命中论文总数"，这是本轮抓到的一个真实口径事故） | 同上 CSV |
| 1,455,119 | 8,282 条指纹命中数之**和**——重复计数上界，非去重论文数（中位数 10，303 条 0 命中，1,512 条 ≥100 命中）/ 同上 CSV / 用于说明"不能把指纹命中和当论文数" | verified（自算） | 同上 CSV |
| 257 / 5,737 / 500 / 49 / 397 / 39 | PPS 其余指纹词典条数：SCIgen / Mathgen / SBIR / Dada / Suspect / Citejacked（CSV 行数 −1）/ 2026-08-17 下载 / 证明全部可公开批量下载 | verified（自测下载） | `f?p=9999:5::IR%5B{scigen\|mathgen\|sbir\|dada\|suspect\|citejacked}%5D_CSV::::` |
| 130,000,000 / 週 | PPS 每周梳理的出版物量 / 作者本人 2025-01-29 的科普文自述 / 无独立核验 | verified（作者自述，日期敏感） | https://theconversation.com/problematic-paper-screener-trawling-for-fraud-in-the-scientific-literature-246317 |
| 764,000+ | Feet of Clay 检测器命中的"引用了撤稿文献的文章"数 / 同上文，2025-01-29 / 其中约 5,000 篇引用了 ≥5 篇撤稿文献 | verified（作者自述，已过时约 19 个月） | 同上 |
| 1.1M / 12,000 | 二手报道的 Feet of Clay 数字（"110 万篇引用约 1.2 万篇撤稿研究"）/ 与作者本人同期（2025-01）自述的 764,000 不一致 / **典型的伪独立佐证：多个二手页面转载同一篇 The Conversation** | unverified（口径冲突，未采用） | techxplore / cobbcountycourier 等转载页 |
| 19,000 | 含 ≥5 条 tortured phrase 的论文数 / 2025-01-29 作者自述 / 注意是"≥5 条"的严格子集，不是 tortured 命中总数 | verified（作者自述，日期敏感） | 同 The Conversation |
| 1,000+ | PPS 促成的撤稿数 / 2025-01-29 作者自述 / 无独立核验 | verified（作者自述） | 同上 |
| 20,274 | Cabells Predatory Reports 收录期刊数 / 截至 2026-01-30 / 对比 DOAJ 的 23,320 正面收录 | verified | https://blog.cabells.com/2026/02/03/cabells-predatory-reports-database-hits-20000-deceptive-journals/ |
| 70+ / 74 | Cabells 判定指标数：博客写"70+ criteria"；"v1.1 共 74 项行为指标"来自二手 / — / 两者不冲突但精度不同 | 70+ = verified；74 = unverified（未见一手清单页） | 同上博客 |
| 23,320 | DOAJ 收录期刊数 / 2026-08-17 API 实时 / 作为"白名单"规模参照 | verified（live API） | `https://doaj.org/api/search/journals/*?pageSize=1` |
| 2026-03-17 | DOAJ 拆分免费/付费元数据服务的生效日；免费版 OAI-PMH / Data Dump / Journal CSV 滞后约一个月，付费版分别为实时 / 1 天内 / 1 小时内 | verified | https://www.doaj.org/docs/premium ；https://blog.doaj.org/2026/03/03/doajs-new-premium-metadata-services/ |
| 40 家 / 125,000 篇每月 / ~1,000 篇每月 | STM Integrity Hub：参与出版商数 / 每月筛查稿件数 / 每月拦截疑似论文工厂投稿数；约 20 个独立检测信号 / 2025-12-08 行业刊物文章，数据源为协会自述 / 无误报率 | verified（但为自述数据） | https://www.csescienceeditor.org/article/the-stm-integrity-hub/ |
| 48 篇 / 1,120 条 | statcheck 敏感度-特异度研究的参考集规模（Wicherts et al. 2011 人工编码，JEP:LMC + JPSP，剔除 1 篇撤稿文章后）/ 只含完整 APA 报告的 t/F/χ² 且 p<.05 / 这是 96.2–99.9% 那个区间的真实分母基础 | verified（一手 PDF） | https://osf.io/download/tcxaj/ |
| 61.1%–61.2% | statcheck 的**抽取召回率**：1,120 条人工编码结果中只抽到 684（v1.0.0/1.0.1）/ 685（v1.2.2）/ 同上样本 / **准确率区间是在这 61% 的交集上算的** | verified（一手 PDF） | 同上 |
| 85.3–100% / 96.0–100% / 96.2–99.9% | statcheck 敏感度 / 特异度 / 总准确率；区间来自 3 个 CRAN 版本 × 是否启用单尾检测 / 上述 48 篇 1,120 条的交集 / 常被简写为"statcheck 准确率 ~99%" | verified（一手 PDF） | 同上 |
| 14 / 64 / 113（20 篇，737 条） | 现场复核：20 篇文章 737 条 NHST 中 113 条被 statcheck 标记；14 条为抽取错误（全部同一篇，把表格下一行数字并入 p 值），64 条（57%）源于统计校正 / 2024 年准实验研究的人工子样本 / 说明"被标记 ≠ 造假信号" | verified | https://journals.sagepub.com/doi/10.1177/25152459241258945 |
| 8.8%→4.3% vs 7.4%→6.4% | statcheck 期刊 vs 对照期刊的不一致率前后变化；决策性不一致 1.2%→0.3% vs 1.0%→0.8%；样本 8,814 篇 / 147,784 条统计量 / **准实验，非随机，作者明言存在选择效应** | verified | 同上 |
| 187 | Böschen 2024 批评 statcheck 时使用的测试对象数量 = **人工构造的文本串**，不是真实论文 / — / 引用其"漏检严重"结论时必须带这个口径 | verified | https://arxiv.org/abs/2408.07948 |
| 260 → 71 → 36 → 16 | GRIM 原论文：检查 260 篇近期实证论文 → 71 篇可做 GRIM 检验 → 36 篇至少 1 处不一致 → 16 篇多处；向 21 篇索要数据，9 篇回应，9 篇全部至少 1 处报告错误 / 心理学顶刊样本，2017 / 常被简化为"半数论文有错" | verified | DOI 10.1177/1948550616673876（OA 记录 https://research.rug.nl/en/publications/b53973dd-be97-4d67-84c6-42bae2253240 ） |
| power = 1 − N·items/10^d | GRIM 检出功率闭式解；我用 20,000 次/点蒙特卡洛验证（N=28 实测 0.718 vs 理论 0.720；N=90 实测 0.099 vs 0.100；N≥100 且 d=2 时恒为 0）/ 单题项、两位小数、随机错误均值 / 说明 GRIM 在大样本上无效 | verified（自行模拟，脚本可复跑） | 本轮自测 + scrutiny GRIM vignette |
| statcheck 1.5.0 / scrutiny 0.6.1 / rsprite2 0.2.1 | CRAN 版本与发布日：2024-02-16(GPL-3) / 2025-12-02(MIT) / 2023-07-06(MIT) / 2026-08-17 实时查询 / 说明许可证允许算法移植 | verified（live crandb） | `https://crandb.r-pkg.org/{pkg}` |
| 46,087 / 3.97 vs 320.02 | 10 家出版商共 46,087 条撤稿；标准化撤稿率 Elsevier 3.97/万篇 vs Hindawi 320.02/万篇 / 基于 RW 库 1997–2026 / 跨两个数量级 | verified（摘要） | https://arxiv.org/abs/2602.19197 （2026-02-22） |
| 14k vs 43k | 2023-09-12 Crossref 收购 RW 库时：Crossref 自有撤稿 14k、RW 库 43k / 收购当时 / 对比今天的 74,607 / 66,287 | verified | https://www.crossref.org/blog/news-crossref-and-retraction-watch |
| 无 LICENSE 文件 | RW 数据仓库 GitLab API 返回 `license: null`；Crossref 表述为"freely available to reuse without a license"+请求引用 / 2026-08-17 查询 + 2025-01-29 博客 / **反驳"RW 数据是 CC0"这一常见转述** | corrected | GitLab API + https://www.crossref.org/blog/retraction-watch-retractions-now-in-the-crossref-api/ |

---

## 对本项目的设计含义

### 1. 三层门菜单（这是本维度要交付的主结构）

| 层 | 门 | 访问方式 | 覆盖 | 误报行为 | 可否自动判定 |
|---|---|---|---|---|---|
| **T0 确定性 + 免费** | 撤稿/EoC 命中 | RW CSV 全量本地化（每工作日更新）+ Crossref `update-to` 单 DOI 实时校验 + PubMed `[PT]` 交叉校验 | 66,287 条撤稿、62,708 个去重原文 DOI；EoC 覆盖**不完整**（README 自述） | 近零假阳性（DOI 精确匹配）；**假阴性来自"尚未被 RW 收录"**，因此绿灯只能表述为"截至 {date} 无撤稿记录" | ✅ 红灯可 hard block |
| **T0 确定性 + 免费** | 劫持刊 / 期刊白名单 | Hijacked Journal Checker xlsx 导出（456 条，含 ISSN 与域名双键）；DOAJ API（23,320 刊，仅作正信号） | 劫持刊列表**极小**，只覆盖已被举报的头部案例 | ISSN/域名精确匹配，假阳性近零；**假阴性巨大** | ✅ 红灯可 hard block；绿灯**不构成**期刊可信度证明 |
| **T0 确定性 + 免费** | 指纹词典匹配（tortured / SCIgen / Mathgen / SBIR / Dada / Suspect / Citejacked） | PPS CSV dump 本地 mirror（共 15,261 条指纹），本地做全文匹配 | 只覆盖已知指纹；PPS 用 Dimensions 的邻近算子（`"A B C"~5`），本地实现需复刻 | 单条指纹命中**不等于**问题论文；PPS 自己也靠人工策展控 FP，无量化 FP 率 | ⚠️ 只能给黄灯（"命中 k 条指纹，需人工判读"） |
| **T1 纯代码取证** | statcheck（p 值一致性） | 本地重写（算法公开，CRAN 版 GPL-3——**注意：若直接移植 R 源码需遵守 GPL；从论文规格重写则不受限**） | 只覆盖**完整 APA 格式**的 t/F/r/χ²/Z/Q；真实召回约 61% | 现场子样本中 57% 的 flag 源于统计校正、12% 源于抽取错误 | ⚠️ 只能给黄灯；且必须自动降级"文中出现 Bonferroni/Greenhouse-Geisser/Huynh-Feldt/Scheffé/Tukey 关键词"的命中 |
| **T1 纯代码取证** | GRIM / GRIMMER | 本地实现（几十行；参照 scrutiny，MIT） | **仅当 N·items < 10^d 时有功率**；需要从文中确定 N、items、小数位 | items 误判 = 假阳性；GRIMMER test 3 已知会把一致值判为不一致 | ⚠️ 黄灯；**必须把 `power = 1 − N·items/10^d` 一起写进证据**，功率为 0 时输出"不适用"而非"通过" |
| **T1 纯代码取证** | DEBIT | 本地实现（`sd = sqrt(n/(n−1)·m(1−m))`） | 仅二元变量 | 把非二元变量当二元 = 假阳性，且机器难以自动确认变量类型 | ⚠️ 黄灯，且需人工/LLM 确认"该变量确为二元"这一前提 |
| **T1 纯代码取证** | SPRITE | 本地实现（rsprite2 MIT） | 需 mean/SD/N/取值上下界 | — | ❌ **不产出判定**，只产出给人看的反例分布 |
| **T2 外部概率性** | Papermill Alarm / Signals / ImageTwin 等 | RapidAPI 或商务签约；输入 title+abstract | 黑箱 | **无任何公开的 FP 口径** | ❌ 只能产出"建议人工复核"标签 |
| **T2 外部概率性** | PubPeer 评论存在性 | `/v3/publications` POST（技术可达但 robots.txt `ai-train=no` + Disallow ClaudeBot，**需先取得授权**） | 2012 至今 | 有评论 ≠ 有问题（也可能是正常学术讨论） | ❌ 只能作提示；未授权时门恒为 UNAVAILABLE |
| **不可访问** | STM Integrity Hub / Cabells Predatory Reports | 仅出版商 / 仅订阅、无 API | — | — | ❌ 在设计文档里显式列为"本项目无法覆盖" |

### 2. 状态机必须是四态，不是二态

`verified / unverified` 两态无法表达污染筛查的真实语义。建议：

- `CLEAN`：T0 全部通过，且 T0 数据快照的日期在 freshness 窗口内 → 可作为"已筛查"证据。
- `FLAGGED`：T0 红灯（撤稿 / EoC / 劫持刊 / 已知指纹强命中）→ 引用该文献的任何 claim 自动降级为 unverified，并在产物中留痕。
- `SUSPECT`：T1/T2 黄灯 → claim 仍可为 verified，但必须携带"取证统计告警"附注。
- `NOT_COVERED`：DOI 缺失、非英文文献、预印本、书籍章节、T0 数据源抓取失败 → **必须显式输出这个状态**，绝不能静默当成 CLEAN。这是本维度对"不把不确定洗成确定"这条产品原则最直接的落地。

### 3. 数据新鲜度本身要成为断言

RW 仓库 README 自带 `generated on YYYY-MM-DD`，GitLab API 有 `last_activity_at`，PPS 页面有 `Last Update` 戳，Hijacked 表格表头有 `last updated`。**每个门的输出都应携带其数据快照日期**，并在超过阈值（建议：RW > 7 天、PPS > 30 天、Hijacked > 90 天）时把结论从 `CLEAN` 降级为 `NOT_COVERED`。这正好契合"keep-if-better + 可复跑客观门"的既有范式：门的输入是一个带日期的本地快照，任何人重跑都能得到同一结论。

### 4. 并发预算要按数据源分桶

- Crossref：**≤3 rps**（响应头硬约束），带 mailto 进 polite pool。
- OpenAlex：有 `cost_usd` 字段与 mailto 礼貌池，适合大批量但**语义不可信**，只用来做候选扩召回。
- NCBI E-utilities：无 API key 时"no more than three URL requests per second"，有 key 时默认 10 rps（官方 E-utilities 指南，https://www.ncbi.nlm.nih.gov/books/NBK25497/ ）。
- **RW / PPS / Hijacked 全部是"下载一次、本地查 N 次"**——这才是 hyper-parallel 扇出时唯一不会被限速掐死的形态。**设计上应把 T0 全部做成本地索引（DOI → 撤稿状态、ISSN/域名 → 劫持状态、指纹 → 匹配器），扇出的子 agent 不打网络。**

### 5. 取证统计必须把"适用条件"和"结论"一起输出

这是本轮最重要的方法论收获：**GRIM 的功率是可计算的**（`1 − N·items/10^d`）。所以门的输出不应是 `pass/fail`，而应是：

```
{ test: "GRIM", verdict: "consistent" | "inconsistent" | "not_applicable",
  power: 0.72, N: 28, items: 1, decimals: 2,
  caveats: ["items 由文中第 3 节确认", "存在缺失值时有效 N 可能 < 28"] }
```

一个 `power: 0.00` 的 "consistent" 与一个 `power: 0.90` 的 "consistent"，证据强度差了一个数量级。把 power 丢掉，就是在制造"假安全"——和这个项目要消灭的"假 verified"是同一种病。

### 6. 反伪独立佐证的具体实现

本轮抓到一个真实案例：Feet of Clay 的数字，作者本人 2025-01-29 写的是 764,000+，而多个二手站点转载后变成"110 万篇 / 1.2 万篇撤稿研究"。这些二手站点全部是同一篇 The Conversation 的转载 → **是一个源，不是三个源**。建议在证据模型里给每条引用打 `upstream_id`（对新闻/转载类，用原始出处的 URL 或 DOI 归一），计算独立源数时按 `upstream_id` 去重。

---

## 未决与风险

1. **本轮 WebSearch 配额在第 12 次检索后耗尽**，以下方向未能核验，需下一轮补：Scopus 的 discontinued titles list、Web of Science 的 delisted journals 名单（两者是否有稳定的机器可读下载）；Scitility Argos、Signals、Morressier 的 API 与覆盖；ImageTwin / Proofig / Seek&Blastn 的准确率口径与访问方式。**在补齐前，不要在规划文档里写这些工具的任何数字。**

2. **PubPeer 的授权状态是硬风险。** `/v3/publications` 端点用任意 devkey 实测可用，但这不构成授权：robots.txt 明确 `ai-train=no`、`use=reference`，并 Disallow 了 ClaudeBot。**建议默认关闭该门，把它做成"需用户自行申请 key 后启用"的可选模块**，并在文档里写明未授权时的行为是 `NOT_COVERED` 而非静默跳过。

3. **Hijacked Journal Checker 的导出路径是脆的**（Google 表格、`format=csv` 已经 400、只有 `format=xlsx` 可用、无版本号无 ETag 契约）。必须写一个"导出失败 → 用上次 mirror + 标记 stale → 超过 90 天降级为 NOT_COVERED"的降级链，而不是让抓取失败静默变成"未命中"。

4. **PPS 的论文级结论不可批量获取**（只有指纹词典可下载）。这意味着本项目不能复用 PPS 的"哪些论文有问题"的判断，只能复用它的**指纹词典**，并且要自己实现 Dimensions 的邻近算子语义（`"A B C"~5` = A、B、C 出现在 5 词窗口内）。**本地匹配与 PPS 官方结果不会完全一致**，这个差异必须在文档中承认，不能宣称"与 PPS 一致"。

5. **T0 绿灯的语义是"截至某日无记录"，不是"干净"。** 撤稿有滞后（arXiv:2602.19197 显示各出版商撤稿延迟差异极大），RW 的 EoC/Correction 覆盖据其 README 自述不完整。任何把 T0 绿灯表述为"该文献可信"的措辞都是把假阴性洗成正面证据——**这条应写进 attacker 的必检清单**。

6. **statcheck 算法移植的许可证问题需要法务级注意**：CRAN 上的 `statcheck` 是 GPL-3。直接翻译其 R 源码到 TypeScript 会触发 GPL 传染；从论文与手册的规格独立重写则不受限。`scrutiny`（GRIM/GRIMMER/DEBIT）与 `rsprite2` 是 MIT，移植无此问题。**建议：GRIM/GRIMMER/DEBIT/SPRITE 参照 MIT 包实现；statcheck 类功能从 APA 报告规格独立实现，并在代码注释中记录这一决定。**

7. **GRIMMER test 3 的已知误报尚未在上游修复**（scrutiny 0.6.1 的 vignette 仍带该警告）。若本项目实现 GRIMMER，必须把 test 3 触发的结果单列，且不参与自动降级——否则会把正确的论文标成可疑。

8. **中文/非英语文献的污染筛查基本是空白**。RW 库以英文文献为主，PPS 依赖 Dimensions 索引，Hijacked 列表以国际刊为主。若本项目要覆盖中文文献，T0 的覆盖率会骤降，`NOT_COVERED` 会成为多数状态——**这需要在产品定位上提前承认，而不是等用户发现。**

9. **所有数字都会过期。** 本文件所有 live 数字的采集日期是 2026-08-17。RW/Crossref/OpenAlex/PubMed 的计数每天都在变；DOAJ 的免费/付费策略 2026-03 刚改过一次；PPS 指纹词典从 2021 年的 276 条涨到今天的 8,282 条。**规划文档引用本文件时必须连日期一起引用。**
