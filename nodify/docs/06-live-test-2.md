# 实测审计 #2 — Opus 冷接管与深树扩展(2026-07-09)

跑法:Opus 只凭 `nd brief` 冷接管已收敛的 ai-jobs-paper 会话,新增政策线:
发散(含反方 N-0008)→ 升格 N-0007 并**拆解**为两个子论点 → recall 优先
(交叉绑定复用 4 篇归档,3 次允许抓取只用 1 次,新增 DOC-0009)→ 故意关死
N-0009(stuck/evidence 带完整理由)→ 根 synthesis 走修订链(SYN-0010
revises SYN-0005)→ 大纲新增 S-06 并 **excluded N-0009 带理由** → 重
assemble(References 9 篇)→ 终态 check 0/0。上轮全部未测路径覆盖完毕。
`nd schema` 判定:"完全消灭 payload 猜测,零看源码"——F2 修复生效。

## 摩擦日志 → 处置

| # | 摩擦 | 处置 |
|---|---|---|
| G1 | 收敛会话的 brief 前沿为空,冷接管者看得见结论、看不见结构(树/文章的存在都不可见),被迫 4-5 条定位命令 + 违规直读 records.jsonl | **代码**:brief 增加 TREE MAP(id·kind·status·parent·✓syn)与 ARTIFACTS(大纲/注册节/final 指针)两节,排在 STUCK 之后、告警之前 |
| G2 | ingest 的示例路径写 session 相对形态,实际只收绝对路径,白付 2 次失败 | **代码**:text_file 接受绝对或 session 相对;示例改真话 |
| G3 | pending→stuck 非法,被迫绕道 investigating;合法迁移表不可发现 | **代码**:pending→stuck 入 LEGAL;非法迁移报错列出当前状态的全部合法去向 |
| G4 | recall 在全 global 距离下区分度弱(8 篇全返) | **接受为已知限制**(V2 设计明确词法+树距离;语义排序属 V4+),记录于此 |
| G5 | article 层只有写命令,更新大纲被迫直读 records.jsonl | **代码**:新增 `nd article show`(读侧:最新大纲+已注册节+final 指针) |
| G6 | outline 重注册原地生效但无提示 | **代码**:revised: true + 告警说明 append-only latest-wins |

## 结论

两轮实测均收敛(0 hard/0 soft),第二轮在禁读源码的约束下完成——CLI 自描述
成立。剩余已知限制:recall 排序弱(G4)、深树>3 层未压测、多 session 并发
不支持(设计如此)。
