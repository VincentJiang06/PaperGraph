# 快照出处与版权

本目录的快照供 `cases.mjs` 做**逐字包含**判定之用。

## 完整正文（开放获取）

- `T1a-nature-alphafold.txt` —— Jumper, J. et al. *Highly accurate protein structure
  prediction with AlphaFold.* **Nature** 596, 583–589 (2021).
  doi:[10.1038/s41586-021-03819-2](https://doi.org/10.1038/s41586-021-03819-2)
  **License: CC BY 4.0** —— 可带署名转发，故保留全文抽取结果。

  **保留全文是有必要的,不是省事**:用例 T1-1 的全部证据力就在于
  「`92.4` 在这篇论文的**整篇正文**里 0 次命中」。截成几句,这条证据就没了。

  ```
  grep -c '92.4' snapshots/T1a-nature-alphafold.txt   # → 0
  ```

- `T6-alphafold-full-jats.xml` —— **同一篇论文的 PMC 完整 JATS 全文**（PMC8371605）。
  **License: CC BY**，2026-08-19 经 PMC OA 接口核实：

  ```
  curl -s "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC8371605"
  #  <record id="PMC8371605" ... license="CC BY" retracted="no">
  ```

  **为什么要与 T1a 并存而不是替换它**：两者是同一篇论文的**两条取证路径**。
  T1a 是纯文本抽取（G4，无结构化定位符）；T6 带 `<sec id>`/`<p id>`，
  可做回指往返验证（G5）。外部标定的 T5-1 与 T1-3 引的是**同一句话**，
  状态却分别是〔已验证〕与〔已归因〕——差别只在取证方式。
  删掉任何一份，ST-V 与 ST-A 的这条对照就没了。

  它同时是段落选择门（`gates/check_passage_select.mjs`）与成本模型
  （`tests/external/cost-model.mjs`）的**共用夹具**：50 个可寻址段、
  渲染后 42,572 字符 = 10.6K token。§S21 那次订正就是拿它量出来的。

## 只保留被引用的句子（非开放获取）

下列五份**不是**开放获取。本仓库只保留测试真正引用到的那一到三句
（引用权范围内，逐字、带完整出处），不转发完整摘要。

| 文件 | 出处 | 保留 |
|---|---|---|
| `T1b-proteins-casp14.txt` | Jumper, J. et al. **Proteins** 89(12):1711–1721 (2021). doi:10.1002/prot.26257 | 1 句 |
| `T2-osc2015.txt` | Open Science Collaboration. **Science** 349:aac4716 (2015). doi:10.1126/science.aac4716 | 3 句 |
| `T3a-dimasi2016.txt` | DiMasi, J.A. et al. **J Health Econ** 47:20–33 (2016). doi:10.1016/j.jhealeco.2016.01.012 | 2 句 |
| `T3b-prasad2017.txt` | Prasad, V. & Mailankody, S. **JAMA Intern Med** 177(11):1569–1575 (2017). doi:10.1001/jamainternmed.2017.3601 | 3 句 |
| `T3c-wouters2020.txt` | Wouters, O.J. et al. **JAMA** 323(9):844–853 (2020). doi:10.1001/jama.2020.1166 | 2 句 |

## 中文语料（T4）

同样只保留被引用的句子。三份都是 Europe PMC 上 `LANG:"chi"` 的中文摘要。

| 文件 | 出处 | 为什么选它 |
|---|---|---|
| `T4a-cn-nematode.txt` | PMID 386886《生防制剂与呋喃丹颗粒剂防治根结线虫幼虫的效果》 | **全角数字**（`73．55％` 用的是全角句点 U+FF0E 与全角百分号 U+FF05）+ 两个并列读数 + 中文空结果「无显著差异」 |
| `T4b-cn-rice.txt` | PMID 382278《水稻叶片上下表面反射率差异及其与氮素状况的关系》 | 上界限定「小于2%」+ 中文空结果「无显著相关性」 |
| `T4c-cn-juncus.txt` | PMID 391824《种植密度、母本大小和移栽期对蔺草生长、开花及产量的影响》 | 中文子句边界：`但` 前后一正一负 |

这三份是本项目**第一次**在真实中文文献上跑整条链路。
系统里的 CJK 归一化、中文否定表、中文数字处理此前只在作者自己造的句子上验过。

## 这对测试意味着什么

裁剪改变了一件事,必须写明:**T2 与 T3 的 claim 现在是在一段
「只含相关句子」的快照上判定的**,而不是在完整摘要上。这让
G-GRADE 的 `content_kind: 'abstract'`（→ G3）成为一个**善意的高估**——
真实的完整摘要能支撑的东西不会比这更少,但这份裁剪快照本身够不上「摘要」。

唯一因此变弱的判定是「引语不在快照里 → G1」那一档:裁剪后,不相关的句子
本来就不在快照里了。该档的正例仍由 `check_cas.mjs` 的合成夹具守着。
