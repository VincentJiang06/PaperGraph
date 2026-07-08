"""F11/D11 — `docs render-prompt` / `proof render-prompt`: the dispatch prompt
is PRODUCED by code, with the registry excerpt V-SRC-05-checked at the boundary.

  * a docs prompt embeds the request fields, the member's OWN plan JSON, the
    registry excerpt and the declared output path;
  * an excerpt-completeness violation is a V-SRC-05 DomainError (never a
    silently thin prompt);
  * the critic prompt renders with {inputs} = claim/plans/merged/query_log paths;
  * S5 advisory leads are PROMPT-ONLY: they ride in the text/envelope and the
    request state never changes (V-SEM-04).
"""

from __future__ import annotations

import pytest

from paperproof.docsdb import registry, wave as wave_mod
from paperproof.errors import DomainError
from paperproof.paths import paths_for
from paperproof.prompts import render
from paperproof.prooftask import builder
from paperproof.queue import engine
from paperproof.store import jsonl

from tests.fakes import scenario
from tests.fakes.workers import FakeDocsWorker

pytestmark = pytest.mark.contract


def _paths(pp):
    return paths_for(pp.tmp_path, "p4-ldi")


def _open_docs_item(paths, pp):
    scenario.seed_docs_facts(paths, [scenario.FACT_CLAIM])
    env = pp("docs", "request", "--target", "NODE-003",
             "--need", "Evidence on 2022 LDI collateral calls.", "--hint", "BoE FSR 2022")
    return env["data"]["request_id"], env["data"]["work_item_id"]


def test_docs_render_prompt_contains_plan_excerpt_and_output(project, pp):
    paths = _paths(pp)
    # a learned T1 profile that matches the request facets rides into {registry}.
    registry.learn(paths, [("boe.example", "official_report")], {}, now="2026-07-07T00:00:00Z")
    dr_id, wi_id = _open_docs_item(paths, pp)

    env = pp("docs", "render-prompt", "--work-item", wi_id)
    data = env["data"]
    text = data["prompt"]
    assert data["template"] == "docs_worker"
    assert dr_id in text                                     # request fields filled
    assert "Evidence on 2022 LDI collateral calls." in text
    assert f'"plan_id": "SP-{dr_id}"' in text                # embedded plan JSON
    assert '"queries"' in text
    assert "boe.example [T1_official]" in text               # the registry excerpt
    assert f"agent_outputs/docs_results/{dr_id}.docs_result.json" in text
    assert "{" + "registry" + "}" not in text                # no unfilled placeholder
    assert "{output_file}" not in text


def test_docs_render_prompt_excerpt_violation_is_v_src_05(project, pp, monkeypatch):
    """An excerpt that drops a required (T1 / facet-matched) profile is refused
    with V-SRC-05 — the render is where the rule is enforced (D11)."""
    paths = _paths(pp)
    registry.learn(paths, [("boe.example", "official_report")], {}, now="2026-07-07T00:00:00Z")
    _dr, wi_id = _open_docs_item(paths, pp)

    monkeypatch.setattr(registry, "matched_profiles", lambda *a, **k: [])
    with pytest.raises(DomainError) as exc:
        render.render_docs_prompt(paths, wi_id)
    assert "V-SRC-05" in exc.value.errors


def test_critic_render_prompt_fills_inputs(project, pp):
    paths = _paths(pp)
    dr_id, _ = _open_docs_item(paths, pp)
    started = pp("docs", "wave", "--request", dr_id, "--fan")["data"]

    docs_worker = FakeDocsWorker({"*": scenario.boe_docs_result_spec()})
    critic_env = None
    for m in sorted(started["members"], key=lambda m: m["work_item_id"]):
        claimed = pp("queue", "claim", "--queue", "docs_queue", "--agent", "w",
                     "--id", m["work_item_id"])["data"]["work_item"]
        docs_worker.run(claimed, paths.project_dir)
        critic_env = pp("docs", "wave-member", claimed["output_files"][0],
                        "--work-item", m["work_item_id"])["data"]
    critic_wi = critic_env["critic_work_item_id"]

    env = pp("docs", "render-prompt", "--work-item", critic_wi)
    text = env["data"]["prompt"]
    assert env["data"]["template"] == "critic_worker"
    assert scenario.FACT_CLAIM in text                        # the claim under search
    assert wave_mod.merged_relpath(dr_id) in text             # the merged result path
    for m in started["members"]:
        assert f"docs/plans/{m['plan_id']}.json" in text      # every member plan
    assert f"agent_outputs/coverage_reports/{started['wave_id']}.r1.coverage_report.json" in text
    assert "{inputs}" not in text and "{output_file}" not in text
    # the report's required wave_id is render-filled — the critic never guesses it.
    assert started["wave_id"] in text
    assert "{wave_id}" not in text


