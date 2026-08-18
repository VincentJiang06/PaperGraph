# 外部调研 v2 · 成本经济学（provider-specific）

- 调研日期：**2026-08-17**
- 维度：成本经济学 — DeepSeek 为主 provider，Anthropic / OpenAI / Google 仅作机制对照
- 方法约束：所有载荷数字必须回到**一手来源**（官方定价页 / 官方文档 / 论文原文），记录**口径三元组**（什么指标 / 在什么样本或档位上 / 与什么相比），并标注 `verified | corrected | unverified`
- 搜索轮次：14 条不同查询（WebSearch ×4，serper ×10），随后逐条回一手页面抓取

---

## 结论摘要

**1. 本轮最大的发现是一个时间炸弹：DeepSeek 在 2026-08-16 16:00 UTC（即本文写作前约 24 小时）刚刚完成一次全线涨价并改为分时计价。** 网上几乎所有"2026 年 DeepSeek 定价"文章（包括 2026-08 月份新写的）报的仍是旧的统一价 `v4-pro $0.435/$0.87`、`v4-flash $0.14/$0.28`。这些数字**今天全部作废**。任何沿用它们的成本模型会低估 1.5×–12× 不等。

**2. DeepSeek 新价卡是一个"三的幂"结构，非常干净，可直接写进代码：**
- 输出价 = 缓存未命中输入价 × **3**
- pro 各行 = flash 各行 × **3**（CNY 口径精确为 3，USD 口径因四舍五入有 ±5% 偏差）
- 缓存未命中输入价 = 缓存命中输入价 × **30**
- 峰时价 = 谷时价 × **2**

于是全部价格由一个基准数 `$0.22 /1M`（flash 谷时 cache-miss 输入）× {1,3} × {1,2} × {1,1/30, 3} 生成。

**3. 三个成本杠杆在 DeepSeek 上的可用性（这是上一轮出错的地方，本轮明确纠正）：**

| 杠杆 | 在 DeepSeek 上 | 机制 | 最大幅度 |
|---|---|---|---|
| **Prompt caching** | ✅ **可用** | 磁盘 KV cache，**默认开启、无需改代码、无写入费、无存储费** | 命中部分降至 **1/30**（≈ 96.7% off） |
| **模型分层** | ✅ **可用** | `deepseek-v4-flash` / `deepseek-v4-pro` | 精确 **3×** |
| **离线批处理（Batch API）** | ❌ **不存在** | 官方文档导航、定价页、Rate Limit 页均无 batch 条目/档位 | — |

**DeepSeek 没有 Batch API。** Anthropic / OpenAI / Google 三家都有且都是 **50% off**——这正是"套用他家数字"最容易踩的坑。DeepSeek 的功能替代品是**分时谷时计价**（同样约 2× 杠杆），但二者性质完全不同：Batch API 是"提交作业、异步取回、换取折扣"，谷时是"在特定钟点发同步请求"。谷时**不提供任何吞吐豁免**，并发限制照旧、超限直接 429 且无排队。因此我们必须自建调度器，而不能指望 provider 排队。

**4. 谷时窗口对中国时区的用户异常友好。** 峰时仅 `01:00–04:00` + `06:00–10:00 UTC` = **7 小时/天**，其余 **17/24 小时（70.8%）为谷时**。换算北京时间，峰时是 **09:00–12:00 与 14:00–18:00**——正好是上班/上课时间。也就是说：**中午 12–14 点、傍晚 18 点以后到次日早 9 点，全部半价。** 本项目的重型 fan-out 勘探跑批天然应该压在夜里。

**5. 在 DeepSeek 的价格水平上，搜索 API 费用会反超 token 费用成为第一成本项。** Simon Willison 实测的一次 deep research 运行总花费 $1.10，其中 **$0.77（70%）是 77 次网页搜索的调用费**，token 只占 $0.304。我们用 serper（$1/千次量级）比 OpenAI 内置搜索（$10/千次）便宜一个数量级，但 DeepSeek 的 token 也比 GPT 便宜一到两个数量级，所以这个"搜索费占大头"的结构在我们这里**依然成立甚至更极端**。成本治理的第一优先级应该是**搜索调用预算**，不是 token 预算。

**6. 多智能体的 token 倍数只有一个可引用的一手数字：Anthropic 的 "agents ≈ 4× chat，multi-agent ≈ 15× chat"。** 但它的口径极窄（Anthropic 自家 Research 系统、BrowseComp 评测、2025-06 发表，至今已 14 个月），**不能当作普适定律**。同文更有用的是它的两个条件句：token 用量单独解释了 **80%** 的性能方差；以及多智能体"要求任务价值高到足以支付增加的性能开销"。

---

## 逐条发现（含 URL）

### A. DeepSeek 官方定价（一手，2026-08-17 抓取）

**A1. 现行价卡（USD / 1M tokens），生效 2026-08-16 16:00 UTC**

> **〔独立复核 · 2026-08-18〕本价卡今日重新抓取一手页，六格单价与两个规格逐个吻合，零改动。**
> 复核项：flash 命中 $0.007/$0.014、未命中 $0.22/$0.44、输出 $0.66/$1.32；
> pro 命中 $0.022/$0.044、未命中 $0.66/$1.32、输出 $1.98/$3.96；上下文 1M、最大输出 384K；
> 峰时窗口 `01:00–04:00` + `06:00–10:00 UTC` 逐字未变。
> **F-25 `as-of-stale` 时钟据此重置到 2026-08-18。**
>
> 复核同时**独立佐证了两条此前只有单一依据的判断**：
> 1. 一手页**通篇没有把前一版价格描述为促销价 / introductory / 限时价**——与 §A4「这是真正的目录价上调、不是促销到期」一致。
>    对照：同期核对的另一家厂商恰好相反，其一手页明确写着某型号的限时价**已转正、原定涨价不会发生**。
>    两个方向的实例并列说明：**「限时价」这个标签本身既可能转正也可能落地，不能从标签推断未来价格。**
> 2. 一手页**只列 USD、不列 CNY**——§A5 里那组人民币目录价（来自二手 TechNode）**至今没有一手对应物**，
>    其 `unverified` 标注应保持，不得因为「算术自洽」而升级为 `verified`。


来源：<https://api-docs.deepseek.com/quick_start/pricing>（同一页抓取两次，结果一致）

| | deepseek-v4-flash | deepseek-v4-pro |
|---|---|---|
| 输入（缓存命中，谷时） | $0.007 | $0.022 |
| 输入（缓存命中，峰时） | $0.014 | $0.044 |
| 输入（缓存未命中，谷时） | $0.22 | $0.66 |
| 输入（缓存未命中，峰时） | $0.44 | $1.32 |
| 输出（谷时） | $0.66 | $1.98 |
| 输出（峰时） | $1.32 | $3.96 |

