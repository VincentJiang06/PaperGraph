# 通用检索/抓取供应商层调研（学术 API 之外的证据来源）

- 维度：ext-web-providers（v2 规划轮）
- 调研日期：**2026-08-17**（本文所有价格/限额均为该日一手页面实读值；本组信息在 2025–2026 年反复变动，超过 30 天须重新核验）
- 方法：先做 8 次 WebSearch 定位候选一手页 → 对每个供应商抓取**官方定价页 / 官方 rate-limit 文档 / 官方 ToS**；对客户端渲染页（serper.dev、brave.com、jina.ai、firecrawl.dev、bochaai）改用浏览器实读 DOM 文本，逐字取数。
- 口径纪律：每个载荷数字都记录"什么指标 / 在哪个样本或档位上 / 与什么比"三元组；凡是从一手数字**算出来**的（如 $/1k、QPS 折算）一律标 `派生`；凡是官方页不可达的一律标 `unverified` 并写明不可达原因。

---

## 结论摘要

1. **这一层的真实瓶颈不是钱，是"每供应商节流上限"，而且各家的节流指标根本不是同一个东西。** 七家供应商用了四种互不可比的节流单位：QPS（serper / Brave / Exa）、RPM（Tavily / Jina / Firecrawl 端点级）、**并发浏览器数**（Firecrawl 计划级）、**每小时配额**（SerpApi）。把它们塞进同一张"并发上限"表而不标注单位，是本轮最容易犯的口径错误。

2. **最贵的不是最快的，最便宜的也不是最松的。** 同一份"1000 次 Google SERP"，serper.dev Starter 档 **$1.00/1k 且 50 QPS**；SerpApi Starter 档 **$25/1k 且 200 次/小时**。价格差 25 倍，吞吐差约 900 倍（派生折算，见风险栏）。对一个 hyper-parallel 系统，SerpApi 低档位在物理上就跑不动扇出，只能当"关键单点 + 法务保险"用。

3. **发现层与取证层必须分开建模。** SERP 类（serper / Brave / SerpApi / Tavily search 默认 / Firecrawl search 默认 / bocha）返回的是**片段**；只有取证层（Jina Reader / Firecrawl scrape / Exa contents / Tavily extract）返回可逐字引用的正文。**片段永远不能支撑 `verified` 状态的断言**——这条应该写进本项目的证据契约里。

4. **意外收获且与本项目直接相关：Firecrawl 有一个 `GET /search/research/papers` 的 Research Index，论文类端点按官方定价表标注为 Free（0 credit）**，且 `/search` 支持 `categories: ["research"]` 把结果限制到 arxiv / nature / ieee 等学术域。这是本维度里唯一"学术专用且不计费"的通用供应商能力。

5. **两个合规硬点，都会咬到"可重跑证据库"这个产品形态：**
   - Brave：官方 FAQ 明写"若要存储 API 结果（哪怕部分），需订阅**显式授予存储权**的计划，通用 ToS 不覆盖"。一个把 Brave 结果长期落盘做证据台账的系统，标准档位是**不合规**的。
   - Jina：免费的 1000 万 token 明确标注 **CC-BY-NC（仅限非商业用途）**。用户写课程论文没问题，但插件若作为产品分发/商用，免费额度不适用。

6. **发现了一处教科书级的"虚假独立佐证"（见核验表 T-FALSE）**：多个二手聚合站声称 Tavily 的限额是 "/search 与 /answer 10 QPS、/contents 100 QPS"。这三个数字**逐字等于 Exa 官方 rate-limit 表**。Tavily 官方文档发布的是 RPM 不是 QPS，而且 Tavily 根本没有 `/contents` 端点（它叫 `/extract`）。这是把 Exa 的表张冠李戴到 Tavily 头上，再被多站转抄形成的假共识。

7. **Jina 的公司归属变了。** jina.ai 页脚今日实读为 `Elastic © 2020-2026`，侧栏产品含 "Elastic Inference Service"。Jina AI 已并入 Elastic。定价/条款存在再次变更的结构性风险，不能按"独立小厂长期稳定"来规划。

---

## 逐条发现（含 URL）

### 1. serper.dev — 发现层首选，且用户已有账号

一手页：<https://serper.dev/>（客户端渲染，浏览器实读 DOM，2026-08-17；页脚 `© 2026 Serper.dev`）
（`https://serper.dev/pricing` 与 `https://serper.dev/pricing-details` 均返回 **404**，定价只在首页锚点内；`https://docs.serper.dev` 在本环境连接被拒。）

- **计费模型：充值制（top-up），非订阅。** 页面原文："No monthly subscriptions; simply pay for the credits you need."
- 四个档位（原文逐字）：

  | 档位 | 价格 | 额度 | 单价 | QPS | 有效期 |
  |---|---|---|---|---|---|
  | Starter | `$50*` | `50k credits` | `$1.00/1k` | `50 queries per second` | `Credits valid for 6 months` |
  | Standard | `$375*` | `500k credits` | `$0.75/1k` | `100 queries per second` | 同上 |
  | Scale | `$1250*` | `2.5M credits` | `$0.50/1k` | `200 queries per second` | 同上 |
  | Ultimate | `$3750*` | `12.5M credits` | `$0.30/1k` | `300 queries per second` | 同上 |

  `*` 原文注："Excluding sales tax/VAT/GST"。
- 免费额度：`Get 2,500 free queries` / `No credit card required`（一次性，非每月）。
- FAQ 逐字（浏览器展开 accordion DOM 取得）："Our default rate limit for the Ultimate credits is 300 queries per second. This allows you to perform approximately 15,000 to 18,000 searches in 1 minute. **If your specific use case requires a higher concurrency we are able to change this limit.**" → 上限可议，不是硬墙。
- **端点清单（首页逐字）**：Search / Images / News / Maps / Places / Videos / Shopping / **Scholar** / **Patents** / Autocomplete。**确认有 scholar 端点**（也有 patents）。
- **scrape 端点：未在任何公开页找到文档。** `https://scrape.serper.dev/` GET 返回 **HTTP 403**（主机存在、拒绝未鉴权 GET），这只是"主机存在"的间接证据，**不足以确认端点契约、计费与限额** → 标 `unverified`。
- Playground / Dashboard 需登录，端点级 credit 表无法从公开页取得。二手源称 scholar 与 search 同价（1 credit ≤10 结果，>10 结果 2 credits），**本轮未取得一手确认**。
- ToS <https://serper.dev/terms>：**未涉及**缓存/存储、限额、并发。仅禁止逆向与"规避对 API key 或账户所施加的任何限制"。
- 返回内容：Google SERP 结构化 JSON（knowledgeGraph / organic / peopleAlsoAsk / relatedSearches），**只有 snippet，无全文**。
- 本机既有集成：`~/playground/dsh-projects/serper-harvester/dsh-web-search-serper/` 已实现 DSH `WebSearchProvider`，provider id `serper`，baseURL `https://google.serper.dev`，目前只打通 `/search` 与 `/news`。

