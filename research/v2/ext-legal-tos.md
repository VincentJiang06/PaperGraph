# 外部调研 v2 · 维度：抓取、存储与再分发的法律/ToS 层

- 调研时点：2026-08-17（所有"当前状态"均以此日为准）
- 调研方法：WebSearch/serper/bocha 检索 → **一手页面 WebFetch/PDF 直读**；凡载荷数字必须落到官方页面、法条原文或法院文书本身
- 适用对象：academic-research-plugin（个人/课程与论文场景，macOS 本地运行，DeepSeek 为主模型，serper.dev + bocha 已具备）
- 免责：本文是工程设计输入，不是法律意见。凡标 `unverified` 的条目在写进代码默认值前必须由人复核。

---

## 结论摘要

1. **法律风险的重心已经从"用了什么"移到"怎么拿到的"。** Bartz v. Anthropic（N.D. Cal. 2024-cv-05417-WHA，Doc 231，2025-06-23）把"取得渠道"和"下游用途"彻底切开：训练本身"spectacularly transformative"、买来的纸书拆扫成数字件也过关，但**从盗版站下载并留存**这一步被判"inherently, irredeemably infringing even if the pirated copies are immediately used for the transformative use and immediately discarded"。判决还点名 Anthropic 的问题之一是"The library copies lacked internal controls limiting access and use."——**本地语料库缺访问控制本身就是被写进判词的减分项**。这两句直接决定本项目的取证层设计。

2. **"机读偏好"标准已经三足鼎立，但三家都明确说自己不产生法律效力。** IETF AIPREF 的 vocab 草案原话："Preferences do not themselves create rights, obligations, or prohibitions"；Cloudflare Content Signals 把自己定位为 EU DSM 第 4(3) 条意义上的 **express reservation of rights**（不是合同）；RSL 1.0 是 XML 许可词表 + 发现机制，不自称可独立执行。**唯一被"准官方"文件写死为必须遵守的是 robots.txt（RFC 9309）**——EU GPAI 行为准则版权章 Measure 1.3(1)(a) 逐字要求签署方"employ web-crawlers that read and follow instructions expressed in accordance with the Robot Exclusion Protocol (robots.txt), as specified in the IETF RFC No. 9309"。

3. **Cloudflare 已经从"收费抓取"转向"按使用付费"，并且 2026-09-15 会改默认值。** Pay Per Crawl（2025-07-01 上线，HTTP 402 + `crawler-price`/`crawler-max-price`，Ed25519/RFC 9421 签名）至 2026-08 仍是 **private beta**；2026-07-01 Cloudflare 宣布演进为 Pay Per Use，并把爬虫分成 Search / Agent / Training 三类。**2026-09-15 起，对新接入域名 + 现有客户的新站点 + 未改过设置的现有免费客户，在展示广告的页面上默认阻断 Training 与 Agent，放行 Search**；多用途（mixed-use）爬虫按最严格类别判定。→ 本项目的抓取器如果自我声明为 training/agent，会在越来越多站点上撞墙；如果不声明身份而伪装浏览器，则同时违反 Measure 1.3(4) 的可发现性期待并加大合同违约面。

4. **出版商 TDM 授权允许的是"项目期内本地留存 + 极短摘录对外"，不允许长期语料库。** Elsevier 的原文条款：项目结束"immediately and permanently delete all copies (including back-ups or otherwise) of the ScienceDirect dataset, but you may retain a copy of the TDM Output"；对外分发的 snippet 上限"a maximum length of 200 characters surrounding and excluding the text entity matched"，且须附 DOI 回链；商业用途禁止。Springer Nature：本地留存"limited to the duration of the TDM project"，终止后须销毁；同时对非 OA 内容依 DSM 2(2)/4(3) **明确保留全部 TDM 权利**。Wiley：非商业学术研究、需 ORCID 换 API token、TDM 与 TDM Output 不得直接或间接商业使用。**三家的共同形状 = 本项目"三档快照"里的 Tier A 必须带 TTL 和项目绑定，Tier B 必须有硬性字符上限。**

5. **管辖区裂开得比 2024 年更厉害，且英国方向反转。** EU：Art.3（研究机构 + 合法访问，副本可**长期保留**用于科研含结果验证，合同不能排除）vs Art.4（任何人、任何目的，但可被机读保留声明 opt-out，副本只能保留"as long as is necessary"）。UK：2026-03-18 政府报告明确 **"A broad copyright exception with opt-out is no longer the government's preferred way forward"**，宽泛 TDM 例外被放弃，仍只剩 CDPA s29A 的非商业研究例外（合法访问 + 不得转让副本 + 合同条款不可排除）。日本：Art.30-4 仍最宽，但文化厅 2024-03-15《General Understanding》把"以输出特定创作者表达为目的的微调"和"以输出原作表达为目的建 RAG 库"排除在外，RAG 更可能落在 Art.47-5 的"轻微利用"。新加坡：s244 计算数据分析例外允许商业用途，但 2026-01/02 新加坡法学院已在提改革案，拟明确"以违反条款方式取得访问 = 无合法访问"。中国：**没有 TDM 例外**，著作权法第 24 条为封闭列举（(一) 个人学习、研究或者欣赏；(二) 适当引用；(六) 课堂教学或科学研究，少量复制，但不得出版发行），《生成式人工智能服务管理暂行办法》第七条要求"使用具有合法来源的数据和基础模型""不得侵害他人依法享有的知识产权"。

6. **一个来自本次调研过程本身的经验事实：一手法律源正在对自动抓取关门。** 本轮 WebFetch 实测：`onlinelibrary.wiley.com` 返回 **HTTP 402 Payment Required**；`sso.agc.gov.sg`（新加坡官方法规库）、`sal.org.sg`、`irishstatutebook.ie`、`japaneselawtranslation.go.jp` 返回 **403**；`eur-lex.europa.eu` 三种 URL 形式均返回空正文。**能稳定拿到的一手源反而是 `legislation.gov.uk`（含保留的 EU 指令条文）、`digital-strategy.ec.europa.eu` 的 PDF、法院文书 PDF、以及各厂自家开发者门户。** → 设计含义：抓取器必须把"一手源不可达"当成一等公民状态，而不是悄悄回落到博客二手源——那正是上一轮 1/3 数字口径失真的机制。

---

## 逐条发现（含 URL）

### A. Cloudflare：AI 爬虫政策与付费抓取机制

**A1. Pay Per Crawl 机制（2025-07-01 上线，至 2026-08 仍 private beta）**
- 一手：https://blog.cloudflare.com/introducing-pay-per-crawl/ （发布时间戳 `2025-07-01T10:00:00.000Z`）
- 机制：源站对未付费爬虫返回 **HTTP 402 Payment Required** 并带响应头 `crawler-price`；爬虫在请求里带 `crawler-max-price` 或 `crawler-exact-price`；成功时 200 + `crawler-charged`。身份验证走 Web Bot Auth：Ed25519 密钥对 + HTTP Message Signatures（RFC 9421），请求头 `signature-agent` / `signature-input` / `signature`。
- 商业形态：Cloudflare 作为 Merchant of Record 汇总计费再分账；站点设"全站统一的每请求单价"（flat, per-request price across their entire site）。
- **状态：private beta，未公布任何 list price。**（一手：https://developers.cloudflare.com/ai-crawl-control/ ，页面 Last updated 2026-08-14，仍标 private beta）
- 口径警告：博客里没有任何具体价格数字；网上流传的"每次抓取 $X"多为第三方推测，**不要写进本项目的成本模型**。

