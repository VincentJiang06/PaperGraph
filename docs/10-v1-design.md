# 10 Version 1 Design

The concrete first version: exact scope, technology, repo layout, CLI surface, worker prompts, build order, and the demo that proves it. Docs 01–09 say what the system is; this doc says what gets built first and in what order. (This absorbs and replaces the earlier roadmap.)

## 1. V1 Scope

V1 is a single-machine, single-project-at-a-time system driven from one Claude Code session.

In:

```text
full pipeline for ONE paper pattern: single_event_mechanism
topic input file → scoping → contract acceptance
BFS expansion (single lane BFS-MAIN + one BFS-ALT lane)
NODE_CHECK / EDGE_CHECK proof tasks (BINDING_CHECK deferred to v1.1)
docs ingest of user-provided files + web search by DocsWorkers
memoized evidence search (keyword/scope match; no embeddings)
commit / freeze / compiler dry-run / draft map / prose / mechanical audit
queue with leases, retries, dead letters
CLI (JSON output) + read-mostly WebUI
paperproof verify + paperproof trace
```

Out (deferred, with the doc that specs them for later):

```text
BINDING_CHECK tasks                    docs/03   → v1.1
semantic AuditWorker pass              docs/06   → v1.1 (v1 audit is mechanical)
contract re-versioning automation      docs/08   → v1.1 (v1: no CLI trigger;
                                       the contract_reopen commit kind is
                                       exercised via the committer API in tests)
multi-case merge lanes + comparison node type / contrasts_with edges   docs/02 → v2
other paper patterns                   docs/01   → v2
grill-me topic interviewer             docs/01   → v2
embedding/semantic evidence search     docs/04   → v2
multi-project concurrency, remote workers, Neo4j/GraphRAG, agent debate: not planned
```

## 2. Technology Choices

```text
Language        Python 3.12+; POSIX only (darwin/linux — fcntl locking)
Models          pydantic v2 (strict mode; extra="forbid" everywhere)
Storage         JSONL + JSON files (docs/07 layout); no database as source of truth
Derived index   DuckDB, rebuilt by `paperproof db rebuild`
CLI             typer; every command prints one JSON envelope to stdout
WebUI           FastAPI + one static page (htmx or vanilla JS + a VENDORED
                cytoscape.js, committed under ui/static/vendor/). No build step,
                no npm. Served by `paperproof ui serve`.
Concurrency     queue leases + snapshot checks (docs/08 §3); fcntl lock around
                each JSONL append; queue/.lock and commit/.lock for the engines
Determinism     injectable clock/actor via PAPERPROOF_NOW / PAPERPROOF_ACTOR;
                canonical serialization (docs/07); id allocation by max+1 scan
Tests           pytest; the full plan is docs/11-test-suite.md
Workers         Claude Code subagents dispatched by the Orchestrator (docs/07);
                FakeWorkers for all automated tests
```

```toml
# pyproject.toml skeleton (dependency floor, not a lockfile)
[project]
name = "paperproof"
requires-python = ">=3.12"
dependencies = [
  "pydantic>=2.7", "typer>=0.12", "fastapi>=0.111",
  "uvicorn>=0.30", "duckdb>=1.0", "pypdf>=4.2",
]
[project.optional-dependencies]
dev = ["pytest>=8", "httpx>=0.27"]
[project.scripts]
paperproof = "paperproof.cli.app:main"
```

Rationale worth recording: no async runtime (parallelism lives in the workers, not the code — code paths are short and serial); no web framework state (the DB is the only read model, rebuilt from JSONL); no git dependency at runtime (snapshots via hashes, not commits).

## 3. Source Layout

