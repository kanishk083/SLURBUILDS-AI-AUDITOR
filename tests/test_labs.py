import numpy as np
import pytest
from datetime import timedelta
from arq import create_pool
from arq.connections import RedisSettings
from backend.config import settings
from backend.db import Session
from backend.models import Audit, now
from backend.labs import late_pool, late_interaction, hierarchy, entity_graph, graph_expand, workspace_lab
from backend.worker import reconcile
from tests.test_auditor import indexed_sample

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_late_pooling_is_bounded_and_normalized():
    text = "A document states the Basic price. The same document specifies the Pro price."
    boundary = text.index(" The")
    vectors = late_pool(text, [(0, boundary), (boundary + 1, len(text))])
    assert len(vectors) == 2
    assert all(len(v) == 384 and np.isclose(np.linalg.norm(v), 1) for v in vectors)
    with pytest.raises(ValueError, match="context window"):
        late_pool(" ".join(["token"] * 400), [(0, 10)])


async def test_maxsim_ranks_matching_text():
    scores = late_interaction(
        "PDF upload formats", ["PDF uploads are supported.", "Fresh oranges grow on citrus trees."]
    )
    assert scores[0] > scores[1]


async def test_hierarchy_and_graph_preserve_source_ids():
    passages = [
        {"id": "A", "text": "Basic and Pro are pricing plans."},
        {"id": "B", "text": "Pro includes PDF uploads."},
        {"id": "C", "text": "Backup retention is 30 days."},
    ]
    tree = hierarchy(passages, clusters=2)
    assert {source for node in tree["nodes"] for source in node["source_ids"]} == {"A", "B", "C"}
    graph = entity_graph(passages)
    assert "A" in graph_expand(graph, "Pro")
    assert "B" in graph_expand(graph, "Pro")


async def test_scoped_database_labs_and_query_plans(client):
    kb, _, _ = await indexed_sample(client)
    async with Session() as db:
        result = await workspace_lab(db, kb, "hnsw", "The Pro plan price")
        row = result["results"][0]
        assert row["neighbor_recall"] is not None
        assert row["plan"]
        assert set(row["candidate_ids"]).issubset(set(row["exact_ids"])) or row["neighbor_recall"] <= 1
    await client.post("/api/v1/auth/guest")
    response = await client.post("/api/v1/labs/run", json={"kb_id": kb, "kind": "graph", "query": "Pro"})
    assert response.status_code == 404


async def test_interrupted_audit_is_reconciled_without_losing_its_budget(client):
    kb, sample, _ = await indexed_sample(client)
    response = await client.post("/api/v1/audits", json={"kb_id": kb, "answer": sample["answer"]})
    audit_id = response.json()["id"]
    async with Session() as db:
        audit = await db.get(Audit, audit_id)
        audit.status = "running"
        audit.attempts = 1
        audit.updated_at = now() - timedelta(minutes=11)
        await db.commit()
    pool = await create_pool(RedisSettings.from_dsn(settings().redis_url))
    try:
        await reconcile({"redis": pool})
    finally:
        await pool.aclose()
    async with Session() as db:
        audit = await db.get(Audit, audit_id)
        assert audit.status == "pending"
        assert audit.attempts == 1


async def test_background_evaluation_report_is_owned_and_labeled(client):
    from backend.evaluation import run_evaluation

    kb, _, _ = await indexed_sample(client)
    response = await client.post(
        "/api/v1/evaluations/run", json={"kb_id": kb, "modes": ["baseline"], "split": "held_out"}
    )
    assert response.status_code == 202
    identifier = response.json()["id"]
    await run_evaluation({}, identifier)
    report = (await client.get("/api/v1/evaluations/" + identifier)).json()
    assert report["status"] == "completed", report
    assert report["result"]["modes"]["baseline"]["case_count"] == 8
    assert report["result"]["human_reviewed"] is False
    await client.post("/api/v1/auth/guest")
    assert (await client.get("/api/v1/evaluations/" + identifier)).status_code == 404


async def test_comparison_modes_hold_retrieval_constant(client):
    from backend.pipeline import run_audit

    kb, _, _ = await indexed_sample(client)
    async with Session() as db:
        plain = await run_audit(db, kb, "", "PDF uploads are supported.", "baseline")
        filtered = await run_audit(db, kb, "", "PDF uploads are supported.", "filter")
    a = next(s for s in plain["claims"][0]["trace"] if s["step"] == "evaluate")
    b = next(s for s in filtered["claims"][0]["trace"] if s["step"] == "evaluate")
    assert a["retrieval_mode"] == b["retrieval_mode"] == "hybrid"
    assert {c["id"] for c in a["candidates"]} == {c["id"] for c in b["candidates"]}
    assert all(c["accepted"] for c in a["candidates"])
