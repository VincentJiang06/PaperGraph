---
name: papergraph
description: >-
  Build or supervise a complete evidence-backed research paper from a topic or
  local source bundle, especially scanned papers needing OCR; use for PaperGraph
  or map-ground-gate-evaluate requests. Do NOT use for OCR-only extraction,
  fact-checking, copy editing, or unrelated software work.
license: MIT
metadata:
  version: "0.1.0"
---

# PaperGraph

Turn one topic and local source bundle into an auditable Markdown paper. The host
coding agent is the orchestrator; project scripts perform only deterministic OCR,
artifact, gate, and evaluation checks. Never call a model-provider API from the
project.

Requires Python 3.10+ and a host coding agent with native subagents. Offline
authoring needs no model API key. Scanned-source ingestion optionally needs
Tencent OCR credentials and outbound HTTPS to `ocr.tencentcloudapi.com`.

## Steps

1. **Preflight.** Confirm the topic, project root, source paths, output run path,
   native subagent support, and whether each source is born-digital or scanned.
   Load [rules/workflow.md](rules/workflow.md). For scanned files, also load
   [rules/ocr-ingestion.md](rules/ocr-ingestion.md). Verify credential presence
   without printing values. Tencent's `TENCENTCLOUD_*` names take precedence
   over the documented shorter aliases.
2. **Ingest evidence.** Preserve born-digital text directly. For a scanned local
   file, use `scripts/ocr_ingest.py`; archive raw, normalized, manifest, and text
   artifacts. Default to `GeneralBasicOCR`. An Accurate call is a separate,
   explicitly authorized repair task and is never part of the live probe.
3. **Scope and map.** Write the thesis question, boundaries, field weight, and
   falsifier. Dispatch one Cartographer with only that scope. Validate its return,
   then let the orchestrator write `positions.md`.
4. **Run parallel author waves.** Dispatch one Advocate per position plus one
   Adversary concurrently. After identifying empirical claims, allocate disjoint
   claim IDs and dispatch one ClaimGrounder per claim concurrently. Workers write
   only declared paths; the orchestrator alone merges shared files and drafts
   `paper.md`. Load [assets/worker-packets.md](assets/worker-packets.md).
5. **Qualify a candidate.** Run both repository author gates on every revision.
   A dual pass means candidate only. Revise the responsible artifact and rerun
   until both pass; never weaken a gate to admit a paper.
6. **Evaluate out of loop.** Freeze the candidate, load
   [rules/held-out-eval.md](rules/held-out-eval.md), derive the literature key
   independently, and fan out all EvalAdvocates, EvalAdversary, ClaimAuditor, and
   at least three Referees. Run `scripts/validate_eval_bundle.py`; any missing or
   nonconforming D1-D5 input fails closed.
7. **Report.** Return artifact paths, both gate verdicts, held-out verdict, worker
   gaps, OCR call count/request IDs, and command evidence. Never print recognized
   text, credentials, authorization headers, or request bodies by default.

## Controls

- OCR accepts local files only and transmits fixed-host `ImageBase64` requests.
- A live probe requires `OCR_LIVE_CONFIRM=ONE_BASIC_CALL`, Basic action, one file,
  and one attempt. It writes evidence outside this skill directory.
- Post-submit timeout is `outcome_unknown` and is not retried. Only explicit
  provider throttling codes receive bounded retry.
- Chat is not durable state. Validate worker returns before the orchestrator
  merges them; shared files always have one writer.
- `SHIP` requires both author gates and a complete D1-D5 held-out pass.

## Metrics

- Offline contract harness: 100% pass and all adversarial edges covered.
- Trigger set: precision and recall at least 0.90 overall and on holdout.
- OCR live acceptance: exactly one Basic request, one request ID, no secret leak.
- Source traceability: 1.0 for normalized OCR artifacts and empirical claims.
- Candidate: both author gates pass. Release: complete D1-D5 pass with no kill
  criterion.

## Modules

| File | Load when |
|---|---|
| [rules/workflow.md](rules/workflow.md) | Every PaperGraph run; ownership, waves, gates, stops. |
| [rules/ocr-ingestion.md](rules/ocr-ingestion.md) | Any scanned local source or OCR failure. |
| [rules/held-out-eval.md](rules/held-out-eval.md) | Candidate evaluation and release decision. |
| [rules/lifecycle.md](rules/lifecycle.md) | Release, rollback, or breaking contract change. |
| [references/ocr-api.md](references/ocr-api.md) | Provider signing, request, response, or limits. |
| [references/artifact-contracts.md](references/artifact-contracts.md) | Creating or validating durable run artifacts. |
| [assets/worker-packets.md](assets/worker-packets.md) | Dispatching bounded author/eval subagents. |

## Scripts

| Command | Purpose |
|---|---|
| `python3 scripts/ocr_ingest.py replay ...` | Normalize an archived provider response offline. |
| `python3 scripts/ocr_ingest.py live-probe ...` | Make one confirmed Basic OCR call. |
| `python3 scripts/validate_eval_bundle.py <dir>` | Fail-closed D1-D5 validation. |
| `python3 evals/run_all.py` | Run the 24-case offline contract harness. |
| `python3 evals/run_trigger_eval.py` | Measure deterministic trigger precision/recall. |
