# Nodify — 设计 V1(revision 2, 2026-07-09)

> **一句话**:把大模型深度搜索的产出从超长 markdown 上下文里解放出来——
> 逻辑与论据被持续抽取进一棵持久化的 node 树,原始文字阅后即焚。
>
> 权威顺序:`nodify/src/nodify/schemas/*.schema.json`(V1 冻结,单一来源,包运行时直接加载)> 测试 > 本文(导读)。
> 防坑基线:沿用 PaperGraph `v3/docs/01-anti-failure.md`,本文 §9 标注 V1 强制等级。

## 1. 问题与主张

深度搜索/深度调研类 agent 的通病:研究状态活在会话上下文里,以超长 md 笔记
的形态无限膨胀——token 成本线性涨、compaction 一来推理链就断、事后无法审计
"为什么得出这个结论"。

Nodify 的主张:**上下文只放思考的前沿,真相放在树上。**

- 每一轮搜索/子调查结束,模型必须把**逻辑**(观点、论点、结论)和**论据**
  (来源引用)蒸馏成树上的结构化记录,然后**丢弃原始文本**;
- 任何时刻,`nd brief` 都能把树渲染成一份 token 有界的简报,模型据此完整
  恢复调查现场——**compaction 免疫**是硬指标,不是附带好处;
- **checkpoint 至上**:观点一旦成形立即落树(单节点 add,不攒批),上下文
  随时可弃;判断"该不该落树"的默认答案是"落"——树里多一个 retired 节点
  无害,上下文里丢一个想法不可恢复;
- 树是可审计的:任何结论都能沿 synthesis → based_on → evidence 走回来源。

## 2. 与 PaperGraph 的关系

Nodify 是从 PaperGraph v3 讨论中泛化出来的**通用框架**:框架只提供思考的
"场"(树 + 记录纪律 + 巡检),思考本身(怎么发散、派不派 subagent、信谁)
全部归模型。PaperGraph 将来 = Nodify + paper 技能(compiler 渲染)。
v3/ 目录的设计文稿被本项目取代,防坑清单继续有效。

**V1/V2 切分**(你的决定):V1 只做 node 树;docs 记忆化库(归档、去重、
quote 逐字校验、树距离 recall、来源压缩)整体进 V2。V1 的论据以**内联引用**
形态挂在结论记录上(见 §4 synthesis.evidence),可回溯性先做到"引用结构
完整",做不到"逐字防伪"——这条边界必须诚实(P2:文档不声称代码没做的事)。

## 3. 树:两种节点 + 一种结论记录

**viewpoint(观点)** —— 探索层,宽松陈述(命题或问题)。工作方式是发散:
提出"有助于判断本观点、但不预设其真假"的新方向(独立性判据),每次发散
强制 ≥1 个 adversarial 方向。状态:`open → expanding → synthesized → closed`,
任意时刻 `retired`。

**claim(论点)** —— 观点发散穷尽(说不出"若被解答会改变判断"的反事实探针)
时**原节点升格**:一个最小的、可直接投入调查的明确问题。升格附 promotion_note
(自由文本,技能规定其必答项:尝试过的方向/为何不成立/反事实探针/预期证据
形态——V1 不做表单 schema,纪律归技能层)。状态:
`pending → investigating → concluded | stuck`,任意时刻 `retired`;
`stuck_reason ∈ {evidence, protocol}`。拆解(拆成子论点)仅在论点层合法。

**synthesis(结论记录)** —— 回流载体,挂在**任意**节点上,统一承担两件事:
- 挂在 claim 上 = 调查的答案(lean/summary/evidence);
- 挂在 viewpoint 上 = 子树收束的判断(based_on.children 指向子节点)。

可随认识更新追加新版(revises 链)。**下游(简报、导出、未来的 compiler)
只消费 synthesis,不消费过程文本**——这就是"提取逻辑、抛弃文字"的落点。

## 4. 记录与文件布局(V1 全部家当)

