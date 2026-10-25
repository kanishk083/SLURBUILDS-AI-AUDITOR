import json
import uuid
import pytest
from sqlalchemy import select, func
from backend.documents import parse, extract_claims, DocumentError
from backend.pipeline import verdict, applicable
from backend.models import Chunk, Document
from backend.db import Session
from backend.worker import ingest_document, audit_answer
from backend.security import rate_limit
from tests.conftest import library, ROOT

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def indexed_sample(client):
    kb = await library(client)
    seeded = (await client.post("/api/v1/demo/seed", params={"kb_id": kb})).json()
    docs = (await client.get("/api/v1/documents", params={"kb_id": kb})).json()
    for doc in docs:
        await ingest_document({}, doc["id"])
    return kb, seeded, docs


async def test_authentication_and_origin(client):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 200
    r = await client.post(
        "/api/v1/knowledge-bases", json={"name": "Attack"}, headers={"Origin": "https://evil.invalid"}
    )
    assert r.status_code == 403
    await client.post("/api/v1/auth/logout")
    assert (await client.get("/api/v1/knowledge-bases")).status_code == 401


async def test_password_signup_login_and_session(client):
    email = f"{uuid.uuid4().hex}@example.com"
    body = {"email": email, "password": "a long private password"}
    assert (await client.post("/api/v1/auth/register", json=body)).status_code == 201
    assert (await client.post("/api/v1/auth/register", json=body)).status_code == 409
    await client.post("/api/v1/auth/logout")
    assert (
        await client.post("/api/v1/auth/login", json={**body, "password": "wrong password value"})
    ).status_code == 401
    assert (await client.post("/api/v1/auth/login", json=body)).status_code == 200


async def test_upload_validation_and_duplicate_handling(client):
    kb = await library(client)
    bad = await client.post(
        "/api/v1/documents", data={"kb_id": kb}, files={"file": ("bad.pdf", b"not a pdf")}
    )
    assert bad.status_code == 422
    bad = await client.post(
        "/api/v1/documents", data={"kb_id": kb}, files={"file": ("binary.md", b"\x00\xff")}
    )
    assert bad.status_code == 422
    body = {"file": ("notes.txt", b"The test artifact supports text uploads.")}
    r = await client.post("/api/v1/documents", data={"kb_id": kb}, files=body)
    assert r.status_code == 202
    duplicate = await client.post("/api/v1/documents", data={"kb_id": kb}, files=body)
    assert duplicate.json()["id"] == r.json()["id"]
    assert duplicate.json()["duplicate"] is True


async def test_ingestion_is_idempotent_and_source_is_traceable(client):
    kb, sample, docs = await indexed_sample(client)
    doc_id = docs[0]["id"]
    await ingest_document({}, doc_id)
    source = await client.get(f"/api/v1/documents/{doc_id}/source")
    assert source.status_code == 200
    assert source.json()["passages"]
    async with Session() as db:
        doc = await db.get(Document, doc_id)
        count = await db.scalar(select(func.count()).select_from(Chunk).where(Chunk.document_id == doc_id))
        assert doc.status == "indexed"
        assert count == doc.chunk_count
        assert doc.attempts == 1
    for passage in source.json()["passages"]:
        assert passage["line_start"] <= passage["line_end"]
        assert passage["id"]


async def test_cross_user_documents_and_audits_are_isolated(client):
    kb, sample, docs = await indexed_sample(client)
    response = await client.post("/api/v1/audits", json={"kb_id": kb, "answer": sample["answer"]})
    audit_id = response.json()["id"]
    # Start an independent user session, not another tab sharing a cookie.
    await client.post("/api/v1/auth/guest")
    assert (await client.get("/api/v1/documents", params={"kb_id": kb})).status_code == 404
    assert (await client.get(f"/api/v1/documents/{docs[0]['id']}/source")).status_code == 404
    assert (await client.delete(f"/api/v1/documents/{docs[0]['id']}")).status_code == 404
    assert (await client.get(f"/api/v1/audits/{audit_id}")).status_code == 404
    assert (
        await client.post("/api/v1/audits", json={"kb_id": kb, "answer": "Another answer."})
    ).status_code == 404


