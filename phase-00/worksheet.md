# Phase 0 - learner worksheet

Status: awaiting learner responses. Empty cells are intentionally unanswered.

Case: [phase00-demo-001](case.json). Source version: synthetic-v1. Verdict choices: supported / contradicted / insufficient_evidence.

## Before you label

Apne words mein AI Auditor ka input/output aur teen verdict definitions likho.

Your explanation:

## Claim labels

| Claim ID | Audited claim | Your verdict | Source ID / version / line | Exact evidence quote, or no evidence | Your reason |
| --- | --- | --- | --- | --- | --- |
| C1 | The Basic plan costs INR 199 per month. | | | | |
| C2 | The Pro plan costs INR 299 per month. | | | | |
| C3 | The maximum size of one uploaded file is 50 MB. | | | | |
| C4 | PDF uploads are supported. | | | | |
| C5 | All stored files are encrypted with AES-256. | | | | |
| C6 | Every account can have unlimited team members. | | | | |

For insufficient evidence, identify that the complete supplied corpus was checked; do not invent an evidence quote or opposing fact.

## Predictions before review

| Experiment | Your predicted behavior | Why? |
| --- | --- | --- |
| E1: D1 line 7 unavailable to retriever | | |
| E2: upload-limit passage disagrees with audited amount | | |
| E3: only retention passage retrieved for encryption claim | | |

For E3, propose a focused rewritten search query:

## Explain the mechanism

Retriever's job:

Retrieval evaluator's job:

Claim verifier's job:

Controller's stopping condition:

## Interview response

In four or five lines: What does AI Auditor verify, how are its verdicts grounded, and what is its limitation when evidence is missing?

## Review notes

Leave blank until learner answers are reviewed. Record corrections and actual understanding evidence here; no invented scores or completed milestones.