```text
src/paperproof/
  schemas/          every *.v1 model, one file per family; THE only schema location
    __init__.py     registry: schema_version string → model class
    spec.py graph.py proof.py docs.py queue.py commit.py freeze.py compiler.py audit.py
  textutil.py       the §0 algorithms (docs/09) — the only tokenizer/counter
  ids.py            id formats + max+1 allocation        clock.py  PAPERPROOF_NOW
  store/
    jsonl.py        append / read / latest_by_id / fcntl locking / path safety
    snapshot.py     take + verify snapshots (graph files, docs/07)
  scoping/          topic parser (P1–P7) → PaperSpec + ProjectContract
  graph/            read models, spine walker, MSA checklist, trace walker
  expander/         proposal ingestion (validation of expansion_proposal.v1)
  prooftask/        bundle builder (ProofTask + ContextPack + DocsPack, -rN revisions)
  validate/
    registry.py     V-* rule registry: rule_id → callable; envelope for failed_rules
    rules/          one module per prefix (v_spec.py v_pr.py v_dr.py ...)
  committer/        decision table, verdict→action + administrative commits,
                    serial apply, CommitDecision, cascade, staleness marking
  docsdb/           ingest, dedup, evidence store, matcher, fingerprint cache,
                    pack builder
  queue/            work items, leases, events, transitions, unblock/expire sweeps
  freeze/           preconditions + FreezeItem + batch-commit request
  compiler/         dry run, gaps, section plan template, draft map, prose ingest
  audit/            mechanical binding/strength/scope/coverage checks
  prompts/          worker prompt templates (§5) — the ONLY dispatch prompts
  cli/              typer app, one module per command group
  ui/               FastAPI app + static/ (incl. vendored cytoscape)
tests/              per docs/11 (layout, fixtures, fakes)
examples/
  topic-input-p4.md
```

## 4. CLI Envelope and Command Contracts

Every command prints exactly one JSON object:

```json
{ "ok": true, "command": "queue claim", "data": {}, "errors": [], "warnings": [] }
```

```text
exit 0  ok
exit 1  validation/domain failure (errors[] carries V-* ids)   — expected, handleable
exit 2  usage error
exit 3  corrupted state (verify failure, bad JSONL line)        — stop and tell human
```

The one-envelope rule covers the closed command surface below. The framework's
`--help`/`-h` eager flag is exempt: it prints standard help text and exits 0, and
is not one of the listed commands.

Global options: `--root <dir>` (default `./data`), `--project <id>` / `PAPERPROOF_PROJECT`. The command list below is **closed for v1**: a workflow need that no command covers means this doc gets amended first. `data` payloads list their essential keys; envelopes may add informational keys but never remove these.