原文："The prices listed below are in units of per 1M tokens."
原文："Peak hours are 01:00 - 04:00 and 06:00 - 10:00 UTC (all other hours are off-peak)."

上下文长度 **1M**，最大输出 **384K**。同时提供 OpenAI 格式与 Anthropic 格式接口。

**A2. 独立交叉验证（CNY 口径）**

来源：<https://technode.com/2026/08/14/deepseek-to-introduce-peak-and-off-peak-pricing-for-its-api/>

TechNode 报的是人民币目录价：flash 峰时 ¥0.10 / ¥3 / ¥9，谷时 ¥0.05 / ¥1.5 / ¥4.5；pro 峰时 ¥0.30 / ¥9 / ¥27，谷时 ¥0.15 / ¥4.5 / ¥13.5。

**这是一次真正的独立交叉验证，不是同源复读**：CNY ÷ USD 在全部 12 个数上都精确等于 **6.818**（9/1.32 = 6.818，27/3.96 = 6.818，0.30/0.044 = 6.818 …）。两套数字来自不同语言、不同发布渠道，却完全自洽 → 官方 USD 表可信。

同时 TechNode 报的峰时窗口是"北京时间 9 点–12 点、14 点–18 点"，换算 UTC+8 后 = `01:00–04:00` + `06:00–10:00 UTC`，与官方文档**完全吻合**。

**A3. 涨价幅度与旧价**

来源：官方公告 <https://api-docs.deepseek.com/news/news260813>，原文："New pricing takes effect at 16:00 UTC, Aug 16, 2026"、"we're updating our API pricing and introducing peak and off-peak rates. Off-peak rates are 50% lower than peak"。

**关键判定：DeepSeek 在公告中【没有】把旧价描述为促销价 / introductory / 限时价。** 这是一次真正的目录价上调，不是促销到期。（对照组：Anthropic 明确使用 introductory 措辞，见 D1。）

旧价（统一价，无分时）来自二手报道，官方页面已下线，标记为 `unverified（二手）`：pro $0.435 in / $0.87 out / $0.003625 cache-hit；flash $0.14 / $0.28 / $0.0028。

推导涨幅（旧价若成立）：

| 行 | pro 谷时 | pro 峰时 | flash 谷时 | flash 峰时 |
|---|---|---|---|---|
| 输出 | 2.28× | **4.55×** | 2.36× | 4.71× |
| 输入（miss） | 1.52× | 3.03× | 1.57× | 3.14× |
| 输入（hit） | 6.07× | **12.14×** | 2.50× | 5.00× |

12.14× 即 +1,114%，与 Qz 头条 "raising API prices by up to 1,100%" 算术自洽（<https://qz.com/deepseek-api-price-increase-v4-peak-off-peak-081326>），与 Engadget "four times pricier"（对应输出峰时 4.55×）也自洽。三个独立媒体的三个不同头条数字都能由同一组新旧价推出 → 旧价数值可信度提高，但仍非一手。

**注意涨价结构的方向：涨得最狠的是缓存命中输入（12×），涨得最轻的是缓存未命中输入（3×）。** 这直接削弱了 prompt caching 这个杠杆的绝对收益——虽然相对折扣仍有 96.7%，但缓存命中的**绝对单价**上涨了一个数量级。对于我们这种反复重放长 system prompt 的多轮 agent 系统，这是最痛的一刀。

其他报道：
- Fortune <https://fortune.com/2026/08/13/deepseek-increases-prices-for-ai-services-by-multiple-times/>
- InfoWorld <https://www.infoworld.com/article/4209439/deepseek-raises-some-v4-prices-by-more-than-10x-as-ai-demand-strains-capacity/>
- PYMNTS <https://www.pymnts.com/news/artificial-intelligence/2026/deepseek-introduces-peak-hour-pricing-that-quadruples-current-levels/>

以上四家在同一时间窗报道同一份 DeepSeek 公告，**属于同一上游的复读，不构成四个独立信源**（本轮方法规则明确要求警惕的"虚假独立佐证"）。真正独立的只有 TechNode 的 CNY 口径（不同币种、可做算术闭合校验）。

**A4. Context Caching 机制（一手）**

来源：<https://api-docs.deepseek.com/guides/kv_cache>

- **默认对所有用户开启，无需改代码**（"enabled by default for all users"）
- 磁盘缓存，按请求边界切分 cache prefix unit，**必须完全匹配**（"fully matches"）某个已持久化的前缀单元才算命中
- **无最小可缓存长度的文档说明**（与 Anthropic 的 1024/2048 token 下限形成对比）
- **TTL 不保证**："Once the cache is no longer in use, it will be automatically cleared, usually within a few hours to a few days."
- **无写入费、无存储费**（文档未提及任何 cache write / storage 计费项）
- **best-effort，不保证命中**："The cache system works on a 'best-effort' basis and does not guarantee a 100% cache hit rate."
- 回传字段：`usage.prompt_cache_hit_tokens` / `usage.prompt_cache_miss_tokens`

→ **这两个字段是我们做成本审计的唯一可信来源，必须逐次记账。**

**A5. 并发与限流（一手）**

来源：<https://api-docs.deepseek.com/quick_start/rate_limit>

- `deepseek-v4-pro`：**500 并发**
- `deepseek-v4-flash`：**2500 并发**
- 账号级限制，与使用哪个 API key 无关
- 超限 → **HTTP 429，无排队机制**
- 可申请扩容，**"no additional cost"**
- 扩容账号下每个 `user_id` 各自独立享有同样的并发额度（500 / 2500）

→ 对"hyper-parallel"设计是极好的消息：2500 路 flash 并发意味着我们的扇出宽度**不会被 provider 限住**，瓶颈会先出现在搜索 API 和本机。但没有排队 = 我们必须自己实现并发闸门与退避。

**A6. Tokenizer 换算（一手，对中文写作重要）**

来源：<https://api-docs.deepseek.com/quick_start/token_usage>

- "1 English character ≈ 0.3 token"（即约 3.33 英文字符/token）
- "1 Chinese character ≈ 0.6 token"（即约 1.67 汉字/token）
- 文档明确这是近似值，精确计数以回传 usage 为准或用官方离线 tokenizer

→ 一篇 1 万字中文课程论文 ≈ **6,000 输出 token**，在 pro 谷时 = 6,000 × $1.98/1M = **$0.0119**。**中文成稿本身的 token 成本可以忽略不计。**本项目的成本全在勘探与核验阶段，不在写作阶段——这一点直接支持"prose is thin, research quality is the product"的定位。

**A7. Batch API：不存在（负面证据，一手）**