### 2. Tavily — RPM 制，且"环境"而非"计划"决定限额

一手页：<https://docs.tavily.com/documentation/rate-limits>、<https://docs.tavily.com/documentation/api-credits>、<https://help.tavily.com/articles/3240802908-rate-limits>（帮助中心标注 `Last updated 6 months ago`，即约 2026-02）

- **限额按 API key 所属"环境"划分，不是按付费档位：**

  | 端点组 | Development | Production |
  |---|---|---|
  | 默认端点（search / extract / map 等） | `100` RPM | `1,000` RPM |
  | `/crawl` | `100` RPM | `100` RPM（**不随环境提升**） |
  | `/research` | `20` RPM | `20` RPM |
  | `/usage` | 10 次 / 10 分钟 | 10 次 / 10 分钟 |

- **官方页面未发布任何 QPS 数字，也未发布任何并发数。** 超限返回 `429 Too Many Requests` 并带 `retry-after` 头（秒）。
- Credit 表（<https://docs.tavily.com/documentation/api-credits> 逐字）：
  - Basic Search = **1 credit**；Advanced Search = **2 credits**
  - Basic Extract = 每 **5** 个成功 URL 计 **1 credit**；Advanced Extract = 每 5 个 URL 计 **2 credits**
  - Map = 每 **10** 页 **1 credit**；带 `instructions` 的 Map = 每 10 页 2 credits
  - Crawl = Map 成本 + Extract 成本（官方例：10 页 basic = 3 credits；10 页 advanced = 5 credits）
  - Research：`model=pro` **15–250 credits/请求**；`model=mini` **4–110 credits/请求**（动态，成本方差极大）
- 计划与单价（同页逐字）：Researcher 1,000 credits 免费 / Project 4,000 @ $30（`$0.0075`/credit）/ Bootstrap 15,000 @ $100（`$0.0067`）/ Startup 38,000 @ $220（`$0.0058`）/ Growth 100,000 @ $500（`$0.005`）/ 按量 `$0.008 / Credit` / Enterprise 定制。
  - <https://www.tavily.com/pricing> 页面本身为滑块式渲染，价格数字取不到；**上述档位表来自 Tavily 自家文档站，仍属一手。**
  - 该页另有 "Free for students"（学生免费），未给出具体额度 → `unverified`。
- 返回内容：`/search` **默认只给片段**。<https://docs.tavily.com/documentation/api-reference/endpoint/search> 逐字：`chunks_per_source` 默认 3、上限 3，每 chunk"maximum 500 characters"；`max_results` 默认 5、范围 0–20。要正文须设 `include_raw_content`（`markdown` | `text` | `false`，默认 `false`）。
- ToS <https://tavily.com/terms>：未直接规定缓存/转售；有一条对本项目相关的限制——禁止"any data mining, robots, or similar data gathering or extraction methods **through the Services**"；且"Tavily and its third-party artificial intelligence service providers may use, process, analyze, and retain Customer Input"（**你的查询会被留存**）。
- 二手情报（**未验证**）：有 Medium 文章标题称 Tavily 已被 Nebius 收购。未找到一手公告 → `unverified`，但列入风险。

### 3. Exa — 语义检索强，但 `/search` 只有 10 QPS，是全表最紧的硬瓶颈之一

一手页：<https://exa.ai/docs/reference/pricing>、<https://exa.ai/docs/reference/rate-limits>（`docs.exa.ai` 307 跳转到 `exa.ai/docs`）、<https://exa.ai/docs/reference/should-we-use-livecrawl>

- **限额（官方页逐字，未区分免费/付费档位）：** `/search` **10 QPS**；`/contents` **100 QPS**；`/answer` **10 QPS**。页面注："Need higher rate limits? Contact us at sales@exa.ai to discuss an Enterprise plan."**官方未发布并发上限。**
- 定价（逐字）：
  - Search：**$7 / 1k requests**（含前 10 条结果）；第 10 条之后 **$1 / 1k results**
  - Contents：**$1 / 1k pages，按内容类型分别计**（同时要 text + highlights = 按 2 页计费）；AI summary 再加 $1 / 1k pages
  - Answer：$5 / 1k requests（含 ≤10 结果）
  - Deep Search：deep-lite $12/1k（~4s）、deep $12/1k（4–15s）、deep-reasoning $15/1k（12–40s）
  - Monitors：$15/1k（≤10 结果）
  - Agent/Research 固定档：minimal $0.012 / low $0.025 / medium $0.10 / high $0.50 / xhigh $1.00 每次；计量档 $0.10/ACU + $0.005/search call
- 免费额度（逐字）："New accounts get $20 in free credits (around 2,800 searches) and the Free Tier adds $10 in credits every month."
- **缓存语义（对证据新鲜度是决定性的）**：官方逐字 "By default, we serve cached content to bias for the fastest response possible."；用 `maxAgeHours` 控制：`24` = 24h 内用缓存、`1` = 近实时、`0` = 永远实时抓、`-1` = 永不实时抓（纯缓存）、**省略 = 仅在无缓存时才实时抓（官方推荐）**。旧的 `livecrawl` 字符串参数（always/never/fallback/preferred）已废弃。
- 官方未在该页说明 livecrawl 是否额外计费 → `unverified`。
- ToS：<https://exa.ai/terms-of-service> 返回的是 **PDF（application/pdf, 208.9KB）**，本轮未解析 → 缓存/转载/robots 条款 `unverified`。

### 4. Firecrawl — 唯一按"并发浏览器数"卖的，且有免费的学术论文索引

一手页：<https://www.firecrawl.dev/pricing.md>（官方提供的 Markdown 版定价，**最可靠取数入口**）、<https://docs.firecrawl.dev/rate-limits>、<https://docs.firecrawl.dev/features/search>、<https://docs.firecrawl.dev/api-reference/endpoint/search>

> **口径陷阱（本轮亲身踩到）**：`firecrawl.dev/pricing` 网页版会**按访问地区自动切换货币**（本机浏览器被判成日本，整页显示 JPY，还带"Billed yearly / Save ¥…"）。网页默认展示的是**年付折算月价**，不是月付挂牌价。必须用 `pricing.md` 取 USD 挂牌价。

