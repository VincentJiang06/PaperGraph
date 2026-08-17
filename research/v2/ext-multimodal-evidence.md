# 外部调研 v2 — 图表/表格承载的数值证据：验证的能力边界

调研日期：2026-08-17（所有"当前 SOTA"类结论以此日期为准，半年内必然漂移）
调研方法：10 次 WebSearch（会话级搜索预算在第 10 次后被兄弟 agent 共同耗尽）+ 22 次一手源 WebFetch/PDF 直读。凡进入核验表的数字，均以 arXiv 摘要页/HTML 全文、ACL Anthology、PMC 全文、Semantic Scholar Graph API（返回出版方原始 abstract）为准，未使用任何博客/摘要站作为数字来源。

---

## 结论摘要

**1. 表格已近饱和，图表远未解决。这是本维度最重要的结构性事实。**
文档解析里"表格"这一项在干净版面上基本被打穿（OmniDocBench 顶部模型总分已达 94.6%，被从业者公开称为 saturated，2026-02-24），而图表数值读取在真实难度基准上仍然崩塌：同一个 Claude Sonnet 3.5 在 ChartQA 上 90.5%、在 ChartQAPro 上只有 55.81%。**因此本项目的第一条路由规则不是"图表怎么读"，而是"能不能不读图表"** —— 优先走表格/正文/附录/作者数据仓库。

**2. 决定图表可读性的头号变量是"有没有印刷数据标签"，不是模型强弱。**
一手实测（Gemini 2.5 Flash，50 张 Vega-Lite 图）：有标签时 MAPE 1.3%–1.8%，去掉标签后 MAPE 升到 7.2%–7.4%。同一模型、同一批图、只改标签，误差放大约 4–5 倍。这是一条可以直接写进代码的门控条件。

**3. "表格结构对了"和"数字对了"是两件事，且前者会伪装成后者。**
Gemini 2.5 Flash 对 200 张 ChartQA 图能生成正确表结构 194/200（97.0%），但同一批工作里无标签图的数值 MAPE >7%。结构正确率高会让下游误以为抽取成功——**结构正确率不得作为任何验证信号**。

**4. 最致命的失效模式是"判对了结论、指错了格子"（grounding error），且它高频。**
SciTabAlign（EMNLP 2025 Findings，SciTab 扩展）：GPT-4o 标签 Macro-F1 88.4，但恢复人类标注的关键单元格 Macro-F1 只有 34.8；在 exact-match 设定下**没有任何模型能让"标签+依据同时正确"超过 50%**。SciTab 原文对 PoT 错误的人工归因也显示 grounding error 占 50%。含义：**"模型说这个数支持该结论"这件事，几乎不携带"模型指的是正确那个数"的信息**。本项目若只校验结论、不校验地址，等于没校验。

**5. 自洽性（self-consistency）只能当分诊信号，不能当验证闸门。**
一手实测：抽样离散度与抽取准确率的 Spearman ρ 仅 −0.30 ~ −0.37（p<0.001，WB-ChartExtract）。相关显著但极弱（解释方差约 9%–14%）。而且代价高：K=20 时仅 27.7% 的图收敛，早停后仍需平均 16.11 次采样/图。**结论：多次采样一致 ≠ 正确，只能用于把"高离散度"的图挑出来送人工。**

**6. 图表族之间差异极大，必须分族路由，不能一刀切。**
同一模型（Gemini 2.5 Flash）在 ExChart-Bench 上的 Adaptive MAPE：scatter 2.63% / bar 3.78% / line 4.35% / **pie 11.58% / radar 28.01%**。雷达图误差是散点图的 10 倍以上。

**7. 领域专用管线在其窄域内远强于通用 VLM，且能给出可复核的中间产物。**
KM-GPT（GPT-5 驱动的 Kaplan–Meier 重建）在 540 张合成图上：坐标轴范围与刻度间隔提取 100%、at-risk 表提取 100%、生存概率 median AE 0.005、处理成功率 538/540（99.6%），对照 SurvdigitizeR 失败 178 张（33.0%）。**窄域 + 可复核约束（at-risk 表、单调性）是把图表数字从"估计"抬到"可验证"的唯一已证路径。**

**8. 人机协作的真实天花板约 90%，不是 99%。规划不得承诺更高。**
一篇 2026-07 发表的系统综述（27 项研究）：LLM 数据抽取总体 47%–99.9%，其中**分类/字符串变量 74%–96%，数值变量仅 47%–88%**；Claude 3.5 Sonnet 在辅助工作流中 91.0%（95% CI 90.4–91.6），对照纯人工 89.0%。AutoForest 用户研究：全自动 82.5%，加人工编辑后 90.2%。LEADS：专家+AI 0.85 vs 专家 0.80。**三条独立证据线都落在 ~0.85–0.91 这个带里。**

**9. 错误结构是"漏"不是"编"，这反转了防护重心。**
同一综述：遗漏（omissions）占错误类型的 60%–74%，幻觉率仅 0.08%–6%。**本项目对图表证据的守门程序应以"覆盖率/漏项检测"为主、以"反幻觉"为辅**——这与文本类验证的直觉相反。

**10. 评测指标本身会骗人，选错指标等于自欺。**
TEDS 与人类判断的相关只有 r=0.68（同一研究里 LLM-as-judge 达 r=0.93）；RMSF1 的数值容差 θ=0.1 意味着**"判对"的单元格仍可有 10% 相对误差**。所以"某模型 RMSF1 87.8"绝不等于"数字精确到能进正文"。

---

## 系统与机制逐条（含 URL）

### A. 真实难度图表基准：饱和基准 vs 硬基准的落差

**A1. CharXiv（NeurIPS 2024 D&B）** — https://arxiv.org/abs/2406.18521
2,323 张取自 arXiv 论文的真实图表，分 descriptive（基础元素识别）与 reasoning（跨视觉元素综合）两类问题，全部人工挑选与校验。摘要原文：最强闭源模型 GPT-4o 在 reasoning 上 47.1%，最强开源 InternVL Chat V1.5 29.2%，人类 80.5%。同时给出一条对本项目非常重要的方法论警告：*"a simple stress test with slightly different charts or questions can deteriorate performance by up to 34.5%"* —— 即**在模板化基准上的高分不可外推到真实图表**。
（备注：广泛流传的"human descriptive 92.1%"我无法从可访问的一手渠道确认，见核验表标记为 unverified。）

