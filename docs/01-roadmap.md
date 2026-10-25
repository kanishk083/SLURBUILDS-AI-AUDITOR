# AI Auditor — phase-wise learning and build plan

Yeh AI Auditor ka authoritative learning sequence hai. Students is general-purpose project ko build karke resume aur interviews mein demonstrate karenge. Scope: [AI Auditor](10-ai-auditor-scope.md). Explanation Hinglish; code aur technical terms English.

Planning hypothesis: small inspectable baseline se start karke same labeled examples par corrective retrieval compare karne se mechanisms, failures aur trade-offs clearly samajh aayenge. Yeh teaching hypothesis hai; learner progress ya quality improvements abhi verified nahi.

## Har phase ka learning loop

1. Research: do ya teen focused questions; original paper/official docs ke relevant sections.
2. Explain: simple example, actual mechanism, phir trade-offs apne words mein.
3. Predict: hypothesis, expected output aur minimal falsification test likho.
4. Build: ek bounded working increment; Python/SQL/API revision actual code ke saath.
5. Evaluate: saved examples par run; failures inspect; [experiment notebook](04-experiment-template.md) fill karo.
6. Defend: ek interview explanation, ek failure/debugging exercise aur ek design decision record karo.

Phase complete tab jab working artifact, observed output aur understanding evidence available ho. Agar user explicitly autonomous implementation maange toh us instruction ke mutabik implement aur explain karo. Suggested session format: focused reading → explanation/prediction → build → output review. Sessions ko need ke hisaab se split karo; fixed calendar estimate nahi hai.

## Phase overview

| Phase | Learning focus | Working output | Completion evidence |
| --- | --- | --- | --- |
| 0 | Claims, evidence, RAG/CRAG and focused revision | Hand-labeled audit examples | Supported/contradicted/insufficient distinction explained |
| 1 | Parsing, chunking, lexical retrieval | Local evidence search CLI | Ranked passages with source locations and baseline failures |
| 2 | Backend, database, ownership, async ingestion | Authorized document/KB API and worker | Upload/status flow, isolation and restart/idempotency checks |
| 3 | Embeddings, exact vectors, hybrid search, reranking | Comparable retrieval modes | Same-corpus relevance and latency measurements |
| 4 | Claim extraction and evidence verification | Baseline AI audit API/CLI | Claim verdicts and valid source citations on reviewed cases |
| 5 | CRAG-style evaluator and bounded correction | Corrective AI audit pipeline | Baseline vs filter-only vs correction comparison and stop traces |
| 6 | Report UI and source navigation | Usable audit application | Documents + question/answer → report → evidence navigation |
| 7 | Evaluation depth, reliability, observability | Reproducible quality/failure report | Held-out validation, isolation/failure tests and cost/latency accounting |
| 8 | Context/query improvement methods | Contextual, parent/window, rewrite and HyDE labs | Standalone and combined ablations with provenance checks |
| 9 | Representation and index trade-offs | HNSW, late chunking and late-interaction labs | Recall, applicability, resource and latency comparisons |
| 10 | Advanced control, graph, hierarchy and visual evidence | Advanced RAG research prototypes | Per-lab dataset, runnable experiment and honest method label |
| 11 | Release, demo and interview preparation | AI Auditor portfolio release | Fresh setup, measured report, walkthrough and defensible resume bullets |

Phases 0–7 establish the usable evaluated core. Phases 8–10 deepen the same project through advanced experiments. Phase 11 packages the actual implemented and evaluated result. Every advanced lab is a learning/build target; default enablement depends on evidence, cost and runtime constraints.

## Phase 0 — product aur evidence ko manually samjho

