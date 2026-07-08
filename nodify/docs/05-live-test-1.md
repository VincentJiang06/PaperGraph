# 实测审计 #1 — Opus 学术写作全流程(2026-07-09)

跑法:Opus agent 只凭 in-repo skill 独立驱动 nd,完成 ai-jobs 学术调查与
成文(session `dogfood/sessions/ai-jobs-paper`)。结果:**收敛**——树 5 节点
全 concluded、5 份 synthesis、8 篇归档(全部逐字 quote 零降级)、5 节文章
assemble 成功、终态 `nd check` 0 hard / 0 soft。4 个并行 Sonnet 搜索工人,
主上下文保持干净。判定:"胜任的 agent 无需人扶就能跑通;摩擦全部来自
payload/路径的猜测,不来自循环本身。"

## 摩擦日志 → 处置

| # | 摩擦 | 处置 |
|---|---|---|
| F1 | notes/ 实际位置(sessions/<id>/notes)不可发现;init/brief 不回报 session_dir | **代码**:init 返回 session_dir/notes_dir,brief 返回 session_dir;技能写明路径 |
| F2 | --file 类命令的 JSON 形状只能读源码逆向 | **代码**:新命令 `nd schema <name>`——打印 schema 全文 + 最小示例 payload(conclude/ingest/outline/expand 有别名) |
| F3 | 问题型论点的 lean 语义没定义("答案是否"只能猜 refutes) | **文档/技能**:约定——命题型 = 对陈述本身;问题型 = 答案相对父观点的方向;无方向信息型用 open/mixed 并在 summary 讲清 |
| F4 | assemble 自动加节标题,草稿自带标题 → 静默重复 | **代码**:register 时草稿以 markdown 标题开头 → 告警;技能写明"草稿不带标题" |
| F5 | quote 校验折叠空白但不折叠 Unicode 标点(' vs ') | **代码**:_norm 增加弯引号/长破折/省略号折叠(放宽只会让旧 quote 继续通过,安全) |
| F6 | word_count 按空白分词,中文恒为个位数 | **代码**:CJK 单字计词(与 recall 分词同源) |
| F7 | "cites nothing" 在 register 与 check 口径不一 | **代码**:register 改为角色感知(仅 argument/evidence 或未知节告警),与 check 对齐 |

## 纪律自审要点 → 技能澄清

- recall-first 在索引为空时可跳过(写明);
- 中文长度预算以**字**计(每节 400-800 字);
- 深树(子论点拆解)与 excluded 纪律本轮未覆盖 → 留给实测 #2 的定向场景。
