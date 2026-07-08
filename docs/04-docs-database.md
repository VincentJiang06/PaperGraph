# 04 Docs Database

The Docs Database is the memoized literature layer. Every source that enters the project is archived once, distilled into reusable EvidenceUnits, and served to proof tasks through DocsPacks. Its two jobs: make repeated search cheap, and make hallucinated citations impossible.

## Objects

### Document (`docs/documents.jsonl`)

One record per archived source:

```json
{
  "schema_version": "document.v1",
  "doc_id": "DOC-001",
  "project_id": "p4-ldi",
  "title": "Bank of England Financial Stability Report, Nov 2022",
  "source_type": "official_report",
  "origin": {"kind": "user_provided", "path": "docs/raw/boe-fsr-2022.pdf"},
  "content_hash": "sha256:…",
  "text_path": "docs/text/DOC-001.txt",
  "citation_key": "BoE2022FSR",
  "ingested_from": "DRES-001",
  "ingested_at": "2026-07-07T00:00:00Z"
}
```

```text
source_type    peer_reviewed | official_report | working_paper | news | dataset | user_notes
origin.kind    user_provided (path under docs/raw/) | web (url)
content_hash   sha256 of the raw file bytes — the dedup key: ingesting the same
               content twice returns the existing doc_id instead of a new record.
text_path      null when no text could be extracted.
citation_key   unique across the project (ingestor appends -b, -c on collision).
```

Since S3 (docs/16) the ingestor writes **`document.v2`** — `document.v1` plus a
`provenance` block (retrieved_at, fetch_method, tier, quoted_via) — going forward;
`document.v1` stays registered and readable. The example above is the v1 core every
v2 record still carries.

Text extraction at ingest: `.txt`/`.md` are copied verbatim to `docs/text/`; `.pdf` is extracted with pypdf; extraction failure ⇒ `text_path=null` + warning. A Document without extractable text can still be indexed by metadata, but its EvidenceUnits cannot pass the quote-substring check [V-DR-05] and cannot back a BINDING_CHECK when that task type arrives in v1.1.

### EvidenceUnit (`docs/evidence_units.jsonl`)

The atomic, reusable evidence record — extracted once by a DocsWorker, cited many times:

```json
{
  "schema_version": "evidence_unit.v1",
  "evidence_id": "EU-001",
  "project_id": "p4-ldi",
  "doc_id": "DOC-001",
  "location": "p.12, Section 3.2",
  "kind": "quote",
  "quote_or_paraphrase": "LDI funds faced collateral calls exceeding their liquid buffers within days.",
  "summary": "Documents the speed and size of collateral calls on LDI funds in Sept 2022.",
  "support_direction": "supports",
  "can_cite_for": ["LDI margin calls created acute liquidity pressure in 2022"],
  "cannot_cite_for": ["all de-risking strategies create liquidity crises"],
  "scope": {"period": "2022", "region": "UK"},
  "extracted_by": "docs-worker-1",
  "ingested_from": "DRES-001",
  "created_at": "2026-07-07T00:00:00Z"
}
```

```text
kind               quote | paraphrase — V-DR-05 (verbatim substring in archived
                   text, whitespace-normalized; docs/09 §0) applies iff kind=quote
                   and the document has a text_path.
support_direction  supports | refutes | context
can_cite_for / cannot_cite_for — the anti-hallucination core: an EvidenceUnit
                   declares its own citation boundary, and Audit checks prose
                   against it. Both must be non-empty [V-DR-02].
```

### DocsRequest (`docs/docs_requests.jsonl`)

Emitted by the Committer when a proof form answers `evidence_check=insufficient` (computed verdict `needs_docs`), or created directly by the Orchestrator; consumed by the docs queue:

```json
{
  "schema_version": "docs_request.v1",
  "request_id": "DR-001",
  "project_id": "p4-ldi",
  "requested_by": "PR-001",
  "target_id": "NODE-001",
  "need": "Primary evidence on the size/speed of LDI collateral calls, Sept-Oct 2022.",
  "search_hints": ["BoE FSR 2022", "gilt crisis LDI margin"],
  "fingerprint": "sha256:…",
  "status": "open",
  "fulfilled_by": null
}
```

