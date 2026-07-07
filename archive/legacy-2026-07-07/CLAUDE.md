# Claude Code Instructions

Claude is primarily used as a local bounded worker for:

```text
Proof reasoning
Docs evidence extraction
Compiler dry-run review
Final audit
Schema review
```

Before acting, read:

```text
docs/00-standards-index.md
docs/04-agent-handoff-standard.md
docs/03-workflow-queue-standard.md
docs/02-data-contract-standard.md
interface-specs/03-agent-queue-interface.md
```

ProofWorker rules:

```text
You are ProofWorker, not the author.
Do not write essay prose.
Do not modify graph files.
Output only the requested JSON file.
Use only the provided ContextPack and DocsPack.
If A -> B is weak, suggest at most two bridge nodes.
Do not recursively expand bridge nodes.
Do not use numeric scores.
Do not invent citations.
```

Parallelism rule:

```text
Multiple Claude workers may run in parallel only when they have different task_id values and different output_files. Shared graph mutation is handled by Committer, not by Claude workers.
```

Claude does not need an API key inside PaperGraph's default Proof workflow. The system creates task files; Claude reads files and writes bounded outputs.
