# TESTING — 测试计划

> 上位约束：[PRINCIPLES.md](PRINCIPLES.md)（P-7 双层质量、P-8 对抗性程序、P-9 fail-closed、
> P-15 A/B 前置、P-18 诚实报告）。外部证据见 SURVEY.md §benchmarks / §claim-verification /
> 第二轮补查各节。**数字核验声明（P-18）**：仅 9 条载荷数字经过独立核验 pass
> （SURVEY §12.11）；本文其余外部数字来自 SURVEY 各节的调研级引用，未独立重核
> （not measured beyond survey），按载荷核验 3/9 失真的基率，引用时保留口径怀疑。

## 1. 三层评测金字塔

### L1 确定性门（in-loop，每轮可复跑，秒级）

全部 re-runnable、零 LLM 或固定 LLM+temperature 0：

- 引用 URL 可达性（HTTP + Wayback 兜底；urlhealth 式确定性验证 + 自纠环可把失效
  引用压到 <1%）；
- 逐字引语命中冻结快照（sha256 校验 + 精确子串，见 EVIDENCE-ENGINE §3b）；
- 书目存在性/撤稿/劫持期刊 join（本地 Retraction Watch CSV，O(1)）；
- claim 状态标签完整性（每条 claim 必有状态 + 证据指针——100% 可机检）；
- 报告内数字与台账/来源数字一致性 diff；
- data 类重跑门（manifest 重执行 + 容差比对）；
- inference 类前提 DAG 完整性。

### L2 二元 rubric judge（held-out 为主）

- 每任务 20-40 条**内容承载型二元 rubric**（行业已从 1-10 打分整体迁移到二元逐条判定，
  因前者被证实有偏且不可解释）；
- judge 协议硬规范：judge 与被评系统**跨厂商**（self-preference 10-25%）；pairwise
  双向换位取平均（position bias 可达 75% 偏首位）；judge 版本 pin 且入评测元数据，
  换代用锚点任务集桥接校准；报告 **Cohen's kappa 而非 raw agreement**（raw 虚高
  33-41pp）；长度/格式从质量维度显式剥离（防表面覆盖偏差）；双 judge 并行，
  分歧样本进人工复核队列；
- 裁判分层按任务类型切（成本维度证据）：可验证二元判定用小模型 + 短裁决
  （14B vs 4B 差距仅 1.74pp，输出成本可降约 800x）；开放式质量评审用强模型或
  PoLL 异构小模型陪审团（便宜 7-8x 且与人类相关性更高）；**高难争议 claim 不信任
  任何 LLM 裁判单独兜底**（JudgeBench：难题上 GPT-4o 裁判≈随机）——回退到
  检索证据 + 确定性检查。

### L3 专家/强对抗盲评（held-out only，里程碑式低频）

- SciArena 式 pairwise 盲评（最强 LLM judge 预测专家偏好仅 65.1% 准确——
  终审必须是人或以对抗性程序替代 rubric 评分，P-8）；
- 对抗性程序面板（继承前代 D2/D3/D4：steelman 打分、adversary 升级反驳、
  独立审计员反向抽取断言查覆盖）；
- **人力预算显式建模**（R1 攻击 MC-6）：专家来源 = 用户本人（本系统用户即
  研究者）+ 里程碑节点各一次；L2 分歧人工复核队列设容量上限（超限积压
  显式报告）；**专家缺席时 fail-closed**：L3 未执行的候选最高停在 candidate，
  不得 SHIP（不许静默退化为纯 LLM 面板）。

## 2. held-out 任务集设计

- **物理隔离**：dev 集（20-30 任务，in-loop 可见）与 held-out 集分离；held-out 的
  任务、rubric、评测脚本存独立目录（理想为独立 git 仓/独立机器），从不进任何 agent
  上下文；进过 loop 的任务视为已烧毁。依据：20 种技术性抗污染手段被证明全部无效，
  唯一可靠的是数据层隔离与轮换。
