from __future__ import annotations

import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven application settings."""

    # ── Application ───────────────────────────────────────────────
    app_name: str = "multi-system-data-assistant"
    environment: str = "local"
    log_level: str = "INFO"

    # ── CORS ──────────────────────────────────────────────────────
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:3000",
        ]
    )

    # ── Ollama / LLM ─────────────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_api_base: str = "http://localhost:11434"
    ollama_api_key: str = ""
    llm_model: str = "ollama_chat/qwen3:4b"
    litellm_timeout_seconds: int = 60
    pythonutf8: str = "1"

    # ── FastAPI ───────────────────────────────────────────────────
    fastapi_host: str = "0.0.0.0"
    fastapi_port: int = 8001

    # ── MCP Server URLs ──────────────────────────────────────────
    
    mcp_observability_url: str = "http://localhost:8010/mcp"
    mcp_business_url: str = "http://localhost:8010/mcp"
    mcp_action_url: str = "http://localhost:8010/mcp"

    # ── MCP Constraints ──────────────────────────────────────────
    allowed_services: list[str] = Field(
        default_factory=lambda: [
            "payment-service",
            "checkout-service",
            "orders-service",
            "inventory-service",
        ]
    )
    max_time_window_hours: int = 24
    max_log_results: int = 50

    # ── Pydantic Settings ─────────────────────────────────────────
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_adk_model(self):
        """Returns a LiteLlm model instance for ADK agents."""
        from google.adk.models.lite_llm import LiteLlm

        return LiteLlm(model=self.llm_model)


@lru_cache
def get_settings() -> Settings:
    """Singleton factory for application settings."""
    settings = Settings()

    os.environ.setdefault("OLLAMA_API_BASE", settings.ollama_api_base)

    if settings.ollama_api_key:
        os.environ["OLLAMA_API_KEY"] = settings.ollama_api_key

    os.environ.setdefault("PYTHONUTF8", settings.pythonutf8)

    return settings