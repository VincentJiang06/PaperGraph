# Nodify V3 — 学术写作层(设计,2026-07-09)

> V3 把树渲染成**可审计的文章**:大纲与成文是带记录的决策,文中每个引用
> 机械回溯到归档条目(P6/P7 的成文形态)。树是整理器,文章是渲染结果。
> 权威顺序不变:schema 文件 > 测试 > 本文。

## 1. 立场

- 写什么、怎么组织、哪些枝入文哪些不入——**全是模型的判断**;框架只记录
  决策并强制可回溯。
- **文章只允许消费 synthesis 与归档 docs**,不消费过程文本(V1 落点的成文
  延伸)。
- 排除决策与收录决策同样留痕:大纲必须列出被排除的枝与理由。

## 2. 记录与布局(新增)

```
sessions/<id>/
  article/records.jsonl    # article.outline.v1 / article.section.v1,append-only
  article/S-xx.md          # 各节成文(nd article section 注册后落此)
  article/final.md         # nd article assemble 产物(含自动参考文献)
```

schema set **v3** = v2 全部 + 2 份:

1. `article.outline.v1` — {outline_id OL-01, title, thesis,
   grounded_in[SYN-ids](≥1), sections[{section_id S-01, title, role ∈
   {introduction, background, argument, evidence, counterpoints, discussion,
   conclusion, other}, node_ids[], intent}](≥1),
   excluded[{node_id, reason}], created_at}
   —— thesis 必须扎根于已有 synthesis(grounded_in 悬空 = 硬错误);新版大纲
   直接追加(latest-per-outline_id... 单 outline_id "OL-01",修订即追加同 id
   新记录,latest 生效)。
2. `article.section.v1` — {section_id, source_file(注册时读取的草稿),
   file(article/S-xx.md), cites[DOC-ids](从文中扫描), word_count,
   created_at}

## 3. CLI 扩表(15 → 19 组)

```
nd article outline --file outline.json    # 记录/修订大纲(校验 SYN/N 引用)
nd article section --id S-01 --file draft.md
      # 注册一节成文:扫描 (cite: DOC-xxxx) 标记,悬空引用 = 硬拒绝;
      # 文件复制为 article/S-01.md,追加记录
nd article assemble                       # 按大纲顺序拼 final.md +
                                          # 自动参考文献(cite 并集 → 条目)
nd schema <alias|record>                  # 自描述:schema 全文 + 示例 payload
      # (实测 #1 F2;无 session 依赖,是唯一不记 event 的命令)
```

成文标注语法(机械可查的最小集):正文引用处写 `(cite: DOC-0001)`;
其余格式自由。assemble 生成 References 一节:每个被引条目一行
`[DOC-0001] title — url`。

## 4. check 融合(article 存在时追加)

- hard:section 记录的 cites 悬空;outline 的 grounded_in/node_ids/excluded
  悬空;assemble 后 final.md 中的 cite 与 records 不一致(重跑 assemble 可修)。
- soft:大纲节未注册成文;成文节不在最新大纲;argument/evidence 节零引用;
  被排除节点无 reason。

## 5. 升级

set v2 session 使用 article 命令 → 提示 `nd upgrade`(v2→v3);upgrade 始终
跳到 CURRENT_SET。
