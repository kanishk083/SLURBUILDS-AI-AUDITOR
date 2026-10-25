import os
from pathlib import Path
import subprocess
import sys
import pytest_asyncio
import psycopg
import httpx

ROOT = Path(__file__).resolve().parents[1]
os.environ["DATABASE_URL"] = "postgresql+asyncpg://auditor:auditor_local@127.0.0.1:55432/auditor_test"
os.environ["REDIS_URL"] = "redis://127.0.0.1:56379/15"
os.environ["DATA_DIR"] = str(ROOT / ".data-test")
os.environ["DEMO_ENABLED"] = "true"

from backend.api import app
from backend.db import engine
from backend.config import settings
from redis.asyncio import Redis


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def database():
    assert settings().database_url.endswith("/auditor_test")
    with psycopg.connect(
        "postgresql://auditor:auditor_local@127.0.0.1:55432/postgres", autocommit=True
    ) as conn:
        if not conn.execute("SELECT 1 FROM pg_database WHERE datname='auditor_test'").fetchone():
            conn.execute("CREATE DATABASE auditor_test")
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"], cwd=ROOT, check=True, capture_output=True
    )
    (settings().data_dir / "files").mkdir(parents=True, exist_ok=True)
    redis = Redis.from_url(settings().redis_url)
    assert settings().redis_url.endswith("/15")
    await redis.flushdb()
    await redis.aclose()
    yield
    await engine.dispose()


@pytest_asyncio.fixture(loop_scope="session")
async def client(database):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as c:
        response = await c.post("/api/v1/auth/guest")
        assert response.status_code == 201
        yield c


async def library(client):
    return (await client.get("/api/v1/knowledge-bases")).json()[0]["id"]
