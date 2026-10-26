# AI Auditor - implementation and verification

Validated date: 2026-10-25. Student portfolio release; local Windows CPU execution.

## What passed

- 19 backend integration tests against actual PostgreSQL, Redis, embedding and NLI models.
- Optimized Next.js production build and TypeScript checks.
- Chrome end-to-end flow: private session, real background ingestion/audit, six expected claim verdicts, source viewer, history, evaluation results, graph lab and mobile overflow check.
- PDF ingestion and page provenance; empty/scanned PDF needs-OCR handling.
- CLI search, static Python checks and Compose configuration validation.
- Actual execution of five research mechanism labs and six optional local audit modes.

GitHub Actions is supplied as source; it was not remotely run. Full API/worker container image build was interrupted by disk exhaustion and is unverified.

## Phase delivery matrix

| Phase | Delivered | Evidence / qualification |
| --- | --- | --- |
| 0 | Synthetic corpus, flawed answer, blank learner worksheet and provisional reference labels | Learner/human review remains separate |
| 1 | Local parser/search CLI and source locators | CLI artifact and parser tests |
| 2 | Authorized API/storage, migrations, Redis/ARQ worker and interrupted-job recovery | Real integration tests |
| 3 | Lexical/dense/hybrid modes and fixed-model embeddings | Actual retrieval/report outputs |
| 4 | Claim extraction, NLI verdicts, exact citation/source navigation | Six-claim fixture and provenance tests |
| 5 | Evidence-strip grading/refinement, correction budgets and visible stop reasons | Controlled baseline/filter/corrective reports |
| 6 | Library organization, upload/audit/report/history/source/evaluation UI | Browser workflow and screenshots |
| 7 | Versioned evaluations, per-class metrics, source/model provenance, isolation/deletion/recovery checks | Measured JSON reports and tests |
| 8 | Structural context, parent windows, multi-query and HyDE experiments | Executed local-mode checks; no broad quality claim |
| 9 | Late-pooling/MaxSim and real index/query-plan experiments | Executed mechanism tests; exact labels in method matrix |
| 10 | Bounded planner, entity graph, cluster hierarchy and optional visual adapter | Local prototypes executed; visual adapter and original trained-paper reproductions unverified |
| 11 | Run scripts, locked local environment, CI source, code walkthrough and source packaging | Fresh-process local app/build/browser verification |

## Controlled evaluation

All three compared modes start from the same hybrid top-5 candidates. Baseline disables retrieval grading/refinement; filter enables it; corrective adds bounded retries. Source and model revisions are in each report.

These 24 small cases are assistant-authored synthetic fixtures. Percentages are fixture agreement, not established real-world accuracy.

| Split | Mode | Cases | Fixture agreement | Macro F1 | Recall@5 | MRR@5 |
| --- | --- | --- | --- | --- | --- | --- |
| Development | baseline | 16 | 50.0% | 0.497 | 1.000 | 1.000 |
| Development | filter | 16 | 87.5% | 0.886 | 1.000 | 1.000 |
| Development | corrective | 16 | 87.5% | 0.886 | 1.000 | 1.000 |
| Held-out | baseline | 8 | 87.5% | 0.886 | 1.000 | 1.000 |
| Held-out | filter | 8 | 87.5% | 0.886 | 1.000 | 1.000 |
| Held-out | corrective | 8 | 87.5% | 0.886 | 1.000 | 1.000 |

Filtering/refinement helped on this development fixture. The tiny held-out set did not establish superior overall agreement for filtering or correction over baseline, and correction did not improve over filter-only in either split. No correction-quality gain is claimed.

All annotated evidence spans were retrieved in this small corpus, yet verification still missed cases. TXT-format support and active-storage deletion were conservative misses in development; the upload-limit paraphrase remained a miss in the held-out filtered/corrective modes. Retrieval success does not guarantee verification success.

P50/P95 values in raw reports are observed local timings under the actual workload, including concurrent checks, not isolated speed benchmarks. Local compute cost is not estimated.

Earlier lexical-baseline artifacts are superseded and excluded from the release package.

## Known failures and boundaries

See the research-method matrix and deployment notes. Local sentence extraction and English NLI remain limited. Generated aids never become original evidence. The hosted credentials probe returned authentication failure. Visual inference, full container application deployment and an independent security audit remain unverified.

This delivery does not imply that a student completed the learning exercises or understands all design choices. Use the Hinglish walkthrough and actual failure traces for that learning.

## Typography verification - 2026-10-26

The larger, stronger type scale uses 17px claims/forms, 16px evidence and 14px verdict labels at the default browser setting. The production frontend build and actual Chrome workflow passed. A focused check measured font sizes/weights and found no page-level horizontal overflow at 320, 390, 760, 1024, 1440 and 1920px; the mobile source dialog passed too. Measurements are in [typography checks](../artifacts/typography-checks.json).