| command | args | effect / data |
| --- | --- | --- |
| `project init <id>` | — | create the docs/07 tree + GS-000001; data: {project_id, root} |
| `project status` | — | data: contract state, per-queue counts, MSA summary, dead letters, current snapshot id (what the Expander cites as based_on_snapshot) |
| `spec build <topic-file>` | `[--patch <json>]` | parse (P1–P7) → write spec+contract drafts; refuses if accepted; data: both docs |
| `spec accept` | — | set accepted_by_user (human step); data: contract |
| `spec show` | — | data: spec + contract |
| `graph list-nodes / list-edges` | `[--state --lane --layer]` | data: current records (latest per id) |
| `graph show <id>` | — | data: record + history + verdict records |
| `graph msa-check` | — | data: MSA-1..9 each {pass, detail}; exit 1 unless all pass |
| `graph park <id>` | `--reason absorbed\|not_needed [--into <id>]` | administrative commit; data: commit_id |
| `graph unpark <id>` | — | administrative commit; data: commit_id |
| `expand ingest <file>` | — | validate V-EXP + commit; data: {commit_id, assigned_ids, work_item_ids} |
| `proof build-tasks` | `--frontier` | build/rebuild bundles for every claimable or stale proof item, minting the next -rN revision per target; `--frontier` is the required (and only) mode in v1; data: bundles built |
| `proof build-task <target-id>` | — | one bundle; data: bundle paths |
| `docs ingest <file>` | `[--source-type --title --citation-key]` | archive user file (dedup by hash); data: doc_id, text_path |
| `docs search` | `--query <text> [--scope <json>]` | run the matcher; data: scored EU list |
| `docs build-pack` | `--task <task-id>` | assemble DocsPack; data: pack path, EU count |
| `docs request` | `--target <id> --need <text> [--hint <h>]...` | Orchestrator-initiated DocsRequest (code appends; cache-checked like any request); data: request_id, status |
| `docs ingest-result <file>` | `--work-item <WI>` | validate V-DR + ingest + unblock; data: assigned ids, request status |
| `queue list` | `[--queue --status]` | data: items (commit_queue = derived view of validated) |
| `queue claim` | `--queue <q> --agent <name> [--id <WI>]` | lease + claim-time manifest; without --id, picks the claimable item with the lowest work_item_id (FIFO); data: work item incl. bundle + output paths |
| `queue heartbeat <WI>` | `--agent` | extend lease |
| `queue release <WI>` | — | back to queued, attempt unchanged |
| `queue complete <WI>` | — | claimed/running → validating (output file must exist) |
| `queue fail <WI>` | `--reason` | manual fail (op=fail, from claimed/running/validating — for hung or hopeless workers); auto retry/dead per attempt |
| `queue expire` | — | sweep expired leases; data: requeued/dead ids |
| `queue requeue <WI>` | — | dead → queued (human decision) |
| `queue events` | `[--after <QE>]` | data: events |
| `validate result <file>` | `--work-item <WI>` | V-PATH+V-PR, compute verdict, append verdict record, item → validated/failed; data: {proof_result_id, computed_verdict} or {failed_rules} (exit 1) |
| `validate proposal <file>` | — | V-EXP static checks; data: ok / failed_rules |
| `validate docs-result <file>` | `--work-item <WI>` | V-PATH+V-DR; data: ok / failed_rules |
| `commit apply` | `--result <PR-id>` | serial commit of a validated verdict (B6); data: {commit_id, actions, post_snapshot}. Proposals commit via `expand ingest` — one path each, never two |
| `freeze apply` | `--target <id> --level local\|subtree\|spine` | preconditions + FreezeItem + batch commit; data: {freeze_id, commit_id} |
| `freeze unfreeze` | `--target <id>` | human-only; revoke + re-open; data: {freeze_id, commit_id} |
| `compiler dry-run` | — | data: full CompilerDryRun (+ gap items enqueued/cancelled) |
| `compiler draft-map` | — | requires writing_ready; enqueues one compile_queue prose item per section (task_id PROSE-<section_id>, output agent_outputs/prose/<section_id>.md); data: DraftMap |
| `compiler ingest-prose <file>` | `--work-item <WI>` | V-PROSE as the item's validate-pass + copy to compiler/prose/ + commit (two queue events, one command); data: section_id / failed_rules |
| `audit run` | `--draft <DRAFTMAP-id>` | mechanical audit; data: AuditReport; exit 1 if findings |
| `db rebuild / db check` | — | data: manifest / {stale_index: bool} |
| `ui serve` | `--port 8420` | serve the docs/07 API + static page |
| `verify` | — | whole-project sweep (docs/09 §3); exit 0 clean, 3 on violation |
| `trace` | `--node <id>` | data: the full trace chain (docs/09 §3) |

## 5. Worker Prompt Templates

Templates live at `src/paperproof/prompts/` and are the **only** prompts used to dispatch workers, so behavior is reproducible. `{placeholders}` are filled from the work item/bundle; `{target_summary}` = task_type + target id + the claim/edge_claim text truncated to 200 characters. The texts below are canonical — the template files carry them verbatim.

### ProofWorker (`proof_worker.txt`)

