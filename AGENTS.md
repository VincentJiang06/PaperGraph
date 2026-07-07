# Agent Protocol

`docs/` (00 → 12) is the single source of truth. Boundary questions: `docs/08-module-contracts.md` wins. Checks: the V-* registry in `docs/09-verification.md`. V1 scope: `docs/10-v1-design.md`. Test structure: `docs/11-test-suite.md`. WebUI design: `docs/12-webui-spec.md`. `docs/13`–`18` are the search program: design-frozen and adoption-staged — implement them ONLY when a docs/00 changelog entry adopts the set. `archive/` is superseded legacy material; `product/` is product/GTM planning — neither is build spec. Never treat them as authoritative for implementation.

Roles are defined in `docs/07-runtime-and-tooling.md`:

```text
Orchestrator   main session; scoping, layer expansion, dispatch, gates via CLI
ProofWorker    one bounded proof task -> one ProofResult file
DocsWorker     one DocsRequest -> Documents + EvidenceUnits
CompileWorker  DraftMap -> prose (the only prose producer)
Implementation agents  build src/paperproof/ following docs/10-v1-design.md
```

Rules for every agent:

1. Read the doc for your stage before acting; read only your task's declared inputs.
2. Write only your declared output paths; workers never write graph/, commit/, freeze/, compiler/.
3. Chat text is not state — only validated output files are.
4. Never bypass the Validator or Committer; never edit frozen structures.
5. Never invent citations; every citation resolves to an archived Document.
6. Discrete enums for academic judgment; never numeric scores.
7. JSONL is append-only; never rewrite history.
8. Parallel work requires disjoint task_ids and output files.
9. Implementation work: follow milestone order in docs/10 §7 with the test gates in docs/11 §9; tests before non-trivial code; schemas live only in src/paperproof/schemas/; text measurement only via textutil (docs/09 §0); a change that deviates from docs/ must update the doc in the same change.