**A2. 2026-07-01 政策转向：Pay Per Crawl → Pay Per Use，2026-09-15 改默认**
- 一手（博客）：https://blog.cloudflare.com/content-independence-day-ai-options/ （2026-07-01）
- 一手（新闻稿）：https://www.cloudflare.com/press/press-releases/2026/cloudflare-allows-the-agentic-internet-to-flourish-with-a-simple-philosophy-your-content-your-rules/ （2026-07-01）
- 三分类：**Search**（收集/索引内容以便日后回答关于它的问题）、**Agent**（实时代表某个人去把事办成）、**Training**（取内容训练或微调模型）。多用途爬虫按**最严格**类别判定。
- **默认值变更（口径极易被放大，务必按原文记）**：自 2026-09-15 起，在**展示广告的页面上**，Training 与 Agent 默认阻断、Search 默认放行；适用范围是**新接入 Cloudflare 的域名 + 现有客户新建的站点 + 到该日仍未在面板改过设置的现有免费客户**。不是"Cloudflare 全网默认封 AI"。
- 合作方（新闻稿列举）：Ceramic.ai、You.com、beehiiv、Patreon、Condé Nast。
- 厂商自报统计（**未经独立核实**）：自动化 agent/bot 已占"more than half of all web requests"；Cloudflare 覆盖"more than 20% of web domains"；"over 50% of crawl traffic from AI crawlers is spent re-fetching unchanged pages"；过去一年签了 50+ 内容许可协议。

**A3. Web Bot Auth（爬虫身份的密码学化）**
- 一手：https://developers.cloudflare.com/bots/reference/bot-verification/web-bot-auth/ （Last updated 2026-07-01）
- 依赖 IETF 草案 `draft-meunier-http-message-signatures-directory-03` 与 `draft-meunier-web-bot-auth-architecture-02`；算法 Ed25519；请求头 `Signature-Agent` / `Signature-Input` / `Signature`；通过 Cloudflare 面板 Bot Submission Form 提交密钥目录 URL 完成注册。
- 设计含义：这是本项目"合法且可审计的抓取身份"的现成路径——**声明真实身份并接受被拒**，好过伪装 UA。

### B. 机读 AI 偏好标准与其法律分量

**B1. Cloudflare Content Signals Policy（2025-09-24）**
- 一手：https://blog.cloudflare.com/content-signals-policy/
- 三个信号，原文定义：
  - `search` — "building a search index and providing search results (e.g., returning hyperlinks and short excerpts from your website's contents). Search does not include providing AI-generated search summaries."
  - `ai-input` — "inputting content into one or more AI models (e.g., retrieval augmented generation, grounding, or other real-time taking of content for generative AI search answers)."
  - `ai-train` — "training or fine-tuning AI models."
- 语法写在 robots.txt 里：`Content-Signal: search=yes, ai-train=no`。
- Cloudflare 对使用 **managed robots.txt** 的存量域名批量写入了上述默认值，涉及 **3.8M+ 域名**；`ai-input` 故意留空不代客户预设。
- 法律定位（关键）：政策文本把信号声明为 **"EXPRESS RESERVATIONS OF RIGHTS UNDER ARTICLE 4 OF THE EUROPEAN UNION DIRECTIVE 2019/790"** —— 即 DSM 第 4(3) 条的机读保留，**不是合同**。政策文本本身以 **CC0** 发布。
- 反证（必须并列记录）：Google 的 John Mueller 公开表示 Google 不识别也不使用该指令；截至 2026-08 没有任何法院判决认定 Content-Signal 具有独立可执行性。→ **它的作用是"证据"，不是"闸门"**：忽视它不会自动构成违约，但会在 Art.4 抗辩里把 opt-out 变成既成事实。

**B2. IETF AIPREF 工作组（vocab + attach）**
- 一手草案渲染：https://ietf-wg-aipref.github.io/drafts/draft-ietf-aipref-vocab.html （文档头 Date **2026-08-14**，Expires 2027-02-15）
- 一手 datatracker：https://datatracker.ietf.org/doc/draft-ietf-aipref-vocab/ （intended status: Proposed Standard；IESG state "I-D Exists"；WG milestone 2026-08；伴随草案 `draft-ietf-aipref-attach-06`）
- 词表（当前仅两个类别，比 RSL/Content Signals 窄）：
  - `train-ai` — "Using an asset to modify the learned parameters of an AI model that is used to generate synthetic content in one or more modalities"
  - `search` — 主要目的是选出资产并把用户导向该资产所在位置的应用（附直链与摘录条件）
- 默认规则：未表达偏好时，所有类别取值 **`unknown`**（不是 yes、也不是 no）。
- 法律分量（逐字）：**"Preferences do not themselves create rights, obligations, or prohibitions."**；以及"Whether and under which circumstances a preference is followed is outside the scope of this specification."
- **状态：仍是 Internet-Draft，尚未成为 RFC。**（口径警告：任何称"IETF 已标准化 AI 偏好"的说法是错的）

**B3. RSL — Really Simple Licensing 1.0**
- 一手：https://rslstandard.org/rsl —— **RSL 1.0，2025-12-10，由 RSL Technical Steering Committee 发布为 Recommendation**（标准 2025-09-10 首发）
- 用途词表：`ai-all` / `ai-train` / `ai-input` / `ai-index` / `search` / `all`
- 支付模型 `type` 取值：`free` / `attribution` / `purchase` / `subscription` / `training` / `crawl` / `use` / `contribution`
- 发现机制：robots.txt 的 `License: <absoluteURL>` 指令；HTTP `Link: <url>; rel="license"; type="application/rsl+xml"`；HTML `<link>` 或 `<script type="application/rsl+xml">`；RSS 的 `<rsl:content>`；媒体文件的 XMP/ID3/EPUB/PNG chunk 内嵌。
- 法律分量：规范**没有**自称可独立执行，仅定位为"machine-readable usage, licensing, payment, and legal terms"的表达与发现机制。其执行力依赖底层版权/合同法。
- 生态：由非营利 RSL Collective（集体权利组织）推动，Yahoo、Medium 等为早期参与方。

**B4. TDMRep（W3C Community Group Final Report，2024-02-02）**
- 一手：https://www.w3.org/community/reports/tdmrep/CG-FINAL-tdmrep-20240202/
- 三种实现：`/.well-known/tdmrep.json`、HTTP 响应头 `tdm-reservation` / `tdm-policy`、HTML `<meta name="tdm-reservation">`。
- 取值：`tdm-reservation: 1` = 保留权利、需授权；`0` = 未保留。`tdm-policy` 指向机读许可条款 URL。
- 法律定位：明确对标 DSM 第 4 条的机读保留。**注意：CG Report ≠ W3C 标准。**

**B5. robots.txt 本身的法律分量**
- 现行事实：robots.txt 是 **RFC 9309（Robots Exclusion Protocol，Proposed Standard）**，被 EU GPAI 行为准则版权章逐字点名为签署方必须遵循的协议（见 D2）。
- 但在美国法下，robots.txt 本身不是法律、不是合同：这一点在 2026 年的多篇执业指引中一致（例：https://www.ropesgray.com/en/insights/alerts/2026/05/web-scraping-in-the-age-of-ai-guidance-for-data-owners-and-scrapers ，2026-05-27）。风险从 robots 转向 **ToS 违约 + CFAA（仅当有认证壁垒时）**。
- **本项目的操作结论：把 robots.txt 当硬约束执行（成本极低、抗辩价值极高），但不要在文档里声称"遵守 robots 就合法"。**

### C. 学术出版商的 TDM 条款（对本地语料留存与引用的实际许可范围）

**C1. Elsevier / ScienceDirect（最清楚、也最严）**
- 一手条款：https://dev.elsevier.com/tdm_service.html （页面标注当前版本 **24-August-2023**）
- 一手政策：https://www.elsevier.com/about/policies-and-standards/text-and-data-mining
- 一手许可：https://www.elsevier.com/about/policies-and-standards/text-and-data-mining/license
- 谁能用：订阅机构的研究者，自助注册取 API key，**仅限非商业学术研究**。
- 留存（逐字）："Upon completion of the relevant text and data mining project, you will immediately and permanently delete all copies (including back-ups or otherwise) of the ScienceDirect dataset, but you may retain a copy of the TDM Output for academic research purposes."
- 摘录上限（逐字）："snippets (which may include a few lines of query-dependent text of individual full text articles or book chapters up to a maximum length of **200 characters** surrounding and excluding the text entity matched)"
- 分发条件：snippet 与书目元数据对外分发时须附 **DOI 回链**指向该篇全文，并带专有权声明。
- 禁止项：用 TDM Output 增强机构库/学科库以至于与最终同行评议版竞争；任何直接或间接商业活动；替代或复刻 Elsevier 既有产品。
- API key 失效条件：6 个月未启用、1 年未访问、机构订阅到期、共享或滥用 key。