三处官方页面均无：
- 文档左侧导航（Quick Start / API Guides / API Reference / News / Other Resources / FAQ / Change Log）**无 Batch 条目** — <https://api-docs.deepseek.com/>
- 定价页**无 batch 档位** — <https://api-docs.deepseek.com/quick_start/pricing>
- Rate Limit 页**无异步作业队列/离线档位** — <https://api-docs.deepseek.com/quick_start/rate_limit>

负面证据强度：中高。三处独立页面一致缺失，且 DeepSeek 若有此功能没有理由不在定价页列出。

**A8. 历史：DeepSeek 的分时折扣是反复变动的（风险信号）**

serper 检索命中多条线索指出：DeepSeek 曾于 **2025-09-04 结束促销定价并同时取消谷时折扣**；旧的谷时窗口是 **16:30–00:30 UTC**（与今天的窗口**完全不同**）。另有二手说法称 2026-07 底/07-31 也有一次分时公告。这些均为二手，**本轮未做一手确认**，列为未决项。

但可以确定的行为模式：**DeepSeek 在 12 个月内至少三次改动计价结构（2025-09 取消谷时折扣 → 2026 年中重新引入 → 2026-08-16 全线上调）。任何把价格硬编码进代码的做法都会在数月内失效。**

至今仍在流传的过期数字（本轮实测到的污染样本，供 attacker 复现）：
- "off-peak 16:30–00:30 UTC，50–75% 折扣" → **已作废窗口**
- "cache hits cost just $0.028/MTok" → 既不是旧价 $0.0028 也不是新价 $0.007/$0.022，**疑为小数点错误**
- "V4-Pro $0.435 / $0.87" → **旧价**，2026-08 月新发的文章仍在用

---

### B. 对照组：他家的缓存与批处理机制（明确标注为 provider-specific，不可套用）

**B1. Anthropic（一手：<https://platform.claude.com/docs/en/about-claude/pricing>）**

缓存乘数（相对基础输入价）：

| 操作 | 乘数 | 有效期 |
|---|---|---|
| 5 分钟缓存写入 | **1.25×** | 5 分钟 |
| 1 小时缓存写入 | **2×** | 1 小时 |
| 缓存读取（命中） | **0.1×** | 同前一次写入 |

原文："A cache hit costs 10% of the standard input price, which means caching pays off after one cache read for the 5-minute duration (1.25x write), or after two cache reads for the 1-hour duration (2x write)."

Batch API：**"a 50% discount on both input and output tokens"**，且原文明确 **"Batch API and prompt caching discounts can be combined"**、"These multipliers stack with other pricing modifiers"。

**与 DeepSeek 的三点结构性差异（不可互相套用）：**
1. Anthropic **写缓存要额外付钱**（1.25×/2×），DeepSeek **写缓存免费**；
2. Anthropic 缓存读 = 0.1×（90% off），DeepSeek = **1/30（96.7% off）**——DeepSeek 更狠；
3. Anthropic 缓存 TTL 是**买断的确定值**（5m/1h），DeepSeek 是 **best-effort、几小时到几天、无保证**。

→ **可移植的只有"缓存对长 system prompt 有效"这个定性结论；任何 1.25×/0.1× 的定量公式在 DeepSeek 上都是错的。**

**B2. OpenAI（一手：<https://developers.openai.com/api/docs/pricing>）**

- 缓存输入 = 标准输入的 **0.1×（90% off）**，例：`gpt-5.6-sol` $5.00 → $0.50
- Batch API：**50% off**
- 文档未说明最小可缓存长度与是否自动（本轮未取到）

**B3. Google Gemini（一手：<https://ai.google.dev/gemini-api/docs/pricing>）**

- Gemini 3.7 Flash：输入 $0.75 / 输出 $3.75 per 1M（列明 through Dec 31, 2026 —— **这是一个有到期日的价格，本身就是需要盯的促销/时限结构**）
- Context caching：$0.075 /1M **外加 $0.50 per 1M tokens per hour 的存储费**
- Batch：约 **50% off**（3.7 Flash batch: $0.375 / $1.875）

**→ Google 是三家里唯一收缓存"存储费"的。DeepSeek 不收。** 若照抄 Google 的缓存成本模型（含 per-hour storage 项），在 DeepSeek 上会凭空多算一笔不存在的费用。

**B4. 三家 vs DeepSeek 机制对照总表**

| 机制 | DeepSeek | Anthropic | OpenAI | Google |
|---|---|---|---|---|
| 缓存是否自动 | ✅ 默认全开 | 需 `cache_control`（有自动模式） | 自动 | 隐式+显式 |
| 缓存写入费 | **无** | 1.25× / 2× | 无 | 有（显式缓存） |
| 缓存存储费 | **无** | 无 | 无 | **$0.50/1M/小时** |
| 缓存读折扣 | **1/30（96.7%）** | 0.1×（90%） | 0.1×（90%） | 约 0.1× |
| 缓存 TTL | 不保证，数小时–数天 | 5m / 1h 可选 | 未说明 | 可设 |
| **Batch API** | ❌ **无** | ✅ 50% | ✅ 50% | ✅ ~50% |
| 分时计价 | ✅ 峰/谷 2× | ❌ | ❌ | ❌ |
| 模型分层比 | pro = 3× flash | Opus:Sonnet:Haiku = 5:2:1（输入） | — | — |

---

### C. 每次 deep research 运行的实测/公开成本

**C1. 单次运行实测（最有价值的一手观测）**

来源：Simon Willison, <https://til.simonwillison.net/llms/o4-mini-deep-research>

任务：Find locations of every surviving orchestrion in the world（结构化 JSON 输出）
模型：`o4-mini-deep-research-2025-06-26`（$2 in / $8 out per 1M）

| 项 | 值 |
|---|---|
| 输入 token | 60,506 |
| 输出 token | 22,883（其中 reasoning 20,416） |
| 合计 token | 83,389 |
| **Token 费用** | **≈ $0.304** |
| **网页搜索费（77 次调用）** | **≈ $0.77** |
| 代码解释器 | ≈ $0.03 |
| **合计** | **$1.10** |

**算术闭合校验（我做的）**：60,506 × $2/1M = $0.1210；22,883 × $8/1M = $0.1831；合计 $0.3041 ✓ 与作者所述 $0.304 精确吻合。→ 这份数字内部自洽，可信度高。

**口径警告**：这是**一次**运行、**一个**任务、**一个**模型的观测，n=1，不是平均值。且 reasoning token 计入 output（60,506 + 22,883 = 83,389 = 作者所述总数）。

**这条观测的结构性结论（可移植）**：搜索调用费 = token 费的 **2.5 倍**，占总成本 **70%**。

**C2. 商业 deep research 的每次运行报价**

来源：Parallel, <https://parallel.ai/blog/deep-research-benchmarks>（发布 2025-09-09，基准测试窗口 2025-08-11 至 08-29）

