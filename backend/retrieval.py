import asyncio
import re
from sqlalchemy import select, text
from backend.models import Chunk, Document
from backend.runtime import embed

STOP = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "of",
    "to",
    "in",
    "for",
    "and",
    "or",
    "per",
    "with",
    "all",
    "every",
    "can",
    "have",
    "has",
    "its",
    "it",
    "be",
    "one",
}
SYNONYMS = {
    "cost": "price pricing fee",
    "costs": "price pricing fee",
    "maximum": "limit capacity",
    "encrypted": "encryption security algorithm",
    "members": "team seats membership",
    "retained": "retention backup",
    "deleted": "deletion retention storage",
    "upload": "file attachment",
    "uploads": "file formats attachment",
    "unlimited": "limits quota",
    "paid": "price billing",
    "supports": "supported formats",
}


def tokens(text_value: str) -> set[str]:
    return {t for t in re.findall(r"[\w]+", text_value.lower()) if t not in STOP and len(t) > 1}


def lexical_similarity(query: str, passage: str) -> float:
    q = {t for t in tokens(query) if not t.isnumeric()}
    p = tokens(passage)
    return len(q & p) / max(1, len(q))


def rewrite(query: str, round_no: int) -> str:
    words = [w for w in re.findall(r"[\w]+", query.lower()) if w not in STOP and not w.isnumeric()]
    expanded = " ".join(SYNONYMS[w] for w in words if w in SYNONYMS)
    if round_no == 1:
        return " ".join(dict.fromkeys(words)) + (" " + expanded if expanded else "")
    focused = [w for w in words if w not in SYNONYMS]
    return " ".join(dict.fromkeys(focused + expanded.split()))


def serialize(chunk: Chunk, name: str, score: float, channel: str) -> dict:
    return {
        "id": chunk.id,
        "document_id": chunk.document_id,
        "document_name": name,
        "ordinal": chunk.ordinal,
        "text": chunk.text,
        "context": chunk.context,
        "page": chunk.page,
        "line_start": chunk.line_start,
        "line_end": chunk.line_end,
        "score": round(float(score), 5),
        "channel": channel,
    }


async def retrieve(db, kb_id: str, query: str, mode: str = "hybrid", top_k: int = 5) -> list[dict]:
    base = (
        select(Chunk, Document.name)
        .join(Document)
        .where(Chunk.kb_id == kb_id, Document.kb_id == kb_id, Document.status == "indexed")
    )
    lexical = []
    if mode != "dense":
        rows = (
            await db.execute(
                base.where(text("to_tsvector('english', chunks.text) @@ websearch_to_tsquery('english', :q)"))
                .order_by(
                    text(
                        "ts_rank_cd(to_tsvector('english', chunks.text), websearch_to_tsquery('english', :q)) DESC"
                    )
                )
                .params(q=query)
                .limit(top_k * 3)
            )
        ).all()
        lexical = [serialize(c, name, lexical_similarity(query, c.text), "lexical") for c, name in rows]
    dense = []
    if mode != "lexical":
        vector = (await asyncio.to_thread(embed, [query]))[0]
        column = Chunk.contextual_embedding if mode == "contextual" else Chunk.embedding
        distance = column.cosine_distance(vector)
        await db.execute(text("SET LOCAL enable_indexscan=off"))
        rows = (
            await db.execute(
                select(Chunk, Document.name, distance.label("distance"))
                .join(Document)
                .where(Chunk.kb_id == kb_id, Document.kb_id == kb_id, Document.status == "indexed")
                .order_by(distance)
                .limit(top_k * 3)
            )
        ).all()
        await db.execute(text("SET LOCAL enable_indexscan=on"))
        dense = [
            serialize(c, name, max(0, 1 - float(d)), "contextual" if mode == "contextual" else "dense")
            for c, name, d in rows
        ]
    if mode == "lexical":
        return lexical[:top_k]
    if mode == "dense":
        return dense[:top_k]
    merged = {}
    for ranking in (lexical, dense):
        for rank, item in enumerate(ranking, 1):
            if item["id"] not in merged:
                merged[item["id"]] = {**item, "fusion": 0, "dense_score": 0.0, "lexical_score": 0.0}
            row = merged[item["id"]]
            row["fusion"] += 1 / (60 + rank)
            row["dense_score" if item["channel"] in ("dense", "contextual") else "lexical_score"] = item[
                "score"
            ]
    for row in merged.values():
        row["score"] = round(max(row["dense_score"], row["lexical_score"]), 5)
        row["channel"] = "hybrid" if mode != "contextual" else "contextual"
    return sorted(merged.values(), key=lambda x: x["fusion"], reverse=True)[:top_k]


async def expand_windows(db, kb_id: str, candidates: list[dict]) -> list[dict]:
    expanded = {c["id"]: c for c in candidates}
    for item in candidates:
        rows = (
            await db.execute(
                select(Chunk, Document.name)
                .join(Document)
                .where(
                    Chunk.kb_id == kb_id,
                    Document.status == "indexed",
                    Chunk.document_id == item["document_id"],
                    Chunk.ordinal.between(max(0, item["ordinal"] - 1), item["ordinal"] + 1),
                )
            )
        ).all()
        for chunk, name in rows:
            expanded.setdefault(chunk.id, serialize(chunk, name, item["score"], "parent_window"))
    return list(expanded.values())[:15]
