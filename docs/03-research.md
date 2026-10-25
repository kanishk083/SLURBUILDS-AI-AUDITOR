---
created: 2026-10-25
project: production-rag-learning
type: research
confidence: medium
---

# Research notes — RAG learning architecture

## Summary

Proposed teaching sequence: manual evidence selection se start karo, phir lexical/exact baselines ke against retrieval aur production features evaluate karo.

## Detail

Research date: 2026-10-25. Neeche source-backed facts aur project recommendations separate hain. Yeh pre-implementation research snapshot hai; current experiments and results [build status](11-build-status.md) mein hain.

| Sub-question | Verified finding | Project implication / hypothesis |
| --- | --- | --- |
| RAG ka core kya hai? | Original work combines model parameters with retrieved external memory. | Manual evidence lab se retrieval aur generation ki responsibilities alag samjhenge. [Paper](https://arxiv.org/abs/2005.11401) |
| Exact vs approximate? | pgvector supports exact search and approximate indexes; filtered ANN can return fewer results. | Pehle exact baseline; HNSW ko filtered workload par compare karenge. [Official docs](https://github.com/pgvector/pgvector) |
| Keyword retrieval ka baseline? | PostgreSQL has full-text parsing and ranking; its built-in ranking is not corpus-level BM25. | PostgreSQL FTS ko lexical baseline label karenge; BM25 claim nahi karenge. [Official docs](https://www.postgresql.org/docs/current/textsearch-controls.html) |
| Worker retries safe hain? | ARQ explicitly says jobs may run more than once. | Idempotent writes, durable job state and interruption experiments required. [Official docs](https://arq-docs.helpmanual.io/#usage) |
| BackgroundTasks enough? | FastAPI distinguishes small same-process background work from heavier work across processes/servers. | Ingestion separate worker mein; durability ke liye storage/dispatch recovery bhi design hogi. [Official docs](https://fastapi.tiangolo.com/tutorial/background-tasks/#caveat) |
| Har PDF extract ho jayega? | pypdf text extraction has layout/resource constraints; image-only scans need OCR. | Digital-text PDFs first; scanned inputs ko explicit needs-OCR/unsupported state milega until OCR exists. [Official docs](https://pypdf.readthedocs.io/en/stable/user/extract-text.html) |
| Zyada context better? | Lost in the Middle found position-dependent degradation on tested models/tasks. | Chosen current model par ordering/context-size experiment; old results ko universal claim nahi banayenge. [Paper](https://arxiv.org/abs/2307.03172) |
| Quality kaise judge hogi? | Ragas separates retrieval/context quality and generation evaluation dimensions. | Human-reviewed golden questions first; model judges supplementary signals honge. [Paper](https://arxiv.org/abs/2309.15217) |
| Multi-user boundaries? | PostgreSQL RLS can restrict rows; table owners and privileged roles can bypass it. | Application authorization mandatory; RLS adopt karne par actual runtime-role tests chahiye. [Official docs](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) |
| Prompt injection ka boundary? | OWASP covers poisoned documents, access inheritance and retrieval-to-generation controls. | Untrusted evidence boundaries plus backend authorization and adversarial tests; delimiters alone enough nahi. [OWASP](https://cheatsheetseries.owasp.org/cheatsheets/RAG_Security_Cheat_Sheet.html) |

## Implications

### Second-order effects

- Chunking change relevance labels ko invalidate kar sakta hai agar labels sirf chunk IDs hain. Source spans aur document versions store karna comparison ko stable banata hai.
- Permission filters relevance aur latency ko affect kar sakte hain. Shared ANN index ke behavior ko realistic tenant/KB distribution par measure karna hoga.
- Retry se duplicate visible chunks aa sakte hain. Active index version publish karne ka step transactional aur repeatable hona chahiye.
- PDF extraction mein page provenance lose hui toh baad mein reliable page citations recover karna difficult hoga. TXT/MD ke liye heading/line locators use honge; fictional page numbers nahi.

### Third-order effects

- Embedding provider/model change sirf configuration switch nahi: dimensions, vector space, reindexing, privacy aur evaluation sab review honge.
- Deletion sirf DB row delete nahi: in-flight workers, files, vectors, caches aur stored citation access ko coordinate karna hoga. Retention/backups ka separate documented lifecycle hoga.
- Hybrid/reranking improvement global average mein achchha dikh sakta hai, lekin identifiers ya Hinglish query slice regress kar sakta hai. Slice reports release decision ka part honge.

## Confidence

Documented mechanisms par high confidence; proposed stack fit aur teaching order par medium confidence. Best chunk size, embedding model, top-K, ANN configuration, accuracy aur cost unknown hain until measured.

Conclusion change hogi agar real corpus mostly scans/tables ho, language mix embedding model se match na kare, ya deployment resources insufficient hon. Learner confirms Python/SQL/APIs familiar hain; focused revision suitable hai.

## Learner clarification and advanced scope

2026-10-25: Python, SQL aur APIs already aate hain; revision pending hai. Modern RAG techniques ko seekhkar isi project mein add karna explicit requirement hai. Updated sequence aur source-backed labs: [modern RAG track](06-modern-rag.md).

Research coverage includes query/evidence preparation, representation, controlled retrieval loops, hierarchical/visual retrieval aur 2026 research candidates. Yeh curated track hai; exhaustive newest-method ranking nahi. Sources establish mechanisms; hamare corpus par improvements abhi unmeasured hain.

## Open Questions

- Focused revision checks mein kaunse specific topics refresh chahiye?
- Real corpus ka domain, size, language aur scanned-PDF percentage?
- Hosted inference allowed hai? Data-handling requirements aur trial budget?
- Expected concurrent users aur deployment constraints?
- Initial quality/latency/cost targets kya honge? Baseline ke baad targets freeze karenge.
