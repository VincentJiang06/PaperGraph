# loop 运行台账

> **这份文件的唯一职责**：让 loop 在上下文被压缩、会话被中断、或换一个人接手之后，
> 仍然知道自己跑到哪、上一次为什么失败、restart 计数器现在是几。
>
> 设计里把它列为 harness_primitive 的第一条。理由很直接：
> **一个只存在于某个上下文窗口里的进度，在那个窗口关掉的一刻就不存在了。**
> 本轮已经实证过一次——一个跑了 29 分钟的攻击 workflow 在压缩边界上丢了句柄，
> 靠 `.output` 文件是 0 字节 + workflows 目录无对应 runId 才判断出它的状态。
>
> **写这份文件的纪律**：只写**事实与判定**，不写计划与感想。
> 每次阶段状态变化时更新；不要等到「做完了再一起补」——那正是它要防的失效。

**设计**：`.loop/arp-build.design.json`（linter PASS） · **runbook**：`.loop/arp-build.loop.md`
**验收入口**：`./gates/run_all.sh [docs|negative|all|m0|everything|publish]`，退出码判定

---

## 阶段状态

| # | 阶段 | check | 状态 | 迭代 / cap | 备注 |
|---|---|---|---|---|---|
| S0 | `m0-blockers` | `node gates/check_m0.mjs` | **实测半程通过**（门 exit=0） | 1 / 3 | 12/12 记录：6 resolved / 6 design-changed / 0 still-blocked。回填半程（契约 A2）进行中 |
| S1 | `status-function` | `check_contracts` + `check_status_exhaustive` | **核心产物已完成** | 1 / 4 | `src/status.mjs` + 穷举 oracle 全绿（550 万向量）。**依赖关系写错了，见下** |
| S2 | `evidence-core` | `check_evidence_core` + 负例 | 未开始 | 0 / 5 | — |
| S3 | `gc0-gates` | `run_all.sh gc0` + `test_gc0_negative` | 未开始 | 0 / 6 | `on_failure: restart` |
| S4 | `profile-boot` | `check_boot.sh` | 未开始 | 0 / 5 | `on_failure: restart`；依赖 S0 的 M0-3a/3b/3c 与 C-12a/C-12b |
| S5 | `fetch-channels` | `check_channels` + `test_rt4_rt5` | 未开始 | 0 / 5 | 依赖 S0 的 M0-1（PDF 可见性）——若 M0-1 判 design-changed，本阶段要重设计 |
| S6 | `orchestration-min` | `check_e2e.sh` | 未开始 | 0 / 6 | **最低进度地板在这里**：跑到这里之前宣布成功一律视为升级 |
| S7 | `ab-honest-test` | `check_ab.mjs` | 未开始 | 0 / 2 | 等预算 A/B；主终点需先按 C-13 重设计 |
| S8 | `attack-fixaudit` | `check_attack_ledger.mjs` | 未开始 | 0 / 4 | `on_failure: restart` |

**外环**：第 1 轮 / cap 5。零变更闸未触发。restart 计数器：全部为 0。

### 〔对设计的更正 · 2026-08-17〕S1 的 `depends_on` 写错了

设计里写 `S1.depends_on = ["m0-blockers"]`，理由是「M0 阻塞项 gate 一切」。
**实际跑起来发现这条依赖是虚的**：`src/status.mjs` 是从 01-CONTRACTS §1.5 直接翻译出来的纯逻辑，
不读文件、不碰 DSH、不依赖任何一条 M0 实测结果。它在 S0 还没产出一条记录时就完整跑通了。

S1 的**真实**依赖是 **03-EVIDENCE-ENGINE 的 C-5**（独立簇归并器）——
`independent_cluster_count` 是 `S` 的核心输入，而目前没有任何组件生产它。
穷举 oracle 现在能跑，是因为我在测试里**自己造**了这个输入；
真实系统里它必须由归并器产出，否则 `S` 的输入永远缺一项。

