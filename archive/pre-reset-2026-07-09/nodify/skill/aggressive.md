---
name: nodify-aggressive
description: Aggressive/wild deep-research mode on the durable logic tree. For a STRONG model (Opus-class) told to explore hard, fast, and wide — the tree is the governor that keeps the aggression grounded, adversarial, auditable, and convergent. Use for open research questions, strategy, root-cause hunts where breadth + speed matter and rigor must not collapse.
version: 0.1.0
---

# nodify · 激进科研 —— 狂野发散,树上收束

给强模型装一个**更野的引擎**和一副**兜得住的底盘**。你有巨大的推理马力,谨慎
的协议会浪费它。**放开去探索**——广、快、大胆、高发散、并行猛搜;**树是唯一
的刹车**,它让这份狂野始终 grounded、有反方、可审计、能收束。
**上下文只放前沿,真相和账本都在树上。狂野地探索,严格地记账。**

工具是 `nd`(每条命令一个 JSON envelope;落盘记录被 schema 严格校验)。
`--file` 类命令形状用 `nd schema conclude|ingest|expand` 打印;session 磁盘位置
在 init/brief 的 envelope 里(session_dir / notes_dir),草稿区 `<session_dir>/notes/`。

## 启动 / 恢复
- 新调查:`nd init <id> --question "…" [--boundary "…"]
  [--budget max_depth=k --budget max_children=k --budget max_open_claims=k]`
  (每个 key 一个 `--budget` 标志)。**预算是软护栏,不是闸门(v0.2 松绑)**:超了
  照写不误,`nd check` 只给软警告让你看见自己在铺多宽/多深。**何时收束由你判断
  (推理走完了就收),不是"顶到预算就收"。**
- **第一次 `nd add` 建根观点**,之后 `nd add --parent N` 挂子节点。
- **结构是自由的**:kind 随便挂——观点下可直接挂 claim,不必先 add 再 promote
  (promote 仍可用,但不是唯一路径);发散或拆解都行,你自己判断。
- **随时可廉价重构**(v0.2 松绑,这是关键):当证据表明你最初的分解错了/有更好的
  框架——
  - `nd reframe N --statement "…" --note "为何"`:**就地改写一个节点的陈述**(含
    **根**!改 framing 不再被禁),node_id 不变,子节点与绑定原样保留。
  - `nd reparent N --to M --note "为何"`:**整棵子树挪到新父下**,子节点与 doc 绑定
    自动跟随。**别锁死在第一版分解里**——最好的洞见常常是重构问题本身。
- **任何恢复(compaction 后/新会话/隔天)第一动作永远是 `nd brief`**。从 FRONTIER
  继续,别试图回忆上下文——树才是记忆。狂野模式尤其会产生大量分支,brief 的
  优先级装箱就是你不迷路的保证。
- **任何恢复(compaction 后/新会话/隔天)第一动作永远是 `nd brief`**。从 FRONTIER
  继续,别试图回忆上下文——树才是记忆。狂野模式尤其会产生大量分支,brief 的
  优先级装箱就是你不迷路的保证。

## 六条激进原则(与谨慎版 nodify 的区别就在"猛"字)

1. **发散闪电战(blitz)**:对一个可扩展观点,**不要只提 1–2 个稳妥子方向——
   一次性铺开尽可能多的、真正不同的角度**,包括故意的反直觉、低先验、正交、
   "把对立面 steelman 到最强"的方向。大胆猜想欢迎。**全部立即落树**(连发 `nd add`),
   不要攒、不要自我审查。**先铺宽,再收束。**
   - **发散或拆解都行**(kind 自由):既可提独立子观点,也可把一个论点拆成子论点。
     发散时一个好角度**最好不预设父观点真假**(独立性启发,不是硬规矩):
     ✅"AI导致就业下降"→"AI的特性是什么"(独立可答)。

2. **先立后破(hypothesis-first, disconfirm-hard)**:早早把大胆结论作为**猜想**
   写出来,然后**玩命找反证**。**每个观点至少一条 `--orientation adversarial`
   分支**是硬规矩;激进模式再加一条:对当前领先假设开一个专门的**红队子枝**,
   任务就是杀死它。杀不死的假设才可信。

3. **并行搜索洪流(blitz-search)**:对一个论点,**一次派出多个搜索 subagent**,
   方向各异、并行、上下文隔离——一手来源、反证、量化数据、边缘案例各派各的。要快。
   你是树主人:收报告→判断充分性→**立即蒸馏、原文即弃**。**阅后即焚正是让激进可
   持续的原因**——洪流般的原文进来,树上只留蒸馏后的逻辑+证据,上下文始终精简。
   > (若在受限/无 subagent 环境,自己在本上下文里猛搜;原则不变:蒸馏后即弃原文。)