**C2. Springer Nature**
- 一手保留声明：https://dev.springernature.com/tdm-reservation-policy/ （页脚 © 2026）
- 逐字要点：对非 OA 内容，依 **Directive (EU) 2019/790 第 2(2) 条定义、第 4(3) 条方式**明确保留全部 TDM 权利，并额外保留"any development, training, programming, improving or enriching of Artificial Intelligence (AI) systems"的权利；授权咨询走 datasolutions@springernature.com。
- OA 内容：CC BY 允许 TDM（需署名/链接/标注改动）；CC BY-NC 允许非商业 TDM（同上 + 不得商用）。
- 一手 API 条款：https://dev.springernature.com/terms-conditions/ —— 机构授权内容可"download and/or extract information to … a server only accessible to you, your institution"，**留存期"limited to the duration of the TDM project, unless otherwise specified in the TDM License"**，终止后须"destroy any copies of content … that may be locally loaded"；TDM Output 可与第三方共享但**仅限非商业**；摘要（abstracts）仅限个人非商业使用，不得再分发。
- **口径警告：Springer Nature 的"允许"与"保留"是两套并行文本——OA 部分按 CC 许可走，非 OA 部分默认全保留。**不要把 OA 那句当成全站结论。

**C3. Wiley（一手源本轮不可达，标 `unverified`）**
- 尝试 https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining → **HTTP 402 Payment Required**；https://olabout.wiley.com/WileyCDA/Section/id-826542.html → **HTTP 522**。
- 二手一致复述（多个大学图书馆指南 + Couperin 2017-2019 合同 PDF）：订阅机构的合法用户可为**非商业学术研究**做 TDM；需接受 click-through TDM 许可并用 **ORCID 换 API token**；只应通过官方 TDM API 访问；"TDM and TDM Output will not be used for direct or indirect commercial purposes without prior consent in writing from Wiley"；英国用户的该协议中涉 TDM 的条款被 2014 年 UK 法规（即 CDPA s29A 体系）覆盖而失效。
- **注意：这些复述互相之间不是独立证据**（多为同一份 STM 样板许可的转述），按"伪独立佐证"处理。**Wiley 条款在写死进代码前必须人工登录核对。**

**C4. 开放侧渠道（Tier A 的主力）**
- **arXiv**：一手 https://info.arxiv.org/help/api/tou.html —— 元数据 **CC0 1.0**；速率"no more than one request every three seconds, and limit requests to a single connection at a time"；**全文不得在自己服务器上存储并对外提供**（"store and serve arXiv e-prints … from your servers"需版权人授权或该 e-print 本身带宽松许可）；须回链 arXiv 抽象页。批量入口另见 https://info.arxiv.org/help/bulk_data.html 与 S3（requester-pays）。
- **Crossref**：一手 https://www.crossref.org/documentation/retrieve-metadata/text-and-data-mining/ （Last updated 2025-10-17）—— **只收元数据，不托管全文**；元数据里常带全文 URL 及其 `intended-application`（如 `text-mining`）与许可 URL（XML 里 `applies_to="tdm"` / `applies_to="vor"`）；官方明说"the presence of a URL in one of these fields does not guarantee access"，可能仍需订阅、登录或接受 TDM 许可。
- **OpenAlex**：数据以 **CC0** 提供，全量可下载（二手核实一致，一手 openalex.org 首页明示 CC0）。
- **Semantic Scholar**：一手 https://api.semanticscholar.org/license/ —— 授权"internal use solely for the purpose of training and evaluating machine learning models … for legitimate, non-commercial, research and/or educational purposes"；**禁止转售/转让/再分发**语料；需署名并带 `utm_source=api`；商业用途需另行扩展许可。→ **可以本地建库训练/评测，不可对外再分发。**

### D. 各法域 TDM 例外的当前状态

**D1. 欧盟 DSM 指令 2019/790（逐字，源：https://www.legislation.gov.uk/eudr/2019/790/article/3 与 /article/4）**
- **Art.3（科研 TDM）**：受益人限研究机构与文化遗产机构，须"合法访问"。第 2 款逐字："Copies of works or other subject matter made in compliance with paragraph 1 shall be stored with an appropriate level of security and **may be retained for the purposes of scientific research, including for the verification of research results**." 第 3 款允许权利人施加网络与数据库的安全完整性措施，但"Such measures shall not go beyond what is necessary to achieve that objective."（合同不得排除 Art.3——见 Art.7(1)）
- **Art.4（通用 TDM）**：第 1 款覆盖"lawfully accessible works"的复制与提取，任何目的、任何主体；第 2 款"may be retained **for as long as is necessary** for the purposes of text and data mining"；第 3 款条件——使用"has not been expressly reserved by their rightholders in an appropriate manner, **such as machine-readable means in the case of content made publicly available online**"；第 4 款不影响 Art.3。
- **本项目最关键的一条差异**：**Art.3 允许长期保留（含为验证研究结果），Art.4 只允许"必要期间"。** 本项目 Tier A 的"可复跑证据"诉求，在法理上正好对上 Art.3 的"verification of research results"——但前提是使用者算 "research organisation"。个人学生/自由研究者是否满足，**未决**（见风险）。

**D2. EU AI Act + GPAI 行为准则版权章（对"最佳实践"最有操作性的一份，可直接抄成 fetcher 规则）**
- 一手 PDF（逐页直读已完成）：Code of Practice for General-Purpose AI Models — Copyright Chapter（WG1 Co-Chair Alexander Peukert / Vice-Chair Céline Castets-Renard；PDF 创建日 2025-08-01；行为准则整体于 2025-07-10 公布）
  https://static1.squarespace.com/static/57718ce22e69cfd869e2f4b4/t/6895aba7e6f10e301fdd606b/1754639271718/Code_of_Practice_for_GeneralPurpose_AI_Models_Copyright_Chapter.pdf
- **Measure 1.1** — 制定、维护并实施一份单一文档的版权政策，并在组织内指派责任人；鼓励公开政策摘要。
- **Measure 1.2**（只抓合法可访问内容）逐字两项承诺：
  - (a) "not to circumvent effective technological measures as defined in Article 6(3) of Directive 2001/29/EC … **in particular by respecting any technological denial or restriction of access imposed by subscription models or paywalls**"
  - (b) "to exclude from their web-crawling websites that make available to the public content and which are, at the time of web-crawling, **recognised as persistently and repeatedly infringing copyright and related rights on a commercial scale by courts or public authorities** in the European Union and the European Economic Area"；并说明欧盟将在一个 EU 网站上公开这些名单的动态超链接列表。
- **Measure 1.3**（识别并遵守权利保留）：
  - (1)(a) 逐字要求爬虫读取并遵循 **robots.txt（IETF RFC No. 9309）**及其后续版本；
  - (1)(b) 遵守其他"基于资产或基于位置的元数据"的机读保留协议（即 TDMRep / Content Signals / RSL 这一层）；
  - (4) 承诺**公开自家爬虫身份、其 robots.txt 特性及所采用的权利保留识别措施**，并提供自动通知机制（如 web feed）；
  - (5) 同时运营搜索引擎者，应确保因遵守 TDM 保留而不至于连带影响该内容在搜索中的索引。
- **Measure 1.4**：技术手段防止模型输出复制受保护训练内容；在 AUP/条款中禁止侵权用途。
- **Measure 1.5**：设联系点，建立权利人投诉机制并勤勉、非任意、合理时限内处理。
- **口径警告（重要）**：本准则的**适用主体是"投放到欧盟市场的通用目的 AI 模型提供者"**，不是本项目这样的个人研究工具；且 Recital (a) 明说"adherence to the Code does not constitute compliance with Union law on copyright"。→ 我们把它当作**可得的最高水位"业界最佳实践清单"**引用，**不得**在文档里写成"本项目受该准则约束"或"符合该准则即合法"。

