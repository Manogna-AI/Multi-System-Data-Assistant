from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven application settings."""

    app_name: str = "Google ADK MCP Multi-System Data Assistant"
    environment: str = "local"
    log_level: str = "INFO"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    primary_model: str = "gemini/gemini-2.5-flash"
    fallback_model: str = "ollama/llama3.1"
    google_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"
    litellm_timeout_seconds: int = 20

    observability_mcp_url: str = "http://localhost:8001/mcp"
    business_mcp_url: str = "http://localhost:8002/mcp"
    action_mcp_url: str = "http://localhost:8003/mcp"

    allowed_services: list[str] = Field(default_factory=lambda: ["payment-service", "checkout-service", "orders-service", "inventory-service"])
    max_time_window_hours: int = 24
    max_log_results: int = 50

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
