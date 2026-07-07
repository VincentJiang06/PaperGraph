"""Audit family: audit_report.v1 (docs/06)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from ._common import STRICT


class AuditFinding(BaseModel):
    model_config = STRICT

    kind: Literal["binding", "strength", "scope", "coverage"]
    location: str
    target_id: str
    detail: str


class AuditReport(BaseModel):
    model_config = STRICT

    schema_version: Literal["audit_report.v1"] = "audit_report.v1"
    audit_id: str
    project_id: str
    draft_ref: str
    findings: list[AuditFinding]
    passed: bool
    created_at: str