- **隔离的两个已知残余（诚实声明，R1 攻击 MC，非可完全消除）**：(1) held-out
  rubric 的**源综述是公开可检索的**——被评系统可能通过检索同一综述部分重构 rubric；
  缓解 = rubric 不逐字复制综述、掺入非公开的人工改写项、季度轮换；(2) **出题 LLM
  与被评系统可能同源**——缓解 = 出题模型与被评模型跨厂商，answer key 由人工终审。
  这两项写进每次评测的 coverage_gaps，不假装隔离是完美的。
- **构造方法**：BrowseComp 逆向出题法（从已验证的有出处结论倒推任务，天然"易验证"）
  + 新 survey 挖掘法（从近 6 个月发表的领域综述半自动产 rubric，保持新鲜防污染）。
- **规模下限（跨领域论文级）**：8-10 个领域 × 5-8 任务 ≈ **50-80 个 held-out 任务**
  （同行评审基准公认规模带 50-130）；rubric 每任务 20-43 条；任务按三轴复杂度
  （conceptual breadth / logical nesting / exploration）分层抽样。
- **领域选择**（覆盖三类证据通道 + 前代四题材避开直接复用防污染）：经济学、
  流行病学、能源政策、科技史、ML 方法、材料/实验科学（图表证据重）、心理学
  （复现危机文献丰富，测 contested 处理）、气候（IPCC 分级实践对照）、
  中文题材 ×1-2（bocha 通道 + GB/T 7714）。
- **轮换**：每季度轮换约 1/3 任务。
- **外部基准补充**：AstaBench（科研 agent 可信度 11 基准套件）做整体能力对照、
  TaxoBench 做文献组织质量对照——作为补充信号，不作为优化目标。

## 3. 头条指标与内部指标

- **对外单一头条硬指标：引用事实支持率**（claim-level factual support rate）。
  依据：这是全行业量化确认的最弱轴（最佳系统引用类 rubric 满足率 <11%；前沿 DR
  报告陈述级事实支持率仅 39-77% [E: SURVEY §12.11 条目1]；专家投票理由中引用
  质量权重最高 23.4%）——本系统核心价值恰好落在此。
- **头条指标的测量协议（堵灌水、同义反复与散文选择性，RT-6 + A7 fix-audit）**：
  分母**不是**系统自己的台账，也**不是作者裁剪的散文报告**（作者可只叙述已 verified
  的 claim、把 unverified/contested 排除出散文来洗白）——而是独立审计员（D4 风格、
  盲于台账、盲于散文）**同时从两侧**抽取取并集：(a) 完整 claim 台账的承重集
  （机器判定，EVIDENCE §3b），(b) 最终报告散文；散文承诺但台账缺 verified 支撑的
  断言、以及台账承重但散文回避不提的断言，**都计入分母**。按承重×实质分层，
  头条取承重×实质层；held-out 侧独立测量（L1 过滤器是被测对象的一部分，不能引用
  其通过率自证）。
- 出厂质量基线参照：Kosmos 独立抽样审计语句准确率 79.4%——我们的 verified 态
  claim 抽样审计准确率必须显著高于此值才有资格声称差异化。
- 内部多维：verified 覆盖率（承重 claim 中 verified-* 占比）、reproduce-rate、
  证据空间覆盖（L1 发散环 vs 独立 answer key）、contested 处理正确率、
  每 claim 成本、每轮新增 verified claim 数（饱和曲线）。
- **超并行特有回归指标**：工具调用规模 vs 引用事实支持率曲线——外部实证显示
  工具调用从 2→150 时事实核查准确率平均掉 ~42%（两前沿模型均值，消融口径），
  验证 gate 挂在每个子环出口的设计（ORCHESTRATION §2 L3）必须使本系统此曲线平坦。
  这是"更多检索≠更可信"的机器可判防线。

## 4. Goodhart 四道防线

1. L1 gate 指标与 L2 judge rubric 维度**严格不重叠**（L1 已测的链接/支持度绝不在
   L2 重复计分）；
