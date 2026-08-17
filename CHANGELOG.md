# CHANGELOG — workflow track

The workflow is validated by running real papers through both gates across distinct domains,
then fixing whatever the tests expose. Newest first.

## 2026-07-10 — active-document reconciliation

- Replaced the stale pre-reset `README.md` and `AGENTS.md` entry points with the current small
  topic-to-paper workflow.
- Separated design/workflow guidance from the exact gate and eval interface documents.
- Made native coding-agent subagents, disjoint parallel tasks, and single-writer shared artifacts
  explicit; the project itself requires no model API key.
- Clarified the quality boundary: both in-loop gates green means candidate, while a complete
  held-out D1-D5 eval is required for `SHIP`.
- Corrected the canonical claim ledger name from `ledger.tsv` to `claims.tsv`.
- Documentation only; no gate, eval, data, or generated-run behavior changed.

## 2026-07-10 — three-domain generality test + gate hardening

**Goal (user):** iterate testing + feature updates until the paper workflow is usable; test it
with three examples from three different fields.

**Examples built (each drives a different workflow muscle), all pass BOTH in-loop gates:**
| Run | Domain | Field-weight | Stresses | Result |
|---|---|---|---|---|
| `runs/ai-employment` | economics / labor | mixed (K.6) | pilot; 1 data + 3 source | ✅ both green |
| `runs/black-death` | medieval economic history | humanities (K.8) | **zero data claims → no-DVC path**; 7 positions at high K | ✅ both green |
| `runs/nuclear-safety` | energy / physical science | science (K.5) | **3-stage DVC** (2 lookups + 1 derived ratio) + 2 source; excluded-with-reason | ✅ both green |
| `runs/alcohol-jcurve` | epidemiology / public health | mixed (K.6) | 6 positions, subtle objection (all-cause vs IHD); 3 source | ✅ both green |

Every empirical number is real: FRED unemployment, OWID energy death rates, and verbatim
quotes from real papers (Eloundou 2023, Brynjolfsson-Li-Raymond 2023, Humlum-Vestergaard 2025,
IPCC/World Nuclear, Kharecha-Hansen 2013, Wood 2018, GBD 2018, Millwood 2019, and encyclopedic
sources for the Black Death facts).

**Feature updates (driven by the tests):**
1. **Divergence gate — paragraph-based engagement (anti-gaming).** Engagement was measured on the
   physical *line* around a `[Pn]` tag; since papers are hard-wrapped (~90 chars), a bare namedrop
   cleared the 40-char bar. Now the gate measures the whole *paragraph* (blank-line block) and
   requires ≥ 200 chars of real argument prose. Spec updated (`gates/divergence.md`). Verified: all
   four papers still PASS; a namedrop-only tag now correctly reads UNHANDLED (negative test C).
2. **Rigor gate — `--verify-sources` (traceability audit).** The `source` check trusted the saved
   `sources/*.txt`. The new optional, networked, **non-fatal** flag re-fetches each `raw_ref` URL
   and confirms the quote is live-present (⚠️ = couldn't confirm; never changes the verdict, since
   pages 403/paywall/JS-render). Spec updated (`gates/rigor.md`). Demo: black-death's 3 quotes
   confirmed at their live URLs; nuclear's 2 flagged ⚠️ (JS/blocked).

**Negative tests (proof the gates are not rubber stamps):**
- Drop a position tag → coverage < 100%, `UNHANDLED`, FAIL.
- Fabricate/redact a saved source quote → `quote NOT in source`, FAIL.
- Mutate a claimed number vs the reproduced value → `MISMATCH`, FAIL (smoke).
- Namedrop-only engagement → `UNHANDLED` (paragraph rule), FAIL.

**Known limitations (honest, not yet closed):**
- The divergence gate enforces structural coverage, not argument *quality* — a bad steelman in a
  long paragraph still passes. Quality is enforced by the loop (cartographer/advocate/adversary +
  orchestrator judgment), not the gate.
- `--verify-sources` cannot confirm quotes behind bot-blocks / JS / paywalls (non-fatal by design).
- The **honest A/B test** (gated loop vs freehand, same topic) that `DESIGN.md` calls for is still
  not run — it is the real proof the gates raise quality, and remains the top open item.
- Only `nuclear-safety` has a complete held-out judgment panel, and it is `REVISE`. The other three
  papers do not yet have complete D2/D3/D4b/D5 panels, so any mechanical `SHIP` label for them is
  provisional rather than a release verdict.
- The current eval harness is not fail-closed on missing panel fields and does not enforce every
  `EVAL.md` verdict condition. The current rigor gate also does not make DVC reproduction failure
  independently fatal. Both remain implementation conformance work; neither was changed here.

## 2026-07-09 — reset + pilot
Reset to the two-gate topic→paper workflow; adopted DVC for Gate 2; first pilot
(`runs/ai-employment`) passed both gates on real data.