- 计划表（`pricing.md` 逐字）：

  | 计划 | 月付挂牌价 | 年付价（折合月） | credits/月 | 并发请求 |
  |---|---|---|---|---|
  | Free | $0 | $0 | 1,000 | **2** |
  | Hobby | **$19** | $190（$16/mo） | 5,000 | **5** |
  | Standard | **$99** | $990（$83/mo） | 100,000 | **50** |
  | Growth | **$399** | $3,990（$333/mo） | 500,000 | **100** |
  | Scale | **$749** | $7,190（$599/mo） | 1,000,000 | **150** |
  | Enterprise | 定制 | 定制 | 定制 | 定制 |

- 端点级 RPM（<https://docs.firecrawl.dev/rate-limits> 逐字，另有独立于并发数的一套限制）：

  | 计划 | /scrape | /map | /crawl | /search | /agent | 最大排队作业 |
  |---|---|---|---|---|---|---|
  | Free | 10 | 10 | 2 | 10 | 2 | 50,000 |
  | Hobby | 100 | 100 | 20 | 100 | 20 | 50,000 |
  | Standard | 500 | 500 | 100 | 500 | 100 | 100,000 |
  | Growth | 5,000 | 5,000 | 1,000 | 5,000 | 1,000 | 200,000 |
  | Scale | 10,000 | 10,000 | 2,000 | 10,000 | 2,000 | 500,000 |

  另：Extract 端点与 `/agent` 共用限额；Batch scrape 与 `/crawl` 共用限额。浏览器沙箱 `/interact` 另有一套（Standard 100 RPM）。
- Credit 表（`pricing.md` 逐字）：Scrape 1/页、Crawl 1/页、Map 1/次、Search **2 / 10 结果**、Interact 2/浏览器分钟、Monitor 1/页/次检查、**Research Index (papers) = Free**、Agent（预览）每日 5 次免费后动态定价。
  - 进阶特性额外计费：`Scrape with JSON format` **+4 credits/页**；`Scrape with Enhanced Mode` **+4 credits/页**；PDF 解析 1 credit / **PDF 页**（不是 1/文件——长 PDF 成本会炸）。
- **`/search` 默认只返回片段**（官方逐字："Search results include query-relevant Highlights by default."）；要正文必须加 `scrapeOptions`（"Add `scrapeOptions` to also retrieve full-page markdown, HTML, links, or screenshots for each result."），且**此时每条结果再按 scrape 单独计费**。
- **学术相关能力（本维度最有价值的发现）**：
  - `sources` 参数只接受 `web` / `images` / `news`；
  - `categories` 参数支持 `github` / **`research`**（把结果限制到 arxiv.org、nature.com、ieee.org 等学术域）/ `pdf`；
  - 独立端点 **`GET /search/research/papers`**（Research Index，论文摘要与引文扩展），按定价表 **0 credit**。
  - 注：`https://docs.firecrawl.dev/features/research-index` 返回 404，Research Index 的**字段契约与覆盖范围本轮未取得一手文档** → 能力存在 `verified`（定价表 + search API 参考页两处官方提及），**契约细节 `unverified`**。
- 其他官方 FAQ 逐字：credits **自助档不结转**（"Credits do not roll over on self-serve plans"，仅 Scale/Enterprise 可结转）；**无按量付费计划**；失败请求不计费。
- ToS <https://www.firecrawl.dev/terms-of-service>：**完全未提 robots.txt，也未提抓取内容的留存/缓存期限**。责任在用户侧（§7.7 defend/indemnify）。明确禁止：违反 GDPR/CCPA 的用途（§5.4.15）、为情报机构做人员数据收集分析（§5.4.16）、催收、背景调查、FCRA 用途。

### 5. Jina Reader — 单位成本最低的全文取证通道，但 robots 检查是**可选项**

一手页：<https://jina.ai/reader/>（浏览器实读整表与参数说明，2026-08-17）

- **官方 Rate Limit 表（逐字，只有 RPM/TPM 两列，无并发列）：**

  | 产品 | 端点 | 无 key | Free key | Paid key | Premium key | 平均延迟 | token 计法 |
  |---|---|---|---|---|---|---|---|
  | Reader | `https://r.jina.ai` | **20 RPM** | **500 RPM** | **500 RPM** | **5000 RPM** | 7.9s | 计**输出**响应 token |
  | Reader(搜索) | `https://s.jina.ai` | 禁用 | **100 RPM** | **100 RPM** | **1000 RPM** | 2.5s | 每请求固定起步 **10,000 tokens** |
  | DeepSearch | `deepsearch.jina.ai/v1/chat/completions` | 禁用 | 50 RPM | 50 RPM | 500 RPM | **56.7s** | 计全过程 token |

  官方说明逐字："Limits are enforced per IP/API key and will be triggered when either the RPM or TPM threshold is reached first. When you provide an API key in the request header, we track rate limits by key rather than IP address."
- 定价（逐字）：
  - **Toy Experiment：1000 万 tokens，Free，`Non-commercial use only (CC-BY-NC)`**
  - Prototype Development：10 亿 tokens，**$50**，`0.050 / 1M tokens`，Standard key
  - Production Deployment：110 亿 tokens，**$500**，`0.045 / 1M tokens`，**Premium key（才有 5000 RPM）**
  - 页面明写："We introduced a new pricing model on **May 6th, 2025**. If you enabled auto-recharge before this date, you'll continue to pay the old price..."（老用户老价，**新 key 一律新价**）
- **缓存是一等公民（对可重跑证据极重要）**，官方请求头逐字：
  - `X-No-Cache`："Our API caches URL contents for a certain amount of time. Set it to true to ignore the cached result..."
  - `X-Cache-Tolerance`："Accept cached content if younger than N seconds. Set to 0 for fresh content..."
  - `DNT`："Prevent this request from being cached or logged on our servers."
  - `X-Set-Cookie` 说明："requests with cookies will not be cached."
  - **官方未公布默认缓存 TTL 的具体秒数** → `unverified`。
- **robots/ToS 姿态：宽松，责任外推。** 请求头 `X-Robots-Txt` 的官方说明逐字："Check robots.txt rules before fetching. Specify which bot name to use for the check." → **robots 检查是显式 opt-in，不是默认行为**。同时提供 `X-Proxy` / `X-Proxy-Url`（国家级代理）、`X-User-Agent`（覆盖 UA，说明写"Useful for accessing sites that require specific browsers **or block crawlers**"）、`X-Set-Cookie`（带登录态）。FAQ 有 "Does Reader actively bypass website anti-bot protection?" 一项，但折叠内容不在 DOM 中，无法取到答案 → `unverified`。
- 其他有用参数：`X-Respond-With: readerlm-v2`（复杂页高质量转换，**"Costs 3x tokens!"**）、`X-Target-Selector` / `X-Remove-Selector`（CSS 精确取正文，直接降 token 成本）、`X-Token-Budget`（硬上限，超了请求失败——**可当成本熔断**）、`X-Timeout`、`X-With-Iframe`、`X-Retain-Images`。
- **公司归属：页脚逐字 `Elastic © 2020-2026`**，产品栏含 "Elastic Inference Service"。Jina AI 已属 Elastic。