**A2. ChartQAPro（ACL 2025 Findings）** — https://aclanthology.org/2025.findings-acl.978/ ； arXiv https://arxiv.org/abs/2504.05506
1,341 张图、1,948 题，含信息图与仪表盘，题型含多选、对话式、假设式、**不可回答题**。21 个模型评测。摘要原文：*"Claude Sonnet 3.5 scores 90.5% on ChartQA but only 55.81% on ChartQAPro"*。
**版本差异（一手核对到的分歧）**：ACL Anthology 定稿写 *"1,341 charts from 99 diverse sources"*，arXiv 摘要页写 *"157 diverse sources"*。同一论文两个版本数字不一致 —— 这本身就是本项目要防的那类问题的实例：引用时必须锁版本。

**A3. ChartBench —— 同名两篇，必须消歧（本轮抓到的一个真实误引）**
- ChartBench (arXiv:2312.15915, 2023-12) — https://arxiv.org/abs/2312.15915 — 42 类、66.6k 图、600k QA，提出 Acc+ 指标，评测 18 开源 + 3 闭源模型。**其摘要中不含 GPT-5，也不含"40–60% 下降"的表述**（时间上也不可能）。
- ChartBench (ACM VRISP 2025, 2025-09-12, DOI 10.1145/3772128.3772169) — https://dl.acm.org/doi/10.1145/3772128.3772169 — 经 Semantic Scholar Graph API 取回出版方原始摘要，确认其中确有：*"systematic evaluation of mainstream models including GPT-4o, GLM-4.1V, GPT5-nano, and GPT5, we find that even the most advanced models experience 40-60% drops in numerical extraction accuracy when processing unlabeled complex charts"*，且覆盖 *"20 core data distribution patterns"*。
**机制教训**：搜索引擎摘要把这两篇混成一篇，并把 GPT-5 的结论挂到 2023 年的论文上。若不打开一手源，这条会被原样写进规划文档。（"GPT-5 在堆叠柱状图上 59.2%"这个具体数字，全文 403 无法读取，标记 unverified，禁止使用。）

### B. 有无数据标签：可门控的分水岭

**B1. ExChart / ExChart-Bench（CHI 2026）** — https://arxiv.org/abs/2606.29808 ； HTML https://arxiv.org/html/2606.29808v1
预研（Table 1–2，Gemini 2.5 Flash）：200 张 ChartQA 图中表结构正确 194/200（97.0%）；50 张 Vega-Lite 图（5 类各 10 张）上 MAPE —— 有标签：逐值提问 1.8%、整表提问 1.3%；无标签：逐值 7.4%、整表 7.2%。
正式基准 ExChart-Bench：3,600 组 chart-table-prompt，33,757 个数值，744 真实 + 2,856 合成；bar 800，其余四类各 700。
指标为 **Adaptive MAPE**：`(1/n)Σ|v̂ᵢ−vᵢ|/V_max × 100%`，以每图最大绝对值归一，单点误差 >100% 截断为 100%。注意这是**按图幅归一**而非按单值归一，比逐值相对误差宽松。
分族结果（Adaptive MAPE，越低越好）：Gemini 2.5 Flash — bar 3.78 / line 4.35 / scatter 2.63 / pie 11.58 / radar 28.01；GLM-4.5V — 3.83 / 5.56 / 4.79 / 9.24 / 13.03；ExChart(7B, 微调) — 5.66 / 7.93 / 0.85 / 5.73 / 3.21。
**推论（我的，非原文）**：微调小模型在 radar 上（3.21）远好于 Gemini（28.01），说明 radar 的难点是"没见过这种编码"而非"分辨率不够"——可被专用工具解决，不必送人工，但通用 VLM 必须禁用于 radar。

### C. 复杂真实图表上的抽取上限与自洽性的真实价值

**C1. Self-Ensembling VLMs for Chart Data Extraction（arXiv:2605.27298, 2026-05-26）** — https://arxiv.org/abs/2605.27298 ； HTML https://arxiv.org/html/2605.27298v1
提出对同一图重复采样表格输出、按单元格取中位数聚合，并用样本间离散度做不确定性估计。
新基准 **WB-ChartExtract**：1,000 张图，源自世界银行数据（52 指标、218 国、65 年），四种图型（line/area/grouped bar/stacked bar）× 四种绘图库（Matplotlib/Seaborn/Plotly/Bokeh），平均数据点数为 ChartQA 的 **7 倍**。
指标 **RMSF1**：把预测与真值都看作 (行头, 列头, 值) 三元组集合，行列头用阈值化归一化 Levenshtein，数值用 clipped relative error，实体相似度 `(1−NL_τ)(1−D_θ)`，**τ=0.5、θ=0.1**，最小代价二部图匹配后取 P/R 调和平均；同时评估转置取高分。
前沿模型单次通过（single-pass）成绩 —— ChartQA → WB-ChartExtract：**GPT-5.1 84.80 → 51.26；Claude Opus 4.6 87.71 → 60.99；Gemini 2.5 Pro 88.23 → 87.83**。
集成增益（single-pass → ensembled）：Qwen3-VL 91.43→93.21 / 52.91→56.23；Seed 1.6 Flash 81.62→87.04 / 35.08→43.17；Llama 4 Scout 75.13→77.10 / 30.41→33.14；DePlot 88.32→89.02 / 23.06→24.57；TinyChart 95.20→95.28 / 28.61→29.37。
**自洽性与正确性的关系（本维度的关键裁决依据）**：*"On WB-ChartExtract, relative MAD is significantly anti-correlated with RMSF1 (Spearman ρ=−0.34 for Umed, ρ=−0.37 for Umean, and ρ=−0.30 for Umax; all p<0.001)"*。
收敛代价：*"At K=20 only 27.7% of images have converged"*；早停策略平均 16.11 次采样/图，保留 99% 的集成增益。

### D. 表格抽取：结构近饱和，但评测指标本身不可信

