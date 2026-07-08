"""The frozen schema set is the law: valid records pass, unknown fields and
out-of-enum values are rejected, kind↔status conditionals hold (P1/P5/P9)."""

from __future__ import annotations

from nodify import schemas

VALID_NODE = {
    "schema": "node.v1", "node_id": "N-0001", "parent_id": None,
    "kind": "viewpoint", "statement": "X导致Y", "why_helps_parent": None,
    "orientation": None, "status": "open", "status_note": None,
    "promotion_note": None, "stuck_reason": None, "revises": None,
    "created_at": "2026-07-09T12:00:00Z", "created_by": "main",
}


def test_schema_set_is_exactly_the_five_frozen_files():
    assert schemas.SCHEMA_NAMES == (
        "envelope.v1", "session.v1", "node.v1", "synthesis.v1", "event.v1")
    assert schemas.schema_set_hash().startswith("sha256:")
    assert schemas.schema_set_hash() == schemas.schema_set_hash()  # stable


def test_valid_node_passes_and_unknown_field_rejected():
    assert schemas.validate(VALID_NODE) == []
    assert schemas.validate({**VALID_NODE, "extra": 1})  # additionalProperties
    assert schemas.validate({**VALID_NODE, "status": "weird"})


def test_kind_status_conditionals():
    claim = {**VALID_NODE, "kind": "claim", "status": "pending",
             "promotion_note": "note"}
    assert schemas.validate(claim) == []
    # viewpoint may not hold claim statuses, and vice versa
    assert schemas.validate({**VALID_NODE, "status": "pending"})
    assert schemas.validate({**claim, "status": "open"})
    # a claim requires a promotion_note; stuck requires a reason
    assert schemas.validate({**claim, "promotion_note": None})
    assert schemas.validate({**claim, "status": "stuck", "stuck_reason": None})
    assert schemas.validate({**claim, "status": "stuck",
                             "stuck_reason": "evidence"}) == []


def test_synthesis_and_event_shapes():
    syn = {
        "schema": "synthesis.v1", "synthesis_id": "SYN-0001", "node_id": "N-0001",
        "lean": "mixed", "summary": "s", "confidence": "low",
        "based_on": {"children": [], "evidence": [{
            "ref_id": "E-01", "title": "t", "url": None, "locator": "a.md:3",
            "quote": None, "tool": None, "note": None}]},
        "open_questions": [], "revises": None,
        "created_at": "2026-07-09T12:00:00Z",
    }
    assert schemas.validate(syn) == []
    assert schemas.validate({**syn, "lean": "score:0.7"})
    ev = {"schema": "event.v1", "event_id": "EV-000001",
          "at": "2026-07-09T12:00:00Z", "actor": "main", "command": "add",
          "mutating": True, "touched": ["N-0001"], "summary": "add 1"}
    assert schemas.validate(ev) == []
    assert schemas.validate({"schema": "nope.v9"})
