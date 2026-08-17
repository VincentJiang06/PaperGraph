# 可复现与溯源基础设施（v2 外部调研 · 维度：每条数据类 claim 的重跑机制）

调研日期：2026-08-17。所有价格/版本/榜单数字均已标注口径与抓取日期；本维度内数字随时间失效极快（沙箱定价 2025-11 与 2026-04 两次变更、DABstep 榜单 2025-06 到 2026-06 涨了 6 倍）。

---

## 结论摘要

1. **不要用 DVC / DataLad / git-annex 做工作态存储。** 三者都建立在「仓库级全局锁」之上，与本项目的超并行多 loop 前提直接冲突。DVC 官方 troubleshooting 明写 `Unable to acquire lock`（锁文件 `.dvc/tmp/lock`）、`dvc repro` 没有 `--jobs` 并行开关、要求并行只能「开多个终端各跑一次 `dvc repro`」，而请求并行调度器的 issue #755 从 2018-06-08 开到今天仍未关闭。这不是配置问题，是设计前提问题。
2. **自建 CAS + 一 claim 一文件的 append-only 账本，是并行写入下唯一无锁的最小方案。** 内容寻址写入天然幂等（`write tmp/<uuid>` → `os.replace objects/<sha256>`），一 claim 一文件消灭合并冲突，git 提交只由 orchestrator 在 gate 时做一次，子 agent 永不碰 git。总代码量 ~200 行，替换掉整个 DVC/DataLad 依赖面。
3. **PROV / RO-Crate 只做导出格式，绝不做内部工作格式。** 但要采纳的是 **Process Run Crate 0.5**（`w3id.org/ro/wfrun/process/0.5`）而非完整 Workflow Run Crate——它的 MUST 只有三条（`@type` ∈ {CreateAction, ActivateAction, UpdateAction}、`@id`、`instrument`），`result`/`endTime`/`agent` 是 SHOULD，且 profile 自己明写「不保证一致性、不保证可复现」。这正好是我们要的：导出时从账本一次性生成，零日常成本。
4. **notebook 验证路线（papermill + nbval）应当整体跳过。** papermill 2.7.0 只做参数化和执行，**根本不比对输出**；nbval 才做比对，而它的比对就是 false-red 制造机——matplotlib 只比对文本 repr（含内存地址 `<AxesImage at 0x7f2cb3374198>`）、dict 顺序、时间戳、RNG 全都会假失败，且**默认不做任何 sanitize**，必须手写 `--sanitize-with` 正则文件。正确做法：真值只允许是「输出 JSON 的纯脚本」，notebook 降级为从已验证脚本生成的展示层。
5. **哈希链审计日志是本项目的过度设计。** 威胁模型不成立：能改 claim 记录的人（本机用户/agent）同样能改哈希链的锚点。真正需要的是「输入内容寻址 + 输出可重跑比对」，那是**功能性**防篡改（改了数据 → 重跑对不上 → 失败），不是**密码学**防篡改。sha256 内容寻址要，Merkle 链不要。
6. **沙箱：v1 用本机 `sandbox-exec`，v1.5 逃生口是 Apple `container`，云沙箱 v1 不上。** 云沙箱最便宜的口径也要把用户的课程数据/论文 PDF 送出机器，收益为零。成本口径陷阱要记住：Modal 的 **Sandbox 费率是它自己普通 function 费率的 3 倍**（$0.00003942 vs $0.0000131 /core/s）；Cloudflare 按**活跃 CPU 时间**计费而 E2B/Modal 按**墙钟时间**计费，两个 $/vCPU-h 数字不可直接比。
7. **v1 范围判定的关键输入：封闭式与开放式的能力差是 2–4 倍，且断层就在「谁定义问题」这条线上。** 数据在手、问题可判定的封闭任务（DABstep hard）从 2025-06 的 14.55% 涨到 2026 年多家宣称 87–100%；而端到端开放任务仍在 21–45%（DSBench 34.12%、BLADE 最佳 F1 44.8%、CORE-Bench-Hard 21.48%、REPRO-Bench 21.4%）。**结论：v1 的重跑门只承接封闭式 claim；开放式端到端分析在 v1 只能产出 `inference` 级状态，机器不得判 `verified`。**
8. **引文类 claim 的门必须是「本地快照 + 归一化子串匹配」，不是「让模型自查」。** SourceCheckup（Wu et al.）测得约 50%–90% 的 LLM 回答**未被其自己所引来源完全支持**，GPT-4+RAG 仍有约 30% 的单句无来源支撑。任何依赖模型自证的引文环节都会以这个量级漏。

---

## 逐条发现（含 URL）

### A. 数据版本化 / 溯源工具族

**A1. DVC —— 买到什么、在并行写入下付出什么**
- 买到：pipeline DAG（`dvc.yaml`）、远端缓存、`dvc repro` 的依赖失效检测、实验对比。
- 付出（**否决性**）：`dvc repro` 命令参考页明确写「如果需要并行执行 stage，可以并发地多次启动 `dvc repro`（例如在不同终端里）」——即**没有内建并行**。https://doc.dvc.org/command-reference/repro
- 但并发启动会撞锁：troubleshooting 页原文「You may encounter an error message saying `Unable to acquire lock` if you have another DVC process running in the project」，锁文件在 `.dvc/tmp/lock`，网络文件系统上还要 `dvc config core.hardlink_lock true`。https://doc.dvc.org/user-guide/troubleshooting
- iterative/dvc issue #755「add scheduler for parallelising execution jobs」，开于 2018-06-08，报错原文「Cannot perform the cmd since DVC is busy and locked」，**至今 open**。https://github.com/iterative/dvc/issues/755
- 判定：**跳过**。我们要的只有「输入内容寻址 + 重跑比对」，DVC 把这两件事绑在一个带全局锁的 pipeline 引擎上一起卖。