**D3. 英国：宽泛 TDM 例外已被放弃（2026-03-18 反转）**
- 一手：https://www.gov.uk/government/publications/report-and-impact-assessment-on-copyright-and-artificial-intelligence/report-on-copyright-and-artificial-intelligence （2026-03-18）
- 结论逐字："A broad copyright exception with opt-out is no longer the government's preferred way forward."；改为继续收集证据；承诺"work with industry and experts to develop best practice on **input transparency**"，但未立法。
- 现行法仍是 **CDPA s29A**（一手：https://www.legislation.gov.uk/ukpga/1988/48/section/29A）：合法访问者为**非商业研究**做计算分析的复制不侵权；须充分标注出处（除非实际不可行）；**副本转让给他人即侵权**（除非版权人授权）；**s29A(5)：任何试图排除或限制本条的合同条款不可执行。**
- 设计含义：s29A 是本项目 Tier A 在英国法下最干净的依据，但它**明确禁止把本地副本转给别人**——语料库不可分享、不可上传、不可作为附件交付。

**D4. 日本：Art.30-4 仍最宽，但边界在收窄**
- 一手条文入口 https://www.japaneselawtranslation.go.jp/en/laws/view/4207 本轮 **403 不可达**（标 `unverified`）；条文要点（信息分析等非"享受作品表达"目的的利用可自由，附"但不得不当损害著作权人利益"之但书）为业界共识，但**未从一手条文核实**。
- 文化厅《General Understanding on AI and Copyright in Japan》（2024-03-15，经 https://apaaonline.org/article/general-understanding-on-ai-and-copyright-in-japan/ 转述）：
  - 以输出特定作品创作性表达为目的的微调/过拟合 → **不落入 30-4**；
  - 以生成含原作创作性表达为特定意图而建 **RAG 数据库** → 不落入 30-4；RAG 更可能走 **Art.47-5**（"轻微利用"）；
  - 明知收集含侵权内容的训练数据者，"may be held liable for copyright infringement by the generative AI depending on the circumstances"；
  - "不当损害"但书的典型场景：**未付费使用专为 TDM 出售的数据库**；规避技术措施加重认定。
- 设计含义：本项目大量使用 RAG（检索证据喂给模型），在日本法下这部分**不能靠 30-4，应靠 47-5 的"轻微"限度** → 直接支持 Tier B 的短摘录设计。

**D5. 新加坡：s244 计算数据分析例外 + 正在推进的收紧**
- 现行法：Copyright Act 2021 ss.243–244；官方 SSO 页本轮 **403**。经 https://laws.sg/legislation/copyright-act-2021/section-244 复述：允许为计算数据分析而复制/准备材料，条件含 **合法访问**、对侵权副本的明知/应知限制、"flagrantly infringing online location"条款，且副本**不得移作他用**，交付他人仅限"verifying the results"或相关"collaborative research or study"。允许商业用途（无非商业限制）。
- 改革动向：新加坡法学院 2026-01/02 文件《Reform of the Computational Data Analysis Exception》（https://sal.org.sg/wp-content/uploads/2026/02/Reform-of-the-Computational-Data-Analysis-Exception-12-Feb-2026.pdf ，本轮 403）提议在 s244 增加拟制条款——**"X is deemed not to have lawful access to the first copy if access to the first copy is obtained in breach of a …"**（后续文字未取到）。
- **口径警告（本轮最大的一处不确定）**：现行 s244 **是否已经**把"违反数据库使用条款"写为丧失合法访问，二手复述与"仍需改革"的事实互相矛盾。**标 `unverified`，必须人工查 SSO 原文。**

**D6. 美国：合理使用可用，但取得渠道是硬门槛**
- 见 E 节（Bartz、Ross、Kadrey）。要点：训练/中间复制的转换性抗辩活着；**盗版取得的初始复制不受下游转换性用途庇护**；与原作构成市场替代的非生成式用途（Ross）不构成转换。

**D7. 中国：无 TDM 例外**
- 一手：《中华人民共和国著作权法》（2020 年第三次修正），https://www.gov.cn/guoqing/2021-10/29/content_5647633.htm
  - 第二十四条首句逐字："在下列情况下使用作品，可以不经著作权人许可，不向其支付报酬，但应当指明作者姓名或者名称、作品名称，并且不得影响该作品的正常使用，也不得不合理地损害著作权人的合法权益："
  - （一）"为个人学习、研究或者欣赏，使用他人已经发表的作品"
  - （二）"为介绍、评论某一作品或者说明某一问题，在作品中适当引用他人已经发表的作品"
  - （六）"为学校课堂教学或者科学研究，翻译、改编、汇编、播放或者少量复制已经发表的作品，供教学或者科研人员使用，**但不得出版发行**"
- 《生成式人工智能服务管理暂行办法》（七部门，2023-07-13 公布，2023-08-15 施行）第七条：依法开展预训练/优化训练等训练数据处理活动，"使用具有合法来源的数据和基础模型"；"涉及知识产权的，不得侵害他人依法享有的知识产权"。（官方口径见 https://www.cac.gov.cn/2023-07/13/c_1690898326863363.htm ；条文中译对照 https://www.chinalawtranslate.com/generative-ai-interim/ ）
- 设计含义（对用户写中文课程论文最直接）：**第 24 条是封闭列举，没有 TDM 项**。(一) 的"个人学习、研究"可以撑住"我自己读、自己分析"，但撑不住"建一个持久对外可查的语料库"；(六) 明确"不得出版发行"。→ **中文来源默认 Tier B/C，Tier A 只对开放许可（CC/OA）与用户自有文件开放。** 论文成稿中的引用走 (二) 适当引用，必须指明作者与作品名。

### E. 2025–2026 与"取得渠道可审计性"直接相关的判决

**E1. Bartz v. Anthropic（N.D. Cal.，No. C 24-05417 WHA，Order on Fair Use，Doc 231，filed 2025-06-23）**
- 一手 PDF 逐页直读：https://copyrightalliance.org/wp-content/uploads/2025/06/Bartz-v.-Anthropic-Order.pdf
- 事实（法院认定的数字，均来自判决书正文）：2021-01/02 下载 Books3（**196,640 册**）；2021-06 从 LibGen 下载 **at least five million** 册；2022-07 从 PiLiMi 下载 **at least two million** 册；合计"pirated **over seven million** copies of books"。后期另花数百万美元购入纸书，拆装订、切页、扫描成 PDF，丢弃纸质原件。
- 三段式认定：
  - **购书 → 拆扫成数字件**：第一要素**支持**合理使用。逐字："the mere conversion of a print book to a digital file to save space and enable searchability was transformative for that reason alone. Therefore, the digital copy should be treated just as if the purchased print copy had been placed in the central library."
  - **用于训练 LLM**：转换性，合理使用。
  - **从盗版站下载并留存进"中央图书馆"**：**不成立合理使用**。逐字："Such piracy of otherwise available copies is inherently, irredeemably infringing even if the pirated copies are immediately used for the transformative use and immediately discarded."；"Building a central library of works to be available for any number of further uses was itself the use for which Anthropic acquired these copies."；"the first factor points against fair use for the central library copies made from pirated sources — and no damages from pirating copies could be undone by later paying for copies of the same works."
- **对语料库工程最有杀伤力的一句**（法院在区分 HathiTrust/Google Books 时说）："The university libraries and Google went to exceedingly great lengths to ensure that all copies were secured against unauthorized uses — both through technical measures and through legal agreements among all participants. **Not so here. The library copies lacked internal controls limiting access and use.**"
- 脚注 7 另指出：若"保留至少一份副本是经与版权人合同授权的"（例如向查重服务提交时接受明示条款），情形会不同。→ **合同授权的留存是一条独立的、可主张的合法留存路径**。
- 和解（**注意这是对"盗版取得"这一支的和解，不是对"训练"的和解**）：金额 **$1.5B**；作品清单 **482,460 件**；每件约 **$3,000**（净额可能略高于 $3,100）；2025-09-25 初步批准；索赔截止 2026-03-30；**最终批准 2026-07-20**（法官 Araceli Martínez-Olguín）。
  - 口径冲突已记录：Authors Guild 页面（最后更新 2026-04-08，https://authorsguild.org/advocacy/artificial-intelligence/what-authors-need-to-know-about-the-anthropic-settlement/ ）载"最终批准听证 2026-05-14"、"约 500,000 titles"；较晚的多篇报道载最终批准日 2026-07-20、482,460 件、已就其中 440,490 件提出索赔（91.3%）。**以晚出的最终批准为准，但 482,460 与索赔率两个数字未取到法院文书一手，标 `unverified`。**