单位是 **CPM = cost per thousand queries**，除以 1000 得每次运行价：

| 产品 | CPM | ≈ 每次运行 | BrowseComp 准确率 |
|---|---|---|---|
| Parallel Pro | $100 | $0.10 | 34% |
| Parallel Ultra | $300 | $0.30 | 45% |
| Parallel Ultra2x | $600 | $0.60 | 51% |
| Parallel Ultra4x | $1,200 | $1.20 | 56% |
| Parallel Ultra8x | $2,400 | $2.40 | 58% |
| GPT-5（对手） | $488 | $0.49 | — |
| Exa（对手） | $402 | $0.40 | — |
| Perplexity（对手） | $709 | $0.71 | — |
| **Anthropic（对手）** | **$5,194** | **$5.19** | — |

**口径警告（严重）**：这是 **Parallel 自己发布的、关于自己竞争对手的**数据，属于厂商自利数据，**未经独立复现**。而且是 **2025-08 的基准**，距今 **12 个月**，期间各家模型和价格全部换过代。**竞品那四行必须标 `unverified`。** 只有"Parallel 自家产品的挂牌 CPM"这一部分可标为"厂商挂牌价"。

但有一个跨源可交叉的定性结论：**准确率从 45% 抬到 58%（+13pp），成本要涨 8×**（$300 → $2,400 CPM）。这个陡峭的边际成本曲线与 Anthropic 的"token 用量单独解释 80% 性能方差"是一致的——**质量确实要用 token 买，而且买得很贵。**

**C3. OpenAI deep research 模型的挂牌价（口径参考）**

- `o3-deep-research`：$10 in / $40 out per 1M
- `o4-mini-deep-research`：$2 in / $8 out per 1M
- OpenAI 内置 web search 工具计费（Anthropic 同价）：**$10 per 1,000 searches**

对比：**serper 约 $1/千次，博查约 ¥36/千次**。OpenAI/Anthropic 内置搜索比 serper 贵约 **10×**。这是我们已有工具链的一个实打实的成本优势。

---

### D. 促销价 vs 目录价：本轮实测到的三个样本（上一轮被烧的正是这个）

**D1. Anthropic — 促销价转正（一手，明确措辞）**

来源：<https://platform.claude.com/docs/en/about-claude/pricing> 页内 Note

原文："The $2/$10 per million input/output token pricing for Claude Sonnet 5, announced at launch as introductory pricing through August 31, 2026, is now the standard price. The previously scheduled increase to $3/$15 per million input/output tokens on September 1, 2026 will not occur."

→ 这是"introductory pricing"的**教科书样本**：曾经有到期日、曾经计划涨到 $3/$15、后来取消上调转为标准价。**若在 2026 年初照抄 $2/$10 而不记录它当时是 introductory，就会得出一个当时正确、随时可能翻倍的数字。**

**D2. Google — 带到期日的价格（一手）**

Gemini 3.7 Flash / 3.6 Flash 的 $0.75 / $3.75 明确标注 **"through Dec 31, 2026"**。→ 2027-01-01 之后未知。**任何跨年的成本模型都不能用这个数。**

**D3. serper.dev — 标题价 ≠ 入门价（口径失真样本）**

serper.dev 首页原文（一手）："Industry-leading SERP API, at an unbeatable price starting at **$0.30 per 1000 queries**"，以及 "Get 2,500 free queries / No credit card required"。

但多个二手来源一致指出实际档位是：Starter $50 / 50k credits = **$1.00/千次**；Standard $375 / 500k = $0.75/千次；Scale $1,250 / 2M+ = 更低；**$0.30/千次 是最高量档**。

→ **"starting at $0.30" 的口径是"最大批量档位"，不是"新用户实付价"。我们的实际单价应按 $1.00/千次 建模，不是 $0.30。这是 3.3× 的差距。** 官方 `/pricing` 页返回 404（疑似需登录），档位表**本轮未取到一手确认**，故标 `unverified`。

**D4. 博查 bocha — 目录价与资源包价相差 10×（未决）**

- 阿里云云市场页（应为一手渠道，但页面 JS 渲染、本轮 WebFetch 未取到正文）搜索摘要显示：Web Search API `bocha-web-search` **目录价 ￥0.036/次调用**（= ¥36/千次），并对比"微软 Bing：￥108/千次"
- 第三方集成文档（voidmuse）复述同一数字 ￥0.036/次调用，Semantic Reranker API "限时免费"
- 但另有来源称"资源包低至 **3.6 元/千次**"（= ¥0.0036/次，正好是目录价的 **1/10**），还有来源称"约 **1 元/千次**"

→ 三个数字相差 36 倍。**要么是目录价/资源包价/促销价三种不同口径，要么其中有小数点错误。本轮无法判定，标 `unverified`，必须在接入前用真实账单实测。**

---

### E. 全文 PDF 上下文的 token 成本（每篇论文）

**E1. Anthropic 官方给出的三个不同口径（一手，同一家，数字差 30×）**

来源：<https://platform.claude.com/docs/en/build-with-claude/pdf-support> 与 <https://platform.claude.com/docs/en/about-claude/pricing>

| 口径 | 数字 | 原文 | 折算 12 页论文 |
|---|---|---|---|
| PDF 文本+图像模式（每页转图） | **1,500–3,000 token/页** | "Each page typically uses 1,500–3,000 tokens per page depending on content density" | **18,000–36,000** |
| Bedrock Converse 纯文本抽取模式 | **≈1,000 token / 3 页**（≈333/页） | "Uses approximately 1,000 tokens for a 3-page PDF" | ≈4,000 |
| Bedrock Claude PDF Chat 视觉模式 | **≈7,000 token / 3 页**（≈2,333/页） | "Uses approximately 7,000 tokens for a 3-page PDF" | ≈28,000 |
| web fetch 工具估算 | **500 kB 论文 PDF ≈ 125,000 token** | "Research paper PDF (500 kB): ~125,000 tokens" | 125,000 |

**口径失真警告**：同一家厂商的官方文档里，"一篇论文多少 token"从 4,000 到 125,000，跨度 **31×**，取决于是纯文本抽取、还是每页转图像、还是按文件字节数 ÷4 估算。最后那个 125,000 极可能是 `500,000 bytes / 4 bytes-per-token` 的启发式，而 PDF 的 500kB 里大部分是字体和图像二进制，**不是文本**，所以它是个**严重高估的上界**。

**→ 教训：引用"一篇论文 X token"时，不写清楚是哪种抽取模式，这个数字就是无意义的。**

**E2. DeepSeek 口径下的推导（我的推导，需实测确认）**

