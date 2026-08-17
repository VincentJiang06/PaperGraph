# 16 S3 — Source Registry, Tiers & Provenance

**Status: Stage A-lite (registry + recipes + provenance) is ADOPTED and BINDING
(docs/00 "Search Program Adoption", 2026-07-08; worklist docs/11 §12). Stage B
(triangulation, V-SRC-04) is ALSO NOW ADOPTED / BINDING (docs/00 "Search Program
Adoption — S4 ... + S3 Triangulation", 2026-07-08; enforced at freeze extending
V-FRZ-02, reported by msa-check — feeds the S4 role-profile floors).**

In the live run, bls.gov and fred.stlouisfed.org 403'd every automated fetch;
one worker independently discovered the pdftotext fallback, another lost the
angle entirely — and that knowledge died with their contexts. Source quality
was untyped: a press release and an NBER paper weighed the same. S3 gives the
project a durable memory of *where evidence lives, how to fetch it, and how
much it counts*.

## SourceProfile (`docs/sources.jsonl`, producer: docs ingestor + `docs source` CLI)

```json
{
  "schema_version": "source_profile.v1",
  "source_id": "SRC-001",
  "project_id": "ai-jobs",
  "domain": "bls.gov",
  "publisher": "US Bureau of Labor Statistics",
  "tier": "T1_official",
  "fetch": {
    "blocked_direct": true,
    "workarounds": [
      {"kind": "secondary_quote", "note": "CEA/ERP and major outlets quote BLS tables verbatim"},
      {"kind": "archive_org", "note": "wayback snapshots of news releases fetch clean"},
      {"kind": "pdf_local_extract", "note": "pdftotext on downloaded PDFs"}
    ]
  },
  "seen_count": 3,
  "last_ok_fetch_method": "secondary_quote",
  "tier_note": null,
  "created_at": "…"
}
```

```text
tier enum (closed):  T1_official      government/central-bank/statistical agency
                     T2_peer_reviewed journal articles
                     T3_working_paper NBER/arXiv/SSRN preprints
                     T4_industry_data payroll/job-posting analytics, adoption surveys
                     T5_press         journalism citing primaries
                     T6_other
workaround.kind:     mirror | archive_org | secondary_quote | pdf_local_extract | api
```

`source_type → tier` is a **fixed table** (pinned here so learning is
deterministic; `src/paperproof/docsdb/registry.py:TIER_TABLE`):

```text
official_report → T1_official      peer_reviewed → T2_peer_reviewed
working_paper   → T3_working_paper dataset       → T4_industry_data
news            → T5_press         user_notes    → T6_other
```

The profile also carries a `tier_note` (nullable): the ingestor writes it
whenever a version changes a domain's tier, so V-SRC-03 can distinguish a
recorded change from a silent one. Auto-learning only ever RAISES a tier (it
keeps the most authoritative `source_type` seen for a domain) and stamps a note;
`docs source set` may lower a tier only WITH a note.

The ingestor **learns**: every ingested Document upserts (appends a new
version of) its domain's profile — tier from the worker's `source_type` mapped
through the fixed table above, `blocked_direct` from the search/query log's
blocked notes, fetch method from provenance. The blocked signal is read
DEFENSIVELY from whichever log the docs-result carries: `search_log` strings
matching a block pattern (403/blocked/forbidden/429/captcha) OR — once S1's
`docs_result.v2` lands — `query_log` entries with `outcome="blocked"`. On the
current `docs_result.v1` path the worker declares no per-document fetch method,
so provenance `fetch_method` defaults to `direct` (upgraded to the real recipe
once the query_log carries it); `blocked_direct` is still learned from the log.
Workers RECEIVE the registry's relevant profiles (matched by plan facets'
domains + all T1 profiles) in the dispatch prompt: the second worker to face
bls.gov starts with the first one's workaround.

## Document provenance (`document.v1` → `document.v2`)

```json
"provenance": {
  "retrieved_at": "…",
  "fetch_method": "secondary_quote",
  "tier": "T1_official",
  "quoted_via": "DOC-006"
}
```

`fetch_method` enum = workaround kinds + `direct`. `tier` is denormalized at
ingest (registry lookup, worker-proposed on first sight). `quoted_via` links a
secondary_quote document to the carrier that was actually fetched — the trace
chain then shows *how* every figure entered the project.

