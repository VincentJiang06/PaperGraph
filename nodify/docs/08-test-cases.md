# Nodify 测试用例组 + Opus 操作守则(2026-07-09)

> 供长期接手工作的 Opus 使用。每个 TC:目的 / 跑法 / 机判 PASS 标准 /
> 采证要求。live 类 TC 由一个独立 agent 按 in-repo skill 跑,**审计者与
> 执行者分开**(maker ≠ checker)。

## Opus 操作守则(每次迭代都适用)

1. **顺序**:选路线图一项 → 先改设计文档 → 改代码 → 补/改单元与契约测试
   → 40+ 全绿 → 跑对应 live TC → 写审计记录(docs/0N-live-test-N.md,
   含摩擦→处置表)→ 提交。
2. **红线**:不许削弱测试来过 gate;闭表(CLI 命令、schema 集)扩表必须
   文档先行;schema 集改动 = 新版本号(v4…),永不改已发布集;技能只留
   仓库内,不装 ~/.claude/skills;搜索工人用 Sonnet;commit 尾行
   Co-Authored-By 按现有惯例;push 只到 GitHub origin。
3. **防坑清单**(v3/docs/01-anti-failure.md P1-P15)每次提交前过一遍;
   尤其 P2(文档不声称代码没做的事)与 P9(单一来源)。
4. **审计记录格式**:跑法一段 + 摩擦→处置表 + 未覆盖项;每条摩擦要么修
   (带回归测试)、要么明确"接受为已知限制"并写进对应设计文档。
5. shell 纪律(P13):命令全字面量;文本扫描用 python;envelope 解析用
   `python3 -c "import json,sys; …"`;BSD grep 无 `\|`/`\s`。

## 用例组

### TC-A 基线回归(每次大改后必跑;en 语言)

- 跑法:全新 session(language=en,en 问题,例如 "Why did NAND flash
  prices swing 2023-2025?"),Opus 按 skill 从零到 assemble,预算:
  树 ≤10 节点、≤6 次抓取、文章 3 节。
- PASS:终态 `nd check` 0 hard;文章 assemble 成功且每个 cite 可回溯;
  全程零"绕过 nd 直读/直写 session 文件"(notes/ 与 recall 给出的
  text_file 除外);摩擦日志新增条目 ≤2。
- 采证:final.md、`nd log` 全量、摩擦日志。

### TC-B 规模压测(R4 前置采证)

- 跑法:脚本(非 agent)用 nd 构造 60 节点、深度 4、20 篇归档、15 份
  synthesis 的会话(预算调大);然后:`nd brief --max-chars 4000/8000/16000`
  三档、`nd check`、`nd tree` 计时。
- PASS:三档 brief 全部 ≤ 上限且截断声明如实;check < 5s;无栈溢出/异常。
- 采证:三档 brief 全文、耗时表;TREE MAP 被挤掉时是否仍能冷接管
  (交给一个 agent 只看 4000 档 brief 提问验证)——此项结论直接决定 R4 方案。

### TC-C 竞争假设(bug 根因场景,M0 场景 C 的 live 版)

- 跑法:虚构一个可判定的排障任务(仓库内造一个带 bug 的小程序 + 日志),
  根下并列 3 个假设观点;要求 agent 用 local 证据(locator 指向日志行)
  证伪其二、证实其一;交叉绑定必须出现(同一日志 doc 对 H1 refutes、
  对 H2 supports)。
- PASS:被证伪假设 retired 带理由;胜出假设 synthesis 的 evidence 全部
  带 locator;check 0 hard;根 synthesis 点名三假设的裁决。
- 采证:树 + syntheses 导出。

### TC-D 修订与卫生(R5/R6 验收)

- 跑法:在 TC-A 会话上:reopen 一个 synthesized 观点(→expanding)加新
  方向;retire 一个还有 active 子树的观点;若 R6 已实现,revise 一个节点
  statement 并处理绑定迁移提示。
- PASS:R5 落地后 check soft 报"active 挂在 retired 祖先下";synthesis
  修订链(revises)正确;`nd show` 血统一致。

### TC-E 损坏恢复(错误路径 UX)

- 跑法:人为往 nodes.jsonl 追加一行非法 JSON / 一条 schema 非法记录;
  让 agent 从 `nd brief` 进场(会撞硬错)。观察它能否凭错误信息定位并
  上报(不许它自己改 canonical 文件)。
- PASS:所有命令的报错都指明文件+原因;agent 的处置是"停下上报"而非
  瞎修;修复(人工删行)后 check 回绿。
- 采证:agent 的错误处置记录 → 报错文案的摩擦项。

### TC-F recall 基准(R2 的量尺)

- 跑法:脚本构造种子库:12 篇条目(标题/摘要/全文/绑定位置刻意设计),
  15 条查询各带标准答案(应命中的 doc_id 集)。跑 `nd recall`,算 recall@3
  与 MRR。**先测基线,后改 R2,改后重跑。**
- PASS:R2 改动后 recall@3 严格不降,目标 ≥0.8;确定性(两跑同结果)。
- 采证:基准脚本入 tests/bench_recall.py(不进默认 pytest,手动跑)。

### TC-G 成本纪律(观察项)

- 跑法:TC-A 附带统计:工人聚合抓取次数、ingest 次数、conclude 次数 vs
  预算口径。
- PASS:聚合抓取 ≤ 预算 1.5 倍;超了记摩擦并回改技能措辞(不加机制,P4)。

### TC-H 文章生命周期(R1 验收)

- 跑法:assemble 后再改一节草稿并重注册但**不**重跑 assemble → `nd check`
  应 hard 报 final.md 陈旧;重 assemble 后回绿。再:大纲删除一节 →
  已注册孤儿节的 soft 告警仍在。
- PASS:如上,全部机判。

### TC-I 三代接力(compaction 免疫的强化版)

- 跑法:三个 agent 依次接手同一会话(每个只许从 `nd brief` 进场,前代
  上下文不可见):A 建树并卡在中途;B 恢复、完成调查;C 恢复、成文。
- PASS:B/C 都能在 ≤3 条定位命令内开始实质工作;终态 0 hard;
  文章引用全回溯。
- 采证:每代的 RECOVERY REPORT;任何"看不懂现场"的点都是 brief 的 bug。

### TC-J 对抗完整性(R9,敌意用例)

- 跑法:明确指示 agent 扮演攻击者,依次尝试:
  (a) conclude 里编造 quote(不在归档文本中);
  (b) cite 未归档的 DOC id 注册文章节;
  (c) evidence 全空但 lean=supports/confidence=high 的结论;
  (d) 绕过 nd 直接向 nodes.jsonl 追加一条自造节点后跑 check;
  (e) ingest 一个空文件/一个二进制文件。
- PASS:(a) 降级+告警且落盘 quote=null;(b) 硬拒;(c) 落盘但 check soft
  点名;(d) schema 或引用完整性抓出(若 agent 伪造得完全合法——记录为
  发现:单写者纪律靠 agent 自律,评估是否需要 R11 完整性签名);(e) 拒收。
- 采证:每项的 envelope 输出原文。

## 执行节奏建议

R1+TC-H → R2+TC-F → R3(顺手)→ TC-B 采证 → R4 决策 → R5/R6+TC-D →
TC-C / TC-I / TC-J 穿插在各里程碑后作为信心检查;TC-A 每次大改必跑。
