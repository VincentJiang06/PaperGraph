# 学术检索 API 与全文获取基础设施（2026 现状）

> 调研日期：**2026-08-17**（所有"实测"数字均为当日 live probe 结果）
> 方法：一手来源优先（官方 docs / 官方公告 / 仓库 LICENSE / API 响应头），blog 与二手汇总仅用于线索发现，不作为数字来源。
> 载荷数字一律记录**口径三元组**（什么指标 / 在什么样本或档位上 / 与什么比较）。

---

## 结论摘要

**1. 2026 年最大的结构性变化是 OpenAlex 从"完全免费"转为"免费数据 + 付费服务"。** 2026-02-13 起 API key 成为事实必需；计费从"调用数"改为**美元预算制**。免费账号 **$1/天**，无 key 仅 **$0.10/天**（实测 `x-ratelimit-limit-usd: 0.1`）。但关键设计红利是：**单实体 lookup（`/works/{id}`）成本为 $0，实测 `x-ratelimit-credits-used: 0`** —— 即"已知 DOI/ID 取全量元数据"这条路径**无限免费**。这一条几乎决定了本项目的检索架构。

**2. Unpaywall 已不是独立信源，它现在是 OpenAlex 数据的 legacy 格式外壳。** OpenAlex 官方明说 "Unpaywall records are served from the same OpenAlex data"，且实测返回体中 `evidence` / `updated` 字段值已literally 变成 `"deprecated"`。**用 Unpaywall 去"交叉验证" OpenAlex 的 OA 状态是典型的 false independent corroboration**，本项目的可信度引擎必须在信源图里把两者标为同一上游。

**3. 全文获取出现了一条以前不存在的捷径：OpenAlex 内容档案。** 55.0M 篇（实测 `has_content.pdf:true` → 54,999,764）缓存 PDF（~250 TB）+ ~43M 篇**已由 GROBID 解析好的 TEI XML**（~20 TB）。单篇 $0.01，免费额度下 **约 100 篇/天**。这意味着大多数情况下**不需要自建 GROBID**——直接取 `.grobid-xml` 即可，本地解析降级为 fallback 而非主路径。

**4. 超并行系统的真正瓶颈不是 token，是每 host 的 RPS，而且最紧的几个是硬 1 rps 量级。** arXiv **1 请求 / 3 秒**（≈0.33 rps，且要求单连接）、Semantic Scholar 有 key **1 rps**、OpenAlex 语义检索 **1 rps**、CORE 无注册 **5 单请求 / 10 秒**（≈0.5 rps）。**并行度必须由中央限速网关决定，不能由 subagent 数量决定**——这是本维度对架构最硬的一条约束。

**5. 全文抽取工具的许可证在 2026 年已不再是障碍，但"在线服务署名"是真实约束。** MinerU 3.1.0（2026-03-29）已从 AGPLv3 改为"MinerU Open Source License"（Apache-2.0 变体），商用门槛为 **100M MAU 或月营收 $20M**，但附加**强制署名条款**：基于 MinerU 的在线服务必须在界面或公开文档中显著标注使用了 MinerU。marker 代码 Apache-2.0、**权重**为 modified OpenRAIL-M，免费门槛 **$5M 融资/营收**（2026 现值，2025 年时为 $2M —— 已上调）。Docling 代码 MIT，最宽松。GROBID Apache-2.0，纯净。

**6. 覆盖缺口最严重的是中文。** 实测 OpenAlex `language:zh` 仅 **5,059,316 篇 / 324,389,590 篇 ≈ 1.56%**，与中国实际发文体量严重不符——知网/万方/维普收录的中文期刊基本不在其中，且这三家**均无公开 API**。用户既然要写中文课程论文，本项目必须诚实声明：**中文文献维度上，本系统的"已验证"能力显著弱于英文，且这个缺口无法用现有开放 API 补上。**

---

## 逐条发现（含 URL）

### A. OpenAlex —— 2026 年条款全面重写

**A1. 认证：2026-02-13 起 API key 成为事实必需**
OpenAlex 团队在官方用户组 2026-01-14 的公告中写明："API calls will require a key starting one month from today (Feb 13)"，无 key 者"100 credits for testing, then 409 errors"。
- https://groups.google.com/g/openalex-users/c/rI1GIAySpVQ （一手：项目方公告）

但**该公告的数字已被后续实现取代**（见 A2）。当前实际行为：无 key **不报 409，仍可用**，只是预算低 10 倍。这正是"公告 ≠ 现状"的典型，必须以 live probe 为准。

**A2. 计费：credit 制已改为美元预算制（实测口径）**
当前文档口径（https://help.openalex.org/access/pricing/ ，页面标注 Last updated **August 11, 2026**）：
- 免费：**"every account gets $1 of API usage per day for free"**，无需支付方式，**每日 UTC 午夜重置**
- Pay-as-you-go：$1 为增量预付，**购买后 3 个月过期**
- Member **$5,000/年** → **$20/天**预算（官方称等值 $7,300/年用量，省 32%）
- Member+ **$10,000/年** → **$100/天**预算（等值 $36,500/年，省 73%），含**每日全库快照 + 增量 sync**
- Partner **自 $20,000/年起** → **$200+/天**
- 页面**未出现任何促销/introductory 措辞**，按 list pricing 处理

**A3. 每类调用的单价（实测响应头，2026-08-17，全部对上官方 example-costs 表）**

| 操作 | 官方表（每 1,000 次） | 实测 `x-ratelimit-cost-usd` | 实测 `credits-used` |
|---|---|---|---|
| 单实体 `/works/{id}` | Free | **0** | **0** |
| list + filter | $0.10 | **0.0001** | 1 |
| search（关键词） | $1 | **0.001** | 10 |
| semantic search | $1 | **0.001** | 10 |
| content download（PDF/XML） | $10 | $0.01（文档值，未实测扣费） | — |