**D1. OmniDocBench（CVPR 2025）** — https://github.com/opendatalab/OmniDocBench — 文本用归一化编辑距离、表格用 TEDS、公式用 CDM；模块化 pipeline 解析器在学术论文/财报上仍优于端到端 VLM。
**D2. "OmniDocBench is Saturated"（LlamaIndex, 2026-02-24）** — https://www.llamaindex.ai/blog/omnidocbench-is-saturated-what-s-next-for-ocr-benchmarks — GLM-OCR 94.6%、PaddleOCR-VL-1.5 >94%、Gemini 3 Pro 90.3%；作者论点是剩余提升多为 edge case 修补，且 TEDS 惩罚的往往是 HTML/LaTeX 表述差异而非语义错误（举例 TEDS 0.3825 与 0.5581 的输出实际语义正确）。
**D3. Beyond String Matching: Semantic Evaluation of PDF Table Extraction（arXiv:2603.18652, 2026-06-01）** — https://arxiv.org/html/2603.18652 — 100 页合成 PDF、451 张表、518 组配对、21 个解析器、1,554 条人工评分（Krippendorff α=0.77）。**TEDS 与人类判断 Pearson r=0.68，规则类指标全部 r≤0.70；LLM-as-judge（Gemma-4-31b-it）r=0.93**。解析器排名（10 分制）：Gemini 3 Pro 9.55、Gemini 3 Flash 9.50、LightOnOCR-2-1B 9.08、Mistral OCR 3 8.89。该文**未单独报告数值单元格准确率**（只报整体语义分）——这是一个真实缺口。

### E. 表格→论断验证：SciTab 谱系

**E1. SciTab（EMNLP 2023）** — https://arxiv.org/abs/2305.13186 ； 全文 https://aclanthology.org/2023.emnlp-main.483.pdf （已逐页直读 Table 1/4/5）
1,225 条真实论文论断（Supported 37% / Refuted 34% / NEI 29%），领域为科学论文，标注者为专家（对照 TabFact/FEVEROUS/SEM-TAB-FACTS 均为 AMT 众包）；最大推理跳数 11，平均推理深度 4.76，**86% 的论断需要 ≥3 步推理**。标注一致性 Cohen's κ = 0.630（假论断任务，872 条）/ 0.719（NEI 任务，900 条）。
Table 4（Macro-F1，zero-shot / in-context）：**GPT-4 zero-shot 2-class 78.22、3-class 64.80；GPT-4+CoT in-context 2-class 76.85、3-class 62.77（CoT 反而更差）**；最佳开源 zero-shot 2-class Vicuna-7B 63.62、3-class FLAN-T5-XL 38.05，原文称二者*"only moderately better (+13.62 and +4.72) than random guessing"*；**Human in-context 2-class 92.40、3-class 84.73**。
Table 5（对 PoT 错误样本的人工归因，50 条）：**grounding errors 50%、ambiguity 22%、calculation 20%、program 8%**。
**人类基线的口径必须标注**：human 数字来自**1 名标注者**，2-class 抽 40 条、3-class 抽 60 条。样本极小，不可当作稳健人类上限引用。

**E2. Table-Text Alignment / SciTabAlign（EMNLP 2025 Findings, arXiv:2506.10486）** — https://arxiv.org/abs/2506.10486 ； HTML https://arxiv.org/html/2506.10486v2
把表格-论断对齐重构为**解释任务**：要求模型指出验证该论断所必需的最小单元格集合。数据集从 SciTab 的 868 条论断中剔除歧义样本后得 **372 条（195 supported / 177 refuted，2 分类）**；人工之间的单元格重叠一致性为 precision 75.2% / recall 89.1% / macro-F1 78.0%。
Table 1（标签 Macro-F1 vs 单元格依据 Macro-F1）：GPT-4o **88.4 → 34.8**；Qwen 2.5 72B **83.5 → 50.8**（依据项最佳）；Llama 3.1 70B 75.2 → 36.8；Qwen 2.5 7B 66.3 → 20.7；Llama 3.1 8B 53.2 → 23.6；TAPAS-large 51.6。
Table 3：exact-match 设定下 *"none of the models achieve a percentage of 50% for this case"*（标签与依据同时正确），多数模型呈现"标签对、依据错"占 60%–88%。
（口径提醒：此处 GPT-4o 的 88.4 是在**剔除歧义后的 372 条 2 分类子集**上，与 E1 中 GPT-4 在原 SciTab 上的 78.22 不可直接比较。）

**E3. GLEAN（arXiv:2603.02212, 2026-01-22）** — https://arxiv.org/abs/2603.02212 — 提出污染感知的轻量表格推理评测协议，覆盖 TabFact / WTQ(Squall) / TableBench / RobuT / SciTab；用 Squall gold SQL 作可执行锚（95.2% 执行率），给出 L0–L4 错误分类；发现 TAPEX 错误偏 grounding(L3)、TAPAS 偏 hallucination/abstention(L2/L0)；证据行启发式对照 SQL 派生行为 **0.62 precision / 0.71 recall（混合召回 0.81）**；并指出 **retrieval Recall@K 可以饱和而端到端 EM/F1 仍然受限**。摘要未给出具体污染幅度数字。

### F. 领域专用抽取管线及其误差界

**F1. KM-GPT（生存曲线 → 个体患者数据，2025-09 bioRxiv / PMC12458341）** — https://pmc.ncbi.nlm.nih.gov/articles/PMC12458341/
GPT-5 多模态推理 + OCR + K-medoids 曲线分离 + 迭代 KM 算法（iKM）+ 图像增强（ESPCN/Laplacian/NLM）。
合成验证：540 张 KM 图（27 组参数 × 20 重复）。**坐标轴范围与刻度间隔提取 100%；at-risk 风险表提取 100%；生存概率 median AE 0.005（95% CI 0.000–0.034）；全随访期 median IAE 0.018（0.002–0.088）；中位 OS 的 AE 0.005（0.000–0.088）；成功处理 538/540（99.6%）**，2 张失败归因于数字化误差。
对照：*"SurvdigitizeR failed to process 178 figures, resulting in a failure rate of 33.0%"*。
真实验证：3 项转移性乳腺癌试验（6 条曲线），例：bevacizumab+paclitaxel 报告 mPFS 11.0 月，KM-GPT 重建 10.9（9.8–12.2）。
**口径警告**：99.6% 与 100% 都是在**自己生成的合成图**上取得；真实世界验证只有 3 项试验 / 6 条曲线。不可把 100% 当作真实论文图上的表现。

