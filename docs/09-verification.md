# 09 Verification

How every module is checked. Three layers:

```text
1. Validation rules  — deterministic runtime checks at every boundary (the V-* registry).
2. Module tests      — unit/contract tests each module must ship with (executable
                       plan: docs/11-test-suite.md).
3. Pipeline checks   — integration scenarios + a global invariant sweep.
```

No LLM participates in any check in this document. Verification is code.

## 0. Shared Text Algorithms

Several rule families need text measurements. These are pinned once, implemented once (`src/paperproof/textutil.py`), and every rule cites them — an implementation may not improvise its own tokenizer.

```text
normalize(s)      NFC → collapse every whitespace run to one space → strip.
casefold(s)       normalize(s) → Unicode casefold.
is_cjk(ch)        codepoint ∈ CJK Unified Ideographs U+4E00–9FFF, Extension A
                  U+3400–4DBF, Hiragana/Katakana U+3040–30FF, or Hangul
                  Syllables U+AC00–D7AF.
tokens(s)         casefold(s) split on non-alphanumeric boundaries; every
                  is_cjk character is its own token; empty tokens dropped.
word_count(s)     count of tokens(s) — a CJK character counts as one word.
sentence_split(s) ASCII terminators . ! ? split when followed by whitespace or
                  EOL; CJK terminators 。 ！ ？ split ALWAYS (CJK prose has no
                  space after them); trailing fragment counts if non-empty.
sentence_count(s) len(sentence_split(s)).
contains(hay, ndl)  casefold(ndl) is a substring of casefold(hay).
quote_match(text, q)  normalize with case PRESERVED; q must be a substring of
                  text after both are whitespace-normalized. (V-DR-05)
scope_compatible(a, b)  for every key present in BOTH objects:
                  period — compatible iff the year-ranges intersect (parse
                  "YYYY" and "YYYY-YYYY"; unparseable ⇒ substring test either
                  direction); region — equal after casefold; actors/mechanisms —
                  non-empty intersection after casefold() of each element.
                  Missing keys never conflict.
stopwords         the frozen list, exactly: a an the and or but if then else
                  when while of at by for with about against between into
                  through during before after above below to from up down in
                  out on off over under again once here there all any both
                  each few more most other some such no nor not only same so
                  than too very can will just is are was were be been being
                  have has had do does did that this these those it its as
                  (82 words; changing it is a spec change).
```

## 1. Validation Rule Registry

Rules are the runtime contract enforcement referenced from `docs/08`. Every rule has a stable ID (error messages, failed_rules, dead letters, and tests all cite these IDs). Prefix = boundary.

### V-SPEC (topic input & scoping)

```text
V-SPEC-01  all 9 required topic sections present, unique, non-empty (parsing
           rules P1–P7, docs/01)
V-SPEC-02  paper_type ∈ supported pattern enum (v1 build additionally requires
           single_event_mechanism — others exit 1 "pattern not implemented")
V-SPEC-03  bfs_plan is a DAG (no cycles, all depends_on ids exist)
V-SPEC-04  hard_exclusions and forbidden_claims are non-empty lists
V-SPEC-05  3–10 seed claims; each ≤ 2 sentences (sentence_count, §0)
```

### V-GATE (global gates)

```text
V-GATE-01  no expansion/proof/dispatch while latest contract accepted_by_user=false
V-GATE-02  every mutation gate call carries a based_on_snapshot that is current
V-GATE-03  no operation may target a frozen record except unfreeze (human) and
           compile/audit (read)
```

### V-SWEEP (evidence seeding, r3 — docs/04)

```text
V-SWEEP-01  the first expansion beyond layer 0 requires, for every
            fact/mechanism seed claim: >=2 EvidenceUnits from >=2 distinct
            documents, or recorded not_found for >=2 sweep angles.
            (`expand ingest` enforces; msa-check reports informationally.)
            Operationalization (r3): a "fact/mechanism seed claim" is a
            layer-0 fact/mechanism node; REQUESTED-for-N is traced
            request→DRES→ingested_from (docs/04).
```

