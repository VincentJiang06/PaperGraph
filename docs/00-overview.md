# 00 Overview

PaperGraph is a research framework that runs **under Claude Code**. It replaces "write the paper linearly" with "build the argument as a graph, prove every edge, then compile prose once at the end."

## Core Thesis

Literary narration and linear text ordering are destructive to argument construction. So PaperGraph:

1. Represents the paper's ideas as a **Logic Graph** — claims are nodes, argumentative moves are directed edges.
2. Expands and verifies the graph layer by layer (BFS-style), producing a parallelizable **proof queue**.
3. Resolves each edge atomically with a **Proof Machine** — a bounded worker fills a fixed check form along an evaluation ladder ("in scope? evidence sufficient? inference holds?"); code computes the verdict from the form via a published decision table.
4. Caches every literature lookup in a **Docs Database** (memoized search) so evidence is reused, not re-searched, and citations cannot be hallucinated.
5. Produces **no prose until the final Compiler step**. Everything before that is structure, verdicts, and evidence bindings.

PaperGraph is not an autonomous paper-writing agent and not a RAG chatbot. It makes an argument verifiable, evidence-bound, and auditable **before** any prose exists.

## Component Map

```text
Topic Input file ──► Scoping ──► ProjectContract (fixed question, scope, outcome direction)
                                      │
                                      ▼
                              Logic Graph  (nodes / edges / layered BFS frontier)
                                      │  emits ProofTasks
                                      ▼
                              Proof Machine  (parallel bounded workers fill check forms;
                                              code computes verdicts by decision table)
                                      │  may request evidence
                                      ▼
                              Docs Database  (documents, EvidenceUnits, memoized search)
                                      │  validated results
                                      ▼
                              Committer  (the ONLY graph mutator)  ──► queue update, bridges
                                      │
                                      ▼
                              Freeze ──► Compiler (dry-run → draft map → prose) ──► Audit

WebUI monitor: read-only view over all of the above, at every stage.
```

## Runtime Model

- **Claude Code is the host.** The main session acts as Orchestrator; ProofWorkers and DocsWorkers are Claude subagents given bounded task files.
- **Files are the state.** All canonical state is JSON/JSONL under `data/projects/<project_id>/`. Agent chat text is never state; only validated output files are.
- **Deterministic code does the gates.** A small Python package `paperproof` provides schema validation, queue operations, commit/freeze/compile logic, and the WebUI server. Claude does judgment; code does bookkeeping.
- No API key is required for proof work: the system writes task files, Claude workers read them and write output files.

## Reading Order

```text
00-overview.md                 this file
01-topic-and-scoping.md        topic input, parsing rules, PaperSpec, ProjectContract
02-logic-graph.md              node/edge schemas, lifecycle, BFS expansion, spine, MSA
03-proof-machine.md            proof tasks, evaluation ladder, decision table, worker protocol
04-docs-database.md            documents, evidence, memoized search, matcher algorithm
05-workflow-and-queue.md       pipeline order, queue state machine, gates, parallelism
06-compiler-and-audit.md       freeze, dry run, section plan, draft map, prose, audit
07-runtime-and-tooling.md      storage layout, ids, snapshots, CLI, subagent wiring, WebUI
08-module-contracts.md         BINDING boundary contracts between all modules
09-verification.md             shared text algorithms, V-* rule registry, pipeline checks
10-v1-design.md                the concrete first version: scope, stack, CLI contracts,
                               worker prompts, build order, demo
11-test-suite.md               the executable test plan: fixtures, fakes, meta-tests,
                               milestone gates
12-webui-spec.md               the WebUI design: shell, tokens, views, components

— search program (ADOPTED — see the changelog entries below) —
13-search-program.md           S1–S5 overview, composition, dependency, staging
14-search-planning.md          S1: deterministic SearchPlans + per-query accounting
15-search-orchestra.md         S2: parallel angle waves, merger, coverage critic
16-source-registry.md          S3: source tiers, fetch recipes, provenance, triangulation
17-coverage-saturation.md      S4: coverage ledger + saturation stop criterion
18-semantic-retrieval.md       S5: hybrid keyword+embedding matching, cross-lingual
```