**F2. AutoForest（森林图端到端生成，arXiv:2606.02403v2, 2026-06-02）** — https://arxiv.org/html/2606.02403v2
数据：32 张森林图，取自 18 篇 Cochrane 系统综述，覆盖 56 项纳入研究，206 张表。用户研究：8 人（4 专家 + 4 学生）。
数据抽取准确率：**全自动 82.5%（专家场景）/ 83.3%（学生场景）；加人工编辑后 90.2%（专家）/ 86.4%（学生）**；表格转换保真：**数值单元格准确率 97.8%、表格检测 98.1%**。
时间：手工（RevMan）70.4 分钟（专家）/ 53.8（学生）→ AutoForest+编辑 29.8 / 26.5，*"nearly halved the time ... (p<0.001)"*。
**必须标注的口径陷阱**：文中"手工专家基线 45.8%"是**限时实验室任务**中 4 名专家的表现，**不是 Cochrane 双人独立抽取流程的准确率**。把 45.8% 当作"人类抽取准确率"引用即是典型的口径掉包，本项目禁止此类引用。

### G. 人 vs 人+AI：三条独立证据线

**G1. 系统综述（J Biomed Inform, 2026-07-25）** — DOI 10.1016/j.jbi.2026.105086（出版方摘要经 Semantic Scholar Graph API 取回）
检索至 2025-12，纳入 27 项研究，覆盖 GPT-4/4o(n=15)、Claude 2–3.5(n=10)、Gemini(n=3) 及 Llama/Mistral/Qwen/DeepSeek。
**总体准确率 47%–99.9%；分类与字符串变量 74%–96%，数值数据仅 47%–88%**；**Claude 3.5 Sonnet 在辅助工作流 91.0%（95% CI 90.4–91.6），高于纯人工 89.0%**；Claude 对 GPT 的头对头优势 OR 1.70（事件计数）；**遗漏占错误类型 60%–74%，幻觉率仅 0.08%–6%**；时间节省 33%–87%；74.1% 研究在 PROBAST+AI 下为低偏倚风险，TRIPOD-LLM 平均合规 88.5%。结论明确：*"integration as assistive tools within dual-extraction workflows requiring human verification, rather than as autonomous extractors"*。

**G2. LEADS（Nature Communications 2025, PMC12460617）** — https://pmc.ncbi.nlm.nih.gov/articles/PMC12460617/
被试内设计（每人一半主题分到 Expert-only、一半到 Expert+AI）。数据抽取：**Expert+AI 0.85 vs Expert-only 0.80**，平均耗时 113.9s → 83.3s（**26.9% 相对时间节省**）。文献筛选：**Recall 0.81 vs 0.78**，580s → 449s（**20.8%**），P<0.001（Mann–Whitney U）。LEADS 独立抽取试验结果 0.78 vs GPT-4o 0.45。
**口径警告**：抽取实验只有 **2 名医学研究者**，每人 360 个抽取任务。0.85 vs 0.80 的 5 个百分点差来自 n=2 的被试样本，不可当作总体效应量。

**G3. 图形数字化的人类基线（Drevon, Fursa & Malcolm, Behavior Modification, 2017）** — https://journals.sagepub.com/doi/10.1177/0145445516673998
2 名编码员从 18 项研究、36 张图、168 条数据序列中提取 3,596 个数据点，报告在数据点数量、y 值、Tau-U 三方面均有高编码者间信度，但作者仍建议对子集做信度检验并对编码员做培训。**具体的 ICC/相关系数数值在可访问渠道（SAGE 全文、PubMed、PALscholar）均被墙，标记 unverified，禁止在文档中给出裸数字。**

### H. 图形感知的心理物理学边界

**H1. Evaluating "Graphical Perception" with Multimodal LLMs（arXiv:2504.04221, 2025-04-05）** — https://arxiv.org/html/2504.04221
复刻 Cleveland–McGill 基本感知任务。基本任务上人类仍占优：angle 人类 MLAE 3.22 vs 微调模型 5.01；area 人类 3.64 vs 10.09；volume 人类 5.18 vs 8.63。位置-角度/位置-长度任务上微调模型反超人类（如 bar 微调 MLAE −2.48 vs 人类 1.035）。人类基线来自 51 名（Cleveland/McGill 与 Heer/Bostock）与 25 名 MTurk 被试；模型每任务测试图仅 55 张。
**推论（我的，非原文）**：反超发生在**微调模型 + 与训练集同源的合成图**上，属于分布内拟合而非感知能力，不可外推到论文里的真实图。可外推的部分只有"角度/面积/体积编码对模型仍显著更难"这一序关系——这与 B1 中 pie(11.58) 和 radar(28.01) 的高误差互相印证（两条独立证据线，非同源）。

---

## 载荷数字核验表

格式：数字 | 口径三元组（什么指标 / 什么样本与条件 / 与什么比较） | 状态 | 一手出处

