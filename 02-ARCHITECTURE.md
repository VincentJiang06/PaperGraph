# 02-ARCHITECTURE — profile 形态、模块分拆、DSH 能力映射

> **本文件的地位**：回答「这套系统在 DSH 上长什么样、由哪几块组成、每块靠 DSH 的什么能力、哪些能力根本不存在」。
>
> **规范源纪律**：所有共享术语（状态枚举与状态函数 S、三个正交谓词、claim kind、`evidence_grade`、写权矩阵、身份与独立性规则、门的分级 GC-0/1/2、flag 词表、文件与目录契约、术语表）**只在 `01-CONTRACTS.md` 定义**。本文件一律写「见 01-CONTRACTS §N」并直接使用该词，**不复述定义**。
>
> **前提纪律**：本文件受 `00-PREMISE.md` 的裁决约束，特别是 B1（超并行是吞吐与核验密度主张，不是质量主张）、B2/P-1′（结构投资必须自证增益）、B5（四类结构性消灭 / 八类明写不防）、B8（我们自己的门在三条代码落地前不可信）。
>
> **硬约束**：本文件中任何关于 DSH 运行时的陈述均以 `research/v2/GROUND-TRUTH-CORRECTIONS.md` 为准。一手读包基线：本机安装 `@deepseek-ai/dsh` **0.1.0-rc.6**，嵌套 194 个包，实测日期 **2026-08-17** [E: gt-profile-plugin.md#头部]。
>
> **写作纪律**：每条载重断言带 `[E: ...]`；语料标 `unverified` 的数字原样带走；无外部证据的工程选择显式标 **〔裁定〕** 并给出「什么会推翻它」。

---

## §A 总体形态

### A.1 一句话形态

**一个 headless-first 的 DSH profile，把「检索 / 取证 / 落盘」做成进程内工具，把「判定」做成 DSH 进程外的门脚本，把「扇出」压进 workflow 的排队通道，把「散文」压成最后一层渲染。**

四句话对应四条一手事实，缺一条这个形态就不成立：

1. 检索取证必须是**我们自己的进程内工具**——因为证据锚点的唯一零风险落点是 `tool/result.data.meta`，而 `meta` 的值来自工具执行器的返回值，第三方工具的 `meta` 不受我们控制 [E: GROUND-TRUTH-CORRECTIONS.md#A1, #E2；gt-evidence-substrate.md#B8]。
2. 判定必须在 **DSH 进程之外**——门要读原始 session JSONL、要跑 `git diff` 做 gate 完整性、要在全新临时目录里重跑分析脚本，这三件事都不在 DSH 的能力面上（见 §C 与 §E）。
3. 扇出必须走 **workflow**——它是五条并发路径里**唯一会排队而不是失败**的那条 [E: gt-orchestration.md#设计含义-1]；出厂 `subagent` 是 continuable，运行时**不设任何上限** [E: gt-orchestration.md#结论摘要-2]。
4. 散文是渲染层——见 01-CONTRACTS §0.1 与 §4 W-10。

### A.2 headless / 终端是一等运行面（用户硬要求 + 一手支撑）

用户要求「调试一律 terminal，WebUI 低效不完整」。这条要求与 DSH 的一手事实是**同向**的，不是妥协：

| 事实 | 一手依据 | 对本项目的意义 |
|---|---|---|
| headless bundle 只 patch `system-prompt` / `hmr` / `tools` 并 insert `code-runtime` / `headless-startup` / `headless-runner`，全文 35 行，**无 Host/HTTP** | [E: gt-profile-plugin.md#G7] | 攻击面最小；不引入 web 前端那一整套行 |
| headless bundle 把 `tools` 行的 config **整键替换**为 `mode: !!js process.env.DSH_TOOLS_MODE`；`dsh-base` 的 `tools` 行**根本没有 config**（注释原文：「omitting it here keeps the schema default (native)」） | 实测 R3：`@deepseek-ai/dsh-base/cordis.patch.yml:424`、`@deepseek-ai/dsh-headless/cordis.patch.yml`；`dsh --profile headless --dump-config` 输出带溯源注释 `# == @deepseek-ai/dsh-base, patched by @deepseek-ai/dsh-headless` | **「出厂呈现模式是 native」不是组合事实，是一个环境变量的函数**——〔裁定 · S0 实测，[E: .loop/m0/C-12a.json]〕更准确的说法是：**`native` 只是 `DSH_TOOLS_MODE` 未设时的 schema 兜底**。两侧运行实测：不设该变量时模型面无 `run_code`；`DSH_TOOLS_MODE=code` 时 `run_code` 可执行并读到 `node:fs`。**凡把「出厂 native」当固定事实承重引用的句子一律不成立**。见 §C 的 C-12a 与 §A.3 的 `tools` / `code-runtime` 两行 |
| headless bundle **insert 了 `code-runtime`**（`@deepseek-ai/dsh-code-runtime-worker-thread`），注释原文「Code Mode is a core execution capability, not a Web component」 | 同上（实测 dump 第 326–327 行） | Code Mode 的**执行能力在 headless 下是挂着的**，只是默认不呈现。要真正拿掉必须 `disabled: true`〔裁定 · S0 实测，[E: .loop/m0/C-12a.json]〕：出厂纯净组合的 dump 里 `code-runtime` 行确实在场；`tools.mode` 钉成字面量 `native` + `code-runtime: disabled` 后，父进程 `DSH_TOOLS_MODE=code` 失效（走到 `dsh: AUTH`）；而 mode 钉成 `code` 且 `code-runtime` disabled 会响亮启动失败。见 C-12a |
| headless profile **没有 `agent-presets` 行**（实测 `dsh --profile harvest-test --dump-config \| grep -c agent-presets` = 0；R3 复核：全安装树里只有 `dsh-web-app/cordis.patch.yml:421` 挂 `agent-presets`，config 为 `default: standard`） | [E: gt-profile-plugin.md#G7, #结论摘要-11] | 所有工具注册在**全局层**，子代理直接继承；**不需要处理 preset 的 mount 三条拒绝规则、generation 永不回收、CLI 覆盖 `roots`** [E: gt-profile-plugin.md#G2, #G3, #G6]。**同时**：`settings.yaml` 的 `agent-presets.default` 在 headless 下是**惰性**的（没有 roster 消费它）——这条把 C-12b 的威胁面从「preset 换 presentAs」收窄到「模型路由」 |
| headless 下**没有 approval answerer**，`ctx.approval` 解析为 `unavailable` → **fail closed** | [E: gt-exec-security.md#H-6, #G-1] | 批跑必须**预先**把权限放到位；我们的检索/取证工具**不得**依赖 `ctx.approval`（依赖即必然失败） |
| CLI 语法：`dsh --profile <name> [--patch <path>]* [app args...]`，launcher flag 必须在前，第一个不认识的 token 起全是 app 参数 | [E: gt-profile-plugin.md#H1] | 门脚本与 e2e 外壳可以稳定地拼命令行 |
| headless 与 web bundle 都把 `hmr` 行 `disabled: true`；CLI 会临时挂一个 watch-only 回退，监视 profile 与 home 的 patch 文件 | [E: gt-profile-plugin.md#H3] | 长跑期间改 `cordis.patch.yml` 会热生效——这是**运行中配置漂移**的入口，运行时指纹（01-CONTRACTS §4 W-12）必须记录实际生效值，不能只记文件 |

**〔裁定 A-1〕本项目不提供、也不依赖 TUI 作为独立运行面。** 本轮一手语料中**没有**任何独立于 headless 的 TUI 包或 profile 行的证据；`dsh web` 只是 `--profile web` 的别名 [E: gt-profile-plugin.md#H1]。因此「terminal 一等」在本文件里的准确含义是：**headless profile + 标准输出 + 门脚本的 CLI 报告**，不是一个交互式全屏界面。
**什么会推翻它**：若在安装树里读到一个提供终端交互面的包（且不是 `dsh-web-frontend` 的转发），则把它作为第三个 bundle 评估。**这条已列入 open questions。**

### A.3 profile 骨架（可直接抄，逐项标注证据强度）

目录形态（四个文件，第四个别碰）：

```
~/.dsh/profiles/academic-research/
  package.json          # dsh.profile.bundles 有序数组 + dependencies
  cordis.patch.yml      # 用户层 patch：并发闸、模型路由、角色实例、预算
  pnpm-workspace.yaml   # dsh plugin 生成；预留 overrides 位
  cordis.yml            # 每次启动被 CLI 无条件重写为 []，人不该编辑
```

依据：`initProfile` 只写前三个；`cordis.yml` 由 `prepareProfile()` 每次 `writeFileSync` 重写为固定常量，本机三个 profile 实测与该常量逐字一致（223 字节）[E: gt-profile-plugin.md#A2, #A3]。profile 名黑名单不含 `academic-research`，合法 [E: gt-profile-plugin.md#A1]。

**`package.json`**：

```jsonc
{
  "name": "dsh-profile-academic-research",
  "private": true,
  "dependencies": {
    // dsh plugin add 会把相对路径改写成绝对路径（anchorPathSpec）
    "dsh-academic-fetch": "file:/…/academic-research-plugin/packages/dsh-academic-fetch",
    "dsh-web-search-serper": "file:/…/serper-harvester/dsh-web-search-serper"
  },
  "dsh": { "profile": { "bundles": [
    "@deepseek-ai/dsh-base",       // 1
    "@deepseek-ai/dsh-headless",   // 2 —— 必须手工补，见下
    "dsh-web-search-serper",       // 3
    "dsh-academic-fetch"           // 4 —— 我们自己的 bundle，排最后
  ] } }
}
```

顺序的四条硬理由（**数组顺序即 patch 应用顺序**，[E: gt-profile-plugin.md#A4]）：

1. `dsh-base` 必须第一，它是所有行的来源。
2. **`@deepseek-ai/dsh-headless` 必须手工补进 `bundles`**：`dsh plugin --profile academic-research add <pkg>` 生成的 profile bundles 只有 `["@deepseek-ai/dsh-base"]`（`DEFAULT_PROFILE_BUNDLES`），headless 不是 `PROFILE_TEMPLATES` 里 `academic-research` 这个名字的模板 [E: gt-profile-plugin.md#A7]。补进去之后 `dsh plugin` 的 reconcile **既不会加也不会删**它，因为 in-box bundle 不是 dependency（代码注释原文：in-box bundles「are never touched」）[E: gt-profile-plugin.md#A8]。本机 `harvest-test` profile 就是这个活例。
3. `dsh-web-search-serper` 排在我们前面：它会 patch `id: web` 的 `searchProvider`。**两个 bundle 同时 patch 同一行时后者全胜且无任何警告**——本机 web profile 实测 bocha（第 3 位）与 serper（第 14 位）都 patch `id: web`，最终生效的是 serper [E: gt-profile-plugin.md#B5]。
4. `dsh-academic-fetch` 排最后，但**它绝不 patch `id: web`**（见 〔裁定 B-1〕），所以第 3、4 位之间不存在争夺。

**`cordis.patch.yml`（profile 用户层）**——它排在**所有 bundle 层之后**，是我们的最终仲裁位 [E: gt-profile-plugin.md#B1]：

```yaml
# ⚠️ patch 的每个顶层键是整体赋值，config 作为一个对象被整体换掉，没有深合并。
#    官方注释原文见 dsh-base/cordis.patch.yml:6-7。[E: gt-profile-plugin.md#B3, #B4]
# ⚠️ patch 匹配不到目标行 —— 静默失效是本机制的头号风险。[E: gt-profile-plugin.md#B3]
#
# 〔裁定 · S0 实测〕**「猜错 id = 静默失效」此前把两件相反的事混为一谈，必须分开写：**
#   ① **patch 的 entry id 猜错 = 真静默**（[E: .loop/m0/M0-3c.json]）。同一个 DSH_HOME、同一份写错
#      id 的 patch：`--dump-config` 报 2 条 `patch: entry "<id>" not found`，而**真实 boot 报 0 条**
#      （同次命令用 `dsh: AUTH` 证明 boot 确实跑到了 LLM）。即真实运行路径上**彻底静默**，
#      连 warn 都没有——「只 warn 不 fail」这个旧说法**低估了它**。
#      ⇒ 唯一能抓住它的地方是 `--dump-config` 的 stderr（§D.3 第 1 段，那条 grep 不可移动）。
#   ② **插件 `inject` 的服务名猜错 = 响亮失败**（[E: .loop/m0/M0-3a.json]）。`assertEntriesActivated()`
#      在 boot 末尾抛错、**退出码 1**，并逐字点名缺失的服务 `pending (waiting for service: <svc>)`。
#      它**不需要**任何门去抓——boot 自己就红。
#   ⇒ 本文件凡出现「猜 id / 猜名字 = 静默失效」的地方，一律按这条对照区分；把 ② 写成静默会让人
#      给一个已经会红的路径再造一道门，把 ① 写成响亮则会让人删掉唯一抓得住它的那条 grep。

# ── 0. 呈现模式与 Code Mode 执行能力：两道都必须显式写死（C-12a，R3 实测）
#    headless bundle 把 tools 行 config 整键换成 `mode: !!js process.env.DSH_TOOLS_MODE`。
#    不写这两行，本 profile 的呈现模式就由**启动进程的环境变量**决定，而 --dump-config
#    只会原样打印那个 !!js 表达式（实测：DSH_TOOLS_MODE=code 时 dump 输出逐字不变），
#    于是任何读 dump 的门都**无法知道实际生效值**。
- id: tools
  config:
    mode: native            # ← 写成字面量，env 接缝被本层整键替换掉；dump 里可 grep
- id: code-runtime
  disabled: true            # ← 结构性拿掉 Code Mode 执行能力（不是靠默认值藏起来）

# ── 1. 同 turn 兄弟工具调用的滚动池：显式写死，不吃出厂值
- id: agent-loop
  config:
    agents: []                 # ← base 里这行 config 就是 {agents: []}，整体替换必须写回来
    maxParallelToolCalls: 4    # 〔裁定〕见 §E.1

# ── 2. 角色实例：一个角色 = 一个独立命名的 subagent 工具实例
#    Child policy is fixed per instance —— 换模型/persona/toolFilter/深度都要换一个工具名。
#    [E: gt-orchestration.md#D3(a)]
- id: tool-subagent           # 出厂：provider: spawn / toolName: subagent / backgroundMode: continuable
  config:
    provider: spawn           # ← subagent 传输后端（见 01-CONTRACTS §9.25）
    toolName: subagent
    backgroundMode: one-shot  # 〔裁定〕见 §E.2
    maxDepth: 3
    agentOptions: { provider: deepseek-official, model: deepseek-v4-flash }

- id: tool-subagent-fork      # 出厂 base 是 one-shot；三个 shipped preset 却是 continuable
  disabled: true              # 〔裁定〕本 profile 不用 fork（取证子代理必须零父历史，01-CONTRACTS §5.3）

- id: tool-ralph
  disabled: true              # 〔裁定〕见 §E.3

# ── 3. code-runtime 预算：显式写死，不沿用包默认值
- id: code-runtime
  config:
    computeMs: 60000
    maxWallMs: 600000
    maxOutputBytes: 67108864
    maxOldGenerationSizeMb: 512

# ── 4. spill 阈值与 pruner：显式重述出厂值，让漂移在 diff 里可见
- id: spill-policy
  config: { maxInlineBytes: 50000 }
- id: tool-result-pruner
  config: { thresholdChars: 8192, headChars: 4096, tailChars: 1024 }

# ── 5. web 的最终仲裁（我们只做兜底，不抢学术检索）
- id: tool-web
  config: { fetch: false, searchTimeoutMs: 60000, searchMaxResults: 8 }

# ── 6. workflow 引擎的并发闸必须显式写死，不能吃 CPU 推导值
#    〔裁定 · S0 实测，[E: .loop/m0/M0-3c.json]〕workflow 是**两行**，都来自 @deepseek-ai/dsh-base，
#    id 已实测确认、可直接写死（不再需要「落地前先 dump 读 id」这一步）：
#      引擎行     id: workflow-worker-thread   name: '@deepseek-ai/dsh-workflow-worker-thread'  出厂 config: {provider: spawn}
#      模型面工具行 id: tool-workflow            name: '@deepseek-ai/dsh-tool-workflow'           出厂无 config
#    命中判据（实测）：patch 后 `--dump-config` 里 `patch: entry` 计数 **= 0**，
#    且目标行上方出现溯源注释 `# == @deepseek-ai/dsh-base, patched by <本文件>`，且该行的值确实变了。
#    ⚠️ 打不中的后果比 v1 写的更坏：**真实 boot 路径上完全静默**（详见本节顶部的对照裁定与 §D.3 第 1 段）。
- id: workflow-worker-thread
  config: { provider: spawn, maxConcurrentAgents: 6, maxTotalAgents: 1000, maxItemsPerCall: 4096 }
#    ⚠️ `tool-workflow` **不 disable**：〔裁定 B-4〕把 workflow 定为批量扇出的唯一入口，
#    这扇 P0 门是本架构要求打开的（C-12c）。且实测残余：**「打中 tool-workflow 且 disabled: true 后
#    workflow 工具是否真的从模型面消失」未验证**——M0-3c 只证明了 dump 里 `disabled: true` 生效，
#    模型面的消失是推断。谁将来要靠 disable 它来收口，必须先补这个实验。
```

**四条必须随骨架一起说的话**（第 1、2 条在 R3 被改写——旧文本把 profile 层叫「最终仲裁位」并把机器级威胁钉在了错误的文件上）：

1. **profile 的 `cordis.patch.yml` 不是最终仲裁位。** 实测的完整层序是
   `bundle 层（bundles 数组顺序）→ profile 的 cordis.patch.yml → $DSH_HOME/cordis.patch.yml → --patch overlays → telemetry 开关`
   （`@deepseek-ai/dsh/lib/profile-boot-DG5t9aNs.js` 的 `composeProfile` / `allPatches`，函数文档逐字：home 层「machine-local preferences that apply to every profile, so it outranks the per-profile layer」）[E: gt-profile-plugin.md#B1；R3 实测同一文件]。
   → 我们只在**最后两层不存在**的前提下才是最终仲裁者。boot 门必须把这个前提断言成事实（§D.3 第 1 段）。

2. **机器级偏好的真实载体是 `$DSH_HOME/settings.yaml`，不是 `$DSH_HOME/cordis.patch.yml`**〔R3/C-12b 改写〕。
   两个文件都真实存在于层序里，但**威胁不成比例**：
   - `$DSH_HOME/cordis.patch.yml` 本机**不存在**（`loadOptionalPatches` 遇 ENOENT 返回无层），且一旦存在会在 `--dump-config` 里现形。
     〔裁定 · S0 实测，[E: .loop/m0/C-12b.json]〕**「不存在 ⇒ 断言恒真 ⇒ 可以删」这个推理是错的，理由必须写死在这里**：
     实测该文件**一旦存在就压过 profile 自己的 patch 层**——不是并列、不是先于。同一个 DSH_HOME 里两层都写 `agent-default-model.model`，
     profile 层写 `FROM-PROFILE`、home 层写 `FROM-DSHHOME`，dump 的最终值是 `FROM-DSHHOME`，溯源注释按施加顺序列出两者
     （`# == @deepseek-ai/dsh-base, patched by <profile>/cordis.patch.yml, <home>/cordis.patch.yml`）。
     → **威胁强度上它能整键改掉我们钉死的任何一行**，包括 §A.3 第 0 块的 `tools.mode` 与 `code-runtime: disabled`。
     它与 `settings.yaml` 的真实区别**不是「弱」，是「可观测」**：它会在 dump 里现形，settings 不会。
     所以 §D.3 第 1b (i) 那条断言的价值不在「它今天会不会红」，而在「它把一条能整键翻掉全部 pin 的层钉成了不存在」——
     **今天恒真恰恰是它该在的理由，不是删它的理由**。
   - `$DSH_HOME/settings.yaml` **本机存在**（R3 实测 1271 字节），由 `dsh-base` 的 `settings` 行（`@deepseek-ai/dsh-settings-file`）挂载，因此**每个 profile 都吃它**，`watch: true` **热重载**，且分层是「schema 默认 → 组合层 base → 用户文档 section」——**用户文档在最上面**，直接覆盖我们写在 `cordis.patch.yml` 里的组合值 [E: gt-profile-plugin.md#D4；R3 实测 `@deepseek-ai/dsh-settings-file/README.md`]。
   - **它对 `--dump-config` 与 `--dump-default-config` 双双不可见**：两个 dump 打印的都是**插件树**，settings 是运行时叠加在树之上的另一层。R3 实测本机 `settings.yaml` 里就带着 `agent-default-model: {provider, model, reasoningEffort}`（模型路由）、`ya-subagent.profiles[].model` 与 `maxDepth`（子代理路由与深度）、`llm-pi-ai.providers`（**活体注册全新的 provider 路由**）、`agent-presets.default`、`auto-compact.thresholds`。
   → 旧文本让 boot 门去断言 `cordis.patch.yml` 不存在。**那道断言检查的是错误的对象**：本机它恒真，而真正能静默改掉模型路由的那个文件门根本没看。正确断言见 §D.3 第 1 段（两个文件都断言，且 `settings.yaml` 走**值级白名单 + 哈希入 manifest**，不是「必须不存在」——它是用户合法的模型选择入口，禁止它就是禁止用户配模型）。

3. **`--dump-config` 不是 boot 真值，而且在 `!!js` 行上连配置真值都不是。**
   已知它少了 CLI 注入的 `agent-presets.roots` 覆盖与 telemetry disable patch 两层 [E: gt-profile-plugin.md#H2, #G6]。
   R3 补一条更狠的：**dump 原样打印未求值的 `!!js` 表达式**。实测 `DSH_TOOLS_MODE=code dsh --profile headless --dump-config` 的 `tools` 行输出与不设该变量时**逐字相同**（都是 `mode: !!js process.env.DSH_TOOLS_MODE`）。
   → 凡是取值来自 `!!js` 的行，**读 dump 的门对它的实际生效值一无所知**。唯一的修法是让我们自己的层把它替换成字面量（§A.3 第 0 块），此后 dump 里出现的就是可 grep 的 `mode: native`（R3 实测：加 `--patch` 后 dump 第 309 行变为 `mode: native`）。
   任何把 dump 当验收证据的门都是**配置层空心门**（gt-house-method 记录的同一失败类已连中三次，见 §D.5）。

4. **第 0 块的两行都经过真实 boot 验证，不是纸面推理**（R3 实测，用故意无效的密钥；〔裁定 · S0 实测，[E: .loop/m0/C-12a.json]〕**S0 在一个干净的临时 `DSH_HOME` 里独立复核，两条都复现**——钉成字面量 `native` 后父进程的 `DSH_TOOLS_MODE=code` **不再起作用**，钉成 `code` 且 `code-runtime: disabled` 则响亮启动失败）：
   - `tools.mode: native` + `code-runtime: disabled` → `dsh --profile headless --patch <pin> "noop"` 退出码 1，stderr 唯一一行是 `dsh: AUTH: Authentication Fails, ...`。**树装得起来**，headless runner 不依赖 `ctx.codeRuntime`。
   - `tools.mode: code` + `code-runtime: disabled` → 退出码 1，stderr 逐字为
     `dsh: UNKNOWN: dsh-tools: mode "code" requires a code runtime — load a ctx.codeRuntime implementation (e.g. @deepseek-ai/dsh-code-runtime-worker-thread) or set tools mode to "native"`。
   → `code-runtime: disabled` 把「Code Mode 被打开」从一个**静默的呈现变化**变成一次**响亮的启动失败**。这是本轮唯一一条真正结构性的收口，它给出了 §D.4 的第六个红样本。

### A.4 自建插件包骨架（照抄本机 serper 插件，逐项标注哪些是抄来的）

样板：`~/playground/dsh-projects/serper-harvester/dsh-web-search-serper/`，文件清单 `package.json` / `cordis.patch.yml` / `lib/index.js`（接线层）/ `lib/provider.js`（纯逻辑）/ `test/unit/*.test.js` / `README.md` / `LICENSE` [E: gt-profile-plugin.md#D]。

```jsonc
// packages/dsh-academic-fetch/package.json
{
  "type": "module",
  "main": "lib/index.js",
  "exports": { ".": {"default": "./lib/index.js"}, "./cas": {...}, "./package.json": "./package.json" },
  "files": ["lib/", "cordis.patch.yml", "README.md", "LICENSE"],   // ← cordis.patch.yml 必须列进 files
  "dsh": { "bundle": { "patch": "./cordis.patch.yml" } },          // ← 声明自己是 bundle 的唯一方式
  "peerDependencies": {                                            // ← 宿主包一律 peer
    "@deepseek-ai/cordis": "^4.0.1",
    "@deepseek-ai/dsh-credentials": "^0.1.0-rc.5",
    "@deepseek-ai/dsh-settings": "^0.1.0-rc.5",
    "@deepseek-ai/dsh-tools": "^0.1.0-rc.5"
  },
  "dependencies": { "@deepseek-ai/schemastery": "^3.18.1" }
}
```

```yaml
# packages/dsh-academic-fetch/cordis.patch.yml —— 只做一件事：把自己插进树
# 顶层 insert（无 id）追加到顶层列表末尾；插入的行立刻进 id 索引，
# 所以 profile 的 cordis.patch.yml 可以按 id 覆盖它。[E: gt-profile-plugin.md#B3]
- insert:
    - id: academic-fetch          # ← 这个 id 就是 boot 门第 1 段要 grep 的那个
      name: dsh-academic-fetch    # ← name 一经写入无法被任何 patch 改写
      config:
        rateGatewaySocket: ~/.dsh/academic-research/gateway.sock
        casRoot: .arc/objects
```

⚠️ **它不 patch `id: web`**，因此与 serper bundle 无争夺（〔裁定 B-1〕、E-28）。

四条纪律，全部有一手代价证据：

1. **`cordis.patch.yml` 必须列进 `files`**，否则发布后 `loadOverlayPatches` 因文件缺失直接 throw（bundle 的 patch 文件走的就是这条「不存在也 throw」的路径）[E: gt-profile-plugin.md#D1, #B7]。
2. **宿主包一律 `peerDependencies`**，靠 `$DSH_HOME/profiles/node_modules` 的扁平回退解析到宿主同一实例 [E: gt-profile-plugin.md#A6, #D1]。违反的代价有活体记录：`@shijunan123/dsh-subagent-effort@0.4.2` 把 `@deepseek-ai/dsh-tools` 写成 regular dependency，pnpm 装了第二份副本，宿主的工具分发器解析到错误模块实例，**每一次工具调用都死于 `Cannot read properties of undefined (reading 'prepare')`**；解法是在 `pnpm-workspace.yaml` 里写 `overrides: '@deepseek-ai/dsh-tools': link:<宿主路径>` [E: gt-profile-plugin.md#D6]。
3. **四个导出：`name` / `inject` / `Config` / `apply`** [E: gt-profile-plugin.md#D3]。⚠️ **`Config` 是纪律不是机制**：`cordis/lib/index.js:956` 是 `if (!runtime.Config) return config;`，没有 `Config` 的插件**不会崩** [E: GROUND-TRUTH-CORRECTIONS.md#A4]。所以「每个自建插件都导出了 `Config`」必须由我们自己的门检查（§D.3）。
   ✅ **`inject` 的服务名已实测闭合**〔裁定 · S0 实测，[E: .loop/m0/M0-3a.json]〕。注册模型面工具的服务名是 **`tools`**（`ToolRuntime` 的 **ctx key**，**不是类名** `ToolRuntime` / `toolRuntime`），逐字写死：

   ```js
   export const inject = ['tools'];   // ← 承重的那一行：ctx key，不是类名
   ```

   正负两例是同一份插件、同一个 profile、**只改这一个字符串**跑出来的：写 `['toolRuntime']` 时 boot 逐字报 `pending (waiting for service: toolRuntime)` 并**退出码 1**；写 `['tools']` 时插件树装得起来（用无效密钥探针跑到 `dsh: AUTH`），且该工具被模型真实调用并返回 `M0-INJECT-PROBE-ALIVE`。
   两条随之钉死的安装纪律（同一实测）：profile 的 `package.json` 里 `dsh.profile.bundles` 追加包名、`dependencies` 追加该包；插件自己的 `cordis.patch.yml` **必须**用 `- insert:` **列表**形式（bare mapping 会在 boot 失败）。
   ⚠️ **一条前提被同一实测推翻**：`inject` 猜错**不是**静默 PENDING。`dsh-app-boot` 的 `assertEntriesActivated()` 在 boot 末尾**无条件**枚举未激活 entry、抛错、退出码 1，并**逐字点名缺失的服务**。这与 patch 的 entry id 猜错是**两件相反的事**，见 §A.3 顶部的对照裁定。
   ⚠️ **残余**（M0-3a honest_limits）：① 只在 `dsh --profile headless` 的 **CLI boot 路径**验证；web profile 与 **HMR 热重载路径**（headless 下 `hmr` 行被 bundle disabled）**未测**，热重载期的 inject 失败是否同样响亮**未知**。② 只对 `tools` 一个服务名做了正负两例实跑；实测记录附的 16 个 ctx key 对照表（`sessions` / `subagents` / `fs` / `systemPrompt` / `skills` / `subprocess` / `sandboxPolicy` / `tokenMeter` / `llm` …）来自 README 标题与编译产物中的 `inject = [...]` 字面量，**属于代码阅读，未逐个运行验证**。③ **该对照表里没有凭据解析服务**——本条只闭合了「工具注册」那一半，`ctx.credentials` 的 inject 名仍未实测，**落地前不得凭记忆写**，仍在 open questions。
4. **用 `@deepseek-ai/schemastery` 而不是 zod**：代码只要求 Standard Schema v1（`Config["~standard"].validate`，且**必须同步，异步会抛 `TypeError`**），zod v3.24+/v4 理论满足；但 DSH 另有两处依赖 schemastery 专有能力（loader 写回配置时的 `Config.simplify`、`dsh-settings` 的 `schema.toJSON()` 与 `role('secret')` 遍历），**用 zod 在这两条路上会退化到什么程度未在本机验证** [E: gt-profile-plugin.md#C1, #未决-1]。

**环境变量纪律**：`DSH_*` / `XDG_*` / `DYLD_*` / `BASH_FUNC_*` 前缀的一切**不能**写进 `.env`（写了直接 throw），必须 `export`；学术 API 的密钥（`OPENALEX_API_KEY` / `CROSSREF_MAILTO` / `S2_API_KEY` / `SERPER_API_KEY` …）可以放 `$DSH_HOME/.env` 或项目 `.env`，并用 `Config` 的 `.role('credential-ref')` + `ctx.credentials.resolve()` 取 [E: gt-profile-plugin.md#H4, #设计含义-7]。

---

## §B 模块分拆

> 每个模块回答四件事：**职责 / 为什么必须是插件（或必须不是）/ 验收方式（含它的红样本）/ 它依赖谁**。
> 「验收方式」一律附**红样本**——一个不会红的门是空心门（01-CONTRACTS §6.5.1；00-PREMISE B8）。

### B.0 模块总表

| id | 名称 | 形态 | 写权（见 01-CONTRACTS §4） | 建造序 |
|---|---|---|---|---|
| **M0** | 架构可行性前置件 | 一次性脚本 + fixture | 无（只读断言） | 1 |
| **M1** | 学术检索与取证插件 `dsh-academic-fetch` | **DSH 插件（bundle）** | W-01 / W-02 / W-06 | 4 |
| **M2** | 证据底座（CAS + manifest + schema） | **纯 Node 库 + CLI，不是插件** | 提供 W-01/W-05/W-06 的物理写入原语 | 2 |
| **M3** | 门脚本集 `checks/` | **纯脚本，绝不是插件** | W-04 / W-05 / W-08 | 3（GC-0）→ 6（GC-1）→ 8（GC-2 聚合器） |
| **M4** | 研究编排 | **workflow 脚本 + 多实例 subagent 工具行，不是 agent preset** | W-12 / W-13 / W-15 | 7 |
| **M5** | 评测轨 | 独立脚本 + held-out 题集（见 §9.26） | 只读 | 9 |
| **M6** | 攻击轨 | fixture 集 + battery 编排 | 只读（除自己的台账） | 8 |
| **M7** | 薄散文出口（确定性组稿器） | 纯脚本 | W-10 | 10 |
| **M8** | 回归外壳 | shell + mjs e2e | 无 | 5 |

### B.1 M0 · 架构可行性前置件

**职责**：把三件「失败即改架构」的事在写第一行产品代码之前跑掉。

1. **RT-5：PDF 抽取管线能否把白字/极小字号文本归入 `non_rendered_text`。** 这是 01-CONTRACTS §7.2.2 显式标注的**可能推翻通道分离的前提**，V7.8 把它定为「必须先解决的架构前提，不是一条普通失败用例」。理由：野外普查显示 70.0% 的注入落在非渲染通道，而 PDF 恰是学术场景的主要摄取对象 [E: ext-security-injection.md#V5；01-CONTRACTS §7.2.2]。
2. **多帧 zstd 解帧器**：session JSONL 落盘是**多个独立 zstd frame 串接**，Node 内置 `zlib.zstdDecompressSync` / `createZstdDecompress` **只解第一帧**（实测：得到 1 行，实际 3675 行）[E: GROUND-TRUTH-CORRECTIONS.md#A3；gt-evidence-substrate.md#H3]。所有读日志的门都建在这个解帧器上，它必须最先存在且最先被红样本证明。
3. **五条加载期不变量的 boot 门骨架**（详见 §D）。

**为什么不是插件**：它不进产品运行路径，只在建造期跑。

**验收（红样本必须先红）**：
- RT-5 红样本：一份**故意含白字注入**的 PDF；若管线把该段文字放进 `rendered_text`，M0 判失败，**架构进入重议**，不是「记一条 TODO」。
- zstd 红样本：一个含 **≥2 个 frame** 的固定 fixture，用 Node 内置 API 读必须只得到第一帧的行数（证明陷阱存在），用我们的解帧器读必须得到全部行（对应 01-CONTRACTS §8.7 V6.6）。
- boot 门红样本：**六个**故意坏掉的插件 fixture，每个必须让 boot 以**对应的**失败文案退出（§D.4）。

**依赖**：无。**它是唯一可以先建的模块。**

### B.2 M1 · 学术检索与取证插件 `dsh-academic-fetch`

**职责**（一个包，四个工具面）：

| 工具面 | 做什么 | 契约锚点 |
|---|---|---|
| 学术检索 | OpenAlex / Crossref / arXiv / Europe PMC / DOAJ 的结构化查询，返回带 DOI/venue/作者/引用数的**结构化 canonical output** | `evidence_grade` 见 §3.3；候选 ≠ 证据见 §9.6 |
| 取证抓取 | 抓取 → **通道分离**（`rendered_text` / `non_rendered_text` / `structured_data` / `http_headers`）→ 抽取 → **在同一次工具执行内**写 CAS → 返回 `meta.evidence` 锚点 | §4 W-01 / W-02 / W-06；§7.2.2 |
| 留存分档 | 在 **fetch 时刻**按降级触发器决定 `retention_tier` 并写进 provenance | §8.6 / §8.6.3 |
| 限速网关客户端 | 一切外呼经中央网关；按 host 分桶 | §6.3 硬要求 5 |

**为什么它必须是插件**（三条，全部是「不做成插件就拿不到」的能力）：

1. **`tool/result.data.meta` 的值只能来自工具执行器的返回值**（`...result.meta !== void 0 ? { meta: result.meta } : {}`）[E: gt-evidence-substrate.md#B8]。它对模型不可见、被 pruner 的替换**完整保留**（`...event.data` 展开）、被持久化逐字保留、事件类型已知因而不影响 resume——这是 01-CONTRACTS §4 W-02 选它作为**唯一零风险落点**的四条理由 [E: gt-evidence-substrate.md#B8, #D4, #B4]。
2. **产物级兜底需要 `tool/call` 事件覆盖**：01-CONTRACTS §4.4 的兜底是「任何未被 `tool/call` / `tool/code-dispatch` 事件覆盖的断言一律 `not_covered`」。只有进程内注册的工具才产生这些事件。
3. **`sourceEventSeqs` 的天然绑定**：自定义 log-only 事件**无法**用 `sourceEventSeqs` 引用它所依据的 `tool/result` seq（运行时直接抛错，实测），而 `tool/result` 与 `tool/call` 的 seq 绑定由核心校验保证 [E: gt-evidence-substrate.md#A6, #B8；01-CONTRACTS §8.2]。

**〔裁定 B-1〕学术检索绝不做成 `WebSearchProvider`。**
理由有二，都是一手的：① 缝的语汇不够——`WebSearchRequest` 只有 `{query, maxResults?}`，`WebSearchSource` 只有 `{url, title?, snippet?, publishedAt?}`，**没有 DOI / 作者 / venue / 引用数**，学术元数据塞进去就丢 [E: gt-exec-security.md#E-1, #E-2, #F-5]。② 位置只有一个——`web.searchProvider` 是单一字段，装两个搜索 bundle 会**静默互相顶掉**且顺序即命运 [E: gt-profile-plugin.md#B5]。
**正确形态**：自有 `ctx.tools.register` 工具，带强制的 `output { schema, render }` 声明 [E: gt-profile-plugin.md#E1]。`ctx.web.search()` 保留为通用兜底，但要接受一次搜索 = 一次完整 Messages 模型调用的代价，且出厂 `searchMaxResults` 为 8 [E: gt-exec-security.md#E-5, #E-7]。
**什么会推翻它**：若 DSH 给 `WebSearchSource` 加了结构化元数据臂（该缝的 doc 明说 recency/domain 过滤是 deferred work，说明这些字段确实在演进中 [E: gt-exec-security.md#E-4]），则重新评估。

**自建义务清单见 01-CONTRACTS §8.5**，本文件只补它未覆盖的落点：这些代码住在 M1 的 `lib/net/` 下，且必须在 `tools/pre-execute` 而非 `execute` 内判定——因为 T0-HARD 的语义是「不发请求」而不是「请求后丢弃」（§8.6.3），只有 pre-execute 能在请求发出前否决。官方不挂 fetch provider 的理由原文是「that provider defers SSRF protection and the model would choose the request target」[E: gt-exec-security.md#E-6]。**本机没有任何 fetch provider 包，`web_fetch` 出厂关闭，`WebFetchBody` 是 `html | text` 的封闭联合、无 PDF 臂** [E: gt-exec-security.md#E-3, #E-6]。

**并发声明**：落盘类工具**必须**声明 `isConcurrencySafe: () => true` 才能吃到滚动池的并行红利；安全契约原文要求「不改父级状态、共享状态可交换或安全失败」——**内容寻址写盘天然满足可交换性** [E: gt-profile-plugin.md#E3, #设计含义-4]。注意 `isConcurrencySafe` 是 fail-closed 的：未知/未声明/参数非法/抛异常一律 exclusive [E: gt-profile-plugin.md#结论摘要-8]。

**验收**：
- 正向：一次抓取产生 ①CAS 里的字节 ②`evidence/<id>.json` ③`tool/result.data.meta.evidence` 三者哈希一致（对应 §8.7 V4.6、V8.3）。
- **红样本 1（反伪造）**：构造一条 `evidence` 记录，其 `object_sha256` 在 CAS 中不存在 → 门必须红（V4.6）。
- **红样本 2（通道分离，RT-4）**：一个页面在 HTML 注释、`<meta>`、`alt`、`aria-label`、`display:none`、零尺寸元素、屏外定位、JSON-LD、HTTP 响应头各放一条注入；期望九条**全部**落入 `non_rendered_*`、**零条**进入可引用证据池、告警计数 = 9（§7.4 V7.5）。
- **红样本 3（T0-HARD）**：给一个影子图书馆域名 → 抓取日志中**不得出现对该域名的请求**（是「不发请求」，不是「请求后丢弃」）；且 401/403 后**不得有换 UA 重试记录**（§8.7 V8.12）。
- **红样本 4（空集不得通过）**：零次抓取的 run，证据门必须红。空集静默通过是本仓库已实证的盲区（`selftest_fidelity.mjs` 的 EMPTY-RUN 红样本）[E: gt-house-method.md#M5]。

**依赖**：M2（落盘原语）、M0（通道分离可行性）。

### B.3 M2 · 证据底座（CAS + manifest + schema）

**职责**：`objects/<sha[:2]>/<sha256>` 内容寻址 + 原子 rename；`claims/` `evidence/` `verdicts/` `gate-reports/` `registries/` 的 JSON Schema；`inferences/*.md` 的 front-matter schema；台账格式门的判定函数。布局是规范的，见 01-CONTRACTS §8.1。

**〔裁定 B-2〕M2 是纯 Node 库 + CLI，不是 DSH 插件。**
理由：门由 conductor 在 **DSH 进程之外**执行（房内纪律：`checks/` 归 conductor 所有、gate 由 conductor 执行、绝不由产物作者执行）[E: gt-house-method.md#A6]。若 CAS 与 schema 只存在于插件的 `apply()` 里，门就无法独立复核台账——那正是 01-CONTRACTS §4 W-04/W-05/W-08 要求「门代码是唯一物理写者」的反面。M1 插件 `import` 这个库，门脚本也 `import` 这个库，**同一份代码两个宿主**。
**代价（必须认账）**：两个宿主意味着两个版本可能漂移。**对策**：M2 导出一个 `LAYOUT_VERSION` 常量，M1 在 `apply()` 里断言、门在第一行断言，不一致即红。**这条对策本身要有红样本**（故意错版本 → 双边都红）。
**什么会推翻它**：若门最终被迫在 DSH 进程内执行（例如需要 `ctx.` 上的某个服务），则 M2 要退化成插件并额外提供进程外的只读复核路径。

**为什么不用仓库级锁工具**：见 01-CONTRACTS §8.3（D-8.3）。并行安全性来源见 §4.5。

**验收**：
- 并行压测：N 个并发写者同时写 CAS 与 `claims/`，结束后无损坏文件、无合并冲突、CAS 中相同内容只有一份（§8.7 V8.7）。
- **红样本**：台账格式门必须对一个**截断的 / 含重复小节的**台账文件判红。这条不是假想——本仓库自己的 `r1-ledger.md` 就有截断与重复小节，R3 把 "ledger garble" 记为 P3 [E: GROUND-TRUTH-CORRECTIONS.md#D3]。
- **红样本**：`claims/<id>.json` 里出现 `status` 字段 → schema 校验必须拒绝（§4.6 V4.1 的静态一半）。

**依赖**：无（可与 M0 并行建造）。

### B.4 M3 · 门脚本集 `checks/`

**职责**：把 01-CONTRACTS §1.5 的状态函数 `S` 与 §6 的门实现出来。按 §6.1 分三类落三个物理子目录——**成员清单不在本文件复述**：

| 子目录 | 成员 | 是否允许发网络请求 | 是否读 `verdicts/` |
|---|---|---|---|
| `checks/gc0/` | 见 01-CONTRACTS §6.2 | **否**（CI 里用禁网沙箱强制） | **否** |
| `checks/gc1/` | 见 01-CONTRACTS §6.3 | 是，且每个输出必须带 `data_as_of`（§6.6 V6.3） | **否** |
| `checks/gc2/` | 只有聚合器，边界见 01-CONTRACTS §6.4 | 否 | **是**（这是它与前两类的唯一物理区别） |

「是否读 `verdicts/`」这一列是**可 grep 的目录级不变量**：`checks/gc0/` 与 `checks/gc1/` 下任何 `verdicts` 字样即门红。这把 §6.1 的分类从文档纪律变成一条静态检查。

**为什么它必须不是插件**（四条）：

1. **gate 完整性依赖 git，而且依赖一个仓库外的入口**：`git status --porcelain -- checks/` 干净 **且** 工作树 `checks/` 与从 **40 位 commit sha** 展开的 pinned 副本逐文件 sha256 相同（规范表述见 01-CONTRACTS §9.22）。这是文件系统与版本控制层的事，与 DSH 无关。〔裁定 · S0 实测，[E: .loop/m0/M0-7.json]〕**锚点不许写成 tag**：实测 git 2.55.0 上服务端 `receive.denyDeletes` 与 `receive.denyNonFastForwards` 对 `refs/tags/*` **全部不生效**（tag 的非快进强推与删除都 ACCEPTED，同一次实验里 `refs/heads/*` 双双 REJECTED），且默认 `core.logAllRefUpdates=true` 时 tag 连 reflog 都不写（0 条）——**tag 可被重指且不留痕**。本仓库那 22 个 `gates-baseline-*` tag 因此**不承担锚点职责**（其中带 PGP 签名的是 0 个，`gates-baseline-22` 已退化成轻量 tag，对象类型 `commit`），它们至多是人类可读的发布标记。该校验**至今零代码实现**，目前完全靠 conductor 自觉 [E: GROUND-TRUTH-CORRECTIONS.md#D1；gt-house-method.md#A7, #A8]。**v2 必须把它写成真脚本**（00-PREMISE B8 的第一条前置代码），但**写成脚本不等于补上洞**——写在 `checks/` 里的脚本从仓库内入口调用时可被一行 `echo` 替换掉（红样本 R3，见 §B.9）。
2. **门要读原始 session JSONL**——多帧 zstd、`decodeStorageRecord`、`surfaceOp === 'append'` 过滤三个地雷（§6.5.4）。这三件事在 DSH 进程内做反而更难（进程内只有活体 session 的内存视图）。
3. **重跑门要在全新临时目录里跑 `uv sync --frozen` + 禁网沙箱**（§2.1）。DSH 的沙箱**不管网络**（bwrap 参数无 `--unshare-net`，Seatbelt profile 是 `(allow default) (deny file-write*)`，Landlock 只表达路径 grant）[E: GROUND-TRUTH-CORRECTIONS.md#A7；gt-exec-security.md#结论摘要-1]。禁网必须由**我们自己的 OS 级沙箱 profile** 提供。
4. **门是 `status` 的唯一物理写者**（§4 W-04）。把它放进插件，等于把写者放进模型可触达的进程——即使模型触达不到那个函数，**审计上无法区分**。

**GC-2 的边界必须在目录结构上可见**：`verdicts/<gate_id>/<claim_id>.json` 由裁决子代理自己写（§4 W-07），`checks/gc2/` 只读它。**裁决是门的输入，不是 status**（§9.11）。任何在 `checks/gc0/` 或 `checks/gc1/` 里读 `verdicts/` 的代码都是缺陷，可用一条 grep 门检测。

**验收**：
- 每个门在 CI 中有对应的 red-case fixture，且该 fixture 使门非零退出（§6.6 V6.4）。
- **红样本（继承的最刺眼一条）**：向重跑门喂一个伪造 metric、无 transform、无原始数据的 claim，门必须非零退出。前代同样的构造得到 **exit 0 PASS**——那是文档宣称「门重执行」而 `rigor_gate.py:189` 只比对 metric 文件的结果 [E: GROUND-TRUTH-CORRECTIONS.md#C1；01-CONTRACTS §2.5 V2.5]。
- **红样本（跨帧）**：含 ≥2 个 zstd frame 的 fixture，只读到第一帧即失败（§6.6 V6.6）。
- **红样本（gate 完整性活着）**：**必须构造一次真实篡改**让 `gate_integrity` 非零退出。00-PREMISE B8 明写「gate-integrity 脚本从未在真实 run 中触发过一次非零退出」需要被证明它活着——**没触发过 ≠ 有效**。〔裁定 · S0 实测，[E: .loop/m0/M0-7.json]〕这条已有跑通的电池，**并且实测把「一次篡改」的下限抬高了**：只篡改一个普通 check 不够，必须包含「**把 `gate_integrity.sh` 自身换成假货并同步补上台账行**」这一格，且**两个入口都要跑**。验收断言（退出码，可机器判定）：干净仓库两个入口皆 `0`；普通 check 被改但未提交 → `2`；已提交 → `3`；`gate_integrity.sh` 自身被替换 + 台账被补 → **仓库外 pinned runner 必须 `3`**。同一格从仓库内入口调用实测为 `0`（被骗过），该值按**已知洞的存档值**记录，**不作为验收断言**——它将来变成非零是能力提升，不是回归。
- **符号执行 `S`**：对第 2 步全部规则断言输出状态不高于输入（§1.6 V1.3）。这条是**纯静态**的，不需要跑数据。

**依赖**：M2（读台账）、M0（zstd 解帧器）。GC-1 子集额外依赖注册表同步器（§4 W-09）。

### B.5 M4 · 研究编排

**职责**：把一次研究任务拆成「覆盖率扇出 / 同一断言的 N 路独立核验 / 上下文卫生」三类允许的并行（00-PREMISE B1 裁决），并且**禁止**把论证链构建、跨 claim 一致性推理、最终裁决扇出去。

**〔裁定 B-3〕M1 阶段用 workflow 脚本 + 多实例 `dsh-tool-subagent` 行，不用 DSH agent preset。**
理由三条：① headless profile 根本没有 `agent-presets` 行，工具在全局层、子代理直接继承 [E: gt-profile-plugin.md#G7]；② 走 preset 要吃下三个代价：mount 的三条拒绝规则、generation 永不回收、CLI 无条件覆盖 `roots` [E: gt-profile-plugin.md#G2, #G3, #G6]；③ **headless 下 `agent-presets` 能否手工 insert 并被真正 mount 未验证**——headless runner 创建 Agent 的路径是否会调 `agentPresets.mount` 没有代码确认，若不调，那行插件就是死重量 [E: gt-profile-plugin.md#未决-5]。
**角色差异用什么表达**：每个角色一个独立命名的 `dsh-tool-subagent` 实例（`toolName` + `agentOptions.{provider, model}` + `persona` + `toolFilter` + `maxDepth` 全部 per-instance 固定）[E: gt-orchestration.md#D3(a), #D1]。README 原话：「Child policy is fixed per instance — another model, persona, tool filter, or depth cap requires another distinctly named tool.」
**什么会推翻它**：若实测确认 headless 下 preset 能被 mount，且我们需要「不同角色看到不同工具集」这一强隔离（而 `toolFilter` 不够——它**不是权限天花板**且**不向下传递** [E: gt-exec-security.md#B-1~B-4]），则切 preset 路线。

**跨厂商独立性的落点**（这是本轮最有价值的机会项）：workflow 脚本的 `agent(prompt, opts)` 支持**五个**选项 `label, phase, schema, provider, model`（`SUPPORTED_AGENT_OPTIONS`），其中 `provider` 映射到 `agentOptions.provider`（**LLM 路由**）[E: GROUND-TRUTH-CORRECTIONS.md#A11, #E1；gt-orchestration.md#D3(b), #X4]。这让 01-CONTRACTS §5.2 的规则 R-I2（裁决者的 LLM 路由必须与 producer 不同）**可以在脚本里直接声明**，不必靠外部编排。
⚠️ **必须消歧**：`dsh-workflow-worker-thread` README `:44` 那句 "Provider choice applies to every child in that run and is not visible to the script" 说的是 `WorkflowStartRequest.subagentProvider`（**subagent 传输后端**），不是 `agentOptions.provider`。见 01-CONTRACTS §9.25。

**扇出路径的选择（一手五条闸门，取值互不相同）** [E: gt-orchestration.md#结论摘要-1]：

| 路径 | 强制上限 | 强制点 | 本机实测 |
|---|---|---|---|
| 一条 assistant 消息里并排调 `subagent` | `maxParallelToolCalls` 出厂 10 | agent-loop 滚动池 | 10 |
| workflow 的 `agent()` / `parallel()` | `maxConcurrentAgents` 出厂 `0` → `min(16, max(1, availableParallelism()-2))` | worker 内 FIFO 信号量 | **12**（`availableParallelism()` = 14；硬顶 16） |
| `backgroundMode: continuable` 后台子代理 | **无任何上限**（整包无 Config，续接管理器无 per-parent 计数） | — | 仅受内存 / 429 限制 |
| `backgroundMode: one-shot` 后台任务 | `maxConcurrentJobsPerOwner` 出厂 10（每 owner，**超限抛错不排队**） | `dsh-jobs-local` | 10 |
| Code Mode `run_code` 子调用 | `maxParallelSubCalls` 出厂 10（**仅 `code`/`both` 呈现模式下存在**） | `dsh-tools` | 10 |

⚠️ **最后一行的适用条件在 R3 被改写**：旧表写「出厂呈现模式是 `native`」并据此认为这一闸门在本项目不存在。**那是把一个环境变量当成了组合事实**——headless bundle 把 `tools` 行 config 整键换成 `mode: !!js process.env.DSH_TOOLS_MODE`，`native` 只是 `DSH_TOOLS_MODE` **未设置时**的 schema 兜底（`dsh-tools/lib/index.js` 里逐字为 `mode ?? "native"`）。本 profile 的 `cordis.patch.yml` 把它钉成字面量 `native` 并 `disabled` 掉 `code-runtime` 之后（§A.3 第 0 块），这一行才真正**不存在**；在那两行落地前，它按「存在且不可观测」对待。详见 §C 的 C-12a。
〔裁定 · S0 实测，[E: .loop/m0/C-12a.json]〕**这条改写被运行实测坐实，两侧都跑了**：不设 `DSH_TOOLS_MODE` 时出厂 headless 模型面共 25 个工具、**无 `run_code`**（但**有 `workflow`**）；`DSH_TOOLS_MODE=code` 时 `run_code` 存在、可执行、并读到 `node:fs`。所以这一闸门在 pin 落地前**确实存在**，只是不可观测——**不得再把「出厂 native」当成它不存在的理由**。

**〔裁定 B-4〕批量扇出的唯一入口是 workflow。**
理由：它是唯一会**排队而不是失败**的路径；有 `maxTotalAgents` 兜底；`agent(prompt, {schema})` 直接拿结构化值 [E: gt-orchestration.md#设计含义-1]。
**必须同时认下的代价**：① 父 turn 全程阻塞到整个 workflow 落定；② **无 journaling、无 resume**；③ `parallel()` / `pipeline()` 把非 fatal 错误**吞成 `null`**，而 `null` 同时表示「thunk 抛了非 fatal 错」「child 非正常结束」「要了 schema 却没拿到 structured」三件事 [E: gt-orchestration.md#E5, #E2, #设计含义-9]。
**对策（硬编码进脚本模板）**：每个 thunk 自己返回 `{ok: true, ...} | {ok: false, reason}`，**绝不依赖 `null` 语义**；`null` 一律折算成 01-CONTRACTS §1.4 的 ST-N，不折算成「无发现」。

**结算通知不是持久信箱**——父被 dispose 时 `keepInbox: false`，未认领的结算通知被 durable 地取消，resume 后的父**读不到任何未决通知**；`report` 同样「没有持久信箱、没有幂等键、没有回执」[E: gt-orchestration.md#C3, #K5, #设计含义-6]。→ **子代理的每条结论必须由子代理自己写进 workspace 的持久台账文件**，通知只当「去读台账」的信号。这与 01-CONTRACTS §8.2 的决定同源。

**验收**：
- 每条 ST-A 的 claim，其 `verdicts/` 记录的 LLM 路由 ≠ producer 的 LLM 路由，且两者 `childId` 不同（§5.6 V5.1）。
- 全部裁决/取证子代理走 `spawn`（零父历史），不存在 `fork` 启动的裁决者（§5.6 V5.5）。
- 全部子代理 `delegationDepth ≤ 3`（§5.6 V5.6）。
- **红样本**：故意让一个裁决者与 producer 用同一 LLM 路由 → 独立性门必须红。
- **红样本（并发闸活着）**：把并发闸设为 1 并投 20 个任务，日志里必须只见到串行；把闸拆掉的负例必须被门抓到。

**依赖**：M1（工具）、M2（台账）、M3-GC0（能判 status 才有编排目标）。

### B.6 M5 · 评测轨

**职责**：held-out 题集上的能力度量（§9.26 的 60/20/20 结构），非对称计分（§9.29），Goodhart 防线（§9.28），以及 search-time contamination 检测（§9.27）。

**为什么不是插件**：它评的是**冻结产物**。GC-2 不得参与生成期——写作阶段禁止调用同一个 rubric judge 自评再改写，judge 只在冻结产物上跑一次 [E: 01-CONTRACTS §6.4]。做成插件会诱导「跑一遍 eval 再改」的闭环，那是对 judge 直接做梯度下降。

**验收**：
- 每个 GC-2 judge 有一份带日期与 `judge_version` 的 κ 校准记录，κ ≥ 0.60 才被标记为终判档；跨 `judge_version` 的分数不得出现在同一张图/表里（§6.6 V6.7）。
- **红样本**：把评测集本体喂进检索路径，contamination 检测必须命中。实测锚点：HLE 3.36–3.44% / GPQA 1.90–4.15% / SimpleQA 0.99–1.20%，且 SimpleQA 上被污染样本准确率 100% vs 未污染约 7%（§9.27）。
- **不得存在**的东西：任何以百分比形式对外报告的门通过率（§9.31 V9.5）。

**依赖**：M3、M7（要有可评的产物）。

### B.7 M6 · 攻击轨

**职责**：RT-1…RT-14 的 fixture 与判定；跨厂商 attacker battery（SEED→五透镜→PROVE-OR-FLAG→跨厂商裁判→fix-audit）[E: gt-house-method.md#M8, #M9]。

**关键纪律**：全部红队用例写成「**status 应当是什么**」，不是「模型应当不上当」（00-PREMISE B5）。

**RT-1 的形状在 R2 被规范源重写，本文件同步**〔见 01-CONTRACTS §1.6 V1.6〕：旧写法「`quote_faithful` 为 `pass` 但 status 不得为 ST-V，因为独立簇数为 1 触发 2b 降级」**已作废**——`K(K-L-T) = 1`，`1 < 1` 为假，2b 根本不触发（§1.5.2）。现行 RT-1 把**两个对象**分开判，通过判据三条缺一即失败：①「该网页 span 逐字为 Z」是 K-L-T，期望 **ST-V**；②「Z 为真」是 K-L-A（`K = 2`），单张伪造网页给不出第二簇，期望 **ST-U**；③**渲染层断言**——K-L-T 的 claim 永远不得以裸事实形态进入正文，必须携带归因。**第 ③ 条是这个用例的牙齿**，它落在 M7 而不是 M3：faithfulness 与 factuality 的混淆发生在渲染层，不在状态机里。

→ **对 M6 的直接后果**：RT-1 的 fixture 必须产出**两条 claim**（不是一条），且 M6 的判定脚本必须同时调用 M7 的渲染期占位符解析器来验第 ③ 条。**凡是本文件其它地方写「独立簇数为 1 触发降级」的措辞一律作废**——正确表述是「独立簇数 < `K(kind)` 触发 2b 降级」；`F-14 single-cluster` 现在作用类型为 `none`，只记录不判定（§7.3.2）。

**必须固定的回归用例（有现成 ground truth）**：11 家中文媒体转述同一条 Nikkei Asia → `independent_cluster_count` 必须归并为 **1**（§5.6 V5.3）；同时引用 Unpaywall 与 OpenAlex 的 OA 状态断言 → 必须为 **1**（§5.6 V5.4，依据是 OpenAlex 官方明说 "Unpaywall records are served from the same OpenAlex data" 且实测返回体 `evidence`/`updated` 字段值已 literally 变成 `"deprecated"`）[E: ext-academic-apis.md#G1, #G2]。

**验收**：
- 一轮攻击后，findings 中「由门发现」的比例 ≥ 30%；低于即判定门套件在做装饰（00-PREMISE B8 的推翻观测，P1 级）。
- **红样本**：battery 自身的 target-awareness——本仓库已记录 `the battery stage receives 'target' but ignores it`，同一套 lens 提示词打在错误形状的对象上 [E: gt-house-method.md#未决-6]。M6 必须为「数据推导 / 文献引证 / 逻辑推断」三类 claim 分化 lens，或显式在 coverage_gaps 里记「未分化」。

**依赖**：M1、M2、M3。M0 的 RT-5 是它的**前置**而不是成员。

### B.8 M7 · 薄散文出口（确定性组稿器）

**职责**：把 `claims/*.status.json` 渲染成 `prose/`。正文数字一律写成 `{{claim:<id>.<field>}}`，渲染期解析，解析不到 → **构建失败**（§4 W-10）。作者 agent 写 outline 与叙述骨架，**不写数字**。

**「薄」的准确含义**：这一层不做判断、不做聚合、不做修辞升级。它做三件事——占位符解析、flag 的**原样**呈现（部分 flag 必须原样显示其参数，如 `chart-extracted` 的 ε，§7.1 F-规则-3）、以及能力受限的主动声明（如 `not-covered-zh` 必须在交付物中显式声明，§7.2 F-32）。

**为什么不是插件**：它是构建期的确定性脚本，输入全在文件里。做成插件只会让它出现在模型可触达的面上。

**验收**：
- `prose/` 渲染产物中正文的每个数字都能反解到一个占位符；裸数字扫描命中数为 0（白名单：年份、章节号、页码）（§4.6 V4.3）。
- 不存在 `overall_status` / `all_verified` / `pass_rate` 字段被写进交付物（§1.6 V1.5）。
- 交付物中不含任何 `retention_tier == A` 的原始件；Tier B 摘录长度全部不超过 §8.6.1 的适用上限；中文摘录全部携带作者与作品名（§8.7 V8.10）。
- **红样本**：一份含**一个手打裸数字**的骨架必须让构建失败。这条对治的是本仓库实证过的失败——badge / 版本 / 覆盖率数字**连续两个 release 都错** [E: gt-house-method.md#M10]。

**依赖**：M3（status 必须先算出来）。

### B.9 M8 · 回归外壳

**职责**：把「门被执行过」这件事本身变成机器事实。

固定形状（每条都对应一个已实证的洞）：

| 步骤 | 断言 | 它对治的实证失败 |
|---|---|---|
| 第 1 行 | **由仓库外的 pinned runner 起跑**：runner 自带 40 位 commit sha（**不从仓库内任何文件读**），`git archive <sha> checks` 展开到仓库外，再断言 `git status --porcelain -- checks/` 干净 **且** 工作树 `checks/` 与展开副本逐文件 sha256 相同，非零即拒 | 该机制**零代码实现**，仅存在于散文 [E: GROUND-TRUTH-CORRECTIONS.md#D1]；且**仓库内入口不算数**——〔裁定 · S0 实测，[E: .loop/m0/M0-7.json]〕把 `gate_integrity.sh` 换成只 `echo OK` 的假货并提交后，仓库内入口 **exit 0**，同一份仓库的仓库外 pinned runner **exit 3** |
| live 幂等 | 同一批输入连续跑两次，第二次 `accepted == 0` | `harvest_e2e.sh` 的 run-2 **从不断言**，实测 run-2 accepted=8；幂等只在离线单测里证过 [E: GROUND-TRUTH-CORRECTIONS.md#D2；01-CONTRACTS §4.6 V4.4] |
| 真实 boot | 一次真实 headless boot（假密钥）必须走到 AUTH 失败而不是 `dsh: plugin tree failed to load` | 配置层检查是空心的，同一失败类连中三次 [E: gt-house-method.md#结论摘要-2；gt-profile-plugin.md#设计含义-8] |
| 并行压测 | §8.7 V8.7 | 「并行 worker 输出不相交这条规则没出过事」已被本仓库自身证伪（m7-eval1 数据丢失 + rm -rf 事故）[E: GROUND-TRUTH-CORRECTIONS.md#B6] |
| 配对记账 | REPORT 中每个成功数必须配一个完整性对子，或显式 `not measured` | `report_gate.sh` 已是这个形状 [E: gt-house-method.md#A11, #M7] |

**〔已知的自指问题 · 已缩小到一个可命名的信任根，未闭合〕** `gate_integrity.sh` 自己也在 `checks/` 里，谁证明它没被改？house 无答案 [E: gt-house-method.md#未决-1]。〔裁定 · S0 实测，[E: .loop/m0/M0-7.json]〕本文件**改裁**——原来那句「本文件不裁定这一条，列入 open questions」连同它给的候选解一起作废：

- **原候选解「由 conductor 从 tag 检出一份干净副本到 `checks/` 之外的路径执行」被两条实测判死。** ① tag 不是不可变锚点：`refs/tags/*` 不受 `receive.denyDeletes` / `receive.denyNonFastForwards` 保护，实测强推与删除都 ACCEPTED，且默认配置下 tag 不写 reflog。② **自提升（self-hoisting）不成立**：发起「检出干净副本」这个动作的代码本身就在被检查的文件里——红样本 R3 把 `gate_integrity.sh` 换成只 `echo OK` 的假货并提交、同时把 `BASELINE.ledger` 追加一行，从仓库内入口 `./checks/gate_integrity.sh` 调用得到 **exit 0**。
- **本仓库能真正做到的最强形态**（红样本已跑通，不是设计）：锚点是 **40 位 commit sha**；该 sha 与调用入口都必须落在 producer 写不到的地方；由一个**仓库外**的 runner 执行 `git archive <sha> checks` 展开到仓库外再跑，并与工作树 `checks/` 逐文件 sha256 比对。同一份被篡改的仓库，仓库内入口 **exit 0**、仓库外 pinned runner **exit 3**。
- **它挡不住什么（逐条都是实测或已确认的推理，不要读成已修）**：① **外部锚点今天不存在**——本仓库 `git remote` 数为 **0**，那个「仓库外的 40 位 sha」现在没有任何地方可放；放在本机另一个文件里，对一个持有 bash 的 producer 不构成边界。② **pinned runner 的绿是买来的**——它能抓到篡改的唯一原因是 sha 由外部传入；第一版 runner 忘了这点、仍去读仓库内的台账，同样被骗过（exit 0）。该机制对实现细节极其脆弱。③ **TOFU**——第一条 baseline 因为它第一才被信任，没有任何东西为它背书。④ **GitHub ruleset 只是搬家**：它能把 tag 配成受限，但那是远端管理员配置项、带 bypass 豁免，且本轮**没有真建仓库、没有真配、没有真试强推**（只读了官方文档）。⑤ **同机同用户不是两条轨道**：「门轨道与 producer 轨道进程级隔离」在一台机器一个用户下只是执行上下文不同，不是权限主体不同。⑥ **签名路径一次没跑过**：22 个 `gates-baseline-*` tag 中带 PGP 签名的是 0 个，本机是否有可用签名密钥也未验证。⑦ tag 实验只在本地 `file://` 传输上做过，ssh/https 服务端是否一致属推理。⑧ 台账的哈希链只防静默改写中间行，**不防整条链重建**——R3 里攻击者直接追加一行就过了仓库内入口。
- **本文件的裁定**：架构层面**认账**「谁能改那 40 位字符串或那个 runner，谁就能让门说谎」，并把**「外部信任根尚未配置」列为 M8 的阻塞项**（不是已解决项）。在它落地之前，M8 第 1 行只能证明「相对于某个由人在仓库外提供的 sha，`checks/` 没被改」，不能证明那个 sha 本身可信。

**依赖**：M3。

### B.10 依赖图与建造顺序

```
M0 架构可行性 ──┐
                ├─→ M1 检索取证插件 ──┐
M2 证据底座 ────┤                      ├─→ M4 编排 ──→ M6 攻击轨 ──→ M5 评测轨
                └─→ M3 门脚本集 ──────┤
                        │             └─→ M8 回归外壳
                        └─────────────────→ M7 散文出口
```

**顺序的理由（每条都是「不这样就白做」）**：

1. **M0 第一，且 RT-5 是阻塞项。** 若 PDF 抽取拿不到可见性信息，通道分离在 PDF 路径上失效，而 PDF 是学术场景的主要摄取对象——这时要改的是架构，不是测试 [E: 01-CONTRACTS §7.2.2, §7.4 V7.8]。多帧 zstd 解帧器同样第一，因为所有读日志的门都建在它上面，写错会**静默只读到 1 行并误判日志为空** [E: GROUND-TRUTH-CORRECTIONS.md#A3]。
2. **M2 第二**：它定义了 CAS 与 schema 的物理形状，M1 与 M3 都 `import` 它。先建它才能让「一个工件一个物理写者」（§4.1 I-W2）在代码层成立而不是在纪律层成立。
3. **M3 的 GC-0 子集第三，早于 M1。** 这是本图最反直觉的一条：**先建门，后建被门检查的东西**。理由是 red-first——门必须先证明自己会红，红案 fixture 由 conductor 播种（§6.5.1）；本仓库的 `b3-fidelity-harness` 存在的唯一理由，就是在昂贵的 b4 之前证明 checker 有判别力 [E: gt-house-method.md#A9]。同时这也是 00-PREMISE B8 的三条前置代码之二（负例套件进 CI）与之三（台账格式门）的落点。
4. **M1 第四**：它现在有了落盘契约（M2）与会红的门（M3-GC0）。
5. **M8 第五，早于编排。** 因为「幂等在 live 层从未被断言」这条洞，如果留到编排之后补，就会重演 D2 的形状——离线单测绿、live 从不触发 [E: GROUND-TRUTH-CORRECTIONS.md#D2]。
6. **M3 的 GC-1 子集第六**：它依赖注册表同步器把 T0 名录全部本地化（下载一次、本地查 N 次、扇出子 agent 不打网络）[E: 01-CONTRACTS §6.3 硬要求 4]。在扇出存在之前建它没有压力测试对象。
7. **M4 第七**：编排是把前面所有件串起来，它不产生新的判定能力。**先建编排会诱导「靠 prompt 保证独立性」**——前代把独立性完全交给 prompt 措辞，结果是该角色在审计上不存在 [E: 01-CONTRACTS §5.1；gt-pg-current.md#C-9]。
8. **M6 第八**：攻击轨需要一个完整的、可被攻击的系统。
9. **M5 第九**：评测需要 held-out 题集与冻结产物。
10. **M7 最后**：散文是渲染层，它的输入是全部已算好的 status。**先建散文出口是本项目最容易犯的错**——它会让「先写文章再补证据」变得可能。

---

## §C DSH 能力映射表

> 判定三档：**〔原生〕**= DSH 出厂即提供，我们只是使用；**〔profile 层实现〕**= DSH 提供接缝或落点，具体代码我们写；**〔需 harness 改造〕**= 当前安装版做不到，要么改 DSH，要么绕开。
> 每条给一手依据。**凡是 01-CONTRACTS 已定义的术语，此处只引用不复述。**

### C.1 机会项（GROUND-TRUTH-CORRECTIONS §E 的四条，v1 不知道的能力）

| # | 需求 | 判定 | 一手依据 | 我们怎么用 |
|---|---|---|---|---|
| C-1 | 裁决者与产出者用不同厂商的模型，且**在脚本里声明** | **〔原生〕** | workflow 脚本 `agent()` 的 `SUPPORTED_AGENT_OPTIONS` 含五项：`label, phase, schema, provider, model`；宿主侧映射到 `agentOptions.{provider, model}` [E: GROUND-TRUTH-CORRECTIONS.md#A11, #E1；gt-orchestration.md#D3(b)] | 落地 01-CONTRACTS §5.2 规则 R-I2。**必须消歧**：README `:44` 那句 provider 指的是 `subagentProvider`（传输后端），见 §9.25 |
| C-2 | 证据元数据挂在模型不可见、抗压缩、抗持久化、类型已知的位置 | **〔profile 层实现〕**（落点原生，内容我们写） | `tool/result.meta` 是 `JsonValue`、「opaque to the core」；loop 用 `createToolResultMessage({callId, content, isError})` 建消息，**`meta` 不进 message**；pruner 用 `...event.data` 展开、`meta` 原样保留；已有一手先例（`dsh-tool-fs` 的 read 结果 `meta` 为 `{path, offset, lines, totalLines, lang}`）[E: GROUND-TRUTH-CORRECTIONS.md#E2；gt-evidence-substrate.md#B8, #D4] | 01-CONTRACTS §4 W-02 的物理落点。**自设 8 KB 上限**，大对象只放 sha256 指针——`meta` 有无隐性上限**未验证**（代码里没看到字节/深度限制，但 wire 层未测）[E: gt-evidence-substrate.md#未决-3；01-CONTRACTS §8.2 D-8.2] |
| C-3 | per-step token 与缓存分解 | **〔原生〕**（读日志） | 每个 `assistant/message.data.usage` 与 `assistant/chunk{type:'usage'}` 都带 `{turn, step}` + 完整 `TokenUsage`；实测样本 `seq 105, turn 1/step 1, {"inputTokens":5935,"outputTokens":138,"cacheReadTokens":6144,"reasoningTokens":14}` [E: GROUND-TRUTH-CORRECTIONS.md#A5, #E3；gt-evidence-substrate.md#F3] | 01-CONTRACTS §4 W-13 的 fold 源。⚠️ **`cacheWriteTokens` 在本机 DeepSeek 路由的样本中未出现**（该 adapter 不报或恒为 0），成本模型若要区分 cache write 必须在目标路由上实测 [E: gt-evidence-substrate.md#未决-4] |
| C-4 | boot 门断言真实的加载期不变量 | **〔profile 层实现〕** | 五条不变量可枚举 [E: GROUND-TRUTH-CORRECTIONS.md#A4, #E4；gt-profile-plugin.md#结论摘要-7, #C2, #C3] | 见 §D。**删除 v1 的「必须 export Config 否则 boot 崩」硬规则** |

### C.2 陷阱项（GROUND-TRUTH-CORRECTIONS §A 的六条 + 两条同级陷阱）

| # | 陷阱 | 判定 | 一手依据 | 设计应对 |
|---|---|---|---|---|
| C-5 | **`ignorable` 只读不写** | **〔需 harness 改造〕→ 绕开** | `Session.append` 的签名与实现里根本没有该通道（只有 `surfaceOp` / `sourceEventSeqs`）；全 194 包 grep 写入方 **0 处**；读端完全支持、写端完全缺失 [E: GROUND-TRUTH-CORRECTIONS.md#A1；gt-evidence-substrate.md#B6] | **不写自定义 log-only 事件**（01-CONTRACTS §8.2）。逃生口 `KNOWN_SESSION_EVENT_TYPES.add()` 实测可行（Set 未冻结、模块单例共享）但官方明写「registration surface … deferred」，且**日志对没装本插件的进程仍不可读** → **一律不用**，只作「若官方开放注册面则升级」的预留路径 [E: gt-evidence-substrate.md#B7, #未决-1]。在野代价已证实：第三方插件写 `ya-subagent/started`，该 session **没有任何 `session/end-seed`** [E: gt-evidence-substrate.md#C1] |
| C-6 | **spill 截断**：超阈值纯文本结果的原文不在日志里 | **〔profile 层实现〕** | spill-policy 是 `tools/post-execute` 变换器，loop 用**流水线最终结果**建 `tool/result`；出厂 `maxInlineBytes: 50000` 字节（UTF-8 字节，不是 code point）[E: GROUND-TRUTH-CORRECTIONS.md#A2；gt-evidence-substrate.md#E2, #E4] | 逐字校验的基底**只能是 CAS 快照文件**；日志只用于绑定「这次抓取确实发生过」（§4 W-01 依据）。**并且**：spill 文件不可依赖为长期证据——root 出厂**未配置**，落在每进程私有的 OS temp 目录、跨进程不可预测、可能被系统清理、无删除 API [E: gt-evidence-substrate.md#E5；01-CONTRACTS §8.4 D-8.12] |
| C-7 | **多帧 zstd** | **〔profile 层实现〕** | 磁盘 `.jsonl.zstd` 是多个独立 frame 串接；Node 内置只解第一帧（实测 1 行 vs 3675 行）[E: GROUND-TRUTH-CORRECTIONS.md#A3；gt-evidence-substrate.md#H3] | 按 magic `28 B5 2F FD` 手动切帧、或 spawn `zstd -dc`、或走 `readRaw` / `/api/session.export`。**M0 的第一件代码**。配套两个同级地雷：按行 `JSON.parse` 后**必须** `decodeStorageRecord`（否则 chunk-row 打包行只有 `seq0`、映射有洞）；**必须**用 `surfaceOp === 'append'` 过滤 append-origin 事件（否则 pruner/compaction 的替换体会冒充原始结果）[E: gt-evidence-substrate.md#H4, #D2, #D4；01-CONTRACTS §6.5.4] |
| C-8 | **`run_code` 旁路** | **〔需 harness 改造〕→ 认账，不宣称围堵** | `dsh-code-runtime-worker-thread` 对沙箱包**零依赖**，程序体用 `new AsyncFunction` 在 worker 自己的 realm 求值，Node 全局（`fetch`/`process`/`globalThis`/`Buffer`/`URL`）都在作用域内；README 自陈 "Containment, not a security boundary … bash-equivalent by design"；程序 spawn 的 OS 进程在 terminate 后**仍存活** [E: GROUND-TRUTH-CORRECTIONS.md#A7；gt-exec-security.md#D-3~D-5] | 它**同时绕过**内核沙箱（只管 bash）与 `ctx.fs` 策略围栏（只管 ctx.fs 工具）。→ 文档里**不得**出现「研究 agent 只能通过我们的检索工具上网」。唯一诚实的表述是产物级兜底（01-CONTRACTS §4.4）。**〔裁定 · S0 实测，[E: .loop/m0/M0-4.json]〕这条边界已经跑过，不再是「未实际执行验证」**：① `node:fs` **可达**——程序体 `const fs = await import('node:fs')` 拿到 fs 并成功 `writeFileSync` + 读回；真实 headless 会话（`DSH_PERMISSION_MODE=read-only`）里**工作区内与工作区外两个文件都写成并在磁盘上核实存在**。② **沙箱对它零约束**，机制已定位：`run_code` 跑在**宿主 DSH 进程的 worker thread** 里（`program pid === host pid`），根本没有一个可被 `sandbox-exec` 包住的子进程；同机、同时刻、同一条 read-only 策略下走内核沙箱的 **bash 路径写文件被拒**（退出码非 0 + stderr 命中该后端的 `denialSignatures` + 文件未生成），`run_code` 路径写成。③ 两条措辞更正：`require` **不在作用域**（`ReferenceError: require is not defined`——程序体是 `new AsyncFunction` 的函数体，不是模块作用域），可达路径只有 `await import()`；`process.env` **键数 = 0**（worker `env: {}` 已实测生效），即它**挡凭据、不挡文件系统**。④ **`node:child_process` 与网络出站仍未实测**——`import()` 通道本身是开的使其大概率同样可达，但那是推断；这两项的措辞**继续按最坏假设**，不得据本条升级。⑤ 另一条仍未测：本轮打穿的是内核沙箱，「`run_code` 绕过 `ctx.fs` 围栏」仍只有代码依据，没有跑过「ctx.fs 拒写 / run_code 写成」的对照 |
| C-9 | **子代理不继承沙箱作为下限** | **〔需 harness 改造〕→ 认账** | `captureDelegatedPolicyOverrides` 只取 `sandboxPolicy.overrideOf(parent.session)`，即父会话的**显式 override**；从不捕获部署出厂值，也不捕获一次性授权。approval 无条件钉为 `'never'` [E: GROUND-TRUTH-CORRECTIONS.md#A8；gt-orchestration.md#C4] | **不得把「子代理受限于父」当安全地板**。设计应对是运行时指纹 + 门：`runs/<run_id>/manifest.json` 中若 `sandbox/mode == danger-full-access`，该次运行的全部产物标记「权限异常，需人工复核」（§4.6 V4.5）。父若切到 `danger-full-access`，所有子代理继承之且**不会有任何提示** [E: gt-exec-security.md#H-6] |
| C-10 | **出厂值 ≠ 包默认值** | **〔profile 层实现〕** | 沙箱：包默认确是 read-only，但**出厂组合覆盖为 workspace-write**；ralph 轮预算：README 与代码 schema 都写 256，**出厂全部组合覆盖为 64**；goal 轮预算 `defaultMaxGoalRounds = 256` 出厂未覆盖、确认为 256 [E: GROUND-TRUTH-CORRECTIONS.md#A9, #A10；gt-orchestration.md#X1, #X2] | 一切「默认」一律引出厂组合（见 §9.23）；两个轮预算不得混谈（见 §9.24）。**profile 的 `cordis.patch.yml` 显式重述我们依赖的每个值**，让漂移在 git diff 里可见 |
| C-11 | **`toolFilter` 不是权限天花板** | **〔需 harness 改造〕→ 认账** | 三处一手 README 明文否认；`restrict` 只过滤「继承来的层」，不过滤 scope 自己注册的工具；子代理拿**全新扁平 scope**，不导入父的 restriction → **不向下传递** [E: gt-exec-security.md#B-1~B-4] | 它是有效的降噪手段，不是安全边界。强制点只能落工具边界（§C.3 的 C-12） |
| C-12 | **`--dump-config` ≠ boot 真值** | **〔profile 层实现〕** | dump 的 layers 不含 CLI 注入的 `agent-presets.roots` 覆盖与 telemetry disable patch [E: gt-profile-plugin.md#H2, #G6] | boot 门必须有**真实 boot** 那一步（§D.3 第 2 段）。同时断言 dump 输出里**没有任何 patch warning**——〔裁定 · S0 实测，[E: .loop/m0/M0-3c.json]〕**这条断言只能挂在 `--dump-config` 上**：同一份写错 id 的 patch，dump 路径报 2 条 warning，**真实 boot 路径报 0 条**（同次命令 `dsh: AUTH` 证明 boot 已跑到 LLM）。所以「真实 boot」与「零 patch warning」是**两段不可互相替代**的检查，不是一段的两种写法 [E: gt-profile-plugin.md#B3, #设计含义-8] |
| **C-12a** | **「出厂呈现模式是 `native`」是环境变量的函数，不是组合事实**〔R3 新增，攻击 C-12a〕 | **〔profile 层实现〕→ 已给出结构性收口** | R3 三项实测：① `dsh-base/cordis.patch.yml:424` 的 `tools` 行**无 config**（注释：omitting it keeps the schema default (native)）；② `@deepseek-ai/dsh-headless/cordis.patch.yml` 把该行 config **整键替换**为 `mode: !!js process.env.DSH_TOOLS_MODE`（`dsh --profile headless --dump-config` 第 306–309 行，带溯源注释 `# == @deepseek-ai/dsh-base, patched by @deepseek-ai/dsh-headless`）；③ `dsh-tools/lib/index.js` 内为 `mode ?? "native"`；④ 同一 bundle **insert 了 `code-runtime`**，即 Code Mode 的执行能力在 headless 下是挂着的。**〔裁定 · S0 实测，[E: .loop/m0/C-12a.json]〕本条已从「读包 + dump 阅读」升级为运行实测，且结论收紧**：出厂纯净组合（bundles 仅 `dsh-base` + `dsh-headless`）的 dump 里，`tools` 行的有效 config 就是那个未求值的 `mode: !!js process.env.DSH_TOOLS_MODE`，`code-runtime` 行确实被 insert 了。**「出厂 native」只是 `DSH_TOOLS_MODE` 未设时的 schema 兜底，不是组合事实**——两侧都跑了：不设该变量时模型面上**没有** `run_code`（附带观测：出厂 headless 模型面共 25 个工具，无 `run_code` 但**有 `workflow`**，与 C-12c 一致）；`DSH_TOOLS_MODE=code` 时 `run_code` 存在、可执行、并**成功读到 `node:fs`**（`readdirSync('/').length` = 21）。§A.3 第 0 块的两行收口也独立复核通过：钉成字面量 `native` + `code-runtime: disabled` 后 `DSH_TOOLS_MODE=code` **不再起作用**（正常走到 `dsh: AUTH`）；把 mode 钉成 `code` 且 `code-runtime` 被 disabled 则**响亮启动失败** | **旧裁定「P0 层不存在 / `run_code` 不在面上」在两行 patch 落地前不成立**：任何父进程 `export DSH_TOOLS_MODE=code` 即可把 `run_code` 推上模型面，而 `--dump-config` 对此**完全不可观测**（实测：设与不设该变量，dump 输出逐字相同）。**收口是 §A.3 第 0 块的两行**：`tools.mode: native` 写成字面量（env 接缝被本层整键替换）+ `code-runtime: disabled`。第二行经真实 boot 验证会把「Code Mode 被打开」变成响亮的启动失败（错误文案见 §A.3 第 4 条），是本轮唯一真正结构性的那一半。**⚠️ S0 实测的三条残余，不得省略**：① 只测了 `DSH_TOOLS_MODE=code`，**`both` 与非法值（如 `bogus`）未测**；② **`ctx.tools.presentAs()` 这条 agent 级绕过路径未测**——`dsh-tools` README 明写单个 agent 可为自己选 code 模式、且 `run_code` 之名「whatever the configured mode」都保留，**§A.3 那两行对它是否有效没有验证**，它是 env 变量之外的第二个接缝；③ 本轮测的是出厂纯净组合，用户本机 `~/.dsh/profiles/headless` 另装了 3 个社区 bundle（claude-marketplace / mp-automator / pipeline-executor），dump 显示它们只 insert 自己的行、未 patch `tools`，但**未逐包审计** |
| **C-12b** | **boot 门把机器级威胁钉在了错误的文件上**〔R3 新增，攻击 C-12b〕 | **〔profile 层实现〕→ 已改写门断言** | `$DSH_HOME/settings.yaml` 由 `dsh-base` 的 `settings` 行挂载（每个 profile 都吃）、`watch: true` 热重载、分层「schema 默认 → 组合层 base → **用户文档 section**」，用户文档在最上面 [E: gt-profile-plugin.md#D4；R3 实测 `dsh-settings-file/README.md` + 本机 1271 字节的 `settings.yaml`]。本机该文件实测携带 `agent-default-model`（模型路由 + `reasoningEffort`）、`ya-subagent.profiles[].model` / `maxDepth`、`llm-pi-ai.providers`（活体注册新 provider 路由）、`agent-presets.default`、`auto-compact.thresholds`。**它对两个 dump 命令双双不可见**（dump 打印插件树，settings 叠在树之上）。〔裁定 · S0 实测，[E: .loop/m0/C-12b.json]〕「settings 覆盖 patch」的证据等级从**文档阅读**升到**运行实测**：三方对撞下 patch 链最终值是 `PATCH-BOGUS-MODEL`，真正发到 API 的是 `SETTINGS-BOGUS-MODEL` | 旧门断言 `$DSH_HOME/cordis.patch.yml` 不存在。该文件确实在层序里（`composeProfile` 实测），但本机不存在且一旦存在会在 dump 里现形——**那条断言在本机恒真**。〔裁定 · S0 实测〕**「恒真」不等于「不会红的检查」，更不等于可以删**：实测该文件一旦存在会**压过 profile 自己的 patch 层**（`FROM-PROFILE` 被 `FROM-DSHHOME` 覆盖），因此它能整键改掉我们钉死的任何一行（含 `tools.mode` 与 `code-runtime`）。它与 `settings.yaml` 的区别是**可观测性**而非威胁强度。改写后的门**两个文件都断言**，且 `settings.yaml` 走「值级白名单 + sha256 入 manifest」而不是「必须不存在」（它是用户配模型的合法入口）；**该哈希只证明 boot 那一刻**——`watch: true` 热重载使运行途中的改动不可见（残余风险，见 §D.3 第 1b (iii) 与 §D.5）。可运行断言见 §D.3 第 1 段 |
| **C-12c** | **`workflow` 工具是第二扇 P0 门，而本架构强制走它**〔R3 新增，C-12a 追查副产物〕 | **〔需 harness 改造〕→ 认账，且不得再宣称「P0 层不存在」** | `dsh-tool-workflow` 的模型面参数含 `script`（**任意 JavaScript 函数体**）；`dsh-workflow-worker-thread` README 自陈 "Workflow scripts are model-written and have the same trust premise as the model's existing bash access" 与 "`node:vm` inside a worker is an API-shaping mechanism, not a security boundary: an escaped script can recover Node capabilities with the host process's privileges"，并明写 "A genuinely untrusted-script sandbox would require a different engine behind the same workflow seam" [E: gt-orchestration.md#E6, #E7；R3 复核 README 原文] | 关掉 `code-runtime` **不等于**关掉任意 JS 执行面：〔裁定 B-4〕把 workflow 定为批量扇出的**唯一入口**，因此这扇门是**本架构要求打开的**。→ ①01-CONTRACTS §0.2 第二层「文件面无文件系统级强制」的成因清单里，`run_code` 之外必须并列 `workflow.script`；②`.arc/` 的写者隔离**不能**靠「不给 `run_code`」实现，只能靠 §0.2 收口所指的**进程级隔离**（门在不挂 `tool-workflow`、不给写 `.arc/` 的独立 profile 里跑）；③本文件不得出现「本 profile 的模型面上没有任意代码执行」这句话。**列入 M0 阻塞项** |

### C.3 需求 → 能力逐条映射

| # | 需求 | 判定 | 一手依据 |
|---|---|---|---|
| C-13 | 强制「证据必须来自被记录的工具调用」 | **〔profile 层实现〕**，三个强制点见 01-CONTRACTS §4.4 | 本文件只补一条 §4.4 未记的一手事实：**三者对顶层调用和 `run_code` 子调用同样生效**，因为子调用**重新进入完整的 tool pipeline**（`pre-execute → guards → execute → post-execute`）[E: gt-exec-security.md#H-1, #D-10] |
| C-14 | 证据索引的同步查询 | **〔profile 层实现〕**，且**必须是内存中的同步结构** | `ToolGuard = (execution) => string \| undefined` 是同步的 [E: gt-exec-security.md#H-2] |
| C-15 | claim 提交工具拒收 `status` 字段 | **〔profile 层实现〕** | `tools/pre-execute` 的 `deny`；「被拒绝」而非「被覆盖」是硬要求（§4.6 V4.1） |
| C-16 | 子代理的返回必须是结构化的，拿不到即失败 | **〔原生〕** | `request.outputSchema` → 子 scope 注册 `structured_output` 工具 + order-190 prompt 段 + 单调 guard；**一次干净的 turn 若没提交必需的结构化值，stopReason 报 `error`，driver 不会重问** [E: gt-orchestration.md#设计含义-3]。workflow 的 `agent(prompt, {schema})` 要了 schema 却没拿到 → 返回 `null` [E: gt-orchestration.md#E5] |
| C-17 | 身份与谱系是机器事实 | **〔原生〕** | `header.parentSession` / `seedLength` / `delegationDepth` / `origin:'subagent'` / `agentPreset` 全部持久化（实测 header 样本含全部字段）；后台上报带 `source {kind:'subagent-report', senderSessionId}` [E: gt-evidence-substrate.md#其它可直接使用的原语；gt-orchestration.md#K5] |
| C-18 | 取证子代理零父历史 | **〔原生〕**（选 `spawn`） | `fork` 的 seed 是父日志从 seq 0 到最后一个 `turn/end` 的连续前缀；spawn 无 seed。两者能力集完全一致 `{outputSchema, depthLimit, toolFilter, persona}` [E: gt-orchestration.md#C2] |
| C-19 | 委派深度限制 | **〔原生〕**，出厂 3 | `resolveChildDepth`；深度单调（runtime 可加深不可降低）。⚠️ **数值型 maxDepth 要求 subagent 传输后端具备 `depthLimit` capability，否则挂载即失败**；进程外后端需写 `maxDepth: 'provider-managed'` [E: gt-profile-plugin.md#I；gt-orchestration.md#C1] |
| C-20 | 中央限速网关（按 host 分桶、跨进程） | **〔需 harness 改造〕→ 自建** | DSH 侧 grep `concurren\|semaphore\|inFlight\|maxSockets` 在 `dsh-llm` 与 `dsh-llm-deepseek` **零命中** → 限流是被动的（429 + 退避），不是主动的 [E: gt-orchestration.md#I6]。外部侧：子代理可能是独立进程，任何「每 agent 内存计数器」在超并行下必然击穿 [E: ext-web-providers.md#D2] |
| C-21 | 禁网重跑沙箱 | **〔需 harness 改造〕→ 用 OS 级** | DSH 沙箱词汇是纯文件效果，网络与进程完全不管（类型注释 + README Known Limitations + 三个后端 profile 构造函数三重佐证）[E: gt-exec-security.md#结论摘要-1]。→ 用 macOS `sandbox-exec` profile（拒网络 + 只允许写 run 目录）+ 硬超时 + `ulimit`。⚠️ `sandbox-exec` **已被 Apple 标记 deprecated**，apple/containerization #737（开于 2026-05-12）**线程内无 Apple 官方回复**；缓解是把「同一 `run.py` 能在 pinned OCI 镜像里跑」写进契约 [E: ext-reproducibility.md#E2] |
| C-22 | 长跑续跑 | **〔原生但有硬缺口〕** | goal 的 `activation` **永不持久化**：fresh cache 与每个 `agent/session-start` 边缘都会 disarm，即使 replay 发现 durable phase 是 active [E: gt-orchestration.md#A1, #A2]。→ **「无人值守跑一夜」在 goal 路径上不成立**，resume 后必须有人类授权的 `resume` 重新 arm。workflow 路径则**无 journaling、无 resume** [E: gt-orchestration.md#设计含义-1] |
| C-23 | 持久信箱 | **〔需 harness 改造〕→ 自建台账** | 父被 dispose 时 `keepInbox: false` 会 durable 地取消未认领通知；`report` 无持久信箱、无幂等键、无回执 [E: gt-orchestration.md#C3, #K5] |
| C-24 | 遥测出厂即关 | **〔原生〕**（CLI 注入 telemetry disable patch） | `composeProfile` 追加 telemetry disable patch [E: gt-profile-plugin.md#B1]。**必须保持关**：开启遥测会把 session-log 记录**逐字镜像**到 OTLP/HTTP logs，**无任何 redaction 规则** [E: gt-evidence-substrate.md#H6；01-CONTRACTS §8.4 D-8.15] |
| C-25 | 自带方法论 skill | **〔profile 层实现〕**，但不要动 `skill-filesystem` 的 `customSkillDirs` | 官方做法是 `customSkillDirs` + `!!js` 解析 `baseUrl`；但 profile 层的 `skill-filesystem` 是**单一行**，patch 它就是整体替换 config——多个插件都想加会互相顶掉。更安全的是在 `apply()` 里 `ctx.skills.registerProvider(...)` 注册**我们自己的 skill provider**（同层内 `provider.name` 唯一即可，`runtime` 是保留名）[E: gt-profile-plugin.md#F1, #F3, #设计含义-6] |
| C-26 | 让用户热改配置 | **〔原生〕** | `installSettingsSection(ctx, ns, Config, config, {...})`；分层是 schema 默认 → 组合层 base → 用户文档 section；`$DSH_HOME/settings.yaml` 热重载；boot 期与注册期校验 fail loud，live reload 的非法 section 保留上一份好值并 warn [E: gt-profile-plugin.md#D4] |
| C-27 | 「模型凭记忆编造引用」的运行时检测 | **〔不存在〕** | 运行时**没有任何**机制能判定这一点 [E: gt-exec-security.md#H-1]。唯一可行的是产物级校验（01-CONTRACTS §4.4） |

---

## §D 加载期与启动门

### D.1 v1 的错误必须先删掉

v1 写「插件**必须** `export const Config` 否则 boot 崩」，并把它当作 gate 的验收判据。**这是假的安全网**：`cordis/lib/index.js:956` 是 `if (!runtime.Config) return config;`——没有 `Config` 的插件拿到未校验的原始 config 照常启动 [E: GROUND-TRUTH-CORRECTIONS.md#A4；gt-profile-plugin.md#C1]。真实因果是反过来的：**有 `Config` 且校验失败**才崩。一个漏写 `Config` 的插件会**静默通过**那道门。

顺带两条 v1 没说的精确性：校验入口是 Standard Schema v1 接缝 `runtime.Config["~standard"].validate(config)`，不是 `Config.validate`；**异步校验直接抛 `TypeError: Async config validation is not supported`** [E: gt-profile-plugin.md#C2]。

**作为团队纪律**，「每个自建插件都导出 `Config`」完全成立且值得保留——但它必须由**我们自己的门**检查，不能指望 boot 帮忙。可行的机器判据：对插件模块做一次 `import()` 并断言 `typeof mod.Config?.['~standard']?.validate === 'function'` [E: gt-profile-plugin.md#设计含义-3]。

### D.2 五条真实的加载期不变量

| # | 不变量 | 违反后 fiber 状态 | 失败文案（一手） |
|---|---|---|---|
| **L1** | 模块能被 import | FAILED(3) | `failed to import loader entry <id> (<name>): ...` |
| **L2** | 导出物形状合法（函数 / 类 / 带 `apply` 的对象） | FAILED(3) | `invalid plugin, expect function or object with an "apply" method, received <typeof>` |
| **L3** | `Config` 校验不抛（有 `Config` 时；且**必须同步**） | FAILED(3) | `ValidationError` / `TypeError: Async config validation is not supported` |
| **L4** | `apply()` 不抛 | FAILED(3) | 原始 reason 由 `fiber.await()` rethrow |
| **L5** | `inject` 的服务最终被提供 | PENDING(0) | `<name>: pending (waiting for service: <missing>)` |

汇总点：`assertEntriesActivated` 在 boot 末尾遍历 `ctx.loader.entries()`，把 FAILED 与 PENDING 都拼成 `<binName>: N entries did not activate\n<name>: <stack>`，`boot()` 捕获后 dispose 并抛 `dsh: plugin tree failed to load: ...` [E: gt-profile-plugin.md#C2, #C3, #结论摘要-7]。
另有第六条兜底（不属于「不变量」但会让 boot 失败）：`assertEntriesLoaded` 对「fiber 为 undefined 且未 disabled」的 entry 报 `plugin(s) failed to load: <names>`；以及 `installFailLoud` 把迟到的 unhandledRejection 变成 exit(1)（带 2 秒 terminal release 窗口）[E: gt-profile-plugin.md#C3, #C4]。

### D.3 boot 门的形态（可运行）

boot 门属于 GC-0（见 01-CONTRACTS §6.2 的成员列表）。它由**四段**组成，**四段全绿才算通过，任一段缺席即红**（缺席不是通过——见 §9.19）。

```bash
#!/usr/bin/env bash
# checks/gc0/boot_gate.sh —— GC-0。四段全绿才通过；任何一段的产物缺席即红。
set -Eeuo pipefail
PROFILE=academic-research

# ── 第 0 段：门自身的完整性（必须是第一行，见 §9.22 / M8）
#    〔裁定 · S0 实测，[E: .loop/m0/M0-7.json]〕锚点是 40 位 commit sha，且**必须由仓库外传入**：
#    任何从仓库内文件（含 BASELINE.ledger、含 tag 名）读锚点的写法都被红样本 R3 骗过（仓库内入口 exit 0）。
#    本脚本自身也在 checks/ 里，所以这一段只在「boot_gate.sh 是仓库外 runner 从 GATES_PINNED_SHA
#    展开出来的那一份」时才算数——直接在仓库内跑 boot_gate.sh 不构成证明，只是自查。
: "${GATES_PINNED_SHA:?refuse: pinned sha must be supplied by the out-of-repo runner}"
[[ "$GATES_PINNED_SHA" =~ ^[0-9a-f]{40}$ ]] || { echo "BAD PIN: not a 40-hex commit sha"; exit 1; }
checks/gate_integrity.sh "$GATES_PINNED_SHA"   # porcelain 干净 + 工作树 checks/ 与 git archive <sha> 逐文件 sha256 相同

# ── 第 1 段：组合成立 + 零 patch warning + 两个用户层被钉死
#    ⚠️ 这一段只证明「组合成立」，不证明模块可 import、不证明 Config 有效。[E: gt-profile-plugin.md#设计含义-8]
DUMP=$(mktemp); WARN=$(mktemp); DEFDUMP=$(mktemp)
dsh --profile "$PROFILE" --dump-config >"$DUMP" 2>"$WARN"
# 行 id 必须整行锚定匹配：`id: web` 会被 `id: web-search-deepseek` 假命中
for row in agent-loop tool-subagent tools code-runtime spill-policy tool-result-pruner tool-web \
           web headless-startup headless-runner academic-fetch; do
  grep -qE "^[[:space:]]*-?[[:space:]]*id:[[:space:]]+${row}[[:space:]]*$" "$DUMP" \
    || { echo "MISSING ROW: ${row}"; exit 1; }
done
# patch 匹配不到目标行 —— 静默失效是本机制的头号风险 [E: gt-profile-plugin.md#B3]
#
# 〔裁定 · S0 实测，[E: .loop/m0/M0-3c.json]〕**这条 grep 必须读 `--dump-config` 的 stderr，
# 不能挪到第 2 段去读真实 boot 的 stderr。这一行是本段不可移动的部分。**
# 理由是实测出来的，不是风格偏好：同一个临时 DSH_HOME、同一份写错 id 的 patch 文件，
#   warnings_on_dump_config=2      ← `--dump-config` 路径报了 2 条 `patch: entry "<id>" not found`
#   warnings_on_real_boot=0        ← 真实 boot 路径**一条都没有**
#   real_boot_reached_llm=1        ← 同次命令里 `dsh: AUTH` 证明真实 boot 确实跑到了 LLM，
#                                     排除了「真实 boot 根本没起来所以没输出」这个解释
# 即：patch 打不中比 v1 文档写的「只 warn 不 fail」**更坏**——它在真实运行路径上**彻底静默**。
# 后果：**这件事只能靠 `--dump-config` 检测。真实 boot 那一步再怎么 grep stderr 都抓不到。**
# 谁把这条 grep 并进第 2 段，就会静默失去这道检查，而门依然全绿。
# 命中判据（正向，实测）：换成真实 id 后 `patch: entry` 计数为 0，且目标行上方出现溯源注释
#   `# == @deepseek-ai/dsh-base, patched by <你的 patch 文件>`，且该行的 config/disabled 确实变了。
# ⚠️ 残余（M0-3c honest_limits）：本轮只实跑了 `- id: <x>` 形式的未命中；下面 grep 里
#   `patch insert:` 与 `name mismatch` 两个分支的文案来自编译产物阅读，**未实跑**。
#   且只在 headless profile 上测过；web profile 的真实 boot 是否打印该 warning 未测。
grep -Eq 'patch: entry .* not found|patch insert: entry .* (not found|is not a group)|name mismatch' "$WARN" \
  && { echo "SILENT PATCH FAILURE"; cat "$WARN"; exit 1; }

# ── 第 1a 段：呈现模式必须是字面量 native，Code Mode 执行能力必须被 disabled（C-12a）
#    实测：DSH_TOOLS_MODE=code 时 dump 输出逐字不变，所以「dump 里还剩一个 !!js」本身即红。
node checks/gc0/assert_tools_presentation.mjs "$DUMP"
#    该脚本的三条断言（YAML 解析后按 id 定位，不做行级 grep）：
#      A. rows['tools'].config.mode === 'native'（**字符串字面量**；出现 !!js / undefined / code / both 即红）
#      B. rows['code-runtime'].disabled === true
#      C. 全树任何一行的 config 里不得残留形如 `!!js process.env.DSH_TOOLS_MODE` 的表达式
#    并且它把 A/B 的实测值写进 runs/<run_id>/manifest.json 的 runtime_fingerprint（W-12）。
#
# 〔裁定 · S0 实测，[E: .loop/m0/C-12a.json]〕上面那三条断言有一个**进程级盲区**：
# 它们读的是 dump，而 **dump 对 `DSH_TOOLS_MODE` 完全不可观测**（实测：设与不设该变量，
# `tools` 行的 dump 输出逐字相同，都是 `mode: !!js process.env.DSH_TOOLS_MODE`）。
# 补一条零成本的正向断言，把「产出这份 dump 的那个进程」的环境也钉住：
test -z "${DSH_TOOLS_MODE:-}" || { echo "DSH_TOOLS_MODE SET IN GATE ENV: $DSH_TOOLS_MODE"; exit 1; }
# **它挡住什么**：门自己这个进程的环境里带着 `DSH_TOOLS_MODE`——而第 1 段的 `--dump-config`
#   正是这个进程跑的，所以这条断言让「本门读到的这份 dump 未被 env 污染」成为机器事实。
#   在 §A.3 第 0 块的 pin 落地**之前**，以及对任何我们没 pin 的 `!!js` 行，这是唯一能拿到的正向信号。
# **它挡不住什么**（三条，必须写明，否则它会被误当成密封）：
#   ① 它只证明**门这个进程**此刻的 env。真正跑 dsh 的若是另一个进程（CI runner / launchd /
#      被 workflow spawn 的子进程），那个进程的 env 本门看不见。
#   ② `ctx.tools.presentAs()` 这条 **agent 级**绕过路径未测：`dsh-tools` README 明写单个 agent
#      可为自己选 code 模式，§A.3 那两行对它是否有效**没有验证**（C-12a honest_limits ③）。
#   ③ 本轮只测了 `DSH_TOOLS_MODE=code`，**`both` 与非法值（如 `bogus`）的行为未测**。

# ── 第 1b 段：两个机器级用户层（C-12b —— 旧门只看了其中较弱的那个）
# (i) home patch 层：真实存在于层序里（composeProfile: bundle → profile → home → --patch → telemetry）
test ! -e "${DSH_HOME:-$HOME/.dsh}/cordis.patch.yml" || { echo "HOME PATCH LAYER PRESENT"; exit 1; }
# (ii) --patch overlays 排在 home 层之后，级别最高：门自己不得被 overlay 掺水
#      dump 与 dump-default 的差集必须恰好等于「我们自己的 profile 层」这一份已知 delta
dsh --profile "$PROFILE" --dump-default-config >"$DEFDUMP" 2>/dev/null
diff "$DEFDUMP" "$DUMP" > "$WORK/layer.delta" || true
cmp -s "$WORK/layer.delta" checks/gc0/expected/layer.delta \
  || { echo "UNEXPECTED USER/OVERLAY LAYER DELTA"; diff checks/gc0/expected/layer.delta "$WORK/layer.delta"; exit 1; }
# (iii) $DSH_HOME/settings.yaml —— 真正能静默改掉模型路由的那个文件。
#       它对两个 dump 命令**双双不可见**，所以必须单独断言。
#       〔裁定 · S0 实测，[E: .loop/m0/C-12b.json]〕「settings 覆盖整条 patch 链」不再是读 README
#       得来的推断，而是运行实测：同一个 DSH_HOME 里 `cordis.patch.yml` 把模型钉成
#       `PATCH-BOGUS-MODEL`（它是 patch 链的最后一层），`settings.yaml` 写 `SETTINGS-BOGUS-MODEL`，
#       真正发到 API 的是后者（`you passed SETTINGS-BOGUS-MODEL`）。该失败发生在模型生成之前，
#       不含模型输出，完全确定。
node checks/gc0/assert_settings_overlay.mjs   # 见下方判定核心
#       ⚠️ **本段的残余风险（S0 实测，写在这里而不是只写在 §D.5）**：`dsh-settings-file` 出厂
#       `watch: true` **热重载**。因此 `assert_settings_overlay.mjs` 的「值级白名单 + sha256 入
#       manifest」**只能证明 boot 那一刻**——运行途中有人改 `settings.yaml`，新值会被热发布，
#       而这道门（它只在 boot 期跑一次）**看不见**。
#       机器判据上的收口只做到这一步：manifest 里的 `settings_sha256` 是**运行起点**的值，
#       任何据此声称「本次运行全程的模型路由如 manifest 所载」的句子都是假的。
#       ⚠️ 更进一步的残余：热重载本身**未实测**（没有在一次运行途中改文件观察是否真的生效），
#       `watch: true` 的后果是从 README 读来的；且本轮只用 `agent-default-model` 一个 namespace
#       验证了覆盖，`llm-pi-ai.providers`（活体注册全新 provider 路由）、`ya-subagent`、
#       `auto-compact` 这三个**威胁更大**的 section 只按同一机制推断，未实测。

# ── 第 2 段：真实 boot（这一步才覆盖 L1..L5）
#    调用形式已实测确认（R3）：任务是**位置参数**，`dsh --profile <name> "<task>"`。
#    用故意无效的 LLM 密钥：期望走到 AUTH 失败，而不是 plugin tree failed to load。
#    实测基线（headless + 本节两行 pin）：退出码 1，stderr 唯一一行
#      `dsh: AUTH: Authentication Fails, Your api key: ****xxxx is invalid`
BOOT=$(mktemp)
DEEPSEEK_API_KEY=invalid-on-purpose-gate-probe \
  dsh --profile "$PROFILE" 'noop' >"$BOOT" 2>&1 || true
# 〔裁定 · S0 实测〕模式写的是**单数** service，不是 services。
# dsh-app-boot 逐字：`const subject = missing.length === 1 ? "service" : "services"`
# ——缺一个服务时输出单数，而那正是最常见的场景。
# 原文写成 'pending (waiting for services' 会**恒不命中**单服务场景，
# 即：这道 boot 门会以全绿出厂，却抓不到它被写出来要抓的那个失败。
# 单数前缀同时覆盖单复数两种输出。
# 这条是 S0 实测抓到的，不是读代码读出来的——读代码的人（包括写这段的我）看不出单复数会差这一次。
for pat in 'plugin tree failed to load' 'did not activate' 'pending (waiting for service' \
           'failed to load:' 'invalid plugin, expect function or object'; do
  grep -qF "$pat" "$BOOT" && { echo "LOAD-TIME INVARIANT VIOLATED: $pat"; cat "$BOOT"; exit 1; }
done
# 正向信号一：必须真的走到 AUTH，否则这一段是一条不会红的检查（见 §D.5 第三条）
grep -qE '^dsh: AUTH:' "$BOOT" || { echo "NO AUTH SIGNAL — gate is vacuous"; cat "$BOOT"; exit 1; }
# 正向信号二：我们的插件必须留下注册痕迹
grep -qF 'academic-fetch' "$BOOT" || { echo "NO REGISTRATION TRACE — gate is vacuous"; exit 1; }

# ── 第 3 段：纪律断言（DSH 不帮你抓的那条）
node checks/gc0/assert_plugin_exports.mjs packages/dsh-academic-fetch   # Config['~standard'].validate 存在且同步

# ── 第 4 段：红样本必须全红（red-first，§6.5.1）
node checks/gc0/boot_gate_selftest.mjs   # 六个坏 fixture，每个必须以对应文案红；fixture 数 != 6 也算红
```

`assert_plugin_exports.mjs` 的判定核心（**同步性也要断言**，因为异步 validate 会抛）：

```js
const mod = await import(new URL('lib/index.js', pkgUrl));
const v = mod.Config?.['~standard']?.validate;
if (typeof v !== 'function') fail('no Standard Schema v1 Config export');
const probe = v(SAMPLE_CONFIG);
if (probe && typeof probe.then === 'function') fail('async Config validation will throw at load');
if (typeof mod.apply !== 'function' && typeof mod.default !== 'function') fail('no apply/default');
```

### D.4 红样本：六个 fixture，六种红

| fixture | 制造方式 | 期望的红 |
|---|---|---|
| `f-L1-import` | `lib/index.js` 里写一个 `import` 不存在的裸包 | `failed to import loader entry` |
| `f-L2-shape` | 导出一个字符串 | `invalid plugin, expect function or object with an "apply" method` |
| `f-L3-config` | `Config` 要求一个必填字段，patch 里不给 | `ValidationError` 路径 → `did not activate` |
| `f-L3b-async` | `Config['~standard'].validate` 返回 Promise | `Async config validation is not supported` |
| `f-L4-apply` | `apply()` 第一行 `throw` | `did not activate` + 原始 stack |
| `f-L5-inject` | `inject: ['nonexistent-service']` | 逐字 `<pkg>: pending (waiting for service: nonexistent-service)`，**且退出码 1**〔裁定 · S0 实测，[E: .loop/m0/M0-3a.json]〕 |

〔裁定 · S0 实测，[E: .loop/m0/M0-3a.json]〕**`f-L5-inject` 的期望文案现在是实测原文，不再是构造的**：把同一份插件的 `inject` 写成 `['toolRuntime']` 跑真实 boot，逐字得到 `pending (waiting for service: toolRuntime)`，退出码 1，boot 在到达 LLM 之前就死在未激活 entry 上（对照组只改这一个字符串写 `['tools']`，同一命令走到 `dsh: AUTH`）。两条随之固定下来的判据：
① 文案是 **`<包名>: pending (waiting for service: <服务名>)`**，**`service` 用单数**（`dsh-app-boot` 逐字 `const subject = missing.length === 1 ? "service" : "services"`，缺一个是最常见情形）；
② **这个 fixture 测的是一次响亮失败，不是静默失效**。任何把它描述成「插件静默不生效 / fiber 静默停在 PENDING」的文字都与实测相反，必须删——`assertEntriesActivated()` 无条件枚举未激活 entry 并抛错。它与 §A.3 顶部对照裁定的 ① 类（patch entry id 猜错，真静默）**不是同一类失败**。

〔裁定 · R1〕**为什么是六不是五**：五条加载期不变量对应五个 fixture，但 L3（Config 校验抛）
被拆成同步抛（`f-L3-config`）与**异步 validate 抛**（`f-L3b-async`）两个独立样本——
后者的一手依据是 `Config["~standard"].validate` 这条 Standard Schema v1 接缝上**异步 validate 会抛**
[E: GROUND-TRUTH-CORRECTIONS.md#A4]，它的失败文案与同步分支不同，合并测会漏掉一整条分支。

原文三处散文写「五个」而 D.4 表实际列了六行，同时 §D.3 又要求断言「恰好有 N 个」。
照散文实现会写成 `== 5`，而表要求 6 个——**这道门会永久红**。
一道永红的门在两周内一定会被 `|| true` 掉，那等于回到空心门，只是更难发现。
这类「散文计数与表格计数不一致」的缺陷现在由 gates/check_doc_metrics.mjs 一类的自述数字门兜住。

**并且**：`boot_gate_selftest.mjs` 必须先断言「fixture 目录里**恰好有 6 个** fixture」再逐个跑（N 必须是字面常量，不得写成「至少 N 个」——见下方裁定）。理由是空集/缺集的 vacuous truth 是本仓库已实证的盲区，`selftest_fidelity.mjs` 专门为此播了 EMPTY-RUN 红样本 [E: gt-house-method.md#M5]。

### D.5 boot 门的诚实边界（攻击者会问的）

- **第 1 段不证明任何运行时事实。** dump 少两层（§C-12）。〔裁定 · S0 实测，[E: .loop/m0/M0-3c.json]〕原来写「dump 路径的 warn 是否 100% 覆盖 boot 期 warn **未验证**」，本轮在 entry-id 未命中这一类上测到了**反方向且更强的结论**：dump 报 2 条、**真实 boot 报 0 条**，即 boot 期在这一类上根本没有 warn 输出，覆盖关系是 `dump ⊋ boot = ∅`。**这使第 1 段成为不可替代的一段，而不是第 2 段的冗余。** 仍未偿的部分：① `dsh-app-boot` 的文档注释逐字写着 patch 未命中「mirroring the Loader's boot-time warning」，与实测的真实 boot 零输出**不符**，本轮**没有深究**是 headless 未接 logger sink 还是别的原因；② group-child 盲区下两边是否会在**其他类别**的 warn 上不一致，仍需构造反例 [E: gt-profile-plugin.md#未决-3]；③ 只在 headless profile 上测过。
- **第 2 段的启动子命令形式已实测闭合**〔裁定 · S0 实测，[E: .loop/m0/M0-3a.json], [E: .loop/m0/C-12a.json]〕。形式是 **`dsh --profile <name> [--patch <path>]* '<task>'`——任务是位置参数**，本轮 S0 的每一条 boot 相关证据命令都逐字用了它并跑通（`DEEPSEEK_API_KEY=invalid-on-purpose-gate-probe dsh --profile headless 'noop'` 稳定产出 `dsh: AUTH`，`dsh: AUTH` 即「boot 成功、失败发生在 LLM 认证」的判据）。**这条不再是 open question。** 残余：只在 headless profile 的 CLI boot 路径验证；web profile 与 HMR 热重载路径未测。
- **`settings.yaml` 的哈希只证明 boot 那一刻。** 〔裁定 · S0 实测，[E: .loop/m0/C-12b.json]〕`dsh-settings-file` 出厂 `watch: true` **热重载**，而第 1b (iii) 段只在 boot 期跑一次。运行途中改 `settings.yaml` 会被热发布，**这道门看不见**，而 settings 是实测中**压过整条 patch 链**的那一层（`you passed SETTINGS-BOGUS-MODEL`）。⇒ manifest 里的 `settings_sha256` 是**运行起点**的值；任何据此声称「本次运行全程的模型路由如 manifest 所载」的句子都是假的。热重载本身**未实跑**（`watch: true` 的后果读自 README），且只用 `agent-default-model` 一个 namespace 验证过覆盖——`llm-pi-ai.providers` / `ya-subagent` / `auto-compact` 三个威胁更大的 section 是推断。
- **第 2 段依赖「AUTH 失败」这个可区分信号。** 若某次改动让无效密钥不再产生可区分的失败，这一段会变成一条**不会红的检查**。对策：第 2 段同时断言 boot 日志里出现了我们插件的注册痕迹（一条 `tool/call` 之前的启动事件），而不是只断言「没有 load 失败」。

---

## §E 运行时约束清单

> 规划期就要认账的硬事实。每条：一手出处 + 设计应对。**这些不是风险登记，是已经确定为真的运行时行为。**

### E.1 并发与预算

| # | 硬事实 | 一手出处 | 设计应对 |
|---|---|---|---|
| E-1 | **不存在单一并发上限**，存在五条互不相同、由不同包强制的闸门（10 / 12（硬顶 16）/ 无限 / 10 / 10） | [E: gt-orchestration.md#结论摘要-1] | 见 §B.5 的表。**批量扇出唯一入口是 workflow**（〔裁定 B-4〕） |
| E-2 | **出厂 `subagent` 与 `subagent_fork` 都是 `continuable`**，而 continuable 路径**运行时不设上限**（`dsh-subagent` 整包无 Config，续接管理器无 per-parent 计数） | [E: gt-orchestration.md#结论摘要-2, #C8, #设计含义-1] | 〔裁定〕profile 层把 `tool-subagent` 显式配回 `one-shot`，把 `tool-subagent-fork` 直接 `disabled`。**理由不只是并发**：continuable fork 子代理会先装 `report` 工具与其 prompt 段落（位于继承历史**之前**），从而**让全部继承前缀的缓存失效** [E: gt-orchestration.md#X3] |
| E-3 | `maxParallelToolCalls` 出厂 10，**且它是用户可热改的 Settings 项**（下一个 tool group 生效，无需重启） | [E: gt-orchestration.md#G1；gt-profile-plugin.md#I] | **它不是安全边界。** 我们显式写 4；真正的并发闸是中央限速网关（C-20），网关的额度不受 Settings 影响 |
| E-4 | 并行组**遇到第一个非并行安全的调用立即中断**；提交顺序始终是模型序 | [E: gt-orchestration.md#G2, #G3] | 编排脚本不得在一组 `subagent` 调用中间夹 exclusive 工具（如 goal 类工具），否则 20 个并排调用会退化成串行 |
| E-5 | workflow 的 `maxConcurrentAgents` 出厂 `0` → `min(16, max(1, availableParallelism()-2))`；本机 `availableParallelism()` = 14 → **12**；**无论多少核硬顶 16** | [E: gt-orchestration.md#E4, #未决-3] | **显式写死**，不吃 CPU 推导——2 核 CI 上该式退化为 1 |
| E-6 | `maxTotalAgents` 的 per-run 覆写**只能降不能升**；`AGENT_CAP` / `ITEM_CAP` / `AGENT_START` / `AGENT_RESULT` 是 fatal，会穿透 `parallel()` 终止整个 run | [E: gt-orchestration.md#E4, #E5, #设计含义-9] | 大批量扇出必须主动分批，不能一次 `parallel(4096 items)` |
| E-7 | **两个轮预算是不同的东西**：goal 的 `defaultMaxGoalRounds` 出厂 256（确认）；ralph 的 `maxRounds` README 与代码 schema 都写 256，**出厂全部组合覆盖为 64** | [E: GROUND-TRUTH-CORRECTIONS.md#A10；gt-orchestration.md#X1, #X2] | 见 01-CONTRACTS §9.24。本 profile `disabled` ralph（〔裁定 E-3〕：它每轮只有一个 child、轮内无扇出、**完成是 worker 自述而无独立评审**、普通 child 失败即终止不重试、只有轮数一种预算 [E: gt-orchestration.md#F3, #F4]） |
| E-8 | goal 的 `activation` **永不持久化**；`blockedAfterConsecutiveRounds` 出厂 3，但运行时只强制轮数计数，「是不是同一个障碍」完全是模型判断 | [E: gt-orchestration.md#A1, #A2, #A5] | **不宣称「无人值守跑一夜」**。若用 goal，必须在障碍指纹上加我们自己的机器比对（写进 workspace 再比） |
| E-9 | LLM 重试出厂：normal / **2 次** / 500ms→10s / ±10% jitter / 5 个可重试 code；**没有任何全局请求并发限制器**（grep 零命中） | [E: gt-orchestration.md#I2, #I6] | 限流必须由我们的中央网关主动做。⚠️ `always` 模式无次数上限会重试永久性失败（认证/配额/非法请求），**不要开** |
| E-10 | `list_agents` **无游标、无上限**，持久化的子会话永远留在列表里 | [E: gt-orchestration.md#K4] | **禁止把 `list_agents` 作为常规轮询手段**——超并行 + 长跑下它是一条线性膨胀的 token 泄漏路径 |

### E.2 上下文、压缩与证据存活

| # | 硬事实 | 一手出处 | 设计应对 |
|---|---|---|---|
| E-11 | spill 出厂 `maxInlineBytes: 50000` **字节**；超阈值纯文本结果的原文**只在 spill 文件里**，不在 session 日志里；spill root 出厂**未配置**，落 OS temp 私有目录 | [E: gt-evidence-substrate.md#E2, #E4, #E5] | 抓取工具**在执行内**直接写 CAS，不依赖事后从日志捞原文（01-CONTRACTS §4 W-01） |
| E-12 | tool-result pruner 出厂 `thresholdChars 8192 / headChars 4096 / tailChars 1024`；装载期硬约束 `head + marker(39) + tail ≤ threshold`；**只在压缩合格时才跑**，below-pressure 的 step 检查从不 prune | [E: gt-evidence-substrate.md#D3, #D5] | 工具结果不承载证据原文，只承载句柄。⚠️ 本机实测存在 23,295 / 27,922 字符的 `tool/result` **未被 prune**——说明 8192 不是逐结果硬上限 |
| E-13 | prune 的替换事件用 `...event.data` 展开，**`meta` 原样保留**；原始事件在原 seq 处纹丝不动 → 对读原始日志的门，prune 完全透明 | [E: gt-evidence-substrate.md#D4] | 这是 §C-2 落点成立的关键。**但见 E-14** |
| E-14 | **压缩从未在本机触发过**（139 个 session、0 条 replace、0 条 `compaction/*`）→ 我们对 compaction/pruner 的一切结论都是**代码级而非运行级** | [E: gt-evidence-substrate.md#D5, #未决-6] | **必须补一个「小 contextWindow 路由 + 强制 compact」的实测场景**，实测证据锚点在真实压缩后的存活情况。在此之前，E-13 按「代码级论证，未运行级验证」对待 |
| E-15 | compaction-basic 出厂 `thresholdRatio 0.8` / `retainRatio 0.16` / `maxTokens 8192`；`compaction/summary` 记录了写摘要的 LLM 路由与 model | [E: gt-evidence-substrate.md#D6] | 「这段摘要是谁写的」有持久答案，可直接支撑「散文不是地面真值」的产品叙事 |
| E-16 | 实测 `request/context`：`{"provider":"deepseek-official","model":"deepseek-v4-pro","contextWindow":1000000}` | [E: gt-evidence-substrate.md#F4] | 上下文窗口不是当前瓶颈；瓶颈是每 host 的 RPS（E-19） |
| E-17 | `ctx.tokenMeter.measure()` 是**固定启发式**（4 字符/token + 结构开销，「Any key is rejected」），**对 CJK 与 JSON schema 系统性低估**；三个 projection 全是累计/last-wins，无 per-step 分解 | [E: gt-evidence-substrate.md#F1, #F2] | 预算门用 `measure()`（与 compaction 同源，不会打架）；**成本报表用日志 fold 出的 per-step usage**（§C-3）。见 01-CONTRACTS §4.3 |

### E.3 执行与安全边界

| # | 硬事实 | 一手出处 | 设计应对 |
|---|---|---|---|
| E-18 | `run_code` 出厂：`computeMs 60000` / `maxWallMs 600000` / `maxOutputBytes 67108864`（64 MiB）/ `maxOldGenerationSizeMb 512`；worker `env: {}`（**拿不到 API key**——〔裁定 · S0 实测，[E: .loop/m0/M0-4.json]〕已从代码依据升为实测：程序体里 `Object.keys(process.env).length` **= 0**。但它**只挡凭据，不挡文件系统**：同一程序体 `await import('node:fs')` 写文件成功）；64 MiB 是**拒绝边界**，超限字节永远到不了 spill 层；中间 binding 值**无字节上限** | [E: gt-exec-security.md#D-1, #D-2, #D-8] | 密钥由宿主侧工具（binding）持有，程序只拿结果。大结果**落盘 + 只返回句柄**，不要 `return` 大对象。profile 里显式写死这四个值（§A.3） |
| E-19 | 每 host 的 RPS 是超并行的真正瓶颈，**具体限额与其中一条已失效的旧值见 01-CONTRACTS §6.3 硬要求 5**（本文件不复述数字与口径警告） | [E: ext-academic-apis.md#D2] | 架构后果有三条：①中央网关按 host 分桶，**arXiv 那一桶必须是串行队列而不是令牌桶**；②网关是**跨进程**的单一权威，子代理拿不到裸密钥；③任一子代理收到 429 必须让整个桶**集体退避**，而不是只让那个子代理睡——否则其余子代理继续撞墙、把退避时间无限拉长 [E: ext-web-providers.md#D2] |
| E-20 | OpenAlex：单实体 lookup **$0 / 0 credit**（实测响应头 `x-ratelimit-credits-used: 0`）；list+filter $0.0001；search / semantic search $0.001；内容下载 **$0.01/篇**，免费档 **约 100 篇/天**（官方原文 "about 100 files per day"）。全部为 **2026-08-17** 实测/文档口径 | [E: ext-academic-apis.md#A3, #A7；核验表 #3/#6/#7] | 检索架构围绕「已知 DOI/ID → 免费单实体 lookup」组织：**先用便宜的发现层拿到 ID，再用免费的 lookup 拿全量元数据**。单价**读自响应头**而非硬编码；同时读 `x-ratelimit-remaining-usd` 以区分「今天钱花完了」与「退避一下再试」，否则会陷入死循环 |
| E-21 | 全文可得性有一个**物理上限**，且 G5 的真实上限还要更低——**具体比例、其 corpus 口径警告、以及未测量的第二层损耗，见 01-CONTRACTS §3.2**（本文件不复述） | [E: ext-academic-apis.md#A7, #A10] | 对架构的直接后果：**取证预算必须按「可得全文的那一小部分」而不是按检索命中数来规划**；命中但取不到全文的条目走 §3.3 的低等级路径而不是排队重试。产品承诺侧的处理见 §3.2 结论，本文件不重复 |
| E-22 | 本机**没有任何 fetch provider 包**；`web_fetch` 出厂关闭（`tool-web: {fetch: false}`）；`WebFetchBody` 是 `html \| text` 封闭联合、**无 PDF 臂**；`web_search` 唯一出厂 provider 是「一次完整 Messages 模型调用」，出厂 `searchMaxResults: 8`、`searchTimeoutMs: 60000` | [E: gt-exec-security.md#E-3~E-7] | 检索与抓取工具全部自建（§B.2）。⚠️ **引用任何「抓取上限」数字前必须确认本机实际装了哪个包**：流传的「web_fetch body 上限 10 万字符」是本 build **未安装**的那个 provider 的常量 [E: GROUND-TRUTH-CORRECTIONS.md#A6] |
| E-23 | web 工具**无任何审批策略**（两个工具都不请求 `ctx.approval`，包也不定义持久 URL/域名授权） | [E: gt-exec-security.md#E-9] | 域名策略必须由我们自己的 `tools/pre-execute` 实现（这也是 T0-HARD「不发请求」的落点，§8.6.3） |
| E-24 | **不要挂 `dsh-tool-cordis`**：它自陈 "Treat this toolset like bash access"；`cordis_inspect what:"api"` 渲染的 API 目录里就包含 `approval` 的 `setPolicy(agent, policy)` 签名——**模型可以读到并调用切换审批策略的入口** | [E: gt-exec-security.md#H-6] | profile 里确保该行不存在。boot 门第 1 段可加一条负向 grep |
| E-25 | bash 沙箱超时出厂 `timeoutMs: 60000` | [E: gt-orchestration.md#设计含义-4] | 长跑复算走 `run_in_background`（占 jobs 的 10 槽）或拆分 |

### E.4 profile / 插件机制

| # | 硬事实 | 一手出处 | 设计应对 |
|---|---|---|---|
| E-26 | patch 的**每个顶层键整体赋值**，`config` 整体被换掉，**无深合并**；`name` **不能被 patch 改写**（要换实现只能 disable 旧行 + insert 新行）；patch 匹配不到**在真实 boot 路径上零输出**（〔裁定 · S0 实测〕比旧写法「只 warn 不 fail」更坏：warn **只在 `--dump-config` 路径**出现，真实 boot 完全静默） | [E: gt-profile-plugin.md#B3, #B4]；[E: .loop/m0/M0-3c.json] | 整体替换时必须把该行原有的键**一起写回**（`agent-loop` 的 `agents: []` 是最容易翻车的一个）。boot 门断言零 patch warning，且**必须读 `--dump-config` 的 stderr**（§D.3 第 1 段）——挪到第 2 段会静默失去这道检查 |
| E-27 | 单次 pass 的盲区：若某层用 `config:` 整体替换了一个 group 行的子列表，新引入的子行**不会进 id 索引**，后续层按 id patch 它们会 warn+skip | [E: gt-profile-plugin.md#B6] | 不要整体替换 group 行的 `config` 数组；要加子行就用 `insert` 带 `id` |
| E-28 | bundle 顺序即命运：两个 bundle 都 patch `id: web` 的 `searchProvider` 时**只有最后一个生效且无任何警告**（本机 web profile 实证） | [E: gt-profile-plugin.md#B5] | 〔裁定 B-1〕不与 serper 争 `web.searchProvider`。若确需换，让 profile 的 `cordis.patch.yml` 作最终仲裁 |
| E-29 | `dsh.client`-only 的包**不会被 reconcile 加进 bundles**（`exportsPatch` 只看 `dsh.bundle.patch`），必须在 profile 的 patch 里手写 `insert:` | [E: gt-profile-plugin.md#D5] | 安装第三方插件后必须 `--dump-config` 确认它真的进了树，光靠 `dsh plugin add` 不够 |
| E-30 | `cordis.yml` 每次启动被无条件重写为 `[]`；原因是 vendored Loader 有「插件自我 dispose 就把当前树写回文件」的行为，不重写会让 bundle 的 insert 下次启动重复一遍 | [E: gt-profile-plugin.md#A3] | 别编辑它；别把它纳入版本控制的期望值 |
| E-31 | `DSH_*` / `XDG_*` / `DYLD_*` / `BASH_FUNC_*` 写进 `.env` **直接 throw**，只能由启动环境提供 | [E: gt-profile-plugin.md#H4] | 运行脚本用 `export`；业务密钥（`OPENALEX_API_KEY` 等）可放 `.env` |
| E-32 | 宿主包写成 regular dependency 会让 pnpm 装第二份副本，宿主工具分发器解析到错误模块实例，**每次工具调用都死** | [E: gt-profile-plugin.md#D6] | 一律 `peerDependencies`；`pnpm-workspace.yaml` 预留 `overrides` 位 |

### E.5 一条关于「诚实边界」的总约束

**能强制的手段与产物级兜底见 01-CONTRACTS §4.4**。本文件补的是它的否定面——**下列四件事在本安装版上不可强制，任何声称它们的句子都是会被攻破的假话**：网络围栏（沙箱词汇是纯文件效果，C-21）、`toolFilter` 当权限上限（C-11）、`run_code` 被沙箱围住（C-8）、「模型不可能凭记忆编造引用」（C-27）。四条各有一手依据，**已在 §C 逐条给出**。

---

## §F 本模块划分的已知弱点

> 诚实记账适用于本文件自己。以下是我知道的弱点，按「攻击者最该先打哪个」排序。

1. **M2 的双宿主是本划分最脆的接缝。** 同一份 CAS/schema 代码同时被 DSH 进程内的 M1 与进程外的 M3 加载。`LAYOUT_VERSION` 断言是我的对策，但**该对策本身尚未被任何实证背书**——本仓库没有同类先例。若两边通过不同的包管理路径解析到不同副本（正是 `dsh-subagent-effort` 那个事故的形状 [E: gt-profile-plugin.md#D6]），断言可能双双读到「自己那份的正确版本」而不报错。**这条需要一个专门的红样本：故意让两边解析到不同副本，断言必须红。**

2. **「先建门，后建被门检查的东西」这条顺序在 M1 上会遇到鸡生蛋问题。** M3-GC0 的红样本需要真实捕获的事件形状（房内纪律要求事件形状必须来自真实捕获而非手编 [E: gt-house-method.md#A9]），而真实事件要等 M1 存在才有。**当前的解**是先用 serper-harvester 已有的真实捕获样本做形状源，M1 上线后再重播一次。这个解**尚未验证形状是否可迁移**——serper 的 `tool/result` 与我们带 `meta.evidence` 的形状不同。

3. **中央限速网关是一个纯自建的跨进程单点，DSH 侧零支撑。** 它一挂，所有取证停摆；它有 bug，就是一个既不在 DSH 的可观测面上、也不在门的判定面上的隐形故障源。而它必须是跨进程的（子代理可能是独立进程 [E: ext-web-providers.md#D2]）。**本文件没有为它设计故障模式与降级路径**，只把它列为 C-20。

4. **`run_code` 旁路让「太严的门」成为真实风险。** 产物级兜底（§4.4）说未被 `tool/call` 覆盖的断言一律 ST-N。但 `run_code` 里的子调用**确实**会落 `tool/code-dispatch` 事件 [E: gt-exec-security.md#D-10]，而一次用 `node:fs` 直接写的抓取则不会。〔裁定 · S0 实测，[E: .loop/m0/M0-4.json]〕**这条弱点的前半段已从假设变成事实**：`node:fs` 在 `run_code` 程序体里可达（`await import('node:fs')`，`require` 不在作用域），且同一 read-only 策略下它写文件成功而 bash 路径被拒——所以「绕开我们记录路径的抓取」不是理论可能，是已实跑的动作。这意味着一条**真实且正确**的证据可能因为取得路径不对而被判 ST-N。房内的教训是「一个逼着记录说假话的门，和一个放行假话的门一样坏」[E: gt-house-method.md#M11]。**本划分选择了严的一侧，但没有量化它的假阴性率。**

5. **compaction 的证据存活是代码级论证，不是运行级证据。** E-13/E-14：本机 139 个 session 从未触发过压缩。M1 的整个证据锚点方案建立在「pruner 用 `...event.data` 展开会保留 `meta`」这条代码事实上——**读代码读对了，但没跑过**。

6. **headless-first 让 preset 路线完全未被验证。** 〔裁定 B-3〕的第三条理由本身是一个未决问题（headless 下 `agentPresets.mount` 是否会被调用未从代码确认 [E: gt-profile-plugin.md#未决-5]）。如果将来需要真正的角色级工具隔离，我们会发现自己既没走 preset、又只有一个**不是权限天花板**的 `toolFilter`。

7. **八个模块本身是 P-1′ 的靶子。** 01-CONTRACTS §9.30 说结构投资必须自证增益（A/B），而不是默认无罪。**本文件划出了八个模块，一个也没有附 A/B 计划。** 唯一被多轮复制的结构收益是可审计性与有界 resume 状态——M2/M3/M8 可以论证落在这两项上，**M4/M5/M6/M7 不能**。这是一个真实的、未被回答的问题，不是保守的美德。

8. **workflow 路径没有 resume，goal 路径需要人类重新 arm。** E-8 与〔裁定 B-4〕的代价合起来意味着：**本架构对「一次长跑中断后从中间接上」没有原生答案**。当前的答案是「台账是唯一持久状态，重跑靠幂等」（V4.4），但那要求每一步都幂等——而**幂等在本仓库的 live 层从未被断言过** [E: GROUND-TRUTH-CORRECTIONS.md#D2]。M8 把它补上了，但那是计划，不是证据。

9. **本文件引用的所有外部数字都带 2026-08-17 的 as-of，且会过期。** API 定价与限速尤其易变：Crossref polite pool 已在 2025-12-01 失效 16 倍 [E: ext-academic-apis.md#核验表 #22]；DeepSeek 定价在 2026-08-16 刚全线移动 〔依据 00-PREMISE B9〕。凡引用本文件的数字必须连日期一起引用。

10. ~~**两处「待实测确认」直接落在可运行的骨架里**~~ —— **两处均已实测闭合**〔裁定 · S0 实测，[E: .loop/m0/M0-3a.json]〕：
    - M1 插件的 `inject` 服务名（§A.4 第 3 条）= **`tools`**（ctx key，不是类名）。正负两例实跑：写错时逐字 `pending (waiting for service: toolRuntime)` + 退出码 1；写对时插件树装起来、工具被模型真实调用。
    - boot 门第 2 段的调用形式（§D.5）= **`dsh --profile <name> [--patch <path>]* '<task>'`，任务是位置参数**，本轮每条 boot 证据命令都用它跑通。

    **实测同时推翻了当初的一条理由。** 原文写「标注而不是猜」的依据是「猜错的骨架看起来可抄」——这条纪律成立，但对 `inject` 而言，**猜错的后果不是静默生效错误，而是响亮的 exit 1 并逐字点名缺失服务**。真正会静默的是另一件事：**patch 的 entry id 猜错**（真实 boot 零输出，[E: .loop/m0/M0-3c.json]）。这两件事此前在本文件里被混为一谈，现已在 §A.3 顶部分开写死。
    **仍未偿**：① `ctx.credentials` 一侧的 inject 服务名**不在**本轮实测的 16 个 ctx key 对照表里，仍是「标注而不是猜」的状态；② 全部 inject/boot 结论只覆盖 headless 的 CLI boot 路径，**web profile 与 HMR 热重载路径未测**，热重载期的 inject 失败是否同样响亮**未知**。

---

**文件版本**：v2-draft-1｜**撰写日期**：2026-08-17｜**DSH 一手基线**：`@deepseek-ai/dsh` 0.1.0-rc.6（194 包，实测 2026-08-17）｜**证据基线**：`research/v2/`（23 文件）｜**规范源**：`01-CONTRACTS.md`｜**前提源**：`00-PREMISE.md`