Documents 01–07 describe modules; 08–12 bind them. On any boundary question (who writes what, what a gate accepts), `08-module-contracts.md` is authoritative. On any check, the rule IDs in `09-verification.md` are authoritative. On what v1 includes, `10-v1-design.md` is authoritative. On test structure, `11-test-suite.md` is authoritative. On WebUI design, `12-webui-spec.md` is authoritative (within the scope docs/10 §6 allows). Documents 13–18 are the **search program**: fully designed and adoption-staged; **all five sets (S1–S5) are now adopted and binding** (the changelog entries below; docs/13 §Normativity).

## Non-Negotiables

```text
1. JSON/JSONL files are canonical state; any DB or cache is derived and rebuildable.
2. Committer is the only module that mutates the Logic Graph.
3. Workers answer closed-enum check forms along the evaluation ladder; verdicts
   are computed by code from a published decision table. No numeric scores for
   academic judgment.
4. An edge with an inference gap gets at most 2 bridge-node proposals; workers
   never expand bridges recursively.
5. Docs produces evidence records only; it never sets proof verdicts or touches the graph.
6. No prose is generated before the Compiler stage; Compiler cannot create new claims or evidence.
7. Citations must resolve to a Document in the Docs Database. No invented citations.
8. Parallel workers must have disjoint output files; shared state changes go through gates.
```

## Naming

```text
Product name:      PaperGraph
Python package:    paperproof
CLI command:       paperproof
Source root:       src/paperproof/
Project data root: data/projects/<project_id>/
Example input:     examples/topic-input-p4.md
```

## Spec Revision r2 (2026-07-07)

This revision deepened every doc so a fresh implementation agent can execute without judgment calls. Normative changes an r1 reader must re-learn:

```text
Evaluation ladder + not_evaluated sentinel added to the check form (docs/03) —
  r1's form was unfillable for e.g. an out-of-scope fact node. Decision-table
  precedence changed: wellformed now outranks evidence; strength is uniformly
  "conditional iff assumptions non-empty" (nodes included).
Spine, MSA checklist items, lane completion (closing proposals), layer-0
  question/thesis seeding, and park/unpark are now mechanical (docs/02).
Lifecycle states change ONLY at commits; rejection cascades tombstone incident
  edges (state_reason=endpoint_rejected); queue gains a `cancelled` status.
CompileWorkers write agent_outputs/prose/ and `compiler ingest-prose` promotes
  to compiler/prose/ (r1 contradicted corollary C1). v1 Audit is fully
  mechanical; the semantic AuditWorker moved to v1.1.
CommitDecision, Tombstone, QueueEvent, verdict_record, DocsRequest-status
  schemas pinned (docs/08, 05, 03, 04); contract gains contract_version.
Matcher, request fingerprint cache, quote/paraphrase kinds, content_hash dedup
  pinned (docs/04). Shared text algorithms pinned (docs/09 §0).
CLI closed list extended: spec build --patch, graph park/unpark, queue
  expire/requeue; per-command contracts pinned (docs/10 §4).
docs/11-test-suite.md added: fixtures, FakeWorker API, 24 golden decision rows,
  hostile catalog, meta-tests, milestone gates.
```

## Spec Revision r2.1 (2026-07-07, correctness pass)

Two independent adversarial audits (an M0/M1 implementability walkthrough and a
step-by-step runtime simulation of S1/S2/S3/S7) were run against r2; every
confirmed finding was fixed. What an r2 reader must re-learn:

```text
Bridges are WIRED: the Committer creates bridge node X AND edge X→B (depends_on
  for definitions, supports otherwise), with lane/layer from the repaired
  edge's source; bridge rounds per edge capped at 2 (docs/08 B6).
MSA-9 added: the spine must contain ≥1 active fact/mechanism node — a cascade
  that hollows out the thesis's support now fails msa-check. Seed layers must
  connect seed chains to the thesis (demo adds EDGE-B-T).
Commit-gate currency is INPUT-SCOPED: proof commits check only target + 1-hop
  since the bundle snapshot (parallel proofs never invalidate each other);
  expansions check the whole graph; V-COMMIT-06 cancels in-flight items on
  tombstoned targets (docs/05, 08, 09).
V-PATH-04 is now the PREFIX rule: JSONL files must hash-match on their
  claim-time first-N bytes (append-only ⇒ concurrent engines can't trip it).
Caps dead-letter via a born-dead item: (created)→dead, op=dead_letter (docs
  cap and bridge cap). `queue fail` got legal edges; validated→stale/cancelled
  edges added; stale is proof-item-only.
Prose items: `compiler ingest-prose --work-item` = validate_pass + commit in
  one command. Docs items: request fields embedded in the prompt (no request
  file); `docs request` CLI added for Orchestrator-initiated requests;
  DRES- resolves via ingested_from stamps.
Edges: claim_version added (narrows work on edges); lane+layer inherited from
  the source node; id scheme carries -dep/-ref type markers; refutes edges may
  only target alternatives in v1 [V-EDGE-04].
Dry runs after a clean spine freeze report zero gaps BY CONSTRUCTION (docs/06
  reachability note) — the gap machinery is for unfreeze cycles and v1.1.
state_detail field added; stopword list frozen verbatim; CJK sentence
  splitting fixed; BFS-ALT's first layer is 1; spec build --patch shape pinned;
  milestone gates re-sequenced so no scenario needs later-milestone modules.
```

## Spec Revision r3 (2026-07-08, from the ai-jobs live run)

The first real end-to-end run (project `ai-jobs`, "AI agents & employment
2020–2025", real Claude workers) exposed defects that made unattended operation
impractical and left the evidence base an order of magnitude too thin. Every r3
change below is grounded in that run's event log (`queue/events.jsonl`,
QE- ids) and requires the implementation + test suite to catch up
(worklist: docs/11 §10). r2.2 (shipped mid-run) already fixed the WebUI
nav/fetch bugs and removed the matcher-hit cache trigger.

```text
EVIDENCE VOLUME (the run's core failure — 24 EUs for a whole paper):
  Evidence Seeding sweep added as a pipeline stage (docs/01, 04, 05): after
    contract acceptance, ingest Known Sources + parallel DocsWorkers over
    (seed claim × angle: official_stats/academic/industry/counter);
    V-SWEEP-01 floor gates expansion beyond layer 0.
  DocsWorker coverage expectations pinned (docs/04, 08 B7, 10 §5): 2–5 docs,
    4–10 EUs per request; disconfirming duty; 403/PDF fetch resilience.
  Evidence floor raised: MSA-4 / V-FRZ-02 / missing_evidence now require ≥2
    EUs from ≥2 distinct documents per spine fact/mechanism node — the run's
    single-source claims were exactly the ones later evidence overturned.

V-PATH-04 (5 of the run's 8 validation failures — QE-000048/51/64/101/104):
  The r2 impl's "committer-owned byte-identity" + all-dirs new-file baseline
  are ruled non-conformant; the scan is exactly three clauses (docs/05):
  JSONL prefix intact, recorded IMMUTABLE files byte-identical (db/** never
  manifested), new files only fail in strict dirs (specs/ graph/ queue/
  commit/ freeze/ audit/). Appends are attributed by verify (V-COMMIT-04),
  not the scan — hostile H10 re-mapped accordingly (docs/11 §6).

DOCS CAP (QE-000114 dead-lettered a healthy target):
  Cap counts needs_docs VERDICTS (3rd, with no new evidence since the 2nd),
  scoped to PR-initiated requests only — sweep/Orchestrator `docs request`
  never counts (docs/04, 08 B7).

FRESH EVIDENCE MUST REACH PENDING PROOFS (the 10-EU-stale-pack incident):
  Evidence-arrival staleness [V-TASK-04]: the docs ingestor marks affected
  queued/blocked proof items stale. DocsPack composition [V-TASK-05] =
  REQUESTED ∪ top-12 MATCHED — requested evidence lands in the target's pack
  unconditionally; the K-cap ends the all-24-EUs-in-every-pack bloat.

CACHE HYGIENE: only DRES-fulfilled requests are fingerprint-cache sources —
  a false "cache" fulfillment can no longer chain (docs/04).

BRIDGE REJECTION defined (docs/02, 08 B6): cascade normally; the repaired
  edge's re-proof re-judges with surviving premises (cancelled blockers count
  as resolved); renewed gap hits the bridge-round cap; prefer narrowing.

OPERATOR ERGONOMICS: `validate` completes claimed items implicitly (shrinks
  the manifest window, one less ceremony step); every failed_rules entry
  carries per-rule detail naming the offending path (bare rule ids proved
  undiagnosable); `ui serve --auto-rebuild` for live monitoring (banner
  default unchanged); worker prompt templates gain a SELF-CHECK block
  (arrays! word counts!) — the run's V-PR-01/V-PR-10 slips (QE-000017/89).
```

