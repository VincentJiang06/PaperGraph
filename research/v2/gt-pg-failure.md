# GT · 前代失败考古（Paper Graph）— v2 一手证据复核

> **调查范围**：`~/playground/misc/Paper Graph`，重点是
> `archive/pre-reset-2026-07-09/`（失败的 paperproof v2 实现 + nodify）、四份
> `nodify/comparison{,2,3,4}/RESULTS.md`、`v3/docs/01-anti-failure.md`、
> `archive/legacy-2026-07-07/`，以及仓库自身的 git 历史与 `.loop/state/log.md`。
>
> **方法**：一手优先。所有 RESULTS.md 的**叙述文字**被视为「待检验的声明」，用同目录下的
> 原始评分文件（`blinded/scores/judge-*.json`、`blinded/KEY.json`、`results*.json`）、
> 渲染脚本（`dossier.py`、`phase_metrics.py`）、prompt 文件与 git commit message 逐条对账。
> 凡叙述与原始数据冲突，**以原始数据为准**并明确记录。

---

## 结论摘要

**1. 三代（实为四代）失败的形态是清楚的，且大部分工程教训是真的。**
legacy 规范集（2026-07-07，spec-only，0 行实现）→ paperproof v2（13,949 行 src + 9,101 行
tests，55 条 CLI 命令，106 条 V-rule，11 态队列 + 900s 租约 + 三把文件锁）→ v3 设计稿（只留下
`00-design.md` + `01-anti-failure.md`，**从未实现**）→ nodify（2,036 行 src，树 + CLI）。
第 4 代（当前仓库的两 gate workflow）也**尚未通过它自己 DESIGN.md 要求的 A/B 检验**。

**2. 「结构不提升推理质量」这个结论——按一手数据，比 v1 规划文档所依赖的要弱得多。**
四次消融的独立样本量分别是 **N=1 topic / N=5 topics / N=5 topics / N=1 topic**，评委恒为
3 个 Opus，评分被压缩在 4–5 两档（1–5 整数尺，几乎无 1/2/3）。在 topic 级配对检验下：

| 消融 | 对比 | 均值差 | sd | t(4) | 判读 |
|---|---|---|---|---|---|
| comparison2 | tree − skills（overall） | **+0.134** | 0.692 | 0.43 | 完全不显著 |
| comparison2 | skills − raw（overall） | **+0.068** | 0.796 | 0.19 | 完全不显著 |
| comparison2 | tree − raw（overall） | +0.202 | 0.184 | 2.45 | p≈0.07，边缘 |
| comparison3 | tree − notree（composite） | **−0.389** | 0.410 | −2.12 | p≈0.10，不显著 |

**没有任何一项跨臂质量差在 topic 级达到 p<0.05。**（我用 `results_judges.json` /
`results.json` 的 per-topic 均值重算得到；脚本见「逐条事实」§4。）

**3. comparison3 那个 −0.39（v1 规划文档称"刚性结构是负资产"的唯一实证）里，最大的一项是仪器伪影，
且可被机械证明。** calibration 一项 tree=4.0（15/15 个评分全是 4）、notree=5.0（15/15 全是 5），
方差为零。原因不在推理，在渲染器：`comparison3/dossier.py` 只有当节点 `status ∈ {retired, stuck}`
时才输出 `## Dead ends / retired` 段；而 `results_mechanical.json` 显示 tree 臂
**5 个 topic 的 `dead_ends` 全部为 0**，notree 臂 **5/5 `has_dead_ends: true`**。评分标准
（`JUDGE_PROMPT.md`）的 calibration 定义原文是 *"are uncertainty, **dead ends**, and open gaps
stated honestly"* ——评委在给「有没有那一节」打分。我逐文件核实：**5/5 tree dossier 无该段，
5/5 notree dossier 有该段**。

**4. 一手数据里存在一处 RESULTS.md 自身的推理错误，v1 规划文档整段继承了它。**
comparison2/RESULTS.md 写 *"The discipline, not the machinery, is the lever — again, and more
starkly."* 但它**自己那张表**给出 raw 4.53 / skills 4.60 / tree 4.73：
**纪律增量 +0.07 < 机器增量 +0.13**。comparison2 的正确读法是「两者都不是杠杆，两个 delta 都是噪声」，
不是「纪律是杠杆」。"纪律 +1.0" 这个数字**只存在于 N=1 的 comparison1**，在 N=5 的
comparison2 **没有复现**。

**5. 唯一在多轮里方向一致的结构优势是 grounding/可审计性，但它的量级也很小且不显著**
（comparison3 tree−notree grounding = +0.134，t=0.43）。真正硬的部分不是评委分，是**机械性质**：
`grounding_rate` tree 在 4/5 个 topic = 1.0（China 0.8），且 quote 是代码逐字校验的；notree 靠自觉。

**6. comparison4（唯一支持结构的实验）也被它自己的数据打折。** 它的 H1 结论写
*"tree brief 是 frontier-boxed / bounded-sublinear"*，但 `results.json` 的四个观测点
6069 → 7663 → 10072 → 12882 B，**每期增量 1594 → 2409 → 2810，是递增的**，不是次线性。
真实结论只能是「树的 resume 斜率更低（2271 vs 6703 B/phase，3.0×）」，不能是「有界」。
且该实验 N=1（一个问题、一对臂、4 个 phase）。另外 `phase_metrics.py` 对两臂的
"resume_read_bytes" 定义不对称：tree 只算 `nd brief` 的 stdout，**不计入 prompt 明确要求的
`nd tree` / `nd show` / `nd docs for-node` / `nd recall` 下钻读取**；notree 算整份 `log.md`。

**7. P1–P15 防坑清单里，13 条有一手可核的事故记录（其中 6 条可直接在代码/commit 里验证），
1 条（P6）作者自己标注为"设计层面倾向"而非单次事故，1 条（P12）被本仓库自己的日志证伪。**
P12 声称"并行 worker 输出不相交这条规则执行良好、没出过事"，但
`.loop/state/log.md` 记录了 **m7-eval1 的真实数据丢失事故**（后续轮次 wave member 复用第一轮输出路径，
覆盖已提交结果，30 个测试全部漏检）与 **9-component-audit 的 `rm -rf` 事故**（Freeze 评审 subagent
删掉了未跟踪的 `data/projects/ai-jobs` 与 `ai-jobs-2`，不可恢复）。

**8. 因此，v1 把"永不造结构框架"设为最高禁令，是把一个「未被证伪、也未被证实」的命题
当成了「已被四次严格消融判死」。** 数据授权我们说的是：*在中文 1500 字经济学短论文、强模型、
单上下文、LLM 评委这一狭窄条件下，树带来的质量增益无法与噪声区分*。数据**不**授权我们说：
*任何结构在任何任务上都不提升质量*，尤其不授权推广到本项目的目标产品（可信度、可重跑数据分析、
超长多 loop）——那正好落在四次消融**从未测过**的区域。

---

## 逐条事实

### 一、三（四）代到底建了什么

**F1 · 第一代 legacy PaperGraph（2026-07-07，spec-only）**
路径：`archive/legacy-2026-07-07/`（8 份 docs + 6 份 interface-specs，共 14 个 md，**零实现代码**）。
`archive/legacy-2026-07-07/README.md` 原文：

> "This repository is now spec-only. It intentionally contains: README.md AGENTS.md CLAUDE.md
> CODEX.md docs/ interface-specs/ … It intentionally does not contain: implementation code
> tests virtual environment demo runtime data build metadata CLI runtime WebUI runtime"