DeepSeek v4 文档未描述视觉 PDF 通路，我们的路径必然是**本地抽取文本再喂入**。按 A6 的 0.3 token/英文字符：

- 典型 arXiv 论文正文抽取后约 40,000–60,000 英文字符
- → **12,000–18,000 token/篇**
- 成本：flash 谷时 cache-miss = 15,000 × $0.22/1M = **$0.0033/篇**；pro 峰时 = 15,000 × $1.32/1M = **$0.0198/篇**

→ **在 DeepSeek 上，把一篇论文全文塞进上下文的成本在 0.3–2 美分之间。这便宜到可以改变设计：我们没有理由做激进的摘要压缩，应当优先保全文可溯源。** 标 `unverified（推导值）`，接入后必须用真实 `usage` 回填。

---

### F. 多智能体 vs 单智能体的 token 倍数

来源（一手）：<https://www.anthropic.com/engineering/multi-agent-research-system>

原文逐字：
- **"agents typically use about 4× more tokens than chat interactions, and multi-agent systems use about 15× more tokens than chats."**
- **"token usage by itself explains 80% of the variance"**（BrowseComp 评测；三个因素合计解释 95% 方差，另两个是工具调用次数与模型选择）
- **"For economic viability, multi-agent systems require tasks where the value of the task is high enough to pay for the increased performance."**
- 适用面："heavy parallelization, information that exceeds single context windows, and interfacing with numerous complex tools"
- **不适用面**："some domains that require all agents to share the same context or involve many dependencies between agents are not a good fit for multi-agent systems today."

**口径三元组（必须与数字同时引用）**：
1. **什么指标**：token 消耗总量倍数
2. **在什么样本上**：Anthropic 自家 Research 产品（Opus 编排 + Sonnet 子代理），BrowseComp 评测集
3. **与什么相比**：与 **Claude.ai 的聊天交互**相比 —— 注意基线是"聊天"，不是"单智能体 agent"。**"多智能体是单智能体的 15 倍"是错误转述；正确的是 15/4 ≈ 3.75× 单 agent。**

**时效警告**：该文发表于 **2025-06**，距今 **14 个月**，其间模型代际、价格、上下文长度全变了。**只能引用其结构性结论，不能引用其倍数做 2026 年的预算。**

**对本项目最重要的一句其实是最后那条"不适用面"**：需要所有 agent 共享同一上下文、或 agent 之间强依赖的任务，不适合多智能体。**我们的"证据勘探"天然可并行（不同论文/不同数据源互不依赖），但"跨证据的逻辑推断与冲突裁决"是强依赖的——后者必须收回单一上下文做，不能扇出。** 这是一条直接的架构约束。

---

## 载荷数字核验表（数字 | 口径三元组 | 状态 | 一手出处）