**E2. Thomson Reuters v. Ross Intelligence（D. Del.，2025-02-11）**
- 认定 2,243 条 Westlaw headnotes 具独创性；Ross 以之训练竞争性法律检索工具，**不构成转换性使用**，合理使用抗辩被驳（"Ross took the headnotes to make it easier to develop a competing legal research tool. So Ross's use is not transformative."）。
- 2026-06-11 第三巡回法院就该案进行口头辩论，成为**首个审理"AI 训练是否构成合理使用"的美国联邦上诉法院**（二手，标 `unverified`）。
- 设计含义：**非生成式、与原产品构成市场替代的用途，转换性抗辩最弱。** 本项目若把某数据库的结构化成果原样复刻成自家可检索资产（而不是产出分析结论），风险最高。

**E3. Kadrey v. Meta（N.D. Cal.）**
- 2025 年就训练部分作出有利于 Meta 的合理使用裁定（原告未能证明市场损害），但**围绕 torrent"做种"（seeding）过程中分发盗版作品的主张仍在继续**。→ 再次印证：分歧点在"取得与再分发"，不在"训练"。（二手，标 `unverified`）

**E4. NYT v. OpenAI 的保全令（对"本地留存"的反向警示）**
- 2025-05-13 Magistrate Judge Ona T. Wang 下令 OpenAI 保存并隔离**全部** output log；OpenAI 2025-06-06 上诉；2025-10-09 双方达成约定终止该持续保存义务。
- 设计含义：**"留存"是双刃的**——诉讼保全令能把你原本会删的东西钉死。本项目的 TTL/删除策略必须是**可暂停的**（legal hold 开关），而不是无条件定时销毁。

---

## 载荷数字核验表（数字 | 口径三元组 | 状态 | 一手出处）

| 数字 | 口径三元组（什么指标 / 什么样本或档位 / 与什么相比） | 状态 | 一手出处 |
|---|---|---|---|
| **200 字符** | Elsevier TDM 对外分发 snippet 的**每篇全文/书章节**长度上限 / 适用 ScienceDirect TDM API 的订阅机构非商业研究 / 是"围绕且**不含**匹配实体本身"的字符数 | `verified` | https://dev.elsevier.com/tdm_service.html （版本标注 24-August-2023）；https://www.elsevier.com/about/policies-and-standards/text-and-data-mining/license |
| **项目结束即"immediately and permanently delete all copies (including back-ups)"，仅 TDM Output 可留** | Elsevier 数据集本地留存义务 / ScienceDirect TDM 通道 / 与"可无限期保留"相对 | `verified` | 同上 dev.elsevier.com |
| **"duration of the TDM project"** | Springer Nature 机构授权内容的本地留存期上限 / 机构 TDM License 项下 / 与 CC BY OA 内容的无期限相对 | `verified` | https://dev.springernature.com/terms-conditions/ |
| **2026-09-15** | Cloudflare 默认值变更生效日 / 适用**新接入域名 + 现有客户新建站点 + 未改设置的现有免费客户**，且**仅在展示广告的页面上** / 变更内容 = 阻断 Training+Agent、放行 Search | `verified` | https://blog.cloudflare.com/content-independence-day-ai-options/ （2026-07-01）；新闻稿同日 |
| **3.8M+ 域名** | 被 Cloudflare 批量写入 `Content-Signal: search=yes, ai-train=no` 的域名数 / 样本 = **已使用 managed robots.txt 功能**的域名，非全部 Cloudflare 域名 / 与"Cloudflare 覆盖 20%+ 网域"不是同一分母 | `verified`（厂商自述） | https://blog.cloudflare.com/content-signals-policy/ （2025-09-24） |
| **HTTP 402 + `crawler-price` / `crawler-max-price` / `crawler-charged`** | Pay Per Crawl 的协议原语 / private beta 客户 / Ed25519 + RFC 9421 签名 | `verified` | https://blog.cloudflare.com/introducing-pay-per-crawl/ （2025-07-01） |
| **Pay Per Crawl 仍为 private beta（截至 2026-08-14）；无公开 list price** | 功能可用性档位 / Cloudflare 全平台 / 与"已 GA/已定价"相对 | `verified` | https://developers.cloudflare.com/ai-crawl-control/ （Last updated 2026-08-14） |
| **"more than half of all web requests" 来自 bot/agent；"more than 20% of web domains"；"over 50% of crawl traffic … re-fetching unchanged pages"；50+ 内容许可协议** | Cloudflare 自报网络级统计 / Cloudflare 自身网络样本 / **无独立验证，属营销语境** | `unverified`（厂商声明） | 同 2026-07-01 博客/新闻稿 |
| **1 request / 3 seconds，单连接** | arXiv 遗留 API（OAI-PMH/RSS/arXiv API）速率上限 / 所有匿名用户 / 与 S3 批量通道（requester-pays）不同 | `verified` | https://info.arxiv.org/help/api/tou.html |
| **arXiv 元数据 CC0 1.0；全文不得自建服务器对外提供** | 许可档位 / 描述性元数据 vs 全文 e-print / 与"全部 arXiv 内容开放"相对 | `verified` | 同上 |
| **RSL 1.0，2025-12-10 Recommendation**（标准首发 2025-09-10） | 规范版本与日期 / RSL Technical Steering Committee 发布 / 与"已成 W3C/IETF 标准"相对——**不是** | `verified` | https://rslstandard.org/rsl |
| **draft-ietf-aipref-vocab，Date 2026-08-14，Expires 2027-02-15，intended status Proposed Standard，仍是 I-D** | 草案状态 / IETF AIPREF WG / 与"已成 RFC"相对——**尚未** | `verified`（口径已校正） | https://ietf-wg-aipref.github.io/drafts/draft-ietf-aipref-vocab.html ；https://datatracker.ietf.org/doc/draft-ietf-aipref-vocab/ |
| ⚠ 同一草案在 datatracker 上 **-06 显示 2026-04-27** | 版本日期 / datatracker 提交记录 vs github.io "latest" 渲染 / 两者相差约 4 个月 | `corrected`（并列记录，勿混用） | 同上两处 |
| **AIPREF 仅定义 2 个类别：`train-ai`、`search`；无偏好时默认 `unknown`** | 词表规模与默认值 / vocab 草案当前版本 / 与 RSL 的 6 值、Content Signals 的 3 值相比更窄 | `verified` | 同上 |
| **"Preferences do not themselves create rights, obligations, or prohibitions."** | AIPREF 对自身法律效力的表述 / 规范正文 / 与 Cloudflare 的"Art.4(3) express reservation"定位相对 | `verified` | 同上 |
| **RFC 9309** | robots.txt 的 IETF 文档号 / 被 GPAI CoP Measure 1.3(1)(a) 逐字点名 / 与"robots.txt 无标准"相对 | `verified`（经 CoP 一手 PDF 转引） | GPAI CoP Copyright Chapter PDF, Measure 1.3(1)(a) |
| **TDMRep：`tdm-reservation` 取 0/1，三种载体，W3C CG Final Report 2024-02-02** | 规范状态 / W3C **Community Group** 报告，非 W3C 标准 / 与 "W3C Recommendation" 相对——**不是** | `verified` | https://www.w3.org/community/reports/tdmrep/CG-FINAL-tdmrep-20240202/ |
| **DSM Art.3(2)：副本"may be retained for the purposes of scientific research, including for the verification of research results"** | 保留期上限 / **研究机构/文化遗产机构** + 合法访问 / 与 Art.4(2) 的"as long as is necessary"相对 | `verified` | https://www.legislation.gov.uk/eudr/2019/790/article/3 |
| **DSM Art.4(2)(3)：保留"as long as is necessary"；可被"machine-readable means"的明示保留排除** | 通用 TDM 例外的边界 / 任何主体、任何目的 / 与 Art.3 的不可合同排除相对 | `verified` | https://www.legislation.gov.uk/eudr/2019/790/article/4 |
| **UK 2026-03-18：宽泛 opt-out 例外被放弃** | 政策结论 / 英国政府 DUAA s137 报告 / 与 2024-12 咨询稿的"preferred option"相对——**已反转** | `verified` | https://www.gov.uk/government/publications/report-and-impact-assessment-on-copyright-and-artificial-intelligence/report-on-copyright-and-artificial-intelligence |
| **CDPA s29A(5)：排除本条的合同条款不可执行；副本转让即侵权** | 英国现行 TDM 例外的两条硬边界 / 非商业研究 + 合法访问 / 与 EU Art.4 可被 opt-out 相对 | `verified` | https://www.legislation.gov.uk/ukpga/1988/48/section/29A |
| **GPAI CoP Measure 1.2(1)(a)(b) / 1.3(1)(a)(b) / 1.3(4)** | 爬虫合规承诺清单 / **适用于投放欧盟市场的 GPAI 模型提供者签署方**，非个人研究工具 / 且 Recital (a) 明说遵守本准则≠符合欧盟版权法 | `verified`（口径已限定） | CoP Copyright Chapter PDF（WG1，PDF 创建 2025-08-01；准则 2025-07-10 公布） |
| **7,000,000+ 盗版册；Books3 = 196,640；LibGen ≥ 5,000,000（2021-06）；PiLiMi ≥ 2,000,000（2022-07）** | 法院认定的下载量 / Anthropic 中央图书馆 / 与"用于训练的册数"不同——法院强调并非全部用于训练 | `verified` | Bartz Order, Doc 231, filed 2025-06-23, pp.3 |
| **"inherently, irredeemably infringing even if … immediately used … and immediately discarded"** | 盗版取得的定性 / 美国 N.D. Cal. 地院 / 与"训练是合理使用"的另一支相对 | `verified` | 同上 p.19 |
| **"The library copies lacked internal controls limiting access and use."** | 法院区分 HathiTrust/Google Books 与本案的关键事实 / 同上 / 直接对应本项目的 ACL 设计 | `verified` | 同上 p.22 |
| **$1.5B / 482,460 件 / ~$3,000 每件 / 最终批准 2026-07-20** | 和解规模 / **仅针对盗版取得那一支**，训练合理使用认定不在和解范围 / 每件为分摊前毛额 | `unverified`（金额多源一致，件数与最终批准日未取到法院文书一手；Authors Guild 页 2026-04-08 仍载"约 500,000 titles / 5-14 听证"） | https://authorsguild.org/advocacy/artificial-intelligence/what-authors-need-to-know-about-the-anthropic-settlement/ + 多篇 2026-07 报道 |
| **Thomson Reuters v. Ross：2,243 条 headnotes 具独创性，非转换性** | 判决要点 / D. Del.，2025-02-11 / 与生成式训练案（Bartz/Kadrey）相区分 | `unverified`（未直读判决书） | 多篇执业提示，2025-02 |
| **新加坡 s244"违反数据库使用条款即无合法访问"** | 现行法条内容 / Copyright Act 2021 / **与 2026 年改革提案的拟增条款可能重叠** | `unverified` — **矛盾未决** | 复述见 https://laws.sg/legislation/copyright-act-2021/section-244 ；官方 sso.agc.gov.sg 本轮 403 |
| **日本 Art.30-4 条文与但书** | 条文原文 / 日本著作权法 / — | `unverified`（一手 japaneselawtranslation.go.jp 403） | 文化厅立场经 https://apaaonline.org/article/general-understanding-on-ai-and-copyright-in-japan/ （2024-03-15） |
| **Wiley TDM：非商业 + ORCID token + 仅官方 API** | 许可条款 / Wiley Online Library 订阅机构 / — | `unverified` — 一手站点对本抓取器返回 **402 / 522** | https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining （402）；https://olabout.wiley.com/WileyCDA/Section/id-826542.html （522） |
| **中国著作权法第 24 条 (一)(二)(六) 原文** | 合理使用封闭列举 / 2020 年第三次修正版 / 与 EU/UK/JP 的 TDM 例外相对——**中国没有对应项** | `verified` | https://www.gov.cn/guoqing/2021-10/29/content_5647633.htm |
| **《生成式人工智能服务管理暂行办法》第七条"合法来源"** | 训练数据合规义务 / 2023-07-13 公布、2023-08-15 施行 / 主体是"服务提供者"，非个人研究者 | `verified` | https://www.cac.gov.cn/2023-07/13/c_1690898326863363.htm |

