# KG-free 证据库与记忆的工程 schema — 外部调研 v2

> 调研日期：2026-08-17。所有"当前值"类数字均标注查询日期，过期需重查。
> 方法：一手源优先（论文 PDF/abs 页、开源仓库源码、官方文档、实时 API 调用）。
> 本轮显式规避"多个二手页转述同一上游 = 三个来源"的假独立佐证。

---

## 结论摘要

**1. 现有系统的去重键几乎都是错的，而且错法一致：要么用 URL，要么用语义相似度。**
WebWeaver（当前 deep research SOTA 之一）的记忆库去重键经源码确认是**原始 URL 字符串精确匹配，无任何归一化**（`url2id[new_content["url"]] = len(url2id) + 1`）。这意味着 N 个并行 worker 从 arXiv abs 页、arXiv PDF、出版社 HTML、PMC 三个镜像访问同一篇论文，会产出 6 条独立记忆和 6 个引用 ID。实测一篇论文（NumPy/Nature）在 Semantic Scholar 上同时挂着 **7 个不同标识符**（DOI / ArXiv / CorpusId / PubMed / PMC / MAG / DBLP），URL 数量则无上界。

**2. 语义相似度去重会主动吃掉矛盾——这是本维度最重要的一条负面结论。**
arXiv 2606.24535（2026-06，生产系统 MemClaw 的复盘）原文：*"a contradiction phrased naturally ('XX is AA' then 'XX is BB') is near-identical text, so the very writes the detector exists to resolve are the ones most likely to be 409'd at the gate."* 其近重复门是**同步、pre-commit、超过 embedding 相似度阈值即返回 409**，而矛盾检测器是**异步 post-commit**。管线顺序保证了矛盾写入永远到不了矛盾检测器。对一个"产品即可信度"的系统，这是致命的。

**3. 主流 agent memory 的矛盾语义全部不适用于科学证据。**
mem0 的更新提示词（源码确认）规定：*"If the retrieved facts contain information that contradicts the information present in the memory, then you have to delete it."* —— **矛盾即删除**。Graphiti 的失效判定则是**纯时间性**：新事件的 `valid_at` 早于旧边即写 `invalid_at` + `expired_at`。两者都假设"世界状态单值、新的覆盖旧的"，这对"用户从孟买搬到班加罗尔"成立，对"2019 年队列研究 vs 2026 年 RCT 结论相反"完全不成立——后者可能两个都对（不同人群），也可能新的那个错。**学术分歧不是状态更新。**

**4. DOI 不是版本锚。**
arXiv 官方文档确认：*"Replacing an article with a new version will not generate a new DOI"*，且该 DOI *"will always point to the latest version of the article"*。所以引用 `10.48550/arXiv.2509.13312` 在语义上是"未来某个版本"，不是你读过的那个。唯一的版本锚是带 `vN` 后缀的 arXiv ID。

**5. 撤稿状态绝不能单源。**
同一天（2026-08-17）实时查询：OpenAlex `is_retracted:true` = **134,175**；Crossref `update-type:retraction` = **74,607**。相差 1.8 倍。两个口径都"正确"，但含义不同，任何一个单独用都会给出错误的撤稿率。

**6. 模糊身份解析可以提议合并，绝不能自动执行合并。**
bioRxiv 生产系统用标题匹配做 preprint→VoR 关联，作者手工复核 120 篇"未发表"预印本，发现 **37.5% 其实已经发表**。这个假阴性把该研究的头条数字从 42.0% 拉到 67.0% 量级——一个生产级模糊匹配器，把一个统计量搞错了约 25 个百分点。

**7. 给本项目的核心 schema 结论：按"来源坐标"去重，绝不按"内容"去重。**
两条矛盾的证据物理上住在语料库的不同位置（不同 work、不同 section、不同句子）。以 `(work_id, locator, extractor_version)` 的内容寻址哈希作为 `evidence_id`，则：并行写入天然幂等（主键碰撞即去重，零协调开销）、去重不需要 embedding 调用（对超并行至关重要）、**矛盾在构造上不可能被去重门吃掉**。这符合项目"由设计消除根因"的偏好。

---

## 系统与机制逐条（含 URL）

### 1. WebWeaver memory bank（阿里 Tongyi Lab）

- 论文：https://arxiv.org/abs/2509.13312 ／ 全文 https://arxiv.org/html/2509.13312v2
- 代码：https://github.com/Alibaba-NLP/DeepResearch/tree/main/WebAgent/WebWeaver
- 关键源文件：https://raw.githubusercontent.com/Alibaba-NLP/DeepResearch/main/WebAgent/WebWeaver/react_agent_search_id.py

**机制（论文陈述）**：planner 交替进行检索与大纲优化，大纲中的引用指向 memory bank；writer 按 section 做定向检索，只取该节相关证据。论文原话：*"Only a short summary of the web page or PDF file is included in the search context, and only necessary raw pages will be retrieved from the memory to write the corresponding sections via the citations in the outline."* 以及 *"extract verifiable, detailed evidence (e.g., quotes, data points), which is stored in a structured memory bank."*

**实现（源码确认，一手）**：
- 每条记忆是 `page_info` 列表中的一个对象，字段为 `url` / `goal` / `summary` / `evidence`。
- 去重：`if new_content['url'] not in url_list` 与 `if new_content["url"] in url2id: continue`。**精确 URL 字符串匹配，无归一化，无内容级重复检测。**
- 引用 ID 分配：`url2id[new_content["url"]] = len(url2id) + 1`，即 `id_1`、`id_2`……**ID 是自增序号，与内容无关，跨 run 不稳定，并行下不可复现。**