**A2. DataLad 的 run-record 模型 —— 值得抄结构，不值得引依赖**
- run record 是一个 key-value 映射，字段：`cmd`（可含占位符）、`dsid`（数据集 DataLad ID）、`exit`（退出码）、`inputs`（声明的输入路径列表）、`outputs`、`pwd`（相对工作目录）。https://docs.datalad.org/en/stable/design/provenance_capture.html
- 存储位置二选一：写进 commit message 正文，或写进根数据集的 `.datalad/runinfo` 下的 sidecar 文件（LZMA 压缩、文件名为校验和）。
- `datalad rerun <SHA>` 基于该记录重放。
- 官方设计文档**没有 limitations 章节**：不捕获计算环境、不保证确定性、只覆盖命令行调用、inputs/outputs 声明「not strictly required」（不声明就退化成不可重放）。文档中**未提及** PROV 或 RO-Crate 导出。
- 判定：**抄字段表，不引依赖**。它底层是 git + git-annex，同样吃 git index 锁；而它的六字段记录正是我们 claim 记录里 `provenance` 块该有的最小集，再加上 DataLad 缺的那两项（环境锁文件哈希、随机种子）。

**A3. W3C PROV-O / RO-Crate**
- PROV-O 是 W3C Recommendation（https://www.w3.org/TR/prov-o/），自称「lightweight ontology」；但学界评价是「已逾十年，基本被局限于小型研究项目」（Nature Sci Data 2025 的 PROV-O→BFO 映射论文，https://www.nature.com/articles/s41597-025-04580-1）。作为**内部工作格式**它要求把每次运行建模成 RDF 三元组，成本与我们的收益完全不成比例。
- RO-Crate 1.2 发布日 **2025-06-04**，状态 Recommendation，PID `https://w3id.org/ro/crate/1.2`；1.2 新增 profile 概念。https://www.researchobject.org/ro-crate/specification/1.2/index.html
- **Process Run Crate 0.5**（`https://w3id.org/ro/wfrun/process/0.5`）才是我们该对齐的 profile——它描述「一个或多个计算工具的一次执行」，而不是完整 workflow。必需项极少：`CreateAction` 的 `@type`/`@id`/`instrument` 为 MUST，`result`/`endTime`/`agent` 为 SHOULD，`object`/`startTime` 为 MAY；profile 自己声明不要求命令行结构、不保证可复现、不保证 action 链的一致性（「there may be an intermediate action that has not been recorded」）。https://www.researchobject.org/workflow-run-crate/profiles/process_run_crate/
- 判定：**导出采纳（Process Run Crate 0.5），工作格式拒绝**。导出器是一个纯函数 `ledger → ro-crate-metadata.json`，只在 `publish` 时跑。

### B. notebook 验证与它的 false-red 问题

**B1. papermill（2.7.0）不做输出比对。** 官方文档定位是「parameterizing and executing Jupyter Notebooks」，支持 Azure/AWS 存储后端，Python 3.10+；文档中没有任何输出校验/比对能力。https://papermill.readthedocs.io/en/latest/ ——所以「papermill 做重跑门」这个方案在第一步就不成立，它只能重跑，不能判定。

**B2. nbval 的比对机制与它的假失败面。** https://nbval.readthedocs.io/en/latest/ · https://github.com/computationalmodelling/nbval
- 机制：把 notebook 里**已存的输出**与**重新执行后的输出**逐 cell 比对，每个 cell 即一条 test。
- 模式：`--nbval` 全量比对；`--nbval-lax` 只跑不比，仅比对带 `#NBVAL_CHECK_OUTPUT` 标记的 cell。
- 标记：`NBVAL_IGNORE_OUTPUT` / `NBVAL_CHECK_OUTPUT` / `NBVAL_SKIP` / `NBVAL_RAISES_EXCEPTION`（后者只校验异常类型，不校验 traceback）；也可用小写连字符 cell tag 形式。
- **默认不做任何 sanitize**，必须显式 `--sanitize-with sanitize.cfg` 写正则替换对。
- 已知假失败源（官方文档自述）：时间戳/日期；matplotlib **只比对文本 repr**、里面带内存地址（`<AxesImage at 0x7f2cb3374198>`）、图像数据根本不比；dict key 顺序；numpy 随机；输出行数不定的循环。
- 判定：**跳过 notebook 验证路线**。false-red 的根因不是工具不好，是「比对渲染后的富输出」这件事本身就不可判定。我们的门只比对**脚本显式写出的结构化 JSON**，比对语义由我们定义（数值容差、集合无序比较），假失败面收敛到接近零。

### C. 内容寻址存储与哈希链

**C1. CAS 模式。** 内容寻址就是「地址 = 内容的密码学哈希」（https://en.wikipedia.org/wiki/Content-addressable_storage）。git-annex 本身就是一个 CAS（https://en.wikipedia.org/wiki/Git-annex）；restic 用 content-defined chunking 做去重的 CAS。研究场景的现成实践见 gitOmmix（临床组学，arXiv 2409.03288）与 HPC 研究数据版本管理（arXiv 2505.06558），两者都落在 git-annex 上——**都继承了 git 的锁问题**。
- 判定：**自建 30 行 CAS**（`objects/<sha256[:2]>/<sha256>` + 原子 rename），不引 git-annex/restic。并行安全性来自 POSIX `rename` 的原子性 + 相同内容写入天然幂等。