### V-PATH (file/path safety, applies to every worker output)

```text
V-PATH-01  output path exactly matches the work item's declared output_files
V-PATH-02  path is project-relative, no upward traversal, no symlink escape
V-PATH-03  file is valid UTF-8 JSON (or .md for prose), single document
V-PATH-04  no writes outside allowed_write_paths — exactly the three clauses of
           docs/05 §Parallelism (r3): (a) JSONL prefix intact (rewrite/truncate
           fails; appends never inspected here — attribution is verify's job),
           (b) recorded IMMUTABLE non-JSONL files byte-identical (db/** never
           in the manifest), (c) new files only in strict dirs fail (specs/
           graph/ queue/ commit/ freeze/ audit/). Failure detail names the
           offending path. The r2 impl's committer-owned byte-identity and
           all-dirs new-file baseline are non-conformant (live-run events
           QE-000048/51/64/101/104).
```

### V-NODE / V-EDGE / V-GRAPH (graph records, checked at commit time)

```text
V-NODE-01  schema fields complete; enums valid; unknown fields rejected
V-NODE-02  claim is 1–2 sentences (sentence_count, §0), single proposition —
           static heuristic: reject iff contains(claim, p) for any p in the
           frozen phrase list ["; and", "and therefore", "which means"];
           best-effort by design (false positives are re-worded, semantic
           compounds are the worker's wellformed_check)
V-NODE-03  node scope is scope_compatible (§0) with the contract scope
V-NODE-04  parents exist and are not rejected
V-EDGE-01  schema/enums valid; source and target exist; source ≠ target
V-EDGE-02  edge_claim states a relation, not a verbatim restatement of either
           endpoint claim (static check: edge_claim ≠ either claim under casefold)
V-EDGE-03  no duplicate (source, target, edge_type) among non-rejected edges
           (recreation after rejection gets a -vN id, docs/07)
V-EDGE-04  edge_type=refutes ⇒ target node_type=alternative (v1 restriction,
           docs/02)
V-GRAPH-01 no supports/depends_on cycles among non-rejected edges
V-GRAPH-02 every non-seed node reachable from some layer-0 node via parents
           or edges
V-GRAPH-03 strength=strong|conditional iff lifecycle_state=active; frozen=true
           only on active records; every strength/state change has a CommitDecision
```

### V-EXP (expansion proposals)

```text
V-EXP-01  lane's previous layer fully committed — no proof item with status
          ∉ {committed, cancelled} targets a record of that lane's frontier
          layer (dead letters block, consistent with MSA-6; an edge belongs
          to its source node's lane, docs/02)
V-EXP-02  based_on_snapshot current
V-EXP-03  ≤12 nodes; layer = lane frontier layer + 1, single layer — for a
          lane with no nodes yet, the first layer is 0 for BFS-MAIN and 1 for
          every other lane (V-EXP-06 reserves layer 0); an empty proposal
          (nodes=[] and edges=[]) is the legal lane-closing form and carries
          the layer it would otherwise have expanded
V-EXP-04  edge refs resolve (existing id or "#index" within proposal)
V-EXP-05  every proposed node passes V-NODE-02/03 statically
V-EXP-06  the first BFS-MAIN proposal (layer 0) contains exactly one question
          node, one thesis node, and a thesis→question supports edge; no other
          proposal in any lane contains question or thesis nodes
V-EXP-07  a lane's first proposal requires all its depends_on lanes complete
```

### V-TASK (task bundles)

```text
V-TASK-01  claim refuses items marked stale (Committer marks on target/1-hop
           mutation, docs/08 B4) until rebuilt with a -rN revision
V-TASK-02  ContextPack contains target + all 1-hop neighbors at its snapshot +
           claim_digest covering every non-rejected node
V-TASK-03  DocsPack evidence ids all resolve to archived Documents
V-TASK-04  (r3) evidence-arrival staleness: after a docs ingest, every
           queued/blocked proof item whose pack composition would change
           (docs/04) is marked stale — a re-proof may never run against a
           pack older than the evidence gathered for it
V-TASK-05  (r3) DocsPack composition = REQUESTED ∪ top-12 MATCHED (docs/04);
           REQUESTED evidence for the target is present unconditionally
```