async def test_real_nli_audit_and_citations(client):
    kb, sample, docs = await indexed_sample(client)
    response = await client.post(
        "/api/v1/audits",
        json={"kb_id": kb, "question": sample["question"], "answer": sample["answer"], "mode": "corrective"},
    )
    assert response.status_code == 202
    audit_id = response.json()["id"]
    await audit_answer({}, audit_id)
    report = (await client.get("/api/v1/audits/" + audit_id)).json()
    assert report["status"] == "completed", report
    result = report["result"]
    key = json.loads((ROOT / "phase-00/reference-key.json").read_text(encoding="utf-8"))
    actual = {row["id"]: row for row in result["claims"]}
    assert len(actual) == 6
    for expected in key["labels"]:
        claim = actual[expected["claim_id"]]
        assert claim["verdict"] == expected["intended_verdict"], claim
        for citation in claim["citations"]:
            source = (await client.get("/api/v1/documents/" + citation["document_id"] + "/source")).json()
            assert any(citation["quote"] in p["text"] for p in source["passages"])
    assert result["counts"] == {"supported": 2, "contradicted": 2, "insufficient_evidence": 2}
    assert result["verification_pairs"] > 0
    assert all(len([s for s in c["trace"] if s["step"] == "evaluate"]) <= 3 for c in actual.values())


async def test_deleting_source_invalidates_stored_evidence_and_cannot_resurrect(client):
    kb, sample, docs = await indexed_sample(client)
    response = await client.post("/api/v1/audits", json={"kb_id": kb, "answer": sample["answer"]})
    audit_id = response.json()["id"]
    await audit_answer({}, audit_id)
    deleted = docs[0]["id"]
    assert (await client.delete("/api/v1/documents/" + deleted)).status_code == 200
    await ingest_document({}, deleted)
    assert (await client.get("/api/v1/documents/" + deleted + "/source")).status_code == 404
    report = (await client.get("/api/v1/audits/" + audit_id)).json()
    assert report["status"] == "invalidated"
    assert report["result"] == {}
    async with Session() as db:
        assert not await db.scalar(select(Chunk).where(Chunk.document_id == deleted))


async def test_redis_rate_limit_is_enforced(client):
    key = "integration:" + uuid.uuid4().hex
    await rate_limit(key, 2)
    await rate_limit(key, 2)
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as error:
        await rate_limit(key, 2)
    assert error.value.status_code == 429


async def test_parser_and_claim_offsets():
    passages = parse(b"# Heading\n\nOne fact here.\n\nSecond fact.\n", ".md", "example.md")
    assert [(p.line_start, p.line_end) for p in passages] == [(1, 1), (3, 3), (5, 5)]
    answer = "The price is INR 19.99.\nPDF uploads are supported."
    claims = extract_claims(answer)
    assert len(claims) == 2
    for c in claims:
        assert answer[c["answer_span"]["start"] : c["answer_span"]["end"]] == c["text"]
    with pytest.raises(DocumentError):
        parse(b"\x00", ".txt", "bad.txt")


async def test_opposing_evidence_is_not_discarded():
    assert applicable("The Pro plan costs INR 299.", "The Pro plan costs INR 499.")
    assert not applicable("The Pro plan costs INR 299.", "The Basic plan costs INR 199.")
    support = {"accepted": True, "relation": "supports"}
    contradiction = {"accepted": True, "relation": "contradicts"}
    assert verdict([contradiction])[0] == "contradicted"
    assert verdict([support, contradiction])[0] == "insufficient_evidence"
    assert verdict([])[0] == "insufficient_evidence"
