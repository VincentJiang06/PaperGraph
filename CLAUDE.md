# Claude Code Instructions

PaperGraph runs under Claude Code. The main session is the **Orchestrator**; bounded subagents act as **ProofWorker**, **DocsWorker**, or **CompileWorker**.

Before acting, read `docs/00-overview.md`; then the doc for the stage you are working on (`docs/01`–`07`). On any boundary question, `docs/08-module-contracts.md` is authoritative; checks are the V-* rules in `docs/09-verification.md`; v1 scope is `docs/10-v1-design.md`; test structure is `docs/11-test-suite.md`. `docs/` is the only source of truth. `archive/` is superseded — never follow it.

## Orchestrator rules

```text
Drive all state changes through the paperproof CLI; never hand-edit JSONL.
Get explicit user acceptance of the ProjectContract before expanding the graph.
Dispatch parallel workers only with distinct task_ids and distinct output files.
Judgment belongs to workers; bookkeeping (validate/commit/freeze/compile) belongs to code.
```

## Worker rules (ProofWorker / DocsWorker)

```text
Read only the task's input files (ProofTask, ContextPack, DocsPack; DocsWorkers additionally read docs/raw/** — that search IS their task).
Write only the task's declared output file (always under agent_outputs/). Never touch graph/, commit/, freeze/, compiler/, docs/*.jsonl, queue/.
Never choose a verdict — walk the evaluation ladder and fill the check form (closed enums, docs/03); code computes the verdict.
Cite only from the provided DocsPack; missing evidence => evidence_check=insufficient + DocsRequest.
Never invent citations. No numeric scores.
Inference gap => at most two bridge proposals; never expand bridges recursively.
No essay prose anywhere except CompileWorker output; notes ≤ 150 words.
Write the output file and stop.
```

## Non-negotiables (all roles)

```text
JSONL is canonical and append-only; DB is derived.
Committer is the only Logic Graph mutator.
No prose before the Compiler stage.
Any deviation from docs/ requires updating the doc in the same change.
```
