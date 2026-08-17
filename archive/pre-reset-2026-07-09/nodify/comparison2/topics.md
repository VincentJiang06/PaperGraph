# Ablation v2 — Sonnet 5, five hard economic-analysis topics

Model under test: **Sonnet 5** (weaker than the v1 Opus run — tests whether the
tree helps MORE with a weaker model). 5 contested topics that need deep, long,
multi-step causal reasoning + adversarial engagement (not lookup-able). Each run
in isolation; only the framework varies (raw / skills / tree).

T1  AI agents 2020-2025 对就业的净效应是什么?区分任务替代与岗位净增减,并直面
    "真实近中性 vs 效应尚未显现"的因果识别难题。
    [identical to the v1 Opus topic → isolates the model-strength variable]

T2  2021-2023 年美国通胀的成因分解:需求侧(财政+货币刺激)与供给侧(供应链、
    劳动力、能源)各自贡献多少?这对"软着陆"能否持续意味着什么?

T3  量化宽松(2008-2021)在多大程度上是发达经济体财富不平等扩大的"原因",
    而非人口、技术、全球化等结构性力量在反事实下也会造成的结果?

T4  中国的人口下降是否必然导致日本式长期停滞?自动化、生产率增长与制度改革
    能在多大程度上抵消劳动力萎缩?

T5  最低工资上调是否降低就业?如何调和 Card-Krueger 式准实验证据与竞争性劳动力
    市场理论——以 2015-2024 美国州级"自然实验"为例。

## Shared deliverable spec (identical across all arms)
- ~1500-1800 word Chinese academic article, real web research.
- Inline citations; save every cited source's fetched text for verification.
- The ONLY variable is the framework (raw / skills / tree). Model = Sonnet 5.
