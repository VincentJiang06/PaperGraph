# 迭代 #1 — V3 缺陷修复(Opus,2026-07-09)

承接 docs/07 路线图,本轮修掉两轮实测暴露的**确定性缺陷**(不含需先采证的
R2/R4/R9/R10 现场项)。纪律:doc-first → code → tests → 本记录。46 tests 全绿;
live 会话 ai-jobs-paper 在新代码下复检仍 0 hard / 0 soft。

## 修复项

| R | 缺陷 | 修法 | 测试 |
|---|---|---|---|
| R1 | **P2 违规**:docs/04 声称 final.md 陈旧性硬检查,代码从未实现 | 把 `assemble` 拆成纯函数 `_render`(确定性,无时间戳);check 在结构无误时重算文章文本与磁盘 final.md 逐字比对,不一致判 hard(提示重跑 assemble) | test_iter1: 改节不重 assemble→hard;内容不变→无误报 |
| R3 | 给已归档条目加绑定要靠"重投同文触发去重合并",绕路且需留着原文件 | `nd docs bind DOC-xxxx --node N --relation R [--note]`(追加 latest 记录;(node,relation) 重复=no-op 告警) | test_iter1: 跨节绑定 / 重复 no-op / 未知 doc·node·relation |
| R5 | 退休一个节点不级联,子树里的 open/pending 工作被静默悬空 | check soft:active 节点若挂在 retired/closed 祖先下,点名最近的 dead 祖先(每个孤儿一条);不自动级联(P4) | test_iter1: 孤儿被点名;随父退休后消失 |
| R6 | node.v1.revises 字段有 schema、无写入方(死表面) | `nd revise N --statement "…"`:铸新节点(新 id·同父同 kind·fresh·revises=N)+ 退休旧节点(note 指向新 id);子节点与绑定**不**自动迁移,命令返回告警 | test_iter1: 铸新/退旧/未迁移告警/退休节拒再 revise |
| R7 | 框架对 subagent/抓取成本零感知 | brief SESSION 增 ACTIVITY 行(从事件日志聚合 add/conclude/ingest/bind/revise 计数);不设机制,只可见(P4) | test_iter1: ACTIVITY 出现且计数正确 |

## 关键设计取舍

- **R1 用重算比对而非哈希/时间戳**:assemble 输出确定且无时间戳,重算与磁盘
  逐字比对即"输出会变 ⇔ stale",无需存额外状态(P9 单一来源)。只在无其他
  article hard 错误时跑,避免对同一根因重复报错。
- **R6 铸新而非原地改**:原地改 statement 会丢历史;铸新+退休保留 revises 链
  可审计。**不级联迁移**是刻意的(P4):框架报告未迁移项,判断权归模型(P11)。
  没有新增 schema——wire 既有字段而非扩面(P5:本轮零 schema 集变更)。
- **R5 报最近 dead 祖先、每孤儿一条**:嵌套退休下不重复报同一孤儿;守卫
  父指针存在(悬空父是独立 hard 项)。

## 未动(需 Opus 现场采证,勿先写代码)

R2 recall 质量(先 TC-F 基准)、R4 规模(先 TC-B)、R8 en 基线、R9 对抗
完整性(TC-J)、R10 语义召回。理由见 docs/07 + docs/08 操作守则。

## 防坑清单核对

P2 修复(R1)、P4 无新机器、P5 零 schema 变更、P9 无镜像、P13 shell 纪律——
全部满足。闭表 20→22 组(docs bind + revise),测试镜像已双向更新。