### 6. Brave Search API — 唯一真正独立的索引，但存储权是收费项

一手页：<https://brave.com/search/api/>（浏览器实读 + FAQ DOM 展开，2026-08-17）

- **2026 年的档位结构已经不是老的 Free/Base/Pro 三档了**，页面上只有三个：

  | 计划 | 价格 | 容量（原文 CAPACITY） | 备注 |
  |---|---|---|---|
  | **Search** | `$5 per 1,000 requests` | `50 queries per second` | 含 `$5 in free credits every month` |
  | **Answers** | `$4 per 1,000 requests` + `$5 per million input/output tokens` | **`2 queries per second`** | 含 `$5 in free credits every month` |
  | Enterprise | 定制 | 定制 | `Full-funnel Zero Data Retention`、定制协议/NDA |

- **免费额度的口径是"每月 $5 抵扣额度"，不是"每月 N 次查询"。** 页面未给出免费档的独立 QPS 或次数上限。按 $5/1k 折算 = **每月约 1,000 次 Search 请求免费**（`派生`）。
- FAQ 逐字："Why is a credit card required to subscribe to a free plan? — The credit card requirement serves as an anti-fraud measure... For free plans, the card is only used to confirm your identity and will not be charged." → **免费档也要绑卡**。
- **存储/缓存权（本项目的合规硬点）**，FAQ 逐字：
  > "If you would like to store the API results in part or whole (for example, to train or tune an LLM), you will need to subscribe to a plan that **explicitly grants storage rights**. Plans with storage rights grant special permissions which are **not covered in our general Terms of Service**."
- 版权姿态，FAQ 逐字：
  > "The Brave Search API does not grant any rights to third-party content such as webpages. Customers who access URLs displayed in the Brave Search API must ensure their access to those webpages complies with the copyright terms of the page publishers."
- 索引规模（官方宣称）："Brave's index includes over 30 billion pages, kept fresh by over 100 million page updates every day."
- 端点：Web、LLM Context、Answers、Image、Video、News、Suggest、Spellcheck，另有 Place Search。SOC 2 Type II。
- 返回内容：SERP 结构（title/url/description/profile），**片段级**；有 "Extra alternate snippets"（最多 5 段）与 "LLM context optimized" 变体，但**不是全文**。
- `https://api-dashboard.search.brave.com/app/documentation/pricing` 与 `https://brave.com/search/api/terms/` 均 **404**；dashboard 需登录 → 更细的档位/限额文档本轮不可达。

### 7. SerpApi — 吞吐结构与 hyper-parallel 相冲，但有法务保险和内置缓存

一手页：<https://serpapi.com/pricing>、<https://serpapi.com/search-api>、<https://serpapi.com/google-scholar-api>

- **节流单位是"每小时搜索数"，不是 QPS，也不是并发数（官方页未发布任何并发数）：**

  | 计划 | 月价 | 搜索/月 | **吞吐/小时** | Legal Shield |
  |---|---|---|---|---|
  | Free | $0 | 250 | 50 | 否 |
  | Starter | $25 | 1,000 | 200 | 否 |
  | Developer | $75 | 5,000 | 1,000 | 否 |
  | Production | $150 | 15,000 | 3,000 | **是** |
  | Big Data | $275 | 30,000 | 6,000 | 是 |
  | Searcher | $725 | 100,000 | 20,000 | 是 |
  | Volume | $1,475 | 250,000 | 50,000 | 是 |
  | Infrastructure | $2,750 | 500,000 | 100,000 | 是 |
  | Cloud 1M…52M | $3,750 … $102,175 | 1M…52M | 110,000 … 620,000 | 是 + ZeroTrace |

  规律（`派生`）：每小时吞吐恒为月额度的 **20%**。
- **缓存条款（官方逐字，<https://serpapi.com/search-api>）**："Cache expires after 1h. **Cached searches are free, and are not counted towards your searches per month.**" 参数 `no_cache`（默认 `false`）强制绕过缓存；`no_cache` 与 `async` 不可同时使用。
  - → 对"可重跑验证"是**正面**特性：1 小时内重复同一查询免费且结果一致。
- **Legal Shield（逐字）**："provides up to **$2 million** in coverage for the scraping and parsing of search engine data"。**Production（$150/mo）及以上才有**。ZeroTrace 仅 Cloud 档。
- **Google Scholar 引擎确认存在**：`engine=google_scholar`，返回 `serpapi_cite_link`、`cited_by.total`、`cites_id`、`cluster_id`（版本聚合）等；**只有 SERP 元数据，不含全文**。官方未对该引擎设特殊价或特殊限额。
- 计费口径注意：Starter $25 / 1,000 次 = **$25.00/1k**（`派生`），是本表最贵的 SERP 单价。

### 8. bocha / 博查（用户已有）— 官方定价页不可达

- `https://open.bochaai.com/` 今日实际渲染为 **LangSearch（博查的国际站）** 定价页，全文口径为 "No fees, No subscriptions... For individuals and small teams, **free access as we build AGI together**"，个人档 Web Search 与 summary 内容均标 `Free`，企业档只写 "Higher QPS (Throughput)"、"Custom pricing based on usage"，**无任何具体数字**。页脚 `©2023-2026`。
- 中文侧"产品价格"链接指向飞书文档 <https://aq6ky2b8nql.feishu.cn/wiki/JYSbwzdPIiFnz4kDYPXcHSDrnZb>（标题「API 定价」，`Last updated: Jun 03`）。**该飞书页正文需登录才渲染，浏览器实读只拿到标题与"Log In or Sign Up"，正文 DOM 为空** → **官方定价页不可达，博查的每千次价格与 QPS 一律 `unverified`**。
- 已确认：Web Search API 返回 `snippet` 字段 + summary 字段，**属片段级 + 摘要级，非原始全文**；另有 Agent Search API 与 Semantic Reranker API。
- 结论：博查只能定位为**中文发现层的补充信源**，且因为限额未知，**必须按最保守的桶（例如 1 QPS）接入**，直到拿到一手数字。

---

## 载荷数字核验表

