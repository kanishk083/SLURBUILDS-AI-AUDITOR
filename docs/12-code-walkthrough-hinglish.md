# AI Auditor — phase-wise code walkthrough

Learning order [phase plan](01-roadmap.md) mein hai. Actual verification [build status](11-build-status.md) mein hai. Code delivery learner mastery prove nahi karti.

## System ka actual contract

Reference documents + question/context + AI answer → claims → evidence retrieval/evaluation → bounded correction → claim verdicts + citations. Original AI answer audit ka subject hai, source evidence nahi. Verdict selected corpus ke relative hai.

## Phase 0 — claim aur evidence

[phase-00/case.json:2](../phase-00/case.json#L2)

Synthetic fixture mein six candidate claims hain. Supported aur contradicted dono ke liye source evidence chahiye. Insufficient evidence ka matlab false prove hona nahi. Reference key assistant-authored/provisional hai; independently human-validated benchmark nahi.

## Phase 1 — files se passages

[backend/documents.py:22](../backend/documents.py#L22)

TXT/Markdown UTF-8 se read hote hain; PDFs se page text extract hota hai. Paragraph/length boundaries ke saath original page/line range retain hoti hai. Empty image-only PDFs needs-OCR state deti hain.

[backend/cli.py:13](../backend/cli.py#L13)

Local search CLI keyword overlap inspect karne deta hai. Yeh early learning baseline hai. Audit comparison baseline hybrid hai, because filtering/correction ke effect ko same retriever ke against isolate karna hai.

## Phase 2 — API, ownership and worker

[backend/api.py:277](../backend/api.py#L277)

Upload route session, owned library, rate/size/format checks karti hai. File path user filename se nahi, server-generated document ID se banta hai. Content hash same library mein duplicate bytes identify karta hai.

[backend/security.py:44](../backend/security.py#L44)

Opaque cookie browser ke paas hoti hai; database token hash store karta hai. Passwords salted scrypt se hashed hain. Owned-KB lookup har user-facing source/audit path par access isolate karta hai.

[backend/models.py:60](../backend/models.py#L60)

Users, libraries, documents, chunks, audits aur evaluations relational lineage establish karte hain. Vector dimension 384 hai. Model/provider change reindexing/version compatibility decision maangta hai.

[backend/worker.py:121](../backend/worker.py#L121)

Pending DB record durable work/outbox state hai. Redis dispatch miss ho toh reconciliation pending records enqueue karti hai. Interrupted jobs stale deadline aur attempt budget ke through recover hote hain.

[backend/worker.py:18](../backend/worker.py#L18)

Worker already-indexed documents skip karta hai. Chunk publication and indexed status one transaction mein commit hote hain. KB row locks source mutation/deletion aur audit publication coordinate karte hain.

Trade-off: coarse KB lock correctness ko simple rakhta hai, lekin same library concurrency serialize ho sakti hai. A high-concurrency version should use versioned evidence snapshots.

## Phase 3 — hybrid retrieval

[backend/retrieval.py:84](../backend/retrieval.py#L84)

Lexical branch PostgreSQL FTS use karti hai. Dense branch local embeddings + pgvector cosine distance use karti hai. Hybrid RRF ranked positions combine karta hai; incompatible raw scores ko blindly add nahi karte.

Every retrieval selected owned KB ke andar hoti hai. Default app vector path exact search retain karta hai. HNSW separate recorded index/query-plan lab hai.

[backend/runtime.py:25](../backend/runtime.py#L25)

MiniLM locally computes vectors. Static public model weights download hote hain; source text embedding ke liye cloud ko nahi bheja jata. Model revisions configuration mein pinned hain.

## Phase 4 — extraction and verification

[backend/documents.py:93](../backend/documents.py#L93)

Local mode sentence/list/semicolon boundaries se candidate claims nikalta hai, with original answer character offsets. Yeh complete atomic-claim/coreference model nahi. Complex/multi-hop statements ko reviewed splits ya stronger extraction chahiye.

[backend/providers.py:18](../backend/providers.py#L18)

Optional hosted adapter exact input spans, supplied evidence IDs and exact source quotes validate karta hai. Calls/tokens bounded hain. Current configured key authentication probe fail hua; hosted execution validated claim nahi hai.

## Phase 5 — CRAG-inspired correction

[backend/pipeline.py:36](../backend/pipeline.py#L36)

Retriever evidence laata hai. Evaluator relevance/applicability dekhta hai. Verifier evidence/claim relation score karta hai. Supporting aur opposing passages dono useful evidence ho sakte hain.

Observed bug: same source chunk mein Basic 199 aur Pro 499 hone par NLI correct Basic claim ko neutral judge kar raha tha. Retrieval successful tha; evidence too coarse thi. Fix: source lines preserve karke focused evidence strips verify karo.

Named-subject guard wrong entity/product matching penalize karta hai. Yeh heuristic hai, general entity-resolution guarantee nahi.

[backend/runtime.py:49](../backend/runtime.py#L49)

Model entailment, contradiction and neutral scores deta hai. They are model scores, not calibrated probabilities of truth.

[backend/pipeline.py:115](../backend/pipeline.py#L115)

Only support → supported. Only opposition → contradicted. Support + opposition → visible conflict/insufficient status. No decisive evidence → insufficient. Missing evidence ko opposite fact mat assume karo.

[backend/pipeline.py:135](../backend/pipeline.py#L135)

Weak evidence par targeted rewrite/retrieve/re-evaluate hota hai. Maximum two correction rounds, duplicate-query checks, deadline and call/pair budgets bounded behavior enforce karte hain.

Baseline/filter/corrective same hybrid top-5 se start hote hain. Baseline grading/refinement disable karta hai; filter unhe enable karta hai; corrective retries add karta hai. Earlier lexical-baseline artifacts superseded hain.

## Phase 6 — audit report UI

[frontend/app/page.tsx:240](../frontend/app/page.tsx#L240)

UI actual document/index status, audit jobs, source evidence, history, evaluation reports and research labs load karti hai. Pending/running results ko completed report render nahi karte; browser test ne isi boundary par ek real bug catch kiya.

Claim expand karke quote and original location inspect kar sakte ho. Trace queries, retained/rejected evidence, correction and stop reason dikhata hai. Source text React ke normal escaped rendering se show hota hai.

## Phase 7 — evaluation and lifecycle correctness

[backend/evaluation.py:12](../backend/evaluation.py#L12)

Reports development/held-out cases, per-class metrics/confusion matrix, first-round Recall@5/MRR@5 and latency expose karte hain. Source checksums, model revisions and pipeline version recorded hain.

Every annotated case has one expected span; first-round Recall@5 its hit fraction hai. No-evidence cases retrieval denominator se excluded hain. Assistant-authored synthetic label agreement universal accuracy nahi hai.

[tests/test_auditor.py:99](../tests/test_auditor.py#L99)

Integration tests actual PostgreSQL, Redis and local models use karti hain. Auth/isolation, duplicate ingestion, citations, deletion, interrupted-job recovery and controlled comparisons test hote hain.

[backend/api.py:376](../backend/api.py#L376)

Source deletion removes chunks/file and invalidates stored evidence reports. Same KB lock in-flight jobs ko deleted source republish karne se rokta hai.

Actual timing includes retrieval/verification rounds, queue wait and end-to-end audit duration. Local compute automatically free assume nahi hoti; no fabricated price estimate.

## Phases 8–10 — modern research mechanisms

[backend/labs.py:171](../backend/labs.py#L171)

Context enrichment, neighbor windows, multi-query and HyDE selectable experiments hain. Generated aids original evidence nahi. Late pooling context-limited hai; MaxSim token interaction trained ColBERT nahi.

Hierarchy extractive cluster representatives use karti hai; graph lab source-linked entity co-occurrence use karta hai. HNSW lab actual plan record karta hai; small filtered corpora par alternate index choose ho sakta hai.

[backend/agent.py:11](../backend/agent.py#L11)

Planner only whitelisted read/search tools propose karta hai. Invalid model output explicit fallback use karta hai. Original KB scope and call budget never expand. Small generator showed quality failures, so generated text never becomes evidence.

Optional visual adapter is not runtime-verified. Exact method boundaries: [research labels](13-research-method-labels.md).

## Phase 11 — interview/demo

Demo: private workspace → sample documents → audit → C2 conflicting price source → insufficient encryption evidence → correction trace → controlled method comparison.

Interview mein one success, one failure and one design trade-off explain karo. Source-to-verdict trace code ke saath follow karo; unsupported accuracy/revenue claims mat add karo.

Resume template: “Built AI Auditor with FastAPI, PostgreSQL/pgvector, Redis/ARQ and a CRAG-inspired evidence loop; implemented source-grounded claim auditing, isolation/recovery tests and reproducible synthetic evaluations.” Measured numbers ke saath dataset scope state karo.

## Understanding checks

1. Relevant passage claim ko contradict bhi kyun kar sakta hai?
2. Evidence refinement NLI outcome kyun change kar sakti hai?
3. RRF ranks combine karta hai ya raw similarity scores?
4. Missing evidence contradiction kyun nahi?
5. Same retriever ke bina CRAG improvement attribute karna kyun misleading hai?
6. Duplicate jobs aur deletion ke beech correctness kaise preserved hai?
7. Implemented mechanism aur original paper reproduction mein kya difference hai?
