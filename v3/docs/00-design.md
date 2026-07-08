# PaperGraph v3 设计 — 一棵树、一个主人、一部法律

> 权威顺序:`v3/schemas/*.schema.json`(法律)> 测试 > 本文(导读)。
> 本文中任何规范性句子要么指向 schema/测试,要么标注 `[unenforced]`(P2)。
> 防坑对照:`01-anti-failure.md`。

## 1. 核心图景

三层结构,单棵树,无编排者:

- **观点层(viewpoint)** —— 抽象观点,宽松逻辑(命题或问题皆可)。工作方式
  是**发散**:提出"有助于判断本观点、但不预设本观点真假"的新方向子问题
  (独立性判据),而非拆解量化。每次发散强制 ≥1 个对抗方向(adversarial)。
- **论点层(claim)** —— 观点发散走到尽头(说不出反事实探针)时,该节点
  **原地升格**为论点:一个最小的、适合直接交给工具解决的明确问题。升格必须
  提交 promote 表单(尝试过的方向 + 为何不成立 + 工具适配)。论点层负责把
  问题转译成**具体研究方向**交给论证层,并判断论证结果是否充分。拆解只在
  论点层合法(论点可拆成子论点)。
- **论证层(argumentation)** —— 不是节点,是挂在论点上的任务+结果记录对。
  由 Sonnet 子代理执行,五种工具,一次任务一个独占 workdir 一个结果文件。
  只报告,不判断充分性归属(报告自评 sufficient 供参考,裁量权在论点层)。

向上回流由**结论记录(synthesis)**承载:观点层在子节点足够时显式写结论
(lean/summary/based_on/open_questions),可随认识追加新版。compiler 只消费
synthesis,不消费原始论证结果——判断被摊到树生长全程,而不是堆在最后。

## 2. 记录与文件布局

```
projects/<id>/
  spec.json                      # spec.v3(5 字段,P15)
  tree/nodes.jsonl               # node.v3,append-only,latest-per-id
  tree/syntheses.jsonl           # synthesis.v3,append-only
  argue/tasks/T-xxxx/task.json   # argue.task.v3;workdir 含 sources/
  argue/results/T-xxxx.result.json   # argue.result.v3(worker 唯一可写物,连同其 workdir)
  docs/index.jsonl               # docs.entry.v3,append-only,latest-per-doc
  docs/store/DOC-xxxx.{raw,txt}  # 归档原文与抽取文本
  local/                         # 用户导入的本地数据/论文(pt import-local 索引)
  article/thesis.json outline.json sections/S-*.md final.md
```

id 形态:`N-0001` `T-0001` `DOC-0001` `SYN-0001` `S-01`,max+1 分配,无计数器
文件(继承 v2 可用的部分)。JSONL 一律 append-only、latest-per-id。

## 3. 状态与合法迁移(全部由 pt 校验)

- viewpoint:`open → expanding → synthesized → closed`;任意时刻 `→ retired`
- claim:`pending → tasked → answered → concluded | stuck`;任意时刻 `→ retired`
  - `stuck` 细分记录 reason:`evidence`(3 轮论证仍不足)/ `protocol`
    (schema 无效重派 2 次仍失败)
- 升格 = 同一 node_id 追加一条 kind=claim 的记录,携带 promotion 表单
- 没有队列、租约、状态机引擎(P4)。并发故事一句话:argue 任务不相交,
  树/docs 写入主会话串行。

## 4. 论证层

两种任务类型,同一结果协议:

| type | 模型 | 工具 | 用途 |
|---|---|---|---|
| `search` | Sonnet | recall(强制第一步)+ web_search + academic | 默认 |
| `analysis` | Sonnet | data_analysis + local + recall | 需要算数/本地数据时由论点层显式选择 |

- **recall-first 记忆化**:`pt argue emit` 在派发时就把 top-k recall 命中
  (文件引用)内嵌进任务包(P8)。
- **不足回路**:结果 `sufficient_for_question=false` 时论点层三选一——
  细化方向重派(≤2 轮)/ 拆解论点 / 接受部分答案并让父 synthesis 记录缺口。
  协议无效 → 带校验错误重派 ≤2 次 → `stuck(protocol)`。
- worker 写权限:自己的 workdir + 声明的结果文件,别处一律不碰(P12)。
- 五工具中 academic 的纪律:引用必须带 venue/authors/year;web_search 抓到的
  页面文本存 workdir/sources/ 以便 ingest 归档(不二次抓网)。

## 5. docs 库

- 单写者:只有 `pt argue ingest` 与 `pt docs import-local` 写 docs/(P7/P12)。
- ingest 四步:schema 校验 → content_hash 去重归档 → quote 逐字校验
  (失败降级 paraphrase+告警)→ 生成绑定(node_id 为准,path 仅快照)。
- **recall 排序 = 树距离优先**:本节点 → 祖先 → 兄弟子树 → 全局;同档内
  CJK 感知词法打分(textutil 从 v2 复用)。语义向量为 v3.1 可选升级,
  不作基础依赖。
- recall 是纯读操作,永不改变任何状态(P8)。

## 6. compiler

三段决策、每段一份 JSON 记录、排除与收录同样留痕:

1. `compile.thesis` —— 从根 synthesis 提炼文章论题;列出树支持/不支持/缺口。
2. `compile.outline` —— 章节↔树枝映射;**必须记录被排除的枝与理由**。
3. `compile.section` —— 逐节成文,行内 `(cite: DOC-xxxx)`。

`pt compile check` 机械校验:每个 cite 解析到归档条目、quote 逐字命中、
每个进入文章的结论沿 synthesis → argue.result → sources → docs.entry →
归档文件走通(P6/P7)。

## 7. 运行时角色

- **主会话(大模型)= 树主人**:expand / promote / synthesize /
  argue emit+ingest / compile,一切落盘经 pt。
- **子代理**:argue worker(Sonnet×2 种任务)、expand-critic(小模型,
  抽查发散独立性,advisory 不阻塞)。
- prompt 三段结构(P11):目标与判断责任 / 资源 / 输出契约(逐键枚举,P1)。

## 8. pt CLI(封闭清单,15 条,P4)

```
pt init <id>                     pt validate
pt tree add --expand-file F     pt tree promote --form-file F
pt tree synthesize --file F     pt tree status [--node N]     pt tree show N
pt argue emit N [--type T]      pt argue ingest T
pt docs import-local PATH       pt docs for-node N            pt recall --node N --query Q
pt compile thesis|outline|section --file F      pt compile check
```

每条命令输出一个 JSON envelope(envelope.v3)。命令清单由契约测试双向镜像;
扩表 = 先改本文 + 测试。

## 9. schema 目录(法律本体,12 份)

envelope / spec / node / expand.result / synthesis / argue.task / argue.result /
docs.entry / recall.result / compile.thesis / compile.outline / compile.section
—— 全部 `additionalProperties:false`,带 `$id` 与版本;**运行时直接加载
schema 文件校验,不写第二份模型镜像**(P9)。项目 init 时记录 schema 集
hash,此后该项目协议冻结(P5)。

## 10. v3 明确不做

队列引擎/租约/状态机、Committer/Validator 分权、verdict 决策表、波次+合议
critic、BFS/top-k、边记录、WebUI、语义检索(v3.1)、多 project 并发。