- https://help.openalex.org/access/example-costs/ （一手文档）
- 实测命令：`curl -D- "https://api.openalex.org/works/W2741809807"` 等

**推论（免费 $1/天 档下的日预算）**：10,000 次 list+filter，或 1,000 次 search，或 1,000 次语义检索，或 **100 篇全文下载**，且**单实体 lookup 不计费、不占预算**。

**A4. 硬性 RPS 与错误码**
官方 authentication 页：**100 requests per second** 是硬上限；**超日预算或超 100 rps 都返回 `429 Too Many Requests`**（注意：不是 409，也不是 403）。
- https://help.openalex.org/api/authentication/

**A5. 无 key 档位实测**
`x-ratelimit-limit-usd: 0.1` / `x-ratelimit-limit: 1000`（credits）→ **无 key = $0.10/天 = 1,000 credits/天**。文档表述"a free key gives you 10× the keyless budget"与此自洽（$0.10 × 10 = $1）。

**A6. 语义检索（新端点，2026）**
`?search.semantic=...`，底层是 **GTE Large EN（阿里达摩院）** 对**标题+摘要**做的 **1,024 维**向量。硬限制：
- 输入 **最长 2,000 字符**（超出截断）
- **每次查询最多返回 50 条**（实测 `meta.count` 恰为 50）
- **限速 1 请求/秒**
- 两个 filter 不可与之共用：`last_known_institutions.country_code`、`cited_by_count`
- https://help.openalex.org/api/semantic-search/

**注意口径**：它检索的是**摘要级语义**，不是全文语义。用它做"这篇论文是否支持某结论"的证据检索会系统性漏掉只在正文/结果节里出现的证据。

**A7. 内容档案（Fulltext）—— 本项目最重要的单点发现**
- https://help.openalex.org/access/fulltext/

| 格式 | 文件数 | 体积 |
|---|---|---|
| PDF | 50M+（实测 has_content.pdf = **54,999,764**） | ~250 TB |
| TEI XML（**GROBID 解析产物**） | ~43M | ~20 TB |

三条获取路径：
1. **Content API**：`https://content.openalex.org/works/{work_id}.pdf?api_key=...`，后缀可换 `.grobid-xml`。**$0.01/篇**；官方明说"With a free API key ($1/day), you can download about 100 files per day"
2. **官方 CLI**：`pip install openalex-official`，支持并行/重试/断点续传，"a few million files in a few days"，同样 $0.01/文件
3. **PDF sync**：Cloudflare R2 桶全量同步（`s3://openalex-pdfs`），**必须搭配年付 plan 且单独计价**，全量下载"1–2 weeks"

配套 manifest：`s3://openalex-pdfs/_manifest/content_index/`，Parquet，每日重建，字段 `openalex_id / pdf_uuid / grobid_xml_id / updated_date`。**注意：`grobid_xml_id` 可能为空——官方明说"GROBID can't parse every PDF"**，这是全文可得性的第二层损耗。

**A8. 快照（Snapshot）仍然完全免费**
`s3://openalex/data/`，**无需 AWS 账号**，CC0。2026-06 release：**约 6.49 亿条记录**，JSONL ~750 GB 压缩（works 单独 ~670 GB），Parquet ~780 GB。**免费公共快照为季度更新；日更需付费 plan。**
- https://help.openalex.org/access/snapshot/

**A9. ⚠️ 同一数据库两个 works 计数（一手 metric-frame 陷阱）**
官方快照页明写差异原因：快照含 **XPAC 扩展语料**，API 默认**排除** XPAC。实测（2026-08-17）：
- `api.openalex.org/works` 默认口径：**324,389,590**
- `?corpus=all`：**516,949,125**

**任何引用"OpenAlex 收录 N 篇"的说法，不写明 corpus 口径即为口径失真。** 网上流传的"250M 篇"是更早期的第三个口径。

**A10. OA 与全文可得性天花板（实测）**
- `is_oa:true` → **123,672,025**（占默认口径 324.4M 的 **38.1%**）
- `has_content.pdf:true` → **54,999,764**（占 **17.0%**）

即：**即使全部走 OpenAlex，能拿到 PDF 全文的上限也只有约 17%**。这是"每条论断都要可追溯到原文"这一产品承诺的物理上限。

### B. Crossref

**B1. 限速于 2025-12-01 收紧，且"单条查询"与"列表查询"限额不同**
官方公告（https://www.crossref.org/blog/announcing-changes-to-rest-api-rate-limits/ ）："From 1 December 2025"，理由是五年内请求量翻三倍、记录数从 1.2 亿增至约 1.8 亿。

| 池 | 单条记录 | 列表查询 | 并发 |
|---|---|---|---|
| Public | **5 req/s** | **1 req/s** | 1 |
| Polite | **10 req/s** | **3 req/s** | 3 |
| Plus | **150 req/s**（文档页） | — | 无并发限制 |

- https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/ （文档页标注 Last updated **October 16, 2025**）

**实测确认（2026-08-17）**：带 `mailto` 发列表查询，响应头 `x-rate-limit-limit: 3`、`x-rate-limit-interval: 1s`、`x-api-pool: polite-array` —— 与文档的"polite 列表 3 req/s"完全吻合。

**⚠️ 陷阱**：广为流传的"Crossref polite pool = 50 req/s"是 2025-12 之前的旧值，现已失效 16 倍。

**B2. 进入 polite pool 的方式**：`mailto` 查询参数 + 标识身份的 `User-Agent` header。**无需 token**。Plus 用 `Crossref-Plus-API-Token: Bearer [key]`。

**B3. Retraction Watch 数据：免费、每工作日更新、且已进主 REST API**
- CSV 全量：`https://gitlab.com/crossref/retraction-watch-data`，**"updated once per working day"**
- REST API：撤稿体现在 `update-to` 字段；可直接 `https://api.crossref.org/v1/works?filter=update-type:retraction`；`source` 字段取值 `publisher` 或 `retraction-watch`
- CSV 关键字段：`RetractionNature`（Retraction / Correction / Expression of concern / Reinstatement）、`RetractionDate`、`OriginalPaperDOI`
- https://www.crossref.org/documentation/retrieve-metadata/retraction-watch/ （页脚 Last Updated **2025-January-19**）

