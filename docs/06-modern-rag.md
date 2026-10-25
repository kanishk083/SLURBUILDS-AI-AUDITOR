---
created: 2026-10-25
project: production-rag-learning
type: research
confidence: medium
---

# Modern RAG — research se project integration tak

## Summary

Foundations ke baad advanced RAG techniques ko isi project mein explain, prototype aur evaluate karenge; measured improvements default pipeline ka part banenge.

## Detail

Python/SQL/API basics familiar hain; unka focused revision parallel chalega. Research checked 2026-10-25. Modern ka matlab sirf recent publication nahi: established useful techniques aur newer research directions dono samjhenge. Yeh selected syllabus hai, exhaustive latest-method list nahi.

Har lab: problem example → primary reading → mechanism apne words mein → prediction → minimal prototype → same-corpus comparison → integration decision. Neeche ke lab IDs curriculum identifiers hain; implemented features nahi.

## A. Query aur evidence ko better banana

Prerequisite: baseline ingestion, lexical+dense search, source spans aur evaluation v0.

| Lab | Mechanism jo seekhna hai | Isi project mein task | Compare aur failure check |
| --- | --- | --- | --- |
| A1. Hybrid + cross-encoder reranking | Lexical/dense candidates fuse karo; query-passage pair ko jointly score karo | Existing hybrid module ko inspectable candidate/rerank stages do | Same candidate pool; top-K relevance vs added latency; missed candidate reranker recover nahi kar sakta |
| A2. Contextual Retrieval | Chunk-specific document context prepend karke index karo | Raw chunk aur generated indexing context alag store; contextual vs plain retrieval mode | Ambiguous chunks par comparison; generated context mein false facts inspect; preprocessing cost count |
| A3. Parent/child + sentence-window expansion | Precise child hit se larger authorized original span load karo | Small passages retrieve karo, same-version parent/neighbor context fetch karo | Fixed context budget; boundary evidence vs extra noise; context expansion permission recheck |
| A4. Query rewriting, multi-query + decomposition | Follow-up resolve karo, alternate searches banao, multi-part question split karo | Original query preserve; rewritten queries retrieve; dedup/fuse results; subquestion evidence map | Same-intent English/Hinglish and chat follow-ups; query drift, search budget and lost constraints |
| A5. HyDE | Hypothetical answer-document embed karke real corpus search karo | Original-query and hypothetical-query modes; generated text separately log as synthetic metadata | Same questions; real source recall, hallucinated terms and additional model cost |

A1 primary: [Sentence Transformers retrieve/rerank](https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html). Read how bi-encoder candidate generation differs from cross-encoder scoring. A normalized-looking score automatically calibrated relevance probability nahi hota.

