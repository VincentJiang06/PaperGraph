> CONTEXT ONLY — DO NOT COPY. Re-derive every contract from the CODE.
> This file is a compacted memory of the OLD contracts, kept only so the
> rebuild does not lose intent. It is gitignored and thrown away after.

# Legacy design-contract compaction (docs/00–18, as of v2.1.1)

## 00-overview.md — system thesis, component map, changelog spine

- Intent: PaperGraph builds a paper as a proven Logic Graph, compiling prose only at the end. Runs under Claude Code: main session = Orchestrator; bounded subagents = ProofWorker / DocsWorker / CoverageCritic / CompileWorker. Files are state; deterministic Python package `paperproof` does all gates; Claude does judgment only.
- Pipeline: Topic → Scoping/ProjectContract → Logic Graph (BFS layers) → Proof Machine (workers fill check forms; code computes verdicts via decision table) → Docs Database (memoized search) → Committer (ONLY graph mutator) → Freeze → Compiler (dry-run → draft map → prose) → Audit. WebUI is a read-only monitor.
- Non-negotiables: JSONL canonical/append-only, DB derived; Committer sole graph mutator; workers answer closed-enum forms, never verdicts, no numeric scores; ≤2 bridge proposals per gap, never recursive; Docs never sets verdicts; no prose before Compiler; citations must resolve to archived Documents; parallel workers have disjoint output files.
- Naming: product PaperGraph, package/CLI `paperproof`, data root `data/projects/<id>/`.
- Changelog is normative: r2 (ladder + not_evaluated sentinel; wellformed outranks evidence; conditional iff assumptions non-empty), r2.1 (bridge wiring; MSA-9; input-scoped commit currency; V-PATH-04 prefix rule), r3 (from ai-jobs live run: evidence-seeding sweep, DocsPack = REQUESTED ∪ top-12 MATCHED, evidence-arrival staleness V-TASK-04, cache-hygiene, 3-clause V-PATH-04 scan, per-rule failure detail, implicit-complete on validate).
- Search program adoption entries: S1+S3-lite (Stage A), S2, S4+S3-triangulation (Stage B, SUPERSEDES the r3 flat docs cap and flat ≥2-EU floor), S5 (Stage C) — all five ADOPTED/BINDING.
- v2.1 (D1–D15): saturation human-review branch; wave CLI closed surface (`docs wave-member`/`wave-resolve`); critic as contracted worker; pipeline order fixed (layer-0 expansion BEFORE sweep); one sweep mechanism (request --fan + wave); angle-folding rules; merger quote-integrity (content_hash-only dedup); round-2 plan discrimination; 512-token embedding truncation; dash-normalized scope periods; render-prompt commands enforce V-SRC-05; publisher independence; ingest-prose implicit complete.
- v2.1.1: enforcement wiring only (V-GATE-01 at expander+verify; V-EDGE-01/03, V-NODE-04 at record time; verify sweeps specs/ + latest_proof_result_id), golden count 24→26 (N11/E15 scope-outranks-duplicate), doc reconciliations (counter fold breadth, content_hash-only merger dedup, local-doc publisher). Known deferred: commit/queue lock race, stuck `validating` items, empty-Actors scope guard.

## 01-topic-and-scoping.md — topic input, PaperSpec, ProjectContract

- Intent: turn a loose idea into a fixed-scope question with a declared outcome direction; everything downstream checks against the contract.
- Topic file: 9 required sections (Topic, Core Question, Intended Thesis, Paper Type, Scope, Exclusions, Seed Claims, Known Sources, Success Criteria); deterministic parsing rules P1–P7 (heading title match, duplicate heading fails V-SPEC-01, "Key: value" scope lines, UTF-8/CJK legal).
- Six paper patterns enumerated; v1 implements only `single_event_mechanism` (two lanes: BFS-MAIN, BFS-ALT).
- `spec build` (code) emits PaperSpec (`paper_spec.v1`) + ProjectContract (`project_contract.v1`); `--patch` is a two-key RFC 7386 merge patch, fixed application order (spec patch → derive contract → contract patch). Nobody hand-edits specs/.
- Contract fields: fixed_question, outcome_direction, structured `scope` (machine authority for V-NODE-03), verbatim `in_scope` (human-readable, patched separately), forbidden_claims, accepted_by_user/accepted_at.
- Rules: `spec accept` is the only acceptance path (human); contract immutable after acceptance (edit = contract_version+1, archive to specs/history/, re-open proofs — v1 manual); V-GATE-01 blocks all expansion/proof/dispatch until accepted.
- Post-acceptance order (v2.1 D4/D5): layer-0 expansion commits first, THEN the evidence-seeding sweep (per fact/mechanism layer-0 node: `docs request --fan` → `docs wave --fan`) until V-SWEEP-01.

## 02-logic-graph.md — nodes, edges, lifecycle, BFS, spine, MSA

