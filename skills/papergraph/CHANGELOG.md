# Changelog

## 0.1.0 - 2026-07-10

- Added the thin PaperGraph orchestrator and on-demand workflow, OCR, eval,
  artifact, worker, and lifecycle contracts.
- Added a stdlib Tencent TC3 client with local-only ImageBase64 ingestion,
  fixed provider surface, strict normalization, bounded retries, atomic replay,
  and a one-call live-probe gate.
- Added fail-closed D1-D5 validation, deterministic trigger routing, and the
  offline end-to-end workflow contract.
- Added a 24-case contract harness, balanced trigger holdout, RED evidence,
  mutation checks, and normalized source schema.

Breaking changes to provider coordinates, action/version, source schema, gate
rules, or release verdicts require a version bump and migration note.
