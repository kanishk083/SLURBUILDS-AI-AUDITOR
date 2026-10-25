---
created: 2026-10-25
project: production-rag-learning
type: decision
confidence: medium
---

# Corrective RAG — selected core design

## Summary

Kanishk ne retrieval-quality evaluation, filtering aur bounded correction ko **AI Auditor** ka core select kiya hai. Students ise resume/interview portfolio project ke roop mein build karenge. Current product scope: [AI Auditor](10-ai-auditor-scope.md). Teaching research-first aur Hinglish rahegi.

## Detail

### Naming aur source check

**CRAG = Corrective Retrieval-Augmented Generation.** Original method retrieval evaluator, action selection, knowledge refinement aur web search use karta hai. [Primary source: CRAG, sections 4.1–4.5](https://arxiv.org/html/2401.15884v3)

**Self-RAG** separately trained reflection-token approach hai. Dono methods related research directions hain; interchangeable names nahi. [Primary source: Self-RAG](https://arxiv.org/abs/2310.11511)

Hamari first implementation private knowledge bases par CRAG-inspired adaptation hogi. Web fallback later, separately configured extension rahega. Private evidence ki kami ko public web automatically fill nahi karega. Is design ka goal unsupported answers reduce karna hai; zero hallucinations guarantee nahi.

### Hypothesis

Agar answer generation se pehle irrelevant context remove karein aur weak evidence par bounded correction karein, toh fixed-retrieval baseline ke comparison mein unsupported answers kam ho sakte hain. Evaluator ki mistakes se useful evidence lose aur latency/cost increase ho sakti hai.

Minimal test: same labeled questions par baseline, filter-only aur filter-plus-correction compare karo. Blind spots: empty evidence, near-match wrong facts, partial multi-part answers aur rewritten query drift.

Blast radius: evidence selection answerability, citations, end-to-end latency aur inference cost affect karegi. Correction har retry par same user/KB permission scope mein chalegi.

### AI Auditor mein role

Product AI-generated answer ko factual claims mein split karke reference documents se verify karega. Neeche ka flow corrective evidence-retrieval subsystem explain karta hai; accepted evidence ke baad claim verifier supported, contradicted ya insufficient-evidence verdict deta hai. Input answer ko reference evidence mat samjho. Manual question exercises subsystem learning ke liye hain.

### Proposed flow

```text
Question + authorized KB scope
  → retrieve candidates
  → evaluate passages against original question
  → filter irrelevant spans; preserve original provenance
  → assess retained evidence coverage
      sufficient → answer with citations
      partial/uncertain → preserve useful evidence + rewrite + retrieve
      absent → rewrite + retrieve
  → re-evaluate within fixed round/time/token budgets
      still insufficient / budget exhausted → explain missing evidence
```

Yeh project policy hai, original paper ke action rules ki exact reproduction nahi. Good match milna multi-part question ke har part ka support establish nahi karta.

### Components aur contracts

| Component | Responsibility |
| --- | --- |
| Retriever | Authorized candidates with source IDs, version, spans and raw text |
| Retrieval evaluator | Original question vs each passage relevance/support assessment; score/rationale and supporting span |
| Evidence gate | Retained set se question sufficiently covered hai ya missing pieces hain? |
| Refiner | Irrelevant spans remove; original units, qualifiers, contradictions and provenance preserve |
| Query rewriter | Missing evidence ko target karna; original intent, dates, identifiers and scope preserve |
| Controller | Retry count, duplicate-query detection, deadline, token/call budget and stop reason |
| Generator + citation resolver | Accepted source evidence se answer; emitted citation IDs validate |
| Trace | Query versions, candidate IDs, judgments, action reasons, timings and usage inspect karna |

A grader LLM use ho sakta hai; evaluation **answer-generating stage** se pehle hogi. Evaluator backend ko small labeled trial ke baad choose karenge: suitable pair-scoring model aur structured LLM assessment ka quality/cost comparison. Reranker candidate order improve karta hai; gate decide karta hai ki evidence answer support karne ke liye enough hai. Roles alag explain honge.

Similarity/reranker/evaluator scores ko interchangeable mat samjho. Threshold values labeled development cases se choose honge; arbitrary score ko percent correctness label nahi karenge. Prompts, evaluator version aur threshold configuration each run mein record honge.

Starting controller policy: maximum two correction rounds, explicit deadline and model-call/token budget. Same rewritten query repeat ho toh stop or choose a different bounded action. Evaluation unavailable ho toh unchecked evidence silently generate nahi hogi; controlled failure/insufficient-evidence state return karo.

### First learning/build slice

1. CRAG sections 4.1–4.5 read karo. Answer karo: evaluator kya judge karta hai, corrective action kab useful hai, aur scorer galat ho toh kya break hota hai?
2. Three synthetic TXT/Markdown docs aur five questions choose karo. Include one unsupported question and one two-part question with only half the support.
3. Har question ke three candidate passages manually label karo: relevant supporting evidence, relevant but incomplete, irrelevant. Source/version/span save karo; near-match wrong unit/date wala candidate bhi include karo.
4. Inspectable keyword retrieval plus evaluator input/output contract banao. Code se pehle predicted labels/actions likho; model grader ko manual labels se compare karo.
5. Gate add karo, phir bounded rewrite/retrieve loop; generation uske baad. Python/SQL/API revision actual implementation ke saath hogi.

First milestone: question ke saamne selected passages, labels/scores, source locations aur next action visible ho. Implementation and measured fixture reports are available in [build status](11-build-status.md); learner labels/mastery have not been assumed.

### Example — synthetic

Question: “Annual paid leave kitni hai?”

- Passage A: “Full-time staff receive 18 paid leave days per year.” → supports requested fact.
- Passage B: “Meal claims require receipts.” → irrelevant.
- Passage C: “Leave requests need approval.” → topic relevant, requested number absent.

Controller ko A preserve karna, B discard karna, aur C ko number ka sufficient evidence treat nahi karna chahiye. A missing ho toh question-targeted retry; phir bhi support absent ho toh insufficient-evidence response.

### Learning sequence adjustment

Follow the authoritative [phase plan](01-roadmap.md): manual audit labels → local retrieval → authorized ingestion → semantic/hybrid retrieval → baseline claim audit → CRAG correction → report UI → evaluation/hardening → advanced labs. Supporting aur opposing evidence dono relevant ho sakte hain; disagreement ko irrelevance samajhkar filter mat karo.

## Implications

Multi-user ingestion, audit history, source access and security remain part of AI Auditor. Generic chat-oriented portions of the original brief are superseded by the claim-audit workflow. Correction adds evaluator error analysis, provenance-preserving filtering and bounded recovery to the core acceptance criteria. App runs are still required to establish any quality gain.

## Confidence

User-selected direction aur method-name distinction par high confidence; exact evaluator/model/threshold configuration par medium/unknown until experiments.

## Open Questions

Corpus domain/languages, inference budget, available hardware aur evaluator runtime/provider choices. Web extension ka trust/privacy design separately specify hoga.