- Intent: claims as nodes, argumentative moves as directed edges with discrete strength; layer-by-layer BFS expansion batches proof work. "One fact, one place" typing discipline.
- LogicNode (`logic_node.v1`): node_type ∈ {question, thesis, fact, mechanism, definition, alternative}; evidence_bindings copied by Committer on NODE pass (edges carry no bindings — their evidence lives in the verdict record); parents = BFS provenance; origin.kind ∈ {seed, expansion, bridge}; claim_version bumps on narrow.
- LogicEdge (`logic_edge.v1`): edge_type ∈ {supports, refutes, depends_on}; V-EDGE-04: refutes may only target an alternative (v1). Edges inherit lane+layer from their source node. `elaborates`/`contrasts_with` deferred to v2.
- Lifecycle: 7 states {candidate, pending_proof, active, needs_repair, needs_docs, rejected, parked}; state changes ONLY at commits; `frozen` is a boolean, not a state; rejected is terminal; rejection cascades tombstone incident edges (state_reason=endpoint_rejected). state_reason is a bare enum token; state_detail is structured.
- JSONL updates are appends: latest record per id is current; history never rewritten.
- Park/unpark are administrative commits (`--reason absorbed|not_needed`, absorbed needs `--into`); parking clears strength.
- Strength: {unassessed, strong, conditional}; conditional iff assumptions non-empty at pass — uniform for nodes and edges.
- Layer 0 (V-EXP-06): exactly one question + one thesis node + supports edge thesis→question + seed claims; no other proposal may contain question/thesis. Lane completion = committed empty (closing) proposal + no open work in the lane; depends_on lanes gate proposals (V-EXP-07).
- Bridge nodes are created AND wired by the Committer (never wait for expansion turn); bridge rejection cascades normally, re-proof re-judges with surviving premises, renewed gap counts toward the 2-round cap.
- Spine (computable): {Q, T, edge T→Q} ∪ active ancestor closure of T along supports/depends_on; refutes/rejected/parked never join. "Touches" adjacency rule catches half-proved expansions.
- MSA checklist MSA-1..9 (mechanical stop criterion, `graph msa-check`): unique Q/T active; T→Q active; spine all active; MSA-4 delegates to S4 role-profile floors; alternatives all rejected/parked; no open work touching the spine (dead letters block); all lanes complete; latest dry run gap-free; MSA-9 spine contains ≥1 active fact/mechanism (anti-vacuous). success_criteria deliberately not consumed by MSA in v1.

## 03-proof-machine.md — check forms, ladder, decision table

- Intent: atomically resolve one logical question per task; the worker NEVER chooses a verdict — it fills a closed-enum check form; code computes the verdict from a published decision table.
- Task types: NODE_CHECK, EDGE_CHECK (BINDING_CHECK deferred to v1.1). Ordering rule: EDGE_CHECK enqueued/claimable only when both endpoints are active (queue-enforced via blocked_by).
- Bundle: ProofTask + ContextPack + DocsPack, self-contained; re-proof/staleness rebuilds mint -rN revisions (bundles immutable). ContextPack carries a claim_digest of every non-rejected node (global duplicate detection).
- Form (`proof_result.v1`): scope_check, duplicate_check{duplicate, duplicate_of}, wellformed_check, evidence_check, inference_check (EDGE only — presence is schema-checked V-PR-04). No verdict field, no worker-invented ids (V-PR-03); PR- id assigned by the Validator.
- Evaluation ladder (only legal form shape, V-PR-14): Stage A scope+duplicate (stop if out_of_scope/duplicate → rest not_evaluated); Stage B wellformed (too_broad/compound → exactly 1 narrow repair, stop); Stage C evidence (fact/mechanism nodes may not answer not_required V-PR-05; insufficient → ≥1 docs_requests, stop; contradicting → stop); Stage D inference (edges; gap → 1–2 bridge repairs; holds_only_with_assumptions ⇔ assumptions non-empty V-PR-15).
- Attachment rules tie each ladder answer to exact attachments; pass ⇒ language_limits.allowed AND .forbidden non-empty, otherwise null (V-PR-13).
- Repair kinds: bridge {kind, claim, node_type ∉ {question,thesis}} and narrow {kind, narrowed_claim}. Committer wires bridges; workers propose claims only.
- Decision table (first match wins, total over ladder-valid forms, precedence is contract): out_of_scope → rejected; duplicate → rejected; too_broad/compound → needs_repair(narrow); contradicting → rejected; insufficient → needs_docs; fails → rejected; gap → needs_repair(bridge); otherwise pass (conditional iff assumptions). 26 golden rows incl. N11/E15 scope-outranks-duplicate.
- Verdict record (`verdict_record.v1`) appended by Validator to proof/proof_results.jsonl; exactly one populated computed_verdict subfield; V-PR-12 recomputes on every verify (mismatch = corruption exit 3).
- Worker protocol: read bundle only, walk ladder, write one output file, stop; ≤150-word notes; no search — missing evidence routes a DocsRequest. Validation failure ⇒ ≤2 retries then dead letter.

## 04-docs-database.md — documents, evidence, memoized search, sweep

- Intent: archive every source once, distill into reusable EvidenceUnits, serve via DocsPacks; make repeated search cheap and hallucinated citations impossible.
- Document (`document.v1`→`v2` since S3, +provenance block): source_type enum (peer_reviewed|official_report|working_paper|news|dataset|user_notes); content_hash sha256 is the dedup key; citation_key unique; text extraction (pypdf) at ingest, text_path null on failure.
- EvidenceUnit (`evidence_unit.v1`): kind quote|paraphrase (quote must be verbatim substring of archived text, V-DR-05); support_direction supports|refutes|context; can_cite_for/cannot_cite_for both non-empty (V-DR-02) — the anti-hallucination core.
- DocsRequest (`docs_request.v1`): status open|fulfilled|not_found; fingerprint = sha256 of normalized need+hints; fulfilled_by DRES-id or "cache"; `fan` flag (S2). DRES- ids number ingest events (no registry file).
- Evidence Seeding sweep (r3/v2.1): contract accept → layer-0 expansion → sweep (one fanned request + wave per fact/mechanism layer-0 node) → proof loop; V-SWEEP-01 floor gates first expansion beyond layer 0 (≥2 EU from ≥2 docs, or not_found on ≥2 angles, per node). Expected post-sweep steady state ~10–20 docs, 30–60 EUs.
- Memoized search: (1) request-level cache = fingerprint equality with a DRES-fulfilled request only ("cache"-fulfilled never chains; matcher-hit cache trigger removed in r2.2 — sufficiency is the ProofWorker's decision, never the cache's); (2) evidence matcher (fixed keyword token-overlap score ≥2 + scope_compatible).
- DocsPack composition (r3): pack = REQUESTED ∪ top-12 MATCHED; REQUESTED (traced request→DRES→ingested_from) included unconditionally. S5 replaces the matcher SCORE with hybrid when the model is present; composition unchanged.
- Evidence-arrival staleness (V-TASK-04): ingest marks affected queued/blocked proof items stale.
- DocsWorker protocol: one request, prompt-embedded fields, SearchPlan execution (docs_result.v2 with query_log), one output file; coverage expectations 2–5 docs / 4–10 EUs, disconfirming duty, 403/PDF fetch resilience; not_found is legitimate. Docs round-trip cap SUPERSEDED by S4 saturation (born-dead reason=saturated; floor_met distinguishes the human_review conflict case).
- Prohibitions: DocsWorkers never set verdicts or touch the graph; no invented sources. DuckDB `db/` index is derived only; JSONL wins.

