from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    database_url: str = "postgresql+asyncpg://auditor:auditor_local@127.0.0.1:55432/auditor"
    redis_url: str = "redis://127.0.0.1:56379/0"
    data_dir: Path = ROOT / ".data"
    demo_enabled: bool = True
    cookie_secure: bool = False
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    nli_model: str = "cross-encoder/nli-deberta-v3-small"
    embedding_revision: str = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
    nli_revision: str = "fa2804872c3b4bd748f38c0185cc85775361e735"
    generator_revision: str = "0fc9ddf78a1e988dac52e2dac162b0ede4fd74ab"
    model_device: str = "cpu"
    audit_provider: str = "local_nli"
    anthropic_api_key: str = ""
    anthropic_base_url: str = "https://api.anthropic.com"
    anthropic_model: str = ""
    max_upload_bytes: int = 20 * 1024 * 1024
    max_document_chars: int = 300_000
    max_document_pages: int = 100
    max_claims: int = 20
    audit_deadline_seconds: int = 180
    max_corrections: int = 2
    nli_threshold: float = 0.75
    relevance_threshold: float = 0.28


@lru_cache
def settings() -> Settings:
    return Settings()