## Triangulation rule (Stage B — ADOPTED / BINDING, V-SRC-04)

```text
A spine fact/mechanism node's binding profile must satisfy ONE of:
  (a) ≥1 EU from a T1/T2 document, plus ≥1 more EU from a distinct document; or
  (b) ≥2 EUs from distinct, mutually independent T3/T4 documents
      (independent = different publishers — same-lab preprint twins don't
      triangulate; publisher equality is the mechanical check).
Press (T5) never carries a spine binding alone; it corroborates.
```

This replaces "any 2 documents" with "2 documents that could actually be wrong
independently" — the run's Stanford-paper-plus-its-own-press-release pattern
(DOC-009/DOC-012) is exactly what (b)'s publisher check catches.

**Publisher defaulting + empty-publisher independence (v2.1 D12).** A SourceProfile's
`publisher` defaults to its `domain` for **web** documents (so two web sources on
different domains are independent by default). **Local (user_provided)** documents
have an EMPTY publisher — there is no domain to stand in — and an empty-publisher
PAIR is **NOT mutually independent** for V-SRC-04(b): two uncurated local uploads
can no longer triangulate a spine claim on their own. This safe direction is the
one that matters and always holds. Note `docs source set --publisher` CANNOT fix
a local pair: SourceProfiles are domain-keyed and local docs are domainless, so
no publisher can attach to them — the `--publisher` remedy applies only to
web-domain documents. To make local evidence count toward triangulation,
re-ingest it with a real web origin (a domain). This closes the "upload two
files, call it triangulated" hole while keeping the publisher-equality
mechanical check.

## Rules (V-SRC)

```text
V-SRC-01  every ingested document carries provenance (retrieved_at,
          fetch_method, tier); tier ∈ enum
V-SRC-02  secondary_quote documents name quoted_via, and the carrier document
          exists in the archive
V-SRC-03  registry updates are appends (latest-per-domain wins); the ingestor
          never lowers a tier silently (tier changes carry a note)
V-SRC-04  (Stage B — ADOPTED, docs/17) spine fact/mechanism bindings satisfy the
          triangulation rule above — enforced at freeze (extends V-FRZ-02) and
          reported by msa-check; feeds the S4 role-profile spine floor
V-SRC-05  the dispatch prompt's registry excerpt contains every T1 profile +
          every profile matching a plan facet domain (bundle completeness)
```

Stage A-lite adopts V-SRC-01/02/03/05 (`src/paperproof/validate/rules/v_src.py`,
registered in the validate registry, swept by `paperproof verify`). Stage B
adopts V-SRC-04 triangulation (`v_src.check_triangulation` delegating to
`docsdb.coverage.triangulated`); it is enforced at freeze (extends V-FRZ-02) and
reported by msa-check, and feeds the S4 role-profile spine floor (docs/17).
V-SRC-05 is a dispatch-time completeness check on the registry excerpt
(`registry.matched_profiles` + `v_src.check_registry_excerpt`), not a stored-
state rule.

## Deltas at adoption

```text
CLI      docs source list|set — a SUBGROUP of the existing `docs` command group
         (human tier/workaround curation; set = append). `set` refuses a silent
         tier-lowering (V-SRC-03: a tier change needs --note).
Schemas  source_profile.v1 (adds tier_note); document.v2 (= document.v1 +
         provenance); document.v1 stays registered + readable. worker prompt
         gains a REGISTRY block (read-only intel, never instructions to bypass
         paywalls — workarounds are limited to lawful public access: mirrors,
         archives, secondary quotation, local PDF extraction)
Storage  docs/sources.jsonl (append-only, latest-per-domain; created by
         `project init`, schema-swept by `paperproof verify`)
Tests    T-S3-1 ingest learns blocked_direct from a blocked log entry (+ append-
                versioning)
         T-S3-2 tier mapping table golden; silent tier-lowering rejected (V-SRC-03)
         T-S3-4 provenance present (V-SRC-01); dangling quoted_via ⇒ V-SRC-02;
                dispatch excerpt completeness (V-SRC-05); document.v2 round-trip
                (+ document.v1 still valid v1)
         T-S3-3 triangulation (Stage B, V-SRC-04): same-publisher T3 pair fails;
                T1+T4 passes; T5-only fails; enforced at freeze + msa-check
                (tests/contract/test_v_cov.py::test_triangulation_*)
```