2. held-out rubric 对生成系统永久保密；
3. 监控"gate 分上升但 held-out 停滞/下降"作为 Goodhart 警报（前代双层分离的
   原设计意图，已被行业实践独立验证）；
4. judge 版本 pin + 桥接校准（见 §1 L2）；
5. **语义漂白检测**（R1 攻击 RT-7：系统均衡策略是把 claim 弱化到 NLI 全过）：
   L2 rubric 全部为内容承载型二元项（弱化后的空泛 claim 无法满足具体 rubric）；
   held-out D4 审计增设"报告结论强度 vs 台账 claim 强度一致性"检查——结论比
   台账强 = kill（前代 D3 已验证此模式），台账整体弱到不支撑任何实质结论 =
   信息量不达标 REVISE。informativeness 永不给 L1 计分（防反向 Goodhart）。

## 5. A/B honest test（里程碑 1，前置）

- **两条正交 A/B 臂（A7 fix-audit：原设计只有第一条，漏了并行度证伪）**：
  - **臂 A｜门体系**：gated（完整系统）vs freehand（同模型裸跑），隔离"门是否
    提升可信度"（继承 P-15）；
  - **臂 B｜并行度**：超并行（完整多 loop）vs **同 token 预算的串行 baseline**
    （单 loop、无内环扇出），隔离"超并行是否比同成本串行产出更可信的研究"——
    这是系统名字里"超并行"的证伪测试，未跑前该前提是假设（README 未偿债 #2）。
  两臂产出**同构渲染**（前代 v3/v4 的 dossier 渲染 confound 教训），都过 held-out
  三层评测；
- 判据：gated 臂在引用事实支持率、verified 覆盖率、对抗面板上不赢 freehand
  → 如实报告，"do not add more framework to hide it"；
- 实验纪律继承前代消融方法论：盲评 + 格式归一化（校验 blinding 工具自身）、
  Latin-square 轮换、预注册假设 + kill-criterion、n 与噪声区间声明（前代 ±0.1-0.4
  在噪声内的教训——A/B 至少 5 topic 起步）。

## 6. 校准纪律

- **所有 gate 阈值不得直接引用文献或厂商数字**，必须用自建 held-out 金标准集现场
  校准（依据：Elicit 官方 94-99% vs 独立评测 81.4% 的落差；scite F1 0.0-0.58 来自
  撤稿引文极端样本——文献数字的口径陷阱本项目已亲历 3 次）；校准集评估本身是
  开发 loop 的客观 gate。
- 学科先验：不同学科证据类型设不同信任基线（DARPA SCORE：经济学 58% vs
  心理学 42% 预期复现率），写进来源等级表而非 agent 临场判断。
- LLM 裁判上岗前过内置人工校准集，校准结果写入配置。

## 6b. 人力预算（最后防线不能零排期，R1 攻击 MC）

L3 专家盲评、L2 分歧样本人工复核、校准集建设都依赖人工——若零排期会静默退化为
LLM 面板，抹掉 P-8 的对抗性价值。显式建模：

- **人力是 held-out 轨的一等预算项**，与 token/API 预算并列声明；
- L3 专家盲评设为**里程碑触发**（A/B 里程碑、季度轮换、重大架构变更），不是每 run；
- 无专家可用时，L3 **降级为跨厂商强模型对抗面板并显式标 `expert: not-available`**
  （coverage_gaps 记录），绝不假装人工完成——诚实降级而非静默替换；
- 校准集与 held-out answer key 的构建是一次性人工投入，摊到多 run；
- 高难/争议 claim（TESTING §1 L3 循环缺口）在无专家时**只能停在 contested/
  logically-derived，不得升 verified**——不靠循环回退伪造真值信号。

## 7. 安全红队测试（attacker 轮的机器可判部分）

**验收标准（双向，非循环——R1 攻击 MC：只证门被执行不够）**：既要证明门条件被
强制执行，也要证明**满足门条件的投毒仍然失败**——攻击注入的虚假 claim 即使凑齐
URL 与引语也不能被置 verified（靠 ≥2 独立发布者源 + venue 层级 + 源完整性 L0/L1
拦截），且**不能压制反证环**（投毒不能使 L4 漏报真实反驳）。

