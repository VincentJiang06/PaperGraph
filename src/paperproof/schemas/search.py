"""Search program family (docs/14 — S1; docs/15 — S2, ADOPTED/BINDING).

``search_plan.v1`` is the deterministic, immutable SearchPlan the plan compiler
emits from a DocsRequest + target/contract scope. It carries the facets, the
per-angle query templates, and the stop thresholds; the DocsWorker executes it
query by query and accounts for every ``qid`` (docs/14 worker accounting).

``search_wave.v1`` + ``coverage_report.v1`` (docs/15 — S2) turn one DocsRequest
into a wave: parallel per-angle members (each executing its S1 plan), a
deterministic merger, and a fresh adversarial coverage critic whose closed form
drives ≤2 bounded follow-up rounds. CODE computes the wave verdict; the critic
only fills the closed form.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel

from ._common import STRICT

# The five angles whose Q2 suffix is pinned in docs/14 §"The plan compiler".
Angle = Literal["official_stats", "academic", "industry", "counter", "news"]
QueryKind = Literal["core", "angle", "hint", "narrow", "counter", "extra"]


class SearchFacets(BaseModel):
    model_config = STRICT

    core_terms: list[str]
    scope_terms: list[str]
    counter_terms: list[str]


class SearchQuery(BaseModel):
    model_config = STRICT

    qid: str
    kind: QueryKind
    text: str


class SearchStop(BaseModel):
    model_config = STRICT

    max_queries: int
    min_docs: int
    min_eus: int


class SearchPlan(BaseModel):
    model_config = STRICT

    schema_version: Literal["search_plan.v1"] = "search_plan.v1"
    plan_id: str
    request_id: str
    project_id: str
    angle: Angle
    facets: SearchFacets
    queries: list[SearchQuery]
    stop: SearchStop


# --- S2 (docs/15): search_wave.v1 ------------------------------------------

WaveStatus = Literal["open", "merging", "critic", "followup", "closed"]


class WaveMember(BaseModel):
    """One wave member = a docs_queue WorkItem (target_type=request) + an
    angle-specific S1 plan (SP-DR-x-<angle>) + a distinct output path
    [V-WAVE-01]. ``round`` is the round it was opened in (round-1 members are
    the initial fan); ``origin`` cites why a follow-up member exists — an
    ``angle:<name>`` no_attempt gap or ``expected_source:<name>`` — required on
    every round>1 member [V-WAVE-04]. Round-1 members carry origin=null."""

    model_config = STRICT

    angle: Angle
    work_item_id: str
    plan_id: str
    round: int = 1
    origin: Optional[str] = None


class SearchWave(BaseModel):
    model_config = STRICT

    schema_version: Literal["search_wave.v1"] = "search_wave.v1"
    wave_id: str
    request_id: str
    project_id: str
    round: int
    members: list[WaveMember]
    status: WaveStatus
    created_at: str


# --- S2 (docs/15): coverage_report.v1 --------------------------------------

AngleCovered = Literal["yes", "tried_empty", "tried_blocked", "no_attempt"]
Presence = Literal["yes", "no", "n/a"]


class AngleCoverage(BaseModel):
    """Per-angle coverage verdict the critic fills. Mandatory angles must be
    answered [V-WAVE-03]; ``news`` is present only when the wave fanned it."""

    model_config = STRICT

    official_stats: Optional[AngleCovered] = None
    academic: Optional[AngleCovered] = None
    industry: Optional[AngleCovered] = None
    counter: Optional[AngleCovered] = None
    news: Optional[AngleCovered] = None


class CoverageForm(BaseModel):
    model_config = STRICT

    angle_covered: AngleCoverage
    primary_source_present: Presence
    disconfirming_captured: Presence


class ExpectedSource(BaseModel):
    model_config = STRICT

    name: str
    why: str
    suggested_query: str


class CoverageReport(BaseModel):
    """The critic's closed form (docs/15). READ-ONLY worker output: it carries
    NO documents or evidence_units — the merger already produced those. CODE
    computes the wave verdict from this form; the critic never does."""

    model_config = STRICT

    schema_version: Literal["coverage_report.v1"] = "coverage_report.v1"
    wave_id: str
    form: CoverageForm
    expected_sources: list[ExpectedSource]
    notes: str