**对本项目的可用性**：字段设计（url/goal/summary/evidence 四元）是合理的最小骨架，`goal` 字段（这次抽取是为了回答什么）值得抄——它让证据带上"为何被采集"的上下文。但去重键和 ID 分配方案必须整体替换。

> 我的推断（非源陈述）：`goal` 字段本质上是把"检索意图"固化进证据行，这与本项目的 `metric_frame` 是同一类设计——把解释该条记录所需的上下文与记录本身绑死，而不是留给下游重建。

### 2. Kosmos structured world model（FutureHouse / Edison Scientific）

- 论文：https://arxiv.org/abs/2511.02824 ／ 全文 https://arxiv.org/html/2511.02824v1

**披露内容**：摘要原文 *"Kosmos uses a structured world model to share information between a data analysis agent and a literature search agent. The world model enables Kosmos to coherently pursue the specified objective over 200 agent rollouts."* 每轮最多派发 10 个文献检索/数据分析任务，用任务输出摘要更新 world model，再查询 world model 提出下一轮任务。

**未披露内容（重要）**：全文中**没有**给出 world model 的数据结构、字段定义、去重机制或矛盾处理规程。论文只说明其*功能*（跨 agent 协调、支撑 200 次 rollout），不说明其*实现*。

> 结论：Kosmos 的 world model **不能作为 schema 参考**，只能作为"结构化共享状态确实能把并行 agent 的连贯性推到 200 rollout"这一存在性证据。任何声称"照 Kosmos 的 world model 设计"的方案都是在填空。

**可迁移的真正价值在其评测方法**：Kosmos 把报告里每条陈述按来源分成"数据分析 / 文献 / 二者之间的解释"三类，分别测准确率，得到 85.5% / 82.1% / **57.9%**。**解释类陈述的准确率比另外两类低约 25–28 个百分点。** 这是本项目"论文组装刻意做薄、研究质量才是产品"这一立场最直接的外部证据，也说明 `verification_method` 必须逐条记录——不同方法的可信度差异极大，混在一起报一个总准确率就是在洗数字。

### 3. mem0

- 论文：https://arxiv.org/abs/2504.19413
- 官方结果页：https://mem0.ai/research
- 决策提示词源码：https://raw.githubusercontent.com/mem0ai/mem0/main/mem0/configs/prompts.py

**写决策操作**：抽取阶段由 LLM 从消息对中提炼事实，再与检索到的既有记忆比对，四选一：**ADD / UPDATE / DELETE / NONE**。源码提示词规则：
- ADD：*"If the retrieved facts contain new information not present in the memory, then you have to add it by generating a new ID."*
- UPDATE：*"If the retrieved facts contain information that is already present in the memory but the information is totally different, then you have to update it."*
- DELETE：*"If the retrieved facts contain information that contradicts the information present in the memory, then you have to delete it."*
- NONE：信息已存在则不动。

**对本项目的判定：DELETE 规则必须拒绝采纳。** 该规则的示例是"Loves cheese pizza" vs "Dislikes cheese pizza" → 删除旧的。用于个人偏好记忆是对的；用于科学证据则等于**用后到的一篇论文静默删除先到的一篇论文**。这正是"claim-graph 框架失败"的一个具体机理：框架层用单值状态假设吞掉了真实的学术分歧。

### 4. Zep / Graphiti（双时间线知识图谱）

- 论文：https://arxiv.org/abs/2501.13956
- 边模型源码：https://raw.githubusercontent.com/getzep/graphiti/main/graphiti_core/edges.py
- 去重/失效源码：https://raw.githubusercontent.com/getzep/graphiti/main/graphiti_core/utils/maintenance/edge_operations.py

**边字段（源码逐字）**：
```python
class Edge(BaseModel, ABC):
    uuid: str
    group_id: str = Field(description='partition of the graph')
    source_node_uuid: str
    target_node_uuid: str
    created_at: datetime

class EntityEdge(Edge):
    name: str            # relation name
    fact: str            # fact representing the edge
    fact_embedding: list[float] | None
    episodes: list[str]  # episode ids that reference this edge
    expired_at: datetime | None   # 'datetime of when the node was invalidated'
    valid_at: datetime | None     # 'datetime of when the fact became true'
    invalid_at: datetime | None   # 'datetime of when the fact stopped being true'
    reference_time: datetime | None
    attributes: dict[str, Any]
```
四个时间戳分两条轴：`created_at`/`expired_at` 是**系统轴**（何时被写入/何时被作废），`valid_at`/`invalid_at` 是**事件轴**（事实何时开始/停止为真）。这是标准双时间线设计，**值得直接借鉴**。

**去重（源码确认，三级）**：
1. 快路径——精确字符串匹配：`edge.source_node_uuid == extracted_edge.source_node_uuid and edge.target_node_uuid == extracted_edge.target_node_uuid and _normalize_string_exact(edge.fact) == normalized_fact`
2. 候选召回——embedding 混合检索（`EDGE_HYBRID_SEARCH_RRF`）
3. 判定——**LLM 裁决**：`prompt_library.dedupe_edges.resolve_edge(...)`，返回 `EdgeDuplicate`

**失效（源码确认）**：`if edge_valid_at_utc < resolved_edge_valid_at_utc: edge.invalid_at = resolved_edge.valid_at; edge.expired_at = now`。**纯时间判定，没有阈值常数，没有"谁更可信"的概念。**

