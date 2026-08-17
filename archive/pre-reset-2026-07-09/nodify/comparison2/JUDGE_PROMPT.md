# Blind review — score short economic-analysis articles

You are an expert peer reviewer for short academic articles in economics. For each
**topic** below there are **three anonymized articles (A, B, C)** by different
authors answering the **same question**. Score each article on its own merits.

## The five topics (each has a folder `blinded/T<k>/` with Article-A/B/C.md)

- **T1**: AI agents 2020-2025 对就业的净效应(任务替代 vs 岗位净增减;"真实近中性 vs 效应尚未显现"的因果识别难题)。
- **T2**: 2021-2023 美国通胀的需求侧 vs 供给侧归因分解,及对"软着陆"可持续性的含义。
- **T3**: 量化宽松(2008-2021)在多大程度上是发达经济体财富不平等扩大的"原因"而非结构性力量反事实下的结果(因果识别)。
- **T4**: 中国人口下降是否必然导致日本式长期停滞;自动化/生产率/制度改革能否抵消。
- **T5**: 最低工资上调是否降低就业;调和 Card-Krueger 准实验与竞争性市场理论(2015-2024 美国州级自然实验)。

## Rubric — integer 1–5 on each dimension (5 = best)
- **structure_logic** — clear thesis; layered, non-circular reasoning; sub-questions genuinely independent (not restatements of the conclusion).
- **evidence_quality** — specific, credible, well-attributed evidence; quantified claims tied to identifiable sources; primary over secondary where it matters.
- **adversarial_rigor** — genuine engagement with the *strongest* counterargument / rival explanation; steelmanned, not strawmanned; the identification/attribution difficulty is actually confronted.
- **calibration** — honest about uncertainty, data limits, and what the evidence does *not* establish; avoids overclaiming.
- **overall** — holistic quality as a rigorous analysis of a hard, contested question.

## Rules
- **Do NOT reward length.** A tighter article that reasons better beats a longer one.
- **Do NOT try to infer how each article was produced** or who wrote it. Judge the text.
- Score each article independently; ties are allowed. Within a topic, A/B/C order is arbitrary.
- Add a 1–2 sentence `rationale` per article naming the single biggest strength and weakness.

## Output — write STRICT JSON to the path given in your dispatch message
```json
{
  "T1": {
    "A": {"structure_logic":4,"evidence_quality":3,"adversarial_rigor":4,"calibration":5,"overall":4,"rationale":"…"},
    "B": {...}, "C": {...}
  },
  "T2": {...}, "T3": {...}, "T4": {...}, "T5": {...}
}
```
Read all 15 files under `blinded/T1..T5/Article-A|B|C.md`, score every one, write the
JSON file, and stop. Your final message = one line confirming the file was written.
