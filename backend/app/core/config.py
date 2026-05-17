from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Enterprise Secure Multi-Source RAG"
    environment: Literal["local", "dev", "staging", "prod"] = "local"
    api_prefix: str = ""
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    jwt_secret_key: str = Field(default="change-me-in-production", min_length=16)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    rate_limit_per_minute: int = 60
    audit_log_path: str = "audit.log"

    vector_backend: Literal["faiss", "memory"] = "faiss"
    faiss_index_path: str = "./runtime/faiss_index"
    embedding_provider: Literal["openai", "local"] = "local"
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-large"
    llm_provider: Literal["openai", "stub"] = "stub"
    openai_chat_model: str = "gpt-4.1"

    reranker_provider: Literal["local", "cohere"] = "local"
    cohere_api_key: str | None = None

    sql_database_url: str = "sqlite+aiosqlite:///./examples/data/enterprise.db"
    tesseract_cmd: str | None = None
    max_context_chunks: int = 8
    min_answer_confidence: float = 0.45


@lru_cache
def get_settings() -> Settings:
    return Settings()