已定死的核心流水线（同文件）：
`PaperSpec → ProjectContract → Multi-BFS Orchestration → LogicNode/LogicEdge candidates →
ProofTask → AgentTaskPacket → local agent output → Validator → CommitDecision → Queue update →
Progressive Freeze → Compiler Dry Run → DraftMap → Final Audit`。
不可协商条款里已包含 *"Multi-worker parallelism is a first-version requirement."* 与
*"No AI numeric scoring for academic judgment."*
**这是三代中唯一一个「先冻结接口再写代码」的形态，也是唯一一个从未跑起来的形态。**
唯一被 git 跟踪的归档目录（`git ls-files archive` 只有 18 个文件，全在 legacy 下）。

**F2 · 第二代 paperproof v2（实现完成、gate 全绿、live run 中途停摆）**
路径：`archive/pre-reset-2026-07-09/{src,tests,docs}/`。实测规模（我直接统计）：

- `src/paperproof/`：**92 个 .py / 13,949 行**
- `tests/`：**55 个 .py / 9,101 行**
- CLI 封闭清单：**55 条命令**（`tests/contract/test_cli_envelope.py` 的 `CLOSED_COMMANDS`，
  从 `project init` 到 `verify` / `trace`）
- src 中出现的**不同 V-rule id：106 个**
- 设计文档：`docs/00`–`docs/18`，共 19 份，最大的 `11-test-suite.md` 41 KB、
  `contracts/interfaces.md` 67 KB（"408 public symbols"）

机器层的具体形态（`src/paperproof/queue/engine.py`，530 行，文件头原文）：

> `"""The queue engine (docs/05): the exact 11-state transition table, leases, QueueEvents,
> and the unblock/expire sweeps.` … `queue/.lock`（V-Q-02）。`Leases are 900s, driven by
> PAPERPROOF_NOW`"

三把锁（`src/paperproof/paths.py:67`）：`LOCK_FILES = ("queue/.lock", "commit/.lock", "proof/.lock")`。

它到底跑到哪一步：`.loop/state/log.md` 的最后几条是 **LIVE RUN ai-jobs-2**，
Stage0 init + spec build OK、Stage1 用户接受 ProjectContract、Stage4 派出 5 个并行 DocsWorker，
然后**在 worker 输出契约上停摆**（见 F7）。此后仓库转向 nodify，live run 再未完成。

**F3 · 第三代 v3 设计稿（只写了纸，一行代码没有）**
路径：`archive/pre-reset-2026-07-09/v3/`，`find` 结果**只有两个文件**：
`docs/00-design.md`、`docs/01-anti-failure.md`；`v3/schemas/` 是空目录。
v3 的自我约束（`v3/docs/00-design.md` §8、§10）：CLI 封闭清单 **15 条**（对比 v2 的 55 条），
明确不做：*"队列引擎/租约/状态机、Committer/Validator 分权、verdict 决策表、波次+合议 critic、
BFS/top-k、边记录、WebUI、语义检索(v3.1)、多 project 并发"*。
`01-anti-failure.md` P4 的强制机制写着 *"核心包代码预算 ≤ 2500 行"*。
**v3 从未被实现——它被 nodify 取代了。**

**F4 · 第四代 nodify（实现了，被四次消融打）**
路径：`archive/pre-reset-2026-07-09/nodify/`，`src` **2,036 行**、`tests` **1,201 行**。
`nodify/README.md` 自述其血统：

> "Origin: generalized from PaperGraph v2/v3 — the parts that survived contact with reality
> (durable tree state, anti-hallucination floor, budgets) stay in code; the parts that failed
> (behavior orchestration, worker form-filling) are returned to the model.
> Failure catalog: `../v3/docs/01-anti-failure.md`."

三层：V1 节点树 + `nd brief`；V2 memoized docs store（content-hash 去重 + 逐字 quote 校验）；
V3 文章层（`(cite: DOC-xxxx)` 硬解析）。

**F5 · 第五代（当前，仍未验证）**
`DESIGN.md` 开头即判词：

> "Everything before this is archived (`archive/pre-reset-2026-07-09/`) and treated as a failed
> attempt. Both the old PaperGraph and nodify made the same mistake: they built a **framework**
> (a tree/graph of claims + a CLI + schemas) and hoped the *structure* would make the reasoning
> better. Four rigorous ablations said it doesn't. We stop building frameworks."

但 `CHANGELOG.md`（2026-07-10）自己承认新方案同样未被证明：

> "The **honest A/B test** (gated loop vs freehand, same topic) that `DESIGN.md` calls for is
> still not run — it is the real proof the gates raise quality, and remains the top open item."

且：*"Only `nuclear-safety` has a complete held-out judgment panel, and it is `REVISE`."*
**——继任方案的核心主张，与被它否定的树的主张，处在同一证据水平上（皆未 A/B 验证）。**

