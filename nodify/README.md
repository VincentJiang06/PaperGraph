# Nodify

Deep research for LLMs, off the long-context treadmill: logic and evidence are
continuously distilled into a durable node tree; raw text is read once and
discarded. The context window holds only the frontier — the tree holds the truth.

- **V1**: the node tree done well — nodes (viewpoint/claim), synthesis records,
  `nd` CLI (9 commands, 4 frozen schemas), the `nd brief` compaction-proof
  briefing, and the nodify thinking skill. See `docs/00-design.md`.
- **V2**: the memoized docs store (archival, content-hash dedup, verbatim quote
  verification, tree-distance recall, source compression).

Origin: generalized from PaperGraph v2/v3 — the parts that survived contact with
reality (durable tree state, anti-hallucination floor, budgets) stay in code;
the parts that failed (behavior orchestration, worker form-filling) are returned
to the model. Failure catalog: `../v3/docs/01-anti-failure.md`.