**促销价 / 引导价 vs 目录价专项标注**：本维度**没有任何可用的公开定价**。Cloudflare Pay Per Crawl / Pay Per Use 至 2026-08 仍为 private beta，官方从未公布单价或价目表；出版商 TDM 授权在机构订阅内不另收费，机构外按个案报价。**任何写着"每次抓取 $0.0X"的数字都不要采信，本项目的成本模型在这一层应记为"未定价 / 需谈判"。**

---

## 对本项目的设计含义

### 一、三档证据快照策略（Three-Tier Evidence Snapshot Policy）

设计原则：**档位由"取得渠道 + 权利信号"决定，不由"内容有多有用"决定。** 决策发生在 fetch 时刻，结果写进 provenance 记录并不可事后上调（只能下调）。

---

#### **Tier A — 全量本地快照（full local snapshot）**

*可长期保存原始字节 + 全文文本 + 可复跑的解析产物；可进入本地向量库；可反复重读；构成"可再分析"承诺的物质基础。*

**准入条件（必须命中至少一条，且不得命中任何降级触发器）：**

| 依据 | 具体情形 | 法律基础 |
|---|---|---|
| A1 开放许可 | CC0 / CC BY / CC BY-SA / CC BY-NC（且下游标注为非商业）/ 公共领域 | 许可本身；Springer Nature 对 OA 内容明示允许 TDM |
| A2 授权 TDM 通道 | Elsevier TDM API、Springer Nature API（机构 TDM License）、Wiley TDM API、其他机构订阅的官方 TDM 端点 | 合同授权。**注意 Bartz 脚注 7 承认"合同授权的留存"是独立正当路径** |
| A3 开放学术基础设施 | arXiv 元数据（CC0）、OpenAlex（CC0）、Crossref 元数据、PMC OA subset、Semantic Scholar（**仅内部非商业，不可再分发**） | 各自条款 |
| A4 用户自有材料 | 用户合法购买/机构订阅下载的 PDF、自己的课件与讲义、导师提供的材料 | Bartz："the person who purchases the textbook owes no further accounting for keeping the copy"；格式转换本身可转换（print→digital "transformative for that reason alone"） |
| A5 法域例外 | EU DSM Art.3（研究机构 + 合法访问，**可长期保留含结果验证**）；UK s29A（非商业研究，**副本不得转让**）；SG s244；JP Art.30-4（非"享受"目的） | 见 D 节 |

**Tier A 的强制附加约束（直接来自 Bartz 的减分点）：**
- **必须有内部访问控制**：语料目录不可被"全库导出"；每条记录带 purpose tag；跨项目复用需显式授权动作并留痕。
- **必须有 TTL**：A2 渠道的记录带 `delete_on_project_end = true` + `ttl_expires_at`；到期自动降级为 Tier B（保留摘录与哈希）而非静默续期。
- **必须可被 legal hold 暂停删除**（NYT v. OpenAI 保全令的教训）。
- **不得外发**：UK s29A 明文禁止转让副本；Semantic Scholar 明文禁止再分发。→ **Tier A 的原始件永远不进交付物、不进 Artifact、不进任何对外分享链接。**

---

#### **Tier B — 短摘录 + 锚点（short excerpt + anchor）**

*只保存有限长度的引文、其在源文档中的精确定位锚点、以及回链；这是本项目**默认档**，也是唯一可以进入最终论文/报告的原文形态。*