**对本项目的判定**：双时间线字段抄，失效规则不抄。科学证据的时间新旧与真值无关；一篇 2026 年的论文不使 2019 年的论文失效。同时注意：第 2、3 级去重（embedding 召回 + LLM 裁决）在超并行下是**每次写入都要一次 LLM 调用**的成本结构，与本项目的并行度不兼容。

### 5. Letta（MemGPT 后继）—— 并发共享内存的唯一明确契约

- memory block 概念：https://www.letta.com/blog/memory-blocks/
- 多 agent 共享内存文档：https://docs.letta.com/guides/agents/multi-agent-shared-memory

**block 字段**：`label`（用途标识，如 human/persona/knowledge）、`value`（字符串内容）、`description`（如何使用该 block 的指引）、size limit（字符或 token 上限）、read-only 标志。

**共享与并发（官方文档逐字，本轮最有工程价值的一段）**：
| 操作 | 用于 | 并发安全？ |
|---|---|---|
| `memory_insert` | 追加新信息 | **Yes（append-only）** |
| `memory_replace` | 定向编辑 | **Mostly（fails if target string changed）** |
| `memory_rethink` | 整体重写 | **No（last-writer-wins）** |

文档明确警告：*"**Anti-pattern**: Multiple agents doing `memory_rethink` on the same block simultaneously leads to lost updates."*
推荐做法：指定单一 owner agent 负责重编辑、其他 agent 只做 append-only、内容里带时间戳和 agent ID、高竞争数据拆到独立 block。
文档同时确认：**没有内建的冲突检测、版本控制或分布式锁**，`block_id` 相同即共享，一方改动其他 agent 立即可见。

> 关键观察（我的推断）：`memory_replace` 的 "fails if target string changed" 本质上就是一个 **compare-and-swap 原语**。Letta 在没有事务系统的前提下，用"目标串必须仍然匹配"实现了乐观并发控制。本项目可以直接把这个语义提升为一等契约。

### 6. Governed Shared Memory / MemClaw（2026-06，生产系统复盘）

- 论文：https://arxiv.org/abs/2606.24535 ／ 全文 https://arxiv.org/html/2606.24535v1

**形式化的四类失效模式**：unauthorized leakage（越权泄漏）、stale propagation（陈旧传播）、**contradiction persistence（矛盾长存）**、provenance collapse（溯源崩塌）。

**四个系统级原语**：scoped retrieval、temporal supersession、provenance tracking、policy-governed memory propagation。

**近重复门的致命顺序错误（逐字）**：
> *"A semantic near-duplicate detector evaluates an incoming write synchronously, pre-commit, returning 409 when embedding similarity exceeds a threshold."*
> *"a contradiction phrased naturally ('XX is AA' then 'XX is BB') is near-identical text, so the very writes the detector exists to resolve are the ones most likely to be 409'd at the gate."*
> *"The contradiction detector evaluates RDF-triple compatibility and sets supersedes_id — but it runs post-commit and asynchronously."*

**取代机制字段**：新行携带 `supersedes_id` 指向旧行，旧行 status 翻转为 `outdated`。且注明结构化检测器**只对服务端认定为单值的谓词生效**——即取代不是无条件的，需要谓词本身是单值语义。

**溯源字段**：*"Every memory object stores its writer identity, source system, derivation history, and modification lineage."* 具体含 tenant/fleet 标识、writing agent、content、`metadata.derived_from`（父标识符）。

**负面结果（诚实披露，价值很高）**：scope 执行是双模的——租户级隔离在每条路径都生效，但子租户级 scope 在 search 路径只部分生效、在 GET-by-id 路径**完全不生效**。作者自陈教训是"分布式记忆系统中管线顺序影响正确性"。

> 这是本轮唯一一篇直接针对"并发 agent 共享内存治理"的一手工程论文，且是生产系统而非玩具实现。其近重复门结论应当作为本项目的**硬约束**写进设计文档。

### 7. SciFact 式立场建模

- 论文：https://aclanthology.org/2020.emnlp-main.609/（Fact or Fiction: Verifying Scientific Claims, EMNLP 2020）

**标签集**：每个 (claim, abstract) 对标注为 **SUPPORTS / REFUTES / NOINFO**；SUPPORTS 与 REFUTES 实例附带摘要中的 gold rationale 句子。规模为 1.4K 专家撰写的 claim。设计上**刻意不在 REFUTES 内部再细分粒度**。

**对本项目的迁移要点（我的推断）**：SciFact 的立场标签挂在 **(claim, abstract) 对**上，不是挂在论文上。这个粒度选择必须保留——同一篇论文完全可能支持某条断言的一部分、反驳另一部分。本项目应把 stance 挂在 **(claim, evidence) 边**上，比 SciFact 更细一级（到句子/span），因为 rationale 句子本来就是 SciFact 的输出之一。

### 8. 身份与版本锚定：实测到的标识符现实

**同一篇论文（NumPy, Nature 2020）在 Semantic Scholar 的 externalIds（2026-08-17 实时 API 调用）**：
```json
{"DOI":"10.1038/s41586-020-2649-2","ArXiv":"2006.10256","CorpusId":219792763,
 "PubMed":"32939066","PubMedCentral":"7759461","MAG":"3035965352",
 "DBLP":"journals/corr/abs-2006.10256"}
paperId: "024a2c03be8e468e7c4fdf9bda36cdc0eaae85fb"
```
- API：https://api.semanticscholar.org/graph/v1/paper/DOI:10.1038/s41586-020-2649-2?fields=paperId,externalIds
- **S2 `paperId` 是一个把 7 个外部标识符聚成一簇的稳定聚类 ID。** 这正是"作品身份"层需要的东西。

