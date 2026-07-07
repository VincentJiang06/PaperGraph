"""M4 WebUI endpoint tests (docs/12 §9, docs/11 §9 M4 row).

FastAPI TestClient over EVERY /api route on an S7-shaped fixture project:
  * /api/overview answers the six Overview questions from ONE call, as real
    values (open, per-agent claims, blocked, committable/validated, frozen,
    stale_index);
  * reads genuinely go through the derived DuckDB index — after `db rebuild`,
    mutating a JSONL without rebuild leaves the endpoint serving the *indexed*
    value plus stale_index=true (proving it is NOT reading JSONL live);
  * S5's dead letter surfaces in /api/overview;
  * a DOM-presence smoke over the served static page (the data-testid hooks).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from paperproof.db import indexer
from paperproof.paths import paths_for
from paperproof.queue import engine
from paperproof.prooftask import builder
from paperproof.ui.app import create_app

from tests.fakes import scenario

pytestmark = pytest.mark.integration


@pytest.fixture
def monitor(project, pp):
    """S7-shaped state (all six questions non-trivial) + a fresh index."""
    paths = scenario.paths_for_pp(pp)
    info = scenario.monitor_fixture(paths)
    indexer.rebuild(paths)
    client = TestClient(create_app(pp.tmp_path, "p4-ldi"))
    return client, paths, info


# --- every route responds ---------------------------------------------------


def test_every_api_route_responds(monitor):
    client, paths, info = monitor
    frozen_id = info["frozen_id"]

    # GET routes (all JSON).
    assert client.get("/api/overview").status_code == 200
    assert client.get("/api/graph").status_code == 200
    assert client.get("/api/graph?lane=BFS-MAIN&state=active").status_code == 200
    assert client.get(f"/api/record/{frozen_id}").json()["found"] is True
    assert client.get("/api/record/NOPE-999").json()["found"] is False
    assert client.get("/api/queue").status_code == 200
    assert client.get("/api/queue?queue=proof_queue&status=blocked").status_code == 200
    assert client.get("/api/queue?queue=commit_queue").status_code == 200
    assert client.get("/api/events?limit=5").json()["count"] == 5
    assert client.get("/api/evidence").status_code == 200
    assert client.get("/api/compiler").status_code == 200
    tr = client.get(f"/api/trace/{frozen_id}").json()
    assert tr["found"] is True and tr["node_id"] == frozen_id

    # filter params actually filter.
    blocked = client.get("/api/queue?queue=proof_queue&status=blocked").json()
    assert blocked["count"] == info["expected"]["blocked"]
    assert all(i["status"] == "blocked" for i in blocked["items"])

    # events paging by ?after= cursor.
    evs = client.get("/api/events").json()["events"]
    assert len(evs) >= 2
    after = evs[0]["event_id"]
    paged = client.get(f"/api/events?after={after}").json()["events"]
    assert all(e["event_id"] != after for e in paged)


# --- the six Overview questions ---------------------------------------------


def test_overview_answers_six_questions(monitor):
    client, paths, info = monitor
    ov = client.get("/api/overview").json()
    exp = info["expected"]

    # Q1 What is open?
    assert ov["open"]["count"] == exp["open"]
    # Q2 Who is working on what?  (per-agent claims)
    assert ov["working"]["count"] == exp["working"]
    by_agent = ov["working"]["by_agent"]
    assert set(by_agent.keys()) == {"worker-1", "worker-2"}
    assert by_agent["worker-1"][0]["target_id"] == info["claimed"]["worker-1"]
    assert by_agent["worker-2"][0]["target_id"] == info["claimed"]["worker-2"]
    # Q3 What is blocked?
    assert ov["blocked"]["count"] == exp["blocked"]
    # Q4 What can be committed?  (validated awaiting commit apply)
    assert ov["committable"]["count"] == exp["committable"]
    # Q5 What is frozen?
    assert ov["frozen"]["count"] == exp["frozen"]
    assert ov["frozen"]["record_ids"] == [info["frozen_id"]]
    # Q6 Is the index stale?  (freshly rebuilt)
    assert ov["stale_index"] is False


# --- reads go through the INDEX, not live JSONL ------------------------------


def test_stale_flips_and_endpoint_reads_index_not_jsonl(monitor):
    client, paths, info = monitor

    ov0 = client.get("/api/overview").json()
    assert ov0["stale_index"] is False
    assert ov0["working"]["by_agent"]["worker-1"][0]["target_id"] == "NODE-007"

    # Mutate a canonical JSONL AFTER the rebuild, WITHOUT rebuilding the index:
    # release NODE-007's claim (appends a new work_item record -> queued, lease
    # cleared). If the endpoint read JSONL live, worker-1 would vanish.
    wi = client.get("/api/overview").json()["working"]["by_agent"]["worker-1"][0]["work_item_id"]
    engine.release(paths, wi)

    ov1 = client.get("/api/overview").json()
    # (1) the change is detected as staleness ...
    assert ov1["stale_index"] is True
    assert "queue/work_items.jsonl" in indexer.check(paths)["changed_sources"]
    # (2) ... but the served value is still the INDEXED (pre-release) one.
    assert ov1["working"]["by_agent"]["worker-1"][0]["target_id"] == "NODE-007"
    # the queue view is likewise still the indexed snapshot.
    q = client.get("/api/queue?queue=proof_queue&status=blocked").json()
    assert q["count"] == info["expected"]["blocked"]

    # A rebuild via the POST write action reconciles the index.
    assert client.post("/api/db/rebuild").json()["ok"] is True
    ov2 = client.get("/api/overview").json()
    assert ov2["stale_index"] is False
    # NODE-007 is back to queued -> no longer claimed by worker-1.
    assert "worker-1" not in ov2["working"]["by_agent"]


# --- POST write actions call the same code paths as the CLI -----------------


def test_post_claim_and_release(monitor):
    client, paths, info = monitor
    # A currently-queued proof item (validated node's edges are blocked; find a
    # queued one by re-opening: release worker-1's claim first).
    wi = client.get("/api/overview").json()["working"]["by_agent"]["worker-1"][0]["work_item_id"]
    r = client.post(f"/api/queue/{wi}/release")
    assert r.json()["ok"] is True
    # now claim it via the UI write path
    c = client.post(f"/api/queue/{wi}/claim", json={"agent": "ui-agent"})
    assert c.json()["ok"] is True
    assert engine.get_item(paths, wi)["status"] == "claimed"
    assert engine.get_item(paths, wi)["lease"]["claimed_by"] == "ui-agent"
    # unknown id -> 404
    assert client.post("/api/queue/WI-999999/claim", json={"agent": "x"}).status_code == 404


# --- S5 dead letter in /api/overview ----------------------------------------


def test_dead_letter_surfaces_in_overview(project, pp):
    paths = scenario.paths_for_pp(pp)
    scenario.seed_layer0(paths)
    builder.build_frontier(paths, "test")
    wi = "WI-000001"
    # claim + manual fail three times -> retries exhausted -> dead (docs/09 S5).
    for _ in range(3):
        if engine.get_item(paths, wi)["status"] == "queued":
            engine.claim(paths, queue_name="proof_queue", agent="w", wi_id=wi)
        pp("queue", "fail", wi, "--reason", "hung")
        if engine.get_item(paths, wi)["status"] == "dead":
            break
    assert engine.get_item(paths, wi)["status"] == "dead"

    indexer.rebuild(paths)
    client = TestClient(create_app(pp.tmp_path, "p4-ldi"))
    ov = client.get("/api/overview").json()
    assert ov["dead_letters"]["count"] >= 1
    assert any(d["work_item_id"] == wi for d in ov["dead_letters"]["items"])


# --- DOM smoke over the served static page ----------------------------------


def test_static_page_dom_hooks_and_no_external_fetch(monitor):
    client, paths, info = monitor
    html = client.get("/").text
    for testid in ("banner", "nav-overview", "nav-map", "nav-queue", "nav-evidence",
                   "nav-compiler", "queue-table", "drawer"):
        assert f'data-testid="{testid}"' in html, testid
    # vendored cytoscape is local, not a CDN.
    assert "vendor/cytoscape.min.js" in html
    assert "http://" not in html and "https://" not in html
    assert "cdn" not in html.lower()
    # the vendored asset is actually served locally (no external fetch).
    assert client.get("/vendor/cytoscape.min.js").status_code == 200