**这条更正本身是 loop 的产出**：一个只在纸上的阶段图会把「概念上的先后」当成「技术上的依赖」。
跑一遍就分开了。不改设计 JSON（那是 R1 时刻的记录），在这里记更正，
下一轮外环迭代时一并修 `depends_on`。

---

## 已经存在的东西（接手的人先看这段）

**六道门 + 三套负例套件，`./gates/run_all.sh` 当前 6/6 绿**

| 门 | 查什么 | 负例套件 |
|---|---|---|
| `check_contracts.mjs` | 词表↔作用表双向完备无重复（V7.9）、状态符号不越界（V7.10）、禁聚合字段（V1.5） | `test_check_contracts.sh` · 6 红 |
| `check_pointers.mjs` | `[E:]` 的文件存在性 + 锚点可解析性；棘轮欠债表；禁把 00-PREMISE 裁决当证据 | `test_check_pointers.sh` · 7 红（含空集闸） |
| `check_doc_metrics.mjs` | README 与各文档的自述数字必须与实测相符 | 红样本已验 |
| `check_m0.mjs` | M0 记录齐全 + 结构合法 + **抽样重跑比对哈希** | `test_check_m0.sh` · 8 红 |
| `check_publishable.mjs` | 发布前：零密钥 / 零本机绝对路径 / 零排除内容混入 | — |
| `run_all.sh` | 统一入口，退出码判定 | — |

**指针实测**：1,349 个 (目标, 锚) 实例，可解析率 90.0%，108 条已知欠债登记在
`.attack/pointer-debt.json`，棘轮方向只许下降。

---

## 未偿债（会阻塞后续阶段的，按阻塞强度排）

1. **03-EVIDENCE-ENGINE 的 C-4 / C-5 / C-6 / C-8**——`S` 的输入生产方。
   C-5（独立簇归并器完全缺席）不修，S1 的 `check_status_exhaustive` 没有合法输入向量可造。
2. **R3 fix-audit 未跑**。R2 的 diff 存在但不完整，现在跑等于审计半成品。
   按 `vince-attacker` 的收敛判据，**本项目目前不构成收敛**。
3. **v1 覆盖率 diff 未完成**——承诺过「只许更全」，尚未验证。
4. **00-PREMISE B8 的自指洞**（`gates-baseline` tag 可 `git tag -f` 重指）——S0 的 M0-7 在处理。
5. **456 个 `[E:]` 指针在公开仓内解析不了**（33.8%），因为排除了对第三方包的逆向档案。
   理由与代价写在 `research/v2/EXCLUDED.md`，门识别为独立的「已声明排除」状态。

---

## 升级条件（这三类才打断人，其余自行推进）

- 需要修改 `01-CONTRACTS.md` 的规范定义才能继续（**契约错了**，不是实现坏了）
- M0 实测结果推翻某条设计前提，且没有不改架构的绕法
- `00-PREMISE` 的某条赌注被观测证伪——尤其 **B1**：若 S7 的 A/B 结果与设计假设相反

---

## ⚠️ S0 实测触发的升级项（2026-08-17）

### 升级 1 · 「exit code 判定」不足以承载 loop（M0-3b，design-changed）

**实测**：`dsh` 的退出码**只反映 harness 成败，不反映任务成败**。
让 agent 跑 `exit 7`，agent 如实报告命令失败，`dsh` 仍然退出 **0**。

这条直接打在整个运行面前提上——README、02-ARCHITECTURE、以及**本 loop 设计的九个阶段**
全都写着「headless + exit code 判定」。

**影响范围有边界，先说清楚**：
- **不受影响**：`gates/` 下的门是纯 node/bash 脚本，跑在 dsh **之外**，退出码完全可靠。
  目前七道门 + 三套负例套件的绿灯不因此失效。
- **受影响**：任何**以 dsh headless 为载体**的验收——即 S6 `orchestration-min` 的端到端 run，
  以及 S7 A/B 两臂的成败判定。那些地方 dsh 恒返回 0，退出码判据是空的。

