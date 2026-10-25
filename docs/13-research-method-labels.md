# Research methods: actual implementation boundaries

| Label | What runs | Boundary |
| --- | --- | --- |
| baseline | Same hybrid top-5 as filter/corrective, no grading/refinement | Fixed-retrieval audit ablation; NLI verification still runs |
| filter | Hybrid retrieval, relevance/applicability gate and source-preserving strips | No correction rounds |
| corrective | Filtering/refinement plus bounded query rewrite/retrieval | Private-KB CRAG-inspired adaptation; original paper also uses web search |
| contextual | Title/heading-enriched vectors | Structural enrichment, not an LLM contextual-prefix reproduction |
| parent_window | Authorized neighboring passages | Bounded context expansion |
| multi_query | Original and deterministic expanded queries | Expansion can drift; original claim remains verification target |
| hyde | Local generated hypothetical search aid | Aid is never evidence; generator showed factual-quality failures |
| adaptive | Lexical routing for exact-value queries, then hybrid recovery | Deterministic prototype, not a trained Adaptive-RAG classifier |
| agentic | Local planner, whitelisted read/search tools and explicit fallback | No arbitrary execution or scope expansion |
| late_pooling | Pool spans after contextual encoding in one MiniLM window | Not a long-document, long-context-model reproduction |
| late_interaction | MiniLM token-level MaxSim | Not trained ColBERT |
| hierarchy | Source-linked KMeans and extractive representatives | Not full RAPTOR |
| graph | Entity co-occurrence and bounded source-linked expansion | Not Microsoft GraphRAG |
| hnsw | Actual pgvector index/query-plan experiment | Small filtered corpora may use another index; inspect recorded plan |
| ColPaliAdapter | Optional visual research adapter | Dependency/model/runtime not verified |

Primary readings: [CRAG](https://arxiv.org/html/2401.15884v3), [Self-RAG](https://arxiv.org/abs/2310.11511), [Contextual Retrieval](https://www.anthropic.com/research/contextual-retrieval), [HyDE](https://arxiv.org/abs/2212.10496), [late chunking](https://arxiv.org/abs/2409.04701), [ColBERT](https://arxiv.org/abs/2004.12832), [RAPTOR](https://arxiv.org/abs/2401.18059), [GraphRAG](https://microsoft.github.io/graphrag/), [ColPali code](https://github.com/illuin-tech/colpali).

Mechanism prototype, successful execution, paper reproduction and held-out improvement are separate achievements. This release does not claim trained Self-RAG/GraphRAG/ColBERT/ColPali reproduction.
