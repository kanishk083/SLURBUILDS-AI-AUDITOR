# Phase 0 - AI Auditor ko manually chalao

Aaj tum human retriever aur verifier dono roles perform karoge. Is exercise ka synthetic service sirf reference material hai; AI Auditor general-purpose student portfolio project hi rahega.

## Learning outcome

AI answer ko factual claims mein decompose karo, relevant original evidence identify karo aur supported / contradicted / insufficient-evidence verdict justify karo. Exact source/version/line preserve karo. Learner answers abhi record nahi hue hain.

## 1. Focused research

[Original RAG paper](https://arxiv.org/abs/2005.11401) ka abstract/introduction padho. Extract karo: model ke parameters mein stored knowledge aur externally retrieved knowledge mein kya difference hai? Source context milna correctness guarantee kyun nahi?

[Original CRAG paper](https://arxiv.org/html/2401.15884v3) ka Figure 2 aur section 4.1 padho; phir sections 4.2-4.5 inspect karo. Extract karo: retrieval evaluator kis stage par aata hai aur weak retrieval par action kyun change hota hai? Paper's Correct/Incorrect/Ambiguous retrieval actions ko hamare supported/contradicted/insufficient claim verdicts se alag rakho.

Meri Hinglish reading notes neeche hain; sources ke mechanisms aur hamare audit policy ke beech difference preserve karo.

## 2. Mechanism

RAG mein relevant external passages retrieve karke generation ko context diya jata hai. CRAG retrieval results evaluate/refine karta hai aur corrective actions select karta hai. Original CRAG web search bhi use karta hai; hamara first version apni selected KB mein bounded retry karega.

AI Auditor mein original AI answer audit ka subject hai. Question aur claim se relevant reference passages dhoondhenge, retrieval quality check karenge, phir claim/evidence relation verify karenge. Input answer ka confident tone source proof nahi.

Roles:
- Retriever: claim judge karne ke liye kaunsa original passage relevant hai?
- Retrieval evaluator: kya passage useful aur applicable evidence hai?
- Claim verifier: passage claim ko support, contradict, ya neither karta hai?
- Controller: enough evidence nahi toh targeted retry, budget exhausted toh uncertainty report.

## 3. Verdict rubric

| Verdict | Test |
| --- | --- |
| supported | Source claim ke material facts/qualifiers ko support karta hai; exact wording match necessary nahi |
| contradicted | Source same subject/context mein explicit incompatible fact establish karta hai |
| insufficient_evidence | Provided corpus se support ya contradiction establish nahi hota |

Relevant contradictory evidence ko discard mat karo. A high similarity score could accompany the wrong number, unit, version or subject. Absence of evidence ko proof of falsehood mat banao. Exercise mein fixed source version 1 use hogi; real source conflicts later labs mein aayenge.

Warm-up, main exercise se separate: source says "Office opens at 9 AM." Claim "Office opens at 9 AM" is supported; claim "Office opens at 11 AM" is contradicted; claim "Office has free parking" has insufficient evidence. All facts here synthetic hain.

## 4. Hypothesis and blast radius

Hypothesis: exact source lines aur preserved quantities ke saath manual labels more inspectable honge, aur relevant-versus-supporting distinction clear hoga.

Minimal test: full corpus inspect karke labels do; phir a specific evidence line temporarily unavailable maan kar verdict reassess karo. Expected observations pehle likho. Actual learner results pending hain.

Blast radius: future model evaluation in labels par depend karegi. Wrong reference label se model correct hote hue bhi incorrect score ho sakta hai. Assistant reference key provisional hai; human review ke bina independent gold labels claim nahi honge.

## 5. Your case

Read these full source files:
- [D1 - plans](sources/d1-plans.md)
- [D2 - uploads](sources/d2-uploads.md)
- [D3 - retention](sources/d3-retention.md)

Original question and flawed AI answer: [case.json](case.json). Each factual claim has an ID and its original-answer character span. These are candidate claims for the exercise, not facts to trust.

Write your own decisions in [worksheet.md](worksheet.md). For each claim: verdict, source/version/line or no evidence, exact quote where applicable, and one-line reason. Definitions par rely karo; distribution/count se labels guess mat karo.

The instructor-style [reference key](reference-key.json) exists for review after your own attempt. It is assistant-authored and provisional; it is not your completed worksheet.

## 6. Small failure experiments

E1: D1 line 7 is temporarily unavailable to the retriever. Predict C1's evidence-based verdict using only the remaining corpus; phir full corpus se compare karo. Search mein miss hua source aur real-world fact false hona separate issues hain.

E2: Relevant upload-limit evidence milta hai, lekin audited amount different hai. Kya passage useful hai? Relevant evidence aur claim agreement ko distinguish karo.

E3: Sirf D3 retrieve hota hai for an encryption claim. Topic data-related hone se kya actual encryption evidence establish hota hai? Agli search ke liye targeted query propose karo; answer invent mat karo.

Source files ko is manual exercise mein modify karne ki zarurat nahi. Treat the stated visibility changes as separate hypothetical experiment conditions.

## 7. Understanding checks

1. "Source mein nahi mila" aur "source ne opposite bola" mein difference?
2. Citation text se related ho, par claim prove na kare, toh citation enough hai?
3. Supporting aur opposing passages dono relevant kyun ho sakte hain?
4. Retrieved evidence unavailable ho toh verifier ko kya report karna chahiye?
5. AI Auditor global truth claim kyun nahi karega, aur verdict ka corpus scope kya hai?

## 8. Completion evidence

Your six labels + locators/reasons; E1-E3 predictions; retrieval evaluator vs claim verifier explanation; and one source-to-verdict walkthrough. Inhe actual responses milne ke baad review karenge. Phase 0 automatically complete mark nahi hogi.

After this review: Phase 1 mein local keyword retrieval implement karke same source IDs and manual labels reuse karenge. Provider/API/DB setup us phase ki specific need ke hisaab se aayega.