| # | 数字 | 口径三元组 | 状态 | 一手出处 |
|---|---|---|---|---|
| 1 | 47.1% | CharXiv **reasoning 题**准确率 / GPT-4o，CharXiv（2,323 张 arXiv 真实图）/ 对比最强开源 29.2% 与人类 80.5% | verified | arXiv:2406.18521 摘要原文 |
| 2 | 29.2% | 同上，最强开源模型 InternVL Chat V1.5 | verified | arXiv:2406.18521 摘要 |
| 3 | 80.5% | CharXiv 上的人类准确率；摘要仅写 "human performance of 80.5%"，紧接 reasoning 比较之后，按上下文为 reasoning 口径 | verified（口径由上下文推定，非原文明写） | arXiv:2406.18521 摘要 |
| 4 | 92.1% | 传称为 CharXiv **descriptive** 题人类准确率 | **unverified** — 仅见于二手摘要，NeurIPS PDF 超限、OpenReview 反爬、charxiv.github.io 排行榜未上线 | 无可用一手源，禁止使用 |
| 5 | up to 34.5% | 在**模板化旧基准**上略改图或题后的性能跌幅上限 / 未指明具体模型 / 说明旧基准分数不可外推 | verified | arXiv:2406.18521 摘要原文 |
| 6 | 90.5% → 55.81% | 同一模型 Claude Sonnet 3.5 的准确率 / ChartQA vs ChartQAPro（1,341 图、1,948 题、21 模型评测）/ 同模型跨基准 | verified | ACL 2025 Findings 978 摘要原文 |
| 7 | 99 vs 157 | ChartQAPro 图表来源数 / ACL 定稿写 99、arXiv 摘要页写 157 / 同论文两版本 | **corrected**：存在版本分歧，引用须锁版本；不得笼统写"157 个来源" | aclanthology.org/2025.findings-acl.978/ 与 arXiv:2504.05506 |
| 8 | 40–60% | 无标签复杂图上**数值抽取准确率的跌幅** / GPT-4o、GLM-4.1V、GPT5-nano、GPT5，ChartBench（20 种数据分布模式）/ 对比有标签图 | verified，但**必须注明是 ACM VRISP 2025 版 ChartBench（2025-09-12）**，与 arXiv:2312.15915 同名不同文 | Semantic Scholar Graph API 返回的出版方原始摘要，DOI 10.1145/3772128.3772169 |
| 9 | 59.2% | 传称 GPT-5 在堆叠柱状图上的准确率 | **unverified** — ACM 全文 403；两个 ChartBench 的摘要均无此数；禁止使用 | 无 |
| 10 | 66.6k 图 / 42 类 / 600k QA | ChartBench(2023) 规模 | verified，注意这是 **arXiv:2312.15915 那一篇**，其中不含 GPT-5 | arXiv:2312.15915 摘要 |
| 11 | 1.3% / 1.8% | **有**数据标签时的 MAPE（整表提问 / 逐值提问）/ Gemini 2.5 Flash，50 张 Vega-Lite 图（5 类各 10 张）/ 对比无标签 7.2%/7.4% | verified | arXiv:2606.29808 Table 2 |
| 12 | 7.2% / 7.4% | **无**数据标签时的 MAPE（整表 / 逐值）/ 同上同批图同模型 / 同上 | verified | arXiv:2606.29808 Table 2 |
| 13 | 97.0%（194/200） | **表结构**正确率（非数值正确率）/ Gemini 2.5 Flash，200 张 ChartQA 图（100 双列 + 100 多列）/ 与数值 MAPE>7% 并置以显示结构-数值脱节 | verified | arXiv:2606.29808 Table 1 |
| 14 | 28.01% / 11.58% / 4.35% / 3.78% / 2.63% | **Adaptive MAPE**（按每图最大绝对值归一，单点误差 >100% 截断）/ Gemini 2.5 Flash，ExChart-Bench radar/pie/line/bar/scatter / 族间比较 | verified | arXiv:2606.29808 Table 4 |
| 15 | 3,600 组 / 33,757 值 / 744 真实 + 2,856 合成 | ExChart-Bench 规模构成 | verified | arXiv:2606.29808 |
| 16 | 84.80 → 51.26 | **RMSF1**（θ=0.1 数值容差，τ=0.5 表头容差，二部图匹配）/ GPT-5.1 单次通过，ChartQA → WB-ChartExtract / 同模型跨基准 | verified | arXiv:2605.27298 HTML 结果表 |
| 17 | 87.71 → 60.99 | 同 #16，Claude Opus 4.6 | verified | arXiv:2605.27298 |
| 18 | 88.23 → 87.83 | 同 #16，Gemini 2.5 Pro —— **异常值**，与另两家 30+ 分的跌幅不一致 | verified（数字），但**机制存疑**，见风险节 R3 | arXiv:2605.27298 |
| 19 | ρ = −0.34（−0.30 ~ −0.37，p<0.001） | **Spearman 相关**：样本间相对 MAD（离散度）vs RMSF1（正确性）/ WB-ChartExtract 1,000 图 / 三种不确定度聚合方式 Umed/Umean/Umax | verified | arXiv:2605.27298 HTML 原句 |
| 20 | 27.7% @ K=20；早停后 16.11 次/图 | 自洽采样**收敛率**与平均采样次数 / WB-ChartExtract / 早停保留 99% 集成增益 | verified | arXiv:2605.27298 |
| 21 | 最高 +23%（相对） | 自集成相对单次通过的**相对提升上限** / WB-ChartExtract / 非绝对分数提升 | verified；对照绝对值：Seed 1.6 Flash 35.08→43.17 是该基准上最大绝对增益 | arXiv:2605.27298 摘要 + 结果表 |
| 22 | 7× | WB-ChartExtract 图的平均数据点数 / 相对 ChartQA | verified | arXiv:2605.27298 摘要 |
| 23 | 78.22 / 64.80 | **Macro-F1**，zero-shot / GPT-4，SciTab 2-class / 3-class（1,225 条专家标注论断）/ 对比人类 92.40 / 84.73 | verified | SciTab EMNLP 2023 Table 4（PDF 逐页直读） |
| 24 | 76.85 / 62.77 | Macro-F1，in-context + CoT / GPT-4，SciTab 2/3-class / **低于不加 CoT**，说明 CoT 在此任务无增益 | verified | SciTab Table 4 |
| 25 | 92.40 / 84.73 | Macro-F1 / **1 名标注者**，2-class 抽 40 条、3-class 抽 60 条 / 作为人类上界 | verified 但**样本极小（n=1 标注者，40/60 条）**，不可作稳健人类基线 | SciTab §4.1 + Table 4 |
| 26 | 50% / 22% / 20% / 8% | PoT 错误样本的人工归因占比：grounding / ambiguity / calculation / program / 50 条错误样本 | verified | SciTab Table 5 |
| 27 | 86%；平均深度 4.76；最大 11 跳 | SciTab 论断需 ≥3 步推理的比例 / 100 条人工标注推理图样本 | verified | SciTab §3.1 + Fig.3 |
| 28 | κ=0.630 / 0.719 | Cohen's Kappa 标注者间一致性 / 假论断任务 872 条 / NEI 任务 900 条 | verified | SciTab §2.3 |
| 29 | 88.4 → 34.8 | **Macro-F1**：标签预测 → 关键单元格依据恢复 / GPT-4o，SciTabAlign 372 条 2 分类子集 / 同模型同样本两项任务 | verified | arXiv:2506.10486 Table 1 |
| 30 | 50.8 | 单元格依据 Macro-F1 的**最佳成绩** / Qwen 2.5 72B + CoT，同上样本 | verified | arXiv:2506.10486 Table 1 |
| 31 | <50% | "标签与依据同时正确"的比例上界，**所有模型无一例外** / exact-match 设定，SciTabAlign | verified | arXiv:2506.10486 Table 3 原句 |
| 32 | 372 条（195/177） | SciTabAlign 样本量，由原 868 条剔除歧义后得；人工间单元格一致性 P 75.2 / R 89.1 / F1 78.0 | verified | arXiv:2506.10486 |
| 33 | r=0.68 vs r=0.93 | **与人类判断的 Pearson 相关**：TEDS vs LLM-as-judge（Gemma-4-31b-it）/ 451 张表、518 组配对、1,554 条人工评分、21 个解析器、Krippendorff α=0.77 / 规则指标全体 r≤0.70 | verified | arXiv:2603.18652 |
| 34 | 9.55 / 9.50 / 9.08 / 8.89（10 分制） | LLM-judge 表格抽取语义分 / Gemini 3 Pro、Gemini 3 Flash、LightOnOCR-2-1B、Mistral OCR 3，100 页合成 PDF 451 表 | verified；注意为**合成 PDF**，非真实扫描件 | arXiv:2603.18652 |
| 35 | 94.6% / >94% / 90.3% | OmniDocBench **总分**（文本编辑距离 + 表格 TEDS + 公式 CDM 的均值）/ GLM-OCR、PaddleOCR-VL-1.5、Gemini 3 Pro / 支撑"基准已饱和"论点 | verified（来源为从业者博客引述，属**二手**）；表格分项 TEDS 数值未取到一手 | llamaindex.ai 博客 2026-02-24 |
| 36 | 100% / 100% | 坐标轴范围与刻度间隔提取准确率 / at-risk 风险表提取准确率 —— KM-GPT，**540 张自生成合成 KM 图** | verified，但样本为合成图，非真实论文图 | PMC12458341 |
| 37 | median AE 0.005（95% CI 0.000–0.034）；median IAE 0.018（0.002–0.088） | 生存概率重建绝对误差 / KM-GPT，540 张合成图 / 全随访期积分绝对误差 | verified（合成图口径） | PMC12458341 |
| 38 | 99.6%（538/540） vs 33.0% 失败（178 张） | 处理成功率 / KM-GPT vs SurvdigitizeR，同 540 张合成图 | verified | PMC12458341 |
| 39 | 11.0 → 10.9（9.8–12.2）月 | 真实试验 mPFS 报告值 vs KM-GPT 重建值 / bevacizumab+paclitaxel / **真实验证仅 3 项试验、6 条曲线** | verified，样本极小 | PMC12458341 |
| 40 | 82.5% → 90.2% | 森林图数据抽取准确率：全自动 → 加人工编辑 / AutoForest，32 张森林图 / 18 篇 Cochrane 综述 / 56 项研究，专家组 4 人 | verified | arXiv:2606.02403v2 |
| 41 | 45.8% | 传为"手工专家数据抽取准确率" | **corrected**：真实口径是**限时实验室任务中 4 名专家用 RevMan 手工完成的准确率**，不是 Cochrane 双人独立抽取的准确率；作为"人类基线"引用属口径掉包 | arXiv:2606.02403v2 用户研究节 |
| 42 | 70.4 → 29.8 分钟（p<0.001） | 完成一张森林图的耗时 / 专家组，手工 RevMan vs AutoForest+编辑 | verified | arXiv:2606.02403v2 |
| 43 | 97.8% / 98.1% | 表格转换的**数值单元格准确率** / **表格检测率** / AutoForest 管线，206 张表 | verified | arXiv:2606.02403v2 |
| 44 | 47%–99.9% | LLM 数据抽取**总体准确率区间** / 27 项研究的跨研究范围（非单一模型成绩）/ 对照人类参考标准 | verified | J Biomed Inform 2026-07-25，DOI 10.1016/j.jbi.2026.105086 出版方摘要 |
| 45 | 74%–96% vs **47%–88%** | 分类/字符串变量 vs **数值变量**的抽取准确率区间 / 同上 27 项研究 / 类型间比较 | verified —— **本项目最关键的一条**：数值是最弱一类 | 同 #44 |
| 46 | 91.0%（95% CI 90.4–91.6） vs 89.0% | 抽取准确率 / Claude 3.5 Sonnet **辅助工作流** vs **纯人工** / 同一综述内的对照 | verified | 同 #44 |
| 47 | 60%–74% vs 0.08%–6% | 错误类型占比：**遗漏** vs **幻觉** / 27 项研究综合 | verified —— 反转防护重心的依据 | 同 #44 |
| 48 | 0.85 vs 0.80；26.9% | 数据抽取准确率（Expert+AI vs Expert-only）与相对时间节省 / **仅 2 名医学研究者**，各 360 个抽取任务，被试内设计 | verified，但 n=2，效应量不稳健 | PMC12460617 |
| 49 | 0.81 vs 0.78；20.8%；P<0.001 | 文献筛选 Recall 与时间节省 / LEADS 用户研究，Mann–Whitney U | verified | PMC12460617 |
| 50 | 0.78 vs 0.45 | 试验结果抽取准确率 / LEADS 独立 vs GPT-4o，人工评估 | verified | PMC12460617 |
| 51 | 3.22 vs 5.01（angle）；3.64 vs 10.09（area）；5.18 vs 8.63（volume） | **MLAE**（越低越好）：人类 vs 微调 Llama 3.2-Vision / Cleveland–McGill 基本感知任务，模型每任务 55 张测试图，人类 51 / 25 名被试 | verified | arXiv:2504.04221 |
| 52 | −2.48 vs 1.035（bar） | MLAE：微调模型**优于**人类 / 位置-角度任务，与训练集同源的合成图 | verified（数字），但属**分布内拟合**，不可外推真实论文图 | arXiv:2504.04221 |
| 53 | 3,596 点 / 168 序列 / 36 图 / 18 研究 / 2 名编码员 | WebPlotDigitizer 编码者间信度研究的样本规模 | verified | Drevon et al. 2017（经开放摘要页确认） |
| 54 | ICC / 相关系数具体值 | WebPlotDigitizer 编码者间信度的**具体数值** | **unverified** — SAGE 全文、PubMed、镜像站均被墙或仅返回定性描述"high levels of intercoder reliability" | 无，禁止给出裸数字 |
| 55 | 0.62 P / 0.71 R（混合 R 0.81）；SQL 执行率 95.2% | 证据行启发式对照 SQL 派生行 / GLEAN，简单查询子集 / 16GB GPU 预算下的小模型评测 | verified | arXiv:2603.02212 摘要 |