```
sessions/<id>/
  session.json            # session.v1:question/boundary_note/budgets/language
  tree/nodes.jsonl        # node.v1,append-only,latest-per-id
  tree/syntheses.jsonl    # synthesis.v1,append-only
  tree/events.jsonl       # event.v1,append-only(全命令 trace)
  notes/                  # 模型自由草稿区(不受 schema 管;阅后即焚的缓冲带)
```

另有 **事件日志**(trace,你点名的硬需求):每条 nd 命令(含只读命令)
追加一条 event.v1 到 `tree/events.jsonl`——谁、何时、什么命令、动了哪些 id、
一行人话摘要。这是事后调试 agent 行为与重建树演化史的唯一依据,V1 就位,
后补不可能。`nd log` 查看。

schema 共 **5 份**(V1 冻结集):

1. `envelope.v1` — CLI 输出封套 {ok, command, data, errors, warnings}
2. `session.v1` — {session_id, question, boundary_note?, language,
   budgets{max_depth, max_children, max_open_claims}, schema_set_hash, created_at}
3. `node.v1` — {node_id N-0001, parent_id?, kind, statement, why_helps_parent?,
   orientation ∈ {neutral, adversarial}?, status, status_note?, promotion_note?,
   stuck_reason?, revises?, created_at, created_by}
   (kind↔status 合法组合由 schema 的条件分支强制;status_note 记录
   retired/closed/stuck 的一行原因——M0 推演 C 场景发现"假设被证伪后退休"
   必须留痕,否则树史读不懂)
4. `synthesis.v1` — {synthesis_id SYN-0001, node_id, lean ∈ {supports, refutes,
   mixed, open}, summary, confidence ∈ {high, medium, low},
   based_on{children[N-ids], evidence[E-refs]}, open_questions[], revises?, created_at}
   其中 evidence 内联引用:{ref_id E-01, title, url?, locator?, quote?, tool?,
   note?}——locator 覆盖本地证据(如 `logs/app.log:1234-1260`,M0 场景 C);
   url 与 locator 至少其一非空由 check 软警告督促
5. `event.v1` — {event_id EV-000001, at, actor, command, mutating,
   touched[ids], summary}

全部 `additionalProperties:false`;运行时直接加载 schema 文件校验,**不写
第二份模型镜像**(P9);`nd init` 记录 schema 集 hash,session 内协议冻结(P5)。

## 5. nd CLI(封闭清单,10 组,P4)

```
nd init <id> --question "…" [--boundary "…"] [--budget k=v …]
nd add --parent N --kind K --statement "…" [--why …] [--orientation …]
                                     # 单节点即时落树(checkpoint 至上的主通道)
nd add --file expand.json            # 批量挂子节点(一次发散原子落盘)
nd promote <N> --note "…"            # viewpoint 原地升格 claim
nd set-status <N> <status> [--note "…"] [--reason evidence|protocol]
nd conclude --file synthesis.json    # 写结论记录
nd brief [--max-chars 8000]          # 树 → token 有界简报(核心命令,见 §6)
nd show <N> | nd tree                # 检视(单节点血统 / 全树骨架)
nd log [--tail N]                    # 事件 trace 查看
nd check                             # 巡检:结构硬错误 + 纪律软警告(见 §7)
nd export [--format json|md]         # 全量导出给下游渲染器
```

共 10 个命令组(add 双模式算一个)。每条命令一个 envelope,且**每条命令
(含只读)追加一条 event**。清单由契约测试双向镜像;扩表 = 先改本文再改测试。
并发故事一句话:**树的一切写入由主会话经 nd 串行执行**;模型派出的任何
subagent 只写 `notes/` 草稿,汇报由主会话蒸馏后落树(P12 的 V1 简化形态)。
框架立场:**鼓励大量 subagent**——上下文隔离的调查工人天然符合"阅后即焚",
技能层提供派发模板;树的串行写入纪律使 subagent 数量与安全性解耦。

## 6. `nd brief` — 本项目的灵魂命令

目标:**模型仅凭一份 brief 就能恢复整场调查**(compaction 免疫的可测表述)。

确定性渲染,优先级装箱,超预算从低优先级截断并如实标注 `[truncated: …]`:

1. session 的 question/boundary + 预算余量;
2. 根链结论:每个 synthesized 观点的最新 synthesis(lean + summary 单行);
3. **前沿**:所有 open/expanding 观点、pending/investigating 论点(带
   statement + 一行血统路径);
4. stuck 论点及原因;
5. 纪律警告摘要(来自 check)。

树本身被预算约束(max_depth × max_children × max_open_claims),所以 brief
天然有界——这是"树取代长上下文"成立的数学前提。

## 7. `nd check` — 硬错误与软警告分离

- **硬(exit 1)**:记录 schema 非法;悬空引用(parent_id / based_on /
  revises 指向不存在的 id);kind↔status 非法组合;预算超限。
- **软(警告,exit 0)**:发散无 adversarial 方向的 viewpoint;based_on 全空
  的 synthesis;evidence 无 url 也无 locator 的引用;长期 open 且无子节点的
  观点;concluded 但无 synthesis 的 claim。
  软警告是"让偷懒可见"的机制(泛化框架的过程保证是软的,这是有意的取舍)。

## 8. 技能层(V1 交付的另一半)

`nodify` skill(prompt,不是代码),三段式纪律(P11:边界严格、内部自由):

1. **蒸馏义务(checkpoint 至上)**:观点成形的当下就 `nd add`,不等轮次
   结束;每轮搜索/子调查结束必须 conclude 或记录缺口;原始文本进 `notes/`
   或直接丢弃;禁止把搜索原文堆进对话继续滚。
1b. **subagent 优先**:凡可并行、可隔离的调查一律派 subagent(搜索、精读、
   数据分析各配建议模板);主会话保持"树主人"角色——收报告、蒸馏、落树,
   自己不淹在原文里。
2. **思维纪律**:发散 vs 拆解的独立性判据(附正反例)、强制反方、反事实
   探针升格、claim 三轮不充分即 stuck 并回流缺口。
3. **恢复协议**:每次 compaction 后/新会话开头,第一动作是 `nd brief`。
   subagent 模式(搜索/分析工人的建议模板)以附录形态提供,模型可改可弃。

## 9. 防坑清单的 V1 强制等级

| P(见 v3/docs/01-anti-failure.md) | V1 等级 |
|---|---|
| P2 文档不声称代码没做的事 | hard(评审项;quote 防伪明示为 V2) |
| P4 反过度机器 | hard(10 组 CLI + 5 schema + 无队列/锁/状态机引擎) |
| P5 协议冻结 | hard(schema_set_hash + validate) |
| P9 单一来源 | hard(schema 运行时加载,无镜像) |
| P10 文档禁行号锚点 | hard(评审项) |
| P13 运维纪律(字面量命令/python 扫描) | hard(loop 硬约束) |
| P14 磁盘状态 | hard(brief 恢复测试:删上下文仅凭 brief 续跑) |
| P1/P3 契约与接线 | 缩面后 hard(5 schema 各有产/销/贯穿测试) |
| P6 自评 / P11 自主性 / P12 并行 | discipline(技能层)+ check 软警告 |
| P7 防幻觉三件套 / P8 缓存零决策 | hard(V2 已落地:quote 逐字/hash 去重/cite 回溯;recall 纯读) |
| P15 spec 瘦身 | hard(session.v1 五字段,无消费路径的字段不准进) |

## 10. 里程碑

- **M0 冻结**:三场景推演(论文调研 / 技术选型 / bug 根因)对着 5 schema 走
  一遍纸面流程 → 冻结 schema + CLI 清单。
- **M1 核心**:nd 实现 + 测试(schema 贯穿、树纪律、brief 装箱与截断、check)。
- **M2 技能**:nodify skill 撰写 + brief 恢复测试(硬指标:仅凭 brief 续跑)。
- **M3 狗粮**:一个真实调研题从 init 跑到 export,halt-and-fix。
- **V2(另立设计)**:docs 记忆化库——归档/去重/quote 逐字/树距离 recall/
  来源压缩;PaperGraph 的 paper 技能与 compiler 接回。

## 11. V1 明确不做

docs 归档与 recall(V2)、quote 逐字校验(V2)、队列/租约/状态机、子代理
结果的 schema 化(模型自管)、WebUI、多 session 并发、语义检索。