六类注入攻击剧本（依据第二轮 security 调研的实证文献）：

1. PoisonedRAG 式证据库投毒（少量毒文高命中）；
2. Fact2Fiction 式针对分解模板的定向证据；
3. 非渲染通道注入（HTTP 头/JSON-LD/HTML 注释/白字——野外测量中 70% 注入藏于此）；
4. UGC 埋毒后诱导检索（UGC 是 deep-research 投毒主通道）；
5. PDF 隐藏 prompt（arXiv 实案 18 篇）；
6. **反证压制**：投毒/注入试图让 L4 反证环漏掉已知反证、或把 contested 证据挡在
   admission 外；
7. **绕过 gateway 直连出网**（bash+curl）取未落事件的"证据"→ 反伪造门必须 FAIL。

**残余风险清单 R1-R9**（P-19 承诺落地，每条配缓解）：R1 中毒证据通过逐字校验
（provenance≠truth）→ ≥2 独立源 + 源完整性；R2 注入污染工具参数/单条证据 →
采集面冻结限制爆炸半径；R3 权威域名洗稿 → venue 层级 + 一手/转引分级；
R4 学术 PDF 隐藏 prompt → 双视图剥离 + 只作数据；R5 防御性/版权注入 DoS →
失败路径确定性；R6 模型层防御残余 ASR 0.5-8% → 只作纵深，状态置位走确定性代码；
R7 二级注入经共享库持久化 → incoming schema 校验 + 下游 datamark；R8 LLM 生成的
分析代码被注入 → 沙箱执行 + 输出仅作数据 + 关键数值双实现；R9 可认证鲁棒防御的
效用代价 → 按任务风险分层启用。

验收不止于"三条件被强制执行"：

## 8. 负向测试与门自检

- EVIDENCE-ENGINE §6 的 **27 条**负向 fixture 全部实装；每条 pass 规则必须有对应
  负向测试，负向测试必须**经工具触发并断言被拒**（"存在即覆盖"禁止，P-9）；
- 每个门自带黄金自测 run（runs/_smoke 模式）+ 对真实外部工件的校准
  （真文献综述对 answer key 应近满覆盖——前代 Wikipedia 校准法）；
- fail-closed 路径本身要有负例（缺面板不得 SHIP 的负向 case——前代 selftest 空白
  不许复制）；
- **eval-of-eval 负向测试**（R1 攻击 MC：评测轨自身要有负例）：向 held-out
  聚合器植入一个"自信但错"的候选（承重结论有 honesty flag / 强于台账 / 引撤稿源），
  断言它**必然被 REVISE**；植入一个缺 D2/D3/D5 面板的候选，断言**不得 SHIP**
  （fail-closed 负例）；聚合器采 validate_eval_bundle.py 的全集校验模式。

## 9. 回归外壳（M8 bench）

- headless 批跑：`dsh --profile academic-research "<task>"`，exit code 判定
  （P-16 TUI 一等）；
- scoreboard.tsv append-only（行永不删除，更差结果也是数据）；
- 每次评测元数据：judge 版本、gate 版本、任务集版本、成本读数（从 session jsonl
  重算交叉核验，从不信自报数字——house 纪律）；
- 报告规范：每个 success 指标配对 integrity/damage 指标，未测显式标 not measured
  （P-18）。

## 10. 自举纪律（本规划自身的示范）

本项目规划文档的载荷数字已跑过一次核验 pass：9 条中 6 verified / 3 corrected，
失真模式统一为"数字真实存在但口径/对象被换掉"。由此固化为产品规则：

- 报告中任何数字必须携带**口径三元组**（测什么指标 / 什么样本 / 与谁对比），
  verify pass 核对三元组而非字符串出现；
- SOTA/"最佳"类 claim 强制携带时点戳，随时间自动降级为 dated；
- 同一上游来源的多次转录只计一个独立来源（证据谱系去伪独立印证）。
