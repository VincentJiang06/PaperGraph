# 16 S3 — Source Registry, Tiers & Provenance

**Status: design-frozen (Stage A-lite: registry+recipes; Stage B: triangulation).**

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

The ingestor **learns**: every ingested Document upserts (appends a new
version of) its domain's profile — tier from the worker's `source_type` mapped
through a fixed table, `blocked_direct` from the query_log's blocked notes,
fetch method from provenance. Workers RECEIVE the registry's relevant profiles
(matched by plan facets' domains + all T1 profiles) in the dispatch prompt:
the second worker to face bls.gov starts with the first one's workaround.

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

## Triangulation rule (Stage B; feeds S4 floors and MSA/freeze)

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

## Rules (V-SRC)

```text
V-SRC-01  every ingested document carries provenance (retrieved_at,
          fetch_method, tier); tier ∈ enum
V-SRC-02  secondary_quote documents name quoted_via, and the carrier document
          exists in the archive
V-SRC-03  registry updates are appends (latest-per-domain wins); the ingestor
          never lowers a tier silently (tier changes carry a note)
V-SRC-04  (Stage B) spine bindings satisfy the triangulation rule — enforced
          at freeze (extends V-FRZ-02) and reported by msa-check
V-SRC-05  the dispatch prompt's registry excerpt contains every T1 profile +
          every profile matching a plan facet domain (bundle completeness)
```

## Deltas at adoption

```text
CLI      docs source list|set (human tier/workaround curation; set = append)
Schemas  source_profile.v1; document.v2 (provenance); worker prompt gains a
         REGISTRY block (read-only intel, never instructions to bypass paywalls
         — workarounds are limited to lawful public access: mirrors, archives,
         secondary quotation, local PDF extraction)
Storage  docs/sources.jsonl
Tests    T-S3-1 ingest learns blocked_direct from a blocked query_log entry
         T-S3-2 tier mapping table golden; silent tier-lowering rejected
         T-S3-3 triangulation: same-publisher T3 pair fails, T1+T4 passes
         T-S3-4 quoted_via dangling ⇒ V-SRC-02
```
