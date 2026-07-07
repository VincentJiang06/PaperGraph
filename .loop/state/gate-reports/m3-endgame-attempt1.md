# Gate report — m3-endgame, attempt 1

## Generator result (Opus/high, fresh)
- `pytest -q`: **363 passed** (335 + 28 new); full gate exit 0 (orchestrator re-ran, confirmed). No regression (schemas/v_commit/S2/determinism subset green).
- New src: freeze/{apply}, compiler/{section_plan,dry_run,draft_map,prose}, audit/{run}, graph/trace.py; real freeze/compiler/audit/trace/msa-check CLI.
- New tests: test_v_frz, test_v_cdr, test_v_prose_aud, S7 full pipeline; S1 freeze coda, S3 MSA-9 coda; FakeCompileWorker.
- Reused: committer freeze_batch/unfreeze_batch, spine walker, MSA-1..9 checklist (confirmed already implements MSA-9).

## Generator OPEN DOC ISSUES → disposition
1. writing_ready ↔ "spine_freeze for current snapshot": FreezeItem has no snapshot_id; bound as "un-revoked spine_freeze exists AND every current spine record frozen". Reasonable; accept (flips false after unfreeze).
2. missing_section_claim target_id = section_id (no node). Consistent with Gap.target_id free string. Accept.

## Evaluator verdict — PASS

Fresh adversarial reviewer; did not trust the generator's tests. Re-ran the gate
(`.venv/bin/python -m pytest -q` → **363 passed**, exit 0) and the 6 M3 test files
in isolation (30 passed). AST hollow-scan of test_v_frz / test_v_cdr /
test_v_prose_aud / test_s7_full_pipeline + the S1 freeze coda + S3 MSA-9 coda:
zero-assertion=0, assert-constant-true=0, skips=0, xfails=0 (asserts:
frz=12,cdr=13,prose_aud=12,s7=27,s1=24,s3=16). All findings below are from my own
throwaway probes (temp projects, degenerate-state mutations, direct CLI), not the
generator's suite.

### Independently reproduced (each stage does real work, no rubber stamps)
1. **msa-check is conditional, not green-unconditionally.** Un-binding evidence
   from the spine mechanism (NODE-003) → `msa-check` all_pass=False with **only
   MSA-4** false, rest true. Detection is real.
2. **MSA-9 vacuous-spine guard (r2.1 fix) genuinely fires.** Rejected the thesis's
   only support so the spine collapses to {Q,T,T→Q} → MSA-9=False while
   MSA-1/MSA-2/MSA-3 pass vacuously and MSA-4 passes vacuously (no fact/mechanism
   in spine). Matches docs/02 MSA-9 and the S3 coda (`spine=={Q,T,EDGE_TQ}`).
3. **Compiler gap detection is NOT a no-op** (proves S7's "zero gaps" is
   by-construction, not broken-detection). Constructed a degenerate graph per kind
   and dry-run reported exactly it: missing_evidence(NODE-003) on unbound evidence;
   unhandled_alternative(NODE-099) on an active alternative; weak_spine_edge on a
   conditional spine edge w/ empty language_limits; contract_violation on a spine
   node with scope {region:Mars} vs the UK/2022 contract.
4. **V-CDR** — gap identity (kind,target_id): first dry-run enqueued exactly one
   `GAP:missing_evidence:NODE-003`; re-run enqueued 0 (idempotent); resolving the
   gap → next run auto-cancelled the item (detail gap_resolved), 0 live items.
   V-CDR-02: hashed graph/ and docs/ before/after dry-run — byte-identical.
   V-CDR-03: section_plan covered all 5 spine nodes exactly once.
5. **Freeze refusals are real (V-FRZ-01..04).** Each precondition independently
   violated → `freeze apply` REFUSED (exit 1, failed_rules names the rule):
   V-FRZ-01 (local freeze on a needs_docs record), V-FRZ-02 (local freeze on a
   fact/mechanism with empty bindings), V-FRZ-03 (open proof item touching the
   closure), V-FRZ-04 (spine freeze with MSA-4 failing). The verify branch of
   V-FRZ-04 is genuinely wired: corrupting a stored `computed_verdict` (MSA stays
   green) → `verify` exit 3 (V-PR-12) → spine freeze refused V-FRZ-04.
   Language-limit union confirmed dedup+sorted across two spine nodes. Unfreeze
   re-opened the proof: NODE-003 frozen→false, lifecycle→pending_proof, a re-proof
   work item enqueued.