## 05-workflow-and-queue.md — pipeline, WorkItem status machine, gates

- Intent: parallel workflow with deterministic gates; every shared-state mutation passes exactly one gate.
- Pipeline order (v2.1 D4): scoping → layer-0 expansion → evidence-seeding sweep → deeper expansion (gated by V-SWEEP-01) → proof loop (build-tasks → workers → validate → commit) → freeze → compiler dry-run → prose → audit.
- Queues: proof_queue, docs_queue (incl. wave members), critic_queue (target_type="wave"), compile_queue; commit_queue is a DERIVED VIEW of validated items (never a stored queue_name). Freeze/audit are events, not queues.
- WorkItem (`work_item.v1`): bundle, output_files, blocked_by, lease{claimed_by, expires_at, manifest}, attempt. lease.manifest = claim-time hash map for V-PATH-04.
- Status machine: 11 states {queued, claimed, running, validating, validated, committed, blocked, stale, failed, dead, cancelled}; the transition table is closed (V-Q-01); every transition emits exactly one QueueEvent (V-Q-03; op enum of 17 values). Notable edges: (created)→dead born-dead (saturation or bridge cap); implicit complete performed by validate/ingest commands (r3/v2.1); validated→stale/cancelled on commit-time refusals; dead→queued only via human `queue requeue`. Terminal: committed, cancelled; dead is terminal-until-human.
- Blocked semantics: EDGE_CHECK claimable only with both endpoints active; needs_docs re-proof blocked by docs items; bridge re-proof blocked by bridge checks. Unblock sweep at start of every queue command. Lease 900s, heartbeat extends, expiry attempt+1, >3 ⇒ dead (V-Q-05); claim atomic under queue lock (V-Q-02).
- Parallelism enforcement (r3 3-clause V-PATH-04 scan, the r2 impl's byte-identity/all-dirs baseline ruled non-conformant): (a) JSONL prefix hash intact; (b) recorded IMMUTABLE non-JSONL files byte-identical (db/** never in manifest); (c) new files fail only in strict dirs (specs/ graph/ queue/ commit/ freeze/ audit/). Failures name the offending path.
- Validation gate: deterministic code; failed_rules with per-rule detail; ≤2 retries then dead letter; worker chat text never consulted.
- Commit gate: single-writer under commit/.lock; staleness precondition is INPUT-SCOPED — proof commits check target+1-hop since bundle snapshot (parallel proofs never invalidate each other); expansions check whole graph; administrative reads under lock. Same input+snapshot ⇒ byte-identical CommitDecision.
- Layer loop spelled as actual CLI commands, including the S2 wave sub-loop (wave → members → auto-merge → critic → wave-resolve; `docs ingest-result` refuses wave members).

## 06-compiler-and-audit.md — freeze, dry run, draft map, prose, audit

- Intent: lock the argument, check readiness, produce prose exactly once, audit it. Freeze never creates claims/evidence.
- Freeze levels/closures: local (one record), subtree (target + active ancestor closure), spine (the spine; precondition for compiling). Preconditions V-FRZ-01..04: closure active; fact/mechanism nodes clear S4 role-profile floor (V-COV-04, supersedes flat rule); no open work touching closure (dead letters block); spine freeze requires MSA pass + verify exit 0. FreezeItem unions dedup/sorted language limits; frozen=true set via Committer batch commit (Freeze never writes graph files). Unfreeze is human-only (action=unfreeze, revokes, re-open proofs).
- Compiler phase 1 dry run (`compiler_dry_run.v1`): section plan + gaps + writing_ready. Gap kinds (closed): missing_evidence (S4 floor), unhandled_alternative, weak_spine_edge (conditional + empty limits proxy), missing_section_claim, contract_violation. Gap identity = (kind, target_id); one compile_queue item per new gap, idempotent re-runs auto-cancel resolved gaps (V-CDR-01); dry run creates nothing (V-CDR-02); section plan covers every spine node exactly once (V-CDR-03). First dry run after a clean spine freeze reports zero gaps BY CONSTRUCTION.
- Section plan template (single_event_mechanism): introduction (Q+T), concepts (definitions), mechanism, evidence (facts), alternatives (dispositions as context), conclusion; deterministic assignment by node_type, order (layer, node_id).
- Phase 2: DraftMap (`draft_map.v1`) fully derived (byte-identical given same inputs); per-section claims with evidence_ids + language limits + edge_order. CompileWorkers write agent_outputs/prose/<section>.md; `compiler ingest-prose` implicit-completes, runs V-PROSE as validate-pass, copies to compiler/prose/ and commits (one command).
- Annotation grammar (regex-checked): claim-bearing sentences carry "(claim: NODE-x)"; citations "(cite: EU-x)" in the same sentence, bound in DraftMap; transitions unannotated.
- Audit (v1 fully mechanical; semantic AuditWorker → v1.1): binding/strength/scope/coverage checks; AuditReport findings typed with location + target_id, routable as compile_queue items (V-AUD-01); audit appends only to audit/, never writes prose (by construction, V-AUD-02).

## 07-runtime-and-tooling.md — roles, storage layout, ids, CLI, WebUI surface

- Intent: how the system runs under Claude Code; where state lives; the CLI/WebUI surface overview (authoritative command contracts live in docs/10 §4).
- Roles: Orchestrator (main session, CLI-only state changes), ProofWorker, DocsWorker, CoverageCritic, CompileWorker, paperproof (code), Human (accepts contract, owns unfreeze/requeue/dead-letter resolution). No API key needed.
- Storage layout under data/projects/<id>/: specs/ (+history/), graph/ (nodes, edges, tombstones, snapshots), proof/ (tasks/context/proof_results.jsonl/.lock), docs/ (raw text docspacks plans merged + documents/evidence_units/docs_requests/sources/waves JSONL), agent_outputs/ (expansions, proof_results, docs_results, coverage_reports, prose), agent_notes/, queue/, commit/, freeze/, compiler/, audit/, db/ (derived, incl. db/semantic/).
- Conventions: JSONL append-only, latest-per-id; every canonical record carries schema_version + project_id + created_at (exceptions: snapshot omits project_id; bundle files omit created_at); RFC 3339 UTC timestamps, injectable clock (PAPERPROOF_NOW); canonical serialization (same data ⇒ same bytes); fcntl append locks + commit/queue/proof locks; POSIX-only; actor identity from --agent/PAPERPROOF_ACTOR/"orchestrator".
- ID formats (assigned by code via max+1 scan, no counter files): NODE-001, EDGE-001-002[-dep|-ref][-vN], EXP-<lane>-L<layer> (file-naming convention exception), PT-/CTX-/DOCSPACK-<target>[-rN], PR-, DOC-/EU-/DRES-, DR-, WI-/QE-, GS-/CD-, TS-, FRZ-, CDR-, DRAFTMAP-, AUD-, SP-DR-x[-<angle>][-rN-<origin-slug>], WV-, SRC-.
- Snapshots: hash+rows over the 3 graph JSONL files; current iff recompute matches; taken by Committer post-commit; docs appends never invalidate graph snapshots.
- CLI grammar `paperproof <group> <command>`; one JSON envelope per command; command-group overview (project/spec/graph/expand/proof/docs/queue/validate/commit/freeze/compiler/audit/db/ui/verify/trace).
- Worker dispatch flow: queue claim → render-prompt (D11) → subagent writes output → validate/ingest (implicit complete) → commit apply (serial).
- WebUI HTTP surface (FastAPI, GET JSON): /api/overview, /api/graph, /api/record/{id}, /api/queue, /api/events, /api/evidence, /api/coverage, /api/compiler, /api/trace/{node}; POST claim/release/db-rebuild only. Derived DuckDB: one table per canonical JSONL + *_current views + index_manifest hashes.

## 08-module-contracts.md — BINDING boundary layer (wins on any boundary question)

- Intent: pins every boundary — producer, consumer, pre/postconditions, write permissions. When another doc disagrees on a boundary, this doc wins.
- Artifact ownership table: exactly one producer per artifact (Committer for graph JSONL; Validator for verdict records; Docs ingestor for documents/EUs; queue engine for work items/events; Freeze gate, Compiler, Audit for their files; workers only their declared agent_outputs/** file). Corollaries: C1 Claude agents never append canonical JSONL (CLI only); C2 unvalidated agent_outputs files are not state.
- B1 Human→Scoping (topic file, V-SPEC-01..03). B2 contract acceptance (immutable after; V-GATE-01 blocks all work pre-acceptance).
- B3 Expander→Commit: ExpansionProposal (`expansion_proposal.v1`), based_on_snapshot from `project status`; ≤12 nodes, one layer, edge refs by existing id or "#index" (V-EXP-01..07); empty proposal closes a lane; Expander never writes graph files.
- B4 ProofTask builder→ProofWorker: self-contained bundle; -rN revisions never overwrite; 1-hop neighborhood definition pinned (V-TASK-02); ContextPack schema (`context_pack.v1`, + S4 coverage block V-COV-02); DocsPack schema (v2 since S5 with retrieval block); staleness split: Committer marks target/1-hop mutation, docs ingestor marks evidence arrival (V-TASK-04); composition V-TASK-05.
- B5 ProofWorker→Validator: the maker/checker heart — form in, verdict computed by code, verdict record appended (PR- id); acceptance = declared path + schema + V-PR + clean V-PATH-04 scan; chat text never parsed.
- B6 verdict→action table (deterministic): pass → active+strength(+bindings on nodes); needs_repair(bridge) → bridge candidates created AND WIRED (node X with lane/layer of the edge's source, parents=[B], origin bridge; edge X→B depends_on-if-definition else supports, synthesized edge_claim; re-proof blocked_by all bridge items); needs_repair(narrow) → claim replaced, claim_version+1; needs_docs → requests/wave + saturation consulted (V-COV-03; human_review action on saturated+floor-met); rejected(...) → tombstone + cascade (incident edges endpoint_rejected; in-flight items cancelled at commit by V-COMMIT-06). Bridge-round cap = 2 per edge, then born dead.
- B6b administrative commit kinds: expansion, park, unpark, freeze_batch, unfreeze_batch, contract_reopen (v1: no CLI trigger, API/tests only).
- CommitDecision (`commit_decision.v1`): kind + action enums closed (action incl. human_review since v2.1); graph-mutating actions carry the full appended record; replay from pre-state + action records must reproduce post-snapshot (V-COMMIT-04). Tombstone (`tombstone.v1`) reason enum: contradicted|out_of_scope|duplicate|endpoint_rejected.
- B7 Committer→Docs: DocsRequest + docs item unless fingerprint cache hit; DocsResult schema (v2 with query_log since S1); ingestor archives, dedups, assigns ids, updates status, unblocks re-proof, marks staleness. B7b wave engine→CoverageCritic: read-only closed form; code computes wave verdict (R_MAX=2).
- B8 Freeze gate (V-FRZ-01..04; frozen set via Committer batch commit). B9 frozen graph→Compiler (V-CDR-01..03). B10 DraftMap→CompileWorker→Audit (V-PROSE-*, mechanical audit).
- Cross-cutting: single-writer summary per directory; snapshot discipline (input-scoped currency = the entire v1 concurrency story); ID discipline (code-only assignment); uniform failure taxonomy (failed_rules + per-rule detail, ≤2 retries, dead letter, human requeue).

## 09-verification.md — shared text algorithms + the V-* rule registry

- Intent: all checking is code (no LLM); three layers — runtime V-* rules, module tests, pipeline checks. Rule IDs are stable and cited everywhere.
- §0 shared text algorithms pinned once (textutil): normalize, casefold, is_cjk, tokens (CJK chars are single tokens), word_count, sentence_split (CJK terminators split always), contains, quote_match (whitespace-normalized substring, case preserved), scope_compatible (period year-range intersection with Unicode-dash normalization v2.1 D10; region casefold-equal; actors/mechanisms intersection; missing keys never conflict), frozen 82-word stopword list.
- Rule families (names + one-line scope):
  - V-SPEC-01..05 (topic/scoping); V-GATE-01..03 (acceptance gate, snapshot currency, frozen-record protection); V-SWEEP-01 (flat pre-proof volume floor — deliberately NOT superseded by S4).
  - V-PATH-01..04 (output path/JSON/write-scope safety; 04 = the 3-clause scan).
  - V-NODE-01..04, V-EDGE-01..04, V-GRAPH-01..03 (commit-time record checks: schema, 1–2-sentence single proposition heuristic, scope compatibility, parent validity; edge endpoint/duplicate/refutes-target rules; acyclicity, reachability, strength-state coherence).
  - V-EXP-01..07 (frontier committed, snapshot current, ≤12 nodes/single layer, refs resolve, static node checks, layer-0 shape, lane dependencies).
  - V-TASK-01..05 (stale-refusal, ContextPack completeness, DocsPack resolution, evidence-arrival staleness, pack composition).
  - V-PR-01..15 (the biggest block: closed enums, task match, no verdict/numeric/id fields, inference-field presence, fact/mechanism evidence duty, DocsPack citation containment, conditional attachments, duplicate_of resolution, repair shapes, notes ≤150 words + id-token scan, narrow validity, verdict recomputation, language-limits iff pass, ladder shape, assumptions iff holds_only_with_assumptions).
  - V-DR-01..06 (doc_ref xor doc_id, cite boundaries non-empty, no worker ids/verdicts, source_type+origin+inline text, quote verbatim, honest not_found).
  - V-SP-01..05 (S1 query accounting); V-SRC-01..05 (provenance, quoted_via, append-only registry/no silent tier-lowering, triangulation, dispatch-excerpt completeness); V-COV-01..05 (ledger determinism, ContextPack coverage block, saturation-not-count, role-profile floors, narrow-inheritance/reset); V-SEM-01..05 (model pin/determinism, matcher naming + fixed-6-decimal scores, loud degrade, no similarity auto-fulfillment, within-doc-only clustering); V-WAVE-01..05 (distinct member outputs, merger determinism, closed critic form, round cap + follow-up origin, one DRES per wave).
  - V-COMMIT-01..06 (input-scoped currency, validated-input, frozen refusal, replayability, post-commit graph invariants, provable-state target/cancel-on-tombstone).
  - V-FRZ-01..04, V-CDR-01..03, V-PROSE-01..04, V-AUD-01..02, V-Q-01..05.
- Module test matrix minimums per module; FakeWorker strategy (deterministic table-driven stand-ins; real LLMs only in milestone live-smoke).
- Pipeline checks: integration scenarios S1–S8 (seed/bridge loop, docs loop + cache, contradiction cascade, 4-way parallel, crash/lease expiry, staleness rebuild, full pipeline to audited prose, db rebuild/corruption); `paperproof verify` = whole-project invariant sweep (exit 3 on violation), precondition of spine freeze and milestone acceptance; `trace --node` walks sentence → claim → freeze → commits → verdicts → bundle → EU → Document → raw file.

## 10-v1-design.md — concrete v1: scope, stack, CLI contracts, prompts, build order

- Intent: what gets built first and in what order; authoritative on v1 scope and the closed CLI surface.
- In scope: full pipeline for single_event_mechanism, two lanes, NODE/EDGE checks, docs ingest + web search, memoized search, commit/freeze/compile/audit, queue with leases/retries/dead letters, CLI + read-mostly WebUI, verify + trace, and the whole adopted S1–S5 search program. Out/deferred: BINDING_CHECK (v1.1), semantic AuditWorker (v1.1), contract re-versioning automation (v1.1), merge lanes/comparison/contrasts_with + other patterns + grill-me interviewer (v2); multi-project/remote/Neo4j not planned.
- Stack: Python 3.12+, pydantic v2 strict extra="forbid", typer, FastAPI + vendored cytoscape (no npm), DuckDB derived, POSIX-only, no async runtime, no git dependency at runtime; determinism via PAPERPROOF_NOW/ACTOR + canonical serialization + max+1 ids.
- Source layout: src/paperproof/{schemas (registry), textutil, ids, clock, store, scoping, graph, expander, prooftask, validate/registry+rules, committer, docsdb, queue, freeze, compiler, audit, prompts, cli, ui}.
- CLI envelope: one JSON object {ok, command, data, errors, warnings}; exit 0/1/2/3 (ok / validation-domain / usage / corruption). Command list CLOSED for v1 — amending it means amending this doc first. Per-command contracts pinned for ~45 commands (project init/status, spec build/accept/show, graph list/show/msa-check/park/unpark, expand ingest, proof build-tasks/build-task/render-prompt, docs ingest/search/build-pack/request/ingest-result/source/plan/wave/wave-member/wave-resolve/coverage/render-prompt, queue lifecycle commands, validate result/proposal/docs-result, commit apply, freeze apply/unfreeze, compiler dry-run/draft-map/render-prompt/ingest-prose, audit run, db rebuild/check + semantic, ui serve [--auto-rebuild], verify, trace).
- Worker prompt templates (proof_worker, docs_worker, critic_worker, compile_worker, retry_suffix) are canonical text, shipped verbatim in src/paperproof/prompts/, drift-guarded by test; each enumerates its exact output key set and forbidden extras, carries the r3 SELF-CHECK block; render-prompt commands (D11) are the canonical renderers (plan/DraftMap/registry embedding, V-SRC-05 enforced at render, retry suffix auto-appended).
- WebUI v1: five views; writes = queue claim/release + db rebuild only.
- Build order: M0 foundation → M1 proof loop → M2 docs → M3 endgame → M4 surface; each milestone gates on verify clean + its docs/11 §9 row. Decision table first (pure function + 26 goldens); Committer replay helper from day one; docs are the program (amend doc in the same change).
- V1 demo (definition of done): 10-step fresh-checkout run with real workers on the P4 topic, exercising bridges, docs cache, lane closure, MSA, freeze, dry run, prose, audit, verify, trace, UI.

## 11-test-suite.md — executable test plan (authoritative on test structure)

- Intent: exactly how the system is tested — runner, layout, fixtures, fakes, meta-tests, milestone gates. Two commitments: no LLM in the suite; coverage measured in RULES (every V-* id provably exercised) not lines.
- pytest with markers {unit, contract, integration, live, slow}; default run excludes live; CLI via CliRunner + subprocess smoke.
- Layout: tests/{unit, contract (one file per rule family + meta-tests), integration (S1–S8 + determinism), fakes (FakeProofWorker/FakeDocsWorker/FakeCriticWorker/FakeCompileWorker + scripts), fixtures (schemas goldens, topics, 26 decision forms, vrules/<RULE-ID>/pass_*|fail_*, hostile, corpus, prose)}.
- Determinism harness: PAPERPROOF_NOW/ACTOR injection; test_determinism runs S1 twice ⇒ byte-identical canonical state.
- Fixture naming is load-bearing (rule-coverage meta-test globs vrules/<id>/pass_*/fail_*).
- FakeWorkers: table-driven, real I/O shape, modes script|crash|hostile; drain() dispatcher with parallel=N thread mode.
- 26 golden decision-table rows (N01–N11, E01–E15) with stable ids; totality fuzz over the full enum product; hostile catalog H01–H18/D01–D05/C01, each mapped to a named rule (H10 remapped to verify-level V-COMMIT-04 replay in r3); validator check order (V-PATH → raw-tree scan → schema → semantic) is contract.
- Meta-tests: rule coverage (vrules fixtures or SCENARIO_COVERED map, dangling pointers fail), CLI conformance (closed command list mirrored; full stub surface registered at M0), schema round-trip, decision totality + V-PR-12 at rest.
- Integration scenarios S1–S8 with pinned per-scenario assertions (bridge wiring/spine membership, cache DRES-only + REQUESTED composition + saturation, cascade + MSA-9 coda, 4-parallel linearizability, lease expiry to dead, -rN immutability, full P4 pipeline + trace + audit, db rebuild idempotency/corruption exit 3).
- Milestone gates M0–M4 (cumulative; live smoke recorded in agent_notes/milestones/).
- Worklists (spec-ahead-of-code, each item a REQUIRED test change): §10 r3 (T-r3-1..10), §12 Stage A S1/S3-lite/S2 (T-S1-*, T-S3-*, T-S2-*), §12b S4 + triangulation (T-S4-*), §12c S5 (T-S5-*, semantic marker skips without deps), §13 v2.1 (T-v2.1-1..18 mirroring D1–D15, incl. the 28-rule registration count assertion), §14 v2.1.1 (T-v2.1.1-1..13 enforcement-wiring regressions, golden count 26).

## 12-webui-spec.md — monitor design (authoritative within docs/10 §6 scope)

- Intent: complete design of the read-mostly monitor; may not widen the v1 scope or API surface (amend docs/10/07 first). Answers within 5s: what is open / who works on what / what is blocked / what can be committed / what is frozen / is the index stale.
- Principles P1–P5: read-mostly mirror (3 writes = claim/release/db-rebuild via the same code paths); every pixel traceable to a canonical record (Record Drawer); honest staleness (loud banner); never color alone (color+glyph pairing normative, CVD-validated tokens); boring tech (one static page, vanilla JS polling, vendored cytoscape, no build step).
- Shell: top bar (contract chip, MSA n/9, open/dead counts), left nav of 5 views (Events auxiliary), single banner slot with priority corruption > stale > contract-unaccepted, hash routing with serialized filters, 5s polling (15s Logic Map with diffing).
- Design tokens as CSS custom properties, light+dark, lifecycle-state and work-item-status palettes with a normative glyph table.
- Global surfaces: Record Drawer (raw JSON, version history, proof history, trace breadcrumb; deep-linkable), empty/error states with retry cards + backoff.
- Views: Overview (contract/MSA/dead letters/queue matrix/recent events, all counts link into filtered views), Logic Map (shape=node_type, fill=lifecycle_state, edge style=strength; lanes as swimlanes; spine highlight; 500-node perf target), Queue (tabs incl. critic + derived commit; wave grouping; dead letters pinned; CopyCmd for requeue/commit), Evidence (master-detail, can/cannot_cite_for, orphans toggle, S4 coverage panel), Compiler (readiness hero, gaps, section plan, prose tabs with annotation chips, audit), Events (cursor-paged).
- CopyCmd device: work the UI may not do renders as a copy-ready CLI command — the gate discipline stays visible. Accessibility bar (contrast, keyboard, no color-alone). Test hooks: endpoint tests, DOM smoke via data-testid, six-questions fixture, stale-banner test.

## 13-search-program.md — S1–S5 umbrella (ADOPTED, binding)

- Intent: staged spec sets turning search from improvisation into machine-checkable thoroughness; each "did we search enough?" question becomes a predicate (plan accounted, wave merged+criticized, sources tiered, coverage measured to saturation, recall semantic).
- Normativity: all five sets ADOPTED and BINDING via docs/00 changelog entries + docs/11 worklists; docs/10 stays authoritative on CLI/build surface, docs/08 on boundaries.
- Motivation mapped 1:1 to live-run failures: S1 improvised queries, S2 serialized angles, S3 lost fetch knowledge/untyped source quality, S4 vibes-based stopping (cap dead-lettered a healthy target), S5 keyword over/under-match + CJK↔EN mismatch.
- Composition: request → S1 plan per angle → S2 wave (members execute plans with S3 recipes/provenance) → deterministic merger → coverage critic → ≤2 follow-up rounds → ingest updates S4 ledger/saturation → S5 hybrid pack assembly → proof resumes; post-saturation needs_docs dead-letters as `saturated`.
- Dependencies: S2 needs S1; S4 needs S1+S2+S3 tiers; S3 and S5 independent. Stage A fixes VOLUME, Stage B STOPPING, Stage C RECALL. Every set ships schemas, closed enums, deterministic algorithms, V-* rules, CLI/prompt deltas, T-S* test hooks.

## 14-search-planning.md — S1 deterministic SearchPlans (ADOPTED)

- Intent: code compiles a deterministic SearchPlan from the claim; the worker executes and accounts for every query; validation rejects unaccounted plan lines.
- SearchPlan (`search_plan.v1`, docs/plans/, immutable, embedded in the prompt): facets (core_terms ≤6 highest-frequency non-stopword tokens, scope_terms, frozen counter_terms), fixed query templates per angle (core, angle+ANGLE_SUFFIX, hint, narrow, counter — counter MANDATORY in every plan), stop caps. Same request ⇒ byte-identical plan.
- docs_result.v2: structured query_log {qid, executed, outcome ∈ productive|empty|blocked|offtopic, urls_seen, docs_taken (integer counts), note} replaces free-text search_log; extra worker queries logged as X-ids (plan is a floor, not a ceiling).
- Rules V-SP-01..05: every qid accounted once (executed=false only blocked+note); counter executed or blocked, never skipped; docs_taken ≤ urls_seen and documents require ≥1 productive entry; honest not_found; plan file resolves and matches the request.
- Adoption deltas: `docs plan --request`; prompt accounting block; docs/plans/ storage; tests T-S1-1..3 (+ T-S1-back regression guard).

## 15-search-orchestra.md — S2 waves, merger, coverage critic (ADOPTED)

- Intent: one request fans into a wave — parallel per-angle members (each on its S1 plan), deterministic merger, fresh adversarial read-only critic whose closed form drives ≤2 bounded follow-up rounds.
- Wave: one member per angle {official_stats, academic, industry, counter} (+news if the period touches the last 18 months); each member = docs_queue item + angle plan SP-DR-x-<angle> + distinct output path. Round>1 members get round+origin-discriminated output paths AND plan ids (D8; origin `angle:<name>`/`expected_source:<name>`, de-duplicated/indexed), compiled with the critic's suggested_query as a hint — never re-executes a byte-identical plan.
- Wave record `search_wave.v1` (docs/waves.jsonl): status open|merging|critic|followup|closed; members carry round + origin (operationalizes V-WAVE-04).
- Merger (code, when every member terminal): dedup by content_hash ONLY (v2.1.1 D-d — canonical-URL collapse subsumed; differing-hash URL collisions keep BOTH docs to protect V-DR-05); canonical_url is a TOTAL normalization helper; drop exact-dup EUs; deterministic ordering; ONE merged docs_result.v2 at docs/merged/, single DRES per wave (V-WAVE-05); merged ingest runs V-DR but not V-SP (per-member check).
- Critic: distinct bounded worker on critic_queue (target_type="wave"), output coverage_report.v1 in agent_outputs/coverage_reports/; closed form (angle_covered ∈ {yes, tried_empty, tried_blocked, no_attempt}; primary_source_present; disconfirming_captured); ≤3 expected_sources; notes ≤100 words; NO documents/evidence_units. CODE computes the wave verdict: sufficient / followup (opens members per no_attempt angle + expected_source; empty spec list closes immediately, D2) / closed at R_MAX=2.
- Rules V-WAVE-01..05. Operationalization pinned: `docs wave` starts + supersedes the single item; `docs wave-member` and `docs wave-resolve` drive it as a closed CLI surface; auto-merge + auto-open critic when the last member lands; fan=false stays the pre-S2 single-member path via `docs ingest-result`.

## 16-source-registry.md — S3 tiers, fetch recipes, provenance, triangulation (ADOPTED)

- Intent: durable project memory of where evidence lives, how to fetch it (403/PDF workarounds), and how much it counts; fixes untyped source quality and per-worker fetch-knowledge loss.
- SourceProfile (`source_profile.v1`, docs/sources.jsonl, append-only latest-per-domain): domain, publisher, tier, fetch {blocked_direct, workarounds}, seen_count, tier_note. Tier enum T1_official … T6_other; workaround kinds mirror|archive_org|secondary_quote|pdf_local_extract|api. Fixed source_type→tier table (official_report→T1 … user_notes→T6) makes learning deterministic.
- Ingestor LEARNS per ingest (tier via table, blocked_direct from block-pattern log entries read defensively from either log version, fetch method from provenance); auto-learning only RAISES tiers; `docs source set` may lower only with a note (V-SRC-03). Workers receive a read-only REGISTRY prompt block (all T1 + facet-matched profiles); lawful public-access workarounds only.
- document.v2 = v1 + provenance {retrieved_at, fetch_method, tier, quoted_via}; quoted_via links secondary quotes to their fetched carrier.
- Triangulation (Stage B, V-SRC-04): spine fact/mechanism bindings need (a) ≥1 EU from T1/T2 + ≥1 from a distinct doc, OR (b) ≥2 EUs from distinct mutually-independent T3/T4 docs (publisher equality is the mechanical check); T5 press never carries a spine binding alone. Publisher defaults to domain for web docs; local docs are empty-publisher and an empty-publisher pair never triangulates (v2.1 D12/v2.1.1 D-c: `--publisher` is domain-keyed, cannot fix local pairs — re-ingest with a web origin).
- Rules V-SRC-01..05; V-SRC-04 enforced at freeze (extends V-FRZ-02) + reported by msa-check; V-SRC-05 is a dispatch-time excerpt-completeness check.

## 17-coverage-saturation.md — S4 ledger, saturation stop, role-profile floors (ADOPTED; SUPERSEDES r3 flat floor + docs cap)

- Intent: "enough" becomes a profile, "stop" becomes saturation (stop when searching stops producing, not when a counter hits N) — fixes both live-run stopping failures.
- Coverage ledger: DERIVED per fact/mechanism/bridge node (no new canonical writer; deterministic fold, V-COV-01): eu_counts by direction, distinct docs/publishers, tiers, angles, mandatory_angles, triangulated, rounds, new_docs_last_round, saturated, floor {required, met}. Via `docs coverage` + /api/coverage.
- Angle folding (v2.1 D6 + v2.1.1 D-a): from (i) TERMINAL wave members (attempted only), (ii) single-request v2 query_logs, (iii) REQUESTED-for-target documents mapped by tier (T1→official_stats, T2/T3→academic, T4→industry), (iv) the CoverageCritic report — authoritative per-angle verdict, only path to `productive` for a waved node. `counter` folds only from an executed/blocked counter qid, a terminal counter member, or the critic verdict — never from mere completion/cache/v1 results.
- mandatory_angles = official_stats, academic, counter (+industry via the market/firm-actor heuristic). saturated := rounds ≥ 2 AND every mandatory angle ∉ {no_attempt} AND new_docs_last_round = 0.
- Role-profile floors (replace the flat ≥2 rule): spine_fact/mechanism ≥2 EU, ≥2 docs, triangulated, counter ∉ {no_attempt}; bridge = spine + ≥3 docs; non-spine fact/mechanism ≥1 EU; definition/question/thesis none. MSA-4 / V-FRZ-02 / compiler missing_evidence all delegate here.
- Saturation replaces the docs cap: not saturated ⇒ needs_docs ALWAYS opens more search; saturated+floor-unmet ⇒ re-proof born dead {reason:"saturated", floor_met:false}; saturated+floor-MET ⇒ conflict: `human_review` CommitDecision action + born-dead trace floor_met:true, resumable via `queue requeue` (D1). ContextPack coverage block tells the worker search is exhausted (narrow or pass conditionally).
- Rules V-COV-01..05 (05: narrows inherit the parent ledger; rounds reset only if core_terms change by more than half — applied by the fold itself, D13).

## 18-semantic-retrieval.md — S5 hybrid keyword+embedding matching (ADOPTED; optional upgrade)

- Intent: fix keyword over-match (period tokens) and paraphrase/cross-lingual (CJK↔EN) under-match without surrendering determinism or auditability. Semantic is an UPGRADE, never a base dependency — degrades to keyword LOUDLY (V-SEM-03).
- Model pin: multilingual-e5-small ONNX, 384-dim, name+revision+weights_sha256 in db/semantic/model.json; fetched once, hash-verified, gitignored; onnxruntime fp32 CPU intra_op_num_threads=1 for byte-stable vectors; mean-pool + L2-normalize; e5 "query:"/"passage:" prefixes; deterministic 512-token truncation (v2.1 D9). Vectors in db/semantic/eu_vectors.parquet (derived/rebuildable).
- Hybrid scoring at pack build: score = 0.6·sscore + 0.4·kscore; include iff sscore ≥ τ=0.35 OR kscore ≥ 2 raw tokens, AND scope_compatible; order (score desc, id asc). α/τ are contract constants. pack = REQUESTED ∪ top-12 UNCHANGED — semantic feeds only the MATCHED half's score.
- Near-dup clustering: cosine ≥ 0.92, WITHIN one document only (across documents never — independent corroboration is triangulation signal); deterministic representative (longest can_cite_for, tie lowest id).
- Auditability: docs_pack.v2 retrieval block names matcher (hybrid.v1|keyword.v1), model pin, per-EU scores as fixed-6-decimal strings; verify recomputes when the model is present (drift = warning); keyword.v1 packs first-class.
- Hard limit (permanent r2.2 lesson): similarity NEVER auto-fulfills a DocsRequest; cache stays fingerprint-only; the one advisory use is top-3 similar-request leads in the dispatch prompt (V-SEM-04).
- Rules V-SEM-01..05; CLI `db semantic rebuild|check`, `docs search --semantic`; optional `[semantic]` extra (onnxruntime, numpy, pyarrow, tokenizers).

## Cross-doc themes

- Pipeline order: topic → scoping/contract accept (human) → layer-0 expansion → evidence-seeding sweep (V-SWEEP-01 gates expansion beyond layer 0) → BFS layer loop (expand → prove → validate → commit; bridges/docs sub-loops) → MSA green → spine freeze → compiler dry-run → draft map → prose → mechanical audit; trace + verify close the loop.
- Maker/checker separation everywhere: bounded LLM workers (ProofWorker, DocsWorker, CoverageCritic, CompileWorker) fill closed-enum forms or produce constrained artifacts; deterministic code computes every verdict (proof decision table, wave verdict, saturation, floors, gap kinds) and performs all bookkeeping. Workers never invent ids, verdicts, or numeric scores; chat text is never state.
- Single-writer ownership: exactly one producer per canonical artifact; the Committer is the only Logic Graph mutator (serial, input-scoped snapshot currency = the whole concurrency story); Claude agents write only agent_outputs/** and agent_notes/**, all canonical appends go through the CLI (corollary C1).
- JSONL is canonical and append-only (latest record per id; prefix-hash integrity, V-PATH-04); every derived store (DuckDB db/, semantic index, coverage ledger, commit_queue view) is rebuildable and never authoritative; canonical serialization + injectable clock/actor make everything byte-reproducible.
- Docs-as-single-source-of-truth doctrine: docs/ is the program; any code/doc divergence requires amending the doc in the same change; authority split — docs/08 boundaries, docs/09 rules, docs/10 v1 scope + closed CLI, docs/11 tests, docs/12 WebUI; archive/ superseded; adoption/supersession happen via dated docs/00 changelog entries paired with docs/11 worklists.
- Search program S1–S5 layering (all adopted): S1 deterministic accountable plans → S2 parallel angle waves + deterministic merger + read-only critic (≤2 rounds) → S3 source tiers/provenance/fetch recipes + triangulation → S4 derived coverage ledger + saturation stop + role-profile floors (supersedes flat caps/floors) → S5 hybrid semantic retrieval (optional, loud degrade, never auto-fulfills). Stage A fixed volume, Stage B stopping, Stage C recall.
- Anti-hallucination chain: citations only from DocsPacks; EUs declare their own can/cannot_cite_for boundaries; quotes verbatim-checked against archived text; prose annotated per sentence and mechanically audited; `trace` walks any sentence back to the raw source file.