| # | 数字 | 口径三元组（指标 / 样本或档位 / 对比基准） | 状态 | 一手出处 |
|---|---|---|---|---|
| 1 | v4-pro 输出 **$1.98 谷 / $3.96 峰** per 1M | 挂牌单价 / 官方目录价，2026-08-16 16:00 UTC 起 / 无 | **verified** | api-docs.deepseek.com/quick_start/pricing（抓两次一致）+ TechNode CNY 算术闭合 |
| 2 | v4-pro 输入 miss **$0.66 谷 / $1.32 峰** | 同上 | **verified** | 同上 |
| 3 | v4-pro 输入 hit **$0.022 谷 / $0.044 峰** | 同上 | **verified** | 同上 |
| 4 | v4-flash 输出 **$0.66 谷 / $1.32 峰** | 同上 | **verified** | 同上 |
| 5 | v4-flash 输入 miss **$0.22 谷 / $0.44 峰** | 同上 | **verified** | 同上 |
| 6 | v4-flash 输入 hit **$0.007 谷 / $0.014 峰**（CNY 精确值 ¥0.05/¥0.10，USD 为四舍五入） | 同上 | **verified**（含舍入说明） | 同上 |
| 7 | 峰时窗口 **01:00–04:00 + 06:00–10:00 UTC**（= 北京 09–12、14–18） | 计费时段定义 / 官方 / 无 | **verified**（双源：官方 UTC + TechNode 北京时，换算一致） | 同上 |
| 8 | 谷时 = 峰时 **×0.5**；谷时占 **17/24 h = 70.8%** | 折扣比例 / 官方 / 峰时价 | **verified**（占比为我算术推导，7h 峰时） | api-docs + news260813 |
| 9 | 缓存命中 = 未命中 **1/30（96.7% off）** | 折扣比例 / 官方目录价 / 同模型同时段的 cache-miss 输入价 | **verified**（CNY 口径精确 1/30） | 同上 |
| 10 | pro = flash **×3**（全部三行） | 价格比 / 官方目录价 / flash 同行 | **verified**（CNY 精确；USD 因舍入 3.0–3.14） | 同上 |
| 11 | 输出 = 未命中输入 **×3** | 价格比 / 官方目录价 / 同模型同时段 | **verified** | 同上 |
| 12 | 新价生效 **2026-08-16 16:00 UTC** | 生效时刻 / 官方公告 / 无 | **verified**（原文逐字） | api-docs.deepseek.com/news/news260813 |
| 13 | 旧统一价 pro **$0.435/$0.87**、flash **$0.14/$0.28**、hit $0.003625/$0.0028 | 挂牌单价 / 2026-08-16 前的目录价 / 无 | **unverified（二手；官方页已下线）** — 但与 Qz "1,100%"、Engadget "4×" 头条算术自洽 | 仅二手：qz.com、fortune.com、engadget.com |
| 14 | 涨幅 **输出峰时 4.55×、缓存命中峰时 12.14×** | 涨幅倍数 / pro 模型 / 旧统一价 | **unverified（依赖 #13）** | 推导 |
| 15 | 旧价**不是**促销价（官方未用 introductory/限时措辞） | 定价性质判定 / 官方公告全文 / 无 | **verified（负面证据）** | news260813 逐字检查 |
| 16 | **DeepSeek 无 Batch API** | 能力有无 / 官方文档导航+定价页+限流页 / Anthropic/OpenAI/Google 均有 | **verified（三处一手页面一致缺失）** | api-docs.deepseek.com/ 、/quick_start/pricing、/quick_start/rate_limit |
| 17 | 并发 **pro 500 / flash 2500**，超限 429 无排队，扩容免费 | 并发上限 / 账号级 / 无 | **verified** | api-docs.deepseek.com/quick_start/rate_limit |
| 18 | 缓存**默认开启、无写入费、无存储费、TTL 数小时–数天不保证** | 机制属性 / 官方 / Anthropic 需付 1.25×/2× 写入费、Google 收 $0.50/1M/h 存储费 | **verified** | api-docs.deepseek.com/guides/kv_cache |
| 19 | 中文 **1 汉字 ≈ 0.6 token**；英文 1 字符 ≈ 0.3 token | 分词换算 / DeepSeek tokenizer / 无 | **verified** | api-docs.deepseek.com/quick_start/token_usage |
| 20 | 1 万字中文论文 ≈ 6,000 输出 token ≈ **$0.0119**（pro 谷时） | 成本推导 / 6,000 tok × $1.98/1M / 无 | **verified（算术）**，依赖 #1、#19 | 推导 |
| 21 | Anthropic 缓存写 **1.25×/2×**、读 **0.1×**；Batch **50% off**，可与缓存叠加 | 乘数 / Anthropic 官方 / 基础输入价 | **verified** | platform.claude.com/docs/en/about-claude/pricing |
| 22 | Claude Sonnet 5 的 $2/$10 曾是 **introductory pricing through 2026-08-31**，原定 9/1 涨至 $3/$15，**已取消上调转为标准价** | 定价性质 / Anthropic 官方 Note / 无 | **verified（逐字）** | 同上 |
| 23 | OpenAI 缓存输入 **0.1×（90% off）**；Batch **50% off**；gpt-5.6-sol $5/$0.50/$30 | 单价与折扣 / OpenAI 官方定价页 / 标准输入价 | **verified** | developers.openai.com/api/docs/pricing |
| 24 | Gemini 3.7 Flash **$0.75/$3.75**，标注 **through Dec 31 2026**；缓存 $0.075 **+ $0.50/1M/小时存储**；Batch ≈50% | 单价与折扣 / Google 官方，付费档 / 标准价 | **verified**（到期日为关键口径） | ai.google.dev/gemini-api/docs/pricing |
| 25 | 内置 web search **$10 / 1,000 searches**（Anthropic 与 OpenAI 同价） | 工具调用费 / 官方 / serper ≈$1/千次 | **verified**（Anthropic 侧一手） | platform.claude.com/docs/en/about-claude/pricing |
| 26 | 单次 deep research 实测 **$1.10**：token $0.304 + 搜索 77 次 $0.77 + 代码 $0.03 | 单次运行实付 / **n=1**，o4-mini-deep-research，orchestrion 检索任务，2025-10 / 无 | **verified（算术闭合：60,506×$2/1M + 22,883×$8/1M = $0.3041 ✓）**，但样本 n=1 | til.simonwillison.net/llms/o4-mini-deep-research |
| 27 | **搜索费占单次运行 70%，是 token 费的 2.5×** | 成本结构占比 / 同 #26 的 n=1 样本 / token 费 | **verified（由 #26 推导）**，可推广性存疑 | 同上 |
| 28 | Parallel Ultra **$300 CPM = $0.30/次**，45% BrowseComp | 挂牌价与准确率 / Parallel 自家产品，BrowseComp，2025-08-11~29 基准 / 无 | **verified（作为厂商挂牌价）** | parallel.ai/blog/deep-research-benchmarks |
| 29 | 竞品 CPM：GPT-5 $488、Exa $402、Perplexity $709、**Anthropic $5,194** | 每千次成本 / **由竞争对手 Parallel 测量并发布**，2025-08 基准，距今 12 个月 / Parallel 自家 | **unverified（厂商自利数据 + 严重过期）** | 同上 |
| 30 | 准确率 45%→58%（+13pp）需成本 **8×**（$300→$2,400 CPM） | 边际成本曲线 / Parallel 自家产品线，BrowseComp / 无 | **verified（厂商自报，内部一致）** | 同上 |
| 31 | **agents ≈ 4× chat；multi-agent ≈ 15× chat** | token 总量倍数 / Anthropic 自家 Research 系统，BrowseComp / **基线是 Claude.ai 聊天，不是单 agent** | **verified（逐字）**，但发表于 2025-06，已 14 个月 | anthropic.com/engineering/multi-agent-research-system |
| 32 | 多智能体 ≈ 单 agent 的 **3.75×**（15/4），**不是 15×** | 倍数换算 / 同上 / 单 agent | **corrected**（纠正常见误传） | 由 #31 推导 |
| 33 | **token 用量单独解释 80% 性能方差**；三因素合计 95% | 方差解释率 / BrowseComp 评测 / 无 | **verified（逐字）** | 同上 |
| 34 | PDF **1,500–3,000 token/页**（文本+图像模式） | 每页 token / Anthropic PDF 支持，含图像 / 纯文本抽取模式 | **verified（逐字）** | platform.claude.com/docs/en/build-with-claude/pdf-support |
| 35 | 纯文本抽取 ≈**333 token/页**；视觉模式 ≈**2,333 token/页**（3 页 PDF 分别 1,000 / 7,000） | 每页 token / Bedrock Converse 两种模式 / 互为对比 | **verified（逐字）** | 同上 |
| 36 | "Research paper PDF (500 kB): ~125,000 tokens" | 每篇 token / web fetch 工具的**估算表** / 无 | **verified（原文确实这么写）** 但**口径可疑**：疑为 bytes/4 启发式，对 PDF 严重高估 | platform.claude.com/docs/en/about-claude/pricing |
| 37 | DeepSeek 口径下一篇论文 ≈ **12,000–18,000 token**，成本 **$0.003–$0.020** | 每篇 token 与成本 / 本地抽取纯文本 × 0.3 tok/char / 无 | **unverified（我的推导，未实测）** | 推导自 #19、#1、#5 |
| 38 | serper "**starting at $0.30 per 1000 queries**" | 单价 / **最高批量档**，非入门档 / 实际入门 ≈$1.00/千次 | **corrected（口径失真：标题价≠实付价，差 3.3×）** | serper.dev 首页（一手）；档位表本轮未取到一手 |
| 39 | serper 入门档 $50 / 50k credits = **$1.00/千次** | 单价 / Starter 档 / 无 | **unverified（仅二手；官方 /pricing 返回 404）** | 多个二手 |
| 40 | 博查 Web Search **￥0.036/次调用**（=¥36/千次）目录价 | 单价 / 阿里云云市场**目录价** / 微软 Bing ¥108/千次 | **unverified**（页面 JS 渲染未取到正文；且另有 ¥3.6/千次、¥1/千次 两个相差 10–36× 的说法） | market.aliyun.com/products/57124001/cmapi00069848.html（未取到正文） |
| 41 | CNY→USD 隐含汇率 **6.818**（DeepSeek 内部换算，非市场汇率） | 汇率 / DeepSeek 价卡两币种口径 / 市场汇率 | **verified（12 个数全部闭合）**；市场汇率本轮**未核验** | 由官方 USD 表 ÷ TechNode CNY 表推导 |
| 42 | 已作废但仍在流传的旧数：谷时窗口 "16:30–00:30 UTC"、"cache hit $0.028/MTok" | 污染样本 / 2026-08 仍在流传的二手文章 / 现行官方值 | **corrected（明确标为错误/过期）** | 与 api-docs 现行值比对 |

