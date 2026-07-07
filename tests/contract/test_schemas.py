"""Schema round-trip meta-test (docs/11 §7).

For every schema_version in the registry: the golden example parses; dump ->
parse -> dump is a fixed point; adding an unknown field rejects; each enum
(Literal) field rejects an out-of-enum value.
"""

from __future__ import annotations

import json
import types
import typing
from pathlib import Path

import pytest
from pydantic import ValidationError

from paperproof.schemas import REGISTRY
from paperproof.serialize import canonical_bytes

pytestmark = pytest.mark.contract

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "schemas"


def _fixture_path(schema_version: str) -> Path:
    return FIXTURES / f"{schema_version}.json"


def test_every_schema_has_exactly_one_fixture():
    on_disk = {p.stem for p in FIXTURES.glob("*.json")}
    registered = set(REGISTRY)
    assert on_disk == registered, {
        "missing_fixtures": sorted(registered - on_disk),
        "orphan_fixtures": sorted(on_disk - registered),
    }


@pytest.mark.parametrize("schema_version", sorted(REGISTRY))
def test_golden_parses_and_is_fixed_point(schema_version: str):
    model = REGISTRY[schema_version]
    raw = _fixture_path(schema_version).read_bytes()
    instance = model.model_validate_json(raw)
    assert instance.model_dump(mode="json")["schema_version"] == schema_version

    b2 = canonical_bytes(instance)
    reparsed = model.model_validate_json(b2)
    b3 = canonical_bytes(reparsed)
    assert b2 == b3, "dump -> parse -> dump must be a fixed point"


@pytest.mark.parametrize("schema_version", sorted(REGISTRY))
def test_unknown_field_rejected(schema_version: str):
    model = REGISTRY[schema_version]
    data = json.loads(_fixture_path(schema_version).read_bytes())
    data["____definitely_unknown_field____"] = 1
    with pytest.raises(ValidationError):
        model.model_validate(data)


def _literal_fields(model) -> list[str]:
    """Names of top-level fields whose annotation is Literal[...] or
    Optional[Literal[...]]."""
    out: list[str] = []
    for name, field in model.model_fields.items():
        if _contains_literal(field.annotation):
            out.append(name)
    return out


def _contains_literal(annotation) -> bool:
    origin = typing.get_origin(annotation)
    if origin is typing.Literal:
        return True
    if origin in (typing.Union, getattr(types, "UnionType", ())):
        return any(_contains_literal(a) for a in typing.get_args(annotation))
    return False


@pytest.mark.parametrize("schema_version", sorted(REGISTRY))
def test_enum_fields_reject_out_of_enum(schema_version: str):
    model = REGISTRY[schema_version]
    fixture = json.loads(_fixture_path(schema_version).read_bytes())
    literal_fields = _literal_fields(model)
    assert literal_fields, f"{schema_version} has no top-level enum field to test"
    for name in literal_fields:
        data = dict(fixture)
        data[name] = "__invalid_enum_value__"
        with pytest.raises(ValidationError):
            model.model_validate(data)