**C2. 哈希链审计日志。** 结构是「append-only 存储 + 逐条哈希前一条 + Merkle 根锚定到可信位置」，包含证明查询 O(log N)（Crosby & Wallach, USENIX Security 2009，https://static.usenix.org/event/sec09/tech/full_papers/crosby.pdf）。反面判据被总结得很干脆：「如果你说不出攻击者是谁、他会改什么、以及为什么现有访问控制不够——你不需要 Merkle 树，你需要一张设计良好的 append-only 表和一个好的备份策略。」（https://dipankar-das.com/blog/merkle-hash-chain-audit-logs/）
- 判定：**跳过**。本项目的「防篡改」需求由重跑门功能性地满足：输入哈希对不上或重跑结果对不上 → 状态自动掉回 `unverified`。把 claim 状态改成 `verified` 而不改数据是做不到的，因为状态**不是写出来的，是 gate 算出来的**。

### D. 网页存证：归档 API 与单文件快照

**D1. Save Page Now（SPN2）。** 官方 API 文档托管在需要登录的 Google Doc（archive.org 上只有该文档的元数据页，且标注「This is not the newest revision」，另有 2022-07-28 / 2023-01-22 两个更新版）。https://archive.org/details/spn-2-public-api-page-docs
- 社区口径（**未经一手核实**）：匿名每分钟 15 个 URL，超限封 IP 5 分钟；带 `WAYBACK_ACCESS_KEY`/`WAYBACK_SECRET_KEY`（archive.org/account/s3.php）可提高速率；日配额据 r/internetarchive 讨论从 4 万 → 3 万 → 1 万下调（约 2025-11）。
- 判定：**best-effort 采纳**。归档 URL 作为 claim 的可选字段，提交失败**不阻断**门，但也不能因此让 claim 升级——真值锚点是本地快照的 sha256，不是 archive.org。

**D2. perma.cc。** 站点对自动抓取返回 HTTP 403（本轮 `perma.cc/pricing` 与 `perma.cc/about` 均被拒），无法一手核价。多所大学图书馆指南（UChicago 2026-04、Uppsala 2026-03）一致称个人免费账户可存 **10 条链接**；**每月 $10 / 10 条新链接** 这个数字最早可追到 infodocket 2019-01-07 的报道，**已 7 年之久，视为失效**。
- 判定：**跳过**。付费、抓不到一手价格、且它提供的能力（第三方托管快照）我们用本地 CAS + best-effort SPN2 已覆盖。

**D3. 单文件快照工具。**
- **monolith**（Rust，`brew install monolith`）：把 CSS/JS/图片全部内联成 data URL 存成单个 HTML5 文档；关键限制是**没有 JS 引擎**，README 原话「websites that retrieve and display data after initial load may require usage of additional tools」——需要先用 Chromium 预渲染。常用 flag：`-j`（去 JS）、`-I`（isolate）、`-e`（忽略网络错误）、`-M`（不写时间戳/URL 元数据）、`-b`（自定义 base URL）。https://github.com/Y2Z/monolith
- **single-file-cli**：需要本机装 Chrome/Chromium（可用 `--browser-executable-path` 指定），支持 `--dump-content`、`--crawl-links`/`--crawl-max-depth`、`--compress-content`、`--urls-file`；**文档未说明输出是否确定性**。https://github.com/gildas-lormeau/single-file-cli
- 判定：**两者都采纳，按页面类型分流**。静态页/PDF 落地页 → monolith 带 `-M`（去掉时间戳可提高字节级确定性）；JS 渲染页 → single-file-cli。**但快照的哈希只用于「这份快照是我当时看到的那份」，不用于跨时间比对**——因为两个工具的输出都不保证字节确定性（single-file 明确未承诺，monolith 默认还会注入时间戳）。跨时间只比对**抽取出的纯文本**。

### E. 沙箱：云 vs 本机

**E1. 云沙箱当前定价（均为一手页面，2026-08-17 抓取）**

| 服务 | 计费单元 | 费率 | 计费口径 |
|---|---|---|---|
| E2B | vCPU / RAM，按秒 | 1 vCPU $0.000014/s（8 vCPU $0.000112/s）；RAM $0.0000045/GiB/s | **墙钟时间**（沙箱存在即计费） |
| Modal（Sandbox） | core / GiB，按秒 | CPU $0.00003942/core/s；内存 $0.00000667/GiB/s | 墙钟时间；**Sandbox 费率 = 普通 function 费率（$0.0000131/core/s）的 3.0 倍** |
| Cloudflare Containers/Sandbox | vCPU / GiB / GB，按 10ms | $0.000020/vCPU-s；内存 $0.0000025/GiB-s；磁盘 $0.00000007/GB-s | **仅活跃 CPU 时间**；需 Workers Paid $5/月底座 |

- E2B：https://e2b.dev/pricing —— Hobby 免费 + **一次性 $100 额度**（属促销性质，不可用于长期成本建模）、10 GiB 存储、最多 20 个并发沙箱、单会话最长 1 小时；Pro $150/月 + 用量，20 GiB、100 并发（可加购至 1100）、单会话最长 24 小时。
- Modal：https://modal.com/pricing —— Starter 免费含 **$30/月**额度、3 席位、100 容器；Team **$250/月 + 用量**含 **$100/月**额度；学术最高 $10k 额度。
- Cloudflare：https://developers.cloudflare.com/containers/pricing/（页面标注 last updated 2026-04-21）—— Workers Paid $5/月含 375 vCPU-分钟、25 GiB-小时、200 GB-小时；实例档位 lite(1/16 vCPU, 256 MiB, 2 GB) → standard-4(4 vCPU, 12 GiB, 20 GB)。CPU 定价变更公告于 2025-11-21（https://developers.cloudflare.com/changelog/post/2025-11-21-new-cpu-pricing/），Sandboxes GA 于 2026-04（InfoQ）。
- Daytona：https://www.daytona.io/pricing 页面只给出 Windows $0.0858/vCPU/h、「$200 免费算力」、「前 5 GiB 免费后按 GiB 计价」，**Linux 的 vCPU/GiB 小时费率未在一手页面给出**；二手（Blaxel/Morph）称 $0.0504/vCPU-hr + $0.0162/GiB-hr —— 标记未核实。

