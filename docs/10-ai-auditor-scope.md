---
created: 2026-10-25
project: AI Auditor
type: decision
confidence: high
---

# AI Auditor — student portfolio project

## Summary

Project ka naam sirf **AI Auditor** hai. Students ise build karke resume aur interviews mein RAG, backend engineering aur evaluation skills demonstrate karenge.

## Detail

### Product definition

Reference documents ke against AI-generated answer ke factual claims audit karo. Har claim ke saath source evidence, verdict aur inspectable retrieval/correction trace dikhao. Product general-purpose rahega; teaching Roman-script Hinglish mein hogi.

Students project ke builders hain. Yeh requirement kisi industry workflow ya student-management application ko imply nahi karti.

### Input aur output

Input: uploaded reference documents, original question/context, aur audit karne ke liye AI-generated answer.

Output: claim-by-claim report with:

- Supported: selected source evidence claim ko support karta hai.
- Contradicted: selected source evidence claim se explicitly conflict karta hai.
- Insufficient evidence: available authorized corpus se support ya contradiction establish nahi hua.
- Supporting/opposing source locations and concise explanations.
- Retrieval attempts, rejected evidence, rewritten queries, stop reason and measured latency/usage.

Insufficient evidence ka matlab claim false prove nahi hua. Verdict uploaded/selected corpus ke relative hoga; source correctness aur applicability separately matter karti hain. Conflicting source versions ko silently reconcile mat karo.

### Proposed pipeline

AI answer + question + documents
→ factual claim extraction
→ authorized retrieval per claim
→ retrieval evaluation and relevance filtering
→ weak evidence par bounded query rewriting/retrieval
→ claim/evidence verification
→ verdicts + citations + audit report.

CRAG-inspired loop evidence quality ko verdict generation se pehle assess karega. Claim ke text ko useful search input ke roop mein use karo; use source evidence mat samjho. Retrieval evaluator aur claim verifier alag responsibilities hain.

### First learning/build increment

Three short synthetic reference documents aur one deliberately flawed AI answer se start karo. Answer mein manually reviewed supported, contradicted aur missing-evidence claims rakho. Pehle claims/evidence/verdicts hand-label karo; phir inspectable retrieval plus evaluator contract implement karo. Claim extraction aur model-based verification next increments mein aayenge.

Expected demonstration: system kaunse passages laaya, kaunse reject hue, correction kyun hui aur verdict kis exact evidence par based hai. Implemented code and scoped synthetic evaluation results are now available: [build status](11-build-status.md). Learner labeling/review remains pending independently.

### Student deliverables

Working local app; readable source; reproducible setup; architecture explanation; golden evaluation set; baseline vs corrective evaluation report; failure examples; and a short demo walkthrough.

Resume bullet template, measured results ke baad:
“Built AI Auditor using FastAPI, PostgreSQL/pgvector and a CRAG-inspired retrieval loop to verify AI-generated claims against uploaded documents; evaluated [actual labeled cases] for [measured metrics].”

Placeholders ko actual measurements ke bina numbers se replace mat karo. Interview preparation mein chunking, hybrid retrieval, evaluator errors, correction budgets, citations, authorization, latency and cost trade-offs cover honge.

### Scope order

Authoritative sequence: [phase-wise learning/build plan](01-roadmap.md). Manual audit labels → local retrieval → authorized ingestion → semantic/hybrid retrieval → baseline claim audit → CRAG correction → report UI → deeper evaluation/hardening → modern labs → portfolio release. Evaluation examples begin before tuning.

Modern RAG methods same project ke measured extension labs rahenge. Teaching research-first, focused backend revision aur stepwise experiments preserve karegi.

## Implications

Prior domain-specific use-case recommendations are superseded. Current product title and student portfolio purpose take precedence over the original generic platform brief.

## Open Questions

Reference corpus, model/provider budget and first implementation environment. Product name aur portfolio audience settled hain.
