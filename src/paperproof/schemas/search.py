"""Search program family (docs/14 — S1, ADOPTED/BINDING).

``search_plan.v1`` is the deterministic, immutable SearchPlan the plan compiler
emits from a DocsRequest + target/contract scope. It carries the facets, the
per-angle query templates, and the stop thresholds; the DocsWorker executes it
query by query and accounts for every ``qid`` (docs/14 worker accounting).
"""

from __future__ import annotations

from typing import Literal

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