**保存内容：** 摘录文本（受硬上限约束）+ 起止偏移 + 页码/段落/XPath/PDF quad-point + DOI/canonical URL + 内容哈希 + 抓取时间。

**硬上限（取所有适用规则中最严者）：**
- 命中 Elsevier 渠道 → **≤200 字符**（"围绕且不含匹配实体本身"）+ 必须附 DOI 回链 + 专有权声明。
- 一般来源 → 默认 **≤300 字符 / 单条**，同一文献累计 **≤1,200 字符**，且不得覆盖该文献任一连续章节的实质部分（避免拼接重构）。
- 中文来源 → 走著作权法第 24 条 (二)"适当引用"，**必须指明作者姓名/名称与作品名称**；单条 ≤200 字。
- 日本法域考量 → RAG 用摘录靠 Art.47-5"轻微利用"而非 30-4，因此摘录长度与用途都应保持"轻微"。

**法律基础：** 引用/适当引用（中国 24(2)、Berne 10(1)、US fair use quotation）；Cloudflare `search` 信号的定义本身即包含"short excerpts"；Elsevier/Springer 的 snippet 分发许可；日本 Art.47-5。

---

#### **Tier C — 仅元数据 + 哈希（metadata + hash only）**

*不保存任何受版权保护的表达。只保存：URL、DOI、标题、作者、年份、期刊/来源、摘要**指针**（不是摘要文本，除非许可允许）、内容哈希（SHA-256）、字节长度、抓取时间戳、HTTP 状态与权利信号头。*

**用途：** 记录"这个证据存在过、我看过、内容是这一份"；支持后续人工复核；支持"曾被拒绝"的负面记录。

**法律基础：** 事实与书目元数据不受著作权保护；Crossref/OpenAlex 元数据 CC0；哈希是不可逆摘要而非复制件。

**注意（未决风险）：** 欧盟**数据库特殊权利**（sui generis，Directive 96/9/EC）独立于著作权，对数据库"实质部分"的系统性提取可能构成侵权——**即使内容本身是事实**。本轮未核实其对本项目规模的适用性，标为未决。

---

### 二、fetcher 必须硬编码的降级触发器

按顺序求值；任一命中即执行对应动作，且**只能下调，不能上调**。每次触发都要把规则 ID 写进 provenance 的 `tier_reason[]`。

| ID | 触发条件 | 动作 | 依据 |
|---|---|---|---|
| **T0-HARD** | 目标域名/镜像命中影子图书馆名单（LibGen、Sci-Hub、Anna's Archive、Z-Library、PiLiMi、Books3 及其已知镜像），或命中"经欧盟/EEA 法院或公权机关认定的持续、重复、商业规模侵权站点"名单 | **硬拒**：不发请求；只写一条"候选被拒"事件记录（不含内容），并向用户报告该证据无法取得 | Bartz："inherently, irredeemably infringing"；GPAI CoP Measure 1.2(1)(b) |
| **T1-AUTH** | 响应 401 / 403 / 407，或检测到登录墙/付费墙/DRM/TPM | 降至 **Tier C**；**绝不尝试任何绕过**（不换 UA 伪装、不用 cookie 走私、不试镜像站、不试 12ft/archive 类去墙服务） | GPAI CoP 1.2(1)(a) 不得规避 TPM 与付费墙；SG s244 合法访问；JP 但书；US CFAA 风险面 |
| **T2-402** | 响应 **402 Payment Required**（含 `crawler-price`） | 降至 **Tier C**，标记 `paid_access_available = true`，**不自动付费**，交由用户决定 | Cloudflare Pay Per Crawl 协议 |
| **T3-ROBOTS** | robots.txt（RFC 9309）对本 UA 的 `Disallow` 命中，或 robots.txt 抓取失败且站点历史上有过 Disallow | **不抓取**；写 Tier C 记录（URL 来自检索索引，非抓取） | GPAI CoP 1.3(1)(a) 逐字要求 |
| **T4-SIGNAL-TRAIN** | robots.txt 含 `Content-Signal: ai-train=no`，或 `tdm-reservation: 1`（header/meta/.well-known），或 RSL `ai-train` 需付费/需授权 | 禁止 Tier A；且该条证据**永久禁止**进入任何微调/训练管线；最高 Tier B | DSM Art.4(3) 明示保留；Cloudflare Content Signals 自我定位 |
| **T5-SIGNAL-INPUT** | `Content-Signal: ai-input=no`，或 RSL `ai-input` 需授权 | 该条证据**不进 RAG 上下文**；降至 **Tier C**（只留可读的引用指针，由人去读） | 同上 |
| **T6-TTL** | 来源为出版商 TDM 通道（Elsevier/Springer/Wiley 等） | Tier A 但强制 `delete_on_project_end = true` + `ttl_expires_at`；到期自动降 Tier B | Elsevier"immediately and permanently delete"；SN"duration of the TDM project" |
| **T7-LEN** | 任何进入交付物的摘录 | 按最严上限截断（Elsevier 渠道 200 字符；一般 300 字符；中文 200 字并强制标注作者与作品名） | Elsevier snippet 条款；中国著作权法 24(二) |
| **T8-NC** | 许可为 CC BY-NC / 出版商非商业 TDM 许可，而项目被标注为商业用途 | 降至 **Tier B**，并在报告中打"非商业限定"标记 | CC BY-NC；Elsevier/Wiley/Semantic Scholar 非商业条款 |
| **T9-RATE** | 单域名请求速率超阈值（arXiv：1 req / 3s 且单连接；一般：1 req/s，并发 1，指数退避；429/503 立即退避） | 退避重试；连续失败 → Tier C | arXiv ToU；避免被认定为滥用/加重 CFAA 风险 |
| **T10-CN** | 来源为中国大陆商业网站/中文出版物且非开放许可 | 默认 **Tier B**（适当引用）；Tier A 仅对 CC/OA 与用户自有文件开放 | 中国著作权法第 24 条为封闭列举，无 TDM 例外 |
| **T11-JURIS-EU3** | 若项目未声明使用者属于 DSM Art.3 意义上的 research organisation | Tier A 的法律依据不得引用 Art.3；改依 A1/A2/A4，或按 Art.4"as long as is necessary"设 TTL | DSM Art.3 主体限定 |
| **T12-UNREACHABLE** | 一手源返回非 2xx、空正文、或被识别为反爬拦截页 | **写 `unverified` 状态并如实上报**；**禁止**用博客/聚合站的转述替代一手源来"补齐"数字 | 本轮实测：Wiley 402、SSO/SAL/irishstatutebook/japaneselawtranslation 403、EUR-Lex 空体；且这正是上一轮口径失真的机制 |
| **T13-HOLD** | 存在 legal hold 标记 | 暂停一切自动删除与 TTL 降级，直到人工解除 | NYT v. OpenAI 保全令 |

**身份策略（与上表配套）：** 抓取器使用固定、可识别的 User-Agent，并**准备好** Web Bot Auth（Ed25519 + `Signature-Agent`/`Signature-Input`/`Signature`，RFC 9421）。**不伪装浏览器**。理由：GPAI CoP 1.3(4) 把"爬虫身份可被权利人发现"列为承诺；伪装同时削弱一切善意抗辩、放大 ToS 违约与 CFAA 面。代价是命中更多 403 —— 这是设计上接受的代价，由 T12 转成诚实的 `unverified` 而不是伪造的"已核实"。

---

### 三、必须记录的 provenance 字段（让取得渠道可审计）

每条证据记录一份不可变的 `acquisition_record`，追加写入（append-only），与证据内容分离存储。

**① 请求与响应**
- `url_requested`、`url_final`、`redirect_chain[]`
- `http_status`、`fetched_at`（UTC ISO-8601）、`elapsed_ms`
- `response_headers_subset`：`content-type`、`etag`、`last-modified`、`link`、`tdm-reservation`、`tdm-policy`、`crawler-price`、`x-robots-tag`

**② 抓取者身份（Bartz 的"who did what"）**
- `fetcher_version`、`user_agent`、`signature_agent`（Web Bot Auth 密钥目录 URL / key id）
- `operator`（用户标识）、`project_id`、`run_id`、`agent_id`（哪个子 agent 发起）

