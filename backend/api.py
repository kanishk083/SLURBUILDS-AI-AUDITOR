import hashlib
import logging
import re
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal
from fastapi import FastAPI, Depends, Request, Response, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from redis.asyncio import Redis
from sqlalchemy import select, func, delete, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from backend.config import settings, ROOT
from backend.db import session, engine
from backend.models import User, LoginSession, KnowledgeBase, Document, Chunk, Audit, now
from backend.security import (
    current_user,
    owned_kb,
    hash_password,
    check_password,
    login_session,
    token_hash,
    rate_limit,
    COOKIE,
)
from backend.pipeline import MODES

cfg = settings()
log = logging.getLogger("auditor.api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app):
    (cfg.data_dir / "files").mkdir(parents=True, exist_ok=True)
    yield
    await engine.dispose()


app = FastAPI(title="AI Auditor", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)
DB = Annotated[AsyncSession, Depends(session)]


@app.middleware("http")
async def request_guards(request: Request, call_next):
    origin = request.headers.get("origin")
    if (
        request.method not in {"GET", "HEAD", "OPTIONS"}
        and origin
        and origin not in cfg.allowed_origins.split(",")
    ):
        return JSONResponse({"detail": "Request origin is not allowed."}, 403)
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Frame-Options"] = "DENY"
    log.info(
        "request method=%s route=%s status=%s duration_ms=%d",
        request.method,
        request.scope.get("route").path if request.scope.get("route") else "/unknown",
        response.status_code,
        (time.perf_counter() - started) * 1000,
    )
    return response


async def user(request: Request, db: DB):
    return await current_user(request, db)


UserDep = Annotated[User, Depends(user)]


class Credentials(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("email")
    @classmethod
    def email_valid(cls, value):
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email.")
        return value


class KBInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def nonempty_name(cls, value):
        if not value.strip():
            raise ValueError("Library name cannot be blank.")
        return value.strip()


class AuditInput(BaseModel):
    kb_id: str = Field(min_length=36, max_length=36)
    question: str = Field(default="", max_length=2000)
    answer: str = Field(min_length=3, max_length=12000)
    mode: Literal[
        "baseline",
        "filter",
        "corrective",
        "contextual",
        "parent_window",
        "multi_query",
        "hyde",
        "adaptive",
        "agentic",
    ] = "corrective"
    provider: Literal["local_nli", "hosted"] = "local_nli"

    @field_validator("answer")
    @classmethod
    def nonempty_answer(cls, value):
        if not value.strip():
            raise ValueError("Answer must contain non-whitespace text.")
        return value.strip()


def doc_dict(doc):
    return {
        "id": doc.id,
        "kb_id": doc.kb_id,
        "name": doc.name,
        "status": doc.status,
        "error": doc.error,
        "chunk_count": doc.chunk_count,
        "created_at": doc.created_at.isoformat(),
        "embedding_model": doc.embedding_model,
        "attempts": doc.attempts,
    }


def audit_dict(audit, detail=False):
    result = {
        "id": audit.id,
        "kb_id": audit.kb_id,
        "question": audit.question,
        "answer": audit.answer,
        "mode": audit.mode,
        "provider": audit.provider,
        "status": audit.status,
        "error": audit.error,
        "created_at": audit.created_at.isoformat(),
    }
    if detail:
        result["result"] = audit.result
    elif audit.result:
        result["counts"] = audit.result.get("counts")
        result["latency_ms"] = audit.result.get("latency_ms")
    return result


@app.get("/health")
async def health():
    return {"status": "ok", "service": "AI Auditor"}


@app.get("/ready")
async def ready(db: DB):
    await db.execute(text("SELECT 1"))
    redis = Redis.from_url(cfg.redis_url)
    try:
        await redis.ping()
    finally:
        await redis.aclose()
    return {"status": "ready"}


@app.get("/api/v1/config")
async def config():
    return {
        "demo_enabled": cfg.demo_enabled,
        "modes": MODES,
        "default_provider": cfg.audit_provider,
        "hosted_configured": bool(cfg.anthropic_api_key and cfg.anthropic_model),
        "embedding_model": cfg.embedding_model,
        "nli_model": cfg.nli_model,
        "max_claims": cfg.max_claims,
    }


async def create_user(db, email, password, response):
    account = User(email=email, password_hash=hash_password(password))
    db.add(account)
    await db.flush()
    kb = KnowledgeBase(owner_id=account.id, name="My reference library")
    db.add(kb)
    await login_session(db, account.id, response)
    await db.commit()
    return {"id": account.id, "email": account.email}


@app.post("/api/v1/auth/register", status_code=201)
async def register(body: Credentials, request: Request, response: Response, db: DB):
    await rate_limit("auth:" + hashlib.sha256(request.client.host.encode()).hexdigest(), 20)
    try:
        return await create_user(db, body.email, body.password, response)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Account could not be created. Use another email or sign in.")


@app.post("/api/v1/auth/guest", status_code=201)
async def guest(request: Request, response: Response, db: DB):
    if not cfg.demo_enabled:
        raise HTTPException(404, "Demo sessions are disabled.")
    await rate_limit("guest:" + hashlib.sha256(request.client.host.encode()).hexdigest(), 20)
    return await create_user(
        db, f"guest-{secrets.token_hex(12)}@demo.invalid", secrets.token_urlsafe(32), response
    )


@app.post("/api/v1/auth/login")
async def login(body: Credentials, request: Request, response: Response, db: DB):
    await rate_limit("auth:" + hashlib.sha256(request.client.host.encode()).hexdigest(), 20)
    account = await db.scalar(select(User).where(User.email == body.email))
    if not account or not check_password(body.password, account.password_hash):
        raise HTTPException(401, "Email or password is incorrect.")
    await login_session(db, account.id, response)
    await db.commit()
    return {"id": account.id, "email": account.email}


@app.get("/api/v1/auth/me")
async def me(account: UserDep):
    return {"id": account.id, "email": account.email}


@app.post("/api/v1/auth/logout")
async def logout(request: Request, response: Response, db: DB, account: UserDep):
    await db.execute(
        delete(LoginSession).where(LoginSession.token_hash == token_hash(request.cookies.get(COOKIE, "")))
    )
    await db.commit()
    response.delete_cookie(COOKIE)
    return {"ok": True}


@app.get("/api/v1/knowledge-bases")
async def list_kbs(db: DB, account: UserDep):
    items = (
        await db.scalars(
            select(KnowledgeBase)
            .where(KnowledgeBase.owner_id == account.id)
            .order_by(KnowledgeBase.created_at)
        )
    ).all()
    return [{"id": kb.id, "name": kb.name} for kb in items]


@app.post("/api/v1/knowledge-bases", status_code=201)
async def create_kb(body: KBInput, db: DB, account: UserDep):
    await rate_limit("kb:" + account.id, 10)
    kb = KnowledgeBase(owner_id=account.id, name=body.name.strip())
    db.add(kb)
    await db.commit()
    return {"id": kb.id, "name": kb.name}


@app.post("/api/v1/documents", status_code=202)
async def upload(db: DB, account: UserDep, kb_id: str = Form(...), file: UploadFile = File(...)):
    await owned_kb(db, kb_id, account.id, lock=True)
    await rate_limit("upload:" + account.id, 30)
    count = await db.scalar(select(func.count()).select_from(Document).where(Document.kb_id == kb_id))
    if count >= 50:
        raise HTTPException(422, "This library is limited to 50 documents.")
    name = Path((file.filename or "upload").replace("\\", "/")).name[:200]
    if any(ord(char) < 32 for char in name):
        raise HTTPException(422, "File name contains invalid control characters.")
    extension = Path(name).suffix.lower()
    if extension not in {".pdf", ".txt", ".md", ".markdown"}:
        raise HTTPException(415, "Upload a PDF, UTF-8 TXT or Markdown file.")
    content = await file.read(cfg.max_upload_bytes + 1)
    if not content or len(content) > cfg.max_upload_bytes:
        raise HTTPException(413, "File is empty or exceeds the 20 MB limit.")
    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(422, "File content does not match a PDF.")
    if extension != ".pdf":
        try:
            decoded = content.decode("utf-8-sig")
            if "\x00" in decoded:
                raise UnicodeError()
        except UnicodeError:
            raise HTTPException(422, "Text uploads must contain valid UTF-8 text.")
    checksum = hashlib.sha256(content).hexdigest()
    duplicate = await db.scalar(
        select(Document).where(Document.kb_id == kb_id, Document.checksum == checksum)
    )
    if duplicate:
        return {**doc_dict(duplicate), "duplicate": True}
    doc = Document(kb_id=kb_id, name=name, checksum=checksum, extension=extension)
    db.add(doc)
    await db.flush()
    path = cfg.data_dir / "files" / doc.id
    path.write_bytes(content)
    try:
        await db.commit()
    except Exception:
        path.unlink(missing_ok=True)
        raise
    # Persisted pending status is the outbox; the worker reconciles missed dispatches.
    return doc_dict(doc)


@app.get("/api/v1/documents")
async def documents(kb_id: str, db: DB, account: UserDep):
    await owned_kb(db, kb_id, account.id)
    docs = (
        await db.scalars(select(Document).where(Document.kb_id == kb_id).order_by(Document.created_at.desc()))
    ).all()
    return [doc_dict(doc) for doc in docs]


async def owned_document(db, document_id, user_id):
    doc = await db.scalar(
        select(Document)
        .join(KnowledgeBase)
        .where(Document.id == document_id, KnowledgeBase.owner_id == user_id)
    )
    if not doc:
        raise HTTPException(404, "Document not found.")
    return doc


@app.get("/api/v1/documents/{document_id}")
async def document(document_id: str, db: DB, account: UserDep):
    return doc_dict(await owned_document(db, document_id, account.id))


@app.get("/api/v1/documents/{document_id}/source")
async def source(document_id: str, db: DB, account: UserDep):
    doc = await owned_document(db, document_id, account.id)
    chunks = (
        await db.scalars(
            select(Chunk).where(Chunk.document_id == doc.id, Chunk.kb_id == doc.kb_id).order_by(Chunk.ordinal)
        )
    ).all()
    return {
        "document": doc_dict(doc),
        "passages": [
            {"id": c.id, "text": c.text, "page": c.page, "line_start": c.line_start, "line_end": c.line_end}
            for c in chunks
        ],
    }


@app.post("/api/v1/documents/{document_id}/retry", status_code=202)
async def retry_document(document_id: str, db: DB, account: UserDep):
    doc = await owned_document(db, document_id, account.id)
    await owned_kb(db, doc.kb_id, account.id, lock=True)
    await rate_limit("retry:" + account.id, 10)
    if doc.status not in {"failed", "needs_ocr"}:
        raise HTTPException(409, "Only failed documents can be retried.")
    doc.status, doc.error, doc.updated_at = "pending", None, now()
    await db.commit()
    return doc_dict(doc)


@app.delete("/api/v1/documents/{document_id}")
async def remove_document(document_id: str, db: DB, account: UserDep):
    doc = await owned_document(db, document_id, account.id)
    await owned_kb(db, doc.kb_id, account.id, lock=True)
    # Invalidate stored evidence too; stale citations must not outlive source deletion.
    audits = (await db.scalars(select(Audit).where(Audit.kb_id == doc.kb_id))).all()
    for audit in audits:
        audit.status, audit.result = "invalidated", {}
        audit.error = "Source library changed. Run the audit again."
    await db.delete(doc)
    await db.commit()
    (cfg.data_dir / "files" / document_id).unlink(missing_ok=True)
    return {"deleted": True}


@app.post("/api/v1/audits", status_code=202)
async def create_audit(body: AuditInput, db: DB, account: UserDep):
    await owned_kb(db, body.kb_id, account.id)
    await rate_limit("audit:" + account.id, 10)
    indexed = await db.scalar(
        select(func.count())
        .select_from(Document)
        .where(Document.kb_id == body.kb_id, Document.status == "indexed")
    )
    if not indexed:
        raise HTTPException(422, "Add at least one indexed reference document first.")
    if body.provider == "hosted" and not (cfg.anthropic_api_key and cfg.anthropic_model):
        raise HTTPException(422, "Hosted model is not configured. Choose local verification.")
    audit = Audit(
        kb_id=body.kb_id,
        question=body.question,
        answer=body.answer.strip(),
        mode=body.mode,
        provider=body.provider,
    )
    db.add(audit)
    await db.commit()
    return audit_dict(audit)


@app.get("/api/v1/audits")
async def list_audits(kb_id: str, db: DB, account: UserDep):
    await owned_kb(db, kb_id, account.id)
    items = (
        await db.scalars(
            select(Audit).where(Audit.kb_id == kb_id).order_by(Audit.created_at.desc()).limit(100)
        )
    ).all()
    return [audit_dict(item) for item in items]


@app.get("/api/v1/audits/{audit_id}")
async def get_audit(audit_id: str, db: DB, account: UserDep):
    audit = await db.scalar(
        select(Audit).join(KnowledgeBase).where(Audit.id == audit_id, KnowledgeBase.owner_id == account.id)
    )
    if not audit:
        raise HTTPException(404, "Audit not found.")
    return audit_dict(audit, True)


@app.post("/api/v1/demo/seed", status_code=202)
async def seed(kb_id: str, db: DB, account: UserDep):
    if not cfg.demo_enabled:
        raise HTTPException(404, "Demo is disabled.")
    await owned_kb(db, kb_id, account.id, lock=True)
    root = ROOT / "phase-00"
    for path in sorted((root / "sources").glob("*.md")):
        content = path.read_bytes()
        checksum = hashlib.sha256(content).hexdigest()
        existing = await db.scalar(
            select(Document).where(Document.kb_id == kb_id, Document.checksum == checksum)
        )
        if existing:
            continue
        doc = Document(kb_id=kb_id, name=path.name, checksum=checksum, extension=".md")
        db.add(doc)
        await db.flush()
        (cfg.data_dir / "files" / doc.id).write_bytes(content)
    await db.commit()
    import json

    case = json.loads((root / "case.json").read_text(encoding="utf-8"))
    return {"question": case["question"], "answer": case["original_answer"]}


@app.get("/api/v1/metrics")
async def metrics(db: DB, account: UserDep):
    rows = (
        await db.scalars(select(Audit).join(KnowledgeBase).where(KnowledgeBase.owner_id == account.id))
    ).all()
    completed = [a for a in rows if a.status == "completed"]
    latencies = sorted(a.result.get("latency_ms", 0) for a in completed)

    def percentile(p):
        return latencies[min(len(latencies) - 1, int((len(latencies) - 1) * p))] if latencies else None

    return {
        "attempted_audits": len(rows),
        "completed_audits": len(completed),
        "failed_audits": sum(a.status == "failed" for a in rows),
        "p50_ms": percentile(0.5),
        "p95_ms": percentile(0.95),
        "sample_count": len(latencies),
        "tokens": sum(
            a.result.get("usage", {}).get("input_tokens", 0)
            + a.result.get("usage", {}).get("output_tokens", 0)
            for a in completed
        ),
        "cost_note": "Local compute cost is not estimated; hosted token pricing is provider-specific.",
    }


class EvaluationInput(BaseModel):
    kb_id: str = Field(min_length=36, max_length=36)
    modes: list[Literal["baseline", "filter", "corrective"]] = Field(
        default=["baseline", "filter", "corrective"], min_length=1, max_length=3
    )
    split: Literal["development", "held_out"] = "development"


@app.post("/api/v1/evaluations/run", status_code=202)
async def create_evaluation(body: EvaluationInput, db: DB, account: UserDep):
    from backend.models import Evaluation

    await owned_kb(db, body.kb_id, account.id)
    await rate_limit("evaluation:" + account.id, 2, 300)
    docs = (
        await db.scalars(select(Document).where(Document.kb_id == body.kb_id, Document.status == "indexed"))
    ).all()
    expected = {"d1-plans.md", "d2-uploads.md", "d3-retention.md"}
    if not expected.issubset({d.name for d in docs}):
        raise HTTPException(422, "Fixture evaluation requires the three indexed sample documents.")
    row = Evaluation(
        owner_id=account.id,
        result={"kb_id": body.kb_id, "modes": list(dict.fromkeys(body.modes)), "split": body.split},
    )
    db.add(row)
    await db.commit()
    return {"id": row.id, "status": row.status}


@app.get("/api/v1/evaluations/{evaluation_id}")
async def get_evaluation(evaluation_id: str, db: DB, account: UserDep):
    from backend.models import Evaluation

    row = await db.scalar(
        select(Evaluation).where(Evaluation.id == evaluation_id, Evaluation.owner_id == account.id)
    )
    if not row:
        raise HTTPException(404, "Evaluation not found.")
    return {
        "id": row.id,
        "status": row.status,
        "result": row.result if row.status in {"completed", "failed"} else None,
    }


class LabInput(BaseModel):
    kb_id: str = Field(min_length=36, max_length=36)
    kind: Literal["late_pooling", "late_interaction", "hierarchy", "graph", "hnsw"]
    query: str = Field(min_length=3, max_length=1000)


@app.post("/api/v1/labs/run")
async def run_lab(body: LabInput, db: DB, account: UserDep):
    from backend.labs import workspace_lab

    await owned_kb(db, body.kb_id, account.id)
    await rate_limit("labs:" + account.id, 5, 60)
    try:
        async with __import__("asyncio").timeout(120):
            return await workspace_lab(db, body.kb_id, body.kind, body.query)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
