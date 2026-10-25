"""Small, source-traceable research mechanisms; method labels are intentionally precise."""

import asyncio
import re
from collections import defaultdict, deque
import numpy as np
from sqlalchemy import select, text
from backend.models import Chunk, Document
from backend.runtime import embed, embedder, token_vectors, generate_local, _model_lock


def late_pool(text_value: str, spans: list[tuple[int, int]]) -> list[list[float]]:
    import torch

    with _model_lock:
        model = embedder()
        encoded = model.tokenizer(
            text_value, return_tensors="pt", return_offsets_mapping=True, truncation=False
        )
        offsets = encoded.pop("offset_mapping")[0].tolist()
        if encoded["input_ids"].shape[1] > model.max_seq_length:
            raise ValueError(
                "Late-pooling lab exceeds this model's context window; use a compatible long-context model."
            )
        encoded = {k: v.to(model.device) for k, v in encoded.items()}
        with torch.inference_mode():
            hidden = model[0].auto_model(**encoded).last_hidden_state[0].cpu().numpy()
        vectors = []
        for start, end in spans:
            indices = [i for i, (a, b) in enumerate(offsets) if b > a and b > start and a < end]
            if not indices:
                raise ValueError("Chunk span contains no model tokens.")
            pooled = hidden[indices].mean(axis=0)
            pooled /= max(np.linalg.norm(pooled), 1e-12)
            vectors.append(pooled.tolist())
        return vectors


def late_interaction(query: str, passages: list[str]) -> list[float]:
    _, q = token_vectors(query)
    q = q / np.maximum(np.linalg.norm(q, axis=1, keepdims=True), 1e-12)
    scores = []
    for passage in passages:
        _, d = token_vectors(passage)
        d = d / np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-12)
        scores.append(float((q @ d.T).max(axis=1).mean()))
    return scores


def hierarchy(passages: list[dict], clusters: int = 3, abstractive=False) -> dict:
    from sklearn.cluster import KMeans

    if not passages:
        return {"nodes": [], "method": "empty"}
    vectors = np.array(embed([p["text"] for p in passages]))
    k = min(clusters, len(passages))
    groups = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(vectors)
    nodes = []
    for group in sorted(set(groups.tolist())):
        indices = np.where(groups == group)[0]
        texts = [passages[i]["text"] for i in indices]
        if abstractive:
            summary = generate_local(
                "Summarize this source material without adding facts: " + " ".join(texts), 100
            )
        else:
            centroid = vectors[indices].mean(axis=0)
            ranked = sorted(indices, key=lambda i: float(vectors[i] @ centroid), reverse=True)
            summary = " ".join(passages[i]["text"] for i in ranked[:2])
        nodes.append(
            {
                "id": f"group-{group}",
                "summary": summary,
                "source_ids": [passages[i]["id"] for i in indices],
                "generated": abstractive,
            }
        )
    return {
        "nodes": nodes,
        "method": "abstractive_cluster_tree" if abstractive else "extractive_cluster_tree",
        "note": "Mechanism lab inspired by hierarchical retrieval; not an exact RAPTOR reproduction.",
    }