**E2. 本机 OS 级沙箱（macOS）**
- `sandbox-exec`（Seatbelt）**已被 Apple 标记 deprecated**，运行时打印「WARNING: sandbox-exec is deprecated. Consider adopting the App Sandbox instead.」；apple/containerization issue #737（开于 **2026-05-12**，标题「Clarify `sandbox-exec` deprecation timeline and provide a replacement for non-App-Store process sandboxing」）指出 Apple 未给出可用替代：App Sandbox 要求代码签名 + Xcode 项目、Endpoint Security 只能观察不能声明策略、System Extensions 受分发限制；**线程内无 Apple 官方回复**。https://github.com/apple/containerization/issues/737
- Apple `container`：**1.0.0 发布于 2026-06-09**，最新 **1.2.2 发布于 2026-08-08**（GitHub Releases API 核实）。每容器一个独立轻量 VM（各自内核与网络栈），完整功能需 Apple Silicon + macOS 26；每容器独立 IP、无端口映射。https://github.com/apple/container/releases
- 判定：**v1 用 `sandbox-exec` profile（拒网络、只允许写 run 目录）+ 硬超时 + `ulimit`；同时把「同一个 `run.py` 能在一个 pinned OCI 镜像里跑」作为契约写死**，这样 v1.5 切到 `container run`（或外部评审者切到任意 Docker）是零改动的。云沙箱 v1 明确不上：唯一收益是隔离强度，代价是把用户的课程数据送出本机。

### F. LLM agent 做数据分析的实测可靠度（v1 范围判定的核心输入）

**F1. 封闭式（数据在手、问题可判定）—— DABstep 的六倍涨幅与它的口径陷阱**
- 基准本体：450 条任务（另有 10 条 dev split），CC-BY-4.0，来自某支付分析平台的真实工作负载改造；官方划分 Easy 16% / Hard 84%（NVIDIA 博文口径）。https://huggingface.co/datasets/adyen/DABstep
- 论文基线（arXiv 2506.23719，2025-06）：**「even the best agent achieves only 14.55% accuracy on the hardest tasks」**。
- DS-STAR（Google，2025-11）：hard 45.24%（同模型 Gemini 2.5 Pro 裸模型仅 12.70%）。https://research.google/blog/ds-star-a-state-of-the-art-versatile-data-science-agent/
- NVIDIA NeMo Agent Toolkit Data Explorer（2026-03-13，厂商自述）：Easy 87.5% / **Hard 89.95%**，模型 Haiku 4.5；同页对比 Claude Code + Opus 4.5（Easy 90.2 / Hard 66.93）、DataPilot（86.11 / 87.57）、DS-STAR（87.5 / 45.24）。方法核心是先用重模型在**代表性任务**上蒸馏出一个 `helper.py` 可复用函数库 + few-shot 示例。https://huggingface.co/blog/nvidia/nemo-agent-toolkit-data-explorer-dabstep-1st-place
- MotherDuck（2026-06）：**做到 450 题中 445 题全对（100%）**，路径是 88% → 93% → 100% 地反复重塑语义层去贴合某一个模型；并且他们发现**有 5 题的 gold answer 可证明是错的**（他们的 SQL 正确、gold 与数据矛盾），验证方式是去翻 HuggingFace 上他人的提交（Adyen 不公布答案）。https://motherduck.com/blog/oops-maybe-we-do-need-semantic-layers/
- **口径判读**：DABstep 的 hard 分数在 2026 年已进入饱和/过拟合区间。它是**单一固定合成支付域数据集 + 公开任务 + 公开 leaderboard（提交表已 97.8 万行）**，且 SOTA 方法明确在 dev split 上蒸馏工具库。因此 87–100% 这些数字**不能读作「agent 会做数据分析」**，只能读作「当问题被写死成可判定的问句、数据就在手边、且允许针对该数据集预热工具时，封闭式分析已足够可靠到可以当地基」。

**F2. 开放式 / 端到端 —— 仍在 21%–45%**
- **DSBench**（ICLR 2025，arXiv 2409.07703）：466 条数据分析任务 + 74 条建模任务，来自 Eloquence 与 Kaggle；**「the best agent solving only 34.12% of data analysis tasks and achieving a 34.74% Relative Performance Gap (RPG)」**。
- **BLADE**（EMNLP Findings 2024，arXiv 2408.09667 / https://blade-bench.github.io/）：12 个数据集与研究问题、逾 500 个分析决策，ground truth 来自专家独立分析；**最佳 F1 44.8%**；结论「LMs often perform basic analysis that can yield decent precision … but poor coverage across runs」，且「most large LMs can generate a non-empty executable analysis over 60% of the time」——即**能跑通 ≠ 分析对**。
- **CORE-Bench**（arXiv 2409.11363）：270 条任务 / 90 篇论文 / CS+社科+医学，任务是**用论文自带的复现包重现结果**。CORE-Agent + GPT-4o：Easy **60.00%** / Medium **57.78%** / Hard **21.48%**；通用 AutoGPT + GPT-4o：35.56 / 37.78 / **6.67%**。平均单任务成本（表 A3，GPT-4o）：Easy **$0.64** / Medium **$1.20** / Hard **$2.96**。
- **REPRO-Bench**（arXiv 2507.18901）：112 条任务实例，每条是一篇有公开复现报告的社科论文，agent 需据 PDF + 复现包判定其可复现性；**现有最佳 agent 准确率仅 21.4%**，作者的 REPRO-Agent 相对提升 71%。
- **口径判读**：F1 与 F2 的分数不可直接相减（不同基准、不同年份模型、不同评分函数），但**形状高度一致**：只要问题的定义权从人手里交给 agent，分数就掉进 20–45% 区间；且 CORE-Bench 内部 Easy→Hard 从 60.00% 掉到 21.48%（同一基准、同一 agent、同一模型，**唯一变量是任务难度**）——这条是最干净的内部对照。

