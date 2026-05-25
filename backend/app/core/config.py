from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # =========================================================
    # APP
    # =========================================================

    app_name: str = "Enterprise Secure Multi-Source RAG"

    environment: Literal[
        "local",
        "dev",
        "staging",
        "prod"
    ] = "local"

    api_prefix: str = ""

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000"
        ]
    )

    # =========================================================
    # SECURITY
    # =========================================================

    jwt_secret_key: str = Field(
        default="change-me-in-production",
        min_length=16
    )

    jwt_algorithm: str = "HS256"

    access_token_expire_minutes: int = 60

    rate_limit_per_minute: int = 60

    audit_log_path: str = "audit.log"

    # =========================================================
    # VECTOR DATABASE
    # =========================================================

    vector_backend: Literal[
        "faiss",
        "memory",
        "pgvector"
    ] = "faiss"

    faiss_index_path: str = "./runtime/faiss_index"

    pgvector_database_url: str | None = None

    # =========================================================
    # EMBEDDINGS
    # =========================================================

    embedding_provider: Literal[
        "openai",
        "local"
    ] = "local"

    embedding_model_name: str = (
        "BAAI/bge-small-en-v1.5"
    )

    openai_api_key: str | None = None

    openai_embedding_model: str = (
        "text-embedding-3-large"
    )

    # =========================================================
    # LLM
    # =========================================================

    llm_provider: Literal[
        "openai",
        "stub",
        "ollama"
    ] = "ollama"

    ollama_base_url: str = (
        "http://localhost:11434"
    )

    ollama_model: str = "phi3"

    openai_chat_model: str = "gpt-4.1"

    # =========================================================
    # RERANKER
    # =========================================================

    reranker_provider: Literal[
        "local",
        "cohere"
    ] = "local"

    cohere_api_key: str | None = None

    # =========================================================
    # SQL DATABASE
    # =========================================================

    sql_database_url: str = (
        "sqlite+aiosqlite:///./examples/data/enterprise.db"
    )

    # =========================================================
    # REDIS
    # =========================================================

    redis_url: str | None = None

    # =========================================================
    # AZURE STORAGE
    # =========================================================

    azure_storage_connection_string: str | None = None

    azure_blob_container: str = "documents"

    # =========================================================
    # OCR
    # =========================================================

    tesseract_cmd: str | None = None

    # =========================================================
    # RAG SETTINGS
    # =========================================================

    max_context_chunks: int = 8

    min_answer_confidence: float = 0.45

    # =========================================================
    # OBSERVABILITY
    # =========================================================

    application_insights_connection_string: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