def test_advisory_leads_are_prompt_only(project, pp, monkeypatch):
    """V-SEM-04: leads appear in the PROMPT (and envelope) only — rendering never
    fulfills or mutates the request. Model absent ⇒ no leads, no block."""
    from paperproof.db import semantic

    paths = _paths(pp)
    dr_id, wi_id = _open_docs_item(paths, pp)

    # model absent: no leads, no ADVISORY block (the degrade is silent HERE only
    # because leads are optional intel, not retrieval — V-SEM-03 covers packs).
    env = pp("docs", "render-prompt", "--work-item", wi_id)
    assert env["data"]["advisory_leads"] == []
    assert "ADVISORY LEADS" not in env["data"]["prompt"]

    # a (faked) lead lands in the prompt; the request record does NOT change.
    fake = [{"request_id": "DR-999", "similarity": "0.912345", "need": "prior similar search"}]
    monkeypatch.setattr(semantic, "advisory_leads", lambda *a, **k: fake)
    out = render.render_docs_prompt(paths, wi_id)
    assert out["advisory_leads"] == fake
    assert "ADVISORY LEADS" in out["prompt"] and "DR-999" in out["prompt"]
    req = jsonl.latest_by_id(paths.resolve("docs/docs_requests.jsonl"), "request_id")[dr_id]
    assert req["status"] == "open" and req["fulfilled_by"] is None


def test_proof_render_prompt_fills_bundle(project, pp):
    paths = _paths(pp)
    scenario.seed_docs_facts(paths, [scenario.FACT_CLAIM])
    builder.build_frontier(paths, "test")
    item = next(i for i in engine.load_items(paths)
                if i["queue_name"] == "proof_queue" and i.get("bundle"))

    env = pp("proof", "render-prompt", "--work-item", item["work_item_id"])
    text = env["data"]["prompt"]
    assert env["data"]["template"] == "proof_worker"
    assert item["bundle"]["task_file"] in text
    assert item["bundle"]["context_pack"] in text
    assert item["bundle"]["docs_pack"] in text
    assert item["output_files"][0] in text
    assert item["target_id"] in text
    assert "{task_file}" not in text and "{output_file}" not in text

    # an unbundled item is refused with a pointer to build-tasks.
    bare = engine.enqueue(paths, queue_name="proof_queue", target_type="node",
                          target_id="NODE-002", actor="test")
    err = pp("proof", "render-prompt", "--work-item", bare["work_item_id"], expect=1)
    assert any("build-tasks" in e for e in err["errors"])


def test_retry_suffix_appended_after_a_validate_fail(project, pp):
    """docs/07 §retries + docs/10 §5: once an item's attempt failed validation,
    the NEXT rendered dispatch prompt carries the retry suffix filled with the
    recorded rules + per-rule detail. A first dispatch carries nothing."""
    paths = _paths(pp)
    registry.learn(paths, [("boe.example", "official_report")], {}, now="2026-07-07T00:00:00Z")
    _dr, wi_id = _open_docs_item(paths, pp)

    first = render.render_docs_prompt(paths, wi_id)["prompt"]
    assert "RETRY" not in first

    claimed = pp("queue", "claim", "--queue", "docs_queue", "--agent", "w",
                 "--id", wi_id)["data"]["work_item"]
    out_path = paths.project_dir / claimed["output_files"][0]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("{}", encoding="utf-8")
    engine.complete(paths, wi_id, "w")
    engine.validate_fail(paths, wi_id, ["V-DR-03"], "code",
                         detail={"V-DR-03": "worker-authored id field 'eu_id' at $.evidence_units[0]"})

    retried = render.render_docs_prompt(paths, wi_id)["prompt"]
    assert "RETRY 2/3" in retried
    assert "V-DR-03" in retried and "eu_id" in retried
    assert "{attempt}" not in retried and "{failed_rules_with_detail}" not in retried


def test_compiler_render_prompt_embeds_the_draft_map(project, pp):
    """D11 for the compile stage: `compiler render-prompt` fills the
    compile_worker template for a compile_queue prose item and embeds the
    latest DraftMap record (the docs-member SearchPlan embed pattern)."""
    paths = _paths(pp)
    jsonl.append(paths.resolve("compiler/draft_maps.jsonl"), {
        "schema_version": "draft_map.v1", "draft_map_id": "DRAFTMAP-000001",
        "project_id": "p4-ldi", "based_on_dry_run": "CDR-000001",
        "sections": [{"section_id": "S1", "node_ids": ["NODE-001"]}],
        "created_at": "2026-07-07T00:00:00Z",
    })
    item = engine.enqueue(paths, queue_name="compile_queue", target_type="section",
                          target_id="S1", task_id="PROSE-S1",
                          output_files=["agent_outputs/prose/S1.md"], actor="test")

    env = pp("compiler", "render-prompt", "--work-item", item["work_item_id"])
    data = env["data"]
    text = data["prompt"]
    assert data["template"] == "compile_worker"
    assert data["draft_map_id"] == "DRAFTMAP-000001"
    assert "Your section: S1" in text
    assert "agent_outputs/prose/S1.md" in text
    assert '"draft_map_id": "DRAFTMAP-000001"' in text        # embedded record
    assert "{draft_map_file}" not in text and "{section_id}" not in text
    assert "{output_file}" not in text

    # a non-compile item is refused.
    err = pp("compiler", "render-prompt", "--work-item", "WI-999999", expect=1)
    assert err["ok"] is False