---

## 对本项目的设计含义

### 1. 成本模型骨架（provider 参数化）

**通用式：**

```
C_run = Σ_agents [ T_miss·P_miss + T_hit·P_hit + T_out·P_out ]      ← token 项
      + N_search · P_search                                          ← 检索项
      + N_rerank · P_rerank + C_fixed                                ← 其他外部服务
```

**DeepSeek 特化后，整张价卡塌缩成一个基准数 × 两个开关：**

```
P_miss(tier, t) = B(tier) · K(t) · $0.22 / 1M
P_hit           = P_miss / 30
P_out           = P_miss · 3

其中  B(flash)=1, B(pro)=3      ← 杠杆②模型分层
      K(off-peak)=1, K(peak)=2  ← 杠杆③的 DeepSeek 替代品（分时，非 batch）
```

定义**有效输入当量** `E = T_miss + T_hit/30 + 3·T_out`，则：

```
C_tokens = B · K · E · $0.22 / 1,000,000
```

**这一个式子就是我们全部的 token 成本模型。** 记账器只需累加每个 agent 的 `(T_miss, T_hit, T_out)`（三者都能从 `usage.prompt_cache_hit_tokens` / `prompt_cache_miss_tokens` / `completion_tokens` 直接读到），乘上它当时的 `B` 和 `K`，即可得精确账单。**建议把 `E` 作为 DSH 侧统一的"成本单位"暴露给 workflow 引擎，用它做预算闸门，而不是用美元**——因为价格会变（见 A8），`E` 不会。

**换 provider 时需要替换的参数（明确标注哪些是 DeepSeek 特有）：**

| 参数 | DeepSeek | 换到 Anthropic 需改什么 |
|---|---|---|
| `P_hit = P_miss/30` | ✅ | 改为 `0.1×`，**且要新增一项 `T_cache_write × 1.25 或 2×` 的写入费** |
| 缓存存储费 | 无 | 无（但换到 Google 要**新增** `$0.50/1M/h × 驻留小时数`） |
| `K(t)` 分时 | ✅ 2× | **删除此项**（三家均无分时） |
| Batch 折扣 | **不存在** | **新增 `×0.5`**，且与缓存可叠加 |
| `B` 分层 | 精确 3× | 改为 Opus:Sonnet:Haiku = 5:2:1（输入） |

### 2. 三个杠杆在我们 provider 上的最终判定

**杠杆①：Prompt caching —— ✅ 可用，且是最省事的一个**

- 默认开启、零代码、零写入费、零存储费。**没有理由不用。**
- 但命中要求"前缀完全匹配"，因此**架构约束**：所有子代理必须共享**逐字节相同的前缀**（system prompt + 工具定义 + 共享上下文），任何一处变动都会击穿整段缓存。→ **所有随机化/时间戳/agent 编号必须放在前缀之后。**
- TTL 无保证（数小时–数天），**不能把缓存命中当作确定性收益写进预算**，只能作为上行空间。悲观预算按 `h=0` 算，实际账单按 `usage` 回填。
- 命中率 `h` 对输入项的效果：`×(1 − 0.967h)`。h=0.8 时输入费降到 22.6%。但由于**输出价是输入价的 3 倍**，如果一个 agent 的输出占比高，缓存对总成本的杠杆会被稀释。→ **缓存主要救"长上下文、短输出"的证据勘探 agent；对"长输出"的综述/写作 agent 几乎无效。**

**杠杆②：模型分层 —— ✅ 可用，且是最干净的一个**

- 精确 3×，全行统一。决策极简：**任何一个子任务，只要 flash 能过验收门，就必须用 flash。**
- 建议的分层原则（与本项目"可信度即产品"的定位对齐）：
  - **flash**：检索、抽取、去重、格式化、初筛、结构化字段提取 —— 这些任务有**确定性验收**（schema 校验、正则、数值一致性），错了能被机器发现
  - **pro**：跨证据冲突裁决、逻辑推断链构造、verified/unverified 的最终判定 —— 这些是**产品本身**，且错误不可被下游机器发现
- 由于 pro 只贵 3×，而 flash 已经很便宜，**不要为了省钱把裁决环节降级到 flash**——那是拿产品换 3 倍的一个小数。

**杠杆③：离线批处理 —— ❌ 在 DeepSeek 上不存在。替代品是分时调度，性质不同，必须重新设计**

- **不要在计划里写"用 Batch API 拿 50% 折扣"。** 我们的 provider 没有这个东西。上一轮正是在这里出的错。
- 替代方案是**谷时调度**，同样约 2× 杠杆，但有三个关键差异必须体现在设计里：
  1. **它是钟点，不是队列。** provider 不会替我们排队，我们必须自己实现一个"作业在谷时窗口内执行"的调度器。
  2. **它不给吞吐豁免。** 并发上限（pro 500 / flash 2500）与超限 429 在谷时完全一样，且**无排队**。→ 我们必须自建并发闸门 + 指数退避，这是 DSH workflow 引擎里必须有的一层。
  3. **窗口会变。** DeepSeek 12 个月内改了至少三次计价结构（A8）。→ **峰谷窗口必须是配置项，不能硬编码**，并且应当有一个"启动时校验价卡"的动作。
- **对中国时区用户的红利**：北京时间 18:00–次日 09:00、以及 12:00–14:00 全是谷时。**本项目的重型 fan-out 勘探应默认排到夜间批次**；白天只跑交互式的轻量查询。这是一条可以直接写进产品行为的规则（"你现在提交的深度勘探将于今晚 20:00 开始，费用减半；如需立即执行请确认"）。

### 3. 成本结构的重心不在 token，在搜索调用

Simon Willison 的实测（#26/#27）显示搜索费是 token 费的 2.5 倍。**在 DeepSeek 上这个比例只会更极端**，因为 DeepSeek 的 token 比 o4-mini 便宜约 3–6×，而 serper 的单价并不比 OpenAI 内置搜索便宜同样的倍数。

一个粗算（中等规模勘探：1 编排 pro + 12 并行 flash + 1 核验 pro，谷时，缓存命中 50–60%）：

- token 侧 `E` 合计约 ~4.6×10⁵ 当量 → **≈ $0.39**
- 搜索侧 60 次 serper + 40 次博查 → **≈ $0.26**（博查若按 ¥0.036/次则占大头）
- **合计 ≈ $0.65/次运行（谷时）；同样配置在峰时 ≈ $1.04**

→ **搜索占 40%。** 因此：

