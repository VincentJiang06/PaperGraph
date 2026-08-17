# Nodify

Deep research for LLMs, off the long-context treadmill: logic and evidence are
continuously distilled into a durable node tree; raw text is read once and
discarded. The context window holds only the frontier — the tree holds the truth.

- **V1** (`docs/00-design.md`): the node tree — nodes (viewpoint/claim),
  synthesis records, the `nd brief` compaction-proof briefing, event-log trace,
  and the nodify thinking skill (in-repo: `skill/SKILL.md`).
- **V2** (`docs/03-v2-design.md`): the memoized docs store — archival,
  content-hash dedup, verbatim quote verification (fabricated quotes never
  land), tree-distance recall, summary-based compression.
- **V3** (`docs/04-v3-design.md`): the article layer — grounded outlines with
  recorded exclusions, `(cite: DOC-xxxx)` hard resolution, mechanical
  references. 18 CLI command groups, 10 frozen schemas in 3 named sets,
  `nd upgrade` between sets.

Origin: generalized from PaperGraph v2/v3 — the parts that survived contact with
reality (durable tree state, anti-hallucination floor, budgets) stay in code;
the parts that failed (behavior orchestration, worker form-filling) are returned
to the model. Failure catalog: `../v3/docs/01-anti-failure.md`.