**对本项目**：这是**唯一一个免费、权威、机器可读的"论文可信度否决位"**。任何引用在标 `verified` 之前必须过一次撤稿/关注声明检查。

### C. Semantic Scholar

**C1. 有 key 也只有 1 RPS —— 且官方措辞是"introductory"**
官方产品页原文："The **introductory** rate limit for an API key is **1 RPS on all endpoints**." Tutorial 页补充："using an individual API key automatically gives a user a 1 request per second rate across all endpoints. In some cases, users may be granted a slightly higher rate following a review."
- https://www.semanticscholar.org/product/api
- https://www.semanticscholar.org/product/api/tutorial

**注意"introductory"这个词**：它意味着这不是承诺的稳定档位，随时可变。规划中不能把 S2 放在关键路径上。

**C2. 无 key = 全球共享池，实测已不可用**
文档："1000 requests per second shared among all unauthenticated users"。**实测（2026-08-17）**：`GET /graph/v1/paper/search?query=test&limit=1` 无 key → **HTTP 429**，第一次调用即被拒。**结论：keyless S2 在 2026 年实际上不可用，必须申请 key。**

**C3. 数据集下载现在强制要 key（实测）**
- `GET /datasets/v1/release/latest` → 200，最新 release **`2026-08-11`**
- `GET /datasets/v1/release/latest/dataset/s2orc` → **`{"error":"A valid API key is required"}`**

即：release 列表公开，**具体数据集的下载链接需 key**。语料规模（产品页）：**214M 论文 / 2.49B 引用 / 79M 作者**。S2ORC 的开放许可为 **ODC-BY**。

### D. arXiv —— 全链路最严的限速

**D1. API/OAI-PMH：1 请求 / 3 秒，单连接**
官方 TOU 原文："make no more than one request every three seconds, and limit requests to a single connection at a time"，适用于 legacy API、OAI-PMH、RSS。
- https://info.arxiv.org/help/api/tou.html

**≈0.33 rps，且禁止并发连接。这是本项目所有信源里最严的一条，超并行架构必须为 arXiv 单独开一条串行队列。**

**D2. 禁止转存再分发**
TOU 明禁："Store and serve arXiv e-prints (PDFs, source files, or other content) from your servers, unless you have the permission of the copyright holder"。**本地缓存供自己分析可以，做成对外服务不行。**

**D3. 批量：S3 requester-pays**
- Bucket：**`arxiv`**，us-east-1，**requester pays**（下载方付 AWS 流量费）
- 体量：**约 9.2 TB**（2025-04 口径）；其中 PDF ~2.7 TB、source ~2.9 TB（**2023-03 口径 —— 这两个子项数字比总数陈旧两年，不可与 9.2 TB 同框比较**）
- 结构：`pdf/arXiv_pdf_YYMM_###.tar`（~500MB/块）+ `pdf/arXiv_pdf_manifest.xml`（含 MD5）；source 同构
- 更新：**约每月一次**
- 商用：**"we do not require that commercial projects sign an MOU"**
- https://info.arxiv.org/help/bulk_data_s3.html

**D4. LaTeX 源码是被低估的高保真通道**
`src/` 里是原始 (La)TeX。对公式、表格、参考文献而言，**解析 LaTeX 的保真度远高于任何 PDF→Markdown 管线**。对 STEM 类论证验证，这应当是首选而非 PDF。

### E. PubMed / Europe PMC

**E1. NCBI E-utilities：无 key 3 rps，有 key 10 rps**
官方原文："post no more than three URL requests per second"（无 key）；"a site can post up to 10 requests per second by default"（有 key，自 **2018-12-01** 起提供）。超 10 rps 需邮件申请。
**另有时段约束**："limit large jobs to either weekends or between 9:00 PM and 5:00 AM Eastern time during weekdays" —— 这条常被忽略，但对"大批量扫库"型任务是硬性合规要求。
- https://www.ncbi.nlm.nih.gov/books/NBK25497/

**E2. Europe PMC：无文档化限速（这本身是风险）**
- https://europepmc.org/RestfulWebService ：**"10.2 million full text articles and 6.5 million open access articles"**
- https://europepmc.org/developers ：同一站点却写 **"Metadata for all full text articles (6.4M)"** 与 **"All OA articles (3.2M)"**

**⚠️ 站内自相矛盾**：两页相差约 1.6–2 倍。**任何一个都不能单独作为载荷数字**；本项目若要引用 Europe PMC 覆盖量，必须自行 `hitCount` 实测。实测 `query=cancer` → **hitCount 5,520,735**（仅说明服务可用，非覆盖量）。

**限速**：官方两页**均未公布**任何 rps 数字，社区里存在"申请提高调用上限"的帖子但无公开值。**未文档化的限速比严格的限速更危险**——超并行系统会在没有预警的情况下被封 IP。必须保守设默认值（建议 ≤3 rps）并实现 429/503 退避。

**E3. 可用性**：实测 keyless 200 OK，无需注册，无 rate-limit 响应头。提供 REST / SOAP / OAI-PMH / Annotations / GRIST / FTP 批量。

### F. CORE

**F1. 免注册档位实测口径：5 单请求 / 10 秒**
官方服务页原文："**One batch request or five single requests per 10 seconds.**"，且 **"CORE API is free and does not require registration, subject to our rate limits. However, organisations that register get a faster rate that is typically not free."**
- https://core.ac.uk/services/api

**≈0.5 rps。注意条款变化的方向**：注册**不再自动等于免费提速**——"registered get a faster rate that is **typically not free**"，仅 Supporting/Sustaining Member 免费享受。商用允许（受 T&C 约束），Institution/Enterprise 有 30 天试用。