## Search Program Adoption (2026-07-08, Stage A)

The design-frozen search program (docs 13–18) is adopted in stages; this is the
first adoption entry, so the referenced sets are now **binding** (docs/13
§Normativity). Later documents stay design-frozen until their own entry lands.

```text
ADOPTED — S1 (docs/14) search planning: deterministic SearchPlans + per-query
  accounting (search_plan.v1; docs_result.v2 query_log).

ADOPTED — S3 Stage A-lite (docs/16) source registry, tiers & provenance:
  source_profile.v1 (docs/sources.jsonl, append-only latest-per-domain) and
  document.v2 (= document.v1 + a provenance block; v1 stays readable). The Docs
  ingestor LEARNS a SourceProfile per web domain on every ingest — tier from the
  fixed source_type→tier table (docs/16), blocked_direct from the search/query
  log's blocked notes (read defensively from whichever log the docs-result
  carries), fetch method from provenance. `docs source list|set` (a subgroup of
  the existing `docs` group) curates tiers/workarounds; the DocsWorker prompt
  gains a read-only REGISTRY block (lawful public-access workarounds only). New
  rules V-SRC-01/02/03/05 (provenance present; secondary_quote carrier exists;
  registry appends with no silent tier-lowering; dispatch-excerpt completeness).

NOT ADOPTED — S3 Stage B triangulation (V-SRC-04), S4 (docs/17), S5 (docs/18)
  remain design-frozen. V-SRC-04 and the docs/16 triangulation section are
  informational until a later adoption entry.
```

## Search Program Adoption — S2 Search Orchestra (2026-07-08)

Adopts S2 (docs/15) as **binding**, completing Stage A (v1.1). S2 turns a single
DocsRequest into a **wave**: parallel per-angle members (each executing its S1
plan), a deterministic merger, and a fresh adversarial coverage critic whose
closed form drives ≤2 bounded follow-up rounds — the multi-modal-sweep +
completeness-critic pattern applied to evidence.

```text
S2 becomes NORMATIVE (docs/15 status → binding):
  Schemas   search_wave.v1, coverage_report.v1 (new); docs_request.v1 gains a
            `fan` flag (r3 sweep requests default fan=true).
  Engine    wave(DR) fans one member per angle {official_stats, academic,
            industry, counter} (news only when the claim period touches the last
            18 months); each member = a docs_queue item + an angle-specific S1
            plan + a distinct output. Merger (code, deterministic): dedup by
            content_hash then canonical URL (frozen tracking-param strip), drop
            dup EUs, emit ONE merged docs_result.v2 at docs/merged/; only the
            merged result is ingested (one DRES per wave).
  Critic    a fresh, adversarial, read-only coverage worker fills a closed form
            (angle_covered/primary_source_present/disconfirming_captured); CODE
            computes the wave verdict (sufficient | followup | closed), R_MAX=2.
  Rules     V-WAVE-01..05 join the registry (docs/09 §V-WAVE).
  CLI       `docs wave --request <DR-id> [--fan]` on the existing `docs` group;
            queue list shows wave grouping.
  Storage   docs/waves.jsonl, docs/merged/.
  Tests     docs/11 §12 carries T-S2-1..4.

Stage A (S1 + S3-lite + S2) then COMPLETE. Still design-frozen: S4 (docs/17,
v1.2 — SUPERSEDES the r3 flat floor + docs cap) and S5 (docs/18, v2 — needs a
vendored embedding model) remain future, pending their own adoption entries.
```