**OpenAlex Work 对象（同日实时调用 https://api.openalex.org/works/https://doi.org/10.1038/s41586-020-2649-2）**：
- `ids` 含 `openalex` / `doi` / `mag` / `pmid`
- 布尔字段 `is_retracted`、`is_paratext` 存在（本例均为 false），另有 `is_xpac`
- `primary_location` 与 `locations[]` 都带 `version` 字段，实测取值 **`publishedVersion`、`submittedVersion`**（COAR/Unpaywall 版本词表；另有 `acceptedVersion`）
- **没有**直接把 preprint 连到发表版的字段；只能通过 `locations` 数组里同时出现 arXiv 与出版社条目间接关联

**arXiv 版本与 DOI（官方文档）**：
- https://info.arxiv.org/help/versions.html：*"Any replacement or withdrawal of that article generates a new version. This will increment its version number by one"*；*"Once made public, each version of a work is considered a permanent part of the scientific record and may not be removed."* 撤回版本只显示撤回理由、不提供下载。
- https://info.arxiv.org/help/doi.html：*"All articles submitted to arXiv are automatically assigned DOIs that correspond to their arXiv ID."*；**"Replacing an article with a new version will not generate a new DOI"**；该 DOI **"will always point to the latest version of the article"**。格式 `https://doi.org/10.48550/arXiv.2202.01037`。
- **结论：arXiv 场景下唯一有效的版本锚是 `arXiv:YYMM.NNNNNvN` 中的 `vN`，DOI 不是。**（对照：Zenodo/DataCite 体系是每版本一个 DOI + 一个 concept DOI；两套体系语义相反，schema 必须能区分。）

### 9. 撤稿状态的程序化获取

**Crossref REST API（实时验证，一手）**：对已撤稿论文 https://api.crossref.org/works/10.1016/S0140-6736(20)31180-6，记录同时含 `update-to` 与 `updated-by` 数组：
```json
"updated-by": [{
  "DOI": "10.1016/s0140-6736(20)31324-6",
  "type": "retraction", "label": "Retraction",
  "source": "retraction-watch",
  "updated": {"date-parts": [[2020,6,5]], "timestamp": 1591315200000},
  "record-id": "23529"
}]
```
`source` 区分 `publisher` 与 `retraction-watch`；`type` 除 `retraction` 外还有 expression of concern、erratum、correction 等。**这是一个完全机器可判定的撤稿/更正事件源，且带日期和 RW record-id。**

**Retraction Watch 数据集**：
- 收购公告 https://www.crossref.org/blog/news-crossref-and-retraction-watch/ （2023-09-12，Crossref 收购 RW 数据库并公开）
- 数据仓库 https://gitlab.com/crossref/retraction-watch-data
- CSV 18 列：Record ID / Title / Subject / Institution / Journal / Publisher / Country / Author / URLs / ArticleType / RetractionDate / RetractionDOI / RetractionPubMedID / OriginalPaperDate / OriginalPaperDOI / OriginalPaperPubMedID / **RetractionNature** / Reason / Paywalled
- README：*"updated every working day by Retraction Watch"*；当前文件标注生成于 **2026-08-14**（查询日 2026-08-17，即 3 天新鲜度）
- **`RetractionNature` 字段是关键**：它区分 Retraction / Correction / Expression of Concern / Reinstatement——即"撤稿"不是布尔量，而是一个带方向的枚举（含**复原** Reinstatement）。任何把撤稿建模成 boolean 的 schema 都会丢掉这个信息。

### 10. preprint → VoR 解析

**bioRxiv 官方 API（实时验证）**：`https://api.biorxiv.org/pubs/biorxiv/{起}/{止}` 直接返回 preprint→published 映射，字段含 `preprint_doi` / `published_doi` / `published_journal` / `preprint_platform` / `preprint_title` / `preprint_authors` / `preprint_category` / `preprint_date` / `published_date` / `preprint_abstract` 等。2026-01-01～01-05 五天区间返回 190 条。**这是最干净的一手 preprint→VoR 通道。**

**但其底层匹配方法有已知的高假阴性**：Abdill & Blekhman, eLife 2019（https://elifesciences.org/articles/45133）明确指出 bioRxiv 的关联系统 *"relies heavily on title-based matching"*。作者手工复核 120 篇随机抽取的"未发表"预印本，发现 **37.5% 实际已发表**；2015 年队列的假阴性率高达 53%，2017 年降到 17% 以下。

**发表率数字本身高度依赖队列窗口**（见核验表）：整体 42.0%（15,797/37,648，截至 2018-11），但 2013–2016 投稿队列为 67.0%，2018 年队列仅 20.0%。**同一个"预印本发表率"可以在 20% 到 67% 之间任取，取决于你怎么框队列。**

---

## 载荷数字核验表