### V-PR (proof check forms) — the most important block

The worker submits a check form along the evaluation ladder; the verdict is computed by code (docs/03 decision table). V-PR validates the form; V-PR-12 validates the computation.

```text
V-PR-01  schema valid; all form answers ∈ their closed enums; unknown fields rejected
V-PR-02  task_id matches the claimed work item; target matches the ProofTask target
V-PR-03  no verdict field; no numeric-valued JSON fields; no id-valued fields
         beyond the schema's own (task_id, target_id, duplicate_of,
         evidence/docs ids) — the worker never invents an id
V-PR-04  inference_check field present iff task_type=EDGE_CHECK; all other form
         fields always present
V-PR-05  fact/mechanism NODE targets: evidence_check ≠ not_required (rule applies
         only when Stage C was evaluated)
V-PR-06  every evidence_used id ∈ the task's DocsPack
V-PR-07  conditional attachments exactly as required (docs/03):
         sufficient|contradicting ⇒ evidence_used ≥1; insufficient ⇒ docs_requests
         ≥1; gap ⇒ 1–2 bridge repairs; too_broad|compound ⇒ exactly 1 narrow
         repair; unevaluated stages ⇒ their attachments empty/null
V-PR-08  duplicate_check.duplicate=true ⇒ duplicate_of ∈ ContextPack ids
         (neighbors ∪ claim_digest), ≠ target_id
V-PR-09  repair_proposals: bridge = {kind, claim, node_type} only (node_type ∉
         {question, thesis}); narrow = {kind, narrowed_claim} only — no ids,
         no edges, no nesting
V-PR-10  notes ≤ 150 words (word_count, §0); no EU-/DOC- id token anywhere in
         the result outside evidence_used unless it ∈ evidence_used ∪ DocsPack
         (regex \b(EU|DOC)-[0-9]+\b)
V-PR-11  narrowed_claim passes V-NODE-02 statically
V-PR-12  the recorded verdict equals the decision-table output for the form
         (recomputed on verify; any mismatch is corruption, exit 3)
V-PR-13  computed verdict = pass ⇒ language_limits.allowed AND .forbidden
         non-empty; otherwise language_limits = null
V-PR-14  ladder shape: each of wellformed/evidence/inference is not_evaluated
         IFF an earlier stage stopped the ladder (docs/03 stage rules) — no
         gratuitous not_evaluated, no answers past a stop
V-PR-15  EDGE_CHECK: assumptions non-empty iff inference_check=
         holds_only_with_assumptions; NODE_CHECK: assumptions empty unless
         evidence_check ∈ {not_required, sufficient}
```

### V-DR (docs results)

```text
V-DR-01  schema valid; every evidence_unit carries exactly one of doc_ref
         (index within this result) or doc_id (existing archived id), and it
         resolves
V-DR-02  every evidence_unit has non-empty can_cite_for AND cannot_cite_for
V-DR-03  no verdict/strength/lifecycle fields anywhere; no DOC-/EU-/DRES- id
         fields authored by the worker (ingestor assigns)
V-DR-04  every document has source_type ∈ enum and an origin (path or url);
         web documents include inline text
V-DR-05  kind=quote ⇒ quote_or_paraphrase passes quote_match (§0) against the
         archived text (checked at ingest, when text exists)
V-DR-06  not_found=true ⇒ documents=[] and evidence_units=[]; the search record
         is non-empty — search_log (docs_result.v1) or query_log (docs_result.v2)
```

### V-SP (search planning — S1, docs/14; checked on docs_result.v2 at the docs validate path)

```text
V-SP-01  every plan qid appears exactly once in query_log; executed=false only
         with outcome=blocked + a non-empty note
V-SP-02  the plan's counter query was executed or blocked — never skipped
V-SP-03  docs_taken ≤ urls_seen per query_log entry; |documents| > 0 requires
         ≥1 productive entry
V-SP-04  not_found=true requires every entry executed|blocked and 0 productive
V-SP-05  the plan file referenced by the result exists and matches request_id
```