## Search Program Adoption — S4 Coverage & Saturation + S3 Triangulation (2026-07-08, Stage B / v1.2)

Adopts S4 (docs/17) AND S3 Stage B triangulation (docs/16 V-SRC-04) as **binding** —
Stage B (v1.2), which fixes STOPPING (the run's docs cap dead-lettered a healthy target
while thin claims froze). Per docs/17 §Deltas this entry EXPLICITLY SUPERSEDES two r3/m5 rules:

```text
SUPERSEDED (replaced, not extended):
  * the r3 flat "docs round-trip cap" (docs/04) -> SATURATION. A needs_docs verdict on a
    target ALWAYS opens more search while NOT saturated; a saturated+floor-unmet target is
    born-dead reason=saturated. No count-based refusal remains (committer/apply.py cap gone).
  * the r3/m5 flat ">=2 EU / >=2 docs" floor (MSA-4, V-FRZ-02, compiler missing_evidence)
    -> ROLE-PROFILE floors (docs/17): spine_fact/mechanism >=2 EU, >=2 docs, TRIANGULATED
    (S3 V-SRC-04), counter angle not no_attempt; bridge = spine_fact + >=3 docs; non-spine
    fact/mechanism >=1 EU; definition/question/thesis no floor.

S4 becomes NORMATIVE (docs/17):
  Ledger    DERIVED per-node coverage ledger (eu_counts, distinct_docs/publishers, tiers,
            angles folded from S1 query_logs + S2 waves, rounds, new_docs_last_round,
            saturated, floor). `docs coverage [--node]` + /api/coverage. No new canonical
            writer -- a deterministic fold over existing records [V-COV-01].
  Saturated rounds>=2 AND every mandatory angle not no_attempt AND new_docs_last_round=0.
  Floors    MSA-4 / V-FRZ-02 delegate to the role-profile table; msa-check prints the
            per-node ledger line for every miss [V-COV-04].
  Rules     V-COV-01..05 join the registry (docs/09 §V-COV).
  CLI       `docs coverage [--node]`; /api/coverage; msa-check output extended.
  Schemas   none canonical (ledger derived); context_pack.v1 gains a coverage block [V-COV-02].

S3 Stage B (docs/16 V-SRC-04) becomes NORMATIVE: a spine fact/mechanism binding must satisfy
  (a) >=1 EU from a T1/T2 doc + >=1 more from a distinct doc, OR (b) >=2 EUs from distinct,
  mutually-independent T3/T4 docs (different publishers). T5 press never carries a spine binding
  alone. Enforced at freeze (extends V-FRZ-02), reported by msa-check.

Still design-frozen: S5 (docs/18, v2 -- hybrid embedding retrieval, needs a vendored offline
model) is the final set, adopted next.
```

## Search Program Adoption — S5 Semantic Retrieval (2026-07-08, Stage C / v2) — COMPLETES the program

Adopts S5 (docs/18) as **binding** — the final set. Hybrid keyword+embedding retrieval with
cross-lingual (CJK<->EN) recall. Semantic is an UPGRADE, not a base dependency: the code
degrades to keyword matching LOUDLY when the model/deps are absent (V-SEM-03).