```text
status        open | fulfilled | not_found   (updates append a full new record, same id)
fingerprint   sha256 over normalize(need) + "\n" + sorted normalized search_hints,
              where normalize = NFC, lowercase, collapse whitespace.
fulfilled_by  DRES- id, or the string "cache" for a cache hit.
fan           bool (S2, docs/15; default false). `--fan` on `docs request` records
              fan=true; a subsequent `docs wave --request DR-x` then fans one
              member per angle. The r3 sweep sets it on every seed request (D5).
```

DRES- ids number ingest events; they have no registry file of their own — a DRES id resolves (for `verify`) iff it appears as `ingested_from` on ≥1 Document/EvidenceUnit or as the `fulfilled_by` of a not_found request. `ingested_from` is null on documents ingested via the `docs ingest` CLI. Orchestrator-initiated requests are created with `paperproof docs request --target <id> --need <text> [--hint <h>]...` (code appends; C1 holds).

## Evidence Seeding (the sweep) — runs BEFORE proof work

**r3, from the ai-jobs live run.** v1 gathered evidence only reactively — one
DocsWorker per `needs_docs` verdict — and the run ended with 24 EvidenceUnits
for a whole paper, most arriving too late to prevent thin packs, dead letters,
and bridge churn. The pipeline therefore gains an explicit **seeding stage**.

**Pipeline order (v2.1, D4 — corrected).** The sweep needs targets that exist:
`docs request --target N` requires node N, and the sweep's coverage floor is keyed
to layer-0 fact/mechanism *nodes*, not raw seed strings. So the order is:
contract accept → **LAYER-0 EXPANSION** → **evidence-seeding sweep** → proof loop
(docs/05 pipeline). V-SWEEP-01 still gates the first expansion *beyond* layer 0.
(The pre-v2.1 "sweep before the expander" ordering was wrong — there were no
target nodes to request against yet.)

```text
1. Ingest every locally available Known Source: `docs ingest <file>` per file.
2. Commit the layer-0 expansion (question + thesis + seed fact/mechanism nodes).
3. The Orchestrator SWEEPS via ONE mechanism (v2.1, D5): for every fact/mechanism
   layer-0 node N,
     paperproof docs request --target N --need <text> [--hint <h>]... --fan
   then
     paperproof docs wave --request DR-x --fan
   The wave (docs/15) provides the four-angle coverage
   {official_stats, academic, industry, counter}; there is no per-(seed×angle)
   single-request procedure any more. `docs request` gains `--fan` (records
   fan=true on the DocsRequest; the sweep always sets it so the follow-up
   `docs wave` fans every angle).
4. Coverage floor before the first expansion beyond layer 0 [V-SWEEP-01]:
   every fact/mechanism layer-0 node has ≥2 EvidenceUnits from ≥2 distinct
   documents, or a recorded not_found for ≥2 sweep angles. `paperproof graph
   msa-check` reports sweep coverage informationally from day one.
   ("REQUESTED-for-N" evidence is traced request→DRES→ingested_from, as for
   DocsPacks.)
```

Sweep requests are Orchestrator-initiated (`requested_by` = the orchestrator
actor, not a PR- id). The old r3 docs round-trip cap they were exempt from is
gone (SUPERSEDED by S4 saturation, docs/17 — see below); saturation is per-node
and never punishes the human's evidence gathering. Expected steady state for a
paper-scale project after the sweep: roughly 10–20 documents and 30–60
EvidenceUnits before the first proof wave — an order of magnitude above the
reactive-only baseline.

## Memoized Search

Two distinct memoization points, both deterministic code:

### 1. Request-level cache (before dispatching any DocsWorker)

```text
On enqueue of a DocsRequest, the docs engine checks fingerprint equality with
any previously fulfilled request WHOSE fulfilled_by IS A DRES ID ⇒ cache hit.
A cache hit appends the request as status=fulfilled, fulfilled_by="cache",
creates no work item, and unblocks the waiting re-proof item immediately.
A miss ⇒ status=open + a docs_queue item.
Requests whose fulfilled_by is itself "cache" are NEVER cache sources — a
false hit must not chain (r3; in the live run the pre-r2.2 false hits DR-003..
DR-005 would otherwise satisfy future identical searches forever).
```