1. **预算闸门必须同时管两个计数器**：`E`（token 当量）与 `N_search`（检索次数）。只管 token 会漏掉一半成本。
2. **检索去重与缓存的价值高于 prompt 压缩。** 同一 query 在不同子代理间重复发出是最贵的浪费。→ **必须有一个跨 agent 的检索结果缓存层（query 归一化 + 结果持久化），这比任何 prompt 优化都值钱。**
3. 博查的单价口径未定（#40，可能差 10–36×）。**接入前必须用真实账单实测一次**，否则整个检索预算是空的。

### 4. 全文 PDF 便宜到可以不做压缩

一篇论文进上下文 ≈ **$0.003–$0.020**（#37，待实测）。这意味着：

- **不要为省钱做激进摘要。** 摘要会切断"claim → 原文"的溯源链，而溯源链正是本项目的产品。花 2 分钱保住可溯源性是极划算的交易。
- v4 的 **1M 上下文 / 384K 输出**足以让一个核验 agent 同时持有 **50–80 篇论文全文**。→ 支持一个"单上下文裁决者"的架构：扇出去做勘探（可并行、弱依赖），**收回单一大上下文做冲突裁决与逻辑推断**（强依赖，按 Anthropic 的结论正是多智能体的不适用面，#F）。
- 但注意 #34–#36 的口径陷阱：**我们必须在自己的流水线里实测并固化"一篇论文多少 token"这个数，且注明抽取模式**，不能引用 Anthropic 的任何一个数（它们之间就差 31×）。

### 5. 可信度产品与成本的耦合

Parallel 的数据（#30）显示准确率 +13pp 需要 8× 成本。这与"token 解释 80% 性能方差"（#33）互相印证：**质量是买来的，且边际成本陡峭。**

对本项目的含义：**不要设一个全局的"质量档位"，要设 per-claim 的。** 一次运行里绝大多数 claim 是低风险的（背景陈述、方法描述），少数是载荷 claim（结论、数字、因果断言）。把 8× 的预算花在载荷 claim 上，其余用 flash 一遍过。→ **成本模型应该以 claim 为单位记账，而不是以 run 为单位**，这样"每个 verified claim 的边际成本"才可度量，也才能作为 loop 的收敛信号。

### 6. 必须写进代码的防腐措施

鉴于 DeepSeek 12 个月三改价（A8）、Google 价格带到期日（D2）、Anthropic 促销转正（D1）：

- **价卡进配置文件，带 `fetched_at` 时间戳与来源 URL**，不进代码常量
- 启动时若价卡 `fetched_at` 超过 N 天 → 告警而非静默使用
- **一切内部预算用 `E`（token 当量）与 `N_search` 计量**，美元只在最后一步展示层换算
- 每次运行落一份 `usage` 明细（hit/miss/output 三个数 + 当时的 B、K），使账单**可事后重算**——这本身就是本项目"可再跑的分析"方法论对自己的应用

---

## 未决与风险

### 未决（需后续一手确认）

1. **旧统一价的一手来源已消失**（#13）。官方定价页已覆盖为新价，无 archive 快照核验。所有涨幅倍数（#14）都建立在二手数字上。**影响有限**（我们只用新价做预算），但"涨了多少"这个叙述不应写进对外文档。
2. **2026-07 是否有过一次分时公告？** 二手来源称"07-31 宣布峰谷"、"不到一个月内第二次调价"，与 08-13 公告的关系不明。本轮只确认了 08-13 公告与 08-16 生效。**未决。**
3. **serper 实际档位表未取到一手**（#38/#39）。官方 `/pricing` 返回 404（疑需登录）。入门价 $1.00/千次 仅二手。**必须用真实账单确认。**
4. **博查定价三个数相差 36×**（#40）：目录价 ¥0.036/次 vs 资源包 ¥3.6/千次 vs "约 ¥1/千次"。阿里云页面 JS 渲染无法抓取。**这是当前成本模型里最大的数值空洞——检索侧占总成本 40%，而其中一半的单价不确定。接入前必须实测。**
5. **DeepSeek v4 是否支持视觉/PDF 直传？** 文档未见相关通路。若不支持，本地 PDF→文本抽取的质量与 token 量需自行实测（#37 全是推导值）。
6. **CNY 与 USD 计费的实际差异**：DeepSeek 内部换算率 6.818（#41）低于市场汇率。若可选择计费币种，可能存在数个百分点的套利。**本轮未核验市场汇率，也未确认账户能否选择币种。**
7. **缓存命中率在我们的真实负载下是多少？** 官方明说 best-effort 且要求前缀完全匹配。h 是成本模型里波动最大的自由参数（h=0 与 h=0.8 之间输入费差 4.4×）。**只能实测。**

### 风险

1. **【高】价格再次变动。** DeepSeek 12 个月三改，且本次是在"AI demand strains capacity"背景下的上调。**假设未来 6 个月内还会再变。** 缓解：价卡外置 + 时间戳 + 启动校验（见含义 6）。
2. **【高】缓存杠杆被侵蚀。** 本次涨价中缓存命中输入涨幅最大（峰时 12×）。若这个趋势延续，"重放长 system prompt"的架构会变得昂贵。缓解：不要把架构建立在"缓存必然便宜"的假设上；`E` 公式里 `T_hit/30` 的那个 30 必须是配置项。
3. **【中】谷时窗口被取消或改动。** 有先例：2025-09-04 DeepSeek 曾直接取消谷时折扣。若我们把"夜间跑批"做成产品承诺，窗口一改就会失信。缓解：把谷时表述为"当前价卡下的优化"，不是产品保证。
4. **【中】并发 429 无排队。** 2500 路 flash 看似宽裕，但一次 hyper-parallel 扇出 + 重试风暴很容易触顶，且 provider 不排队。缓解：DSH 侧必须有并发信号量 + 抖动退避，且**扇出宽度应是预算的函数，不是常数**。
5. **【中】搜索费失控。** 搜索占成本 40%，且是最容易被 agent"多问几次"悄悄放大的一项。缓解：`N_search` 硬闸门 + 跨 agent 检索结果缓存。
6. **【中】口径污染再次发生。** 本轮实测到至少三个仍在流传的过期/错误数字（#42），且是在 2026-08 新发的文章里。**本项目自己的知识库若抓取这些页面，会把错误数字当证据。** 缓解：把"provider 定价"列为**必须回官方页面**的白名单话题，禁止用二手页面作为定价类 claim 的证据。
7. **【低】厂商自利基准数据。** Parallel 关于竞品的 CPM（#29）是竞争对手测的、12 个月前的。若我们的系统抓到这类页面并当作中立证据，会产生带偏见的结论。**这恰好是本项目要解决的问题本身**——可以作为一个内建的测试用例：系统应当能自动识别"发布者是被比较方的竞争对手"这一利益冲突，并将该证据降级为 unverified。