| 数字 | 口径三元组（指标 / 样本条件 / 对比基准） | 状态 | 一手出处 |
|---|---|---|---|
| **93.37%** | Citation Accuracy (C.Acc.) = 被判为 "support" 的 statement-URL 对占该任务全部唯一对的比例，再按任务平均 / DeepResearch Bench 100 题 22 领域，WebWeaver + Claude-sonnet-4-20250514，**裁判为 Gemini-2.5-Flash（LLM 裁判，非人工）** / vs Gemini-2.5-pro-deepresearch 78.30% | verified | arxiv.org/html/2509.13312v2 Table 1；定义见 arxiv.org/html/2506.11763v1 Eq.5 |
| **78.30%** | 同上 C.Acc. / 同基准，Gemini-2.5-pro-deepresearch / 次优专有系统 | verified | arxiv.org/html/2509.13312v2 Table 1 |
| **200.75 / 165.34** | E.Cit. = 每任务平均"被支持的 statement-URL 对"总数 / 同基准，WebWeaver vs Gemini-2.5-pro-deepresearch / — | verified | 同上；定义 Eq.6 |
| **96% / 92%** | FACT 裁判(Gemini-2.5-Flash)与人工评测的一致率，分别针对 "support" 判定与 "not support" 判定 / 100 个 statement-URL 对 / — | verified | arxiv.org/html/2506.11763v1 Appendix C |
| **100 题 / 22 领域** | DeepResearch Bench 规模，博士级任务，领域专家出题 | verified | arxiv.org/abs/2506.11763 |
| **79.4%** | 被独立专家科学家判为 Supported 的陈述占比（判定二元 Supported/Refuted，依据自行复现分析或文献佐证）/ **从 3 份代表性报告中抽取的 102 条陈述** / **无任何其他 AI 系统或人类报告的对照数字** | verified | arxiv.org/html/2511.02824v1 |
| **85.5% / 82.1% / 57.9%** | 同上准确率，按陈述来源分层：数据分析 / 文献综述 / 二者之间的综合解释 / 102 条内的三个子集（子样本很小；57.9% 与 11/19 精确吻合，但论文未给分层 n，此为**我的推断**） | verified（分层 n 为 unverified） | arxiv.org/html/2511.02824v1 |
| **1,500 篇 / 42,000 行 / 200 rollouts / 12 小时 / 20 cycles** | 单次 Kosmos 运行的平均量：读论文数、执行代码行数、agent rollout 数、最长运行时长、测试过的最大 cycle 数 | verified | arxiv.org/abs/2511.02824 摘要 |
| **6 个月** | 合作者**自报**的"等效于自己多少研究时间"，均值，针对单次 20-cycle 运行 / 主观自报，非测量 | verified（作为自报） | arxiv.org/abs/2511.02824 摘要 |
| **26%** | LLM-as-a-Judge 指标上的**相对**提升 / LOCOMO 基准 / vs OpenAI Memory | verified | arxiv.org/abs/2504.19413 |
| **91% / >90%** | p95 延迟降低 / token 成本节省 / vs full-context 方案（非 vs 其他 memory 系统） | verified | arxiv.org/abs/2504.19413 |
| **92.5 / 94.4** | mem0 官网自报 LoCoMo / LongMemEval 分数，**页面未说明该分数是准确率、J score 还是 LLM 裁判分**；未列具名竞品 / 页面日期 2026-08-14 | **corrected** — 二手转述为 "91.6 / 94.8"，与官方页当前值不符；两者至少一个已过期 | mem0.ai/research（2026-08-14 版） |
| **75.14% ±0.17** | J score / LoCoMo，**包含第 5 类对抗题**、Zep 自行修改过 system prompt 与检索模板、**单次运行** / vs mem0 最佳配置约 +10% 相对 | verified（作为 Zep 主张） | blog.getzep.com/lies-damn-lies-statistics-is-mem0-really-sota-in-agent-memory/ |
| **58.44% ±0.20** | 同一个 Zep 系统的复算 / LoCoMo，**仅第 1–4 类**、还原 mem0 原始 prompt 与模板、**10 次独立运行取平均** / vs Zep 旧版算法 65.99% ±0.16 | verified（作为 mem0 复算） | github.com/getzep/zep-papers/issues/5 |
| **16.70 pp** | 上两行之差：**同一系统、同一基准，仅因题目类别纳入与 prompt 配置不同** | verified（我的算术） | 两行相减 |
| **~73% vs ~68%** | J score / LoCoMo，**朴素 full-context 基线** vs mem0 最佳配置 / — | verified（作为 Zep 主张） | blog.getzep.com/lies-damn-lies-statistics-… |
| **16k–26k tokens** | LoCoMo 对话平均长度，Zep 据此论证该基准落在现代 LLM 上下文窗内、不足以测长期记忆 | verified | 同上 |
| **94.8% vs 93.4%** | DMR (Deep Memory Retrieval) 基准得分 / Zep vs MemGPT | verified | arxiv.org/abs/2501.13956 摘要 |
| **up to 18.5%** | LongMemEval 准确率提升，**"up to" 为上界表述而非典型值**；同时称延迟降低 90% | verified（口径本身即模糊） | arxiv.org/abs/2501.13956 摘要 |
| **6.4%** | LoCoMo 答案键"根本性有缺陷"的比例 / 某次审计 / — | **unverified** — 仅见于二手综述页，未找到一手审计报告 | 二手（不采用） |
| **1,409 claims / 5,183 abstracts** | SciFact 规模：专家撰写 claim 数 / 语料摘要数；测试集每类 100 claim 平衡 | 部分 verified（ACL 页仅确认 "1.4K claims"，精确拆分来自二手） | aclanthology.org/2020.emnlp-main.609/ |
| **42.0%（15,797/37,648）** | 已在同行评审期刊发表的 bioRxiv 预印本占比 / **全站所有预印本，截至 2018-11**，匹配方式为 bioRxiv 内部标题匹配 / — | verified | elifesciences.org/articles/45133 |
| **67.0% / 64.0% / 20.0%** | 同一发表率，分别限定于 2013–2016 投稿队列 / 含 2017 / 仅 2018 队列 | verified | 同上 |
| **37.5%** | 手工复核 120 篇随机抽取的"未发表"预印本中，**实际已发表**的比例（即标题匹配的假阴性率）；2015 队列 53%，2017 队列 <17% | verified | 同上 |
| **134,175** | OpenAlex `is_retracted:true` 的 work 数 / 实时查询 2026-08-17 | verified | api.openalex.org/works?filter=is_retracted:true |
| **74,607** | Crossref `update-type:retraction` 的 work 数 / 实时查询 2026-08-17 | verified | api.crossref.org/works?filter=update-type:retraction |
| **1.8×** | 上两行之比：**同日、同"撤稿"概念、两个权威源相差近一倍** | verified（我的算术） | 两行相除 |
| **~50,000（43,000 + 14,000，含重叠）** | 2023-09 Crossref 收购时 RW 库 + Crossref 自有撤稿元数据的量级 / **2023 年数据，已过期，仅供趋势参照** | verified（作为 2023 值） | crossref.org/blog/news-crossref-and-retraction-watch/ |
| **18 列** | Retraction Watch CSV 的列数；含 `RetractionNature`（Retraction/Correction/EoC/Reinstatement 枚举） | verified | gitlab.com/crossref/retraction-watch-data README |
| **2026-08-14** | RW 数据文件当前生成日期（查询日 2026-08-17）；README 称每个工作日更新 | verified | 同上 |
| **7** | 同一篇论文（NumPy/Nature）在 S2 上的外部标识符数量：DOI/ArXiv/CorpusId/PubMed/PMC/MAG/DBLP | verified | api.semanticscholar.org 实时调用 2026-08-17 |
| **190 条** | bioRxiv preprint→published 映射在 2026-01-01～01-05 五天窗口内的记录数 | verified | api.biorxiv.org/pubs/biorxiv/2026-01-01/2026-01-05 |
| **100%（depth-four）** | MemClaw 成功重建的四层派生链比例，writer identity 正确，每跳亚秒延迟 / **生产系统自测，无基线对照** | verified（无对照） | arxiv.org/html/2606.24535v1 |
| **35% / 44.8% / 0.4%** | arXiv 多版本论文占比（全站 / 量子计算 / 医学） | **unverified** — 仅见于搜索摘要转述，未能定位一手论文；**不得作为裸数字使用** | — |
| **29.2%，中位 5 个月** | 2024–2025 年四大安全会议论文中以 arXiv 预印本形式出现的比例，及预印本先于发表的中位月数 | verified（一手摘要） | arxiv.org/abs/2606.18320 |