### V-COMMIT

```text
V-COMMIT-01  input-scoped currency (docs/05 §Commit Gate): proof_verdict ⇒
             target + 1-hop neighborhood unchanged since the verdict's bundle
             snapshot; expansion ⇒ based_on_snapshot current for the whole
             graph; administrative ⇒ trivially current (reads under lock)
V-COMMIT-02  input artifact passed validation: proof ⇒ a verdict record exists
             for it; expansion ⇒ `expand ingest` validated it in-process this
             invocation; administrative ⇒ preconditions checked in-process
V-COMMIT-03  no target in the mutation set is frozen
V-COMMIT-04  the CommitDecision lists every append; replaying actions against
             the pre-snapshot reproduces the post-snapshot (checked in tests)
V-COMMIT-05  post-commit graph passes V-GRAPH-01..03
V-COMMIT-06  a proof verdict commits only onto a target in a provable state
             (pending_proof | needs_repair | needs_docs); a target tombstoned
             while the item was in flight ⇒ no-op commit, item → cancelled
```

### V-FRZ / V-CDR / V-PROSE / V-AUD

```text
V-FRZ-01   every record in the closure is active
V-FRZ-02   every fact/mechanism node in the closure has ≥2 evidence bindings
           drawn from ≥2 distinct documents (r3 — one source per empirical
           claim proved too thin in the live run; single-source spine claims
           were the ones the later evidence overturned)
V-FRZ-03   no work item with status ∉ {committed, cancelled} touches the closure
V-FRZ-04   spine_freeze ⇒ MSA checklist passes and `verify` exits 0
V-CDR-01   gap identity (kind, target_id): each new gap spawns exactly one
           compile_queue item; re-run deduplicates and cancels resolved gaps
V-CDR-02   dry run appends nothing to graph/ or docs/
V-CDR-03   section_plan covers every spine node exactly once
V-PROSE-01 every (claim: NODE-x) annotation resolves to a DraftMap claim
V-PROSE-02 every (cite: EU-x) ∈ the DraftMap bindings of a node annotated in
           the same sentence
V-PROSE-03 no forbidden_language string of the section appears in its prose
           (contains, §0)
V-PROSE-04 every DraftMap claim of the section is annotated ≥1 time
V-AUD-01   audit findings carry kind + location + target_id (routable)
V-AUD-02   audit writes only audit/; prose files untouched (hash check)
```

### V-Q (queue engine)

```text
V-Q-01  status transitions only along the table in docs/05 (11-state enum incl.
        cancelled; no edges out of committed/cancelled)
V-Q-02  claim is atomic: a work item never has two live leases
V-Q-03  every status change has exactly one QueueEvent (heartbeat may repeat
        running→running)
V-Q-04  blocked_by ids exist; an item is claimable only when its blockers are
        resolved AND (EDGE_CHECK) both endpoints are active
V-Q-05  expired lease ⇒ requeue with attempt+1; attempt >3 ⇒ dead
```

## 2. Module Test Matrix (summary)

Each module ships with contract tests; the executable plan — file layout, fixture catalog, FakeWorker API, meta-tests, milestone gates — is `docs/11-test-suite.md`. The non-negotiable minimums:

| Module | Must-have tests |
| --- | --- |
| Schemas | round-trip every schema_version; unknown-field rejection; enum rejection |
| JSONL store | append-only (no rewrite); latest-by-id; path traversal rejected; concurrent append safety |
| Scoping | golden topic file → expected PaperSpec/Contract (byte-exact under the determinism harness); each V-SPEC rule has a failing fixture |
| Queue | full lifecycle walk; every V-Q rule violated by a scenario; crash-recovery (kill between claim and event) |
| Task builder | bundle self-containment; staleness invalidation; -rN revision immutability |
| Validator | one passing + ≥1 failing fixture **per V-PR and V-DR rule** — the largest fixture set in the project |
| Committer | verdict→action: one golden test per row of the docs/08 B6 table + each B6b kind; determinism (same input+snapshot twice ⇒ byte-identical decisions); stale snapshot refusal; frozen target refusal; rejection cascade |
| Decision table | one golden form per reachable row (the 24-row enumeration, docs/11 §6); precedence tests; totality fuzz over the full enum product (ladder-valid ⇒ exactly one verdict; ladder-invalid ⇒ V-PR-14) |
| Docs ingestor | dedup by content_hash; V-DR-05 quote check; request-level cache hit does no search; fingerprint stability |
| Freeze | each V-FRZ precondition violated ⇒ refusal; language-limit union correctness; unfreeze re-open |
| Compiler | gap detection per kind; V-CDR idempotency + auto-cancel; DraftMap determinism and ordering |
| Audit | seeded violation of each finding kind is caught; clean draft passes |