```text
You are a PaperGraph ProofWorker. You resolve exactly ONE proof task and write
exactly ONE file.

Read only these files, nothing else in the project:
  TASK: {task_file}    CONTEXT: {context_pack}    DOCS: {docs_pack}
Your question: {task_type} on {target_summary}.

You do NOT choose a verdict. You fill the check form; code computes the verdict.
Walk the evaluation ladder in order; where it stops, every later form field is
"not_evaluated" and its attachments stay empty/null:

A. scope_check (in_scope | out_of_scope) against contract_scope and
   forbidden_claims; duplicate_check against claim_digest/neighbors
   (duplicate = same proposition, not merely related; duplicate_of must be an
   id from the ContextPack). If out_of_scope or duplicate: STOP the ladder.
B. wellformed_check (single_proposition | too_broad | compound) on the target's
   own text. If too_broad/compound: attach exactly ONE repair
   {"kind":"narrow","narrowed_claim":"…"} (1-2 sentences, one proposition); STOP.
C. evidence_check (not_required | sufficient | insufficient | contradicting).
   fact/mechanism nodes may NOT answer not_required. Cite only EvidenceUnit ids
   from the DocsPack in evidence_used; sufficient/contradicting require ≥1.
   insufficient: attach ≥1 docs_requests [{need, search_hints[]}]; STOP.
   contradicting: STOP.
D. (edges only) inference_check (holds | holds_only_with_assumptions | gap | fails).
   gap: attach 1-2 repairs {"kind":"bridge","claim":"…","node_type":
   "fact|mechanism|definition|alternative"} — never more, never recursive.
   holds_only_with_assumptions: assumptions must be non-empty; holds: empty.

If your answers reach a pass (single_proposition; evidence not_required or
sufficient; edges: inference holds or holds_only_with_assumptions): fill
language_limits with ≥1 "allowed" sentence (the strongest wording the evidence
carries) and ≥1 "forbidden" sentence (the overclaim to avoid). Otherwise
language_limits must be null.

Hard rules: no verdict field, no id fields, no numeric values anywhere;
notes ≤ 150 words; NODE forms have no inference_check field at all; never
modify any file except the output; never cite outside the DocsPack — missing
evidence means insufficient + docs_requests; never invent citations.

Write proof_result.v1 JSON to {output_file}. Allowed writes: {output_file},
agent_notes/**. Then stop. Your chat text is discarded.
```

### DocsWorker (`docs_worker.txt`)

```text
You are a PaperGraph DocsWorker. You serve exactly ONE DocsRequest and write
exactly ONE file.

REQUEST: {request_id}
Need: {need}    Hints: {search_hints}
Search docs/raw/ (user-provided sources — reading it is part of your task
inputs) first, then the web if available.

For each useful source add a documents[] entry: {title, source_type ∈
peer_reviewed|official_report|working_paper|news|dataset|user_notes,
origin {kind: user_provided|web, path or url}, citation_key, and for web
sources the full extracted text INLINE as "text"}.
Extract evidence_units[]: {doc_ref: <index into your documents> OR doc_id:
<existing archived id>, location, kind: quote|paraphrase, quote_or_paraphrase,
summary, support_direction ∈ supports|refutes|context, can_cite_for (≥1),
cannot_cite_for (≥1), scope {period?, region?}}.

Quotes must be verbatim from the source. Never invent sources or quotes. Never
judge graph claims — no verdict/strength/lifecycle language. You assign NO ids.
If nothing usable exists: not_found=true, empty lists, and record search_log
(the queries you actually ran) — an honest not_found beats a stretched source.

Write docs_result.v1 JSON to {output_file}. Allowed writes: {output_file},
agent_notes/**. Then stop. Your chat text is discarded.
```

### CompileWorker (`compile_worker.txt`)

```text
You are a PaperGraph CompileWorker. You write prose for exactly ONE section
from a DraftMap and write exactly ONE file.

DRAFT MAP: {draft_map_file}   Your section: {section_id}

Rules:
- Every claim-bearing sentence carries "(claim: NODE-xxx)" inside the sentence.
- Every citation "(cite: EU-xxx)" sits in the same sentence as the claim it
  backs, and only for an EvidenceUnit bound to that node in the DraftMap.
- Use only node_ids/evidence_ids present in the DraftMap; every claim of your
  section appears at least once; transitions need no annotations.
- Stay inside allowed_language; never produce any forbidden_language string;
  no new claims, no strengthening.

Write Markdown to {output_file} (agent_outputs/prose/{section_id}.md). Allowed
writes: {output_file}, agent_notes/**. Then stop. Your chat text is discarded.
```

### Retry suffix (`retry_suffix.txt`, appended on validation failure)