**r2.2 change (removed the matcher-hit cache trigger).** An earlier rule also
declared a cache hit when the evidence matcher found ≥1 EvidenceUnit for the
target claim. The ai-jobs live run showed this to be wrong: the v1 matcher is a
deliberately dumb keyword matcher (below), so it produced **false cache hits** —
a genuinely new evidence need (e.g. an aggregate-employment bridge premise) was
declared "fulfilled" merely because loosely-related task-automation evidence
already existed, which silently overrode a ProofWorker's own
`evidence_check=insufficient` judgment and blocked the fresh search the argument
required. **Sufficiency is the ProofWorker's decision** (from the
matcher-populated DocsPack), never the cache's. The request-level cache now only
avoids re-running a *literally identical* search (fingerprint equality); the
matcher still assembles DocsPacks (point 2) unchanged.

### 2. Evidence matcher (DocsPack assembly, `docs build-pack`)

The matcher that selects EvidenceUnits for a target claim is fixed:

```text
tokens(s)   := NFC(s) → lowercase → split per docs/09 §0 (CJK chars are
               single tokens) → drop the builtin English stopword list
score(EU)   := |tokens(claim) ∩ (tokens(EU.summary) ∪ tokens(EU.quote_or_paraphrase)
               ∪ tokens(join(EU.can_cite_for)))|
include EU  iff score(EU) ≥ 2 AND scope_compatible(EU.scope, target.scope)
               (scope compatibility: docs/09 §0)
order       by (score desc, evidence_id asc)
```

**DocsPack composition (r3 — replaces "matcher output, no cap"):**

```text
pack(target) := REQUESTED ∪ top-K(MATCHED), where
REQUESTED = every EU ingested from a DocsRequest whose target_id is this
            record (traced via request → DRES → ingested_from). These are
            included UNCONDITIONALLY — in the live run, evidence fetched FOR a
            target only reached its pack via matcher luck (common tokens like
            "2020"/"employment" happened to match everything).
MATCHED   = matcher output as above, minus REQUESTED; K = 12.
```

The K-cap exists because the run showed score≥2 over-includes on period/domain
tokens — NODE-006's pack carried all 24 project EUs. Bounded packs keep worker
context small and deterministic. The keyword matcher above is the base; **S5
(docs/18) replaces the matcher SCORE at pack build with a hybrid keyword+embedding
score when the pinned model is present**, degrading to this keyword score loudly
when it is absent (V-SEM-03). `pack = REQUESTED ∪ top-12 MATCHED` is unchanged —
semantic feeds the MATCHED half's ranking only.

A **DocsPack** (`docs/docspacks/DOCSPACK-<task>[-rN].json`) is a frozen bundle of EvidenceUnits + document metadata assembled for one proof task. Proof workers cite only from their DocsPack, so every citation in every ProofResult resolves to an archived Document by construction. An empty DocsPack is valid.

**Evidence-arrival staleness (r3).** When the ingestor archives new
EvidenceUnits, it marks stale (docs/05) every queued/blocked **proof** item
whose target would now receive a different pack — i.e. any target the new EUs
are REQUESTED for, plus any whose matcher output changes. In the live run the
NODE-006 re-proof was about to run against a 10-EU pack while 24 EUs existed;
only a manual `proof build-task` rebuilt it. Freshly relevant evidence must
reach pending proofs without human intervention [V-TASK-04].

## DocsWorker Protocol

DocsWorkers are Claude subagents, parallel-safe like ProofWorkers:

```text
1. Serve one DocsRequest — its fields (request_id, need, search_hints) are
   embedded in the dispatch prompt; there is no per-request file to read.
2. Search: user-provided sources under docs/raw/ first, then web if allowed.
3. Write ONE DocsResult file (schema: docs/08 B7) to the declared output path
   agent_outputs/docs_results/<request_id>.docs_result.json, containing
   documents and evidence units. Web documents include their full extracted
   text INLINE in the result (the worker cannot write docs/raw/ — the
   ingestor archives).
4. Stop. Chat text is discarded.
```