**M0-3b 记录给出的收口**（已写进该记录的 `doc_action`）：
> 任何以 headless 为载体的 check，其「失败」信号必须由**被测方在 stdout 里显式写出**，
> harness 退出码只做二次兜底。

即：`check_e2e.sh` 不能写成 `dsh --profile ... ; test $? -eq 0`，
必须写成「跑完后用**门脚本**读产物并判定」——这恰好是本项目一直在做的形态
（门在 DSH 进程外、读 CAS 与 claim 台账），所以修法不改架构，只改验收脚本的写法。

**待办**：S6/S7 的 check 字段要重写；README 与 02 的「exit code 判定」措辞要改。

### 升级 2 · git tag 不是不可变锚点（M0-7，design-changed）

**实测**（git 2.55.0）：`receive.denyDeletes` 与 `receive.denyNonFastForwards`
对 `refs/tags/*` **全部不生效**——tag 的非快进强推与删除都 ACCEPTED；
同一次实验里对 `refs/heads/*` 则双双 REJECTED。且默认 `core.logAllRefUpdates=true` 时
tag **连 reflog 都不写**（0 条）。

R1 的 C-11 判「`gates-baseline` tag 可被 `git tag -f` 重指」，本轮把它加强了：
**远端也拦不住**。00-PREMISE B8 里「补 gate-integrity 洞」的方案基础不成立，需要另找锚点。

## S0 已确认的一手事实（这些从"我们以为"变成了"我们跑过"）

| 项 | 结论 | 方向 |
|---|---|---|
| **M0-1** PDF 可见性 | **架构前提成立**。PyMuPDF `get_texttrace()` 逐 span 给出 color / size(0.1pt) / type(Tr 3) / opacity / layer / seqno；7 段对抗夹具中 6 段隐藏文本全部归入 `non_rendered` | ✅ 好消息——通道分离在 PDF 路径上可实现，RT-5 不推翻架构 |
| **M0-2b** 多帧 zstd | **确认是地雷**。28 frame 的真实日志：`zstd -dc` 55 行，Node 内置 1 行，手动切帧循环回到 55 行。本机 **155 个 session 无一例外** | ⚠️ 必须写进契约 |
| **M0-3a** inject 服务名 | 是 `tools`（`ToolRuntime` 的 ctx key），不是类名。**且「猜错=静默 PENDING」这条前提是错的**——猜错时 boot 退出码 1，是响亮失败 | 修正了一条设计假设 |
| **M0-4** run_code → fs | **能，且沙箱零约束**。同机同时刻同策略下：bash 路径写文件被 `sandbox-exec` 拒绝，`run_code` 用 `await import('node:fs')` 成功写入并读回 | ✅ 证实了 §0.2 两层表的诚实改写是对的 |
| **M0-5** compaction | **能触发，且 meta 逐字保留**。把 `thresholdRatio` 压到 0.02 跑真实会话，出现 6 条 `compaction/prune` 与 6 条 `surfaceOp{op:'replace'}`；6/6 替换体的 `data.meta` 与原事件**JSON 逐字相同** | ✅ 整个证据锚点方案的地基被实测证实 |
| **C-12a** 出厂呈现模式 | headless bundle **确实整键替换** `tools` 行，且额外 insert 了 `code-runtime` 行。「出厂 native」只是 `DSH_TOOLS_MODE` 未设时的兜底 | ⚠️ 「run_code 不在面上」的说法要删 |
| **C-12b** boot 门钉哪个文件 | **两个都要，且 `settings.yaml` 更强**——它在运行期盖过整条 patch 链。三方对撞实测：patch 链最终值 `PATCH-BOGUS-MODEL`，实际打到 API 的是 `SETTINGS-BO…` | ⚠️ boot 门要重写 |
| **M0-6** 限速网关 | DSH 侧**并非零支撑**：`dsh-mcp-client` 有 spawn + 指数退避 + 尝试预算 + `failOnStartupError`。网关起不来时 dsh 退出码 1、0 字节 stdout、一个 turn 都没跑。但网关**中途崩溃后被静默换进程**（pid 71338→71389） | 部分好消息 + 一条新风险 |