**Seekho/research:** Factual claim kya hai? Topic relevance aur actual support mein kya difference hai? RAG retrieval aur claim verification ki responsibilities kya hain? [RAG paper](https://arxiv.org/abs/2005.11401), abstract/introduction; [CRAG paper](https://arxiv.org/html/2401.15884v3), sections 4.1–4.5; [revision checklist](07-revision-check.md).

**Banao:** Three short synthetic documents, original question and one deliberately flawed AI answer. Answer mein six manually reviewed claims rakho: two supported, two contradicted aur two insufficient-evidence cases. Record exact source spans and intended verdicts. Yeh starter exercise hai, complete benchmark nahi.

**Experiment:** Ek evidence passage hide karo; supported case insufficient ho sakta hai. Ek unit/date change karo; topic relevance ke bawajood verdict badal sakta hai. Missing support ko false claim mat label karo.

**Done:** Tum pipeline draw kar sako, har manual verdict justify kar sako aur retrieval error vs verification error explain kar sako.

**Interview:** “AI Auditor kya verify karta hai, aur uske verdicts ka scope kya hai?”

## Phase 1 — inspectable local retrieval

**Seekho/research:** Text normalization, sentence/paragraph boundaries, tokens vs characters, overlap aur lexical ranking. Keyword search paraphrase par kyun miss kar sakta hai? [PostgreSQL text-search concepts](https://www.postgresql.org/docs/current/textsearch-controls.html).

**Banao:** TXT/Markdown files read karne wala small Python CLI. Chunks ke saath document/version/line spans preserve karo. First transparent keyword baseline; PostgreSQL FTS later phase 2 mein. Manually identified claims ko queries ki tarah use karo.

**Experiment:** Same claims par chunk boundaries/overlap compare; identifier vs paraphrase failures record karo. Return top-K evidence with inspectable scores and locators.

**Done:** Every hit ko original text mein locate kar sako; saved results aur first retrieval evaluation available ho. Model-generated claim extraction abhi dependency nahi.

**Interview:** “Chunk size aur overlap ka precision, context aur storage par kya effect hai?”

## Phase 2 — backend aur reliable ingestion

**Seekho/research:** FastAPI/Pydantic contracts, async SQLAlchemy, transactions/migrations, authentication vs authorization, process boundaries, queue retries. [FastAPI background-work caveat](https://fastapi.tiangolo.com/tutorial/background-tasks/#caveat), [ARQ execution semantics](https://arq-docs.helpmanual.io/#usage), [pypdf extraction limits](https://pypdf.readthedocs.io/en/stable/user/extract-text.html).

**Banao:** Docker Compose services; KB/document metadata and memberships; private upload API; TXT/MD/digital-text PDF parsing; ARQ ingestion worker; status and error visibility. Persist ownership from the first DB-backed slice. Introduce persisted job/outbox or dispatch reconciliation so DB commit followed by missed enqueue can recover.

**Experiment:** Same job twice, worker restart, corrupt upload, scanned PDF without OCR, cross-user document fetch and delete/worker race. API/provider usage research happens before real integration.

**Done:** Authorized upload → indexed status works; unauthorized access tests pass; repeat execution creates no duplicate active chunks. Unsupported extraction needs an explicit state.

**Interview:** “Queue retries ke saath idempotency aur DB/queue consistency kaise maintain ki?”

## Phase 3 — semantic aur hybrid retrieval

**Seekho/research:** Embeddings, vector dimensions/model compatibility, cosine/dot/L2, exact neighbors, lexical+dense fusion and cross-encoder reranking. [pgvector docs](https://github.com/pgvector/pgvector), [retrieve/rerank](https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html).

**Banao:** Pluggable embedding call; pgvector exact retrieval; PostgreSQL lexical mode; hybrid/RRF mode and optional reranker experiment. Record model/version/dimension and keep source provenance.

**Experiment:** Same source-labeled claims par lexical, dense, hybrid aur reranked outputs compare. Candidate coverage, Hit/Recall@K, MRR and retrieval latency report. Include numbers, negations and English/Hinglish paraphrases. Initial starter cases expand into at least 20 reviewed learning cases; enlarge further for representative validation.

**Done:** Mode-specific results reproducible hain; failed paraphrase/identifier cases explain kar sako. Compare relevant evidence, not merely plausible-looking similarity.

**Interview:** “Semantic retrieval alone enough kyun nahi? Fusion aur reranking mein kya difference hai?”

## Phase 4 — baseline AI Auditor

**Seekho/research:** Atomic factual claims, context preservation, support/contradiction, missing evidence, structured outputs and citation validation. Retrieval assessment evidence usefulness dekhti hai; verifier claim/evidence relation dekhta hai. [Audit scope](10-ai-auditor-scope.md), [evaluation contract](05-evaluation-contract.md).

**Banao:** AI answer → claim extraction → fixed retrieval → evidence verification → structured audit report. Preserve exact original answer span per claim. Begin verifier development with manual claims; then compare automatic extraction against reviewed claims. Add authorized audit submit/status/history APIs.

**Experiment:** Compound sentences, qualifiers, wrong units/dates, empty retrieval and fabricated citation IDs. Topic-relevant supporting aur opposing passages dono retain karo; disagreement irrelevant evidence nahi hai.

**Done:** Per-claim supported/contradicted/insufficient verdicts, source IDs/locators and explanations available. Baseline report is versioned; no correction gains claimed yet. Split development/held-out examples before threshold tuning.

**Interview:** “AI judge ki mistakes kaise measure ki? Insufficient evidence contradiction kyun nahi hai?”

## Phase 5 — CRAG-inspired correction

**Seekho/research:** Retrieval evaluator, evidence sufficiency, threshold tuning, refining, rewriting, state-machine control and budgeted stop conditions. Original CRAG vs our private-KB adaptation: [design](08-crag-design.md).

**Banao:** Per-candidate evidence assessment and set-coverage gate. Useful supporting/opposing spans preserve karo. Weak evidence → targeted rewrite/retrieve/re-evaluate, maximum two correction rounds plus explicit time/call/token budgets. Persistent weak evidence → insufficient verdict; evaluator failure is a visible controlled failure.

**Experiment:** Fixed retrieval vs filter-only vs filter+correction. Measure evidence retention, false rejection/acceptance, actual recovery, end-to-end cost and latency. Add repeated-query and query-drift cases. Positive-looking evaluator scores alone recovery prove nahi karte.

**Done:** Every action/stop reason inspectable; retry permissions unchanged; baseline comparison report includes improvements, regressions and inconclusive cases.

**Interview:** “Correction kab help karti hai, kab damage? Loop aur grader hallucination kaise control ki?”

## Phase 6 — usable audit report UI

**Seekho/research:** Next.js/TypeScript data flow, upload/polling states, safe rendering, asynchronous jobs and source navigation. Framework versions/official setup instructions phase start par verify karo.

**Banao:** Document/KB selector, question + AI-answer input, audit progress, claim verdict table, cited source viewer, audit history and correction trace. Live progress/polling se start; streaming if useful and justified.

**Experiment:** Empty/loading/error states, long answer, interrupted job, unauthorized source click, deleted source and PDF page vs TXT/MD line navigation.

**Done:** Complete demo: documents upload → answer submit → audit status → claim report → actual cited evidence. UI uncertainty and missing evidence clearly communicate kare.

**Interview:** “Async ingestion/audit UX aur source authorization kaise work karta hai?”

## Phase 7 — rigorous evaluation aur hardening

**Seekho/research:** Dataset leakage, judge limitations, confusion matrices, citation correctness, groundedness, observability and operational failure semantics. [Evaluation guidance](05-evaluation-contract.md), [Ragas paper](https://arxiv.org/abs/2309.15217), [OWASP RAG security](https://cheatsheetseries.owasp.org/cheatsheets/RAG_Security_Cheat_Sheet.html).

**Banao:** Versioned evaluation command/report, traces/structured logs, latency/usage/failure dashboard; bounded provider retries, rate limits, deletion lifecycle and representative integration tests. Existing authorization/idempotency controls ko yahan broaden karo.

**Experiment:** Held-out cases, injection in documents/answers, cross-user and stale/deleted evidence, provider limits/outages, concurrency and budget exhaustion. Judge outputs ko human-reviewed labels se compare karo.

**Done:** Retrieval, extraction, verification and correction failures separate report hon; accepted baseline goals freeze before held-out run. Fresh run actual numbers reproduce kare; private raw content logs mein expose na ho.

**Interview:** “Quality objectively kaise establish ki? P95 aur per-audit cost kaise measure ki?”

## Phase 8 — modern query/context improvement labs

Research/build details and primary sources: [labs A1–A5](06-modern-rag.md).

**Seekho/banao:** Contextual Retrieval, parent-child/sentence-window expansion, multi-query rewriting/decomposition aur HyDE. Each ko separate experiment configuration banao; a single giant pipeline mein sab ek saath introduce mat karo.

**Experiment:** Plain vs contextual indexes; small retrieval hits vs expanded context; original vs transformed queries. Synthetic context/HyDE text ko original evidence mat label karo. Measure provenance preservation, query drift and extra model calls.

**Done:** Each lab has reading notes, mechanism explanation, runnable comparison and adopt/reject/revisit decision. Helpful standalone changes ke combinations separately compare hon.

**Interview:** “Contextual indexing, context expansion aur query expansion mein mechanism-level difference kya hai?”

## Phase 9 — representation aur index research

Research/build details: [labs B1–B2 and pgvector readings](06-modern-rag.md).

**Seekho/banao:** Exact vs HNSW with permission filters; early vs late chunking; single-vector vs ColBERT-style late interaction. Compatible token-level/runtime access verify karo. Start multi-vector scoring on a tiny corpus.

**Experiment:** Same eligible vectors/query/filter; inspect query plans. Report ANN neighbor recall separately from task relevance. Record dimensions, vector count, index size, memory, compute and warm/cold latency.

**Done:** Three independently explainable experiments; no single-vector index labeled full late-interaction implementation. Exact reproduction vs inspired prototype explicitly documented. Hardware blockers trigger a precise smaller experiment plan.

**Interview:** “Late chunking vs late interaction? Filtering ke saath ANN behavior kyun change hota hai?”

## Phase 10 — advanced RAG research inside AI Auditor

[Modern lab catalog](06-modern-rag.md) is the reading/method reference. Yeh phase sub-labs mein complete hoga:

| Sub-lab | Seekho aur prototype | Required evidence |
| --- | --- | --- |
| 10A | Self-RAG mechanisms, support critique and adaptive routing | Reflection-token training vs prompt-only inspired variant accurately labeled; route/verification errors |
| 10B | Agentic retrieval tools and bounded controller | Authorized keyword/semantic/read tools, multi-hop audit traces, call budgets and cancellation |
| 10C | RAPTOR-style hierarchy and GraphRAG | Tree/graph summaries with original source mapping; local/global questions and update/deletion effects |
| 10D | Layout-aware parsing and multimodal retrieval | Table/chart/page evidence; structured parser and ColPali-style retrieval comparisons with page/region labels |
| 10E | Selected current research reproduction | Full-method/code/license review, narrow reproducible test, negative results and limitations |

Each sub-lab: controlled dataset → prediction → minimal implementation → baseline comparison → interview explanation. Derived summaries/graphs must respect source permissions and deletion. A retrieved image/page still needs a verifier capable of assessing its evidence.

**Done:** Every completed lab has inspectable artifacts and actual outcomes. Compute/provider limitations are documented; no paper reproduction or completed feature claimed without evidence. Frontier readings refresh before implementation.

**Interview:** “Is advanced method ne AI Auditor mein kya measurable value add ki, aur complexity kab justified nahi thi?”

## Phase 11 — portfolio release

**Seekho:** System design narration, experiment interpretation, debugging walkthrough and concise technical writing.

**Banao:** Fresh-machine setup guide, architecture/data-flow notes, measured evaluation report, known limitations, reproducible demo dataset, short walkthrough and interview Q&A. Package the implemented app as `AI-Auditor-v1.0.zip` after acceptance checks.

**Experiment:** Fresh checkout/install and end-to-end audit run. Demonstrate a correct verdict, a baseline retrieval miss, an attempted correction and a failure/insufficient-evidence case. Outcomes actual run se choose karo; success script mat fabricate karo.

**Done:** Student can explain one source-to-verdict trace, one recovered failure and one unresolved trade-off; reproduce reported numbers; and write resume bullets with actual measurements.

**Interview:** “Agar dobara build karna ho toh kya simplify karoge, aur kyun?”

## Phase 0 ka first session

Start the prepared [Phase 0 workshop](../phase-00/README.md); source files, case and unanswered worksheet are included. Reference key is assistant-authored and provisional until human review.

1. AI Auditor ka input/output apne words mein likho.
2. Three verdict definitions ek example each ke saath explain karo.
3. Three small reference docs aur one answer select/create karo.
4. Six claims ke expected verdict, source span and reason manually record karo.
5. Predict karo: relevant source hide karne par kya result hona chahiye?
6. Retrieval evaluator aur claim verifier ki separate responsibilities explain karo.

Starter worksheet fields: `case_id, question, original_answer, claim_id, claim_text, answer_span, source_version, source_span, expected_verdict, rationale`. Missing source support ke liye empty evidence field valid hai.

## Project rules and checkpoints

- Evidence aur evaluation Phase 0 se; ownership Phase 2 se; untrusted-input awareness throughout.
- Every phase keeps an inspectable artifact and a design/experiment note. Use the [notebook template](04-experiment-template.md).
- Capture development config, corpus/source versions, model settings and commands. Freeze candidate selection before held-out runs.
- Check primary sources before provider/API/runtime integration; pricing and version compatibility are implementation-time research items.
- Baseline and experimental modes stay comparable. Measure accuracy/support together with coverage, latency and cost.
- A runnable phase is not automatically mastery; explain, predict and debug it. Progress is not pre-marked complete.
- Overall pace depends on sessions, corpus, hardware and trial budget; decide scheduling after early phases reveal actual effort.

## Proposed API and data-model reference

| Endpoint | Responsibility |
| --- | --- |
| `POST /api/v1/documents` | Authorized KB upload and async ingestion acceptance |
| `GET /api/v1/documents` | Accessible documents/status |
| `GET /api/v1/documents/{id}` | Authorized metadata/status |
| `DELETE /api/v1/documents/{id}` | Revocation and indexed/file cleanup lifecycle |
| `POST /api/v1/audits` | Question/AI answer plus authorized KB context |
| `GET /api/v1/audits` | Authorized audit history |
| `GET /api/v1/audits/{id}` | Status, claim verdicts, citations and trace |
| `POST /api/v1/evaluations/run` | Authorized bounded evaluation job |
| `GET /health` | Process health; readiness separately specified |

Phase 2 defines KB/membership/source-fetch contracts too. Proposed core entities: organizations, memberships, knowledge_bases, knowledge_base_access, documents, document_versions, ingestion_jobs, chunks, audit_runs, audit_claims, claim_evidence, evaluation_runs. Exact schema follows the bounded slice and actual authorization model.

This is the learning sequence. Current code and actual verification are tracked in [build status](11-build-status.md); read the [Hinglish code walkthrough](12-code-walkthrough-hinglish.md) alongside it. Delivered implementation does not prove learner mastery or production readiness.
