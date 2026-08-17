# Lifecycle

Version 0.1.0 is the first executable contract release.

## Release checklist

1. `python3 evals/run_all.py` passes every offline case.
2. Every guidance adversarial edge maps to a passing case.
3. Trigger precision and recall clear 0.90 overall and on the fixed holdout.
4. Signing-body and fail-closed mutations are detected.
5. Security scan finds no real secret, raw shell interpolation, undeclared host,
   or interactive prompt.
6. One explicitly confirmed GeneralBasicOCR probe records exactly one request and
   leaks no credential or recognized text in command output.
7. Guidance re-audit and an independent attacker battery are clean.

## Breaking changes

Changing the provider host/action/version, normalized source schema, artifact
paths, author gate formulas, or `SHIP` conditions requires a version bump,
changelog entry, fixture update, migration note, and full release checklist.
Never silently weaken a gate or reinterpret an old artifact in place.

## Rollback

Restore the previous complete skill-directory snapshot, then rerun that version's
offline harness before use. Keep raw OCR archives immutable so normalized outputs
can be regenerated under the restored schema. A rollback does not rewrite prior
run or evaluation evidence.
