"""Execute actual optional mechanisms and audit modes; report results, not paper-reproduction claims."""

import asyncio, json, time
from pathlib import Path
from sqlalchemy import select
from backend.db import Session, engine
from backend.models import User, KnowledgeBase
from backend.pipeline import run_audit
from backend.labs import workspace_lab


async def main():
    context = json.loads(Path("artifacts/demo-context.json").read_text())
    results = {"runtime": "local CPU", "labs": {}, "modes": {}}
    async with Session() as db:
        account = await db.scalar(select(User).where(User.email == context["email"]))
        kb = await db.scalar(
            select(KnowledgeBase).where(
                KnowledgeBase.id == context["kb_id"], KnowledgeBase.owner_id == account.id
            )
        )
        for kind in ["late_pooling", "late_interaction", "hierarchy", "graph", "hnsw"]:
            started = time.perf_counter()
            try:
                result = await workspace_lab(db, kb.id, kind, "The Pro plan costs INR 299 per month.")
                results["labs"][kind] = {
                    "status": "executed",
                    "elapsed_s": round(time.perf_counter() - started, 2),
                    "result": result,
                }
            except Exception as exc:
                results["labs"][kind] = {
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "reason": str(exc),
                }
        for mode in ["contextual", "parent_window", "multi_query", "hyde", "adaptive", "agentic"]:
            started = time.perf_counter()
            try:
                report = await run_audit(
                    db, kb.id, "What is the Pro price?", "The Pro plan costs INR 299 per month.", mode
                )
                results["modes"][mode] = {
                    "status": "executed",
                    "elapsed_s": round(time.perf_counter() - started, 2),
                    "verdict": report["claims"][0]["verdict"],
                    "trace": report["claims"][0]["trace"],
                }
            except Exception as exc:
                results["modes"][mode] = {
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "reason": str(exc),
                }
    await engine.dispose()
    Path("artifacts/research-checks.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "labs": {k: v["status"] for k, v in results["labs"].items()},
                "modes": {
                    k: {"status": v["status"], "verdict": v.get("verdict")}
                    for k, v in results["modes"].items()
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