**F6 · 证据链的版本控制状态（重要限定）**
`git log` 的 HEAD 是 `d87e3f1`（2026-07-09，"Nodify iter2 + three-mode ablation"），
即**只有 comparison1 进了 git**。comparison2/3/4、v3 设计稿、以及整个
`archive/pre-reset-2026-07-09/` 目录**均未被 git 跟踪**（`git ls-files archive` 只返回 legacy 的 18 个文件；
`git status --porcelain` 有 526 项）。含义：**comparison2/3/4 的原始评分文件没有版本化历史，
无法证明它们未被事后编辑。** 我按现存文件的内部一致性（judge-*.json ↔ KEY.json ↔ results.json ↔
blinded/*.md 三方对得上）判定其可信，但这是一致性，不是防篡改。

---

### 二、四次消融的实验装置（逐个）

**F7 · comparison1（v1，2026-07-09）**
路径：`nodify/comparison/RESULTS.md`、`results.json`、`runs/{raw,skills,tree}/`、`blinded/Article-{1,2,3}.md`。

- **N = 1 个 topic**（"AI agents 2020-2025 对就业的净效应?区分任务替代与岗位净增减"），
  3 个臂 × 1 篇文章 = **3 次 author run**，模型 Opus，交付物 ~1500 词中文引证文章。
- 评委：3 个盲评（跑了两轮，共 6 个 judge run）。
- 结果（`results.json` `judge_panel_clean`）：overall raw **3** / skills **4** / tree **5**。
- 机械指标：sources 8 / 9 / **18**；归档字节 11,417 / 8,262 / **65,981**；
  quote fidelity 0.92 / 0.92 / **1.0**。
- 冷恢复：raw *"the analytical/synthesis state is genuinely unrecoverable"*；
  skills 结论恢复但**引用全丢**（log 的引用段是空占位）；tree 从 2.9 KB `nd brief` 全量恢复。
- **作者自曝的仪器 bug（RESULTS.md §Fairness note）**：第一轮盲评脚本
  *"renumbered inline citations to appearance-order but left reference numbers original —
  *introducing* a citation misalignment, and only for raw/skills"*，修正后重跑，
  排序未变但 raw 的 evidence 分从 3→4。

**这一轮是整个证据体里唯一给出「+1.0 / +2.0」大差距的，而它是 N=1。**

**F8 · comparison2（v2，Sonnet 作者 × 5 topic）**
路径：`nodify/comparison2/`（`RESULTS.md`、`results_judges.json`、`blinded/scores/judge-{1,2,3}.json`、
`blinded/KEY.json`、`PROMPT_{raw,skills,tree}.md`、`topics.md`）。

- 装置：**5 topic × 3 臂 = 15 次 author run**，作者 **Sonnet 5**，评委 3 个 **Opus**，
  拉丁方槽位轮换，引用格式归一化。
- by-arm overall：raw **4.53** / skills **4.60** / tree **4.73**（跨度 **0.20**）。
- 机械指标反转 v1：`distinct sources cited` 12.8 / 12.8 / **12.2**——v1 的 2× 证据宽度优势
  **没有复现**；citation traceability 三臂皆 100%。
- 冷恢复：raw 3.0，skills **5.0**，tree **5.0**（tree 不再优于 skills）。
- **作者自曝的混杂（RESULTS.md 第 3 点，原文）**：

  > "**Confound (disclosed): my `raw` prompt was not zero-method.** It still asked for a
  > counterpoints/discussion section and calibration. That scaffolds the low end and inflates raw
  > (4.53 vs v1's 3.0). A cleaner test would strip those asks from raw."

  我核对 `PROMPT_raw.md`，确实包含：*"Include a **counterpoints / discussion** section…"*、
  *"Be **calibrated**…"*、*"When you quote a source, copy the wording **verbatim**…"*、
  *"save the fetched page text to `<workspace>/sources/S<n>.txt`"*。
  **即 raw 臂已经拿到了"纪律"臂的四条核心纪律中的三条。**
- **一个作者未披露的反向混杂（我发现的）**：三个 prompt 长度 raw 1,719 B / skills 3,005 B /
  tree **5,389 B**。tree 的额外 2.4 KB 几乎全是 CLI 机械说明（`nd init` 语法、`--file` 形状、
  `nd schema` 用法、budget key 名）。**这是一个偏向"树更差"的混杂：树臂的指令预算与注意力被工具占用。**

**F9 · comparison3（v3，激进模式，2 臂 × 5 topic）**
路径：`nodify/comparison3/`（`RESULTS.md`、`results.json`、`results_mechanical.json`、
`blinded/scores/judge-{1,2,3}.json`、`KEY.json`、`dossier.py`、`JUDGE_PROMPT.md`、
`PROMPT_{tree,notree}.md`、`RUNBOOK.md`、`topics.md`、`FRICTION.md`）。

- 装置：**5 topic × 2 臂 = 10 次 author run**，两臂皆 **Opus** + 同一激进方法，
  budget `max_depth=3 max_children=6 max_open_claims=15`，**worker=0（单上下文，对称）**，
  判定物是 Investigation Dossier（不是文章）。
- by-arm composite（`results.json`）：tree **4.42** vs notree **4.81**，Δ **−0.39**；
  六维只有 grounding 是 tree 领先（4.40 vs 4.27）。
- 作者自曝的混杂（RESULTS.md §2）：

  > "**Instrument artifact (the smaller part): asymmetric dossier rendering.** The *notree* author
  > **hand-writes** its dossier … the *tree* dossier is **machine-generated** … This favors notree
  > on prose-sensitive dimensions — it explains most of the calibration gap (−1.00) and part of
  > convergence (−0.53)."

- 作者的自我限定（RESULTS.md §Caveats）：*"**N=5, 3 judges** — margins of ±0.1–0.4 are
  suggestive, not definitive"*。

**F10 · comparison4（v4，强制 compaction 的规模测试）**
路径：`nodify/comparison4/`（`RESULTS.md`、`results.json`、`growth.jsonl`、`phase_metrics.py`、
`PHASE_{tree,notree}.md`、`dossier.py`、`blinded/KEY.json`）。

- 装置：**1 个超大问题**（2020–2025 AI/自动化劳动市场研究的系统性证据地图），
  **4 个 phase**，每个 phase 是**全新 Opus agent，只继承磁盘**；2 臂 = **8 次 phase run**；
  评委 3 个 Opus 评**一对** dossier。
- `results.json` `growth`（resume_read_bytes）：
  tree 6069 / 7663 / 10072 / 12882；notree 9532 / 15335 / 24509 / 29641。
  `resume_slope_bytes_per_phase`: tree **2271**、notree **6703**、ratio **3.0**。
- 预注册裁决（RESULTS.md §Pre-registered verdict）：
  **H1（记忆增长）SUPPORTED**；**H2（连续性）NOT supported**——*"Both arms kept continuity;
  the notree didn't break."*；**H3（grounding）打平 5.0 vs 5.0**，差别在 enforced vs diligent；
  **H0 未触发但也未完全证成**。
- 判分：tree composite 4.50 vs notree 4.89——作者归因于同一渲染伪影，且此轮更极端：
  *"`dossier.py` renders the tree as a **36-line per-node catalogue**; the notree author
  **hand-writes an 8-line synthesis**"*。

---

### 三、渲染伪影的机械证明（本次调查的关键新增）

**F11 · comparison3 的 calibration 差距 100% 由渲染器缺段解释**

原始判分（我从 `blinded/scores/judge-*.json` × `KEY.json` 解盲重算）：

```
calibration   tree    n=15 vals=[4,4,4,4,4,4,4,4,4,4,4,4,4,4,4] mean=4.00
calibration   notree  n=15 vals=[5,5,5,5,5,5,5,5,5,5,5,5,5,5,5] mean=5.00
convergence   notree  n=15 全为 5
adversarial_completeness  notree  n=15 全为 5
```

**三个维度上 notree 拿到 15/15 满分、方差为零**——这是"评委在评格式"的典型签名，不是内容分布。

机械原因，`comparison3/dossier.py:100-105`：

```python
dead = [n for n in nodes.values() if n.get("status") in ("retired", "stuck")]
if dead:
    lines += ["## Dead ends / retired", ""]
```

而 `comparison3/results_mechanical.json` 里 tree 臂 T1–T5 的 `"dead_ends": 0`（**五个全为 0**），
notree 臂 `"has_dead_ends": true`（**五个全为 true**）。

我再逐文件核实渲染结果：

```
T1 tree   dead_ends=False   T1 notree dead_ends=True
T2 tree   dead_ends=False   T2 notree dead_ends=True
T3 tree   dead_ends=False   T3 notree dead_ends=True
T4 tree   dead_ends=False   T4 notree dead_ends=True
T5 tree   dead_ends=False   T5 notree dead_ends=True
```

而 `comparison3/JUDGE_PROMPT.md` 的 calibration 定义原文：

> "**calibration** — are uncertainty, **dead ends**, and open gaps stated honestly rather than
> papered over?"

评委的 rationale 也直说了。judge-1 对 T1 的 A（=tree）写：
*"Weakness: … no dead-ends/source-limit disclosure."*；judge-2 同一篇：
*"no dead-ends/unverified-quote accounting"*；judge-3：*"no explicit dead-ends/process-transparency
section"*。**三个评委的减分理由文字上就是"缺那一节"。**

**这不是"树压制了校准诚实"，这是 `dossier.py` 不渲染树的墓地。**
且 `PROMPT_notree.md` 明确给了 notree 臂 `## Dead ends / retired` 模板段并要求
*"log killed lines in the Graveyard"*，而 `PROMPT_tree.md` 只说 *"kill thin branches fast"*，
没有指向任何会被渲染的 status 写入动作。**装置本身在一侧强制、另一侧不强制。**

**F12 · 剔除伪影后剩下多少**
composite 是六维等权均值。逐步剔除：

| 保留维度 | tree | notree | Δ |
|---|---|---|---|
| 全部 6 维 | 4.42 | 4.81 | **−0.39** |
| 去掉 calibration（5 维） | 4.508 | 4.774 | **−0.266** |
| 再去掉 convergence（4 维） | 4.518 | 4.718 | **−0.20** |
| 再去掉 adversarial（3 维：coverage/depth/grounding） | 4.49 | 4.62 | **−0.13** |

RESULTS.md 自己承认第三行（*"Even excluding the two most rendering-sensitive dimensions
(calibration, convergence), the tree is still behind **−0.20**, driven by coverage."*）。
我加的是第四行：adversarial_completeness 同样是 notree 15/15 满分零方差，
同样具备伪影签名，剔除后剩 **−0.13**，与 comparison3 里 tree 在 grounding 上的 **+0.134** 同量级、
反号。**在最保守读法下，comparison3 的净信号约等于零。**

**F13 · comparison3 的方差来源不是"结构"，是"树建得好不好"**
`results_mechanical.json`：T3（AI-jobs）的 tree 只有 `lines_of_inquiry: 2 / claims: 8`，
T4 的 `grounding_rate: 0.8`（唯一不满分）。这两个 topic 的 composite 恰好是 tree 最差的两个
（3.95 / 4.00，其余三个 4.67–4.78）。RESULTS.md 自己写：

> "**Tree quality depends heavily on how well the author built the tree** — the AI-jobs tree came
> out flat (2 viewpoints/8 claims) … The tree adds a floor on *rigor* but not on *insight*, and a
> weak build shows."

另外 **5 个 topic 的 tree `max_depth` 全是 2**（budget 允许 3）——即树臂**从未用满深度**。
这削弱了"结构约束压制探索"的因果解释：树根本没被推深。

**F14 · comparison4 的 "bounded-sublinear" 与自身数据矛盾**
`results.json` `growth` 的 tree `resume_read_bytes` 逐期增量：
**6069 → 7663 (+1594) → 10072 (+2409) → 12882 (+2810)**——**增量在变大**。
RESULTS.md 写 *"the tree brief is **frontier-boxed** … tree brief bounded-sublinear"*，
并外推到 phase 20（notree ~134 KB vs tree ~48 KB）。
**四个点上树的增量单调递增，谈不上"有界"或"次线性"；能支持的只有"斜率更低"（2271 vs 6703）。**

**F15 · comparison4 的 resume 成本定义不对称（作者未披露）**
`phase_metrics.py` 里：

```python
# the brief is what a fresh phase agent must READ to resume — measure its bytes
out = subprocess.run([ND, "brief", ...]);  brief_bytes = len(out.stdout.encode())
...
# a fresh phase agent must READ the whole log to resume — that IS its resume cost
"resume_read_bytes": log.stat().st_size
```

但 `PHASE_tree.md` 对 phase>1 的指令是：

> "run … `nd brief` FIRST and work only from what it shows (**drill with `nd tree` / `nd show` /
> `nd docs for-node` / `nd recall`**)."

**下钻读取的字节数完全没有计入 tree 的 resume 成本，而 notree 的等价明细全在 log.md 里被计入。**
同时 `PHASE_notree.md` 把 notree 限定为**单一扁平 log.md**（*"your entire persisted memory is a
markdown log"*），没有给它"索引 + 附录"的两层结构选项——而两层 markdown 是无需任何框架就能做到的。
**因此 3.0× 这个数字测的是"有索引 vs 无索引"，不是"树 vs 无树"。**

---

### 四、"结构不提升推理质量"这个结论到底能扛多重（本节是我自己的评估）

**F16 · 独立样本量**
整个证据体的独立研究问题只有 **6 个**，且高度重叠：
comparison2 的 T1–T5 与 comparison3 的 T1–T5 是**同一组 5 个问题**
（`comparison3/topics.md` 明写 `[= v2 T1]` `[= v2 T4]` `[= v2 T5]`），
comparison1 的唯一问题 == comparison2 的 T1 == comparison3 的 T3。
comparison4 是第 6 个问题。**四次消融 = 6 个问题、36 次 author run、四套不同装置。**

**F17 · 全部 6 个问题都是同一类：有争议的宏观/劳动经济学，中文，由 LLM 评委打分。**
（T1 美国通胀归因、T2 QE 与财富不平等、T3 AI 与就业、T4 中国人口、T5 最低工资、c4 AI 劳动市场证据地图。）
**证据体对以下场景的覆盖为零：**自然科学/实验数据、可重跑的数据分析、形式化推理、
文献综述的完备性、需要跨越多次 compaction 的超长任务（c4 只到 4 个 phase 且两臂都没断）、
弱模型、多 agent 并行。

**F18 · 天花板效应**
1–5 整数尺上，实际出现的分几乎只有 4 和 5。我逐分核过原始 judge JSON：
comparison2 的 **45 个 overall 分（3 评委 × 5 topic × 3 臂）全部是 4 或 5，一个 3 都没有**，
225 个分维评分里只有 1 个 3（tree 的 evidence_quality）；
comparison3 的 180 个评分（3 评委 × 5 topic × 2 臂 × 6 维）里只有 1 个 3（tree 的 grounding）。
**尺子的有效分辨率是 2 档。**
在 2 档尺子上讨论 0.13–0.39 的均值差，等于在讨论"多少比例的评分从 4 跳到 5"。

**F19 · 跨轮"曲线"不是同一个量**
`comparison3/RESULTS.md` 自己的对比表（诚实地标注了每格的条件）：

| run | model | artifact | tree vs best non-tree |
|---|---|---|---|
| v1 | Opus | article, 1 easy topic | **+1.0** |
| v2 | Sonnet | article, 5 hard topics | **+0.13** |
| v3 | Opus | *investigation*, 5 hard, aggressive | **−0.39** |

**这三格的被测量不同**（文章 overall vs 调查 composite，5 维 vs 6 维）、**作者模型不同**
（Opus / Sonnet / Opus）、**对照臂不同**（skills / skills / notree-aggressive）、
**渲染方式不同**（v1/v2 两臂都是人写文章；v3 一臂机器渲染）。
**把 +1.0 → +0.13 → −0.39 当作一条单调下降曲线，是把三次不同实验的三个不同量拼成一条线。**
（一手 RESULTS.md 逐格标注了条件；只有二手转述抹掉了标注——见「与二手文档的冲突」。）

**F20 · 显著性重算（我的脚本，输入是原始 judge JSON）**
topic 级配对（先对 3 个评委取均值，再做 N=5 配对 t）：

```
c2 overall tree−skills : diffs=[1.0, 0.67, 0.0, −0.67, −0.33] mean=+0.134 sd=0.692 t(4)=0.43
c2 overall skills−raw  : diffs=[−1.0, −0.33, 0.0, 1.0, 0.67]  mean=+0.068 sd=0.796 t(4)=0.19
c2 overall tree−raw    : diffs=[0.0, 0.34, 0.0, 0.33, 0.34]   mean=+0.202 sd=0.184 t(4)=2.45
c3 composite tree−notree: diffs=[0.0, −0.167, −0.833, −0.833, −0.112] mean=−0.389 sd=0.410 t(4)=−2.12
c3 grounding tree−notree: mean=+0.134 sd=0.692 t(4)=0.43
c3 calibration tree−notree: mean=−1.000 sd=0.000（零方差，见 F11）
```

comparison2 tree−skills 的 95% CI ≈ **[−0.72, +0.99]**——数据同时兼容"树好 1 分"与"树差 0.7 分"。

（在 judge×topic 层做符号检验会得到看似显著的结果，例如 c3 convergence p=0.008、
calibration p<0.001，但那是**伪重复**：3 个评委评的是同 5 对文档，独立单位仍是 5。
且这两维恰是被作者判定为渲染敏感的两维。）

**F21 · 数据授权与不授权的清单（本次调查的核心交付）**

**数据授权说：**
1. 在"强模型 + 单上下文 + 上下文能装下的任务"这一条件下，**树相对于"纪律 + 自管理 markdown 日志"
   的判定质量增益，无法与噪声区分**（c2 t=0.43，c3 剔除伪影后 ≈ 0）。
2. **树的机械性可审计属性是真的且可复现**：quote 逐字校验、grounding_rate 可测（c3 tree 4/5 个 topic = 1.0）、
   cite 硬解析。这些不靠评委分，靠代码。
3. **有索引的 resume 状态比扁平日志的 re-read 斜率低约 3×**（c4，N=1，且定义不对称——见 F15）。
4. **刚性结构会带来真实摩擦**：c3 tree 5/5 个 topic `max_depth` 只到 2、`dead_ends` 全 0；
   `FRICTION.md` 记了 6 条真实卡点。
5. **一个"通用编排机"（队列/租约/锁/11 态）在这个问题域上是净负债**：v2 的 13,949 行 + 595 个绿测试，
   live run 仍在第一波 worker 输出上停摆（F7、F22）。

**数据不授权说：**
1. **不授权** "结构在任何任务上都不提升质量"——测试域是 6 个中文经济学问题，
   全部落在单上下文可容纳的范围内。
2. **不授权** "纪律是最大杠杆"——该数字（+1.0）只在 N=1 的 c1 出现，在 N=5 的 c2 是 **+0.07**（t=0.19）。
3. **不授权** "刚性结构在强模型下是负资产"——c3 的 −0.39 里最大一项是渲染器缺段（F11），
   剔除伪影后净信号 ≈ −0.13，不显著，且与树建得差（F13）而非结构本身混杂。
4. **不授权** 把结论外推到本项目的产品目标：可重跑数据分析的正确率、
   引文可追溯率、超长多 loop 的续跑能力——**这三项四次消融一项都没测**。
5. **不授权** "四次严格消融判死"这种措辞。四次消融的作者本人在每一轮都写了限定语
   （c1 "the tree is not magic"、c2 "Sonnet 5 is still a strong model"、
   c3 "N=5, 3 judges — suggestive, not definitive"、c4 "H2 NOT supported at this scale"）。

**F22 · 一个常被忽略的反证：v2 的死因不是"结构无用"，是"机器层挤掉了研究层"**
`.loop/state/log.md` 的 live run 记录显示，v2 从未走到"结构有没有帮助推理"这个问题——
它停在 worker 输出契约上（见 F23）。**"结构=质量"这一命题在 paperproof v2 上根本没有被测试过。**
四次消融测的全部是 nodify（2,036 行的轻量树），不是那个 13,949 行的框架。
**因此"三代框架被四次消融判死"在字面上不成立：被消融测过的只有第四代（nodify）。**

---

### 五、P1–P15 防坑清单的证据审计

来源：`archive/pre-reset-2026-07-09/v3/docs/01-anti-failure.md`（11,631 B，2026-07-09 02:22）。
文档自称 *"每一条都来自 v2 的**真实事故**(不是假设)"*。逐条核：

| P | 事故是否有独立一手记录 | 证据 |
|---|---|---|
| **P1** | **是（部分）** | git `807050a` |
| **P2** | **是（三个子项全中）** | git `2c70c6d`、`997cf62` |
| **P3** | **是（三个子项全中）** | git `2c70c6d`、`.loop/state/log.md` |
| **P4** | **是（代码可验；"多数失败在机器层"部分成立）** | `queue/engine.py`、log `v2-review-done` |
| **P5** | **是** | log 的 r3→S1–S5→v2.1→v2.1.1 链 |
| **P6** | **否（作者自标为"设计层面倾向"）** | 文档自述 |
| **P7** | **是** | git `807050a` |
| **P8** | **是** | `docs/04-docs-database.md:169` |
| **P9** | **是（代码里直接可见）** | `paths.py:46` vs `verify.py`、git `997cf62` |
| **P10** | **是** | git `997cf62` |
| **P11** | **否（用户口头点名，无事故日志）** | 文档自述 |
| **P12** | **被证伪（其"没出过事"的断言）** | log `m7-eval1`、log `9-component-audit` |
| **P13** | **否（仅此文一处提及）** | 全库搜 `exit 127` 只命中本文件 |
| **P14** | **是** | log `m10-interrupt`、`progress.md` 抬头 |
| **P15** | **是（可逐字核对）** | `docs/01-topic-and-scoping.md` |

**关键引文：**

**P1**（"v2 首次 live run，5/5 个 DocsWorker 输出 schema 非法"）——commit `807050a`
（2026-07-09 00:04）原文：

> "First live-run wave (ai-jobs-2 WV-001, NODE-003) surfaced a class of DocsWorker output defects
> the docs_worker template under-specified. Fixed at the source so the whole class cannot recur…
> replace the loose 'documents, evidence_units, not_found, query_log' hint with an EXHAUSTIVE
> per-level output contract … and an explicit ban on echoing dispatch metadata
> (plan_id/angle/work_item_id) or inventing ids (eu_id/doc_index/…)."

**限定**：commit 说的是 "a class of defects"，没有说 5/5。`.loop/state/log.md` 事后记
*"Wave WV-001 state: official_stats/academic/news committed; industry/counter to re-dispatch under
fixed contracts."* ——即 5 个中 3 个最终提交、2 个需重派。
**"5/5 全部非法"这个精确数字只在 `01-anti-failure.md` 自己声称，无独立佐证。**

**P2**（"文档声称，代码不做"）——commit `2c70c6d` 原文，三个子项逐一命中：

> "render.py: … appends the retry_suffix automatically when the item's last attempt failed
> validation (**docs/07 said this happens; no code ever did it**) … adds render_compile_prompt —
> compile_worker.txt/retry_suffix.txt were registered but **NEVER rendered by anything**
> (CompileWorker dispatch had no wiring at all)."
> "docs/10 §5: canonical template blocks re-synced (**docs_worker had already drifted**)"

V-CDR-03 子项由 commit `997cf62` 证实：
> "V-CDR-03 now ENFORCED: spine() does not filter node_type, so an active alternative wired into
> the thesis ancestor closure joins the spine and was silently dropped from the section plan;
> compiler dry-run now refuses with V-CDR-03 (**+ test proving the path is reachable**)"

**P3**（"组件各自正确，接线是断的"）——commit `2c70c6d`：
> "critic_worker.txt: V-WAVE-03 reads the report's 'form' WRAPPER and the schema requires wave_id;
> **the template named neither and the critic had no way to know the wave id.**"

管线顺序矛盾由 log `v2-review-done` 证实：*"two competing sweep mechanisms + wrong pipeline order
(layer-0 must precede sweep)"*。

**P4**（"机器压过研究"）——代码可直接验证：`queue/engine.py` 530 行、11 态表、900s 租约、
`paths.py:67` 三把锁。**但"live run 的大多数失败发生在机器层"这句需要修正**：
真正跑起来的那次 live run，**halt 点在 worker 输出契约层（P1），不是队列层**。
机器层的大批 P0 是**上线前的评审**发现的（log `v2-review-done`）：
*"wave lifecycle has NO production driver … reactive saturation UNREACHABLE -> needs_docs livelock
… merger URL-dedup breaks quote EUs -> wave can never close"*。
锁竞争确实一直 deferred：log `m11` 记 *"THEME 3 low follow-ups (NOT fixed): committer cross-lock"*。

**P7**（幻觉三件套）——commit `807050a`：
> "Add the V-DR-05 rule for workers: a kind=quote must be a **CONTIGUOUS verbatim span
> (no '…'/'...' elision/stitching)** or use paraphrase."

**P8**（缓存自动视为已解决）——**这是全清单里事故描述最完整的一条**，
`docs/04-docs-database.md:169` 原文：

> "**r2.2 change (removed the matcher-hit cache trigger).** … The ai-jobs live run showed this to
> be wrong: the v1 matcher is a deliberately dumb keyword matcher, so it produced **false cache
> hits** — a genuinely new evidence need (e.g. an aggregate-employment bridge premise) was declared
> 'fulfilled' merely because loosely-related task-automation evidence already existed, which
> **silently overrode a ProofWorker's own `evidence_check=insufficient` judgment** and blocked the
> fresh search the argument required. **Sufficiency is the ProofWorker's decision** … never the
> cache's."

并被固化成永久教条（`docs/18-semantic-retrieval.md:85`）：
*"## What semantics may NOT do (the r2.2 lesson, made permanent) — Similarity NEVER auto-fulfills
a DocsRequest."*

**P9**（同一事实两份）——**唯一一条可以在当前代码里直接读到的**：
`src/paperproof/paths.py:46` 的 `EMPTY_JSONL`（17 项）与 `src/paperproof/verify.py` 的
`_JSONL_FILES`（17 项，逐字相同），并由 commit `997cf62` 加的漂移守卫拴住：
*"New drift guards (tests/contract/test_wiring.py): paths.EMPTY_JSONL == verify._JSONL_FILES
(**two hand-maintained copies**)"*。

**P10**（行号锚点必然过期）——commit `997cf62`：
> "3 fresh-reader faithfulness verifiers (maker != checker); their 14 findings (wrong DOCSPACK
> producer attribution, false cross-module lock invariant, 6 wrong dependency cells, stale counts,
> **off-by-one anchors**) all fixed."
（"3 处" 这个精确计数只在 `01-anti-failure.md`；"off-by-one anchors" 本身有一手佐证。）

**P12 —— 被本仓库自己的日志证伪。** P12 原文：

> "**事故**：v2 规则'并行 worker 必须不同 task_id + 不同输出文件'执行良好，**没出过事**——
> 这是要**保持**的约束而不是修复项。"

`.loop/state/log.md` 的两条记录直接冲突：

> `[2026-07-08] m7-eval1 | fresh Evaluator FAIL: **real DATA-LOSS bug (all 30 tests missed it)** —
> follow-up wave members **reuse round-1 output paths** (wave.py:308 path keyed only by
> request_id+angle; :532-535/:233-234 followups hardcoded official_stats), **overwriting committed
> results**; V-WAVE-01/02 only called from tests, verify never sweeps them."

> `[2026-07-08] 9-component-audit | … **INCIDENT: Freeze reviewer's `rm -rf ... data` deleted
> untracked data/projects/ai-jobs + ai-jobs-2 (gitignored, unrecoverable**; NON-BREAKING — no
> src/test dependency; ai-jobs-2 regenerable)."

第一条正是"并行输出路径冲突导致已提交结果被覆盖"，**是 P12 声称从未发生的那一类事故**，
而且 **30 个测试全部漏检**。第二条是一个只读评审 subagent 用 `rm -rf` 删掉了不可恢复的运行数据。
**P12 应当被改写为"并行隔离必须由分配器保证唯一路径 + 由 verify 扫描断言，而不是靠约定"。**

**P15**（spec 幻想复杂度）——可逐字核对：`docs/01-topic-and-scoping.md` 写
*"### Required sections — **Nine sections**, matched by heading title text"*，
解析规则确实是 **P1–P7**，`Supported paper patterns` 列了 **6 种**，其中注明
*"single_event_mechanism (**the only pattern implemented in v1**)"*。**事故属实。**

---

### 六、nodify 摩擦日志（三份，全部一手）

**F23 · `comparison3/FRICTION.md`（激进消融跑出来的 6 条）**

1. **budget flag/key 不一致**：文档写 `--budget depth=k width=k open_claims=k`，
   实际要 *"one `--budget k=v` per key"*、键名是 `max_depth/max_children/max_open_claims`。
2. **没有 root 重置**：*"the first `nd add` is the sole root viewpoint; a second root-add errors
   `root already exists`, and the root is non-revisable. **The pilot mis-scoped its first add and
   had to `rm -rf sessions/cmp` + re-init.**"* ——刚性结构导致**整场重来**。
3. **claim 不能直接挂在 viewpoint 下**：`add --kind claim` 报
   *"children of a viewpoint are viewpoints"*，必须 add-viewpoint 再 `nd promote`。
4. **`nd tree` 不显示 `orientation`**：*"adversarial coverage is invisible from `tree` alone …
   **Easy to misread as 'no adversarial branches.'**"*
5. **ingest 成功信封形状不明**：*"doc_id was not where the author parsed it
   (`data.doc.doc_id` / `data.doc_id` both None though ingest succeeded)"*。
6. **`nd docs for-node <id>` 返回空但绑定存在**（两个冷恢复探针独立发现）：
   *"a fresh agent relying on `for-node` for provenance would **wrongly conclude a node is
   unsourced**."* ——**溯源命令会给出假阴性**，这是可信度系统最危险的一类缺陷。

另附一条 harness bug：*"`dossier.py` treated evidence `url` as required; when an author left
`url:null` and pointed by `doc_id`, evidence rendered blank (**T2 tree lost all 45 evidence URLs**)"*。

**F24 · `nodify/docs/05-live-test-1.md`（实测 #1，7 条摩擦）**
判词：*"胜任的 agent 无需人扶就能跑通；**摩擦全部来自 payload/路径的猜测，不来自循环本身**。"*
F1 notes/ 位置不可发现；**F2 `--file` 类命令的 JSON 形状只能读源码逆向**（→ 新增 `nd schema`）；
F3 问题型论点的 lean 语义未定义；F4 assemble 重复标题；F5 quote 校验不折叠 Unicode 标点
（弯引号导致误判）；F6 `word_count` 按空白分词、中文恒为个位数；F7 "cites nothing" 两处口径不一。

**F25 · `nodify/docs/06-live-test-2.md`（实测 #2 冷接管，6 条）**
**G1 是本项目最相关的一条**：*"收敛会话的 brief 前沿为空，冷接管者看得见结论、看不见结构
（树/文章的存在都不可见），被迫 4-5 条定位命令 + **违规直读 records.jsonl**"*
→ 修法是 brief 增加 TREE MAP 与 ARTIFACTS 两节。
**含义：resume 摘要必须同时携带「结论」与「结构/工件清单」，否则接管者会绕过 API 直读原始记录。**
G2 ingest 示例路径写的是相对形态、实际只收绝对路径（*"白付 2 次失败"*）；
G3 `pending→stuck` 非法、合法迁移表不可发现；
**G4 recall 在全 global 距离下区分度弱（8 篇全返）——被接受为已知限制**；
G5 article 层只有写命令没有读命令，*"更新大纲被迫直读 records.jsonl"*；G6 outline 重注册无提示。

**F26 · 三份摩擦日志的共同模式（我的归纳）**
17 条摩擦里，**没有一条是"逻辑树的思想不对"**；压倒性多数是同一类：
**CLI/schema 不自描述 → agent 只能猜 payload、猜路径、猜信封形状**。
`nd schema` 一个命令就消掉了整类（实测 #2 判词：*"完全消灭 payload 猜测，零看源码"*）。
**这条对 academic-research-plugin 的价值高于四次消融的任何一个分数。**

---

## 与二手文档的冲突

对照对象：`<repo>/.archive/v1-2026-08-17/PRINCIPLES.md`
（v1 规划的最高禁令 P-1/P-2/P-3）。

**C1 ·（严重）"被四次严格消融判死" —— 过度断言**
v1 原文：*"Paper Graph 的三代框架…被四次严格消融判死"*。
一手事实：四次消融的独立样本是 6 个问题（三轮共用同一组 5 个经济学问题）、36 次 author run、
评分尺有效分辨率 2 档；**topic 级配对检验下没有任何一项跨臂差达到 p<0.05**（F20）。
四位作者自己每轮都写了限定语（c3: *"N=5, 3 judges — margins of ±0.1–0.4 are **suggestive, not
definitive**"*）。**"判死"这个措辞在一手文档中不存在。**
唯一接近的是 `DESIGN.md` 的 *"Four rigorous ablations said it doesn't"*——那是 DESIGN.md 的
修辞，而 DESIGN.md 本身是二手转述（它没有引用任何具体数字）。

**C2 ·（严重）"质量增量曲线 v1 +1.0 → v2 +0.13 → v3 −0.39" —— 三个不同的量被拼成一条曲线**
三格的被测量、作者模型、对照臂、渲染方式全部不同（F19）。
一手 `comparison3/RESULTS.md` 的同一张表**逐格标注了 model / artifact 列**；
v1 转述时把标注抹掉，只留数字，从而把"三次不同实验"变成了"一条单调趋势"。

**C3 ·（严重）"−0.39 = 刚性结构在强模型激进模式下是负资产" —— 最大分项是渲染伪影**
一手可机械证明：calibration −1.00 的 15/15 零方差，源自 `dossier.py` 只在
`status ∈ {retired, stuck}` 时渲染 Dead ends 段，而 tree 臂 5/5 个 topic `dead_ends=0`（F11）。
剔除三个具备伪影签名的维度后净差 −0.13，与 grounding 的 +0.134 同量级反号（F12）。
**v1 引用了 comparison3 的结论句，但没有引用 comparison3 自己在同一文件里写的
"asymmetric dossier rendering … explains most of the calibration gap (−1.00)"。**

**C4 ·（严重）"纪律无需工具就贡献了消融中最大的单项增量（raw→skills +1.0）" ——
该数字来自 N=1，且在 N=5 时不复现**
一手：comparison2 的 by-arm overall 是 raw **4.53** / skills **4.60** / tree **4.73**。
**skills − raw = +0.07（t=0.19），tree − skills = +0.13（t=0.43）——机器增量反而比纪律增量大。**
另注：这是一手 RESULTS.md **自身的推理错误**（它写 *"The discipline, not the machinery, is the
lever — again, and more starkly"*，与自己的表格矛盾），v1 整段继承。
且 comparison2 的 raw prompt 已含三条纪律（`PROMPT_raw.md` 要求 counterpoints 段、calibration、
verbatim quote、保存源文本），作者自己披露为 confound——**这意味着 c2 里的 raw 臂本来就是"半纪律臂"，
skills−raw 这个差本就注定接近 0**。

**C5 ·（中）"595 个测试全绿的框架在产品维度归零归档" —— 数字对，因果错**
595 属实（commit `2c70c6d` 尾行 *"595 passed."*；最终 m11 gate 是 587 default + 4 semantic）。
但**这 595 个测试保护的是 paperproof v2，而四次消融测的是 nodify（2,036 行）**。
paperproof v2 从未被任何消融测过——它死在 live run 的 worker 输出契约上，
连"结构有没有帮助推理"这个问题都没走到（F22）。**"595 绿测试的框架被消融判死"是把两个不同的东西缝在一起。**

**C6 ·（中）"P4 复杂度预算…机器层压过研究层是 v2 live run 的真实死因（8 次校验失败中 5 次是机器层故障）"
—— 括号里的统计量在一手证据里不存在**
我在整个仓库（含 `.loop/state/`、git log、archive 全部 md/json）搜索该统计，**零命中**。
唯一相关的 "5/5" 是 `01-anti-failure.md` P1 自己声称的 "5/5 个 DocsWorker 输出 schema 非法"，
而那是**契约层**（prompt 未逐键枚举）事故，不是"机器层"事故。
且真实 live run 的 halt 点恰恰在契约层而非队列层（F7/P4 条目）。
**这个数字看起来是二手转述阶段产生的。**

**C7 ·（中）"P1–P15 整体继承" —— 其中 P12 已被本仓库日志证伪，P6/P11/P13 无事故记录**
详见 F-表与 P12 引文。若整体继承而不修订，会把一条**已被证伪的安全断言**
（"并行输出不相交这条规则没出过事"）写进新系统的原则层。

**C8 ·（中）"frontier-boxed brief 的日志斜率比线性日志低 3 倍（v4 消融唯一实证优势）" ——
方向对，但被两个未披露的问题削弱**
(a) 一手 `results.json` 的四个点显示 tree 增量**递增**（+1594/+2409/+2810），
RESULTS.md 的 "bounded-sublinear" 与数据矛盾（F14）；
(b) `phase_metrics.py` 只把 `nd brief` 的 stdout 计为 tree 的 resume 成本，
**不计 prompt 明确要求的 `nd tree`/`nd show`/`nd docs for-node`/`nd recall` 下钻**，
而 notree 计整份 log；同时 notree 被 prompt 限死为单一扁平 log（F15）。
**该数字测的是"有索引 vs 无索引"，不是"树 vs 无树"，且 N=1。**

**C9 ·（低，但方向重要）v1 未记录：继任方案（两 gate workflow）同样未验证**
`CHANGELOG.md`（2026-07-10）自述 *"The honest A/B test … is still not run … remains the top open
item"*，且 *"Only `nuclear-safety` has a complete held-out judgment panel, and it is `REVISE`"*。
v1 把该方案当作"已被证明的正确方向"继承，一手证据不支持。

---

## 对 academic-research-plugin 设计的含义

**M1 · 把 P-1 从「禁令」降级为「举证责任」。**
正确的表述不是"永不造结构框架"，而是：
**任何结构投资必须先声明它要买的可测属性，并附一个能在本系统语料上重跑的度量。**
四次消融真正证明的是「拿判定质量作为结构的验收指标，在 4–5 档 LLM 评分尺上是测不出来的」——
这是**度量方法**的失败，不是结构的失败。本项目的产品恰好是**可信度**，
它的验收指标（verified/unverified 比例、引文可追溯率、数据重跑一致率）**都是机械可测的**，
不需要 LLM 评委——**这正是四次消融缺的那把尺子**。

**M2 · 结构投资的白名单可以放宽到四类（v1 的三类 + 一类）。**
在一手证据下站得住的：
1. **强制可审计性**（quote 逐字子串校验 / content_hash 去重 / cite 硬解析）——
   c1 fidelity 1.0 vs 0.92、c3 grounding_rate 4/5 = 1.0；**这是唯一跨四轮方向一致的优势**，
   且靠代码不靠评委。
2. **有索引的 resume 状态**——c4 斜率 3×（限定见 C8）。但**必须同时携带结构而非只有结论**
   （nodify G1 的教训：只给结论会导致接管者违规直读原始记录）。
3. **结论强制落盘**（P14）。
4. **（新增）溯源查询必须是主路径且有假阴性测试**——FRICTION #6：
   `nd docs for-node` 返回空但绑定存在，**会让接管者误判"该结论无来源"**。
   对以"每条 claim 带 verified/unverified 状态"为产品的系统，**溯源假阴性 = 产品事故**，
   必须有专门的 fixture 测试（存在绑定 → 查询必须命中）。

**M3 · 用可核验答案做验收，而不是用评委分——这一步前代已经想到但没跑。**
`nodify/docs/12-depth-and-rigor.md`（v1–v4 全部结束后写的最后一份设计，标记 ADOPTED，**从未执行**）
已经诊断到位：

> "**Tasks: questions with CHECKABLE answers** — so rigor is scored against ground truth, not a
> judge. … **correctness / false-claim rate** — of the load-bearing conclusions, how many are
> actually true (checked against ground truth). *The headline for rigor.*"

并预注册了 kill-criterion：*"**H0 / kill-criterion:** if a strong model already deepens +
self-refutes natively … the scaffold adds nothing and we say so … **This is the real risk.**"*
**本项目应当直接从这里起跑：第一个 eval 就用 checkable-answer 任务集 + false-claim rate，
不要再造一个 LLM 评委面板。**

**M4 · 复杂度预算要写进合同，但预算的单位不是行数，是"机器层 vs 研究层的失败比"。**
v2 的教训在代码里可读：55 条 CLI 命令 / 106 条 V-rule / 11 态队列 / 900s 租约 / 3 把锁 /
13,949 行 —— 全绿 595 测试，live run 仍停在第一波。v3 的应对是 15 条命令 + ≤2500 行预算（未执行）；
nodify 落到 2,036 行（执行了）。**建议的合同断言：每个 gate 报告必须分类统计本轮失败
（研究内容层 / 契约层 / 机器层），机器层占比超过阈值即触发简化，而不是等到 live run。**

**M5 · P1（逐键枚举 schema）+ 漂移守卫是全清单里 ROI 最高的一条，必须原样继承。**
commit `807050a` 与 `2c70c6d` 显示：一次"逐键枚举 + 禁键点名 + 合法样例 + 模板↔schema 漂移测试"
的改造，直接把一整类 worker 输出失败消灭（*"Fixed at the source so the whole class cannot recur
(fix-from-root, not per-output patching)"*）。
配套：**CLI 必须自描述**（`nd schema <name>` 打印 schema 全文 + 最小合法 payload），
一手判词是 *"完全消灭 payload 猜测，零看源码"*（F25）。
对本项目的超并行 fan-out，这条的价值随 worker 数线性放大。

**M6 · 并行隔离必须由代码保证唯一路径 + verify 扫描，不能靠约定（改写 P12）。**
两条一手事故：m7 的路径复用覆盖已提交结果（30 个测试漏检，靠 fresh evaluator 才发现），
以及评审 subagent 的 `rm -rf` 删掉不可恢复的运行数据。
落地要求：(a) 输出路径由分配器生成且含轮次/来源维度；(b) 冲突由 verify 主动扫描并 exit 非零；
(c) **只读角色的 subagent 必须在物理上无写权限**（worktree / 只读挂载 / 禁 `rm`）；
(d) 运行产物不得只存在于 gitignored 目录。

**M7 · 缓存/召回永远不得代替判断（P8，一手事故最完整的一条）。**
*"Sufficiency is the ProofWorker's decision … never the cache's."*
对本项目直译：**任何"已有相似证据"的召回命中，都不得把一条 claim 自动标记为 verified。**
召回只能作为材料内嵌进任务包（P8 的 v3 对策：*"recall 只提供材料，永不改变任何状态"*，
强制机制是 *"测试断言 recall 前后项目文件哈希不变"*）——这条建议原样抄。

**M8 · 不要重复"用 dossier/渲染器代表推理质量"的错误。**
c3/c4 两轮的最大教训之一是**渲染器决定了判分**。若本系统要做任何 A/B，
两臂的呈现必须机械对称（同一渲染器渲染两臂，或两臂都手写），
且任何"是否存在某一节"的差异必须先排除再解读分数。

**M9 · 承认覆盖空白，把它变成第一批 eval。**
四次消融零覆盖的区域正是本项目的产品核心：可重跑数据分析、引文到原文的精确定位、
超长多 loop 续跑、并行 worker 一致性、弱模型。**这些不是"前代已证否"的方向，是"前代从未测过"的方向。**
把它们写成第一批 eval 任务，本身就是对 v1 最高禁令的正确修正。

---

## 未决问题

1. **`01-anti-failure.md` 的 P1 "5/5 个 DocsWorker 输出 schema 非法" 无独立佐证。**
   commit `807050a` 只说 "a class of defects"，`.loop/state/log.md` 事后记 3 个已提交、2 个待重派。
   真实失败数可能是 5、也可能是 2。**若要在新系统里引用这个数字，需要降级为"至少 2/5"。**

2. **comparison2/3/4 未进 git，无篡改防护。** 内部一致性可查（judge JSON ↔ KEY ↔ results ↔
   blinded md 三方对得上），但没有版本历史。若后续攻击方质疑数据真实性，我无法从版本控制反驳。

3. **c3 tree 臂 5/5 个 topic 的 `dead_ends=0` 的原因未查清。** 三种可能：
   (a) `PROMPT_tree.md` 没有要求写 retired/stuck；(b) nodify 的 status 迁移不便
   （实测 #2 G3 记 `pending→stuck` 曾非法）；(c) 树的结构让作者不倾向"杀分支"。
   **区分这三者决定了"结构是否真的压制了 kill-fast 纪律"，我没有足够记录判定。**

4. **c3 tree 臂 5/5 个 topic `max_depth` 都只有 2（budget 允许 3）的原因未查清。**
   如果是刚性带来的摩擦（FRICTION #3：claim 不能直接挂 viewpoint 下，必须 add + promote），
   那么 c3 测的是"这一版实现的刚性"而非"结构本身"。

5. **`nodify/docs/12-depth-and-rigor.md` 描述的 `nd challenge` 实验从未执行。**
   它是整个证据体里唯一一个用 ground-truth 正确率而非评委分做验收的设计。
   **"结构能否降低 false-claim rate"这个问题至今没有任何数据。**

6. **继任的两 gate workflow 的 A/B 也没跑。** `CHANGELOG.md` 自认这是 top open item。
   **本项目继承它的哪些部分，同样处在"未验证"状态，不应被当作已验证前提。**

7. **P13（zsh/BSD grep/stderr 混流）没有独立记录。** 全库搜 `exit 127` 只命中
   `01-anti-failure.md` 一处。这几条运维坑很可能是真的（它们的形态很具体），
   但无法从一手材料确认；作为"经验建议"继承可以，作为"事故驱动的硬约束"引用则超出证据。

8. **未验证：nodify 的 `nd check` 在四次消融中到底拦下过什么。**
   c1 提到 *"1 soft warning that one divergence layer lacked an adversarial direction"*
   （框架看见了自己的缺口），c2 提到 orphan section records 的 2 条 benign warning，
   c3/c4 都是 clean/near-clean。**"强制机制真的拦下了错误"这一点，除了 quote 逐字校验以外，
   一手证据里几乎没有正面案例。** 这对"用 check 保证可信度"的设计是个需要补的空白。