---

## 对本项目的设计含义

### A. 三层身份模型（回答"N 个并行 worker 从不同 URL 抽取同一篇论文"）

```
work_id      作品身份（跨版本、跨 URL、跨标识符的同一件学术工作）
  └ version_id   版本身份（你实际读到的那一版）
      └ evidence_id  证据身份（那一版里的某个具体片段）
```

**`work_id` 解析阶梯（确定性，按序，失败即降级）**

| 级 | 输入 | 键 | 置信度 | 允许自动合并？ |
|---|---|---|---|---|
| 0 | 已有 S2 `paperId` 或 OpenAlex work ID | 直接用 | exact | 是 |
| 1 | DOI | 归一化 DOI（小写、剥离 `https://doi.org/` 前缀与尾部标点） | exact | 是 |
| 2 | arXiv ID / PMID / PMCID | 经 S2 或 OpenAlex 解析到聚类 ID | exact | 是 |
| 3 | 标题 + 首作者姓 + 年份指纹 | `normalize(title)+surname+year` | **low** | **否——只允许提出候选，进人工/裁决队列** |

第 3 级的禁令来自实测：bioRxiv 的生产级标题匹配假阴性率 37.5%，足以把一个头条统计量搞错约 25 个百分点。**模糊身份可以提议合并，绝不能静默执行合并。** 未解析成功的证据以 `work_id = "unresolved:<hash>"` 落库，照常可引用，只是不参与跨源聚合——**绝不因为解析不了就丢弃或强行合并**。

**URL 的地位被彻底降级**：`access_url` 是 payload 字段，**永远不是键**。这是对 WebWeaver 方案（`url2id[url] = len(url2id)+1`）的直接否定。

**`version_id` = `work_id@<version_token>`**
- arXiv：token = `v2` 等显式版本号。**因为 arXiv DOI 恒指最新版（官方确认），DOI 不能充当版本锚。**
- 期刊 VoR：token = 归一化 DOI + `retrieved_at` 日期
- 网页/其他：token = URL + 正文内容哈希 + `retrieved_at`
- 必填 `version_kind` 枚举，直接复用 OpenAlex/COAR 实测词表：`submittedVersion` / `acceptedVersion` / `publishedVersion` / `unknown`

### B. 去重键：按来源坐标，绝不按内容（核心建议）

```
evidence_id = sha256(work_id ‖ version_id ‖ locator ‖ normalize(quote) ‖ extractor_version)
```
其中 `locator` = 结构化位置（section 路径 + 字符区间，或引文在正文中的定位哈希）。