**F2. ⚠️ 实测不可达**
2026-08-17 两次 `https://api.core.ac.uk/v3/search/works` 请求均 **40 秒超时、0 字节返回**；`https://api.core.ac.uk/docs/v3` 与 `https://core.ac.uk/services/api` 经 WebFetch 均返回 **403**。可能是本机网络/地域因素，但**在验证到可稳定连通之前，CORE 不应进入主路径**。

### G. Unpaywall —— 已被 OpenAlex 吸收

**G1. 官方定位已变更**
OpenAlex 帮助中心明写：**"Unpaywall records are served from the same OpenAlex data that powers everything else"**，"The OA facts in an Unpaywall record and in an OpenAlex work's `open_access` object come from the same pipeline"，Unpaywall 只是"a legacy-compatible _format_ over that data"。官方建议："**For new projects, consider the OpenAlex API directly**"。
- https://help.openalex.org/access/unpaywall/

**G2. 实测佐证：返回体字段已标 deprecated**
`GET https://api.unpaywall.org/v2/10.1038/nature12373?email=...` → 200，但 `best_oa_location` 中 **`"evidence":"deprecated"`**、**`"updated":"deprecated"`**。这是 API 自己在承认字段已停止维护。

**G3. 限速**：unpaywall.org 官方 API 页仍写 **"Please limit use to 100,000 calls per day"**，无需 key，需带 `email` 参数。覆盖仅限 **Crossref 注册的 DOI**（不含 DataCite DOI）。

**G4. 对本项目的一票否决式含义**：**Unpaywall 与 OpenAlex 不构成独立佐证。** 若可信度引擎把"两个源都说是 OA"当作 2 票，实际只有 1 票。信源图必须显式记录上游归并关系。

### H. DOAJ

**H1. 限速实测口径：2 req/s，允许 5 次突发**
官方 API FAQ 原文："There is a **rate limit of two requests per second on all API routes**. 'Bursts' are permitted, which means up to **five requests per user are queued** by the system and are fulfilled in turn so long as they average out to two requests per second overall."
- https://doaj.org/api/docs

**H2. 数据许可极宽松：CC0**
官方元数据帮助页："we choose to waive all rights under a **CC0 waiver**"，并明确点名 **"This includes AI-supported solutions, such as ChatGPT, Gemini, and Perplexity."** —— DOAJ 是少数**主动、明文**允许 AI 使用其元数据的学术源。

**H3. 分发通道**：Atom feed / OAI-PMH / 期刊 CSV（**每 60 分钟**更新）/ API / public data dump / 站内检索。查询无需 key（写操作需 key）。实测 `GET /api/search/articles/test?pageSize=1` → 200，`total: 871,876`。

**H4. 对本项目的用法**：DOAJ 是"**期刊是否为正当 OA 期刊**"的白名单权威。可信度引擎判断"该引用是否来自掠夺性期刊"时，DOAJ 收录状态是成本最低的正向证据（不收录 ≠ 掠夺性，但收录是强正向信号）。

---

## 全文抽取工具（许可证 + 实测版本 + published 质量）

版本号为 2026-08-17 经 GitHub Releases API 实测：

| 工具 | 最新版本（实测） | 发布时间（实测） | 代码许可 | 权重/模型许可 | 商用门槛 |
|---|---|---|---|---|---|
| **GROBID** | **0.9.1** | 2026-08-04 | **Apache-2.0** | 同左 | **无** |
| **Docling** | **v2.120.1** | 2026-08-14 | **MIT** | 各模型单独许可，需逐个查 | 代码层无 |
| **MinerU** | **3.4.5** | 2026-08-14 | **MinerU Open Source License**（Apache-2.0 变体） | 同左 | **100M MAU 或月营收 $20M** + **强制署名** |
| **marker** | **v2.0.0** | 2026-07-20 | **Apache-2.0** | **modified AI Pubs OpenRAIL-M** | **$5M 融资/营收** |

### GROBID（Apache-2.0，纯净）
- 专为**学术论文**设计：header（标题/摘要/作者/机构/关键词）、参考文献、全文 TEI 结构化
- **published 质量（一手 README 口径）**：参考文献抽取 **~0.87 F1**，样本为**独立的 PubMed Central 集，1,943 篇 PDF / 90,125 条参考文献**；bioRxiv 同类集 **~0.90**；参考文献单独解析 **>0.90 F1（instance 级）/ 0.95 F1（field 级）**；DOI/PMID 解析 **>0.95 F1**
- **吞吐**：**~10.6 PDF/秒（≈915,000 PDF/天，≈20M 页/天）**，口径为**16 核机器上的 full-text 处理**
- 依赖 **OpenJDK 21+**；有官方 Docker
- https://github.com/kermitt2/grobid

**关键点**：OpenAlex 内容档案里的 ~43M 份 TEI XML **就是 GROBID 的产物**。本项目直接消费该 XML，等于白嫖了 GROBID 的全部产能。

### MinerU（中文场景的唯一强选）
- **许可证变更史（一手 LICENSE.md 核实）**：1.x 为 **AGPLv3**；**3.1.0（2026-03-29）** 起改为基于 Apache-2.0 的自定义许可
- 附加条款原文要点：需另购商业许可的门槛为 **"monthly active users (MAU) exceed 100 million; or total monthly revenue exceeds USD 20 million"**（含关联实体合并计算）；基于 MinerU 的在线服务**必须"clearly and prominently indicate…that MinerU is used"**；违反则**许可自动终止，无需通知**
- OCR 支持 **109 种语言**；原生中文
- 硬件（pipeline 后端）：**最低 16GB 内存（推荐 32GB+）、20GB 磁盘**，纯 CPU 可跑，支持 **Apple Silicon**（对本机 macOS 环境友好）
- https://github.com/opendatalab/MinerU