```text
RETRY {attempt}/3 — your previous output failed validation:
{failed_rules_with_detail}
Fix exactly these violations and rewrite the COMPLETE output file at the same
path. Do not change anything else.
```

## 6. WebUI V1

Five views over the DuckDB index, HTTP surface pinned in docs/07, full design spec in docs/12 (stale banner via `db check` on load):

```text
Overview   MSA checklist, per-queue counts, dead letters, contract status
Logic Map  cytoscape graph; color=lifecycle_state, border=frozen, edge
           style=strength; click → detail drawer: raw JSON + proof history
           (form + computed verdict) + trace chain
Queue      table per queue: id, target, status, owner, attempt, blocked_by
Evidence   Documents ↔ EvidenceUnits with can/cannot_cite_for
Compiler   latest dry run: section plan, gaps, writing_ready; draft text when present
```

Write actions in v1 UI: queue claim/release and db rebuild only. Everything else is CLI.

## 7. Build Order

Five milestones; each ends with `paperproof verify` clean **plus its gate row in docs/11 §9** (the authoritative per-milestone test list + live smoke). Sequential — no milestone starts before the previous one's acceptance passes. Within a milestone, modules with disjoint file ownership may be built in parallel.

```text
M0 foundation   schemas/ textutil ids clock store/ scoping/ validate/registry
                + V-SPEC,V-PATH rules; project init; spec build/accept
M1 proof loop   queue/ prooftask/ decision table + V-PR,V-EXP,V-Q,V-COMMIT rules /
                committer/ expander — scenarios S1,S3,S4,S5,S6 + determinism
M2 docs         docsdb/ V-DR rules; needs_docs loop; matcher + fingerprint cache — S2
M3 endgame      freeze/ compiler/ audit/ graph msa-check + trace — S7
M4 surface      db indexer, ui/, remaining CLI polish — S8 + endpoint tests
```

Implementation notes that keep Opus out of the weeds:

```text
Build textutil + ids + clock FIRST — nearly every module imports them.
The decision table is a pure function (form, task_type) → verdict; write it and
  its 24 goldens before any queue/committer code.
The Committer is the hardest module: implement replay (V-COMMIT-04) as a test
  helper from day one, or determinism bugs surface late.
Never hand-roll JSON writing; everything goes through the canonical serializer.
When a doc and an implementation urge diverge, amend the doc in the same change
  (CLAUDE.md rule) — the docs are the program.
```

## 8. The V1 Demo (definition of done)

Run from a fresh checkout, real Claude workers, the P4 topic:

```text
1  paperproof project init p4-ldi
2  paperproof spec build examples/topic-input-p4.md → human reviews → spec accept
3  Expander writes the layer-0 proposal (question node, thesis node, the
   thesis→question edge, seed claims A,B, EDGE-A-B, and EDGE-B-T so the seed
   chain supports the thesis) → expand ingest → layer loop: build-tasks →
   dispatch ProofWorkers (≥2 in parallel) → validate → commit
4  EDGE-A-B form: inference gap → needs_repair(bridge); Committer wires C,D
   plus edges C→B, D→B; all four proved active; edge re-proved to
   pass(conditional)
5  a needs_docs verdict routes a DocsRequest; DocsWorker archives a BoE source;
   the same request made again hits cache (fulfilled_by="cache", no worker)
6  expansion to layer 2 in BFS-MAIN; BFS-ALT opens after MAIN closes;
   alternatives rejected or parked(absorbed) — both lanes closed with empty
   proposals
7  msa-check green → spine freeze (runs verify) → dry run → writing_ready
   (zero gaps by construction after a clean freeze — docs/06)
8  CompileWorkers write annotated sections to agent_outputs/prose/ →
   ingest-prose → audit run reports zero findings
9  paperproof verify → exit 0; paperproof trace --node <thesis-id> walks
   sentence → evidence → raw file
10 ui serve shows the finished Logic Map and empty queues
```

Every step above maps to a boundary contract in docs/08 and rules in docs/09 — the demo is the contracts, executed once, for real.