**③ 取得渠道（本设计的核心字段）**
- `channel`：枚举 `open_license` | `publisher_tdm_api` | `institutional_proxy` | `public_web` | `search_api`（serper/bocha）| `user_supplied_file` | `licensed_dataset`
- `channel_credential_ref`：**只存引用与机构名，绝不存明文凭据**
- `purchase_or_subscription_ref`：若为 A4，记录订阅/购买凭证的引用（不是凭证本身）
- `acquisition_cost`：`free` | `covered_by_subscription` | `paid`（含金额与凭据引用）| `refused_paywall`

**④ 权利信号快照（判定当时的现场证据）**
- `robots_txt_url`、`robots_txt_hash`、`robots_fetched_at`、`robots_decision`（`allowed` / `disallowed` / `absent`）、`robots_matched_rule`
- `content_signal_raw`（原始 `Content-Signal:` 行）
- `tdmrep`（来源：header / meta / well-known；值 0/1；`tdm-policy` URL）
- `rsl_license_url` 与解析出的 usage/payment 类型
- `license_from_crossref`（Crossref 元数据里的 license URL 与 `applies_to`）
- `cc_license_id`（若可判定）

**⑤ 档位判定（可复核的决策链）**
- `tier`：`A` | `B` | `C` | `REFUSED`
- `tier_reason[]`：命中的规则 ID 列表（T0…T13）
- `legal_basis[]`：援引的依据 ID（A1…A5 / 24(二) / s29A / Art.3 / Art.4 / s244 / 30-4 / 47-5 / fair use）
- `decided_by`（规则引擎版本）、`decided_at`
- `downgraded_from`（若曾更高档）与降级时间戳

**⑥ 内容指纹与留存**
- `content_hash`（原始字节 SHA-256）、`normalized_text_hash`、`byte_length`
- `stored_path`（Tier A/B）或 `null`（Tier C）、`encrypted`、`acl`（谁/哪个 project 可读）
- `ttl_expires_at`、`delete_on_project_end`、`legal_hold`（bool + 设置人 + 时间）
- `deleted_at` + `deletion_attestation`（删除也要留证——证明确实执行了 Elsevier 那句"immediately and permanently delete"）

**⑦ 摘录锚点（Tier B 专属）**
- `excerpt_text`、`char_len`、`start_offset`、`end_offset`
- `anchor`：`page` / `paragraph_index` / `xpath` / `pdf_quad_points` / `section_heading`
- `doi`、`canonical_url`、`attribution_string`（作者姓名/名称 + 作品名，中文引用强制）
- `snippet_cap_applied`（哪条上限规则生效）

**⑧ 链路与结论绑定**
- `parent_record_id`（从某次 API 结果衍生时）
- `claim_ids[]`：这条证据支撑了哪些结论（与本项目"每条 claim 带 verified/unverified"的核心机制对接）
- `metric_frame`（当证据是一个数字时）：`{ what_metric, on_what_sample_or_tier, compared_to_what }` —— **把本轮的方法规则固化成数据结构**
- `corroboration_group_id`：用于识别"伪独立佐证"——多个 URL 若可追溯到同一上游，归入同一组，**计为一个来源**

**⑨ 完整性**
- append-only 日志（每条记录带前一条的哈希，形成链）；本地即可，无需外部时间戳服务

---

### 四、与本项目其他层的接口

- **与"machine-decided verified/unverified"机制**：`tier` + `legal_basis` + `metric_frame` + `corroboration_group_id` 是判定器的输入。规则："一个数字若只有 Tier C 记录、或所有支撑记录同属一个 `corroboration_group_id`、或 `tier_reason` 含 T12-UNREACHABLE → 强制 `unverified`。"
- **与"可再跑的数据分析"**：Tier A 是唯一能支撑"重跑得到同样结果"的档位；因此项目应主动**把选题引向 A1/A3/A4 密集的领域**（OA 论文、公开数据集、用户自有材料），而不是在付费墙上硬碰。这是策略层结论，不只是合规层。
- **与交付物**：Artifact / 论文 / 报告里只允许出现 Tier B 的摘录与 Tier C 的元数据。**Tier A 的原始件永不外发。**
- **与中文写作场景**：中文引用默认走第 24 条 (二)，模板必须自动生成"指明作者姓名或者名称、作品名称"的标注；(六) 的"不得出版发行"意味着为课程/科研少量复制的材料不可公开发布。

---

## 未决与风险

1. **【高】新加坡 s244 现行文本存在直接矛盾。** 二手复述称条文已含"违反数据库使用条款即无合法访问"，但 SAL 2026-01/02 的改革文件又在提议增加该拟制条款。官方 `sso.agc.gov.sg` 对本抓取器返回 403。**在把"违反 ToS = 无合法访问"写成新加坡法域规则前，必须人工登录 SSO 核对 s244 全文。**

2. **【高】使用者是否算 DSM Art.3 的 "research organisation"。** Art.3 是本项目"长期保留 + 结果验证"最贴合的依据（其文字几乎就是本项目的产品定义），但主体限于研究机构与文化遗产机构。个人学生/自由研究者大概率**不**满足，退回 Art.4 的"as long as is necessary" + 可被 opt-out。→ 建议：Tier A 的默认法律依据设为 A1/A2/A4（许可与合同），把 Art.3 作为"用户声明其机构身份后才启用"的可选依据。

3. **【中】Wiley TDM 条款未经一手核实**（站点对自动抓取返回 402/522）。现有复述多源同文（STM 样板许可转述），属伪独立佐证。

4. **【中】日本 Art.30-4 条文原文未一手核实**（japaneselawtranslation.go.jp 403）。文化厅立场经协会转述取得，方向可信但措辞未核。

5. **【中】欧盟数据库特殊权利（sui generis，Dir. 96/9/EC）本轮完全未覆盖。** 它独立于著作权，针对"实质部分"的系统性提取，对大规模抓取学术数据库可能是比著作权更直接的风险点。**建议补一轮专项调研。**

6. **【中】Bartz 和解的两个数字（482,460 件、最终批准 2026-07-20）未取到法院文书一手**，且与 Authors Guild 页面（2026-04-08 更新，载"约 500,000 titles"、"最终批准听证 2026-05-14"）冲突。已按"晚出为准 + 标 unverified"处理。

7. **【中】Cloudflare 2026-09-15 默认值的实际影响面无法预估。** 它只作用于"展示广告的页面"，而学术站点大多不展示广告；但"mixed-use 按最严格类别判定"这条可能把很多通用爬虫一并卡住。**本项目应在 2026-09-15 后重测一次目标站点集的可达性**，把它作为一个定期回归项。

8. **【中】GPAI 行为准则的引用口径极易被拉伸。** 它约束的是投放欧盟市场的 GPAI 模型提供者，不是个人研究工具，且明说"遵守 ≠ 合规"。本文已把它限定为"最佳实践清单"。**后续文档若把它写成"本项目适用/符合该准则"即为口径失真，应在 attacker 轮次专门检查这一点。**

9. **【中】Content Signals / RSL / TDMRep / AIPREF 四套信号语义不完全对齐**（类别数分别为 3 / 6 / 1 / 2），且优先级无标准规定。本项目需要自定一套合并规则（建议：**取交集中最严格者**），并把该规则显式写进 `decided_by`，以便日后标准收敛时可重放。

10. **【低但会持续恶化】一手法律与出版商源对自动抓取的敌意在上升。** 本轮 6 个一手源被拒。这直接压低本项目"verified"的达成率。**对策不是绕过，而是（a）把"人工核对队列"做成一等产物——机器把无法自动核实的条目整理成带 URL 与待验证问题的清单交给用户；（b）在 Artifact/报告里如实显示 `unverified` 并说明原因。** 这恰恰是本项目"credibility 即产品"的正确表达。

11. **【低】Pay Per Crawl 无任何公开定价**，成本模型在这一层只能记"未定价"。若日后 GA 并公布价目，需重新评估"付费取得 → 升 Tier A"这条路径是否值得自动化。