**F3. 引文/引语类的可靠度**
- SourceCheckup（Wu et al.）：**约 50%–90% 的 LLM 回答未被其所引来源完全支持**；GPT-4 + RAG 仍有**约 30% 的单句无来源支撑**、近半数回答不完全被支持。预印本 v1（arXiv 2402.02008，2024-02-03）口径为 1200 个生成问题 / 逾 4 万条「陈述-来源」对；正式发表版（Nat Commun 2025, s41467-025-58551-6）被广泛转述为 800 个问题 / 5.8 万对——**两个版本口径不同，转述时必须指明是哪一版**。
- 判定：引语门必须是**确定性字符串匹配**，不能是模型自评。

---

## 载荷数字核验表

| 数字 | 口径三元组（什么指标 / 什么样本或档位 / 与什么比） | 状态 | 一手出处 |
|---|---|---|---|
| CORE-Bench 270 任务 / 90 论文 / 3 学科 | 基准规模 / 全集 / — | verified | arXiv 2409.11363 摘要 |
| CORE-Agent Hard **21.48%**、Medium 57.78%、Easy 60.00% | 任务级准确率 / CORE-Agent + **GPT-4o**，2024-09 论文 / 对同表 AutoGPT | verified | arXiv 2409.11363v2 Table 5 |
| AutoGPT Hard **6.67%** | 同上 / 通用 agent + GPT-4o / 对 CORE-Agent 21.48% | verified | 同上 |
| CORE-Agent 单任务成本 Easy $0.64 / Med $1.20 / **Hard $2.96** | OpenAI API 平均成本 / GPT-4o，2024 年当时价 / 难度三档间比 | verified | arXiv 2409.11363v2 Table A3 |
| DABstep **450** 任务（+10 dev） | 数据集行数 / default split / — | verified | huggingface.co/datasets/adyen/DABstep |
| DABstep Easy 16% / Hard **84%** | 任务占比 / 全集 / — | verified（厂商页转述基准方划分） | HF blog nvidia（2026-03-13） |
| DABstep hard **14.55%** | 任务级准确率 / 论文自评的最佳 agent，2025-06 / 论文内各 baseline | verified | arXiv 2506.23719 摘要 |
| DABstep hard **45.24%**（DS-STAR，Gemini 2.5 Pro；裸模型 12.70%） | 任务级准确率 / 单一 agent 系统，2025-11 / 同模型无 agent | verified | research.google DS-STAR 博文 |
| DABstep hard **89.95%** / easy 87.5%（NVIDIA + Haiku 4.5） | 任务级准确率 / **厂商自报**、方法含在 dev split 上蒸馏 helper.py，2026-03 / 同页 Opus 4.5 66.93、DataPilot 87.57 | verified（数字属实）+ **口径警示**：单一固定数据集、可针对性预热，不代表通用能力 | HF blog nvidia |
| DABstep **100%（445/450）** | 自评全对 / MotherDuck 语义层 + 特定模型，2026-06；**剔除 5 条 gold 可证为错的题** / 其自身 88%→93%→100% 迭代 | verified（自报）+ **基准饱和/答案有误证据** | motherduck.com 博文 |
| 「多个 2026 页面都说 DABstep hard ~90%」 | — | **伪独立佐证**：Energent 94.4%、多篇比较文均回溯到 NVIDIA 那一篇 HF 博文或各自厂商自报，非独立复核 | — |
| DSBench 466 分析任务 / 74 建模任务；最佳 agent **34.12%**；RPG **34.74%** | 任务解决率 / 全集，2024-09 论文 / 人类/Kaggle 基线 | verified | arXiv 2409.07703 摘要 |
| BLADE 12 数据集 / >500 分析决策；最佳 **F1 44.8%**；「>60% 能产出非空可执行分析」 | 决策级 F1（含 precision/coverage@10）/ 全集 / 专家独立分析为 ground truth | verified | blade-bench.github.io + arXiv 2408.09667 |
| REPRO-Bench **112** 实例；最佳 agent **21.4%** | 可复现性判定准确率 / 社科论文 + 公开复现报告 / — | verified | arXiv 2507.18901 摘要 |
| REPRO-Agent「相对提升 71%」≈ 36.6% | 绝对值系由 21.4×1.71 **推算**，摘要只给相对值 | **unverified（派生数）** | 同上 |
| SourceCheckup **50%–90%** 回答未被所引来源完全支持；GPT-4+RAG **~30%** 单句无支撑 | 回答级 / 句级两个不同粒度 / 七个模型横比 | verified | arXiv 2402.02008 摘要 |
| SourceCheckup 样本量：预印本 **1200 问 / >4 万对**；发表版转述 **800 问 / 5.8 万对** | 样本规模 / **v1 预印本 vs Nat Commun 2025 正式版，两版不同** / — | 预印本 verified；发表版数字 **unverified**（nature.com 对自动抓取 303 重定向到登录） | arXiv 2402.02008；Nat Commun s41467-025-58551-6 |
| E2B **$0.000014/s per 1 vCPU**（8 vCPU $0.000112/s）；RAM **$0.0000045/GiB/s** | 按秒**墙钟**计费 / 所有档位同价 / — | verified | e2b.dev/pricing |
| E2B Hobby：**一次性 $100 额度**、10 GiB、20 并发、1h 会话；Pro **$150/月**、20 GiB、100 并发（可加至 1100）、24h 会话 | 档位限额 / Hobby vs Pro / — | verified；**$100 为一次性促销额度，不可用于长期成本建模** | 同上 |
| 「E2B 默认 2 vCPU $0.000028/s」 | 二手博文口径 / 2 vCPU 默认配置 / — | **corrected → 与一手一致**（2 × $0.000014），非独立来源 | morphllm/beam 等博文回溯至同一价目表 |
| Modal Sandbox **$0.00003942/core/s**、内存 $0.00000667/GiB/s | 按秒墙钟、**non-preemptible** / **Sandbox + Notebooks 专用档** / 普通 function 档 $0.0000131 与 $0.00000222 | verified；**口径陷阱：Sandbox 是普通档的 3.0 倍** | modal.com/pricing |
| Modal Starter **$30/月**免费额度；Team **$250/月 + 用量**（含 $100/月额度） | 套餐费 / 两档 / — | verified | 同上 |
| Cloudflare **$0.000020/vCPU-s**、$0.0000025/GiB-s、$0.00000007/GB-s；按 **10ms** 计费 | **仅活跃 CPU 时间**计费 / Workers Paid 底座 **$5/月**，含 375 vCPU-分钟 + 25 GiB-小时 + 200 GB-小时 / E2B/Modal 按墙钟——**不可直接换算比较** | verified（页面标注 last updated 2026-04-21） | developers.cloudflare.com/containers/pricing/ |
| Daytona Linux **$0.0504/vCPU-hr + $0.0162/GiB-hr** | 按秒计费 / Linux 沙箱 / — | **unverified**：一手 pricing 页只给 Windows $0.0858/vCPU/h、$200 免费额度、前 5 GiB 免费，Linux 费率未列 | daytona.io/pricing（2026-08-14 抓取时间戳） |
| Apple `container` **1.0.0 = 2026-06-09**；最新 **1.2.2 = 2026-08-08** | 发布日期 / GitHub Releases / — | verified | api.github.com/repos/apple/container/releases |
| `sandbox-exec` 仍为 deprecated，Apple 未给替代；issue #737 开于 **2026-05-12**、无官方回复 | 弃用状态 / macOS 26.x / App Sandbox、Endpoint Security、System Extensions 三条均不适用 | verified | github.com/apple/containerization/issues/737 |
| RO-Crate **1.2 发布于 2025-06-04**，Recommendation | 规范版本 / — / 1.1 | verified | researchobject.org RO-Crate 1.2 spec |
| Process Run Crate **0.5**；MUST 仅 3 项（`@type`/`@id`/`instrument`） | profile 必需项 / 单次工具执行 / 完整 Workflow Run Crate | verified | researchobject.org/workflow-run-crate/profiles/process_run_crate/ |
| DataLad run record 六字段：`cmd`/`dsid`/`exit`/`inputs`/`outputs`/`pwd` | 记录 schema / 命令行执行 / — | verified | docs.datalad.org provenance_capture |
| DVC issue **#755**（并行调度器）开于 **2018-06-08**，仍 open；`dvc repro` **无 `--jobs`**；锁文件 `.dvc/tmp/lock` | 并发能力 / 单仓库多进程 / — | verified（三个一手页面互证） | github.com/iterative/dvc/issues/755；doc.dvc.org/command-reference/repro；doc.dvc.org/user-guide/troubleshooting |
| papermill **2.7.0**，**不做输出比对** | 能力边界 / 官方文档 / nbval | verified | papermill.readthedocs.io |
| nbval 四个标记 + 无默认 sanitize + matplotlib 仅比对文本 repr | 假失败面 / 官方文档自述 / — | verified | nbval.readthedocs.io |
| monolith **无 JS 引擎** | 能力边界 / README 原文 / single-file-cli（有 Chromium） | verified | github.com/Y2Z/monolith |
| SPN2 匿名 **15 URL/分钟**、超限封 IP 5 分钟；日配额降至 1 万 | 速率限制 / 匿名 vs S3-key 认证 / — | **unverified**：官方 API 文档托管于需登录的 Google Doc，archive.org 上只有元数据页且标注非最新版 | archive.org/details/spn-2-public-api-page-docs（元数据页） |
| perma.cc 免费个人 10 条链接；付费 **$10/月 / 10 条新链接** | 档位限额 / 个人账户 / 机构 registrar 免费 | **unverified/失效**：站点对自动抓取返回 **HTTP 403**；$10 数字最早见于 infodocket **2019-01-07** | 多所大学图书馆指南（2026-04）仅证实免费 10 条 |

