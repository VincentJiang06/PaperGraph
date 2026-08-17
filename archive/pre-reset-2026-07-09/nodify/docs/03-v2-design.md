# Nodify V2 — docs 记忆化库(设计,2026-07-09)

> V2 给 V1 的树补上**证据的家**:归档、去重、逐字防伪、树距离召回、
> 摘要式压缩。V1 的防坑 P7/P8 从"V2 再说"升为 **hard**。
> 权威顺序不变:schema 文件 > 测试 > 本文。

## 1. V2 增加什么(以及仍然不做什么)

做:
- **归档**:来源文本收进 `docs/store/`,index 单写者、append-only;
- **content_hash 去重**:同一文本第二次入库 = 给已有条目追加绑定,不复制;
- **quote 逐字校验(P7 hard)**:synthesis 证据带 doc_id + quote 时,与归档
  文本做 whitespace-normalized 子串校验;不命中→ quote 自动降级为 null +
  envelope 告警(结论仍落盘,幻觉引文不落盘);`nd check` 静态复检全部
  已落盘 quote(归档文本被改动 = 硬错误);
- **树距离召回**:`nd recall --node N --query "…"`,距离档
  self > descendant > ancestor > sibling > global,同档内 CJK 感知词法
  重合度,纯读零写(P8 hard:召回只供材料,永不改状态);
- **压缩化**:index 只存短 summary(强制 ≤500 字符),全文留在磁盘文件;
  召回返回 summary + 文件引用,模型按需 Read——上下文里永远只有摘要。

不做(留给 V3+ 或永不):网络抓取(工人自己抓,主会话只 ingest 工人存下的
文本)、语义向量、跨 session 共享库、来源可信度分级。

## 2. 记录与布局(新增部分)

```
sessions/<id>/
  docs/index.jsonl         # docs.entry.v1,append-only,latest-per-doc
  docs/store/DOC-xxxx.txt  # 归档文本(唯一必存);同名 .raw.* 可选存原件
```

新 schema 3 份,与 V1 的 5 份构成 **schema set v2**:

1. `docs.entry.v1` — {doc_id DOC-0001, kind ∈ {paper, web, report, dataset,
   local}, title, url?, content_hash sha256, text_file, summary(≤500),
   bindings[{node_id, relation ∈ {supports, refutes, context, background},
   note?, bound_at}](≥1), origin?, retrieved_at}
2. `recall.result.v1` — {node_id, query, hits[{doc_id, title, summary,
   text_file, distance ∈ {self, descendant, ancestor, sibling, global}, why}]}
   (CLI data 载荷的形状约束;召回不落盘)
3. `synthesis.v2` — synthesis.v1 + evidence 条目新增 `doc_id?`(指向归档
   条目;给了 doc_id 且给了 quote 才触发逐字校验)

## 3. schema set 版本化(P5 的 V2 形态)

- 冻结集有名字:**set v1**(5 份)与 **set v2**(v1 的 4 份 + synthesis.v2 +
  docs 两份;synthesis.v1 仍可读旧记录)。
- session.json 里的 schema_set_hash 标识 session 属于哪个集;nd 认得全部
  历史集的 hash。
- v1 session 使用 docs/recall/synthesis.v2 能力 → 明确拒绝并提示
  **`nd upgrade`**:唯一一条重写 session.json 的命令(v1 hash → v2 hash,
  一次性、幂等、记事件)。旧记录不迁移——synthesis.v1 记录在 v2 session 里
  依旧合法可读。

## 4. CLI 扩表(11 → 15 组;先改本文再改测试)

```
nd docs ingest --file entry.json   # 入库:{kind,title,url?,text_file(待归档的文本路径),summary,bindings[...]}
                                   # 代码算 hash;命中已有条目→只追加绑定
nd docs bind DOC-xxxx --node N --relation R [--note …]
                                   # 给已归档条目加绑定,无需重投文本(R3);
                                   # (node,relation) 重复 = no-op 告警
nd docs for-node <N> [--all]       # 列出绑定到 N(默认含祖先)的条目
nd recall --node N --query "…" [--k 8]
nd upgrade                         # schema set v1 → v2(幂等,记事件)
```

conclude 行为变化(v2 session):写 synthesis.v2;evidence 里 doc_id 存在时
校验其条目存在(悬空 = 硬错误),quote 存在时逐字校验(失败 = 降级+告警)。

check 扩展:hard += 条目 schema / text_file 缺失 / bindings 悬空 /
synthesis.evidence.doc_id 悬空 / 已落盘 quote 与归档文本不再命中;
soft += 结论证据既无 doc_id 也无 url/locator、召回可命中却未引用(V3 再说,
先不做)、条目零绑定(不可能:schema 强制 ≥1)。

## 5. 工作流(技能层的 V2 增补)

1. **recall-first**:升格论点、派工人之前,先 `nd recall`;命中的条目直接
   把 text_file 喂给工人("先读这个,再决定搜什么")。
2. **蒸馏后归档**:工人报告里值得留档的来源,让工人把抓到的文本存到
   notes/(草稿区),主会话 `nd docs ingest` 归档并绑定节点,然后 conclude
   的 evidence 用 doc_id 引用。阅后即焚现在有了"焚前入库"一步。
3. 归档判断标准(纪律,非机制):结论实际依赖的来源必归档;背景性浏览
   不归档——库是证据库,不是浏览历史。

## 6. 召回排序(确定性)

对每个条目取其全部 bindings 相对查询节点的**最近距离档**:
self(绑定在本节点)> descendant(绑定在本节点子树)> ancestor(绑定在
祖先链)> sibling(绑定在本节点父节点的子树内,即直接兄弟枝)> global(其余,
含更远的叔伯枝)。
同档内:查询词与 title+summary 的词法重合度(CJK 单字成词 + 拉丁词),
再按 doc_id 升序定序。返回 top-k(默认 8)。
