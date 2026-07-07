# Codex Instructions

Codex is primarily used for future implementation packages:

```text
schemas
validators
storage
queue
CLI
DB indexer
WebUI state/API
tests
integration wiring
```

Before implementation, read:

```text
docs/00-standards-index.md
docs/01-product-architecture-standard.md
docs/02-data-contract-standard.md
docs/03-workflow-queue-standard.md
docs/04-agent-handoff-standard.md
docs/05-tooling-webui-cli-db-standard.md
docs/06-implementation-work-packages-standard.md
docs/07-demo-acceptance-standard.md
interface-specs/00-interface-spec-index.md
```

Rules:

1. Treat this repository as spec-only until implementation starts.
2. Use `paperproof` as package and CLI name.
3. Split work by implementation package.
4. Write failing tests before non-trivial implementation.
5. Keep state transitions deterministic.
6. Do not change research outputs unless explicitly requested.
7. Do not invent ProofResult or EvidenceUnit content for real research claims.
8. Do not make hidden LLM/API calls for Proof.
9. Keep Committer as the only Logic Graph writer.
10. Ensure JSONL remains canonical and DB remains rebuildable.
11. Use `interface-specs/` for exact payloads, CLI grammar, API endpoints, queue events, and handoff bundles.