---

## 对本项目的设计含义

### 1. 三态而非两态：`verified` / `inference` / `unverified`

任务书写的是 verified/unverified 二态，但 F 段的证据要求中间态。若把「论文说 X，所以 Y」这种蕴含判断也塞进 `verified`，等于把 SourceCheckup 那 50–90% 的漏检率引进产品核心。

- `verified`：由**确定性程序**判定为真。只有两条来源——(a) 重跑脚本产出的数值在容差内复现；(b) 引语在本地快照抽取文本中被归一化匹配命中。
- `inference`：LLM 判断（蕴含、外推、跨源综合）。**必须携带其所依赖的 verified 锚点 id 列表**，且渲染时带可见标记。
- `unverified`：门跑失败或没跑。**默认状态**，任何异常都掉回这里。

关键不变量：**状态字段不是 agent 写的，是 gate 算出来的。** agent 只能写 claim 的内容与证据指针，`status` 字段由 `verify` 命令覆盖写。这一条同时消灭了「哈希链审计日志」的需求（C2）。

### 2. 数据类 claim 的最小溯源设计（重跑门）

**目录布局**（无锁、可并行）

```
objects/<sha[:2]>/<sha>          # CAS：原始数据、PDF、网页快照、抽取文本
claims/<claim_id>.json           # 一 claim 一文件，原子写，永不改写只新增
analysis/<claim_id>/run.py       # 单文件纯脚本，唯一输出 out.json
analysis/<claim_id>/uv.lock      # 环境锁
```

