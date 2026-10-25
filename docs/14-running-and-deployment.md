# Run and deployment notes

## Verified local topology

Browser on localhost:3000 → Next.js production server → FastAPI on 127.0.0.1:8000. PostgreSQL/pgvector is bound to 127.0.0.1:55432, Redis to 127.0.0.1:56379. API and ARQ worker run as project-scoped native Python processes. Files live under .data/files.

The Windows setup script uses the exact tested local dependency lock. Frontend uses npm ci and an optimized build. Start/stop scripts track process IDs plus creation times so unrelated reused PIDs are not stopped.

On this specific machine, the task-created virtual environment, Torch cache and newly downloaded NLI/generator caches were relocated to D:/AI-Auditor-runtime with original-path junctions after C: became full. Source stays in the project folder. Runtime/cache directories are not shipped in the archive.

## Configuration

Copy .env.example to .env if overriding defaults. Keep real provider credentials server-side and out of version control.

Important settings:
- DATABASE_URL, REDIS_URL and DATA_DIR select local services/storage.
- AUDIT_PROVIDER defaults to local_nli. The browser can choose hosted only when server credentials exist; existence does not establish validity.
- EMBEDDING_MODEL/NLI_MODEL and their revision fields control the models. New embeddings require compatible dimensions and source reindexing.
- DEMO_ENABLED controls private guest/demo endpoints.
- COOKIE_SECURE must be true with HTTPS deployment; ALLOWED_ORIGINS must match the actual browser origin.
- Local model scores/thresholds are experimental, not calibrated truth confidence.

Local operation does not send source text to an external inference API. Optional hosted verification sends selected source passages and claims to the configured provider. Public model weights download during warm-up.

## Docker app profile

The Compose file also defines API, worker and web image builds:

```sh
docker compose --profile app up -d --build
```

This full image path is provided but not fully validated here. Its backend build hit host disk exhaustion; the interrupted storage operation also caused temporary database I/O errors. Volumes were preserved, task runtime files relocated, Docker restarted and the native app/integration/browser tests revalidated.

Do not describe the full container profile as proven in this environment. Ensure adequate host/Docker-disk space before attempting it. Database/Redis Compose services and Compose configuration validation passed.

API readiness precedes worker/web startup. CPU model downloads require time and model-cache storage. The web image bakes its internal API rewrite target during its build.

## Source lifecycle

Documents are immutable upload records identified by content checksum and server-generated ID. Duplicate bytes within a library reuse the record. Ingestion status/errors are queryable; failed documents have a retry API.

Pending state is recoverable even after missed Redis dispatch. A stale active job is recovered after ten minutes, with a three-attempt interruption budget. Normal parsing/provider failures are explicit failed states.

Deletion coordinates through the library lock, removes indexed chunks/private bytes, and invalidates stored audit reports. Coarse library locking favors inspectability/correctness over same-library concurrency.

## Test isolation and data handling

Integration tests use the dedicated auditor_test database, Redis database 15 and .data-test directory. Production/local app uses auditor, Redis database 0 and .data. Tests never truncate the app database.

Source release packaging uses an allowlist. .env, private files, opaque cookies, virtual environments, node_modules, model weights, browser failure traces and runtime logs are excluded.

## Scope limits

- Local extraction uses sentence boundaries, not complete semantic decomposition.
- Default embedding/NLI models were tested on English synthetic references; multilingual/complex reasoning support is not established.
- PDF extraction supports digital text; OCR/layout-rich/visual processing is a separate research path.
- The application stores private files locally; an S3 deployment adapter is not implemented.
- Input size/page/text limits exist, but adversarial PDF resource isolation has not been independently security-audited.
- User workspaces are private/owner-scoped; shared organization role management is not implemented.
- The optional ColPali adapter is unverified and may need additional model access, dependency compatibility and hardware.
- No trained Self-RAG/GraphRAG/ColBERT reproduction, external penetration test, cloud deployment or production-readiness claim is made.