> 口径三元组 = 什么指标 / 在什么样本或档位上 / 与什么比。
> 状态：`verified`=一手页逐字；`verified(派生)`=由一手数字算出、算式已列；`corrected`=二手说法被一手推翻并改正；`unverified`=一手不可达或一手未发布。

### A. 节流上限（**本维度最载荷的一组数字**）

| 数字 | 口径三元组 | 状态 | 一手出处 |
|---|---|---|---|
| serper Starter **50 QPS** | 每秒查询数 / Starter 档（$50, 50k credits）/ 对比同档其他 SERP 供应商 | `verified` | serper.dev 首页定价卡（2026-08-17 浏览器实读） |
| serper Standard/Scale/Ultimate **100 / 200 / 300 QPS** | 同上 / 三个更高档 / — | `verified` | 同上 |
| serper "可申请提高并发" | 定性 / Ultimate 档 FAQ / — | `verified` | serper.dev FAQ accordion 原文 |
| Tavily Production **1,000 RPM** | 每分钟请求数 / **Production 环境 key**、默认端点 / 与 Development 的 100 RPM 比 | `verified` | docs.tavily.com/documentation/rate-limits |
| Tavily Development **100 RPM** | 同上 / Development 环境 key / — | `verified` | 同上 |
| Tavily `/crawl` **100 RPM（两个环境相同）** | 每分钟 / crawl 端点 / 与默认端点 1,000 RPM 比 | `verified` | 同上 |
| Tavily `/research` **20 RPM** | 每分钟 / research 端点、两环境相同 / — | `verified` | 同上 |
| Tavily **无官方 QPS、无官方并发数** | 指标缺失 / 官方 rate-limit 页 / — | `verified`（确认"未发布"） | 同上 + help.tavily.com |
| **T-FALSE：Tavily "/search 10 QPS、/contents 100 QPS"** | 声称的每秒查询数 / Tavily / — | **`corrected`** | 二手（coldiq 等）声称；**与 exa.ai/docs/reference/rate-limits 逐字相同**，且 Tavily 无 `/contents` 端点、官方只发 RPM。判定为把 Exa 的表张冠李戴，多站转抄形成假共识 |
| Exa `/search` **10 QPS** | 每秒查询数 / 全体非 Enterprise 用户、search 端点 / 与 `/contents` 100 QPS 比 | `verified` | exa.ai/docs/reference/rate-limits |
| Exa `/contents` **100 QPS**、`/answer` **10 QPS** | 同上 / 对应端点 / — | `verified` | 同上 |
| Firecrawl 并发浏览器 **2 / 5 / 50 / 100 / 150** | **同时在跑的浏览器数**（≠RPM）/ Free / Hobby / Standard / Growth / Scale / — | `verified` | docs.firecrawl.dev/rate-limits + pricing.md 两处一致 |
| Firecrawl Standard `/scrape` **500 RPM**、`/crawl` **100 RPM** | 每分钟请求数 / Standard 档、对应端点 / 与并发数 50 是**两套独立限制** | `verified` | docs.firecrawl.dev/rate-limits |
| Jina `r.jina.ai` **20 / 500 / 500 / 5000 RPM** | 每分钟请求数 / 无 key / Free key / Paid key / Premium key / — | `verified` | jina.ai/reader Rate Limit 表（浏览器实读） |
| Jina `s.jina.ai` **禁用 / 100 / 100 / 1000 RPM** | 同上 / 搜索端点 / 与 Reader 端点比 | `verified` | 同上 |
| **Jina "并发 2 / 50 / 500"** | 声称的并发请求数 / Jina key 档位 / — | **`corrected` → `unverified`** | 二手页面与自动摘要都出现此列；**2026-08-17 浏览器实读官方表只有 RPM/TPM 两列，无并发列**。一手无此数字 |
| Brave Search **50 QPS** | 每秒查询数 / Search 计划（$5/1k）/ 与 Answers 的 2 QPS 比 | `verified` | brave.com/search/api CAPACITY 字段 |
| Brave Answers **2 QPS** | 每秒查询数 / Answers 计划 / 同上 | `verified` | 同上 |
| SerpApi **50 / 200 / 1,000 / 3,000 / 6,000 / 20,000 / 50,000 / 100,000 次每小时** | **每小时配额**（≠瞬时并发）/ Free…Infrastructure 八档 / — | `verified` | serpapi.com/pricing |
| SerpApi 每小时 = 月额度的 **20%** | 比例 / 全部自助档 / — | `verified(派生)` | 200/1,000、1,000/5,000、3,000/15,000、6,000/30,000 均 = 0.2 |
| SerpApi Production **≈0.83 QPS 均值** | 由 3,000/小时折算的每秒均值 / Production 档 / 与 serper Starter 50 QPS 比 | `verified(派生)`；**运营含义 `unverified`** | 3,000÷3,600=0.833。**注意口径**：官方口径是小时配额，未禁止小时内突发，因此"0.83 QPS"是均值不是瞬时墙 |
| bocha / LangSearch QPS | 每秒查询数 / 任意档 / — | **`unverified`（官方页不可达）** | 定价文档 aq6ky2b8nql.feishu.cn/wiki/JYSbwzdPIiFnz4kDYPXcHSDrnZb 需登录，正文 DOM 为空 |

### B. 价格（注意：credit ≠ request，plan ≠ 单价）