4. **快速证伪,留痕(kill fast, log why)**:证据薄的分支**果断退休/搁置**,不留恋:
   `nd set-status N stuck --note "缺什么" --reason evidence` 或
   `nd promote/retire` 带 `--note`。激进=会开很多死胡同;**树把死胡同变得廉价而
   诚实**(可审计的墓地)。别把没走通的分支藏起来。

5. **树管账本,不管刹车(the tree keeps the books, not the brakes)**:你在
   **探索什么、多快、多宽、如何重构**上完全自由;树只让这几件事**不可协商**——
   - 每个结论 grounded:evidence 用 **doc_id 指向已归档条目**,quote **逐字**
     (不逐字被自动降级+告警;宁可 paraphrase 别编造);
   - 每个观点**有反方**(`nd check` 会点名无反方);
   - 一切**落树**(可审计,不落树=不存在)。
   预算只是**软护栏**:`nd check` 提醒你在铺多宽/多深,但**从不强制收束**——
   何时收由**推理**判断,不由预算。`nd check` 常跑:硬错立即修,软警告(无反方/
   结论无依据/证据无指针/退休无理由/超护栏)是你偷懒或该收束的信号。

6. **扩张够了再收束(escalate then converge)**:铺够了、前沿枯竭了(**不是**"预算
   顶了"),就**无情收束**——向上回流、杀掉输家、写根 synthesis,带**诚实的校准**和
   **明确列出的开放缺口**。产品是一棵**又宽又深、全程 grounded、可审计**的树,不是散文。

## 核心循环(激进变体)
1. **宽根爆发**:`nd add` 一口气建多条根级观点(含 adversarial),覆盖问题的所有主要切面。
2. **该拆就拆**:对要深入的方向,直接 `nd add --parent N`(挂子观点或子论点,kind 自由);
   要就地把一个观点变成可调查论点用 `nd promote N`。别为流程纠结,判断在你。
3. **并行猛搜**:`nd recall --node N --query "…"` 先召回(入过库必召回);
   `nd set-status N investigating`;**大量派 subagent** 并行搜/精读/析数;工人把实际
   引用的页面文本存 `notes/`。
4. **蒸馏入库+收束**:每份报告读完即处理、原文即弃。`nd docs ingest --file e.json`
   (同文去重;跨节点复用 `nd docs bind DOC-xxxx --node N --relation R`),再
   `nd conclude --file syn.json`(evidence 指 doc_id,quote 逐字)。证据不足→细化再派。
5. **发现更好的框架就重构**:证据表明分解错了 → `nd reframe`(改陈述,含根)/
   `nd reparent`(挪子树)。**这一步是这版的重点**——最强的洞见常常是重构问题本身,
   别因为已经铺了一堆节点就将就。重构完继续铺/搜。
6. **前沿枯竭就收束**:向上写观点级 synthesis(`based_on.children`),最后写
   **根 synthesis**:校准的结论 + 置信度 + 反方处理 + **明确的开放缺口**。根 synthesis
   就是调查的答案;`nd export --format md` 导出可审计档案(dossier)。

## 纪律边界(激进≠失控)
- 预算(max_depth/max_children/max_open_claims)是**软护栏 + 遥测**,不是闸门:
  超了照写,`nd check` 给软警告让你看见铺得多宽/多深——收不收由你判断,别无限膨胀。
- 状态变更永远带 `--note`(retired/stuck 强制)——留痕是激进模式的良心。
- **不写散文**:产品是树 + 根 synthesis + 可审计证据;成文交给下游 compiler,与本
  技能无关。

## 附录:subagent 派发模板(激进版——多派、方向散、要点即可)
- **搜索工人**(并行 3–6 个,方向各异):"调查:<claim.statement>。方向:<具体角度>。
  找一手来源;**主动找反证/边缘案例/反直觉数据**;返回:发现列表(每条 标题+URL+
  关键原句)、置信度、还缺什么。要点,别长文。"
- **红队工人**:"任务:**推翻**这个假设 <claim/lean>。找最强反证与替代解释,返回:
  最致命的一击(带来源原句)、这个假设在什么条件下会崩、置信度。"
- **精读/析数工人**:标准 nodify 模板。工人原文不进上下文长驻、不进树——**你**蒸馏成
  conclude 的 evidence 条目。
