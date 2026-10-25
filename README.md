# AI Auditor

A runnable, general-purpose student portfolio project that audits AI-generated claims against uploaded reference documents.

**Documents + question + AI answer → claim extraction → scoped retrieval → evidence grading/refinement → bounded correction → verdicts and citations.**

Verdicts: supported, contradicted, insufficient evidence. Missing evidence is not proof that a claim is false.

## Run locally on Windows

Requirements: Python 3.13, Node 22, uv, Docker Desktop running, network access for initial package/model downloads, and several GB of free storage.

From this folder in PowerShell:

```powershell
.\scripts\setup.ps1
.\scripts\start-local.ps1
```

Open [AI Auditor](http://localhost:3000). API reference: [FastAPI docs](http://127.0.0.1:8000/docs).

This machine already has the app configured; use the running local URL. To stop the recorded app processes:

```powershell
.\scripts\stop-local.ps1
```

PostgreSQL and Redis remain available. Use `docker compose stop postgres redis` when you want to stop those services too. No command in the stop script removes volumes.

## Try the complete flow

1. Choose **Open workspace** for a private demo, or create an account.
2. Click **Load sample**. Wait for the three documents to index.
3. Click **Audit answer**. The six-claim sample produces two supported, two contradicted and two insufficient-evidence verdicts in the verified fixture.
4. Expand a claim, open its cited source and inspect its retrieval trail.
5. Open **Compare methods** to run fixture evaluation or scoped research labs.
6. Use **New library** to organize another reference set, or upload your own UTF-8 TXT/Markdown or text-readable PDF.

Each demo session has isolated storage/library access. Demo documents and labels are synthetic, not real product policies or independent human ground truth.

## Implemented components

| Layer | Implementation |
| --- | --- |
| Interface | Next.js, TypeScript, Manrope, responsive report/source/history/evaluation views |
| API | FastAPI, typed requests, opaque HTTP-only sessions, password hashing and ownership checks |
| Persistence | Async SQLAlchemy, PostgreSQL/pgvector, Alembic migrations |
| Jobs | Redis + ARQ, persisted pending state, reconciliation and bounded interrupted-job recovery |
| Retrieval | PostgreSQL full text, local MiniLM vectors, hybrid RRF, exact-search baseline and HNSW research index |
| Verification | Local English NLI with source-preserving evidence strips; optional hosted adapter |
| Corrective loop | Applicability/relevance gate, bounded deterministic rewriting, re-retrieval and visible stop reasons |
| Research | Context enrichment, parent windows, multi-query, HyDE, adaptive/read-only agent modes; token/hierarchy/graph/index labs |
| Evaluation | Versioned synthetic cases, confusion/per-class metrics, Recall@5/MRR@5, latency, source/model provenance |
| Storage | Private local files; UUID paths, upload bounds, duplicate-content handling and source deletion/invalidation |

The selected private-KB approach is CRAG-inspired. Read [exact method boundaries](docs/13-research-method-labels.md) before describing paper reproductions.

## Validation and measured limits

See [build status and actual results](docs/11-build-status.md), [development report](artifacts/evaluation-development.json), [held-out report](artifacts/evaluation-held_out.json), and [research checks](artifacts/research-checks.json).

The verified build has 19 real-service/model backend tests, a passing optimized frontend build, and a passing Chrome desktop/mobile end-to-end workflow. The browser test exercises actual audit, citations, history, fixture evaluations and a graph lab.

These are small, assistant-authored synthetic fixtures. They do not establish real-world accuracy or production readiness. Local extraction is sentence-based; compound/coreferential claims and domain-specific/multilingual inference remain limited.

Configured hosted credentials failed the authentication probe. Hosted and visual adapters are optional and not runtime-verified. Full API/worker image build was interrupted by this machine's C: storage exhaustion; local native API/worker plus Docker database/Redis are verified. [Deployment notes](docs/14-running-and-deployment.md).

## Learn the system in Hinglish

- [Phase-wise code walkthrough](docs/12-code-walkthrough-hinglish.md): actual files/line references, decisions and real failures.
- [Learning/build phases](docs/01-roadmap.md).
- [AI Auditor scope](docs/10-ai-auditor-scope.md).
- [CRAG design](docs/08-crag-design.md).
- [Modern RAG readings](docs/06-modern-rag.md).
- [Phase 0 workshop](phase-00/README.md).

The assistant was authorized to build first and explain afterward. Delivered code does not imply completed learner exercises.

## Reproduce checks

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m backend.cli search "Basic plan price"
.\.venv\Scripts\python.exe scripts\demo_evaluate.py
.\.venv\Scripts\python.exe scripts\demo_evaluate.py --split held_out
.\.venv\Scripts\python.exe scripts\run_research_checks.py
```

With the app running, use `npm test` from `frontend/` for the real browser workflow. Playwright uses installed Chrome; CI installs it explicitly. The GitHub Actions workflow is included but was not remotely executed.

Exact validated Windows package versions and model revisions: [runtime manifest](evaluation/runtime-manifest.json), [local dependency lock](requirements-local.lock). Frontend dependencies use package-lock.json.

Create the source release with `python scripts/package_release.py`. The archive excludes environments, model weights, secrets, private uploaded files and session data.