| 数字 | 口径三元组 | 状态 | 一手出处 |
|---|---|---|---|
| serper **$1.00 / 1k**（$50 / 50k credits） | 每千 credit 价 / Starter 充值档、**含税前**、credits **6 个月过期** / 与 SerpApi Starter $25/1k 比 | `verified` | serper.dev 首页 |
| serper $0.75 / $0.50 / $0.30 每 1k | 同上 / Standard / Scale / Ultimate | `verified` | 同上 |
| serper 免费 **2,500 次**（一次性） | 总量 / 新账号、免绑卡 / 与 Tavily 每月 1,000 credits 比 | `verified` | 同上 |
| Tavily Basic Search = **1 credit**，Advanced = **2 credits** | credit 消耗 / 每次 search 请求 / — | `verified` | docs.tavily.com/documentation/api-credits |
| Tavily Project **$30 / 4,000 credits = $0.0075/credit** | 单 credit 价 / Project 月订阅 / 与 PAYG $0.008 比 | `verified` | 同上 |
| Tavily basic search **≈$7.5 / 1k** | 每千次 basic search / Project 档 / 与 Exa search $7/1k、Brave $5/1k 比 | `verified(派生)` | 1 credit × $0.0075 × 1000 |
| Tavily Research **15–250 credits/请求**（pro） | credit 消耗区间 / research 端点 `model=pro` / 与 basic search 1 credit 比 → **最高 250 倍方差** | `verified` | 同上 |
| Exa Search **$7 / 1k requests**（含前 10 结果） | 每千请求 / 标准 search、**≤10 结果** / 超出部分另计 $1/1k results | `verified` | exa.ai/docs/reference/pricing |
| Exa Contents **$1 / 1k pages，按内容类型分别计** | 每千页每类型 / contents 端点 / **text+highlights = 2 倍** | `verified` | 同上 |
| Exa 新账号 **$20 免费额度（约 2,800 次搜索）+ 每月 $10** | 免费额度 / 新注册 + Free Tier 月度 / — | `verified` | 同上（"around 2,800 searches" 为 Exa 自己的折算） |
| Firecrawl Standard **月付 $99 / 年付 $990（$83/mo）** | 月挂牌价 vs 年付折月价 / Standard 档 / **网页默认展示的是年付价** | `verified` | firecrawl.dev/pricing.md（USD 权威版） |
| Firecrawl Hobby/Growth/Scale 月付 **$19 / $399 / $749** | 同上 / 三档 / 年付分别 $16/$333/$599 折月 | `verified` | 同上 |
| Firecrawl scrape **≈$0.99 / 1k 页** | 每千页取全文 / Standard 月付档 / 与 Jina Reader 比 | `verified(派生)` | $99 ÷ 100,000 credits × 1 credit/页 × 1000 |
| Firecrawl JSON/Enhanced 模式 **+4 credits/页**（共 5） | 增量 credit / 每页 / 相对基础 scrape 的 **5 倍** | `verified` | pricing.md |
| Firecrawl PDF **1 credit / PDF 页**（非每文件） | credit 单位 / PDF 解析 / 长 PDF 成本线性放大 | `verified` | pricing.md |
| **Firecrawl Research Index（论文）= Free（0 credit）** | credit 消耗 / `GET /search/research/papers` 端点 / 与 `/search` 2 credits/10 结果比 | `verified`（定价表 + API 参考页两处官方提及）；**字段契约 `unverified`**（features/research-index 404） | pricing.md + docs.firecrawl.dev/api-reference/endpoint/search |
| Jina **$0.050 / 1M tokens**（$50 / 1B） | 每百万 token / Prototype 充值档、**Standard key** / 与 Production 档 $0.045 比 | `verified` | jina.ai/reader 定价卡 |
| Jina **$0.045 / 1M tokens**（$500 / 11B，含 Premium key） | 同上 / Production 档 / **只有这一档给 5000 RPM** | `verified` | 同上 |
| Jina Reader 计费按**输出** token | 计费基数 / r.jina.ai / 与 s.jina.ai 的"每请求起步 10,000 tokens"比 | `verified` | 官方 Rate Limit 表 "Token Usage Counting" 列 |
| Jina Reader **≈$0.25–0.75 / 1k 页** | 每千页全文 / 假设单页输出 5k–15k tokens / 与 Firecrawl $0.99/1k 比 | **`unverified`（依赖我方假设的页面 token 数）** | 算式：$0.05/1M × (5k~15k) × 1000。**token/页由我假设，非官方数字** |
| Jina 免费 **10M tokens = CC-BY-NC 仅非商业** | 授权口径 / Toy Experiment 档 / 与付费档无此限制比 | `verified` | jina.ai/reader 定价卡原文 |
| Brave Search **$5 / 1k requests** | 每千请求 / Search 计划 / 与 Answers $4/1k+token 费比 | `verified` | brave.com/search/api |
| Brave 免费 **每月 $5 抵扣 ≈ 1,000 次 Search** | 免费额度折算 / Search 计划 / — | `verified(派生)` | $5 ÷ ($5/1k)。官方只给"$5 free credits"，次数是折算 |
| SerpApi Starter **$25 / 1k** | 每千次搜索 / Starter 档 $25/1,000 / **全表最贵** | `verified(派生)` | serpapi.com/pricing（$25 ÷ 1,000 × 1000） |
| SerpApi Infrastructure **$5.50 / 1k** | 同上 / $2,750 / 500,000 / — | `verified(派生)` | 同上 |
| SerpApi 缓存 **1 小时，命中免费且不计入月额度** | 缓存 TTL + 计费 / 全部计划 / 与 Exa 默认吃缓存但未公布 TTL 比 | `verified` | serpapi.com/search-api 原文 |
| SerpApi Legal Shield **最高 $200 万** | 保额 / **Production（$150/mo）及以上** / Free/Starter/Developer 无 | `verified` | serpapi.com/pricing 原文 |
| bocha 每千次价格 | 每千次 / 任意档 / — | **`unverified`（官方定价页需登录）** | — |
| **促销 / 引流价识别** | — | — | **本轮未发现任何被标注为 promotional/introductory 的价格。** 但两处"看起来像折扣"的必须点名：① Firecrawl 网页默认展示**年付折月价**并标 "Save $…"，月付挂牌价高 19–25%；② Jina "老用户老价"条款（2025-05-06 前开启自动充值者保留旧价），**新用户一律新价** |

---

## 对本项目的设计含义

### D1. 证据契约：片段永远不能构成 `verified`

七家里，**默认返回全文的只有 Jina Reader、Firecrawl `/scrape`、Exa `/contents`、Tavily `/extract`**。serper / Brave / SerpApi / bocha / Tavily `/search` 默认 / Firecrawl `/search` 默认，全部只给片段（Tavily 甚至硬性写死"每 chunk ≤500 字符、每源最多 3 chunk"）。

→ **落到设计**：证据对象必须带 `evidence_grade` 字段，取值至少 `snippet` / `fulltext` / `fulltext+anchor`。状态机规则：**任何 `verified` 断言的引文必须来自 `fulltext` 级证据，并携带取回时间戳与取回参数**（Exa 的 `maxAgeHours`、Jina 的 `X-Cache-Tolerance`、SerpApi 的 `no_cache`）。片段只能支撑 `unverified`，最多用于"值得去取全文"的路由信号。

### D2. 中心化限流是必需品，不是优化项——而且必须是**跨进程**的

DSH 子代理可能是独立进程，任何"每 agent 内存计数器"的方案在 hyper-parallel 下必然击穿。**限流器必须是单一权威**：一个本地 broker 进程，或 SQLite + 文件锁实现的令牌桶（macOS 本机，`~/Library/Application Support/…` 或项目内 `.state/`）。所有供应商调用一律经过它，子代理拿不到裸 API key。

**按"最先炸"排序的分级：**