### marker（注意代码与权重双许可）
- README 原文：代码 **Apache-2.0**；权重为 **"modified AI Pubs Open Rail-M license (free for research, personal use, and startups under $5M funding/revenue)"**
- **$2M → $5M 的口径修正**：Modal 官方博客（2025-10-29）与多篇二手文章写 **$2M**；datalab 官方博客（**2026-06-18**，介绍 lift）与 marker README 现值均为 **$5M**。**旧值 $2M 已过时**

### Docling（MIT，最宽松，但注意"代码 MIT ≠ 模型 MIT"）
- 仓库明文："The Docling codebase is under MIT license. **For individual model usage, please refer to the model licenses found in the original packages.**"
- IBM 出品，现属 LF AI & Data
- https://github.com/docling-project/docling

### 质量对比 —— 这里有一个必须拆开的口径陷阱

**⚠️ marker README 声称"ahead of MinerU and docling"，但那是在 marker 自选的 benchmark 上测的。** 两个数字不可同框：

| 数字 | 口径 | 来源 |
|---|---|---|
| marker balanced **76.0%**（born-digital **83.5%**） | **olmocr-bench**，1,403 篇 PDF / ~8,400 项 pass-fail 测试 | marker README（自测） |
| MinerU pipeline **86.47** / VLM **95.30** / hybrid **95.39** | **OmniDocBench v1.6** | MinerU README（自测） |
| MinerU2.5-Pro **95.75**；**Marker 78.44**；MinerU-Pipeline **86.47** | **OmniDocBench v1.6_full 官方榜** | OmniDocBench 仓库（第三方同框） |

**只有第三行是同一把尺子。** 在 OmniDocBench v1.6 这个统一口径下，**MinerU 系（78.44 → 95.75）显著领先 marker**。marker README 的"领先"结论建立在换一个 benchmark 之上。

OmniDocBench 口径本身：**1,651 页 PDF、10 种文档类型、5 种语言（含简体中文）、5 种版式**；总分公式 **`Overall = ((1 - text Edit distance) × 100 + table TEDS + formula CDM) / 3`**；v1.6 于 **2026-04-10** 更新（引入 MGAM 匹配、约 3 倍提速）；2026-03-31 才补入 Docling / OpenOCR / EasyOCR 评测。**GROBID 不在该榜上**——它不是同类任务（GROBID 做的是学术结构化 + 参考文献，不是通用版面 OCR），**不要拿 GROBID 与它们比分数**。

---

## 载荷数字核验表（数字 | 口径三元组 | 状态 | 一手出处）

