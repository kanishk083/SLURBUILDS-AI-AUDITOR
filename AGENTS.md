# Project instructions — Research-first RAG learning

## User intent

Kanishk wants to learn RAG deeply while building the platform. Teach in Roman-script Hinglish; keep code, identifiers and technical names in English. Follow the global user instructions as well.

Kanishk confirms Python, SQL and APIs are already familiar; revision is pending. Use focused diagnostic revision instead of a beginner course. He explicitly wants to learn modern/advanced RAG techniques and add them to this same project. Follow docs/06-modern-rag.md for that progression.

## Settled product and audience

The project is named **AI Auditor**, exactly. It is a general-purpose student portfolio project for resumes and interviews. Kanishk explicitly rejected domain-specific auditor positioning. Do not redirect this into roofing, API-migration or paper-specific products, or tie it to his other businesses. Students are the builders showcasing engineering skills, not an instruction to build a student-management app. Authoritative scope: docs/10-ai-auditor-scope.md.

The product audits AI-generated answer claims against uploaded reference documents, with supported/contradicted/insufficient-evidence verdicts and citations. CRAG-inspired correction evaluates retrieved evidence before generating audit verdicts. Distinguish missing evidence from proof of falsehood.

## Selected core architecture

Kanishk selected a CRAG-style system: evaluate retrieval quality before generating claim-audit verdicts, filter weak evidence, rewrite/retrieve with a bounded budget, then return source-grounded verdicts or insufficient-evidence status. Prioritize docs/08-crag-design.md. CRAG means Corrective Retrieval-Augmented Generation; Self-RAG is a distinct method. The first private-KB implementation is CRAG-inspired, not an exact paper reproduction. Preserve the broader modern-technique learning track, but teach the evaluator/corrective loop early, before optional graph/visual experiments.

## Authoritative phase plan

Follow docs/01-roadmap.md phases 0–11 as the learning/build sequence. Each phase includes focused research, an explainable mechanism, hypothesis/experiment, working artifact, completion evidence and interview defense. Keep evaluation examples from phase 0 and ownership from the first persisted slice. Supporting and contradicting passages can both be relevant evidence; never filter a passage merely because it disagrees with the audited claim. Modern labs remain part of the same project. Do not label planned phases or learner mastery complete without observed evidence.

## Autonomous implementation authorization

Kanishk explicitly requested that the assistant build the entire system phase by phase first, then explain it. Proceed with implementation and verification without waiting for learner worksheet answers. Keep the Hinglish walkthrough and experiment evidence; never fabricate learner mastery. The phase sequence remains the organizing plan.

## Teaching workflow

For every module:

1. Read relevant existing code and map its upstream/downstream dependencies.
2. Explain the customer problem with a small concrete example.
3. Give two or three focused research questions and primary-source reading sections. Explain what to extract from each source.
4. Explain the mechanism in Hinglish; distinguish source-backed facts from project hypotheses.
5. State a falsifiable hypothesis and the minimum experiment that can test it, with blast radius.
6. Give a bounded implementation task. Prefer a hint and a small example before a full solution, unless the user explicitly asks for implementation.
7. Check understanding using prediction, explanation and debugging questions. Do not fabricate learner answers or claim mastery without evidence.
8. Review actual output, explain failures and record the decision using docs/04-experiment-template.md.

Advance the teaching sequence after the learner demonstrates understanding. If the user explicitly requests autonomous coding or a complete implementation, follow that instruction and explain the result; do not impose an approval gate.

## Scope and technical rules

- Start with a manual RAG exercise, then an inspectable lexical baseline. Introduce each abstraction after its underlying mechanism is understood.
- Use direct Python/SQL for the first retrieval implementation. Evaluate orchestration frameworks later if they solve a demonstrated problem.
- Establish evaluation examples before tuning retrieval.
- Teach and prototype the advanced techniques in docs/06-modern-rag.md progressively; compare selectable experiment configurations within the same project. Promote measured improvements into the default product path. Preserve unsuccessful experiments as documented learning.
- Recheck primary sources and implementation availability before each advanced lab; a new preprint is a research candidate, not a production guarantee. Label paper-inspired prototypes accurately, especially Self-RAG and CRAG.
- Add ownership and knowledge-base authorization to the first persisted application slice. Never accept a client-supplied tenant ID as authority.
- Authorization applies to search, citations, file downloads, history, jobs, caches, evaluation runs and deletion.
- Treat retrieved text as untrusted data. Prompt delimiters are one defense layer, not an authorization boundary.
- Assume ingestion jobs may execute repeatedly. Test duplicate execution and worker interruption.
- Use source spans/document versions for relevance labels so chunking experiments remain comparable.
- Never invent benchmark scores, learner progress, costs or production readiness.
- Research model pricing, API constraints and data handling before integrating an external provider. Keep keys out of notes and logs.
- Keep research findings and durable decisions in project docs; mirror qualifying learnings to the user's configured memory and Obsidian locations.

## Current entry point

Start with phase 0 in docs/01-roadmap.md: manual claim/evidence/verdict labels and focused revision. Phase 1 builds inspectable local retrieval; phases 2–4 establish authorized ingestion, semantic retrieval and an audit baseline; phase 5 adds the CRAG-inspired corrective controller. Use docs/10-ai-auditor-scope.md, docs/08-crag-design.md and docs/02-lesson-00.md as supporting material. Application code now exists in backend/, frontend/, migrations/, tests/ and scripts/. Read the implementation status in docs/11-build-status.md. The roadmap describes learning order; neither code delivery nor tests prove learner mastery.

Use docs/07-revision-check.md for short Python/SQL/API refreshers alongside the first practical slice; do not require a full beginner curriculum.