---

## 对本项目的设计含义

### D1. 裁决：图表派生数字的默认状态是 `unverified`，且需要引入第三档 `estimated`

现有二值（verified / unverified）在这个维度上不够用。理由：无标签图读数的误差是**有界但非零**的（Adaptive MAPE 3%–8%，#14；RMSF1 在 10% 容差下仅 51–88，#16–18），它既不是"已验证"，也不该和"完全没查过"同列。**建议三档：`verified` / `estimated(±ε, method)` / `unverified`。** `estimated` 必须强制携带误差量级 ε 与方法标签，且**在任何比较、排序、阈值判断中禁止参与**——只允许出现在描述性叙述里，并必须原样显示 ε。

### D2. 升级路径与准入条件（每条都锚定在实测数字上）

| 路径 | 触发条件（机器可判） | 允许的最终状态 | 数字依据 |
|---|---|---|---|
| **P0 绕开图表** | 同一数值在正文/表格/附录/作者数据仓库中存在 | `verified` | 表格路线近饱和（#33–35）；数值-类型抽取仍是最弱项（#45），故仍需 P1 的双读一致 |
| **P1 印刷标签直读** | 图上存在印刷数据标签，且 OCR 可读、单位与坐标轴一致性检查通过 | `verified` | 有标签 MAPE 1.3%–1.8%（#11） |
| **P2 无标签几何读数** | 无印刷标签，图族属 bar/line/scatter，非对数轴/非断轴/序列不重叠 | **上限 `estimated(±8%)`，永不 `verified`** | 无标签 MAPE 7.2%–7.4%（#12）；族内 Adaptive MAPE 2.6%–4.4%（#14） |
| **P3 领域专用管线** | 图族命中已注册的专用管线（KM 曲线、森林图），且管线的**可复核约束**全部通过 | `verified`（受 D4 约束） | KM-GPT 轴/风险表 100%、median AE 0.005（#36–37）；AutoForest 数值单元格 97.8%（#43） |
| **P4 人工判读** | 上述全部失败，或图族在 D3 黑名单内 | `verified`（人工签名），或维持 `unverified` | 人机协作上限 ~0.90–0.91（#40, #46, #48） |