## S0 实测抓到的一道空心门（值得单列）

02-ARCHITECTURE §D.3 的 boot 门里，检测「服务未解析」的 grep 模式写的是

    'pending (waiting for services'     ← 复数

而 `dsh-app-boot` 的实际输出逐字为

    const subject = missing.length === 1 ? "service" : "services"

**缺一个服务时输出的是单数 `service`——而那正是最常见的场景。**
这道门会以全绿出厂，却恒不命中它被写出来要抓的那个失败。

三处已改为单数前缀（同时覆盖单复数）并补了裁定。

**为什么这条重要**：它是**读代码读不出来、只有跑一遍才会暴露**的缺陷类型。
写那段的人（是我）读了正确的源码、抄的时候多了一个 s，而任何 review 都不会盯单复数。
本轮迄今抓到的空心/误报门已有五处（`D-1` 指针门空心、`check_m0` 三处误报、本条），
其中只有这一条是**实测**抓到的，其余四条靠的是独立上下文审计与 red-first。
两种手段都必要，覆盖的失败面不同。

**附带推翻一条前提**：此前文档写「猜 id = 静默失效」，把两件事混为一谈。实测分开了：
- `inject` **服务名**猜错 → `assertEntriesActivated()` 抛出，**响亮 exit 1** 并逐字点名缺失服务
- patch 的 **entry id** 猜错 → `--dump-config` 报 warning，**真实 boot 路径零输出、彻底静默**

后者比文档写的「只 warn 不 fail」更坏，且决定了这件事**只能**靠 `--dump-config` 检测。

## 变更日志

只记**状态变化**与**判定**，一行一条，新的在上。

- `2026-08-17` · **S0 门通过**（`check_m0` exit=0，12/12 记录）。`run_all.sh everything` **8/8 全绿**。
  实测抓到 02 §D.3 boot 门的单复数拼错（见上），已修。回填轮 `w0ky1s4bu` 处理其余 11 条待改项。
- `2026-08-17` · **S0 实测回来了**：12 条记录。6 resolved / 5 design-changed / 0 still-blocked。
  两条触发升级（见上）：exit code 不传导、git tag 不是不可变锚点。
  两条是好消息：PDF 通道分离可实现、compaction 下 `data.meta` 逐字保留 6/6。
- `2026-08-17` · **R2 补修完成**：03-EVIDENCE-ENGINE +325 行（新增 G-CTR-SCAN 与 G-CLUSTER 两道门的完整契约）、
  00-PREMISE +98 行、05-TESTING 已改。七道门全绿。
- `2026-08-17` · **check_m0 自身修了三处误报**：`>/tmp` 重定向、诚实声明的不可复现证据、带说明的 `doc_action`。
  三次都是**门在惩罚更好的做法**。已写进门里作为设计教训：过严的 schema 会训练出满足 schema 而非说真话的行为。
- `2026-08-17` · S1 核心产物完成：`src/status.mjs` + 穷举 oracle（550 万向量全绿，六值全可达，C-1 回归 4/4）。
- `2026-08-17` · S0 开工：`check_m0.mjs` + `test_check_m0.sh`（8 红样本）落地并全过；
  其中 R-3「resolved 但哈希编造」直接对应设计里给 S0 写的 `passing_but_wrong`，是该阶段验收的牙齿。
- `2026-08-17` · loop 设计过 linter（0 fail），runbook 渲染为 `arp-build.loop.md`。
- `2026-08-17` · R2 部分完成：01-CONTRACTS 的 P1 全修；03/00/05 的 P1 首批派发因会话额度失败，已重派。
- `2026-08-17` · R1 攻击轮：164 findings，9 枚种子生效 6 枚命中，无攻击者作废。
- `2026-08-17` · 同步到 `github.com/VincentJiang06/PaperGraph`（`8859393`），前代存档在 `71ccea0`。