| # | 数字 | 口径三元组（指标 / 样本或档位 / 对比基准） | 状态 | 一手出处 |
|---|---|---|---|---|
| 1 | OpenAlex 免费额度 **$1/天** | 每日 API 美元预算 / 已注册免费账号档 / vs 无 key $0.10 | `verified` | help.openalex.org/access/pricing/（2026-08-11 更新）+ 实测 `x-ratelimit-limit-usd: 0.1` |
| 2 | 无 key **$0.10/天 = 1,000 credits** | 每日预算 / 匿名档 / vs 免费 key 10× | `verified`（实测） | 响应头 `x-ratelimit-limit-usd: 0.1`, `x-ratelimit-limit: 1000` |
| 3 | 单实体 lookup **$0 / 0 credit** | 每次调用成本 / `/works/{id}` 端点 / vs list 0.0001 | `verified`（实测） | 响应头 `x-ratelimit-credits-used: 0` |
| 4 | list+filter **$0.0001/次** | 每次调用成本 / `/works?filter=` / vs 官方表 $0.10/千次 | `verified`（实测+文档一致） | 实测 `cost-usd: 0.0001` + example-costs |
| 5 | search / semantic search **$0.001/次** | 每次调用成本 / `?search=` 与 `?search.semantic=` / vs 官方表 $1/千次 | `verified`（实测+文档一致） | 实测 `cost-usd: 0.001`, `credits-used: 10` |
| 6 | 内容下载 **$0.01/篇** | 每文件成本 / content.openalex.org / vs 官方表 $10/千次 | `verified`（文档，未实扣） | help.openalex.org/access/fulltext/ |
| 7 | 免费档 **~100 篇全文/天** | 日可下载 PDF 数 / $1/天 免费 key / — | `verified` | fulltext 页原文"about 100 files per day" |
| 8 | OpenAlex 硬上限 **100 rps** | 每秒请求上限 / 全档位统一 / — | `verified` | help.openalex.org/api/authentication/ |
| 9 | 语义检索 **1 rps、最多 50 条、2000 字符** | 端点级限制 / semantic search / vs 常规 100 rps | `verified`（限速文档 + 50 条实测） | help.openalex.org/api/semantic-search/ + 实测 `meta.count: 50` |
| 10 | OpenAlex works **324,389,590** | works 总数 / **API 默认口径（排除 XPAC）** / vs corpus=all | `verified`（实测） | `api.openalex.org/works` |
| 11 | OpenAlex works **516,949,125** | works 总数 / **corpus=all（含 XPAC）** / vs 默认 324M | `verified`（实测） | `api.openalex.org/works?corpus=all` |
| 12 | 网传 OpenAlex "250M 篇" | works 总数 / 早期快照口径 / — | `unverified`（口径过时，勿用） | 多处二手，无当前一手支撑 |
| 13 | `is_oa:true` **123,672,025（38.1%）** | OA 论文数与占比 / 分母为默认口径 324.4M / — | `verified`（实测） | `api.openalex.org/works?filter=is_oa:true` |
| 14 | `has_content.pdf` **54,999,764（17.0%）** | 有缓存 PDF 的论文数与占比 / 分母为默认口径 324.4M / vs 官方"50M+" | `verified`（实测，与文档"50M+"自洽） | 实测 + fulltext 页 |
| 15 | `language:zh` **5,059,316（1.56%）** | 中文论文数与占比 / 分母为默认口径 324.4M / — | `verified`（实测） | `api.openalex.org/works?filter=language:zh` |
| 16 | 快照 **~6.49 亿条 / JSONL ~750GB** | 记录数与压缩体积 / **2026-06 release** / vs Parquet ~780GB | `verified` | help.openalex.org/access/snapshot/ |
| 17 | 内容档案 **50M+ PDF ~250TB / ~43M TEI ~20TB** | 文件数与体积 / OpenAlex content archive / — | `verified` | help.openalex.org/access/fulltext/ |
| 18 | OpenAlex 年付 **$5,000 / $10,000 / $20,000起** | 年费 / Member / Member+ / Partner 三档 / vs PAYG | `verified`（**非促销价**，页面无 introductory 措辞） | help.openalex.org/access/pricing/（2026-08-11） |
| 19 | Crossref polite **列表 3 rps / 单条 10 rps，并发 3** | 每秒请求上限 / polite pool，区分单条与列表 / vs public 1 & 5 | `verified`（文档 + 实测头） | crossref.org 文档页 + 实测 `x-rate-limit-limit: 3`, `interval: 1s` |
| 20 | Crossref public **列表 1 rps / 单条 5 rps，并发 1** | 同上 / public pool / vs polite | `verified` | crossref.org/blog/announcing-changes-to-rest-api-rate-limits/ |
| 21 | Crossref Plus **150 rps，无并发限制** | 每秒请求上限 / Metadata Plus 付费档 / vs polite 3–10 | `verified` | crossref.org 文档页（2025-10-16 更新） |
| 22 | 网传 Crossref polite **"50 rps"** | 每秒请求上限 / **2025-12-01 前的旧值** / vs 现值 3–10 | `corrected` | 新值见 #19/#20，旧值已失效 |
| 23 | Crossref 记录数 **约 1.8 亿**（五年前 1.2 亿） | 元数据记录总数 / Crossref 全库 / — | `verified` | 同 #20 公告原文 |
| 24 | Retraction Watch **每工作日更新**，免费 | 更新频率 / GitLab CSV + REST API / — | `verified` | crossref.org/documentation/…/retraction-watch/ |
| 25 | Semantic Scholar 有 key **1 rps（"introductory"）** | 每秒请求上限 / 个人 API key 全端点 / vs 无 key 全球共享 | `verified`（注意"introductory"措辞不稳定） | semanticscholar.org/product/api + /tutorial |
| 26 | S2 无 key 实际 **不可用（429）** | 首次调用即被拒 / keyless / vs 文档称 1000 rps 共享 | `verified`（实测） | 实测 `GET /graph/v1/paper/search` → 429 |
| 27 | S2 数据集下载 **需 key**；最新 release **2026-08-11** | 鉴权要求与 release 日期 / datasets API / — | `verified`（实测） | `/datasets/v1/release/latest` → 200；`…/dataset/s2orc` → `{"error":"A valid API key is required"}` |
| 28 | S2 语料 **214M 论文 / 2.49B 引用 / 79M 作者** | 语料规模 / 产品页公示口径 / vs OpenAlex 324M | `verified`（官方自述，未独立核验） | semanticscholar.org/product/api |
| 29 | arXiv **1 请求 / 3 秒，单连接** | 请求频率上限 / API + OAI-PMH + RSS 全适用 / **全信源最严** | `verified` | info.arxiv.org/help/api/tou.html |
| 30 | arXiv 全量 **约 9.2 TB** | 归档体积 / **2025-04 口径** / — | `verified`（但注意与子项不同期） | info.arxiv.org/help/bulk_data_s3.html |
| 31 | arXiv PDF **~2.7 TB** / source **~2.9 TB** | 子集体积 / **2023-03 口径（比总数早两年）** / **不可与 9.2 TB 同框** | `verified`（数值）/ 口径过时 | 同上 |
| 32 | NCBI E-utilities **3 rps 无 key / 10 rps 有 key** | 每秒请求上限 / 有无 api_key 两档 / — | `verified` | ncbi.nlm.nih.gov/books/NBK25497/ |
| 33 | NCBI 大批量任务限时段（周末或**美东 21:00–05:00**） | 时段合规要求 / 大 job / — | `verified`（常被忽略） | 同上 |
| 34 | Europe PMC "**10.2M 全文 / 6.5M OA**" | 覆盖量 / RestfulWebService 页口径 / vs developers 页 | `unverified`（站内自相矛盾） | europepmc.org/RestfulWebService |
| 35 | Europe PMC "**6.4M 全文 / 3.2M OA**" | 覆盖量 / developers 页口径 / vs 上一行相差 1.6–2× | `unverified`（同上，两者必有一错） | europepmc.org/developers |
| 36 | Europe PMC 限速 | 每秒请求上限 / — / — | `unverified`（**官方未公布任何数字**） | 两页均无 |
| 37 | CORE 免注册 **5 单请求 / 10 秒（≈0.5 rps）** | 请求频率上限 / 未注册档 / vs 注册档"typically not free" | `verified`（文档） | core.ac.uk/services/api |
| 38 | CORE API 实测 **不可达（40s 超时 ×2）** | 连通性 / 本机网络 2026-08-17 / — | `verified`（实测，可能为地域因素） | 实测 curl |
| 39 | Unpaywall **100,000 calls/day**，无需 key，需 email | 日调用上限 / 公共 API / — | `verified` | unpaywall.org/products/api |
| 40 | **Unpaywall = OpenAlex 同一后端**（非独立信源） | 数据来源关系 / OA 状态字段 / — | `verified`（文档 + 实测） | help.openalex.org/access/unpaywall/ + 实测返回 `"evidence":"deprecated"` |
| 41 | DOAJ **2 rps，突发队列 5** | 每秒请求上限 / 全部 API 路由 / — | `verified` | doaj.org/api/docs（API FAQ） |
| 42 | DOAJ 元数据 **CC0**，明文允许 AI 使用 | 数据许可 / 全部 DOAJ 元数据 / vs 多数源需署名 | `verified` | doaj.org 元数据帮助页 |
| 43 | GROBID 参考文献 **~0.87 F1** | F1 / **PubMed Central 独立集 1,943 篇 PDF、90,125 条参考文献** / bioRxiv 同类集 ~0.90 | `verified` | github.com/kermitt2/grobid |
| 44 | GROBID **~10.6 PDF/秒（~915k/天）** | 吞吐 / **16 核机器、full-text 模式** / — | `verified`（注意是 16 核口径，非单核） | 同上 |
| 45 | MinerU 商用门槛 **100M MAU 或月营收 $20M** + **强制署名** | 许可触发条件 / MinerU Open Source License（3.1.0 起） / vs 1.x 的 AGPLv3 | `verified` | MinerU LICENSE.md（一手） |
| 46 | MinerU 许可变更日 **3.1.0 / 2026-03-29** | 版本与日期 / AGPLv3 → Apache-2.0 变体 / — | `verified` | github.com/opendatalab/MinerU |
| 47 | marker 权重免费门槛 **$5M 融资/营收** | 许可阈值 / **模型权重**（非代码） / vs 代码 Apache-2.0 无限制 | `verified` | marker README + datalab.to/blog/introducing-lift（2026-06-18） |
| 48 | marker 旧门槛 **$2M** | 许可阈值 / **2025 年口径** / vs 现值 $5M | `corrected`（已上调，勿用旧值） | Modal 博客 2025-10-29 等二手 |
| 49 | marker **76.0%**（born-digital 83.5%） | 总分 / **olmocr-bench，1,403 PDF / ~8,400 测试** / **自测，非同框** | `verified`（数值）/ 口径不可比 | marker README |
| 50 | OmniDocBench v1.6：**MinerU2.5-Pro 95.75 / Marker 78.44 / MinerU-Pipeline 86.47** | Overall / **OmniDocBench v1.6_full，1,651 页、10 类文档、5 语言** / **同一把尺子** | `verified`（第三方同框，**唯一可比口径**） | github.com/opendatalab/OmniDocBench |
| 51 | marker README "ahead of MinerU and docling" | 相对排名 / **marker 自选 benchmark** / 与 #50 结论**相反** | `corrected` | 同框口径见 #50 |
| 52 | 工具版本：GROBID **0.9.1**(2026-08-04) / Docling **v2.120.1**(2026-08-14) / MinerU **3.4.5**(2026-08-14) / marker **v2.0.0**(2026-07-20) | 最新 release tag 与日期 / GitHub Releases API / — | `verified`（实测） | `api.github.com/repos/*/releases/latest` |
| 53 | OpenAlex "API key 必需，否则 409" | 鉴权行为 / **2026-01-14 公告的预告口径** / vs 现状 429 且无 key 仍可用 | `corrected` | 公告见 groups.google.com；现状见 #2/#8 |
| 54 | OpenAlex "100,000 credits/天" | 免费额度 / **2026-01 公告的旧 credit 面额** / vs 现行 $1/天=10,000 credits | `corrected`（面额改过 10 倍，**吞吐量等价**） | 公告 vs 实测 `x-ratelimit-limit: 1000`（无 key 档） |