### FakeWorker strategy

LLM workers cannot be unit-tested deterministically, so the pipeline is tested with **FakeWorkers**: table-driven stand-ins that read a real task bundle and emit a canned, schema-valid output file (API: docs/11 §5). The fixture set includes happy forms for every decision-table row, hostile outputs each caught by a specific V-* rule (that mapping is itself asserted), and crash modes for lease expiry. Real-LLM smoke tests run only in milestone acceptance, never in the unit suite.

## 3. Pipeline Checks

### Integration scenarios (golden-path scripts, run with FakeWorkers)

```text
S1 seed loop      layer-0 seed (Q, T, A, B; edges T→Q, A→B, B→T — B→T is what
                  connects the chain to the thesis so it can join the spine) →
                  EDGE-A-B form: inference gap → needs_repair(bridge) →
                  Committer wires bridges C,D + edges C→B, D→B (docs/08 B6) →
                  prove C,D and their edges active → re-prove EDGE-A-B
                  (ContextPack now contains C,D as B's neighbors) →
                  pass(conditional) → local freeze
S2 docs loop      NODE_CHECK evidence insufficient → needs_docs → DocsRequest →
                  DocsResult ingested → identical second request is a cache hit
                  (no docs work item) → re-proof pass(strong)
S3 contradiction  fact node contradicted → tombstone → incident edges cascade to
                  rejected(endpoint_rejected), their items cancelled
S4 parallel       8 proof items, 4 concurrent FakeWorkers → all committed, zero
                  cross-writes, event log linearizable
S5 crash          worker dies mid-task → lease expiry → requeue attempt+1 →
                  second worker wins
S6 stale          commit lands between bundle build and claim → item stale →
                  rebuilt as -r2 → claim succeeds
S7 full pipeline  P4 example → 2 layers + closed lanes → msa-check green →
                  spine freeze → dry run (zero gaps by construction, docs/06
                  reachability note; the gap path is fixture-tested in V-CDR)
                  → writing_ready → draft map → prose → ingest → audit clean
S8 rebuild        delete db/ → rebuild → identical /api answers; corrupt one
                  JSONL line → loader reports file+line, refuses to skip silently
```

### Global invariant sweep

`paperproof verify` runs the whole registry against a project at rest — every stored record re-validated against its schema, every cross-reference resolved (ids, blocked_by, duplicate_of, evidence ids, commit refs), V-GRAPH-* on the full graph, V-PR-12 recomputation over all verdict records, V-Q event-log/state consistency replay, snapshot-chain validity, DB manifest freshness (warning only). Exit 0 = clean; any violation = exit 3 (corrupted state — stop and tell the human). This command is:

```text
- the last step of every integration scenario,
- a precondition of spine freeze (run internally) and of compiling,
- the acceptance command for every implementation milestone.
```

### Traceability chain (the audit-of-the-audit)

For any sentence in the final prose it must be mechanically possible to walk:

```text
sentence → (claim: NODE-x) → FreezeItem → CommitDecision(s) → verdict record(s)
        → ProofTask bundle → DocsPack → EvidenceUnit → Document → raw file
```

`paperproof trace --node NODE-x` prints this chain as JSON (node, claim, freeze_id, commit ids, PR ids with their bundle paths, evidence ids with doc + raw path + location, prose occurrences by section:sentence); S7 asserts it resolves for every spine node.
