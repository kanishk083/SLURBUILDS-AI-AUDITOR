import argparse
import asyncio
import json
from pathlib import Path
from sqlalchemy import select
from backend.db import Session, engine
from backend.models import KnowledgeBase, User
from backend.documents import parse
from backend.retrieval import tokens
from backend.config import ROOT


def local_search(query: str, folder: Path):
    candidates = []
    for path in sorted(folder.iterdir()):
        if path.suffix.lower() not in {".txt", ".md", ".markdown", ".pdf"}:
            continue
        for passage in parse(path.read_bytes(), path.suffix.lower(), path.name):
            overlap = len(tokens(query) & tokens(passage.text)) / max(1, len(tokens(query)))
            if overlap:
                candidates.append(
                    {
                        "source": path.name,
                        "text": passage.text,
                        "line_start": passage.line_start,
                        "line_end": passage.line_end,
                        "page": passage.page,
                        "score": overlap,
                    }
                )
    return sorted(candidates, key=lambda r: r["score"], reverse=True)[:5]


async def database_command(args):
    from backend.evaluation import evaluate
    from backend.labs import workspace_lab

    async with Session() as db:
        user = await db.scalar(select(User).where(User.email == args.email))
        if not user:
            raise SystemExit("Account not found. Create a local account and load sample sources first.")
        kb = (
            await db.scalar(
                select(KnowledgeBase).where(KnowledgeBase.owner_id == user.id, KnowledgeBase.id == args.kb_id)
            )
            if args.kb_id
            else await db.scalar(select(KnowledgeBase).where(KnowledgeBase.owner_id == user.id))
        )
        if not kb:
            raise SystemExit("Owned knowledge base not found.")
        if args.command == "evaluate":
            result = await evaluate(db, kb.id, args.modes.split(","), args.split)
        else:
            result = await workspace_lab(db, kb.id, args.kind, args.query)
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print("Report saved:", target)
        if args.command == "evaluate":
            print(
                json.dumps(
                    {
                        k: {
                            "fixture_agreement": v["fixture_agreement"],
                            "macro_f1": v["macro_f1"],
                            "cases": v["case_count"],
                        }
                        for k, v in result["modes"].items()
                    },
                    indent=2,
                )
            )
    await engine.dispose()


def main():
    parser = argparse.ArgumentParser(prog="python -m backend.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--folder", type=Path, default=ROOT / "phase-00/sources")
    for command in ["evaluate", "lab"]:
        p = sub.add_parser(command)
        p.add_argument("--email", required=True)
        p.add_argument("--kb-id")
        p.add_argument("--output", default="artifacts/" + command + "-report.json")
        if command == "evaluate":
            p.add_argument("--modes", default="baseline,filter,corrective")
            p.add_argument("--split", choices=["development", "held_out"], default="development")
        else:
            p.add_argument(
                "--kind",
                choices=["late_pooling", "late_interaction", "hierarchy", "graph", "hnsw"],
                required=True,
            )
            p.add_argument("--query", default="What is the price?")
    args = parser.parse_args()
    if args.command == "search":
        print(json.dumps(local_search(args.query, args.folder), indent=2))
    else:
        asyncio.run(database_command(args))


if __name__ == "__main__":
    main()