| 级别 | 供应商/端点 | 一手上限 | 为什么必须集中管 |
|---|---|---|---|
| **P0 极紧，绝不暴露给子代理** | Brave **Answers** | 2 QPS | 三个子代理同时发一次就超 |
| P0 | Exa `/search`、`/answer` | 各 10 QPS | 扇出 20 路语义检索直接 429 |
| P0 | Tavily `/research` | 20 RPM | 每 3 秒才 1 次；且单次可能吃 250 credits |
| P0 | Tavily `/crawl` | 100 RPM（**Production 也不涨**） | 唯一不随环境升级的端点，最容易被误判为"升级就好了" |
| **P1 紧，需专用队列** | Firecrawl 并发浏览器 | Standard 50 | 与 RPM 是**两套独立限制**，必须同时建模：`min(并发槽, RPM 桶)` |
| P1 | SerpApi | Production 3,000 次/小时 | **小时配额**语义：需要滑动窗口计数器，不是令牌桶 |
| P1 | Tavily 默认端点（若持 **Development** key） | 100 RPM ≈1.67 QPS | 极易被误当成"Tavily 就是慢"，其实是 key 环境选错 |
| **P2 宽，仍需桶但可放大扇出** | serper | 50 QPS（Starter） | 本项目扇出主力 |
| P2 | Brave **Search** | 50 QPS | 独立索引，值得当二号发现源 |
| P2 | Jina Reader `r.jina.ai` | 500 RPM（付费）≈8.3 QPS | 取证主力 |
| P2 | Exa `/contents` | 100 QPS | 取证补充，比它的 `/search` 宽 10 倍——**发现与取证要拆成两个桶** |
| P2 | Firecrawl `/scrape` | 500 RPM（Standard） | 取证备胎 |
| **P3 未知，按最保守桶接** | bocha / LangSearch | 未知 | 先按 1 QPS 接，拿到一手数字再放开 |

**额外两条：**
- Tavily 的 429 带 `retry-after` 头。**任一子代理收到 429，必须让整个供应商桶集体退避**（而不是只让那个 agent 睡），否则其余子代理会继续撞墙、把退避时间无限拉长。
- serper FAQ 明确"更高并发可议"——**扩容路径是发邮件，不是升档**，这一点要写进运维手册。

### D3. 推荐的主链与备链

**发现层（广度优先，先便宜后精准）**
1. **主：serper.dev `/search`**（$1.00/1k、50 QPS、已有账号、已有 DSH provider 代码 `serper-harvester/dsh-web-search-serper/`）
2. **学术发现：serper `/scholar`**（同价 1 credit 量级，**未取得一手 credit 表确认**）+ **Firecrawl `GET /search/research/papers`（0 credit）** + Firecrawl `/search?categories=["research"]`
3. **中文：bocha / 博查**（用户已有；按 1 QPS 保守桶）
4. **独立索引交叉验证：Brave Search**（$5/1k、50 QPS）。**它的价值不是便宜，是"不是 Google 的复述"**——本项目要做"独立佐证"判定，就必须有一个非 Google 血统的索引，否则所有"多源一致"都是同一上游的回声。
5. **语义/长尾：Exa `/search`**（$7/1k，**但 10 QPS 是硬墙**，只在 serper+Brave 都没打中时才升级调用）
6. **法务敏感的关键单点：SerpApi Production+**（$2M Legal Shield）。**不做扇出**，只在"这条证据必须站得住且可能被质疑抓取合法性"时打一发。

**取证层（全文，成本敏感）**
1. **主：Jina Reader `r.jina.ai`**（$0.05/1M 输出 token，500 RPM）。配 `X-Target-Selector` 精确取正文、`X-Token-Budget` 做单页成本熔断、`X-Cache-Tolerance` 做可复现性控制。
2. **备（JS 重 / 反爬 / PDF 分页）：Firecrawl `/scrape`**（≈$0.99/1k 页；PDF 按**页**计费要预算告警）
3. **顺手取：Exa `/contents`**（100 QPS，已经用 Exa 搜到时直接带出；**必须显式设 `maxAgeHours`**）
4. **不单独接 Tavily `/extract`**——只在已经因为别的原因用了 Tavily 时顺带用；单独引入不划算（每 5 URL 才 1 credit 看着便宜，但要多养一条鉴权/限流/错误处理链路）。

**明确不推荐做主力**：SerpApi（吞吐结构与 hyper-parallel 冲突，单价最高）；Brave Answers（2 QPS + 它替你做了总结，等于把"证据判定"外包给别人的模型，与本项目"机器判定可追溯"的产品定位直接冲突）。

### D4. 缓存语义直接决定"可重跑"能不能成立

这是本维度对产品最深的影响，四家的缓存语义完全不同：

| 供应商 | 缓存默认 | 可控参数 | 对可重跑证据的含义 |
|---|---|---|---|
| Exa | **默认吃缓存** | `maxAgeHours`（0=总是实时，-1=永不实时） | **危险默认**：不设参数就可能拿到旧内容却当成"今天取的"。凡是"截至今日"类断言，必须 `maxAgeHours: 0` 并记录该参数 |
| Jina Reader | 缓存一段时间（**TTL 未公布**） | `X-No-Cache`、`X-Cache-Tolerance`（秒）、`DNT` | 复现时应固定同一 `X-Cache-Tolerance`，否则两次运行不可比 |
| SerpApi | 1 小时 | `no_cache` | **正面**：1 小时内重跑同查询免费且结果一致，天然适合"验证者复算" |
| Firecrawl / Tavily / Brave / serper | 未公布缓存控制参数 | — | 视为"每次都是新抓"，但**不能假设**；证据里必须记录取回时间戳 |

→ **落到设计**：证据记录的必填字段应包含 `fetched_at`、`provider`、`endpoint`、`cache_policy_used`（把上述参数原样存下来）。没有 `cache_policy_used`，"可重跑"就是空话。

### D5. 两个合规红线要写进架构，不是写进 README 脚注

1. **Brave 结果不得长期落盘**（除非买带 storage rights 的计划）。本项目的证据台账天然要长期存。**方案**：Brave 的返回只用于**路由决策**（决定去抓哪个 URL），落盘的是从原站取回的全文 + 原始 URL，**不落盘 Brave 的 snippet/排序结果**。这条要在代码层强制（Brave provider 的返回对象打 `ephemeral: true`，序列化器拒绝写盘）。
2. **Jina 免费额度是 CC-BY-NC**。用户写课程论文属非商业，可用；但**插件若对外分发或商用，必须走付费 key**。README 与首次运行提示里要明说，不能让用户在不知情下踩。

