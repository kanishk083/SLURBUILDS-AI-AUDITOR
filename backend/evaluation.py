import time
import numpy as np
from sqlalchemy import select
from backend.config import ROOT, settings
from backend.models import Evaluation, KnowledgeBase, Document, now
from backend.db import Session
from backend.pipeline import run_audit, PIPELINE_VERSION

LABELS = ["supported", "contradicted", "insufficient_evidence"]


async def evaluate(db, kb_id: str, modes: list[str], split: str = "development") -> dict:
    import json

    dataset = json.loads((ROOT / "evaluation/cases.json").read_text(encoding="utf-8"))
    cases = [c for c in dataset["cases"] if c["split"] == split]
    output = {
        "pipeline_version": PIPELINE_VERSION,
        "retrieval_control": "same hybrid top-5; baseline disables grading/refinement; filter enables them; corrective adds bounded retries",
        "model": settings().nli_model,
        "nli_revision": settings().nli_revision,
        "embedding_revision": settings().embedding_revision,
        "source_manifest": [
            {"name": d.name, "checksum": d.checksum}
            for d in (
                await db.scalars(
                    select(Document).where(Document.kb_id == kb_id, Document.status == "indexed")
                )
            ).all()
        ],
        "dataset": dataset["version"],
        "split": split,
        "label_source": dataset["label_source"],
        "human_reviewed": dataset["human_reviewed"],
        "notice": dataset["notice"],
        "modes": {},
    }
    for mode in modes:
        rows = []
        started = time.perf_counter()
        for case in cases:
            report = await run_audit(db, kb_id, "", case["claim"], mode, "local_nli")
            claim = report["claims"][0]
            hit = None
            first_rank = None
            if case["source_name"]:
                candidates = [
                    e for step in claim["trace"] if step["step"] == "evaluate" for e in step["candidates"]
                ]
                hit = any(
                    e["document_name"] == case["source_name"]
                    and e["line_start"] <= case["line"] <= e["line_end"]
                    for e in candidates
                )
                first_round = next(
                    (step for step in claim["trace"] if step["step"] == "evaluate"), {"candidates": []}
                )
                ordered_ids = list(dict.fromkeys(e["id"] for e in first_round["candidates"]))
                matching_ids = {
                    e["id"]
                    for e in first_round["candidates"]
                    if e["document_name"] == case["source_name"]
                    and e["line_start"] <= case["line"] <= e["line_end"]
                }
                first_rank = next(
                    (
                        rank
                        for rank, identifier in enumerate(ordered_ids[:5], 1)
                        if identifier in matching_ids
                    ),
                    0,
                )
            rows.append(
                {
                    "case_id": case["id"],
                    "expected": case["expected"],
                    "predicted": claim["verdict"],
                    "agreement": claim["verdict"] == case["expected"],
                    "retrieval_hit": hit,
                    "first_relevant_rank_at5": first_rank,
                    "extracted_claim_count": len(report["claims"]),
                    "latency_ms": report["latency_ms"],
                    "verification_pairs": report["verification_pairs"],
                    "citations": [
                        {
                            "document_name": e["document_name"],
                            "line_start": e["line_start"],
                            "line_end": e["line_end"],
                        }
                        for e in claim["citations"]
                    ],
                }
            )
        confusion = {label: {other: 0 for other in LABELS} for label in LABELS}
        for row in rows:
            confusion[row["expected"]][row["predicted"]] += 1
        metrics = {}
        for label in LABELS:
            tp = confusion[label][label]
            predicted = sum(confusion[other][label] for other in LABELS)
            actual = sum(confusion[label].values())
            precision = tp / predicted if predicted else 0
            recall = tp / actual if actual else 0
            metrics[label] = {
                "precision": precision,
                "recall": recall,
                "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0,
                "support": actual,
            }
        hits = [r["retrieval_hit"] for r in rows if r["retrieval_hit"] is not None]
        first_ranks = [r["first_relevant_rank_at5"] for r in rows if r["first_relevant_rank_at5"] is not None]
        output["modes"][mode] = {
            "case_count": len(rows),
            "fixture_agreement": sum(r["agreement"] for r in rows) / max(1, len(rows)),
            "macro_f1": sum(m["f1"] for m in metrics.values()) / len(metrics),
            "per_class": metrics,
            "confusion": confusion,
            "retrieval_hit_rate": sum(hits) / len(hits) if hits else None,
            "recall_at5": sum(rank > 0 for rank in first_ranks) / len(first_ranks) if first_ranks else None,
            "mrr_at5": sum(1 / rank if rank else 0 for rank in first_ranks) / len(first_ranks)
            if first_ranks
            else None,
            "retrieval_metric_note": "First-round unique chunks; each annotated case has one expected source span. Missing-evidence cases excluded.",
            "p50_ms": float(np.percentile([r["latency_ms"] for r in rows], 50)),
            "p95_ms": float(np.percentile([r["latency_ms"] for r in rows], 95)),
            "total_seconds": round(time.perf_counter() - started, 2),
            "cases": rows,
        }
    return output


async def run_evaluation(ctx, evaluation_id: str):
    async with Session() as db:
        row = await db.scalar(select(Evaluation).where(Evaluation.id == evaluation_id).with_for_update())
        if not row or row.status != "pending":
            return
        row.status = "running"
        row.updated_at = now()
        row.attempts += 1
        config = dict(row.result)
        owner_id = row.owner_id
        await db.commit()
    try:
        async with Session() as db:
            kb = await db.scalar(
                select(KnowledgeBase)
                .where(KnowledgeBase.id == config["kb_id"], KnowledgeBase.owner_id == owner_id)
                .with_for_update()
            )
            if not kb:
                raise ValueError("Evaluation library is unavailable.")
            result = await evaluate(db, kb.id, config["modes"], config["split"])
            row = await db.get(Evaluation, evaluation_id)
            if row:
                row.status, row.result, row.updated_at = "completed", result, now()
                await db.commit()
    except Exception as exc:
        async with Session() as db:
            row = await db.get(Evaluation, evaluation_id)
            if row:
                row.status = "failed"
                row.result = {"error": "Evaluation failed: " + type(exc).__name__}
                await db.commit()