```text
S5 becomes NORMATIVE (docs/18):
  Model     multilingual-e5-small (384-dim), run via onnxruntime (deterministic fp32 CPU,
            NO torch). Pinned in db/semantic/model.json (name, revision, weights_sha256);
            fetched-once into gitignored db/semantic/ + hash-verified (NOT committed --
            sidesteps GitHub 100MB). Embedding = mean-pool(last_hidden_state, attention_mask)
            then L2-normalize; e5 "query:"/"passage:" prefixes. (Probe-validated: ZH<->EN
            cos 0.88 > unrelated 0.74; byte-identical re-embed.)
  Hybrid    score = 0.6*sscore + 0.4*kscore; include iff sscore>=0.35 OR kscore>=2-tokens;
            order (score desc, id asc); pack = REQUESTED U top-12 (r3 rule UNCHANGED --
            semantic feeds the MATCHED half only). tau=0.35, alpha=0.6 are contract constants.
  Cluster   near-dup EUs (cosine>=0.92) cluster ONLY within a document; representative
            deterministic (longest can_cite_for, tie=lowest id) [V-SEM-05].
  Deps      OPTIONAL extra `semantic` = onnxruntime,numpy,pyarrow,tokenizers (pyproject).
            db/semantic/eu_vectors.parquet is derived/rebuildable like all db/.
  No-auto   similarity NEVER auto-fulfills a DocsRequest (cache stays fingerprint-only);
            advisory top-3-similar leads are prompt-only [V-SEM-04].
  Rules     V-SEM-01..05 join the registry (docs/09 §V-SEM).
  CLI       `db semantic rebuild|check`; `docs search --semantic`.
  Schemas   docs_pack.v2 (retrieval block: matcher, model, alpha/tau, per-EU scores as
            fixed-6-decimal strings for byte-determinism); docs_pack.v1 stays readable.

After S5, the SEARCH PROGRAM (S1-S5) is fully adopted and implemented -- v2 complete.
```

## Spec Revision v2.1 (2026-07-08, post-adoption consistency + live-run readiness)

With S1–S5 all adopted (the four entries above), four adversarial reviews audited
the whole v2 project end-to-end. v2.1 is the consistency + live-run-readiness
pass: it reconciles the surfaces the staged adoptions left inconsistent, drives
the S2 wave from the CLI as a closed surface, and fixes the defects a real run
hits first. Every change is pinned; the spec and the code move together. What a
v2 reader must re-learn:

```text
SATURATION HUMAN-REVIEW BRANCH (D1): a saturated + floor-MET needs_docs is a
  worker/floor CONFLICT, not a dead search. The Committer records a CommitDecision
  action `human_review` (this action JOINS the closed CommitAction enum) AND
  enqueues the re-proof item born dead — (created)→dead, op=dead_letter, detail
  {reason:"saturated", floor_met:true} — so humans get a queue trace and
  `queue requeue` resumes after review. V-COV-03 reworded: born-dead reason is
  ALWAYS `saturated`; detail.floor_met distinguishes the conflict case (worker
  said insufficient though the floor is met).

WAVE DRIVING IS A CLOSED CLI SURFACE (D2): `docs ingest-result` REFUSES a
  wave-member item (a clear error naming the right command). New commands:
  `docs wave-member <output_file> --work-item <WI>` (validates the member against
  ITS angle plan — plan resolved from the item's task_id
  SP-DR-x-<angle>[-rN-...] — implicit-completes from claimed, then
  wave.complete_member; when ALL members are terminal the engine AUTO-runs merge +
  open_critic, doc-faithful to docs/15 "runs when every member is terminal") and
  `docs wave-resolve <coverage_report_file> --work-item <WI>` (V-WAVE-03 validate,
  implicit-complete, resolve_critic; code computes the verdict). A `followup`
  verdict whose follow-up spec list is EMPTY closes the wave immediately (no idle
  round).

CRITIC WORKER (D3): the CoverageCritic is a contracted bounded worker on
  `critic_queue` (WorkItem target_type=`wave`), output agent_outputs/coverage_reports/;
  its canonical dispatch template joins docs/10 §5 (templates stay the ONLY
  dispatch prompts). prompts/critic_worker.txt ships the identical text.

PIPELINE ORDER FIXED (D4): contract accept → LAYER-0 EXPANSION → evidence-seeding
  sweep → proof loop. Sweep targets are layer-0 nodes and `docs request --target`
  requires the node to exist, so the old "sweep before expander" diagram was
  wrong. V-SWEEP-01 still gates the first expansion BEYOND layer 0.

ONE SWEEP MECHANISM (D5): sweep = one DocsRequest per fact/mechanism layer-0 node
  (`docs request --target N --need ... --hint ... --fan`) then `docs wave --request
  DR-x --fan` (the wave provides the 4-angle coverage). `docs request` gains a
  `--fan` flag (records fan=true; sweep uses it). The old per-(seed×angle)
  single-request procedure (docs/04) is replaced.

ANGLE FOLDING (D6, fixes the reactive-saturation livelock + the counter
  over-report): the coverage ledger folds `angles` from (i) TERMINAL wave members
  (angle marked ATTEMPTED only), (ii) single-request v2 query_logs, (iii) archived
  documents REQUESTED-for-the-target by tier (T1→official_stats, T2/T3→academic,
  T4→industry), and (iv) the wave's CoverageCritic report — the AUTHORITATIVE
  per-angle verdict, the only path to `productive` for a waved node (docs/17);
  `counter` folds ONLY from an executed-or-blocked counter qid in a
  v2 query_log — never from mere request completion, never from cache fulfillments
  or v1 results. `academic` is now attemptable on the single-request path
  (saturation reachable) and counter is honest.

MERGER QUOTE-INTEGRITY (D7): dedup by content_hash; a canonical-URL collision with
  DIFFERING content_hash keeps BOTH documents (re-pointing EUs across differing
  texts broke V-DR-05). canonical_url is TOTAL (unparseable port → raw netloc
  fallback), strips `www.`, defaults a scheme — consistent with the registry's
  domain normalization.

FOLLOW-UP MEMBER PLANS (D8): a round>1 member's plan id/file is round+origin-
  discriminated (like its output path), compiled WITH the critic's suggested_query
  as a hint — round 2 must not re-execute a byte-identical round-1 plan. Duplicate
  expected_source names are de-duplicated/indexed so origins (and thus paths/plans)
  stay unique.

SEMANTIC TRUNCATION (D9): embedding input is deterministically truncated at 512
  model tokens (tokenizer-enforced); pinned in docs/18 as part of the embedding
  contract.

scope_compatible DASH-NORMALIZATION (D10): docs/09 §0 `scope_compatible` period
  parsing normalizes Unicode dashes (en/em/fullwidth ~) to ASCII "-" before
  year-range parsing (the live topic's "2020–2025" en dash made ASCII "2020-2025"
  proposals fail V-NODE-03).

PROMPT RENDERING + V-SRC-05 ENFORCEMENT (D11): new CLI `docs render-prompt
  --work-item <WI>` (docs items incl. wave members and critic items) and `proof
  render-prompt --work-item <WI>` emit the fully-filled canonical template (plan
  embedded; `{registry}` = the V-SRC-05 excerpt via the registry renderer, checked
  by check_registry_excerpt at render time; S5 advisory top-3 similar-request leads
  included here — prompt-only). This is WHERE V-SRC-05 is enforced.

PUBLISHER INDEPENDENCE (D12): a SourceProfile's publisher defaults to its domain
  for web documents; local (user_provided) documents have empty publisher, and an
  empty-publisher PAIR is NOT mutually independent for V-SRC-04(b) unless a human
  curates publishers via `docs source set` — two uncurated local uploads can no
  longer triangulate a spine claim.

V-COV-05 WIRING (D13): the ledger's rounds/new-docs fold applies the narrow-reset
  rule (rounds reset to 0 when the narrowed claim's core_terms change by more than
  half) — the canonical rule fn is consulted by the fold itself.

COMPILER ingest-prose (D14): performs the implicit complete from claimed/running
  (like `validate result` / `docs ingest-result`) and accepts absolute paths
  (normalized to project-relative). Prose items JOIN the r3 implicit-complete list
  everywhere it is described.

VERIFY COVERAGE (D15): `verify` sweeps V-WAVE-04/05 in addition to 01/02;
  V-TASK-02/03 are checked at bundle build; V-SRC-04 at freeze uses the single
  canonical triangulation fn.

SUPERSESSION LEFTOVERS CLEANED: every place that still described the r3 flat docs
  cap / flat ≥2 floor as live (docs/02 MSA-4, docs/04 cap section, docs/05
  born-dead row, docs/06, docs/08 B6/B7/B8) now delegates to the docs/17
  role-profile floors + saturation. Adoption status made consistent across
  docs/00, docs/13, docs/10, docs/11, docs/14, README, AGENTS, CLAUDE.md — all
  five sets (S1–S5) are ADOPTED.
```