Since S1/S2 (docs/14, docs/15) the DocsWorker executes a compiled **SearchPlan**
and writes **`docs_result.v2`** (a structured `query_log` replaces `search_log`);
under S2 the worker is a **wave member** on one angle with its own angle-specific
plan and its result is ingested per-member (`docs wave-member`), not via
`docs ingest-result`. The prompt is emitted by `docs render-prompt --work-item`
(D11) with the plan embedded and the S3 registry excerpt filled. See docs/14/15
for plan/wave mechanics; the fields here are the doc/EU core every version carries.

**Coverage expectations per request (r3, normative for the worker prompt):**

```text
Target 2–5 documents and 4–10 EvidenceUnits per request. Padding is still
forbidden — the floor is honesty, the ceiling is focus — but a single-document
result for a claim with a live literature is under-searched, and the live run
showed reactive single-shot searches leave the whole project at ~24 EUs.
Disconfirming duty: when the searched literature contains evidence AGAINST the
claim, the worker MUST capture it (support_direction=refutes|context) rather
than cherry-pick — the run's honest refutes (EU-014/017/022) are what let the
system reject a false premise.
Fetch resilience: official-statistics sites often 403 automated fetches; the
worker should fall back to mirrors, archived copies, or secondary sources
citing the primary figures, and extract PDF text locally (e.g. pdftotext)
rather than abandoning the angle. Record every query in search_log either way.
```

Id assignment and appending to canonical JSONL is done by the Docs ingestor (code) after validation (V-DR rules, docs/09). Inside a DocsResult, an evidence unit points at its document with exactly one of `doc_ref` (integer index into this result's `documents` list) or `doc_id` (an existing archived id) [V-DR-01].

`not_found` is a legitimate terminal result: the waiting re-proof then runs with the unchanged DocsPack, and the worker must answer the form honestly for the evidence it has — typically `wellformed_check=too_broad` (⇒ a narrow repair to a claim the available evidence can carry) or `inference_check=holds_only_with_assumptions` with tighter language limits.

**Docs round-trip cap — SUPERSEDED by S4 saturation (docs/17, V-COV-03).** The r3
count-based cap (3rd needs_docs verdict ⇒ dead letter) is GONE; no count-based
refusal remains. Stopping is now **saturation**, computed per node from the
coverage ledger: a needs_docs verdict ALWAYS opens more search while the target is
NOT saturated (`rounds ≥ 2 AND every mandatory angle ∉ {no_attempt} AND
new_docs_last_round = 0` is false); a **saturated** target opens no new search.
Born-dead has exactly one reason, `saturated`, and fires only when the role-profile
floor (docs/17) is ALSO unmet: (created)→dead, op=dead_letter, detail
`{reason:"saturated", floor_met:false}`. If the floor IS met but the worker still
answered insufficient, the two facts conflict (floors are necessary, not
sufficient): the Committer records a `human_review` CommitDecision action AND
still enqueues the re-proof item born dead with detail `{reason:"saturated",
floor_met:true}`, so humans get a queue trace and `queue requeue` resumes after
review (v2.1 D1). This lets the human's evidence gathering (sweep / `docs request`)
never punish a target — saturation measures whether the *world's literature*
keeps producing, not how many cycles ran.

Prohibitions:

```text
DocsWorkers never set proof verdicts and never touch the graph.
An EvidenceUnit never contains a judgment about whether a graph edge holds —
only what the source itself supports.
No invented sources: every EvidenceUnit must point at an archived Document;
quotes must appear verbatim in the archived text [V-DR-05].
```

## Derived Index

For query speed a DuckDB index (`db/`) mirrors documents/evidence/queue state. It is derived only: deleting it and rebuilding from JSONL is a normal operation, and a stale index must be detectable (`db/index_manifest.json` stores source-file hashes; `paperproof db check` compares). If JSONL and DB disagree, JSONL wins.