补充一条软红线：**Firecrawl 与 Jina 的 ToS 都不承诺 robots.txt 合规**（Firecrawl ToS 完全不提；Jina 的 robots 检查是 `X-Robots-Txt` 显式 opt-in）。一个以"学术可信度"为产品的系统，**应当主动把 robots 检查打开**（Jina 侧设 `X-Robots-Txt`），并把"是否遵守 robots"作为证据元数据的一部分。这是产品差异化，不只是合规。

### D6. 成本模型必须以"载荷证据单位"计价，不是以 API 调用计价

一条 `verified` 断言的真实成本 ≈ `发现（N 次 SERP）+ 取证（M 次全文）+ 可能的 PDF 页数`。用今日一手价粗算一条典型断言（3 次 serper + 2 次 Jina 全文，按每页 10k token）：
`3 × $0.001 + 2 × $0.0005 = $0.004`（`派生`，且 Jina 那一半依赖我方假设的 token/页 → 整体标 `unverified`）。
真正会炸预算的是三个乘数：**Tavily research 的 250 credits 上限、Firecrawl 的 +4 credits 进阶模式与 PDF 按页计费、Jina 的 ReaderLM-v2（3 倍 token）**。这三处必须有硬预算闸门，且闸门要在**调用前**判定（Jina 有现成的 `X-Token-Budget` 可直接当熔断器）。

### D7. 供应商抽象层的接口形状

各家节流单位不同，所以 provider 接口不能只暴露 `rateLimit: number`。建议：

```
ProviderQuota = {
  unit: 'qps' | 'rpm' | 'concurrent' | 'per_hour',
  value: number,
  scope: 'account' | 'key' | 'endpoint' | 'ip',
  source: 'official' | 'derived' | 'assumed',   // 让"未验证"在运行时也可见
  verifiedAt: ISODate,
}
```
一个供应商可以同时挂多条（Firecrawl = `concurrent:50` **且** `rpm:500@/scrape`）。`source: 'assumed'` 的桶（如 bocha）在日志里要持续告警，逼着人去补一手数字。

---

## 未决与风险

### 未决（明确标注为本轮未拿到一手）

1. **serper 的 scrape 端点**——`scrape.serper.dev` 主机存在（403），但无公开文档，端点契约/计费/限额全部 `unverified`。`docs.serper.dev` 在本环境连接被拒（两次 socket closed），Playground/Dashboard 需登录。**建议**：用户已有 serper 账号，登录后台 30 秒即可确认，这是最高性价比的补验项。
2. **serper 各端点的 credit 表**（scholar 是否与 search 同价、>10 结果是否 2 credits）——二手一致但无一手 → `unverified`。同样可由用户登录后台补齐。
3. **bocha / 博查全部定价与 QPS**——官方定价页托管在飞书 wiki 且需登录，正文 DOM 为空。国际站 LangSearch 只写"Free"，无数字。
4. **Firecrawl Research Index 的字段契约与覆盖范围**——`docs.firecrawl.dev/features/research-index` 返回 404；只从定价表和 search API 参考页确认了端点存在且免费。**这是对本项目价值最高的未决项，值得单独补一轮。**
5. **Exa ToS**（缓存/转载/robots 条款）——`exa.ai/terms-of-service` 返回 PDF，本轮未解析。
6. **Exa livecrawl 是否额外计费**——官方 livecrawl 页未说明。
7. **Jina Reader 的默认缓存 TTL 秒数**、以及 FAQ "Does Reader actively bypass website anti-bot protection?" 的答案——折叠内容不在 DOM 中。
8. **Brave 带 storage rights 的计划叫什么、多少钱**——`api-dashboard.search.brave.com/app/documentation/pricing` 与 `brave.com/search/api/terms/` 均 404，dashboard 需登录。**这直接决定 D5 红线能否用钱解决。**
9. **Tavily 计划 → 环境（Dev/Prod key）的映射**——文档只说"环境"，定价页只说"Higher rate limits"，**哪一档才拿得到 1,000 RPM 的 Production key 未确认**。这是 Tavily 能否进主链的决定性数字。
10. **Tavily "Free for students"** 的具体额度未公布（对写课程论文的用户可能有直接价值）。

### 风险

1. **口径混淆风险（最高）**：QPS / RPM / 并发浏览器 / 每小时配额，四种单位。任何把它们排进同一列而不标单位的表，都会在容量规划时给出错误结论。**本文核验表已强制标单位，后续文档必须继承。**
2. **虚假独立佐证已被实证发生**（T-FALSE：Exa 的限额表被转抄成 Tavily 的）。二手聚合站（coldiq / costbench / xpay / apiserpent / usagepricing 等）在本组话题上互相转抄严重，**本维度后续一律不得引用聚合站数字**。
3. **自动摘要引入的幻觉列**（Jina "并发 2/50/500"）：即使是对一手 URL 的抓取，**经过摘要模型也可能凭先验补出官方页上不存在的列**。凡是关键节流数字，应以浏览器实读 DOM 原文为准（本轮对 serper/Brave/Jina/Firecrawl 均已如此处理）。
4. **价格展示形态陷阱**：Firecrawl 网页按 IP 地区切货币（本机被判 JPY）且默认展示年付折月价。**取数必须用 `pricing.md`。** 同类风险适用于任何带地区定价的供应商。
5. **供应商归属变动**：Jina 已并入 Elastic（页脚 `Elastic © 2020-2026`，一手）；Tavily 疑似被 Nebius 收购（二手，`unverified`）。**两条主链候选都在换东家**，定价与条款的稳定性预期要下调。架构上应保证 provider 可替换（D7 的抽象层就是为此）。
6. **预付制沉没成本**：serper credits **6 个月过期**。按用量预付而非一次性顶格充值。
7. **Firecrawl credits 自助档不结转**，且无按量付费计划——月度用量波动大的研究型负载（本项目正是）会系统性浪费额度。
8. **合规**：Brave 存储权（D5-1）、Jina CC-BY-NC（D5-2）、Firecrawl/Jina 均不承诺 robots 合规。
9. **方法论披露（必须记录）**：本轮 **WebSearch 只完成了 8 次**，第 9 次起本会话的共享搜索预算（200/200）已耗尽，未达任务书要求的"至少 12 次"。**补偿方式**：改为对已知官方域直接抓取，共完成约 34 次一手页抓取/浏览器实读（含 8 次 404/403/PDF/需登录的失败尝试，均已在正文点名）。由于本任务的验证力来自**一手页面**而非搜索次数，判断该替代不损害结论质量；但**"是否遗漏了本轮完全没想到的供应商"这一覆盖面风险无法用一手抓取补偿**，标为未决。若需补齐，可用本机已装的 `serper-search` skill（走用户自己的 serper key）继续检索。