**claim 记录（数据类）最小 schema** —— 直接抄 DataLad 六字段 + 补它缺的两项：

```json
{
  "claim_id": "d-3f9a…",  "kind": "data",
  "statement": "2019–2024 年样本中 A 组均值比 B 组高 {{value}}（p={{p}}）",
  "provenance": {
    "cmd": "python run.py",  "pwd": "analysis/d-3f9a",  "exit": 0,
    "inputs":  [{"path": "data/panel.csv", "sha256": "…"}],
    "outputs": [{"path": "out.json",       "sha256": "…"}],
    "env_lock_sha256": "…",  "seed": 20260817,
    "started_at": "2026-08-17T…Z",  "duration_s": 4.2
  },
  "values": {"value": 0.137, "p": 0.0031},
  "tolerance": {"value": {"rel": 1e-9}, "p": {"rel": 1e-6}},
  "status": "verified",  "verified_at": "2026-08-17T…Z"
}
```

**规则（全部可机器强制）**
- 正文里**不许出现手打的数字**。数字一律写成 `{{claim:d-3f9a.value}}`，渲染期解析；解析不到 → 构建失败。这一条把「口径漂移」从人的自律问题变成编译期错误——正是本轮方法规则要治的那个病。
- `run.py` 必须是脚本不是 notebook（B 段）。输出必须是扁平 JSON。禁止在脚本里 print 结论句。
- 重跑在**全新临时目录**里做：从 CAS 按哈希重新物化输入 → `uv sync --frozen` → `PYTHONHASHSEED=0` + 沙箱（禁网）→ 跑 → 与 `values` 按 `tolerance` **数值比对**（不是字符串比对，这是绕开 nbval 全部假失败的关键）。
- 并行安全：claim 文件一写一个、CAS 幂等、git 只由 orchestrator 碰。

**重跑门必须 fail closed 的六个点**（任一触发 → `unverified`，并阻断该句渲染为事实陈述）
1. 任一输入的 sha256 缺失或不匹配（数据被换了）；
2. `run.py` 非零退出、超时、或触发沙箱的网络拒绝（分析脚本联网 = 不可复现）；
3. `out.json` 缺失或不符 schema；
4. 任一数值超出声明容差；
5. `values` 里存在正文引用了但 `out.json` 没产出的 key；
6. **正文里出现了未被任何 claim ref 覆盖的裸数字**（正则扫描 + 白名单：年份、章节号、引文页码）。

第 6 条是本轮方法规则的直接落地：上一轮「1/3 载荷数字口径失真」的失败，本质是数字可以脱离其产出过程独立存在于句子里。堵死这条路，口径就没法漂。

### 3. 引语类 claim 的最小溯源设计（溯源门）

**记录 schema**

```json
{
  "claim_id": "q-8c21…",  "kind": "quote",
  "quote": "even the best agent achieves only 14.55% accuracy on the hardest tasks",
  "source": {"kind":"arxiv","id":"2506.23719","url":"https://arxiv.org/abs/2506.23719",
             "locator":"abstract","retrieved_at":"2026-08-17T…Z"},
  "snapshot": {"raw_sha256":"…","text_sha256":"…","extractor":"pymupdf-1.24"},
  "archive_url": null,
  "match": {"mode":"exact_normalized","score":1.0},
  "status": "verified"
}
```

**归一化匹配算法（确定性，无模型参与）**
1. NFKC → 统一引号/破折号/省略号 → 折叠空白；
2. **PDF 专项**：跨行连字符还原（`analy-\nsis` → `analysis`）、去掉页眉页脚重复行；
3. **中文专项**（本项目必需）：全角/半角标点统一、**整串去空白**后比对（中文 PDF 抽取的空格位置不可靠）；
4. 精确命中 → `verified`；
5. 未命中 → rapidfuzz `partial_ratio ≥ 95` 找最佳跨度 → 状态 `corrected`，**把 quote 字段改写成快照里的真实跨度**再重判；
6. `< 95` → `unverified`。

**快照策略**：PDF 存原始字节 + 抽取文本两份进 CAS；网页按 D3 分流（静态 → monolith `-M`；JS 渲染 → single-file-cli）并同样存抽取文本。**跨时间只比对抽取文本的哈希，不比对快照字节**（两个工具都不保证字节确定性）。SPN2 提交 best-effort，写进 `archive_url`，失败不阻断。

**溯源门必须 fail closed 的五个点**
1. 快照文件不存在或 `raw_sha256` 不匹配；
2. **抽取文本为空或 CJK/拉丁字符比例异常**（扫描版 PDF、抽取失败）→ 必须走 OCR 路径或判 `unverified`。**绝不能因为抽取失败就让匹配「找不到」并静默降级成软表述**——这是最危险的假阴性；
3. 匹配分 < 95；
4. `retrieved_at` 超过该来源类型的 TTL 且 claim 被复用（**易变来源必须有 TTL**：定价页 30 天、榜单 30 天、arXiv 论文永久、正式发表版永久）；
5. claim 声称是直接引语（带引号渲染）但 `match.mode` 不是 `exact_normalized`。

**第三态的强制**：只给出「某论文表明 Y」而无逐字跨度的转述，必须携带一个 `anchor_span`（快照里的真实文字）。门只验证 anchor 存在；anchor → 转述 的蕴含永远记为 `inference`，机器不得升为 `verified`。这条把 SourceCheckup 的 50–90% 风险隔离到一个显式标记的类别里，而不是让它渗进全文。

### 4. 采纳 / 跳过一览

