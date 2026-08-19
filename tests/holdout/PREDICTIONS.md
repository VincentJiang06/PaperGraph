# 留出集 · 事前预测（写于运行之前）

〔本文件存在的理由〕§S19 四指出：本项目的 21/21 有相当一部分是
**「修到符合标签为止」**的结果——T2-1/T2-2/T2-4/T3-3/T3-4 都是先判错、
再改代码改到判对的。那样得到的数字是软的：它同时包含「设计对了」和「拟合了这批题」。

要把它变硬只有一个办法：**一批没参与过修复的用例，先写期望再跑，跑出什么报什么。**

因此本文件在**任何一次运行之前**写完，逐条记下：
① 我认为正确的判定（专家标签）；② 我预测系统会给出什么；③ 两者不一致时我预测的原因。

**②与①不一致的地方，就是我事前认为系统会错的地方。** 跑完之后不许修改本文件。

八条 claim 全部取自 meta 分析摘要 —— 本项目此前四个话题都没有的文体。

| 编号 | 载荷 | 应判 | **预测** | 理由 |
|---|---|---|---|---|
| H-1 | 56.8%，discriminator `neuropathy` | attributed | attributed | 三个并列合并患病率 → G-FRAME 触发；判据说清了 → 放行。摘要 G3 → 天花板 ST-A |
| H-2 | 56.8%，**无** discriminator | unverified | unverified | 同上但没说是哪一个 → 降 K-L-A，1 簇不足 |
| H-3 | OR = 2.19（阳性发现） | attributed | attributed | 「statistically significant higher」是肯定发现，不得被否定表误伤 |
| H-4 | MD = -1.09 min（**空结果**） | unverified | unverified | 「no statistically significant difference」在 NEG-N 表内，MD 落在该子句 |
| H-5 | RR = 1.13（`nonsignificant`） | unverified | **attributed ✗** | **预测会漏**：`nonsignificant` 一词不在任何算子表里（表里只有 `not statistically significant`）。这是 SA-3 那条有限枚举的又一次兑现 |
| H-6 | OR = 4.12，discriminator `heart failure` | attributed | attributed | 三个并列 OR → G-FRAME 触发；判据说清了 |
| H-7 | RR = 0.77（`significantly lower`） | attributed | attributed | 「lower」是方向词不是否定词，不得误伤。这条测的是假阳侧 |
| H-8 | MD = -70.18 U/L，**I² = 98%** | attributed | attributed | 系统会放行。**但这是一个已知盲点**：I²=98% 意味着这个合并估计几乎没有意义，而本系统对异质性一无所知 |

## 两条事前就知道的缺口

**H-5 · 词表有限枚举。** `nonsignificant` / `non-significant` / `did not reach significance`
是同一个意思的不同写法，表里只有其中一种。这不是新发现，是 SA-3 认账过的那条，
但这次是**在事前预测里点名**，而不是事后解释。

**H-8 · 异质性不可见。** I² = 98% 表示各研究之间的差异几乎全部不是抽样误差，
合并估计在统计上很难说代表什么。本系统的六值状态里没有任何一档表达这件事，
G-GRADE 也不看它。一条 I²=98% 的合并估计与一条 I²=4% 的，在本系统眼里完全一样。
**这是一个真实的、此前从未记过账的缺口**，由这批新文体逼出来。

## 一条我不确定的

**H-3 与 H-7 的假阳风险。** 两句都含 `significant` / `lower` 这类词，
而 NEG-N 里有 `not statistically significant`。若匹配是子串式的，
`statistically significant higher` 可能被 `not statistically significant` 的
某个片段误命中。我预测不会（算子表是整词匹配），但没有把握。
