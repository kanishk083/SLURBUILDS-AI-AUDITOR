# Evaluation contract

## Dataset before tuning

Pehle 20 manually reviewed learning questions banao; yeh smoke baseline hai, statistical production proof nahi. Release se pehle representative set expand karo aur development vs held-out questions split karo. Repeatedly held-out par tune mat karo.

Cases include: direct fact, paraphrase, exact identifier, multiple sources, boundary-spanning evidence, missing answer, conflicting/versioned documents, English/Hinglish variants, unauthorized document, deleted document aur injected instructions.

Har item mein `query_id`, `question`, `principal/tenant`, `authorized_kb_ids`, `document_versions`, `expected_source_spans`, `expected_facts`, `answerable` aur `case_type` record karo. Chunking badle toh spans se relevant chunks remap karo. Empty relevance labels wali unanswerable query ko Recall@K denominator mein mat daalo.

## Metrics

| Metric | Is project mein definition |
| --- | --- |
| Task Recall@K | Per answerable query: retrieved relevant evidence units / all labeled relevant evidence units; macro-average across queries. Source span hit mapping rule freeze karo. |
| Hit@K | Answerable queries mein fraction jahan at least one relevant evidence unit top K mein hai. Recall@K se alag report karo. |
| MRR@K | First relevant hit rank ka reciprocal; no hit in K means 0; average across answerable queries. |
| ANN neighbor recall@K | Exact top-K neighbor IDs aur ANN top-K IDs ka intersection / K, with identical eligible vectors and filters. Task relevance se separate. |
| Citation correctness | Supported claim-citation pairs / all emitted claim-citation pairs. Zero pairs means N/A, perfect correctness nahi. |
| Citation coverage | Supported claims with valid supporting citation / all verifiable factual answer claims. Abstentions separately evaluate karo. |
| Answer faithfulness | Retrieved evidence se supported factual claims / all verifiable factual claims; human rubric first, judge model + rubric version record karo. No factual claims means N/A. |
| Abstention | Unanswerable queries par abstention rate AND answerable queries par false-abstention rate; counts/confusion matrix bhi. |
| Latency | Retrieval duration, time to first token, aur full answer duration ke p50/p95 separately; concurrency, sample count, failures and warm/cold status record karo. |
| Cost | Actual provider-reported token usage + verified unit pricing; embedding/indexing costs separate. Local compute ko automatically free label mat karo. |
| Failures | Failed queries / attempted queries aur terminal ingestion failures / submitted documents; retries separately. |

## Method

Same corpus, query set, authorization context aur model settings ke saath baseline/candidate compare karo. Deterministic metrics scripts se compute honge; human or LLM judgments ko separately label karo. Stochastic generation ke repeat runs report karo.

Report mein config, command, dataset/source snapshot, measured timestamp aur per-query failures honge. Security violations zero observed hone chahiye in defined tests; finite tests absolute security prove nahi karte.

## Integration acceptance scenarios

- User A ke question, source download, citation, history aur evaluation mein user B ka data expose nahi hota.
- Invalid/oversized uploads reject hote hain; corrupt/scanned files ka explicit inspectable state hota hai.
- Same ingestion job repeat aur worker interruption se duplicate active chunks nahi bante; stuck jobs recover hote hain.
- Concurrent delete/re-ingest se deleted document active index mein resurrect nahi hota.
- Source link correct version/page/span kholta hai; unauthorized/fabricated citation IDs reject hote hain.
- Evidence absent ho toh system insufficient-evidence behavior dikhata hai; valid answerable case par unnecessary abstention track hota hai.
- Malicious document text permission ya tool scope change nahi karta.
- Provider timeout, rate limit aur stream disconnect se observable bounded failure hoti hai; retry partial answers duplicate nahi karta.

Relevance/latency/cost targets baseline dekhne ke baad define aur held-out run se pehle freeze honge. Actual scoped synthetic measurements [build status](11-build-status.md) mein hain; no production-readiness or representative real-world accuracy claim is made.

## AI Auditor claim evaluation

Preserve manual claim labels and original answer spans. Compare extracted factual claims against human-reviewed claims using a documented semantic matching rubric; do not use exact string equality as the only criterion. On aligned claims, report supported/contradicted/insufficient-evidence confusion matrix and per-class precision/recall/F1, plus macro-F1; separately report missed/extra claims so extraction failures do not disappear from the audit results.

Evaluate citations for both supporting and contradicting verdicts against the indicated relation. Topic-relevant opposing evidence must survive retrieval filtering. Missing evidence must not become a contradicted verdict. Report source-version conflicts explicitly and define their evaluation policy.

## CRAG core evaluation

Candidate relevance aur evidence-set sufficiency alag label honge. Ground truth: human-reviewed question/source spans. Evaluator score, reranker score aur vector similarity ko calibrated truth probability mat assume karo.

- Relevant labeled passages mein accepted fraction aur irrelevant passages mein rejected fraction separately report karo. Sab discard karke achchha rejection score lena success nahi.
- Evidence-set sufficiency labels: sufficient, partial/uncertain, absent. Gate ko multi-part questions par missing support identify karna hoga.
- Track false acceptance of insufficient sets, false rejection of sufficient sets, correction recovery, new failures after correction, abstention and total cost/latency.
- Recovery denominator: initially insufficient cases; report how many finish with independently verified sufficient evidence, not only a higher evaluator score.
- Compare fixed retrieval, evaluation/filter only, and evaluation + bounded correction on identical questions/corpus. Freeze thresholds on development data before held-out testing.
- Include empty retrieval, evaluator failure, repeated rewritten query, query drift, relevant-but-contradictory passages, near-miss units/dates, partial multi-hop support and budget exhaustion.

## Advanced technique experiments

Every run records retrieval mode, rewriting/contextualization prompt version, index version, reranker, controller limits and all model calls. Record the original user question alongside transformed queries. Tune on development cases; select the final configuration before held-out validation.

- Multi-query/HyDE: compare against the original query, track query drift and extra generation/embedding calls. Synthetic hypothetical text is never accepted as source evidence.
- Context expansion/compression: measure evidence-span preservation and final context tokens; raw originals remain the citation authority.
- Iterative/agentic: report end-to-end latency, total tokens, tool calls, iterations, budget exhaustion, loop/stop failures and all authorization violations observed. Intermediate answers are not trusted evidence.
- Graph/hierarchy: evaluate local fact and global synthesis questions separately; inspect extraction/summary errors and source backtracking. Index build, update and deletion overhead count.
- Visual retrieval: use page/region relevance labels and answer-support checks for charts/tables. Retrieval score alone does not validate a visual answer.
- Confidence/abstention: evaluate on labeled cases; self-reported certainty is not a calibrated probability. Record correctness versus abstention/coverage, including false abstentions.

Compare the standalone technique and, after it shows value, its combination with the current best development configuration. Keep input corpus, permissions, resource budgets and measurement conditions comparable; disclose unavoidable differences.
