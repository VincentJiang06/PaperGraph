"""Shared nested models used across schema families.

These are not schema_version-bearing top-level models; they are reusable
sub-objects (Scope) with the strict config used everywhere.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, model_serializer

STRICT = ConfigDict(extra="forbid")


class Scope(BaseModel):
    """Structured scope object: optional keys period/region/actors/mechanisms.

    Same shape wherever a scope appears (contract, node, evidence, ...).
    Absent keys are omitted on serialization (never emitted as null) so that a
    partial scope round-trips to a fixed point.
    """

    model_config = STRICT

    period: Optional[str] = None
    region: Optional[str] = None
    actors: Optional[list[str]] = None
    mechanisms: Optional[list[str]] = None

    @model_serializer
    def _serialize(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if self.period is not None:
            out["period"] = self.period
        if self.region is not None:
            out["region"] = self.region
        if self.actors is not None:
            out["actors"] = self.actors
        if self.mechanisms is not None:
            out["mechanisms"] = self.mechanisms
        return out