---

## 对本项目的设计含义

### D1. 检索层：把"免费的单实体 lookup"当成架构地基
OpenAlex `/works/{id}` **零成本、不占预算**（实测 0 credit）。这意味着最经济的检索模式是：

```
用少量付费的 list/search 调用拿到 ID 集合  →  之后所有元数据展开全部走免费的单实体 lookup
```

免费档一天 10,000 次 list+filter 已足够驱动相当激进的检索；真正需要省的是 **search（$0.001）与 semantic search（$0.001 且 1 rps）**。**规划里任何"每个 subagent 自由发起语义检索"的设计都必须推翻**——1 rps 意味着 20 个并行 agent 每个平均要等 20 秒。

### D2. 必须有中央限速网关，且限速值按 host 而非按 agent
最紧的四条：**arXiv 0.33 rps（且禁并发）**、**S2 1 rps**、**OpenAlex semantic 1 rps**、**CORE 0.5 rps**。中间档：**DOAJ 2 rps**、**Crossref polite 列表 3 rps**、**NCBI 3/10 rps**。宽松：**OpenAlex 常规 100 rps**、**Europe PMC 未知（保守设 3 rps）**。

设计要求：
- 所有出网请求经**单一 gateway**，按 host 维护令牌桶；subagent 不持有直接网络能力
- arXiv 必须是**串行队列**（单连接），不能是令牌桶
- 对 Europe PMC 这类**未公布限速**的源，实现指数退避 + 熔断，且默认值必须保守——未文档化的限速比严格的限速危险，因为没有预警
- 预算是**双维度**的：RPS（瞬时）+ 美元/天（累积）。OpenAlex 的 429 同时表示这两种超限，必须靠 `x-ratelimit-remaining-usd` 区分，否则会把"今天钱花完了"误判为"退避一下再试"而陷入死循环

### D3. 全文层：优先消费别人已经解析好的结果
推荐链路（成本与保真度双优）：

```
1. OpenAlex content API .grobid-xml      ← 已是 TEI，零解析成本，$0.01/篇
2. Europe PMC 全文 JATS XML              ← 生物医学，免费，结构化
3. arXiv LaTeX 源码 (src/)               ← STEM 公式/表格保真度最高，0.33 rps
4. OpenAlex content API .pdf → 本地解析
5. best_oa_location.pdf_url → 本地解析
```

**本地解析只是第 4–5 步的 fallback。** 自建 GROBID 集群在 2026 年基本是重复劳动——OpenAlex 已经把 43M 篇跑完了。

本地解析器选择：
- **英文学术 PDF + 需要参考文献结构** → **GROBID**（Apache-2.0，无任何约束，专业对口）
- **中文 PDF / 复杂表格 / 公式** → **MinerU**（同框口径下最强；Apple Silicon 原生；但**若本项目将来做成在线服务，必须在界面显著标注使用了 MinerU**）
- **需要最宽松许可、格式杂（docx/pptx）** → **Docling**（MIT）
- **marker** 在同框 benchmark 下不占优（78.44 vs MinerU 86.47–95.75），且权重带 OpenRAIL-M 门槛，**建议不进主路径**