**关键设计约束：P2 的产物不得被下游任何"关键 if 分支"消费。** 因为 θ=0.1 的容差意味着即使按 RMSF1 判"对"的单元格也可能有 10% 误差（#16 口径），一个 8% 误差的数字足以翻转"A 优于 B"这类比较结论。

### D3. 必须路由到人工或专用工具的图族黑名单（通用 VLM 一律禁用）

按 #14 的实测排序，以下族禁止走 P1/P2：
- **雷达图 / 极坐标图**（Adaptive MAPE 28.01%，是散点图的 10.6 倍）
- **饼图 / 环形图**（11.58%；与 #51 中"角度编码人类都比模型强"的心理物理学证据互相印证，属两条独立证据线）
- **堆叠柱状图**（ChartBench 2025 明确列为无标签复杂图的重灾区，#8；WB-ChartExtract 含堆叠柱后前沿模型跌到 51–61，#16–17）
- **稠密多线图 / 序列重叠**（同 #8）
- **对数轴、断轴、双 Y 轴**（#20 相关文献未覆盖 → 属未知区，按最坏处理）
- **面积图 / 体积编码 / 3D**（#51：area 与 volume 上人类 MLAE 优势最大）

工程落点：先跑一个**廉价的图族分类器 + 标签存在性检测器**作为路由前置，而不是先让 VLM 读数再事后判断。前置分类的成本远低于事后 16 次自洽采样（#20）。

### D4. 自洽性的正确用法：分诊，不是闸门

ρ=−0.34（#19）意味着离散度只解释约 12% 的正确性方差。因此：
- **禁止**："N 次采样一致 → 标记 verified"。
- **允许**："离散度进入最高分位 → 强制降级到 `unverified` 并入人工队列"。（低精度高召回的负向筛，正是弱相关信号唯一合理的用法。）
- **预算纪律**：默认采样次数上限设为 3–5，而不是 16（#20 的 16.11 次是为了榨取最后 1% 增益，对本项目的成本收益不成立）。集成的绝对增益也有限（最好情形 35.08→43.17，#21），不能指望它把 P2 抬进 P1。

### D5. 最高优先级机制：每个图表/表格派生数字必须携带"地址"，且地址要独立校验

这是 #29–31 直接推出的设计强制项。GPT-4o 结论对 88.4 / 依据对 34.8，且没有模型能让两者同时对超过 50%——**意味着"结论正确"这一信号对"依据正确"几乎没有预测力**。落地：
- 数据结构：每个数字带 `{value, unit, address}`，其中 address 对表格是 (论文 id, 表号, 行头, 列头)，对图表是 (图号, 系列名, x 值)。
- 校验：**用一个只看 address 不看结论的独立 agent 反向取值**——给定 address 去原文/原表重新取一次数，与 value 比对。这把"验证结论"换成了"验证寻址"，而 SciTab 的 grounding error 占 50%（#26）说明后者才是主要失效点。
- 这条同时解释了为什么 CoT 在 SciTab 上反而更差（#24）：推理链条延长的是结论侧，不是寻址侧。**本项目不应把"更长的推理"当作图表证据的质量杠杆。**

### D6. 守门重心从"反幻觉"转向"反漏项"

#47：遗漏占错误 60%–74%，幻觉仅 0.08%–6%。当前主流 agent 验证设计（含本项目 v1）几乎全部瞄准幻觉。落地调整：
- 增加一个**覆盖率闸门**：对每张进入证据集的图/表，先枚举其应有的数值槽位（系列数 × 数据点数，或行数 × 列数），再检查抽取结果的填充率。填充率不足即判失败，**早于**任何数值正确性检查。
- ExChart 的 97% 结构正确率（#13）恰好为这个闸门提供了可行性：结构（槽位骨架）是可靠的，可以拿它当作覆盖率的分母。**结构不能当正确性信号，但能当覆盖率的标尺** —— 这是把一个"不可用作验证"的高分指标转成有用工程量的方式。