def entity_graph(passages: list[dict]) -> dict:
    nodes = defaultdict(set)
    edges = defaultdict(set)
    for p in passages:
        entities = sorted(set(re.findall(r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|[A-Z]{2,})\b", p["text"])))
        entities = [
            e
            for e in entities
            if e not in {"The", "All", "Every", "This", "Document", "Version", "Synthetic"}
        ]
        for entity in entities:
            nodes[entity].add(p["id"])
        for i, a in enumerate(entities):
            for b in entities[i + 1 :]:
                edges[(a, b)].add(p["id"])
    return {
        "nodes": [{"entity": k, "source_ids": sorted(v)} for k, v in nodes.items()],
        "edges": [{"a": a, "b": b, "source_ids": sorted(ids)} for (a, b), ids in edges.items()],
        "note": "Rule-based entity co-occurrence lab; not Microsoft's GraphRAG pipeline.",
    }


def graph_expand(graph: dict, entity: str, max_hops=2) -> list[str]:
    adjacency = defaultdict(set)
    sources = defaultdict(set)
    for node in graph["nodes"]:
        sources[node["entity"]].update(node["source_ids"])
    for edge in graph["edges"]:
        adjacency[edge["a"]].add(edge["b"])
        adjacency[edge["b"]].add(edge["a"])
    queue = deque([(entity, 0)])
    seen = set()
    output = set()
    while queue:
        item, hops = queue.popleft()
        if item in seen:
            continue
        seen.add(item)
        output.update(sources[item])
        if hops < max_hops:
            queue.extend((neighbor, hops + 1) for neighbor in adjacency[item])
    return sorted(output)


async def index_benchmark(db, kb_id: str, queries: list[str], top_k=5):
    import time

    vectors = await asyncio.to_thread(embed, queries)
    results = []
    for query, vector in zip(queries, vectors):
        statement = (
            select(Chunk.id)
            .where(Chunk.kb_id == kb_id)
            .order_by(Chunk.embedding.cosine_distance(vector))
            .limit(top_k)
        )
        await db.execute(text("SET LOCAL enable_indexscan=off"))
        await db.execute(text("SET LOCAL enable_bitmapscan=off"))
        started = time.perf_counter()
        exact = list((await db.scalars(statement)).all())
        exact_ms = (time.perf_counter() - started) * 1000
        await db.execute(text("SET LOCAL enable_indexscan=on"))
        await db.execute(text("SET LOCAL enable_bitmapscan=on"))
        await db.execute(text("SET LOCAL enable_seqscan=off"))
        await db.execute(text("SET LOCAL hnsw.iterative_scan='strict_order'"))
        started = time.perf_counter()
        ann = list((await db.scalars(statement)).all())
        ann_ms = (time.perf_counter() - started) * 1000
        literal = statement.compile(compile_kwargs={"literal_binds": True})
        plan = (await db.execute(text("EXPLAIN (FORMAT JSON) " + str(literal)))).scalar()
        results.append(
            {
                "query": query,
                "exact_ids": exact,
                "candidate_ids": ann,
                "neighbor_recall": len(set(exact) & set(ann)) / len(exact) if exact else None,
                "exact_ms": exact_ms,
                "indexed_ms": ann_ms,
                "plan": plan,
                "note": "Inspect plan: planner may use a non-HNSW index on small filtered corpora.",
            }
        )
    await db.execute(text("SET LOCAL enable_seqscan=on"))
    return results


async def workspace_lab(db, kb_id: str, kind: str, query: str):
    rows = (
        await db.scalars(
            select(Chunk)
            .join(Document)
            .where(Chunk.kb_id == kb_id, Document.status == "indexed")
            .order_by(Chunk.document_id, Chunk.ordinal)
            .limit(100)
        )
    ).all()
    passages = [{"id": c.id, "text": c.text, "document_id": c.document_id} for c in rows]
    if not passages:
        raise ValueError("Index reference documents first.")
    if kind == "late_interaction":
        scores = await asyncio.to_thread(late_interaction, query, [p["text"] for p in passages])
        ranked = sorted(
            [{**p, "score": s} for p, s in zip(passages, scores)], key=lambda p: p["score"], reverse=True
        )
        return {
            "method": "MiniLM MaxSim mechanism lab",
            "not_exact_reproduction": "ColBERT",
            "results": ranked[:5],
        }
    if kind == "late_pooling":
        selected = passages[:3]
        joined = "\n".join(p["text"] for p in selected)
        spans = []
        start = 0
        for p in selected:
            spans.append((start, start + len(p["text"])))
            start += len(p["text"]) + 1
        late = await asyncio.to_thread(late_pool, joined, spans)
        early = await asyncio.to_thread(embed, [p["text"] for p in selected])
        return {
            "method": "Context-window late-pooling mechanism lab",
            "model_context_limited": True,
            "source_ids": [p["id"] for p in selected],
            "early_late_cosine": [float(np.dot(a, b)) for a, b in zip(early, late)],
        }
    if kind == "hierarchy":
        return await asyncio.to_thread(hierarchy, passages)
    if kind == "graph":
        graph = entity_graph(passages)
        entity = next((n["entity"] for n in graph["nodes"] if n["entity"].lower() in query.lower()), None)
        return {**graph, "expanded_source_ids": graph_expand(graph, entity) if entity else []}
    if kind == "hnsw":
        return {
            "method": "Exact vs indexed query-plan experiment",
            "results": await index_benchmark(db, kb_id, [query]),
        }
    raise ValueError("Unknown lab.")


class ColPaliAdapter:
    """Optional page-image research adapter; requires separately installed model/runtime."""

    def __init__(self, model_name="vidore/colpali-v1.3", device="cpu"):
        from colpali_engine.models import ColPali, ColPaliProcessor

        self.processor = ColPaliProcessor.from_pretrained(model_name)
        self.model = ColPali.from_pretrained(model_name).to(device).eval()
        self.device = device

    def retrieve(self, query, images):
        import torch

        with torch.inference_mode():
            image_inputs = self.processor.process_images(images).to(self.device)
            query_inputs = self.processor.process_queries([query]).to(self.device)
            docs = self.model(**image_inputs)
            q = self.model(**query_inputs)
            scores = self.processor.score_multi_vector(q, docs)[0]
        return scores.cpu().tolist()