**为什么必须这样**：MemClaw 的一手教训——同步近重复门会把矛盾当重复毙掉（"XX is AA" 与 "XX is BB" 在 embedding 空间近乎重合）。**两条真正矛盾的证据在语料库中物理上位于不同位置**，因此按来源坐标去重在构造上不可能吃掉矛盾；而按内容相似度去重必然会。

**由此获得的四个性质（对超并行至关重要）**：
1. **幂等**：N 个 worker 抽到同一句 → 同一 `evidence_id` → 主键碰撞 → 天然去重，零协调开销、零锁。
2. **零 LLM 成本**：去重是哈希比对，不需要 embedding 调用，也不需要 Graphiti 式的"每次写入一次 LLM 裁决"。
3. **管线顺序无关**：MemClaw 那个"去重门 vs 矛盾检测器"的顺序 bug 类被设计消除，而不是被规避。
4. **可复现**：`extractor_version` 入键，意味着换了 prompt/模型重跑会产生新行而非覆盖旧行 —— 满足"可重跑"这一产品前提。

**证据库整体 append-only、行不可变。** 依据 Letta 的并发契约表：append-only 是唯一被官方标为并发安全的操作；整体重写（`memory_rethink`）被明确标为反模式、会丢更新。

**可变的判断放在独立的 overlay 表**（键为 `evidence_id`），用 compare-and-swap 更新——即 Letta `memory_replace` 的 "fails if target string changed" 语义提升为一等契约：状态转移必须携带读到的版本号，不匹配则失败重试。**不可变事实 / 可变判断分离**，是并行安全的关键切口。

### C. 学术分歧 vs 证据被取代（两种关系，绝不混用）

现有系统全部只有一种关系，且都错：mem0 = 矛盾即 DELETE；Graphiti = 时间新者胜。本项目必须区分：

| 关系 | 触发条件 | 是否自动执行 | 旧证据去向 |
|---|---|---|---|
| `supersedes` | **仅限机器可判定的学术记录事件** | 是 | 标 `superseded`，**保留可查** |
| `contradicts` | 不同 work 的结论不相容 | **否，永不自动消解** | 双方均保持 live |

**`supersedes` 的白名单（穷举，全部机器可判）**：
1. Crossref `updated-by` 中 `type ∈ {retraction, correction, erratum, expression-of-concern}` — 实时可查，带 date 与 RW `record-id`
2. Retraction Watch `RetractionNature` 枚举（含 **Reinstatement** —— 撤稿可被撤销，所以该字段必须是枚举而非 boolean）
3. **同一 work 的版本递增**（arXiv v1→v2，或 preprint→VoR 且 `published_doi` 由 bioRxiv API 确证）
4. 同一组作者在后续论文中显式声明取代自己的前一结果

**不在白名单内的一切不相容，都是 `contradicts`**，claim 状态置 `contested`，双方立场、样本条件、metric_frame 一并呈现。这直接杜绝 mem0 式的"后来的论文静默删掉先来的论文"。

**立场词表沿用 SciFact 的 SUPPORTS / REFUTES / NOINFO，但挂在 (claim, evidence) 边上**（比 SciFact 的 (claim, abstract) 再细一级）——因为同一篇论文可以支持断言的一部分、反驳另一部分。

**注意 MemClaw 的补充约束**：其结构化取代检测器"只对服务端认定为单值的谓词生效"。同理，本项目只应对**单值谓词**（如"该论文是否被撤稿"）启用自动取代；对多值谓词（如"某干预的效应量"）永远走 `contradicts`。

### D. 每条证据的必填字段

**身份层（全部必填）**：`evidence_id`（内容寻址）、`work_id`、`version_id`、`version_kind`、`locator`

**内容层（全部必填）**：
- `quote` —— **逐字原文**，有长度上界。无 quote 即无证据；这是"可追溯到源文本"的物理实现。
- `claim_text` —— 抽取出的命题
- `metric_frame` —— **本项目独有、也是与所有被调研系统的根本差异**：`{metric, sample_or_condition, comparator}` 三元组。凡含数字的证据，缺此字段即**不可用**，只能落为 `unverified`。
  - 依据：同一系统同一基准因类别纳入与 prompt 配置不同而差 16.70 pp（Zep 75.14 vs 58.44）；"预印本发表率"因队列窗口不同可在 20%–67% 间任取。**指标名相同不代表口径相同，所以 metric_frame 必须包含评测配置，而不只是指标名。**
- `judge_provenance`（当数字来自 LLM 裁判时必填）：裁判模型 + 其人工一致率。依据：93.37% 这个数字实为 Gemini-2.5-Flash 的判定结果，而该裁判自身与人工的一致率是 96%/92%——不记录这一层，就是在把裁判误差洗成系统性能。

**判定层（全部必填，可随时间变更，走 CAS）**：
- `stance` ∈ {SUPPORTS, REFUTES, NOINFO}
- `verification_status` ∈ {verified, corrected, unverified}
- `verification_method` ∈ {rerun_analysis, source_quote, logical_inference} —— 对应项目的三种门。
  依据：Kosmos 实测三类的准确率为 85.5% / 82.1% / **57.9%**，跨度约 28 pp。**不逐条记录方法就无法解释总准确率**；且解释类最弱这一事实，正面支持"论文组装做薄、验证做厚"。
- `claim_status` ∈ {open, verified, contested, superseded}