### D7. 期望值管理：把 ~0.90 写进产品承诺，而不是 0.99

三条独立证据线（#40 AutoForest 90.2%、#46 综述 91.0%、#48 LEADS 0.85）都落在 0.85–0.91。**本项目对图表派生数字的准确率承诺上限应显式写为 ~90%，即每 10 个此类数字预期约 1 个仍错。** 这直接决定了产品形态：
- 图表派生数字必须**逐条可点开看原图与地址**，因为审阅成本无法归零；
- 不得生成"全部已验证"的整体性断言，只能生成逐数字状态；
- 时间收益是真实的（#42 手工 70.4 → 29.8 分钟；#49 时间节省 20.8%–26.9%；#44 综述 33%–87%），**产品价值主张应落在"同等准确率下的速度"和"可追溯性"，而不是"比人更准"**（比人更准的证据只有 +2 个百分点，#46）。

### D8. 评测自身的选择：不要用 TEDS 当内部质量门

TEDS 与人类判断 r=0.68（#33）。若本项目内部用 TEDS 做表格抽取的回归门，会同时（a）惩罚无害的格式差异、（b）放过真实语义错误。建议内部门使用**数值单元格级的精确比对 + 地址比对**（自建，确定性、可复跑），把 LLM-as-judge 只用于人工抽检环节。这也符合本项目"可重跑的客观闸门"这一根本原则——r=0.93 的 LLM judge 虽然更准，但它不是确定性的，不能当 gate。

---

## 未决与风险

**R1（方法缺口）搜索次数未达任务要求的 12 次。** 会话级 WebSearch 预算（200 次）在我发出第 10 次搜索后被兄弟 agent 共同耗尽。我以 22 次一手源直取（arXiv 摘要页/HTML 全文、ACL Anthology、PMC 全文、PDF 逐页直读、Semantic Scholar Graph API 取出版方原始摘要）作为补偿。**风险方向是覆盖面而非准确性**：进入核验表的数字准确性不受影响，但可能遗漏了整类系统（如商用文档 AI 的表格准确率官方口径、2026 年新出的图表专用 benchmark）。建议下一轮补搜：商用 Document AI 官方准确率口径、ChartX/EvoChart 谱系、以及 2026 H1 的图表 benchmark 新作。

**R2（无法核实，禁止使用）三个数字。** #4（CharXiv descriptive 人类 92.1%）、#9（GPT-5 堆叠柱 59.2%）、#54（WebPlotDigitizer 的 ICC 具体值）。前两个的阻断原因是 PDF 超限 / OpenReview 反爬 / ACM 403，第三个是 SAGE 付费墙。这三条已在文中显式标注，**任何下游文档若出现这些数字而无新的一手出处，即为回归**。

**R3（异常值，机制存疑）Gemini 2.5 Pro 在 WB-ChartExtract 上 87.83，而 GPT-5.1 只有 51.26（#16, #18）。** 同一基准上前沿模型相差 36 分，超出能力差异的合理范围。三种可能：(a) 输出格式契合度差异——RMSF1 依赖行列头的 Levenshtein 匹配（τ=0.5），表头命名风格不同会系统性压低分数；(b) 该基准源自世界银行公开数据，存在训练污染的可能（GLEAN #55 正是针对这类污染提出的协议）；(c) 前沿模型仅作 single-pass 参考点，可能未做提示词适配。**含义：不要把 87.83 当作"Gemini 能读复杂图"的证据，也不要把 51.26 当作"GPT-5.1 不能"。本项目选型不应基于这一组数字。** 需要用自建的、确定性的数值+地址比对重测。

**R4（口径污染源，已在本轮拦下两例，说明这类错误的基准发生率不低）**
- 例一：搜索引擎把 ChartBench(2023, arXiv) 与 ChartBench(2025, ACM VRISP) 合并，把 GPT-5 的结论挂到 2023 年论文上（#8/#9/#10）。
- 例二：AutoForest 的"45.8% 手工专家准确率"实为限时实验室任务成绩，极易被当作"人类抽取准确率"引用（#41）。
两例都发生在**同一批搜索结果的前 3 条**内。这从经验上支持任务前提中"约 1/3 载荷数字口径失真"的估计——**建议把"一手源直取 + 口径三元组"固化为本项目的写入期强制闸门，而不是事后审计项**。

**R5（时效）本文所有模型分数在 6 个月内必然过时。** 具体易失效项：#16–18（前沿模型 RMSF1，2026-05 数据）、#34–35（解析器排名，2026-02/06 数据）、#14（Gemini 2.5 Flash 分族 MAPE，2026-06 数据）。**结构性结论（有无标签的分水岭、结论-依据脱节、遗漏主导错误、族间差异序关系）比具体分数稳健得多，设计应锚定前者。** 建议为 #16–18 与 #34–35 设置到期日 2027-02，届时强制重测。

**R6（合成图 vs 真实图的外推风险）** #36–38 的 KM-GPT 100%/99.6% 全部来自自生成的 540 张合成图，真实验证仅 3 项试验 6 条曲线（#39）；#34 的解析器排名也来自 100 页合成 PDF。**合成基准上的接近满分不构成真实论文图上的能力证据。** 本项目若采纳 P3 领域管线路径，必须自建一个真实论文图的小规模金标集（建议 ≥50 张，来自目标学科的实际文献）再决定是否给 `verified`。

**R7（未覆盖的图族）** 对数轴、断轴、双 Y 轴、误差棒/置信带、箱线图、热力图、桑基图 —— 本轮搜到的所有基准均未单独报告这些族的误差。在拿到数据前，按 D3 一律列入黑名单（最坏假设）。这是一个明确的、可由后续调研关闭的缺口。

**R8（推论与源陈述的分界，供审阅者复核）** 本文中明确标注为"我的推论、非原文"的有三处：(a) §B1 关于 radar 难点是编码陌生而非分辨率的解释；(b) §H1 关于微调模型反超属分布内拟合的判断；(c) §结论摘要第 1 条"优先走表格/正文"这一路由优先级。其余所有带数字的陈述均为源陈述，出处见核验表。设计含义（D1–D8）全部为我的设计裁决，其锚定的数字已逐条标注。
