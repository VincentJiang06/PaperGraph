"""Compiler (docs/06, docs/08 B9/B10): the only prose producer.

Two phases: `dry-run` builds the deterministic section plan, detects the five gap
kinds, and reports writing_ready; `draft-map` derives the byte-identical DraftMap
and enqueues one prose work item per section. `ingest-prose` runs V-PROSE as a
work item's validate-pass, promotes agent_outputs/prose/ to compiler/prose/, and
commits the item.
"""