**记录层（全部必填）**：
- `retraction_status` + **`retraction_checked_at`** —— 必须带检查时间戳，因为它会过期。**且必须双源**（Crossref + OpenAlex）：同日两源相差 1.8 倍（74,607 vs 134,175），单源必然给出错误的撤稿判断。不一致时置 `retraction_status = disputed`，不做静默取舍。
- `provenance`：`written_by`（agent id）、`written_at`、`derived_from`（父 evidence_id 列表）、`extractor_version`
  依据：MemClaw 把 provenance collapse 列为四大失效模式之一，其对象存 writer identity / source system / derivation history / modification lineage，并实测可重建四层派生链。
- `retrieved_at`、`access_url`（数据，非键）
- `superseded_by`（可空）+ `supersession_reason`（白名单枚举）
- `contradicts`（evidence_id 列表，永不自动消解）

**可从 WebWeaver 借用的一个字段**：`goal` —— 本次抽取意在回答什么。它把"为何采集"绑进记录，与 `metric_frame` 同属一类设计（解释该行所需的上下文不留给下游重建）。

### E. 明确的反模式清单（来自一手证据，写进设计文档作为硬约束）

1. **禁止**以 URL 为去重键（WebWeaver 实测：同论文多 URL → 多条记忆 + 多个引用 ID）
2. **禁止**同步 pre-commit 的语义近重复门（MemClaw 实测：会 409 掉矛盾本身）
3. **禁止**矛盾即删除（mem0 提示词规则，对科学证据是灾难）
4. **禁止**纯时间性失效（Graphiti 规则：新的不使旧的失效——科学上不成立）
5. **禁止**多 agent 对同一记忆块整体重写（Letta 官方标注的反模式，丢更新）
6. **禁止**把撤稿建模为 boolean（RW `RetractionNature` 含 Reinstatement）
7. **禁止**用 DOI 作为 arXiv 内容的版本锚（官方：DOI 恒指最新版）
8. **禁止**单源撤稿判定（两权威源同日相差 1.8 倍）
9. **禁止**无 metric_frame 的裸数字入库
10. **警惕"框架能赢"的幻觉**：LoCoMo 上朴素 full-context 基线 J score ~73%，高于 mem0 最佳配置 ~68%。**任何记忆/证据框架都必须先证明自己胜过"把东西全塞进上下文"这一朴素基线**，否则框架本身就是净负债——这与前代项目"claim-graph 框架失败"的结论高度一致。

---

## 未决与风险

**未能一手核实（不得当作已知）**
1. **arXiv 多版本占比**（二手称全站 35%、量子计算 44.8%、医学 0.4%）——找不到一手论文，本轮 WebSearch 预算耗尽。若"版本漂移有多严重"要作为设计论据，必须补做：可用 arXiv OAI-PMH 或 Kaggle arXiv 全量元数据自行统计，这是可自证的。
2. **LoCoMo 答案键 6.4% 有缺陷**——仅见二手综述。
3. **Klein et al. 预印本↔发表版文本相似度的具体阈值与样本量**——PDF 为二进制未能解析，只取到摘要级结论"文本内容变化很小"。若要用"版本漂移小所以可以不锚版本"作论据，此条必须补齐（且我倾向于**不用**该论据：即使平均漂移小，本项目关心的是尾部——被引用的那句话是否改了）。
4. **mem0 官网 92.5/94.4 与二手 91.6/94.8 的差异**——未能确定哪个是当前值、指标定义为何。mem0 官网页面未说明分数的指标类型，这本身就是一个口径缺陷。

**方法论风险**
5. **本轮所有"最新 SOTA"数字都会快速过期。** mem0 自家页面（2026-08-14）与三天前的二手转述已经对不上。任何进入本项目文档的性能数字都必须带 `as_of` 日期，并设复查周期。
6. **假独立佐证的残余风险**：Kosmos 的 world model、WebWeaver 的 memory bank 都被大量二手页转述且互相引用。本轮所有结构性结论均回到 arXiv 全文或 GitHub 源码，但 Kosmos 一项**确证为"未披露"**——若后续有人从二手页看到 world model 的字段描述，那大概率是杜撰或推测，需警惕。

**设计层未决**
7. **`locator` 的具体粒度未定**：section 路径 + 字符区间在 PDF 上不稳定（不同解析器给出不同偏移）。可能需要退化为"引文文本的归一化哈希 + 首次出现序号"。这直接影响 `evidence_id` 的跨 run 稳定性，是**必须在实现前解决**的问题。
8. **`extractor_version` 入键会导致换模型即全库翻倍。** 需要一个"逻辑等价证据"的软链接层（新旧行互指），否则升级一次 prompt 就把历史验证结果全部作废。这与"keep-if-better 循环"的交互尚未想清。
9. **`contradicts` 的发现机制未定。** 按来源坐标去重意味着系统不会主动比较内容——那么矛盾由谁发现？倾向方案：矛盾检测**异步、离线、只在 claim 层（而非 evidence 层）运行**，且只对同一 claim 下已聚集的证据集做，永不阻塞写入路径。这正是 MemClaw 做对的那一半（异步矛盾检测），只是要把它错的那一半（同步近重复门）整个拿掉。
10. **OpenAlex `is_retracted` 的精确率未知。** 134,175 这个数远高于 Crossref 的 74,607，怀疑其口径包含撤稿声明本身（`is_paratext` 类条目）或采用了更宽的判据。落地前应抽样人工核验，否则"撤稿检查"会产生大量假阳性、误杀有效证据。
