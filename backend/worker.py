import asyncio
import logging
from datetime import timedelta
from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import select, delete
from backend.config import settings
from backend.db import Session, engine
from backend.documents import parse, DocumentError
from backend.models import Document, Chunk, Audit, KnowledgeBase, Evaluation, now
from backend.evaluation import run_evaluation
from backend.pipeline import run_audit
from backend.runtime import embed

log = logging.getLogger("auditor.worker")


async def ingest_document(ctx, document_id: str):
    cfg = settings()
    async with Session() as db:
        doc = await db.scalar(select(Document).where(Document.id == document_id).with_for_update())
        if not doc or doc.status != "pending":
            return
        doc.status, doc.updated_at = "indexing", now()
        doc.attempts += 1
        await db.commit()
    try:
        async with Session() as db:
            doc = await db.get(Document, document_id)
            if not doc:
                return
            # All source mutations/audit publication use the same KB lock, preventing deletion resurrection.
            kb = await db.scalar(select(KnowledgeBase).where(KnowledgeBase.id == doc.kb_id).with_for_update())
            doc = await db.scalar(select(Document).where(Document.id == document_id).with_for_update())
            if not kb or not doc or doc.status != "indexing":
                return
            content = (cfg.data_dir / "files" / doc.id).read_bytes()
            passages = await asyncio.to_thread(parse, content, doc.extension, doc.name)
            vectors = await asyncio.to_thread(embed, [p.text for p in passages])
            contextual = await asyncio.to_thread(
                embed, [doc.name + " / " + p.context + "\n" + p.text for p in passages]
            )
            await db.execute(delete(Chunk).where(Chunk.document_id == doc.id))
            for ordinal, (p, vector, context_vector) in enumerate(zip(passages, vectors, contextual)):
                db.add(
                    Chunk(
                        document_id=doc.id,
                        kb_id=doc.kb_id,
                        ordinal=ordinal,
                        text=p.text,
                        context=p.context,
                        page=p.page,
                        line_start=p.line_start,
                        line_end=p.line_end,
                        embedding=vector,
                        contextual_embedding=context_vector,
                    )
                )
            doc.status, doc.error = "indexed", None
            doc.embedding_model, doc.chunk_count, doc.updated_at = cfg.embedding_model, len(passages), now()
            await db.commit()
    except Exception as exc:
        async with Session() as db:
            doc = await db.get(Document, document_id)
            if doc:
                message = (
                    str(exc)
                    if isinstance(exc, DocumentError)
                    else "Indexing failed. Check model setup or retry."
                )
                doc.status = "needs_ocr" if message.startswith("needs_ocr:") else "failed"
                doc.error, doc.updated_at = message, now()
                await db.commit()
        log.error("document_ingestion_failed document_id=%s error_type=%s", document_id, type(exc).__name__)


async def audit_answer(ctx, audit_id: str):
    async with Session() as db:
        audit = await db.scalar(select(Audit).where(Audit.id == audit_id).with_for_update())
        if not audit or audit.status != "pending":
            return
        audit.status, audit.updated_at = "running", now()
        audit.attempts += 1
        await db.commit()
    try:
        async with Session() as db:
            audit = await db.get(Audit, audit_id)
            if not audit:
                return
            kb = await db.scalar(
                select(KnowledgeBase).where(KnowledgeBase.id == audit.kb_id).with_for_update()
            )
            audit = await db.scalar(select(Audit).where(Audit.id == audit_id).with_for_update())
            if not kb or not audit or audit.status != "running":
                return
            result = await run_audit(db, kb.id, audit.question, audit.answer, audit.mode, audit.provider)
            result["queue_wait_ms"] = round((audit.updated_at - audit.created_at).total_seconds() * 1000)
            result["end_to_end_ms"] = round((now() - audit.created_at).total_seconds() * 1000)
            audit.result, audit.status = result, "completed"
            audit.completed_at = audit.updated_at = now()
            await db.commit()
    except Exception as exc:
        from backend.providers import ProviderError

        async with Session() as db:
            audit = await db.get(Audit, audit_id)
            if audit:
                audit.status = "failed"
                audit.error = (
                    str(exc)
                    if isinstance(exc, (ProviderError, DocumentError, ValueError))
                    else "Audit timed out."
                    if isinstance(exc, TimeoutError)
                    else "Audit failed. Check model setup and retry."
                )
                audit.updated_at = now()
                await db.commit()
        log.error("audit_failed audit_id=%s error_type=%s", audit_id, type(exc).__name__)


async def reconcile(ctx):
    cutoff = now() - timedelta(minutes=10)
    async with Session() as db:
        for model, active in [(Document, "indexing"), (Audit, "running"), (Evaluation, "running")]:
            stale = (
                await db.scalars(
                    select(model)
                    .where(model.status == active, model.updated_at < cutoff)
                    .with_for_update(skip_locked=True)
                )
            ).all()
            for item in stale:
                item.status = "pending" if item.attempts < 3 else "failed"
                item.updated_at = now()
                item.error = (
                    "Worker interrupted; retry budget exhausted." if item.status == "failed" else None
                )
        await db.commit()
        docs = (await db.scalars(select(Document).where(Document.status == "pending").limit(100))).all()
        audits = (await db.scalars(select(Audit).where(Audit.status == "pending").limit(100))).all()
        for doc in docs:
            await ctx["redis"].enqueue_job(
                "ingest_document", doc.id, _job_id=f"ingest:{doc.id}:{doc.attempts}"
            )
        for audit in audits:
            await ctx["redis"].enqueue_job(
                "audit_answer", audit.id, _job_id=f"audit:{audit.id}:{audit.attempts}"
            )

    async with Session() as db:
        evaluations = (await db.scalars(select(Evaluation).where(Evaluation.status == "pending"))).all()
        for row in evaluations:
            await ctx["redis"].enqueue_job(
                "run_evaluation", row.id, _job_id="eval:" + row.id + ":" + str(row.attempts)
            )


async def startup(ctx):
    (settings().data_dir / "files").mkdir(parents=True, exist_ok=True)
    await reconcile(ctx)


async def shutdown(ctx):
    await engine.dispose()


class WorkerSettings:
    functions = [ingest_document, audit_answer, run_evaluation]
    redis_settings = RedisSettings.from_dsn(settings().redis_url)
    cron_jobs = [cron(reconcile, second={0, 10, 20, 30, 40, 50}, run_at_startup=True)]
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 2
    job_timeout = 300
    keep_result = 5
    health_check_interval = 15