| 组件 | 决定 | 理由（一句） |
|---|---|---|
| 自建 CAS（sha256 + 原子 rename） | **采纳** | 并行无锁、30 行、幂等 |
| 一 claim 一文件 append-only 账本 | **采纳** | 消灭合并冲突；状态由 gate 计算 |
| DataLad run-record 六字段 schema | **采纳（抄结构）** | 现成的最小充分记录 |
| Process Run Crate 0.5 导出器 | **采纳（仅 publish 期）** | MUST 只三项，成本近零，换来学术界可读的交付物 |
| `uv.lock` + `PYTHONHASHSEED=0` + 显式 seed | **采纳** | 确定性的最低门槛 |
| `sandbox-exec`（禁网 + 限写）+ 硬超时 | **采纳（v1）** | 零成本、零延迟、今天可用 |
| OCI 镜像契约（`container run` 可跑） | **采纳（写进契约，v1.5 启用）** | 逃生口 + 外部评审可复现 |
| monolith / single-file-cli 双路快照 | **采纳** | 覆盖静态与 JS 渲染两类页面 |
| SPN2 归档 | **采纳（best-effort，不阻断）** | 锦上添花，速率限制口径未明 |
| DVC | **跳过** | 全局锁 + 无并行 repro，与超并行前提冲突 |
| DataLad / git-annex（作为依赖） | **跳过** | 同上，继承 git 索引锁 |
| PROV-O RDF 作为工作格式 | **跳过** | 成本远超收益；导出用 RO-Crate 足够 |
| 完整 Workflow Run Crate | **跳过** | 我们没有 workflow 引擎，Process 层就够 |
| papermill / nbval / notebook 验证 | **跳过** | papermill 不比对；nbval 的比对即 false-red 之源 |
| Merkle / 哈希链审计日志 | **跳过** | 威胁模型不成立；重跑门已提供功能性防篡改 |
| perma.cc | **跳过** | 付费、403 抓不到一手价、能力已被本地快照覆盖 |
| E2B / Modal / Daytona / Cloudflare 云沙箱 | **跳过（v1）** | 唯一收益是隔离强度，代价是数据出本机 |

### 5. v1 范围判定（F 段的直接推论）

- **v1 只承接封闭式数据 claim**：问题由人（或上游 planner，且人可见）写成「一个可判定的问句 + 一个具体数据文件」，agent 只负责写 `run.py`。这一层的能力已被 DABstep 的饱和证据支持到「足以当地基」。
- **开放式端到端分析（选题→选方法→选口径→出结论）在 v1 不得产出 `verified`**。DSBench 34.12% / BLADE F1 44.8% / CORE-Bench-Hard 21.48% / REPRO-Bench 21.4% 都指向同一件事：**定义权一旦交出去，六到八成的产出是错的**。这类产出在 v1 只能是 `inference`，且必须并列展示它依赖的 verified 锚点。
- **成本形状**：CORE-Bench 里 hard 任务单价是 easy 的 4.6 倍（$2.96 vs $0.64，GPT-4o 2024 价）。移植到 DeepSeek v4 绝对值会低一个量级，但「难任务成本非线性上升」的形状不变 → 重跑门必须有**每 claim 的时间与 token 预算**，超预算即 `unverified`（而不是无限重试）。

---

## 未决与风险

1. **SPN2 速率限制无一手来源**（官方 API 文档在需登录的 Google Doc 内；archive.org 上的镜像标注非最新版）。设计上已用「best-effort、不阻断」把风险吸收掉，但若未来把 `archive_url` 提升为交付物要求，必须先拿到一手速率口径。
2. **perma.cc 定价无法核实**（站点对自动抓取返回 403；仅能确认「个人免费 10 条」这一条来自多所大学图书馆指南；$10/月来自 2019 年报道，视为失效）。当前决定是跳过，故不阻塞。
3. **`sandbox-exec` 弃用时间线未知**。apple/containerization #737 至 2026-05-12 无 Apple 回复。缓解：把「同一 `run.py` 能在 pinned OCI 镜像里跑」写进契约，使切换到 `container run`（1.0.0 于 2026-06-09 发布，1.2.2 于 2026-08-08）成为零改动操作。剩余风险：Apple 在某次小版本里直接移除 `sandbox-exec`，届时 v1 的隔离层需在一次迭代内切走。
4. **Daytona Linux 费率未核实**（一手页只列 Windows 与免费额度）。不影响 v1 决定（不上云沙箱），但若后续评估云沙箱须重取。
5. **DABstep 类基准的可信度本身在下降**：MotherDuck 证实 450 题里至少 5 题 gold 答案可证为错，且 Adyen 不公布答案、需从他人提交反推。若我们要用任何公开基准做本项目的自评回归，**不能直接用 DABstep 分数**，须自建一小组带已知真值的封闭式回归任务。
6. **中文 PDF 文本抽取是溯源门最大的假阴性来源**（CNKI/万方导出常见乱序、乱码、缺字）。已在门里加了「抽取质量哨兵」（空文本 / 字符比例异常即判 `unverified`），但该哨兵的阈值需要用真实中文论文样本标定，v1 前必须做一次实测；在标定完成前，中文引语门应偏保守（宁可多判 `unverified`）。
7. **快照工具的字节非确定性未被文档承诺**（single-file-cli 未说明；monolith 默认注入时间戳，需 `-M`）。当前设计已回避（跨时间只比抽取文本），但如果将来要做「快照未被篡改」的字节级校验，需要先实测两个工具的确定性。
8. **`verified` 的语义边界仍需在写作规范里钉死**：`verified` 只保证「这个数字确实来自这段代码跑这份数据」或「这句话确实出现在那份快照里」，**不保证方法正确、样本代表、口径恰当**。这一点若不在产品文案与文档模板里显式声明，会制造比不做验证更危险的错误信心。
