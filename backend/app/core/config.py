"""
Central application configuration.

All configuration is loaded from environment variables (see .env.example).
Nothing here should ever contain a real secret - defaults are safe for
local/demo usage only.
"""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    app_name: str = "AegisFlow"
    environment: str = Field(default="development")  # development | production
    demo_mode: bool = Field(default=True)  # ALWAYS default to demo/safe mode
    log_level: str = Field(default="INFO")

    # --- Database ---
    database_url: str = Field(default="sqlite:///./aegisflow.db")

    # --- Security ---
    cors_allowed_origins: List[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    max_request_body_bytes: int = Field(default=1_000_000)  # 1 MB
    rate_limit_per_minute: int = Field(default=120)

    # --- AI / Groq ---
    groq_api_key: str = Field(default="")
    groq_model: str = Field(default="llama-3.3-70b-versatile")
    ai_prompt_version: str = Field(default="v1")

    # --- Threat Intel ---
    virustotal_api_key: str = Field(default="")
    enrichment_cache_ttl_seconds: int = Field(default=3600)
    enrichment_timeout_seconds: float = Field(default=5.0)

    # --- RAG ---
    vector_db_path: str = Field(default="./chroma_data")
    embedding_model_name: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    rag_relevance_threshold: float = Field(default=0.35)

    # --- Response actions ---
    enable_real_response_adapter: bool = Field(default=False)  # must stay False by default
    approval_expiry_minutes: int = Field(default=30)

    # --- MCP ---
    mcp_tool_timeout_seconds: float = Field(default=10.0)


@lru_cache
def get_settings() -> Settings:
    return Settings()
