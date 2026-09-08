"""
Typed application settings.

All configuration is loaded from environment variables (or a local .env
file during development). Nothing here should ever contain a real secret —
see .env.example for the variable names.
"""
from functools import lru_cache
from typing import List, Literal

from pydantic import AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_env: Literal["local", "staging", "production"] = "local"
    app_url: str = "http://localhost:8000"
    app_secret: str = Field(..., description="Session/signing secret")
    allowed_origins: str = "http://localhost:5173"

    # --- Database ---
    database_url: str = Field(..., description="PostgreSQL connection string")
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # --- LLM provider ---
    llm_provider: Literal["gemini"] = "gemini"
    gemini_api_key: str | None = None
    #gemini_chat_model: str = "gemini-3.6-flash"
    gemini_chat_model: str = "gemini-flash-lite-latest"
    embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = 768

    # --- RAG ---
    rag_top_k: int = 5
    rag_similarity_threshold: float = 0.72

    # --- Email ---
    email_provider: Literal["smtp", "transactional"] = "smtp"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    lead_email_to: str = "info@moinsystemsai.com"

    # --- Rate limiting ---
    rate_limit: str = "30/minute"

    @field_validator("allowed_origins")
    @classmethod
    def _no_wildcard_in_production(cls, v: str) -> str:
        return v

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — import and call this, don't instantiate Settings() directly."""
    return Settings()
