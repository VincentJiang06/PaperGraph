# PaperGraph 商业推广方案

> 前提判断：这大概率是开源项目。本方案按"开源为主体、保留商业化选项"设计——开源本身就是获客渠道，商业化只在信任建立之后才有意义。

## 1. 定位与信息设计

**类目**：不进"AI 写作工具"类目（红海且污名化），自建类目——**论证工程 / Argument Engineering**。

**One-liner 候选**（按渠道选用）：

```text
主打     Prove your argument before you write it.
         （先证明，后写作。）
技术圈   A compiler for arguments: claims are nodes, inferences are proved,
         prose is the last 5%.
学术圈   把"AI 帮你写"倒过来：AI 负责抬杠和查证，你负责思想，
         全程留下可审计的证据链。
```

**三条信息纪律**（所有物料遵守）：

```text
1. 永远说"验证器"，不说"写作助手"。演示重点是论证被拆掉再修好的过程，
   不是最后生成的散文。
2. 永远带审计链画面：sentence → node → evidence → 原文页码。
   这是别人复制不了的视觉锤。
3. 诚实报成本（token/时间）。学术用户对"too good to be true"极度敏感，
   诚实本身就是差异化。
```

## 2. 开源策略

```text
License   Apache-2.0。理由：学术与企业采用无摩擦；防云厂商套壳对本项目
          不是真实威胁（价值在工作流与社区，不在代码本身）；AGPL 会吓退
          高校 IT 与企业试点。
仓库资产  README 顶部放 20 秒 GIF：Logic Map 由蓝转绿、一条边断裂弹出
          bridge、最后 trace 链展开。这个 GIF 决定 50% 的转化。
          P4 示例一条命令可跑（含 FakeWorker 离线模式——没有 API/订阅
          的人也能看到全流程）。
          docs/ 本身是营销资产："规范先行、文档即程序、由 AI 执行落地"
          是 2026 年工程圈最热的叙事之一，单独可以讲一场 talk。
治理      CONTRIBUTING 明确"docs 是法律"：PR 必须同步改规范。
          新论文模式（paper_type 模板）设计成最容易的外部贡献入口。
```

## 3. 分阶段推广

### Phase 0 — 发布前（v1 完成后 2–4 周）

```text
□ 3–5 个种子用户（博士生/政策分析师各半）真实跑完一篇，收集证言与
  失败案例；失败案例写成 issue 公开——学术圈吃"局限性诚实"这一套。
□ 录两条视频：20 秒 GIF（README/社交）+ 8 分钟完整走查（YouTube/B站）。
□ 写发布文章《线性写作有害论》（Why linear writing is harmful to
  arguments）——立场文，不是产品文；产品在文末出现。
□ 提交 Anthropic 社区展示渠道（built-with-Claude / cookbook / MCP &
  agent showcase）。这是最对口的免费流量：PaperGraph 是 Claude Code
  subagent 编排的教科书案例。
```

### Phase 1 — 发布（第 1 个月）

```text
海外  Show HN（标题打"argument compiler"角度，不打 AI 角度）；
      X/Twitter 长帖：judge-free worker + 判定表的确定性设计，钓
      agent-engineering 人群；r/PhD、r/AcademicWriting、r/artificial 分发
      不同角度版本。
国内  知乎长文（学术写作方法论角度）+ B站演示（研究生受众）+
      即刻/少数派（工具角度）。中文学术写作人群密度高、痛点强，
      且几乎没有竞品声量——值得做同权重投入而非"顺便翻译"。
目标  GitHub 1k star；≥50 个真实跑通 S7 全流程的项目（以 Discord/issue
      反馈计，不装遥测）。
```

### Phase 2 — 社区深耕（第 2–6 个月）

```text
□ Discord/微信群：设"本周论证"栏目——公开拆解一个真实论证的图。
□ 模板经济：每个新 paper_type（对照案例、实证、文献综述图谱）都是一次
  内容发布 + 一次贡献者招募。
□ 学术合法性闭环：写方法论 preprint（arXiv/SSRN），让用户在论文里
  引用工具——学术工具最强的增长回路是"被引用"。
□ 高校写作中心/方法课合作 2–3 家，做 workshop（提供现成课件）。
□ 每月一篇"审计报告"式博客：真实项目的 token 成本、失败率、
  dead letter 分布——把运营数据当内容。
```

### Phase 3 — 可持续化（6 个月后，视信号决定）

启动条件：周活项目 > 200，或出现机构级询单（智库/咨询/出版社）。

## 4. 商业化路径（备选项与推荐）

```text
a) Open core + 托管协作层（推荐主路径）
   本地 CLI/WebUI 永久免费开源；收费的是"PaperGraph Cloud"：
   项目托管、导师/客户只读审阅链接、团队评论落在节点上、托管 worker 池。
   本质是卖协作与托管，不是卖功能——最不伤开源社区的模型。
   定价想象：个人 $0 / 团队席位 $15–30/月 / 机构按席位年签。

b) 垂直版本（备选，信号驱动）
   法律 brief / 尽调报告 / 政策合规写作——这些行业为"审计链"付费的
   意愿远高于学术。若 Phase 2 出现此类询单，做行业模板 + 私有部署包。

c) 服务与培训（现金流补充）
   高校 site license + workshop 打包；出版社/期刊的"论证审计"试点。

d) 赞助（保底）
   GitHub Sponsors + Anthropic 生态合作（credits/联合案例）。

不推荐：对个人研究者收订阅费。学术个人付费意愿低、流失高，
且会立刻杀死社区增长——个人永远免费。
```

## 5. 指标体系

```text
虚荣指标（对外）  star、发布文阅读量
真实指标（对内）  跑通 S7 全流程的项目数（北极星）
                  spine freeze 达成率（进入者中多少人走到冻结）
                  dead letter 人工仲裁率（方法可用性的反向指标）
                  模板贡献数、方法论 preprint 被引数
原则              不内置遥测；数据来自自愿反馈与云版（若有）。
                  学术用户对隐私极敏感，"零遥测"本身写进 README 当卖点。
```

## 6. 风险与应对

```text
"AI 代写"污名     信息纪律第 1 条；主动写《这不是代写工具》立场页；
                  强调产出物自带全程审计痕迹——比人肉写作更可查。
Claude Code 依赖  规范层 harness 无关；Phase 2 做一个最小 OpenAI/本地
                  模型 worker 适配作为"可移植性证明"（不求好用，求存在）。
类目教育太贵      不正面教育，用 GIF 让人"看见"论证被修复；
                  蹭"spec-driven development"的既有热度侧面进入。
巨头抄袭          抄得走功能，抄不走规范社区与模板生态；docs/ 的
                  开放性本身是护城河（标准之争打法）。
维护者倦怠        范围纪律：v1 封闭清单已写进 docs/10；对需求说不的
                  依据是公开规范，不是个人意志。
```

## 7. 第一周行动清单（当 v1 代码落地后）

```text
1. 录 20 秒 GIF + 8 分钟走查视频
2. README 按本方案信息纪律重写第一屏
3. FakeWorker 离线演示模式打磨（无 API 也能体验）
4. 发布文《线性写作有害论》初稿
5. 找 3 个种子用户（优先：写学位论文开题的博士生）
6. 提交 Anthropic 社区展示 + 准备 Show HN 文案 A/B 两版
```
