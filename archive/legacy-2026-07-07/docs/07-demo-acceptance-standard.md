# 07 Demo Acceptance Standard

The first demo proves the workflow, not final prose quality.

## Demo Topic

Primary demo:

```text
P4: 从低利率到利率再定价：成熟养老金市场的流动性风险、杠杆约束与资产负债管理重构
```

Core event:

```text
2022 UK LDI crisis
```

Core question:

```text
Why can pension de-risking transform solvency risk into liquidity risk?
```

Forbidden overreach:

```text
do not generalize to all mature markets without qualifiers
do not give direct China policy prescription
do not claim fund-level causal estimation without data
do not treat one event as proof of universal mechanism
```

## Demo Inputs

```text
original paper draft
abstract
known references
official/regulatory sources
manual notes
user-provided paper summaries
```

## Demo Required Outputs

```text
PaperSpec
ProjectContract
Claim Graph
Edge Graph
ProofTask queue
AgentTaskPacket files
Evidence Ledger
ProofResult log
CommitDecision log
Queue state
Freeze report
CompilerDryRunReport
DraftMap if ready
AuditReport
WebUI state
Handoff bundle
```

## Seed Graph

Minimal seed:

```text
A: UK LDI strategies created margin-call liquidity pressure during rapid gilt yield movements.
B: Pension de-risking may reduce funding volatility while increasing liquidity fragility.
EDGE-A-B: A supports B.
```

Expected ProofResult:

```text
verdict: needs_bridge or supported_with_limits
support_level: C or B
edge_sustainability: not_directly_sustainable or conditionally_sustainable
```

Expected bridges:

```text
C: Distinguish solvency/funding risk from liquidity risk.
D: Show how leverage/collateral mechanics connect gilt yield movements to forced liquidity demand.
```

Expected Committer behavior:

```text
EDGE-A-B status becomes needs_bridge or active_with_limits
Bridge nodes C/D become candidate LogicNodes if needed
New WorkItems are appended to queue/work_items.jsonl
CommitDecision records all mutations
```

## Acceptance Steps

### Step 1: Spec

Pass criteria:

```text
paper_type set
orchestration pattern set
core question set
scope set
hard exclusions set
bfs_plan is a DAG
proof/docs/compiler policies set
```

### Step 2: Logic

Pass criteria:

```text
10-20 candidate claims extracted
each claim has one clear proposition
each node has type, scope, lifecycle_state
each edge has source, target, edge_claim, edge_type
no prose paragraphs are treated as nodes
```

### Step 3: Proof + Docs

Pass criteria:

```text
each core node has NODE_CHECK
each core edge has EDGE_CHECK
each empirical claim has evidence or DocsRequest
ProofResult uses discrete verdicts
no numeric scores
needs_bridge has at most two bridge proposals
needs_docs has DocsRequest
Proof does not mutate graph
```

### Step 4: Commit

Pass criteria:

```text
validated ProofResults are committed deterministically
bridge proposals create candidate nodes only through Committer
docs requests enter docs_queue
contradicted claims create tombstones
CommitDecision is append-only
```

### Step 5: Freeze

Pass criteria:

```text
local freeze only after validated support
empirical nodes require EvidenceUnit
allowed_language and forbidden_language are preserved
pending bridge/docs blocks freeze
frozen graph is protected from Logic mutation
```

### Step 6: Compiler Dry Run

Pass criteria:

```text
section plan generated from frozen graph
missing claims/evidence listed as compiler gaps
compiler does not create new LogicNode
compiler does not create EvidenceUnit
writing_ready is false until core blockers are resolved
```

### Step 7: WebUI / CLI / DB

Pass criteria:

```text
DB index rebuilds from JSONL
CLI queue list/claim/release/complete works
WebUI shows Logic Map and Queue Board
Queue items show ID, status, owner, blocked_by, next_action
Parallel lanes show active workers
stale_index is visible when DB is stale
```

## Demo Success Definition

Minimal success:

```text
The system can transform a seed edge A -> B into a proof task, agent task packet, validated ProofResult, deterministic CommitDecision, bridge queue update, compiler gap report, and WebUI-visible state.
```

Full demo success:

```text
The P4 paper can be represented as a frozen core argument with evidence-bound claims, known limitations, compiler readiness status, and final audit findings.
```
