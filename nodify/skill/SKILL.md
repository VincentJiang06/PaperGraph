---
name: nodify
description: Run any deep investigation on a durable logic tree (nd CLI) instead of long markdown context — distill logic + evidence into nodes, discard raw text, survive compaction. Use for research questions, tech decisions, root-cause hunts.
version: 0.1.0
---

# nodify — 树上思考,阅后即焚

你在做一场深度调查(研究问题 / 技术选型 / 根因分析)。不要把状态堆在上下文
里:**上下文只放思考的前沿,真相放在树上。** 工具是 `nd`(每条命令输出一个
JSON envelope;所有落盘记录被 schema 严格校验,trace 自动记录)。

## 启动 / 恢复

- 新调查:`nd init <id> --question "…" [--boundary "…"] [--budget k=v]`,然后
  `nd add --statement "…"` 建根观点。
- **任何恢复场景(compaction 后、新会话、隔天续做)第一动作永远是
  `nd brief`**。简报按优先级装箱:前沿 > 已收束结论 > 未上折的答案 > 卡点。
  从 FRONTIER 一节继续干活,不要试图回忆上下文里发生过什么——树才是记忆。

## 核心循环

1. **发散(观点层)**:对一个 open/expanding 观点提出新方向子观点,
   `nd add --parent N --statement "…" --why "…" [--orientation adversarial]`。
   - **发散≠拆解**:合法的子方向,其答案**不预设父观点真假**。
     ✅ "AI导致就业下降" → "AI的特性是什么"(不管降没降都能答)
     ❌ "AI导致就业下降" → "就业下降了多少"(预设了下降,这是拆解)
   - **每次发散至少一个 adversarial 方向**(专门找会推翻父观点的证据线)。
   - 观点一成形**立即落树**,不要攒批——上下文随时可弃,树不会丢。
2. **升格(观点→论点)**:当你对一个观点再也说不出"若被解答会改变判断的
   新方向"(反事实探针失败),它就穷尽了:
   `nd promote N --note "尝试过的方向/为何不成立/反事实探针/预期证据形态"`。
   论点必须是**最小的、可直接投入调查的明确问题**。太大就先
   `nd add --parent <claim>` 拆解成子论点。
3. **调查(论证层)**:**先召回再搜索**——`nd recall --node N --query "…"`,
   命中的条目把 text_file 直接喂给工人("先读这个,再决定搜什么");然后
   `nd set-status N investigating`,**大量派 subagent**——搜索、精读、数据
   分析各派各的,并行,上下文互相隔离(模板见附录)。工人须把实际引用的
   页面文本存到 notes/ 供归档。你是树主人:收报告、判断充分性、蒸馏,
   自己不淹在原文里。
4. **蒸馏(焚前入库)**:每个 subagent 报告读完立即处理,原文丢弃。
   结论**实际依赖**的来源先归档:让工人把抓到的页面文本存 notes/,然后
   `nd docs ingest --file entry.json`({kind,title,url?,text_file,summary≤500,
   bindings:[{node_id,relation}]})——同文自动去重,只加绑定。再写结论:
   `nd conclude --file syn.json` —— evidence 条目用 **doc_id 指向归档条目**,
   quote 必须逐字(不逐字会被自动降级并告警;宁可 paraphrase 别编);
   没归档的次要来源至少带 url 或 locator(check 会点名)。
   证据不足→细化方向重派(≤2 轮),再不行
   `nd set-status N stuck --note "缺什么" --reason evidence`,让缺口回流。
5. **收束(向上回流)**:一个观点的子节点足够回答它时,写观点级结论
   (based_on.children 列上依据的子节点)。根观点的 synthesis 就是调查的
   最终答案。中途认识变了就写新版(revises 旧 SYN id)。
6. **交付**:`nd export --format md|json` 给下游(写文、决策备忘、复盘)。

## 纪律(check 会盯着)

- `nd check` 常跑:硬错误必须立刻修;软警告(无反方、结论无依据、证据无
  指针、退休无理由)是你偷懒的清单,别让它长。
- 状态变更永远带 `--note`(retired/stuck 强制)——一年后读树史的人靠它。
- 预算(深度/宽度/开放论点数)是发散贪婪的缰绳;顶到预算就先收束再扩。

## 附录:subagent 派发模板(建议,可改可弃)

- **搜索工人**(并行数个,方向不同):"调查问题:<claim.statement>。研究
  方向:<你给的具体方向>。要求:找一手来源;主动找反证;返回:发现列表
  (每条附 来源标题+URL+关键原句)、置信度、还缺什么。不要写长文,要点即可。"
- **精读工人**:"精读 <url/文件>。问题:<claim>。返回:与问题直接相关的
  结论、原句引用(带定位)、该来源的立场与局限。"
- **分析工人**:"数据:<文件/来源>。问题:<claim>。做<具体分析>,返回:
  方法一行、结果、对问题的含义、代码/中间产物存 notes/。"
- 工人返回后:**你**蒸馏成 conclude 的 evidence 条目;工人的原文不进上下文
  长驻,不进树。
