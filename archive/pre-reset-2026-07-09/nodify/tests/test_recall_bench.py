"""TC-F: deterministic recall benchmark (R2). A fixed corpus where each doc's
discriminating term lives ONLY in its archived body (not title/summary) — so
recall@1 is perfect only when the body is scored. This test would fail on the
pre-R2 ranker (title+summary only) and gates the improvement against regression.
"""

from __future__ import annotations

from tests.conftest import write_json

# doc_id (assigned in order) -> (title, summary, body-with-unique-term, gold query)
CORPUS = [
    ("劳动力市场综述 A", "宏观就业趋势的总体回顾",
     "This report analyzes translator and translation jobs displaced by machine translation.",
     "translator translation jobs"),
    ("行业观察 B", "企业侧的用工变化",
     "Salesforce cut customer support headcount as Agentforce handled interactions.",
     "customer support headcount"),
    ("学术研究 C", "任务暴露度测算",
     "Eloundou task-level exposure estimates show 80 percent of workers affected by LLMs.",
     "task exposure LLM estimates"),
    ("统计口径 D", "官方就业统计",
     "OECD found little detectable effect of AI on aggregate employment levels.",
     "OECD aggregate employment detectable"),
    ("入门级分析 E", "年龄分层的就业效应",
     "Stanford ADP payroll data show entry-level early-career employment decline.",
     "entry-level early-career payroll"),
    ("政策工具 F", "劳动力市场干预",
     "Active labor market policy reskilling programs meta-analysis effectiveness.",
     "reskilling active labor market policy"),
    ("裁员追踪 G", "AI 归因裁员统计",
     "Challenger tracker counted AI-attributed layoffs rising sharply.",
     "Challenger AI-attributed layoffs tracker"),
    ("互补岗位 H", "新增岗位证据",
     "LinkedIn economic graph shows new AI engineer and annotator roles created.",
     "AI engineer annotator new roles"),
]


def _seed(session, tmp_path):
    session("add", "--statement", "AI 对就业的净效应?")            # N-0001
    session("add", "--parent", "N-0001", "--statement", "证据枢纽")   # N-0002 (query node)
    for i, (title, summary, body, _q) in enumerate(CORPUS, 1):
        f = tmp_path / f"d{i}.txt"
        f.write_text(body, encoding="utf-8")
        session("docs", "ingest", "--file", write_json(tmp_path / f"d{i}.json", {
            "kind": "report", "title": title, "url": f"https://ex.org/{i}",
            "text_file": str(f), "summary": summary,
            "bindings": [{"node_id": "N-0002", "relation": "context"}]}))


def test_recall_body_term_ranks_first(session, tmp_path):
    """Each gold query's discriminating term is body-only; the improved ranker
    must place that doc first."""
    _seed(session, tmp_path)
    for i, (_t, _s, _b, query) in enumerate(CORPUS, 1):
        gold = f"DOC-{i:04d}"
        hits = session("recall", "--node", "N-0002", "--query", query)["data"]["recall"]["hits"]
        assert hits[0]["doc_id"] == gold, (query, gold, [h["doc_id"] for h in hits[:3]])


def test_recall_at_3_and_mrr_meet_target(session, tmp_path):
    _seed(session, tmp_path)
    hits_at_3 = 0
    rr_sum = 0.0
    n = len(CORPUS)
    for i, (_t, _s, _b, query) in enumerate(CORPUS, 1):
        gold = f"DOC-{i:04d}"
        ranked = [h["doc_id"] for h in
                  session("recall", "--node", "N-0002", "--query", query)["data"]["recall"]["hits"]]
        if gold in ranked[:3]:
            hits_at_3 += 1
        if gold in ranked:
            rr_sum += 1.0 / (ranked.index(gold) + 1)
    recall_at_3 = hits_at_3 / n
    mrr = rr_sum / n
    assert recall_at_3 >= 0.9, f"recall@3={recall_at_3:.3f}"
    assert mrr >= 0.9, f"MRR={mrr:.3f}"


def test_recall_flags_zero_match(session, tmp_path):
    _seed(session, tmp_path)
    hits = session("recall", "--node", "N-0002",
                   "--query", "quantum entanglement unrelated")["data"]["recall"]["hits"]
    # nothing matches; every hit is honestly flagged as a non-match
    assert hits and all("NO query-token match" in h["why"] for h in hits)