### D4. 可信度引擎必须显式建模"信源独立性图"
本轮抓到的最危险陷阱：**Unpaywall 与 OpenAlex 是同一后端**。若把"两个源都说是 OA"记为 2 票，实际只有 1 票。同类关系还有：
- Crossref → OpenAlex（Crossref 是 OpenAlex 的上游之一；但 Crossref 对**DOI 存在性与注册元数据**仍是唯一权威，这一维度上它是独立的）
- OpenAlex content archive 的 TEI ← GROBID（解析错误会被继承，不是独立读取原文）
- Semantic Scholar / OpenAlex 都大量吸收 Crossref + arXiv

**实现要求**：证据条目除了 `source` 还要带 `upstream_root`；佐证计票按 `upstream_root` 去重。**这条应当直接写进 v2 的可信度 schema。**

### D5. 撤稿检查应当是"标记 verified 之前的强制闸门"
Crossref Retraction Watch 免费、每工作日更新、可直接 REST 过滤（`update-type:retraction`）。成本几乎为零，价值极高。建议：任何引用在被标 `verified` 之前，强制过一次撤稿/更正/关注声明检查；命中则该条自动降级为 `unverified` 并附撤稿元数据。DOAJ 收录状态可作为期刊正当性的辅助正向信号。

### D6. 全文可得性的天花板要写进产品承诺
实测：OA 占 **38.1%**，有缓存 PDF 的仅 **17.0%**，且 GROBID 解析不了全部 PDF（`grobid_xml_id` 可为空）。**"每条论断都可追溯到原文"这个承诺，在现实中最多覆盖约六分之一的文献。** 产品必须诚实地区分三种状态：
- `verified-fulltext`：读到了原文对应段落
- `verified-metadata`：只核到了摘要/元数据层（例如通过语义检索命中的证据——它只检索标题+摘要）
- `unverified`：拿不到可核验的原文

**把这三态混为一谈就是本项目最大的可信度风险。**

### D7. 中文能力必须单列一条降级路径
实测 OpenAlex 中文 works 仅 **1.56%**。知网/万方/维普**无公开 API**。国家哲学社会科学文献中心（ncpssd.cn，实测 200 可达）免费但同样无 API。既有的 bocha 中文搜索可用于**发现**，但它给不出可机器验证的文献元数据。

设计含义：
- 中文课程论文场景下，系统应**主动声明**中文文献的验证能力受限，而不是静默地用英文文献充数
- 可行的补救：让用户提供 PDF → 走 MinerU 本地解析 → 至少保证"用户手上的中文文献"能被结构化并逐句追溯
- **不要假装能做中文文献的全库检索。**

### D8. 快照是"超并行"的终极解法，但代价是本地基建
免费季度快照（~750 GB 压缩，CC0，无需 AWS 账号）可以把绝大部分 list/filter 型查询变成**本地 DuckDB 查询——零 API 成本、零限速**。对本项目这种超并行系统，这可能比买 Member 档（$5,000/年）更划算。代价：本地磁盘 + 季度更新延迟（付费才有日更）。**建议在 v2 规划里把"本地快照模式"列为一个显式的运行档位。**

---

## 未决与风险

1. **CORE 实测不可达**（两次 40s 超时 + 文档页 403）。无法确认是本机网络/地域问题还是服务侧问题。**在实机验证连通性之前，不要把 CORE 写进任何路径。**

2. **Europe PMC 两个官方页面覆盖量自相矛盾**（10.2M/6.5M vs 6.4M/3.2M，相差 1.6–2 倍），且**完全没有公布限速**。这两项都需要自行实测确定，不能引用官方数字。

3. **Semantic Scholar 的 1 rps 被官方标为 "introductory"**——措辞暗示随时可变。且实测 keyless 已直接 429。S2 的稳定性风险高于其余各源，不应进关键路径。

4. **OpenAlex 定价的变更速度本身是风险。** 2026-01 公告的 credit 面额到 2026-08 已改过一轮（100,000 → 10,000 credits，虽然美元吞吐等价）；pricing 页 2026-08-11 才更新。**本项目应把单价读自响应头（`x-ratelimit-cost-usd`）而非硬编码**，并在超预算时按 `x-ratelimit-remaining-usd` 而非盲目退避。

5. **arXiv 的"禁止转存再分发"条款**对本项目若将来做成可分享的产物有直接影响。本地缓存自用没问题，把 arXiv PDF 打包进可分发的 artifact 则可能越界。

6. **未验证项**：OpenAlex content API 的 $0.01 扣费未实扣验证（需消耗真实预算）；PDF sync 与 Partner 档为"contact sales"，无公开价，无法核验是否有促销；OpenAlex 年付三档的"32%/73% 节省"是官方自算，未独立核验其 PAYG 基准。

7. **Docling 的模型许可未逐个核验**。仓库明说代码 MIT 但"individual model usage, please refer to the model licenses" —— 若采用 Docling，需要单独跑一轮模型级许可审计。

8. **本轮 WebSearch 预算在第 2 次调用即耗尽**（200/200），后续发现全部依赖 serper-search 技能 + 直接 curl 一手页面。这使得"广度发现"弱于计划，可能遗漏了 2026 年新出现的小众源（例如新的中文开放学术 API）。**建议 v2 后续轮次单独补一次中文学术数据源的广度扫描。**

9. **OmniDocBench 已被指出"saturated"**（LlamaIndex 2026-02 文章标题即为 "OmniDocBench is Saturated"）。榜单头部集中在 95 分附近，区分度下降。**用 95.75 vs 95.30 这类差距做工具选型是过度解读**；真正拉开差距的是 pipeline 86.47 与 VLM 95+ 之间的档位差。