A2 primary: [Anthropic Contextual Retrieval](https://www.anthropic.com/research/contextual-retrieval), method and evaluation setup. Original approach contextual embeddings aur contextual BM25 discuss karta hai. Hamare PostgreSQL FTS experiment ko contextual FTS label karenge; BM25 reproduction tab jab actual BM25 implementation add aur verify ho. Vendor benchmark gains ko apne scores nahi bolenge.

A3 is our proposed context-expansion experiment. A4 ke controlled multi-step decisions ke liye [Adaptive-RAG](https://arxiv.org/abs/2403.14403) aur [A-RAG](https://arxiv.org/abs/2602.03442) padho. Query rewriting/decomposition variants hamari explicit engineering experiments hongi, in papers ki exact reproduction ka claim nahi.

A5 primary: [HyDE paper](https://arxiv.org/abs/2212.10496). Hypothetical document retrieval aid hai; final answer ka evidence sirf retrieved actual documents hain.

## B. Representation ko samajhna

Prerequisite: embedding tokenization, pooling, model dimensions, exact similarity baseline; required model/runtime capability verify karo.

| Lab | Mechanism jo seekhna hai | Isi project mein task | Compare aur failure check |
| --- | --- | --- | --- |
| B1. Late chunking | Long text ke contextual token representations par chunk-wise pooling | Compatible model se token embeddings lo; span-aligned chunk vectors produce karo | Early chunking vs late, same model where supported; contextual references, token limits, compute |
| B2. Late interaction / ColBERT | Single vector ke badle multiple token vectors aur query-document interaction | Tiny corpus par explicit token-level matching scorer; existing dense baseline se compare | Relevant hits, multi-vector storage, memory and scoring latency |

B1 primary: [Late Chunking](https://arxiv.org/abs/2409.04701). Yeh generated contextual prefix se different mechanism hai. Black-box API jo sirf one pooled vector return karti hai usse native late chunking assume nahi kar sakte; compatible service support ya token-level access chahiye.

B2 primary: [ColBERT](https://arxiv.org/abs/2004.12832). Late interaction aur late chunking alag concepts hain. Small exact scorer first; pgvector single-vector HNSW ko automatic full ColBERT implementation mat label karo. Scalable multi-vector indexing ka decision measured need ke baad.

## C. Corrective, adaptive aur agentic retrieval

User-selected priority: C1 corrective retrieval is now the core architecture, introduced early through [CRAG design](08-crag-design.md). C2/C3 remain later extensions; this section is the deeper research track.

Early C1 prerequisite: inspectable retrieval, source spans, per-call authorization and labeled evaluation cases. Answer-side checks and C2/C3 additionally need grounded generation and a verified citation resolver.

| Lab | Mechanism jo seekhna hai | Isi project mein task | Compare aur failure check |
| --- | --- | --- | --- |
| C1. Corrective retrieval | Retrieved evidence quality check; weak result par bounded recovery | Retrieve → assess → reformulate/retrieve once more or abstain state machine | Missing/noisy evidence cases; recovery vs extra cost; loop cap |
| C2. Self-reflection + adaptive routing | Support critique aur question complexity se retrieval strategy choose karna | Claim/evidence checker; direct/single-hop/multi-hop route experiment | False confidence, wrong routing, unnecessary abstention; compare with fixed pipeline |
| C3. Agentic RAG | Model authorized retrieval tools select karta hai aur evidence iteratively reads | Scoped keyword_search, semantic_search, read_chunk tools; bounded controller | Multi-hop questions; trace every call; tool budgets, deadline, cancellation and malicious text |

C1 primary: [CRAG](https://arxiv.org/abs/2401.15884). Paper mein retrieval evaluation aur corrective actions, including web search, hain. Private-KB project ka first prototype KB-only aur CRAG-inspired hoga. Web sources add karne par provenance, policy aur separate source category explicitly design karni hogi.

C2 primary: [Self-RAG](https://arxiv.org/abs/2310.11511) and [Adaptive-RAG](https://arxiv.org/abs/2403.14403). Original Self-RAG special reflection tokens ke saath training use karta hai. Prompt-only critique ko Self-RAG-inspired label karenge. Paper-faithful reproduction chahiye toh published model/training setup, license aur compute separately inspect honge. Private-document answers ke no-retrieval route ko unsupported factual answers dene ki permission nahi milegi.

C3 primary: [A-RAG, February 2026](https://arxiv.org/abs/2602.03442). Paper keyword search, semantic search aur chunk-read interfaces expose karta hai. Hamara first implementation in ideas se informed bounded prototype hoga; exact reproduction ke liye full methods/code verify karenge.

Starting experimental caps, adjustable after measurement: at most two recovery rounds and six retrieval/read calls, plus an explicit end-to-end deadline and token budget. Har expanded query aur tool read par original user's authorized corpus scope preserve hoga. Agent khud se permissions ya budget expand nahi kar sakta.

## D. Hierarchical, graph aur visual retrieval

Prerequisite: reliable document versions/provenance; derived artifact lifecycle; representative global/visual queries.

| Lab | Mechanism jo seekhna hai | Isi project mein task | Compare aur failure check |
| --- | --- | --- | --- |
| D1. RAPTOR-style hierarchy | Chunks ko recursively cluster/summarize karke multiple abstraction levels retrieve karo | Small summary tree; every node maps to original authorized spans | Local facts vs global synthesis; summary distortion, build/update cost |
| D2. GraphRAG | Entities/relations, communities, local/global graph-backed retrieval | Small per-KB graph; local vs global search experiment; DRIFT study/variant | Relationship/global questions; extraction errors, disconnected evidence and indexing cost |
| D3. Layout-aware + multimodal RAG | Text extraction ke saath tables/layout; then page-image retrieval | Digital text baseline vs Docling-style structured parse; ColPali-style visual retrieval lab | Table/chart questions, source page/region support, storage/compute and parsing failures |

D1 primary: [RAPTOR](https://arxiv.org/abs/2401.18059). Summary tree ki generated statements ko original source spans se verify karo. Generic hierarchical prototype ko exact RAPTOR reproduction nahi bolenge.

D2 primary: [Microsoft GraphRAG query docs](https://microsoft.github.io/graphrag/query/overview/). Local search entity-oriented context aur raw chunks use karta hai; global search community reports use karta hai; DRIFT community context se follow-up exploration karta hai. GraphRAG har factual lookup ka default replacement assume nahi karenge.

D3 primary: [Docling document model](https://docling-project.github.io/docling/concepts/docling_document/) and [ColPali](https://arxiv.org/abs/2407.01449). Docling structured parsing/provenance aur ColPali page-image multi-vector retrieval different stages hain. Retrieved page ke chart/table ka answer verify karne ke liye suitable visual understanding/extraction bhi chahiye.

Graphs aur summaries ko per-KB boundaries mein build karo, unless a separately authorized aggregation scope is explicitly implemented. Mixed-permission generated summary ko post-filter karna original private facts unlearn nahi karta. Source deletion/version change derived artifacts ko invalidate karega.

## E. Current research ko evaluate karna seekho

| Lab | Primary research candidate | Narrow project experiment |
| --- | --- | --- |
| E1a. Adaptive budget | [AB-RAG, June 2026](https://arxiv.org/abs/2606.29090) proposes confidence-informed retrieval under a budget | Fixed vs adaptive retrieval budget; inspect confidence signals, accuracy/coverage and cost; reproduce only after full method review |
| E1b. Reliability across layers | [LayerRAG-Bench, July 2026](https://arxiv.org/abs/2607.27353) studies evidence/tool/session/authorization failures | Inject stale evidence, wrong-session state and missing tool outputs; report layer-specific failure/recovery |

Yeh research candidates hain. Abstract/publication date alone se production recommendation ya independently reproduced validity establish nahi hoti. Lab shuru karte waqt full paper, released artifacts, license, dependencies, evaluation leakage aur newer independent evidence check karenge. Reproduction infeasible ho toh exact blocker aur smaller inspired experiment record hoga.

## Integration approach

Same project mein baseline aur experiment configurations selectable hongi. Proposed mode names: `hybrid`, `contextual`, `multi_query`, `hyde`, `late_chunking`, `late_interaction`, `corrective`, `agentic`, `hierarchical`, `graph`, `visual`. Current implemented modes, executed checks and unverified adapters are listed in the [method matrix](13-research-method-labels.md) and [build status](11-build-status.md).

Research code ko pehle narrow lab mein rakho. Repeated implementations se stable common contract emerge ho tab retrieval interface extract karo; abhi generic plugin framework build mat karo. Model/GPU experiments ki dependencies core API image mein automatically include nahi hongi.

Evaluation runner same question set par selected modes compare karega. Developer evaluation view candidates, source spans, rewritten queries, timings, call budgets aur config version inspect karne dega; private raw content logs mein publish nahi hoga.

## Implications

Har technique ke liye working learning prototype target hai. Default product pipeline mein promotion ke liye representative development cases par measurable benefit, acceptable cost/latency, intact authorization/citations aur complete lifecycle behavior chahiye. Unhelpful prototype bhi project ke documented experimental mode ke roop mein useful learning rahega.

Har advanced module se pehle focused research refresh: canonical mechanism → official current implementation → recent relevant primary research → model/hardware/data constraints → exact experiment. Sirf newest naam dekhkar dependency ya provider choose nahi karenge.

## Confidence

Referenced mechanisms par high confidence; hamare corpus par suitability medium/unknown. Proposed mode combinations aur budgets experimental hain. Current measured core ablations and executed mechanism checks [build status](11-build-status.md) mein hain; broad method superiority remains unestablished.

## Open Questions

Representative corpus/domain, deployment hardware, trial budget, allowed external providers aur advanced labs ke runtime constraints implementation se pehle establish karne hain.