6. **V-PROSE-01..04** each rejected the crafted violation with the right rule
   (unknown claim id→01; cite outside/unbound→02; forbidden substring→03; claim
   never annotated→04); clean prose passed. End-to-end `compiler ingest-prose`:
   dirty file rejected (exit 1, failed_rules=[V-PROSE-03]), item requeued, NOT
   promoted; clean file accepted → promoted to compiler/prose/ → item committed.
7. **Audit passed=true is earned, not a constant.** Clean prose → passed=true,
   findings=[]. Tainting the promoted prose flipped it every time: forbidden
   language→strength (S7 variant, re-confirmed); cite to non-existent EU→binding;
   cite outside a claim sentence→binding; (claim:) to a non-spine node→scope;
   unannotated draft claim→coverage. V-AUD-02: prose hash unchanged across an
   audit run.
8. **Trace resolves to a REAL file (A20, docs/09 §3).** For NODE-003:
   freeze_id FRZ-001 → commit ids → 2 proof_results (needs_docs then pass, with
   real bundle task_file paths) → EU-001 → DOC-001 → raw_path docs/raw/DOC-001.txt
   AND text_path docs/text/DOC-001.txt, both present on disk with the archived BoE
   text; prose_occurrences {SEC-mechanism:1}. Honesty check: binding a node to an
   EU whose Document row is absent → resolved=True but raw_path/text_path=null
   (missing archive surfaced, not faked); binding to a non-existent EU →
   resolved=False. Chain is not echoing ids.

### Disposition judgments (both SOUND)
- **writing_ready without snapshot_id** — sound. Because a frozen record cannot be
  mutated (V-GATE-03), the spine set cannot drift while a spine_freeze holds, so
  "un-revoked spine_freeze exists AND every current spine record frozen" is an
  adequate stand-in for "spine_freeze for the current snapshot." Reproduced the
  flip: writing_ready True after freeze → False after `freeze unfreeze NODE-003`.
- **missing_section_claim target_id=section_id** — sound. Gap.target_id is a free
  string; the gap has no node (empty template section), and SEC-introduction is the
  only routable identifier. Reproduced: detect_gaps with an intro-less plan →
  {kind:missing_section_claim, target_id:"SEC-introduction"}.

### Non-blocking notes (do not block the M3 gate)
- N1 (pre-existing, M1). `paperproof verify` does NOT resolve node
  `evidence_bindings` or `duplicate_of` cross-refs, though docs/09 §3 lists
  "evidence ids ... duplicate_of" among what the sweep resolves. Repro: append a
  NODE-003 version with evidence_bindings=["EU-999-nonexistent"] → `verify` exit 0.
  It DOES catch dangling blocked_by (V-Q-04), schema, V-GRAPH, V-PR-12, and commit
  snapshot refs. verify.py last changed in M1 (f759446), so this is not an M3
  regression, and the live pipeline cannot produce dangling bindings (Committer
  copies evidence_used, which V-PR-06 constrains to the DocsPack; V-FRZ-02 requires
  ≥1 binding). Defense-in-depth only; V-FRZ-04's verify integration is real
  (proven above). Worth closing when docs/09 §3's crossref list is next touched.
- N2 (cosmetic). trace `evidence[].resolved` reflects only EU existence, so a
  present EU pointing at a missing Document reports resolved=True with null paths.
  Honest via the nulls, but a stricter flag would set resolved=False. No functional
  impact.

## N1 closed (post-gate additive hardening)
- verify._crossref extended: non-rejected node evidence_bindings resolve to archived EUs;
  rejected(duplicate) node state_detail.duplicate_of + tombstone duplicate_of resolve to
  real ids. Dangling → V-XREF exit 3. New tests/contract/test_verify.py (4 cases).
- 367 passed; evaluator's exact repro (EU-999 binding) now exit 3; S1/S2/S3/S7 terminal
  verify still exit 0 (inert on clean states). V-XREF is verify-internal, not a registry rule.
